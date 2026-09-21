#!/usr/bin/env python3
"""Build motion/av/clip-chain from motion/av/still-to-video-8s.

Not imported by pytest (leading underscore). Run from repo root:

  python3 tests/python/_build_clip_chain.py

Clones the standalone LTX I2V App, drops the full-batch SaveImage
(``ez_ltx_hero_frames``), and expands to four Beat groups that share one
UNET / video VAE / audio VAE / CLIP / EZQuality / EZVideoFormat /
EZImageDescribe. Continuity is EZClipLastFrame IMAGE → next I2V start.
Do not copy Klein identity, EZUnloadModels, ImageFromBatch, or EZFilmConcat.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

from _lab_layout import GROUP_TITLE_INSET, finalize_layout, group as _group
from _lab_paths import LAB_ROOT, apply_lab_identity, lab_json
from _stamp_app_mode import stamp_suite_graph
from _wire_format import FORMAT_BLURB, _link_out, ensure_format_note

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_film.concat import (  # noqa: E402
    CLIP_CAP_DEFAULT_S,
    CLIP_COUNT_MAX,
    CLIP_PREFIX_DEFAULT,
)

REL = "motion/av/clip-chain"
SOURCE_REL = "motion/av/still-to-video-8s"
BEAT_COUNT = 4
BEAT_BASE = 100
BEAT_STRIDE = 40
ID_GATE = 30
ID_SEED = 31
ID_REWRITE = 32
ID_AUDIO = 33
ID_LOGLINE = 34
ID_CONCAT = 40
ID_DISCLOSURE = 41
SHARED_IDS = frozenset({1, 2, 3, 4, 13, 14, 17, 22, 23, 24})
SRC = {
    "pos": 5,
    "neg": 6,
    "i2v": 7,
    "cond": 8,
    "ks": 9,
    "vdec": 10,
    "cat": 15,
    "sep": 16,
    "vhs": 18,
    "enh": 19,
    "adec": 20,
    "neg_enh": 21,
}
OFF = {
    "pos": 0,
    "neg": 1,
    "i2v": 2,
    "cond": 3,
    "ks": 4,
    "vdec": 5,
    "cat": 6,
    "sep": 7,
    "vhs": 8,
    "enh": 9,
    "adec": 10,
    "neg_enh": 11,
    "last": 12,
    "save": 13,
}
BEAT_X = 1480.0
BEAT_Y0 = 80.0
BEAT_DY = 980.0
DURATION_HINT = "8 seconds, 24 fps"
AUDIO_NOTES_DEFAULT = "world SFX matching the start image, no score"
BEAT_PROMPTS = (
    "",
    (
        "The start image holds as the first frame. The camera continues the "
        "slow dolly, then eases into a gentle pan as fabric or foliage keeps "
        "drifting. Light wind and world SFX matching the start image sit under "
        "the action. Keep every object and surface from the start image; do "
        "not redesign. No music and no score."
    ),
    (
        "The start image holds as the first frame. The subject continues the "
        "same action while the camera holds, then drifts a half-step closer. "
        "World SFX stay continuous with the previous beat. Keep every object "
        "and surface from the start image; do not redesign. No music and no "
        "score."
    ),
    (
        "The start image holds as the first frame. Motion settles: the camera "
        "eases to a hold as fabric or foliage slows. World SFX stay under the "
        "action and fade slightly. Keep every object and surface from the "
        "start image; do not redesign. No music and no score."
    ),
)
OPERATOR_NOTE = f"""## {REL}

{FORMAT_BLURB}

LTX canvas 1280x704 (width/height must be divisible by 32; 720 and 1080 are invalid).

Four LTX AV beats share one UNET / video VAE / audio VAE / CLIP. Last frame of beat N starts beat N+1. EZClipConcat stitches the four MP4s (hard cut). Primary output: `${{COMFY_OUTPUT_DIR}}/{CLIP_PREFIX_DEFAULT}.mp4` plus per-beat VHS (`ez_clip_b0N_ltx_video`) and last-frame PNG (`ez_clip_b0N_last`). No full-batch SaveImage.

