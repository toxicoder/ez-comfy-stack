#!/usr/bin/env python3
"""Overlay the Detail rung into a graph before the CLI POSTs it to /prompt.

The browser applies the rung table from custom_nodes/ez_quality before Queue,
so a graph under the UI posts overlaid widget values while the CLI submit paths
posted the authored ones. This module is the submit-path seam: read a
serialized graph, resolve one Detail rung, hand the graph to
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
  --quality    Rung id from ez_quality.presets.QUALITY_CHOICES (draft,
               standard, final). A legacy tier id is accepted too and resolves
               onto a rung. Empty means take the tier the graph records on its
               own EZQuality node.
  --comfy-url  ComfyUI base URL used for the loader combo options. Empty (the
               default) skips the on-disk presence check entirely.

Outputs:
  Nothing on success. One line on stderr when the run fails, and one naming a
  rung this graph's model family cannot honor.

Returns:
  0 when --out holds the overlaid graph; 1 when --graph is missing or is not a
  JSON object, when --quality names an unknown tier, or when --out cannot be
  written.

Rung resolution order: --quality, then the graph's EZQuality widget, then
standard. A legacy tier id on either path resolves through
ez_quality.presets.normalize_quality onto a selectable rung, and an
unrecognised EZQuality widget value resolves to standard the way the EZQuality
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
from typing import TYPE_CHECKING, Mapping, NamedTuple, cast

from ez_quality.presets import (
    QUALITY_CHOICES,
    apply_to_graph,
    infer_occupancy,
    normalize_quality,
    tier_is_honored,
)

if TYPE_CHECKING:
    from ez_common import Json, JsonObject

# Node type plus widget slot that records the graph's own Detail choice.
QUALITY_NODE_TYPE = "EZQuality"
QUALITY_WIDGET_INDEX = 0

# Seconds to wait on ComfyUI object_info before skipping the presence check.
OBJECT_INFO_TIMEOUT_SECONDS = 2.0

# Rung a graph with no usable recorded choice falls back to. Read off the same
# normalizer the EZQuality node uses, so the CLI and the node never disagree on
# what "no choice" means.
DEFAULT_RUNG = normalize_quality("")

# Tier ids that are no longer selectable but stay accepted input: an old saved
# graph, --quality, EZ_QUALITY, or a console answer may still name one. Where
# each lands is owned by the table in ez_quality.presets, never by this file.
LEGACY_TIER_IDS: tuple[str, ...] = (
    "lab",
    "custom",
    "high",
    "Free Commercial Use (<$10M)",
    "free_commercial",
    "ultra",
    "max",
    "flux3-fast",
    "flux3-quality",
    "flux3-nvfp4",
    "qwen-image",
    "qwen-image-turbo",
    "qwen-image-nvfp4",
    "qwen-image-turbo-nvfp4",
)

# Accepted --quality spellings, casefolded, each mapped onto the rung it
# resolves to. Selectable rungs resolve to themselves; a legacy id resolves
# through normalize_quality so the stamping below always writes a rung.
_ACCEPTED_TIERS: dict[str, str] = {
    spelling.casefold(): normalize_quality(spelling)
    for spelling in (*QUALITY_CHOICES, *LEGACY_TIER_IDS)
}


class QualityApplyError(Exception):
    """Raised when the graph, the requested tier, or the output is unusable."""


class Availability(NamedTuple):
    """Loader combo options; None skips the on-disk presence check."""

    unets: list[str] | None = None
    clips: list[str] | None = None
    vaes: list[str] | None = None


def _fetch_object_info(comfy_url: str) -> JsonObject | None:
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


def _object_info_field(info: Mapping[str, Json], node_type: str, field: str) -> Json:
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
    entry = cast("JsonObject", info.get(node_type) or {})
    inputs = cast("JsonObject", entry.get("input") or {})
    required = cast("JsonObject", inputs.get("required") or {})
    return required.get(field)


def _loader_options(info: Mapping[str, Json], node_type: str, field: str) -> list[str] | None:
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


def recorded_quality(graph: Mapping[str, Json]) -> str:
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
    for node in cast("list[Json]", graph.get("nodes") or []):
        if not isinstance(node, dict) or node.get("type") != QUALITY_NODE_TYPE:
            continue
        values = node.get("widgets_values") or []
        if isinstance(values, list) and len(values) > QUALITY_WIDGET_INDEX:
            return str(values[QUALITY_WIDGET_INDEX])
    return ""


def canonical_tier(value: str) -> str | None:
    """Map one accepted spelling onto the rung it resolves to.

    Globals:
      None
    Args:
      value: Rung id or legacy tier id, as typed or as the graph recorded it.
    Outputs:
      None
    Returns:
      The resolved rung id, or None when the spelling names neither a
      selectable rung nor a legacy tier id.
    """
    return _ACCEPTED_TIERS.get(str(value or "").strip().casefold())


def resolve_quality(graph: Mapping[str, Json], requested: str) -> str:
    """Pick the rung to overlay: --quality, then the graph, then standard.

    Globals:
      None
    Args:
      graph: Serialized ComfyUI graph (source of the recorded tier).
      requested: The --quality value, or empty to defer to the graph.
    Outputs:
      None
    Returns:
      A resolved rung id, so a legacy tier id never reaches the table.
    Raises:
      QualityApplyError: When --quality names a tier the table does not know.
    """
    if requested:
        choice = canonical_tier(requested)
        if choice is None:
            raise QualityApplyError(f"unknown quality tier: {requested}")
        return choice
    return canonical_tier(recorded_quality(graph)) or DEFAULT_RUNG


def load_graph(path: Path) -> JsonObject:
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


def write_graph(graph: Mapping[str, Json], path: Path) -> None:
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
    """Overlay one rung into ``graph_path`` and write ``out_path``.

    Globals:
      None
    Args:
      graph_path: Graph to read.
      out_path: Overlaid graph to write.
      quality: --quality value (a rung or a legacy tier id), or empty to use
        the tier the graph records on its own EZQuality node.
      comfy_url: ComfyUI base URL for loader options, or empty to skip.
    Outputs:
      The overlaid graph at ``out_path``. Prints nothing on success, or one line
      on stderr naming a rung this graph's family cannot honor.
    Returns:
      None
    Raises:
      QualityApplyError: On any unusable input or unwritable output.
    """
    graph = load_graph(graph_path)
    tier = resolve_quality(graph, quality)
    availability = resolve_availability(comfy_url)
    family = infer_occupancy(graph)
    if not tier_is_honored(family, tier):
        print(
            f"quality_apply: {graph_path} is a {family} graph and cannot honor"
            f" '{tier}'; the graph is written unchanged",
            file=sys.stderr,
        )
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
    parser.add_argument(
        "--quality",
        default="",
        help="Detail rung (draft, standard, final); a legacy tier id also"
        " resolves (default: the graph's own)",
    )
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
