"""TRELLIS-2 encyclopedia rows.

Helpers and combo catalogs live in :mod:`workflow_nodes_lib`.
"""

from __future__ import annotations

from typing import Any

from workflow_nodes_lib import _n, _s, _w

def trellis_nodes() -> dict[str, Any]:
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
                _s("voxel", "LATENT", "in", "Structure decode voxels."),
                _s("positive", "CONDITIONING", "out", "Pass-through."),
                _s("negative", "CONDITIONING", "out", "Pass-through."),
                _s("LATENT", "LATENT", "out", "Shape latent."),
            ],
        ),
        "Trellis2UpsampleStage": _n(
            "TRELLIS.2 Upsample Stage",
            "Upsample the shape latent toward 512.",
            lab="Lab widget 512. download-3d --tier trellis2.",
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
            widgets=[_w("resolution", index=0, typ="COMBO", rng="512", desc="Target structure resolution.", gen="512 is the lab INT8 mesh. Lower is faster and blockier.", choices=[("512", "Lab default."), ("256", "Faster, coarser.")])],
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
                _s("voxel", "LATENT", "out", "Voxel grid."),
            ],
            widgets=[_w("resolution", index=0, typ="COMBO", rng="32", desc="Voxel grid size.", gen="32 is the lab structure decode.", choices=[("32", "Lab default.")])],
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
                _s("voxel_colors", "VOXEL_COLORS", "out", "Colors for PaintMesh."),
            ],
        ),
        "PaintMesh": _n(
            "Paint Mesh",
            "Apply voxel colors onto the mesh.",
            origin="comfy-extras",
            sockets=[
                _s("mesh", "MESH", "in", "Shape mesh."),
                _s("voxel_colors", "VOXEL_COLORS", "in", "Decoded colors."),
                _s("mesh", "MESH", "out", "Painted mesh."),
            ],
        ),
        "MeshToFile3D": _n(
            "Mesh to File 3D",
            "Write a GLB/mesh file.",
            lab="optional/klein/trellis2 may leave the path empty (Comfy default). dcc/trellis/still-to-mesh writes assets/objects/_lab-mug/mesh.",
            origin="comfy-extras",
            sockets=[
                _s("mesh", "MESH", "in", "Painted mesh."),
                _s("model_3d", "MODEL_3D", "out", "File handle."),
            ],
            widgets=[],
            variants=[
                {
                    "widgets": [
                        _w("filename_prefix", index=0, desc="Output stem under the output folder.", gen="Lab mug pack uses assets/objects/_lab-mug/mesh."),
                    ]
                }
            ],
        )
    }