**8 seconds, 24 fps** (193 frames = 1+8n) chain-wide. Duration combo stays 5/8/10/12; mixed per-beat lengths are unsupported. Four × 8 s sequential prints are tens of minutes on GB10 — not a hang. Headroom preflight still applies at `start`.

Occupancy: ltx — stop Wan, podcast, music, other LTX. One GB10 job. Occupancy ltx XOR. `occupancy enter ltx` before Queue. No Klein identity on this canvas.

Duplicate Beat groups on canvas for beats 5–24:

1. Duplicate the last Beat group.
2. Set `VHS_VideoCombine.filename_prefix` to `ez_clip_b05_ltx_video` (then b06…).
3. Set last-frame SaveImage prefix to `ez_clip_b05_last`.
4. Wire previous `EZClipLastFrame.last_frame` → new `LTXVImgToVideo.image`.
5. Wire new `VHS_VideoCombine.Filenames` → the next free `EZClipConcat.clip_0N` (`clip_05` for the fifth beat).
6. Keep the shared UNET / VAE / CLIP / Format / Seed / Rewrite / Audio notes wires (do not duplicate loaders).
7. Save under `_user/` if you want a personal App; shipped `_lab` stays 4 beats.

Past 24 stems: host `./scripts/utilities/concat-shots.sh --files a.mp4,b.mp4 --cap-seconds <sum> --yes` (default `--files` cap is 90 s).

LTX-2.5 distilled AV. LTX Community License — not Apache. $10M company-revenue cap. Disclose AI-generated media; do not strip provenance; do not distill.

Prompt enhance is on by default (on-box Qwen3-4B-Instruct-2507). After Queue, the Enhance node shows the prompt CLIP used (or a passthrough reason). Turn Enhance off to use the widget text as-is. Optional style dropdown is hidden on I2V.

LoadImage default example.png; after a still set ez_still_hero_*.png. Match input Format. MagCache off.
"""


def _by_id(graph: dict[str, Any]) -> dict[int, dict[str, Any]]:
    """Index nodes by integer id."""
    return {int(node["id"]): node for node in graph.get("nodes") or []}


def _beat_id(index: int, key: str) -> int:
    """Return the node id for beat ``index`` (0-based) slot ``key``."""
    return BEAT_BASE + index * BEAT_STRIDE + OFF[key]


def _clone_node(
    src: dict[str, Any],
    nid: int,
    pos: list[float],
    title: str | None = None,
) -> dict[str, Any]:
    """Deep-copy a node, assign a new id, and clear links.

    Args:
        src: Template node.
        nid: New node id.
        pos: Canvas position.
        title: Optional replacement title.

    Returns:
        Detached node dict.
    """
    node = copy.deepcopy(src)
    node["id"] = nid
    node["order"] = nid
    node["pos"] = [float(pos[0]), float(pos[1])]
    node["mode"] = 0
    if title is not None:
        node["title"] = title
    for inp in node.get("inputs") or []:
        if inp.get("link") is not None:
            inp["link"] = None
    for out in node.get("outputs") or []:
        out["links"] = []
    return node


def _mk(
    nid: int,
    ntype: str,
    pos: list[float],
    size: list[float],
    title: str,
    widgets: list[Any] | dict[str, Any],
    inputs: list[dict[str, Any]],
    outputs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Serialize one Comfy node."""
    return {
        "id": nid,
        "type": ntype,
        "pos": pos,
        "size": size,
        "flags": {},
        "order": nid,
        "mode": 0,
        "inputs": inputs,
        "outputs": outputs,
        "properties": {"Node name for S&R": ntype},
        "widgets_values": widgets,
        "title": title,
    }


