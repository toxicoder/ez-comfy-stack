"""ComfyUI node: cut one subject out of a photo so it can become a 3D model.

The ``3d`` Apps condition a TRELLIS.2 mesh on a single still. A photo with a
busy room behind the product teaches the shape stage that the room is part of
the object, so the operator preps the input first and hands ``EZCutout`` the
original. This node keeps the character or object and drops everything else.

BiRefNet is the matte model. Its weights are an opt-in manifest pack
(``birefnet``, never a default download), and the reference implementation
imports ``timm``, ``kornia``, ``einops`` and ``transformers`` at module load.
Every one of those imports is lazy and every failure path here is fail-soft:
a host without the dependencies, without the weights, or with the kill switch
set gets the input image back unchanged plus a status line that says why, in
the same shape :mod:`ez_image.person_mask` uses for the person paste.
"""

from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING, Protocol, TypedDict, TypeAlias, TypeGuard

from .person_mask import dilate_mask, feather_mask

if TYPE_CHECKING:
    from types import ModuleType

    from ez_common import ComfyInputTypes, ImageTensor, Json, JsonList, NodeRegistry, Tensor
    from ez_image.cubic import Bhwc, PixelTree

CATEGORY = "ez-comfy/image"
"""Comfy menu category for the cutout pre-pass."""

MaskGrid: TypeAlias = "list[list[float]]"
"""A single HW alpha in 0..1."""

Frame: TypeAlias = "list[list[list[float]]]"
"""One HWC float image in 0..1."""

CutoutImage: TypeAlias = "ImageTensor | PixelTree"
"""What Comfy hands in and what the pass-through returns untouched."""

CutoutOutputs: TypeAlias = "tuple[CutoutImage, CutoutImage, MaskGrid, str]"
"""``(image, matte, mask, status)``; see :func:`remove_background`."""

MapSource: TypeAlias = "Tensor | Json"
"""One BiRefNet logit map: a torch tensor, or the nested list it converts to."""


class CutoutModel(Protocol):
    """The slice of the BiRefNet module this node calls.

    ``transformers`` and ``torch`` are absent from the hermetic lane, so the
    model is described by the two members this node actually calls.
    """

    def __call__(self, tensor: Tensor) -> Tensor:
        """Run one forward pass.

        Args:
            tensor: Batched CHW float tensor.

        Returns:
            Logit map or pyramid of them.
        """
        ...

    def eval(self) -> None:
        """Put the module in inference mode."""
        ...


class CutoutUiText(TypedDict):
    """Operator-visible status block Comfy renders under the node."""

    text: tuple[str, ...]


class CutoutResult(TypedDict):
    """Comfy OUTPUT payload: status plus the three sockets."""

    ui: CutoutUiText
    result: tuple[CutoutImage, CutoutImage, MaskGrid]

REASON_DISABLED = "cutout off: image passed through"
"""UI status when ``EZ_CUTOUT`` turns the node off."""
REASON_NO_MODEL = "no cutout model: image passed through"
"""UI status when BiRefNet cannot be loaded."""
REASON_EMPTY = "no subject found: image passed through"
"""UI status when the matte covers almost nothing."""
REASON_CUT = "cut out subject"
"""UI status when a subject was isolated."""

MODEL_REPO = "ZhengPeng7/BiRefNet"
"""Hugging Face repo the opt-in ``birefnet`` pack mirrors."""
MODEL_SUBDIR = "ZhengPeng7__BiRefNet_birefnet"
"""Pack ``tier_dir``: ``${MODELS_DIR}/<repo with / as __>_<tier>``."""
MODEL_URL_BASE = "https://huggingface.co/ZhengPeng7/BiRefNet/resolve/main"
"""Direct file URLs for the self-serve first-run download."""
MODEL_FILES: tuple[str, ...] = (
    "model.safetensors",
    "config.json",
    "birefnet.py",
    "BiRefNet_config.py",
)
"""Every file ``trust_remote_code`` needs before it will build the model.

``model.safetensors`` alone is not loadable: ``config.json`` carries the
``auto_map`` that names ``birefnet.BiRefNet`` and the architecture flags, and
the two ``.py`` files are that class.
"""
DOWNLOAD_TIMEOUT_S = 120
"""Socket timeout for the optional first-run weight download."""

MODEL_IMAGE_SIZE = 1024
"""Side length BiRefNet was trained and published at."""
IMAGENET_MEAN = (0.485, 0.456, 0.406)
"""Per-channel mean the backbone was normalised with."""
IMAGENET_STD = (0.229, 0.224, 0.225)
"""Per-channel std the backbone was normalised with."""

