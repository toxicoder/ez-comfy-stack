"""Family-specific Detail rungs (draft / standard / final).

This module is the only definition of what a rung asks for. The frontend reads
a table generated from it (``export_table`` -> tests/python/_build_quality_js.py
-> custom_nodes/ez_quality/js/ez_quality_presets.js, via ``bazelisk run
//tests:build_quality_js``) and derives the combo from that table, so no rung
number or weight name lives in JS.

``standard`` is the rung this App ships tuned for and it writes nothing on
every family: the graph keeps exactly what it was authored with, so the default
rung cannot drift and there is no authored-value snapshot left to compare.
``draft`` is the quick look and ``final`` is the best this App's own stack can
do. Each of them attempts every write in its row, and an apply where any write
cannot land is refused whole: nothing is renamed and nothing is substituted for
a file that is not on disk.

A rung never changes width, height, frames, or length, and never writes
``EZImageFormat`` or any other size widget. A rung writes only the fields its
own family owns, so no rung drops another vendor's weights onto a graph. Klein
9B, FLUX.2-dev, and the ``Free Commercial Use (<$10M)`` size retarget are no
longer reachable from any rung; the detectors for those filenames stay because
the checker and the safety lane import them, and a loader that still holds one
is a swappable source, never a write target.

Old tier ids stay accepted input (saved graphs, ``--quality``, ``EZ_QUALITY``,
the TUI) and normalize onto the three rungs through ``_QUALITY_NORMALIZE``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Mapping, Sequence, TypeAlias, cast

if TYPE_CHECKING:
    from collections.abc import Callable

    from ez_common import Json, JsonMap, JsonObject, WidgetsValues

QualityGraphNode: TypeAlias = "Mapping[str, Json]"
"""One ``nodes`` row as parsed from a graph document, before any shaping."""

# ---------------------------------------------------------------------------
# The ladder: three rungs, one default.
# ---------------------------------------------------------------------------

QUALITY_DRAFT = "draft"
"""Quick look: the cheapest rung this family can still show."""
QUALITY_STANDARD = "standard"
"""What this App ships tuned for. Writes nothing, on every family."""
QUALITY_FINAL = "final"
"""Best this App's own stack can do."""
QUALITY_DEFAULT = QUALITY_STANDARD
"""Every App opens here, because this rung needs no state to be correct."""

QUALITY_CHOICES: tuple[str, ...] = (QUALITY_DRAFT, QUALITY_STANDARD, QUALITY_FINAL)
"""The whole selectable value set. Nothing else is offered anywhere."""
NAMED_QUALITY_CHOICES: tuple[str, ...] = QUALITY_CHOICES
"""Rungs that name a level; the combo and the table iterate these."""

# ---------------------------------------------------------------------------
# Accepted input only: ids that old graphs, ``--quality``, and ``EZ_QUALITY``
# still carry. None of them is selectable, and no rung writes what they name.
# ---------------------------------------------------------------------------

QUALITY_CUSTOM = "custom"
QUALITY_LAB = "lab"
QUALITY_HIGH = "high"
QUALITY_FREE_COMMERCIAL = "Free Commercial Use (<$10M)"
QUALITY_FREE_COMMERCIAL_ALIAS = "free_commercial"
QUALITY_ULTRA = "ultra"
QUALITY_MAX = "max"
QUALITY_FLUX3_FAST = "flux3-fast"
QUALITY_FLUX3_QUALITY = "flux3-quality"
QUALITY_FLUX3_NVFP4 = "flux3-nvfp4"
QUALITY_QWEN_IMAGE = "qwen-image"
QUALITY_QWEN_IMAGE_TURBO = "qwen-image-turbo"
QUALITY_QWEN_IMAGE_NVFP4 = "qwen-image-nvfp4"
QUALITY_QWEN_IMAGE_TURBO_NVFP4 = "qwen-image-turbo-nvfp4"

# Legacy groups the checker still walks when it reports what an opt-in pack put
# on disk. They no longer drive a rung.
FLUX3_QUALITY_CHOICES: tuple[str, ...] = (
    QUALITY_FLUX3_FAST,
    QUALITY_FLUX3_QUALITY,
    QUALITY_FLUX3_NVFP4,
)
QWEN_QUALITY_CHOICES: tuple[str, ...] = (
    QUALITY_QWEN_IMAGE,
    QUALITY_QWEN_IMAGE_TURBO,
    QUALITY_QWEN_IMAGE_NVFP4,
    QUALITY_QWEN_IMAGE_TURBO_NVFP4,
)

# casefold(accepted id) -> rung. Anything unrecognised lands on ``standard``,
# which is the rung that writes nothing, so a stale stamp cannot mislabel a
# graph the way a substituted weight used to.
_QUALITY_NORMALIZE: dict[str, str] = {
    key.casefold(): target
    for key, target in (
        (QUALITY_DRAFT, QUALITY_DRAFT),
        (QUALITY_STANDARD, QUALITY_STANDARD),
        (QUALITY_FINAL, QUALITY_FINAL),
        (QUALITY_CUSTOM, QUALITY_STANDARD),
        (QUALITY_LAB, QUALITY_STANDARD),
        ("", QUALITY_STANDARD),
        (QUALITY_HIGH, QUALITY_FINAL),
        (QUALITY_ULTRA, QUALITY_FINAL),
        (QUALITY_MAX, QUALITY_FINAL),
        (QUALITY_FREE_COMMERCIAL, QUALITY_FINAL),
        (QUALITY_FREE_COMMERCIAL_ALIAS, QUALITY_FINAL),
        (QUALITY_FLUX3_FAST, QUALITY_DRAFT),
        (QUALITY_FLUX3_QUALITY, QUALITY_STANDARD),
        (QUALITY_FLUX3_NVFP4, QUALITY_FINAL),
        (QUALITY_QWEN_IMAGE, QUALITY_STANDARD),
        (QUALITY_QWEN_IMAGE_TURBO, QUALITY_DRAFT),
        (QUALITY_QWEN_IMAGE_NVFP4, QUALITY_FINAL),
        (QUALITY_QWEN_IMAGE_TURBO_NVFP4, QUALITY_DRAFT),
    )
}

# ---------------------------------------------------------------------------
# Filenames, family step/CFG overlays, widget indexes.
# ---------------------------------------------------------------------------

# Klein filenames the rungs may name. Klein 9B and FLUX.2-dev stay listed only
# because the checker reports what is on disk; no rung writes them.
KLEIN_DISTILLED = "flux-2-klein-4b-fp8.safetensors"
KLEIN_NVFP4 = "flux-2-klein-4b-nvfp4.safetensors"
KLEIN_BASE = "flux-2-klein-base-4b-fp8.safetensors"
KLEIN_9B = "flux-2-klein-9b-fp8.safetensors"
KLEIN_9B_BASE = "flux-2-klein-base-9b-fp8.safetensors"
KLEIN_9B_NVFP4 = "flux-2-klein-9b-nvfp4.safetensors"
FLUX2_DEV = "flux2_dev_fp8mixed.safetensors"
# FLUX 3 Image Klein (KLEIN3) weights from the official Comfy repo. Opt-in.
KLEIN3_DISTILLED = "flux3-image-klein-int8-convrot.safetensors"
KLEIN3_BASE = "flux3-image-klein-base-int8-convrot.safetensors"
KLEIN3_NVFP4 = "flux3-image-klein-base-nvfp4.safetensors"
# Qwen-Image 2.1 stills (Comfy-Org repack plus the BennyDaBall NVFP4
# conversions). Opt-in only, Qwen RESEARCH LICENSE AGREEMENT, never a default.
QWEN_IMAGE_INT8 = "qwen_image_2.1_int8_convrot.safetensors"
QWEN_IMAGE_TURBO_INT8 = "qwen_image_2.1_turbo_int8_convrot.safetensors"
QWEN_IMAGE_NVFP4 = "qwen_image_2.1_nvfp4.safetensors"
QWEN_IMAGE_TURBO_NVFP4 = "qwen_image_2.1_turbo_nvfp4.safetensors"

