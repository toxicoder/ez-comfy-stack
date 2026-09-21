"""Image-studio run preview. Same resolvers Queue uses. No model load.

``ez_image`` must not import this pack at startup. The preview route imports
this module lazily.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any

from ez_image.formats import resolve_canvas
from ez_image.modes import ITERATE_EDIT_LINE, resolve_studio_mode
from ez_image.refs import load_input_still
from ez_prompt_enhance._styles import apply_style_to_prompt
from ez_prompt_enhance.background import BACKGROUND_MODES, wrap_background_prompt
from ez_prompt_enhance.client import STYLE_IGNORED_MODES, STYLE_NONE, style_ids
from ez_prompt_enhance.lettering import wrap_text_swap_prompt
from ez_prompt_enhance.samples import is_custom, resolve_prompt

# Default lab graph when the preview body omits lab_rel.
_LAB_REL = "stills/image-studio"
# Enhance class whose sample catalog image-studio uses.
_NODE_TYPE = "EZKleinPromptEnhance"


@dataclass(frozen=True)
class StudioPreview:
    """Values image-studio will send on the next Queue.

    Attributes:
        ok: False only when the composer itself fails (route wrapper).
        summary: Multiline text for the This run box.
        enhance_mode: Klein mode linked into Prompt Enhance.
        prefix: SaveImage prefix.
        context: Enhance context STRING (look splice, plus edit line or instruction).
        prompt: Rewriter source, or the CLIP text when Rewrite is off.
        prompt_source: ``sample recipe`` or ``prompt box``.
        style_note: Applied style id, ``style none``, or the ignore reason.
        rewrite: True when Rewrite prompt is on.
        width: Latent width Python will emit.
        height: Latent height Python will emit.
        batch: Batch size.
        hint: Enhance duration / framing line.
        format_label: Format combo label after Match input.
        has_image: True when a reference still will be attached.
        filename: Reference filename, or empty.
        missing_file: True when a filename was set but did not load.
        next_pass: Short pass name (``text to image`` or ``edit <file>``).
        iterate: Iterate switch.
        steps: KSampler steps as displayed.
        cfg: KSampler CFG as displayed.
        unet: UNET filename as displayed.
        seed: Seed as displayed.
        seed_note: Fixed, or a note that the seed changes at Run.
    """

    ok: bool
    summary: str
    enhance_mode: str
    prefix: str
    context: str
    prompt: str
    prompt_source: str
    style_note: str
    rewrite: bool
    width: int
    height: int
    batch: int
    hint: str
    format_label: str
    has_image: bool
    filename: str
    missing_file: bool
    next_pass: str
    iterate: bool
    steps: str
    cfg: str
    unet: str
    seed: str
    seed_note: str


def _as_str(value: object) -> str:
    """Coerce a widget value to a stripped string.

    Args:
        value: Combo, number, or None.

    Returns:
        Stripped string, or empty.
    """
    if isinstance(value, str):
        return value.strip()
    if value is None:
        return ""
    return str(value).strip()


def _as_bool(value: object, *, default: bool = False) -> bool:
    """Parse a Comfy BOOLEAN.

    Args:
        value: Bool, number, or yes/no string.
        default: Value when ``value`` is None.

    Returns:
        Parsed flag.
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def _style_id(value: object) -> str:
    """Return a catalog style id, or ``none``.

    Args:
        value: Style combo.

    Returns:
        Known id, or :data:`STYLE_NONE`.
    """
    raw = _as_str(value) or STYLE_NONE
    if raw not in style_ids():
        return STYLE_NONE
    return raw


def _seed_note(seed: str, control: object) -> str:
    """Describe whether the displayed seed is the one Queue will use.

    Args:
        seed: Displayed seed.
        control: KSampler ``control_after_generate``.

    Returns:
        A single summary line.
    """
    kind = _as_str(control).casefold() or "fixed"
    if kind in {"randomize", "random", "increment", "decrement"}:
        return f"Seed {seed} — changes when you Run ({kind})"
    return f"Seed {seed} (fixed)"


