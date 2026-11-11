#!/usr/bin/env python3
"""Build the 3d-lane Studio Apps (blockout, shot-to-prop, prop-variants).

Run from repo root:
  python3 tests/python/_build_3d_apps.py

Every graph here is a TRELLIS.2 printer on the ``trellis`` occupancy lane, so
it shares the model pins and the node primitives of ``_build_trellis_workflow``
rather than restating them. The chain ends on ``SaveGLB``, the only node that
writes a file. Single-mesh Apps route through ``MeshToFile3D`` first, which
converts to GLB bytes in memory; a batched App feeds ``SaveGLB`` the MESH
directly, because ``MeshToFile3D`` keeps only batch item 0.
"""

from __future__ import annotations

from typing import Any

from _build_trellis_workflow import _in
from _build_trellis_workflow import _node
from _build_trellis_workflow import _out
from _build_trellis_workflow import _Wires
from _lab_layout import finalize_layout
from _lab_paths import lab_dest
from _lab_paths import write_lab_graph
from _stamp_app_mode import apply_lab_completeness_flags
from _stamp_app_mode import ensure_occupancy_note
from _stamp_app_mode import stamp_app_mode

UNET = "trellis_2_int8_convrot.safetensors"
CLIP_VISION = "dino_v3_vit_l.safetensors"
SHAPE_VAE = "trellis_2_shape_vae_bf16.safetensors"
TEXTURE_VAE = "trellis_2_texture_vae_bf16.safetensors"

# ComfyUI's Trellis2UpsampleStage takes target_resolution as an int bounded to
# 1024-2048 in steps of 128. The 512 and 256 that older notes named are not
# accepted by the node at all.
UPSAMPLE_RESOLUTION = 1024
STRUCTURE_RESOLUTION = "32"

MODEL_LINES = (
    "UNET: `trellis_2_int8_convrot.safetensors`. CLIP vision: `dino_v3_vit_l.safetensors` "
    "(DINOv3 license, opt-in pack). Structure decode stays at 32."
)

DINO_LINE = (
    "DINOv3 is Meta's custom commercial-friendly license - not Apache. MIT TRELLIS weights "
    "without DINOv3 cannot Queue."
)