def _primitive(
    nid: int,
    pos: list[float],
    size: list[float],
    out_type: str,
    title: str,
    value: Any,
) -> dict[str, Any]:
    """Build a PrimitiveNode (INT / BOOLEAN / STRING)."""
    return _mk(
        nid,
        "PrimitiveNode",
        pos,
        size,
        title,
        [value, "fixed"],
        [],
        [
            {
                "name": out_type,
                "type": out_type,
                "links": [],
                "widget": {"name": "value"},
                "slot_index": 0,
            }
        ],
    )


def _reset_io(graph: dict[str, Any]) -> None:
    """Drop every link and clear sockets on remaining nodes."""
    for node in graph.get("nodes") or []:
        for inp in node.get("inputs") or []:
            if inp.get("link") is not None:
                inp["link"] = None
        for out in node.get("outputs") or []:
            out["links"] = []
    graph["links"] = []
    graph["last_link_id"] = 0


def _strip_printers(graph: dict[str, Any]) -> None:
    """Keep shared loaders / Format / Describe / Note. Drop the 8 s printer."""
    graph["nodes"] = [
        node for node in graph.get("nodes") or [] if int(node["id"]) in SHARED_IDS
    ]
    _reset_io(graph)


def _make_last_frame(nid: int, pos: list[float], beat: int) -> dict[str, Any]:
    """EZClipLastFrame for one beat."""
    return _mk(
        nid,
        "EZClipLastFrame",
        pos,
        [280, 60],
        f"Beat {beat} last frame",
        [],
        [{"name": "image", "type": "IMAGE", "link": None}],
        [
            {
                "name": "last_frame",
                "type": "IMAGE",
                "links": [],
                "slot_index": 0,
            }
        ],
    )


def _make_last_save(nid: int, pos: list[float], beat: int) -> dict[str, Any]:
    """Last-frame SaveImage (one PNG, prefix ends with ``_last``)."""
    return _mk(
        nid,
        "SaveImage",
        pos,
        [280, 270],
        f"Save beat {beat} last frame",
        [f"ez_clip_b{beat:02d}_last"],
        [{"name": "images", "type": "IMAGE", "link": None}],
        [],
    )


def _make_concat(nid: int, pos: list[float]) -> dict[str, Any]:
    """EZClipConcat with clip_01–24 sockets (four wired by the builder)."""
    inputs: list[dict[str, Any]] = [
        {"name": f"clip_{index:02d}", "type": "VHS_FILENAMES", "link": None}
        for index in range(1, CLIP_COUNT_MAX + 1)
    ]
    inputs.append(
        {
            "name": "disclosure",
            "type": "STRING",
            "link": None,
            "widget": {"name": "disclosure"},
        }
    )
    return _mk(
        nid,
        "EZClipConcat",
        pos,
        [420, 280],
        "Save clip chain (MP4) — play / download",
        [CLIP_PREFIX_DEFAULT, CLIP_CAP_DEFAULT_S, 0],
        inputs,
        [{"name": "path", "type": "STRING", "links": [], "slot_index": 0}],
    )


