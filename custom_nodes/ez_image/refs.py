"""Optional reference stills for Klein T2I graphs (fail-soft when empty)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .nodes import CATEGORY, snap_dim

if TYPE_CHECKING:
    from ez_common import ComfyInputTypes


def _as_bool(value: object) -> bool:
    """Parse a Comfy BOOLEAN or presence flag.

    Args:
        value: Bool, number, or yes/no string.

    Returns:
        Parsed flag.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def _image_present(image: object) -> bool:
    """True when ``image`` looks like a non-empty Comfy IMAGE batch.

    Args:
        image: Optional IMAGE tensor or None.

    Returns:
        True when the value has a usable spatial size.
    """
    if image is None:
        return False
    shape = getattr(image, "shape", None)
    if shape is None:
        return False
    try:
        return int(shape[1]) > 1 and int(shape[2]) > 1
    except (TypeError, IndexError, ValueError):
        return False


class EZOptionalImage:
    """Optional example/reference stills. Empty filename or no tensor is fine."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return optional IMAGE inputs and filename widgets.

        Returns:
            Optional image/filename map.
        """
        img = ("IMAGE",)
        path = ("STRING", {"default": "", "multiline": False})
        return {
            "required": {
                "filename": path,
            },
            "optional": {
                "image": img,
                "image_2": img,
                "image_3": img,
                "filename_2": path,
                "filename_3": path,
            },
        }

    # Comfy node contract.
    RETURN_TYPES = ("IMAGE", "INT", "BOOLEAN")
    RETURN_NAMES = ("image", "count", "has_image")
    FUNCTION = "run"
    CATEGORY = CATEGORY
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Optional example or reference stills. Empty is valid — Queue without "
        "a file. Klein graphs attach a present still via EZKleinRefCanvas."
    )

    def run(
        self,
        image: object = None,
        image_2: object = None,
        image_3: object = None,
        filename: object = "",
        filename_2: object = "",
        filename_3: object = "",
    ) -> dict[str, Any]:
        """Count present stills. Do not raise on empty.

        Args:
            image: Optional first IMAGE tensor.
            image_2: Optional second IMAGE tensor.
            image_3: Optional third IMAGE tensor.
            filename: Optional path; ignored when empty or missing.
            filename_2: Optional second path.
            filename_3: Optional third path.

        Returns:
            First present image (or None), count, and has_image flag.
        """
        del filename, filename_2, filename_3
        present = [item for item in (image, image_2, image_3) if _image_present(item)]
        count = len(present)
        first = present[0] if present else None
        has_image = count > 0
        note = f"{count} reference still(s)" if has_image else "no reference still"
        return {
            "ui": {"text": (note,)},
            "result": (first, count, has_image),
        }


class EZKleinRefCanvas:
    """Empty Flux2 latent, or ReferenceLatent when a still is present."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return latent, VAE, and optional image inputs.

        Returns:
            Required latent/vae plus optional image flag.
        """
        return {
            "required": {
                "latent": ("LATENT",),
                "vae": ("VAE",),
            },
            "optional": {
                "image": ("IMAGE",),
                "has_image": ("BOOLEAN", {"default": False}),
            },
        }

    # Comfy node contract.
    RETURN_TYPES = ("LATENT", "IMAGE")
    RETURN_NAMES = ("latent", "image")
    FUNCTION = "run"
    CATEGORY = CATEGORY
    DESCRIPTION = (
        "When has_image is set, snap ÷16, VAE-encode, and attach ReferenceLatent. "
        "Otherwise pass the empty Flux2 latent through. Never errors if empty."
    )

    def run(
        self,
        latent: Any,
        vae: Any,
        image: object = None,
        has_image: object = False,
    ) -> tuple[Any, Any]:
        """Attach a Klein reference latent when a still is present.

        Args:
            latent: Empty Flux2 latent canvas.
            vae: Flux2 VAE.
            image: Optional start still.
            has_image: Presence flag from EZOptionalImage.

        Returns:
            Latent (possibly with reference) and the image (or None).
        """
        if not _as_bool(has_image) or not _image_present(image):
            return (latent, image)
        encoded = _encode_ref(image, vae)
        if encoded is None:
            return (latent, image)
        attached = _reference_latent(latent, encoded)
        return (attached, image)


class EZDescribeImage:
    """Fail-soft caption for non-multimodal graphs. Empty without VL weights."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return optional image inputs.

        Returns:
            Optional IMAGE and has_image flag.
        """
        return {
            "required": {
                "has_image": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "image": ("IMAGE",),
            },
        }

    # Comfy node contract.
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("caption",)
    FUNCTION = "run"
    CATEGORY = CATEGORY
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Describe a reference still for models that are not multimodal. "
        "Fail-soft: empty string when no image or no VL GGUF is installed."
    )

    def run(
        self,
        image: object = None,
        has_image: object = False,
    ) -> dict[str, Any]:
        """Return an empty caption unless a VL backend is wired later.

        Args:
            image: Optional still.
            has_image: Presence flag.

        Returns:
            Caption STRING (empty when unused) and a ui reason.
        """
        if not _as_bool(has_image) or not _image_present(image):
            return {"ui": {"text": ("no reference still",)}, "result": ("",)}
        return {
            "ui": {"text": ("no VL weights",)},
            "result": ("",),
        }


def _encode_ref(image: Any, vae: Any) -> Any | None:
    """VAE-encode a still snapped to the Klein grid.

    Args:
        image: IMAGE tensor (BHWC).
        vae: Object with ``encode``.

    Returns:
        Encoded latent, or None when encode is unavailable.
    """
    encode = getattr(vae, "encode", None)
    if encode is None:
        return None
    height = int(image.shape[1])
    width = int(image.shape[2])
    snap_h = snap_dim(height)
    snap_w = snap_dim(width)
    if snap_h != height or snap_w != width:
        from .nodes import _resize_bhwc

        image = _resize_bhwc(image, snap_h, snap_w)
    try:
        return encode(image)
    except Exception:  # noqa: BLE001 — fail-soft to empty latent
        return None


def _reference_latent(empty: Any, encoded: Any) -> Any:
    """Attach ``encoded`` as a Flux2 reference onto ``empty`` when possible.

    Args:
        empty: Empty latent dict.
        encoded: Encoded start still.

    Returns:
        Combined latent, or ``empty`` when the helper is missing.
    """
    try:
        from comfy_extras.nodes_flux import ReferenceLatent  # type: ignore[import-not-found]
    except Exception:  # noqa: BLE001 — hermetic tests / older Comfy
        if isinstance(empty, dict):
            merged = dict(empty)
            merged["reference"] = encoded
            return merged
        return empty
    node = ReferenceLatent()
    result = node.append(empty, encoded)
    if isinstance(result, tuple):
        return result[0]
    return result


NODE_CLASS_MAPPINGS: dict[str, type] = {
    "EZOptionalImage": EZOptionalImage,
    "EZKleinRefCanvas": EZKleinRefCanvas,
    "EZDescribeImage": EZDescribeImage,
}
"""Comfy class-name registry for optional-ref nodes."""

NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {
    "EZOptionalImage": "Optional reference stills",
    "EZKleinRefCanvas": "Klein canvas (optional ref)",
    "EZDescribeImage": "Describe reference still",
}
"""Comfy display-name registry for optional-ref nodes."""
