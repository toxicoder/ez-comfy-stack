"""ComfyUI nodes: snap a still to the Flux.2 Klein grid and restore source size."""

from __future__ import annotations

import importlib
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
    DURATION_CHOICES,
    DURATION_DEFAULT,
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
FLUX2_LATENT_CHANNELS = 128
"""Flux.2 / Klein empty-latent channel count (EmptyFlux2LatentImage)."""
_EMPTY_FLUX2_MODULES = (
    "comfy_extras.nodes_flux",
    "comfy_extras.nodes_flux2",
)
"""Import paths that may define EmptyFlux2LatentImage."""


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


class _LatentShape:
    """Hermetic stand-in for a zeros Flux.2 latent tensor (shape only)."""

    def __init__(self, shape: tuple[int, ...]) -> None:
        """Record the empty-latent NCHW shape.

        Args:
            shape: ``(batch, 128, height // 16, width // 16)``.
        """
        self.shape = shape


def _call_empty_flux2(width: int, height: int, batch_size: int) -> Any | None:
    """Ask Comfy EmptyFlux2LatentImage for a zeros latent when the class exists.

    Args:
        width: Pixel width (already ÷16).
        height: Pixel height (already ÷16).
        batch_size: Latent batch.

    Returns:
        LATENT dict, or None when Comfy is missing or the call fails.
    """
    for mod_name in _EMPTY_FLUX2_MODULES:
        try:
            mod = importlib.import_module(mod_name)
            cls = getattr(mod, "EmptyFlux2LatentImage", None)
        except Exception:  # noqa: BLE001 — hermetic tests / older Comfy
            continue
        if cls is None:
            continue
        try:
            node = cls()
        except Exception:  # noqa: BLE001 — constructor may need Comfy
            continue
        for method in ("execute", "generate", "run"):
            fn = getattr(node, method, None)
            if not callable(fn):
                continue
            try:
                result = fn(width, height, batch_size)
            except TypeError:
                try:
                    result = fn(width=width, height=height, batch_size=batch_size)
                except Exception:  # noqa: BLE001 — signature mismatch
                    continue
            except Exception:  # noqa: BLE001 — fail-soft to zeros fallback
                continue
            if isinstance(result, tuple):
                return result[0]
            return result
    return None


def _zeros_flux2_latent(width: int, height: int, batch_size: int) -> dict[str, Any]:
    """Build a zeros Flux.2 latent dict without requiring Comfy.

    Args:
        width: Pixel width (already ÷16).
        height: Pixel height (already ÷16).
        batch_size: Latent batch.

    Returns:
        ``{"samples": tensor_or_shape}`` with NCHW ``(B, 128, H/16, W/16)``.
    """
    spatial_h = max(1, int(height) // GRID)
    spatial_w = max(1, int(width) // GRID)
    shape = (int(batch_size), FLUX2_LATENT_CHANNELS, spatial_h, spatial_w)
    try:
        import torch
    except Exception:  # noqa: BLE001 — hermetic tests
        torch = None
    if torch is not None:
        zeros = getattr(torch, "zeros", None)
        if callable(zeros):
            return {"samples": zeros(shape)}
    return {"samples": _LatentShape(shape)}


def empty_flux2_latent(width: int, height: int, batch_size: int = 1) -> dict[str, Any]:
    """Return an empty Flux.2 latent for ``width``×``height``.

    Prefers Comfy ``EmptyFlux2LatentImage``. Falls back to zeros (torch when
    present, shape-only otherwise).

    Args:
        width: Pixel width.
        height: Pixel height.
        batch_size: Latent batch.

    Returns:
        LATENT dict with a ``samples`` tensor.
    """
    snap_w = snap_dim(int(width))
    snap_h = snap_dim(int(height))
    batch = max(1, int(batch_size))
    comfy = _call_empty_flux2(snap_w, snap_h, batch)
    if isinstance(comfy, dict):
        return comfy
    return _zeros_flux2_latent(snap_w, snap_h, batch)


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


class EZEmptyFlux2FromImage:
    """Allocate an empty Flux.2 latent matching a still's snapped W×H."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for this node.

        Returns:
            Required IMAGE input.
        """
        return {"required": {"image": ("IMAGE",)}}

    # Comfy node contract.
    RETURN_TYPES = ("LATENT",)
    RETURN_NAMES = ("latent",)
    FUNCTION = "run"
    CATEGORY = CATEGORY
    DESCRIPTION = (
        "Empty Flux.2 noise canvas at the still's width and height snapped to "
        "÷16. stills/background-swap uses this as KSampler.latent_image so "
        "the encoded source is only a ReferenceLatent, not the denoise start."
    )

    def run(self, image: Any) -> tuple[Any]:
        """Build an empty Flux.2 latent for ``image``.

        Args:
            image: Comfy IMAGE tensor (BHWC).

        Returns:
            One-tuple with the empty LATENT dict.
        """
        height = int(image.shape[1])
        width = int(image.shape[2])
        return (empty_flux2_latent(width, height, 1),)


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
                "duration_s": (list(DURATION_CHOICES), {"default": DURATION_DEFAULT}),
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
        "provided still. Duration is LTX-only (5/8/10/12 s, default 8) and "
        "writes the latent length in the frontend. Quality does not change "
        "size."
    )

    def run(
        self,
        family: object,
        format: object,
        width: object = 832,
        height: object = 480,
        size_mode: object = SIZE_MODE_MATCH,
        duration_s: object = DURATION_DEFAULT,
        image: object = None,
    ) -> dict[str, Any]:
        """Resolve family and format widgets to a clip canvas.

        Args:
            family: Wan 5B or LTX-2.5 combo (id or label).
            format: Format / platform combo (id or label).
            width: Custom width; ignored unless format is Custom.
            height: Custom height; ignored unless format is Custom.
            size_mode: Match input or Force format.
            duration_s: LTX clip length combo; Wan ignores this at Queue.
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
        summary = f"{result.width}×{result.height} · {result.label} · {duration_s}"
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
    "EZEmptyFlux2FromImage": EZEmptyFlux2FromImage,
    "EZMatchImageSize": EZMatchImageSize,
    "EZImageFormat": EZImageFormat,
    "EZVideoFormat": EZVideoFormat,
    "EZImageUpscale": EZImageUpscale,
}
"""Comfy class-name registry."""

NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {
    "EZSnapImage": "Snap image (div 16)",
    "EZEmptyFlux2FromImage": "Empty Flux.2 from image",
    "EZMatchImageSize": "Match image size",
    "EZImageFormat": "Format / platform",
    "EZVideoFormat": "Format / platform (video)",
    "EZImageUpscale": "Upscale still",
}
"""Comfy display-name registry."""
