"""Shared ComfyUI group geometry, stage layout, and node spacing.

Not imported by pytest collection (leading underscore). Builders import it.

The operator note sits at ``(LAB_X0, LAB_NODE_Y0)``. Check models and Quality
share that row to the right. Remaining nodes flow left-to-right / top-to-bottom
in MODEL → INPUT → PROMPT → SETTINGS → OUTPUT columns (or existing named
SHOT/Beat groups, shifted as blocks under the header).

ComfyUI draws the group title in the top LiteGraph.NODE_TITLE_HEIGHT (30px) of
``group.bounding``. Native ``LGraphGroup.resizeTo`` uses that plus 10px pad.
Lab graphs add a small extra gap so the first node is not flush with the header.

Node spacing uses an estimated Nodes 2.0 (Vue) AABB so serialized LiteGraph
``size`` values do not pack widgets on top of each other. Estimates are never
written back into ``node.size``.
"""

from __future__ import annotations

import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

# LiteGraph.NODE_TITLE_HEIGHT (30) + native resizeTo pad (10) + 16px gap.
GROUP_TITLE_INSET = 56
GROUP_FONT_SIZE = 24
# Operator note origin; pipeline columns start at the same x below the header.
LAB_X0 = 40
LAB_NODE_Y0 = 80
LAB_GROUP_Y0 = LAB_NODE_Y0 - GROUP_TITLE_INSET

# Clear pixels between estimated node AABBs (Nodes 2.0 Vue widgets run taller
# than LiteGraph computeSize). pad=NODE_GAP/2 is the overlap-test expansion.
NODE_GAP = 48.0
ROW_Y_TOLERANCE = 40.0
COL_X_TOLERANCE = 80.0
VUE_HEIGHT_EXTRA = 24.0
GROUP_BOX_PAD = 20.0
QUALITY_TYPE = "EZQuality"
CHECK_TYPE = "EZModelCheck"
NOTE_TYPES = frozenset({"Note", "MarkdownNote"})
GROUP_COLOR_A = "#3f789e"
GROUP_COLOR_B = "#a1309b"

GENERIC_GROUP_TITLES = frozenset(
    {
        "NOTE",
        "QUALITY",
        "MODEL",
        "INPUT",
        "PROMPT",
        "SETTINGS",
        "OUTPUT",
        "DURATION",
        "FORMAT",
    }
)
STAGE_ORDER = ("MODEL", "INPUT", "PROMPT", "SETTINGS", "OUTPUT")
HEADER_STAGES = frozenset({"NOTE", "QUALITY"})

_MODEL_TYPES = frozenset(
    {
        "UNETLoader",
        "CLIPLoader",
        "VAELoader",
        "CheckpointLoaderSimple",
        "CLIPVisionLoader",
        "LoraLoader",
        "DualCLIPLoader",
        "UnetLoaderGGUF",
    }
)
_INPUT_TYPES = frozenset(
    {
        "LoadImage",
        "LoadAudio",
        "EZOptionalImage",
        "EZKleinRefCanvas",
        "EZDCCOccupancyGate",
        "EZDCCLoadGuideStill",
        "EZDCCLoadGuideVideo",
        "EZDCCLoadStillPack",
        "EZImageDescribe",
        "EZDubIngest",
    }
)
_PROMPT_TYPES = frozenset(
    {
        "CLIPTextEncode",
        "EZKleinPromptEnhance",
        "EZWanPromptEnhance",
        "EZLTXPromptEnhance",
        "EZNegativePromptEnhance",
        "EZAceStepPromptEnhance",
        "EZDreamXPromptEnhance",
        "EZLongCatPromptEnhance",
        "EZZimagePromptEnhance",
        "EZCinemaRack",
        "EZAudioRack",
        "EZRapLyrics",
        "EZPodcastScript",
        "EZPodcastLearn",
        "EZCreativeResearch",
        "EZSamplePrompt",
        "EZPromptJoin",
        "EZContextJoin",
        "EZAppForge",
        "TextEncodeAceStepAudio1.5",
        "Trellis2Conditioning",
    }
)
_SETTINGS_TYPES = frozenset(
    {
        "EZImageFormat",
        "EZVideoFormat",
        "EZImageMode",
        "EmptyFlux2LatentImage",
        "EmptyLTXVLatentVideo",
        "LTXVEmptyLatentAudio",
        "EmptyAceStep1.5LatentAudio",
        "EmptyTrellis2LatentStructure",
        "Wan22ImageToVideoLatent",
        "ModelSamplingAuraFlow",
        "ModelSamplingSD3",
        "PrimitiveNode",
        "KSampler",
        "LTXVConditioning",
        "LTXVImgToVideo",
        "LTXVConcatAVLatent",
        "LTXVSeparateAVLatent",
        "LTXVAddGuide",
        "LTXVCropGuides",
        "LTXVModalityGuidance",
        "ConditioningZeroOut",
        "ReferenceLatent",
        "VAEEncode",
        "LTXVAudioVAEEncode",
        "EZUnloadModels",
        "EZBackgroundCast",
        "EZMatchImageSize",
        "EZSnapImage",
        "EZEmptyFlux2FromImage",
    }
)
_OUTPUT_TYPES = frozenset(
    {
        "VAEDecode",
        "VAEDecodeAudio",
        "LTXVAudioVAEDecode",
        "SaveImage",
        "SaveAudio",
        "SaveAudioMP3",
        "VHS_VideoCombine",
        "EZImageUpscale",
        "EZFilmConcat",
        "EZClipConcat",
        "EZClipLastFrame",
        "EZFilmDisclosure",
        "EZPodcastDisclosure",
        "EZAudioMetadata",
        "EZAlbumPack",
        "MeshToFile3D",
        "PaintMesh",
        "ImageFromBatch",
        "ImageScale",
        "AudioAdjustVolume",
        "AudioConcat",
        "AudioMerge",
        "EZAudioLoopToMatch",
        "EZKokoroTTS",
        "EZDubRender",
        "EZDubScript",
        "Trellis2ShapeStage",
        "Trellis2TextureStage",
        "Trellis2UpsampleStage",
        "VaeDecodeShapeTrellis",
        "VaeDecodeStructureTrellis2",
        "VaeDecodeTextureTrellis",
    }
)

