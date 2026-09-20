"""Wire EZImageFormat / EZVideoFormat into lab graphs that own a canvas.

Not collected by pytest (leading underscore). Builders and the one-shot
patcher import this. Do not rerun film / DCC builders from here.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from _creator_pack3 import PACK3
from _services_pack import SERVICES
from _lab_layout import GROUP_TITLE_INSET, finalize_layout, node_pos, set_node_pos
from _lab_paths import LAB_ROOT, apply_lab_identity, lab_json
from _stamp_app_mode import stamp_suite_graph

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_image.formats import (  # noqa: E402
    CUSTOM_ID,
    get_format,
    load_formats,
)
from ez_image.video_formats import (  # noqa: E402
    FAMILY_LTX,
    FAMILY_WAN,
    get_family,
    get_video_format,
    load_video_formats,
    resolve_video_canvas,
)

FORMAT_BLURB = (
    "Format / platform sets pixels (Custom uses Width × Height). "
    "Quality does not change size."
)
STILL_FORMAT_TYPE = "EZImageFormat"
VIDEO_FORMAT_TYPE = "EZVideoFormat"
STILL_LATENT = "EmptyFlux2LatentImage"
WAN_LATENT = "Wan22ImageToVideoLatent"
LTX_I2V = "LTXVImgToVideo"
LTX_T2V = "EmptyLTXVLatentVideo"
ENHANCE_TYPES = (
    "EZKleinPromptEnhance",
    "EZWanPromptEnhance",
    "EZLTXPromptEnhance",
)
KLEIN_GENERIC = frozenset(
    {
        "stills/still-draft",
        "stills/still-hero",
        "stills/still-daily",
        "stills/still-studio",
        "stills/image-studio",
        "stills/thumbnail",
        "stills/instagram-square",
        "stills/open-graph",
        "stills/banner-wide",
        "stills/shorts-still",
        "stills/hook-still",
        "stills/character-draft",
        "stills/product-packshot",
        "stills/podcast-cover",
        "stills/endcard-cta",
        "stills/quote-bg",
        "stills/lower-third-bg",
        "stills/food-tabletop",
        "stills/identity-sheet",
        "stills/storyboard-6up",
        "stills/dream-house",
        "stills/style-lock",
        "stills/camera-angles",
        "stills/lighting-trio",
        "stills/color-moods",
        "stills/time-of-day",
        "stills/before-after",
    }
)
VIDEO_GENERIC = frozenset(
    {
        "motion/silent/still-to-video-5s",
        "motion/silent/text-to-video-5s",
        "motion/silent/still-to-shot",
        "motion/loops/gif-loop",
        "motion/loops/bumper-loop",
        "motion/loops/sticker-loop",
        "motion/silent/shorts-still-5s",
        "motion/silent/orbit-still-5s",
        "motion/silent/push-in-still-5s",
        "motion/silent/parallax-still-5s",
        "motion/av/still-to-video-8s",
        "motion/av/text-to-video-8s",
        "motion/av/still-to-shot",
        "motion/av/shorts-still-8s",
        "motion/av/hook-av",
        "motion/av/broll-ambient",
        "motion/av/weather-broll",
        "motion/av/interior-ambience",
        "motion/av/dialogue-8s",
        "motion/av/multishot-8s",
        "motion/av/product-hero",
        "motion/av/first-last-8s",
        "motion/silent/first-last-5s",
        "motion/av/audio-to-video-8s",
        "stills/talking-head",
    }
)
STILL_REL_FORMAT = {
    "stills/still-studio": "aspect_16_9_ltx",
    "stills/image-studio": "aspect_16_9_ltx",
    "stills/still-draft": "aspect_16_9_draft",
    "stills/still-hero": "aspect_16_9_ltx",
    "stills/still-daily": "aspect_16_9_mid",
}
PACK3_STILL_KINDS = frozenset({"klein_single", "klein_pack"})
PACK3_VIDEO_KINDS = frozenset({"wan_i2v", "wan_loop", "ltx_av"})
SERVICES_STILL_KINDS = frozenset({"klein_single"})
SERVICES_VIDEO_KINDS = frozenset({"wan_i2v", "wan_loop", "ltx_av"})


def _pack3_rels(kinds: frozenset[str]) -> frozenset[str]:
    return frozenset(spec.rel for spec in PACK3 if spec.kind in kinds)


def _services_rels(kinds: frozenset[str]) -> frozenset[str]:
    return frozenset(spec.rel for spec in SERVICES if spec.kind in kinds)


STILL_SCOPE = KLEIN_GENERIC | _pack3_rels(PACK3_STILL_KINDS) | _services_rels(
    SERVICES_STILL_KINDS
)
VIDEO_SCOPE = VIDEO_GENERIC | _pack3_rels(PACK3_VIDEO_KINDS) | _services_rels(
    SERVICES_VIDEO_KINDS
)
FORMAT_SCOPE = STILL_SCOPE | VIDEO_SCOPE


def format_kind(lab_rel: str) -> str | None:
    """Return ``still``, ``video``, or None when the graph stays locked.

    Args:
        lab_rel: ``extra.lab_rel`` id.

    Returns:
        Kind string, or None.
    """
    rel = str(lab_rel or "").strip()
    if rel in STILL_SCOPE:
        return "still"
    if rel in VIDEO_SCOPE:
        return "video"
    return None


def _nodes_of(graph: dict[str, Any], ntype: str) -> list[dict[str, Any]]:
    return [node for node in graph.get("nodes") or [] if node.get("type") == ntype]


def _lab_rel(graph: dict[str, Any]) -> str:
    extra = graph.get("extra") or {}
    rel = extra.get("lab_rel")
    if isinstance(rel, str) and rel.strip():
        return rel.strip()
    return str(graph.get("id") or "").strip()


def _int_widgets(node: dict[str, Any]) -> list[int]:
    values = node.get("widgets_values")
    if isinstance(values, dict):
        return []
    out: list[int] = []
    for item in values or []:
        if isinstance(item, bool):
            continue
        if isinstance(item, int):
            out.append(item)
        elif isinstance(item, float):
            out.append(int(item))
    return out


def pick_still_format(
    lab_rel: str, width: int, height: int, prefix: str = ""
) -> Any:
    """Choose a still catalog row for a graph's current canvas.

    Args:
        lab_rel: Lab-relative id.
        width: Authored latent width.
        height: Authored latent height.
        prefix: SaveImage prefix when unique in the catalog.

    Returns:
        ``FormatSpec`` (Custom when nothing unique matches).
    """
    pinned = STILL_REL_FORMAT.get(lab_rel)
    if pinned:
        return get_format(pinned)
    rows = load_formats()
    if prefix:
        hits = [row for row in rows if row.prefix == prefix and row.id != CUSTOM_ID]
        sized = [row for row in hits if row.width == width and row.height == height]
        if len(sized) == 1:
            return sized[0]
        if len(hits) == 1:
            return hits[0]
    aspect = [
        row
        for row in rows
        if row.group == "aspect"
        and row.id != CUSTOM_ID
        and row.width == width
        and row.height == height
    ]
    if len(aspect) == 1:
        return aspect[0]
    sized = [
        row
        for row in rows
        if row.id != CUSTOM_ID and row.width == width and row.height == height
    ]
    if len(sized) == 1:
        return sized[0]
    return get_format(CUSTOM_ID)


def pick_video_format(family: str, width: int, height: int) -> Any:
    """Choose a video catalog row for a family's authored size.

    Args:
        family: ``wan`` or ``ltx``.
        width: Authored latent width.
        height: Authored latent height.

    Returns:
        ``VideoFormatSpec`` (Custom when the size is not a preset).
    """
    hits = [
        row
        for row in load_video_formats()
        if row.family == family and row.width == width and row.height == height
    ]
    if hits:
        return hits[0]
    return get_video_format(CUSTOM_ID, family=family)


def _inject_blurb(text: str) -> str:
    """Insert FORMAT_BLURB after the first paragraph when missing."""
    if FORMAT_BLURB in text:
        return text
    stripped = text.strip()
    if not stripped:
        return FORMAT_BLURB + "\n"
    parts = text.split("\n\n", 1)
    if len(parts) == 1:
        return text.rstrip() + "\n\n" + FORMAT_BLURB + "\n"
    return parts[0] + "\n\n" + FORMAT_BLURB + "\n\n" + parts[1]


def ensure_format_note(graph: dict[str, Any]) -> None:
    """Add the Format / platform sentence to the operator note."""
    extra = graph.setdefault("extra", {})
    extra["lab_note"] = _inject_blurb(str(extra.get("lab_note") or ""))
    for node in graph.get("nodes") or []:
        if node.get("type") != "Note":
            continue
        values = list(node.get("widgets_values") or [])
        if not values:
            continue
        values[0] = _inject_blurb(str(values[0] or ""))
        node["widgets_values"] = values


def _next_node_id(graph: dict[str, Any]) -> int:
    ids = [int(node["id"]) for node in graph.get("nodes") or []]
    nid = (max(ids) + 1) if ids else 1
    graph["last_node_id"] = nid
    return nid


def _next_link_id(graph: dict[str, Any]) -> int:
    last = int(graph.get("last_link_id") or 0)
    for link in graph.get("links") or []:
        if isinstance(link, list) and link:
            last = max(last, int(link[0]))
    nid = last + 1
    graph["last_link_id"] = nid
    return nid


def _append_link(
    graph: dict[str, Any],
    src: int,
    src_slot: int,
    dst: int,
    dst_slot: int,
    ltype: str,
) -> int:
    link_id = _next_link_id(graph)
    links = list(graph.get("links") or [])
    links.append([link_id, src, src_slot, dst, dst_slot, ltype])
    graph["links"] = links
    return link_id


def _push_output_link(node: dict[str, Any], slot: int, link_id: int) -> None:
    outputs = list(node.get("outputs") or [])
    while len(outputs) <= slot:
        outputs.append(
            {
                "name": "",
                "type": "*",
                "links": [],
                "slot_index": len(outputs),
            }
        )
    out = outputs[slot]
    existing = list(out.get("links") or [])
    existing.append(link_id)
    out["links"] = existing
    out["slot_index"] = slot
    node["outputs"] = outputs


def _input_slot(node: dict[str, Any], name: str) -> int | None:
    for index, item in enumerate(node.get("inputs") or []):
        if item.get("name") == name:
            return index
    return None


def _ensure_widget_input(
    node: dict[str, Any], name: str, typ: str, link_id: int
) -> int:
    """Attach a widget input, or reuse the existing socket.

    Args:
        node: Destination node.
        name: Widget / input name.
        typ: Comfy type.
        link_id: Link to store on the socket.

    Returns:
        Input slot index.
    """
    inputs = list(node.get("inputs") or [])
    for index, item in enumerate(inputs):
        if item.get("name") == name:
            item["link"] = link_id
            item["type"] = typ
            item["widget"] = {"name": name}
            node["inputs"] = inputs
            return index
    inputs.append(
        {
            "name": name,
            "type": typ,
            "link": link_id,
            "widget": {"name": name},
        }
    )
    node["inputs"] = inputs
    return len(inputs) - 1


def _ensure_plain_input(
    node: dict[str, Any], name: str, typ: str, link_id: int
) -> int:
    """Attach a non-widget STRING input (Enhance context)."""
    inputs = list(node.get("inputs") or [])
    for index, item in enumerate(inputs):
        if item.get("name") == name:
            item["link"] = link_id
            item["type"] = typ
            node["inputs"] = inputs
            return index
    inputs.append({"name": name, "type": typ, "link": link_id})
    node["inputs"] = inputs
    return len(inputs) - 1


def _link_out(
    graph: dict[str, Any],
    src: dict[str, Any],
    src_slot: int,
    dst: dict[str, Any],
    name: str,
    ltype: str,
    *,
    widget: bool = True,
) -> None:
    if widget:
        placeholder = _ensure_widget_input(dst, name, ltype, 0)
    else:
        placeholder = _ensure_plain_input(dst, name, ltype, 0)
    link_id = _append_link(
        graph, int(src["id"]), src_slot, int(dst["id"]), placeholder, ltype
    )
    if widget:
        _ensure_widget_input(dst, name, ltype, link_id)
    else:
        _ensure_plain_input(dst, name, ltype, link_id)
    _push_output_link(src, src_slot, link_id)


def _primary_enhance(graph: dict[str, Any]) -> dict[str, Any] | None:
    for ntype in ENHANCE_TYPES:
        hits = _nodes_of(graph, ntype)
        if hits:
            return hits[0]
    return None


def _first_save(graph: dict[str, Any]) -> dict[str, Any] | None:
    hits = _nodes_of(graph, "SaveImage")
    return hits[0] if hits else None


def _save_prefix(graph: dict[str, Any]) -> str:
    save = _first_save(graph)
    if save is None:
        return ""
    values = save.get("widgets_values") or []
    if values and isinstance(values[0], str):
        return values[0].strip()
    return ""


def _is_loop_graph(graph: dict[str, Any]) -> bool:
    for node in _nodes_of(graph, WAN_LATENT):
        nums = _int_widgets(node)
        if len(nums) >= 3 and nums[2] == 49:
            return True
    for node in _nodes_of(graph, "VHS_VideoCombine"):
        values = node.get("widgets_values")
        if isinstance(values, dict) and values.get("pingpong") is True:
            return True
    return False


def _settings_anchor(graph: dict[str, Any], fallback: dict[str, Any]) -> list[float]:
    for grp in graph.get("groups") or []:
        title = str(grp.get("title") or "")
        if title in {"SETTINGS", "FORMAT"}:
            box = list(grp.get("bounding") or [0, 0, 400, 400])
            return [float(box[0]) + 20.0, float(box[1]) + float(GROUP_TITLE_INSET)]
    x, y = node_pos(fallback)
    return [x, y + 160.0]


def _still_latents(graph: dict[str, Any]) -> list[dict[str, Any]]:
    return _nodes_of(graph, STILL_LATENT)


def _video_latents(graph: dict[str, Any]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for ntype in (WAN_LATENT, LTX_I2V, LTX_T2V):
        found.extend(_nodes_of(graph, ntype))
    return found


def _same_size(nodes: list[dict[str, Any]]) -> tuple[int, int] | None:
    sizes: set[tuple[int, int]] = set()
    for node in nodes:
        nums = _int_widgets(node)
        if len(nums) < 2:
            return None
        sizes.add((nums[0], nums[1]))
    if len(sizes) != 1:
        return None
    return next(iter(sizes))


def _make_still_node(
    nid: int, pos: list[float], spec: Any, width: int, height: int, batch: int
) -> dict[str, Any]:
    return {
        "id": nid,
        "type": STILL_FORMAT_TYPE,
        "pos": pos,
        "size": [360, 220],
        "flags": {},
        "order": nid,
        "mode": 0,
        "inputs": [],
        "outputs": [
            {"name": "width", "type": "INT", "links": [], "slot_index": 0},
            {"name": "height", "type": "INT", "links": [], "slot_index": 1},
            {"name": "batch", "type": "INT", "links": [], "slot_index": 2},
            {"name": "hint", "type": "STRING", "links": [], "slot_index": 3},
            {"name": "prefix", "type": "STRING", "links": [], "slot_index": 4},
            {"name": "context", "type": "STRING", "links": [], "slot_index": 5},
        ],
        "properties": {"Node name for S&R": STILL_FORMAT_TYPE},
        "widgets_values": [spec.label, "none", width, height, batch],
        "title": "Format / platform",
    }


def _make_video_node(
    nid: int,
    pos: list[float],
    family_label: str,
    spec: Any,
    width: int,
    height: int,
) -> dict[str, Any]:
    return {
        "id": nid,
        "type": VIDEO_FORMAT_TYPE,
        "pos": pos,
        "size": [360, 180],
        "flags": {},
        "order": nid,
        "mode": 0,
        "inputs": [],
        "outputs": [
            {"name": "width", "type": "INT", "links": [], "slot_index": 0},
            {"name": "height", "type": "INT", "links": [], "slot_index": 1},
            {"name": "hint", "type": "STRING", "links": [], "slot_index": 2},
            {"name": "prefix", "type": "STRING", "links": [], "slot_index": 3},
        ],
        "properties": {"Node name for S&R": VIDEO_FORMAT_TYPE},
        "widgets_values": [family_label, spec.label, width, height],
        "title": "Format / platform",
    }


def wire_still_format(graph: dict[str, Any]) -> bool:
    """Insert EZImageFormat and link latent / hint / optional prefix.

    Args:
        graph: Serialized lab graph (mutated).

    Returns:
        True when a new format node was inserted.
    """
    if _nodes_of(graph, STILL_FORMAT_TYPE):
        ensure_format_note(graph)
        return False
    latents = _still_latents(graph)
    size = _same_size(latents) if latents else None
    if not latents or size is None:
        return False
    width, height = size
    batch = 1
    nums = _int_widgets(latents[0])
    if len(nums) >= 3:
        batch = nums[2]
    rel = _lab_rel(graph)
    prefix = _save_prefix(graph)
    spec = pick_still_format(rel, width, height, prefix)
    if spec.id != CUSTOM_ID:
        width, height = spec.width, spec.height
    nid = _next_node_id(graph)
    fmt = _make_still_node(
        nid, _settings_anchor(graph, latents[0]), spec, width, height, batch
    )
    graph.setdefault("nodes", []).append(fmt)
    for latent in latents:
        values = list(latent.get("widgets_values") or [])
        if len(values) >= 2:
            values[0], values[1] = width, height
            latent["widgets_values"] = values
        latent["title"] = "Latent (wired from Format)"
        _link_out(graph, fmt, 0, latent, "width", "INT")
        _link_out(graph, fmt, 1, latent, "height", "INT")
        _link_out(graph, fmt, 2, latent, "batch_size", "INT")
    enhance = _primary_enhance(graph)
    if enhance is not None:
        _link_out(graph, fmt, 3, enhance, "duration_hint", "STRING")
        if rel == "stills/still-studio":
            _link_out(graph, fmt, 5, enhance, "context", "STRING", widget=False)
    saves = _nodes_of(graph, "SaveImage")
    wire_prefix = rel == "stills/still-studio" or (
        "/creator/" in rel and len(saves) == 1
    )
    if wire_prefix and saves:
        _link_out(graph, fmt, 4, saves[0], "filename_prefix", "STRING")
    ensure_format_note(graph)
    return True


def wire_video_format(graph: dict[str, Any]) -> bool:
    """Insert EZVideoFormat and link width/height (and hint on non-loop graphs).

    Args:
        graph: Serialized lab graph (mutated).

    Returns:
        True when a new format node was inserted.
    """
    if _nodes_of(graph, VIDEO_FORMAT_TYPE):
        ensure_format_note(graph)
        return False
    latents = _video_latents(graph)
    size = _same_size(latents) if latents else None
    if not latents or size is None:
        return False
    width, height = size
    family = FAMILY_WAN if _nodes_of(graph, WAN_LATENT) else FAMILY_LTX
    spec = pick_video_format(family, width, height)
    if spec.id != CUSTOM_ID:
        width, height = spec.width, spec.height
    else:
        snapped = resolve_video_canvas(family, CUSTOM_ID, width=width, height=height)
        width, height = snapped.width, snapped.height
    family_label = get_family(family).label
    nid = _next_node_id(graph)
    fmt = _make_video_node(
        nid,
        _settings_anchor(graph, latents[0]),
        family_label,
        spec,
        width,
        height,
    )
    graph.setdefault("nodes", []).append(fmt)
    for latent in latents:
        values = list(latent.get("widgets_values") or [])
        if len(values) >= 2:
            values[0], values[1] = width, height
            latent["widgets_values"] = values
        _link_out(graph, fmt, 0, latent, "width", "INT")
        _link_out(graph, fmt, 1, latent, "height", "INT")
    enhance = _primary_enhance(graph)
    if enhance is not None and not _is_loop_graph(graph):
        _link_out(graph, fmt, 2, enhance, "duration_hint", "STRING")
    ensure_format_note(graph)
    return True


def wire_lab_graph(graph: dict[str, Any]) -> bool:
    """Wire a format picker when the graph is in scope.

    Args:
        graph: Serialized lab graph (mutated).

    Returns:
        True when a node was inserted.
    """
    kind = format_kind(_lab_rel(graph))
    if kind == "still":
        return wire_still_format(graph)
    if kind == "video":
        return wire_video_format(graph)
    return False


def dump_wired_graph(path: Path, graph: dict[str, Any]) -> None:
    """Stamp, space, and write a wired lab graph.

    Args:
        path: Destination ``*.json``.
        graph: Graph dict.
    """
    rel = path.relative_to(LAB_ROOT).with_suffix("").as_posix()
    from _wire_image_describe import wire_image_describe
    from _wire_upscale import wire_upscale

    apply_lab_identity(graph, rel)
    wire_lab_graph(graph)
    wire_upscale(graph, rel)
    wire_image_describe(graph)
    stamp_suite_graph(graph)
    finalize_layout(graph)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")


def patch_scoped_lab_graphs() -> list[str]:
    """Wire every in-scope shipped lab graph and rewrite JSON.

    Returns:
        Lab-relative ids that gained a format node (already-wired skipped).
    """
    inserted: list[str] = []
    for rel in sorted(FORMAT_SCOPE):
        path = lab_json(rel)
        graph = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(graph, dict):
            continue
        added = wire_lab_graph(graph)
        dump_wired_graph(path, graph)
        if added:
            inserted.append(rel)
    return inserted


def main() -> None:
    """Patch in-scope lab graphs from the repo root."""
    inserted = patch_scoped_lab_graphs()
    print(f"wired format picker on {len(inserted)} graphs")


if __name__ == "__main__":
    main()
