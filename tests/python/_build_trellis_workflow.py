#!/usr/bin/env python3
"""Build the TRELLIS-only lab graph (no Pixal3D).

Run from repo root:
  python3 tests/python/_build_trellis_workflow.py
"""

from __future__ import annotations

import json
from typing import Any

from _lab_paths import lab_dest
from _stamp_app_mode import stamp_suite_graph

NOTE = """## klein-trellis2-lab-example

Klein still → native TRELLIS.2 INT8 mesh (Comfy core nodes).

```bash
./scripts/manage.sh download-3d --tier trellis2
./scripts/manage.sh occupancy enter trellis --yes
```

LoadImage: a Klein still (`ez_still_*.png` or a clay plate). Unload models first (EZUnloadModels).
UNET: `trellis_2_int8_convrot.safetensors`. CLIP vision: `dino_v3_vit_l.safetensors` (DINOv3 license, opt-in pack).
Lab upsample **512** (not 1536). TRELLIS-only canvas. Occupancy: trellis.

DINOv3 is Meta's custom commercial-friendly license — not Apache. MIT TRELLIS weights without DINOv3 cannot Queue.
"""


def _node(
    nid: int,
    ntype: str,
    *,
    pos: tuple[float, float],
    size: tuple[float, float],
    inputs: list[dict[str, Any]],
    outputs: list[dict[str, Any]],
    widgets: list[Any] | None = None,
    title: str | None = None,
    order: int = 0,
) -> dict[str, Any]:
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
        "properties": {"Node name for S&R": ntype, "cnr_id": "comfy-core"},
        "widgets_values": list(widgets or []),
    }
    if title:
        node["title"] = title
    return node


def _in(name: str, typ: str, link: int | None = None) -> dict[str, Any]:
    entry: dict[str, Any] = {"name": name, "type": typ}
    if link is not None:
        entry["link"] = link
    return entry


def _out(name: str, typ: str, links: list[int] | None = None) -> dict[str, Any]:
    return {"name": name, "type": typ, "links": list(links or [])}