# Touching group edges is OK; positive overlap area above this is a defect.
_GROUP_OVERLAP_EPS = 1.0
_MOVE_EPS = 0.5

# Minimum serialized-or-estimated height for widgets that Vue draws taller.
_TYPE_HEIGHT_FLOOR: dict[str, float] = {
    "CLIPTextEncode": 160.0,
    "KSampler": 262.0,
    "SaveImage": 270.0,
    "LoadImage": 314.0,
    "EZQuality": 82.0,
    "EZModelCheck": 140.0,
    "EZImageFormat": 220.0,
    "EZImageMode": 140.0,
    "EZOptionalImage": 120.0,
    "EZKleinRefCanvas": 140.0,
    "EZVideoFormat": 180.0,
    "EZRapLyrics": 420.0,
    "EZPodcastScript": 420.0,
    "EZSamplePrompt": 420.0,
    "EZCreativeResearch": 420.0,
}


def node_pos(node: dict[str, Any]) -> tuple[float, float]:
    """Return (x, y) for a serialized Comfy node."""
    pos = node.get("pos") or [0, 0]
    if isinstance(pos, dict):
        return float(pos.get("0", 0)), float(pos.get("1", 0))
    return float(pos[0]), float(pos[1])


def _coord(value: float) -> int | float:
    """Round canvas coords; keep ints when the value is whole pixels."""
    rounded = round(value)
    if abs(value - rounded) < 0.05:
        return int(rounded)
    return round(value, 1)


def set_node_pos(node: dict[str, Any], x: float, y: float) -> None:
    """Write ``pos`` without switching list/dict shape."""
    pos = node.get("pos")
    cx, cy = _coord(x), _coord(y)
    if isinstance(pos, dict):
        pos["0"] = cx
        pos["1"] = cy
        return
    node["pos"] = [cx, cy]


def node_size(node: dict[str, Any]) -> tuple[float, float]:
    """Return (width, height) for a serialized Comfy node."""
    size = node.get("size", [200, 100])
    if isinstance(size, dict):
        return float(size.get("0", 200)), float(size.get("1", 100))
    return float(size[0]), float(size[1])


def _height_floor(ntype: str) -> float:
    if ntype in _TYPE_HEIGHT_FLOOR:
        return _TYPE_HEIGHT_FLOOR[ntype]
    if ntype.endswith("PromptEnhance"):
        return 420.0
    if ntype.startswith("SaveAudio"):
        return 270.0
    return 0.0


def estimated_node_size(node: dict[str, Any]) -> tuple[float, float]:
    """Return collision size: max(serialized, type floor) plus Vue chrome.

    Never smaller than the stored LiteGraph size. Not written back to JSON.
    """
    width, height = node_size(node)
    ntype = str(node.get("type") or "")
    height = max(height, _height_floor(ntype)) + VUE_HEIGHT_EXTRA
    return width, height


def node_center(node: dict[str, Any]) -> tuple[float, float]:
    """Return the centre of a node's serialized rect (Comfy membership)."""
    x, y = node_pos(node)
    width, height = node_size(node)
    return x + width / 2.0, y + height / 2.0


def contains_centre(box: list[float], cx: float, cy: float) -> bool:
    """True if (cx, cy) lies inside bounding ``[x, y, w, h]`` (inclusive)."""
    x, y, width, height = (float(box[0]), float(box[1]), float(box[2]), float(box[3]))
    return x <= cx <= x + width and y <= cy <= y + height


