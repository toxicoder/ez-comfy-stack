"""Family-specific Quality overlays (custom / draft / lab / standard / high /
Free Commercial Use / ultra / max / flux3-fast / flux3-quality / flux3-nvfp4).

This module is the only definition of what a tier asks for. The frontend reads
a table generated from it (``export_table`` -> tests/python/_build_quality_js.py
-> custom_nodes/ez_quality/js/ez_quality_presets.js) and derives the combo from
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
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

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

CLIP_4B = "qwen_3_4b.safetensors"
CLIP_8B = "qwen_3_8b_fp8mixed.safetensors"
CLIP_MISTRAL = "mistral_3_small_flux2_bf16.safetensors"
CLIP_TYPE_FLUX2 = "flux2"
# KLEIN3 text encoder (Qwen3-VL) plus the optional prompt upsampler.
KLEIN3_TE = "qwen3vl_4b_int8_convrot.safetensors"
KLEIN3_UPSAMPLER = "qwen3.5_9b_flux3_prompt_upsampler_int8_convrot.safetensors"

VAE_FULL = "flux2-vae.safetensors"
VAE_SMALL = "full_encoder_small_decoder.safetensors"

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

KSAMPLER_STEPS_INDEX = 2
KSAMPLER_CFG_INDEX = 3
UNET_NAME_INDEX = 0
CLIP_NAME_INDEX = 0
VAE_NAME_INDEX = 0

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


def normalize_quality(value: object) -> str:
    """Return a legal quality id, defaulting to lab.

    Args:
        value: Combo widget value.

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


def _wan_steps(choice: str) -> int:
    """Wan 5B step overlay.

    Args:
        choice: Named quality (not custom/lab).

    Returns:
        Step count.
    """
    if choice == QUALITY_DRAFT:
        return WAN_DRAFT_STEPS
    if choice == QUALITY_STANDARD:
        return WAN_STANDARD_STEPS
    if choice == QUALITY_MAX:
        return WAN_MAX_STEPS
    return WAN_HIGH_STEPS


def _ltx_steps(choice: str) -> int:
    """LTX / film step overlay.

    Args:
        choice: Named quality.

    Returns:
        Step count.
    """
    if choice == QUALITY_DRAFT:
        return LTX_DRAFT_STEPS
    if choice == QUALITY_STANDARD:
        return LTX_STANDARD_STEPS
    if choice == QUALITY_MAX:
        return LTX_MAX_STEPS
    return LTX_HIGH_STEPS


def _audio_steps(choice: str) -> int:
    """ACE / audio step overlay.

    Args:
        choice: Named quality.

    Returns:
        Step count.
    """
    if choice == QUALITY_DRAFT:
        return AUDIO_DRAFT_STEPS
    if choice == QUALITY_STANDARD:
        return AUDIO_STANDARD_STEPS
    if choice == QUALITY_MAX:
        return AUDIO_MAX_STEPS
    return AUDIO_HIGH_STEPS


def _trellis_steps(choice: str) -> int:
    """TRELLIS step overlay.

    Args:
        choice: Named quality.

    Returns:
        Step count.
    """
    if choice == QUALITY_DRAFT:
        return TRELLIS_DRAFT_STEPS
    if choice == QUALITY_STANDARD:
        return TRELLIS_STANDARD_STEPS
    if choice == QUALITY_MAX:
        return TRELLIS_MAX_STEPS
    return TRELLIS_HIGH_STEPS


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

    Wan, audio, trellis, and inspire are no-ops. Python never writes size.

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


def infer_occupancy(graph: Mapping[str, Any]) -> str:
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
    types = {str(node.get("type") or "") for node in graph.get("nodes") or []}
    if "EZFilmConcat" in types:
        return "film"
    if "MeshToFile3D" in types:
        return "trellis"
    if "SaveAudio" in types or "SaveAudioMP3" in types:
        return "audio"
    if "VHS_VideoCombine" in types or "SaveVideo" in types:
        for node in graph.get("nodes") or []:
            if node.get("type") != "UNETLoader":
                continue
            values = node.get("widgets_values") or []
            name = str(values[0]) if values else ""
            if "ltx" in name.lower():
                return "ltx"
            if "wan" in name.lower():
                return "wan"
        return "wan"
    if "SaveImage" in types:
        return "klein"
    return ""


