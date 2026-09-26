"""Paste photographed people back onto a cubic block-world plate.

The segmenter is torchvision DeepLabV3 ResNet50 (COCO person class, BSD-3).
It is not part of ``download-models``. Missing weights fail soft: the cubic
plate is saved and people stay cubed.
"""

from __future__ import annotations

import os
from typing import Any
from urllib.request import urlopen

from .cubic import read_bhwc, write_bhwc

CATEGORY = "ez-comfy/image"
"""Comfy menu category for the people paste."""

REASON_NOT_CUBIC = "not a cubic prompt"
"""UI status when the plate is an ordinary place swap."""
REASON_OFF = "person mask off"
"""UI status when ``EZ_PERSON_MASK=off``."""
REASON_MISSING = "person mask missing"
"""UI status when the segmenter or the pixels cannot run."""
REASON_PASTED = "pasted people"
"""UI status when source people were composited."""
REASON_NO_PEOPLE = "no people in mask"
"""UI status when the segmenter found no person pixels."""

PERSON_CLASS = 15
"""Pascal VOC person index on DeepLabV3 COCO-with-VOC weights."""
IMAGENET_MEAN = (0.485, 0.456, 0.406)
"""Mean the COCO DeepLab weights were trained with."""
IMAGENET_STD = (0.229, 0.224, 0.225)
"""Std the COCO DeepLab weights were trained with."""
WEIGHT_NAME = "deeplabv3_resnet50_coco-cd0a2569.pth"
"""Torchvision checkpoint filename."""
WEIGHT_URL = (
    "https://download.pytorch.org/models/deeplabv3_resnet50_coco-cd0a2569.pth"
)
"""Direct checkpoint URL (BSD-3). Not a default download."""
DOWNLOAD_TIMEOUT_S = 120
"""Socket timeout for the optional first-run weight download."""
DILATE_RADIUS = 2
"""Pixels grown past the segmentation so the paste owns its full silhouette."""
FEATHER_RADIUS = 6
"""Soft-edge width of the paste, so the rim blends instead of a hard line."""

_SEGMENTER: Any = None
"""Cached DeepLab module after a successful load."""


def reset_person_segmenter() -> None:
    """Drop the cached segmenter so the next Queue loads again."""
    global _SEGMENTER
    _SEGMENTER = None


def person_mask_disabled() -> bool:
    """True when the operator turned the person paste off.

    Returns:
        Whether ``EZ_PERSON_MASK`` is 0 / off / false / no.
    """
    flag = os.environ.get("EZ_PERSON_MASK", "").strip().lower()
    return flag in {"0", "off", "false", "no"}


def person_mask_path() -> str:
    """Return the on-disk checkpoint path.

    ``EZ_PERSON_MASK_PATH`` wins. Otherwise
    ``${MODELS_DIR}/comfy/ez-person/<filename>``.

    Returns:
        Absolute or env-relative path. The file may be absent.
    """
    override = os.environ.get("EZ_PERSON_MASK_PATH", "").strip()
    if override:
        return override
    root = os.environ.get("MODELS_DIR", "/mnt/models").strip() or "/mnt/models"
    return os.path.join(root, "comfy", "ez-person", WEIGHT_NAME)


def _file_ready(path: str) -> bool:
    """True when ``path`` is a non-empty file.

    Args:
        path: Checkpoint path.

    Returns:
        Whether the file can be loaded.
    """
    try:
        return os.path.isfile(path) and os.path.getsize(path) > 0
    except OSError:
        return False


def ready_weight_path() -> str | None:
    """Return the checkpoint path when it is already on disk.

    Returns:
        Path, or None when the file is missing or empty.
    """
    path = person_mask_path()
    if _file_ready(path):
        return path
    return None


