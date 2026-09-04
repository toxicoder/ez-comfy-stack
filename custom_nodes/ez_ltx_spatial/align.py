"""LTX video VAE spatial alignment (32×). Stdlib only; no Comfy import.

The LTX-2.5 video encoder space-to-depth stages require pixel H and W
divisible by 32. Broadcast 720 and 1080 are not (720/16=45, then the next
``/2`` einops split fails). Floor to the multiple, matching T2V ``height//32``.
"""

from __future__ import annotations

from typing import Any

SPATIAL_MULTIPLE = 32
WIDGET_MINIMUM = 64


def snap_dim(
    n: int,
    multiple: int = SPATIAL_MULTIPLE,
    minimum: int = 0,
) -> int:
    """Floor ``n`` to a multiple of ``multiple``.

    Args:
        n: Pixel or widget length.
        multiple: Alignment (LTX VAE is 32).
        minimum: When set, never return below this (widget path uses 64).
            Crop path uses 0 so a side cannot grow.

    Returns:
        Aligned length. May be 0 when ``minimum`` is 0 and ``n < multiple``.
    """
    snapped = (int(n) // int(multiple)) * int(multiple)
    if minimum and snapped < int(minimum):
        return int(minimum)
    return snapped


def snap_hw(
    width: int,
    height: int,
    multiple: int = SPATIAL_MULTIPLE,
    minimum: int = WIDGET_MINIMUM,
) -> tuple[int, int]:
    """Snap a width/height widget pair.

    Args:
        width: Pixel width widget.
        height: Pixel height widget.
        multiple: Alignment.
        minimum: Comfy LTX widget floor (64).

    Returns:
        ``(width, height)`` each floored to ``multiple`` and at least ``minimum``.
    """
    return (
        snap_dim(width, multiple=multiple, minimum=minimum),
        snap_dim(height, multiple=multiple, minimum=minimum),
    )


def center_crop_bcthw(
    x: Any,
    multiple: int = SPATIAL_MULTIPLE,
) -> Any:
    """Center-crop the last two axes of a ``B,C,T,H,W`` (or ``…,H,W``) tensor.

    Never grows a side. If a side is already aligned, or too small to yield a
    positive multiple, that side is left unchanged.

    Args:
        x: Object with ``.shape`` and spatial slicing on the last two axes.
        multiple: Alignment.

    Returns:
        ``x`` unchanged when aligned; otherwise a spatial slice.
    """
    shape = getattr(x, "shape", None)
    if shape is None or len(shape) < 2:
        return x
    height = int(shape[-2])
    width = int(shape[-1])
    h2 = snap_dim(height, multiple=multiple, minimum=0)
    w2 = snap_dim(width, multiple=multiple, minimum=0)
    if h2 <= 0:
        h2 = height
    if w2 <= 0:
        w2 = width
    if h2 == height and w2 == width:
        return x
    y0 = (height - h2) // 2
    x0 = (width - w2) // 2
    return x[..., y0 : y0 + h2, x0 : x0 + w2]