CLIP_4B = "qwen_3_4b.safetensors"
CLIP_8B = "qwen_3_8b_fp8mixed.safetensors"
CLIP_MISTRAL = "mistral_3_small_flux2_bf16.safetensors"
CLIP_TYPE_FLUX2 = "flux2"
# KLEIN3 text encoder (Qwen3-VL) plus the optional prompt upsampler.
KLEIN3_TE = "qwen3vl_4b_int8_convrot.safetensors"
KLEIN3_UPSAMPLER = "qwen3.5_9b_flux3_prompt_upsampler_int8_convrot.safetensors"
# Qwen-Image 2.1 text encoders: the Qwen3VL-8B companion, plus the encoder each
# BennyDaBall NVFP4 pack ships with.
QWEN_TE = "qwen3vl_8b_int8_convrot.safetensors"
QWEN_TE_NVFP4 = "qwen3vl_8b_nvfp4.safetensors"
QWEN_TE_TURBO_NVFP4 = "qwen3vl_8b_turbo_nvfp4.safetensors"

VAE_FULL = "flux2-vae.safetensors"
VAE_SMALL = "full_encoder_small_decoder.safetensors"
# Qwen-Image 2.1 VAE, shared by all four opt-in weights.
QWEN_VAE = "qwen_image_2.1_vae_bf16.safetensors"

# Klein: draft is the NVFP4 quick look, final is the base FP8 recipe BFL
# publishes for the 4B base weight.
KLEIN_DRAFT_STEPS = 4
KLEIN_DRAFT_CFG = 1.0
KLEIN_FINAL_STEPS = 24
KLEIN_FINAL_CFG = 3.5
# KLEIN3: the distilled weight is guidance-free (official range 4-16 steps);
# the base recipe is BFL's own 50 steps at CFG 3.5, and NVFP4 follows it.
KLEIN3_DRAFT_STEPS = 16
KLEIN3_DRAFT_CFG = 1.0
KLEIN3_FINAL_STEPS = 50
KLEIN3_FINAL_CFG = 3.5
# Qwen-Image 2.1: the Turbo weight is the distilled sibling, so it takes the
# guidance-free low-step recipe (16 at CFG 1.0); the base weight takes the
# 50-step CFG 3.5 recipe.
QWEN_DRAFT_STEPS = 16
QWEN_DRAFT_CFG = 1.0
QWEN_FINAL_STEPS = 50
QWEN_FINAL_CFG = 3.5

WAN_DRAFT_STEPS = 12
WAN_FINAL_STEPS = 32
LTX_DRAFT_STEPS = 12
LTX_FINAL_STEPS = 32
AUDIO_DRAFT_STEPS = 4
AUDIO_FINAL_STEPS = 24
TRELLIS_DRAFT_STEPS = 8
TRELLIS_FINAL_STEPS = 28

# A TRELLIS stage authored at this CFG runs without guidance: it is the texture
# pass, not one of the three guided stages. The TRELLIS ladder is tuned against
# the guided stages, so it leaves this one on its authored step count.
TRELLIS_GUIDANCE_FREE_CFG = 1.0

KSAMPLER_STEPS_INDEX = 2
KSAMPLER_CFG_INDEX = 3
UNET_NAME_INDEX = 0
CLIP_NAME_INDEX = 0
CLIP_TYPE_INDEX = 1
VAE_NAME_INDEX = 0

# The only node types a rung can write. A graph that carries none of them has
# nothing for a rung to change, so it gets no Detail combo; keep this in step
# with the node dispatch in _OVERLAY_FIELDS_BY_TYPE.
OVERLAY_NODE_TYPES: frozenset[str] = frozenset(
    {"KSampler", "UNETLoader", "CLIPLoader", "VAELoader"}
)

BANNED_UNET_NEEDLES: tuple[str, ...] = (
    "MiniMax",
    "Seedance",
    "Kling",
    "z_image_turbo",
)

_NOOP_OCCUPANCY = frozenset({"llm", "none"})

# Widget slot each overlay field lives in, per node type. A field whose slot is
# past the end of widgets_values has no prompt slot and refuses the apply.
_OVERLAY_FIELDS_BY_TYPE: dict[str, tuple[str, ...]] = {
    "KSampler": ("steps", "cfg"),
    "UNETLoader": ("unet_name",),
    "CLIPLoader": ("clip_name", "clip_type"),
    "VAELoader": ("vae_name",),
}
_FIELD_SLOT_INDEX: dict[str, int] = {
    "steps": KSAMPLER_STEPS_INDEX,
    "cfg": KSAMPLER_CFG_INDEX,
    "unet_name": UNET_NAME_INDEX,
    "clip_name": CLIP_NAME_INDEX,
    "clip_type": CLIP_TYPE_INDEX,
    "vae_name": VAE_NAME_INDEX,
}

# Reason text, spelled the way the frontend spells it, so the caption the CLI
# prints is the caption the browser prints.
FIELD_WIDGET_NAMES: dict[str, str] = {
    "steps": "steps",
    "cfg": "cfg",
    "unet_name": "unet_name",
    "clip_name": "clip_name",
    "vae_name": "vae_name",
    "clip_type": "type",
}
_NO_RUNGS_REASON = " graphs carry no Detail rungs"


@dataclass(frozen=True)
class QualityOverlay:
    """Optional widget writes. None means leave the authored value."""

    steps: int | None = None
    cfg: float | None = None
    unet_name: str | None = None
    clip_name: str | None = None
    vae_name: str | None = None
    clip_type: str | None = None


@dataclass(frozen=True)
class _Target:
    """One live widget a rung may write, and what it holds now."""

    node_index: int
    node_type: str
    current: Json
    has_slot: bool


@dataclass(frozen=True)
class RungWrite:
    """One write a plan says will land."""

    node_index: int
    node_type: str
    field: str
    value: int | float | str


@dataclass(frozen=True)
class RungPlan:
    """What one apply would do, and every reason it must not."""

    family: str
    rung: str
    writes: tuple[RungWrite, ...]
    reasons: tuple[str, ...]

    @property
    def refused(self) -> bool:
        """True when any requested write could not land.

        Args:
            None.

        Returns:
            True when the whole apply must be refused.
        """
        return bool(self.reasons)


def normalize_quality(value: Json) -> str:
    """Return a selectable rung, mapping every accepted id onto one.

    Args:
        value: Combo widget value or parsed body value.

    Returns:
        One of QUALITY_CHOICES.
    """
    raw = str(value or "").strip().casefold()
    return _QUALITY_NORMALIZE.get(raw, QUALITY_STANDARD)


def rung_label(rung: str) -> str:
    """Capitalize one rung the way the caption names it.

    Args:
        rung: Rung id, any case, or an accepted legacy id.

    Returns:
        ``Draft``, ``Standard``, or ``Final``.
    """
    return RUNG_LABEL[normalize_quality(rung)]


def is_banned_unet(name: str) -> bool:
    """True when a UNET filename is a studio-banned weight.

    Args:
        name: Candidate diffusion-model filename.

    Returns:
        True when any banned needle matches.
    """
    blob = name.lower()
    return any(needle.lower() in blob for needle in BANNED_UNET_NEEDLES)


