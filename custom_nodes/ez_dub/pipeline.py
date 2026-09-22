"""Ingest, VAD, diarize, ASR, translate, clone, mix. Heavy deps stay lazy."""

from __future__ import annotations

import inspect
import os
import shutil
import subprocess
import sys
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, cast

if TYPE_CHECKING:
    from ez_common.protocols import ProgressReporter

from .hooks import AsrHook, EmbedHook, FetchHook, TranslateHook, TtsHook
from .media import extract_audio, fetch_url, ingest, input_directory, is_url
from .media import list_input_media, resolve_media_source, source_combo_options
from .media import _strip_annotated_name
from .speech import (
    cluster_embeddings,
    cosine,
    crop_hallucination_tail,
    energy_vad,
    envelope_cv,
    expected_speech_s,
    is_speech_like,
    match_rms,
    normalize_clone_pcm,
    raise_to_peak,
    speech_band_ratio,
    speech_onset_slice,
    strip_leading_silence,
    tonal_frame_fraction,
    voiced_fraction,
    zc_interval_cv,
    zero_crossing_rate,
)
from .speech import (
    _concat_crossfade,
    _extract_refs,
    _filter_ref_turns,
    _frame_rms,
    _peak_normalize,
    _slice_pcm,
    _speaker_ref_text,
    _trim_silence,
    _turn_rms,
    _voiced_span,
    _zero_cross_indices,
)

from .align import (
    MAX_SPEED,
    SAMPLE_RATE,
    build_timeline,
    collect_room_tone,
    fit_turn,
    lock_duration,
    resample_linear,
    rms,
)
from .audio import read_wav, write_wav
from .disclosure import DISCLOSURE_TEXT, apply_spoken_disclosure, disclosure_for
from .jobstore import dub_dir, load_state, save_state, write_json
from .qc import evaluate_qc
from .sanitize import looks_like_target, sanitize_target
from .srt import turns_to_srt
from .turns import (
    ScriptPayload,
    Turn,
    assign_overlap,
    empty_payload,
    merge_adjacent_turns,
    normalize_turn,
)

# Dub catalog: engines, stages, ISO language widgets, media suffixes.
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
ENGINE_CHATTERBOX = "chatterbox-ml"
ENGINE_QWEN3TTS = "qwen3tts"
ENGINES = (ENGINE_CHATTERBOX, ENGINE_QWEN3TTS)
STAGE_ALL = "all"
STAGE_ANALYZE = "analyze"
STAGE_RENDER = "render"
STAGES = (STAGE_ALL, STAGE_ANALYZE, STAGE_RENDER)
LANG_NAMES: dict[str, str] = {
    "ar": "Arabic",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "es": "Spanish",
    "fi": "Finnish",
    "fr": "French",
    "he": "Hebrew",
    "hi": "Hindi",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "ms": "Malay",
    "nl": "Dutch",
    "no": "Norwegian",
    "pl": "Polish",
    "pt": "Portuguese",
    "ru": "Russian",
    "sv": "Swedish",
    "sw": "Swahili",
    "tr": "Turkish",
    "zh": "Chinese",
}
LANG_CODES = tuple(LANG_NAMES.keys())
SOURCE_LANG_WIDGET = ("auto",) + LANG_CODES
TARGET_LANG_WIDGET = LANG_CODES
SOURCE_NONE = "(none)"
AUDIO_SUFFIXES = (".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac")
VIDEO_SUFFIXES = (".mp4", ".mkv", ".mov", ".webm")
MEDIA_SUFFIXES = AUDIO_SUFFIXES + VIDEO_SUFFIXES

# Tests inject these (often untyped lambdas). Production stays None (fail-soft).
fetch_hook: FetchHook | Callable[..., Any] | None = None
asr_hook: AsrHook | Callable[..., Any] | None = None
embed_hook: EmbedHook | Callable[..., Any] | None = None
translate_hook: TranslateHook | Callable[..., Any] | None = None
tts_hook: TtsHook | Callable[..., Any] | None = None


def _log(message: str) -> None:
    """Write an ``[ez_dub]`` status line to stderr.

    Args:
        message: Human status without a trailing newline.
    """
    print(f"[ez_dub] {message}", file=sys.stderr)


def _progress(total: int) -> ProgressReporter | None:
    """Comfy ProgressBar when the sibling pack is importable.

    Args:
        total: Expected steps.

    Returns:
        ProgressBar-like object, or None in pytest.
    """
    _ensure_lab_custom_nodes_path()
    try:
        from ez_common import node_progress

        return node_progress(total)
    except Exception:  # noqa: BLE001 — pytest / missing pack
        return None


def _ensure_lab_custom_nodes_path() -> None:
    """Make sibling ez_* packs importable under ComfyUI 0.34+ load_custom_node.

    Comfy registers directory packs as the filesystem path, not the folder
    name, and does not put custom_nodes on sys.path.
    """
    root = str(Path(__file__).resolve().parent.parent)
    if root not in sys.path:
        sys.path.insert(0, root)




# Clone/ASR/translate knobs, status strings, pack files, process-local handles.
TRANSLATE_MAX_TOKENS = 512
TRANSLATE_TEMPERATURE = 0.3
TRANSLATE_TIMEOUT_S = 120
CLONE_TEXT_LIMIT = 300
CFG_AUTO = -1.0
CFG_CROSS_LANG = 0.3
CFG_CROSS_LANG_RETRY = 0.5
CFG_RETRY_BELOW = 0.45
CFG_SAME_LANG = 0.5
EXAGGERATION_DEFAULT = 0.5
CLONE_TEMPERATURE = 0.8
CLONE_REPETITION_PENALTY = 1.2
CLONE_MIN_P = 0.05
CLONE_TOP_P = 1.0
EXPECTED_WORDS_PER_S = 2.7
TAIL_SLACK = 1.6
VOICED_MIN_FRAC = 0.20
ZCR_NOISE_FRAC = 0.25
ZCR_SPEECH_MIN = 150.0
ZC_INTERVAL_CV_MIN = 0.18
ZC_INTERVAL_MIN_GAPS = 8
ENVELOPE_CV_MIN = 0.12
CLONE_UNVOICED_STATUS = "clone unvoiced — empty mix"
ONSET_ABS = 0.02
ONSET_REL = 0.12
ONSET_HOLD_S = 0.08
ONSET_PAD_S = 0.03
CLONE_TOKEN_RATE = 25
CLONE_SILENCE_PAD_S = 3.0
CLONE_TOKEN_SLACK = 1.8
CLONE_TOKEN_MIN = 200
CLONE_TOKEN_MAX = 1000
PCM_INT_RANGE = 1.5
REF_MIN_TURN_S = 0.8
REF_SINGLE_S = 6.0
REF_TARGET_S = 8.0
REF_MAX_S = 10.0
REF_MIN_RMS = 0.008
REF_SILENCE_RMS = 0.008
REF_XFADE_MS = 30
REF_PEAK = 0.89
REF_PURITY_MIN_DIM = 8
REF_PURITY_COSINE = 0.55
CLONE_MISSING_STATUS = (
    "clone engine missing — pip install chatterbox-tts and "
    "./scripts/manage.sh download-dub --tier clone"
)
T3_MODEL_STATUS = "chatterbox-tts missing t3_model=v3 — upgrade chatterbox-tts"
PERTH_STATUS = (
    "resemble-perth watermarker missing — PerTh stays on. "
    "docker exec ez-comfy-studio /comfy-state/ComfyUI/.venv/bin/python -m pip install "
    "'setuptools<82' then restart"
)
TRANSLATE_LLAMA_STATUS = (
    "llama.cpp unavailable — Llama did not import. "
    "docker exec ez-comfy-studio /comfy-state/ComfyUI/.venv/bin/python -m pip install "
    "--force-reinstall --no-deps --only-binary=:all: "
    "https://github.com/abetlen/llama-cpp-python/releases/download/v0.3.35/"
    "llama_cpp_python-0.3.35-py3-none-manylinux2014_aarch64.manylinux_2_17_aarch64.whl"
)
TRANSLATE_BLOCKING_MARKERS = (
    "llama.cpp unavailable",
    "GGUF missing",
    "GGUF failed to load",
)
NO_TURNS_STATUS = "no turns — ASR/translate did not run"
NO_TARGET_STATUS = (
    "no target lines — translation did not produce target-language text"
)
ASR_HALLUCINATION_SILENCE_S = 2.0
MISSING_SOURCE_STATUS = (
    "missing source.wav — pick Source file or Upload media, "
    "turn I have rights on, then Queue"
)
_GENERIC_INGEST_STATUS = frozenset({"", "pending", "ok", "ingest"})
ASR_WHEEL_STATUS = "faster-whisper not installed — pip install faster-whisper"
ASR_PACK_STATUS = (
    "ASR pack missing — run ./scripts/manage.sh download-dub --tier asr"
)
CLONE_REQUIRED_FILES = (
    "ve.pt",
    "s3gen.pt",
    "grapheme_mtl_merged_expanded_v1.json",
    "Cangjie5_TC.json",
    "t3_mtl23ls_v3.safetensors",
    "conds.pt",
)
QWEN3_WHEEL_STATUS = (
    "qwen3tts extra not installed — "
    "docker exec ez-comfy-studio /comfy-state/ComfyUI/.venv/bin/python -m pip install "
    "einops soundfile && docker exec ez-comfy-studio "
    "/comfy-state/ComfyUI/.venv/bin/python -m pip install --no-deps qwen-tts"
)
QWEN3_PACK_STATUS = (
    "qwen3tts pack incomplete — ./scripts/manage.sh download-podcast --tier qwen3tts"
)
QWEN3_TOKENIZER_STATUS = (
    "qwen3tts tokenizer missing — ./scripts/manage.sh download-podcast --tier qwen3tts"
)
QWEN3_BASE_REQUIRED_FILES = (
    "model.safetensors",
    "config.json",
    "generation_config.json",
    "tokenizer_config.json",
    "vocab.json",
    "merges.txt",
    "preprocessor_config.json",
)
QWEN3_TOKENIZER_REQUIRED_FILES = (
    "speech_tokenizer/config.json",
    "speech_tokenizer/configuration.json",
    "speech_tokenizer/preprocessor_config.json",
    "speech_tokenizer/model.safetensors",
)
WHISPER_REQUIRED_FILES = ("model.bin", "config.json", "tokenizer.json")
# Spark CTranslate2 wheels are CPU-only; try int8 CPU before CUDA float16.
WHISPER_LOAD_ATTEMPTS: tuple[tuple[str, str], ...] = (
    ("cpu", "int8"),
    ("cuda", "float16"),
)
S3_SR = 16000

