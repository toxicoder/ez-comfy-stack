"""ComfyUI node: global Quality combo for lab graphs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .check import STATUS_DEFAULT
from .presets import QUALITY_CHOICES, QUALITY_LAB, normalize_quality

if TYPE_CHECKING:
    from ez_common import ComfyInputTypes

# Comfy menu category for the Quality node.
CATEGORY = "ez-comfy"


class EZQuality:
    """Hold the workflow-global Quality combo. JS applies family overlays."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for this node.

        Returns:
            Required widget map (quality combo).
        """
        return {
            "required": {
                "quality": (list(QUALITY_CHOICES), {"default": QUALITY_LAB}),
            }
        }

    # Comfy node contract.
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("quality",)
    FUNCTION = "report"
    CATEGORY = CATEGORY
    OUTPUT_NODE = True
    DESCRIPTION = (
        "custom freezes the last overlay. lab restores graph defaults. "
        "draft / standard / high are Apache Klein 4B. "
        "Free Commercial Use (<$10M) is Klein 4B stills (never 9B or FLUX.2-dev) "
        "plus LTX-2.5 steps; Wan / audio / trellis are no-ops. "
        "ultra is Klein 9B distilled when on disk (FLUX Non-Commercial, not YouTube-ok). "
        "max is 9B base or FLUX.2-dev when on disk (same NC license). "
        "Named qualities may swap UNET, CLIP, and VAE. Never changes size. "
        "Editing Steps / CFG / UNET / CLIP / VAE selects custom so Queue keeps "
        "those values. Prompt text is not overlaid. "
        "Not --tier quality."
    )

    def report(self, quality: str) -> dict[str, Any]:
        """Normalize the Quality combo for UI and downstream STRING.

        Args:
            quality: Lab / Draft / High widget value.

        Returns:
            Comfy output-node payload with the normalized quality id.
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
    "EZQuality": "Quality",
    "EZModelCheck": "Check models",
}
