"""Resolve required model files for a lab graph + Quality combo.

Hermetic: stdlib only. Disk roots are injectable. Does not download.
Operator commands are host paths from the repo root (never container paths).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from .presets import (
    CLIP_4B,
    CLIP_8B,
    CLIP_MISTRAL,
    FLUX2_DEV,
    KLEIN_9B,
    KLEIN_9B_BASE,
    KLEIN_9B_NVFP4,
    KLEIN_DISTILLED,
    QUALITY_FREE_COMMERCIAL,
    QUALITY_LAB,
    QUALITY_MAX,
    QUALITY_ULTRA,
    VAE_FULL,
    VAE_SMALL,
    infer_occupancy,
    is_flux2_dev_unet,
    is_klein_9b_unet,
    normalize_quality,
)

# Host operator commands (repo root). manage.sh has no download-image/wan/ltx.
CMD_DOWNLOAD_MODELS = "./scripts/manage.sh download-models"
CMD_IMAGE_9B = "./scripts/utilities/download-image.sh run --tier 9b"
CMD_IMAGE_9B_BASE = "./scripts/utilities/download-image.sh run --tier 9b-base"
CMD_IMAGE_FLUX2_DEV = "./scripts/utilities/download-image.sh run --tier flux2-dev"
CMD_WAN_FUN = "./scripts/utilities/download-wan.sh run --tier fun-inp"
CMD_WAN_VACE = "./scripts/utilities/download-wan.sh run --tier vace"
CMD_WAN_S2V = "./scripts/utilities/download-wan.sh run --tier s2v"
CMD_LTX_ICLORA = "./scripts/utilities/download-ltx.sh run --tier iclora"
CMD_LLM_DESCRIBE = "./scripts/utilities/download-llm.sh run --tier describe"
CMD_LLM_35B = "./scripts/manage.sh download-llm --tier qwen36-35b-a3b"
CMD_MUSIC = "./scripts/manage.sh download-music --tier turbo"
CMD_PODCAST = "./scripts/manage.sh download-podcast --tier analog"
CMD_DUB = "./scripts/manage.sh download-dub --tier all"
CMD_TRELLIS = "./scripts/manage.sh download-3d --tier trellis2"
CMD_RESTORE = "./scripts/manage.sh download-restore --tier seedvr2-3b"
CMD_LONGCAT = "./scripts/manage.sh download-longcat"
CMD_DREAMX = "./scripts/manage.sh download-dreamx"
CMD_RESTART = "Then restart Comfy so models/* re-link."

# Comfy models/* layout under MODELS_DIR/comfy.
SUB_UNET = "diffusion_models"
SUB_CLIP = "text_encoders"
SUB_VAE = "vae"
SUB_LORA = "loras"
SUB_LLM = "llm"
SUB_ONNX = "onnx"
SUB_TTS = "tts"
SUB_CKPT = "checkpoints"

WAN_5B = "wan2.2_ti2v_5B_fp16.safetensors"
WAN_VAE = "wan2.2_vae.safetensors"
WAN_CLIP = "umt5_xxl_fp8_e4m3fn_scaled.safetensors"
LTX_UNET = "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors"
LTX_CLIP = "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors"
LTX_VIDEO_VAE = "ltx-2.5-video-vae-bf16.safetensors"
LTX_AUDIO_VAE = "ltx-2.5-audio-vae-bf16.safetensors"
LTX_ICLORA = "ltx-2.3-22b-ic-lora-union-control-ref0.5.safetensors"
LLM_GGUF = "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
LLM_DESCRIBE = "Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf"
LLM_DESCRIBE_PROJ = "mmproj-Qwen2.5-VL-3B-Instruct-Q8_0.gguf"
LLM_35B = "Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf"
ACE_TURBO = "ace_step_1.5_turbo_aio.safetensors"
TRELLIS_UNET = "trellis_2_int8_convrot.safetensors"
TRELLIS_SHAPE = "trellis_2_shape_vae_bf16.safetensors"
TRELLIS_TEXTURE = "trellis_2_texture_vae_bf16.safetensors"
TRELLIS_DINO = "dino_v3_vit_l.safetensors"
KOKORO_ONNX = "kokoro-v1.0.onnx"
DUB_T3 = "t3_mtl23ls_v3.safetensors"
DREAMX_WEIGHTS = "cross_attn_weights.safetensors"
SEEDVR2 = "seedvr2_ema_3b.pth"

STATUS_DEFAULT = "Click Check models. Queue does not run this node."
"""Canvas status until the operator clicks Check models."""

ENHANCE_TYPES = frozenset(
    {
        "EZKleinPromptEnhance",
        "EZWanPromptEnhance",
        "EZLTXPromptEnhance",
        "EZZimagePromptEnhance",
        "EZLongCatPromptEnhance",
        "EZDreamXPromptEnhance",
        "EZAceStepPromptEnhance",
        "EZNegativePromptEnhance",
    }
)
DUB_TYPES = frozenset({"EZDubIngest", "EZDubScript", "EZDubRender"})
PODCAST_TTS_TYPES = frozenset({"EZKokoroTTS"})
RESEARCH_TYPES = frozenset({"EZCreativeResearch", "EZAppForge"})
_LTX_OCC = frozenset({"ltx", "film"})
_DEFAULT_FILES = frozenset(
    {
        KLEIN_DISTILLED,
        CLIP_4B,
        VAE_FULL,
        WAN_5B,
        WAN_VAE,
        WAN_CLIP,
        LTX_UNET,
        LTX_CLIP,
        LTX_VIDEO_VAE,
        LTX_AUDIO_VAE,
        LLM_GGUF,
    }
)
_FOLDER_KEYS = (
    "unet",
    "diffusion_models",
    "clip",
    "text_encoders",
    "vae",
    "loras",
    "checkpoints",
    "llm",
)


@dataclass(frozen=True)
class FileSpec:
    """One file under ``comfy/<subdir>/<name>``."""

    subdir: str
    name: str
    needle: str = ""
    """When set, any basename in ``subdir`` containing this needle counts."""


@dataclass(frozen=True)
class Need:
    """One required pack (all files, or any file when ``satisfy`` is any)."""

    pack: str
    cmd: str
    files: tuple[FileSpec, ...]
    satisfy: str = "all"


@dataclass(frozen=True)
class CheckHints:
    """Compact graph snapshot from JS or a serialized lab graph."""

    lab_rel: str = ""
    occupancy: str = ""
    quality: str = QUALITY_LAB
    types: tuple[str, ...] = ()
    unets: tuple[str, ...] = ()
    clips: tuple[str, ...] = ()
    vaes: tuple[str, ...] = ()
    loras: tuple[str, ...] = ()
    checkpoints: tuple[str, ...] = ()
    enhance_on: bool = False
    describe_on: bool = False
    flags: tuple[str, ...] = ()


@dataclass
class FileRow:
    """One scanned file (or needle group)."""

    name: str
    pack: str
    cmd: str
    state: str
    subdir: str = ""


@dataclass
class CheckResult:
    """Scan outcome for one Check models click."""

    ok: bool
    lab_rel: str
    occupancy: str
    quality: str
    present: list[FileRow] = field(default_factory=list)
    missing: list[FileRow] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)


def models_roots() -> list[Path]:
    """Return MODELS_ROOT / MODELS_DIR then container fallbacks.

    Returns:
        Unique model-root candidates (may not exist yet).
    """
    found: list[Path] = []
    seen: set[str] = set()
    for key in ("MODELS_ROOT", "MODELS_DIR"):
        raw = os.environ.get(key, "").strip()
        if not raw:
            continue
        path = Path(raw)
        token = str(path)
        if token in seen:
            continue
        seen.add(token)
        found.append(path)
    for fallback in (Path("/models"), Path("/mnt/models")):
        token = str(fallback)
        if token in seen:
            continue
        seen.add(token)
        found.append(fallback)
    return found


def _as_bool(value: object, *, default: bool = False) -> bool:
    """Coerce JSON / widget values to bool.

    Args:
        value: Widget or JSON value.
        default: Fallback when ``value`` is empty.

    Returns:
        Boolean.
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().casefold()
    if not text:
        return default
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default


