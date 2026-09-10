"""Ingest, VAD, diarize, ASR, translate, clone, mix. Heavy deps stay lazy."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from .align import (
    SAMPLE_RATE,
    build_timeline,
    collect_room_tone,
    fit_turn,
    lock_duration,
    rms,
)
from .audio import read_wav, write_wav
from .jobstore import dub_dir, save_state, write_json
from .rights import require_rights
from .srt import turns_to_srt
from .turns import assign_overlap, empty_payload, normalize_turn

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
DISCLOSURE_TEXT = (
    "This audio is an AI-translated dub. Voices are synthesized from the "
    "original speakers with the rights-holder's authorization."
)
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

# Tests inject these. Production stays None (fail-soft).
fetch_hook: Callable[[str, Path], Path] | None = None
asr_hook: Callable[[Path, str], list[dict[str, Any]]] | None = None
embed_hook: Callable[[list[float], int], list[float]] | None = None
translate_hook: Callable[[list[dict[str, Any]], str, str], list[dict[str, Any]]] | None = (
    None
)
tts_hook: Callable[[str, str, str, str], tuple[list[float], int]] | None = None


def _log(message: str) -> None:
    print(f"[ez_dub] {message}", file=sys.stderr)


def is_url(source: object) -> bool:
    """True when the widget looks like an http(s) URL."""
    text = (source if isinstance(source, str) else str(source or "")).strip()
    lowered = text.lower()
    return lowered.startswith("http://") or lowered.startswith("https://")


def input_directory() -> Path:
    """Comfy input dir, then ``COMFY_OUTPUT_DIR/input``, then ``/inputs``.

    Returns:
        Directory path (may not exist yet).
    """
    try:
        import folder_paths  # type: ignore[import-not-found]

        path = Path(folder_paths.get_input_directory())
        if str(path):
            return path
    except Exception:  # noqa: BLE001 — Comfy is optional in unit tests
        pass
    env = (os.environ.get("COMFY_OUTPUT_DIR") or os.environ.get("COMFY_OUTPUT") or "").strip()
    if env:
        return Path(env) / "input"
    if Path("/inputs").is_dir():
        return Path("/inputs")
    return Path("input")


def list_input_media(root: Path | None = None) -> list[str]:
    """Audio and video filenames in the Comfy input folder (not recursive).

    Arguments:
        root: Override directory (tests). Default is ``input_directory()``.
    Returns:
        Sorted basenames with a media suffix. Missing dirs yield ``[]``.
    """
    folder = root if root is not None else input_directory()
    if not folder.is_dir():
        return []
    names: list[str] = []
    for entry in folder.iterdir():
        if not entry.is_file():
            continue
        if entry.name.startswith("."):
            continue
        if entry.suffix.lower() not in MEDIA_SUFFIXES:
            continue
        names.append(entry.name)
    names.sort(key=str.lower)
    return names


def source_combo_options(root: Path | None = None) -> list[str]:
    """Combo values: ``(none)`` first, then ``list_input_media``.

    Arguments:
        root: Override directory (tests).
    Returns:
        Non-empty list so the node can load with an empty input folder.
    """
    return [SOURCE_NONE, *list_input_media(root)]


def _strip_annotated_name(name: str) -> str:
    """Drop a Comfy `` [input]`` annotation from a combo value."""
    if name.endswith("]") and " [" in name:
        return name.rsplit(" [", 1)[0]
    return name


def resolve_media_source(
    source: object,
    source_url: object = "",
    *,
    input_dir: Path | None = None,
) -> str:
    """Turn App widgets into a path or URL for ``ingest``.

    Arguments:
        source: Combo basename, ``(none)``, or an existing path.
        source_url: Optional http(s) override.
        input_dir: Override input folder (tests).
    Returns:
        URL string or an existing filesystem path as a string.
    Raises:
        FileNotFoundError: empty ``(none)`` or missing file.
    """
    url = (source_url if isinstance(source_url, str) else str(source_url or "")).strip()
    if url and is_url(url):
        return url
    text = (source if isinstance(source, str) else str(source or "")).strip()
    if not text or text == SOURCE_NONE:
        raise FileNotFoundError("empty source")
    if is_url(text):
        return text
    path = Path(text).expanduser()
    if path.is_file():
        return str(path)
    folder = input_dir if input_dir is not None else input_directory()
    candidate = folder / _strip_annotated_name(text)
    if candidate.is_file():
        return str(candidate)
    try:
        import folder_paths  # type: ignore[import-not-found]

        annotated = folder_paths.get_annotated_filepath(text)
        if annotated:
            found = Path(annotated)
            if found.is_file():
                return str(found)
    except Exception:  # noqa: BLE001 — Comfy is optional in unit tests
        pass
    raise FileNotFoundError(f"source missing: {path}")


TRANSLATE_MAX_TOKENS = 512
TRANSLATE_TEMPERATURE = 0.3
TRANSLATE_TIMEOUT_S = 120
CLONE_TEXT_LIMIT = 300
CLONE_MISSING_STATUS = (
    "clone engine missing — pip install chatterbox-tts and "
    "./scripts/manage.sh download-dub --tier clone"
)
T3_MODEL_STATUS = "chatterbox-tts missing t3_model=v3 — upgrade chatterbox-tts"
NO_TURNS_STATUS = "no turns — ASR/translate did not run"
ASR_WHEEL_STATUS = "faster-whisper not installed — pip install faster-whisper"
ASR_PACK_STATUS = (
    "ASR pack missing — run ./scripts/manage.sh download-dub --tier asr"
)
CLONE_REQUIRED_FILES = (
    "ve.pt",
    "s3gen.pt",
    "grapheme_mtl_merged_expanded_v1.json",
    "t3_mtl23ls_v3.safetensors",
    "conds.pt",
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
_VOICE_ENCODER: Any = None


def language_code(code: object) -> str:
    """Map a widget value to an ISO 639-1 code (Chatterbox ``language_id``).

    Arguments:
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
    """Map a widget code to an English language name (display only)."""
    raw = language_code(code)
    if raw == "auto":
        return "the source language"
    return LANG_NAMES.get(raw, LANG_NAMES["en"])