def _instantiate_beat(
    graph: dict[str, Any],
    templates: dict[str, dict[str, Any]],
    index: int,
) -> dict[str, dict[str, Any]]:
    """Clone one Beat group from the 8 s printer templates.

    Args:
        graph: Graph being built (nodes appended).
        templates: Source printer nodes keyed like ``SRC``.
        index: 0-based beat index.

    Returns:
        Slot name → new node.
    """
    beat_n = index + 1
    ox = BEAT_X
    oy = BEAT_Y0 + index * BEAT_DY
    nodes: dict[str, dict[str, Any]] = {}
    enh = _clone_node(
        templates["enh"],
        _beat_id(index, "enh"),
        [ox, oy],
        f"Beat {beat_n}",
    )
    values = list(enh.get("widgets_values") or [])
    while len(values) < 8:
        values.append("")
    if index > 0:
        values[1] = BEAT_PROMPTS[index]
    values[0] = "custom"
    values[2] = True
    values[3] = "i2v"
    values[4] = DURATION_HINT
    values[5] = AUDIO_NOTES_DEFAULT
    values[6] = "none"
    values[7] = REL
    enh["widgets_values"] = values
    if index > 0:
        enh["inputs"] = [
            item
            for item in (enh.get("inputs") or [])
            if item.get("name") != "image_desc"
        ]
    nodes["enh"] = enh
    pos = _clone_node(
        templates["pos"],
        _beat_id(index, "pos"),
        [ox + 460, oy],
        f"Beat {beat_n} prompt",
    )
    pos["widgets_values"] = [values[1]]
    nodes["pos"] = pos
    nodes["neg_enh"] = _clone_node(
        templates["neg_enh"],
        _beat_id(index, "neg_enh"),
        [ox, oy + 420],
        f"Beat {beat_n} negative enhance",
    )
    nodes["neg"] = _clone_node(
        templates["neg"],
        _beat_id(index, "neg"),
        [ox + 460, oy + 420],
        f"Beat {beat_n} negative",
    )
    nodes["i2v"] = _clone_node(
        templates["i2v"],
        _beat_id(index, "i2v"),
        [ox + 920, oy],
    )
    nodes["i2v"]["widgets_values"] = [1280, 704, 193, 1]
    nodes["cond"] = _clone_node(
        templates["cond"],
        _beat_id(index, "cond"),
        [ox + 920, oy + 240],
    )
    nodes["cat"] = _clone_node(
        templates["cat"],
        _beat_id(index, "cat"),
        [ox + 920, oy + 360],
    )
    nodes["ks"] = _clone_node(
        templates["ks"],
        _beat_id(index, "ks"),
        [ox + 1280, oy],
        f"Beat {beat_n} KSampler",
    )
    nodes["sep"] = _clone_node(
        templates["sep"],
        _beat_id(index, "sep"),
        [ox + 1280, oy + 300],
    )
    nodes["vdec"] = _clone_node(
        templates["vdec"],
        _beat_id(index, "vdec"),
        [ox + 1640, oy],
    )
    nodes["adec"] = _clone_node(
        templates["adec"],
        _beat_id(index, "adec"),
        [ox + 1640, oy + 80],
    )
    vhs = _clone_node(
        templates["vhs"],
        _beat_id(index, "vhs"),
        [ox + 1960, oy],
        f"Beat {beat_n} video (MP4) — open node for preview",
    )
    widgets = vhs.get("widgets_values")
    if isinstance(widgets, dict):
        widgets = dict(widgets)
        widgets["filename_prefix"] = f"ez_clip_b{beat_n:02d}_ltx_video"
        widgets["save_output"] = True
        vhs["widgets_values"] = widgets
    nodes["vhs"] = vhs
    nodes["last"] = _make_last_frame(
        _beat_id(index, "last"), [ox + 1640, oy + 200], beat_n
    )
    nodes["save"] = _make_last_save(
        _beat_id(index, "save"), [ox + 1960, oy + 460], beat_n
    )
    graph.setdefault("nodes", []).extend(nodes.values())
    return nodes


def _wire_shared(graph: dict[str, Any], shared: dict[str, dict[str, Any]]) -> None:
    """Wire occupancy, describe, empty audio, and concat disclosure."""
    _link_out(
        graph, shared["load"], 0, shared["gate"], "image", "IMAGE", widget=False
    )
    _link_out(
        graph,
        shared["gate"],
        0,
        shared["describe"],
        "image",
        "IMAGE",
        widget=False,
    )
    _link_out(
        graph,
        shared["audio_vae"],
        0,
        shared["empty"],
        "audio_vae",
        "VAE",
        widget=False,
    )
    _link_out(
        graph,
        shared["disclosure"],
        0,
        shared["concat"],
        "disclosure",
        "STRING",
        widget=True,
    )