def _as_str_tuple(value: object) -> tuple[str, ...]:
    """Normalize a JSON list or single string to unique stripped names.

    Args:
        value: List, string, or other.

    Returns:
        Unique non-empty strings.
    """
    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if not isinstance(value, (list, tuple)):
        return ()
    seen: list[str] = []
    found: set[str] = set()
    for item in value:
        text = str(item).strip()
        if not text or text in found:
            continue
        found.add(text)
        seen.append(text)
    return tuple(seen)


def _first_bool(values: Sequence[Any]) -> bool | None:
    """Return the first boolean in a widgets_values list.

    Args:
        values: Node widgets_values.

    Returns:
        First bool, or None.
    """
    for item in values:
        if isinstance(item, bool):
            return item
    return None


def _loader_name(values: object) -> str:
    """First string widget (UNET/CLIP/VAE filename).

    Args:
        values: widgets_values list or dict.

    Returns:
        Filename, or empty.
    """
    if isinstance(values, dict):
        for key in ("unet_name", "ckpt_name", "lora_name", "vae_name"):
            raw = values.get(key)
            if raw:
                return str(raw).strip()
        return ""
    if not isinstance(values, (list, tuple)) or not values:
        return ""
    first = values[0]
    if isinstance(first, (dict, list, bool)):
        return ""
    return str(first).strip()


