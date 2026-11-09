"""Family-specific Quality overlays (custom / draft / lab / standard / high /
Free Commercial Use / ultra / max / flux3-fast / flux3-quality / flux3-nvfp4 /
qwen-image / qwen-image-turbo / qwen-image-nvfp4 / qwen-image-turbo-nvfp4).

This module is the only definition of what a tier asks for. The frontend reads
a table generated from it (``export_table`` -> tests/python/_build_quality_js.py
-> custom_nodes/ez_quality/js/ez_quality_presets.js, via ``bazelisk run
//tests:build_quality_js``) and derives the combo from
that table, so no tier number or weight name lives in JS. ``match_tier`` is the
mirror of the apply: it names the level the widgets currently sit on.

Overlays never change width, height, frames, or length. Named qualities may
swap UNET, CLIP, and VAE when the files are present; a value that cannot be
written is a failed apply, not a silent skip. ``custom`` keeps whatever the
widgets currently hold, and ``match_tier`` is what decides that a graph sits
there. ``lab`` means the widgets still equal the load-time authored values.
``Free Commercial Use (<$10M)`` is Apache Klein 4B + LTX-2.5 only - never
Klein 9B or FLUX.2-dev. Wan / audio / trellis are no-ops for that choice.
The flux3-* profiles apply only to graphs that pin FLUX 3 Image Klein
weights; on any other graph they are no-ops, and on such a graph the Klein
ladder is a no-op too rather than a Klein 4B downgrade.
The qwen-image* profiles apply only to graphs that pin opt-in Qwen-Image 2.1
weights. Those are the Qwen RESEARCH LICENSE AGREEMENT (section 2.b bars
commercial use without a separate paid Qwen license), so no qwen tier is a
default or a recommended profile and Klein 4B stays the Apache still; on any
other graph they are no-ops, and on such a graph the Klein ladder and the
flux3-* profiles are no-ops too.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Mapping, Sequence, TypeAlias, cast

if TYPE_CHECKING:
    from ez_common import Json, JsonMap, JsonObject, WidgetsValues

QualityGraphNode: TypeAlias = "Mapping[str, Json]"
"""One ``nodes`` row as parsed from a graph document, before any shaping."""

# Quality ids, Klein filenames, family step/CFG overlays, widget indexes.
QUALITY_CUSTOM = "custom"
QUALITY_DRAFT = "draft"
QUALITY_LAB = "lab"
QUALITY_STANDARD = "standard"
QUALITY_HIGH = "high"
QUALITY_FREE_COMMERCIAL = "Free Commercial Use (<$10M)"
QUALITY_FREE_COMMERCIAL_ALIAS = "free_commercial"
QUALITY_ULTRA = "ultra"
QUALITY_MAX = "max"
QUALITY_FLUX3_FAST = "flux3-fast"
QUALITY_FLUX3_QUALITY = "flux3-quality"
QUALITY_FLUX3_NVFP4 = "flux3-nvfp4"
# Opt-in Qwen-Image 2.1 tiers: one combo row per download-image --tier, so the
# combo, the checker, and the CLI all name the same opt-in pack.
QUALITY_QWEN_IMAGE = "qwen-image"
QUALITY_QWEN_IMAGE_TURBO = "qwen-image-turbo"
QUALITY_QWEN_IMAGE_NVFP4 = "qwen-image-nvfp4"
QUALITY_QWEN_IMAGE_TURBO_NVFP4 = "qwen-image-turbo-nvfp4"
QUALITY_CHOICES: tuple[str, ...] = (
    QUALITY_CUSTOM,
    QUALITY_DRAFT,
    QUALITY_LAB,
    QUALITY_STANDARD,
    QUALITY_HIGH,
    QUALITY_FREE_COMMERCIAL,
    QUALITY_ULTRA,
    QUALITY_MAX,
    QUALITY_FLUX3_FAST,
    QUALITY_FLUX3_QUALITY,
    QUALITY_FLUX3_NVFP4,
    QUALITY_QWEN_IMAGE,
    QUALITY_QWEN_IMAGE_TURBO,
    QUALITY_QWEN_IMAGE_NVFP4,
    QUALITY_QWEN_IMAGE_TURBO_NVFP4,
)
# casefold(widget value) -> canonical QUALITY_CHOICES entry (incl. alias).
_QUALITY_NORMALIZE: dict[str, str] = {
    choice.casefold(): choice for choice in QUALITY_CHOICES
}
_QUALITY_NORMALIZE[QUALITY_FREE_COMMERCIAL_ALIAS] = QUALITY_FREE_COMMERCIAL
# Profiles that only ever write on a graph pinning FLUX 3 Image Klein weights.
FLUX3_QUALITY_CHOICES: tuple[str, ...] = (
    QUALITY_FLUX3_FAST,
    QUALITY_FLUX3_QUALITY,
    QUALITY_FLUX3_NVFP4,
)
# Profiles that only ever write on a graph pinning Qwen-Image 2.1 weights.
# Opt-in only: none of them is a default or a recommended profile.
QWEN_QUALITY_CHOICES: tuple[str, ...] = (
    QUALITY_QWEN_IMAGE,
    QUALITY_QWEN_IMAGE_TURBO,
    QUALITY_QWEN_IMAGE_NVFP4,
    QUALITY_QWEN_IMAGE_TURBO_NVFP4,
)

# Klein filenames, family step/CFG overlays, widget indexes.
KLEIN_DISTILLED = "flux-2-klein-4b-fp8.safetensors"
KLEIN_NVFP4 = "flux-2-klein-4b-nvfp4.safetensors"
KLEIN_BASE = "flux-2-klein-base-4b-fp8.safetensors"
KLEIN_9B = "flux-2-klein-9b-fp8.safetensors"
KLEIN_9B_BASE = "flux-2-klein-base-9b-fp8.safetensors"
KLEIN_9B_NVFP4 = "flux-2-klein-9b-nvfp4.safetensors"
FLUX2_DEV = "flux2_dev_fp8mixed.safetensors"
# FLUX 3 Image Klein (KLEIN3) weights from the official Comfy repo.
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
# Qwen-Image 2.1 VAE, shared by all four opt-in tiers.
QWEN_VAE = "qwen_image_2.1_vae_bf16.safetensors"

KLEIN_DRAFT_STEPS = 4
KLEIN_DRAFT_CFG = 1.0
KLEIN_STANDARD_STEPS = 8
KLEIN_STANDARD_CFG = 1.0
KLEIN_HIGH_DISTILLED_STEPS = 8
KLEIN_HIGH_DISTILLED_CFG = 1.0
KLEIN_HIGH_BASE_STEPS = 24
KLEIN_HIGH_BASE_CFG = 3.5
KLEIN_9B_STEPS = 4
KLEIN_9B_CFG = 1.0
KLEIN_9B_BASE_STEPS = 20
KLEIN_9B_BASE_CFG = 5.0
FLUX2_DEV_STEPS = 20
FLUX2_DEV_CFG = 4.0
# KLEIN3: distilled is guidance-free (official range 4-16 steps); the base
# recipe is BFL's own 50 steps at CFG 3.5, and NVFP4 follows the base recipe.
KLEIN3_FAST_STEPS = 16
KLEIN3_FAST_CFG = 1.0
KLEIN3_QUALITY_STEPS = 50
KLEIN3_QUALITY_CFG = 3.5
KLEIN3_NVFP4_STEPS = 50
KLEIN3_NVFP4_CFG = 3.5
# Qwen-Image 2.1: the Turbo pair is the distilled sibling, so it takes the same
# guidance-free low-step recipe FLUX 3 fast uses (16 at CFG 1.0); the non-Turbo
# pair takes FLUX 3's base recipe (50 at CFG 3.5), and each NVFP4 conversion
# follows the recipe of the INT8 weight it converts.
QWEN_QUALITY_STEPS = 50
QWEN_QUALITY_CFG = 3.5
QWEN_TURBO_STEPS = 16
QWEN_TURBO_CFG = 1.0
QWEN_NVFP4_STEPS = 50
QWEN_NVFP4_CFG = 3.5
QWEN_TURBO_NVFP4_STEPS = 16
QWEN_TURBO_NVFP4_CFG = 1.0

WAN_DRAFT_STEPS = 12
WAN_STANDARD_STEPS = 20
WAN_HIGH_STEPS = 28
WAN_MAX_STEPS = 32
LTX_DRAFT_STEPS = 12
LTX_STANDARD_STEPS = 20
LTX_HIGH_STEPS = 28
LTX_MAX_STEPS = 32
AUDIO_DRAFT_STEPS = 4
AUDIO_STANDARD_STEPS = 8
AUDIO_HIGH_STEPS = 16
AUDIO_MAX_STEPS = 24
TRELLIS_DRAFT_STEPS = 8
TRELLIS_STANDARD_STEPS = 12
TRELLIS_HIGH_STEPS = 20
TRELLIS_MAX_STEPS = 28

# A TRELLIS stage authored at this CFG runs without guidance: it is the texture
# pass, not one of the three guided stages. The TRELLIS ladder is tuned against
# the guided stages, so it leaves this one on its authored step count.
TRELLIS_GUIDANCE_FREE_CFG = 1.0

KSAMPLER_STEPS_INDEX = 2
KSAMPLER_CFG_INDEX = 3
UNET_NAME_INDEX = 0
CLIP_NAME_INDEX = 0
VAE_NAME_INDEX = 0

# The only node types apply_to_graph can write. A graph that carries none of
# them has nothing for a tier to change, so it gets no Quality combo; keep this
# in step with the node dispatch in apply_to_graph.
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
_LTX_OCCUPANCY = frozenset({"ltx", "film"})
_FREEZE_QUALITIES = frozenset({QUALITY_CUSTOM, QUALITY_LAB})


@dataclass(frozen=True)
class QualityOverlay:
    """Optional widget writes. None means leave the authored value."""

    steps: int | None = None
    cfg: float | None = None
    unet_name: str | None = None
    clip_name: str | None = None
    vae_name: str | None = None
    clip_type: str | None = None


def normalize_quality(value: Json) -> str:
    """Return a legal quality id, defaulting to lab.

    Args:
        value: Combo widget value or parsed body value.

    Returns:
        One of QUALITY_CHOICES.
    """
    raw = str(value or QUALITY_LAB).strip().casefold()
    return _QUALITY_NORMALIZE.get(raw, QUALITY_LAB)


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

    Args:
        name: UNET filename.

    Returns:
        True when the name looks like Klein 9B.
    """
    blob = name.lower()
    return "klein" in blob and "9b" in blob


