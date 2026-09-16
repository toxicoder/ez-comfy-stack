"""Family-specific Quality overlays (Lab / Draft / High).

Python is the source of truth. The frontend JS mirrors these constants.
Overlays never change width, height, frames, length, CLIP, or VAE.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

QUALITY_LAB = "lab"
QUALITY_DRAFT = "draft"
QUALITY_HIGH = "high"
QUALITY_CHOICES: tuple[str, ...] = (QUALITY_LAB, QUALITY_DRAFT, QUALITY_HIGH)

KLEIN_DISTILLED = "flux-2-klein-4b-fp8.safetensors"
KLEIN_NVFP4 = "flux-2-klein-4b-nvfp4.safetensors"
KLEIN_BASE = "flux-2-klein-base-4b-fp8.safetensors"

KLEIN_DRAFT_STEPS = 4
KLEIN_DRAFT_CFG = 1.0
KLEIN_HIGH_DISTILLED_STEPS = 8
KLEIN_HIGH_DISTILLED_CFG = 1.0
KLEIN_HIGH_BASE_STEPS = 24
KLEIN_HIGH_BASE_CFG = 3.5

WAN_DRAFT_STEPS = 12
WAN_HIGH_STEPS = 28
LTX_DRAFT_STEPS = 12
LTX_HIGH_STEPS = 28
AUDIO_DRAFT_STEPS = 4
AUDIO_HIGH_STEPS = 16
TRELLIS_DRAFT_STEPS = 8
TRELLIS_HIGH_STEPS = 20

KSAMPLER_STEPS_INDEX = 2
KSAMPLER_CFG_INDEX = 3
UNET_NAME_INDEX = 0

BANNED_UNET_NEEDLES: tuple[str, ...] = (
    "FLUX.2-dev",
    "flux-2-dev",
    "flux2-dev",
    "klein-9b",
    "flux-2-klein-9b",
    "MiniMax",
    "Seedance",
    "Kling",
    "z_image_turbo",
)

_NOOP_OCCUPANCY = frozenset({"llm", "none"})
_LTX_OCCUPANCY = frozenset({"ltx", "film"})


@dataclass(frozen=True)
class QualityOverlay:
    """Optional widget writes. None means leave the authored value."""

    steps: int | None = None
    cfg: float | None = None
    unet_name: str | None = None


def normalize_quality(value: object) -> str:
    """Return a legal quality id, defaulting to lab.

    Args:
        value: Combo widget value.

    Returns:
        lab, draft, or high.
    """
    raw = str(value or QUALITY_LAB).strip().lower()
    if raw in QUALITY_CHOICES:
        return raw
    return QUALITY_LAB


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


def is_wan_14b_unet(name: str) -> bool:
    """True for Wan 14B / A14B filenames (not the 5B lab default).

    Args:
        name: UNET filename.

    Returns:
        True when the name looks like a 14B Wan transformer.
    """
    blob = name.lower()
    return "14b" in blob


def _available(available_unets: Sequence[str] | None) -> set[str]:
    if available_unets is None:
        return set()
    return {str(item) for item in available_unets if str(item).strip()}


def _pick_unet(name: str, available: set[str]) -> str | None:
    if is_banned_unet(name):
        return None
    if available and name not in available:
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
) -> QualityOverlay:
    """Return the overlay for one sampler + UNET pair.

    Args:
        occupancy: extra.lab_app_mode.occupancy (klein, wan, ltx, …).
        quality: lab, draft, or high.
        authored_steps: Current KSampler steps.
        authored_cfg: Current KSampler CFG.
        unet_name: Current UNETLoader filename (may be empty).
        available_unets: Combo options. Empty/None refuses UNET swaps.

    Returns:
        Overlay with None for knobs that must stay authored.
    """
    del authored_cfg
    choice = normalize_quality(quality)
    occ = (occupancy or "").strip().lower()
    if choice == QUALITY_LAB or occ in _NOOP_OCCUPANCY:
        return QualityOverlay()
    if is_wan_14b_unet(unet_name):
        return QualityOverlay()
    available = _available(available_unets)

    if occ == "klein" or is_klein_4b_unet(unet_name):
        return _klein_overlay(choice, authored_steps, unet_name, available)
    if occ == "wan":
        steps = WAN_DRAFT_STEPS if choice == QUALITY_DRAFT else WAN_HIGH_STEPS
        return QualityOverlay(steps=steps)
    if occ in _LTX_OCCUPANCY:
        steps = LTX_DRAFT_STEPS if choice == QUALITY_DRAFT else LTX_HIGH_STEPS
        return QualityOverlay(steps=steps)
    if occ == "audio":
        steps = AUDIO_DRAFT_STEPS if choice == QUALITY_DRAFT else AUDIO_HIGH_STEPS
        return QualityOverlay(steps=steps)
    if occ == "trellis":
        steps = TRELLIS_DRAFT_STEPS if choice == QUALITY_DRAFT else TRELLIS_HIGH_STEPS
        return QualityOverlay(steps=steps)
    return QualityOverlay()


def _klein_overlay(
    choice: str,
    authored_steps: int,
    unet_name: str,
    available: set[str],
) -> QualityOverlay:
    if choice == QUALITY_DRAFT:
        unet: str | None = None
        if is_klein_4b_unet(unet_name) and unet_name == KLEIN_BASE:
            unet = _pick_unet(KLEIN_DISTILLED, available)
        return QualityOverlay(
            steps=KLEIN_DRAFT_STEPS,
            cfg=KLEIN_DRAFT_CFG,
            unet_name=unet,
        )
    base = _pick_unet(KLEIN_BASE, available)
    if base is not None and is_klein_4b_unet(unet_name):
        return QualityOverlay(
            steps=KLEIN_HIGH_BASE_STEPS,
            cfg=KLEIN_HIGH_BASE_CFG,
            unet_name=base,
        )
    steps = authored_steps
    if steps < KLEIN_HIGH_DISTILLED_STEPS:
        steps = KLEIN_HIGH_DISTILLED_STEPS
    return QualityOverlay(
        steps=steps,
        cfg=KLEIN_HIGH_DISTILLED_CFG,
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


def _first_unet_name(graph: Mapping[str, Any]) -> str:
    for node in graph.get("nodes") or []:
        if node.get("type") != "UNETLoader":
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
) -> dict[str, Any]:
    """Mutate KSampler / UNETLoader widgets_values in place.

    Does not touch latent size, frames, CLIP, or VAE. Lab is a no-op.

    Args:
        graph: Serialized Comfy graph (mutated).
        quality: lab, draft, or high.
        available_unets: Combo options for UNET swaps.

    Returns:
        The same graph dict.
    """
    choice = normalize_quality(quality)
    if choice == QUALITY_LAB or graph_has_wan14(graph):
        return graph
    occupancy = infer_occupancy(graph)
    unet_name = _first_unet_name(graph)
    overlay = resolve_overlay(
        occupancy=occupancy,
        quality=choice,
        authored_steps=0,
        authored_cfg=1.0,
        unet_name=unet_name,
        available_unets=available_unets,
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
            )
            if local.steps is not None and len(values) > KSAMPLER_STEPS_INDEX:
                values[KSAMPLER_STEPS_INDEX] = local.steps
            if local.cfg is not None and len(values) > KSAMPLER_CFG_INDEX:
                values[KSAMPLER_CFG_INDEX] = local.cfg
        elif ntype == "UNETLoader":
            if overlay.unet_name is None or len(values) <= UNET_NAME_INDEX:
                continue
            current = str(values[UNET_NAME_INDEX])
            if not is_klein_4b_unet(current):
                continue
            if is_banned_unet(overlay.unet_name):
                continue
            values[UNET_NAME_INDEX] = overlay.unet_name
    return graph
