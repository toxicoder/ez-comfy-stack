"""Standalone LTX App duration: 8.00 s / 193 frames.

Not collected by pytest (leading underscore). Tests and the one-shot
patcher import this. Film / concat printers stay 5.00 s / 121 frames.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from _lab_paths import LAB_ROOT, ROOT, lab_graph_paths, lab_rel_of

CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_film.ltx_timing import (  # noqa: E402
    DURATION_APP_S,
    FRAMES_APP,
    FRAMES_DEFAULT,
    ltx_frames_for_duration,
)

LTX_LENGTH_TYPES = frozenset(
    {"LTXVImgToVideo", "EmptyLTXVLatentVideo", "LTXVEmptyLatentAudio"}
)
FILM_KEEP_RELS = frozenset({"motion/av/still-to-shot"})
SUBGRAPH_APP = ROOT / "custom_nodes" / "ez_studio_blocks" / "subgraphs" / "ltx-av-8s.json"
SUBGRAPH_APP_OLD = ROOT / "custom_nodes" / "ez_studio_blocks" / "subgraphs" / "ltx-av-12s.json"
SUBGRAPH_APP_LEGACY = ROOT / "custom_nodes" / "ez_studio_blocks" / "subgraphs" / "ltx-av-5s.json"

# Old lab-rel → 8s lab-rel (full paths only; do not stem-rewrite Wan twins).
APP_REL_RENAMES: dict[str, str] = {
    "motion/av/still-to-video-12s": "motion/av/still-to-video-8s",
    "motion/av/text-to-video-12s": "motion/av/text-to-video-8s",
    "motion/av/shorts-still-12s": "motion/av/shorts-still-8s",
    "motion/av/dialogue-12s": "motion/av/dialogue-8s",
    "motion/av/multishot-12s": "motion/av/multishot-8s",
    "motion/av/first-last-12s": "motion/av/first-last-8s",
    "motion/av/audio-to-video-12s": "motion/av/audio-to-video-8s",
    "dcc/canny-control-12s": "dcc/canny-control-8s",
    "dcc/depth-control-12s": "dcc/depth-control-8s",
    "motion/av/still-to-video-5s": "motion/av/still-to-video-8s",
    "motion/av/text-to-video-5s": "motion/av/text-to-video-8s",
    "motion/av/shorts-still-5s": "motion/av/shorts-still-8s",
    "motion/av/dialogue-5s": "motion/av/dialogue-8s",
    "motion/av/multishot-5s": "motion/av/multishot-8s",
    "motion/av/first-last-5s": "motion/av/first-last-8s",
    "motion/av/audio-to-video-5s": "motion/av/audio-to-video-8s",
    "dcc/canny-control-5s": "dcc/canny-control-8s",
    "dcc/depth-control-5s": "dcc/depth-control-8s",
}

_HINT_RE = re.compile(r"\b(?:5|12) seconds, 24 fps")
_CLOSE_RE = re.compile(r"(?:Five|Twelve) seconds\.")


def iter_nodes(graph: MappingLike) -> list[dict[str, Any]]:
    """Return parent nodes plus nested subgraph nodes.

    Args:
        graph: Comfy workflow or subgraph wrapper.

    Returns:
        Mutable node dicts.
    """
    nodes: list[dict[str, Any]] = []
    raw = graph.get("nodes") or []
    if isinstance(raw, list):
        nodes.extend(n for n in raw if isinstance(n, dict))
    defs = graph.get("definitions") or {}
    if isinstance(defs, dict):
        for sub in defs.get("subgraphs") or []:
            if not isinstance(sub, dict):
                continue
            nested = sub.get("nodes") or []
            if isinstance(nested, list):
                nodes.extend(n for n in nested if isinstance(n, dict))
    return nodes


MappingLike = dict[str, Any]


def is_film_rel(rel: str) -> bool:
    """Return whether ``rel`` is a 90s / long-film graph.

    Args:
        rel: ``_lab``-relative id.

    Returns:
        True for ``films/`` trees.
    """
    return rel.startswith("films/")


def is_standalone_ltx_app(graph: MappingLike, rel: str) -> bool:
    """Return whether this lab graph is a standalone LTX video App.

    Film bibles and the concat-safe ``still-to-shot`` printer stay 5.00 s.

    Args:
        graph: Parsed workflow.
        rel: ``_lab``-relative id.

    Returns:
        True when the canvas owns an LTX video latent and is not a film printer.
    """
    if is_film_rel(rel) or rel in FILM_KEEP_RELS:
        return False
    types = {str(n.get("type") or "") for n in iter_nodes(graph)}
    return bool(types & {"LTXVImgToVideo", "EmptyLTXVLatentVideo"})


def ltx_length(node: MappingLike) -> int | None:
    """Return the authored frame count on an LTX length widget.

    Args:
        node: Comfy node dict.

    Returns:
        Frame count, or None when the node is not an LTX length widget.
    """
    ntype = str(node.get("type") or "")
    values = node.get("widgets_values")
    if ntype not in LTX_LENGTH_TYPES or not isinstance(values, list) or not values:
        return None
    if ntype == "LTXVEmptyLatentAudio":
        return int(values[0])
    if len(values) < 3:
        return None
    return int(values[2])


def apply_ltx_app_length(graph: MappingLike, frames: int = FRAMES_APP) -> None:
    """Stamp ``frames`` onto LTX video/audio latents and 8 s duration copy.

    Args:
        graph: Parsed workflow or subgraph wrapper (mutated in place).
        frames: Legal ``1+8n`` length (lab App default 193).
    """
    for node in iter_nodes(graph):
        ntype = str(node.get("type") or "")
        values = node.get("widgets_values")
        if isinstance(values, list):
            if ntype in ("LTXVImgToVideo", "EmptyLTXVLatentVideo") and len(values) > 2:
                values[2] = frames
            elif ntype == "LTXVEmptyLatentAudio" and values:
                values[0] = frames
            _rewrite_widget_strings(values)
        title = node.get("title")
        if isinstance(title, str):
            for old in ("289", "121"):
                if old in title:
                    node["title"] = title.replace(old, str(frames))
                    break
    extra = graph.get("extra")
    if isinstance(extra, dict):
        for key in ("lab_note", "lab_description"):
            text = extra.get(key)
            if isinstance(text, str):
                extra[key] = rewrite_operator_copy(text)
    for node in iter_nodes(graph):
        if node.get("type") != "Note":
            continue
        values = node.get("widgets_values")
        if isinstance(values, list):
            _rewrite_widget_strings(values)


def _rewrite_widget_strings(values: list[Any]) -> None:
    """Rewrite duration hints and 'Five seconds.' closers in widget slots."""
    for i, val in enumerate(values):
        if not isinstance(val, str):
            continue
        updated = rewrite_operator_copy(val)
        updated = _HINT_RE.sub("8 seconds, 24 fps", updated)
        updated = _CLOSE_RE.sub("Eight seconds.", updated)
        values[i] = updated


def rewrite_operator_copy(text: str) -> str:
    """Rewrite 12 s / 289-frame operator copy to the 8 s App default.

    Also rewrites leftover 5 s App copy. Leaves 90s-film warnings and Wan
    5 s smoke sentences that name silent graphs. Does not rewrite numeric
    coordinates or Gemma4-12b filenames.

    Args:
        text: Note, description, or prompt.

    Returns:
        Updated copy.
    """
    out = text
    out = out.replace("289 frames", f"{FRAMES_APP} frames")
    out = out.replace("**289 frames", f"**{FRAMES_APP} frames")
    out = out.replace("~12 s", "~8 s")
    out = out.replace("(~12 s)", "(~8 s)")
    out = out.replace("12.00s print", "8.00s print")
    out = out.replace("12.00 s print", "8.00 s print")
    out = out.replace("depth-guided 12.00s", "depth-guided 8.00s")
    out = out.replace("**portrait** 12.00s print", "**portrait** 8.00s print")
    out = out.replace("canny**-guided 12.00s print", "canny**-guided 8.00s print")
    out = out.replace("I2V smoke (~12 s)", "I2V smoke (~8 s)")
    out = out.replace("T2V AV smoke (~12 s)", "T2V AV smoke (~8 s)")
    out = out.replace("Vertical AV Shorts I2V (~12 s)", "Vertical AV Shorts I2V (~8 s)")
    out = out.replace("US-safe 12.00s AV I2V print", "US-safe 8.00s AV I2V print")
    out = out.replace("Standalone LTX Apps default to 12.00 s", "Standalone LTX Apps default to 8.00 s")
    out = out.replace("default to 12.00 s", "default to 8.00 s")
    out = out.replace("lab 12.00s", "lab 8.00s")
    out = out.replace("AV ~12 s", "AV ~8 s")
    out = out.replace("SFX ~12 s", "SFX ~8 s")
    out = out.replace("(289 frames = 1+8n @ 24 fps)", f"({FRAMES_APP} frames = 1+8n @ 24 fps)")
    out = out.replace("smoke/demo (289 frames)", f"smoke/demo ({FRAMES_APP} frames)")
    out = out.replace("Widgets: seed 42 fixed · 289 frames", f"Widgets: seed 42 fixed · {FRAMES_APP} frames")
    out = out.replace("Twelve seconds.", "Eight seconds.")
    out = out.replace("12 seconds, 24 fps", "8 seconds, 24 fps")
    return out


def rewrite_app_ids(graph: MappingLike, new_rel: str) -> None:
    """Stamp graph id, lab_rel, catalog widgets, and note headings.

    Args:
        graph: Parsed workflow (mutated).
        new_rel: Canonical ``_lab``-relative id.
    """
    stem = new_rel.rsplit("/", 1)[-1]
    graph["id"] = stem
    extra = graph.setdefault("extra", {})
    extra["lab_rel"] = new_rel
    if extra.get("lab_profile"):
        extra["lab_profile"] = new_rel
    for old, new in sorted(APP_REL_RENAMES.items(), key=lambda item: len(item[0]), reverse=True):
        _replace_in_obj(graph, old, new)
    for node in iter_nodes(graph):
        values = node.get("widgets_values")
        if not isinstance(values, list):
            continue
        for i, val in enumerate(values):
            if val == new_rel or (isinstance(val, str) and val.endswith(stem)):
                continue
            if isinstance(val, str) and val in APP_REL_RENAMES:
                values[i] = APP_REL_RENAMES[val]


def _replace_in_obj(obj: Any, old: str, new: str) -> None:
    """Replace ``old`` with ``new`` in strings nested under ``obj``."""
    if isinstance(obj, dict):
        for key, val in list(obj.items()):
            if isinstance(val, str) and old in val:
                obj[key] = val.replace(old, new)
            else:
                _replace_in_obj(val, old, new)
    elif isinstance(obj, list):
        for i, val in enumerate(obj):
            if isinstance(val, str) and old in val:
                obj[i] = val.replace(old, new)
            else:
                _replace_in_obj(val, old, new)


def assert_frames_contract() -> None:
    """Raise if App/film frame constants drift from duration math."""
    if ltx_frames_for_duration(DURATION_APP_S) != FRAMES_APP:
        raise AssertionError("FRAMES_APP must match ltx_frames_for_duration(8.00)")
    if ltx_frames_for_duration(5.00) != FRAMES_DEFAULT:
        raise AssertionError("FRAMES_DEFAULT must match ltx_frames_for_duration(5.00)")


def dump_graph(path: Path, graph: MappingLike) -> None:
    """Write workflow JSON with trailing newline.

    Args:
        path: Destination.
        graph: Workflow dict.
    """
    path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")


def lab_apps() -> list[tuple[str, Path, dict[str, Any]]]:
    """Return ``(rel, path, graph)`` for every standalone LTX App on disk."""
    rows: list[tuple[str, Path, dict[str, Any]]] = []
    for path in lab_graph_paths():
        rel = lab_rel_of(path)
        graph = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(graph, dict):
            continue
        if is_standalone_ltx_app(graph, rel):
            rows.append((rel, path, graph))
    return rows


def apply_repo() -> list[str]:
    """Patch standalone LTX Apps to 8 s and rename ``*-12s`` stems.

    Returns:
        Human-readable actions taken.
    """
    assert_frames_contract()
    log: list[str] = []
    for rel, path, graph in lab_apps():
        apply_ltx_app_length(graph)
        new_rel = APP_REL_RENAMES.get(rel, rel)
        if new_rel != rel:
            rewrite_app_ids(graph, new_rel)
            dest = LAB_ROOT / f"{new_rel}.json"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dump_graph(dest, graph)
            if dest.resolve() != path.resolve():
                path.unlink()
            log.append(f"moved {rel} -> {new_rel}")
        else:
            dump_graph(path, graph)
            log.append(f"patched {rel}")

    new_sub = SUBGRAPH_APP
    sub_path = next(
        (p for p in (new_sub, SUBGRAPH_APP_OLD, SUBGRAPH_APP_LEGACY) if p.is_file()),
        None,
    )
    if sub_path is not None:
        graph = json.loads(sub_path.read_text(encoding="utf-8"))
        apply_ltx_app_length(graph)
        blob = json.dumps(graph)
        blob = blob.replace("ltx-av-12s", "ltx-av-8s")
        blob = blob.replace("ltx-av-5s", "ltx-av-8s")
        blob = blob.replace("still-to-video-12s", "still-to-video-8s")
        blob = blob.replace("still-to-video-5s", "still-to-video-8s")
        graph = json.loads(blob)
        dump_graph(new_sub, graph)
        if sub_path.resolve() != new_sub.resolve():
            sub_path.unlink()
        log.append("patched subgraph ltx-av-8s")
    return log


if __name__ == "__main__":
    for line in apply_repo():
        print(line)