def hints_from_args(args: Mapping[str, Any]) -> CheckHints:
    """Build hints from a POST body.

    Args:
        args: JSON object from ``/ez_quality/check``.

    Returns:
        Normalized hints.
    """
    graph = args.get("graph")
    if isinstance(graph, Mapping) and (
        not args.get("occupancy") and not args.get("types")
    ):
        return hints_from_graph(graph)
    flags = _as_str_tuple(args.get("flags") or args.get("extra_flags"))
    return CheckHints(
        lab_rel=str(args.get("lab_rel") or "").strip(),
        occupancy=str(args.get("occupancy") or "").strip().lower(),
        quality=normalize_quality(args.get("quality")),
        types=_as_str_tuple(args.get("types")),
        unets=_as_str_tuple(args.get("unets")),
        clips=_as_str_tuple(args.get("clips")),
        vaes=_as_str_tuple(args.get("vaes")),
        loras=_as_str_tuple(args.get("loras")),
        checkpoints=_as_str_tuple(args.get("checkpoints")),
        enhance_on=_as_bool(args.get("enhance_on")),
        describe_on=_as_bool(args.get("describe_on")),
        flags=flags,
    )


def hints_from_graph(graph: Mapping[str, Any]) -> CheckHints:
    """Build hints from a serialized Comfy graph.

    Args:
        graph: Lab JSON object.

    Returns:
        Normalized hints.
    """
    raw_extra = graph.get("extra")
    extra: dict[str, Any] = dict(raw_extra) if isinstance(raw_extra, dict) else {}
    safe_nodes = [n for n in graph.get("nodes") or [] if isinstance(n, Mapping)]
    occupancy = infer_occupancy({**dict(graph), "nodes": safe_nodes})
    lab_rel = str(extra.get("lab_rel") or graph.get("id") or "").strip()
    quality = QUALITY_LAB
    types: list[str] = []
    unets: list[str] = []
    clips: list[str] = []
    vaes: list[str] = []
    loras: list[str] = []
    checkpoints: list[str] = []
    enhance_on = False
    describe_on = False
    for node in safe_nodes:
        ntype = str(node.get("type") or "")
        if not ntype:
            continue
        types.append(ntype)
        values = node.get("widgets_values") or []
        name = _loader_name(values)
        if ntype == "UNETLoader" and name:
            unets.append(name)
        elif ntype == "CLIPLoader" and name:
            clips.append(name)
        elif ntype == "VAELoader" and name:
            vaes.append(name)
        elif ntype in {"LoraLoader", "LoraLoaderModelOnly"} and name:
            loras.append(name)
        elif ntype == "CheckpointLoaderSimple" and name:
            checkpoints.append(name)
        elif ntype == "EZQuality" and isinstance(values, (list, tuple)) and values:
            quality = normalize_quality(values[0])
        if ntype in ENHANCE_TYPES:
            flag = _first_bool(values if isinstance(values, (list, tuple)) else [])
            if flag is True:
                enhance_on = True
            elif flag is None:
                enhance_on = True
        if ntype == "EZImageDescribe":
            flag = _first_bool(values if isinstance(values, (list, tuple)) else [])
            if flag is True:
                describe_on = True
    flags: list[str] = []
    if extra.get("lab_iclora"):
        flags.append("iclora")
    if extra.get("lab_vace"):
        flags.append("vace")
    rel = lab_rel.casefold()
    if "iclora" in rel and "iclora" not in flags:
        flags.append("iclora")
    if "vace" in rel and "vace" not in flags:
        flags.append("vace")
    if "fun-inp" in rel or "fun_inp" in rel:
        flags.append("fun-inp")
    if "/s2v" in f"/{rel}" or rel.endswith("s2v") or "speech-to-video" in rel:
        flags.append("s2v")
    return CheckHints(
        lab_rel=lab_rel,
        occupancy=occupancy,
        quality=quality,
        types=tuple(types),
        unets=tuple(unets),
        clips=tuple(clips),
        vaes=tuple(vaes),
        loras=tuple(loras),
        checkpoints=tuple(checkpoints),
        enhance_on=enhance_on,
        describe_on=describe_on,
        flags=tuple(dict.fromkeys(flags)),
    )


