#!/usr/bin/env python3
"""Build the ``film`` lane lab graph the ez_edit agent queues for cutaways.

A reduced Wan 2.2 TI2V-5B silent text-to-video chain (same weights and node
chain as ``video/silent/text-to-video-5s``) sized for one generated cutaway
clip. The graph ships twice: the promoted lab graph under
``workflows/_lab/film/`` and a byte-identical package copy under
``custom_nodes/ez_edit/graphs/`` that the editing agent queues by path.

Run from repo root:
  python3 tests/python/_build_editing_workflows.py
"""

from __future__ import annotations

import json
from typing import Any

from _lab_layout import finalize_layout
from _lab_paths import ROOT, apply_lab_identity, lab_dest
from _stamp_app_mode import (
    apply_lab_completeness_flags,
    ensure_occupancy_note,
    stamp_app_mode,
)
from _wire_prompt_enhance import (
    apply_enhance_policy,
    insert_negative_enhance,
    normalize_enhance_widgets,
    wire_enhance,
)

LAB_REL = "film/generate-cutaway"
PACKAGE_SUBPATH = "custom_nodes/ez_edit/graphs/generate-cutaway.json"

WAN_UNET = "wan2.2_ti2v_5B_fp16.safetensors"
WAN_CLIP = "umt5_xxl_fp8_e4m3fn_scaled.safetensors"
WAN_VAE = "wan2.2_vae.safetensors"

WIDTH = 832
HEIGHT = 480
FRAMES = 121
FPS = 24
SHIFT = 8
SEED = 42
STEPS = 20
CFG = 5
SAMPLER = "uni_pc"
SCHEDULER = "simple"
PREFIX = "ez_edit_cutaway"
OCCUPANCY_MODE = "wan"
DURATION_HINT = "5 seconds, 24 fps"
PROMPT_TITLE = "Prompt (cutaway)"
NEGATIVE_TITLE = "Negative"
ENHANCE_TITLE = "Wan Prompt Enhance"
NEG_ENHANCE_TITLE = "Negative Prompt Enhance"
LATENT_TITLE = "Video size & length"
SAMPLER_TITLE = "KSampler"
SAVER_TITLE = "Save cutaway (MP4) - open node for preview"

PROMPT = (
    "A clean unmarked product cutaway: a matte graphite desk lamp with a slim "
    "articulated arm and a weighted circular base sits on a bare oak workbench "
    "beside a stack of unmarked hardcover books. Soft north-window daylight from "
    "the left, gentle falloff, shallow depth of field, faint dust motes drifting "
    "in the beam. The lamp head tilts two degrees downward across the shot while "
    "the dust keeps drifting. 40mm-equivalent lens, locked-off camera, 16:9. "
    "Photoreal b-roll. No audio."
)
NEGATIVE = (
    "morphing, identity drift, warping objects, face melting, flicker, jitter, "
    "frame stutter, rubbery motion, melting edges, texture crawl, sudden cuts, "
    "watermark, burned-in text"
)

NOTE = f"""## {LAB_REL}

Silent Wan 2.2 TI2V-5B text-to-video cutaway the **Edit** agent queues when a
timeline needs a generated clip. One GB10 job: the graph refuses to render while
another heavy mode holds occupancy.

Models: ``{WAN_UNET}`` + ``{WAN_CLIP}`` (CLIP type wan) + ``{WAN_VAE}``.
Weights: ``./scripts/manage.sh download-wan --tier 5b``.

Widgets the agent patches (see ``extra.lab_edit.widgets``):
- Prompt: the Wan Prompt Enhance ``prompt`` widget - it owns the Positive CLIP,
  so that is the text UMT5 encodes. Set **Rewrite prompt** off to send it to
  CLIP verbatim; the 4B rewriter is optional here because the agent authors.
- Rewrite negative stays on: it keeps the negative from fighting the positive.
- Video size and length: latent node ``width`` / ``height`` inputs and the frame
  count in its ``widgets_values[2]``.
- FPS: frame rate on the MP4 saver. Duration = length / FPS.
- Seed on the sampler, filename prefix on the saver.

Primary output: MP4 at ``${{COMFY_OUTPUT_DIR}}/{PREFIX}_*.mp4`` (container
``/outputs``). No audio track - the edit timeline owns audio.

The agent queues the package copy at ``{PACKAGE_SUBPATH}``, written byte-identical
to this lab graph. Edit ``tests/python/_build_editing_workflows.py`` and re-run;
never hand-edit either JSON.
"""

