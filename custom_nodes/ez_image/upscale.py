"""Resolve still upscale targets (hermetic: stdlib only)."""

from __future__ import annotations

# Combo ids (widget values). none is a tensor passthrough.
UPSCALE_NONE = "none"
UPSCALE_2X = "2x"
UPSCALE_4X = "4x"
UPSCALE_4K = "4K"
UPSCALE_IDS: tuple[str, ...] = (
    UPSCALE_NONE,
    UPSCALE_2X,
    UPSCALE_4X,
    UPSCALE_4K,
)
"""Stable combo values for EZImageUpscale."""

DEFAULT_UPSCALE = UPSCALE_NONE
"""App / graph default: pass the decoded still through."""

# 4K delivery box (landscape). Portrait uses the swapped pair.
BOX_LANDSCAPE: tuple[int, int] = (3840, 2160)
BOX_PORTRAIT: tuple[int, int] = (2160, 3840)


def _as_str(value: object) -> str:
    """Coerce a combo widget to a stripped string.

    Args:
        value: Combo value or None.

    Returns:
        Stripped string, or empty.
    """
    if isinstance(value, str):
        return value.strip()
    if value is None:
        return ""
    return str(value).strip()


def normalize_upscale(value: object) -> str:
    """Return a known upscale id, defaulting to none.

    Args:
        value: Combo id or label (``2×`` accepted as ``2x``).

    Returns:
        One of :data:`UPSCALE_IDS`.
    """
    raw = _as_str(value)
    if not raw:
        return DEFAULT_UPSCALE
    folded = raw.replace("×", "x").replace(" ", "")
    lower = folded.casefold()
    if lower in {UPSCALE_NONE, "off", "passthrough"}:
        return UPSCALE_NONE
    if lower in {UPSCALE_2X, "2"}:
        return UPSCALE_2X
    if lower in {UPSCALE_4X, "4"}:
        return UPSCALE_4X
    if lower in {UPSCALE_4K.casefold(), "4k", "uhd", "2160p"}:
        return UPSCALE_4K
    return DEFAULT_UPSCALE


def upscale_combo_labels() -> list[str]:
    """Return combo values in widget order.

    Returns:
        Copy of :data:`UPSCALE_IDS`.
    """
    return list(UPSCALE_IDS)


def _fit_box(width: int, height: int, box_w: int, box_h: int) -> tuple[int, int]:
    """Scale ``width``×``height`` to fit inside the box (integer pixels).

    Args:
        width: Source width.
        height: Source height.
        box_w: Maximum width.
        box_h: Maximum height.

    Returns:
        Target width and height, at least 1.
    """
    src_w = max(int(width), 1)
    src_h = max(int(height), 1)
    scale = min(box_w / src_w, box_h / src_h)
    out_w = max(int(round(src_w * scale)), 1)
    out_h = max(int(round(src_h * scale)), 1)
    return out_w, out_h


def resolve_upscale_hw(
    width: int, height: int, mode: object
) -> tuple[int, int] | None:
    """Return target H×W, or ``None`` when the still should pass through.

    Args:
        width: Source width in pixels.
        height: Source height in pixels.
        mode: Upscale combo value.

    Returns:
        ``(width, height)`` to resize to, or ``None`` for a no-op.
    """
    kind = normalize_upscale(mode)
    src_w = max(int(width), 1)
    src_h = max(int(height), 1)
    if kind == UPSCALE_NONE:
        return None
    if kind == UPSCALE_2X:
        return src_w * 2, src_h * 2
    if kind == UPSCALE_4X:
        return src_w * 4, src_h * 4
    box_w, box_h = BOX_LANDSCAPE if src_w >= src_h else BOX_PORTRAIT
    out_w, out_h = _fit_box(src_w, src_h, box_w, box_h)
    if out_w == src_w and out_h == src_h:
        return None
    return out_w, out_h