def is_flux2_dev_unet(name: str) -> bool:
    """True for FLUX.2-dev diffusion filenames.

    Args:
        name: UNET filename.

    Returns:
        True when the name looks like flux2_dev / flux-2-dev.
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
    """Return the overlay for one sampler + loader set.

    Args:
        occupancy: extra.lab_app_mode.occupancy (klein, wan, ltx, ...).
        quality: quality id.
        authored_steps: Current KSampler steps.
        authored_cfg: Current KSampler CFG.
        unet_name: Current UNETLoader filename (may be empty).
        available_unets: UNET combo options. Empty/None refuses UNET swaps.
        clip_name: Current CLIPLoader filename.
        available_clips: CLIP combo options.
        vae_name: Current VAELoader filename.
        available_vaes: VAE combo options.

    Returns:
        Overlay with None for knobs that must stay authored.
    """
    del authored_cfg
    choice = normalize_quality(quality)
    occ = (occupancy or "").strip().lower()
    if choice in _FREEZE_QUALITIES or occ in _NOOP_OCCUPANCY:
        return QualityOverlay()
    if is_wan_14b_unet(unet_name):
        return QualityOverlay()
    # A graph that pins FLUX 3 Image Klein weights has its own three profiles.
    # The Klein ladder must never drop Klein 4B weights onto them.
    if choice not in FLUX3_QUALITY_CHOICES and (
        is_klein3_unet(unet_name) or is_klein3_clip(clip_name)
    ):
        return QualityOverlay()
    # Same for a graph that pins opt-in Qwen-Image 2.1 weights: neither the
    # Klein ladder nor the FLUX 3 profiles may drop other vendors' weights
    # onto them, and the reverse guard below keeps the qwen tiers off them.
    if choice not in QWEN_QUALITY_CHOICES and (
        is_qwen_image_unet(unet_name) or is_qwen_image_clip(clip_name)
    ):
        return QualityOverlay()
    available = _available(available_unets)
    clips = _available(available_clips)
    vaes = _available(available_vaes)

    if choice == QUALITY_FREE_COMMERCIAL:
        return _free_commercial_overlay(
            occ,
            authored_steps,
            unet_name,
            clip_name,
            vae_name,
            available,
            clips,
            vaes,
        )

    if choice in FLUX3_QUALITY_CHOICES:
        return _flux3_overlay(
            choice, unet_name, clip_name, vae_name, available, clips, vaes
        )

    if choice in QWEN_QUALITY_CHOICES:
        return _qwen_image_overlay(
            choice, unet_name, clip_name, vae_name, available, clips, vaes
        )

    if occ == "klein" or is_klein_4b_unet(unet_name) or is_klein_9b_unet(unet_name):
        return _klein_overlay(
            choice,
            authored_steps,
            unet_name,
            clip_name,
            vae_name,
            available,
            clips,
            vaes,
        )
    if occ == "wan":
        return QualityOverlay(steps=_wan_steps(choice))
    if occ in _LTX_OCCUPANCY:
        return QualityOverlay(steps=_ltx_steps(choice))
    if occ == "audio":
        return QualityOverlay(steps=_audio_steps(choice))
    if occ == "trellis":
        return QualityOverlay(steps=_trellis_steps(choice))
    return QualityOverlay()


def _wan_steps(choice: str) -> int | None:
    """Wan 5B step overlay.

    Args:
        choice: Named quality (not custom/lab).

    Returns:
        Step count, or None when Wan has no level by that name.
    """
    if choice == QUALITY_DRAFT:
        return WAN_DRAFT_STEPS
    if choice == QUALITY_STANDARD:
        return WAN_STANDARD_STEPS
    if choice == QUALITY_HIGH:
        return WAN_HIGH_STEPS
    if choice == QUALITY_MAX:
        return WAN_MAX_STEPS
    return None


def _ltx_steps(choice: str) -> int | None:
    """LTX / film step overlay.

    Args:
        choice: Named quality.

    Returns:
        Step count, or None when LTX has no level by that name.
    """
    if choice == QUALITY_DRAFT:
        return LTX_DRAFT_STEPS
    if choice == QUALITY_STANDARD:
        return LTX_STANDARD_STEPS
    if choice == QUALITY_HIGH:
        return LTX_HIGH_STEPS
    if choice == QUALITY_MAX:
        return LTX_MAX_STEPS
    return None


def _audio_steps(choice: str) -> int | None:
    """ACE / audio step overlay.

    Args:
        choice: Named quality.

    Returns:
        Step count, or None when audio has no level by that name.
    """
    if choice == QUALITY_DRAFT:
        return AUDIO_DRAFT_STEPS
    if choice == QUALITY_STANDARD:
        return AUDIO_STANDARD_STEPS
    if choice == QUALITY_HIGH:
        return AUDIO_HIGH_STEPS
    if choice == QUALITY_MAX:
        return AUDIO_MAX_STEPS
    return None


def _trellis_steps(choice: str) -> int | None:
    """TRELLIS step overlay.

    Args:
        choice: Named quality.

    Returns:
        Step count, or None when TRELLIS has no level by that name.
    """
    if choice == QUALITY_DRAFT:
        return TRELLIS_DRAFT_STEPS
    if choice == QUALITY_STANDARD:
        return TRELLIS_STANDARD_STEPS
    if choice == QUALITY_HIGH:
        return TRELLIS_HIGH_STEPS
    if choice == QUALITY_MAX:
        return TRELLIS_MAX_STEPS
    return None


def is_trellis_guidance_free_stage(node: Mapping[str, Json], family: str) -> bool:
    """True when one TRELLIS KSampler is the unguided texture pass.

    The TRELLIS graph runs three guided stages at CFG 7.5 and one texture
    stage at CFG 1.0. The step ladder is tuned against the guided stages, and
    the texture stage's own step count is part of its recipe, so the overlay
    leaves that sampler alone and reads the tier off the guided stages.

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


