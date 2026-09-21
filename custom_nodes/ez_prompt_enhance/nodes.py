"""ComfyUI nodes: one prompt enhancer per US-safe generation model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

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
    with_audio_system,
    with_cinema_system,
    with_context_system,
    with_style_system,
)
from .client import _close_llm
from .audio import (
    FLAVOR_ACE_VOCAL,
    FLAVORS as AUDIO_FLAVORS,
    NONE as AUDIO_NONE,
    WIDGET_AXIS_ORDER as AUDIO_WIDGET_AXIS_ORDER,
    combo_ids as audio_combo_ids,
    format_notes as audio_format_notes,
    recipe_combo_ids as audio_recipe_combo_ids,
    splice as audio_splice,
)
from .cinema import (
    FLAVOR_KLEIN,
    FLAVORS,
    NONE as CINEMA_NONE,
    WIDGET_AXIS_ORDER,
    combo_ids,
    format_notes,
    recipe_combo_ids,
    splice,
)
from .background import (
    BACKGROUND_MODES,
    REASON_PRECISE_BACKGROUND,
    format_background_cast,
    is_background_instruction,
    splice_source_caption,
    wrap_background_prompt,
)
from .describe import describe_image, last_status as describe_last_status
from .lettering import wrap_text_swap_prompt
from .samples import CUSTOM, resolve_ace_sample, resolve_prompt, sample_combo_labels

KLEIN_MODE_COMBO = [
    "t2i",
    "edit",
    "identity",
    "text_swap",
    "background_swap",
    "background_edit",
]
"""Klein Prompt Enhance mode combo; EZImageMode.enhance_mode must match."""

if TYPE_CHECKING:
    from ez_common import ComfyInputTypes

# Shared Comfy widget specs (boolean, optional context, hidden catalog).
_ENHANCE_BOOL = (
    "BOOLEAN",
    {"default": True, "label_on": "On", "label_off": "Off"},
)
_CONTEXT_INPUT = (
    "STRING",
    {"forceInput": True, "dynamicPrompts": False},
)
_CATALOG_INPUT = ("STRING", {"default": "", "multiline": False})


def _visual_input_types(
    *,
    catalog_id: str,
    duration_default: str,
    modes: list[str] | None = None,
    audio_notes: bool = False,
) -> ComfyInputTypes:
    """Build the shared visual Enhance widget map (stable key order).

    Args:
        catalog_id: Default sample catalog stem.
        duration_default: Duration / framing widget default.
        modes: Mode combo list. ``None`` omits the mode widget (Z-Image).
        audio_notes: Insert the LTX/DreamX audio_notes widget before style.

    Returns:
        Comfy ``INPUT_TYPES`` payload.
    """
    required: dict[str, Any] = {
        "sample": _sample_input(catalog_id),
        "prompt": (
            "STRING",
            {"multiline": True, "default": "", "dynamicPrompts": False},
        ),
        "enhance": _ENHANCE_BOOL,
    }
    if modes:
        required["mode"] = (list(modes), {"default": modes[0]})
    required["duration_hint"] = ("STRING", {"default": duration_default})
    if audio_notes:
        required["audio_notes"] = (
            "STRING",
            {"multiline": True, "default": "", "dynamicPrompts": False},
        )
    required["style"] = (style_ids(), {"default": STYLE_NONE})
    required["catalog"] = _CATALOG_INPUT
    return {
        "required": required,
        "optional": {
            "context": _CONTEXT_INPUT,
            "image_desc": (
                "STRING",
                {"forceInput": True, "dynamicPrompts": False},
            ),
        },
    }


def _sample_input(catalog_id: str) -> tuple[list[str], dict[str, str]]:
    """Combo widget: union of sample labels, preferred catalog first.

    Args:
        catalog_id: Family default catalog stem.

    Returns:
        ``(labels, {default: custom})`` widget spec.
    """
    return (sample_combo_labels(catalog_id), {"default": CUSTOM})


def _as_bool(value: object) -> bool:
    """Parse a Comfy BOOLEAN widget.

    Args:
        value: Bool, number, or yes/no string.

    Returns:
        Parsed flag; unrecognized strings are False.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def _family_id(value: object) -> str:
    """Normalize a negative-prompt family combo.

    Args:
        value: Widget value.

    Returns:
        Known family id, or ``klein``.
    """
    raw = value if isinstance(value, str) else str(value or "klein")
    cleaned = raw.strip().lower()
    if cleaned in NEGATIVE_FAMILIES:
        return cleaned
    return "klein"


