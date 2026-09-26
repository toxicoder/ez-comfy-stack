"""Enhance-node widget order (matches Comfy INPUT_TYPES required keys).

``_enhance_mode`` used to guess the mode index from list length (5-wide vs
7-wide). Look up ``mode`` by name instead.
"""

from __future__ import annotations

from typing import Mapping

# Visual families that include a mode combo (Klein / Wan / LongCat).
VISUAL_WITH_MODE: tuple[str, ...] = (
    "sample",
    "prompt",
    "enhance",
    "mode",
    "duration_hint",
    "style",
    "catalog",
)
# Z-Image omits mode.
VISUAL_ZIMAGE: tuple[str, ...] = (
    "sample",
    "prompt",
    "enhance",
    "duration_hint",
    "style",
    "catalog",
)
# LTX inserts audio_notes before style (mode stays).
VISUAL_AUDIO: tuple[str, ...] = (
    "sample",
    "prompt",
    "enhance",
    "mode",
    "duration_hint",
    "audio_notes",
    "style",
    "catalog",
)
# DreamX has audio_notes but no mode combo (hardcoded i2v).
VISUAL_AUDIO_NO_MODE: tuple[str, ...] = (
    "sample",
    "prompt",
    "enhance",
    "duration_hint",
    "audio_notes",
    "style",
    "catalog",
)
ACE_ORDER: tuple[str, ...] = (
    "sample",
    "tags",
    "lyrics",
    "enhance",
    "mode",
    "catalog",
)

ENHANCE_WIDGET_ORDER: dict[str, tuple[str, ...]] = {
    "EZKleinPromptEnhance": VISUAL_WITH_MODE,
    "EZWanPromptEnhance": VISUAL_WITH_MODE,
    "EZLongCatPromptEnhance": VISUAL_WITH_MODE,
    "EZZimagePromptEnhance": VISUAL_ZIMAGE,
    "EZLTXPromptEnhance": VISUAL_AUDIO,
    "EZDreamXPromptEnhance": VISUAL_AUDIO_NO_MODE,
    "EZAceStepPromptEnhance": ACE_ORDER,
}

DEFAULT_MODE: dict[str, str] = {
    "EZZimagePromptEnhance": "t2i",
    "EZDreamXPromptEnhance": "i2v",
}


def enhance_widget_index(ntype: str, name: str) -> int | None:
    """Return the widgets_values index for ``name``, or None.

    Args:
        ntype: Comfy class_type.
        name: Widget name.

    Returns:
        Index into ``widgets_values``, or None when the type has no such widget.
    """
    order = ENHANCE_WIDGET_ORDER.get(ntype)
    if order is None or name not in order:
        return None
    return order.index(name)


def enhance_mode(node: Mapping[str, object]) -> str:
    """Return the enhance node's mode widget (t2i / i2v / vocal / ...).

    Args:
        node: Serialized Comfy node.

    Returns:
        Mode id, a family default, or empty string.
    """
    ntype = str(node.get("type") or "")
    raw = node.get("widgets_values")
    values = list(raw) if isinstance(raw, list) else []
    idx = enhance_widget_index(ntype, "mode")
    if idx is not None:
        if len(values) > idx:
            return str(values[idx])
        return ""
    return DEFAULT_MODE.get(ntype, "")