# Process-local handles. Tests reset these. Production loads once per Queue.
_WHISPER: Any = None
_WHISPER_DIR_CACHED = ""
_CHATTERBOX: Any = None
_CHATTERBOX_CKPT = ""
_CHATTERBOX_ERR = ""
_CHATTERBOX_COND_KEY = ""
_VOICE_ENCODER: Any = None
_QWEN3: Any = None
_QWEN3_ERR = ""
_QWEN3_PROMPT: Any = None
_QWEN3_PROMPT_KEY = ""


def language_code(code: object) -> str:
    """Map a widget value to an ISO 639-1 code (Chatterbox ``language_id``).

    Args:
        code: Widget ISO code, language name, or ``auto``.
    Returns:
        ``auto``, a two-letter code, or ``en`` when unknown.
    """
    raw = (code if isinstance(code, str) else str(code or "en")).strip().lower()
    if raw in {"", "auto"}:
        return "auto"
    if raw in LANG_NAMES:
        return raw
    for key, name in LANG_NAMES.items():
        if raw == name.lower():
            return key
    if len(raw) == 2 and raw.isalpha():
        return raw
    return "en"


def language_name(code: object) -> str:
    """Map a widget code to an English language name (display only).

    Args:
        code: Widget ISO code, language name, or ``auto``.

    Returns:
        English display name, or ``the source language`` for ``auto``.
    """
    raw = language_code(code)
    if raw == "auto":
        return "the source language"
    return LANG_NAMES.get(raw, LANG_NAMES["en"])


def clone_cfg_weight(
    source: object, target: object, override: object = CFG_AUTO
) -> float:
    """CFG for Chatterbox generate. Auto is 0.3 on language transfer.

    ``0.0`` disables T3 CFG and often vocodes a moan instead of the
    target line. ``0.3`` still reduces reference-accent lock vs 0.5.

    Args:
        source: ISO source or ``auto``.
        target: ISO target.
        override: Widget value. ``< 0`` means auto.
    Returns:
        Weight in ``[0.0, 1.0]``.
    """
    value = CFG_AUTO
    if isinstance(override, bool):
        value = CFG_AUTO
    elif isinstance(override, (int, float)):
        value = float(override)
    elif isinstance(override, str):
        try:
            value = float(override.strip())
        except ValueError:
            value = CFG_AUTO
    if value >= 0.0:
        if value > 1.0:
            return 1.0
        return value
    src = language_code(source)
    tgt = language_code(target)
    if _same_language(src, tgt):
        return CFG_SAME_LANG
    return CFG_CROSS_LANG


def clone_cfg_retry(cfg: float) -> float | None:
    """Stronger CFG for a second take, or None when the first is already high.

    Args:
        cfg: CFG used on the first generate.

    Returns:
        Retry weight, or None when no second take is warranted.
    """
    if float(cfg) < CFG_RETRY_BELOW:
        return CFG_CROSS_LANG_RETRY
    return None


def dub_llm_timeout_s() -> int:
    """Per-turn GGUF timeout for translation (default 120 s).

    Returns:
        Timeout in seconds from ``EZ_DUB_LLM_TIMEOUT_S`` or the default.
    """
    raw = os.environ.get("EZ_DUB_LLM_TIMEOUT_S", str(TRANSLATE_TIMEOUT_S)).strip()
    try:
        value = int(raw)
    except ValueError:
        return TRANSLATE_TIMEOUT_S
    if value < 1:
        return TRANSLATE_TIMEOUT_S
    return value