def _next_pass(
    *,
    iterate: bool,
    has_image: bool,
    filename: str,
    enhance_mode: str,
) -> str:
    """Short name of the pass Queue will run.

    Args:
        iterate: Iterate switch.
        has_image: Reference still will be attached.
        filename: Reference filename.
        enhance_mode: Resolved Klein mode.

    Returns:
        ``text to image``, ``edit <file>``, or the mode with an optional file.
    """
    if has_image and filename and (iterate or enhance_mode == "edit"):
        return f"edit {filename}"
    if not has_image and (iterate or enhance_mode == "t2i"):
        return "text to image"
    if has_image and filename:
        return f"{enhance_mode} · {filename}"
    return enhance_mode


def _reference(filename: object, image: object) -> tuple[object, str, bool]:
    """Load the reference still the same way EZOptionalImage does.

    Args:
        filename: Combo value. Empty is no still.
        image: Test override tensor. When set, the file is not read.

    Returns:
        ``(image or None, filename, missing_file)``.
    """
    name = _as_str(filename)
    if image is not None:
        return image, name, False
    if not name:
        return None, "", False
    loaded = load_input_still(name)
    if loaded is None:
        return None, name, True
    return loaded, name, False


def _prompt_text(
    source: str,
    enhance_mode: str,
    style_id: str,
    *,
    rewrite: bool,
) -> tuple[str, str]:
    """Apply the same wrap and style the Enhance node applies without an LLM.

    Args:
        source: Resolved sample or textarea.
        enhance_mode: Klein mode.
        style_id: Catalog style id or none.
        rewrite: When on, style is noted but not baked into the source.

    Returns:
        ``(text, style_note)``.
    """
    text = source
    if enhance_mode == "text_swap":
        text = wrap_text_swap_prompt(text)
    elif enhance_mode in BACKGROUND_MODES:
        text = wrap_background_prompt(text, enhance_mode, "")
    ignored = STYLE_IGNORED_MODES.get(enhance_mode)
    if style_id != STYLE_NONE and ignored:
        return text, ignored
    if style_id == STYLE_NONE:
        return text, "style none"
    if not rewrite:
        text = apply_style_to_prompt(text, style_id)
    return text, f"style {style_id}"


def _summary(preview: StudioPreview) -> str:
    """Join the This run lines.

    Args:
        preview: Resolved fields. ``summary`` on the input is ignored.

    Returns:
        Multiline summary.
    """
    lines: list[str] = []
    if preview.missing_file:
        lines.append(
            f"Reference file missing ({preview.filename}) — this run is text to image."
        )
    lines.append(f"Next pass: {preview.next_pass}")
    lines.append(f"Enhance mode: {preview.enhance_mode}")
    lines.append(f"Prompt ({preview.prompt_source}): {preview.prompt}")
    lines.append(f"Style: {preview.style_note}")
    if preview.rewrite:
        lines.append("Rewrite is on — this is the rewriter source, not the CLIP text.")
    else:
        lines.append("Rewrite is off — this prompt is the CLIP text.")
    lines.append(f"Size: {preview.width}×{preview.height} · batch {preview.batch}")
    lines.append(f"Prefix: {preview.prefix}")
    lines.append(f"Steps {preview.steps} · CFG {preview.cfg} · {preview.unet}")
    lines.append(preview.seed_note)
    if preview.iterate:
        lines.append(
            "Iterate is on — Creator mode is not used for mode, instruction, or prefix."
        )
        if preview.batch > 1:
            lines.append("Iterate feeds the first still only.")
    if preview.context:
        lines.append(f"Context: {preview.context}")
    return "\n".join(lines)