def group_members(graph: dict[str, Any], group: dict[str, Any]) -> list[dict[str, Any]]:
    """Nodes whose centre sits inside the group rect (Comfy ``containsCentre``)."""
    box = group["bounding"]
    return [node for node in graph.get("nodes") or [] if contains_centre(box, *node_center(node))]


def group(
    gid: int,
    title: str,
    x: float,
    y: float,
    w: float,
    h: float,
    color: str,
) -> dict[str, Any]:
    """Serialize a LiteGraph group with the lab title-bar contract."""
    return {
        "id": gid,
        "title": title,
        "bounding": [x, y, w, h],
        "color": color,
        "font_size": GROUP_FONT_SIZE,
        "flags": {},
    }


def _h_overlap(a: list[float], b: list[float]) -> bool:
    ax, _ay, aw, _ah = a
    bx, _by, bw, _bh = b
    return ax < bx + bw and ax + aw > bx


def _overlap_area(a: list[float], b: list[float]) -> float:
    ax, ay, aw, ah = (float(v) for v in a)
    bx, by, bw, bh = (float(v) for v in b)
    ix = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    return ix * iy


def title_inset_hits(graph: dict[str, Any], inset: float = GROUP_TITLE_INSET) -> list[str]:
    """Groups whose first member node sits under ``inset`` px from the top."""
    hits: list[str] = []
    for grp in graph.get("groups") or []:
        members = group_members(graph, grp)
        if not members:
            continue
        min_y = min(node_pos(node)[1] for node in members)
        top = float(grp["bounding"][1])
        gap = min_y - top
        if gap + 1e-6 < inset:
            title = grp.get("title", "?")
            hits.append(f"{title}: inset {gap:.1f}px < {inset}")
    return hits


def group_overlap_hits(graph: dict[str, Any]) -> list[str]:
    """Pairs of groups whose rects overlap by more than a touching edge."""
    groups = list(graph.get("groups") or [])
    hits: list[str] = []
    for i, a in enumerate(groups):
        for b in groups[i + 1 :]:
            area = _overlap_area(a["bounding"], b["bounding"])
            if area > _GROUP_OVERLAP_EPS:
                hits.append(
                    f"{a.get('title', a.get('id'))} vs {b.get('title', b.get('id'))}: {area:.1f}px²"
                )
    return hits


def ensure_group_title_inset(graph: dict[str, Any], inset: float = GROUP_TITLE_INSET) -> None:
    """Shift each group up so member nodes clear the title bar.

    Keeps group height (bottom moves with top) so stacked neighbours keep their
    gap. Stops at another group's bottom (touching is OK). Does not move nodes;
    remaining shortfalls are builder layout bugs and fail ``title_inset_hits``.
    """
    groups = list(graph.get("groups") or [])
    if not groups:
        return
    # Top-most first so a lower group can rise up to a neighbour that already moved.
    ordered = sorted(groups, key=lambda grp: float(grp["bounding"][1]))
    for grp in ordered:
        members = group_members(graph, grp)
        if not members:
            continue
        box = grp["bounding"]
        min_y = min(node_pos(node)[1] for node in members)
        extra = inset - (min_y - float(box[1]))
        if extra <= 0:
            continue
        new_y = float(box[1]) - extra
        this_bottom = float(box[1]) + float(box[3])
        for other in groups:
            if other is grp:
                continue
            other_box = other["bounding"]
            if not _h_overlap(box, other_box):
                continue
            other_bottom = float(other_box[1]) + float(other_box[3])
            other_top = float(other_box[1])
            if other_top < this_bottom and other_bottom > new_y:
                new_y = max(new_y, other_bottom)
        applied = float(box[1]) - new_y
        if applied <= 0:
            continue
        box[1] = new_y


def _estimated_rect(node: dict[str, Any]) -> tuple[float, float, float, float]:
    x, y = node_pos(node)
    width, height = estimated_node_size(node)
    return x, y, x + width, y + height


def _rects_overlap(
    left: tuple[float, float, float, float],
    right: tuple[float, float, float, float],
    pad: float = 0.0,
) -> bool:
    return (
        left[0] - pad < right[2] + pad
        and left[2] + pad > right[0] - pad
        and left[1] - pad < right[3] + pad
        and left[3] + pad > right[1] - pad
    )


def _h_overlap_rect(
    left: tuple[float, float, float, float],
    right: tuple[float, float, float, float],
) -> bool:
    return left[0] < right[2] and left[2] > right[0]


def node_overlap_hits(graph: dict[str, Any], pad: float | None = None) -> list[str]:
    """Pairs of nodes whose estimated Vue AABBs overlap (including ``pad``).

    Default ``pad`` is ``NODE_GAP / 2`` so a clean ``NODE_GAP`` edge gap passes
    and anything tighter is a defect.
    """
    expand = NODE_GAP / 2.0 if pad is None else pad
    nodes = list(graph.get("nodes") or [])
    boxes: list[tuple[object, object, tuple[float, float, float, float]]] = []
    for node in nodes:
        boxes.append((node.get("id"), node.get("type"), _estimated_rect(node)))
    hits: list[str] = []
    for i, left in enumerate(boxes):
        for right in boxes[i + 1 :]:
            if _rects_overlap(left[2], right[2], expand):
                hits.append(f"{left[0]}({left[1]}) vs {right[0]}({right[1]})")
    return hits


