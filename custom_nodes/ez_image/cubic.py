"""Block-study reference for Cubic block world, and the Klein condition router.

Ordinary background swaps still attach the photograph. A cube / voxel /
block-world prompt attaches a coarse cube picture of that photo instead, so
Klein is not locked to photoreal surfaces.
"""

from __future__ import annotations

from typing import Any

CATEGORY = "ez-comfy/image"
"""Comfy menu category for the cubic reference router."""

CELL_DIVISOR = 36
"""Block study cell is about ``min(side) / CELL_DIVISOR``."""
CELL_MIN = 12
"""Smallest block-study cell, in pixels."""
CELL_MAX = 40
"""Largest block-study cell, in pixels."""
QUANT_STEPS = 4
"""Five palette levels (0, 0.25, 0.5, 0.75, 1)."""
BEVEL = 0.2
"""Fraction of each cell that reads as a lit top or a shaded bottom."""
LIGHTEN = 0.25
"""How far a lit cube face moves toward white."""
DARKEN = 0.65
"""Scale applied to a shaded cube face."""


def cell_size(height: int, width: int) -> int:
    """Return the block-study cell for a still of this size.

    Args:
        height: Pixel height.
        width: Pixel width.

    Returns:
        Cell edge in pixels, clamped to 12-40.
    """
    side = max(1, min(int(height), int(width)))
    raw = int(round(side / CELL_DIVISOR))
    if raw < CELL_MIN:
        return CELL_MIN
    if raw > CELL_MAX:
        return CELL_MAX
    return raw


def _try_torch() -> Any:
    """Import torch when the Comfy environment has it.

    Returns:
        The torch module, or None when import fails.
    """
    try:
        import torch
    except Exception:  # noqa: BLE001 - hermetic tests
        return None
    return torch


def _is_hwc(data: list[Any]) -> bool:
    """True when ``data`` is HWC (a pixel is numbers, not a list).

    Args:
        data: Nested list from a tensor or a test image.

    Returns:
        Whether the first pixel channel is numeric.
    """
    try:
        return isinstance(data[0][0][0], (int, float))
    except (TypeError, IndexError):
        return False


def read_bhwc(image: Any) -> list[Any]:
    """Copy a Comfy IMAGE or nested list into BHWC Python lists.

    Args:
        image: BHWC tensor, HWC tensor, or nested lists.

    Returns:
        Batch of HWC float images.

    Raises:
        TypeError: ``image`` has no readable pixels.
    """
    if isinstance(image, list):
        data: Any = image
    else:
        current = image
        detach = getattr(current, "detach", None)
        if callable(detach):
            current = detach()
        cpu = getattr(current, "cpu", None)
        if callable(cpu):
            current = cpu()
        to_list = getattr(current, "tolist", None)
        if not callable(to_list):
            raise TypeError("image has no pixels")
        data = to_list()
    if not isinstance(data, list):
        raise TypeError("image pixels are not a list")
    if not data:
        return []
    if _is_hwc(data):
        return [data]
    return data


def write_bhwc(data: list[Any], like: Any) -> Any:
    """Return ``data`` as a tensor when ``like`` is one, else the lists.

    Args:
        data: BHWC nested lists.
        like: Image that supplied the pixels (tensor or list).

    Returns:
        Torch tensor matching ``like`` when torch and a device are present,
        otherwise ``data``.
    """
    torch = _try_torch()
    device = getattr(like, "device", None)
    dtype = getattr(like, "dtype", None)
    if torch is not None and device is not None and dtype is not None:
        return torch.tensor(data, dtype=dtype, device=device)
    return data


def _quantize_channel(value: float) -> float:
    """Snap one channel onto five levels in ``0..1``.

    Args:
        value: Source channel.

    Returns:
        Quantized channel.
    """
    if value < 0.0:
        clamped = 0.0
    elif value > 1.0:
        clamped = 1.0
    else:
        clamped = float(value)
    return round(clamped * QUANT_STEPS) / QUANT_STEPS


def _mean_color(image: list[Any], y0: int, y1: int, x0: int, x1: int) -> list[float]:
    """Average the pixels in a cell.

    Args:
        image: One HWC frame.
        y0: Inclusive top.
        y1: Exclusive bottom.
        x0: Inclusive left.
        x1: Exclusive right.

    Returns:
        Quantized mean color.
    """
    channels = len(image[y0][x0])
    totals = [0.0] * channels
    count = 0
    for y in range(y0, y1):
        row = image[y]
        for x in range(x0, x1):
            pixel = row[x]
            for index in range(channels):
                totals[index] += float(pixel[index])
            count += 1
    return [_quantize_channel(total / count) for total in totals]


def _shade(color: list[float], scale: float, lift: float) -> list[float]:
    """Lighten or darken a quantized cube face.

    Args:
        color: Base face color.
        scale: Multiply (1 keeps the color).
        lift: Add toward white after scaling.

    Returns:
        Shaded color clamped to ``0..1``.
    """
    shaded: list[float] = []
    for channel in color:
        value = channel * scale + lift
        if value > 1.0:
            value = 1.0
        shaded.append(value)
    return shaded


