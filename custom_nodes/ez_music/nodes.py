"""ComfyUI node for US-safe original rap lyrics (ACE-Step encoder companion)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
FLAVOR_RAP = "rap_lyrics"

DRAFT_LYRICS = """[intro]
yeah
local signal
on the box

[verse]
Fan stays loud on a quiet street
Weights on disk, no rented beat
Card runs hot, the cut stays clean
If it ships from here it stays unseen

[chorus]
Own the booth, own the stack
No ghost in the hook, no borrowed track
Spark in the rack, the master comes back"""

FULL_LYRICS = """[intro]
yeah
local signal
on the box

[verse]
Fan stays loud on a quiet street
Weights on disk, no rented beat
Card runs hot, the cut stays clean
If it ships from here it stays unseen

[chorus]
Own the booth, own the stack
No ghost in the hook, no borrowed track
Spark in the rack, the master comes back

[verse]
Rack light blinks on a solo take
No rented hook, no leased name
Bars stay tight, the booth stays mine
Stamp the master, keep the line

[chorus]
Own the booth, own the stack
No ghost in the hook, no borrowed track
Spark in the rack, the master comes back

[outro]
yeah
local signal
cut"""


def _log(message: str) -> None:
    print(f"[ez_music] {message}", file=sys.stderr)


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return bool(value)
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def load_writer_prompt(name: str = FLAVOR_RAP) -> str:
    """Load the rap-lyrics system prompt from this pack.

    Arguments:
        name: stem without .txt (default ``rap_lyrics``).
    Returns:
        File contents stripped of trailing whitespace.
    Raises:
        FileNotFoundError if the prompt file is missing.
    """
    stem = name if name else FLAVOR_RAP
    path = PROMPTS_DIR / f"{stem}.txt"
    return path.read_text(encoding="utf-8").strip()


def _pack_text(text: str, status: str) -> dict[str, Any]:
    return {
        "ui": {"text": (text,), "passthrough": (status,)},
        "result": (text,),
    }


class EZRapLyrics:
    """Draft original rap lyrics via the on-box GGUF. Enhance defaults off."""

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {
            "required": {
                "lyrics": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": DRAFT_LYRICS,
                        "dynamicPrompts": False,
                    },
                ),
                "enhance": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("lyrics",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/music"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Rewrites lab-original rap lyrics with the on-box Qwen3-4B-Instruct "
        "GGUF. Enhance defaults off so Queue works offline. Missing GGUF "
        "passes the widget text through. Forbids living-MC names and famous "
        "hooks. ACE-Step still invents the vocal timbre from tags plus lyrics."
    )

    def run(self, lyrics, enhance=False):
        original = lyrics if isinstance(lyrics, str) else str(lyrics)
        if not _as_bool(enhance):
            return _pack_text(original, "enhance off")
        try:
            from ez_prompt_enhance.client import _close_llm
            from ez_prompt_enhance.client import complete
        except Exception as exc:  # noqa: BLE001 — fail-soft
            _log(f"prompt enhance client unavailable: {exc}")
            return _pack_text(original, "llama.cpp unavailable")
        try:
            system = load_writer_prompt(FLAVOR_RAP)
        except FileNotFoundError as exc:
            _log(f"rap lyrics prompt missing: {exc}")
            return _pack_text(original, "passthrough")
        try:
            rewritten, reason = complete(system, original)
        finally:
            try:
                _close_llm()
            except Exception as exc:  # noqa: BLE001 — unload is best-effort
                _log(f"writer unload failed: {exc}")
        if not (rewritten or "").strip():
            return _pack_text(original, reason or "passthrough")
        return _pack_text(rewritten, "")


NODE_CLASS_MAPPINGS = {
    "EZRapLyrics": EZRapLyrics,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EZRapLyrics": "Rap Lyrics",
}