class _Scene:
    """Node/link builder that allocates ids, so chrome nodes never collide.

    The 3d graphs add EZQuality and EZModelCheck after the chain is built;
    allocating ids from one counter is what keeps those two from landing on
    top of an already-used id.
    """

    def __init__(self) -> None:
        self.nodes: list[dict[str, Any]] = []
        self.wires = _Wires()

    def add(
        self,
        ntype: str,
        *,
        title: str,
        inputs: list[dict[str, Any]] | None = None,
        outputs: list[dict[str, Any]] | None = None,
        widgets: list[Any] | None = None,
        size: tuple[float, float] = (280.0, 90.0),
        pos: tuple[float, float] = (40.0, 440.0),
    ) -> dict[str, Any]:
        node = _node(
            len(self.nodes) + 1,
            ntype,
            pos=pos,
            size=size,
            inputs=inputs or [],
            outputs=outputs or [],
            widgets=widgets,
            title=title,
            order=len(self.nodes),
        )
        self.nodes.append(node)
        return node

    def note(self, text: str) -> dict[str, Any]:
        return self.add(
            "Note",
            title="Operator note",
            widgets=[text],
            size=(720.0, 360.0),
            pos=(40.0, 40.0),
        )

    def wire(self, frm: dict[str, Any], fslot: int, to: dict[str, Any], tslot: int, ltype: str) -> int:
        return self.wires.wire(frm, fslot, to, tslot, ltype)

    def model_stack(self, *, textured: bool) -> dict[str, dict[str, Any]]:
        """Loaders shared by every 3d printer."""
        clip = self.add(
            "CLIPVisionLoader",
            title="DINOv3 ViT-L",
            outputs=[_out("CLIP_VISION", "CLIP_VISION")],
            widgets=[CLIP_VISION],
            size=(360.0, 80.0),
        )
        unet = self.add(
            "UNETLoader",
            title="TRELLIS.2 INT8",
            outputs=[_out("MODEL", "MODEL")],
            widgets=[UNET, "default"],
            size=(360.0, 90.0),
        )
        vae_shape = self.add(
            "VAELoader",
            title="Shape VAE",
            outputs=[_out("VAE", "VAE")],
            widgets=[SHAPE_VAE],
            size=(360.0, 70.0),
        )
        stack = {"clip": clip, "unet": unet, "vae_shape": vae_shape}
        if textured:
            stack["vae_texture"] = self.add(
                "VAELoader",
                title="Texture VAE",
                outputs=[_out("VAE", "VAE")],
                widgets=[TEXTURE_VAE],
                size=(360.0, 70.0),
            )
        return stack

    def structure(self, stack: dict[str, dict[str, Any]], cond: dict[str, Any], batch_size: int) -> dict[str, Any]:
        """Structure latent -> sampler -> voxel grid."""
        unet = stack["unet"]
        empty = self.add(
            "EmptyTrellis2LatentStructure",
            title=f"Empty structure x{batch_size}",
            outputs=[_out("LATENT", "LATENT")],
            widgets=[batch_size],
        )
        ks_struct = self.add(
            "KSampler",
            title="KSampler (structure)",
            inputs=[
                _in("model", "MODEL"),
                _in("positive", "CONDITIONING"),
                _in("negative", "CONDITIONING"),
                _in("latent_image", "LATENT"),
            ],
            outputs=[_out("LATENT", "LATENT")],
            widgets=[42, "fixed", 12, 7.5, "euler", "normal", 1],
            size=(280.0, 270.0),
        )
        self.wire(unet, 0, ks_struct, 0, "MODEL")
        self.wire(cond, 0, ks_struct, 1, "CONDITIONING")
        self.wire(cond, 1, ks_struct, 2, "CONDITIONING")
        self.wire(empty, 0, ks_struct, 3, "LATENT")
        decode = self.add(
            "VaeDecodeStructureTrellis2",
            title="Decode structure 32",
            inputs=[_in("samples", "LATENT"), _in("vae", "VAE")],
            outputs=[_out("voxel", "VOXEL")],
            widgets=[STRUCTURE_RESOLUTION],
        )
        self.wire(ks_struct, 0, decode, 0, "LATENT")
        self.wire(stack["vae_shape"], 0, decode, 1, "VAE")
        return decode

    def conditioning(self, image: dict[str, Any], stack: dict[str, dict[str, Any]]) -> dict[str, Any]:
        cond = self.add(
            "Trellis2Conditioning",
            title="Trellis2 conditioning",
            inputs=[_in("clip_vision_model", "CLIP_VISION"), _in("image", "IMAGE")],
            outputs=[_out("positive", "CONDITIONING"), _out("negative", "CONDITIONING")],
        )
        self.wire(stack["clip"], 0, cond, 0, "CLIP_VISION")
        self.wire(image, 0, cond, 1, "IMAGE")
        return cond

    def shape(
        self,
        stack: dict[str, dict[str, Any]],
        cond: dict[str, Any],
        voxel: dict[str, Any],
        *,
        upsample: bool,
        shape_steps: int,
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        """Voxel grid -> shape stage -> optional upsample -> decoded mesh.

        Returns the decoded shape node, the conditioning source the texture
        stage must reuse (the upsample stage when it ran, the shape stage when
        it did not), and the sampler holding the refined shape latent.
        """
        shape_stage = self.add(
            "Trellis2ShapeStage",
            title="Shape stage",
            inputs=[
                _in("positive", "CONDITIONING"),
                _in("negative", "CONDITIONING"),
                _in("voxel", "VOXEL"),
            ],
            outputs=[
                _out("positive", "CONDITIONING"),
                _out("negative", "CONDITIONING", slot=1),
                _out("LATENT", "LATENT", slot=2),
            ],
        )
        self.wire(cond, 0, shape_stage, 0, "CONDITIONING")
        self.wire(cond, 1, shape_stage, 1, "CONDITIONING")
        self.wire(voxel, 0, shape_stage, 2, "VOXEL")
        ks_shape = self.add(
            "KSampler",
            title="KSampler (shape)",
            inputs=[
                _in("model", "MODEL"),
                _in("positive", "CONDITIONING"),
                _in("negative", "CONDITIONING"),
                _in("latent_image", "LATENT"),
            ],
            outputs=[_out("LATENT", "LATENT")],
            widgets=[42, "fixed", shape_steps, 7.5, "euler", "normal", 1],
            size=(280.0, 270.0),
        )
        self.wire(stack["unet"], 0, ks_shape, 0, "MODEL")
        self.wire(shape_stage, 0, ks_shape, 1, "CONDITIONING")
        self.wire(shape_stage, 1, ks_shape, 2, "CONDITIONING")
        self.wire(shape_stage, 2, ks_shape, 3, "LATENT")

        last_latent = ks_shape
        cond_src = shape_stage
        if upsample:
            up = self.add(
                "Trellis2UpsampleStage",
                title="Upsample 1024",
                inputs=[
                    _in("positive", "CONDITIONING"),
                    _in("negative", "CONDITIONING"),
                    _in("shape_latent", "LATENT"),
                    _in("vae", "VAE"),
                ],
                outputs=[
                    _out("positive", "CONDITIONING"),
                    _out("negative", "CONDITIONING", slot=1),
                    _out("LATENT", "LATENT", slot=2),
                ],
                widgets=[UPSAMPLE_RESOLUTION],
                size=(300.0, 130.0),
            )
            self.wire(shape_stage, 0, up, 0, "CONDITIONING")
            self.wire(shape_stage, 1, up, 1, "CONDITIONING")
            self.wire(ks_shape, 0, up, 2, "LATENT")
            self.wire(stack["vae_shape"], 0, up, 3, "VAE")
            ks_up = self.add(
                "KSampler",
                title="KSampler (1024)",
                inputs=[
                    _in("model", "MODEL"),
                    _in("positive", "CONDITIONING"),
                    _in("negative", "CONDITIONING"),
                    _in("latent_image", "LATENT"),
                ],
                outputs=[_out("LATENT", "LATENT")],
                widgets=[42, "fixed", 12, 7.5, "euler", "simple", 1],
                size=(280.0, 270.0),
            )
            self.wire(stack["unet"], 0, ks_up, 0, "MODEL")
            self.wire(up, 0, ks_up, 1, "CONDITIONING")
            self.wire(up, 1, ks_up, 2, "CONDITIONING")
            self.wire(up, 2, ks_up, 3, "LATENT")
            last_latent = ks_up
            cond_src = up

        decode_shape = self.add(
            "VaeDecodeShapeTrellis",
            title="Decode shape",
            inputs=[_in("samples", "LATENT"), _in("vae", "VAE")],
            outputs=[
                _out("mesh", "MESH"),
                _out("shape_subdivides", "SHAPE_SUBDIVIDES", slot=1),
            ],
        )
        self.wire(last_latent, 0, decode_shape, 0, "LATENT")
        self.wire(stack["vae_shape"], 0, decode_shape, 1, "VAE")
        return decode_shape, cond_src, last_latent

    def texture(
        self,
        stack: dict[str, dict[str, Any]],
        shape_out: tuple[dict[str, Any], dict[str, Any], dict[str, Any]],
    ) -> dict[str, Any]:
        """Reuse the refined conditioning to paint the decoded mesh."""
        decode_shape, cond_src, shape_latent = shape_out
        tex_stage = self.add(
            "Trellis2TextureStage",
            title="Texture stage",
            inputs=[
                _in("positive", "CONDITIONING"),
                _in("negative", "CONDITIONING"),
                _in("shape_latent", "LATENT"),
            ],
            outputs=[
                _out("positive", "CONDITIONING"),
                _out("negative", "CONDITIONING", slot=1),
                _out("LATENT", "LATENT", slot=2),
            ],
        )
        self.wire(cond_src, 0, tex_stage, 0, "CONDITIONING")
        self.wire(cond_src, 1, tex_stage, 1, "CONDITIONING")
        self.wire(shape_latent, 0, tex_stage, 2, "LATENT")
        ks_tex = self.add(
            "KSampler",
            title="KSampler (texture)",
            inputs=[
                _in("model", "MODEL"),
                _in("positive", "CONDITIONING"),
                _in("negative", "CONDITIONING"),
                _in("latent_image", "LATENT"),
            ],
            outputs=[_out("LATENT", "LATENT")],
            widgets=[43, "fixed", 12, 1, "euler", "normal", 1],
            size=(280.0, 270.0),
        )
        self.wire(stack["unet"], 0, ks_tex, 0, "MODEL")
        self.wire(tex_stage, 0, ks_tex, 1, "CONDITIONING")
        self.wire(tex_stage, 1, ks_tex, 2, "CONDITIONING")
        self.wire(tex_stage, 2, ks_tex, 3, "LATENT")
        decode_tex = self.add(
            "VaeDecodeTextureTrellis",
            title="Decode texture",
            inputs=[
                _in("samples", "LATENT"),
                _in("vae", "VAE"),
                _in("shape_subdivides", "SHAPE_SUBDIVIDES"),
            ],
            outputs=[_out("voxel_colors", "VOXEL")],
        )
        self.wire(ks_tex, 0, decode_tex, 0, "LATENT")
        self.wire(stack["vae_texture"], 0, decode_tex, 1, "VAE")
        self.wire(decode_shape, 1, decode_tex, 2, "SHAPE_SUBDIVIDES")
        paint = self.add(
            "PaintMesh",
            title="Paint mesh",
            inputs=[_in("mesh", "MESH"), _in("voxel_colors", "VOXEL")],
            outputs=[_out("mesh", "MESH")],
            size=(240.0, 80.0),
        )
        self.wire(decode_shape, 0, paint, 0, "MESH")
        self.wire(decode_tex, 0, paint, 1, "VOXEL")
        return paint

    def save(
        self, mesh: dict[str, Any], prefix: str, *, batched: bool = False
    ) -> dict[str, Any]:
        """Terminate the chain on the only node that writes a .glb.

        A batched chain feeds ``SaveGLB`` the MESH directly: its MESH branch
        loops the batch and writes one file per item, while ``MeshToFile3D``
        keeps only the first item and hands over a single File3D.

        Args:
            mesh: Producer node whose MESH output is saved.
            prefix: ``filename_prefix`` widget for ``SaveGLB``.
            batched: Skip ``MeshToFile3D`` so every batch item is written.

        Returns:
            The ``SaveGLB`` node.
        """
        if batched:
            save = self.add(
                "SaveGLB",
                title="Save GLB",
                inputs=[_in("mesh", "MESH")],
                widgets=[prefix],
                size=(280.0, 80.0),
            )
            self.wire(mesh, 0, save, 0, "MESH")
            return save
        glb = self.add(
            "MeshToFile3D",
            title="To GLB bytes",
            inputs=[_in("mesh", "MESH")],
            outputs=[_out("model_3d", "FILE_3D_GLB")],
            size=(240.0, 60.0),
        )
        self.wire(mesh, 0, glb, 0, "MESH")
        save = self.add(
            "SaveGLB",
            title="Save GLB",
            inputs=[_in("mesh", "FILE_3D_GLB")],
            widgets=[prefix],
            size=(280.0, 80.0),
        )
        self.wire(glb, 0, save, 0, "FILE_3D_GLB")
        return save

    def root(self, *, stem: str, note: str, description: str, lab_trellis: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": stem,
            "revision": 1,
            "last_node_id": max(int(node["id"]) for node in self.nodes),
            "last_link_id": self.wires.last_link_id,
            "nodes": self.nodes,
            "links": self.wires.links,
            "groups": [],
            "config": {},
            "extra": {
                "lab_note": note,
                "lab_profile": f"3d/{stem}",
                "lab_description": description,
                "lab_trellis": lab_trellis,
            },
            "version": 0.4,
        }


def _gate_and_unload(scene: _Scene, source: dict[str, Any]) -> dict[str, Any]:
    """Guard the queue, then free VRAM, before anything conditions."""
    gate = scene.add(
        "EZDCCOccupancyGate",
        title="Occupancy gate",
        inputs=[_in("image", "IMAGE")],
        outputs=[_out("image", "IMAGE")],
        widgets=["trellis"],
    )
    scene.wire(source, 0, gate, 0, "IMAGE")
    unload = scene.add(
        "EZUnloadModels",
        title="Unload models (pass IMAGE)",
        inputs=[_in("image", "IMAGE")],
        outputs=[_out("image", "IMAGE")],
        size=(280.0, 80.0),
    )
    scene.wire(gate, 0, unload, 0, "IMAGE")
    return unload


def build_blockout() -> dict[str, Any]:
    """Gray-box blockout: structure and shape only, no texture pass."""
    note = "\n\n".join(
        (
            "## 3d/blockout-mesh",
            "Still pack plate -> untextured gray-box blockout for set dressing and framing.",
            "Structure and shape stages only: no upsample, no texture VAE, no PaintMesh. Shape "
            "sampling drops to 8 steps because a blockout is a proxy, not a deliverable.",
            "Source: `EZDCCLoadStillPack` (slug `go-see`, plate `mug`, layer `first`).",
            MODEL_LINES,
            "SaveGLB writes the mesh to `output/assets/objects/_lab-blockout/blockout_NNNNN_.glb` "
            "- MeshToFile3D only converts in memory. Do not mint an Asset Bible row from this graph.",
            DINO_LINE,
        )
    )
    scene = _Scene()
    scene.note(note)
    pack = scene.add(
        "EZDCCLoadStillPack",
        title="Still pack plate",
        outputs=[
            _out("IMAGE", "IMAGE"),
            _out("MASK", "MASK", slot=1),
            _out("STRING metadata", "STRING", slot=2),
        ],
        widgets=["go-see", "mug", "first"],
        size=(320.0, 314.0),
    )
    image = _gate_and_unload(scene, pack)
    stack = scene.model_stack(textured=False)
    cond = scene.conditioning(image, stack)
    voxel = scene.structure(stack, cond, batch_size=1)
    decode_shape, _cond_src, _shape_latent = scene.shape(stack, cond, voxel, upsample=False, shape_steps=8)
    scene.save(decode_shape, "assets/objects/_lab-blockout/blockout")
    graph = scene.root(
        stem="blockout-mesh",
        note=note,
        description="Still pack plate to untextured TRELLIS.2 blockout mesh. No texture pass.",
        lab_trellis={
            "unet": UNET,
            "resolution": None,
            "stages": ["structure", "shape"],
            "textured": False,
            "batch_size": 1,
            "save_prefix": "assets/objects/_lab-blockout/blockout",
            "native_only": True,
        },
    )
    return _finish(graph, inputs=[("Still pack plate", "plate")], handoff=("3d/trellis2",))


def build_shot_to_prop() -> dict[str, Any]:
    """Textured prop mesh sourced from a DCC guide still of a live shot."""
    note = "\n\n".join(
        (
            "## 3d/shot-to-prop",
            "DCC guide still -> textured TRELLIS.2 prop mesh, so a hero object in a finished shot "
            "becomes an asset you can re-composite into other shots.",
            "Source: `EZDCCLoadGuideStill` (slug `go-see`, shot `12`, layer `first`). The preview "
            "node draws the guide layer you are turning into geometry before the queue spends GPU.",
            MODEL_LINES,
            "Upsample `target_resolution` is an int and ComfyUI only accepts 1024-2048 in steps of "
            "128; this graph runs the 1024 floor.",
            "SaveGLB writes the mesh to `output/assets/objects/_lab-shot-prop/prop_NNNNN_.glb` "
            "- MeshToFile3D only converts in memory. Do not mint an Asset Bible row from this graph.",
            DINO_LINE,
        )
    )
    scene = _Scene()
    scene.note(note)
    guide = scene.add(
        "EZDCCLoadGuideStill",
        title="Guide still",
        outputs=[
            _out("IMAGE", "IMAGE"),
            _out("MASK", "MASK", slot=1),
            _out("STRING metadata", "STRING", slot=2),
        ],
        widgets=["go-see", "12", "first"],
        size=(320.0, 314.0),
    )
    preview = scene.add(
        "EZDCCPreviewGuideLayer",
        title="Preview guide layer",
        inputs=[_in("image", "IMAGE")],
        outputs=[_out("IMAGE", "IMAGE")],
        widgets=["hero still"],
    )
    scene.wire(guide, 0, preview, 0, "IMAGE")
    image = _gate_and_unload(scene, preview)
    stack = scene.model_stack(textured=True)
    cond = scene.conditioning(image, stack)
    voxel = scene.structure(stack, cond, batch_size=1)
    shape_out = scene.shape(stack, cond, voxel, upsample=True, shape_steps=12)
    mesh = scene.texture(stack, shape_out)
    scene.save(mesh, "assets/objects/_lab-shot-prop/prop")
    graph = scene.root(
        stem="shot-to-prop",
        note=note,
        description="Guide still of a shot to textured TRELLIS.2 prop mesh. Upsample 1024.",
        lab_trellis={
            "unet": UNET,
            "resolution": UPSAMPLE_RESOLUTION,
            "stages": ["structure", "shape", "upsample", "texture"],
            "textured": True,
            "batch_size": 1,
            "save_prefix": "assets/objects/_lab-shot-prop/prop",
            "native_only": True,
        },
    )
    return _finish(graph, inputs=[("Guide still", "shot_id")], handoff=("3d/prop-variants",))


def build_prop_variants() -> dict[str, Any]:
    """Four candidate meshes from one still, inside a single occupancy session."""
    note = "\n\n".join(
        (
            "## 3d/prop-variants",
            "Klein still -> four candidate meshes in one queue, so prop exploration costs one "
            "occupancy session instead of four.",
            "Source: `LoadImage` with a Klein still (`ez_still_*.png` or a clay plate). "
            "`EmptyTrellis2LatentStructure` batch_size is 4 and the batch flows through every "
            "stage, so SaveGLB writes one .glb per batch item. SaveGLB takes the MESH directly "
            "here: MeshToFile3D keeps only batch item 0, which would silently drop 3 of the 4.",
            MODEL_LINES,
            "Upsample `target_resolution` is an int and ComfyUI only accepts 1024-2048 in steps of "
            "128; this graph runs the 1024 floor.",
            "SaveGLB writes four files to `output/assets/objects/_lab-variants/prop_NNNNN_.glb`. "
            "Do not mint an Asset Bible row from this graph.",
            DINO_LINE,
        )
    )
    scene = _Scene()
    scene.note(note)
    load = scene.add(
        "LoadImage",
        title="Klein still",
        outputs=[_out("IMAGE", "IMAGE"), _out("MASK", "MASK", slot=1)],
        widgets=["example.png", "image"],
        size=(320.0, 314.0),
    )
    image = _gate_and_unload(scene, load)
    stack = scene.model_stack(textured=True)
    cond = scene.conditioning(image, stack)
    voxel = scene.structure(stack, cond, batch_size=4)
    shape_out = scene.shape(stack, cond, voxel, upsample=True, shape_steps=12)
    mesh = scene.texture(stack, shape_out)
    scene.save(mesh, "assets/objects/_lab-variants/prop", batched=True)
    graph = scene.root(
        stem="prop-variants",
        note=note,
        description="Klein still to four textured TRELLIS.2 mesh candidates in one queue.",
        lab_trellis={
            "unet": UNET,
            "resolution": UPSAMPLE_RESOLUTION,
            "stages": ["structure", "shape", "upsample", "texture"],
            "textured": True,
            "batch_size": 4,
            "save_prefix": "assets/objects/_lab-variants/prop",
            "native_only": True,
        },
    )
    return _finish(graph, inputs=[("Klein still", "image")], handoff=())


def _finish(
    graph: dict[str, Any],
    *,
    inputs: list[tuple[str, str]],
    handoff: tuple[str, ...],
) -> dict[str, Any]:
    ensure_occupancy_note(graph, "trellis")
    stamp_app_mode(
        graph,
        inputs=inputs,
        outputs=["Save GLB"],
        lane="3d",
        occupancy="trellis",
        handoff=handoff,
        default_view="app",
        enhance_off_identity=True,
    )
    return apply_lab_completeness_flags(graph)


BUILDERS = {
    "3d/blockout-mesh": build_blockout,
    "3d/shot-to-prop": build_shot_to_prop,
    "3d/prop-variants": build_prop_variants,
}


def main() -> None:
    for stem, builder in BUILDERS.items():
        dest = lab_dest(stem, lane="3d")
        graph = builder()
        finalize_layout(graph)
        write_lab_graph(dest, graph)
        print(dest)


if __name__ == "__main__":
    main()
