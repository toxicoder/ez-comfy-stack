#!/usr/bin/env python3
"""Build the stills/upscale-reframe lab App (Upscale & Reframe image utility).

Not imported by pytest (leading underscore). Run from repo root:

  python3 tests/python/_build_upreframe.py

Writes only ``workflows/_lab/stills/upscale-reframe.json``. The loaded still
enters the sampler as a ReferenceLatent and the canvas comes from
EZImageFormat, so a narrower or taller aspect generates the missing area
instead of stretching the source. The source is snapped to the Flux.2 Klein
div16 VAE grid (EZSnapImage) before VAEEncode, like stills/text-swap.
Format / upscale / describe / quality / check-models nodes are inserted by the
shared wiring helpers in ``dump_wired_graph`` (identity -> format -> upscale ->
describe -> stamp -> layout), so this module only authors the chain around
them.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from _lab_paths import lab_dest
from _wire_format import dump_wired_graph

ROOT = Path(__file__).resolve().parents[2]

REL = "stills/upscale-reframe"
SAVE_PREFIX = "ez_reframe"
CANVAS = (1280, 704)

PROMPT = (
    "Keep the subject, camera height, light, palette, and lens character of the "
    "reference still. Reframe the shot so the new canvas is filled: back the "
    "camera away or swing it sideways and continue the same place into the new "
    "edges. Keep the horizon level and keep scale, ground contact, and "
    "perspective consistent with the reference. Original characters only, and "
    "no added lettering."
)
NEGATIVE = (
    "stretched and smeared subject, duplicated limbs, duplicated lettering, "
    "watermarks, black border vignette, mushy background, oversharpen halos, "
    "muddy blacks"
)
DESCRIPTION = (
    "Klein 4B upscale and reframe of a loaded still. Format sets the target "
    "aspect, Upscale (default none) is lanczos on the finished PNG. "
    "Prefix ez_reframe."
)
NOTE = f"""## stills/upscale-reframe

Klein 4B **Upscale & Reframe**. Load a still, choose the aspect the result must land in on **Format / platform** (or type Custom Width x Height), set **Output size** to **Force format** so that canvas wins over the input's own aspect, then pick **Upscale** when the result also has to be bigger.

Reframe changes the canvas, not the pixels. The loaded still is snapped to the Klein VAE grid, VAE-encoded, and attached to the positive prompt as a ReferenceLatent; the sampler's `latent_image` is a blank Flux.2 canvas sized by Format / platform (or Custom Width x Height). A narrower or taller crop therefore generates the missing area instead of stretching or padding the source.

Output size stays on **Match input** in the shipped graph: the canvas then follows the loaded still's own aspect (nearest catalog row), so a still that already matches the target aspect keeps it - nothing is stretched or padded. Switch to **Force format** to push a still into a different aspect.

Upscale (default none) is lanczos on the finished PNG: 2x and 4x multiply the canvas, 4K fits it in a 3840x2160 box (portrait 2160x3840).

Do not Queue without a start image; with nothing to reference this is a blank canvas. Prompt names only what must survive the crop.

Occupancy: klein - stop Wan, LTX, podcast, music. One GB10 job.
Prompt enhance is on by default (on-box Qwen3-4B-Instruct-2507). After Queue, the Enhance node shows the prompt CLIP used. Turn Enhance off to pin the widget text.
"""


def _out(name: str, ltype: str) -> dict[str, Any]:
    """Serialize one output socket with no links yet."""
    return {"name": name, "type": ltype, "links": [], "slot_index": 0}


def _inp(name: str, ltype: str, *, shape: int | None = None) -> dict[str, Any]:
    """Serialize one input socket with no link yet."""
    item: dict[str, Any] = {"name": name, "type": ltype, "link": None}
    if shape is not None:
        item["shape"] = shape
    return item


def _node(
    nid: int,
    ntype: str,
    pos: list[float],
    size: list[float],
    title: str,
    widgets: list[Any],
    inputs: list[dict[str, Any]],
    outputs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build one serialized node with ``order`` = id (layout re-stages it)."""
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


