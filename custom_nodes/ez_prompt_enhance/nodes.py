"""ComfyUI nodes: one prompt enhancer per US-safe generation model."""

from __future__ import annotations

from .client import (
    LOCK_IDS,
    LOCK_VIEW,
    STYLE_IGNORED_MODES,
    STYLE_NONE,
    EnhanceResult,
    _log,
    apply_style_to_prompt,
    complete,
    enhance_prompt,
    flavor_for_system,
    format_style_instruction,
    join_prompt,
    load_system_prompt,
    style_ids,
    with_style_system,
)
from .client import _close_llm


_ENHANCE_BOOL = (
    "BOOLEAN",
    {"default": True, "label_on": "On", "label_off": "Off"},
)


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def _style_id(value: object) -> str:
    raw = value if isinstance(value, str) else str(value or STYLE_NONE)
    cleaned = raw.strip() or STYLE_NONE
    if cleaned not in style_ids():
        return STYLE_NONE
    return cleaned


def _compose_user(prompt: str, duration_hint: str, audio_notes: str = "") -> str:
    parts = [prompt.strip()]
    hint = (duration_hint or "").strip()
    if hint:
        parts.append(f"Duration / framing: {hint}")
    notes = (audio_notes or "").strip()
    if notes:
        parts.append(f"Audio notes: {notes}")
    return "\n\n".join(parts)


def _pack(result: EnhanceResult) -> dict:
    return {
        "ui": {
            "text": (result.text,),
            "passthrough": (result.status,),
        },
        "result": (result.text,),
    }


def _run(
    system_name: str,
    prompt: str,
    enhance: object,
    duration_hint: str,
    audio_notes: str = "",
    style: object = STYLE_NONE,
    mode: str = "",
) -> dict:
    original = prompt if isinstance(prompt, str) else str(prompt)
    do_enhance = _as_bool(enhance)
    style = _style_id(style)
    apply_style = style != STYLE_NONE
    ignored = STYLE_IGNORED_MODES.get(mode)
    if apply_style and ignored:
        apply_style = False
        _log(ignored)

    if not do_enhance:
        text = original
        if apply_style:
            text = apply_style_to_prompt(original, style)
        return _pack(EnhanceResult(text, "enhance off"))

    user = _compose_user(original, duration_hint, audio_notes)
    system = load_system_prompt(system_name)
    if apply_style:
        instruction = format_style_instruction(style, flavor_for_system(system_name))
        if instruction:
            user = f"{user}\n\n{instruction}"
        system = with_style_system(system, style)
    out = enhance_prompt(
        system,
        user,
        enhance=True,
        fallback=original,
    )
    if apply_style:
        out = EnhanceResult(apply_style_to_prompt(out.text, style), out.reason)
    return _pack(out)