def dub_llm_timeout_s() -> int:
    """Per-turn GGUF timeout for translation (default 120 s)."""
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

    Arguments:
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
    """Operator-facing ASR miss. Include ImportError detail when present."""
    if exc is None:
        return ASR_WHEEL_STATUS
    return f"{ASR_WHEEL_STATUS} ({exc})"


def _import_whisper_model() -> tuple[Any | None, str]:
    """Load WhisperModel or an operator-facing ImportError reason."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        return None, asr_wheel_status(exc)
    return WhisperModel, ""


def preflight_asr() -> str:
    """Empty when faster-whisper can load; otherwise an operator-facing reason."""
    _, miss = _import_whisper_model()
    if miss:
        return miss
    if not _whisper_dir():
        return ASR_PACK_STATUS
    return ""


def preflight_clone() -> str:
    """Empty when Chatterbox V3 can load; otherwise an operator-facing reason."""
    try:
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS  # noqa: F401
    except ImportError:
        return (
            "chatterbox-tts not installed — optional runtime: pip install chatterbox-tts"
        )
    if clone_ckpt_dir() is None:
        return "clone pack missing — run ./scripts/manage.sh download-dub --tier clone"
    return ""


def load_translate_prompt() -> str:
    """Writer system prompt for GGUF translation."""
    path = PROMPTS_DIR / "translate_turns.txt"
    return path.read_text(encoding="utf-8").strip()


def cosine(left: list[float], right: list[float]) -> float:
    """Cosine similarity; 0 when either vector is empty/zero."""
    n = min(len(left), len(right))
    if n == 0:
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for i in range(n):
        a = float(left[i])
        b = float(right[i])
        dot += a * b
        na += a * a
        nb += b * b
    if na <= 0.0 or nb <= 0.0:
        return 0.0
    return dot / ((na ** 0.5) * (nb ** 0.5))


def cluster_embeddings(
    vectors: list[list[float]],
    max_speakers: int = 0,
    threshold: float = 0.55,
) -> list[str]:
    """Greedy nearest-centroid clustering.

    Arguments:
        vectors: One embedding per segment.
        max_speakers: 0 means cap at 8.
        threshold: Below this, start a new speaker (until the cap).
    Returns:
        Speaker ids ``spk00``… aligned with ``vectors``.
    """
    labels: list[str] = []
    centroids: list[tuple[str, list[float], int]] = []
    cap = int(max_speakers) if int(max_speakers) > 0 else 8
    cap = max(1, cap)
    for vector in vectors:
        if not centroids:
            centroids.append(("spk00", [float(x) for x in vector], 1))
            labels.append("spk00")
            continue
        best_i = 0
        best = -1.0
        for i, (_sid, mean, _count) in enumerate(centroids):
            score = cosine(vector, mean)
            if score > best:
                best = score
                best_i = i
        if best < threshold and len(centroids) < cap:
            sid = f"spk{len(centroids):02d}"
            centroids.append((sid, [float(x) for x in vector], 1))
            labels.append(sid)
            continue
        sid, mean, count = centroids[best_i]
        new_mean = [
            (m * count + float(x)) / (count + 1) for m, x in zip(mean, vector)
        ]
        centroids[best_i] = (sid, new_mean, count + 1)
        labels.append(sid)
    return labels


def energy_vad(
    samples: list[float],
    rate: int,
    frame_ms: int = 20,
    hop_ms: int = 10,
    thresh: float = 0.02,
    min_s: float = 0.3,
    pad_s: float = 0.05,
) -> list[tuple[float, float]]:
    """Energy VAD fallback when Silero is missing.

    Returns:
        List of ``(t0, t1)`` speech spans in seconds.
    """
    sr = int(rate) or SAMPLE_RATE
    n = len(samples)
    if n == 0:
        return []
    frame = max(1, int(sr * frame_ms / 1000))
    hop = max(1, int(sr * hop_ms / 1000))
    voiced: list[bool] = []
    i = 0
    while i + frame <= n:
        chunk = samples[i : i + frame]
        voiced.append(rms(chunk) >= thresh)
        i += hop
    if not voiced:
        return []
    spans: list[tuple[float, float]] = []
    start: int | None = None
    for idx, flag in enumerate(voiced):
        if flag and start is None:
            start = idx
        if not flag and start is not None:
            spans.append((start, idx))
            start = None
    if start is not None:
        spans.append((start, len(voiced)))
    out: list[tuple[float, float]] = []
    pad = float(pad_s)
    min_len = float(min_s)
    for a, b in spans:
        t0 = max(0.0, a * hop / sr - pad)
        t1 = min(n / sr, (b * hop + frame) / sr + pad)
        if t1 - t0 >= min_len:
            out.append((t0, t1))
    return out


def _slice_pcm(samples: list[float], rate: int, t0: float, t1: float) -> list[float]:
    sr = int(rate) or SAMPLE_RATE
    a = max(0, int(round(t0 * sr)))
    b = min(len(samples), int(round(t1 * sr)))
    if b <= a:
        return []
    return [float(x) for x in samples[a:b]]


def _run(cmd: list[str]) -> tuple[int, str]:
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


def fetch_url(url: str, dest_dir: Path) -> Path:
    """Download media with yt-dlp (or a test hook).

    Arguments:
        url: http(s) URL the operator owns or is licensed to fetch.
        dest_dir: Job directory.
    Returns:
        Path to a local media file.
    Raises:
        FileNotFoundError: yt-dlp missing or download failed.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    hook = fetch_hook
    if hook is not None:
        return hook(url, dest_dir)
    out_tmpl = str(dest_dir / "download.%(ext)s")
    code, err = _run(
        [
            "yt-dlp",
            "--no-playlist",
            "-f",
            "bestaudio/best",
            "-o",
            out_tmpl,
            url,
        ]
    )
    if code != 0:
        raise FileNotFoundError(
            f"yt-dlp failed (install it for URL ingest): {err or code}"
        )
    found = sorted(dest_dir.glob("download.*"))
    if not found:
        raise FileNotFoundError("yt-dlp produced no file")
    return found[0]


