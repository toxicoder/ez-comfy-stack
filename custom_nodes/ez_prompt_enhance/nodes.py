"""ComfyUI nodes: one prompt enhancer per US-safe generation model."""

from __future__ import annotations

from .client import (
    LOCK_IDS,
    LOCK_VIEW,
    NEGATIVE_FAMILIES,
    NEGATIVE_MAX_TOKENS,
    STYLE_IGNORED_MODES,
    STYLE_NONE,
    EnhanceResult,
    _log,
    apply_style_to_prompt,
    complement_negative,
    complete,
    compose_context_user,
    compose_negative_user,
    enhance_prompt,
    flavor_for_system,
    format_style_instruction,
    join_context_fields,
    join_prompt,
    load_system_prompt,
    style_ids,
    with_context_system,
    with_style_system,
)
from .client import _close_llm
from .samples import CUSTOM, resolve_ace_sample, resolve_prompt, sample_combo_labels


_ENHANCE_BOOL = (
    "BOOLEAN",
    {"default": True, "label_on": "On", "label_off": "Off"},
)
_CONTEXT_INPUT = (
    "STRING",
    {"forceInput": True, "dynamicPrompts": False},
)
_CATALOG_INPUT = ("STRING", {"default": "", "multiline": False})


def _sample_input(catalog_id: str) -> tuple:
    return (sample_combo_labels(catalog_id), {"default": CUSTOM})


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def _family_id(value: object) -> str:
    raw = value if isinstance(value, str) else str(value or "klein")
    cleaned = raw.strip().lower()
    if cleaned in NEGATIVE_FAMILIES:
        return cleaned
    return "klein"


def _style_id(value: object) -> str:
    raw = value if isinstance(value, str) else str(value or STYLE_NONE)
    cleaned = raw.strip() or STYLE_NONE
    if cleaned not in style_ids():
        return STYLE_NONE
    return cleaned


def _compose_user(
    prompt: str,
    duration_hint: str,
    audio_notes: str = "",
    context: str = "",
) -> str:
    parts = [compose_context_user(prompt, context)]
    if not parts[0]:
        parts = []
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
    context: str = "",
    sample: object = CUSTOM,
    catalog: object = "",
    node_type: str = "",
) -> dict:
    original = resolve_prompt(
        catalog,
        sample,
        prompt,
        node_type=node_type,
        mode=mode,
    )
    ctx = context if isinstance(context, str) else str(context or "")
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

    user = _compose_user(original, duration_hint, audio_notes, ctx)
    system = load_system_prompt(system_name)
    system = with_context_system(system, ctx)
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
                "sample": _sample_input("klein_t2i"),
                "prompt": (
                    "STRING",
                    {"multiline": True, "default": "", "dynamicPrompts": False},
                ),
                "enhance": _ENHANCE_BOOL,
                "mode": (["t2i", "edit", "identity"], {"default": "t2i"}),
                "duration_hint": ("STRING", {"default": "YouTube 16:9 still"}),
                "style": (style_ids(), {"default": STYLE_NONE}),
                "catalog": _CATALOG_INPUT,
            },
            "optional": {
                "context": _CONTEXT_INPUT,
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Rewrites a lazy prompt for Klein 4B / Qwen3-4B with the on-box "
        "Qwen3-4B-Instruct-2507 GGUF. Modes: t2i, edit, identity (camera-free "
        "bible). Optional context is bible/research (ignored when Enhance is "
        "off). Enhance defaults on. After Queue the CLIP prompt box is the "
        "CLIP string; Enhance status explains passthrough. Fail-soft without "
        "a GGUF (run download-models)."
    )

    def run(
        self,
        prompt,
        enhance,
        mode,
        duration_hint,
        style=STYLE_NONE,
        context="",
        sample=CUSTOM,
        catalog="",
    ):
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
            context=context,
            sample=sample,
            catalog=catalog,
            node_type="EZKleinPromptEnhance",
        )


class EZWanPromptEnhance:
    """Rewrite a lazy prompt for Wan 2.2 TI2V-5B (UMT5, silent)."""

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {
            "required": {
                "sample": _sample_input("wan_t2v"),
                "prompt": (
                    "STRING",
                    {"multiline": True, "default": "", "dynamicPrompts": False},
                ),
                "enhance": _ENHANCE_BOOL,
                "mode": (["t2v", "i2v", "flf", "vace"], {"default": "t2v"}),
                "duration_hint": ("STRING", {"default": "5 seconds, 24 fps"}),
                "style": (style_ids(), {"default": STYLE_NONE}),
                "catalog": _CATALOG_INPUT,
            },
            "optional": {
                "context": _CONTEXT_INPUT,
            },
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
        "Optional context is ignored when Enhance is off. Fail-soft without a GGUF."
    )

    def run(
        self,
        prompt,
        enhance,
        mode,
        duration_hint,
        style=STYLE_NONE,
        context="",
        sample=CUSTOM,
        catalog="",
    ):
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
            context=context,
            sample=sample,
            catalog=catalog,
            node_type="EZWanPromptEnhance",
        )


