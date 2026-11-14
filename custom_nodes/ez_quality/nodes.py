"""ComfyUI node: global Detail combo for lab graphs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .check import STATUS_DEFAULT
from .presets import QUALITY_DEFAULT, QUALITY_CHOICES, normalize_quality

if TYPE_CHECKING:
    from ez_common import ComfyInputTypes

# Comfy menu category for the Detail node.
CATEGORY = "ez-comfy"


class EZQuality:
    """Hold the workflow-global Detail combo. JS applies family rungs."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for this node.

        Returns:
            Required widget map (the Detail rung).
        """
        return {
            "required": {
                "quality": (list(QUALITY_CHOICES), {"default": QUALITY_DEFAULT}),
            }
        }

    # Comfy node contract.
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("quality",)
    FUNCTION = "report"
    CATEGORY = CATEGORY
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Three rungs. draft is the quick look, standard is what this App ships "
        "tuned for, final is the best this App's own stack can do. standard "
        "writes nothing on any family, so the graph keeps exactly what it was "
        "authored with. "
        "Klein: draft 4 steps CFG 1.0 on the NVFP4 UNET, final 24 steps CFG 3.5 "
        "on the base FP8 UNET - Apache-2.0. Wan / LTX / film / audio / trellis "
        "write steps only, and trellis writes the guided stages only. "
        "Never changes size: no rung touches a width, height, frames, length, "
        "or EZImageFormat widget. "
        "A rung writes only its own family's weights, and an apply where any "
        "write cannot land is refused whole - nothing is renamed and no weight "
        "is substituted. The caption names the live stack, steps, CFG, and "
        "license, and says Edited when the widgets left the rung behind. "
        "Opt-in FLUX 3 Image Klein graphs are FLUX Non-Commercial; opt-in "
        "Qwen-Image 2.1 graphs are the Qwen Research license; standard writes "
        "nothing on those either. "
        "Not --tier quality."
    )

    def report(self, quality: str) -> dict[str, Any]:
        """Normalize the Detail combo for UI and downstream STRING.

        Args:
            quality: Detail widget value, or an accepted legacy tier id.

        Returns:
            Comfy output-node payload with the normalized rung id.
        """
        choice = normalize_quality(quality)
        return {
            "ui": {"text": (choice,)},
            "result": (choice,),
        }


class EZModelCheck:
    """Manual disk check for occupancy + Quality weights. Queue skips it."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for this node.

        Returns:
            Required status STRING (JS overwrites after Check models).
        """
        return {
            "required": {
                "status": (
                    "STRING",
                    {
                        "default": STATUS_DEFAULT,
                        "multiline": True,
                        "dynamicPrompts": False,
                    },
                ),
            }
        }

    # Comfy node contract. Not an output node so Queue Prompt never runs it.
    RETURN_TYPES = ()
    FUNCTION = "idle"
    CATEGORY = CATEGORY
    OUTPUT_NODE = False
    DESCRIPTION = (
        "Click Check models to see whether occupancy + Quality weights are "
        "on disk. Queue does not run this node. Missing files print the host "
        "download command (download-models or an opt-in --tier)."
    )

    def idle(self, status: str = "") -> tuple[()]:
        """No-op. The JS button POSTs /ez_quality/check instead.

        Args:
            status: Unused status widget.

        Returns:
            Empty Comfy tuple.
        """
        del status
        return ()


# Comfy custom-node registries.
NODE_CLASS_MAPPINGS: dict[str, type] = {
    "EZQuality": EZQuality,
    "EZModelCheck": EZModelCheck,
}
NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {
    "EZQuality": "Detail",
    "EZModelCheck": "Check models",
}