def extract_audio(src: Path, dest: Path, rate: int = SAMPLE_RATE) -> None:
    """ffmpeg-extract mono 16-bit PCM to dest (never copy a WAV as-is)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    code, err = _run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-ac",
            "1",
            "-ar",
            str(int(rate) or SAMPLE_RATE),
            "-c:a",
            "pcm_s16le",
            str(dest),
        ]
    )
    if code != 0 or not dest.is_file():
        raise FileNotFoundError(f"ffmpeg extract failed: {err or src}")


def ingest(
    source: str,
    have_rights: object,
    slug: str,
    *,
    root: Path | None = None,
) -> tuple[Path, str]:
    """Rights-gated ingest of a local path or URL.

    Returns:
        ``(job_dir, status)``.
    """
    require_rights(have_rights)
    dest = dub_dir(slug, root=root)
    dest.mkdir(parents=True, exist_ok=True)
    text = (source if isinstance(source, str) else str(source or "")).strip()
    if not text:
        raise FileNotFoundError("empty source")
    if is_url(text):
        media = fetch_url(text, dest)
    else:
        media = Path(text).expanduser()
        if not media.is_file():
            raise FileNotFoundError(f"source missing: {media}")
    wav = dest / "source.wav"
    extract_audio(media, wav)
    if media.suffix.lower() in {".mp4", ".mkv", ".mov", ".webm"}:
        shutil.copy(media, dest / "source_video.mp4")
    save_state(
        dest,
        {
            "slug": dest.name,
            "stage": "ingest",
            "status": "ok",
            "source": text,
            "error": None,
            "flags": [],
        },
    )
    return dest, "ok"


def _default_embed(pcm: list[float], rate: int) -> list[float]:
    """Tiny energy/zcr fingerprint so clustering works without ONNX."""
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
    global _VOICE_ENCODER
    _VOICE_ENCODER = None


def _get_voice_encoder() -> Any | None:
    """Load Chatterbox VoiceEncoder + ve.pt once. None when the pack/wheel is missing."""
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
    """Linear resample a turn slice to the VoiceEncoder rate."""
    sr = int(rate) or SAMPLE_RATE
    if sr == dest_rate:
        return [float(x) for x in pcm]
    if not pcm or dest_rate < 1:
        return []
    out_len = max(1, int(round(len(pcm) * dest_rate / sr)))
    from .align import resample_linear

    return resample_linear(pcm, out_len)


def speaker_embed(pcm: list[float], rate: int) -> list[float]:
    """Speaker embedding from ve.pt when available; energy fingerprint otherwise."""
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
) -> tuple[list[dict[str, Any]], str, str]:
    """ASR segments become turns; cluster speakers from those slices.

    Energy VAD is not the turn source. Missing Whisper returns empty turns
    plus an operator-facing reason (never unlabeled empty-text windows).

    Returns:
        ``(turns, detected_language, reason)``.
    """
    hook = asr_hook
    detected = ""
    raw: list[dict[str, Any]] = []
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
        return [], "", "missing source.wav"
    vectors: list[list[float]] = []
    for turn in raw:
        chunk = _slice_pcm(samples, rate, float(turn["t0"]), float(turn["t1"]))
        turn["rms"] = rms(chunk)
        vectors.append(speaker_embed(chunk, rate))
    speakers = cluster_embeddings(vectors, max_speakers=max_speakers)
    for turn, speaker in zip(raw, speakers):
        turn["speaker"] = speaker
    return assign_overlap(raw), detected, ""


def _close_whisper() -> None:
    global _WHISPER, _WHISPER_DIR_CACHED
    _WHISPER = None
    _WHISPER_DIR_CACHED = ""


def _load_whisper_model(model_dir: str) -> Any:
    """Construct WhisperModel, trying CPU int8 then CUDA float16."""
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
    """Cached faster-whisper handle plus a miss reason."""
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
) -> tuple[list[dict[str, Any]], str, str]:
    """Transcribe the whole file. Turns are Whisper segments with text."""
    if not wav_path.is_file():
        return [], "", "missing source.wav"
    model, miss = _get_whisper()
    if model is None:
        _log(miss or asr_wheel_status())
        return [], "", miss or asr_wheel_status()
    try:
        lang = None if language in {"", "auto"} else language
        try:
            segments, info = model.transcribe(
                str(wav_path),
                language=lang,
                word_timestamps=False,
                vad_filter=True,
            )
        except TypeError:
            segments, info = model.transcribe(
                str(wav_path), language=lang, word_timestamps=False
            )
    except Exception as exc:  # noqa: BLE001 — fail-soft
        reason = f"faster-whisper failed: {exc}"
        _log(reason)
        return [], "", reason
    turns: list[dict[str, Any]] = []
    for i, seg in enumerate(list(segments), start=1):
        text = str(getattr(seg, "text", "") or "").strip()
        start = float(getattr(seg, "start", 0.0) or 0.0)
        end = float(getattr(seg, "end", start) or start)
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
    """First directory that has model.bin, config.json, and tokenizer.json."""
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


def _copy_source_targets(turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Copy ``text`` into empty ``text_target`` fields."""
    out: list[dict[str, Any]] = []
    for turn in turns:
        item = dict(turn)
        if not str(item.get("text_target") or "").strip():
            item["text_target"] = str(item.get("text") or "")
        out.append(item)
    return out