def _wire_beat(
    graph: dict[str, Any],
    shared: dict[str, dict[str, Any]],
    beat: dict[str, dict[str, Any]],
    prev_last: dict[str, Any] | None,
    index: int,
) -> dict[str, Any]:
    """Wire one beat onto shared loaders and the previous last frame.

    Args:
        graph: Graph (mutated).
        shared: Shared loader / primitive / concat nodes.
        beat: This beat's nodes.
        prev_last: Previous ``EZClipLastFrame``, or None for beat 1.
        index: 0-based beat index.

    Returns:
        This beat's last-frame node (for the next I2V start).
    """
    _link_out(graph, shared["clip"], 0, beat["pos"], "clip", "CLIP", widget=False)
    _link_out(graph, shared["clip"], 0, beat["neg"], "clip", "CLIP", widget=False)
    _link_out(graph, beat["enh"], 0, beat["pos"], "text", "STRING", widget=True)
    _link_out(
        graph, beat["enh"], 0, beat["neg_enh"], "positive", "STRING", widget=False
    )
    _link_out(graph, beat["neg_enh"], 0, beat["neg"], "text", "STRING", widget=True)
    _link_out(
        graph, beat["pos"], 0, beat["i2v"], "positive", "CONDITIONING", widget=False
    )
    _link_out(
        graph, beat["neg"], 0, beat["i2v"], "negative", "CONDITIONING", widget=False
    )
    _link_out(
        graph, shared["video_vae"], 0, beat["i2v"], "vae", "VAE", widget=False
    )
    if prev_last is None:
        _link_out(
            graph, shared["gate"], 0, beat["i2v"], "image", "IMAGE", widget=False
        )
    else:
        _link_out(graph, prev_last, 0, beat["i2v"], "image", "IMAGE", widget=False)
    _link_out(graph, shared["fmt"], 0, beat["i2v"], "width", "INT", widget=True)
    _link_out(graph, shared["fmt"], 1, beat["i2v"], "height", "INT", widget=True)
    _link_out(
        graph, beat["i2v"], 0, beat["cond"], "positive", "CONDITIONING", widget=False
    )
    _link_out(
        graph, beat["i2v"], 1, beat["cond"], "negative", "CONDITIONING", widget=False
    )
    _link_out(
        graph, beat["i2v"], 2, beat["cat"], "video_latent", "LATENT", widget=False
    )
    _link_out(
        graph, shared["empty"], 0, beat["cat"], "audio_latent", "LATENT", widget=False
    )
    _link_out(graph, shared["unet"], 0, beat["ks"], "model", "MODEL", widget=False)
    _link_out(
        graph, beat["cond"], 0, beat["ks"], "positive", "CONDITIONING", widget=False
    )
    _link_out(
        graph, beat["cond"], 1, beat["ks"], "negative", "CONDITIONING", widget=False
    )
    _link_out(
        graph, beat["cat"], 0, beat["ks"], "latent_image", "LATENT", widget=False
    )
    _link_out(graph, shared["seed"], 0, beat["ks"], "seed", "INT", widget=True)
    _link_out(
        graph, beat["ks"], 0, beat["sep"], "av_latent", "LATENT", widget=False
    )
    _link_out(
        graph, beat["sep"], 0, beat["vdec"], "samples", "LATENT", widget=False
    )
    _link_out(
        graph, shared["video_vae"], 0, beat["vdec"], "vae", "VAE", widget=False
    )
    _link_out(
        graph, beat["sep"], 1, beat["adec"], "samples", "LATENT", widget=False
    )
    _link_out(
        graph, shared["audio_vae"], 0, beat["adec"], "audio_vae", "VAE", widget=False
    )
    _link_out(graph, beat["vdec"], 0, beat["vhs"], "images", "IMAGE", widget=False)
    _link_out(graph, beat["adec"], 0, beat["vhs"], "audio", "AUDIO", widget=False)
    _link_out(graph, beat["vdec"], 0, beat["last"], "image", "IMAGE", widget=False)
    _link_out(graph, beat["last"], 0, beat["save"], "images", "IMAGE", widget=False)
    _link_out(
        graph,
        beat["vhs"],
        0,
        shared["concat"],
        f"clip_{index + 1:02d}",
        "VHS_FILENAMES",
        widget=False,
    )
    _link_out(
        graph, shared["fmt"], 2, beat["enh"], "duration_hint", "STRING", widget=True
    )
    _link_out(
        graph, shared["rewrite"], 0, beat["enh"], "enhance", "BOOLEAN", widget=True
    )
    _link_out(
        graph, shared["audio"], 0, beat["enh"], "audio_notes", "STRING", widget=True
    )
    _link_out(
        graph, shared["logline"], 0, beat["enh"], "context", "STRING", widget=False
    )
    if index == 0:
        _link_out(
            graph,
            shared["describe"],
            0,
            beat["enh"],
            "image_desc",
            "STRING",
            widget=False,
        )
    return beat["last"]