def _node(
    nid: int,
    ntype: str,
    *,
    pos: tuple[float, float],
    size: tuple[float, float],
    inputs: list[dict[str, Any]],
    outputs: list[dict[str, Any]],
    widgets: list[Any] | dict[str, Any],
    title: str | None = None,
    order: int = 0,
    core: bool = True,
) -> dict[str, Any]:
    """Serialize one Comfy node.

    Args:
        nid: Node id.
        ntype: Comfy class name.
        pos: Canvas position (``finalize_layout`` restages it).
        size: Serialized node size.
        inputs: Input slot rows.
        outputs: Output slot rows.
        widgets: ``widgets_values`` payload.
        title: Canvas title; defaults to ``ntype``.
        order: Execution hint.
        core: True for comfy-core nodes (adds the ``cnr_id`` property).

    Returns:
        Serialized node dict.
    """
    properties: dict[str, str] = {"Node name for S&R": ntype}
    if core:
        properties["cnr_id"] = "comfy-core"
    node: dict[str, Any] = {
        "id": nid,
        "type": ntype,
        "pos": [pos[0], pos[1]],
        "size": [size[0], size[1]],
        "flags": {},
        "order": order,
        "mode": 0,
        "inputs": inputs,
        "outputs": outputs,
        "properties": properties,
        "widgets_values": widgets,
    }
    if title:
        node["title"] = title
    return node


def _in(
    name: str,
    typ: str,
    link: int | None = None,
    *,
    widget: str | None = None,
    optional: bool = False,
) -> dict[str, Any]:
    """Build one input slot row.

    Args:
        name: Slot name.
        typ: Slot type.
        link: Link id when the slot is wired.
        widget: Widget name when the slot projects a widget.
        optional: True for a Comfy optional slot (``shape`` 7).

    Returns:
        Serialized input row.
    """
    row: dict[str, Any] = {"name": name, "type": typ, "link": link}
    if optional:
        row["shape"] = 7
    if widget is not None:
        row["widget"] = {"name": widget}
    return row


def _out(name: str, typ: str, links: list[int] | None = None) -> dict[str, Any]:
    """Build one output slot row.

    Args:
        name: Slot name.
        typ: Slot type.
        links: Outbound link ids.

    Returns:
        Serialized output row.
    """
    return {"name": name, "type": typ, "links": list(links or []), "slot_index": 0}


def _wiring() -> tuple[list[list[Any]], Any]:
    """Return an empty link list and a ``wire`` helper bound to it.

    Returns:
        ``(links, wire)`` where ``wire(src, src_slot, dst, dst_slot, ltype)``
        appends a link row and records it on both nodes.
    """
    links: list[list[Any]] = []

    def wire(
        src: dict[str, Any],
        src_slot: int,
        dst: dict[str, Any],
        dst_slot: int,
        ltype: str,
    ) -> int:
        link_id = len(links) + 1
        links.append([link_id, int(src["id"]), src_slot, int(dst["id"]), dst_slot, ltype])
        src["outputs"][src_slot]["links"].append(link_id)
        dst["inputs"][dst_slot]["link"] = link_id
        return link_id

    return links, wire