def split_clone_text(text: str, limit: int = CLONE_TEXT_LIMIT) -> list[str]:
    """Split clone text so each chunk stays within Chatterbox's ~300 char cap.

    Args:
        text: One turn's target sentence(s).
        limit: Max characters per generate() call.
    Returns:
        Non-empty chunks. Empty input yields ``[]``.
    """
    raw = " ".join((text or "").split())
    cap = int(limit) if int(limit) > 0 else CLONE_TEXT_LIMIT
    if not raw:
        return []
    if len(raw) <= cap:
        return [raw]
    chunks: list[str] = []
    rest = raw
    while rest:
        if len(rest) <= cap:
            chunks.append(rest)
            break
        cut = rest.rfind(" ", 0, cap)
        if cut < max(1, cap // 4):
            cut = cap
        piece = rest[:cut].strip()
        if piece:
            chunks.append(piece)
        rest = rest[cut:].strip()
    return chunks


def asr_wheel_status(exc: BaseException | None = None) -> str:
    """Operator-facing ASR miss. Include ImportError detail when present.

    Args:
        exc: Optional ImportError to append.

    Returns:
        Status string for Dub status.
    """
    if exc is None:
        return ASR_WHEEL_STATUS
    return f"{ASR_WHEEL_STATUS} ({exc})"


def _import_whisper_model() -> tuple[Any | None, str]:
    """Load WhisperModel or an operator-facing ImportError reason.

    Returns:
        ``(WhisperModel class, "")`` or ``(None, reason)``. The class is
        ``Any`` because faster-whisper is an optional runtime dep.
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        return None, asr_wheel_status(exc)
    return WhisperModel, ""


def preflight_asr() -> str:
    """Empty when faster-whisper can load; otherwise an operator-facing reason.

    Returns:
        Empty string on success, else a blocking Dub status.
    """
    _, miss = _import_whisper_model()
    if miss:
        return miss
    if not _whisper_dir():
        return ASR_PACK_STATUS
    return ""


def perth_status(exc: BaseException | None = None) -> str:
    """Operator-facing PerTh miss. Include ImportError detail when present.

    Args:
        exc: Optional ImportError to append.

    Returns:
        Status string for Dub status.
    """
    if exc is None:
        return PERTH_STATUS
    return f"{PERTH_STATUS} ({exc})"


def preflight_perth() -> str:
    """Empty when PerTh watermarker is callable; otherwise an operator-facing reason.

    Returns:
        Empty string on success, else a blocking Dub status.
    """
    try:
        import perth
    except ImportError as exc:
        return perth_status(exc)
    if not callable(getattr(perth, "PerthImplicitWatermarker", None)):
        return PERTH_STATUS
    return ""


def preflight_clone() -> str:
    """Empty when Chatterbox V3 can load; otherwise an operator-facing reason.

    Returns:
        Empty string on success, else a blocking Dub status.
    """
    try:
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    except ImportError:
        return (
            "chatterbox-tts not installed — optional runtime: pip install chatterbox-tts"
        )
    loader = getattr(ChatterboxMultilingualTTS, "from_local", None)
    if not callable(loader):
        return "chatterbox-tts missing from_local — upgrade chatterbox-tts"
    try:
        if "t3_model" not in inspect.signature(loader).parameters:
            return T3_MODEL_STATUS
    except (TypeError, ValueError):
        return T3_MODEL_STATUS
    perth_miss = preflight_perth()
    if perth_miss:
        return perth_miss
    if clone_ckpt_dir() is None:
        return "clone pack missing — run ./scripts/manage.sh download-dub --tier clone"
    return ""


def _import_qwen3_model() -> tuple[Any | None, str]:
    """Load Qwen3TTSModel or an operator-facing ImportError reason.

    Returns:
        ``(model class, "")`` or ``(None, reason)``. The class is ``Any``
        because qwen-tts is an optional runtime dep.
    """
    try:
        from qwen_tts import Qwen3TTSModel  # type: ignore[import-not-found]
    except ImportError as exc:
        return None, f"{QWEN3_WHEEL_STATUS} ({exc})"
    except Exception:  # noqa: BLE001 — optional runtime
        return None, QWEN3_WHEEL_STATUS
    return Qwen3TTSModel, ""


def preflight_qwen3() -> str:
    """Empty when Qwen3-TTS can load offline; otherwise an operator-facing reason.

    Returns:
        Empty string on success, else a blocking Dub status.
    """
    model_cls, miss = _import_qwen3_model()
    if miss:
        return miss
    folder = qwen3_base_dir()
    if folder is None or not qwen3_base_is_complete(folder):
        return QWEN3_PACK_STATUS
    if not qwen3_tokenizer_is_complete(folder):
        return QWEN3_TOKENIZER_STATUS
    loader = getattr(model_cls, "from_pretrained", None)
    if not callable(loader):
        return "qwen3tts missing from_pretrained"
    return ""


def translate_llama_status() -> str:
    """Operator-facing Dub status when Llama cannot import.

    Returns:
        Blocking status from ez_prompt_enhance, or a local fallback.
    """
    try:
        _ensure_lab_custom_nodes_path()
        from ez_prompt_enhance.client import llama_cpp_unavailable_status
    except Exception:  # noqa: BLE001 — missing pack is a dub hard miss
        return TRANSLATE_LLAMA_STATUS
    return llama_cpp_unavailable_status()


def preflight_translate() -> str:
    """Empty when the on-box GGUF writer can load; otherwise a blocking reason.

    Returns:
        Empty string on success, else a blocking Dub status.
    """
    try:
        _ensure_lab_custom_nodes_path()
        from ez_prompt_enhance.client import _get_llama
        from ez_prompt_enhance.client import status_for_reason
    except Exception:  # noqa: BLE001 — missing pack is a dub hard miss
        return translate_llama_status()
    try:
        _handle, reason = _get_llama()
    except Exception as exc:  # noqa: BLE001 — ctypes load is RuntimeError
        _log(f"llama.cpp preflight raised: {exc}")
        return translate_llama_status()
    if not reason:
        return ""
    return status_for_reason(reason) or reason


def translate_blocking_status(status: str) -> str:
    """Return ``status`` when it names a fatal translate miss; else empty.

    Args:
        status: Payload or preflight status.

    Returns:
        The same status when it is fatal, else ``""``.
    """
    raw = (status or "").strip()
    if not raw:
        return ""
    for marker in TRANSLATE_BLOCKING_MARKERS:
        if marker in raw:
            return raw
    return ""


def _translation_needed(
    enhance: bool, source_language: str, target_language: str
) -> bool:
    """True when Queue must run the GGUF writer (cross-language, enhance on).

    Args:
        enhance: Widget; False pins widget text.
        source_language: ISO source or ``auto``.
        target_language: ISO target.

    Returns:
        Whether translation must run.
    """
    if not enhance:
        return False
    return not _same_language(source_language, target_language)


def load_translate_prompt() -> str:
    """Writer system prompt for GGUF translation.

    Returns:
        Contents of ``prompts/translate_turns.txt``.
    """
    path = PROMPTS_DIR / "translate_turns.txt"
    return path.read_text(encoding="utf-8").strip()




def _run(cmd: list[str]) -> tuple[int, str]:
    """Run a subprocess; never raise on a missing binary.

    Args:
        cmd: argv.

    Returns:
        ``(returncode, stderr or stdout)``. Missing binary is ``(127, ...)``.
    """
    try:
        proc = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        return 127, str(exc)
    err = (proc.stderr or proc.stdout or "").strip()
    return int(proc.returncode), err




def _default_embed(pcm: list[float], rate: int) -> list[float]:
    """Tiny energy/zcr fingerprint so clustering works without ONNX.

    Args:
        pcm: Turn slice PCM.
        rate: Unused (call-site compatibility).

    Returns:
        Four-float fingerprint.
    """
    del rate
    if not pcm:
        return [0.0, 0.0, 0.0, 0.0]
    energy = rms(pcm)
    zc = 0
    prev = 0.0
    for sample in pcm[:: max(1, len(pcm) // 400)]:
        if sample == 0:
            continue
        if prev != 0 and (sample > 0) != (prev > 0):
            zc += 1
        prev = sample
    peak = max(abs(float(x)) for x in pcm)
    mean = sum(float(x) for x in pcm) / len(pcm)
    return [energy, float(zc), peak, mean]


def _close_voice_encoder() -> None:
    """Drop the cached Chatterbox VoiceEncoder handle."""
    global _VOICE_ENCODER
    _VOICE_ENCODER = None


def _get_voice_encoder() -> Any | None:
    """Load Chatterbox VoiceEncoder + ve.pt once. None when the pack/wheel is missing.

    Returns:
        Encoder handle, or None. Typed ``Any`` because chatterbox is optional.
    """
    global _VOICE_ENCODER
    if _VOICE_ENCODER is not None:
        return _VOICE_ENCODER
    ckpt = clone_ckpt_dir()
    if ckpt is None:
        return None
    ve_path = Path(ckpt) / "ve.pt"
    if not ve_path.is_file():
        return None
    try:
        import torch
        from chatterbox.models.voice_encoder import VoiceEncoder
    except Exception:  # noqa: BLE001 — optional runtime
        return None
    try:
        encoder = VoiceEncoder()
        state = torch.load(str(ve_path), map_location="cpu", weights_only=True)
        encoder.load_state_dict(state)
        encoder.eval()
    except Exception as exc:  # noqa: BLE001 — fail-soft to energy fingerprint
        _log(f"voice encoder load failed: {exc}")
        return None
    _VOICE_ENCODER = encoder
    return encoder


def _resample_for_encoder(pcm: list[float], rate: int, dest_rate: int = S3_SR) -> list[float]:
    """Linear resample a turn slice to the VoiceEncoder rate.

    Args:
        pcm: Turn slice PCM.
        rate: Current sample rate.
        dest_rate: VoiceEncoder rate (16 kHz).

    Returns:
        Resampled PCM.
    """
    sr = int(rate) or SAMPLE_RATE
    if sr == dest_rate:
        return [float(x) for x in pcm]
    if not pcm or dest_rate < 1:
        return []
    out_len = max(1, int(round(len(pcm) * dest_rate / sr)))
    from .align import resample_linear

    return resample_linear(pcm, out_len)


def speaker_embed(pcm: list[float], rate: int) -> list[float]:
    """Speaker embedding from ve.pt when available; energy fingerprint otherwise.

    Args:
        pcm: Turn slice PCM.
        rate: Sample rate.

    Returns:
        Embedding vector (dimension depends on the encoder).
    """
    hook = embed_hook
    if hook is not None:
        return hook(pcm, rate)
    encoder = _get_voice_encoder()
    if encoder is None or not pcm:
        return _default_embed(pcm, rate)
    wav = _resample_for_encoder(pcm, rate)
    if not wav:
        return _default_embed(pcm, rate)
    try:
        import numpy as np

        arr = np.asarray(wav, dtype=np.float32)
        embeds = encoder.embeds_from_wavs([arr], sample_rate=S3_SR)
        if embeds is None:
            return _default_embed(pcm, rate)
        flat = _pcm_list(embeds[0] if getattr(embeds, "__len__", None) else embeds)
        if flat:
            return flat
    except Exception as exc:  # noqa: BLE001 — energy fingerprint is the fallback
        _log(f"voice encoder embed failed: {exc}")
    return _default_embed(pcm, rate)


def analyze_pcm(
    samples: list[float],
    rate: int,
    *,
    max_speakers: int = 0,
    language: str = "auto",
    wav_path: Path | None = None,
) -> tuple[list[Turn], str, str]:
    """ASR segments become turns; cluster speakers from those slices.

    Energy VAD is not the turn source. Missing Whisper returns empty turns
    plus an operator-facing reason (never unlabeled empty-text windows).

    Args:
        samples: Source PCM.
        rate: Sample rate.
        max_speakers: Cluster cap; 0 means default.
        language: Whisper language or ``auto``.
        wav_path: Source wav (required for ASR).

    Returns:
        ``(turns, detected_language, reason)``. Turns are JSON mappings.
    """
    hook = asr_hook
    detected = ""
    raw: list[Turn] = []
    if hook is not None and wav_path is not None:
        asr_turns = hook(wav_path, language)
        raw = [normalize_turn(item, i + 1) for i, item in enumerate(asr_turns or [])]
        if not raw:
            return [], "", "no speech"
    elif wav_path is not None:
        raw, detected, reason = _whisper_segments(wav_path, language)
        if reason:
            return [], detected, reason
    else:
        return [], "", MISSING_SOURCE_STATUS
    _log(f"ASR {len(raw)} segments — clustering speakers")
    bar = _progress(max(len(raw), 1))
    vectors: list[list[float]] = []
    for turn in raw:
        chunk = _slice_pcm(samples, rate, float(turn["t0"]), float(turn["t1"]))
        turn["rms"] = rms(chunk)
        vectors.append(speaker_embed(chunk, rate))
        if bar is not None:
            bar.update(1)
    speakers = cluster_embeddings(vectors, max_speakers=max_speakers)
    for turn, speaker in zip(raw, speakers):
        turn["speaker"] = speaker
    return assign_overlap(raw), detected, ""


def _close_whisper() -> None:
    """Drop the cached faster-whisper handle."""
    global _WHISPER, _WHISPER_DIR_CACHED
    _WHISPER = None
    _WHISPER_DIR_CACHED = ""


def _load_whisper_model(model_dir: str) -> Any:
    """Construct WhisperModel, trying CPU int8 then CUDA float16.

    Args:
        model_dir: CTranslate2 snapshot path.

    Returns:
        Loaded model handle (optional faster-whisper type).
    """
    whisper_cls, miss = _import_whisper_model()
    if whisper_cls is None:
        raise ImportError(miss or ASR_WHEEL_STATUS)
    last: Exception | None = None
    for device, compute in WHISPER_LOAD_ATTEMPTS:
        try:
            return whisper_cls(model_dir, device=device, compute_type=compute)
        except Exception as exc:  # noqa: BLE001 — try the next device
            last = exc
            _log(f"faster-whisper {device}/{compute} failed: {exc}")
    if last is not None:
        raise last
    raise RuntimeError("faster-whisper failed to load")


def _get_whisper() -> tuple[Any | None, str]:
    """Cached faster-whisper handle plus a miss reason.

    Returns:
        ``(model, "")`` or ``(None, reason)``. Model is optional-dep ``Any``.
    """
    global _WHISPER, _WHISPER_DIR_CACHED
    _cls, miss = _import_whisper_model()
    if _cls is None:
        return None, miss or ASR_WHEEL_STATUS
    model_dir = _whisper_dir()
    if not model_dir:
        return None, ASR_PACK_STATUS
    if _WHISPER is not None and _WHISPER_DIR_CACHED == model_dir:
        return _WHISPER, ""
    try:
        _WHISPER = _load_whisper_model(model_dir)
    except Exception as exc:  # noqa: BLE001 — fail-soft
        _WHISPER = None
        _WHISPER_DIR_CACHED = ""
        return None, f"faster-whisper failed: {exc}"
    _WHISPER_DIR_CACHED = model_dir
    return _WHISPER, ""


def _whisper_segments(
    wav_path: Path, language: str
) -> tuple[list[Turn], str, str]:
    """Transcribe the whole file. Turns are Whisper segments with text.

    Args:
        wav_path: Source wav.
        language: Whisper language or ``auto``.

    Returns:
        ``(turns, detected_iso, reason)``. Turns are JSON mappings.
    """
    if not wav_path.is_file():
        return [], "", MISSING_SOURCE_STATUS
    model, miss = _get_whisper()
    if model is None:
        _log(miss or asr_wheel_status())
        return [], "", miss or asr_wheel_status()
    try:
        lang = None if language in {"", "auto"} else language
        path = str(wav_path)
        try:
            segments, info = model.transcribe(
                path,
                language=lang,
                word_timestamps=True,
                vad_filter=True,
                beam_size=5,
                condition_on_previous_text=False,
                hallucination_silence_threshold=ASR_HALLUCINATION_SILENCE_S,
            )
        except TypeError:
            try:
                segments, info = model.transcribe(
                    path,
                    language=lang,
                    word_timestamps=True,
                    vad_filter=True,
                    beam_size=5,
                    condition_on_previous_text=False,
                )
            except TypeError:
                try:
                    segments, info = model.transcribe(
                        path,
                        language=lang,
                        word_timestamps=True,
                        vad_filter=True,
                    )
                except TypeError:
                    segments, info = model.transcribe(
                        path, language=lang, word_timestamps=False
                    )
    except Exception as exc:  # noqa: BLE001 — fail-soft
        reason = f"faster-whisper failed: {exc}"
        _log(reason)
        return [], "", reason
    turns: list[Turn] = []
    for i, seg in enumerate(list(segments), start=1):
        text = str(getattr(seg, "text", "") or "").strip()
        start = float(getattr(seg, "start", 0.0) or 0.0)
        end = float(getattr(seg, "end", start) or start)
        words = getattr(seg, "words", None) or []
        if words:
            first = words[0]
            last = words[-1]
            w0 = (
                first.get("start")
                if isinstance(first, dict)
                else getattr(first, "start", None)
            )
            w1 = (
                last.get("end")
                if isinstance(last, dict)
                else getattr(last, "end", None)
            )
            try:
                if w0 is not None:
                    start = float(w0)
                if w1 is not None:
                    end = float(w1)
            except (TypeError, ValueError):
                pass
        if not text or end <= start:
            continue
        turns.append(
            {
                "id": i,
                "speaker": "spk00",
                "t0": start,
                "t1": end,
                "text": text,
                "text_target": "",
                "overlap": False,
                "rms": 0.0,
            }
        )
    detected = str(getattr(info, "language", "") or "").strip().lower()
    code = language_code(detected) if detected else ""
    if not turns:
        return [], code, "no speech"
    return turns, code, ""


def _whisper_dir() -> str:
    """First directory that has model.bin, config.json, and tokenizer.json.

    Returns:
        Snapshot path string, or ``""`` when missing.
    """
    for root in _model_roots():
        candidates = (
            Path(root) / "Systran__faster-whisper-large-v3_whisper",
            Path(root) / "comfy" / "whisper",
            Path(root) / "Systran__faster-whisper-large-v3_asr",
        )
        for folder in candidates:
            if all((folder / name).is_file() for name in WHISPER_REQUIRED_FILES):
                return str(folder)
    return ""


def _copy_source_targets(turns: Sequence[Mapping[str, Any]]) -> list[Turn]:
    """Copy ``text`` into empty ``text_target`` fields.

    Args:
        turns: JSON turns.

    Returns:
        Shallow copies with ``text_target`` filled when empty.
    """
    out: list[Turn] = []
    for turn in turns:
        item = cast(Turn, dict(turn))
        if not str(item.get("text_target") or "").strip():
            item["text_target"] = str(item.get("text") or "")
        out.append(item)
    return out


def _same_language(source: str, target: str) -> bool:
    """True when both resolve to the same ISO code (``auto`` is never same).

    Args:
        source: Widget or ISO source.
        target: Widget or ISO target.

    Returns:
        Whether clone may copy source text as the target line.
    """
    src = language_code(source)
    tgt = language_code(target)
    if src in {"", "auto"}:
        return False
    return src == tgt


def _translate_user_message(
    text: str,
    source: str,
    target: str,
    *,
    prev_source: str = "",
    prev_target: str = "",
    next_source: str = "",
    window_s: float = 0.0,
) -> str:
    """Build the GGUF user prompt for one turn.

    Args:
        text: Source sentence.
        source: Source language widget.
        target: Target language widget.
        prev_source: Previous source line (context only).
        prev_target: Previous translation (context only).
        next_source: Following source line (context only).
        window_s: Source turn duration in seconds (hint only).

    Returns:
        Prompt string with ``/no_think``.
    """
    src_name = language_name(source)
    tgt = language_code(target)
    tgt_name = language_name(tgt)
    parts = [
        f"/no_think\nTranslate from {src_name} to {tgt_name} ({tgt}). "
        "Output only the translated sentence.\n\n"
        f"Source: {text}"
    ]
    if window_s > 0.0:
        parts.append(f"Source window: {window_s:.1f} s.")
    if prev_source:
        parts.append(
            "Context (previous turn, do not translate this block):\n"
            f"Source: {prev_source}\n"
            f"Target: {prev_target}"
        )
    if next_source:
        parts.append(f"Following source (do not translate): {next_source}")
    return "\n\n".join(parts)


def translate_turns(
    turns: Sequence[Mapping[str, Any]],
    target_language: str,
    source_language: str,
    *,
    enhance: bool = True,
) -> tuple[list[Turn], str]:
    """Fill ``text_target`` one turn at a time.

    Fatal GGUF/llama.cpp misses leave ``text_target`` empty so render cannot
    clone the source language as the target.

    Args:
        turns: JSON turns with source ``text``.
        target_language: ISO target.
        source_language: ISO source or ``auto``.
        enhance: When False, copy source into ``text_target``.

    Returns:
        ``(turns, status)``.
    """
    tgt = language_code(target_language)
    src = language_code(source_language)
    if not enhance:
        return _copy_source_targets(turns), "enhance off"
    if _same_language(src, tgt):
        return _copy_source_targets(turns), "same language"
    hook = translate_hook
    if hook is not None:
        return cast(list[Turn], list(hook(list(turns), tgt, src))), ""
    spoken = [t for t in turns if str(t.get("text") or "").strip()]
    if not spoken:
        return [cast(Turn, dict(t)) for t in turns], "no turns"
    try:
        _ensure_lab_custom_nodes_path()
        from ez_prompt_enhance.client import REASON_EMPTY
        from ez_prompt_enhance.client import REASON_GGUF_MISSING
        from ez_prompt_enhance.client import REASON_LLAMA_UNAVAILABLE
        from ez_prompt_enhance.client import REASON_LLM_LOAD_FAILED
        from ez_prompt_enhance.client import _close_llm
        from ez_prompt_enhance.client import complete
    except Exception as exc:  # noqa: BLE001 — fail-soft
        _log(f"prompt enhance client unavailable: {exc}")
        return [cast(Turn, dict(t)) for t in turns], "llama.cpp unavailable"
    system = load_translate_prompt()
    timeout = dub_llm_timeout_s()
    translated = 0
    passthrough = 0
    suspect = 0
    last_reason = ""
    merged: list[Turn] = []
    fatal = ""
    try:
        n_turns = len(turns)
        for idx, turn in enumerate(turns):
            item = cast(Turn, dict(turn))
            source_text = str(item.get("text") or "").strip()
            if not source_text:
                item["text_target"] = str(item.get("text_target") or "")
                merged.append(item)
                continue
            if fatal:
                item["text_target"] = ""
                passthrough += 1
                merged.append(item)
                continue
            prev_source = ""
            prev_target = ""
            if merged:
                prev_source = str(merged[-1].get("text") or "").strip()
                prev_target = str(merged[-1].get("text_target") or "").strip()
            next_source = ""
            if idx + 1 < n_turns:
                next_source = str(turns[idx + 1].get("text") or "").strip()
            window_s = max(
                0.0,
                float(item.get("t1") or 0.0) - float(item.get("t0") or 0.0),
            )
            user = _translate_user_message(
                source_text,
                src,
                tgt,
                prev_source=prev_source,
                prev_target=prev_target,
                next_source=next_source,
                window_s=window_s,
            )
            rewritten, reason = complete(
                system,
                user,
                max_tokens=TRANSLATE_MAX_TOKENS,
                temperature=TRANSLATE_TEMPERATURE,
                timeout_s=timeout,
            )
            if reason in {
                REASON_GGUF_MISSING,
                REASON_LLAMA_UNAVAILABLE,
                REASON_LLM_LOAD_FAILED,
            }:
                fatal = reason
                item["text_target"] = ""
                passthrough += 1
                last_reason = reason
                merged.append(item)
                continue
            cleaned = sanitize_target(
                rewritten or "", source_text=source_text, language=tgt
            )
            needs_retry = (not cleaned or cleaned == source_text) or (
                src != tgt and not looks_like_target(cleaned, tgt)
            )
            if needs_retry and src != tgt:
                rewritten, reason = complete(
                    system,
                    user,
                    max_tokens=TRANSLATE_MAX_TOKENS,
                    temperature=TRANSLATE_TEMPERATURE,
                    timeout_s=timeout,
                )
                cleaned = sanitize_target(
                    rewritten or "", source_text=source_text, language=tgt
                )
            if not cleaned:
                item["text_target"] = ""
                passthrough += 1
                last_reason = reason or REASON_EMPTY
                merged.append(item)
                continue
            if cleaned == source_text:
                item["text_target"] = ""
                passthrough += 1
                last_reason = "passthrough"
                merged.append(item)
                continue
            if src != tgt and not looks_like_target(cleaned, tgt):
                item["text_target"] = ""
                passthrough += 1
                suspect += 1
                last_reason = "passthrough"
                merged.append(item)
                continue
            item["text_target"] = cleaned
            translated += 1
            merged.append(item)
    finally:
        try:
            _close_llm()
        except Exception as exc:  # noqa: BLE001 — unload is best-effort
            _log(f"writer unload failed: {exc}")
    total = translated + passthrough
    if fatal:
        return merged, fatal
    extra = f"; {suspect} suspect" if suspect else ""
    if passthrough and translated:
        return merged, f"translated {translated}/{total}; {passthrough} passthrough{extra}"
    if passthrough:
        if suspect:
            return merged, f"{last_reason or 'passthrough'}; {suspect} suspect"
        return merged, last_reason or "passthrough"
    if translated:
        return merged, f"translated {translated}/{total}{extra}"
    return merged, ""


def clone_token_budget(text: str) -> int:
    """T3 ``max_new_tokens`` cap for one clone line.

    Includes a hush-token pad so leading silence tokens still fit; onset
    crop strips that prefix after decode. Chatterbox ``generate`` hardcodes
    1000 (~40 s) when this wrap is absent.

    Args:
        text: Target-language line.
    Returns:
        Token count in ``[CLONE_TOKEN_MIN, CLONE_TOKEN_MAX]``.
    """
    need = CLONE_SILENCE_PAD_S + expected_speech_s(text) * CLONE_TOKEN_SLACK
    tokens = int(round(need * CLONE_TOKEN_RATE))
    if tokens < CLONE_TOKEN_MIN:
        return CLONE_TOKEN_MIN
    if tokens > CLONE_TOKEN_MAX:
        return CLONE_TOKEN_MAX
    return tokens




def _pcm_list(wav: object) -> list[float]:
    """Flatten a TTS tensor/array/list into mono float PCM in [-1, 1].

    Args:
        wav: Optional TTS waveform (tensor/array/list; no torch import here).

    Returns:
        Mono float PCM.
    """
    if wav is None:
        return []
    data: Any = wav
    try:
        data = data.detach().cpu().float().reshape(-1)
    except Exception:  # noqa: BLE001 — not a tensor
        pass
    try:
        data = data.tolist()
    except Exception:  # noqa: BLE001 — already a list
        pass
    if isinstance(data, (int, float)):
        return normalize_clone_pcm([float(data)])
    if not isinstance(data, (list, tuple)):
        return []
    out: list[float] = []
    stack: list[Any] = list(data)
    while stack:
        item = stack.pop(0)
        if isinstance(item, (list, tuple)):
            stack = list(item) + stack
            continue
        try:
            out.append(float(item))
        except (TypeError, ValueError):
            continue
    return normalize_clone_pcm(out)


def _model_roots() -> list[str]:
    """MODELS_DIR candidates, then ``/models`` and ``/mnt/models``.

    Returns:
        Unique directory strings (may not exist).
    """
    roots: list[str] = []
    for key in ("MODELS_ROOT", "MODELS_DIR"):
        value = (os.environ.get(key) or "").strip()
        if value and value not in roots:
            roots.append(value)
    for fallback in ("/models", "/mnt/models"):
        if fallback not in roots:
            roots.append(fallback)
    return roots


def clone_dir_is_complete(folder: Path) -> bool:
    """True when ``from_local`` can load multilingual V3 from this directory.

    Args:
        folder: Candidate snapshot.

    Returns:
        Whether all :data:`CLONE_REQUIRED_FILES` exist.
    """
    return all((folder / name).is_file() for name in CLONE_REQUIRED_FILES)


def clone_ckpt_dir() -> Path | None:
    """First complete Chatterbox multilingual V3 snapshot (not t3-only comfy/tts).

    Returns:
        Snapshot path, or None.
    """
    for root in _model_roots():
        candidates = (
            Path(root) / "ResembleAI__chatterbox_clone",
            Path(root) / "comfy" / "tts",
            Path(root) / "tts",
        )
        for folder in candidates:
            if clone_dir_is_complete(folder):
                return folder
    return None


def pkuseg_home_dir() -> Path | None:
    """MODELS_DIR pkuseg home when the ontonotes zip or extract is present.

    Returns:
        Directory path, or None.
    """
    env = (os.environ.get("PKUSEG_HOME") or "").strip()
    if env:
        return Path(env)
    for root in _model_roots():
        folder = Path(root) / "pkuseg"
        if (folder / "spacy_ontonotes.zip").is_file() or (
            folder / "spacy_ontonotes"
        ).is_dir():
            return folder
    return None


@contextmanager
def _chatterbox_local_only(ckpt: Path) -> Iterator[None]:
    """Force Cangjie + pkuseg onto the clone snapshot. No Hub during load/generate.

    Args:
        ckpt: Clone snapshot directory.

    Returns:
        Context manager. Restores Hub download hooks on exit.
    """
    cangjie = ckpt / "Cangjie5_TC.json"
    prev_offline = os.environ.get("HF_HUB_OFFLINE")
    prev_pkuseg = os.environ.get("PKUSEG_HOME")
    os.environ["HF_HUB_OFFLINE"] = "1"
    pkuseg_home = pkuseg_home_dir()
    if pkuseg_home is not None:
        os.environ["PKUSEG_HOME"] = str(pkuseg_home)
    patches: list[tuple[Any, str, Any]] = []

    def _local_download(
        repo_id: str,
        filename: str,
        cache_dir: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Serve Cangjie from the snapshot; refuse other Hub filenames.

        Args:
            repo_id: Unused Hub repo.
            filename: Requested file.
            cache_dir: Unused Hub cache.
            **kwargs: Unused Hub kwargs (optional-dep boundary).

        Returns:
            Local Cangjie path.
        """
        del repo_id, cache_dir, kwargs
        if filename == "Cangjie5_TC.json" and cangjie.is_file():
            return str(cangjie)
        raise RuntimeError(f"hub download blocked: {filename}")

    def _patch(mod: Any, name: str) -> None:
        """Replace ``mod.name`` with ``_local_download`` and record the original.

        Args:
            mod: Module or None (optional huggingface_hub).
            name: Attribute to wrap.
        """
        if mod is None or not hasattr(mod, name):
            return
        patches.append((mod, name, getattr(mod, name)))
        setattr(mod, name, _local_download)

    try:
        try:
            import huggingface_hub

            _patch(huggingface_hub, "hf_hub_download")
        except Exception:  # noqa: BLE001 — optional at unit-test time
            pass
        tok_mod = sys.modules.get("chatterbox.models.tokenizers.tokenizer")
        if tok_mod is not None:
            _patch(tok_mod, "hf_hub_download")
        yield
    finally:
        for mod, name, orig in reversed(patches):
            setattr(mod, name, orig)
        if prev_offline is None:
            os.environ.pop("HF_HUB_OFFLINE", None)
        else:
            os.environ["HF_HUB_OFFLINE"] = prev_offline
        if prev_pkuseg is None:
            os.environ.pop("PKUSEG_HOME", None)
        else:
            os.environ["PKUSEG_HOME"] = prev_pkuseg


def _from_local_multilingual(loader: Callable[..., Any], ckpt: str, device: str) -> Any:
    """Call ``from_local`` with T3 V3. Older wheels cannot load our snapshot.

    Only remap a missing ``t3_model`` parameter. Inner TypeError (PerTh
    watermarker None, conds.pt, pkuseg) must surface as ``chatterbox failed``.

    Args:
        loader: ``ChatterboxMultilingualTTS.from_local``.
        ckpt: Snapshot path string.
        device: ``cuda`` or ``cpu``.

    Returns:
        Loaded model handle (optional chatterbox type).
    """
    try:
        params = inspect.signature(loader).parameters
    except (TypeError, ValueError) as exc:
        raise RuntimeError(T3_MODEL_STATUS) from exc
    if "t3_model" not in params:
        raise RuntimeError(T3_MODEL_STATUS)
    return loader(ckpt, device=device, t3_model="v3")


def _close_chatterbox() -> None:
    """Drop the cached Chatterbox handle and last error."""
    global _CHATTERBOX, _CHATTERBOX_CKPT, _CHATTERBOX_ERR, _CHATTERBOX_COND_KEY
    _CHATTERBOX = None
    _CHATTERBOX_CKPT = ""
    _CHATTERBOX_ERR = ""
    _CHATTERBOX_COND_KEY = ""


def _chatterbox_device() -> str:
    """``cuda`` when torch reports it, else ``cpu``.

    Returns:
        Device string for ``from_local``.
    """
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
    except Exception:  # noqa: BLE001 — CPU is the safe default
        pass
    return "cpu"


def _install_lab_tts_compat() -> None:
    """Re-apply the lab Chatterbox deprecation shims once torch is loaded.

    ``docker/pythonpath/sitecustomize.py`` installs these at interpreter start,
    but recent torch exposes ``torch.backends`` through a proxy whose attribute
    lookup can hand back an object the start-up sweep never patched. Calling the
    hook here, after torch is definitely imported, keeps the deprecated
    ``torch.backends.cuda.sdp_kernel`` ``FutureWarning`` out of Dub logs
    regardless of which process or import order loaded torch.

    Returns:
        None
    """
    try:
        import importlib

        sitecustomize = importlib.import_module("sitecustomize")
    except ImportError:
        return  # Lab pythonpath not on this interpreter; nothing to re-apply.
    try:
        ensure = getattr(sitecustomize, "ensure_lab_tts_compat_hooks", None)
        if callable(ensure):
            ensure()
    except Exception as exc:  # noqa: BLE001 — shim is an optimisation, never blocking
        _log(f"lab tts compat hook failed: {exc}")


def _load_chatterbox_model() -> tuple[Any | None, str]:
    """Uncached from_local. Prefer this snapshot over a mixed comfy/tts dir.

    Returns:
        ``(model, "")`` or ``(None, reason)``. Model is optional-dep ``Any``.
    """
    _install_lab_tts_compat()
    try:
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    except ImportError:
        return (
            None,
            "chatterbox-tts not installed — optional runtime: pip install chatterbox-tts",
        )
    ckpt = clone_ckpt_dir()
    if ckpt is None:
        return (
            None,
            "clone pack missing — run ./scripts/manage.sh download-dub --tier clone",
        )
    loader = getattr(ChatterboxMultilingualTTS, "from_local", None)
    if not callable(loader):
        return None, "chatterbox-tts missing from_local — upgrade chatterbox-tts"
    try:
        with _chatterbox_local_only(ckpt):
            model = _from_local_multilingual(loader, str(ckpt), _chatterbox_device())
    except RuntimeError as exc:
        return None, str(exc)
    except Exception as exc:  # noqa: BLE001 — fail-soft
        return None, f"chatterbox failed: {exc}"
    return model, ""


def _get_chatterbox() -> tuple[Any | None, str]:
    """Cached Chatterbox Multilingual V3 handle (including a failed load).

    Returns:
        ``(model, "")`` or ``(None, reason)``. Model is optional-dep ``Any``.
    """
    global _CHATTERBOX, _CHATTERBOX_CKPT, _CHATTERBOX_ERR
    ckpt = clone_ckpt_dir()
    ckpt_s = str(ckpt) if ckpt is not None else ""
    if _CHATTERBOX is not None and _CHATTERBOX_CKPT == ckpt_s and ckpt_s:
        return _CHATTERBOX, ""
    if (
        _CHATTERBOX is None
        and _CHATTERBOX_ERR
        and _CHATTERBOX_CKPT == ckpt_s
        and ckpt_s
    ):
        return None, _CHATTERBOX_ERR
    model, err = _load_chatterbox_model()
    if model is None:
        _CHATTERBOX = None
        _CHATTERBOX_CKPT = ckpt_s
        _CHATTERBOX_ERR = err
        return None, err
    _CHATTERBOX = model
    _CHATTERBOX_CKPT = ckpt_s
    _CHATTERBOX_ERR = ""
    return model, ""


@contextmanager
def _cap_t3_tokens(model: Any, budget: int) -> Iterator[None]:
    """Pin ``t3.inference(..., max_new_tokens)`` for one generate() call.

    Args:
        model: Loaded Chatterbox handle (optional-dep ``Any``).
        budget: Token cap.

    Returns:
        Context manager. Restores ``t3.inference`` on exit.
    """
    t3 = getattr(model, "t3", None)
    infer = getattr(t3, "inference", None)
    if t3 is None or not callable(infer):
        yield
        return
    cap = int(budget)
    if cap < 1:
        cap = CLONE_TOKEN_MAX

    def _capped(*args: Any, **kwargs: Any) -> Any:
        """t3.inference wrapper that clamps ``max_new_tokens``.

        Args:
            *args: Forwarded positional (optional TTS API).
            **kwargs: Forwarded keywords; ``max_new_tokens`` is capped.

        Returns:
            Inner inference result (optional TTS tensor/object).
        """
        raw = kwargs.get("max_new_tokens", CLONE_TOKEN_MAX)
        try:
            current = int(raw) if raw is not None else CLONE_TOKEN_MAX
        except (TypeError, ValueError):
            current = CLONE_TOKEN_MAX
        if current < 1:
            current = CLONE_TOKEN_MAX
        kwargs["max_new_tokens"] = min(current, cap)
        return infer(*args, **kwargs)

    t3.inference = _capped
    try:
        yield
    finally:
        t3.inference = infer


def _try_chatterbox(
    text: str,
    language_id: str,
    ref_wav: str,
    *,
    exaggeration: float = EXAGGERATION_DEFAULT,
    cfg_weight: float = CFG_SAME_LANG,
    temperature: float = CLONE_TEMPERATURE,
) -> tuple[list[float], int, str]:
    """Lazy Chatterbox Multilingual generate. Empty PCM plus a reason on miss.

    Args:
        text: Target-language chunk.
        language_id: ISO language id.
        ref_wav: Speaker reference path.
        exaggeration: Chatterbox exaggeration.
        cfg_weight: Chatterbox CFG.
        temperature: Sampling temperature.

    Returns:
        ``(pcm, rate, error)``. ``error`` is empty on success.
    """
    global _CHATTERBOX_COND_KEY
    model, err = _get_chatterbox()
    if model is None:
        return [], SAMPLE_RATE, err or CLONE_MISSING_STATUS
    generate = getattr(model, "generate", None)
    if not callable(generate):
        return [], SAMPLE_RATE, "chatterbox missing generate"
    kwargs: dict[str, Any] = {
        "language_id": language_id,
        "exaggeration": float(exaggeration),
        "cfg_weight": float(cfg_weight),
        "temperature": float(temperature),
    }
    try:
        params: Any = inspect.signature(generate).parameters
    except (TypeError, ValueError):
        params = {}
    has_rep = "repetition_penalty" in params
    has_min_p = "min_p" in params
    has_top_p = "top_p" in params
    has_var = any(
        item.kind == inspect.Parameter.VAR_KEYWORD for item in params.values()
    )
    if has_rep or has_var:
        kwargs["repetition_penalty"] = CLONE_REPETITION_PENALTY
    if has_min_p or has_var:
        kwargs["min_p"] = CLONE_MIN_P
    if has_top_p or has_var:
        kwargs["top_p"] = CLONE_TOP_P
    ref = (ref_wav or "").strip()
    cond_key = ""
    if ref and Path(ref).is_file():
        cond_key = f"{ref}|{float(exaggeration):.4f}"
        kwargs["audio_prompt_path"] = ref
    try:
        ckpt = clone_ckpt_dir()
        with _cap_t3_tokens(model, clone_token_budget(text)):
            if ckpt is not None:
                with _chatterbox_local_only(ckpt):
                    wav = generate(text, **kwargs)
            else:
                wav = generate(text, **kwargs)
        pcm = _pcm_list(wav)
        rate = int(getattr(model, "sr", SAMPLE_RATE) or SAMPLE_RATE)
    except Exception as exc:  # noqa: BLE001 — fail-soft
        return [], SAMPLE_RATE, f"chatterbox failed: {exc}"
    if not pcm:
        return [], rate, "chatterbox returned empty audio"
    if cond_key:
        _CHATTERBOX_COND_KEY = cond_key
    return pcm, rate, ""


def _close_qwen3() -> None:
    """Drop the cached Qwen3-TTS handle and voice-clone prompt."""
    global _QWEN3, _QWEN3_ERR, _QWEN3_PROMPT, _QWEN3_PROMPT_KEY
    _QWEN3 = None
    _QWEN3_ERR = ""
    _QWEN3_PROMPT = None
    _QWEN3_PROMPT_KEY = ""


def _qwen3_snapshot_candidates() -> list[Path]:
    """Possible Base snapshot directories under model roots.

    Returns:
        Candidate paths (may not exist).
    """
    found: list[Path] = []
    for root in _model_roots():
        found.extend(
            (
                Path(root) / "Qwen__Qwen3-TTS-12Hz-0.6B-Base_qwen3tts",
                Path(root) / "Qwen__Qwen3-TTS-12Hz-0.6B-Base",
                Path(root) / "qwen3tts",
            )
        )
    return found


def qwen3_base_is_complete(folder: Path) -> bool:
    """True when Base metadata + talker weights are on disk.

    Args:
        folder: Candidate snapshot.

    Returns:
        Whether all :data:`QWEN3_BASE_REQUIRED_FILES` exist.
    """
    return all((folder / name).is_file() for name in QWEN3_BASE_REQUIRED_FILES)


def qwen3_tokenizer_is_complete(folder: Path) -> bool:
    """True when the nested 12Hz speech tokenizer is on disk.

    Args:
        folder: Candidate snapshot.

    Returns:
        Whether all :data:`QWEN3_TOKENIZER_REQUIRED_FILES` exist.
    """
    return all((folder / name).is_file() for name in QWEN3_TOKENIZER_REQUIRED_FILES)


def qwen3_dir_is_complete(folder: Path) -> bool:
    """True when ``from_pretrained(..., local_files_only=True)`` can run.

    Args:
        folder: Candidate snapshot.

    Returns:
        Whether Base + tokenizer files exist.
    """
    return qwen3_base_is_complete(folder) and qwen3_tokenizer_is_complete(folder)


def qwen3_base_dir() -> Path | None:
    """First Base snapshot that has any sentinel (even incomplete).

    Returns:
        Snapshot path, or None.
    """
    for folder in _qwen3_snapshot_candidates():
        if (folder / "model.safetensors").is_file() or (folder / "config.json").is_file():
            return folder
    return None


def qwen3_ckpt_dir() -> Path | None:
    """First complete local Qwen3-TTS Base snapshot (0.6B download-podcast pack).

    Returns:
        Snapshot path, or None.
    """
    for folder in _qwen3_snapshot_candidates():
        if qwen3_dir_is_complete(folder):
            return folder
    return None


def _from_pretrained_local(loader: Callable[..., Any], ckpt: str) -> Any:
    """Call ``from_pretrained`` with ``local_files_only=True`` when supported.

    Args:
        loader: ``Qwen3TTSModel.from_pretrained``.
        ckpt: Snapshot path string.

    Returns:
        Loaded model handle (optional qwen-tts type).
    """
    try:
        return loader(ckpt, local_files_only=True)
    except TypeError:
        return loader(ckpt)


def _load_qwen3_model() -> tuple[Any | None, str]:
    """Uncached Qwen3-TTS Base handle. None plus a reason on miss.

    Returns:
        ``(model, "")`` or ``(None, reason)``. Model is optional-dep ``Any``.
    """
    model_cls, miss = _import_qwen3_model()
    if model_cls is None:
        return None, miss or QWEN3_WHEEL_STATUS
    ckpt = qwen3_ckpt_dir()
    if ckpt is None:
        folder = qwen3_base_dir()
        if folder is None or not qwen3_base_is_complete(folder):
            return None, QWEN3_PACK_STATUS
        return None, QWEN3_TOKENIZER_STATUS
    loader = getattr(model_cls, "from_pretrained", None)
    if not callable(loader):
        return None, "qwen3tts missing from_pretrained"
    try:
        return _from_pretrained_local(loader, str(ckpt)), ""
    except Exception as exc:  # noqa: BLE001 — fail-soft
        return None, f"qwen3tts failed: {exc}"


def _get_qwen3() -> tuple[Any | None, str]:
    """Cached Qwen3-TTS handle (including a failed load).

    Returns:
        ``(model, "")`` or ``(None, reason)``. Model is optional-dep ``Any``.
    """
    global _QWEN3, _QWEN3_ERR
    if _QWEN3 is not None:
        return _QWEN3, ""
    if _QWEN3_ERR:
        return None, _QWEN3_ERR
    model, err = _load_qwen3_model()
    if model is None:
        _QWEN3_ERR = err
        return None, err
    _QWEN3 = model
    _QWEN3_ERR = ""
    return model, ""


def _qwen3_language(language_id: str) -> str:
    """English language name for Qwen3-TTS (``Spanish``, not ``es``).

    Args:
        language_id: ISO code or ``auto``.

    Returns:
        English language name, or ``Auto``.
    """
    raw = language_code(language_id)
    if raw == "auto":
        return "Auto"
    return LANG_NAMES.get(raw, LANG_NAMES["en"])


def _try_qwen3tts(
    text: str,
    language_id: str,
    ref_wav: str,
    ref_text: str = "",
) -> tuple[list[float], int, str]:
    """Lazy Qwen3-TTS Base clone. Empty PCM plus a reason on miss.

    Args:
        text: Target-language chunk.
        language_id: ISO language id.
        ref_wav: Speaker reference path.
        ref_text: Optional transcript sidecar text.

    Returns:
        ``(pcm, rate, error)``. ``error`` is empty on success.
    """
    global _QWEN3_PROMPT, _QWEN3_PROMPT_KEY
    model, err = _get_qwen3()
    if model is None:
        return [], SAMPLE_RATE, err or QWEN3_WHEEL_STATUS
    clone = getattr(model, "generate_voice_clone", None)
    if not callable(clone):
        return [], SAMPLE_RATE, "qwen3tts missing generate_voice_clone"
    ref = (ref_wav or "").strip()
    transcript = (ref_text or "").strip() or (_speaker_ref_text(ref) if ref else "")
    xvec_only = not bool(transcript)
    lang = _qwen3_language(language_id)
    prompt = None
    make_prompt = getattr(model, "create_voice_clone_prompt", None)
    if callable(make_prompt) and ref and Path(ref).is_file():
        key = f"{ref}|{transcript}|{int(xvec_only)}"
        if key != _QWEN3_PROMPT_KEY or _QWEN3_PROMPT is None:
            try:
                prompt = make_prompt(
                    ref_audio=ref,
                    ref_text=transcript or None,
                    x_vector_only_mode=xvec_only,
                )
            except Exception as exc:  # noqa: BLE001 — fall through to inline refs
                _log(f"qwen3tts prompt failed: {exc}")
                prompt = None
            else:
                _QWEN3_PROMPT = prompt
                _QWEN3_PROMPT_KEY = key
        else:
            prompt = _QWEN3_PROMPT
    kwargs: dict[str, Any] = {"text": text, "language": lang}
    if prompt is not None:
        kwargs["voice_clone_prompt"] = prompt
    else:
        if ref and Path(ref).is_file():
            kwargs["ref_audio"] = ref
        if transcript:
            kwargs["ref_text"] = transcript
        kwargs["x_vector_only_mode"] = xvec_only
    try:
        packed: Any = clone(**kwargs)
        wavs, sr = packed
    except Exception as exc:  # noqa: BLE001 — fail-soft
        return [], SAMPLE_RATE, f"qwen3tts failed: {exc}"
    first: object = wavs
    if isinstance(wavs, (list, tuple)) and wavs:
        first = wavs[0]
    pcm = _pcm_list(first)
    rate = int(sr or SAMPLE_RATE)
    if not pcm:
        return [], rate, "qwen3tts returned empty audio"
    return pcm, rate, ""


def synthesize_turn(
    text: str,
    language: str,
    ref_wav: str,
    engine: str,
    *,
    exaggeration: float = EXAGGERATION_DEFAULT,
    cfg_weight: float = CFG_SAME_LANG,
    ref_text: str = "",
) -> tuple[list[float], int, str]:
    """Clone one line. Tests inject ``tts_hook``. ``language`` is an ISO code.

    Args:
        text: Target-language line.
        language: ISO language id.
        ref_wav: Speaker reference path.
        engine: Clone engine id.
        exaggeration: Chatterbox exaggeration.
        cfg_weight: Chatterbox CFG.
        ref_text: Optional Qwen3 ref transcript.

    Returns:
        ``(pcm, rate, error)``. ``error`` is empty on success.
    """
    hook = tts_hook
    lang = language_code(language)
    chunks = split_clone_text(text)
    if not chunks:
        return [], SAMPLE_RATE, ""
    name = engine if engine in ENGINES else ENGINE_CHATTERBOX
    pieces: list[list[float]] = []
    out_rate = SAMPLE_RATE
    last_err = ""
    for chunk in chunks:
        if hook is not None:
            pcm, sr = hook(chunk, lang, ref_wav, engine)
            err = ""
        elif name == ENGINE_QWEN3TTS:
            pcm, sr, err = _try_qwen3tts(chunk, lang, ref_wav, ref_text=ref_text)
        else:
            pcm, sr, err = _try_chatterbox(
                chunk,
                lang,
                ref_wav,
                exaggeration=exaggeration,
                cfg_weight=cfg_weight,
                temperature=CLONE_TEMPERATURE,
            )
        if err:
            last_err = err
            _log(err)
        if not pcm:
            continue
        out_rate = sr or out_rate
        cropped = crop_hallucination_tail(pcm, out_rate, chunk)
        if cropped:
            pieces.append(cropped)
    if not pieces:
        return [], out_rate, last_err
    if len(pieces) == 1:
        return pieces[0], out_rate, ""
    return _concat_crossfade(pieces, out_rate), out_rate, ""


def _maybe_loudnorm_yt(
    dest: Path,
    mix: list[float],
    rate: int,
    source_len: int,
    room: list[float],
) -> list[float]:
    """Fail-soft ffmpeg loudnorm on ez_dub_yt.wav. Keep raised PCM on miss.

    Args:
        dest: Job directory.
        mix: Raised mix PCM (fallback).
        rate: Sample rate.
        source_len: Required sample count.
        room: Room-tone loop for duration lock.

    Returns:
        Loudnorm PCM, or ``mix`` on miss.
    """
    yt = dest / "ez_dub_yt.wav"
    loud = dest / "ez_dub_yt.loudnorm.wav"
    code, _err = _run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(yt),
            "-af",
            "loudnorm=I=-14:LRA=11:TP=-1.5",
            str(loud),
        ]
    )
    if int(code) != 0 or not loud.is_file():
        return mix
    try:
        shutil.copyfile(loud, yt)
        pcm, _sr = read_wav(yt)
    except Exception:  # noqa: BLE001 — fail-soft
        return mix
    if not pcm:
        return mix
    if len(pcm) != int(source_len):
        pcm, _flags = lock_duration(pcm, source_len, room=room, rate=rate)
        write_wav(yt, pcm, rate)
    return pcm