def command_for_filename(name: str) -> str:
    """Return the host download command for a basename.

    Args:
        name: Model filename.

    Returns:
        Operator command string.
    """
    blob = name.lower().replace(".", "-")
    if name in _DEFAULT_FILES:
        return CMD_DOWNLOAD_MODELS
    if "iclora" in blob or "ic-lora" in blob:
        return CMD_LTX_ICLORA
    if "fun" in blob and "inp" in blob:
        return CMD_WAN_FUN
    if "vace" in blob:
        return CMD_WAN_VACE
    if "s2v" in blob:
        return CMD_WAN_S2V
    if is_klein_9b_unet(name):
        if "base" in blob:
            return CMD_IMAGE_9B_BASE
        return CMD_IMAGE_9B
    if is_flux2_dev_unet(name) or "mistral" in blob:
        return CMD_IMAGE_FLUX2_DEV
    if "qwen_3_8b" in blob or "qwen-3-8b" in blob:
        return CMD_IMAGE_9B
    if "ace_step" in blob or "ace-step" in blob:
        return CMD_MUSIC
    if "trellis" in blob or "dino_v3" in blob:
        return CMD_TRELLIS
    if "qwen2.5-vl" in blob or "qwen2-5-vl" in blob or "mmproj" in blob:
        return CMD_LLM_DESCRIBE
    if "35b" in blob and "gguf" in blob:
        return CMD_LLM_35B
    if "kokoro" in blob:
        return CMD_PODCAST
    if "chatterbox" in blob or "t3_mtl" in blob or "whisper" in blob:
        return CMD_DUB
    if "seedvr" in blob:
        return CMD_RESTORE
    if "longcat" in blob:
        return CMD_LONGCAT
    if "dreamx" in blob or "cross_attn" in blob:
        return CMD_DREAMX
    return CMD_DOWNLOAD_MODELS