def _paint_cell(
    frame: list[Any],
    color: list[float],
    y0: int,
    y1: int,
    x0: int,
    x1: int,
) -> None:
    """Write one beveled cube face into ``frame``.

    Args:
        frame: Output HWC image, mutated.
        color: Quantized face color.
        y0: Inclusive top.
        y1: Exclusive bottom.
        x0: Inclusive left.
        x1: Exclusive right.
    """
    height = y1 - y0
    band = max(1, int(round(height * BEVEL)))
    lit = _shade(color, 1.0, LIGHTEN)
    shaded = _shade(color, DARKEN, 0.0)
    for y in range(y0, y1):
        rel = y - y0
        if rel < band:
            face = lit
        elif rel >= height - band:
            face = shaded
        else:
            face = color
        row = frame[y]
        for x in range(x0, x1):
            row[x] = list(face)


def block_study_frame(image: list[Any]) -> list[Any]:
    """Rebuild one HWC frame as a coarse beveled cube grid.

    Args:
        image: Source HWC frame.

    Returns:
        New HWC frame. Empty input returns an empty list.
    """
    if not image or not image[0] or not image[0][0]:
        return []
    height = len(image)
    width = len(image[0])
    channels = len(image[0][0])
    frame: list[Any] = [
        [[0.0] * channels for _x in range(width)] for _y in range(height)
    ]
    cell = cell_size(height, width)
    y0 = 0
    while y0 < height:
        y1 = min(height, y0 + cell)
        x0 = 0
        while x0 < width:
            x1 = min(width, x0 + cell)
            color = _mean_color(image, y0, y1, x0, x1)
            _paint_cell(frame, color, y0, y1, x0, x1)
            x0 = x1
        y0 = y1
    return frame


def block_study(image: Any) -> Any:
    """Return a coarse cube picture of ``image`` (same layout, cube faces).

    Args:
        image: Comfy IMAGE tensor or BHWC/HWC lists.

    Returns:
        Block study in the same container kind as ``image`` when it is a tensor.
    """
    batch = read_bhwc(image)
    painted = [block_study_frame(frame) for frame in batch]
    return write_bhwc(painted, image)


def _erase_frame(
    frame: list[Any], mask: list[list[float]], radius: int
) -> list[Any]:
    """Fill one frame's masked pixels with blurred, re-quantized colors.

    Args:
        frame: Block-study HWC frame.
        mask: HW mask, ``>= 0.5`` where a person stands.
        radius: Box-blur radius in pixels for the fill color.

    Returns:
        New HWC frame. Masked pixels hold the blurred frame's color snapped
        onto the five-level palette; other pixels copy the frame.
    """
    # Lazy import: ez_image.person_mask imports this module at top level.
    from ez_image.person_mask import feather_mask

    height = len(frame)
    width = len(frame[0])
    channels = len(frame[0][0])
    planes: list[list[list[float]]] = []
    for channel in range(channels):
        plane = [
            [float(frame[y][x][channel]) for x in range(width)]
            for y in range(height)
        ]
        planes.append(feather_mask(plane, radius))
    out: list[Any] = []
    for y in range(height):
        row: list[Any] = []
        for x in range(width):
            if mask[y][x] >= 0.5:
                row.append([_quantize_channel(planes[c][y][x]) for c in range(channels)])
            else:
                row.append(list(frame[y][x]))
        out.append(row)
    return out


def erase_people(study: Any, image: Any) -> Any:
    """Erase the source's people from a block study.

    Person pixels of ``study`` are filled with a large-kernel blur of the
    study itself, re-quantized to the five-level palette, so the study shows
    a plausible background where the people stood instead of cubed figures.
    Fails soft: when the segmenter is unavailable or finds no person pixels,
    ``study`` is returned unchanged.

    Args:
        study: Block-study IMAGE in the container kind ``block_study`` gives
            back (tensor or lists).
        image: Source still the person mask is computed for.

    Returns:
        The study with person pixels filled, in the same container kind as
        ``study``; unchanged ``study`` when nothing is erased.
    """
    frames = read_bhwc(study)
    if not frames or not frames[0] or not frames[0][0]:
        return study
    # Lazy import: ez_image.person_mask imports this module at top level.
    from ez_image.person_mask import _resize_mask, segment_people

    mask = segment_people(image)
    if not mask:
        return study
    height = len(frames[0])
    width = len(frames[0][0])
    resized = _resize_mask(mask, height, width)
    if not resized or not any(v >= 0.5 for row in resized for v in row):
        return study
    radius = cell_size(height, width)
    painted = [_erase_frame(frame, resized, radius) for frame in frames]
    return write_bhwc(painted, study)


