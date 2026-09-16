"""ComfyUI node: global Quality combo for lab graphs."""

from __future__ import annotations

from typing import Any

from .presets import QUALITY_CHOICES, QUALITY_LAB, normalize_quality

CATEGORY = "ez-comfy"


class EZQuality:
    """Hold the workflow-global Quality combo. JS applies family overlays."""

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "quality": (list(QUALITY_CHOICES), {"default": QUALITY_LAB}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("quality",)
    FUNCTION = "report"
    CATEGORY = CATEGORY
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Lab default, Draft (faster), or High (slower). "
        "Family-specific overlays on steps, CFG, and Klein 4B UNET. "
        "Not --tier quality. Never selects banned weights. "
        "High on Klein base needs download-image --tier base."
    )

    def report(self, quality: str) -> dict[str, Any]:
        choice = normalize_quality(quality)
        return {
            "ui": {"text": (choice,)},
            "result": (choice,),
        }


NODE_CLASS_MAPPINGS: dict[str, type] = {
    "EZQuality": EZQuality,
}
NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {
    "EZQuality": "Quality",
}