def _need(pack: str, cmd: str, *files: FileSpec, satisfy: str = "all") -> Need:
    """Build a Need.

    Args:
        pack: Pack id.
        cmd: Host command.
        files: File specs.
        satisfy: ``all`` or ``any``.

    Returns:
        Need row.
    """
    return Need(pack=pack, cmd=cmd, files=files, satisfy=satisfy)


def requirements_for(hints: CheckHints) -> list[Need]:
    """Return packs this graph + Quality must have on disk.

    Args:
        hints: Compact graph snapshot.

    Returns:
        Need list (may be empty for empty ``none`` canvases).
    """
    occ = (hints.occupancy or "").strip().lower()
    quality = normalize_quality(hints.quality)
    types = set(hints.types)
    flags = {item.casefold() for item in hints.flags}
    rel = hints.lab_rel.casefold()
    needs: list[Need] = []

    if occ == "klein":
        needs.append(
            _need(
                "klein-4b",
                CMD_DOWNLOAD_MODELS,
                FileSpec(SUB_UNET, KLEIN_DISTILLED),
            )
        )
        needs.append(
            _need(
                "klein-qwen-te",
                CMD_DOWNLOAD_MODELS,
                FileSpec(SUB_CLIP, CLIP_4B),
            )
        )
        needs.append(
            _need(
                "flux2-vae",
                CMD_DOWNLOAD_MODELS,
                FileSpec(SUB_VAE, VAE_FULL),
                FileSpec(SUB_VAE, VAE_SMALL),
                satisfy="any",
            )
        )
    elif occ == "wan":
        needs.append(
            _need(
                "wan-ti2v-5b",
                CMD_DOWNLOAD_MODELS,
                FileSpec(SUB_UNET, WAN_5B),
                FileSpec(SUB_VAE, WAN_VAE),
                FileSpec(SUB_CLIP, WAN_CLIP),
            )
        )
    elif occ in _LTX_OCC:
        needs.append(
            _need(
                "ltx-2.5",
                CMD_DOWNLOAD_MODELS,
                FileSpec(SUB_UNET, LTX_UNET),
                FileSpec(SUB_CLIP, LTX_CLIP),
                FileSpec(SUB_VAE, LTX_VIDEO_VAE),
                FileSpec(SUB_VAE, LTX_AUDIO_VAE),
            )
        )
    elif occ == "audio":
        needs.append(
            _need(
                "music-turbo",
                CMD_MUSIC,
                FileSpec(SUB_CKPT, ACE_TURBO),
            )
        )
    elif occ == "trellis":
        needs.append(
            _need(
                "trellis2",
                CMD_TRELLIS,
                FileSpec(SUB_UNET, TRELLIS_UNET),
                FileSpec(SUB_VAE, TRELLIS_SHAPE),
                FileSpec(SUB_VAE, TRELLIS_TEXTURE),
                FileSpec(SUB_CLIP, TRELLIS_DINO),
            )
        )
    elif occ == "llm":
        needs.append(
            _need("llm-qwen3-4b", CMD_DOWNLOAD_MODELS, FileSpec(SUB_LLM, LLM_GGUF))
        )

    if occ == "klein" and quality == QUALITY_ULTRA:
        needs.append(
            _need(
                "klein-9b",
                CMD_IMAGE_9B,
                FileSpec(SUB_UNET, KLEIN_9B),
                FileSpec(SUB_UNET, KLEIN_9B_NVFP4),
                satisfy="any",
            )
        )
        needs.append(
            _need("klein-9b-te", CMD_IMAGE_9B, FileSpec(SUB_CLIP, CLIP_8B))
        )
    if occ == "klein" and quality == QUALITY_MAX:
        needs.append(
            _need(
                "klein-max-unet",
                CMD_IMAGE_9B_BASE,
                FileSpec(SUB_UNET, KLEIN_9B_BASE),
                FileSpec(SUB_UNET, FLUX2_DEV),
                satisfy="any",
            )
        )

    if hints.enhance_on or (types & RESEARCH_TYPES):
        needs.append(
            _need("llm-qwen3-4b", CMD_DOWNLOAD_MODELS, FileSpec(SUB_LLM, LLM_GGUF))
        )
    if hints.describe_on:
        needs.append(
            _need(
                "llm-describe",
                CMD_LLM_DESCRIBE,
                FileSpec(SUB_LLM, LLM_DESCRIBE),
                FileSpec(SUB_LLM, LLM_DESCRIBE_PROJ),
            )
        )
    if "iclora" in flags or "iclora" in rel:
        needs.append(
            _need("ltx-iclora", CMD_LTX_ICLORA, FileSpec(SUB_LORA, LTX_ICLORA))
        )
    if "vace" in flags or "vace" in rel:
        needs.append(
            _need(
                "wan-vace",
                CMD_WAN_VACE,
                FileSpec(SUB_UNET, "", needle="vace"),
            )
        )
    if "fun-inp" in flags or "fun-inp" in rel or "fun_inp" in rel:
        needs.append(
            _need(
                "wan-fun-inp",
                CMD_WAN_FUN,
                FileSpec(SUB_UNET, "", needle="fun"),
            )
        )
    if "s2v" in flags:
        needs.append(
            _need(
                "wan-s2v",
                CMD_WAN_S2V,
                FileSpec(SUB_UNET, "", needle="s2v"),
            )
        )
    if types & DUB_TYPES:
        needs.append(_need("dub-clone", CMD_DUB, FileSpec(SUB_TTS, DUB_T3)))
    if types & PODCAST_TTS_TYPES:
        needs.append(_need("podcast-analog", CMD_PODCAST, FileSpec(SUB_ONNX, KOKORO_ONNX)))
    if "EZLongCatPromptEnhance" in types:
        needs.append(
            _need(
                "longcat-video",
                CMD_LONGCAT,
                FileSpec(SUB_UNET, "", needle="longcat"),
            )
        )
    if "EZDreamXPromptEnhance" in types:
        needs.append(
            _need(
                "dreamx-creator",
                CMD_DREAMX,
                FileSpec(SUB_UNET, DREAMX_WEIGHTS),
            )
        )
    if any("seedvr" in name.lower() for name in hints.unets + hints.checkpoints):
        needs.append(_need("seedvr2-3b", CMD_RESTORE, FileSpec(SUB_UNET, SEEDVR2)))

    for name in hints.unets:
        needs.append(
            _need(
                "authored-unet",
                command_for_filename(name),
                FileSpec(SUB_UNET, name),
            )
        )
    for name in hints.clips:
        needs.append(
            _need(
                "authored-clip",
                command_for_filename(name),
                FileSpec(SUB_CLIP, name),
            )
        )
    for name in hints.vaes:
        needs.append(
            _need(
                "authored-vae",
                command_for_filename(name),
                FileSpec(SUB_VAE, name),
            )
        )
    for name in hints.loras:
        needs.append(
            _need(
                "authored-lora",
                command_for_filename(name),
                FileSpec(SUB_LORA, name),
            )
        )
    for name in hints.checkpoints:
        needs.append(
            _need(
                "authored-ckpt",
                command_for_filename(name),
                FileSpec(SUB_CKPT, name),
            )
        )
    if quality == QUALITY_FREE_COMMERCIAL and occ == "klein":
        # Free Commercial Use never needs 9B / FLUX.2-dev even if ultra leftovers.
        needs = [
            need
            for need in needs
            if need.pack
            not in {"klein-9b", "klein-9b-te", "klein-max-unet", "flux2-dev"}
        ]
    return needs