def is_klein_4b_unet(name: str) -> bool:
    """True for Apache Klein 4B filenames (distilled, NVFP4, or base).

    Args:
        name: UNET filename.

    Returns:
        True when the name is Klein 4B and not 9B.
    """
    blob = name.lower()
    if "9b" in blob:
        return False
    return "klein" in blob and "4b" in blob


def is_klein_9b_unet(name: str) -> bool:
    """True for Klein 9B filenames (distilled, base, or NVFP4).

    Detector only: no rung writes a 9B weight. It stays because the safety lane
    and the checker report on these files.

    Args:
        name: UNET filename.

    Returns:
        True when the name looks like Klein 9B.
    """
    blob = name.lower()
    return "klein" in blob and "9b" in blob


def is_flux2_dev_unet(name: str) -> bool:
    """True for FLUX.2-dev diffusion filenames.

    Detector only: no rung writes a FLUX.2-dev weight. It stays because the
    safety lane and the checker report on these files.

    Args:
        name: UNET filename.

    Returns:
        True when the name looks like flux2_dev / flux2-dev.
    """
    blob = name.lower().replace(".", "-")
    return "flux2-dev" in blob or "flux-2-dev" in blob or "flux2_dev" in name.lower()


def _klein3_blob(name: str) -> str:
    """Fold separators in a KLEIN3 filename so needles match either style.

    Args:
        name: Candidate filename.

    Returns:
        Lowercased name with dots and underscores folded to dashes.
    """
    return name.lower().replace(".", "-").replace("_", "-")


def is_klein3_unet(name: str) -> bool:
    """True for FLUX 3 Image Klein UNET filenames (distilled/base/NVFP4).

    Args:
        name: UNET filename.

    Returns:
        True when the name is a KLEIN3 diffusion weight.
    """
    blob = _klein3_blob(name)
    return "flux3-image-klein" in blob or "flux-3-image-klein" in blob


def is_klein3_clip(name: str) -> bool:
    """True for the KLEIN3 Qwen3-VL text-encoder filename.

    Args:
        name: CLIP filename.

    Returns:
        True when the name is the KLEIN3 text encoder.
    """
    return "qwen3vl-4b" in _klein3_blob(name)


def is_klein3_upsampler(name: str) -> bool:
    """True for the optional KLEIN3 prompt upsampler filename.

    Args:
        name: Text-encoder / model filename.

    Returns:
        True when the name is the KLEIN3 prompt upsampler.
    """
    return "flux3-prompt-upsampler" in _klein3_blob(name)


def _qwen_blob(name: str) -> str:
    """Fold separators in a Qwen-Image filename so needles match either style.

    Args:
        name: Candidate filename.

    Returns:
        Lowercased name with dots and underscores folded to dashes.
    """
    return name.lower().replace(".", "-").replace("_", "-")


def is_qwen_image_unet(name: str) -> bool:
    """True for opt-in Qwen-Image 2.1 UNET filenames (INT8/NVFP4, both twins).

    Args:
        name: UNET filename.

    Returns:
        True when the name is a Qwen-Image 2.1 diffusion weight.
    """
    blob = _qwen_blob(name)
    return "qwen-image-2-1" in blob and ("convrot" in blob or "nvfp4" in blob)


def is_qwen_image_clip(name: str) -> bool:
    """True for the Qwen-Image 2.1 Qwen3VL-8B text-encoder filenames.

    Args:
        name: CLIP filename.

    Returns:
        True when the name is a Qwen-Image 2.1 text encoder.
    """
    return "qwen3vl-8b" in _qwen_blob(name)


def is_qwen_image_vae(name: str) -> bool:
    """True for the Qwen-Image 2.1 VAE filename.

    Args:
        name: VAE filename.

    Returns:
        True when the name is the Qwen-Image 2.1 VAE.
    """
    return "qwen-image-2-1-vae" in _qwen_blob(name)


def is_wan_14b_unet(name: str) -> bool:
    """True for Wan 14B / A14B filenames (not the 5B lab default).

    Args:
        name: UNET filename.

    Returns:
        True when the name looks like a 14B Wan transformer.
    """
    blob = name.lower()
    return "14b" in blob


def is_flux2_clip(name: str) -> bool:
    """True for Klein / FLUX.2 text-encoder filenames.

    Args:
        name: CLIP filename.

    Returns:
        True when the name is Qwen3 4B/8B or Mistral Flux2.
    """
    blob = name.lower()
    return "qwen_3_" in blob or ("mistral" in blob and "flux2" in blob)


def is_flux2_vae(name: str) -> bool:
    """True for Flux.2 VAE filenames (full or small decoder).

    Args:
        name: VAE filename.

    Returns:
        True when the name is a Flux.2 VAE.
    """
    blob = name.lower()
    return "flux2-vae" in blob or "flux2_vae" in blob or "small_decoder" in blob


def _is_swappable_target(field: str, current: str) -> bool:
    """True when a loader still holds a weight a rung may replace.

    Mirror of ``isSwappableTarget`` in ``ez_quality.js``. Klein 9B and
    FLUX.2-dev are swappable *away from*, never toward: a rung never names them,
    and leaving them unswappable would refuse a graph that is asking for the
    Apache weight back.

    Args:
        field: Overlay field being written.
        current: Filename the loader holds now (empty when it holds nothing).

    Returns:
        True when the current value is one this overlay may replace.
    """
    name = str(current or "")
    if not name:
        return True
    if field == "unet_name":
        return (
            is_klein_4b_unet(name)
            or is_klein_9b_unet(name)
            or is_flux2_dev_unet(name)
            or is_klein3_unet(name)
            or is_qwen_image_unet(name)
        )
    if field == "clip_name":
        return is_flux2_clip(name) or is_klein3_clip(name) or is_qwen_image_clip(name)
    if field == "vae_name":
        return is_flux2_vae(name) or is_qwen_image_vae(name)
    return True


def _available(available: Sequence[str] | None) -> set[str]:
    """Normalize combo options to a set.

    Args:
        available: Combo options, or None.

    Returns:
        Filename set (empty when None).
    """
    if available is None:
        return set()
    return {str(item) for item in available if str(item).strip()}


def _pick_unet(name: str, available: set[str]) -> str | None:
    """Return ``name`` when it is allowed and present.

    Args:
        name: Candidate UNET filename.
        available: Combo options; empty means no presence check.

    Returns:
        ``name``, or None when banned or missing from the combo.
    """
    if is_banned_unet(name):
        return None
    if not available or name not in available:
        return None
    return name


def _changed(current: str, picked: str | None) -> str | None:
    """Return ``picked`` only when it differs from ``current``.

    Args:
        current: Current widget filename.
        picked: Candidate, or None.

    Returns:
        ``picked`` when it should be written.
    """
    if picked is None or picked == current:
        return None
    return picked


def _pick_file(name: str, available: set[str]) -> str | None:
    """Return ``name`` when present in the combo (empty combo = no check).

    Args:
        name: Candidate filename.
        available: Combo options.

    Returns:
        ``name`` or None.
    """
    if not available or name not in available:
        return None
    return name


def _same_value(left: Json, right: Json) -> bool:
    """Compare two widget values the way the combo and KSampler report them.

    Args:
        left: Observed widget value.
        right: Requested overlay value.

    Returns:
        True when the two hold the same setting.
    """
    if left is None or right is None:
        return left is None and right is None
    if isinstance(left, (int, float)) or isinstance(right, (int, float)):
        try:
            return float(left) == float(right)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return False
    return str(left) == str(right)