def _same_language(source: str, target: str) -> bool:
    src = language_code(source)
    tgt = language_code(target)
    if src in {"", "auto"}:
        return False
    return src == tgt


def _translate_user_message(text: str, source: str, target: str) -> str:
    src_name = language_name(source)
    tgt = language_code(target)
    tgt_name = language_name(tgt)
    return (
        f"/no_think\nTranslate from {src_name} to {tgt_name} ({tgt}). "
        "Output only the translated sentence.\n\n"
        f"Source: {text}"
    )


def translate_turns(
    turns: list[dict[str, Any]],
    target_language: str,
    source_language: str,
    *,
    enhance: bool = True,
) -> tuple[list[dict[str, Any]], str]:
    """Fill ``text_target`` one turn at a time. Missing GGUF copies source text."""
    tgt = language_code(target_language)
    src = language_code(source_language)
    if not enhance:
        return _copy_source_targets(turns), "enhance off"
    if _same_language(src, tgt):
        return _copy_source_targets(turns), "same language"
    hook = translate_hook
    if hook is not None:
        return hook(turns, tgt, src), ""
    spoken = [t for t in turns if str(t.get("text") or "").strip()]
    if not spoken:
        return [dict(t) for t in turns], "no turns"
    try:
        from ez_prompt_enhance.client import REASON_EMPTY
        from ez_prompt_enhance.client import REASON_GGUF_MISSING
        from ez_prompt_enhance.client import REASON_LLAMA_UNAVAILABLE
        from ez_prompt_enhance.client import _close_llm
        from ez_prompt_enhance.client import complete
    except Exception as exc:  # noqa: BLE001 — fail-soft
        _log(f"prompt enhance client unavailable: {exc}")
        return _copy_source_targets(turns), "llama.cpp unavailable"
    system = load_translate_prompt()
    timeout = dub_llm_timeout_s()
    translated = 0
    passthrough = 0
    last_reason = ""
    merged: list[dict[str, Any]] = []
    fatal = ""
    try:
        for turn in turns:
            item = dict(turn)
            source_text = str(item.get("text") or "").strip()
            if not source_text:
                item["text_target"] = str(item.get("text_target") or "")
                merged.append(item)
                continue
            if fatal:
                item["text_target"] = source_text
                passthrough += 1
                merged.append(item)
                continue
            user = _translate_user_message(source_text, src, tgt)
            rewritten, reason = complete(
                system,
                user,
                max_tokens=TRANSLATE_MAX_TOKENS,
                temperature=TRANSLATE_TEMPERATURE,
                timeout_s=timeout,
            )
            if reason in {REASON_GGUF_MISSING, REASON_LLAMA_UNAVAILABLE}:
                fatal = reason
                item["text_target"] = source_text
                passthrough += 1
                last_reason = reason
                merged.append(item)
                continue
            cleaned = (rewritten or "").strip()
            if (not cleaned or cleaned == source_text) and src != tgt:
                rewritten, reason = complete(
                    system,
                    user,
                    max_tokens=TRANSLATE_MAX_TOKENS,
                    temperature=TRANSLATE_TEMPERATURE,
                    timeout_s=timeout,
                )
                cleaned = (rewritten or "").strip()
            if not cleaned or (cleaned == source_text):
                item["text_target"] = source_text
                passthrough += 1
                last_reason = (reason or REASON_EMPTY) if not cleaned else "passthrough"
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
    if passthrough and translated:
        return merged, f"translated {translated}/{total}; {passthrough} passthrough"
    if passthrough:
        return merged, last_reason or "passthrough"
    if translated:
        return merged, f"translated {translated}/{total}"
    return merged, ""


