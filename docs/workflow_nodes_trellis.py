"""TRELLIS-2 encyclopedia rows.

Helpers and combo catalogs live in :mod:`workflow_nodes_lib`.
"""

from __future__ import annotations


from workflow_nodes_lib import NodeSpecs, _n, _s, _w

def trellis_nodes() -> NodeSpecs:
    """TRELLIS-2 structure/texture/mesh nodes.

    Returns:
        Node specs keyed by type.
    """
    return {
        "Trellis2Conditioning": _n(
            "TRELLIS.2 Conditioning",
            "Encode a still with CLIP Vision into TRELLIS positive/negative.",
            origin="comfy-extras",
            sockets=[
                _s("clip_vision_model", "CLIP_VISION", "in", "DINOv3 ViT-L."),
                _s("image", "IMAGE", "in", "Klein still."),
                _s("positive", "CONDITIONING", "out", "Shape/texture positive."),
                _s("negative", "CONDITIONING", "out", "Negative."),
            ],
        ),
        "Trellis2ShapeStage": _n(
            "TRELLIS.2 Shape Stage",
            "Sample structure from a voxel latent.",
            origin="comfy-extras",
            sockets=[
                _s("positive", "CONDITIONING", "in", "Vision cond."),
                _s("negative", "CONDITIONING", "in", "Negative."),
                _s("voxel", "VOXEL", "in", "Structure decode voxels."),
                _s("positive", "CONDITIONING", "out", "Pass-through."),
                _s("negative", "CONDITIONING", "out", "Pass-through."),
                _s("LATENT", "LATENT", "out", "Shape latent."),
            ],
        ),
        "Trellis2UpsampleStage": _n(
            "TRELLIS.2 Upsample Stage",
            "Upsample the shape latent toward 1024.",
            lab="Lab queues the 1024 floor. download-3d --tier trellis2.",
            origin="comfy-extras",
            sockets=[
                _s("positive", "CONDITIONING", "in", "Cond."),
                _s("negative", "CONDITIONING", "in", "Cond."),
                _s("shape_latent", "LATENT", "in", "Shape latent."),
                _s("vae", "VAE", "in", "TRELLIS VAE."),
                _s("positive", "CONDITIONING", "out", "Cond."),
                _s("negative", "CONDITIONING", "out", "Cond."),
                _s("LATENT", "LATENT", "out", "Upsampled shape."),
            ],
            widgets=[_w("target_resolution", index=0, typ="INT", rng="1024-2048 step 128; lab 1024", desc="Structure resolution the upsampled shape stage renders at.", gen="ComfyUI accepts only 1024-2048 in steps of 128 and defaults to 1024; every lab 3D graph queues that floor. There is no 512 or 256 on this widget (the old lab note about 512 predates the rename).")],
        ),
        "Trellis2TextureStage": _n(
            "TRELLIS.2 Texture Stage",
            "Sample voxel colors for the mesh.",
            origin="comfy-extras",
            sockets=[
                _s("positive", "CONDITIONING", "in", "Cond."),
                _s("negative", "CONDITIONING", "in", "Cond."),
                _s("shape_latent", "LATENT", "in", "Shape."),
                _s("positive", "CONDITIONING", "out", "Cond."),
                _s("negative", "CONDITIONING", "out", "Cond."),
                _s("LATENT", "LATENT", "out", "Texture latent."),
            ],
        ),
        "VaeDecodeStructureTrellis2": _n(
            "TRELLIS.2 Decode Structure",
            "Decode structure latent to voxels.",
            origin="comfy-extras",
            sockets=[
                _s("samples", "LATENT", "in", "Structure latent."),
                _s("vae", "VAE", "in", "TRELLIS VAE."),
                _s("voxel", "VOXEL", "out", "Voxel grid."),
            ],
            widgets=[_w("resolution", index=0, typ="COMBO", rng="32 or 64; lab 32", desc="Voxel grid size.", gen="32 is the lab structure decode. 64 is the only other upstream option and is the finer grid.", choices=[("32", "Lab default."), ("64", "Finer voxel grid; slower.")])],
        ),
        "VaeDecodeShapeTrellis": _n(
            "TRELLIS Decode Shape",
            "Decode shape latent to a mesh.",
            origin="comfy-extras",
            sockets=[
                _s("samples", "LATENT", "in", "Shape latent."),
                _s("vae", "VAE", "in", "VAE."),
                _s("mesh", "MESH", "out", "Untextured mesh."),
                _s("shape_subdivides", "SHAPE_SUBDIVIDES", "out", "Subdivision payload for texture decode."),
            ],
        ),
        "VaeDecodeTextureTrellis": _n(
            "TRELLIS Decode Texture",
            "Decode texture latent to voxel colors.",
            origin="comfy-extras",
            sockets=[
                _s("samples", "LATENT", "in", "Texture latent."),
                _s("vae", "VAE", "in", "VAE."),
                _s("shape_subdivides", "SHAPE_SUBDIVIDES", "in", "From shape decode."),
                _s("voxel_colors", "VOXEL", "out", "Colors for PaintMesh."),
            ],
        ),
        "PaintMesh": _n(
            "Paint Mesh",
            "Apply voxel colors onto the mesh.",
            origin="comfy-extras",
            sockets=[
                _s("mesh", "MESH", "in", "Shape mesh."),
                _s("voxel_colors", "VOXEL", "in", "Decoded colors."),
                _s("mesh", "MESH", "out", "Painted mesh."),
            ],
        ),
        "MeshToFile3D": _n(
            "Mesh to File 3D",
            "Build the GLB payload in memory. No widgets; writes nothing.",
            lab="A graph must end MeshToFile3D -> SaveGLB to get a file on disk: this node only builds the payload, SaveGLB writes it.",
            origin="comfy-extras",
            sockets=[
                _s("mesh", "MESH", "in", "Painted mesh."),
                _s("model_3d", "FILE_3D_GLB", "out", "GLB payload for SaveGLB."),
            ],
            widgets=[],
            variants=[
                {
                    "widgets": [
                        _w("filename_prefix", index=0, desc="Not a widget on this node. Graphs authored before SaveGLB was split out still store a save prefix here; the node ignores it and writes nothing.", gen="3d/still-to-mesh keeps assets/objects/_lab-mug/mesh here. The live prefix lives on SaveGLB."),
                    ]
                }
            ],
        ),
        "SaveGLB": _n(
            "Save 3D Model",
            "Write the .glb under the output folder. Output node; no output sockets.",
            lab="3d/trellis2 uses prefix 3d/trellis2. The DCC pack graphs use assets/objects/_lab-<name>/<stem>. Needs MeshToFile3D upstream.",
            origin="comfy-extras",
            sockets=[
                _s("mesh", "MESH", "in", "MultiType socket: accepts MESH or any FILE_3D_* payload. Lab wires MeshToFile3D's model_3d into it."),
            ],
            widgets=[_w("filename_prefix", index=0, desc="Output stem under the ComfyUI output folder.", gen="3d/trellis2 lands the .glb under <output>/3d/, the DCC pack graphs under <output>/assets/objects/... The directory part of the prefix is created on demand. Hidden prompt and extra_pnginfo are injected by the backend and are not widgets.")],
        )
    }
