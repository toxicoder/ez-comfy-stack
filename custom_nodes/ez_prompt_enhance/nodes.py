"""ComfyUI nodes: one prompt enhancer per US-safe generation model."""

from __future__ import annotations

from .client import enhance_prompt, load_system_prompt


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def _compose_user(prompt: str, duration_hint: str, audio_notes: str = "") -> str:
    parts = [prompt.strip()]
    hint = (duration_hint or "").strip()
    if hint:
        parts.append(f"Duration / framing: {hint}")
    notes = (audio_notes or "").strip()
    if notes:
        parts.append(f"Audio notes: {notes}")
    return "\n\n".join(parts)


def _run(system_name: str, prompt: str, enhance: object, duration_hint: str, audio_notes: str = "") -> dict:
    original = prompt if isinstance(prompt, str) else str(prompt)
    do_enhance = _as_bool(enhance)
    if not do_enhance:
        return {"ui": {"text": [original]}, "result": (original,)}
    user = _compose_user(original, duration_hint, audio_notes)
    out = enhance_prompt(load_system_prompt(system_name), user, enhance=True)
    return {"ui": {"text": [out]}, "result": (out,)}


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
                "enhance": ("BOOLEAN", {"default": False}),
                "mode": (["t2i", "edit"], {"default": "t2i"}),
                "duration_hint": ("STRING", {"default": "YouTube 16:9 still"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    DESCRIPTION = (
        "Rewrites a lazy prompt for Klein 4B / Qwen3-4B. Off-box Grok when "
        "Enhance is on and XAI_API_KEY is set; otherwise passes the prompt through."
    )

    def run(self, prompt, enhance, mode, duration_hint):
        name = "klein_edit" if mode == "edit" else "klein_t2i"
        return _run(name, prompt, enhance, duration_hint)


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
                "enhance": ("BOOLEAN", {"default": False}),
                "mode": (["t2v", "i2v"], {"default": "t2v"}),
                "duration_hint": ("STRING", {"default": "5 seconds, 24 fps"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    DESCRIPTION = (
        "Rewrites a lazy prompt for Wan 2.2 TI2V-5B. T2V is look+motion+one "
        "camera move; I2V is motion+camera only. No audio. Fail-soft without a key."
    )

    def run(self, prompt, enhance, mode, duration_hint):
        name = "wan_i2v" if mode == "i2v" else "wan_t2v"
        return _run(name, prompt, enhance, duration_hint)


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
                "enhance": ("BOOLEAN", {"default": False}),
                "mode": (["t2v", "i2v"], {"default": "t2v"}),
                "duration_hint": ("STRING", {"default": "5 seconds, 24 fps"}),
                "audio_notes": (
                    "STRING",
                    {"multiline": True, "default": "", "dynamicPrompts": False},
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    DESCRIPTION = (
        "Rewrites a lazy prompt for LTX-2.5. Flowing present-tense paragraph "
        "with audio interleaved. Fail-soft without XAI_API_KEY."
    )

    def run(self, prompt, enhance, mode, duration_hint, audio_notes=""):
        name = "ltx_i2v" if mode == "i2v" else "ltx_t2v"
        return _run(name, prompt, enhance, duration_hint, audio_notes)


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
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    DESCRIPTION = (
        "Joins a shared identity paragraph with a shot-specific camera line "
        "so one Queue can vary views without duplicating the subject bible."
    )

    def run(self, identity, shot):
        a = (identity if isinstance(identity, str) else str(identity)).strip()
        b = (shot if isinstance(shot, str) else str(shot)).strip()
        if a and b:
            return (f"{a} {b}",)
        return (a or b,)


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
