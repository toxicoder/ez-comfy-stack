#!/usr/bin/env python3
"""Build the 3d-lane Studio Apps.

Seven TRELLIS.2 printers ship from here: blockout, shot-to-prop, prop-variants,
hero-from-photos, multi-image-asset, character-batch, and world-elements. The
eighth App, set-dressing, prints nothing: it writes the ``scene.json`` that
places the assets the printers minted.

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

# App Mode help text for the knobs the lane wants on the front page. Written once
# here so every 3d App describes the same widget the same way.
RESOLUTION_HELP = (
    "Structure resolution the refined shape stage renders at. ComfyUI accepts only "
    "1024-2048 in steps of 128; 1024 is the floor and the lab default."
)
TEXTURE_HELP = (
    "Steps on the texture sampler. 12 is the authored pass; 4-6 is a paint draft "
    "before you commit the full pass. The mesh geometry does not change."
)
PREFIX_HELP = (
    "Output stem under the ComfyUI output folder. Keep the assets/objects/_lab-... "
    "convention so the mesh lands in the one tree the catalog and the Blender "
    "exporter walk."
)
BATCH_HELP = (
    "Meshes per Queue. SaveGLB writes one .glb per batch item, so the whole set "
    "comes off one occupancy session."
)
SHAPE_STEPS_HELP = (
    "Steps on the structure-refinement sampler. A proxy reads fine at 8; 12 is the "
    "authored pass for a deliverable."
)


def _image_input(title: str, *, label: str, description: str) -> tuple[str, str, dict[str, str]]:
    """One ``LoadImage`` App row: the node's ``image`` picker with operator text."""
    return (title, "image", {"label": label, "description": description})


def _resolution_input() -> tuple[str, str, dict[str, str]]:
    """The upsample stage's ``target_resolution`` as an App row."""
    return (
        "Upsample 1024",
        "target_resolution",
        {"label": "Upsample resolution", "description": RESOLUTION_HELP},
    )


def _texture_input() -> tuple[str, str, dict[str, str]]:
    """The texture sampler's ``steps`` as an App row."""
    return (
        "KSampler (texture)",
        "steps",
        {"label": "Texture pass", "description": TEXTURE_HELP},
    )


def _prefix_input() -> tuple[str, str, dict[str, str]]:
    """The ``SaveGLB`` ``filename_prefix`` as an App row."""
    return ("Save GLB", "filename_prefix", {"label": "Save prefix", "description": PREFIX_HELP})


def _batch_input() -> tuple[str, str, dict[str, str]]:
    """The structure latent's ``batch_size`` as an App row (batched Apps only)."""
    return (
        "EmptyTrellis2LatentStructure",
        "batch_size",
        {"label": "Batch", "description": BATCH_HELP},
    )