def _download(url: str, dest: str) -> bool:
    """Download ``url`` to ``dest``.

    Args:
        url: Checkpoint URL.
        dest: Destination file.

    Returns:
        True when a non-empty file was written.
    """
    try:
        with urlopen(url, timeout=DOWNLOAD_TIMEOUT_S) as response:  # noqa: S310
            payload = response.read()
    except Exception:  # noqa: BLE001 — offline / blocked
        return False
    if not payload:
        return False
    try:
        with open(dest, "wb") as handle:
            handle.write(payload)
    except OSError:
        return False
    return _file_ready(dest)


def download_weight() -> str | None:
    """Download the person checkpoint into ``person_mask_path`` when writable.

    Returns:
        Path after a successful download, or None.
    """
    path = person_mask_path()
    folder = os.path.dirname(path)
    try:
        os.makedirs(folder, exist_ok=True)
    except OSError:
        return None
    if not os.access(folder, os.W_OK):
        return None
    if _download(WEIGHT_URL, path):
        return path
    return None


def _deeplab_tools() -> tuple[Any, Any, Any] | None:
    """Import torch and torchvision DeepLab, if both exist.

    Returns:
        ``(torch, deeplabv3_resnet50, weights enum)``, or None.
    """
    try:
        import torch
        from torchvision.models.segmentation import (  # type: ignore[import-not-found]
            DeepLabV3_ResNet50_Weights,
            deeplabv3_resnet50,
        )
    except Exception:  # noqa: BLE001 — hermetic tests / CPU dev venv
        return None
    return torch, deeplabv3_resnet50, DeepLabV3_ResNet50_Weights


def _torch_load(torch_mod: Any, path: str) -> Any:
    """Load a state dict, including older torch without ``weights_only``.

    Args:
        torch_mod: Torch module.
        path: Checkpoint file.

    Returns:
        Whatever ``torch.load`` returns.
    """
    try:
        return torch_mod.load(path, map_location="cpu", weights_only=True)
    except TypeError:
        return torch_mod.load(path, map_location="cpu")


def load_segmenter() -> Any:
    """Load DeepLabV3, downloading the checkpoint on first success.

    Returns:
        An eval-mode module, or None when weights and torchvision are missing.
    """
    if person_mask_disabled():
        return None
    tools = _deeplab_tools()
    if tools is None:
        return None
    torch_mod, factory, weights_enum = tools
    path = ready_weight_path()
    if path is None:
        path = download_weight()
    try:
        if path is not None:
            model = factory(weights=None)
            state = _torch_load(torch_mod, path)
            model.load_state_dict(state)
        else:
            model = factory(weights=weights_enum.COCO_WITH_VOC_LABELS_V1)
    except Exception:  # noqa: BLE001 — bad file or download refused
        return None
    eval_fn = getattr(model, "eval", None)
    if callable(eval_fn):
        eval_fn()
    return model


def _try_torch() -> Any:
    """Import torch when it exists.

    Returns:
        The torch module, or None.
    """
    try:
        import torch
    except Exception:  # noqa: BLE001 — hermetic tests
        return None
    return torch


def _logits_are_batched(data: list[Any]) -> bool:
    """True when ``data`` is BCHW rather than CHW.

    Args:
        data: Logits nested list.

    Returns:
        Whether the first spatial row is still a list.
    """
    try:
        return isinstance(data[0][0][0], list)
    except (TypeError, IndexError):
        return False


def person_mask_from_logits(logits: list[Any]) -> list[list[float]]:
    """Mark pixels whose winning class is person.

    Args:
        logits: CHW class scores.

    Returns:
        HW mask in ``{0, 1}``.

    Raises:
        ValueError: ``logits`` is empty.
        TypeError: A score is not numeric.
        IndexError: A spatial row is short.
    """
    if not logits:
        raise ValueError("empty logits")
    height = len(logits[0])
    width = len(logits[0][0]) if height else 0
    classes = len(logits)
    mask: list[list[float]] = []
    for y in range(height):
        row: list[float] = []
        for x in range(width):
            best = 0
            best_v = float(logits[0][y][x])
            for cls in range(1, classes):
                value = float(logits[cls][y][x])
                if value > best_v:
                    best_v = value
                    best = cls
            row.append(1.0 if best == PERSON_CLASS else 0.0)
        mask.append(row)
    return mask


