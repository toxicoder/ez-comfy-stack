"""Optional reference stills for Klein T2I graphs (fail-soft when empty)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .nodes import CATEGORY, snap_dim

if TYPE_CHECKING:
    from ez_common import ComfyInputTypes

DEFAULT_MAX_REFS = 3
"""Reference frames taken from a wired batch when the widget is unset."""

MIN_MAX_REFS = 1
"""Lowest accepted ``max_refs`` widget value."""

MAX_MAX_REFS = 4
"""Highest accepted ``max_refs`` widget value (Klein reference budget)."""


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


def _batch_len(image: object) -> int:
    """Return the leading batch size of a tensor-shaped value.

    Args:
        image: IMAGE or latent-samples tensor, or None.

    Returns:
        Frame count, or 1 when the shape is missing or unreadable.
    """
    shape = getattr(image, "shape", None)
    if shape is None:
        return 1
    try:
        length = int(shape[0])
    except (TypeError, IndexError, ValueError):
        return 1
    return length if length > 0 else 1


def _ref_limit(value: object) -> int:
    """Clamp the ``max_refs`` widget into the canvas range.

    Args:
        value: Widget value (int, number, or junk from a stale graph).

    Returns:
        Reference count between ``MIN_MAX_REFS`` and ``MAX_MAX_REFS``.
    """
    raw: Any = value
    try:
        limit = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_MAX_REFS
    if limit < MIN_MAX_REFS:
        return MIN_MAX_REFS
    if limit > MAX_MAX_REFS:
        return MAX_MAX_REFS
    return limit


def _count_note(count: int) -> str:
    """Return the honest status line for a collected still count.

    Args:
        count: Total frames the node found.

    Returns:
        Plain ui text, never a placeholder.
    """
    if count <= 0:
        return "no reference still"
    if count == 1:
        return "1 reference still"
    return f"{count} reference stills"


def _filename_str(value: object) -> str:
    """Strip a filename widget to a path string.

    Args:
        value: Combo or STRING widget.

    Returns:
        Stripped filename, or empty.
    """
    if isinstance(value, str):
        return value.strip()
    if value is None:
        return ""
    return str(value).strip()


def input_still_choices() -> list[str]:
    """Return ``input/`` still names with an empty first choice.

    Empty stays valid so optional refs Queue without a file.

    Returns:
        Combo values starting with ``""``.
    """
    names: list[str] = [""]
    try:
        import folder_paths  # type: ignore[import-not-found]

        found = folder_paths.get_filename_list("input")
    except Exception:  # noqa: BLE001 - hermetic tests / missing Comfy
        found = None
    if found:
        names.extend(str(item) for item in found if str(item).strip())
    return names


def load_input_still(filename: object) -> object | None:
    """Load a still from Comfy ``input/`` when ``filename`` is set.

    Args:
        filename: Combo value (empty is a no-op).

    Returns:
        BHWC float batch, or None when empty/unreadable.
    """
    name = _filename_str(filename)
    if not name:
        return None
    try:
        import numpy as np
        from PIL import Image

        import folder_paths  # type: ignore[import-not-found]
    except Exception:  # noqa: BLE001 - hermetic tests / missing deps
        return None
    try:
        path = folder_paths.get_annotated_filepath(name)
    except Exception:  # noqa: BLE001 - missing helper
        path = None
    if not path:
        return None
    try:
        with Image.open(path) as img:
            rgb = img.convert("RGB")
            arr = (np.asarray(rgb).astype("float32") / 255.0)
    except Exception:  # noqa: BLE001 - unreadable file
        return None
    if getattr(arr, "ndim", 0) != 3:
        return None
    return arr[None, ...]


def _concat_frames(frames: list[Any]) -> Any:
    """Join several BHWC stills on the batch axis with torch.

    Args:
        frames: Present stills, more than one.

    Returns:
        Concatenated batch, or ``frames[0]`` when torch is missing or the
        join fails, so an uneven set still reaches the sampler.
    """
    try:
        import torch
    except Exception:  # noqa: BLE001 - hermetic tests have no torch
        return frames[0]
    cat = getattr(torch, "cat", None)
    if not callable(cat):
        return frames[0]
    try:
        return cat(frames, dim=0)
    except Exception:  # noqa: BLE001 - mismatched sizes keep the first still
        return frames[0]


class EZOptionalImage:
    """Optional example/reference stills. Empty filename or no tensor is fine."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return the three upload pickers, the mute switch, and the batch socket.

        Widget order is positional: saved graphs store widgets_values as a
        bare ``[""]``, so ``filename`` must stay slot 0 and the rest defaults.

        Returns:
            Required filename combo plus optional mute, pickers, and IMAGE.
        """
        choices = input_still_choices()
        return {
            "required": {
                # Slot 0 and the frozen name: ez_outputs.js and 98 graphs
                # address "filename" directly.
                "filename": (list(choices), {"default": "", "image_upload": True}),
            },
            "optional": {
                "use_references": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "label_on": "Use references",
                        "label_off": "References off",
                    },
                ),
                "filename_2": (list(choices), {"default": "", "image_upload": True}),
                "filename_3": (list(choices), {"default": "", "image_upload": True}),
                "image": ("IMAGE",),
            },
        }

    # Comfy node contract.
    RETURN_TYPES = ("IMAGE", "INT", "BOOLEAN")
    RETURN_NAMES = ("image", "count", "has_image")
    FUNCTION = "run"
    CATEGORY = CATEGORY
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Optional example or reference stills. Empty is valid - Queue without "
        "a file. Up to three upload pickers plus one wired image batch, all of "
        "which reach the model as reference latents. use_references mutes them "
        "without clearing your picks. Klein graphs attach a present still via "
        "EZKleinRefCanvas."
    )

    def run(
        self,
        filename: object = "",
        use_references: object = True,
        filename_2: object = "",
        filename_3: object = "",
        image: object = None,
    ) -> dict[str, Any]:
        """Collect the present stills. Never raise on empty or missing files.

        Args:
            filename: First picker; empty is a no-op.
            use_references: False mutes every reference, picks stay as set.
            filename_2: Second picker; empty is a no-op.
            filename_3: Third picker; empty is a no-op.
            image: Optional wired BHWC batch; counts by its leading dimension.

        Returns:
            Dict with the still (or None), the frame count, the has_image
            flag, and a ui note.
        """
        if not _as_bool(use_references):
            return {"ui": {"text": ("references off",)}, "result": (None, 0, False)}
        frames: list[Any] = []
        count = 0
        if _image_present(image):
            frames.append(image)
            count += _batch_len(image)
        seen: set[str] = set()
        for value in (filename, filename_2, filename_3):
            name = _filename_str(value)
            if not name or name in seen:
                continue
            seen.add(name)
            loaded = load_input_still(name)
            if _image_present(loaded):
                frames.append(loaded)
                count += _batch_len(loaded)
        first: Any = None
        if len(frames) == 1:
            first = frames[0]
        elif len(frames) > 1:
            first = _concat_frames(frames)
        has_image = count > 0
        return {
            "ui": {"text": (_count_note(count),)},
            "result": (first, count, has_image),
        }


class EZKleinRefCanvas:
    """Empty Flux2 latent, or ReferenceLatent when a still is present."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return latent, VAE, optional image, and the reference cap.

        Returns:
            Required latent/vae plus the image, has_image, and max_refs
            widgets in saved-graph order.
        """
        return {
            "required": {
                "latent": ("LATENT",),
                "vae": ("VAE",),
            },
            "optional": {
                "image": ("IMAGE",),
                "has_image": ("BOOLEAN", {"default": False}),
                "max_refs": (
                    "INT",
                    {
                        "default": DEFAULT_MAX_REFS,
                        "min": MIN_MAX_REFS,
                        "max": MAX_MAX_REFS,
                        "step": 1,
                    },
                ),
            },
        }

    # Comfy node contract.
    RETURN_TYPES = ("LATENT", "IMAGE")
    RETURN_NAMES = ("latent", "image")
    FUNCTION = "run"
    CATEGORY = CATEGORY
    DESCRIPTION = (
        "When has_image is set, snap div16, VAE-encode once, and attach at "
        "most max_refs frames as ReferenceLatent. Otherwise pass the empty "
        "Flux2 latent through. Never errors if empty."
    )

    def run(
        self,
        latent: Any,
        vae: Any,
        image: object = None,
        has_image: object = False,
        max_refs: object = DEFAULT_MAX_REFS,
    ) -> tuple[Any, Any]:
        """Attach Klein reference latents when a still is present.

        Args:
            latent: Empty Flux2 latent canvas.
            vae: Flux2 VAE.
            image: Optional start still (BHWC batch).
            has_image: Presence flag from EZOptionalImage.
            max_refs: Highest number of batch frames to attach.

        Returns:
            Latent (possibly with references) and the image (or None).
        """
        if not _as_bool(has_image) or not _image_present(image):
            return (latent, image)
        encoded = _encode_ref(image, vae)
        if encoded is None:
            return (latent, image)
        frames = _encoded_frames(encoded, _ref_limit(max_refs))
        return (_reference_latent_chain(latent, frames), image)


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
    except Exception:  # noqa: BLE001 - fail-soft to empty latent
        return None


def _encoded_frames(encoded: Any, max_refs: int) -> list[Any]:
    """Split an encoded still into per-frame reference pieces.

    Args:
        encoded: VAE-encoded still batch (latent dict or samples tensor).
        max_refs: Highest number of frames to hand to the reference helper.

    Returns:
        One piece per frame capped at ``max_refs``, or ``[encoded]`` whole
        when the batch cannot be split (single frame, or unsliciable data).
    """
    samples = encoded.get("samples") if isinstance(encoded, dict) else encoded
    frames = _batch_len(samples)
    if frames <= 1 or samples is None:
        return [encoded]
    pieces: list[Any] = []
    for index in range(min(frames, max_refs)):
        try:
            piece = samples[index : index + 1]
        except Exception:  # noqa: BLE001 - unsliciable batch stays one reference
            return [encoded]
        if isinstance(encoded, dict):
            merged = dict(encoded)
            merged["samples"] = piece
            pieces.append(merged)
        else:
            pieces.append(piece)
    return pieces if pieces else [encoded]


def _reference_latent_chain(empty: Any, frames: list[Any]) -> Any:
    """Attach every encoded frame by chaining ``ReferenceLatent.append``.

    One frame behaves exactly like a single :func:`_reference_latent` call.
    A step that raises stops the chain and keeps what already attached, so
    the sampler still gets a usable latent.

    Args:
        empty: Empty latent dict.
        frames: Per-frame encoded stills, oldest first.

    Returns:
        Combined latent, or the last good latent when a step fails.
    """
    current = empty
    for frame in frames:
        try:
            current = _reference_latent(current, frame)
        except Exception:  # noqa: BLE001 - fail soft with what attached so far
            break
    return current


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
    except Exception:  # noqa: BLE001 - hermetic tests / older Comfy
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