class EZKleinPromptEnhance:
    """Rewrite a lazy still/edit prompt for FLUX.2 Klein 4B (Qwen3-4B)."""

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {
            "required": {
                "prompt": (
                    "STRING",
                    {"multiline": True, "default": "", "dynamicPrompts": False},
                ),
                "enhance": _ENHANCE_BOOL,
                "mode": (["t2i", "edit", "identity"], {"default": "t2i"}),
                "duration_hint": ("STRING", {"default": "YouTube 16:9 still"}),
                "style": (style_ids(), {"default": STYLE_NONE}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Rewrites a lazy prompt for Klein 4B / Qwen3-4B with the on-box "
        "Qwen3-4B-Instruct-2507 GGUF. Modes: t2i, edit, identity (camera-free "
        "bible). Enhance defaults on. After Queue the CLIP prompt box is the "
        "CLIP string; Enhance status explains passthrough. Fail-soft without "
        "a GGUF (run download-models)."
    )

    def run(self, prompt, enhance, mode, duration_hint, style=STYLE_NONE):
        if mode == "edit":
            name = "klein_edit"
        elif mode == "identity":
            name = "klein_identity"
        else:
            name = "klein_t2i"
        return _run(
            name,
            prompt,
            enhance,
            duration_hint,
            style=style,
            mode=mode,
        )


class EZWanPromptEnhance:
    """Rewrite a lazy prompt for Wan 2.2 TI2V-5B (UMT5, silent)."""

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {
            "required": {
                "prompt": (
                    "STRING",
                    {"multiline": True, "default": "", "dynamicPrompts": False},
                ),
                "enhance": _ENHANCE_BOOL,
                "mode": (["t2v", "i2v", "flf", "vace"], {"default": "t2v"}),
                "duration_hint": ("STRING", {"default": "5 seconds, 24 fps"}),
                "style": (style_ids(), {"default": STYLE_NONE}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Rewrites a lazy prompt for Wan 2.2 TI2V-5B. T2V is look+motion+one "
        "camera move; I2V is motion+camera only; flf is Fun InP first-last; "
        "vace is join/inpaint. No audio. Style is ignored on I2V/flf/vace. "
        "Fail-soft without a GGUF."
    )

    def run(self, prompt, enhance, mode, duration_hint, style=STYLE_NONE):
        if mode == "i2v":
            name = "wan_i2v"
        elif mode == "flf":
            name = "wan_flf"
        elif mode == "vace":
            name = "wan_vace"
        else:
            name = "wan_t2v"
        return _run(
            name,
            prompt,
            enhance,
            duration_hint,
            style=style,
            mode=mode,
        )


class EZLTXPromptEnhance:
    """Rewrite a lazy prompt for LTX-2.5 (Gemma4-with-proj, joint AV)."""

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {
            "required": {
                "prompt": (
                    "STRING",
                    {"multiline": True, "default": "", "dynamicPrompts": False},
                ),
                "enhance": _ENHANCE_BOOL,
                "mode": (["t2v", "i2v"], {"default": "t2v"}),
                "duration_hint": ("STRING", {"default": "5 seconds, 24 fps"}),
                "audio_notes": (
                    "STRING",
                    {"multiline": True, "default": "", "dynamicPrompts": False},
                ),
                "style": (style_ids(), {"default": STYLE_NONE}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Rewrites a lazy prompt for LTX-2.5. Flowing present-tense paragraph "
        "with audio interleaved. Style is ignored on I2V. Fail-soft without a GGUF."
    )

    def run(self, prompt, enhance, mode, duration_hint, audio_notes="", style=STYLE_NONE):
        name = "ltx_i2v" if mode == "i2v" else "ltx_t2v"
        return _run(
            name,
            prompt,
            enhance,
            duration_hint,
            audio_notes,
            style=style,
            mode=mode,
        )


class EZPromptJoin:
    """Join a shared identity paragraph with a shot-specific camera line."""

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {
            "required": {
                "identity": (
                    "STRING",
                    {
                        "multiline": True,
                        "forceInput": True,
                        "dynamicPrompts": False,
                    },
                ),
                "shot": (
                    "STRING",
                    {"multiline": True, "default": "", "dynamicPrompts": False},
                ),
                "inventory": (
                    "STRING",
                    {"multiline": True, "default": "", "dynamicPrompts": False},
                ),
                "lock": (list(LOCK_IDS), {"default": LOCK_VIEW}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    DESCRIPTION = (
        "Joins a shared world bible with a shot card. lock=view front-loads the "
        "shot so Klein sees a new camera in a walkthrough of the same place; "
        "lock=state keeps framing and changes only light, grade, or the named "
        "action. Inventory is a locked object list."
    )

    def run(self, identity, shot, inventory="", lock=LOCK_VIEW):
        return (join_prompt(identity, shot, inventory, lock),)


def _pack_ace(tags: str, lyrics: str, status: str) -> dict:
    preview = tags if not lyrics.strip() else f"{tags}\n---\n{lyrics}"
    return {
        "ui": {
            "text": (preview,),
            "passthrough": (status,),
        },
        "result": (tags, lyrics),
    }


class EZAceStepPromptEnhance:
    """Rewrite ACE-Step 1.5 tags and lyrics with the on-box GGUF."""

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {
            "required": {
                "tags": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "boom bap, hip-hop, dusty drums, 88 bpm",
                        "dynamicPrompts": False,
                    },
                ),
                "lyrics": (
                    "STRING",
                    {"multiline": True, "default": "", "dynamicPrompts": False},
                ),
                "enhance": _ENHANCE_BOOL,
                "mode": (["vocal", "instrumental"], {"default": "vocal"}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("tags", "lyrics")
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Rewrites ACE-Step 1.5 tags (genre first) and lyrics. Instrumental "
        "mode forces no-vocals tags and [inst] lyrics. Enhance defaults on. "
        "Fail-soft without a GGUF."
    )

    def run(self, tags, lyrics, enhance=True, mode="vocal"):
        original_tags = tags if isinstance(tags, str) else str(tags or "")
        original_lyrics = lyrics if isinstance(lyrics, str) else str(lyrics or "")
        instrumental = mode == "instrumental"
        if not _as_bool(enhance):
            if instrumental and "instrumental" not in original_tags.lower():
                original_tags = (
                    f"{original_tags.rstrip(', ')}, instrumental, no vocals"
                    if original_tags.strip()
                    else "instrumental, no vocals"
                )
            if instrumental and not original_lyrics.strip():
                original_lyrics = "[inst]"
            return _pack_ace(original_tags, original_lyrics, "enhance off")
        try:
            tag_system = load_system_prompt(
                "ace_instrumental" if instrumental else "ace_tags"
            )
        except FileNotFoundError as exc:
            _log(f"ACE system prompt missing: {exc}")
            return _pack_ace(original_tags, original_lyrics, "passthrough")
        rewritten_tags = original_tags
        rewritten_lyrics = original_lyrics
        reason = None
        try:
            out_tags, reason = complete(tag_system, original_tags or "instrumental bed")
            if (out_tags or "").strip():
                rewritten_tags = out_tags.strip()
            if instrumental:
                rewritten_lyrics = original_lyrics.strip() or "[inst]"
            elif original_lyrics.strip():
                lyric_system = load_system_prompt("ace_lyrics")
                out_lyrics, lyric_reason = complete(lyric_system, original_lyrics)
                if (out_lyrics or "").strip():
                    rewritten_lyrics = out_lyrics.strip()
                elif lyric_reason:
                    reason = reason or lyric_reason
        finally:
            try:
                _close_llm()
            except Exception as exc:  # noqa: BLE001 — unload is best-effort
                _log(f"ACE writer unload failed: {exc}")
        if instrumental and "instrumental" not in rewritten_tags.lower():
            rewritten_tags = f"{rewritten_tags.rstrip(', ')}, instrumental, no vocals"
        status = ""
        if not (rewritten_tags or "").strip() or (
            rewritten_tags == original_tags and reason
        ):
            status = reason or "passthrough"
            rewritten_tags = original_tags
            rewritten_lyrics = original_lyrics if not instrumental else (
                original_lyrics.strip() or "[inst]"
            )
        return _pack_ace(rewritten_tags, rewritten_lyrics, status)


NODE_CLASS_MAPPINGS = {
    "EZKleinPromptEnhance": EZKleinPromptEnhance,
    "EZWanPromptEnhance": EZWanPromptEnhance,
    "EZLTXPromptEnhance": EZLTXPromptEnhance,
    "EZPromptJoin": EZPromptJoin,
    "EZAceStepPromptEnhance": EZAceStepPromptEnhance,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EZKleinPromptEnhance": "Klein Prompt Enhance",
    "EZWanPromptEnhance": "Wan Prompt Enhance",
    "EZLTXPromptEnhance": "LTX Prompt Enhance",
    "EZPromptJoin": "Prompt Join",
    "EZAceStepPromptEnhance": "ACE-Step Prompt Enhance",
}
