"""Guide-pack paths and lazy IMAGE decode (hermetic at import: stdlib only)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

SHOT_STILL_LAYERS = ("first", "last", "clay", "depth", "canny")
SHOT_VIDEO_LAYERS = ("clay", "depth", "canny")
STILL_PACK_LAYERS = ("first", "rgb", "depth", "canny", "normal")
VIDEO_FILENAMES = {
    "clay": "clay.mp4",
    "depth": "depth.mp4",
    "canny": "canny.mp4",
}


def output_directory() -> Path:
    """Operator output dir: env, then Comfy folder_paths, then ``/outputs``.

    Prefer ``COMFY_OUTPUT_DIR`` so occupancy state matches ``occupancy.sh``.
    Never hardcode ``/mnt/comfy-output``. Never write ``MODELS_DIR``.

    Returns:
        Directory path (may not exist yet).
    """
    env = (os.environ.get("COMFY_OUTPUT_DIR") or "").strip()
    if env:
        return Path(env)
    try:
        import folder_paths  # type: ignore[import-not-found]

        return Path(folder_paths.get_output_directory())
    except Exception:  # noqa: BLE001 — Comfy optional in unit tests
        return Path("/outputs")


def shot_dir(slug: str, shot_id: str) -> Path:
    """``guides/<slug>/<shot_id>/`` under the output directory."""
    return output_directory() / "guides" / str(slug) / str(shot_id)


def still_dir(slug: str, plate: str) -> Path:
    """``guides/<slug>/stills/<plate>/`` under the output directory."""
    return output_directory() / "guides" / str(slug) / "stills" / str(plate)


def camera_json_path(slug: str, shot_id: str) -> Path:
    """Optional ``camera.json`` next to the shot pack."""
    return shot_dir(slug, shot_id) / "camera.json"


def shot_still_path(pack_dir: Path, layer: str) -> Path:
    """Resolve a still PNG inside a shot pack. Depth is dumped mist 0-1."""
    if layer in {"first", "clay"}:
        return pack_dir / "first.png"
    if layer == "last":
        return pack_dir / "last.png"
    if layer == "depth":
        seq = pack_dir / "depth" / "0001.png"
        if seq.is_file():
            return seq
        return pack_dir / "depth.png"
    if layer == "canny":
        seq = pack_dir / "canny" / "0001.png"
        if seq.is_file():
            return seq
        return pack_dir / "canny.png"
    raise ValueError(f"unknown shot still layer {layer!r}")


def shot_video_path(pack_dir: Path, layer: str) -> Path:
    """Absolute mp4 path for a video layer. Does not decode frames."""
    name = VIDEO_FILENAMES.get(layer)
    if name is None:
        raise ValueError(f"unknown shot video layer {layer!r}")
    return pack_dir / name


def still_pack_path(pack_dir: Path, layer: str) -> Path:
    """Resolve a PNG inside an ``ez.guide.still.v1`` pack."""
    if layer in {"first", "rgb"}:
        return pack_dir / "first.png"
    if layer in {"depth", "canny", "normal"}:
        return pack_dir / f"{layer}.png"
    raise ValueError(f"unknown still pack layer {layer!r}")


def decode_png(path: Path) -> tuple[Any, Any]:
    """Decode a PNG to Comfy IMAGE + MASK. Torch is imported here only.

    Depth pixels are returned as dumped (mist 0-1, near=white, far=black).

    Args:
        path: PNG file.

    Returns:
        ``(image, mask)`` — IMAGE ``[B,H,W,C]`` float 0-1, MASK ``[B,H,W]``.
    """
    import numpy as np
    from PIL import Image
    import torch

    opened = Image.open(path)
    has_alpha = opened.mode in {"RGBA", "LA"} or (
        opened.mode == "P" and "transparency" in opened.info
    )
    if has_alpha:
        converted = opened.convert("RGBA")
        arr = np.asarray(converted, dtype=np.float32) / 255.0
        rgb = arr[..., :3]
        alpha = arr[..., 3]
    else:
        converted = opened.convert("RGB")
        rgb = np.asarray(converted, dtype=np.float32) / 255.0
        alpha = np.ones(rgb.shape[:2], dtype=np.float32)
    image = torch.from_numpy(rgb)[None, ...]
    mask = torch.from_numpy(alpha)[None, ...]
    return image, mask