BACKDROP_WHITE = "white"
"""Keep the subject and paint the vacated pixels white."""
BACKDROP_BLACK = "black"
"""Keep the subject and paint the vacated pixels black."""
BACKDROP_KEEP = "keep original"
"""Keep every pixel: only the matte and mask are useful in this mode."""
BACKDROPS: tuple[str, ...] = (BACKDROP_WHITE, BACKDROP_BLACK, BACKDROP_KEEP)
"""What replaces the removed background."""
DEFAULT_BACKDROP = BACKDROP_WHITE
"""White keeps a cutout legible on the light App thumbnails."""

DILATE_RADIUS = 2
"""Default pixels grown past the matte so thin detail survives."""
FEATHER_RADIUS = 2
"""Default soft-edge width, so the rim is not a hard cut."""
MIN_SUBJECT_RATIO = 0.002
"""Below this share of pixels the matte is treated as a failed detection."""
MISS_COOLDOWN_S = 600
"""Seconds to skip reload attempts after a failed model load."""

_MODEL: CutoutModel | None = None
"""Cached BiRefNet module after a successful load."""
_LAST_MISS_S: float | None = None
"""``time.monotonic`` stamp of the last failed load, or None."""


def reset_cutout_model() -> None:
    """Drop the cached model and the load-failure cooldown."""
    global _MODEL, _LAST_MISS_S
    _MODEL = None
    _LAST_MISS_S = None


def cutout_disabled() -> bool:
    """True when the operator turned the cutout pre-pass off.

    Returns:
        Whether ``EZ_CUTOUT`` is 0 / off / false / no.
    """
    flag = os.environ.get("EZ_CUTOUT", "").strip().lower()
    return flag in {"0", "off", "false", "no"}


def cutout_roots() -> list[str]:
    """Return model-root candidates, host and container order.

    The Compose container sets ``MODELS_ROOT=/models`` and never sets
    ``MODELS_DIR`` (that name is the host ``.env``), so both env vars are
    consulted, then the documented container and host fallbacks.

    Returns:
        Unique directory strings (may not exist).
    """
    roots: list[str] = []
    for key in ("MODELS_ROOT", "MODELS_DIR"):
        value = (os.environ.get(key) or "").strip()
        if value and value not in roots:
            roots.append(value)
    for fallback in ("/models", "/mnt/models"):
        if fallback not in roots:
            roots.append(fallback)
    return roots


def _dir_in(root: str) -> str:
    """Return the pack directory under one model root.

    Args:
        root: Model root directory.

    Returns:
        ``<root>/ZhengPeng7__BiRefNet_birefnet``.
    """
    return os.path.join(root, MODEL_SUBDIR)


def model_dir() -> str:
    """Return the preferred on-disk pack directory.

    ``EZ_CUTOUT_MODEL_DIR`` wins. Otherwise the first model root's pack
    directory (see :func:`cutout_roots`). :func:`ready_model_dir` still probes
    every root.

    Returns:
        Absolute or env-relative path. The directory may be absent.
    """
    override = os.environ.get("EZ_CUTOUT_MODEL_DIR", "").strip()
    if override:
        return override
    return _dir_in(cutout_roots()[0])


def _file_ready(path: str) -> bool:
    """True when ``path`` is a non-empty file.

    Args:
        path: File path.

    Returns:
        Whether the file can be read.
    """
    try:
        return os.path.isfile(path) and os.path.getsize(path) > 0
    except OSError:
        return False


def _dir_ready(folder: str) -> bool:
    """True when ``folder`` holds every file the loader needs.

    Args:
        folder: Candidate pack directory.

    Returns:
        Whether the directory is loadable as-is.
    """
    return all(_file_ready(os.path.join(folder, name)) for name in MODEL_FILES)


def ready_model_dir() -> str | None:
    """Return the first pack directory already on disk.

    Probes ``EZ_CUTOUT_MODEL_DIR`` when set, then every model root's pack
    directory.

    Returns:
        Directory path, or None when no root holds a complete pack.
    """
    override = os.environ.get("EZ_CUTOUT_MODEL_DIR", "").strip()
    candidates = [override] if override else [_dir_in(r) for r in cutout_roots()]
    for folder in candidates:
        if _dir_ready(folder):
            return folder
    return None


def _download(url: str, dest: str) -> bool:
    """Download ``url`` to ``dest``.

    Globals:
        DOWNLOAD_TIMEOUT_S: Socket timeout.

    Args:
        url: Remote file URL.
        dest: Local path to write.

    Returns:
        Whether the file landed non-empty.
    """
    import urllib.request  # noqa: S310 - fixed https host above

    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with urllib.request.urlopen(url, timeout=DOWNLOAD_TIMEOUT_S) as response:  # noqa: S310
            payload = response.read()
        if not payload:
            return False
        with open(dest, "wb") as handle:
            handle.write(payload)
        return _file_ready(dest)
    except Exception:
        return False