def _style_id(value: object) -> str:
    """Normalize a style combo.

    Args:
        value: Widget value.

    Returns:
        Catalog id, or ``none`` when unknown.
    """
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
    """Build the rewriter user message from widgets.

    Args:
        prompt: Resolved operator prompt.
        duration_hint: Duration / framing line.
        audio_notes: Optional LTX/DreamX audio notes.
        context: Optional bible/research block.

    Returns:
        User message with optional duration, audio, and Context sections.
    """
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


def _pack(result: EnhanceResult) -> dict[str, Any]:
    """Pack a single-string Enhance result for Comfy.

    Args:
        result: Rewritten text plus passthrough reason.

    Returns:
        OUTPUT_NODE payload with ``ui`` and ``result``.
    """
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
    image_desc: str = "",
    background_cast: str = "",
) -> dict[str, Any]:
    """Resolve sample, optionally rewrite, and pack CLIP text.

    Args:
        system_name: Prompt file stem under ``prompts/``.
        prompt: Custom textarea when the sample combo is Custom.
        enhance: BOOLEAN widget; off is fail-soft passthrough.
        duration_hint: Duration / framing line.
        audio_notes: Optional audio notes for AV families.
        style: Style catalog id or none.
        mode: Family mode (i2v/flf/…) used to ignore style.
        context: Optional supporting STRING.
        sample: Sample combo label.
        catalog: Hidden catalog widget.
        node_type: Comfy class name for family catalog fallback.
        image_desc: Optional still caption from EZImageDescribe.
        background_cast: Optional compact token from EZBackgroundCast.

    Returns:
        Packed Enhance payload. LLM miss returns the original prompt.
    """
    original = resolve_prompt(
        catalog,
        sample,
        prompt,
        node_type=node_type,
        mode=mode,
    )
    precise_background = False
    if mode == "text_swap":
        original = wrap_text_swap_prompt(original)
    elif mode in BACKGROUND_MODES:
        precise_background = is_background_instruction(original)
        original = wrap_background_prompt(original, mode, background_cast)
    ctx = context if isinstance(context, str) else str(context or "")
    caption = image_desc if isinstance(image_desc, str) else str(image_desc or "")
    if mode in BACKGROUND_MODES:
        original = splice_source_caption(original, caption)
    if caption.strip():
        ctx = join_context_fields(("Context", ctx), ("Image", caption))
    do_enhance = _as_bool(enhance)
    style = _style_id(style)
    apply_style = style != STYLE_NONE
    ignored = STYLE_IGNORED_MODES.get(mode)
    if apply_style and ignored:
        apply_style = False
        _log(ignored)

    skip_precise = bool(precise_background and do_enhance)
    if skip_precise:
        do_enhance = False

    if not do_enhance:
        text = original
        if apply_style:
            text = apply_style_to_prompt(original, style)
        status = REASON_PRECISE_BACKGROUND if skip_precise else "enhance off"
        return _pack(EnhanceResult(text, status))

    user = _compose_user(original, duration_hint, audio_notes, ctx)
    system = load_system_prompt(system_name)
    system = with_cinema_system(system, system_name, mode)
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
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for Klein still/edit/lettering/background.

        Returns:
            Required and optional widget map.
        """
        types = _visual_input_types(
            catalog_id="klein_t2i",
            duration_default="YouTube 16:9 still",
            modes=list(KLEIN_MODE_COMBO),
        )
        optional = dict(types.get("optional") or {})
        optional["background_cast"] = _CONTEXT_INPUT
        return {
            "required": types["required"],
            "optional": optional,
        }

    # Comfy node registration fields.
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Rewrites a lazy prompt for Klein 4B / Qwen3-4B with the on-box "
        "Qwen3-4B-Instruct-2507 GGUF. Modes: t2i, edit, identity (camera-free "
        "bible), text_swap (glyph-lock lettering), background_swap (replace "
        "environment including ground), background_edit (restyle environment). "
        "Named background samples skip the rewriter (precise instruction). "
        "Optional context is bible/research (ignored when Enhance is "
        "off). Enhance defaults on. After Queue the CLIP prompt box is the "
        "CLIP string; Enhance status explains passthrough. Fail-soft without "
        "a GGUF (run download-models)."
    )

    def run(
        self,
        prompt: str,
        enhance: object,
        mode: str,
        duration_hint: str,
        style: object = STYLE_NONE,
        context: str = "",
        sample: object = CUSTOM,
        catalog: object = "",
        image_desc: str = "",
        background_cast: str = "",
    ) -> dict[str, Any]:
        """Rewrite a Klein still/edit/identity prompt.

        Args:
            prompt: Custom textarea used when sample is Custom.
            enhance: BOOLEAN; off returns the resolved prompt (style may still apply).
            mode: ``t2i``, ``edit``, ``identity``, ``text_swap``, ``background_swap``,
                or ``background_edit``.
            duration_hint: Framing line (e.g. YouTube 16:9 still).
            style: Style catalog id or none.
            context: Optional bible/research STRING.
            sample: Sample combo label.
            catalog: Hidden catalog widget.
            image_desc: Optional still caption from EZImageDescribe.
            background_cast: Optional compact token from EZBackgroundCast.

        Returns:
            Packed CLIP prompt and Enhance status.
        """
        if mode == "edit":
            name = "klein_edit"
        elif mode == "identity":
            name = "klein_identity"
        elif mode == "text_swap":
            name = "klein_text_swap"
        elif mode == "background_swap":
            name = "klein_background_swap"
        elif mode == "background_edit":
            name = "klein_background_edit"
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
            image_desc=image_desc,
            background_cast=background_cast,
        )


class EZWanPromptEnhance:
    """Rewrite a lazy prompt for Wan 2.2 TI2V-5B (UMT5, silent)."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for Wan t2v/i2v/flf/vace/s2v.

        Returns:
            Required and optional widget map.
        """
        return _visual_input_types(
            catalog_id="wan_t2v",
            duration_default="5 seconds, 24 fps",
            modes=["t2v", "i2v", "flf", "vace", "s2v"],
        )

    # Comfy node registration fields.
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Rewrites a lazy prompt for Wan 2.2 TI2V-5B / A14B / Fun InP / VACE / "
        "S2V. T2V is look+motion+one camera move; I2V is motion+camera only; "
        "flf is Fun InP first-last; vace is join/inpaint; s2v is talking-head "
        "(wav owns lip-sync). No audio except s2v. Style is ignored on "
        "I2V/flf/vace/s2v. Optional context is ignored when Enhance is off. "
        "Fail-soft without a GGUF."
    )

    def run(
        self,
        prompt: str,
        enhance: object,
        mode: str,
        duration_hint: str,
        style: object = STYLE_NONE,
        context: str = "",
        sample: object = CUSTOM,
        catalog: object = "",
        image_desc: str = "",
    ) -> dict[str, Any]:
        """Rewrite a Wan video prompt.

        Args:
            prompt: Custom textarea used when sample is Custom.
            enhance: BOOLEAN; off returns the resolved prompt (style may still apply).
            mode: ``t2v``, ``i2v``, ``flf``, ``vace``, or ``s2v``.
            duration_hint: Duration / fps line.
            style: Style catalog id or none (ignored on i2v/flf/vace/s2v).
            context: Optional supporting STRING.
            sample: Sample combo label.
            catalog: Hidden catalog widget.
            image_desc: Optional still caption from EZImageDescribe.

        Returns:
            Packed CLIP prompt and Enhance status.
        """
        if mode == "i2v":
            name = "wan_i2v"
        elif mode == "flf":
            name = "wan_flf"
        elif mode == "vace":
            name = "wan_vace"
        elif mode == "s2v":
            name = "wan_s2v"
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
            image_desc=image_desc,
        )


class EZLTXPromptEnhance:
    """Rewrite a lazy prompt for LTX-2.5 (Gemma4-with-proj, joint AV)."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for LTX t2v/i2v/iclora.

        Returns:
            Required and optional widget map.
        """
        return _visual_input_types(
            catalog_id="ltx_t2v",
            duration_default="8 seconds, 24 fps",
            modes=["t2v", "i2v", "iclora"],
            audio_notes=True,
        )

    # Comfy node registration fields.
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Rewrites a lazy prompt for LTX-2.5. Flowing present-tense paragraph "
        "with audio interleaved. iclora describes look/materials, not the "
        "control type. Style is ignored on I2V. Optional context "
        "(identity/logline) is ignored when Enhance is off. Fail-soft without a GGUF."
    )

    def run(
        self,
        prompt: str,
        enhance: object,
        mode: str,
        duration_hint: str,
        audio_notes: str = "",
        style: object = STYLE_NONE,
        context: str = "",
        sample: object = CUSTOM,
        catalog: object = "",
        image_desc: str = "",
    ) -> dict[str, Any]:
        """Rewrite an LTX joint-AV prompt.

        Args:
            prompt: Custom textarea used when sample is Custom.
            enhance: BOOLEAN; off returns the resolved prompt (style may still apply).
            mode: ``t2v``, ``i2v``, or ``iclora``.
            duration_hint: Duration / fps line.
            audio_notes: Optional acoustic events.
            style: Style catalog id or none (ignored on i2v).
            context: Optional identity/logline STRING.
            sample: Sample combo label.
            catalog: Hidden catalog widget.
            image_desc: Optional still caption from EZImageDescribe.

        Returns:
            Packed CLIP prompt and Enhance status.
        """
        if mode == "i2v":
            name = "ltx_i2v"
        elif mode == "iclora":
            name = "ltx_iclora"
        else:
            name = "ltx_t2v"
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
            image_desc=image_desc,
        )


class EZPromptJoin:
    """Join a shared identity paragraph with a shot-specific camera line."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for identity/shot join.

        Returns:
            Required widget map.
        """
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

    # Comfy node registration fields.
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

    def run(
        self,
        identity: str,
        shot: str,
        inventory: str = "",
        lock: str = LOCK_VIEW,
    ) -> tuple[str]:
        """Join bible, inventory, persist lock, and shot line.

        Args:
            identity: Camera-free place/subject bible.
            shot: Camera, light, or action line for this still.
            inventory: Object list that must repeat across views.
            lock: ``view`` (new camera) or ``state`` (same camera).

        Returns:
            One-element CLIP tuple.
        """
        return (join_prompt(identity, shot, inventory, lock),)


class EZContextJoin:
    """Pack labeled desk fields into one context STRING for rewriter nodes."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for labeled context fields.

        Returns:
            Required and optional widget map.
        """
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

    # Comfy node registration fields.
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
        a: object,
        label_a: object = "Logline",
        label_b: object = "Script",
        label_c: object = "Audio policy",
        label_d: object = "Score",
        b: object = "",
        c: object = "",
        d: object = "",
    ) -> tuple[str]:
        """Join up to four labeled STRING fields.

        Args:
            a: First context field (required input).
            label_a: Label for ``a``.
            label_b: Label for ``b``.
            label_c: Label for ``c``.
            label_d: Label for ``d``.
            b: Optional second field.
            c: Optional third field.
            d: Optional fourth field.

        Returns:
            One-element context tuple (empty fields omitted).
        """
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

    Args:
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
        """Emit the current section tag with any pending cue lines."""
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


def _pack_ace(tags: str, lyrics: str, status: str) -> dict[str, Any]:
    """Pack ACE-Step tags and lyrics for Comfy.

    Args:
        tags: Genre-first tag string.
        lyrics: Section-tagged lyrics or ``[inst]``.
        status: Enhance passthrough reason, or empty.

    Returns:
        OUTPUT_NODE payload with ``ui`` preview and ``(tags, lyrics)``.
    """
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
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for ACE-Step tags/lyrics.

        Returns:
            Required and optional widget map.
        """
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

    # Comfy node registration fields.
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
        tags: str,
        lyrics: str,
        enhance: object = True,
        mode: str = "vocal",
        context: str = "",
        sample: object = CUSTOM,
        catalog: object = "",
    ) -> dict[str, Any]:
        """Rewrite ACE-Step tags and lyrics.

        Args:
            tags: Custom tags when sample is Custom.
            lyrics: Custom lyrics when sample is Custom.
            enhance: BOOLEAN; off sanitizes instrumental lyrics only.
            mode: ``vocal`` or ``instrumental``.
            context: Optional episode-script STRING.
            sample: Sample combo label.
            catalog: Hidden catalog widget.

        Returns:
            Packed tags/lyrics and Enhance status. Fail-soft without a GGUF.
        """
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
            tag_system = with_audio_system(
                tag_system,
                "ace_instrumental" if instrumental else "ace_tags",
                mode,
            )
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
                lyric_system = with_audio_system(
                    load_system_prompt("ace_lyrics"), "ace_lyrics", mode
                )
                lyric_system = with_context_system(lyric_system, ctx)
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