def assert_no_overlap(graph: dict[str, Any]) -> None:
    """Raise SystemExit when estimated node AABBs overlap."""
    hits = node_overlap_hits(graph)
    if hits:
        raise SystemExit(f"overlap {hits[0]}")
    group_hits = group_overlap_hits(graph)
    if group_hits:
        raise SystemExit(f"group overlap {group_hits[0]}")


def finalize_layout(graph: dict[str, Any]) -> None:
    """Stage nodes, space AABBs, refit groups, then refuse remaining overlaps.

    Builders call this immediately before writing JSON.
    """
    organize_stages(graph)
    ensure_node_spacing(graph)
    assert_no_overlap(graph)


def _same_column(left_x: float, right_x: float) -> bool:
    return abs(left_x - right_x) < COL_X_TOLERANCE


def _cluster_rows(nodes: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Group nodes whose tops are close, unless they share a column."""
    ordered = sorted(nodes, key=lambda node: (node_pos(node)[1], node_pos(node)[0]))
    rows: list[list[dict[str, Any]]] = []
    for node in ordered:
        x, y = node_pos(node)
        placed = False
        for row in rows:
            anchor_y = min(node_pos(member)[1] for member in row)
            if abs(y - anchor_y) > ROW_Y_TOLERANCE:
                continue
            if any(_same_column(x, node_pos(member)[0]) for member in row):
                continue
            row.append(node)
            placed = True
            break
        if not placed:
            rows.append([node])
    return rows


def _spread_row_x(row: list[dict[str, Any]]) -> bool:
    """Push nodes right so estimated widths in this row do not overlap."""
    moved = False
    ordered = sorted(row, key=lambda node: node_pos(node)[0])
    prev_right = None
    for node in ordered:
        x, y = node_pos(node)
        width, _height = estimated_node_size(node)
        if prev_right is not None and x < prev_right + NODE_GAP:
            x = prev_right + NODE_GAP
            set_node_pos(node, x, y)
            moved = True
        prev_right = x + width
    return moved


def _place_rows(rows: list[list[dict[str, Any]]]) -> bool:
    """Push each row down as a unit so it clears already-placed estimated AABBs."""
    moved = False
    placed: list[tuple[float, float, float, float]] = []
    for row in rows:
        dy = 0.0
        for node in row:
            rect = _estimated_rect(node)
            for prev in placed:
                if not _h_overlap_rect(rect, prev):
                    continue
                need = prev[3] + NODE_GAP - rect[1]
                if need > dy:
                    dy = need
        if dy > _MOVE_EPS:
            for node in row:
                x, y = node_pos(node)
                set_node_pos(node, x, y + dy)
            moved = True
        for node in row:
            placed.append(_estimated_rect(node))
    return moved


def _clearance_moves(
    left: tuple[float, float, float, float],
    right: tuple[float, float, float, float],
) -> tuple[float, float]:
    """Return (dx, dy) to move ``right`` so estimated AABBs keep ``NODE_GAP``."""
    need_x = left[2] + NODE_GAP - right[0]
    need_y = left[3] + NODE_GAP - right[1]
    if need_x <= _MOVE_EPS and need_y <= _MOVE_EPS:
        return 0.0, 0.0
    if need_x <= _MOVE_EPS:
        return 0.0, max(0.0, need_y)
    if need_y <= _MOVE_EPS:
        return max(0.0, need_x), 0.0
    if need_x <= need_y:
        return need_x, 0.0
    return 0.0, need_y


def _resolve_collisions(nodes: list[dict[str, Any]]) -> bool:
    """Separate remaining padded-AABB hits with the smaller of right vs down."""
    moved = False
    for _ in range(48):
        cycle = False
        ordered = sorted(nodes, key=lambda node: (node_pos(node)[1], node_pos(node)[0]))
        for i, node in enumerate(ordered):
            rect = _estimated_rect(node)
            dx = 0.0
            dy = 0.0
            for prev in ordered[:i]:
                prev_rect = _estimated_rect(prev)
                if not _rects_overlap(prev_rect, rect, NODE_GAP / 2.0):
                    continue
                extra_x, extra_y = _clearance_moves(prev_rect, rect)
                dx = max(dx, extra_x)
                dy = max(dy, extra_y)
            if dx <= _MOVE_EPS and dy <= _MOVE_EPS:
                continue
            if dx > _MOVE_EPS and dy > _MOVE_EPS:
                if dx <= dy:
                    dy = 0.0
                else:
                    dx = 0.0
            x, y = node_pos(node)
            set_node_pos(node, x + dx, y + dy)
            cycle = True
            moved = True
        if not cycle:
            break
    return moved


def _snapshot_group_members(
    graph: dict[str, Any],
) -> list[tuple[dict[str, Any], list[dict[str, Any]]]]:
    by_id = {int(node["id"]): node for node in graph.get("nodes") or []}
    snapped: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
    for grp in graph.get("groups") or []:
        members = group_members(graph, grp)
        live = [by_id[int(node["id"])] for node in members if int(node["id"]) in by_id]
        snapped.append((grp, live))
    return snapped


def _refit_group(grp: dict[str, Any], members: list[dict[str, Any]]) -> bool:
    if not members:
        return False
    xs: list[float] = []
    ys: list[float] = []
    rights: list[float] = []
    bottoms: list[float] = []
    for node in members:
        x, y = node_pos(node)
        width, height = estimated_node_size(node)
        xs.append(x)
        ys.append(y)
        rights.append(x + width)
        bottoms.append(y + height)
    new_x = min(xs) - GROUP_BOX_PAD
    new_y = min(ys) - GROUP_TITLE_INSET
    new_r = max(rights) + GROUP_BOX_PAD
    new_b = max(bottoms) + GROUP_BOX_PAD
    box = grp.setdefault("bounding", [new_x, new_y, new_r - new_x, new_b - new_y])
    new_box = [new_x, new_y, new_r - new_x, new_b - new_y]
    changed = False
    for i, value in enumerate(new_box):
        if abs(float(box[i]) - value) > _MOVE_EPS:
            changed = True
        box[i] = _coord(value)
    return changed


def _separate_overlapping_groups(
    membership: list[tuple[dict[str, Any], list[dict[str, Any]]]],
) -> bool:
    moved = False
    ordered = sorted(membership, key=lambda item: float(item[0]["bounding"][1]))
    for i, (lower_grp, lower_members) in enumerate(ordered):
        lower_box = lower_grp["bounding"]
        for upper_grp, _upper_members in ordered[:i]:
            upper_box = upper_grp["bounding"]
            if _overlap_area(upper_box, lower_box) <= _GROUP_OVERLAP_EPS:
                continue
            if not _h_overlap(upper_box, lower_box):
                continue
            upper_bottom = float(upper_box[1]) + float(upper_box[3])
            dy = upper_bottom - float(lower_box[1])
            if dy <= _MOVE_EPS:
                continue
            for node in lower_members:
                x, y = node_pos(node)
                set_node_pos(node, x, y + dy)
            moved = True
            _refit_group(lower_grp, lower_members)
    return moved


def _space_one_graph(graph: dict[str, Any]) -> bool:
    nodes = list(graph.get("nodes") or [])
    if not nodes:
        return False
    membership = _snapshot_group_members(graph)
    moved = False
    rows = _cluster_rows(nodes)
    for row in rows:
        if _spread_row_x(row):
            moved = True
    if _place_rows(rows):
        moved = True
    if _resolve_collisions(nodes):
        moved = True
    for grp, members in membership:
        if _refit_group(grp, members):
            moved = True
    ensure_group_title_inset(graph)
    if _separate_overlapping_groups(membership):
        moved = True
        for grp, members in membership:
            _refit_group(grp, members)
        ensure_group_title_inset(graph)
    return moved


def ensure_node_spacing(graph: dict[str, Any]) -> bool:
    """Push nodes down/right so estimated Vue AABBs keep ``NODE_GAP``.

    Preserves left-to-right row order. Does not rewrite ``size``. Recurses into
    ``definitions.subgraphs``. Idempotent once gaps are clean.

    Arguments:
        graph: Serialized Comfy graph (mutated).
    Returns:
        True when any node ``pos`` or group ``bounding`` changed.
    """
    moved = False
    for _ in range(8):
        cycle = _space_one_graph(graph)
        defs = graph.get("definitions")
        if isinstance(defs, dict):
            for sub in defs.get("subgraphs") or []:
                if isinstance(sub, dict) and sub.get("nodes"):
                    if _space_one_graph(sub):
                        cycle = True
        if not cycle:
            break
        moved = True
    else:
        moved = True
    if moved:
        graph["revision"] = int(graph.get("revision") or 0) + 1
    return moved


def operator_note(graph: dict[str, Any]) -> dict[str, Any] | None:
    """Return the on-canvas operator note when present.

    Prefers a node whose title starts with ``Operator``, else the first
    ``Note`` / ``MarkdownNote``.

    Args:
        graph: Serialized Comfy graph.

    Returns:
        Node dict or None.
    """
    notes = [
        node
        for node in graph.get("nodes") or []
        if str(node.get("type") or "") in NOTE_TYPES
    ]
    if not notes:
        return None
    titled = [
        node
        for node in notes
        if str(node.get("title") or "").startswith("Operator")
    ]
    return titled[0] if titled else notes[0]


def has_named_stages(graph: dict[str, Any]) -> bool:
    """True when any group title is not a generic MODEL/PROMPT/… stage.

    Args:
        graph: Serialized Comfy graph.

    Returns:
        True when SHOT/Beat/RACK-style groups should be preserved.
    """
    for grp in graph.get("groups") or []:
        title = str(grp.get("title") or "").strip()
        if title and title not in GENERIC_GROUP_TITLES:
            return True
    return False


def stage_for_type(ntype: str) -> str:
    """Return the default stage title for a Comfy node type.

    Args:
        ntype: Serialized ``node.type``.

    Returns:
        One of NOTE, QUALITY, MODEL, INPUT, PROMPT, SETTINGS, OUTPUT.
    """
    if ntype in NOTE_TYPES:
        return "NOTE"
    if ntype in {QUALITY_TYPE, CHECK_TYPE}:
        return "QUALITY"
    if ntype in _MODEL_TYPES or ntype.endswith("Loader"):
        return "MODEL"
    if ntype in _INPUT_TYPES:
        return "INPUT"
    if ntype in _PROMPT_TYPES or ntype.endswith("PromptEnhance"):
        return "PROMPT"
    if ntype in _SETTINGS_TYPES:
        return "SETTINGS"
    if ntype in _OUTPUT_TYPES or ntype.startswith("Save"):
        return "OUTPUT"
    return "SETTINGS"


def topo_rank(graph: dict[str, Any]) -> dict[int, int]:
    """Return topological rank from serialized links (sources are rank 0).

    Args:
        graph: Serialized Comfy graph.

    Returns:
        Map of node id to rank. Isolated nodes are rank 0.
    """
    nodes = {
        int(node["id"]): node
        for node in graph.get("nodes") or []
        if node.get("id") is not None
    }
    incoming: dict[int, set[int]] = {nid: set() for nid in nodes}
    outgoing: dict[int, set[int]] = {nid: set() for nid in nodes}
    for link in graph.get("links") or []:
        if isinstance(link, dict):
            src = int(link.get("origin_id") or link.get("from") or 0)
            dst = int(link.get("target_id") or link.get("to") or 0)
        elif isinstance(link, (list, tuple)) and len(link) >= 4:
            src = int(link[1])
            dst = int(link[3])
        else:
            continue
        if src in nodes and dst in nodes:
            outgoing[src].add(dst)
            incoming[dst].add(src)
    rank: dict[int, int] = {nid: 0 for nid in nodes}
    ready: deque[int] = deque(nid for nid, preds in incoming.items() if not preds)
    seen: set[int] = set()
    while ready:
        nid = ready.popleft()
        if nid in seen:
            continue
        seen.add(nid)
        for dest in outgoing[nid]:
            rank[dest] = max(rank[dest], rank[nid] + 1)
            incoming[dest].discard(nid)
            if not incoming[dest] and dest not in seen:
                ready.append(dest)
    return rank


def _header_ids(graph: dict[str, Any]) -> set[int]:
    ids: set[int] = set()
    note = operator_note(graph)
    if note is not None:
        ids.add(int(note["id"]))
    for node in graph.get("nodes") or []:
        if node.get("type") in {QUALITY_TYPE, CHECK_TYPE}:
            ids.add(int(node["id"]))
    return ids


def _place_header(graph: dict[str, Any]) -> tuple[float, float]:
    """Park the operator note at origin and Check/Quality to its right.

    Returns:
        Pipeline origin ``(x, y)`` left-aligned with the note, below the header.
    """
    origin_x = float(LAB_X0)
    origin_y = float(LAB_NODE_Y0)
    note = operator_note(graph)
    check = next(
        (node for node in graph.get("nodes") or [] if node.get("type") == CHECK_TYPE),
        None,
    )
    quality = next(
        (node for node in graph.get("nodes") or [] if node.get("type") == QUALITY_TYPE),
        None,
    )
    cursor_x = origin_x
    header_bottom = origin_y
    if note is not None:
        set_node_pos(note, origin_x, origin_y)
        width, height = estimated_node_size(note)
        header_bottom = origin_y + height
        cursor_x = origin_x + width + NODE_GAP
    if check is not None:
        set_node_pos(check, cursor_x, origin_y)
        width, height = estimated_node_size(check)
        header_bottom = max(header_bottom, origin_y + height)
        cursor_x += width + NODE_GAP
    if quality is not None:
        set_node_pos(quality, cursor_x, origin_y)
        _width, height = estimated_node_size(quality)
        header_bottom = max(header_bottom, origin_y + height)
    pipeline_y = header_bottom + GROUP_BOX_PAD + GROUP_TITLE_INSET + NODE_GAP
    return origin_x, pipeline_y


def _sort_stage_nodes(
    nodes: list[dict[str, Any]], ranks: dict[int, int]
) -> list[dict[str, Any]]:
    return sorted(
        nodes,
        key=lambda node: (
            ranks.get(int(node["id"]), 0),
            node_pos(node)[1],
            node_pos(node)[0],
            int(node["id"]),
        ),
    )


def _stack_column(
    nodes: list[dict[str, Any]],
    x: float,
    y0: float,
    ranks: dict[int, int],
) -> float:
    """Place ``nodes`` top-to-bottom at ``x``. Returns column width."""
    y = y0
    max_width = 0.0
    for node in _sort_stage_nodes(nodes, ranks):
        set_node_pos(node, x, y)
        width, height = estimated_node_size(node)
        y += height + NODE_GAP
        if width > max_width:
            max_width = width
    return max_width


def _restage_columns(
    graph: dict[str, Any],
    header_ids: set[int],
    origin_x: float,
    pipeline_y: float,
) -> dict[str, list[dict[str, Any]]]:
    """Lay remaining nodes into MODEL…OUTPUT columns. Returns stage members."""
    ranks = topo_rank(graph)
    buckets: dict[str, list[dict[str, Any]]] = {stage: [] for stage in STAGE_ORDER}
    extras: list[dict[str, Any]] = []
    for node in graph.get("nodes") or []:
        nid = int(node["id"])
        if nid in header_ids:
            continue
        stage = stage_for_type(str(node.get("type") or ""))
        if stage in HEADER_STAGES:
            extras.append(node)
            continue
        buckets.setdefault(stage, []).append(node)
    x = origin_x
    members: dict[str, list[dict[str, Any]]] = {}
    for stage in STAGE_ORDER:
        column = buckets.get(stage) or []
        if not column:
            continue
        width = _stack_column(column, x, pipeline_y, ranks)
        members[stage] = list(column)
        x += width + NODE_GAP
    if extras:
        _stack_column(extras, origin_x, pipeline_y, ranks)
        members["NOTE_EXTRA"] = extras
    return members


def _reanchor_pipeline(
    graph: dict[str, Any],
    header_ids: set[int],
    origin_x: float,
    pipeline_y: float,
) -> None:
    """Rigid-translate remaining nodes so the pipeline starts below the header."""
    remaining = [
        node
        for node in graph.get("nodes") or []
        if int(node["id"]) not in header_ids
    ]
    if not remaining:
        return
    for node in remaining:
        x, y = node_pos(node)
        if x < origin_x:
            set_node_pos(node, origin_x, y)
    xs = [node_pos(node)[0] for node in remaining]
    ys = [node_pos(node)[1] for node in remaining]
    dx = origin_x - min(xs)
    dy = pipeline_y - min(ys)
    if dx < 0:
        dx = 0.0
    if dy < 0:
        dy = 0.0
    if dx <= _MOVE_EPS and dy <= _MOVE_EPS:
        return
    for node in remaining:
        x, y = node_pos(node)
        set_node_pos(node, x + dx, y + dy)


def _append_below(
    anchor: list[dict[str, Any]],
    newcomers: list[dict[str, Any]],
    origin_x: float,
    pipeline_y: float,
    ranks: dict[int, int],
) -> None:
    if anchor:
        x = min(node_pos(node)[0] for node in anchor)
        y = (
            max(
                node_pos(node)[1] + estimated_node_size(node)[1]
                for node in anchor
            )
            + NODE_GAP
        )
    else:
        x = origin_x
        y = pipeline_y
    for node in _sort_stage_nodes(newcomers, ranks):
        set_node_pos(node, x, y)
        y += estimated_node_size(node)[1] + NODE_GAP


def _snapshot_groups(
    graph: dict[str, Any], header_ids: set[int]
) -> list[tuple[str, str, list[dict[str, Any]]]]:
    snapped: list[tuple[str, str, list[dict[str, Any]]]] = []
    for grp in graph.get("groups") or []:
        title = str(grp.get("title") or "").strip()
        if not title or title in {"NOTE", "QUALITY"}:
            continue
        members = [
            node
            for node in group_members(graph, grp)
            if int(node["id"]) not in header_ids
        ]
        if not members:
            continue
        color = str(grp.get("color") or GROUP_COLOR_A)
        snapped.append((title, color, members))
    return snapped


def _fit_members(
    gid: int, title: str, members: list[dict[str, Any]], color: str
) -> dict[str, Any]:
    grp = group(gid, title, 0, 0, 100, 100, color)
    _refit_group(grp, members)
    return grp


def _group_color(index: int) -> str:
    return GROUP_COLOR_A if index % 2 == 0 else GROUP_COLOR_B


def _rebuild_groups(
    graph: dict[str, Any],
    header_ids: set[int],
    snapshot: list[tuple[str, str, list[dict[str, Any]]]],
    restaged: dict[str, list[dict[str, Any]]] | None,
) -> None:
    nodes = list(graph.get("nodes") or [])
    new_groups: list[dict[str, Any]] = []
    gid = 1
    note = operator_note(graph)
    if note is not None:
        new_groups.append(_fit_members(gid, "NOTE", [note], _group_color(0)))
        gid += 1
    quality_nodes = [
        node for node in nodes if node.get("type") in {QUALITY_TYPE, CHECK_TYPE}
    ]
    if quality_nodes:
        new_groups.append(
            _fit_members(gid, "QUALITY", quality_nodes, _group_color(1))
        )
        gid += 1
    used: set[int] = set(header_ids)
    if restaged is not None:
        for stage in STAGE_ORDER:
            members = restaged.get(stage) or []
            if not members:
                continue
            new_groups.append(
                _fit_members(gid, stage, members, _group_color(gid))
            )
            gid += 1
            used.update(int(node["id"]) for node in members)
        graph["groups"] = new_groups
        return
    ranks = topo_rank(graph)
    origin_x = float(LAB_X0)
    preserved_by_title: dict[str, list[dict[str, Any]]] = {}
    for title, color, members in snapshot:
        new_groups.append(_fit_members(gid, title, members, color))
        gid += 1
        used.update(int(node["id"]) for node in members)
        preserved_by_title.setdefault(title, []).extend(members)
    leftovers = [node for node in nodes if int(node["id"]) not in used]
    leftover_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for node in leftovers:
        stage = stage_for_type(str(node.get("type") or ""))
        if stage in HEADER_STAGES:
            continue
        leftover_buckets[stage].append(node)
    pipeline_nodes = [
        node for node in nodes if int(node["id"]) not in header_ids
    ]
    pipeline_y = min(
        (node_pos(node)[1] for node in pipeline_nodes),
        default=float(LAB_NODE_Y0),
    )
    occupied_right = origin_x
    for node in pipeline_nodes:
        right = node_pos(node)[0] + estimated_node_size(node)[0]
        if right > occupied_right:
            occupied_right = right
    for stage in STAGE_ORDER:
        newcomers = leftover_buckets.get(stage) or []
        if not newcomers:
            continue
        if stage in preserved_by_title:
            _append_below(
                preserved_by_title[stage],
                newcomers,
                origin_x,
                pipeline_y,
                ranks,
            )
            preserved_by_title[stage].extend(newcomers)
            continue
        width = _stack_column(
            newcomers, occupied_right + NODE_GAP, pipeline_y, ranks
        )
        occupied_right += NODE_GAP + width
        new_groups.append(
            _fit_members(gid, stage, newcomers, _group_color(gid))
        )
        gid += 1
        preserved_by_title[stage] = list(newcomers)
    # Refit preserved groups after leftover appends.
    by_title = {grp["title"]: grp for grp in new_groups}
    for title, members in preserved_by_title.items():
        grp = by_title.get(title)
        if grp is not None:
            _refit_group(grp, members)
    graph["groups"] = new_groups


def organize_stages(graph: dict[str, Any]) -> None:
    """Place the operator note top-left and stage the rest left-to-right.

    Empty-group graphs get MODEL/INPUT/PROMPT/SETTINGS/OUTPUT columns.
    Graphs that already have groups keep those memberships and shift as
    blocks under the header. Recurses into ``definitions.subgraphs``.

    Args:
        graph: Serialized Comfy graph (mutated).
    """
    nodes = list(graph.get("nodes") or [])
    if nodes:
        header_ids = _header_ids(graph)
        snapshot = _snapshot_groups(graph, header_ids)
        origin_x, pipeline_y = _place_header(graph)
        restaged: dict[str, list[dict[str, Any]]] | None
        if snapshot:
            _reanchor_pipeline(graph, header_ids, origin_x, pipeline_y)
            restaged = None
        else:
            restaged = _restage_columns(graph, header_ids, origin_x, pipeline_y)
        _rebuild_groups(graph, header_ids, snapshot, restaged)
    defs = graph.get("definitions")
    if isinstance(defs, dict):
        for sub in defs.get("subgraphs") or []:
            if isinstance(sub, dict) and sub.get("nodes"):
                organize_stages(sub)


def relayout_lab_graphs(root: Path | None = None) -> int:
    """Run ``finalize_layout`` on every lab JSON. Returns files written."""
    from _lab_paths import ROOT, lab_graph_paths

    written = 0
    for path in lab_graph_paths(root):
        graph = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(graph, dict):
            continue
        before = json.dumps(graph, sort_keys=True)
        try:
            finalize_layout(graph)
        except SystemExit as exc:
            raise SystemExit(f"{path}: {exc}") from exc
        after = json.dumps(graph, sort_keys=True)
        if before == after:
            continue
        path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
        written += 1
    blocks = ROOT / "custom_nodes" / "ez_studio_blocks" / "subgraphs"
    if blocks.is_dir():
        for path in sorted(blocks.glob("*.json")):
            graph = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(graph, dict):
                continue
            before = json.dumps(graph, sort_keys=True)
            try:
                finalize_layout(graph)
            except SystemExit as exc:
                raise SystemExit(f"{path}: {exc}") from exc
            after = json.dumps(graph, sort_keys=True)
            if before == after:
                continue
            path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
            written += 1
    return written


if __name__ == "__main__":
    count = relayout_lab_graphs()
    print(f"relayout wrote {count} graphs")