def _folder_paths_has(name: str) -> bool:
    """True when Comfy ``folder_paths`` lists ``name``.

    Args:
        name: Basename.

    Returns:
        True when the combo includes the file.
    """
    if not name:
        return False
    try:
        import folder_paths  # type: ignore[import-not-found]
    except Exception:  # noqa: BLE001 — optional in pytest
        return False
    getter = getattr(folder_paths, "get_filename_list", None)
    if getter is None:
        return False
    for key in _FOLDER_KEYS:
        try:
            names = getter(key)
        except Exception:  # noqa: BLE001 — unknown folder key
            continue
        if not names:
            continue
        if name in names:
            return True
    return False


def _iter_basenames(root: Path, subdir: str) -> list[str]:
    """List files in ``root/comfy/subdir``.

    Args:
        root: Models root.
        subdir: Layout folder.

    Returns:
        Basenames (may be empty).
    """
    path = root / "comfy" / subdir
    if not path.is_dir():
        return []
    names: list[str] = []
    try:
        for child in path.iterdir():
            if child.name.startswith("."):
                continue
            names.append(child.name)
    except OSError:
        return []
    return names


def inspect_file(spec: FileSpec, roots: Sequence[Path]) -> str:
    """Return present / missing / broken / absolute for one spec.

    Args:
        spec: File or needle.
        roots: Models roots.

    Returns:
        State token.
    """
    reasons: list[str] = []
    needle = (spec.needle or "").casefold()
    for root in roots:
        if needle:
            for name in _iter_basenames(root, spec.subdir):
                if needle in name.casefold():
                    return "present"
            continue
        path = root / "comfy" / spec.subdir / spec.name
        try:
            if path.is_symlink():
                target = os.readlink(path)
                if os.path.isabs(target):
                    reasons.append("absolute")
                    continue
                if not path.exists():
                    reasons.append("broken")
                    continue
            if path.is_file() and path.stat().st_size > 0:
                return "present"
        except OSError:
            reasons.append("missing")
            continue
    if spec.name and _folder_paths_has(spec.name):
        return "present"
    if "broken" in reasons:
        return "broken"
    if "absolute" in reasons:
        return "absolute"
    return "missing"