def _shape_steps_input() -> tuple[str, str, dict[str, str]]:
    """The shape sampler's ``steps`` as an App row."""
    return ("KSampler (shape)", "steps", {"label": "Shape steps", "description": SHAPE_STEPS_HELP})


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

    def conditioning(
        self, image: dict[str, Any], stack: dict[str, dict[str, Any]], *, title: str = "Trellis2 conditioning"
    ) -> dict[str, Any]:
        cond = self.add(
            "Trellis2Conditioning",
            title=title,
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
        upsample_cond: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        """Voxel grid -> shape stage -> optional upsample -> decoded mesh.

        Returns the decoded shape node, the conditioning source the texture
        stage must reuse (the upsample stage when it ran, the shape stage when
        it did not), and the sampler holding the refined shape latent.

        ``upsample_cond`` lets a multi-view App drive the upsample stage from a
        different view's ``Trellis2Conditioning`` than the shape stage reads;
        unset, the upsample stage inherits the shape stage's conditioning.
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
            self.wire(upsample_cond or shape_stage, 0, up, 0, "CONDITIONING")
            self.wire(upsample_cond or shape_stage, 1, up, 1, "CONDITIONING")
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
        *,
        cond: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Reuse the refined conditioning to paint the decoded mesh.

        ``cond`` lets a multi-view App paint from another view's conditioning
        (the world-elements ground plate, for example); unset, the pass reuses
        the conditioning the refined shape stage ran on.
        """
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
        paint_cond = cond or cond_src
        self.wire(paint_cond, 0, tex_stage, 0, "CONDITIONING")
        self.wire(paint_cond, 1, tex_stage, 1, "CONDITIONING")
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

    def root(
        self,
        *,
        stem: str,
        note: str,
        description: str,
        lab_trellis: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        extra: dict[str, Any] = {
            "lab_note": note,
            "lab_profile": f"3d/{stem}",
            "lab_description": description,
        }
        if lab_trellis is not None:
            extra["lab_trellis"] = lab_trellis
        return {
            "id": stem,
            "revision": 1,
            "last_node_id": max(int(node["id"]) for node in self.nodes),
            "last_link_id": self.wires.last_link_id,
            "nodes": self.nodes,
            "links": self.wires.links,
            "groups": [],
            "config": {},
            "extra": extra,
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
    return _finish(
        graph,
        inputs=[
            (
                "Still pack plate",
                "plate",
                {
                    "label": "Plate",
                    "description": (
                        "Which plate of the still pack the blockout is printed from. "
                        "The pack slug and the layer stay on the node."
                    ),
                },
            ),
            _shape_steps_input(),
            _prefix_input(),
        ],
        handoff=("3d/trellis2",),
    )


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
    return _finish(
        graph,
        inputs=[
            (
                "Guide still",
                "slug",
                {
                    "label": "Shot pack",
                    "description": (
                        "Which DCC shot pack the guide still comes out of. Set it with "
                        "Shot id below, then check the preview before you Queue."
                    ),
                },
            ),
            (
                "Guide still",
                "shot_id",
                {
                    "label": "Shot id",
                    "description": (
                        "Shot whose hero object becomes the prop. The guide still of this "
                        "shot is what TRELLIS.2 conditions on."
                    ),
                },
            ),
            (
                "Guide still",
                "layer",
                {
                    "label": "Guide layer",
                    "description": (
                        "Which guide layer of the shot becomes the prop. The preview node "
                        "draws this same layer before the queue spends GPU."
                    ),
                },
            ),
            _resolution_input(),
            _texture_input(),
            _prefix_input(),
        ],
        handoff=("3d/prop-variants",),
    )


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
    return _finish(
        graph,
        inputs=[
            _image_input(
                "Klein still",
                label="Klein still",
                description=(
                    "Still already in input/ (the container inputs folder). Every batch "
                    "item is printed from this one plate, so candidates differ by seed, "
                    "not by source."
                ),
            ),
            _batch_input(),
            _resolution_input(),
            _texture_input(),
            _prefix_input(),
        ],
        handoff=(),
    )


def build_hero_from_photos() -> dict[str, Any]:
    """One plate -> one fully textured, upsampled hero mesh."""
    note = "\n\n".join(
        (
            "## 3d/hero-from-photos",
            "One Klein still -> one textured hero mesh: structure, shape, the 1024 upsample, "
            "then the texture pass paints the geometry. This is the entry point of the lane "
            "when you have a single good plate and want a single good asset.",
            "Source: `LoadImage` with a Klein still (`ez_still_*.png` or a clay plate). The "
            "App row exposes the source image, the upsample `target_resolution`, the texture "
            "pass steps, and the `SaveGLB` prefix, so a Run can be retuned without opening "
            "the graph.",
            MODEL_LINES,
            "Upsample `target_resolution` is an int and ComfyUI only accepts 1024-2048 in steps of "
            "128; this graph runs the 1024 floor.",
            "Batch stays 1 and the mesh converts through MeshToFile3D, which keeps only batch "
            "item 0 - raise the batch on `3d/character-batch` instead. SaveGLB writes the mesh to "
            "`output/assets/objects/_lab-hero/hero_NNNNN_.glb`; MeshToFile3D only converts in "
            "memory. Do not mint an Asset Bible row from this graph.",
            "Queue `3d/multi-image-asset` when one plate is not enough and the object needs "
            "several views fused.",
            DINO_LINE,
        )
    )
    scene = _Scene()
    scene.note(note)
    load = scene.add(
        "LoadImage",
        title="Hero still",
        outputs=[_out("IMAGE", "IMAGE"), _out("MASK", "MASK", slot=1)],
        widgets=["example.png", "image"],
        size=(320.0, 314.0),
    )
    image = _gate_and_unload(scene, load)
    stack = scene.model_stack(textured=True)
    cond = scene.conditioning(image, stack)
    voxel = scene.structure(stack, cond, batch_size=1)
    shape_out = scene.shape(stack, cond, voxel, upsample=True, shape_steps=12)
    mesh = scene.texture(stack, shape_out)
    scene.save(mesh, "assets/objects/_lab-hero/hero")
    graph = scene.root(
        stem="hero-from-photos",
        note=note,
        description="One Klein still to one textured TRELLIS.2 hero mesh. Upsample 1024.",
        lab_trellis={
            "unet": UNET,
            "resolution": UPSAMPLE_RESOLUTION,
            "stages": ["structure", "shape", "upsample", "texture"],
            "textured": True,
            "batch_size": 1,
            "save_prefix": "assets/objects/_lab-hero/hero",
            "native_only": True,
        },
    )
    return _finish(
        graph,
        inputs=[
            _image_input(
                "Hero still",
                label="Hero still",
                description=(
                    "Still already in input/ (the container inputs folder). The one plate "
                    "this asset is printed from - pick the cleanest view you have."
                ),
            ),
            _resolution_input(),
            _texture_input(),
            _prefix_input(),
        ],
        handoff=("3d/multi-image-asset",),
    )


def build_multi_image_asset() -> dict[str, Any]:
    """Four views of one object fused into a single textured mesh."""
    note = "\n\n".join(
        (
            "## 3d/multi-image-asset",
            "Four stills of one object (front, side, back, top-down) -> one textured mesh, "
            "so an asset is fused from several views instead of hallucinated from one.",
            "Sources: four `LoadImage` nodes, each gated, unloaded, and run through its own "
            "`Trellis2Conditioning`. The four views share ONE `Trellis2ShapeStage`: the front "
            "view conditions the structure stage, the side view the shape stage, the back view "
            "the upsample stage, and the top-down view the texture pass. Four shape stages "
            "would be four separate meshes, so the lane fuses inside one.",
            MODEL_LINES,
            "Upsample `target_resolution` is an int and ComfyUI only accepts 1024-2048 in steps of "
            "128; this graph runs the 1024 floor.",
            "Batch stays 1 and the mesh converts through MeshToFile3D, which keeps only batch "
            "item 0. SaveGLB writes the mesh to "
            "`output/assets/objects/_lab-multiview/asset_NNNNN_.glb`; MeshToFile3D only converts "
            "in memory. Do not mint an Asset Bible row from this graph.",
            "Queue `3d/world-elements` next to place the fused asset in a set.",
            DINO_LINE,
        )
    )
    scene = _Scene()
    scene.note(note)
    stack = scene.model_stack(textured=True)
    view_keys = ("front", "side", "back", "top-down")
    view_labels = {
        "front": "Front view",
        "side": "Side view",
        "back": "Back view",
        "top-down": "Top-down view",
    }
    view_help = {
        "front": (
            "Still already in input/. The face of the object: it conditions the structure "
            "stage, so the voxel grid follows this view."
        ),
        "side": (
            "Still already in input/. 90 degrees round from the front; it conditions the "
            "shape stage that refines the geometry."
        ),
        "back": (
            "Still already in input/. Opposite the front; it conditions the upsample stage, "
            "so the refined detail agrees with this side."
        ),
        "top-down": (
            "Still already in input/. Looked down on from above; it conditions the texture "
            "pass that paints the mesh."
        ),
    }
    conds: dict[str, dict[str, Any]] = {}
    for key in view_keys:
        load = scene.add(
            "LoadImage",
            title=view_labels[key],
            outputs=[_out("IMAGE", "IMAGE"), _out("MASK", "MASK", slot=1)],
            widgets=["example.png", "image"],
            size=(320.0, 314.0),
        )
        image = _gate_and_unload(scene, load)
        conds[key] = scene.conditioning(image, stack, title=f"Conditioning ({key})")
    voxel = scene.structure(stack, conds["front"], batch_size=1)
    shape_out = scene.shape(
        stack,
        conds["side"],
        voxel,
        upsample=True,
        shape_steps=12,
        upsample_cond=conds["back"],
    )
    mesh = scene.texture(stack, shape_out, cond=conds["top-down"])
    scene.save(mesh, "assets/objects/_lab-multiview/asset")
    graph = scene.root(
        stem="multi-image-asset",
        note=note,
        description="Four views of one object fused into one textured TRELLIS.2 mesh.",
        lab_trellis={
            "unet": UNET,
            "resolution": UPSAMPLE_RESOLUTION,
            "stages": ["structure", "shape", "upsample", "texture"],
            "textured": True,
            "batch_size": 1,
            "save_prefix": "assets/objects/_lab-multiview/asset",
            "native_only": True,
        },
    )
    return _finish(
        graph,
        inputs=[
            _image_input("Front view", label="Front view", description=view_help["front"]),
            _image_input("Side view", label="Side view", description=view_help["side"]),
            _image_input("Back view", label="Back view", description=view_help["back"]),
            _image_input("Top-down view", label="Top-down view", description=view_help["top-down"]),
            _resolution_input(),
            _texture_input(),
            _prefix_input(),
        ],
        handoff=("3d/world-elements",),
    )


def build_character_batch() -> dict[str, Any]:
    """Four candidate characters off one plate, inside a single occupancy session."""
    note = "\n\n".join(
        (
            "## 3d/character-batch",
            "Klein still -> four textured candidate characters in one queue, so a cast call "
            "costs one occupancy session instead of four.",
            "Source: `LoadImage` with a Klein still (`ez_still_*.png` or a clay plate). "
            "`EmptyTrellis2LatentStructure` batch_size is 4 and the batch flows through every "
            "stage, so SaveGLB writes one .glb per candidate. SaveGLB takes the MESH directly "
            "here: MeshToFile3D keeps only batch item 0, which would silently drop 3 of the 4.",
            MODEL_LINES,
            "Upsample `target_resolution` is an int and ComfyUI only accepts 1024-2048 in steps of "
            "128; this graph runs the 1024 floor.",
            "SaveGLB writes four files to `output/assets/objects/_lab-characters/character_NNNNN_.glb`. "
            "Do not mint an Asset Bible row from this graph.",
            DINO_LINE,
        )
    )
    scene = _Scene()
    scene.note(note)
    load = scene.add(
        "LoadImage",
        title="Character sheet",
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
    scene.save(mesh, "assets/objects/_lab-characters/character", batched=True)
    graph = scene.root(
        stem="character-batch",
        note=note,
        description="Klein still to four textured TRELLIS.2 character candidates in one queue.",
        lab_trellis={
            "unet": UNET,
            "resolution": UPSAMPLE_RESOLUTION,
            "stages": ["structure", "shape", "upsample", "texture"],
            "textured": True,
            "batch_size": 4,
            "save_prefix": "assets/objects/_lab-characters/character",
            "native_only": True,
        },
    )
    return _finish(
        graph,
        inputs=[
            _image_input(
                "Character sheet",
                label="Character sheet",
                description=(
                    "Still already in input/ (the container inputs folder). Every candidate "
                    "is printed from this one plate, so the four differ by seed, not by "
                    "source."
                ),
            ),
            _batch_input(),
            _resolution_input(),
            _texture_input(),
            _prefix_input(),
        ],
        handoff=(),
    )


def build_world_elements() -> dict[str, Any]:
    """One textured prop mesh plus the ground plate its paint reads."""
    note = "\n\n".join(
        (
            "## 3d/world-elements",
            "Prop still -> one textured .glb, painted against a ground plate so the asset "
            "matches the surface it is going to sit on.",
            "A world in this stack is a set of instanced `.glb` assets plus a `scene.json` "
            "layout composed off-line. This graph writes one prop .glb per Run: you instance "
            "it and place the instances in that layout. This stack produces no gaussian splat "
            "and no captured point cloud - only meshes.",
            "Sources: `LoadImage` prop source (structure, shape, and upsample) and `LoadImage` "
            "ground plate (the texture pass). Each is gated and unloaded on its own way into "
            "the graph, and each runs through its own `Trellis2Conditioning`.",
            MODEL_LINES,
            "Upsample `target_resolution` is an int and ComfyUI only accepts 1024-2048 in steps of "
            "128; this graph runs the 1024 floor.",
            "Batch stays 1 and the mesh converts through MeshToFile3D, which keeps only batch "
            "item 0. SaveGLB writes the mesh to "
            "`output/assets/objects/_lab-world/element_NNNNN_.glb`; MeshToFile3D only converts in "
            "memory. Do not mint an Asset Bible row from this graph.",
            "`Compose scene layout` is the second half of this Queue: it writes the "
            "`scene.json` that instances the `.glb` slugs already in the Asset Bible, "
            "with their placement and one camera, under `output/scenes/`. Its `assets` "
            "box takes one slug per line, so you place the set once and refine the "
            "rows in the DCC. Blender or a host viewer assembles the scene from that "
            "document - see the Blender desk.",
            "`3d/set-dressing` is the App on the handoff: it composes the whole set "
            "at once, every slug you have printed, with no mesh printed again.",
            DINO_LINE,
        )
    )
    scene = _Scene()
    scene.note(note)
    stack = scene.model_stack(textured=True)
    prop_load = scene.add(
        "LoadImage",
        title="Prop source",
        outputs=[_out("IMAGE", "IMAGE"), _out("MASK", "MASK", slot=1)],
        widgets=["example.png", "image"],
        size=(320.0, 314.0),
    )
    prop_image = _gate_and_unload(scene, prop_load)
    cond_prop = scene.conditioning(prop_image, stack, title="Conditioning (prop)")
    plate_load = scene.add(
        "LoadImage",
        title="Ground plate",
        outputs=[_out("IMAGE", "IMAGE"), _out("MASK", "MASK", slot=1)],
        widgets=["example.png", "image"],
        size=(320.0, 314.0),
    )
    plate_image = _gate_and_unload(scene, plate_load)
    cond_plate = scene.conditioning(plate_image, stack, title="Conditioning (ground plate)")
    voxel = scene.structure(stack, cond_prop, batch_size=1)
    shape_out = scene.shape(stack, cond_prop, voxel, upsample=True, shape_steps=12)
    mesh = scene.texture(stack, shape_out, cond=cond_plate)
    scene.save(mesh, "assets/objects/_lab-world/element")
    # The layout half of the world lives in this graph, so the operator queues
    # the mesh and the scene.json document in one visit to the trellis lane.
    scene.add(
        "EZSceneLayout",
        title="Compose scene layout",
        outputs=[_out("scene", "STRING"), _out("summary", "STRING", slot=1)],
        widgets=[
            "lab-world",
            "hero-olive-jacket\nmug-cobalt-chipped",
            "2.1, 1.6, 3.4",
            "0, 1.2, 0",
            35,
            "none",
            "world-elements",
            False,
        ],
        size=(360.0, 330.0),
    )
    graph = scene.root(
        stem="world-elements",
        note=note,
        description="Prop still plus a ground plate to one textured TRELLIS.2 .glb for a set.",
        lab_trellis={
            "unet": UNET,
            "resolution": UPSAMPLE_RESOLUTION,
            "stages": ["structure", "shape", "upsample", "texture"],
            "textured": True,
            "batch_size": 1,
            "save_prefix": "assets/objects/_lab-world/element",
            "native_only": True,
        },
    )
    return _finish(
        graph,
        inputs=[
            _image_input(
                "Prop source",
                label="Prop source",
                description=(
                    "Still already in input/ (the container inputs folder). The prop whose "
                    "geometry this Run prints."
                ),
            ),
            _image_input(
                "Ground plate",
                label="Ground plate",
                description=(
                    "Still already in input/. The surface the prop will sit on: the texture "
                    "pass is conditioned on it so the paint matches the real ground."
                ),
            ),
            _resolution_input(),
            _texture_input(),
            _prefix_input(),
            _shape_steps_input(),
            (
                "Compose scene layout",
                "assets",
                {
                    "label": "Scene assets",
                    "description": (
                        "One Asset Bible slug per line. The layout document instances "
                        "these slugs; an unknown slug leaves the file unwritten and the "
                        "summary line says why."
                    ),
                },
            ),
            (
                "Compose scene layout",
                "camera_pos",
                {
                    "label": "Camera position",
                    "description": (
                        '"x, y, z" in metres. Blank falls back to the camera default '
                        "in schemas/scene.json."
                    ),
                },
            ),
            (
                "Compose scene layout",
                "hdri",
                {
                    "label": "HDRI",
                    "description": (
                        "polyhaven:<name> or none. The document records the lighting "
                        "reference the DCC loads; none keeps the viewer's default."
                    ),
                },
            ),
        ],
        handoff=("3d/set-dressing",),
        outputs=("Save GLB", "Compose scene layout"),
        optional_unwired=("EZSceneLayout",),
    )


def build_set_dressing() -> dict[str, Any]:
    """Asset Bible slugs -> one scene.json layout: the world half with no GPU."""
    note = "\n\n".join(
        (
            "## 3d/set-dressing",
            "Asset Bible slugs -> one `scene.json` shopping list: where each `.glb` "
            "stands, how it is turned, how big, plus one camera and one lighting "
            "reference.",
            "A world in this stack is instanced `.glb` assets plus this document, "
            "assembled off-line in Blender or a host viewer. This graph prints no "
            "mesh and loads no model, so it costs no GPU time and queues beside a "
            "running trellis job. This stack mints no gaussian splat and no "
            "captured point cloud.",
            "`Compose scene layout` writes `output/scenes/<filename>_NNNNN.json` "
            "against `schemas/scene.json`, never `${MODELS_DIR}`. The counter suffix "
            "keeps a re-Queue from clobbering the draft you are editing; `overwrite` "
            "is the only way to replace a file.",
            "`assets` takes one Asset Bible slug per line, optionally "
            "`slug:relative/path.glb`. An unknown slug, a path outside the bible, a "
            "`scene_id` that is not lowercase-hyphenated, or a camera part that is "
            "not a number leaves the file unwritten and the summary line says why: "
            "the App fails soft rather than raising on the canvas.",
            "Print the slugs you list first - `3d/world-elements` for a prop that "
            "must match its ground, `3d/hero-from-photos` for a hero asset. The "
            "document is a shopping list, and a slug nobody printed shows up in the "
            "DCC as an empty row.",
        )
    )
    scene = _Scene()
    scene.note(note)
    scene.add(
        "EZSceneLayout",
        title="Compose scene layout",
        outputs=[_out("scene", "STRING"), _out("summary", "STRING", slot=1)],
        widgets=[
            "lab-set",
            "hero-olive-jacket\nmug-cobalt-chipped",
            "2.1, 1.6, 3.4",
            "0, 1.2, 0",
            35,
            "none",
            "set-dressing",
            False,
        ],
        size=(380.0, 360.0),
        pos=(820.0, 40.0),
    )
    graph = scene.root(
        stem="set-dressing",
        note=note,
        description="Asset Bible slugs to one scene.json layout: instances, camera, and HDRI.",
    )
    return _finish(
        graph,
        inputs=[
            (
                "Compose scene layout",
                "scene_id",
                {
                    "label": "Scene id",
                    "description": (
                        "Lowercase words joined by single hyphens. It names the set "
                        "inside the document; anything else refuses the write."
                    ),
                },
            ),
            (
                "Compose scene layout",
                "assets",
                {
                    "label": "Scene assets",
                    "description": (
                        "One Asset Bible slug per line, optionally "
                        "slug:relative/path.glb. The document instances these slugs; "
                        "an unknown slug leaves the file unwritten and the summary "
                        "line says why."
                    ),
                },
            ),
            (
                "Compose scene layout",
                "camera_pos",
                {
                    "label": "Camera position",
                    "description": (
                        '"x, y, z" in metres. Blank falls back to the camera default '
                        "in schemas/scene.json."
                    ),
                },
            ),
            (
                "Compose scene layout",
                "camera_look",
                {
                    "label": "Camera look-at",
                    "description": (
                        '"x, y, z" in metres. The point the camera aims at. Blank '
                        "falls back to the schema default."
                    ),
                },
            ),
            (
                "Compose scene layout",
                "camera_fov",
                {
                    "label": "Camera FOV",
                    "description": (
                        "Vertical field of view in degrees, 10-120. 35 is the "
                        "authored default; go wide to read a whole room."
                    ),
                },
            ),
            (
                "Compose scene layout",
                "hdri",
                {
                    "label": "HDRI",
                    "description": (
                        "polyhaven:<name> or none. The document records the lighting "
                        "reference the DCC loads; none keeps the viewer's default."
                    ),
                },
            ),
            (
                "Compose scene layout",
                "filename",
                {
                    "label": "Scene filename",
                    "description": (
                        "Basename under output/scenes/. The file lands as "
                        "<filename>_NNNNN.json so a re-Queue keeps your last draft."
                    ),
                },
            ),
        ],
        handoff=(),
        outputs=("Compose scene layout",),
        occupancy="none",
        optional_unwired=("EZSceneLayout",),
    )


def _finish(
    graph: dict[str, Any],
    *,
    inputs: list[tuple[str, str] | tuple[str, str, dict[str, str]]],
    handoff: tuple[str, ...],
    outputs: tuple[str, ...] = ("Save GLB",),
    occupancy: str = "trellis",
    optional_unwired: tuple[str, ...] = (),
) -> dict[str, Any]:
    ensure_occupancy_note(graph, occupancy)
    if optional_unwired:
        # A terminal OUTPUT_NODE with no sockets to wire: it takes its widgets
        # and writes the document, so the isolate rule does not apply to it.
        graph.setdefault("extra", {})["lab_optional_unwired"] = sorted(
            set(graph["extra"].get("lab_optional_unwired") or []) | set(optional_unwired)
        )
    stamp_app_mode(
        graph,
        inputs=inputs,
        outputs=list(outputs),
        lane="3d",
        occupancy=occupancy,
        handoff=handoff,
        default_view="app",
        enhance_off_identity=True,
    )
    return apply_lab_completeness_flags(graph)


BUILDERS = {
    "3d/blockout-mesh": build_blockout,
    "3d/shot-to-prop": build_shot_to_prop,
    "3d/prop-variants": build_prop_variants,
    "3d/hero-from-photos": build_hero_from_photos,
    "3d/multi-image-asset": build_multi_image_asset,
    "3d/character-batch": build_character_batch,
    "3d/world-elements": build_world_elements,
    "3d/set-dressing": build_set_dressing,
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