class EZZimagePromptEnhance:
    """Rewrite a lazy still prompt for Z-Image Turbo (Qwen3-4B)."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for Z-Image Turbo t2i.

        Returns:
            Required and optional widget map.
        """
        return _visual_input_types(
            catalog_id="klein_t2i",
            duration_default="YouTube 16:9 still",
        )

    # Comfy node registration fields.
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Rewrites a lazy prompt for Z-Image Turbo (Qwen3-4B chat wrap). "
        "Turbo ignores a separate negative CLIP; exclusions stay in the "
        "positive. Optional context is ignored when Enhance is off. "
        "Fail-soft without a GGUF."
    )

    def run(
        self,
        prompt: str,
        enhance: object,
        duration_hint: str,
        style: object = STYLE_NONE,
        context: str = "",
        sample: object = CUSTOM,
        catalog: object = "",
        image_desc: str = "",
    ) -> dict[str, Any]:
        """Rewrite a Z-Image Turbo still prompt.

        Args:
            prompt: Custom textarea used when sample is Custom.
            enhance: BOOLEAN; off returns the resolved prompt (style may still apply).
            duration_hint: Framing line.
            style: Style catalog id or none.
            context: Optional supporting STRING.
            sample: Sample combo label.
            catalog: Hidden catalog widget.
            image_desc: Optional still caption from EZImageDescribe.

        Returns:
            Packed CLIP prompt and Enhance status.
        """
        return _run(
            "zimage_t2i",
            prompt,
            enhance,
            duration_hint,
            style=style,
            mode="t2i",
            context=context,
            sample=sample,
            catalog=catalog,
            node_type="EZZimagePromptEnhance",
            image_desc=image_desc,
        )