def imagenet_normalize(batch: list[Any]) -> list[Any]:
    """Map BHWC ``0..1`` pixels onto the DeepLab ImageNet normalization.

    Args:
        batch: BHWC frames.

    Returns:
        A new batch. Channels after the third are dropped.
    """
    normalized: list[Any] = []
    for frame in batch:
        new_frame: list[Any] = []
        for row in frame:
            new_row: list[Any] = []
            for pixel in row:
                channels: list[float] = []
                for index, (mean, std) in enumerate(zip(IMAGENET_MEAN, IMAGENET_STD, strict=False)):
                    value = float(pixel[index]) if index < len(pixel) else 0.0
                    channels.append((value - mean) / std)
                new_row.append(channels)
            new_frame.append(new_row)
        normalized.append(new_frame)
    return normalized


def run_deeplab(model: Any, image: Any) -> list[list[float]] | None:
    """Run ``model`` and return an HW person mask.

    Args:
        model: DeepLab-like module. Dict outputs use the ``out`` key.
        image: Source still (BHWC).

    Returns:
        HW mask, or None when torch or the forward pass is unavailable.
    """
    torch_mod = _try_torch()
    if torch_mod is None:
        return None
    raw: Any = None
    try:
        batch = imagenet_normalize(read_bhwc(image))
        tensor = torch_mod.tensor(batch)
        mover = getattr(tensor, "movedim", None)
        if callable(mover):
            tensor = mover(-1, 1)
        eval_fn = getattr(model, "eval", None)
        if callable(eval_fn):
            eval_fn()
        no_grad = getattr(torch_mod, "no_grad", None)
        if callable(no_grad):
            context: Any = no_grad()
            with context:
                raw = model(tensor)
        else:
            raw = model(tensor)
    except Exception:  # noqa: BLE001 — fail-soft
        return None
    if isinstance(raw, dict):
        raw = raw.get("out")
    if raw is None:
        return None
    to_list = getattr(raw, "tolist", None)
    if callable(to_list):
        data = to_list()
    elif isinstance(raw, list):
        data = raw
    else:
        return None
    if not isinstance(data, list) or not data:
        return None
    logits: Any = data[0] if _logits_are_batched(data) else data
    try:
        return person_mask_from_logits(logits)
    except (TypeError, IndexError, ValueError):
        return None


def segment_people(image: Any) -> list[list[float]] | None:
    """Return an HW person mask for ``image``.

    A successful model is cached. A miss is not, so a later download can
    still paste people.

    Args:
        image: Source still.

    Returns:
        HW mask, or None when the segmenter is off or unavailable.
    """
    global _SEGMENTER
    if person_mask_disabled():
        return None
    if _SEGMENTER is None:
        loaded = load_segmenter()
        if loaded is None:
            return None
        _SEGMENTER = loaded
    return run_deeplab(_SEGMENTER, image)


def _resize_mask(mask: list[list[float]], height: int, width: int) -> list[list[float]]:
    """Nearest-resize an HW mask.

    Args:
        mask: Source mask.
        height: Target height.
        width: Target width.

    Returns:
        Resized mask. Empty input stays empty.
    """
    src_h = len(mask)
    if src_h < 1 or height < 1 or width < 1:
        return []
    src_w = len(mask[0])
    if src_h == height and src_w == width:
        return mask
    out: list[list[float]] = []
    for y in range(height):
        sy = min(src_h - 1, int(y * src_h / height))
        row = mask[sy]
        out.append(
            [float(row[min(src_w - 1, int(x * src_w / width))]) for x in range(width)]
        )
    return out