def _collapse_commands(cmds: Sequence[str]) -> list[str]:
    """Unique commands, download-models first.

    Args:
        cmds: Command strings.

    Returns:
        Ordered unique commands.
    """
    seen: set[str] = set()
    out: list[str] = []
    preferred = [cmd for cmd in cmds if cmd == CMD_DOWNLOAD_MODELS]
    rest = [cmd for cmd in cmds if cmd != CMD_DOWNLOAD_MODELS]
    for cmd in preferred + rest:
        if not cmd or cmd in seen:
            continue
        seen.add(cmd)
        out.append(cmd)
    return out


def scan(hints: CheckHints, roots: Sequence[Path]) -> CheckResult:
    """Check disk for each requirement.

    Args:
        hints: Graph snapshot.
        roots: Models roots.

    Returns:
        Present/missing rows and collapsed commands.
    """
    quality = normalize_quality(hints.quality)
    present: list[FileRow] = []
    missing: list[FileRow] = []
    seen_ok: set[tuple[str, str]] = set()
    for need in requirements_for(hints):
        states = [(spec, inspect_file(spec, roots)) for spec in need.files]
        if need.satisfy == "any":
            ok = any(state == "present" for _spec, state in states)
            if ok:
                for spec, state in states:
                    if state != "present":
                        continue
                    key = (spec.subdir, spec.name or spec.needle)
                    seen_ok.add(key)
                    present.append(
                        FileRow(
                            name=spec.name or spec.needle,
                            pack=need.pack,
                            cmd=need.cmd,
                            state=state,
                            subdir=spec.subdir,
                        )
                    )
                continue
            label = " or ".join(
                spec.name or f"*{spec.needle}*" for spec in need.files
            )
            missing.append(
                FileRow(
                    name=label,
                    pack=need.pack,
                    cmd=need.cmd,
                    state="missing",
                    subdir=need.files[0].subdir if need.files else "",
                )
            )
            continue
        for spec, state in states:
            key = (spec.subdir, spec.name or spec.needle)
            row = FileRow(
                name=spec.name or spec.needle,
                pack=need.pack,
                cmd=need.cmd,
                state=state,
                subdir=spec.subdir,
            )
            if state == "present":
                if key in seen_ok:
                    continue
                seen_ok.add(key)
                present.append(row)
                continue
            if any(
                item.subdir == spec.subdir
                and item.name == row.name
                and item.cmd == row.cmd
                for item in missing
            ):
                continue
            missing.append(row)
    if quality == QUALITY_MAX and hints.occupancy == "klein":
        _fix_max_clip(hints, roots, present, missing)
    commands = _collapse_commands([row.cmd for row in missing])
    return CheckResult(
        ok=not missing,
        lab_rel=hints.lab_rel,
        occupancy=hints.occupancy,
        quality=quality,
        present=present,
        missing=missing,
        commands=commands,
    )