def _widgets_map(by_title: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Return the agent-facing widget map keyed by patch name.

    Args:
        by_title: Node lookup by canvas title.

    Returns:
        Mapping of patch name to ``{"node": id, "widget": name}``.
    """

    def ref(title: str, widget: str) -> dict[str, Any]:
        return {"node": int(by_title[title]["id"]), "widget": widget}

    return {
        "prompt": ref(ENHANCE_TITLE, "prompt"),
        "enhance": ref(ENHANCE_TITLE, "enhance"),
        "negative_prompt": ref(NEG_ENHANCE_TITLE, "prompt"),
        "negative_enhance": ref(NEG_ENHANCE_TITLE, "enhance"),
        "width": ref(LATENT_TITLE, "width"),
        "height": ref(LATENT_TITLE, "height"),
        "length": ref(LATENT_TITLE, "length"),
        "fps": ref(SAVER_TITLE, "frame_rate"),
        "seed": ref(SAMPLER_TITLE, "seed"),
        "filename_prefix": ref(SAVER_TITLE, "filename_prefix"),
    }


def build_generate_cutaway() -> dict[str, Any]:
    """Build the ``film/generate-cutaway`` lab graph.

    Returns:
        Serialized Comfy graph, stamped and laid out.
    """
    links, wire = _wiring()

    note = _node(
        1,
        "Note",
        pos=(40, 80),
        size=(960, 340),
        inputs=[],
        outputs=[],
        widgets=[NOTE],
        title="Operator note",
        order=0,
    )
    unet = _node(
        2,
        "UNETLoader",
        pos=(40, 548),
        size=(360, 82),
        inputs=[],
        outputs=[_out("MODEL", "MODEL")],
        widgets=[WAN_UNET, "default"],
        title="Wan 2.2 TI2V-5B",
        order=1,
    )
    clip = _node(
        3,
        "CLIPLoader",
        pos=(40, 702),
        size=(360, 110),
        inputs=[],
        outputs=[_out("CLIP", "CLIP")],
        widgets=[WAN_CLIP, "wan", "default"],
        title="UMT5 CLIP (wan)",
        order=2,
    )
    vae = _node(
        4,
        "VAELoader",
        pos=(40, 884),
        size=(360, 58),
        inputs=[],
        outputs=[_out("VAE", "VAE")],
        widgets=[WAN_VAE],
        title="Wan 2.2 VAE",
        order=3,
    )
    positive = _node(
        5,
        "CLIPTextEncode",
        pos=(460, 548),
        size=(420, 160),
        inputs=[_in("clip", "CLIP"), _in("text", "STRING", widget="text")],
        outputs=[_out("CONDITIONING", "CONDITIONING")],
        widgets=[PROMPT],
        title=PROMPT_TITLE,
        order=4,
    )
    negative = _node(
        6,
        "CLIPTextEncode",
        pos=(460, 800),
        size=(420, 120),
        inputs=[_in("clip", "CLIP"), _in("text", "STRING", widget="text")],
        outputs=[_out("CONDITIONING", "CONDITIONING")],
        widgets=[NEGATIVE],
        title=NEGATIVE_TITLE,
        order=5,
    )
    latent = _node(
        7,
        "Wan22ImageToVideoLatent",
        pos=(940, 548),
        size=(280, 150),
        inputs=[
            _in("vae", "VAE"),
            _in("start_image", "IMAGE", optional=True),
            _in("width", "INT", widget="width"),
            _in("height", "INT", widget="height"),
        ],
        outputs=[_out("LATENT", "LATENT")],
        widgets=[WIDTH, HEIGHT, FRAMES, 1],
        title=LATENT_TITLE,
        order=6,
    )
    shift = _node(
        8,
        "ModelSamplingSD3",
        pos=(940, 448),
        size=(210, 58),
        inputs=[_in("model", "MODEL")],
        outputs=[_out("MODEL", "MODEL")],
        widgets=[SHIFT],
        title="Shift",
        order=7,
    )
    sampler = _node(
        9,
        "KSampler",
        pos=(1320, 548),
        size=(320, 262),
        inputs=[
            _in("model", "MODEL"),
            _in("positive", "CONDITIONING"),
            _in("negative", "CONDITIONING"),
            _in("latent_image", "LATENT"),
        ],
        outputs=[_out("LATENT", "LATENT")],
        widgets=[SEED, "fixed", STEPS, CFG, SAMPLER, SCHEDULER, 1],
        title=SAMPLER_TITLE,
        order=8,
    )
    decode = _node(
        10,
        "VAEDecode",
        pos=(1740, 548),
        size=(240, 46),
        inputs=[_in("samples", "LATENT"), _in("vae", "VAE")],
        outputs=[_out("IMAGE", "IMAGE")],
        widgets=[],
        title="VAE Decode",
        order=9,
    )
    gate = _node(
        11,
        "EZDCCOccupancyGate",
        pos=(2080, 548),
        size=(280, 90),
        inputs=[_in("image", "IMAGE")],
        outputs=[_out("image", "IMAGE")],
        widgets=[OCCUPANCY_MODE],
        title=f"Occupancy gate ({OCCUPANCY_MODE})",
        order=10,
        core=False,
    )
    saver = _node(
        12,
        "VHS_VideoCombine",
        pos=(2460, 548),
        size=(320, 420),
        inputs=[
            _in("images", "IMAGE"),
            _in("audio", "AUDIO", optional=True),
            _in("meta_batch", "VHS_BatchManager", optional=True),
            _in("vae", "VAE", optional=True),
        ],
        outputs=[_out("Filenames", "VHS_FILENAMES")],
        widgets={
            "frame_rate": FPS,
            "loop_count": 0,
            "filename_prefix": PREFIX,
            "format": "video/h264-mp4",
            "pix_fmt": "yuv420p",
            "crf": 18,
            "save_metadata": True,
            "trim_to_audio": False,
            "pingpong": False,
            "save_output": True,
        },
        title=SAVER_TITLE,
        order=11,
        core=False,
    )

    wire(clip, 0, positive, 0, "CLIP")
    wire(clip, 0, negative, 0, "CLIP")
    wire(unet, 0, shift, 0, "MODEL")
    wire(shift, 0, sampler, 0, "MODEL")
    wire(positive, 0, sampler, 1, "CONDITIONING")
    wire(negative, 0, sampler, 2, "CONDITIONING")
    wire(vae, 0, latent, 0, "VAE")
    wire(latent, 0, sampler, 3, "LATENT")
    wire(sampler, 0, decode, 0, "LATENT")
    wire(vae, 0, decode, 1, "VAE")
    wire(decode, 0, gate, 0, "IMAGE")
    wire(gate, 0, saver, 0, "IMAGE")

    nodes = [
        note,
        unet,
        clip,
        vae,
        positive,
        negative,
        latent,
        shift,
        sampler,
        decode,
        gate,
        saver,
    ]

    graph: dict[str, Any] = {
        "id": LAB_REL,
        "revision": 1,
        "last_node_id": max(int(node["id"]) for node in nodes),
        "last_link_id": max(int(link[0]) for link in links),
        "nodes": nodes,
        "links": links,
        "groups": [],
        "config": {},
        "extra": {
            "lab_note": NOTE,
            "lab_profile": LAB_REL,
            "lab_description": (
                "Wan 2.2 5B silent T2V cutaway for the edit agent, 121 frames @ 24 fps"
            ),
            "lab_edit": {
                "graph": PACKAGE_SUBPATH,
                "occupancy_mode": OCCUPANCY_MODE,
                "prefix": PREFIX,
                "size": [WIDTH, HEIGHT],
                "frames": FRAMES,
                "fps": FPS,
            },
        },
        "version": 0.4,
    }

    # House enhance pair: Wan rewrite owns the Positive CLIP, the negative
    # rewrite reads that final positive (lab invariant, never hand-wire it).
    # The agent therefore patches the enhance node's prompt widget, which is
    # what reaches UMT5; the CLIP widgets below it are frontend mirrors.
    wire_enhance(
        graph,
        positive,
        ntype="EZWanPromptEnhance",
        title=ENHANCE_TITLE,
        widgets=["custom", PROMPT, True, "t2v", DURATION_HINT, "none", LAB_REL],
        size_h=420,
    )
    insert_negative_enhance(graph)
    normalize_enhance_widgets(graph)
    apply_enhance_policy(graph)

    by_title = {str(node.get("title") or node["type"]): node for node in graph["nodes"]}
    graph["extra"]["lab_edit"]["widgets"] = _widgets_map(by_title)

    ensure_occupancy_note(graph, OCCUPANCY_MODE)
    stamp_app_mode(
        graph,
        inputs=[
            (ENHANCE_TITLE, "prompt", {"label": "Prompt", "height": 140}),
            (ENHANCE_TITLE, "enhance", {"label": "Rewrite prompt"}),
            (NEG_ENHANCE_TITLE, "enhance", {"label": "Rewrite negative"}),
            (LATENT_TITLE, "width", {"label": "Width"}),
            (LATENT_TITLE, "height", {"label": "Height"}),
            (LATENT_TITLE, "length", {"label": "Frames"}),
            (SAVER_TITLE, "frame_rate", {"label": "FPS"}),
            (SAMPLER_TITLE, "seed", {"label": "Seed"}),
        ],
        outputs=[SAVER_TITLE],
        lane="film",
        occupancy=OCCUPANCY_MODE,
        handoff=(),
        default_view="app",
        enhance_off_identity=False,
    )
    apply_lab_completeness_flags(graph)
    graph["last_node_id"] = max(int(node["id"]) for node in graph["nodes"])
    graph["last_link_id"] = max(int(link[0]) for link in graph["links"])
    apply_lab_identity(graph, LAB_REL)
    finalize_layout(graph)
    return graph


def _write(graph: dict[str, Any], dest: Any) -> None:
    """Write ``graph`` as pretty JSON with a trailing newline.

    Args:
        graph: Serialized Comfy graph.
        dest: Destination path.

    Returns:
        None.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    """Write the lab graph and its byte-identical package copy.

    Returns:
        Process exit code.
    """
    graph = build_generate_cutaway()
    lab_path = lab_dest(LAB_REL, lane="film")
    _write(graph, lab_path)
    package_path = ROOT / PACKAGE_SUBPATH
    _write(graph, package_path)
    if lab_path.read_bytes() != package_path.read_bytes():
        raise SystemExit(f"{package_path} is not byte-identical to {lab_path}")
    print(f"wrote {lab_path}")
    print(f"wrote {package_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