def _maybe_yt_mp3_48k(dest: Path) -> None:
    """Fail-soft 48 kHz / 320k MP3 next to the duration-locked YT wav.

    Args:
        dest: Job directory containing ``ez_dub_yt.wav``.
    """
    yt = dest / "ez_dub_yt.wav"
    mp3 = dest / "ez_dub_yt_48k.mp3"
    if not yt.is_file():
        return
    _run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(yt),
            "-ar",
            "48000",
            "-ac",
            "1",
            "-b:a",
            "320k",
            str(mp3),
        ]
    )


def _write_render_qc(
    dest: Path,
    mix: list[float],
    rate: int,
    turns: list[dict[str, Any]],
    lang: str,
    flags: list[str],
    *,
    extra_qc: list[str],
    peak: float,
) -> None:
    """Write qc.json and append ``qc:`` onto ``flags``. Never raises.

    Args:
        dest: Job directory.
        mix: Mix PCM.
        rate: Sample rate.
        turns: JSON turns.
        lang: ISO target.
        flags: Mutable status flags (appended).
        extra_qc: Extra QC check ids.
        peak: Mix peak passed to evaluate_qc.
    """
    try:
        report = evaluate_qc(
            mix,
            rate,
            turns,
            target_language=lang,
            peak=peak,
            extra_flags=extra_qc,
        )
        write_json(dest / "qc.json", report)
        qc_flags = [str(x) for x in (report.get("flags") or [])]
        if qc_flags:
            flags.append("qc: " + ",".join(qc_flags))
    except Exception as exc:  # noqa: BLE001 — QC must not fail the mix
        _log(f"qc failed: {exc}")