def _number_text(value: Json) -> str:
    """Render a numeric widget value the way the caption reads it.

    ``3`` and ``3.0`` render alike, so the Python caption is byte-identical to
    what the frontend renders for the same graph.

    Args:
        value: Observed or requested steps / CFG value.

    Returns:
        The value as text.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return str(value)
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return str(number)


def _field_text(field: str, value: Json) -> str:
    """Render one overlay value for the caption.

    Args:
        field: Overlay field name.
        value: The value to render.

    Returns:
        A number for steps/cfg, a weight name without its extension otherwise,
        or ``unset`` when the widget holds nothing.
    """
    if field in ("steps", "cfg"):
        return _number_text(value)
    name = str(value or "").strip()
    if not name:
        return "unset"
    if field == "unet_name" and name in UNET_STACK_LABEL:
        return UNET_STACK_LABEL[name]
    return name.rsplit(".", 1)[0]


# ---------------------------------------------------------------------------
# What the caption says. The caption is the only place truth lives: it is read
# off the live widgets, never off the rung name.
# ---------------------------------------------------------------------------

LICENSE_LABEL: dict[str, str] = {
    "klein": "Apache-2.0",
    "wan": "Apache-2.0",
    # LTX-2.5 is gated and capped, and the license page is explicit that the
    # audio model is not Apache; the film lane renders the same LTX weights.
    "ltx": "LTX Community License (gated, $10M company cap)",
    "film": "LTX Community License (gated, $10M company cap)",
    "audio": "MIT (ACE-Step)",
    "trellis": "MIT (TRELLIS.2)",
    "klein3": "FLUX Non-Commercial",
    "qwen": "Qwen Research license",
}
"""One license word per family, stated where the choice is made.