def _fit_hwc(frame: list[Any], height: int, width: int) -> list[Any]:
    """Nearest-resize one HWC frame to ``height``×``width``.

    Args:
        frame: Source frame.
        height: Target height.
        width: Target width.

    Returns:
        Resized frame.
    """
    src_h = len(frame)
    if src_h < 1 or height < 1 or width < 1:
        return []
    src_w = len(frame[0])
    if src_h == height and src_w == width:
        return frame
    out: list[Any] = []
    for y in range(height):
        sy = min(src_h - 1, int(y * src_h / height))
        row = frame[sy]
        out.append(
            [list(row[min(src_w - 1, int(x * src_w / width))]) for x in range(width)]
        )
    return out


def dilate_mask(mask: list[list[float]], radius: int) -> list[list[float]]:
    """Square dilate. A pixel turns on when any window pixel is on.

    Args:
        mask: HW mask.
        radius: Chebyshev radius. ``0`` copies the mask.

    Returns:
        Dilated mask.
    """
    height = len(mask)
    if height < 1:
        return []
    width = len(mask[0])
    if radius <= 0:
        return [list(row) for row in mask]

    def _dilate_axis(rows: list[list[float]]) -> list[list[float]]:
        """Dilate each row. Out-of-window pixels count as off.

        Args:
            rows: HW mask rows.

        Returns:
            Dilated rows.
        """
        dilated: list[list[float]] = []
        for row in rows:
            prefix = [0.0]
            for value in row:
                prefix.append(prefix[-1] + (1.0 if value >= 0.5 else 0.0))
            new_row: list[float] = []
            count = len(row)
            for index in range(count):
                left = max(0, index - radius)
                right = min(count, index + radius + 1)
                got = prefix[right] - prefix[left]
                new_row.append(1.0 if got > 0 else 0.0)
            dilated.append(new_row)
        return dilated

    horizontal = _dilate_axis(mask)
    transposed = [list(col) for col in zip(*horizontal, strict=False)]
    vertical = _dilate_axis(transposed)
    return [list(col) for col in zip(*vertical, strict=False)]


def feather_mask(mask: list[list[float]], radius: int) -> list[list[float]]:
    """Separable box blur so the paste edge is not a hard cut.

    Args:
        mask: HW mask.
        radius: Blur radius. ``0`` copies the mask.

    Returns:
        Feathered mask in ``0..1``.
    """
    height = len(mask)
    if height < 1:
        return []
    if radius <= 0:
        return [list(row) for row in mask]

    def _blur_axis(rows: list[list[float]]) -> list[list[float]]:
        """Box-blur each row, ignoring samples past the ends.

        Args:
            rows: HW mask rows.

        Returns:
            Blurred rows.
        """
        blurred: list[list[float]] = []
        for row in rows:
            prefix = [0.0]
            for value in row:
                prefix.append(prefix[-1] + float(value))
            new_row: list[float] = []
            count = len(row)
            for index in range(count):
                left = max(0, index - radius)
                right = min(count - 1, index + radius)
                span = right - left + 1
                new_row.append((prefix[right + 1] - prefix[left]) / span)
            blurred.append(new_row)
        return blurred

    horizontal = _blur_axis(mask)
    transposed = [list(col) for col in zip(*horizontal, strict=False)]
    vertical = _blur_axis(transposed)
    return [list(col) for col in zip(*vertical, strict=False)]


def _mask_peak(mask: list[list[float]]) -> float:
    """Return the largest mask value.

    Args:
        mask: HW mask.

    Returns:
        Peak, or 0 when empty.
    """
    peak = 0.0
    for row in mask:
        for value in row:
            if value > peak:
                peak = value
    return peak


def _composite(
    plate: list[Any],
    source: list[Any],
    mask: list[list[float]],
) -> list[Any]:
    """Blend ``source`` over ``plate`` with ``mask``.

    Args:
        plate: Cubic HWC frame.
        source: Photographed HWC frame, same size.
        mask: HW weights.

    Returns:
        Composited HWC frame.
    """
    out: list[Any] = []
    for y, plate_row in enumerate(plate):
        src_row = source[y]
        mask_row = mask[y]
        new_row: list[Any] = []
        for x, plate_px in enumerate(plate_row):
            weight = float(mask_row[x])
            keep = 1.0 - weight
            src_px = src_row[x]
            channels = len(plate_px)
            pixel: list[float] = []
            for index in range(channels):
                src_v = float(src_px[index]) if index < len(src_px) else 0.0
                pixel.append(float(plate_px[index]) * keep + src_v * weight)
            new_row.append(pixel)
        out.append(new_row)
    return out