def _clamp_render_knobs(
    speed: float,
    exaggeration: object,
    cfg_weight: float,
    payload: Mapping[str, Any],
) -> tuple[float, float, float]:
    """Clamp speed/exaggeration and resolve clone CFG.

    Args:
        speed: Time-compression ceiling widget.
        exaggeration: Chatterbox exaggeration widget.
        cfg_weight: Chatterbox CFG widget; ``< 0`` means auto.
        payload: JSON script mapping (source/target language).

    Returns:
        ``(pace, exaggeration, cfg)``.
    """
    pace = float(speed) if speed else 1.0
    if pace < 0.5:
        pace = 0.5
    if pace > 1.5:
        pace = 1.5
    try:
        exag = float(exaggeration)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        exag = EXAGGERATION_DEFAULT
    if exag < 0.25:
        exag = 0.25
    if exag > 2.0:
        exag = 2.0
    cfg = clone_cfg_weight(
        payload.get("source_language"),
        payload.get("target_language"),
        cfg_weight,
    )
    return pace, exag, cfg


def fit_speed_cap(pace: float) -> float:
    """Compression ceiling for :func:`fit_turn`.

    Lab default ``1.0`` uses :data:`MAX_SPEED` (1.25×). Values above
    ``1.0`` stay capped at ``MAX_SPEED`` so 1.5 cannot crush.

    Args:
        pace: Speaking-speed widget after clamp.

    Returns:
        Factor in ``[1.0, MAX_SPEED]``.
    """
    value = float(pace) if pace else 1.0
    if value <= 1.0:
        return MAX_SPEED
    if value > MAX_SPEED:
        return MAX_SPEED
    return value