def _free_commercial_overlay(
    occupancy: str,
    authored_steps: int,
    unet_name: str,
    clip_name: str,
    vae_name: str,
    available: set[str],
    clips: set[str],
    vaes: set[str],
) -> QualityOverlay:
    """Apache Klein 4B stills + LTX-2.5 steps. Never 9B / FLUX.2-dev.

    Wan, audio, trellis, and labs/assist graphs are no-ops. Python never writes size.

    Args:
        occupancy: Graph occupancy id.
        authored_steps: Current KSampler steps.
        unet_name: Current UNET filename.
        clip_name: Current CLIP filename.
        vae_name: Current VAE filename.
        available: UNET combo options.
        clips: CLIP combo options.
        vaes: VAE combo options.

    Returns:
        Overlay for the commercial path, or empty.
    """
    if (
        occupancy == "klein"
        or is_klein_4b_unet(unet_name)
        or is_klein_9b_unet(unet_name)
        or is_flux2_dev_unet(unet_name)
    ):
        return _klein_high(
            authored_steps, unet_name, clip_name, vae_name, available, clips, vaes
        )
    if occupancy in _LTX_OCCUPANCY:
        return QualityOverlay(steps=LTX_HIGH_STEPS)
    return QualityOverlay()


def _flux3_overlay(
    choice: str,
    unet_name: str,
    clip_name: str,
    vae_name: str,
    available: set[str],
    clips: set[str],
    vaes: set[str],
) -> QualityOverlay:
    """FLUX 3 Image Klein profile, or empty when the graph pins other weights.

    Args:
        choice: One of FLUX3_QUALITY_CHOICES.
        unet_name: Current UNET filename.
        clip_name: Current CLIP filename.
        vae_name: Current VAE filename.
        available: UNET combo options.
        clips: CLIP combo options.
        vaes: VAE combo options.

    Returns:
        Overlay for the pinned KLEIN3 family, or empty for any other family.
    """
    if not (is_klein3_unet(unet_name) or is_klein3_clip(clip_name)):
        return QualityOverlay()
    if choice == QUALITY_FLUX3_NVFP4:
        unet = _pick_unet(KLEIN3_NVFP4, available)
        steps, cfg = KLEIN3_NVFP4_STEPS, KLEIN3_NVFP4_CFG
    elif choice == QUALITY_FLUX3_QUALITY:
        unet = _pick_unet(KLEIN3_BASE, available)
        steps, cfg = KLEIN3_QUALITY_STEPS, KLEIN3_QUALITY_CFG
    else:
        unet = _pick_unet(KLEIN3_DISTILLED, available)
        steps, cfg = KLEIN3_FAST_STEPS, KLEIN3_FAST_CFG
    return QualityOverlay(
        steps=steps,
        cfg=cfg,
        unet_name=_changed(unet_name, unet),
        clip_name=_changed(clip_name, _pick_file(KLEIN3_TE, clips)),
        vae_name=_changed(vae_name, _pick_file(VAE_FULL, vaes)),
        clip_type=CLIP_TYPE_FLUX2,
    )


