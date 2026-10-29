#!/usr/bin/env python3
"""Overlay the Quality tier into a graph before the CLI POSTs it to /prompt.

The browser applies the tier table from custom_nodes/ez_quality before Queue,
so a graph under the UI posts overlaid widget values while the CLI submit paths
posted the authored ones. This module is the submit-path seam: read a
serialized graph, resolve one Quality tier, hand the graph to
ez_quality.presets.apply_to_graph (the Python table), and write the result for
the caller to POST. It is the production caller that keeps the table honest.

Globals:
  None on import. Reads only --graph, writes only --out, and reaches for the
  network only when --comfy-url is non-empty.

Arguments:
  python3 scripts/lib/quality_apply.py --graph IN.json --out OUT.json \
      [--quality TIER] [--comfy-url URL]

  --graph      Serialized ComfyUI graph JSON (LiteGraph shape) to read.
  --out        Path to write the overlaid graph to.
  --quality    Tier id from ez_quality.presets.QUALITY_CHOICES. Empty means
               take the tier the graph records on its own EZQuality node.
  --comfy-url  ComfyUI base URL used for the loader combo options. Empty (the
               default) skips the on-disk presence check entirely.

Outputs:
  Nothing on success. One line on stderr when the run fails.

Returns:
  0 when --out holds the overlaid graph; 1 when --graph is missing or is not a
  JSON object, when --quality names an unknown tier, or when --out cannot be
  written.

Tier resolution order: --quality, then the graph's EZQuality widget, then lab.
An unrecognised EZQuality widget value resolves to lab the way the EZQuality
node normalizes it, so only an explicit --quality is ever refused. The
object_info lookup never fails the run: an unreachable ComfyUI skips the loader
presence check instead of blocking the POST.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any, Mapping, NamedTuple

from ez_quality.presets import (
    QUALITY_CHOICES,
    QUALITY_FREE_COMMERCIAL,
    QUALITY_FREE_COMMERCIAL_ALIAS,
    QUALITY_LAB,
    apply_to_graph,
)

# Node type plus widget slot that records the graph's own Quality choice.
QUALITY_NODE_TYPE = "EZQuality"
QUALITY_WIDGET_INDEX = 0

# Seconds to wait on ComfyUI object_info before skipping the presence check.
OBJECT_INFO_TIMEOUT_SECONDS = 2.0

# Accepted --quality spellings, casefolded, plus the free-commercial alias.
_ACCEPTED_TIERS: dict[str, str] = {choice.casefold(): choice for choice in QUALITY_CHOICES}
_ACCEPTED_TIERS[QUALITY_FREE_COMMERCIAL_ALIAS.casefold()] = QUALITY_FREE_COMMERCIAL


class QualityApplyError(Exception):
    """Raised when the graph, the requested tier, or the output is unusable."""


class Availability(NamedTuple):
    """Loader combo options; None skips the on-disk presence check."""

    unets: list[str] | None = None
    clips: list[str] | None = None
    vaes: list[str] | None = None


def _fetch_object_info(comfy_url: str) -> dict[str, Any] | None:
    """GET ``{comfy_url}/object_info``.

    Globals:
      None
    Args:
      comfy_url: ComfyUI base URL; a trailing slash is optional.
    Outputs:
      None. Every transport or decode error is swallowed on purpose.
    Returns:
      The parsed object_info mapping, or None when ComfyUI is unreachable.
    """
    url = f"{comfy_url.rstrip('/')}/object_info"
    try:
        with urllib.request.urlopen(url, timeout=OBJECT_INFO_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:  # offline / unparseable must degrade, never block the POST
        return None
    return payload if isinstance(payload, dict) else None


def _object_info_field(info: Mapping[str, Any], node_type: str, field: str) -> Any:
    """Pull one widget spec out of object_info.

    Globals:
      None
    Args:
      info: Parsed object_info mapping.
      node_type: ComfyUI node class, e.g. ``UNETLoader``.
      field: Widget name, e.g. ``unet_name``.
    Outputs:
      None
    Returns:
      The raw widget spec, or None when any level is absent.
    """
    entry = info.get(node_type) or {}
    inputs = entry.get("input") or {}
    required = inputs.get("required") or {}
    return required.get(field)


def _loader_options(info: Mapping[str, Any], node_type: str, field: str) -> list[str] | None:
    """Read one loader combo option list out of object_info.

    Globals:
      None
    Args:
      info: Parsed object_info mapping.
      node_type: ComfyUI node class, e.g. ``UNETLoader``.
      field: Combo widget name, e.g. ``unet_name``.
    Outputs:
      None
    Returns:
      The option strings, or None when the combo is not described.
    """
    spec = _object_info_field(info, node_type, field)
    if isinstance(spec, list) and spec and isinstance(spec[0], list):
        return [str(item) for item in spec[0]]
    return None


def resolve_availability(comfy_url: str) -> Availability:
    """Resolve the loader combo options the tier table may swap against.

    Globals:
      None
    Args:
      comfy_url: ComfyUI base URL, or empty to skip the lookup.
    Outputs:
      None
    Returns:
      Availability with every field None when the URL is empty or ComfyUI does
      not answer, so apply_to_graph skips the on-disk presence check.
    """
    if not comfy_url:
        return Availability()
    info = _fetch_object_info(comfy_url)
    if info is None:
        return Availability()
    return Availability(
        unets=_loader_options(info, "UNETLoader", "unet_name"),
        clips=_loader_options(info, "CLIPLoader", "clip_name"),
        vaes=_loader_options(info, "VAELoader", "vae_name"),
    )


def recorded_quality(graph: Mapping[str, Any]) -> str:
    """Return the tier the graph records on its own EZQuality node.

    Globals:
      None
    Args:
      graph: Serialized ComfyUI graph.
    Outputs:
      None
    Returns:
      The raw EZQuality widget value, or an empty string when the graph carries
      no usable EZQuality widget.
    """
    for node in graph.get("nodes") or []:
        if not isinstance(node, dict) or node.get("type") != QUALITY_NODE_TYPE:
            continue
        values = node.get("widgets_values") or []
        if isinstance(values, list) and len(values) > QUALITY_WIDGET_INDEX:
            return str(values[QUALITY_WIDGET_INDEX])
    return ""


def canonical_tier(value: str) -> str | None:
    """Map one spelling onto a canonical tier id.

    Globals:
      None
    Args:
      value: Tier id as typed or as the graph recorded it.
    Outputs:
      None
    Returns:
      The QUALITY_CHOICES entry, or None when the spelling is unknown.
    """
    return _ACCEPTED_TIERS.get(str(value or "").strip().casefold())


def resolve_quality(graph: Mapping[str, Any], requested: str) -> str:
    """Pick the tier to overlay: --quality, then the graph, then lab.

    Globals:
      None
    Args:
      graph: Serialized ComfyUI graph (source of the recorded tier).
      requested: The --quality value, or empty to defer to the graph.
    Outputs:
      None
    Returns:
      A canonical tier id.
    Raises:
      QualityApplyError: When --quality names a tier the table does not know.
    """
    if requested:
        choice = canonical_tier(requested)
        if choice is None:
            raise QualityApplyError(f"unknown quality tier: {requested}")
        return choice
    return canonical_tier(recorded_quality(graph)) or QUALITY_LAB


def load_graph(path: Path) -> dict[str, Any]:
    """Read a serialized graph off disk.

    Globals:
      None
    Args:
      path: Path to the graph JSON.
    Outputs:
      None
    Returns:
      The parsed graph mapping.
    Raises:
      QualityApplyError: When the file is missing, unreadable, or not a JSON
        object.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        reason = exc.strerror or str(exc)
        raise QualityApplyError(f"cannot read graph {path}: {reason}") from exc
    try:
        graph = json.loads(raw)
    except ValueError as exc:
        raise QualityApplyError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(graph, dict):
        raise QualityApplyError(f"{path} must hold a JSON object")
    return graph