def _first_loader_name(graph: Mapping[str, Any], node_type: str) -> str:
    """First loader filename of ``node_type``.

    Args:
        graph: Serialized Comfy graph.
        node_type: UNETLoader, CLIPLoader, or VAELoader.

    Returns:
        Filename, or empty string when none is present.
    """
    for node in graph.get("nodes") or []:
        if node.get("type") != node_type:
            continue
        values = node.get("widgets_values") or []
        if values:
            return str(values[0])
    return ""


def graph_has_wan14(graph: Mapping[str, Any]) -> bool:
    """True when any UNETLoader is a Wan 14B file.

    Args:
        graph: Serialized Comfy graph.

    Returns:
        True when a 14B UNET is present.
    """
    for node in graph.get("nodes") or []:
        if node.get("type") != "UNETLoader":
            continue
        values = node.get("widgets_values") or []
        if values and is_wan_14b_unet(str(values[0])):
            return True
    return False


def apply_to_graph(
    graph: dict[str, Any],
    quality: str,
    *,
    available_unets: Sequence[str] | None = None,
    available_clips: Sequence[str] | None = None,
    available_vaes: Sequence[str] | None = None,
) -> dict[str, Any]:
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
    for node in graph.get("nodes") or []:
        ntype = node.get("type")
        values = node.get("widgets_values")
        if not isinstance(values, list):
            continue
        if ntype == "KSampler":
            authored_steps = (
                int(values[KSAMPLER_STEPS_INDEX])
                if len(values) > KSAMPLER_STEPS_INDEX
                else 0
            )
            authored_cfg = (
                float(values[KSAMPLER_CFG_INDEX])
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
            ):
                continue
            values[UNET_NAME_INDEX] = overlay.unet_name
        elif ntype == "CLIPLoader":
            if overlay.clip_name is None or len(values) <= CLIP_NAME_INDEX:
                continue
            current = str(values[CLIP_NAME_INDEX])
            if current and not (is_flux2_clip(current) or is_klein3_clip(current)):
                continue
            values[CLIP_NAME_INDEX] = overlay.clip_name
            if overlay.clip_type is not None and len(values) > 1:
                values[1] = overlay.clip_type
        elif ntype == "VAELoader":
            if overlay.vae_name is None or len(values) <= VAE_NAME_INDEX:
                continue
            current = str(values[VAE_NAME_INDEX])
            if current and not is_flux2_vae(current):
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

QUALITY_FAMILIES: tuple[str, ...] = (
    "klein",
    QUALITY_FAMILY_KLEIN3,
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
        family: Occupancy id, or QUALITY_FAMILY_KLEIN3.
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
        occupancy="klein" if family == QUALITY_FAMILY_KLEIN3 else family,
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
        family: Occupancy id, or QUALITY_FAMILY_KLEIN3.
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
        family: Occupancy id, or QUALITY_FAMILY_KLEIN3.

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


def _same_value(left: object, right: object) -> bool:
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
    observed: Mapping[str, object],
    *,
    family: str,
    authored: Mapping[str, object] | None = None,
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
        family: Occupancy id, or QUALITY_FAMILY_KLEIN3.
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
        family: Occupancy id, or QUALITY_FAMILY_KLEIN3.
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


def export_table() -> dict[str, Any]:
    """Return the full tier table in JSON-safe form.

    Args:
        None.

    Returns:
        Mapping with the tier table, owned fields, labels, and tier order.
    """
    table: dict[str, dict[str, dict[str, Any]]] = {}
    owned: dict[str, list[str]] = {}
    labels: dict[str, dict[str, str]] = {}
    for family in QUALITY_FAMILIES:
        table[family] = {}
        labels[family] = {}
        for choice in NAMED_QUALITY_CHOICES:
            profile = tier_profile(family, choice)
            table[family][choice] = {
                field: getattr(profile, field) for field in OVERLAY_FIELDS
            }
            labels[family][choice] = tier_label(family, choice)
        owned[family] = list(family_owned_fields(family))
    return {
        "choices": list(QUALITY_CHOICES),
        "named": list(NAMED_QUALITY_CHOICES),
        "families": list(QUALITY_FAMILIES),
        "fields": list(OVERLAY_FIELDS),
        "table": table,
        "owned": owned,
        "labels": labels,
        "custom": QUALITY_CUSTOM,
        "lab": QUALITY_LAB,
    }