def _fit_group(
    gid: int,
    title: str,
    members: list[dict[str, Any]],
    color: str,
) -> dict[str, Any]:
    """Build a group box from member positions."""
    xs: list[float] = []
    ys: list[float] = []
    rights: list[float] = []
    bottoms: list[float] = []
    for node in members:
        pos = node.get("pos") or [0, 0]
        size = node.get("size") or [200, 100]
        x, y = float(pos[0]), float(pos[1])
        w = float(size[0] if not isinstance(size, dict) else size.get("0", 200))
        h = float(size[1] if not isinstance(size, dict) else size.get("1", 100))
        xs.append(x)
        ys.append(y)
        rights.append(x + w)
        bottoms.append(y + h)
    pad = 20.0
    gx = min(xs) - pad
    gy = min(ys) - GROUP_TITLE_INSET
    return _group(
        gid,
        title,
        gx,
        gy,
        max(rights) + pad - gx,
        max(bottoms) + pad - gy,
        color,
    )


def _place_groups(
    shared: dict[str, dict[str, Any]],
    beats: list[dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Return LiteGraph groups for models, start, four beats, and publish."""
    models = [
        shared["unet"],
        shared["video_vae"],
        shared["clip"],
        shared["audio_vae"],
        shared["empty"],
    ]
    start = [
        shared["load"],
        shared["gate"],
        shared["describe"],
        shared["fmt"],
        shared["seed"],
        shared["rewrite"],
        shared["audio"],
        shared["logline"],
    ]
    groups = [
        _fit_group(1, "1. LTX models", models, "#a1309b"),
        _fit_group(2, "2. Start / occupancy / format", start, "#3f789e"),
    ]
    colors = ("#3f789e", "#a1309b")
    for index, beat in enumerate(beats):
        groups.append(
            _fit_group(
                3 + index,
                f"{3 + index}. Beat {index + 1} (8.00s LTX)",
                list(beat.values()),
                colors[index % 2],
            )
        )
    groups.append(
        _fit_group(
            7,
            "7. Publish clip chain",
            [shared["concat"], shared["disclosure"]],
            "#3f789e",
        )
    )
    return groups


def _sync_ids(graph: dict[str, Any]) -> None:
    """Stamp last_node_id / last_link_id from live nodes and links."""
    graph["last_node_id"] = max(int(node["id"]) for node in graph["nodes"])
    last_link = 0
    for link in graph.get("links") or []:
        if isinstance(link, list) and link:
            last_link = max(last_link, int(link[0]))
    graph["last_link_id"] = last_link


def build_clip_chain() -> dict[str, Any]:
    """Deep-copy still-to-video-8s and expand to four last-frame beats.

    Returns:
        Serialized lab graph (not yet written).
    """
    source = json.loads(lab_json(SOURCE_REL).read_text(encoding="utf-8"))
    graph = copy.deepcopy(source)
    src_nodes = _by_id(graph)
    templates = {key: src_nodes[nid] for key, nid in SRC.items()}
    _strip_printers(graph)
    live = _by_id(graph)
    load = live[4]
    load["title"] = "Start image"
    note = live[17]
    note["widgets_values"] = [OPERATOR_NOTE]
    note["title"] = "Operator note — clip chain"
    note["size"] = [960, 520]
    fmt = live[23]
    fmt["widgets_values"] = [
        "LTX-2.5",
        fmt["widgets_values"][1],
        1280,
        704,
        "Match input",
        "8 seconds",
    ]
    empty = live[14]
    empty["widgets_values"] = [193, 24.0, 1]
    empty["pos"] = [40.0, 620.0]
    fmt["pos"] = [620.0, 1200.0]
    load["pos"] = [620.0, 80.0]
    live[24]["pos"] = [620.0, 430.0]
    live[1]["pos"] = [40.0, 80.0]
    live[2]["pos"] = [40.0, 200.0]
    live[3]["pos"] = [40.0, 320.0]
    live[13]["pos"] = [40.0, 500.0]
    live[22]["pos"] = [40.0, -120.0]
    note["pos"] = [40.0, 4480.0]

    gate = _mk(
        ID_GATE,
        "EZDCCOccupancyGate",
        [980.0, 80.0],
        [280, 90],
        "Occupancy gate (ltx)",
        ["ltx"],
        [{"name": "image", "type": "IMAGE", "link": None}],
        [{"name": "image", "type": "IMAGE", "links": [], "slot_index": 0}],
    )
    seed = _primitive(ID_SEED, [620.0, 560.0], [320, 82], "INT", "Seed", 42)
    rewrite = _primitive(
        ID_REWRITE, [620.0, 680.0], [320, 82], "BOOLEAN", "Rewrite prompt", True
    )
    audio = _primitive(
        ID_AUDIO,
        [620.0, 800.0],
        [420, 160],
        "STRING",
        "Audio notes",
        AUDIO_NOTES_DEFAULT,
    )
    logline = _primitive(
        ID_LOGLINE, [620.0, 1000.0], [420, 160], "STRING", "Logline / context", ""
    )
    concat = _make_concat(ID_CONCAT, [40.0, 4100.0])
    disclosure = _mk(
        ID_DISCLOSURE,
        "EZFilmDisclosure",
        [500.0, 4100.0],
        [420, 120],
        "LTX AI-media disclosure (end-card)",
        [""],
        [],
        [{"name": "text", "type": "STRING", "links": [], "slot_index": 0}],
    )
    graph["nodes"].extend([gate, seed, rewrite, audio, logline, concat, disclosure])

    shared = {
        "unet": live[1],
        "video_vae": live[2],
        "clip": live[3],
        "load": load,
        "audio_vae": live[13],
        "empty": empty,
        "note": note,
        "quality": live[22],
        "fmt": fmt,
        "describe": live[24],
        "gate": gate,
        "seed": seed,
        "rewrite": rewrite,
        "audio": audio,
        "logline": logline,
        "concat": concat,
        "disclosure": disclosure,
    }
    beats = [
        _instantiate_beat(graph, templates, index) for index in range(BEAT_COUNT)
    ]
    extra = graph.setdefault("extra", {})
    extra["lab_profile"] = REL
    extra["lab_description"] = (
        "Four LTX AV beats with last-frame continuity, 8.00 s / 193 each"
    )
    extra["lab_note"] = OPERATOR_NOTE
    extra["lab_ltx_av"] = True
    extra["lab_rel"] = REL
    apply_lab_identity(graph, REL)
    _wire_shared(graph, shared)
    prev_last: dict[str, Any] | None = None
    for index, beat in enumerate(beats):
        prev_last = _wire_beat(graph, shared, beat, prev_last, index)
    graph["groups"] = _place_groups(shared, beats)
    graph["id"] = "clip-chain"
    graph["revision"] = 1
    graph["version"] = 0.4
    _sync_ids(graph)
    ensure_format_note(graph)
    stamp_suite_graph(graph)
    finalize_layout(graph)
    _sync_ids(graph)
    return graph


def main() -> None:
    """Build and write the clip-chain lab graph."""
    graph = build_clip_chain()
    path = LAB_ROOT / "motion" / "av" / "clip-chain.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