def _qwen_image_overlay(
    choice: str,
    unet_name: str,
    clip_name: str,
    vae_name: str,
    available: set[str],
    clips: set[str],
    vaes: set[str],
) -> QualityOverlay:
    """Qwen-Image 2.1 profile, or empty when the graph pins other weights.

    Opt-in only: these weights are the Qwen RESEARCH LICENSE AGREEMENT
    (section 2.b bars commercial use without a separate paid Qwen license), so
    no tier here is a default or a recommended profile and Klein 4B stays the
    Apache still. The CLIPLoader type is left authored - the graph authors the
    Qwen3VL type, and this tier has nothing to rewrite it to.

    Args:
        choice: One of QWEN_QUALITY_CHOICES.
        unet_name: Current UNET filename.
        clip_name: Current CLIP filename.
        vae_name: Current VAE filename.
        available: UNET combo options.
        clips: CLIP combo options.
        vaes: VAE combo options.

    Returns:
        Overlay for the pinned Qwen-Image family, or empty for any other family.
    """
    if not (is_qwen_image_unet(unet_name) or is_qwen_image_clip(clip_name)):
        return QualityOverlay()
    if choice == QUALITY_QWEN_IMAGE:
        unet, te = QWEN_IMAGE_INT8, QWEN_TE
        steps, cfg = QWEN_QUALITY_STEPS, QWEN_QUALITY_CFG
    elif choice == QUALITY_QWEN_IMAGE_TURBO:
        unet, te = QWEN_IMAGE_TURBO_INT8, QWEN_TE
        steps, cfg = QWEN_TURBO_STEPS, QWEN_TURBO_CFG
    elif choice == QUALITY_QWEN_IMAGE_NVFP4:
        unet, te = QWEN_IMAGE_NVFP4, QWEN_TE_NVFP4
        steps, cfg = QWEN_NVFP4_STEPS, QWEN_NVFP4_CFG
    else:
        unet, te = QWEN_IMAGE_TURBO_NVFP4, QWEN_TE_TURBO_NVFP4
        steps, cfg = QWEN_TURBO_NVFP4_STEPS, QWEN_TURBO_NVFP4_CFG
    return QualityOverlay(
        steps=steps,
        cfg=cfg,
        unet_name=_changed(unet_name, _pick_unet(unet, available)),
        clip_name=_changed(clip_name, _pick_file(te, clips)),
        vae_name=_changed(vae_name, _pick_file(QWEN_VAE, vaes)),
    )