class EZLTXPromptEnhance:
    """Rewrite a lazy prompt for LTX-2.5 (Gemma4-with-proj, joint AV)."""

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {
            "required": {
                "sample": _sample_input("ltx_t2v"),
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
                "catalog": _CATALOG_INPUT,
            },
            "optional": {
                "context": _CONTEXT_INPUT,
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Rewrites a lazy prompt for LTX-2.5. Flowing present-tense paragraph "
        "with audio interleaved. Style is ignored on I2V. Optional context "
        "(identity/logline) is ignored when Enhance is off. Fail-soft without a GGUF."
    )

    def run(
        self,
        prompt,
        enhance,
        mode,
        duration_hint,
        audio_notes="",
        style=STYLE_NONE,
        context="",
        sample=CUSTOM,
        catalog="",
    ):
        name = "ltx_i2v" if mode == "i2v" else "ltx_t2v"
        return _run(
            name,
            prompt,
            enhance,
            duration_hint,
            audio_notes,
            style=style,
            mode=mode,
            context=context,
            sample=sample,
            catalog=catalog,
            node_type="EZLTXPromptEnhance",
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


class EZContextJoin:
    """Pack labeled desk fields into one context STRING for rewriter nodes."""

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {
            "required": {
                "a": _CONTEXT_INPUT,
                "label_a": ("STRING", {"default": "Logline"}),
                "label_b": ("STRING", {"default": "Script"}),
                "label_c": ("STRING", {"default": "Audio policy"}),
                "label_d": ("STRING", {"default": "Score"}),
            },
            "optional": {
                "b": _CONTEXT_INPUT,
                "c": _CONTEXT_INPUT,
                "d": _CONTEXT_INPUT,
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("context",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    DESCRIPTION = (
        "Joins up to four labeled STRING fields into one context block. "
        "Empty values are omitted. Wire the output into Prompt Enhance context."
    )

    def run(
        self,
        a,
        label_a="Logline",
        label_b="Script",
        label_c="Audio policy",
        label_d="Score",
        b="",
        c="",
        d="",
    ):
        return (
            join_context_fields(
                (str(label_a or "Logline"), a if isinstance(a, str) else str(a or "")),
                (str(label_b or "Script"), b if isinstance(b, str) else str(b or "")),
                (
                    str(label_c or "Audio policy"),
                    c if isinstance(c, str) else str(c or ""),
                ),
                (str(label_d or "Score"), d if isinstance(d, str) else str(d or "")),
            ),
        )


def sanitize_instrumental_lyrics(lyrics: str) -> str:
    """Keep ACE structure tags; fold free-text lines into the brackets.

    ACE-Step sings any non-empty line under a section marker. Instrumental
    scores belong as ``[drop - warped 808]`` (cues inside the brackets) or
    empty-body ``[inst]``.

    Arguments:
        lyrics: Widget lyrics, possibly with production cues as lines.
    Returns:
        Empty-body or cue-in-bracket section tags, or ``[inst]`` if empty.
    """
    text = lyrics.strip() if isinstance(lyrics, str) else str(lyrics or "").strip()
    if not text:
        return "[inst]"
    kept: list[str] = []
    pending_inner: str | None = None
    pending_cues: list[str] = []

    def flush() -> None:
        nonlocal pending_inner, pending_cues
        if pending_inner is None:
            pending_cues = []
            return
        if pending_cues:
            extra = ", ".join(pending_cues)
            if " - " in pending_inner:
                pending_inner = f"{pending_inner}, {extra}"
            else:
                pending_inner = f"{pending_inner} - {extra}"
        kept.append(f"[{pending_inner}]")
        pending_inner = None
        pending_cues = []

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            flush()
            pending_inner = line[1:-1].strip()
            continue
        if pending_inner is None:
            continue
        pending_cues.append(line)
    flush()
    return "\n\n".join(kept) if kept else "[inst]"


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
                "sample": _sample_input("rap_draft"),
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
                "catalog": _CATALOG_INPUT,
            },
            "optional": {
                "context": _CONTEXT_INPUT,
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("tags", "lyrics")
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Rewrites ACE-Step 1.5 tags (genre first) and lyrics. Instrumental "
        "mode forces no-vocals tags and [inst] lyrics. Optional context "
        "(episode script) is ignored when Enhance is off. Enhance defaults on. "
        "Fail-soft without a GGUF."
    )

    def run(
        self,
        tags,
        lyrics,
        enhance=True,
        mode="vocal",
        context="",
        sample=CUSTOM,
        catalog="",
    ):
        original_tags, original_lyrics = resolve_ace_sample(
            catalog,
            sample,
            tags,
            lyrics,
            node_type="EZAceStepPromptEnhance",
            mode=mode,
        )
        ctx = context if isinstance(context, str) else str(context or "")
        instrumental = mode == "instrumental"
        if not _as_bool(enhance):
            if instrumental and "instrumental" not in original_tags.lower():
                original_tags = (
                    f"{original_tags.rstrip(', ')}, instrumental, no vocals"
                    if original_tags.strip()
                    else "instrumental, no vocals"
                )
            if instrumental:
                original_lyrics = sanitize_instrumental_lyrics(original_lyrics)
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
            tag_system = with_context_system(tag_system, ctx)
            out_tags, reason = complete(
                tag_system,
                compose_context_user(original_tags or "instrumental bed", ctx),
            )
            if (out_tags or "").strip():
                rewritten_tags = out_tags.strip()
            if instrumental:
                rewritten_lyrics = sanitize_instrumental_lyrics(
                    original_lyrics.strip() or "[inst]"
                )
            elif original_lyrics.strip():
                lyric_system = with_context_system(
                    load_system_prompt("ace_lyrics"), ctx
                )
                out_lyrics, lyric_reason = complete(
                    lyric_system,
                    compose_context_user(original_lyrics, ctx),
                )
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
                sanitize_instrumental_lyrics(original_lyrics.strip() or "[inst]")
            )
        return _pack_ace(rewritten_tags, rewritten_lyrics, status)


class EZSamplePrompt:
    """STRING source with a sample-prompt combo plus Custom textarea."""

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {
            "required": {
                "sample": _sample_input("forge_lazy"),
                "prompt": (
                    "STRING",
                    {"multiline": True, "default": "", "dynamicPrompts": False},
                ),
                "catalog": _CATALOG_INPUT,
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    DESCRIPTION = (
        "Picks a lab sample prompt or Custom text. Wire into Prompt Enhance "
        "or a desk field. Custom uses the textarea as typed."
    )

    def run(self, prompt, catalog="", sample=CUSTOM):
        return (
            resolve_prompt(
                catalog,
                sample,
                prompt,
                node_type="EZSamplePrompt",
            ),
        )


class EZNegativePromptEnhance:
    """Rewrite a negative CLIP seed so it does not fight the positive."""

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {
            "required": {
                "prompt": (
                    "STRING",
                    {"multiline": True, "default": "", "dynamicPrompts": False},
                ),
                "enhance": _ENHANCE_BOOL,
                "family": (list(NEGATIVE_FAMILIES), {"default": "klein"}),
            },
            "optional": {
                "positive": (
                    "STRING",
                    {"forceInput": True, "dynamicPrompts": False},
                ),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Rewrites a negative CLIP seed against the enhanced positive so the "
        "negative does not fight the intended medium, lighting, or subject. "
        "Keeps watermarks and melt/flicker artifacts. Enhance defaults on. "
        "Fail-soft without a GGUF; a deterministic complement still runs."
    )

    def run(self, prompt, enhance, family="klein", positive=""):
        original = prompt if isinstance(prompt, str) else str(prompt or "")
        pos = positive if isinstance(positive, str) else str(positive or "")
        fam = _family_id(family)
        do_enhance = _as_bool(enhance)
        text = original
        status = ""
        if do_enhance:
            try:
                system = load_system_prompt(f"negative_{fam}")
            except FileNotFoundError as exc:
                _log(f"negative system prompt missing: {exc}")
                system = ""
            if system:
                user = compose_negative_user(original, pos)
                rewritten, reason = complete(
                    system,
                    user,
                    max_tokens=NEGATIVE_MAX_TOKENS,
                )
                if (rewritten or "").strip():
                    text = rewritten.strip()
                else:
                    status = reason or "passthrough"
            else:
                status = "passthrough"
        else:
            status = "enhance off"
        text = complement_negative(text, pos)
        return _pack(EnhanceResult(text, status))


NODE_CLASS_MAPPINGS = {
    "EZKleinPromptEnhance": EZKleinPromptEnhance,
    "EZWanPromptEnhance": EZWanPromptEnhance,
    "EZLTXPromptEnhance": EZLTXPromptEnhance,
    "EZNegativePromptEnhance": EZNegativePromptEnhance,
    "EZPromptJoin": EZPromptJoin,
    "EZContextJoin": EZContextJoin,
    "EZAceStepPromptEnhance": EZAceStepPromptEnhance,
    "EZSamplePrompt": EZSamplePrompt,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EZKleinPromptEnhance": "Klein Prompt Enhance",
    "EZWanPromptEnhance": "Wan Prompt Enhance",
    "EZLTXPromptEnhance": "LTX Prompt Enhance",
    "EZNegativePromptEnhance": "Negative Prompt Enhance",
    "EZPromptJoin": "Prompt Join",
    "EZContextJoin": "Context Join",
    "EZAceStepPromptEnhance": "ACE-Step Prompt Enhance",
    "EZSamplePrompt": "Sample Prompt",
}
