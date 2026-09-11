"""ComfyUI nodes: load host Blender guide packs, gate occupancy."""

from __future__ import annotations

import json
from typing import Any

from . import pack as dcc_pack
from .occupancy_gate import HEAVY_MODES, check_occupancy
from .pack import (
    SHOT_STILL_LAYERS,
    SHOT_VIDEO_LAYERS,
    STILL_PACK_LAYERS,
    camera_json_path,
    shot_dir,
    shot_still_path,
    shot_video_path,
    still_dir,
    still_pack_path,
)
from .qc import (
    load_shot,
    load_still,
    raise_defects,
    require_file,
    validate_pack,
    validate_still_pack,
)

CATEGORY = "ez-comfy/dcc"


class EZDCCLoadGuideStill:
    """Load one still layer from ``guides/<slug>/<shot_id>/``."""

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "slug": ("STRING", {"default": "go-see"}),
                "shot_id": ("STRING", {"default": "12"}),
                "layer": (list(SHOT_STILL_LAYERS), {"default": "first"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("image", "mask", "metadata")
    FUNCTION = "run"
    CATEGORY = CATEGORY
    DESCRIPTION = (
        "Load clay/depth/canny/first/last from a host guide pack. "
        "Fail-closed QC. Depth stays mist 0-1 (near=white, far=black)."
    )

    def run(self, slug: str, shot_id: str, layer: str) -> tuple[Any, Any, str]:
        pack = shot_dir(slug, shot_id)
        raise_defects(validate_pack(pack, require_full_seq=False))
        path = require_file(shot_still_path(pack, layer), label=f"{layer} still")
        image, mask = dcc_pack.decode_png(path)
        meta = json.dumps(load_shot(pack), default=str)
        return image, mask, meta


class EZDCCLoadGuideVideo:
    """Return the absolute mp4 path for a guide-pack video layer. No frame decode."""

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "slug": ("STRING", {"default": "go-see"}),
                "shot_id": ("STRING", {"default": "12"}),
                "layer": (list(SHOT_VIDEO_LAYERS), {"default": "clay"}),
            }
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("path", "fps")
    FUNCTION = "run"
    CATEGORY = CATEGORY
    DESCRIPTION = (
        "Absolute clay.mp4 / depth.mp4 / canny.mp4 path at 24 fps. "
        "Does not decode 120 frames in Python."
    )

    def run(self, slug: str, shot_id: str, layer: str) -> tuple[str, int]:
        pack = shot_dir(slug, shot_id)
        raise_defects(validate_pack(pack, require_full_seq=False))
        path = require_file(shot_video_path(pack, layer), label=f"{layer}.mp4")
        return str(path.resolve()), 24


class EZDCCLoadStillPack:
    """Load one layer from ``guides/<slug>/stills/<plate>/`` (ez.guide.still.v1)."""

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "slug": ("STRING", {"default": "go-see"}),
                "plate": ("STRING", {"default": "mug"}),
                "layer": (list(STILL_PACK_LAYERS), {"default": "first"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("image", "mask", "metadata")
    FUNCTION = "run"
    CATEGORY = CATEGORY
    DESCRIPTION = (
        "Load a blender-stills plate. Allowed sizes match guide_pack.STILL_SIZES."
    )

    def run(self, slug: str, plate: str, layer: str) -> tuple[Any, Any, str]:
        pack = still_dir(slug, plate)
        raise_defects(validate_still_pack(pack))
        path = require_file(still_pack_path(pack, layer), label=f"{layer} still")
        image, mask = dcc_pack.decode_png(path)
        meta = json.dumps(load_still(pack), default=str)
        return image, mask, meta


class EZDCCCameraJson:
    """Load ``camera.json`` as STRING. Empty string if missing. No CAMERA socket."""

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "slug": ("STRING", {"default": "go-see"}),
                "shot_id": ("STRING", {"default": "12"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("camera_json",)
    FUNCTION = "run"
    CATEGORY = CATEGORY
    DESCRIPTION = "Optional camera.json from the shot pack. Missing file → empty string."

    def run(self, slug: str, shot_id: str) -> tuple[str]:
        path = camera_json_path(slug, shot_id)
        if not path.is_file():
            return ("",)
        return (path.read_text(encoding="utf-8"),)


class EZDCCPreviewGuideLayer:
    """Identity IMAGE pass-through with a label."""

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "image": ("IMAGE",),
                "label": ("STRING", {"default": "guide"}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "run"
    CATEGORY = CATEGORY
    DESCRIPTION = "Identity pass-through so a guide layer can sit on the canvas."

    def run(self, image: object, label: str = "guide") -> tuple[object]:
        _ = label
        return (image,)


class EZDCCOccupancyGate:
    """Pass-through IMAGE that fail-closes on occupancy XOR."""

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "image": ("IMAGE",),
                "required_mode": (list(HEAVY_MODES), {"default": "klein"}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "run"
    CATEGORY = CATEGORY
    DESCRIPTION = (
        "Read .occupancy.json. Missing file passes. blender-desk vs a heavy "
        "mode fails. Does not start Compose or spawn Blender."
    )

    def run(self, image: object, required_mode: str) -> tuple[object]:
        check_occupancy(required_mode)
        return (image,)


NODE_CLASS_MAPPINGS = {
    "EZDCCLoadGuideStill": EZDCCLoadGuideStill,
    "EZDCCLoadGuideVideo": EZDCCLoadGuideVideo,
    "EZDCCLoadStillPack": EZDCCLoadStillPack,
    "EZDCCCameraJson": EZDCCCameraJson,
    "EZDCCPreviewGuideLayer": EZDCCPreviewGuideLayer,
    "EZDCCOccupancyGate": EZDCCOccupancyGate,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EZDCCLoadGuideStill": "Load guide still",
    "EZDCCLoadGuideVideo": "Load guide video path",
    "EZDCCLoadStillPack": "Load still pack",
    "EZDCCCameraJson": "Load camera.json",
    "EZDCCPreviewGuideLayer": "Preview guide layer",
    "EZDCCOccupancyGate": "Occupancy gate",
}

# Re-export for tests that mention the QC exception next to nodes.
__all__ = [
    "EZDCCCameraJson",
    "EZDCCLoadGuideStill",
    "EZDCCLoadGuideVideo",
    "EZDCCLoadStillPack",
    "EZDCCOccupancyGate",
    "EZDCCPreviewGuideLayer",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
