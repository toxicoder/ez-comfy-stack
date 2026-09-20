"""Bare lettering wraps into a Klein text-swap CLIP instruction."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_prompt_enhance.lettering import (  # noqa: E402
    LETTERING_LOCK,
    is_lettering_instruction,
    wrap_text_swap_prompt,
)
from ez_prompt_enhance.nodes import EZKleinPromptEnhance  # noqa: E402
from ez_prompt_enhance import client  # noqa: E402


def test_wrap_bare_lettering_and_passthrough_instructions() -> None:
    wrapped = wrap_text_swap_prompt("HELLO")
    assert wrapped.startswith("Replace the visible lettering with: HELLO.")
    assert LETTERING_LOCK in wrapped
    assert wrap_text_swap_prompt("  OPEN  ").startswith(
        "Replace the visible lettering with: OPEN."
    )
    targeted = "Replace SALE with OPEN"
    assert wrap_text_swap_prompt(targeted) == targeted
    full = (
        "Replace the visible lettering with: CLOSED. Keep the same typeface, "
        "weight, color, size, tracking, perspective, material, lighting, and "
        "every other pixel of the image. Spell CLOSED exactly."
    )
    assert wrap_text_swap_prompt(full) == full
    assert wrap_text_swap_prompt("") == ""
    assert wrap_text_swap_prompt(None) == ""
    assert is_lettering_instruction(targeted)
    assert not is_lettering_instruction("HELLO")
    assert wrap_text_swap_prompt(42).startswith("Replace the visible lettering with: 42.")
    assert is_lettering_instruction("") is False
    assert is_lettering_instruction("the visible lettering with: WAVE") is True
    lock = (
        "Keep typeface and tracking. Spell HELLO. Lock every other pixel of the image."
    )
    assert is_lettering_instruction(lock) is True


def test_klein_text_swap_wraps_when_enhance_is_off() -> None:
    klein = EZKleinPromptEnhance()
    off = klein.run("HELLO", False, "text_swap", "match the source still")
    assert off["result"][0].startswith("Replace the visible lettering with: HELLO.")
    with patch.object(client, "complete", return_value=("rewritten-swap", None)) as mock:
        klein.run("OPEN", True, "text_swap", "match the source still", "none")
    user = mock.call_args[0][1]
    assert "Replace the visible lettering with: OPEN." in user
