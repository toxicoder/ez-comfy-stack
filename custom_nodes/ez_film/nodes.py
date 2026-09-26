"""ComfyUI nodes: unload models between Klein/LTX, stitch film and clip shots."""

from __future__ import annotations

import gc
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from .concat import (
    CLIP_CAP_DEFAULT_S,
    CLIP_CAP_MAX_S,
    CLIP_COUNT_MAX,
    CLIP_PREFIX_DEFAULT,
    copy_publish_master,
    log,
    output_directory,
    publish_path,
    resolve_shot_path,
    stitch_clips,
    stitch_film,
    write_disclosure_sidecar,
    write_preview_html,
)
from .shots import DEFAULT_CAP_SECONDS, FILM_CHOICES, SHOT_COUNT

if TYPE_CHECKING:
    from ez_common import ComfyInputTypes


def _unload_models() -> str:
    """Best-effort Comfy + CUDA unload. Always safe to call.

    Returns:
        Status string for logs.
    """
    status = "gc"
    try:
        import comfy.model_management as mm  # type: ignore[import-not-found]

        mm.unload_all_models()
        if hasattr(mm, "soft_empty_cache"):
            mm.soft_empty_cache()
        status = "unloaded"
    except Exception as exc:  # noqa: BLE001 - Comfy optional in tests
        log(f"model unload skipped: {exc}")
        status = "skipped"
    gc.collect()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception as exc:  # noqa: BLE001 - torch optional in tests
        log(f"cuda empty_cache skipped: {exc}")
    return status


class EZUnloadModels:
    """Pass-through IMAGE that unloads diffusion models first."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return the Comfy widget schema.

        Returns:
            Required IMAGE input.
        """
        return {"required": {"image": ("IMAGE",)}}

    # Comfy node contract.
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/film"
    DESCRIPTION = (
        "Unload Comfy models, then pass the identity IMAGE to LTX shot 1. "
        "Keeps Klein 4B and LTX-2.5 from sitting in memory together."
    )

    def run(self, image: object) -> tuple[object]:
        """Unload models, then return the same IMAGE tensor.

        Args:
            image: Comfy IMAGE batch (identity pass-through).

        Returns:
            One-element tuple of the input image.
        """
        _unload_models()
        return (image,)


class EZFilmConcat:
    """Stitch 18 LTX shot MP4s into a 90s act or 90s film master."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return the Comfy widget schema.

        Returns:
            Film, cap, xfade, act, 18 VHS shots, and optional disclosure.
        """
        required: dict[str, Any] = {
            "film": (list(FILM_CHOICES), {"default": "go-see"}),
            "cap_seconds": (
                "FLOAT",
                {
                    "default": DEFAULT_CAP_SECONDS,
                    "min": 1.0,
                    "max": DEFAULT_CAP_SECONDS,
                    "step": 0.05,
                },
            ),
            "xfade_cs": (
                "INT",
                {
                    "default": 0,
                    "min": 0,
                    "max": 50,
                    "step": 1,
                },
            ),
            "act": (
                "INT",
                {
                    "default": 0,
                    "min": 0,
                    "max": 5,
                    "step": 1,
                },
            ),
        }
        for index in range(1, SHOT_COUNT + 1):
            required[f"shot_{index:02d}"] = ("VHS_FILENAMES",)
        return {
            "required": required,
            "optional": {
                "disclosure": ("STRING", {"forceInput": True, "default": ""}),
            },
        }

    # Comfy node contract.
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("path",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/film"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Concat 18 LTX 5.00s MP4s in beat/shot order. H.264 CRF 18 + AAC + "
        "YouTube loudnorm + faststart, cap 90s. act=0 writes the 90s film "
        "master; act=1-5 writes ez_<slug>_actN_90s.mp4 for festival shorts. "
        "xfade_cs is audio-only acrossfade (10 = 0.10s, overlap off so "
        "duration stays on picture); 0 is a hard cut. A play/download overlay "
        "appears when Queue finishes."
    )

    def run(
        self,
        film: str,
        cap_seconds: float = DEFAULT_CAP_SECONDS,
        xfade_cs: int = 0,
        disclosure: str = "",
        *,
        act: int = 0,
        **shots: object,
    ) -> dict[str, Any]:
        """Stitch 18 shot MP4s and return a VHS-style preview payload.

        Args:
            film: Film id from the catalog.
            cap_seconds: Publish duration cap (default 90; widget max 90).
            xfade_cs: Audio acrossfade in centiseconds; 0 is a hard cut.
            act: 0 = 90s film master; 1-5 = act master for 7.5 min films.
            disclosure: Optional LTX disclosure text for the sidecar.
            shots: ``shot_01`` ... ``shot_18`` VHS_FILENAMES payloads.

        Returns:
            Comfy output dict with ``ui.gifs`` preview and ``result`` path.
        """
        paths = []
        for index in range(1, SHOT_COUNT + 1):
            path = resolve_shot_path(shots.get(f"shot_{index:02d}"))
            file_path = Path(path)
            if not file_path.is_file() or file_path.stat().st_size < 1:
                raise RuntimeError(
                    f"missing or unreadable shot_{index:02d} ({path}); "
                    "refusing to stitch fewer than 18 stems"
                )
            paths.append(path)
        dest_dir = output_directory()
        dest_dir.mkdir(parents=True, exist_ok=True)
        out_mp4 = str(publish_path(film, dest_dir, act=int(act)))
        stitch_film(paths, out_mp4, float(cap_seconds), xfade_cs=int(xfade_cs))
        write_disclosure_sidecar(out_mp4, disclosure)
        write_preview_html(out_mp4)
        copy_publish_master(out_mp4, film, dest_dir)
        filename = publish_path(film, dest_dir, act=int(act)).name
        return {
            "ui": {
                "gifs": [
                    {
                        "filename": filename,
                        "subfolder": "",
                        "type": "output",
                        "format": "video/h264-mp4",
                        "frame_rate": 24,
                    }
                ]
            },
            "result": (out_mp4,),
        }