def _link(
    graph: dict[str, Any],
    src: dict[str, Any],
    src_slot: int,
    dst: dict[str, Any],
    dst_name: str,
    ltype: str,
) -> None:
    """Append one link row and mirror it on both sockets."""
    dst_slot = next(
        index
        for index, item in enumerate(dst["inputs"])
        if item.get("name") == dst_name
    )
    link_id = int(graph["last_link_id"]) + 1
    graph["last_link_id"] = link_id
    out = src["outputs"][src_slot]
    out["links"] = list(out.get("links") or []) + [link_id]
    out["slot_index"] = src_slot
    dst["inputs"][dst_slot]["link"] = link_id
    graph["links"].append([link_id, src["id"], src_slot, dst["id"], dst_slot, ltype])


def _nodes() -> list[dict[str, Any]]:
    """Author every node the wiring helpers do not insert."""
    by_id: dict[int, dict[str, Any]] = {}

    def add(*args: Any) -> None:
        node = _node(*args)
        by_id[int(node["id"])] = node

    add(
        1,
        "UNETLoader",
        [40, 508],
        [360, 82],
        "Klein 4B distilled FP8",
        ["flux-2-klein-4b-fp8.safetensors", "default"],
        [],
        [_out("MODEL", "MODEL")],
    )
    add(
        2,
        "CLIPLoader",
        [40, 662],
        [360, 106],
        "Qwen3-4B TE",
        ["qwen_3_4b.safetensors", "flux2", "default"],
        [],
        [_out("CLIP", "CLIP")],
    )
    add(
        3,
        "VAELoader",
        [40, 840],
        [360, 58],
        "Flux2 VAE",
        ["flux2-vae.safetensors"],
        [],
        [_out("VAE", "VAE")],
    )
    add(
        4,
        "CLIPTextEncode",
        [816, 1000],
        [420, 160],
        "Positive",
        [PROMPT],
        [_inp("clip", "CLIP"), _inp("text", "STRING")],
        [_out("CONDITIONING", "CONDITIONING")],
    )
    add(
        5,
        "CLIPTextEncode",
        [816, 1724],
        [420, 120],
        "Negative",
        [NEGATIVE],
        [_inp("clip", "CLIP"), _inp("text", "STRING")],
        [_out("CONDITIONING", "CONDITIONING")],
    )
    add(
        6,
        "EmptyFlux2LatentImage",
        [1284, 508],
        [280, 106],
        "Canvas from Format",
        [CANVAS[0], CANVAS[1], 1],
        [
            _inp("width", "INT"),
            _inp("height", "INT"),
            _inp("batch_size", "INT"),
        ],
        [_out("LATENT", "LATENT")],
    )
    add(
        7,
        "KSampler",
        [1284, 990],
        [320, 262],
        "KSampler",
        [42, "fixed", 8, 1.0, "euler", "simple", 1.0],
        [
            _inp("model", "MODEL"),
            _inp("positive", "CONDITIONING"),
            _inp("negative", "CONDITIONING"),
            _inp("latent_image", "LATENT"),
        ],
        [_out("LATENT", "LATENT")],
    )
    add(
        8,
        "VAEDecode",
        [1652, 508],
        [240, 46],
        "VAE Decode",
        [],
        [_inp("samples", "LATENT"), _inp("vae", "VAE")],
        [_out("IMAGE", "IMAGE")],
    )
    add(
        9,
        "SaveImage",
        [1652, 778],
        [280, 270],
        "Save reframe",
        [SAVE_PREFIX],
        [_inp("images", "IMAGE")],
        [],
    )
    add(
        10,
        "Note",
        [40, 80],
        [960, 280],
        "Operator note",
        [NOTE],
        [],
        [],
    )
    add(
        11,
        "LoadImage",
        [448, 508],
        [320, 314],
        "Source still",
        ["example.png", "image"],
        [],
        [_out("IMAGE", "IMAGE"), _out("MASK", "MASK")],
    )
    add(
        12,
        "EZKleinPromptEnhance",
        [816, 508],
        [420, 280],
        "Klein Prompt Enhance (reframe)",
        [
            "custom",
            PROMPT,
            True,
            "edit",
            "16:9 landscape reframe",
            "none",
            REL,
        ],
        [],
        [_out("prompt", "STRING")],
    )
    add(
        13,
        "VAEEncode",
        [1284, 686],
        [240, 80],
        "Encode source plate",
        [],
        [_inp("pixels", "IMAGE"), _inp("vae", "VAE")],
        [_out("LATENT", "LATENT")],
    )
    add(
        14,
        "ReferenceLatent",
        [1284, 838],
        [280, 80],
        "Positive + source plate",
        [],
        [_inp("conditioning", "CONDITIONING"), _inp("latent", "LATENT", shape=7)],
        [_out("CONDITIONING", "CONDITIONING")],
    )
    add(
        15,
        "EZNegativePromptEnhance",
        [816, 1232],
        [420, 280],
        "Negative Prompt Enhance",
        [NEGATIVE, True, "klein"],
        [_inp("positive", "STRING")],
        [_out("prompt", "STRING")],
    )
    add(
        16,
        "EZSnapImage",
        [1284, 440],
        [240, 60],
        "Snap to Klein grid",
        [],
        [_inp("image", "IMAGE")],
        [_out("image", "IMAGE")],
    )
    return [by_id[key] for key in sorted(by_id)]


