"""ComfyUI nodes: one prompt enhancer per US-safe generation model."""

from __future__ import annotations

from .client import (
    LOCK_IDS,
    LOCK_VIEW,
    REASON_STYLE_IGNORED_I2V,
    STYLE_NONE,
    EnhanceResult,
    _log,
    apply_style_to_prompt,
    enhance_prompt,
    flavor_for_system,
    format_style_instruction,
    join_prompt,
    load_system_prompt,
    style_ids,
    with_style_system,
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
    if apply_style and mode == "i2v":
        apply_style = False
        _log(REASON_STYLE_IGNORED_I2V)

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
                "enhance": ("BOOLEAN", {"default": True}),
                "mode": (["t2i", "edit"], {"default": "t2i"}),
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
        "Qwen3-4B-Instruct-2507 GGUF. Enhance defaults on. After Queue the "
        "CLIP prompt box is the CLIP string; Enhance status explains passthrough. "
        "Fail-soft without a GGUF (run download-models)."
    )

    def run(self, prompt, enhance, mode, duration_hint, style=STYLE_NONE):
        name = "klein_edit" if mode == "edit" else "klein_t2i"
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
                "enhance": ("BOOLEAN", {"default": True}),
                "mode": (["t2v", "i2v"], {"default": "t2v"}),
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
        "camera move; I2V is motion+camera only. No audio. Style is ignored on "
        "I2V. Fail-soft without a GGUF."
    )

    def run(self, prompt, enhance, mode, duration_hint, style=STYLE_NONE):
        name = "wan_i2v" if mode == "i2v" else "wan_t2v"
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
                "enhance": ("BOOLEAN", {"default": True}),
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
        "Joins a shared world bible with a shot card. lock=view is a new camera "
        "of the same place; lock=state keeps framing and changes only light, "
        "grade, or the named action. Inventory is a locked object list."
    )

    def run(self, identity, shot, inventory="", lock=LOCK_VIEW):
        return (join_prompt(identity, shot, inventory, lock),)


NODE_CLASS_MAPPINGS = {
    "EZKleinPromptEnhance": EZKleinPromptEnhance,
    "EZWanPromptEnhance": EZWanPromptEnhance,
    "EZLTXPromptEnhance": EZLTXPromptEnhance,
    "EZPromptJoin": EZPromptJoin,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EZKleinPromptEnhance": "Klein Prompt Enhance",
    "EZWanPromptEnhance": "Wan Prompt Enhance",
    "EZLTXPromptEnhance": "LTX Prompt Enhance",
    "EZPromptJoin": "Prompt Join",
}