FILM_DISCLOSURE = (
    "This video includes AI-generated picture and sound (LTX Community License). "
    "Do not strip provenance. Not legal advice."
)
"""LTX Community License AI-media disclosure prepended by EZFilmDisclosure."""


class EZFilmDisclosure:
    """LTX Community License end-card text (disclose AI media)."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return the Comfy widget schema.

        Returns:
            Optional multiline end-card text.
        """
        return {
            "required": {
                "text": ("STRING", {"default": "", "multiline": True}),
            }
        }

    # Comfy node contract.
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/film"
    DESCRIPTION = (
        "Prepend the LTX Community License AI-media disclosure. "
        "Idempotent. Not legal advice."
    )

    def run(self, text: str = "") -> tuple[str]:
        """Prepend the LTX disclosure when it is not already present.

        Args:
            text: Operator end-card body.

        Returns:
            One-element tuple of disclosure text.
        """
        body = str(text or "").strip()
        if body.startswith(FILM_DISCLOSURE):
            return (body,)
        if not body:
            return (FILM_DISCLOSURE,)
        return (f"{FILM_DISCLOSURE}\n\n{body}",)


def _clip_present(payload: object) -> bool:
    """True when a clip socket carries a non-empty VHS payload.

    Missing, ``None``, ``""``, and ``[]`` are unwired (not a hole).

    Args:
        payload: Optional ``VHS_FILENAMES`` value.

    Returns:
        Whether the socket should count as a stem.
    """
    return payload not in (None, "", [])