class EZLongCatPromptEnhance:
    """Rewrite a lazy prompt for LongCat-Video (T2V / I2V / continuation)."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for LongCat t2v/i2v/vc.

        Returns:
            Required and optional widget map.
        """
        return _visual_input_types(
            catalog_id="wan_t2v",
            duration_default="5 seconds, 30 fps",
            modes=["t2v", "i2v", "vc"],
        )

    # Comfy node registration fields.
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Rewrites a lazy prompt for LongCat-Video. T2V is scene+motion+"
        "cinematography; I2V extends the still; vc continues previous frames. "
        "No native audio. Style is ignored on I2V/vc. Optional context is "
        "ignored when Enhance is off. Fail-soft without a GGUF."
    )

    def run(
        self,
        prompt: str,
        enhance: object,
        mode: str,
        duration_hint: str,
        style: object = STYLE_NONE,
        context: str = "",
        sample: object = CUSTOM,
        catalog: object = "",
        image_desc: str = "",
    ) -> dict[str, Any]:
        """Rewrite a LongCat-Video prompt.

        Args:
            prompt: Custom textarea used when sample is Custom.
            enhance: BOOLEAN; off returns the resolved prompt (style may still apply).
            mode: ``t2v``, ``i2v``, or ``vc``.
            duration_hint: Duration / fps line.
            style: Style catalog id or none (ignored on i2v/vc).
            context: Optional supporting STRING.
            sample: Sample combo label.
            catalog: Hidden catalog widget.
            image_desc: Optional still caption from EZImageDescribe.

        Returns:
            Packed CLIP prompt and Enhance status.
        """
        if mode == "i2v":
            name = "longcat_i2v"
        elif mode == "vc":
            name = "longcat_vc"
        else:
            name = "longcat_t2v"
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
            node_type="EZLongCatPromptEnhance",
            image_desc=image_desc,
        )


