"""ComfyUI nodes: snap a still to the Flux.2 Klein grid and restore source size."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .formats import (
    DEFAULT_BATCH,
    LOOK_NONE,
    MAX_BATCH,
    MAX_DIM,
    MIN_BATCH,
    MIN_DIM,
    SIZE_MODE_CHOICES,
    SIZE_MODE_MATCH,
    default_format_label,
    format_combo_labels,
    look_combo_labels,
    resolve_canvas,
)
from .upscale import (
    DEFAULT_UPSCALE,
    normalize_upscale,
    resolve_upscale_hw,
    upscale_combo_labels,
)
from .video_formats import (
    DEFAULT_FAMILY,
    FAMILY_LTX,
    default_video_format_label,
    family_combo_labels,
    get_family,
    resolve_video_canvas,
    video_format_combo_labels,
)

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
        "they already match. stills/text-swap uses this so the PNG matches the "
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


class EZImageFormat:
    """Pick a Klein still canvas (aspect or named platform) and look recipe."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for format, look, and custom size.

        Returns:
            Required widget map.
        """
        labels = format_combo_labels()
        default_label = default_format_label()
        if default_label not in labels:
            default_label = labels[0]
        return {
            "required": {
                "format": (labels, {"default": default_label}),
                "look": (look_combo_labels(), {"default": LOOK_NONE}),
                "width": (
                    "INT",
                    {
                        "default": 1280,
                        "min": MIN_DIM,
                        "max": MAX_DIM,
                        "step": GRID,
                    },
                ),
                "height": (
                    "INT",
                    {
                        "default": 704,
                        "min": MIN_DIM,
                        "max": MAX_DIM,
                        "step": GRID,
                    },
                ),
                "batch_size": (
                    "INT",
                    {
                        "default": DEFAULT_BATCH,
                        "min": MIN_BATCH,
                        "max": MAX_BATCH,
                        "step": 1,
                    },
                ),
                "size_mode": (list(SIZE_MODE_CHOICES), {"default": SIZE_MODE_MATCH}),
            },
            "optional": {
                "image": ("IMAGE",),
            },
        }

    # Comfy node contract.
    RETURN_TYPES = ("INT", "INT", "INT", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("width", "height", "batch", "hint", "prefix", "context")
    FUNCTION = "run"
    CATEGORY = CATEGORY
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Klein still canvas. Format / platform sets width, height, SaveImage "
        "prefix, and Enhance framing. Custom uses the width/height widgets "
        "(snapped to ÷16). Match input snaps aspect to a provided still. "
        "Look recipe splices a Cinema Rack starter into Enhance context. "
        "Quality does not change size. Empty of lettering."
    )

    def run(
        self,
        format: object,
        look: object = LOOK_NONE,
        width: object = 1280,
        height: object = 704,
        batch_size: object = DEFAULT_BATCH,
        size_mode: object = SIZE_MODE_MATCH,
        image: object = None,
    ) -> dict[str, Any]:
        """Resolve format widgets to a Klein canvas.

        Args:
            format: Format / platform combo (id or label).
            look: Cinema Rack recipe label or none.
            width: Custom width; ignored unless format is Custom.
            height: Custom height; ignored unless format is Custom.
            batch_size: Batch widget.
            size_mode: Match input or Force format.
            image: Optional still used when matching input ratio.

        Returns:
            Comfy output-node payload with width, height, batch, hint,
            SaveImage prefix, and Enhance context.
        """
        result = resolve_canvas(
            format,
            width=width,
            height=height,
            batch=batch_size,
            look=look,
            size_mode=size_mode,
            image=image,
        )
        summary = f"{result.width}×{result.height} · {result.prefix} · {result.label}"
        return {
            "ui": {"text": (summary,)},
            "result": (
                result.width,
                result.height,
                result.batch,
                result.hint,
                result.prefix,
                result.context,
            ),
        }


class EZVideoFormat:
    """Pick a Wan or LTX clip canvas (aspect or named platform)."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for family, format, and custom size.

        Returns:
            Required widget map. Format combo is the union of both families
            so Queue accepts either label; ``run`` falls back when the pick
            does not match Family.
        """
        families = family_combo_labels()
        family_default = families[0] if families else "Wan 5B"
        labels = video_format_combo_labels()
        default_label = default_video_format_label(DEFAULT_FAMILY)
        if labels and default_label not in labels:
            default_label = labels[0]
        family_spec = get_family(DEFAULT_FAMILY)
        ltx = get_family(FAMILY_LTX)
        max_dim = max(family_spec.max_dim, ltx.max_dim)
        min_dim = min(family_spec.min_dim, ltx.min_dim)
        return {
            "required": {
                "family": (families, {"default": family_default}),
                "format": (labels, {"default": default_label}),
                "width": (
                    "INT",
                    {
                        "default": family_spec.custom_width,
                        "min": min_dim,
                        "max": max_dim,
                        "step": family_spec.grid,
                    },
                ),
                "height": (
                    "INT",
                    {
                        "default": family_spec.custom_height,
                        "min": min_dim,
                        "max": max_dim,
                        "step": family_spec.grid,
                    },
                ),
                "size_mode": (list(SIZE_MODE_CHOICES), {"default": SIZE_MODE_MATCH}),
            },
            "optional": {
                "image": ("IMAGE",),
            },
        }

    # Comfy node contract.
    RETURN_TYPES = ("INT", "INT", "STRING", "STRING")
    RETURN_NAMES = ("width", "height", "hint", "prefix")
    FUNCTION = "run"
    CATEGORY = CATEGORY
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Wan / LTX clip canvas. Family picks the VAE grid (Wan ÷16, LTX ÷32). "
        "Format / platform sets width, height, and Enhance framing. Custom "
        "uses the width/height widgets. Match input snaps aspect to a "
        "provided still. Length stays on the latent node. Quality does "
        "not change size."
    )

    def run(
        self,
        family: object,
        format: object,
        width: object = 832,
        height: object = 480,
        size_mode: object = SIZE_MODE_MATCH,
        image: object = None,
    ) -> dict[str, Any]:
        """Resolve family and format widgets to a clip canvas.

        Args:
            family: Wan 5B or LTX-2.5 combo (id or label).
            format: Format / platform combo (id or label).
            width: Custom width; ignored unless format is Custom.
            height: Custom height; ignored unless format is Custom.
            size_mode: Match input or Force format.
            image: Optional still used when matching input ratio.

        Returns:
            Comfy output-node payload with width, height, Enhance hint,
            and a filename prefix (graphs may leave VHS prefix unwired).
        """
        result = resolve_video_canvas(
            family,
            format,
            width=width,
            height=height,
            size_mode=size_mode,
            image=image,
        )
        summary = f"{result.width}×{result.height} · {result.label}"
        return {
            "ui": {"text": (summary,)},
            "result": (
                result.width,
                result.height,
                result.hint,
                result.prefix,
            ),
        }


class EZImageUpscale:
    """Optional lanczos upscale after a still decode. none is a passthrough."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for the still and upscale combo.

        Returns:
            Required widget map. ``upscale`` may be linked from another
            EZImageUpscale so multi-save graphs share one App dropdown.
        """
        labels = upscale_combo_labels()
        return {
            "required": {
                "image": ("IMAGE",),
                "upscale": (labels, {"default": DEFAULT_UPSCALE}),
            }
        }

    # Comfy node contract.
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "upscale")
    FUNCTION = "run"
    CATEGORY = CATEGORY
    DESCRIPTION = (
        "Optional still upscale after decode. none passes the tensor through. "
        "2x and 4x are lanczos. 4K fits the still in a 3840×2160 box "
        "(portrait 2160×3840). No extra weights. Wire upscale into more "
        "EZImageUpscale nodes so one App dropdown drives every SaveImage."
    )

    def run(self, image: Any, upscale: object = DEFAULT_UPSCALE) -> tuple[Any, str]:
        """Resize ``image`` when the combo is not none.

        Args:
            image: Comfy IMAGE tensor (BHWC).
            upscale: Combo id (none / 2x / 4x / 4K).

        Returns:
            Image (possibly unchanged) and the normalized combo id.
        """
        kind = normalize_upscale(upscale)
        height = int(image.shape[1])
        width = int(image.shape[2])
        target = resolve_upscale_hw(width, height, kind)
        if target is None:
            return (image, kind)
        out_w, out_h = target
        return (_resize_bhwc(image, out_h, out_w), kind)


NODE_CLASS_MAPPINGS: dict[str, type] = {
    "EZSnapImage": EZSnapImage,
    "EZMatchImageSize": EZMatchImageSize,
    "EZImageFormat": EZImageFormat,
    "EZVideoFormat": EZVideoFormat,
    "EZImageUpscale": EZImageUpscale,
}
"""Comfy class-name registry."""

NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {
    "EZSnapImage": "Snap image (div 16)",
    "EZMatchImageSize": "Match image size",
    "EZImageFormat": "Format / platform",
    "EZVideoFormat": "Format / platform (video)",
    "EZImageUpscale": "Upscale still",
}
"""Comfy display-name registry."""