class EZClipLastFrame:
    """Last frame of a decoded video batch (duration-safe)."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return the Comfy widget schema.

        Returns:
            Required IMAGE input.
        """
        return {"required": {"image": ("IMAGE",)}}

    # Comfy node contract.
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("last_frame",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/film"
    DESCRIPTION = (
        "Return the last frame of an IMAGE batch (index -1). "
        "Use as the next clip's I2V start. Do not hardcode ImageFromBatch 120."
    )

    def run(self, image: object) -> tuple[object]:
        """Return the last frame, keeping a batch dimension of 1.

        Args:
            image: Comfy IMAGE batch (BHWC).

        Returns:
            One-element tuple of ``image[-1:]``.
        """
        if image is None:
            raise ValueError("empty IMAGE batch; cannot extract last frame")
        shape = getattr(image, "shape", None)
        if shape is None or int(shape[0]) == 0:
            raise ValueError("empty IMAGE batch; cannot extract last frame")
        return (cast(Any, image)[-1:],)


class EZClipConcat:
    """Stitch N clip MP4s. Cap is a ceiling, not a pad-to-runtime."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return the Comfy widget schema.

        Returns:
            Prefix, cap, xfade, required ``clip_01``, optional ``clip_02``...24.
        """
        required: dict[str, Any] = {
            "prefix": ("STRING", {"default": CLIP_PREFIX_DEFAULT}),
            "cap_seconds": (
                "FLOAT",
                {
                    "default": CLIP_CAP_DEFAULT_S,
                    "min": 1.0,
                    "max": CLIP_CAP_MAX_S,
                    "step": 0.05,
                },
            ),
            "xfade_cs": (
                "INT",
                {"default": 0, "min": 0, "max": 50, "step": 1},
            ),
            "clip_01": ("VHS_FILENAMES",),
        }
        optional: dict[str, Any] = {
            "disclosure": ("STRING", {"forceInput": True, "default": ""}),
        }
        for index in range(2, CLIP_COUNT_MAX + 1):
            optional[f"clip_{index:02d}"] = ("VHS_FILENAMES",)
        return {"required": required, "optional": optional}

    # Comfy node contract.
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("path",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/film"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Concat 1-24 LTX duration-head MP4s (5/8/10/12 s). H.264 CRF 18 + "
        "AAC + YouTube loudnorm + faststart. Cap is a fail-closed ceiling "
        "(default 600 s), not a pad-to-runtime. v1 is a hard cut "
        "(xfade_cs must be 0). A play/download overlay appears when Queue "
        "finishes."
    )

    def run(
        self,
        prefix: str,
        cap_seconds: float = CLIP_CAP_DEFAULT_S,
        xfade_cs: int = 0,
        clip_01: object = None,
        disclosure: str = "",
        **clips: object,
    ) -> dict[str, Any]:
        """Stitch wired clip MP4s and return a VHS-style preview payload.

        Args:
            prefix: Output filename stem (default ``ez_clip_chain``).
            cap_seconds: Publish ceiling (default 600; widget max 1800).
            xfade_cs: Must be 0 in v1 (hard cut).
            clip_01: First ``VHS_FILENAMES`` payload (required).
            disclosure: Optional LTX disclosure text for the sidecar.
            clips: ``clip_02`` ... ``clip_24`` optional VHS payloads.

        Returns:
            Comfy output dict with ``ui.gifs`` preview and ``result`` path.
        """
        if int(xfade_cs) > 0:
            raise RuntimeError(
                "clip xfade not in v1; use xfade_cs=0 (hard cut)"
            )
        payloads = _collect_clip_payloads(clip_01, clips)
        paths = [_resolve_clip_path(index, payload) for index, payload in payloads]
        dest_dir = output_directory()
        dest_dir.mkdir(parents=True, exist_ok=True)
        name = str(prefix or CLIP_PREFIX_DEFAULT).strip() or CLIP_PREFIX_DEFAULT
        filename = f"{name}.mp4"
        out_mp4 = str(dest_dir / filename)
        stitch_clips(paths, out_mp4, float(cap_seconds), xfade_cs=int(xfade_cs))
        write_disclosure_sidecar(out_mp4, disclosure)
        write_preview_html(out_mp4)
        return {
            "ui": {
                "gifs": [
                    {
                        "filename": filename,
                        "subfolder": "",
                        "type": "output",
                        "format": "video/h264-mp4",
                        "frame_rate": 24,
                    }
                ]
            },
            "result": (out_mp4,),
        }


def _collect_clip_payloads(
    clip_01: object, clips: dict[str, object]
) -> list[tuple[int, object]]:
    """Collect wired clips until a trailing gap; refuse holes.

    Args:
        clip_01: Required first payload.
        clips: Optional ``clip_02``...``clip_24`` kwargs.

    Returns:
        ``(1-based index, payload)`` pairs in order.
    Raises:
        RuntimeError: missing ``clip_01`` or a hole before a later clip.
    """
    if not _clip_present(clip_01):
        raise RuntimeError(f"missing or unreadable clip_01 ({clip_01})")
    ordered: list[tuple[int, object]] = [(1, clip_01)]
    for index in range(2, CLIP_COUNT_MAX + 1):
        payload = clips.get(f"clip_{index:02d}")
        if _clip_present(payload):
            ordered.append((index, payload))
            continue
        for later in range(index + 1, CLIP_COUNT_MAX + 1):
            if _clip_present(clips.get(f"clip_{later:02d}")):
                raise RuntimeError(
                    f"missing clip_{index:02d}; refusing to stitch with a hole"
                )
        break
    return ordered


def _resolve_clip_path(index: int, payload: object) -> str:
    """Resolve a VHS payload to a readable video path.

    Args:
        index: 1-based clip socket index.
        payload: ``VHS_FILENAMES`` value.

    Returns:
        Video path string.
    Raises:
        RuntimeError: empty payload or missing/unreadable file.
    """
    try:
        path = resolve_shot_path(payload)
    except ValueError:
        raise RuntimeError(
            f"missing or unreadable clip_{index:02d} ({payload})"
        ) from None
    file_path = Path(path)
    if not file_path.is_file() or file_path.stat().st_size < 1:
        raise RuntimeError(f"missing or unreadable clip_{index:02d} ({path})")
    return path


# Comfy pack registry.
NODE_CLASS_MAPPINGS = {
    "EZUnloadModels": EZUnloadModels,
    "EZFilmConcat": EZFilmConcat,
    "EZFilmDisclosure": EZFilmDisclosure,
    "EZClipLastFrame": EZClipLastFrame,
    "EZClipConcat": EZClipConcat,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EZUnloadModels": "Unload models (pass IMAGE)",
    "EZFilmConcat": "Save 90s film (MP4) - play / download",
    "EZFilmDisclosure": "LTX AI-media disclosure (end-card)",
    "EZClipLastFrame": "Last frame (IMAGE) - next I2V start",
    "EZClipConcat": "Save clip chain (MP4) - play / download",
}