def _empty_render(
    dest: Path,
    rate: int,
    status: str,
    flags: list[str],
) -> tuple[list[float], int, str]:
    """Persist an export-stage failure and return an empty mix.

    Args:
        dest: Job directory.
        rate: Sample rate.
        status: Operator-facing reason.
        flags: Status flags to store.

    Returns:
        ``([], rate, status)``.
    """
    save_state(
        dest,
        {
            "slug": dest.name,
            "stage": "export",
            "status": status,
            "error": None,
            "flags": flags,
        },
    )
    return [], rate, status


def render_mix(
    samples: list[float],
    rate: int,
    payload: Mapping[str, Any],
    dest: Path,
    *,
    engine: str = ENGINE_CHATTERBOX,
    keep_bed: bool = True,
    spoken_disclosure: bool = False,
    speed: float = 1.0,
    exaggeration: float = EXAGGERATION_DEFAULT,
    cfg_weight: float = CFG_AUTO,
) -> tuple[list[float], int, str]:
    """Clone, align, mix, write stems/SRT/disclosure.

    Returns:
        ``(mix_wav, rate, status)``. ``mix_wav`` is the listen clip
        (``ez_dub_mix``): overlay when spoken disclosure is on, leading
        hush stripped when it is off. ``ez_dub_yt.wav`` stays source-timed.

    Args:
        samples: Source PCM.
        rate: Sample rate.
        payload: JSON script mapping.
        dest: Job directory.
        engine: Clone engine id.
        keep_bed: Keep source in non-speech gaps.
        spoken_disclosure: Overlay a localized bumper on the mix wav.
        speed: Time-compression ceiling.
        exaggeration: Chatterbox exaggeration.
        cfg_weight: Chatterbox CFG; ``< 0`` means auto.
    """
    pace, exag, cfg = _clamp_render_knobs(
        speed, exaggeration, cfg_weight, payload
    )
    blocked = translate_blocking_status(str(payload.get("status") or ""))
    if blocked:
        return [], rate, blocked
    turns = list(payload.get("turns") or [])
    if not turns:
        return [], rate, NO_TURNS_STATUS
    name = engine if engine in ENGINES else ENGINE_CHATTERBOX
    if tts_hook is None:
        if name == ENGINE_CHATTERBOX:
            clone_miss = preflight_clone()
            if clone_miss:
                return [], rate, clone_miss
        elif name == ENGINE_QWEN3TTS:
            qwen_miss = preflight_qwen3()
            if qwen_miss:
                return [], rate, qwen_miss
    refs = _extract_refs(samples, rate, turns, dest / "speakers")
    lang = language_code(payload.get("target_language") or "es")
    src_lang = str(payload.get("source_language") or "en")
    tgt_lang = str(payload.get("target_language") or "es")
    cross_lang = not _same_language(src_lang, tgt_lang)
    clones: list[dict[str, Any]] = []
    render_dir = dest / "render"
    render_dir.mkdir(parents=True, exist_ok=True)
    flags: list[str] = []
    had_spoken = False
    cloned = False
    cloned_n = 0
    last_err = ""
    retry_cfg = clone_cfg_retry(cfg)

    def _prep_clone(raw_pcm: list[float], raw_sr: int, text: str) -> list[float]:
        """Resample to mix rate and crop a hallucination tail.

        Args:
            raw_pcm: Clone PCM.
            raw_sr: Clone sample rate.
            text: Target line (duration prior).

        Returns:
            Mix-rate PCM.
        """
        out = raw_pcm
        if raw_sr != rate:
            out = resample_linear(
                out, int(round(len(out) * rate / max(raw_sr, 1)))
            )
        return crop_hallucination_tail(out, rate, text)

    _log(f"render {len(turns)} turns ({name})")
    bar = _progress(max(len(turns), 1))
    for i, turn in enumerate(turns):
        nxt_t0 = turns[i + 1]["t0"] if i + 1 < len(turns) else (len(samples) / max(rate, 1))
        spill = max(0.0, float(nxt_t0) - float(turn["t1"]))
        spoken = _spoken_clone_text(turn, payload)
        ref = refs.get(str(turn["speaker"]))
        if bar is not None:
            bar.update(1)
        if not spoken:
            continue
        _log(f"TTS {i + 1}/{len(turns)} {turn.get('speaker')}")
        had_spoken = True
        pcm, sr, err = synthesize_turn(
            spoken,
            lang,
            str(ref) if ref else "",
            engine if engine in ENGINES else ENGINE_CHATTERBOX,
            exaggeration=exag,
            cfg_weight=cfg,
            ref_text=_speaker_ref_text(ref) if ref else "",
        )
        if not pcm:
            flags.append(f"turn {turn['id']} clone missing")
            if err:
                last_err = err
            continue
        pcm = _prep_clone(pcm, sr, spoken)
        write_wav(render_dir / f"turn_{int(turn['id']):04d}.raw.wav", pcm, rate)
        if not is_speech_like(pcm, rate):
            used_retry = False
            if retry_cfg is not None:
                pcm2, sr2, err2 = synthesize_turn(
                    spoken,
                    lang,
                    str(ref) if ref else "",
                    engine if engine in ENGINES else ENGINE_CHATTERBOX,
                    exaggeration=exag,
                    cfg_weight=retry_cfg,
                    ref_text=_speaker_ref_text(ref) if ref else "",
                )
                if err2:
                    last_err = err2
                if pcm2:
                    pcm2 = _prep_clone(pcm2, sr2, spoken)
                    write_wav(
                        render_dir / f"turn_{int(turn['id']):04d}.raw.wav",
                        pcm2,
                        rate,
                    )
                    if is_speech_like(pcm2, rate):
                        pcm = pcm2
                        used_retry = True
            if not used_retry:
                flags.append(f"turn {turn['id']} clone unvoiced")
                continue
        cloned = True
        cloned_n += 1
        src_chunk = _slice_pcm(samples, rate, float(turn["t0"]), float(turn["t1"]))
        pcm = match_rms(pcm, rms(src_chunk))
        cap = fit_speed_cap(pace)
        fitted, meta = fit_turn(
            pcm,
            rate,
            float(turn["t1"]) - float(turn["t0"]),
            spill_s=spill,
            max_speed=cap,
        )
        if meta.get("trimmed"):
            flags.append(f"turn {turn['id']} trimmed")
        write_wav(render_dir / f"turn_{int(turn['id']):04d}.wav", fitted, rate)
        clones.append({"t0": turn["t0"], "pcm": fitted})
    (dest / f"ez_dub.{src_lang}.srt").write_text(
        turns_to_srt(turns, field="text"), encoding="utf-8"
    )
    (dest / f"ez_dub.{tgt_lang}.srt").write_text(
        turns_to_srt(turns, field="text_target"), encoding="utf-8"
    )
    (dest / "ez_dub.disclosure.txt").write_text(
        disclosure_for(lang) + "\n", encoding="utf-8"
    )
    (dest / "ez_dub.disclosure.en.txt").write_text(
        DISCLOSURE_TEXT + "\n", encoding="utf-8"
    )
    write_json(dest / "translation.json", payload)
    if not had_spoken:
        has_source = any(str(t.get("text") or "").strip() for t in turns)
        if cross_lang and has_source:
            status = NO_TARGET_STATUS
        else:
            status = "no spoken text — ASR produced empty turns"
        return _empty_render(dest, rate, status, flags)
    unvoiced_only = (not cloned) and any("unvoiced" in f for f in flags)
    if not cloned and not unvoiced_only:
        status = last_err or CLONE_MISSING_STATUS
        flags.append(status)
        return _empty_render(dest, rate, status, flags)
    if not cloned and unvoiced_only and cross_lang:
        status = CLONE_UNVOICED_STATUS
        flags.append(status)
        _write_render_qc(
            dest,
            [],
            rate,
            turns,
            lang,
            flags,
            extra_qc=["clone_unvoiced", "mix_not_speech"],
            peak=0.0,
        )
        save_state(
            dest,
            {
                "slug": dest.name,
                "stage": "export",
                "status": status,
                "error": None,
                "flags": flags,
            },
        )
        return [], rate, status
    mix = build_timeline(samples, clones, rate, keep_bed=keep_bed)
    room = collect_room_tone(samples, turns, rate)
    mix, lock_flags = lock_duration(mix, len(samples), room=room, rate=rate)
    if not is_speech_like(mix, rate):
        status = CLONE_UNVOICED_STATUS
        flags.append(status)
        extra_qc = ["mix_not_speech"]
        if any("unvoiced" in f for f in flags):
            extra_qc.append("clone_unvoiced")
        peak_raw = max((abs(float(x)) for x in mix), default=0.0)
        _write_render_qc(
            dest, mix, rate, turns, lang, flags, extra_qc=extra_qc, peak=peak_raw
        )
        save_state(
            dest,
            {
                "slug": dest.name,
                "stage": "export",
                "status": status,
                "error": None,
                "flags": flags,
            },
        )
        return [], rate, status
    mix = raise_to_peak(mix)
    write_wav(dest / "ez_dub_yt.wav", mix, rate)
    mix = _maybe_loudnorm_yt(dest, mix, rate, len(samples), room)
    _maybe_yt_mp3_48k(dest)
    mix_wav = mix
    if spoken_disclosure:
        first_ref = ""
        if turns:
            spk = str(turns[0].get("speaker") or "")
            ref = refs.get(spk) if spk else None
            if ref:
                first_ref = str(ref)
            elif refs:
                first_ref = str(next(iter(refs.values())))
        mix_wav, disc_status = apply_spoken_disclosure(
            list(mix),
            rate,
            language=lang,
            engine=name,
            ref_wav=first_ref,
            turns=turns,
            synthesize=synthesize_turn,
        )
        flags.append(disc_status)
    else:
        mix_wav = strip_leading_silence(mix, rate)
    write_wav(dest / "ez_dub_mix.wav", mix_wav, rate)
    peak = max((abs(float(x)) for x in mix), default=0.0)
    flags.append(f"peak={peak:.2f}")
    if peak < 0.25:
        flags.append("quiet mix")
    qc_extra: list[str] = []
    if any(" trimmed" in f or f.endswith(" trimmed") for f in flags):
        qc_extra.append("trimmed_clone")
    if any("unvoiced" in f for f in flags):
        qc_extra.append("clone_unvoiced")
    _write_render_qc(
        dest, mix, rate, turns, lang, flags, extra_qc=qc_extra, peak=peak
    )
    status = f"{len(refs)} speakers, {cloned_n} turns cloned"
    if lock_flags.get("trimmed"):
        flags.append("duration trimmed")
    if flags:
        status = status + "; " + "; ".join(flags)
    save_state(
        dest,
        {
            "slug": dest.name,
            "stage": "export",
            "status": status,
            "error": None,
            "flags": flags,
        },
    )
    return mix_wav, rate, status