def _extract_refs(
    samples: list[float],
    rate: int,
    turns: list[dict[str, Any]],
    dest: Path,
    max_s: float = 12.0,
) -> dict[str, Path]:
    """Concatenate the longest clean turns per speaker into a ref wav."""
    dest.mkdir(parents=True, exist_ok=True)
    by_spk: dict[str, list[dict[str, Any]]] = {}
    for turn in turns:
        if turn.get("overlap"):
            continue
        by_spk.setdefault(str(turn["speaker"]), []).append(turn)
    refs: dict[str, Path] = {}
    sr = int(rate) or SAMPLE_RATE
    budget = int(max_s * sr)
    for speaker, group in by_spk.items():
        ordered = sorted(group, key=lambda t: (t["t1"] - t["t0"]), reverse=True)
        pcm: list[float] = []
        for turn in ordered:
            pcm.extend(_slice_pcm(samples, sr, turn["t0"], turn["t1"]))
            if len(pcm) >= budget:
                break
        if not pcm:
            continue
        path = dest / f"{speaker}.wav"
        write_wav(path, pcm[:budget], sr)
        refs[speaker] = path
    return refs


def _pcm_list(wav: object) -> list[float]:
    """Flatten a TTS tensor/array/list into mono float PCM."""
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
        return [float(data)]
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
    return out