Kept honest against docs/licenses.mdx, which is the policy of record: Klein 4B
and Wan are Apache, LTX-2.5 is the gated LTX Community License under a company
revenue cap, and ACE-Step and TRELLIS.2 are MIT.
"""

STACK_LABEL: dict[str, str] = {
    "klein": "Klein 4B",
    "wan": "Wan 2.2 5B",
    "ltx": "LTX-2.5",
    "film": "LTX-2.5 film",
    "audio": "ACE-Step 1.5",
    "trellis": "TRELLIS.2",
    "klein3": "FLUX 3 Image Klein",
    "qwen": "Qwen-Image 2.1",
}
"""The <stack> term for a family whose rungs do not name a transformer."""

UNET_STACK_LABEL: dict[str, str] = {
    KLEIN_NVFP4: "Klein 4B nvfp4",
    KLEIN_DISTILLED: "Klein 4B distilled",
    KLEIN_BASE: "Klein 4B base",
    KLEIN3_DISTILLED: "FLUX 3 Klein int8",
    KLEIN3_BASE: "FLUX 3 Klein base int8",
    KLEIN3_NVFP4: "FLUX 3 Klein nvfp4",
    QWEN_IMAGE_INT8: "Qwen-Image 2.1 int8",
    QWEN_IMAGE_TURBO_INT8: "Qwen-Image 2.1 turbo int8",
    QWEN_IMAGE_NVFP4: "Qwen-Image 2.1 nvfp4",
    QWEN_IMAGE_TURBO_NVFP4: "Qwen-Image 2.1 turbo nvfp4",
}
"""The <stack> term when a live loader holds one of these weights."""

RUNG_LABEL: dict[str, str] = {
    QUALITY_DRAFT: "Draft",
    QUALITY_STANDARD: "Standard",
    QUALITY_FINAL: "Final",
}
"""How the caption names a rung when it says what that rung sets."""

EDITED_PREFIX = "Edited: "
"""Prefix for a caption whose live widgets left the rung behind."""


def caption_for(family: str, rung: str, live: JsonMap | None = None) -> str:
    """Render the single truth line for one family, rung, and live widgets.

    The line is ``<stack> - <steps> steps - CFG <cfg> - <license>``, read off
    what the widgets actually hold rather than off the rung name, so a row can
    never claim a write the graph does not have. A family whose ladder has no
    CFG gets no CFG term. When the live widgets differ from what the selected
    rung asked for (a hand edit, or a partial write that was refused), the line
    carries the ``Edited: `` prefix and each differing term names what the rung
    sets, e.g. ``Edited: Klein 4B base - 20 steps (Final sets 24) - CFG 3.5 -
    Apache-2.0``. ``standard`` writes nothing, so it can never be left behind.
    A field the caller does not report is not a disagreement: it simply earns no
    term of its own.

    Args:
        family: Occupancy id, QUALITY_FAMILY_KLEIN3, or QUALITY_FAMILY_QWEN.
        rung: Rung id, any case; an accepted legacy id normalizes first.
        live: Observed value per overlay field name.

    Returns:
        The caption line, or empty for a family that carries no rungs.
    """
    owned = family_owned_fields(family)
    if not owned:
        return ""
    choice = normalize_quality(rung)
    row = _rung_row(family, choice)
    state: JsonMap = dict(live) if live else {}
    owns = set(owned)
    says = rung_label(choice)
    edited = False
    terms: list[str] = [_stack_text(family, owns, state.get("unet_name"))]
    # A field the caller does not report is not a disagreement, so only a live
    # value that is actually present can leave the rung behind.
    if "unet_name" in owns and row.unet_name is not None:
        unet = state.get("unet_name")
        if unet is not None and not _same_value(unet, row.unet_name):
            edited = True
            terms[0] += f" ({says} sets {_field_text('unet_name', row.unet_name)})"
    if "steps" in owns and state.get("steps") is not None:
        steps = state.get("steps")
        term = f"{_number_text(steps)} steps"
        if row.steps is not None and not _same_value(steps, row.steps):
            edited = True
            term += f" ({says} sets {row.steps})"
        terms.append(term)
    if "cfg" in owns and state.get("cfg") is not None:
        cfg = state.get("cfg")
        term = f"CFG {_number_text(cfg)}"
        if row.cfg is not None and not _same_value(cfg, row.cfg):
            edited = True
            term += f" ({says} sets {_number_text(row.cfg)})"
        terms.append(term)
    for field in ("clip_name", "vae_name", "clip_type"):
        if field not in owns or state.get(field) is None:
            continue
        wanted = getattr(row, field)
        if wanted is None or _same_value(state.get(field), wanted):
            continue
        edited = True
        observed = _field_text(field, state.get(field))
        wants = _field_text(field, wanted)
        name = FIELD_WIDGET_NAMES[field]
        terms.append(f"{name} {observed} ({says} sets {wants})")
    license_word = LICENSE_LABEL[family]
    terms.append(license_word)
    return (EDITED_PREFIX if edited else "") + " - ".join(terms)


def _stack_text(family: str, owns: set[str], live_unet: Json) -> str:
    """Name the stack the caption opens with.

    Every family with a rung names its own stack and license, so both lookups
    are keyed by construction on the ladder table.

    Args:
        family: Rung family.
        owns: Overlay fields this family's rungs write.
        live_unet: Filename the UNETLoader holds now, when known.

    Returns:
        The <stack> term.
    """
    default = STACK_LABEL[family]
    if "unet_name" not in owns:
        return default
    return _field_text("unet_name", live_unet) if live_unet else default


# ---------------------------------------------------------------------------
# Family detection and the rung table.
# ---------------------------------------------------------------------------

# resolve_overlay reports only the widgets a rung actually changes, so the
# family fixture must classify as the family while differing from every value
# its rungs request; otherwise a request would be recorded as "no change".
# These names are branch fixtures only and never appear in a graph.
_KLEIN_TABLE_UNET = "flux-2-klein-4b-table-sentinel-fp8.safetensors"
_KLEIN_TABLE_CLIP = "qwen_3_4b_table_sentinel.safetensors"
_KLEIN_TABLE_VAE = "flux2-vae-table-sentinel.safetensors"
_KLEIN3_TABLE_UNET = "flux3-image-klein-table-sentinel-int8-convrot.safetensors"
_QWEN_TABLE_UNET = "qwen_image_2.1_base_int8_convrot.safetensors"

# Transformer each family authors, so a table row is evaluated against the
# loaders that family really pins. resolve_overlay branches on the pinned
# weights, so the family fixture is what makes a row mean that family.
WAN_5B_UNET = "wan2.2_ti2v_5B_fp16.safetensors"
LTX_UNET = "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors"
TRELLIS_UNET = "trellis_2_int8_convrot.safetensors"

# Graphs that pin FLUX 3 Image Klein still stamp occupancy "klein", so the
# table needs a family of its own to record their rungs separately.
QUALITY_FAMILY_KLEIN3 = "klein3"
# Opt-in Qwen-Image 2.1 stills stamp occupancy "klein" too, and are opt-in (not
# Apache), so they get their own family rather than riding the Klein ladder.
QUALITY_FAMILY_QWEN = "qwen"

QUALITY_FAMILIES: tuple[str, ...] = (
    "klein",
    QUALITY_FAMILY_KLEIN3,
    QUALITY_FAMILY_QWEN,
    "wan",
    "ltx",
    "film",
    "audio",
    "trellis",
    "none",
    "llm",
)

_FAMILY_PINNED: dict[str, dict[str, str]] = {
    "klein": {
        "unet": _KLEIN_TABLE_UNET,
        "clip": _KLEIN_TABLE_CLIP,
        "vae": _KLEIN_TABLE_VAE,
    },
    QUALITY_FAMILY_KLEIN3: {
        "unet": _KLEIN3_TABLE_UNET,
        "clip": "",
        "vae": "",
    },
    QUALITY_FAMILY_QWEN: {
        "unet": _QWEN_TABLE_UNET,
        "clip": "",
        "vae": "",
    },
    "wan": {"unet": WAN_5B_UNET, "clip": "", "vae": ""},
    "ltx": {"unet": LTX_UNET, "clip": "", "vae": ""},
    "film": {"unet": LTX_UNET, "clip": "", "vae": ""},
    "audio": {"unet": "", "clip": "", "vae": ""},
    "trellis": {"unet": TRELLIS_UNET, "clip": "", "vae": ""},
    "none": {"unet": "", "clip": "", "vae": ""},
    "llm": {"unet": "", "clip": "", "vae": ""},
}

# The six widgets the overlay is allowed to own, in serialization order.
OVERLAY_FIELDS: tuple[str, ...] = (
    "steps",
    "cfg",
    "unet_name",
    "clip_name",
    "vae_name",
    "clip_type",
)

# Combo options that mean "everything on disk", so a derived row records what a
# rung asks for before availability filters it. apply_to_graph filters again.
_ALL_CATALOG_WEIGHTS: frozenset[str] = frozenset(
    {
        KLEIN_DISTILLED,
        KLEIN_NVFP4,
        KLEIN_BASE,
        CLIP_4B,
        KLEIN3_TE,
        VAE_FULL,
        VAE_SMALL,
        KLEIN3_DISTILLED,
        KLEIN3_NVFP4,
        QWEN_IMAGE_INT8,
        QWEN_IMAGE_TURBO_INT8,
        WAN_5B_UNET,
        LTX_UNET,
        TRELLIS_UNET,
    }
)

# The one rung table. ``standard`` is absent on purpose: it writes nothing,
# everywhere, which is the rule that deleted the lab/custom state machine.
_RUNG_ROWS: dict[str, dict[str, QualityOverlay]] = {
    "klein": {
        QUALITY_DRAFT: QualityOverlay(
            steps=KLEIN_DRAFT_STEPS,
            cfg=KLEIN_DRAFT_CFG,
            unet_name=KLEIN_NVFP4,
            clip_name=CLIP_4B,
            vae_name=VAE_SMALL,
            clip_type=CLIP_TYPE_FLUX2,
        ),
        QUALITY_FINAL: QualityOverlay(
            steps=KLEIN_FINAL_STEPS,
            cfg=KLEIN_FINAL_CFG,
            unet_name=KLEIN_BASE,
            clip_name=CLIP_4B,
            vae_name=VAE_FULL,
            clip_type=CLIP_TYPE_FLUX2,
        ),
    },
    QUALITY_FAMILY_KLEIN3: {
        QUALITY_DRAFT: QualityOverlay(
            steps=KLEIN3_DRAFT_STEPS,
            cfg=KLEIN3_DRAFT_CFG,
            unet_name=KLEIN3_DISTILLED,
        ),
        QUALITY_FINAL: QualityOverlay(
            steps=KLEIN3_FINAL_STEPS,
            cfg=KLEIN3_FINAL_CFG,
            unet_name=KLEIN3_NVFP4,
        ),
    },
    QUALITY_FAMILY_QWEN: {
        QUALITY_DRAFT: QualityOverlay(
            steps=QWEN_DRAFT_STEPS,
            cfg=QWEN_DRAFT_CFG,
            unet_name=QWEN_IMAGE_TURBO_INT8,
        ),
        QUALITY_FINAL: QualityOverlay(
            steps=QWEN_FINAL_STEPS,
            cfg=QWEN_FINAL_CFG,
            unet_name=QWEN_IMAGE_INT8,
        ),
    },
    "wan": {
        QUALITY_DRAFT: QualityOverlay(steps=WAN_DRAFT_STEPS),
        QUALITY_FINAL: QualityOverlay(steps=WAN_FINAL_STEPS),
    },
    "ltx": {
        QUALITY_DRAFT: QualityOverlay(steps=LTX_DRAFT_STEPS),
        QUALITY_FINAL: QualityOverlay(steps=LTX_FINAL_STEPS),
    },
    "film": {
        QUALITY_DRAFT: QualityOverlay(steps=LTX_DRAFT_STEPS),
        QUALITY_FINAL: QualityOverlay(steps=LTX_FINAL_STEPS),
    },
    "audio": {
        QUALITY_DRAFT: QualityOverlay(steps=AUDIO_DRAFT_STEPS),
        QUALITY_FINAL: QualityOverlay(steps=AUDIO_FINAL_STEPS),
    },
    "trellis": {
        QUALITY_DRAFT: QualityOverlay(steps=TRELLIS_DRAFT_STEPS),
        QUALITY_FINAL: QualityOverlay(steps=TRELLIS_FINAL_STEPS),
    },
}


def _rung_row(family: str, rung: str) -> QualityOverlay:
    """Return the literal values one rung asks of one family.

    Nothing is filtered here: no presence check and no comparison with what the
    graph holds, so the caller can tell "already set" from "cannot be set".

    Args:
        family: Occupancy id, QUALITY_FAMILY_KLEIN3, or QUALITY_FAMILY_QWEN.
        rung: Rung id, any case, or an accepted legacy id.

    Returns:
        Requested overlay; empty for ``standard`` and for a family with no
        rungs of its own.
    """
    choice = normalize_quality(rung)
    if choice == QUALITY_STANDARD:
        return QualityOverlay()
    return _RUNG_ROWS.get(family, {}).get(choice, QualityOverlay())


def family_for(occupancy: str, *, unet_name: str = "", clip_name: str = "") -> str:
    """Rung family one sampler + loader set belongs to.

    A graph that pins FLUX 3 or opt-in Qwen-Image weights has its own family,
    so neither the Klein ladder nor the other vendor's ladder can drop its
    weights onto it.

    Args:
        occupancy: Graph occupancy id (may be empty).
        unet_name: Current UNETLoader filename.
        clip_name: Current CLIPLoader filename.

    Returns:
        An entry of QUALITY_FAMILIES; ``none`` for anything this table does not
        cover.
    """
    occ = (occupancy or "").strip().lower()
    if occ in _NOOP_OCCUPANCY:
        return occ
    if occ not in QUALITY_FAMILIES:
        return "none"
    if is_klein3_unet(unet_name) or is_klein3_clip(clip_name):
        return QUALITY_FAMILY_KLEIN3
    if is_qwen_image_unet(unet_name) or is_qwen_image_clip(clip_name):
        return QUALITY_FAMILY_QWEN
    return occ


def _graph_pins(
    graph: Mapping[str, Json],
    unet_test: Callable[[str], bool],
    clip_test: Callable[[str], bool],
) -> bool:
    """True when a live loader holds weights one opt-in family owns.

    Args:
        graph: Serialized Comfy graph.
        unet_test: Predicate over a UNETLoader filename.
        clip_test: Predicate over a CLIPLoader filename.

    Returns:
        True when any live loader pins the family.
    """
    for node in cast("list[QualityGraphNode]", graph.get("nodes") or []):
        if not _is_live_node(node):
            continue
        ntype = node.get("type")
        values = node.get("widgets_values")
        name = str(values[0]) if isinstance(values, list) and values else ""
        if ntype == "UNETLoader" and unet_test(name):
            return True
        if ntype == "CLIPLoader" and clip_test(name):
            return True
    return False


def graph_family(graph: Mapping[str, Json]) -> str:
    """Rung family a whole graph belongs to.

    Mirror of ``graphFamily`` in ``ez_quality.js``: the occupancy decides, then
    the loaders a live lane actually pins can pull the graph into the opt-in
    FLUX 3 or Qwen-Image family.

    Args:
        graph: Serialized Comfy graph.

    Returns:
        An entry of QUALITY_FAMILIES; ``none`` for anything this table does not
        cover.
    """
    occ = infer_occupancy(graph)
    if occ in _NOOP_OCCUPANCY:
        return occ
    if occ not in QUALITY_FAMILIES:
        return "none"
    if _graph_pins(graph, is_klein3_unet, is_klein3_clip):
        return QUALITY_FAMILY_KLEIN3
    if _graph_pins(graph, is_qwen_image_unet, is_qwen_image_clip):
        return QUALITY_FAMILY_QWEN
    return occ


def resolve_overlay(
    *,
    occupancy: str,
    quality: str,
    authored_steps: int,
    authored_cfg: float,
    unet_name: str,
    available_unets: Sequence[str] | None = None,
    clip_name: str = "",
    available_clips: Sequence[str] | None = None,
    vae_name: str = "",
    available_vaes: Sequence[str] | None = None,
) -> QualityOverlay:
    """Return the overlay one rung asks of one sampler + loader set.

    A rung names absolute values, so the authored step count and CFG no longer
    feed anything.

    Args:
        occupancy: extra.lab_app_mode.occupancy (klein, wan, ltx, ...).
        quality: Rung id, or an accepted legacy id (it normalizes first).
        authored_steps: Unused; kept so callers that still read the graph can
            pass what they read.
        authored_cfg: Unused; see ``authored_steps``.
        unet_name: Current UNETLoader filename (may be empty).
        available_unets: UNET combo options. Empty/None refuses UNET swaps.
        clip_name: Current CLIPLoader filename.
        available_clips: CLIP combo options.
        vae_name: Current VAELoader filename.
        available_vaes: VAE combo options.

    Returns:
        Overlay with None for knobs that must stay authored.
    """
    del authored_steps, authored_cfg
    family = family_for(occupancy, unet_name=unet_name, clip_name=clip_name)
    choice = normalize_quality(quality)
    if is_wan_14b_unet(unet_name):
        return QualityOverlay()
    row = _rung_row(family, choice)
    available = _available(available_unets)
    clips = _available(available_clips)
    vaes = _available(available_vaes)
    unet = _pick_unet(row.unet_name, available) if row.unet_name else None
    clip = _pick_file(row.clip_name, clips) if row.clip_name else None
    vae = _pick_file(row.vae_name, vaes) if row.vae_name else None
    return QualityOverlay(
        steps=row.steps,
        cfg=row.cfg,
        unet_name=_changed(unet_name, unet),
        clip_name=_changed(clip_name, clip),
        vae_name=_changed(vae_name, vae),
        clip_type=row.clip_type,
    )


def is_trellis_guidance_free_stage(node: Mapping[str, Json], family: str) -> bool:
    """True when one TRELLIS KSampler is the unguided texture pass.

    The TRELLIS graph runs three guided stages at CFG 7.5 and one texture
    stage at CFG 1.0. The step ladder is tuned against the guided stages, and
    the texture stage's own step count is part of its recipe, so the overlay
    leaves that sampler alone and reads the rung off the guided stages.

    Args:
        node: One graph node.
        family: Inferred family for the graph the node belongs to.

    Returns:
        True when the overlay must not write this sampler's steps.
    """
    if family != "trellis" or str(node.get("type") or "") != "KSampler":
        return False
    values = node.get("widgets_values")
    if not isinstance(values, list) or len(values) <= KSAMPLER_CFG_INDEX:
        return False
    held = values[KSAMPLER_CFG_INDEX]
    if isinstance(held, bool) or not isinstance(held, (int, float)):
        return False
    return float(held) == TRELLIS_GUIDANCE_FREE_CFG


def infer_occupancy(graph: Mapping[str, Json]) -> str:
    """Occupancy from extra, else a coarse type heuristic.

    Args:
        graph: Serialized Comfy graph.

    Returns:
        Occupancy id (may be empty).
    """
    extra = graph.get("extra") if isinstance(graph.get("extra"), dict) else {}
    mode = extra.get("lab_app_mode") if isinstance(extra, dict) else None
    if isinstance(mode, dict):
        occ = str(mode.get("occupancy") or "").strip()
        if occ:
            return occ
    nodes = cast("list[QualityGraphNode]", graph.get("nodes") or [])
    types = {str(node.get("type") or "") for node in nodes}
    if "EZFilmConcat" in types:
        return "film"
    if "MeshToFile3D" in types:
        return "trellis"
    if "SaveAudio" in types or "SaveAudioMP3" in types:
        return "audio"
    if "VHS_VideoCombine" in types or "SaveVideo" in types:
        for node in nodes:
            if node.get("type") != "UNETLoader":
                continue
            values = cast("WidgetsValues", node.get("widgets_values") or [])
            name = str(values[0]) if values else ""
            if "ltx" in name.lower():
                return "ltx"
            if "wan" in name.lower():
                return "wan"
        return "wan"
    if "SaveImage" in types:
        return "klein"
    return ""


def _is_live_node(node: Mapping[str, Json]) -> bool:
    """True when a node is in the queued prompt.

    Muted and bypassed lanes drive no write and wear no caption, which is the
    same rule the frontend applies, so both sides refuse the same applies.

    Args:
        node: One graph node.

    Returns:
        True when the node is unmuted and unbypassed.
    """
    return node.get("mode") is None or node.get("mode") == 0


def graph_has_wan14(graph: Mapping[str, Json]) -> bool:
    """True when any live UNETLoader is a Wan 14B file.

    Args:
        graph: Serialized Comfy graph.

    Returns:
        True when a 14B UNET is present.
    """
    for node in cast("list[QualityGraphNode]", graph.get("nodes") or []):
        if node.get("type") != "UNETLoader" or not _is_live_node(node):
            continue
        values = cast("WidgetsValues", node.get("widgets_values") or [])
        if values and is_wan_14b_unet(str(values[0])):
            return True
    return False


def _overlay_instances(
    graph: Mapping[str, Json],
    family: str,
) -> dict[str, list[_Target]]:
    """Collect every live widget a rung may write, per overlay field.

    Mirror of ``collectOverlayInstances`` in ``ez_quality.js``.

    Args:
        graph: Serialized Comfy graph.
        family: The family whose overlay is being read.

    Returns:
        Field name to the live targets for that field.
    """
    out: dict[str, list[_Target]] = {field: [] for field in OVERLAY_FIELDS}
    nodes = cast("list[QualityGraphNode]", graph.get("nodes") or [])
    for index, node in enumerate(nodes):
        if not _is_live_node(node) or is_trellis_guidance_free_stage(node, family):
            continue
        ntype = str(node.get("type") or "")
        fields = _OVERLAY_FIELDS_BY_TYPE.get(ntype)
        if not fields:
            continue
        values = node.get("widgets_values")
        if not isinstance(values, list):
            continue
        for field in fields:
            slot = _FIELD_SLOT_INDEX[field]
            has_slot = len(values) > slot
            out[field].append(
                _Target(
                    node_index=index,
                    node_type=ntype,
                    current=values[slot] if has_slot else None,
                    has_slot=has_slot,
                )
            )
    return out


def _write_block_reason(
    field: str,
    target: _Target,
    wanted: Json,
    wan14: bool,
    available: set[str],
) -> str:
    """Why one write cannot land, or empty when it can.

    Mirror of ``writeBlockReason`` in ``ez_quality.js``, with the same wording,
    so a CLI refusal and a browser caption name the same thing. An empty answer
    means the queued prompt will really hold the rung value.

    Args:
        field: Overlay field being written.
        target: The live widget that would receive it.
        wanted: Value the rung asks for.
        wan14: True when a live Wan 14B loader pins the graph.
        available: Combo options for this field; empty means no presence check.

    Returns:
        Reason text, or empty when the write can land.
    """
    if wan14:
        return "Wan 14B is not overlaid"
    wanted_text = str(wanted)
    if field == "unet_name" and is_banned_unet(wanted_text):
        return f"{wanted_text} is not allowed"
    current = str(target.current or "")
    if not _is_swappable_target(field, current):
        return f"cannot swap {current}"
    if available and wanted_text not in available:
        return f"{wanted_text} not installed"
    if not target.has_slot:
        return f"{FIELD_WIDGET_NAMES[field]} has no prompt slot"
    return ""


def plan_rung_writes(
    graph: Mapping[str, Json],
    rung: str,
    *,
    available_unets: Sequence[str] | None = None,
    available_clips: Sequence[str] | None = None,
    available_vaes: Sequence[str] | None = None,
) -> RungPlan:
    """Decide every write one rung asks of one graph, and what blocks it.

    Mirror of ``planTierWrites`` in ``ez_quality.js``. A rung is write-or-refuse:
    any write that cannot land refuses the whole apply, and nothing is ever
    substituted for a weight that is not installed. ``standard`` writes nothing,
    so it is never refused. The ``type`` widget of a CLIPLoader has no on-disk
    catalog, so it carries no presence check.

    Args:
        graph: Serialized Comfy graph.
        rung: Rung id, any case, or an accepted legacy id.
        available_unets: UNET combo options; empty/None skips the presence check.
        available_clips: CLIP combo options.
        available_vaes: VAE combo options.

    Returns:
        The writes that would land, plus every reason the apply must be refused.
    """
    choice = normalize_quality(rung)
    family = graph_family(graph)
    if choice == QUALITY_STANDARD:
        return RungPlan(family=family, rung=choice, writes=(), reasons=())
    if not family_owned_fields(family):
        return RungPlan(
            family=family,
            rung=choice,
            writes=(),
            reasons=(f"{family}{_NO_RUNGS_REASON}",),
        )
    row = _rung_row(family, choice)
    targets = _overlay_instances(graph, family)
    wan14 = graph_has_wan14(graph)
    catalogs = {
        "unet_name": _available(available_unets),
        "clip_name": _available(available_clips),
        "vae_name": _available(available_vaes),
    }
    writes: list[RungWrite] = []
    reasons: list[str] = []
    for field in OVERLAY_FIELDS:
        wanted = getattr(row, field)
        if wanted is None:
            continue
        entries = targets[field]
        if not entries:
            reason = f"{FIELD_WIDGET_NAMES[field]} widget not on graph"
            if reason not in reasons:
                reasons.append(reason)
            continue
        for target in entries:
            if _same_value(target.current, wanted):
                continue
            reason = _write_block_reason(
                field, target, wanted, wan14, catalogs.get(field, set())
            )
            if reason:
                if reason not in reasons:
                    reasons.append(reason)
                continue
            writes.append(
                RungWrite(
                    node_index=target.node_index,
                    node_type=target.node_type,
                    field=field,
                    value=wanted,
                )
            )
    return RungPlan(
        family=family, rung=choice, writes=tuple(writes), reasons=tuple(reasons)
    )


def rung_refusal_reasons(
    graph: Mapping[str, Json],
    rung: str,
    *,
    available_unets: Sequence[str] | None = None,
    available_clips: Sequence[str] | None = None,
    available_vaes: Sequence[str] | None = None,
) -> tuple[str, ...]:
    """Return every reason one apply must be refused, in the caption's words.

    The whole list, never a truncated pair: a CLI or a caption that hides the
    second reason is how a graph ends up labelled with a rung it never had.

    Args:
        graph: Serialized Comfy graph.
        rung: Rung id, any case, or an accepted legacy id.
        available_unets: UNET combo options; empty/None skips the presence check.
        available_clips: CLIP combo options.
        available_vaes: VAE combo options.

    Returns:
        Reason strings, empty when the apply would land.
    """
    return plan_rung_writes(
        graph,
        rung,
        available_unets=available_unets,
        available_clips=available_clips,
        available_vaes=available_vaes,
    ).reasons


def apply_to_graph(
    graph: JsonObject,
    quality: str,
    *,
    available_unets: Sequence[str] | None = None,
    available_clips: Sequence[str] | None = None,
    available_vaes: Sequence[str] | None = None,
) -> JsonObject:
    """Write one rung's whole table into KSampler / loader widgets, or refuse it.

    Write-or-refuse, exactly like ``applyQuality`` in ``ez_quality.js``: if any
    write in the row cannot land, nothing at all is written and no weight is
    substituted for a file that is missing. ``rung_refusal_reasons`` names why.
    Does not touch latent size, frames, or any ``EZImageFormat`` widget.

    Args:
        graph: Serialized Comfy graph (mutated).
        quality: Rung id, or an accepted legacy id (it normalizes first).
        available_unets: Combo options for UNET swaps.
        available_clips: Combo options for CLIP swaps.
        available_vaes: Combo options for VAE swaps.

    Returns:
        The same graph dict, unchanged when the apply was refused.
    """
    plan = plan_rung_writes(
        graph,
        quality,
        available_unets=available_unets,
        available_clips=available_clips,
        available_vaes=available_vaes,
    )
    if plan.refused:
        return graph
    nodes = cast("list[QualityGraphNode]", graph.get("nodes") or [])
    for write in plan.writes:
        values = cast("WidgetsValues", nodes[write.node_index]["widgets_values"])
        values[_FIELD_SLOT_INDEX[write.field]] = write.value
    return graph


# ---------------------------------------------------------------------------
# Rung table - the one definition the frontend is generated from.
# ---------------------------------------------------------------------------


def _profile(
    family: str,
    quality: str,
    *,
    available_unets: Sequence[str] | None,
    available_clips: Sequence[str] | None,
    available_vaes: Sequence[str] | None,
    authored_steps: int = 0,
) -> QualityOverlay:
    """Resolve one family row against a loader availability set.

    Args:
        family: Occupancy id, QUALITY_FAMILY_KLEIN3, or QUALITY_FAMILY_QWEN.
        quality: Combo value.
        available_unets: UNET combo options, None for the whole catalog.
        available_clips: CLIP combo options.
        available_vaes: VAE combo options.
        authored_steps: KSampler steps, carried through to resolve_overlay.

    Returns:
        Overlay of requested values; None leaves that widget authored.
    """
    pinned = _FAMILY_PINNED.get(family)
    if pinned is None:
        return QualityOverlay()
    everything = sorted(_ALL_CATALOG_WEIGHTS)
    return resolve_overlay(
        occupancy=family,
        quality=quality,
        authored_steps=authored_steps,
        authored_cfg=1.0,
        unet_name=pinned["unet"],
        available_unets=everything if available_unets is None else available_unets,
        clip_name=pinned["clip"],
        available_clips=everything if available_clips is None else available_clips,
        vae_name=pinned["vae"],
        available_vaes=everything if available_vaes is None else available_vaes,
    )


def tier_profile(
    family: str,
    quality: str,
    *,
    available_unets: Sequence[str] | None = None,
    available_clips: Sequence[str] | None = None,
    available_vaes: Sequence[str] | None = None,
    authored_steps: int = 0,
) -> QualityOverlay:
    """Return what one rung asks one family to change.

    Args:
        family: Occupancy id, QUALITY_FAMILY_KLEIN3, or QUALITY_FAMILY_QWEN.
        quality: Combo value.
        available_unets: UNET combo options, None for the whole catalog.
        available_clips: CLIP combo options.
        available_vaes: VAE combo options.
        authored_steps: KSampler steps, carried through to resolve_overlay.

    Returns:
        Overlay of requested values; None leaves that widget authored.
    """
    return _profile(
        family,
        quality,
        available_unets=available_unets,
        available_clips=available_clips,
        available_vaes=available_vaes,
        authored_steps=authored_steps,
    )


def family_owned_fields(family: str) -> tuple[str, ...]:
    """Return the overlay fields this family's rungs write.

    Fields no rung in the family ever sets stay authored, so an edit to one of
    them never leaves the rung's level. ``standard`` writes nothing, so the
    answer comes from ``draft`` and ``final`` alone.

    Args:
        family: Occupancy id, QUALITY_FAMILY_KLEIN3, or QUALITY_FAMILY_QWEN.

    Returns:
        Field names in OVERLAY_FIELDS order, empty for a no-op family.
    """
    owned: set[str] = set()
    for choice in NAMED_QUALITY_CHOICES:
        profile = tier_profile(family, choice)
        for field in OVERLAY_FIELDS:
            if getattr(profile, field) is not None:
                owned.add(field)
    return tuple(f for f in OVERLAY_FIELDS if f in owned)


def tiers_for_family(family: str) -> tuple[str, ...]:
    """Return the rungs one family can actually carry, in combo order.

    ``standard`` belongs to every family that has a combo at all, because it
    writes nothing and therefore always lands. A ``draft`` or ``final`` belongs
    to the family only when its row writes at least one field: a rung whose
    overlay is all-None changes no widget, yet the combo still stamps it as
    applied, so those stay out. That is what keeps a Klein graph from offering
    the FLUX 3 and Qwen-Image rows and a Wan graph from offering a weight swap
    it has no loader for.

    Args:
        family: Occupancy id, QUALITY_FAMILY_KLEIN3, or QUALITY_FAMILY_QWEN.

    Returns:
        Rung ids in QUALITY_CHOICES order; empty for a no-op family.
    """
    if not family_owned_fields(family):
        return ()
    honored: list[str] = []
    for choice in QUALITY_CHOICES:
        if choice == QUALITY_STANDARD:
            honored.append(choice)
            continue
        profile = tier_profile(family, choice)
        if any(getattr(profile, field) is not None for field in OVERLAY_FIELDS):
            honored.append(choice)
    return tuple(honored)


def tier_label(family: str, quality: str) -> str:
    """Describe one rung the way the combo should, weights before steps.

    Klein rungs swap weights rather than climbing a step ladder, so the label
    names the transformer and the sampler settings it pins. ``standard`` names
    nothing, because it writes nothing.

    Args:
        family: Occupancy id, QUALITY_FAMILY_KLEIN3, or QUALITY_FAMILY_QWEN.
        quality: Combo value.

    Returns:
        Caption text, empty for a rung that changes nothing.
    """
    profile = tier_profile(family, quality)
    parts: list[str] = []
    if profile.unet_name:
        parts.append(profile.unet_name.rsplit(".", 1)[0])
    if profile.steps is not None:
        parts.append(f"{profile.steps} steps")
    if profile.cfg is not None:
        parts.append(f"CFG {profile.cfg}")
    return ", ".join(parts)


def tier_is_honored(family: str, quality: str) -> bool:
    """True when one family can actually carry one rung.

    A rung the family does not list would write no widget and still stamp the
    row, so the operator would be told a level was reached that the graph never
    had. Refusing it is the whole contract: there is no fallback rung.

    Args:
        family: Occupancy id, such as ``wan``.
        quality: Raw rung as typed, any case, or an accepted legacy id.

    Returns:
        True when applying the rung writes something or lands by writing nothing.
    """
    return normalize_quality(quality) in tiers_for_family(family)


def export_table() -> dict[str, Json]:
    """Return the full rung table in JSON-safe form.

    Args:
        None.

    Returns:
        Mapping with the rung table, owned fields, per-family rung lists,
        labels, the caption's license and stack words, and the rung order.
    """
    table: JsonObject = {}
    owned: JsonObject = {}
    labels: JsonObject = {}
    tiers: JsonObject = {}
    for family in QUALITY_FAMILIES:
        per_choice: JsonObject = {}
        per_label: JsonObject = {}
        for choice in NAMED_QUALITY_CHOICES:
            profile = tier_profile(family, choice)
            per_choice[choice] = {
                field: getattr(profile, field) for field in OVERLAY_FIELDS
            }
            per_label[choice] = tier_label(family, choice)
        table[family] = per_choice
        labels[family] = per_label
        owned[family] = list(family_owned_fields(family))
        tiers[family] = list(tiers_for_family(family))
    payload: JsonObject = {
        "choices": list(QUALITY_CHOICES),
        "default": QUALITY_DEFAULT,
        "named": list(NAMED_QUALITY_CHOICES),
        "families": list(QUALITY_FAMILIES),
        "fields": list(OVERLAY_FIELDS),
        "table": table,
        "owned": owned,
        "labels": labels,
        "tiers": tiers,
        "licenses": dict(LICENSE_LABEL),
        "stacks": dict(STACK_LABEL),
        "unet_stacks": dict(UNET_STACK_LABEL),
        "rung_labels": dict(RUNG_LABEL),
        "field_names": dict(FIELD_WIDGET_NAMES),
        "edited_prefix": EDITED_PREFIX,
    }
    return payload