def reinsert_people(
    plate: Any,
    source: Any,
    prompt: str,
    *,
    segment: Any = None,
) -> tuple[Any, str]:
    """Paste detected people from ``source`` onto ``plate`` for cube prompts.

    Args:
        plate: Decoded cubic (or ordinary) still.
        source: Full-resolution source still from LoadImage.
        prompt: Enhance STRING.
        segment: Optional mask callable. Default is :func:`segment_people`.

    Returns:
        Image (same container kind as ``plate``) and a short status.
    """
    from ez_prompt_enhance.background import is_reconstruction

    text = prompt if isinstance(prompt, str) else str(prompt or "")
    if not is_reconstruction(text):
        return plate, REASON_NOT_CUBIC
    if person_mask_disabled():
        return plate, REASON_OFF
    mask_fn = segment if segment is not None else segment_people
    try:
        mask = mask_fn(source)
    except Exception:  # noqa: BLE001 — fail-soft to the cubic plate
        return plate, REASON_MISSING
    if not mask:
        return plate, REASON_MISSING
    try:
        plate_b = read_bhwc(plate)
        source_b = read_bhwc(source)
    except (TypeError, IndexError, ValueError):
        return plate, REASON_MISSING
    if not plate_b or not source_b:
        return plate, REASON_MISSING
    painted: list[Any] = []
    pasted = False
    for index, frame in enumerate(plate_b):
        if not frame or not frame[0]:
            painted.append(frame)
            continue
        height = len(frame)
        width = len(frame[0])
        src = source_b[index] if index < len(source_b) else source_b[0]
        src = _fit_hwc(src, height, width)
        if not src:
            painted.append(frame)
            continue
        person = _resize_mask(mask, height, width)
        person = dilate_mask(person, DILATE_RADIUS)
        person = feather_mask(person, FEATHER_RADIUS)
        if _mask_peak(person) <= 0.0:
            painted.append(frame)
            continue
        painted.append(_composite(frame, src, person))
        pasted = True
    status = REASON_PASTED if pasted else REASON_NO_PEOPLE
    return write_bhwc(painted, plate), status


class EZReinsertPeople:
    """Paste unmodified people onto a cubic rebuild. Other swaps pass through."""

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        """Return Comfy sockets. Prompt is a link, not an App widget.

        Returns:
            Required plate, source still, and prompt.
        """
        return {
            "required": {
                "plate": ("IMAGE",),
                "source": ("IMAGE",),
                "prompt": ("STRING", {"forceInput": True, "dynamicPrompts": False}),
            }
        }

    # Comfy node contract.
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "run"
    CATEGORY = CATEGORY
    OUTPUT_NODE = True
    DESCRIPTION = (
        "stills/background-swap. Cubic block world pastes detected people "
        "from the source photo onto the rebuilt plate. Other prompts return "
        "the plate unchanged. Missing person weights fail soft."
    )

    def run(self, plate: Any, source: Any, prompt: str) -> dict[str, Any]:
        """Composite people when the prompt is a cube rebuild.

        Args:
            plate: Decoded still.
            source: Full-resolution source still from LoadImage.
            prompt: Enhance STRING.

        Returns:
            OUTPUT_NODE payload. ``result`` is the image the rest of the
            graph saves. ``ui.text`` is the paste status.
        """
        image, status = reinsert_people(plate, source, prompt)
        return {"ui": {"text": (status,)}, "result": (image,)}


NODE_CLASS_MAPPINGS: dict[str, type] = {
    "EZReinsertPeople": EZReinsertPeople,
}
"""Comfy class-name registry for the people paste."""

NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {
    "EZReinsertPeople": "Reinsert people",
}
"""Comfy display-name registry for the people paste."""