def _model_roots() -> list[str]:
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
    """True when ``from_local`` can load multilingual V3 from this directory."""
    return all((folder / name).is_file() for name in CLONE_REQUIRED_FILES)


def clone_ckpt_dir() -> Path | None:
    """First complete Chatterbox multilingual V3 snapshot (not t3-only comfy/tts)."""
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


def _from_local_multilingual(loader: Callable[..., Any], ckpt: str, device: str) -> Any:
    """Call ``from_local`` with T3 V3. Older wheels cannot load our snapshot."""
    try:
        return loader(ckpt, device=device, t3_model="v3")
    except TypeError as exc:
        raise RuntimeError(T3_MODEL_STATUS) from exc


def _close_chatterbox() -> None:
    global _CHATTERBOX, _CHATTERBOX_CKPT
    _CHATTERBOX = None
    _CHATTERBOX_CKPT = ""


def _chatterbox_device() -> str:
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
    except Exception:  # noqa: BLE001 — CPU is the safe default
        pass
    return "cpu"


def _load_chatterbox_model() -> tuple[Any | None, str]:
    """Uncached from_local. Prefer this snapshot over a mixed comfy/tts dir."""
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
        model = _from_local_multilingual(loader, str(ckpt), _chatterbox_device())
    except RuntimeError as exc:
        return None, str(exc)
    except Exception as exc:  # noqa: BLE001 — fail-soft
        return None, f"chatterbox failed: {exc}"
    return model, ""


def _get_chatterbox() -> tuple[Any | None, str]:
    """Cached Chatterbox Multilingual V3 handle."""
    global _CHATTERBOX, _CHATTERBOX_CKPT
    ckpt = clone_ckpt_dir()
    ckpt_s = str(ckpt) if ckpt is not None else ""
    if _CHATTERBOX is not None and _CHATTERBOX_CKPT == ckpt_s and ckpt_s:
        return _CHATTERBOX, ""
    model, err = _load_chatterbox_model()
    if model is None:
        _CHATTERBOX = None
        _CHATTERBOX_CKPT = ""
        return None, err
    _CHATTERBOX = model
    _CHATTERBOX_CKPT = ckpt_s
    return model, ""