def _klein_overlay(
    choice: str,
    authored_steps: int,
    unet_name: str,
    clip_name: str,
    vae_name: str,
    available: set[str],
    clips: set[str],
    vaes: set[str],
) -> QualityOverlay:
    """Klein / Flux.2 still overlay for a named quality.

    Args:
        choice: Named quality (not custom/lab).
        authored_steps: Current KSampler steps.
        unet_name: Current UNET filename.
        clip_name: Current CLIP filename.
        vae_name: Current VAE filename.
        available: UNET combo options.
        clips: CLIP combo options.
        vaes: VAE combo options.

    Returns:
        Overlay for Klein occupancy.
    """
    if choice == QUALITY_DRAFT:
        unet = None
        if is_klein_4b_unet(unet_name) or is_klein_9b_unet(unet_name):
            unet = _pick_unet(KLEIN_NVFP4, available) or _pick_unet(
                KLEIN_DISTILLED, available
            )
        return QualityOverlay(
            steps=KLEIN_DRAFT_STEPS,
            cfg=KLEIN_DRAFT_CFG,
            unet_name=_changed(unet_name, unet),
            clip_name=_changed(clip_name, _pick_file(CLIP_4B, clips)),
            vae_name=_changed(
                vae_name, _pick_file(VAE_SMALL, vaes) or _pick_file(VAE_FULL, vaes)
            ),
            clip_type=CLIP_TYPE_FLUX2,
        )
    if choice == QUALITY_STANDARD:
        return QualityOverlay(
            steps=KLEIN_STANDARD_STEPS,
            cfg=KLEIN_STANDARD_CFG,
            unet_name=_changed(unet_name, _pick_unet(KLEIN_DISTILLED, available)),
            clip_name=_changed(clip_name, _pick_file(CLIP_4B, clips)),
            vae_name=_changed(
                vae_name, _pick_file(VAE_SMALL, vaes) or _pick_file(VAE_FULL, vaes)
            ),
            clip_type=CLIP_TYPE_FLUX2,
        )
    if choice == QUALITY_HIGH:
        return _klein_high(
            authored_steps, unet_name, clip_name, vae_name, available, clips, vaes
        )
    if choice == QUALITY_ULTRA:
        nine = _pick_unet(KLEIN_9B, available) or _pick_unet(KLEIN_9B_NVFP4, available)
        if nine is not None:
            return QualityOverlay(
                steps=KLEIN_9B_STEPS,
                cfg=KLEIN_9B_CFG,
                unet_name=_changed(unet_name, nine),
                clip_name=_changed(clip_name, _pick_file(CLIP_8B, clips)),
                vae_name=_changed(
                    vae_name, _pick_file(VAE_SMALL, vaes) or _pick_file(VAE_FULL, vaes)
                ),
                clip_type=CLIP_TYPE_FLUX2,
            )
        return _klein_high(
            authored_steps, unet_name, clip_name, vae_name, available, clips, vaes
        )
    if choice == QUALITY_MAX:
        nine_base = _pick_unet(KLEIN_9B_BASE, available)
        if nine_base is not None:
            return QualityOverlay(
                steps=KLEIN_9B_BASE_STEPS,
                cfg=KLEIN_9B_BASE_CFG,
                unet_name=_changed(unet_name, nine_base),
                clip_name=_changed(clip_name, _pick_file(CLIP_8B, clips)),
                vae_name=_changed(
                    vae_name, _pick_file(VAE_SMALL, vaes) or _pick_file(VAE_FULL, vaes)
                ),
                clip_type=CLIP_TYPE_FLUX2,
            )
        dev = _pick_unet(FLUX2_DEV, available)
        if dev is not None:
            return QualityOverlay(
                steps=FLUX2_DEV_STEPS,
                cfg=FLUX2_DEV_CFG,
                unet_name=_changed(unet_name, dev),
                clip_name=_changed(clip_name, _pick_file(CLIP_MISTRAL, clips)),
                vae_name=_changed(
                    vae_name, _pick_file(VAE_SMALL, vaes) or _pick_file(VAE_FULL, vaes)
                ),
                clip_type=CLIP_TYPE_FLUX2,
            )
        return _klein_high(
            authored_steps, unet_name, clip_name, vae_name, available, clips, vaes
        )
    return _klein_high(
        authored_steps, unet_name, clip_name, vae_name, available, clips, vaes
    )


