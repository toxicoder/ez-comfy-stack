"""Family-specific Quality overlays (custom / draft / lab / standard / high /
Free Commercial Use / ultra / max).

Python is the source of truth. The frontend JS mirrors these constants.
Overlays never change width, height, frames, or length. Named qualities may
swap UNET, CLIP, and VAE when the files are present. ``custom`` is a freeze.
``Free Commercial Use (<$10M)`` is Apache Klein 4B + LTX-2.5 only — never
Klein 9B or FLUX.2-dev. Wan / audio / trellis are no-ops for that choice.
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
QUALITY_CHOICES: tuple[str, ...] = (
    QUALITY_CUSTOM,
    QUALITY_DRAFT,
    QUALITY_LAB,
    QUALITY_STANDARD,
    QUALITY_HIGH,
    QUALITY_FREE_COMMERCIAL,
    QUALITY_ULTRA,
    QUALITY_MAX,
)
# casefold(widget value) → canonical QUALITY_CHOICES entry (incl. alias).
_QUALITY_NORMALIZE: dict[str, str] = {
    choice.casefold(): choice for choice in QUALITY_CHOICES
}
_QUALITY_NORMALIZE[QUALITY_FREE_COMMERCIAL_ALIAS] = QUALITY_FREE_COMMERCIAL

# Klein filenames, family step/CFG overlays, widget indexes.
KLEIN_DISTILLED = "flux-2-klein-4b-fp8.safetensors"
KLEIN_NVFP4 = "flux-2-klein-4b-nvfp4.safetensors"
KLEIN_BASE = "flux-2-klein-base-4b-fp8.safetensors"
KLEIN_9B = "flux-2-klein-9b-fp8.safetensors"
KLEIN_9B_BASE = "flux-2-klein-base-9b-fp8.safetensors"
KLEIN_9B_NVFP4 = "flux-2-klein-9b-nvfp4.safetensors"
FLUX2_DEV = "flux2_dev_fp8mixed.safetensors"

CLIP_4B = "qwen_3_4b.safetensors"
CLIP_8B = "qwen_3_8b_fp8mixed.safetensors"
CLIP_MISTRAL = "mistral_3_small_flux2_bf16.safetensors"
CLIP_TYPE_FLUX2 = "flux2"

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
        occupancy: extra.lab_app_mode.occupancy (klein, wan, ltx, …).
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
            ):
                continue
            values[UNET_NAME_INDEX] = overlay.unet_name
        elif ntype == "CLIPLoader":
            if overlay.clip_name is None or len(values) <= CLIP_NAME_INDEX:
                continue
            current = str(values[CLIP_NAME_INDEX])
            if current and not is_flux2_clip(current):
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