def _try_chatterbox(
    text: str, language_id: str, ref_wav: str
) -> tuple[list[float], int, str]:
    """Lazy Chatterbox Multilingual generate. Empty PCM plus a reason on miss."""
    model, err = _get_chatterbox()
    if model is None:
        return [], SAMPLE_RATE, err or CLONE_MISSING_STATUS
    generate = getattr(model, "generate", None)
    if not callable(generate):
        return [], SAMPLE_RATE, "chatterbox missing generate"
    kwargs: dict[str, Any] = {"language_id": language_id}
    ref = (ref_wav or "").strip()
    if ref and Path(ref).is_file():
        kwargs["audio_prompt_path"] = ref
    try:
        wav = generate(text, **kwargs)
        pcm = _pcm_list(wav)
        rate = int(getattr(model, "sr", SAMPLE_RATE) or SAMPLE_RATE)
    except Exception as exc:  # noqa: BLE001 — fail-soft
        return [], SAMPLE_RATE, f"chatterbox failed: {exc}"
    if not pcm:
        return [], rate, "chatterbox returned empty audio"
    return pcm, rate, ""


def _bind_generate(module_name: str) -> Callable[[str], Any] | None:
    """Return ``model.generate`` from an optional TTS module, or None."""
    try:
        module = __import__(module_name, fromlist=["Qwen3TTS"])
        loaded = module.Qwen3TTS.from_pretrained()
        method = getattr(loaded, "generate", None)
    except Exception:  # noqa: BLE001 — optional runtime
        return None
    if not callable(method):
        return None
    return method


def _try_qwen3tts(
    text: str, language_id: str, ref_wav: str
) -> tuple[list[float], int, str]:
    """Lazy Qwen3-TTS generate. Empty PCM plus a reason on miss."""
    del language_id, ref_wav
    generate = _bind_generate("qwen_tts") or _bind_generate("qwen3_tts")
    if generate is None:
        return (
            [],
            SAMPLE_RATE,
            "qwen3tts extra not installed — download-podcast --tier qwen3tts",
        )
    try:
        wav = generate(text)
    except Exception as exc:  # noqa: BLE001 — fail-soft
        return [], SAMPLE_RATE, f"qwen3tts failed: {exc}"
    pcm = _pcm_list(wav)
    if not pcm:
        return [], SAMPLE_RATE, "qwen3tts returned empty audio"
    return pcm, SAMPLE_RATE, ""


def synthesize_turn(
    text: str,
    language: str,
    ref_wav: str,
    engine: str,
) -> tuple[list[float], int, str]:
    """Clone one line. Tests inject ``tts_hook``. ``language`` is an ISO code."""
    hook = tts_hook
    lang = language_code(language)
    chunks = split_clone_text(text)
    if not chunks:
        return [], SAMPLE_RATE, ""
    if hook is not None:
        joined: list[float] = []
        rate = SAMPLE_RATE
        for chunk in chunks:
            pcm, sr = hook(chunk, lang, ref_wav, engine)
            rate = sr or rate
            joined.extend(pcm)
        return joined, rate, ""
    name = engine if engine in ENGINES else ENGINE_CHATTERBOX
    joined_pcm: list[float] = []
    out_rate = SAMPLE_RATE
    last_err = ""
    for chunk in chunks:
        if name == ENGINE_QWEN3TTS:
            pcm, sr, err = _try_qwen3tts(chunk, lang, ref_wav)
        else:
            pcm, sr, err = _try_chatterbox(chunk, lang, ref_wav)
        if err:
            last_err = err
            _log(err)
        if not pcm:
            continue
        out_rate = sr or out_rate
        joined_pcm.extend(pcm)
    if not joined_pcm:
        return [], out_rate, last_err
    return joined_pcm, out_rate, ""