def _spoken_clone_text(turn: Mapping[str, Any], payload: Mapping[str, Any]) -> str:
    """Target-language line for clone. Never fall back to source on a cross-language job.

    Args:
        turn: JSON turn mapping.
        payload: JSON script mapping.

    Returns:
        Clone text, or ``""`` when cross-lang ``text_target`` is empty.
    """
    target = str(turn.get("text_target") or "").strip()
    if target:
        return target
    src = language_code(payload.get("source_language") or "")
    tgt = language_code(payload.get("target_language") or "es")
    if _same_language(src, tgt):
        return str(turn.get("text") or "").strip()
    return ""


def _fail_analyze(
    dest: Path,
    *,
    target_language: str,
    source_language: str,
    stage: str,
    reason: str,
) -> tuple[ScriptPayload, str]:
    """Persist an empty translation payload and a blocking Dub status.

    Args:
        dest: Job directory.
        target_language: ISO target.
        source_language: ISO source or ``auto``.
        stage: Widget stage.
        reason: Blocking Dub status.

    Returns:
        ``(empty_payload, reason)``.
    """
    payload = empty_payload(
        target_language=target_language,
        source_language=source_language,
        stage=stage,
        status=reason,
    )
    write_json(dest / "turns.json", [])
    write_json(dest / "translation.json", payload)
    save_state(
        dest,
        {
            "slug": dest.name,
            "stage": "translate",
            "status": reason,
            "source_language": source_language,
            "target_language": target_language,
            "error": None,
            "flags": [],
        },
    )
    return payload, reason


