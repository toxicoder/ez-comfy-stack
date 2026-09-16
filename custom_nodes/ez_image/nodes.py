"""ComfyUI nodes: snap a still to the Flux.2 Klein grid and restore source size."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ez_common import ComfyInputTypes

CATEGORY = "ez-comfy/image"
"""Comfy menu category for Klein canvas helpers."""

GRID = 16
"""Flux.2 Klein VAE spatial multiple (EmptyFlux2LatentImage step)."""


def snap_dim(n: int, multiple: int = GRID) -> int:
    """Return the largest multiple of ``multiple`` that is <= ``n``, min ``multiple``.

    Args:
        n: Source pixel count.
        multiple: Alignment (Klein VAE is 16).

    Returns:
        Snapped dimension, at least ``multiple``.
    """
    value = int(n)
    if value < multiple:
        return multiple
    return (value // multiple) * multiple


def _resize_bhwc(image: Any, height: int, width: int) -> Any:
    """Resize a Comfy IMAGE tensor (BHWC) with lanczos when Comfy is present.

    Args:
        image: Batched HWC tensor.
        height: Target height.
        width: Target width.

    Returns:
        Resized BHWC tensor.

    Raises:
        RuntimeError: Neither Comfy ``common_upscale`` nor torch is importable.
    """
    try:
        from comfy.utils import common_upscale  # type: ignore[import-not-found]
    except Exception:  # noqa: BLE001 — hermetic tests / missing Comfy
        common_upscale = None
    if common_upscale is not None:
        nchw = image.movedim(-1, 1)
        scaled = common_upscale(nchw, int(width), int(height), "lanczos", "disabled")
        return scaled.movedim(1, -1)
    try:
        import torch.nn.functional as F
    except Exception as exc:  # noqa: BLE001 — fail closed in production
        raise RuntimeError("EZ image resize needs Comfy common_upscale or torch") from exc
    nchw = image.movedim(-1, 1)
    scaled = F.interpolate(
        nchw,
        size=(int(height), int(width)),
        mode="bicubic",
        align_corners=False,
    )
    return scaled.movedim(1, -1)


class EZSnapImage:
    """Scale a still down to the largest Flux.2 Klein ÷16 canvas that fits."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for this node.

        Returns:
            Required IMAGE input.
        """
        return {"required": {"image": ("IMAGE",)}}

    # Comfy node contract.
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "run"
    CATEGORY = CATEGORY
    DESCRIPTION = (
        "Scale a still to the largest width and height that fit inside the "
        "source and are multiples of 16 (Flux.2 Klein VAE). Used so a Klein "
        "edit latent matches the start image, then EZMatchImageSize restores "
        "the exact source pixels."
    )

    def run(self, image: Any) -> tuple[Any]:
        """Snap ``image`` to the Klein VAE grid.

        Args:
            image: Comfy IMAGE tensor (BHWC).

        Returns:
            One-tuple with the snapped image (unchanged when already aligned).
        """
        height = int(image.shape[1])
        width = int(image.shape[2])
        snap_h = snap_dim(height)
        snap_w = snap_dim(width)
        if snap_h == height and snap_w == width:
            return (image,)
        return (_resize_bhwc(image, snap_h, snap_w),)


class EZMatchImageSize:
    """Resize a still to another image's exact height and width."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for this node.

        Returns:
            Required edited image and size reference.
        """
        return {
            "required": {
                "image": ("IMAGE",),
                "size_src": ("IMAGE",),
            }
        }

    # Comfy node contract.
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "run"
    CATEGORY = CATEGORY
    DESCRIPTION = (
        "Lanczos-resize ``image`` to ``size_src`` width and height. No-op when "
        "they already match. klein/text-swap uses this so the PNG matches the "
        "uploaded still, including odd sizes such as 1920x1080."
    )

    def run(self, image: Any, size_src: Any) -> tuple[Any]:
        """Match ``image`` to ``size_src`` spatial size.

        Args:
            image: Edited still (BHWC).
            size_src: Source still whose H×W is the target.

        Returns:
            One-tuple with the resized (or original) image.
        """
        ref_h = int(size_src.shape[1])
        ref_w = int(size_src.shape[2])
        height = int(image.shape[1])
        width = int(image.shape[2])
        if height == ref_h and width == ref_w:
            return (image,)
        return (_resize_bhwc(image, ref_h, ref_w),)


NODE_CLASS_MAPPINGS: dict[str, type] = {
    "EZSnapImage": EZSnapImage,
    "EZMatchImageSize": EZMatchImageSize,
}
"""Comfy class-name registry."""

NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {
    "EZSnapImage": "Snap image (div 16)",
    "EZMatchImageSize": "Match image size",
}
"""Comfy display-name registry."""