def write_graph(graph: Mapping[str, Any], path: Path) -> None:
    """Write the overlaid graph.

    Globals:
      None
    Args:
      graph: Graph to serialize.
      path: Destination path.
    Outputs:
      The JSON document at ``path``.
    Returns:
      None
    Raises:
      QualityApplyError: When the destination cannot be written.
    """
    try:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(graph, handle)
            handle.write("\n")
    except OSError as exc:
        reason = exc.strerror or str(exc)
        raise QualityApplyError(f"cannot write {path}: {reason}") from exc


def apply_quality_file(
    *,
    graph_path: Path,
    out_path: Path,
    quality: str,
    comfy_url: str,
) -> None:
    """Overlay one tier into ``graph_path`` and write ``out_path``.

    Globals:
      None
    Args:
      graph_path: Graph to read.
      out_path: Overlaid graph to write.
      quality: --quality value, or empty to use the graph's own tier.
      comfy_url: ComfyUI base URL for loader options, or empty to skip.
    Outputs:
      The overlaid graph at ``out_path``. Prints nothing on success.
    Returns:
      None
    Raises:
      QualityApplyError: On any unusable input or unwritable output.
    """
    graph = load_graph(graph_path)
    tier = resolve_quality(graph, quality)
    availability = resolve_availability(comfy_url)
    apply_to_graph(
        graph,
        tier,
        available_unets=availability.unets,
        available_clips=availability.clips,
        available_vaes=availability.vaes,
    )
    write_graph(graph, out_path)


def _cli(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Globals:
      None
    Args:
      argv: Optional argument list (defaults to ``sys.argv[1:]``).
    Outputs:
      One-line message on stderr on failure; nothing on success.
    Returns:
      0 on success, 1 on a usable-input or write error.
    """
    parser = argparse.ArgumentParser(prog="quality_apply")
    parser.add_argument("--graph", required=True, help="graph JSON to read")
    parser.add_argument("--out", required=True, help="overlaid JSON to write")
    parser.add_argument("--quality", default="", help="tier id (default: the graph's own)")
    parser.add_argument(
        "--comfy-url",
        default="",
        help="ComfyUI base URL for loader combo options (default: skip)",
    )
    args = parser.parse_args(argv)
    try:
        apply_quality_file(
            graph_path=Path(args.graph),
            out_path=Path(args.out),
            quality=args.quality,
            comfy_url=args.comfy_url,
        )
    except QualityApplyError as exc:
        print(f"quality_apply: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