def build_graph() -> dict[str, Any]:
    """Assemble the reframe chain before the wiring helpers run.

    Returns:
        Serialized graph dict (no Format / Upscale / Quality nodes yet).
    """
    nodes = {int(node["id"]): node for node in _nodes()}
    graph: dict[str, Any] = {
        "id": REL.split("/", 1)[1],
        "revision": 1,
        "last_node_id": max(nodes),
        "last_link_id": 0,
        "nodes": list(nodes.values()),
        "links": [],
        "groups": [],
        "config": {},
        "extra": {
            "lab_profile": REL,
            "lab_flux_tier": "fast",
            "ds": {"scale": 1, "offset": [0, 0]},
            "lab_note": NOTE,
            "lab_description": DESCRIPTION,
        },
        "version": 0.4,
    }
    live = nodes
    links: list[tuple[int, int, int, str, str]] = [
        (1, 0, 7, "model", "MODEL"),
        (2, 0, 4, "clip", "CLIP"),
        (2, 0, 5, "clip", "CLIP"),
        (3, 0, 8, "vae", "VAE"),
        (3, 0, 13, "vae", "VAE"),
        (4, 0, 14, "conditioning", "CONDITIONING"),
        (5, 0, 7, "negative", "CONDITIONING"),
        (6, 0, 7, "latent_image", "LATENT"),
        (7, 0, 8, "samples", "LATENT"),
        (8, 0, 9, "images", "IMAGE"),
        (11, 0, 16, "image", "IMAGE"),
        (16, 0, 13, "pixels", "IMAGE"),
        (12, 0, 4, "text", "STRING"),
        (12, 0, 15, "positive", "STRING"),
        (13, 0, 14, "latent", "LATENT"),
        (14, 0, 7, "positive", "CONDITIONING"),
        (15, 0, 5, "text", "STRING"),
    ]
    for src_id, src_slot, dst_id, dst_name, ltype in links:
        _link(graph, live[src_id], src_slot, live[dst_id], dst_name, ltype)
    return graph


def main() -> None:
    """Build and write the reframe lab graph."""
    graph = build_graph()
    path = lab_dest(REL)
    dump_wired_graph(path, graph)
    print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