def missing_source_status(dest: Path) -> str:
    """Operator-facing reason when ``source.wav`` is absent.

    Args:
        dest: Job directory that may contain ``state.json`` from a failed ingest.

    Returns:
        Persisted ingest error/status, or :data:`MISSING_SOURCE_STATUS`.
    """
    state = load_state(dest)
    status = str(state.get("status") or "").strip()
    error = str(state.get("error") or "").strip()
    if status and status not in _GENERIC_INGEST_STATUS:
        return status
    if error and error not in _GENERIC_INGEST_STATUS:
        return error
    return MISSING_SOURCE_STATUS


def analyze_job(
    dest: Path,
    *,
    target_language: str,
    source_language: str,
    max_speakers: int,
    enhance: bool,
    stage: str,
    widget_payload: Mapping[str, Any] | None = None,
) -> tuple[ScriptPayload, str]:
    """Analyze + translate, or pin widget JSON when enhance is off / stage=render.

    Args:
        dest: Job directory.
        target_language: ISO target.
        source_language: ISO source or ``auto``.
        max_speakers: Cluster cap; 0 means default.
        enhance: When False, pin widget text.
        stage: ``all``, ``analyze``, or ``render``.
        widget_payload: Current widget JSON (JSON boundary).

    Returns:
        ``(payload, status)``.
    """
    wav = dest / "source.wav"
    name = stage if stage in STAGES else STAGE_ALL
    widget_turns = list((widget_payload or {}).get("turns") or [])
    if name == STAGE_RENDER:
        if widget_turns:
            payload = cast(ScriptPayload, dict(widget_payload or {}))
            payload["stage"] = STAGE_RENDER
            payload["target_language"] = target_language
            return payload, "pinned widget"
        payload = empty_payload(
            target_language=target_language,
            source_language=source_language,
            stage=STAGE_RENDER,
            status=NO_TURNS_STATUS,
        )
        return payload, NO_TURNS_STATUS
    if not enhance and widget_turns:
        payload = cast(ScriptPayload, dict(widget_payload or {}))
        payload["stage"] = name
        payload["target_language"] = target_language
        return payload, "enhance off"
    if not wav.is_file():
        reason = missing_source_status(dest)
        payload = empty_payload(
            target_language=target_language,
            source_language=source_language,
            stage=name,
            status=reason,
        )
        return payload, reason
    if (
        _translation_needed(enhance, source_language, target_language)
        and translate_hook is None
    ):
        miss = preflight_translate()
        if miss:
            return _fail_analyze(
                dest,
                target_language=target_language,
                source_language=source_language,
                stage=name,
                reason=miss,
            )
    if asr_hook is None:
        asr_miss = preflight_asr()
        if asr_miss:
            return _fail_analyze(
                dest,
                target_language=target_language,
                source_language=source_language,
                stage=name,
                reason=asr_miss,
            )
    samples, rate = read_wav(wav)
    turns, detected, asr_reason = analyze_pcm(
        samples,
        rate,
        max_speakers=max_speakers,
        language=source_language,
        wav_path=wav,
    )
    src = language_code(source_language)
    if src == "auto" and detected:
        src = language_code(detected)
    if asr_reason and not turns:
        return _fail_analyze(
            dest,
            target_language=target_language,
            source_language=src,
            stage=name,
            reason=asr_reason,
        )
    turns = merge_adjacent_turns(turns)
    turns, reason = translate_turns(
        turns, target_language, src, enhance=enhance
    )
    n_spk = len({str(t.get("speaker") or "") for t in turns})
    status = f"{n_spk} speakers, {len(turns)} turns"
    if reason:
        status = f"{status}; {reason}"
    payload = {
        "target_language": target_language,
        "source_language": src,
        "stage": name,
        "status": status,
        "turns": turns,
    }
    write_json(dest / "turns.json", turns)
    write_json(dest / "translation.json", payload)
    save_state(
        dest,
        {
            "slug": dest.name,
            "stage": "translate",
            "status": status,
            "source_language": source_language,
            "target_language": target_language,
            "error": None,
            "flags": [],
        },
    )
    return cast(ScriptPayload, payload), status