def _fix_max_clip(
    hints: CheckHints,
    roots: Sequence[Path],
    present: list[FileRow],
    missing: list[FileRow],
) -> None:
    """Require 8B TE when 9B base is on disk, else Mistral when FLUX.2-dev is.

    Args:
        hints: Graph snapshot (unused occupancy already klein).
        roots: Models roots.
        present: Present rows (mutated).
        missing: Missing rows (mutated).
    """
    del hints
    has_base = inspect_file(FileSpec(SUB_UNET, KLEIN_9B_BASE), roots) == "present"
    has_dev = inspect_file(FileSpec(SUB_UNET, FLUX2_DEV), roots) == "present"
    if has_base:
        state = inspect_file(FileSpec(SUB_CLIP, CLIP_8B), roots)
        row = FileRow(name=CLIP_8B, pack="klein-9b-te", cmd=CMD_IMAGE_9B, state=state, subdir=SUB_CLIP)
        if state == "present":
            present.append(row)
        elif not any(item.name == CLIP_8B for item in missing):
            missing.append(row)
        return
    if has_dev:
        state = inspect_file(FileSpec(SUB_CLIP, CLIP_MISTRAL), roots)
        row = FileRow(
            name=CLIP_MISTRAL,
            pack="flux2-dev",
            cmd=CMD_IMAGE_FLUX2_DEV,
            state=state,
            subdir=SUB_CLIP,
        )
        if state == "present":
            present.append(row)
        elif not any(item.name == CLIP_MISTRAL for item in missing):
            missing.append(row)


def format_report(result: CheckResult) -> str:
    """Human status for the node widget and App chip.

    Args:
        result: Scan outcome.

    Returns:
        Multiline operator text.
    """
    label = result.lab_rel or "this App"
    quality = result.quality or QUALITY_LAB
    if result.ok:
        names = ", ".join(row.name for row in result.present[:8] if row.name)
        extra = f"\n{names}." if names else ""
        return f"Ready for {label} @ {quality}{extra}"
    lines = [f"Missing for {label} @ {quality}"]
    for row in result.missing:
        tag = row.state if row.state != "missing" else "missing"
        lines.append(f"- {row.name} ({tag})")
    if result.commands:
        lines.append("Run:")
        lines.extend(result.commands)
        lines.append(CMD_RESTART)
    return "\n".join(lines)


def run_check(
    args: Mapping[str, Any],
    *,
    roots: Sequence[Path] | None = None,
) -> dict[str, Any]:
    """Scan and return a JSON-ready payload.

    Args:
        args: POST body or test dict.
        roots: Models roots. Default: :func:`models_roots`.

    Returns:
        ``ok``, ``message``, ``present``, ``missing``, ``commands``.
    """
    hints = hints_from_args(args)
    result = scan(hints, list(roots) if roots is not None else models_roots())
    return {
        "ok": result.ok,
        "message": format_report(result),
        "lab_rel": result.lab_rel,
        "occupancy": result.occupancy,
        "quality": result.quality,
        "present": [
            {"name": row.name, "pack": row.pack, "cmd": row.cmd, "state": row.state}
            for row in result.present
        ],
        "missing": [
            {"name": row.name, "pack": row.pack, "cmd": row.cmd, "state": row.state}
            for row in result.missing
        ],
        "commands": result.commands,
    }