def _klein_high(
    authored_steps: int,
    unet_name: str,
    clip_name: str,
    vae_name: str,
    available: set[str],
    clips: set[str],
    vaes: set[str],
) -> QualityOverlay:
    """Apache high: 4B base if present, else distilled 8 steps.

    Args:
        authored_steps: Current KSampler steps.
        unet_name: Current UNET filename.
        clip_name: Current CLIP filename.
        vae_name: Current VAE filename.
        available: UNET combo options.
        clips: CLIP combo options.
        vaes: VAE combo options.

    Returns:
        High overlay.
    """
    base = _pick_unet(KLEIN_BASE, available)
    clip = _pick_file(CLIP_4B, clips)
    vae = _pick_file(VAE_SMALL, vaes) or _pick_file(VAE_FULL, vaes)
    if base is not None and (
        is_klein_4b_unet(unet_name) or is_klein_9b_unet(unet_name) or not unet_name
    ):
        return QualityOverlay(
            steps=KLEIN_HIGH_BASE_STEPS,
            cfg=KLEIN_HIGH_BASE_CFG,
            unet_name=_changed(unet_name, base),
            clip_name=_changed(clip_name, clip),
            vae_name=_changed(vae_name, vae),
            clip_type=CLIP_TYPE_FLUX2,
        )
    steps = authored_steps
    if steps < KLEIN_HIGH_DISTILLED_STEPS:
        steps = KLEIN_HIGH_DISTILLED_STEPS
    return QualityOverlay(
        steps=steps,
        cfg=KLEIN_HIGH_DISTILLED_CFG,
        unet_name=_changed(unet_name, _pick_unet(KLEIN_DISTILLED, available)),
        clip_name=_changed(clip_name, clip),
        vae_name=_changed(vae_name, vae),
        clip_type=CLIP_TYPE_FLUX2,
    )


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


def _first_loader_name(graph: Mapping[str, Json], node_type: str) -> str:
    """First loader filename of ``node_type``.

    Args:
        graph: Serialized Comfy graph.
        node_type: UNETLoader, CLIPLoader, or VAELoader.

    Returns:
        Filename, or empty string when none is present.
    """
    for node in cast("list[QualityGraphNode]", graph.get("nodes") or []):
        if node.get("type") != node_type:
            continue
        values = cast("WidgetsValues", node.get("widgets_values") or [])
        if values:
            return str(values[0])
    return ""


def graph_has_wan14(graph: Mapping[str, Json]) -> bool:
    """True when any UNETLoader is a Wan 14B file.

    Args:
        graph: Serialized Comfy graph.

    Returns:
        True when a 14B UNET is present.
    """
    for node in cast("list[QualityGraphNode]", graph.get("nodes") or []):
        if node.get("type") != "UNETLoader":
            continue
        values = cast("WidgetsValues", node.get("widgets_values") or [])
        if values and is_wan_14b_unet(str(values[0])):
            return True
    return False


def apply_to_graph(
    graph: JsonObject,
    quality: str,
    *,
    available_unets: Sequence[str] | None = None,
    available_clips: Sequence[str] | None = None,
    available_vaes: Sequence[str] | None = None,
) -> JsonObject:
    """Mutate KSampler / loader widgets_values in place.

    Does not touch latent size or frames. Lab and custom are no-ops.

    Args:
        graph: Serialized Comfy graph (mutated).
        quality: quality id.
        available_unets: Combo options for UNET swaps.
        available_clips: Combo options for CLIP swaps.
        available_vaes: Combo options for VAE swaps.

    Returns:
        The same graph dict.
    """
    choice = normalize_quality(quality)
    if choice in _FREEZE_QUALITIES or graph_has_wan14(graph):
        return graph
    occupancy = infer_occupancy(graph)
    unet_name = _first_loader_name(graph, "UNETLoader")
    clip_name = _first_loader_name(graph, "CLIPLoader")
    vae_name = _first_loader_name(graph, "VAELoader")
    overlay = resolve_overlay(
        occupancy=occupancy,
        quality=choice,
        authored_steps=0,
        authored_cfg=1.0,
        unet_name=unet_name,
        available_unets=available_unets,
        clip_name=clip_name,
        available_clips=available_clips,
        vae_name=vae_name,
        available_vaes=available_vaes,
    )
    for node in cast("list[QualityGraphNode]", graph.get("nodes") or []):
        ntype = node.get("type")
        values = node.get("widgets_values")
        if not isinstance(values, list):
            continue
        if ntype == "KSampler":
            if is_trellis_guidance_free_stage(node, occupancy):
                continue
            authored_steps = (
                int(cast("int", values[KSAMPLER_STEPS_INDEX]))
                if len(values) > KSAMPLER_STEPS_INDEX
                else 0
            )
            authored_cfg = (
                float(cast("float", values[KSAMPLER_CFG_INDEX]))
                if len(values) > KSAMPLER_CFG_INDEX
                else 1.0
            )
            local = resolve_overlay(
                occupancy=occupancy,
                quality=choice,
                authored_steps=authored_steps,
                authored_cfg=authored_cfg,
                unet_name=unet_name,
                available_unets=available_unets,
                clip_name=clip_name,
                available_clips=available_clips,
                vae_name=vae_name,
                available_vaes=available_vaes,
            )
            if local.steps is not None and len(values) > KSAMPLER_STEPS_INDEX:
                values[KSAMPLER_STEPS_INDEX] = local.steps
            if local.cfg is not None and len(values) > KSAMPLER_CFG_INDEX:
                values[KSAMPLER_CFG_INDEX] = local.cfg
        elif ntype == "UNETLoader":
            if overlay.unet_name is None or len(values) <= UNET_NAME_INDEX:
                continue
            if is_banned_unet(overlay.unet_name):
                continue
            current = str(values[UNET_NAME_INDEX])
            if current and not (
                is_klein_4b_unet(current)
                or is_klein_9b_unet(current)
                or is_flux2_dev_unet(current)
                or is_klein3_unet(current)
                or is_qwen_image_unet(current)
            ):
                continue
            values[UNET_NAME_INDEX] = overlay.unet_name
        elif ntype == "CLIPLoader":
            if overlay.clip_name is None or len(values) <= CLIP_NAME_INDEX:
                continue
            current = str(values[CLIP_NAME_INDEX])
            if current and not (
                is_flux2_clip(current)
                or is_klein3_clip(current)
                or is_qwen_image_clip(current)
            ):
                continue
            values[CLIP_NAME_INDEX] = overlay.clip_name
            if overlay.clip_type is not None and len(values) > 1:
                values[1] = overlay.clip_type
        elif ntype == "VAELoader":
            if overlay.vae_name is None or len(values) <= VAE_NAME_INDEX:
                continue
            current = str(values[VAE_NAME_INDEX])
            if current and not (is_flux2_vae(current) or is_qwen_image_vae(current)):
                continue
            values[VAE_NAME_INDEX] = overlay.vae_name
    return graph