def preview_studio_run(
    *,
    category: object = "",
    mode: object = "",
    iterate: object = False,
    filename: object = "",
    format_value: object = "",
    width: object = 1280,
    height: object = 704,
    batch: object = 1,
    size_mode: object = "Match input",
    look: object = "none",
    prompt: object = "",
    sample: object = "custom",
    style: object = "none",
    rewrite: object = True,
    steps: object = "",
    cfg: object = "",
    unet: object = "",
    seed: object = "",
    seed_control: object = "fixed",
    lab_rel: str = _LAB_REL,
    catalog: object = "",
    image: object = None,
) -> StudioPreview:
    """Resolve the image-studio widgets to the values Queue will send.

    Args:
        category: Creator category combo.
        mode: Creator mode combo.
        iterate: Iterate switch.
        filename: Optional reference filename.
        format_value: Format / platform combo.
        width: Width widget (used when Format is Custom).
        height: Height widget.
        batch: Batch widget.
        size_mode: Match input or Force format.
        look: Look recipe combo.
        prompt: Prompt textarea.
        sample: Sample combo.
        style: Style combo.
        rewrite: Rewrite prompt switch.
        steps: KSampler steps widget.
        cfg: KSampler CFG widget.
        unet: UNET filename widget.
        seed: Seed widget.
        seed_control: ``control_after_generate``.
        lab_rel: Graph id for the sample catalog.
        catalog: Hidden catalog widget. Empty uses ``lab_rel``.
        image: Optional tensor override. Skips the file load.

    Returns:
        Preview fields and the This run summary.
    """
    loaded, name, missing = _reference(filename, image)
    has_image = False
    if loaded is not None:
        from ez_image.formats import image_hw

        has_image = image_hw(loaded) is not None
    iterating = _as_bool(iterate)
    canvas = resolve_canvas(
        format_value,
        width=width,
        height=height,
        batch=batch,
        look=look,
        size_mode=size_mode,
        image=loaded if has_image else None,
    )
    resolved = resolve_studio_mode(
        mode,
        category=category,
        extra_context=canvas.context,
        iterate=iterating,
        has_image=has_image,
    )
    do_rewrite = _as_bool(rewrite, default=True)
    catalog_id = _as_str(catalog) or lab_rel
    source = resolve_prompt(
        catalog_id,
        sample,
        prompt,
        node_type=_NODE_TYPE,
        mode=resolved.enhance_mode,
        lab_rel=lab_rel,
    )
    prompt_source = "prompt box" if is_custom(sample) else "sample recipe"
    style_id = _style_id(style)
    sent, style_note = _prompt_text(
        source,
        resolved.enhance_mode,
        style_id,
        rewrite=do_rewrite,
    )
    seed_text = _as_str(seed)
    preview = StudioPreview(
        ok=True,
        summary="",
        enhance_mode=resolved.enhance_mode,
        prefix=resolved.prefix,
        context=resolved.context,
        prompt=sent,
        prompt_source=prompt_source,
        style_note=style_note,
        rewrite=do_rewrite,
        width=canvas.width,
        height=canvas.height,
        batch=canvas.batch,
        hint=canvas.hint,
        format_label=canvas.label,
        has_image=has_image,
        filename=name,
        missing_file=missing,
        next_pass=_next_pass(
            iterate=iterating,
            has_image=has_image,
            filename=name,
            enhance_mode=resolved.enhance_mode,
        ),
        iterate=iterating,
        steps=_as_str(steps),
        cfg=_as_str(cfg),
        unet=_as_str(unet),
        seed=seed_text,
        seed_note=_seed_note(seed_text, seed_control),
    )
    return replace(preview, summary=_summary(preview))


def preview_payload(body: object) -> dict[str, Any]:
    """Build the JSON object for ``POST /ez_image/studio-preview``.

    Args:
        body: Widget snapshot from the App. Non-dicts are treated as empty.

    Returns:
        Preview fields plus ``summary``. ``ok`` is true.
    """
    raw: dict[str, Any] = body if isinstance(body, dict) else {}
    preview = preview_studio_run(
        category=raw.get("category", ""),
        mode=raw.get("mode", ""),
        iterate=raw.get("iterate", False),
        filename=raw.get("filename", ""),
        format_value=raw.get("format", raw.get("format_value", "")),
        width=raw.get("width", 1280),
        height=raw.get("height", 704),
        batch=raw.get("batch", raw.get("batch_size", 1)),
        size_mode=raw.get("size_mode", "Match input"),
        look=raw.get("look", "none"),
        prompt=raw.get("prompt", ""),
        sample=raw.get("sample", "custom"),
        style=raw.get("style", "none"),
        rewrite=raw.get("rewrite", raw.get("enhance", True)),
        steps=raw.get("steps", ""),
        cfg=raw.get("cfg", ""),
        unet=raw.get("unet", ""),
        seed=raw.get("seed", ""),
        seed_control=raw.get("seed_control", "fixed"),
        lab_rel=str(raw.get("lab_rel") or _LAB_REL),
        catalog=raw.get("catalog", ""),
    )
    payload = asdict(preview)
    payload["ok"] = True
    return payload