def render_mix(
    samples: list[float],
    rate: int,
    payload: dict[str, Any],
    dest: Path,
    *,
    engine: str = ENGINE_CHATTERBOX,
    keep_bed: bool = True,
    spoken_disclosure: bool = True,
    speed: float = 1.0,
) -> tuple[list[float], int, str]:
    """Clone, align, mix, write stems/SRT/disclosure.

    Returns:
        ``(mix, rate, status)``.
    """
    pace = float(speed) if speed else 1.0
    if pace < 0.5:
        pace = 0.5
    if pace > 1.5:
        pace = 1.5
    turns = list(payload.get("turns") or [])
    if not turns:
        return [], rate, NO_TURNS_STATUS
    refs = _extract_refs(samples, rate, turns, dest / "speakers")
    lang = language_code(payload.get("target_language") or "es")
    clones: list[dict[str, Any]] = []
    render_dir = dest / "render"
    render_dir.mkdir(parents=True, exist_ok=True)
    flags: list[str] = []
    had_spoken = False
    cloned = False
    cloned_n = 0
    last_err = ""
    for i, turn in enumerate(turns):
        nxt_t0 = turns[i + 1]["t0"] if i + 1 < len(turns) else (len(samples) / max(rate, 1))
        spill = max(0.0, float(nxt_t0) - float(turn["t1"]))
        spoken = str(turn.get("text_target") or turn.get("text") or "").strip()
        ref = refs.get(str(turn["speaker"]))
        if not spoken:
            continue
        had_spoken = True
        pcm, sr, err = synthesize_turn(
            spoken,
            lang,
            str(ref) if ref else "",
            engine if engine in ENGINES else ENGINE_CHATTERBOX,
        )
        if not pcm:
            flags.append(f"turn {turn['id']} clone missing")
            if err:
                last_err = err
            continue
        cloned = True
        cloned_n += 1
        if sr != rate:
            from .align import resample_linear

            pcm = resample_linear(pcm, int(round(len(pcm) * rate / max(sr, 1))))
        if pace != 1.0 and pcm:
            from .align import resample_linear

            pcm = resample_linear(pcm, max(1, int(round(len(pcm) / pace))))
        fitted, meta = fit_turn(
            pcm,
            rate,
            float(turn["t1"]) - float(turn["t0"]),
            spill_s=spill,
        )
        if meta.get("trimmed"):
            flags.append(f"turn {turn['id']} trimmed")
        write_wav(render_dir / f"turn_{int(turn['id']):04d}.wav", fitted, rate)
        clones.append({"t0": turn["t0"], "pcm": fitted})
    src_lang = str(payload.get("source_language") or "en")
    tgt_lang = str(payload.get("target_language") or "es")
    (dest / f"ez_dub.{src_lang}.srt").write_text(
        turns_to_srt(turns, field="text"), encoding="utf-8"
    )
    (dest / f"ez_dub.{tgt_lang}.srt").write_text(
        turns_to_srt(turns, field="text_target"), encoding="utf-8"
    )
    (dest / "ez_dub.disclosure.txt").write_text(DISCLOSURE_TEXT + "\n", encoding="utf-8")
    write_json(dest / "translation.json", payload)
    if not had_spoken:
        status = "no spoken text — ASR produced empty turns"
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
    if not cloned:
        status = last_err or CLONE_MISSING_STATUS
        flags.append(status)
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
    if spoken_disclosure:
        flags.append("disclosure sidecar")
    write_wav(dest / "ez_dub_mix.wav", mix, rate)
    write_wav(dest / "ez_dub_yt.wav", mix, rate)
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
    return mix, rate, status


def analyze_job(
    dest: Path,
    *,
    target_language: str,
    source_language: str,
    max_speakers: int,
    enhance: bool,
    stage: str,
    widget_payload: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], str]:
    """Analyze + translate, or pin widget JSON when enhance is off / stage=render."""
    wav = dest / "source.wav"
    name = stage if stage in STAGES else STAGE_ALL
    widget_turns = list((widget_payload or {}).get("turns") or [])
    if name == STAGE_RENDER:
        if widget_turns:
            payload = dict(widget_payload or {})
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
        payload = dict(widget_payload or {})
        payload["stage"] = name
        payload["target_language"] = target_language
        return payload, "enhance off"
    if not wav.is_file():
        payload = empty_payload(
            target_language=target_language,
            source_language=source_language,
            stage=name,
            status="missing source.wav",
        )
        return payload, "missing source.wav"
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
        payload = empty_payload(
            target_language=target_language,
            source_language=src,
            stage=name,
            status=asr_reason,
        )
        write_json(dest / "turns.json", [])
        write_json(dest / "translation.json", payload)
        save_state(
            dest,
            {
                "slug": dest.name,
                "stage": "translate",
                "status": asr_reason,
                "source_language": source_language,
                "target_language": target_language,
                "error": None,
                "flags": [],
            },
        )
        return payload, asr_reason
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
    return payload, status