def _clone_conditioning(conditioning: Any) -> Any:
    """Copy a conditioning list so a reference attach cannot alias it.

    Args:
        conditioning: Comfy conditioning, or anything else.

    Returns:
        A shallow copy of each cond dict. Non-lists pass through.
    """
    if not isinstance(conditioning, list):
        return conditioning
    cloned: list[Any] = []
    for item in conditioning:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            meta = item[1]
            if isinstance(meta, dict):
                meta_copy = dict(meta)
                refs = meta_copy.get("reference_latents")
                if isinstance(refs, list):
                    meta_copy["reference_latents"] = list(refs)
            else:
                meta_copy = meta
            cloned.append([item[0], meta_copy])
        else:
            cloned.append(item)
    return cloned


def _attach_fallback(conditioning: Any, latent: Any) -> Any:
    """Record ``latent`` on conditioning when Comfy ReferenceLatent is absent.

    Args:
        conditioning: Already cloned conditioning.
        latent: Photo or block-study latent.

    Returns:
        Conditioning with the latent attached, or ``conditioning`` unchanged.
    """
    if isinstance(conditioning, list):
        for item in conditioning:
            if (
                isinstance(item, list)
                and len(item) >= 2
                and isinstance(item[1], dict)
            ):
                refs = list(item[1].get("reference_latents") or [])
                refs.append(latent)
                item[1]["reference_latents"] = refs
        return conditioning
    if isinstance(conditioning, dict):
        out = dict(conditioning)
        out["reference"] = latent
        return out
    return conditioning


def attach_reference(conditioning: Any, latent: Any) -> Any:
    """Attach ``latent`` as a Flux.2 reference without mutating the input.

    Args:
        conditioning: Positive conditioning from CLIP.
        latent: Encoded photo or block study.

    Returns:
        Conditioning that carries ``latent``.
    """
    cloned = _clone_conditioning(conditioning)
    try:
        from comfy_extras.nodes_flux import ReferenceLatent  # type: ignore[import-not-found]
    except Exception:  # noqa: BLE001 - hermetic tests / older Comfy
        return _attach_fallback(cloned, latent)
    try:
        node = ReferenceLatent()
        result = node.append(cloned, latent)
    except Exception:  # noqa: BLE001 - fail-soft to the dict attach
        return _attach_fallback(cloned, latent)
    if isinstance(result, tuple):
        return result[0]
    return result


def _encode_image(image: Any, vae: Any) -> Any | None:
    """VAE-encode ``image``.

    Args:
        image: Block-study IMAGE.
        vae: Object with ``encode``.

    Returns:
        Latent, or None when encode is missing or fails.
    """
    encode = getattr(vae, "encode", None)
    if not callable(encode):
        return None
    try:
        return encode(image)
    except Exception:  # noqa: BLE001 - fail-soft to the photo reference
        return None


class EZCubicCondition:
    """Photo reference for place swaps; block-study reference for cube rebuilds."""

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        """Return Comfy sockets. Prompt is a link, not an App widget.

        Returns:
            Required conditioning, photo latent, snapped image, VAE, and prompt.
        """
        return {
            "required": {
                "conditioning": ("CONDITIONING",),
                "latent": ("LATENT",),
                "image": ("IMAGE",),
                "vae": ("VAE",),
                "prompt": ("STRING", {"forceInput": True, "dynamicPrompts": False}),
            }
        }

    # Comfy node contract.
    RETURN_TYPES = ("CONDITIONING",)
    RETURN_NAMES = ("conditioning",)
    FUNCTION = "run"
    CATEGORY = CATEGORY
    DESCRIPTION = (
        "stills/background-swap. Ordinary place prompts attach the encoded "
        "photo. Cube, voxel, and block-world prompts attach a coarse block "
        "study of that photo so Klein rebuilds the place instead of copying it."
    )

    def run(
        self,
        conditioning: Any,
        latent: Any,
        image: Any,
        vae: Any,
        prompt: str,
    ) -> tuple[Any]:
        """Pick the photo latent or a block-study latent.

        Args:
            conditioning: Positive CLIP conditioning (no reference yet).
            latent: VAE encode of the snapped photograph.
            image: Snapped source still.
            vae: Flux.2 VAE.
            prompt: Enhance STRING (already wrapped).

        Returns:
            One-tuple of conditioning with exactly one reference latent.
        """
        from ez_prompt_enhance.background import is_reconstruction

        text = prompt if isinstance(prompt, str) else str(prompt or "")
        if not is_reconstruction(text):
            return (attach_reference(conditioning, latent),)
        try:
            study = block_study(image)
            study = erase_people(study, image)
            encoded = _encode_image(study, vae)
        except Exception:  # noqa: BLE001 - keep the photo reference
            encoded = None
        if encoded is None:
            return (attach_reference(conditioning, latent),)
        return (attach_reference(conditioning, encoded),)


NODE_CLASS_MAPPINGS: dict[str, type] = {
    "EZCubicCondition": EZCubicCondition,
}
"""Comfy class-name registry for the cubic reference router."""

NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {
    "EZCubicCondition": "Cubic or photo reference",
}
"""Comfy display-name registry for the cubic reference router."""