def download_model() -> bool:
    """Fetch the BiRefNet pack into the first writable model root.

    The opt-in route is ``bazelisk run //scripts:run-utility -- download-3d
    --tier birefnet``, which owns the keep-set. This is the same-file fallback
    for a host that has not run it, mirroring the person mask's behaviour.

    Globals:
        _LAST_MISS_S: Reset on success so the next load retries.

    Returns:
        Whether a complete pack is now on disk.
    """
    global _LAST_MISS_S
    for root in cutout_roots():
        folder = _dir_in(root)
        try:
            os.makedirs(folder, exist_ok=True)
        except OSError:
            continue
        if not os.access(folder, os.W_OK):
            continue
        for name in MODEL_FILES:
            dest = os.path.join(folder, name)
            if _file_ready(dest):
                continue
            if not _download(f"{MODEL_URL_BASE}/{name}", dest):
                return False
        _LAST_MISS_S = None
        return _dir_ready(folder)
    return False


def _cutout_tools() -> tuple[ModuleType, ModuleType] | None:
    """Import the inference dependencies, or None.

    Kept lazy so hermetic pytest and a CPU venv without torch still import
    this pack.

    Returns:
        ``(torch, numpy)`` modules, or None when either is missing.
    """
    try:
        import numpy as np
        import torch
    except Exception:
        return None
    return torch, np


def load_model() -> CutoutModel | None:
    """Load BiRefNet, fail-soft on every path.

    Never raises: a host without ``timm`` / ``kornia`` / ``einops`` /
    ``transformers``, without the opt-in weights, or with a broken download
    gets ``None`` and the node passes the image through.

    Globals:
        _MODEL: Populated on success.
        _LAST_MISS_S: Stamped on failure to throttle retries.

    Returns:
        The eval-mode model, or None.
    """
    global _MODEL, _LAST_MISS_S
    if _MODEL is not None:
        return _MODEL
    if cutout_disabled():
        return None
    if _LAST_MISS_S is not None and (
        time.monotonic() - _LAST_MISS_S < MISS_COOLDOWN_S
    ):
        return None
    tools = _cutout_tools()
    if tools is None:
        _LAST_MISS_S = time.monotonic()
        return None
    folder = ready_model_dir()
    if folder is None:
        if not download_model():
            _LAST_MISS_S = time.monotonic()
            return None
        folder = ready_model_dir()
        if folder is None:
            _LAST_MISS_S = time.monotonic()
            return None
    try:
        from transformers import AutoModelForImageSegmentation

        model = AutoModelForImageSegmentation.from_pretrained(
            folder, trust_remote_code=True
        )
        model.eval()
    except Exception:
        _LAST_MISS_S = time.monotonic()
        return None
    _MODEL = model
    return _MODEL