def build_trellis() -> dict[str, Any]:
    links: list[list[Any]] = []
    lid = 1

    def wire(
        frm: dict[str, Any],
        fslot: int,
        to: dict[str, Any],
        tslot: int,
        ltype: str,
    ) -> int:
        nonlocal lid
        link_id = lid
        lid += 1
        links.append([link_id, int(frm["id"]), fslot, int(to["id"]), tslot, ltype])
        frm["outputs"][fslot]["links"].append(link_id)
        to["inputs"][tslot]["link"] = link_id
        return link_id

    note = _node(
        1,
        "Note",
        pos=(40, 40),
        size=(720, 360),
        inputs=[],
        outputs=[],
        widgets=[NOTE],
        title="Operator note",
        order=0,
    )
    load = _node(
        2,
        "LoadImage",
        pos=(40, 440),
        size=(320, 314),
        inputs=[],
        outputs=[_out("IMAGE", "IMAGE"), _out("MASK", "MASK")],
        widgets=["example.png", "image"],
        title="Klein still",
        order=1,
    )
    unload = _node(
        3,
        "EZUnloadModels",
        pos=(400, 440),
        size=(280, 80),
        inputs=[_in("image", "IMAGE")],
        outputs=[_out("image", "IMAGE")],
        title="Unload models (pass IMAGE)",
        order=2,
    )
    clip = _node(
        4,
        "CLIPVisionLoader",
        pos=(40, 800),
        size=(360, 80),
        inputs=[],
        outputs=[_out("CLIP_VISION", "CLIP_VISION")],
        widgets=["dino_v3_vit_l.safetensors"],
        title="DINOv3 ViT-L",
        order=3,
    )
    unet = _node(
        5,
        "UNETLoader",
        pos=(40, 920),
        size=(360, 90),
        inputs=[],
        outputs=[_out("MODEL", "MODEL")],
        widgets=["trellis_2_int8_convrot.safetensors", "default"],
        title="TRELLIS.2 INT8",
        order=4,
    )
    vae_shape = _node(
        6,
        "VAELoader",
        pos=(40, 1040),
        size=(360, 70),
        inputs=[],
        outputs=[_out("VAE", "VAE")],
        widgets=["trellis_2_shape_vae_bf16.safetensors"],
        title="Shape VAE",
        order=5,
    )
    vae_tex = _node(
        7,
        "VAELoader",
        pos=(40, 1140),
        size=(360, 70),
        inputs=[],
        outputs=[_out("VAE", "VAE")],
        widgets=["trellis_2_texture_vae_bf16.safetensors"],
        title="Texture VAE",
        order=6,
    )
    cond = _node(
        8,
        "Trellis2Conditioning",
        pos=(720, 440),
        size=(260, 80),
        inputs=[_in("clip_vision_model", "CLIP_VISION"), _in("image", "IMAGE")],
        outputs=[_out("positive", "CONDITIONING"), _out("negative", "CONDITIONING")],
        order=7,
    )
    empty = _node(
        9,
        "EmptyTrellis2LatentStructure",
        pos=(720, 560),
        size=(260, 80),
        inputs=[],
        outputs=[_out("LATENT", "LATENT")],
        widgets=[1],
        order=8,
    )
    ks_struct = _node(
        10,
        "KSampler",
        pos=(1040, 440),
        size=(280, 270),
        inputs=[
            _in("model", "MODEL"),
            _in("positive", "CONDITIONING"),
            _in("negative", "CONDITIONING"),
            _in("latent_image", "LATENT"),
        ],
        outputs=[_out("LATENT", "LATENT")],
        widgets=[42, "fixed", 12, 7.5, "euler", "normal", 1],
        title="KSampler (structure)",
        order=9,
    )
    decode_struct = _node(
        11,
        "VaeDecodeStructureTrellis2",
        pos=(1380, 440),
        size=(280, 90),
        inputs=[_in("samples", "LATENT"), _in("vae", "VAE")],
        outputs=[_out("voxel", "VOXEL")],
        widgets=["32"],
        order=10,
    )
    shape_stage = _node(
        12,
        "Trellis2ShapeStage",
        pos=(1380, 560),
        size=(280, 80),
        inputs=[
            _in("positive", "CONDITIONING"),
            _in("negative", "CONDITIONING"),
            _in("voxel", "VOXEL"),
        ],
        outputs=[
            _out("positive", "CONDITIONING"),
            _out("negative", "CONDITIONING"),
            _out("LATENT", "LATENT"),
        ],
        order=11,
    )
    ks_shape = _node(
        13,
        "KSampler",
        pos=(1720, 440),
        size=(280, 270),
        inputs=[
            _in("model", "MODEL"),
            _in("positive", "CONDITIONING"),
            _in("negative", "CONDITIONING"),
            _in("latent_image", "LATENT"),
        ],
        outputs=[_out("LATENT", "LATENT")],
        widgets=[42, "fixed", 12, 7.5, "euler", "normal", 1],
        title="KSampler (shape)",
        order=12,
    )
    upsample = _node(
        14,
        "Trellis2UpsampleStage",
        pos=(2060, 440),
        size=(300, 130),
        inputs=[
            _in("positive", "CONDITIONING"),
            _in("negative", "CONDITIONING"),
            _in("shape_latent", "LATENT"),
            _in("vae", "VAE"),
        ],
        outputs=[
            _out("positive", "CONDITIONING"),
            _out("negative", "CONDITIONING"),
            _out("LATENT", "LATENT"),
        ],
        widgets=["512"],
        title="Upsample 512",
        order=13,
    )
    ks_up = _node(
        15,
        "KSampler",
        pos=(2420, 440),
        size=(280, 270),
        inputs=[
            _in("model", "MODEL"),
            _in("positive", "CONDITIONING"),
            _in("negative", "CONDITIONING"),
            _in("latent_image", "LATENT"),
        ],
        outputs=[_out("LATENT", "LATENT")],
        widgets=[42, "fixed", 12, 7.5, "euler", "simple", 1],
        title="KSampler (512)",
        order=14,
    )
    decode_shape = _node(
        16,
        "VaeDecodeShapeTrellis",
        pos=(2760, 440),
        size=(280, 80),
        inputs=[_in("samples", "LATENT"), _in("vae", "VAE")],
        outputs=[_out("mesh", "MESH"), _out("shape_subdivides", "SHAPE_SUBDIVIDES")],
        order=15,
    )
    tex_stage = _node(
        17,
        "Trellis2TextureStage",
        pos=(2760, 560),
        size=(280, 100),
        inputs=[
            _in("positive", "CONDITIONING"),
            _in("negative", "CONDITIONING"),
            _in("shape_latent", "LATENT"),
        ],
        outputs=[
            _out("positive", "CONDITIONING"),
            _out("negative", "CONDITIONING"),
            _out("LATENT", "LATENT"),
        ],
        order=16,
    )
    ks_tex = _node(
        18,
        "KSampler",
        pos=(3100, 440),
        size=(280, 270),
        inputs=[
            _in("model", "MODEL"),
            _in("positive", "CONDITIONING"),
            _in("negative", "CONDITIONING"),
            _in("latent_image", "LATENT"),
        ],
        outputs=[_out("LATENT", "LATENT")],
        widgets=[43, "fixed", 12, 1, "euler", "normal", 1],
        title="KSampler (texture)",
        order=17,
    )
    decode_tex = _node(
        19,
        "VaeDecodeTextureTrellis",
        pos=(3440, 440),
        size=(280, 100),
        inputs=[
            _in("samples", "LATENT"),
            _in("vae", "VAE"),
            _in("shape_subdivides", "SHAPE_SUBDIVIDES"),
        ],
        outputs=[_out("voxel_colors", "VOXEL")],
        order=18,
    )
    paint = _node(
        20,
        "PaintMesh",
        pos=(3780, 440),
        size=(240, 80),
        inputs=[_in("mesh", "MESH"), _in("voxel_colors", "VOXEL")],
        outputs=[_out("mesh", "MESH")],
        order=19,
    )
    glb = _node(
        21,
        "MeshToFile3D",
        pos=(4080, 440),
        size=(240, 60),
        inputs=[_in("mesh", "MESH")],
        outputs=[_out("model_3d", "FILE_3D_GLB")],
        title="Save GLB",
        order=20,
    )

    wire(load, 0, unload, 0, "IMAGE")
    wire(unload, 0, cond, 1, "IMAGE")
    wire(clip, 0, cond, 0, "CLIP_VISION")
    wire(unet, 0, ks_struct, 0, "MODEL")
    wire(cond, 0, ks_struct, 1, "CONDITIONING")
    wire(cond, 1, ks_struct, 2, "CONDITIONING")
    wire(empty, 0, ks_struct, 3, "LATENT")
    wire(ks_struct, 0, decode_struct, 0, "LATENT")
    wire(vae_shape, 0, decode_struct, 1, "VAE")
    wire(cond, 0, shape_stage, 0, "CONDITIONING")
    wire(cond, 1, shape_stage, 1, "CONDITIONING")
    wire(decode_struct, 0, shape_stage, 2, "VOXEL")
    wire(unet, 0, ks_shape, 0, "MODEL")
    wire(shape_stage, 0, ks_shape, 1, "CONDITIONING")
    wire(shape_stage, 1, ks_shape, 2, "CONDITIONING")
    wire(shape_stage, 2, ks_shape, 3, "LATENT")
    wire(shape_stage, 0, upsample, 0, "CONDITIONING")
    wire(shape_stage, 1, upsample, 1, "CONDITIONING")
    wire(ks_shape, 0, upsample, 2, "LATENT")
    wire(vae_shape, 0, upsample, 3, "VAE")
    wire(unet, 0, ks_up, 0, "MODEL")
    wire(upsample, 0, ks_up, 1, "CONDITIONING")
    wire(upsample, 1, ks_up, 2, "CONDITIONING")
    wire(upsample, 2, ks_up, 3, "LATENT")
    wire(ks_up, 0, decode_shape, 0, "LATENT")
    wire(vae_shape, 0, decode_shape, 1, "VAE")
    wire(upsample, 0, tex_stage, 0, "CONDITIONING")
    wire(upsample, 1, tex_stage, 1, "CONDITIONING")
    wire(ks_up, 0, tex_stage, 2, "LATENT")
    wire(unet, 0, ks_tex, 0, "MODEL")
    wire(tex_stage, 0, ks_tex, 1, "CONDITIONING")
    wire(tex_stage, 1, ks_tex, 2, "CONDITIONING")
    wire(tex_stage, 2, ks_tex, 3, "LATENT")
    wire(ks_tex, 0, decode_tex, 0, "LATENT")
    wire(vae_tex, 0, decode_tex, 1, "VAE")
    wire(decode_shape, 1, decode_tex, 2, "SHAPE_SUBDIVIDES")
    wire(decode_shape, 0, paint, 0, "MESH")
    wire(decode_tex, 0, paint, 1, "VOXEL")
    wire(paint, 0, glb, 0, "MESH")

    nodes = [
        note,
        load,
        unload,
        clip,
        unet,
        vae_shape,
        vae_tex,
        cond,
        empty,
        ks_struct,
        decode_struct,
        shape_stage,
        ks_shape,
        upsample,
        ks_up,
        decode_shape,
        tex_stage,
        ks_tex,
        decode_tex,
        paint,
        glb,
    ]
    graph: dict[str, Any] = {
        "id": "klein-trellis2-lab-example",
        "revision": 1,
        "last_node_id": 21,
        "last_link_id": lid - 1,
        "nodes": nodes,
        "links": links,
        "groups": [],
        "config": {},
        "extra": {
            "lab_note": NOTE,
            "lab_profile": "klein-trellis2-lab-example",
            "lab_description": "Klein still to native TRELLIS.2 INT8 mesh. 512. TRELLIS-only.",
            "lab_trellis": {
                "unet": "trellis_2_int8_convrot.safetensors",
                "resolution": 512,
                "native_only": True,
            },
        },
        "version": 0.4,
    }
    return stamp_suite_graph(graph)


def main() -> None:
    dest = lab_dest("klein-trellis2-lab-example", lane="optional")
    graph = build_trellis()
    dest.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    print(dest)


if __name__ == "__main__":
    main()