# ---------------------------------------------------------------------------
# Tier table - the one definition the frontend is generated from.
# ---------------------------------------------------------------------------

# Transformer each family authors, so a table row is evaluated against the
# loaders that family really pins. resolve_overlay branches on the pinned
# weights, so the family fixture is what makes a row mean that family.
WAN_5B_UNET = "wan2.2_ti2v_5B_fp16.safetensors"
LTX_UNET = "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors"
TRELLIS_UNET = "trellis_2_int8_convrot.safetensors"

# Graphs that pin FLUX 3 Image Klein still stamp occupancy "klein", so the
# table needs a family of its own to record their profiles separately.
QUALITY_FAMILY_KLEIN3 = "klein3"
# Opt-in Qwen-Image 2.1 stills stamp occupancy "klein" too, and are opt-in (not
# Apache), so they get their own family rather than riding the Klein ladder.
QUALITY_FAMILY_QWEN = "qwen"

# resolve_overlay reports only the widgets it would actually change, so the
# family fixture must classify as the family while differing from every value
# its tiers request; otherwise a request would be recorded as "no change".
# These names are branch fixtures only and never appear in a graph.
_KLEIN_TABLE_UNET = KLEIN_9B_NVFP4
_KLEIN_TABLE_CLIP = CLIP_MISTRAL
_KLEIN_TABLE_VAE = VAE_FULL
_KLEIN3_TABLE_UNET = "flux3-image-klein-distilled-int8-convrot.safetensors"
_KLEIN3_TABLE_CLIP = "qwen3vl_4b_table_sentinel.safetensors"
_KLEIN3_TABLE_VAE = VAE_SMALL
_QWEN_TABLE_UNET = "qwen_image_2.1_base_int8_convrot.safetensors"
_QWEN_TABLE_CLIP = "qwen3vl_8b_table_sentinel.safetensors"
_QWEN_TABLE_VAE = VAE_FULL

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
        "clip": _KLEIN3_TABLE_CLIP,
        "vae": _KLEIN3_TABLE_VAE,
    },
    QUALITY_FAMILY_QWEN: {
        "unet": _QWEN_TABLE_UNET,
        "clip": _QWEN_TABLE_CLIP,
        "vae": _QWEN_TABLE_VAE,
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
# tier asks for before availability filters it. apply_to_graph filters again.
_ALL_CATALOG_WEIGHTS: frozenset[str] = frozenset(
    {
        KLEIN_DISTILLED,
        KLEIN_NVFP4,
        KLEIN_BASE,
        KLEIN_9B,
        KLEIN_9B_BASE,
        KLEIN_9B_NVFP4,
        FLUX2_DEV,
        KLEIN3_DISTILLED,
        KLEIN3_BASE,
        KLEIN3_NVFP4,
        CLIP_4B,
        CLIP_8B,
        CLIP_MISTRAL,
        KLEIN3_TE,
        VAE_FULL,
        VAE_SMALL,
        QWEN_IMAGE_INT8,
        QWEN_IMAGE_TURBO_INT8,
        QWEN_IMAGE_NVFP4,
        QWEN_IMAGE_TURBO_NVFP4,
        QWEN_TE,
        QWEN_TE_NVFP4,
        QWEN_TE_TURBO_NVFP4,
        QWEN_VAE,
        WAN_5B_UNET,
        LTX_UNET,
        TRELLIS_UNET,
    }
)

NAMED_QUALITY_CHOICES: tuple[str, ...] = tuple(
    choice for choice in QUALITY_CHOICES if choice not in _FREEZE_QUALITIES
)


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
        authored_steps: KSampler steps, used by the Klein high floor.

    Returns:
        Overlay of requested values; None leaves that widget authored.
    """
    pinned = _FAMILY_PINNED.get(family)
    if pinned is None:
        return QualityOverlay()
    everything = sorted(_ALL_CATALOG_WEIGHTS)
    return resolve_overlay(
        occupancy=(
            "klein"
            if family in (QUALITY_FAMILY_KLEIN3, QUALITY_FAMILY_QWEN)
            else family
        ),
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
    """Return what one tier asks one family to change.

    Args:
        family: Occupancy id, QUALITY_FAMILY_KLEIN3, or QUALITY_FAMILY_QWEN.
        quality: Combo value.
        available_unets: UNET combo options, None for the whole catalog.
        available_clips: CLIP combo options.
        available_vaes: VAE combo options.
        authored_steps: KSampler steps for the Klein high floor.

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
    """Return the overlay fields any named tier sets for one family.

    Fields no tier in the family ever sets stay authored, so a user edit to
    one of them does not leave the pre-configured level.

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
    """Return the named tiers one family can actually honor.

    A tier belongs to a family when its profile writes at least one overlay
    field for that family. A tier whose overlay is all-None changes no widget,
    yet the combo still stamps it as applied, so those tiers stay out of the
    family's list and the graph keeps only ``lab`` and ``custom``. That is what
    keeps a Klein graph from offering the FLUX 3 and Qwen-Image ladders and a
    Wan graph from offering a weight swap it has no loader for.

    Args:
        family: Occupancy id, QUALITY_FAMILY_KLEIN3, or QUALITY_FAMILY_QWEN.

    Returns:
        Tier ids in QUALITY_CHOICES order; empty for a no-op family.
    """
    honored: list[str] = []
    for choice in NAMED_QUALITY_CHOICES:
        profile = tier_profile(family, choice)
        if any(getattr(profile, field) is not None for field in OVERLAY_FIELDS):
            honored.append(choice)
    return tuple(honored)


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


def match_tier(
    observed: JsonMap,
    *,
    family: str,
    authored: JsonMap | None = None,
    available_unets: Sequence[str] | None = None,
    available_clips: Sequence[str] | None = None,
    available_vaes: Sequence[str] | None = None,
    authored_steps: int = 0,
) -> str:
    """Return the quality id that matches the widgets a graph now holds.

    Named tiers win over ``lab`` because the tier names what Queue would send.
    Only the fields the family owns are compared, so an edit outside the
    overlay keeps the level. Unowned fields stay whatever the user left them.

    Args:
        observed: Current value per overlay field name.
        family: Occupancy id, QUALITY_FAMILY_KLEIN3, or QUALITY_FAMILY_QWEN.
        authored: Load-time values per overlay field name, when known.
        available_unets: UNET combo options.
        available_clips: CLIP combo options.
        available_vaes: VAE combo options.
        authored_steps: KSampler steps for the Klein high floor.

    Returns:
        A named quality, QUALITY_LAB, or QUALITY_CUSTOM.
    """
    owned = family_owned_fields(family)
    if not owned:
        return QUALITY_LAB
    for choice in NAMED_QUALITY_CHOICES:
        profile = _profile(
            family,
            choice,
            available_unets=available_unets,
            available_clips=available_clips,
            available_vaes=available_vaes,
            authored_steps=authored_steps,
        )
        if all(
            _same_value(observed.get(field), getattr(profile, field))
            for field in owned
        ):
            return choice
    if authored is not None and all(
        _same_value(observed.get(field), authored.get(field)) for field in owned
    ):
        return QUALITY_LAB
    return QUALITY_CUSTOM


def tier_label(family: str, quality: str) -> str:
    """Describe one tier the way the combo should, weights before steps.

    Klein tiers swap weights rather than climbing a step ladder, so the label
    names the transformer and the sampler settings it pins.

    Args:
        family: Occupancy id, QUALITY_FAMILY_KLEIN3, or QUALITY_FAMILY_QWEN.
        quality: Combo value.

    Returns:
        Caption text, empty for a tier that changes nothing.
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
    """True when one family can actually carry one tier.

    ``custom`` and ``lab`` always pass: one leaves the graph alone and the other
    restores what it shipped with. Any other tier must have at least one field
    the family writes, or applying it changes nothing and the operator would be
    told a level was reached that the graph never had.

    Args:
        family: Occupancy id, such as ``wan``.
        quality: Raw tier as typed, any case.

    Returns:
        True when applying the tier writes something, or it is a freeze tier.
    """
    choice = normalize_quality(quality)
    if choice in _FREEZE_QUALITIES:
        return True
    return choice in tiers_for_family(family)


def export_table() -> dict[str, Json]:
    """Return the full tier table in JSON-safe form.

    Args:
        None.

    Returns:
        Mapping with the tier table, owned fields, per-family tier lists,
        labels, and tier order.
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
        "named": list(NAMED_QUALITY_CHOICES),
        "families": list(QUALITY_FAMILIES),
        "fields": list(OVERLAY_FIELDS),
        "table": table,
        "owned": owned,
        "labels": labels,
        "tiers": tiers,
        "custom": QUALITY_CUSTOM,
        "lab": QUALITY_LAB,
    }
    return payload