def _preprocess(pixels: Frame, size: int) -> list[list[list[float]]]:
    """Resize one HWC float image to the model canvas and normalise it.

    Args:
        pixels: HWC floats in 0..1.
        size: Target square side.

    Returns:
        CHW floats ready for the backbone.
    """
    height = len(pixels)
    width = len(pixels[0]) if height else 0
    out: list[list[list[float]]] = []
    for channel in range(3):
        mean = IMAGENET_MEAN[channel]
        std = IMAGENET_STD[channel]
        plane: list[list[float]] = []
        for row in range(size):
            src_y = min(height - 1, row * height // size) if height else 0
            line: list[float] = []
            for col in range(size):
                src_x = min(width - 1, col * width // size) if width else 0
                value = pixels[src_y][src_x][channel] if width else 0.0
                line.append((value - mean) / std)
            plane.append(line)
        out.append(plane)
    return out


def _to_mask(raw: MapSource, height: int, width: int) -> MaskGrid:
    """Turn a raw model output into an HW alpha in 0..1.

    BiRefNet returns a list of single-channel *logit* maps; the last entry is
    the full-resolution prediction and needs the sigmoid the card applies.

    Args:
        raw: Model output (a list of maps or one map).
        height: Source image height.
        width: Source image width.

    Returns:
        HW alpha, nearest-resampled to the source size.
    """
    import math

    sheet = raw[-1] if isinstance(raw, (list, tuple)) and raw else raw
    grid = _as_grid(sheet)
    if not grid or not grid[0]:
        return [[0.0] * max(width, 1) for _ in range(max(height, 1))]
    out_h = max(height, 1)
    out_w = max(width, 1)
    src_h = len(grid)
    src_w = len(grid[0])
    mask: MaskGrid = []
    for row in range(out_h):
        src_y = min(src_h - 1, row * src_h // out_h)
        src_row = grid[src_y]
        line = []
        for col in range(out_w):
            src_x = min(src_w - 1, col * src_w // out_w)
            value = float(src_row[src_x])
            line.append(1.0 / (1.0 + math.exp(-value)))
        mask.append(line)
    return mask


def _is_rows(value: MapSource) -> TypeGuard[JsonList]:
    """True when ``value`` is a non-empty list whose first entry is a list.

    Args:
        value: Candidate rows.

    Returns:
        Whether it looks like a 2D-ish sequence.
    """
    return isinstance(value, list) and bool(value) and isinstance(value[0], list)


def _numeric_rows(value: JsonList) -> MaskGrid:
    """Return ``value`` as rows of floats, or empty when anything is not a number.

    Args:
        value: Rows of scalar candidates.

    Returns:
        2D float list, empty when any entry is not numeric.
    """
    rows: MaskGrid = []
    for item in value:
        if not isinstance(item, list):
            return []
        numbers: list[float] = []
        for entry in item:
            if isinstance(entry, bool) or not isinstance(entry, (int, float)):
                return []
            numbers.append(float(entry))
        rows.append(numbers)
    return rows


def _as_grid(raw: MapSource) -> MaskGrid:
    """Coerce a torch tensor / nested list into a 2D float list.

    Args:
        raw: Model map in any of the shapes BiRefNet can hand back.

    Returns:
        2D float list, empty when nothing readable was found.
    """
    data: MapSource = raw
    detach = getattr(data, "detach", None)
    if callable(detach):
        data = detach()
    cpu = getattr(data, "cpu", None)
    if callable(cpu):
        data = cpu()
    to_list = getattr(data, "tolist", None)
    if callable(to_list):
        data = to_list()
    while _is_rows(data) and _is_rows(data[0]):
        data = data[0]
    if _is_rows(data):
        return _numeric_rows(data)
    return []


def segment_subject(image: Frame) -> MaskGrid | None:
    """Return an HW subject alpha for one image.

    Globals:
        _MODEL: Reused when already loaded.

    Args:
        image: One HWC float image (0..1) or nested lists.

    Returns:
        HW alpha in 0..1, or None when the model cannot run.
    """
    model = load_model()
    if model is None:
        return None
    tools = _cutout_tools()
    if tools is None:
        return None
    torch, _np = tools
    height = len(image)
    width = len(image[0]) if height else 0
    if not height or not width:
        return None
    try:
        batch = _preprocess(image, MODEL_IMAGE_SIZE)
        tensor = torch.tensor([batch], dtype=torch.float32)
        device = getattr(model, "device", None)
        if device is not None:
            tensor = tensor.to(device)
        with torch.no_grad():
            raw = model(tensor)
        return _to_mask(raw, height, width)
    except Exception:
        return None


def _blend(
    pixels: Frame,
    mask: MaskGrid,
    backdrop: str,
) -> Frame:
    """Composite one subject over ``backdrop`` using an HW alpha.

    Args:
        pixels: HWC floats in 0..1.
        mask: HW alpha in 0..1.
        backdrop: One of :data:`BACKDROPS`.

    Returns:
        HWC floats with the background replaced.
    """
    floor = 1.0 if backdrop == BACKDROP_WHITE else 0.0
    painted: Frame = []
    for y, row in enumerate(pixels):
        line: list[list[float]] = []
        for x, pixel in enumerate(row):
            alpha = mask[y][x] if y < len(mask) and x < len(mask[y]) else 0.0
            out: list[float] = []
            for channel in range(3):
                source = pixel[channel] if channel < len(pixel) else 0.0
                if backdrop == BACKDROP_KEEP:
                    out.append(source)
                else:
                    out.append(source * alpha + floor * (1.0 - alpha))
            line.append(out)
        painted.append(line)
    return painted


def _matte_image(mask: MaskGrid) -> Frame:
    """Return an HWC grey copy of ``mask`` so stock SaveImage can write it.

    Args:
        mask: HW alpha in 0..1.

    Returns:
        HWC floats where every channel is the alpha.
    """
    return [[[value, value, value] for value in row] for row in mask]


def remove_background(
    image: CutoutImage,
    backdrop: str = DEFAULT_BACKDROP,
    dilate: int = DILATE_RADIUS,
    feather: int = FEATHER_RADIUS,
) -> CutoutOutputs:
    """Cut the subject out of ``image``.

    Args:
        image: Comfy IMAGE (BHWC tensor or nested lists).
        backdrop: What replaces the removed background.
        dilate: Pixels grown past the matte; clamped to 0..32.
        feather: Soft-edge width; clamped to 0..32.

    Returns:
        ``(image, matte, mask, status)`` where image and matte are IMAGE and
        mask is a BHWC-free HW MASK. On every failure path the input image is
        returned unchanged with a white matte and a status that says why.
    """
    from .cubic import read_bhwc, write_bhwc

    shots = read_bhwc(image)
    if not shots:
        return image, image, [], REASON_NO_MODEL
    subject = shots[0]
    if cutout_disabled():
        return _passthrough(image, subject, REASON_DISABLED)
    mask = segment_subject(subject)
    if mask is None:
        return _passthrough(image, subject, REASON_NO_MODEL)
    if _subject_ratio(mask) < MIN_SUBJECT_RATIO:
        return _passthrough(image, subject, REASON_EMPTY)
    grown = feather_mask(dilate_mask(mask, max(0, min(dilate, 32))), max(0, min(feather, 32)))
    painted = _blend(subject, grown, backdrop)
    matte = _matte_image(grown)
    return (
        write_bhwc([painted], image),
        write_bhwc([matte], image),
        grown,
        REASON_CUT,
    )


def _passthrough(
    image: CutoutImage,
    subject: Frame,
    status: str,
) -> CutoutOutputs:
    """Return the untouched input plus an opaque matte and a status line.

    Args:
        image: The original Comfy IMAGE, kept as-is for downstream nodes.
        subject: HWC pixels used to size the opaque matte.
        status: Operator-visible reason.

    Returns:
        ``(image, matte, mask, status)``.
    """
    from .cubic import write_bhwc

    height = len(subject)
    width = len(subject[0]) if height else 0
    opaque = [[1.0] * max(width, 1) for _ in range(max(height, 1))]
    return image, write_bhwc([_matte_image(opaque)], image), opaque, status


def _subject_ratio(mask: MaskGrid) -> float:
    """Return the mean alpha of ``mask``.

    Args:
        mask: HW alpha in 0..1.

    Returns:
        Share of pixels the model called subject, 0.0 for an empty mask.
    """
    if not mask:
        return 0.0
    total = 0.0
    count = 0
    for row in mask:
        for value in row:
            total += value
            count += 1
    return 0.0 if not count else total / count


class EZCutout:
    """Remove a photo background so one subject can become a 3D model."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy sockets.

        Returns:
            Required image plus the backdrop and matte-edge controls.
        """
        return {
            "required": {
                "image": ("IMAGE",),
                "backdrop": (list(BACKDROPS), {"default": DEFAULT_BACKDROP}),
                "dilate": ("INT", {"default": DILATE_RADIUS, "min": 0, "max": 32}),
                "feather": ("INT", {"default": FEATHER_RADIUS, "min": 0, "max": 32}),
            }
        }

    # Comfy node contract.
    RETURN_TYPES = ("IMAGE", "IMAGE", "MASK")
    RETURN_NAMES = ("image", "matte", "mask")
    FUNCTION = "run"
    CATEGORY = CATEGORY
    OUTPUT_NODE = False
    DESCRIPTION = (
        "photos/cutout. BiRefNet matte for image-to-3D input prep: keeps one "
        "character or object and drops the room behind it. Outputs the cut "
        "still, a grey matte for SaveImage, and the MASK. Fail-soft: missing "
        "weights, missing timm/kornia/einops/transformers, or EZ_CUTOUT=0 "
        "pass the input through unchanged."
    )

    def run(
        self,
        image: CutoutImage,
        backdrop: str = DEFAULT_BACKDROP,
        dilate: int = DILATE_RADIUS,
        feather: int = FEATHER_RADIUS,
    ) -> CutoutResult:
        """Cut the subject out and report what happened.

        Args:
            image: Comfy IMAGE from LoadImage.
            backdrop: What replaces the removed background.
            dilate: Pixels grown past the matte.
            feather: Soft-edge width.

        Returns:
            ``ui.text`` is the operator-visible status; ``result`` is
            ``(image, matte, mask)``.
        """
        cut, matte, mask, status = remove_background(image, backdrop, dilate, feather)
        return {"ui": {"text": (status,)}, "result": (cut, matte, mask)}


NODE_CLASS_MAPPINGS: NodeRegistry = {
    "EZCutout": EZCutout,
}
"""Comfy class-name registry for the cutout pre-pass."""

NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {
    "EZCutout": "Cut out subject (BiRefNet)",
}
"""Comfy display-name registry for the cutout pre-pass."""
