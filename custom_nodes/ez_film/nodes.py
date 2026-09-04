"""ComfyUI nodes: unload models between Klein/LTX, stitch 18 film shots."""

from __future__ import annotations

import gc
from typing import Any

from .concat import (
    log,
    output_directory,
    publish_path,
    resolve_shot_path,
    stitch_film,
)
from .shots import DEFAULT_CAP_SECONDS, FILM_CHOICES, SHOT_COUNT


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
    except Exception as exc:  # noqa: BLE001 — Comfy optional in tests
        log(f"model unload skipped: {exc}")
        status = "skipped"
    gc.collect()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception as exc:  # noqa: BLE001 — torch optional in tests
        log(f"cuda empty_cache skipped: {exc}")
    return status


class EZUnloadModels:
    """Pass-through IMAGE that unloads diffusion models first."""

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {"required": {"image": ("IMAGE",)}}

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/film"
    DESCRIPTION = (
        "Unload Comfy models, then pass the identity IMAGE to LTX shot 1. "
        "Keeps Klein 4B and LTX-2.5 from sitting in memory together."
    )

    def run(self, image: object) -> tuple[object]:
        _unload_models()
        return (image,)


class EZFilmConcat:
    """Stitch 18 LTX shot MP4s into ``ez_{slug}_90s.mp4`` with a 90s cap."""

    @classmethod
    def INPUT_TYPES(cls) -> dict:
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
        }
        for index in range(1, SHOT_COUNT + 1):
            required[f"shot_{index:02d}"] = ("VHS_FILENAMES",)
        return {"required": required}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("path",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/film"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Concat 18 LTX 5.00s MP4s in beat/shot order. Video stream-copy, "
        "AAC + YouTube loudnorm, cap 90s. Open this node for the 90s preview."
    )

    def run(self, film: str, cap_seconds: float = DEFAULT_CAP_SECONDS, **shots: object):
        paths = [
            resolve_shot_path(shots.get(f"shot_{index:02d}"))
            for index in range(1, SHOT_COUNT + 1)
        ]
        dest_dir = output_directory()
        dest_dir.mkdir(parents=True, exist_ok=True)
        out_mp4 = str(publish_path(film, dest_dir))
        stitch_film(paths, out_mp4, float(cap_seconds))
        filename = publish_path(film, dest_dir).name
        return {
            "ui": {
                "gifs": [
                    {
                        "filename": filename,
                        "subfolder": "",
                        "type": "output",
                        "format": "video/h264-mp4",
                    }
                ]
            },
            "result": (out_mp4,),
        }


NODE_CLASS_MAPPINGS = {
    "EZUnloadModels": EZUnloadModels,
    "EZFilmConcat": EZFilmConcat,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EZUnloadModels": "Unload models (pass IMAGE)",
    "EZFilmConcat": "Save 90s film (MP4) — open node for preview",
}