class EZDreamXPromptEnhance:
    """Rewrite a lazy first-frame+text prompt for DreamX-Creator (UMT5, joint AV)."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for DreamX i2v.

        Returns:
            Required and optional widget map.
        """
        return _visual_input_types(
            catalog_id="ltx_i2v",
            duration_default="5 seconds, 24 fps",
            audio_notes=True,
        )

    # Comfy node registration fields.
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Rewrites a lazy prompt for DreamX-Creator. First frame owns look; "
        "the paragraph is visual dynamics plus interleaved acoustic events. "
        "Style is ignored (start image owns look). Optional context is "
        "ignored when Enhance is off. Fail-soft without a GGUF."
    )

    def run(
        self,
        prompt: str,
        enhance: object,
        duration_hint: str,
        audio_notes: str = "",
        style: object = STYLE_NONE,
        context: str = "",
        sample: object = CUSTOM,
        catalog: object = "",
        image_desc: str = "",
    ) -> dict[str, Any]:
        """Rewrite a DreamX first-frame+text prompt.

        Args:
            prompt: Custom textarea used when sample is Custom.
            enhance: BOOLEAN; off returns the resolved prompt (style ignored on i2v).
            duration_hint: Duration / fps line.
            audio_notes: Optional acoustic events.
            style: Style catalog id or none (ignored; start image owns look).
            context: Optional supporting STRING.
            sample: Sample combo label.
            catalog: Hidden catalog widget.
            image_desc: Optional still caption from EZImageDescribe.

        Returns:
            Packed CLIP prompt and Enhance status.
        """
        return _run(
            "dreamx_i2v",
            prompt,
            enhance,
            duration_hint,
            audio_notes,
            style=style,
            mode="i2v",
            context=context,
            sample=sample,
            catalog=catalog,
            node_type="EZDreamXPromptEnhance",
            image_desc=image_desc,
        )


class EZSamplePrompt:
    """STRING source with a sample-prompt combo plus Custom textarea."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for the sample-prompt source.

        Returns:
            Required widget map.
        """
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

    # Comfy node registration fields.
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    DESCRIPTION = (
        "Picks a lab sample prompt or Custom text. Wire into Prompt Enhance "
        "or a desk field. Custom uses the textarea as typed."
    )

    def run(
        self,
        prompt: str,
        catalog: object = "",
        sample: object = CUSTOM,
    ) -> tuple[str]:
        """Resolve a sample combo or Custom textarea.

        Args:
            prompt: Custom textarea used when sample is Custom.
            catalog: Hidden catalog widget.
            sample: Sample combo label.

        Returns:
            One-element prompt tuple.
        """
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
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for negative CLIP rewrite.

        Returns:
            Required and optional widget map.
        """
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

    # Comfy node registration fields.
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Rewrites a negative CLIP seed against the final positive so the "
        "negative does not fight the intended medium, lighting, subject, or "
        "audio. Keeps anatomy and watermark artifacts unless the positive "
        "asked for that body. Enhance defaults on and stays on when Rewrite "
        "prompt is off. Fail-soft without a GGUF; a deterministic complement "
        "still runs."
    )

    def run(
        self,
        prompt: object,
        enhance: object,
        family: object = "klein",
        positive: object = "",
    ) -> dict[str, Any]:
        """Rewrite a negative CLIP seed against the positive.

        Args:
            prompt: Negative seed textarea.
            enhance: BOOLEAN; off still runs deterministic complement.
            family: Negative prompt family (klein/wan/ltx/…).
            positive: Optional CLIP-bound positive STRING.

        Returns:
            Packed negative prompt and Enhance status.
        """
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
                system = with_cinema_system(system, f"negative_{fam}")
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


# Optional STRING inputs on EZPromptBundle. Films wire 18 shot prompts.
BUNDLE_INPUTS = 24


class EZPromptBundle:
    """Concatenate final prompt strings for one shared negative."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return up to 24 forceInput STRING sockets.

        Returns:
            Optional widget map. Unconnected sockets are omitted at run time.
        """
        optional: dict[str, tuple[object, ...]] = {}
        for index in range(1, BUNDLE_INPUTS + 1):
            optional[f"text_{index:02d}"] = (
                "STRING",
                {"forceInput": True, "dynamicPrompts": False},
            )
        return {"required": {}, "optional": optional}

    # Comfy node registration fields.
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    DESCRIPTION = (
        "Joins final prompt strings for one shared negative. No LLM. "
        "Empty inputs are skipped. Wire each shot's CLIP source here."
    )

    def run(self, **texts: object) -> tuple[str]:
        """Join non-empty prompt strings in slot order.

        Args:
            **texts: ``text_01`` … ``text_24`` STRING values.

        Returns:
            One string, paragraphs separated by a blank line.
        """
        parts: list[str] = []
        for index in range(1, BUNDLE_INPUTS + 1):
            raw = texts.get(f"text_{index:02d}", "")
            text = raw if isinstance(raw, str) else str(raw or "")
            cleaned = text.strip()
            if cleaned:
                parts.append(cleaned)
        return ("\n\n".join(parts),)


class EZCinemaRack:
    """Pick one technique per cinematography axis and splice a CLIP string."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for Cinema Rack axes.

        Returns:
            Required widget map (subject, flavor, recipe, 13 axes).
        """
        required: dict[str, tuple[object, ...]] = {
            "subject": (
                "STRING",
                {
                    "multiline": True,
                    "default": "",
                    "dynamicPrompts": False,
                },
            ),
            "flavor": (list(FLAVORS), {"default": FLAVOR_KLEIN}),
            "recipe": (recipe_combo_ids(), {"default": CINEMA_NONE}),
        }
        for axis_id in WIDGET_AXIS_ORDER:
            required[axis_id] = (combo_ids(axis_id), {"default": CINEMA_NONE})
        return {"required": required}

    # Comfy node registration fields.
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("prompt", "notes")
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Splice one pick per cinematography axis into a Klein, Wan, or LTX "
        "prompt. Recipe fills empty axes only. Wan emits one camera verb. "
        "I2V drops look axes so the start image owns grade. Editing is omitted "
        "on stills. No LLM."
    )

    def run(
        self,
        subject: object,
        flavor: object = FLAVOR_KLEIN,
        recipe: object = CINEMA_NONE,
        **axes: object,
    ) -> tuple[str, str]:
        """Splice axis picks into a model-native CLIP string.

        Args:
            subject: Optional front-loaded subject sentence.
            flavor: Klein / Wan / LTX flavor id.
            recipe: Named splice that fills empty axes only.
            **axes: One technique id per cinematography axis.

        Returns:
            Prompt text and operator notes (drops, Wan camera).
        """
        picks = {
            axis_id: str(axes.get(axis_id, CINEMA_NONE) or CINEMA_NONE)
            for axis_id in WIDGET_AXIS_ORDER
        }
        result = splice(
            picks,
            flavor=flavor if isinstance(flavor, str) else FLAVOR_KLEIN,
            subject=subject if isinstance(subject, str) else str(subject or ""),
            recipe=recipe if isinstance(recipe, str) else CINEMA_NONE,
        )
        return (result.text, format_notes(result))


class EZAudioRack:
    """Pick one technique per audio axis and splice ACE tags and lyrics form."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for Audio Rack axes.

        Returns:
            Required widget map (brief, flavor, recipe, 13 axes).
        """
        required: dict[str, tuple[object, ...]] = {
            "brief": (
                "STRING",
                {
                    "multiline": True,
                    "default": "",
                    "dynamicPrompts": False,
                },
            ),
            "flavor": (list(AUDIO_FLAVORS), {"default": FLAVOR_ACE_VOCAL}),
            "recipe": (audio_recipe_combo_ids(), {"default": AUDIO_NONE}),
        }
        for axis_id in AUDIO_WIDGET_AXIS_ORDER:
            required[axis_id] = (audio_combo_ids(axis_id), {"default": AUDIO_NONE})
        return {"required": required}

    # Comfy node registration fields.
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("tags", "lyrics", "notes")
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Splice one pick per audio/music axis into ACE-Step tags and lyrics "
        "form. Recipe fills empty axes only. Vocal identity is omitted on "
        "instrumental and podcast-bed flavors. Instrumental forces no-vocals "
        "tags and [inst] form. Exactly one BPM when tempo is picked. No LLM."
    )

    def run(
        self,
        brief: object,
        flavor: object = FLAVOR_ACE_VOCAL,
        recipe: object = AUDIO_NONE,
        **axes: object,
    ) -> tuple[str, str, str]:
        """Splice axis picks into ACE tags and lyrics form.

        Args:
            brief: Optional lyrics seed. Ignored on instrumental flavors.
            flavor: ace_vocal / ace_instrumental / podcast_bed.
            recipe: Named splice that fills empty axes only.
            **axes: One technique id per audio axis.

        Returns:
            Tags, lyrics form, and operator notes (drops, BPM).
        """
        picks = {
            axis_id: str(axes.get(axis_id, AUDIO_NONE) or AUDIO_NONE)
            for axis_id in AUDIO_WIDGET_AXIS_ORDER
        }
        result = audio_splice(
            picks,
            flavor=flavor if isinstance(flavor, str) else FLAVOR_ACE_VOCAL,
            brief=brief if isinstance(brief, str) else str(brief or ""),
            recipe=recipe if isinstance(recipe, str) else AUDIO_NONE,
        )
        return (result.tags, result.lyrics, audio_format_notes(result))


class EZBackgroundCast:
    """BOOLEAN toggles for who counts as background on Klein background Apps."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for the two character-cast flags.

        Returns:
            Required BOOLEAN widget map.
        """
        flag = (
            "BOOLEAN",
            {"default": True, "label_on": "On", "label_off": "Off"},
        )
        return {
            "required": {
                "other_characters": flag,
                "background_characters": flag,
            }
        }

    # Comfy node contract.
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("cast",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    DESCRIPTION = (
        "Choose whether companions and extras count as background on "
        "background-swap and background-edit. On treats them as environment; "
        "off keeps them locked with the main subject."
    )

    def run(
        self,
        other_characters: object = True,
        background_characters: object = True,
    ) -> tuple[str]:
        """Serialize the two flags into a compact cast token.

        Args:
            other_characters: BOOLEAN; on treats companions as background.
            background_characters: BOOLEAN; on treats extras as background.

        Returns:
            One-tuple with ``other=1,crowd=1`` style token.
        """
        return (
            format_background_cast(
                other_characters=other_characters,
                background_characters=background_characters,
            ),
        )


class EZImageDescribe:
    """Caption a still for Prompt Enhance. Off skips the VLM."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for enable and an optional still.

        Returns:
            Required enable flag and optional lazy IMAGE.
        """
        return {
            "required": {
                "enable": (
                    "BOOLEAN",
                    {"default": False, "label_on": "On", "label_off": "Off"},
                ),
            },
            "optional": {
                "image": ("IMAGE", {"lazy": True}),
            },
        }

    # Comfy node contract.
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("caption",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/prompt"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Caption a source still so Prompt Enhance can name inventory and "
        "lettering. Off (default) returns empty and does not load the "
        "describe GGUF. Opt-in weights: download-llm --tier describe."
    )

    def check_lazy_status(self, enable: object = False, image: object = None) -> list[str]:
        """Request the IMAGE only when the toggle is on.

        Args:
            enable: Comfy BOOLEAN widget.
            image: Current lazy IMAGE (ignored).

        Returns:
            ``[\"image\"]`` when enable is on, else empty.
        """
        del image
        if _as_bool(enable):
            return ["image"]
        return []

    def run(self, enable: object = False, image: Any = None) -> dict[str, Any]:
        """Caption ``image`` when enable is on.

        Args:
            enable: BOOLEAN; off returns an empty caption without a VLM.
            image: Optional Comfy IMAGE tensor.

        Returns:
            Packed caption and a status line (describe off / GGUF missing).
        """
        caption = describe_image(enable=enable, image=image)
        status = describe_last_status()
        return {
            "ui": {
                "text": (caption,),
                "passthrough": (status,),
            },
            "result": (caption,),
        }


# Comfy node registries.
NODE_CLASS_MAPPINGS: dict[str, type] = {
    "EZImageDescribe": EZImageDescribe,
    "EZBackgroundCast": EZBackgroundCast,
    "EZKleinPromptEnhance": EZKleinPromptEnhance,
    "EZWanPromptEnhance": EZWanPromptEnhance,
    "EZLTXPromptEnhance": EZLTXPromptEnhance,
    "EZZimagePromptEnhance": EZZimagePromptEnhance,
    "EZLongCatPromptEnhance": EZLongCatPromptEnhance,
    "EZDreamXPromptEnhance": EZDreamXPromptEnhance,
    "EZNegativePromptEnhance": EZNegativePromptEnhance,
    "EZPromptBundle": EZPromptBundle,
    "EZPromptJoin": EZPromptJoin,
    "EZContextJoin": EZContextJoin,
    "EZAceStepPromptEnhance": EZAceStepPromptEnhance,
    "EZSamplePrompt": EZSamplePrompt,
    "EZCinemaRack": EZCinemaRack,
    "EZAudioRack": EZAudioRack,
}

NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {
    "EZImageDescribe": "Describe image",
    "EZBackgroundCast": "Background cast",
    "EZKleinPromptEnhance": "Klein Prompt Enhance",
    "EZWanPromptEnhance": "Wan Prompt Enhance",
    "EZLTXPromptEnhance": "LTX Prompt Enhance",
    "EZZimagePromptEnhance": "Z-Image Prompt Enhance",
    "EZLongCatPromptEnhance": "LongCat Prompt Enhance",
    "EZDreamXPromptEnhance": "DreamX Prompt Enhance",
    "EZNegativePromptEnhance": "Negative Prompt Enhance",
    "EZPromptBundle": "Prompt Bundle",
    "EZPromptJoin": "Prompt Join",
    "EZContextJoin": "Context Join",
    "EZAceStepPromptEnhance": "ACE-Step Prompt Enhance",
    "EZSamplePrompt": "Sample Prompt",
    "EZCinemaRack": "Cinema Rack",
    "EZAudioRack": "Audio Rack",
}
