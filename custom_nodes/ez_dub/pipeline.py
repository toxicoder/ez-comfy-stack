"""Ingest, VAD, diarize, ASR, translate, clone, mix. Heavy deps stay lazy."""

from __future__ import annotations

import json
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
from .turns import assign_overlap, empty_payload, normalize_turn, parse_payload

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


def language_name(code: object) -> str:
    """Map a widget code to a Chatterbox language name."""
    raw = (code if isinstance(code, str) else str(code or "en")).strip().lower()
    if raw in LANG_NAMES:
        return LANG_NAMES[raw]
    for key, name in LANG_NAMES.items():
        if raw == name.lower():
            return name
    return LANG_NAMES["en"]


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
    """Copy WAV or ffmpeg-extract mono PCM to dest."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() == ".wav" and src.is_file():
        shutil.copy(src, dest)
        return
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


def analyze_pcm(
    samples: list[float],
    rate: int,
    *,
    max_speakers: int = 0,
    language: str = "auto",
    wav_path: Path | None = None,
) -> list[dict[str, Any]]:
    """VAD + cluster + optional ASR hook."""
    spans = energy_vad(samples, rate)
    if not spans:
        return []
    vectors: list[list[float]] = []
    chunks: list[list[float]] = []
    embed = embed_hook or _default_embed
    for t0, t1 in spans:
        chunk = _slice_pcm(samples, rate, t0, t1)
        chunks.append(chunk)
        vectors.append(embed(chunk, rate))
    speakers = cluster_embeddings(vectors, max_speakers=max_speakers)
    turns: list[dict[str, Any]] = []
    for i, ((t0, t1), speaker, chunk) in enumerate(
        zip(spans, speakers, chunks), start=1
    ):
        turns.append(
            {
                "id": i,
                "speaker": speaker,
                "t0": t0,
                "t1": t1,
                "text": "",
                "text_target": "",
                "overlap": False,
                "rms": rms(chunk),
            }
        )
    turns = assign_overlap(turns)
    hook = asr_hook
    if hook is not None and wav_path is not None:
        asr_turns = hook(wav_path, language)
        if asr_turns:
            return [normalize_turn(item, i + 1) for i, item in enumerate(asr_turns)]
    if hook is None:
        _try_faster_whisper(turns, wav_path, language)
    return turns


def _try_faster_whisper(
    turns: list[dict[str, Any]], wav_path: Path | None, language: str
) -> None:
    if wav_path is None or not wav_path.is_file():
        return
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        _log(
            "faster-whisper not installed — optional runtime: pip install "
            "faster-whisper (invalidates a baked venv layer if you rebuild)"
        )
        return
    model_dir = _whisper_dir()
    try:
        model = WhisperModel(model_dir or "large-v3", device="cpu")
        lang = None if language in {"", "auto"} else language
        segments, _info = model.transcribe(str(wav_path), language=lang, word_timestamps=False)
    except Exception as exc:  # noqa: BLE001 — fail-soft
        _log(f"faster-whisper failed: {exc}")
        return
    segs = list(segments)
    for turn in turns:
        bits: list[str] = []
        for seg in segs:
            start = float(getattr(seg, "start", 0.0) or 0.0)
            end = float(getattr(seg, "end", start) or start)
            if end < turn["t0"] or start > turn["t1"]:
                continue
            bits.append(str(getattr(seg, "text", "") or "").strip())
        if bits:
            turn["text"] = " ".join(bits)


def _whisper_dir() -> str:
    for key in ("MODELS_ROOT", "MODELS_DIR"):
        root = (os.environ.get(key) or "").strip()
        if not root:
            continue
        for rel in (
            "comfy/whisper",
            "Systran__faster-whisper-large-v3_whisper",
            "Systran__faster-whisper-large-v3_asr",
        ):
            path = os.path.join(root, rel)
            if os.path.isdir(path):
                return path
    return ""


def translate_turns(
    turns: list[dict[str, Any]],
    target_language: str,
    source_language: str,
    *,
    enhance: bool = True,
) -> tuple[list[dict[str, Any]], str]:
    """Fill ``text_target``. Missing GGUF copies source text."""
    if not enhance:
        out = []
        for turn in turns:
            item = dict(turn)
            if not str(item.get("text_target") or "").strip():
                item["text_target"] = str(item.get("text") or "")
            out.append(item)
        return out, "enhance off"
    hook = translate_hook
    if hook is not None:
        return hook(turns, target_language, source_language), ""
    copied = []
    for turn in turns:
        item = dict(turn)
        if not str(item.get("text_target") or "").strip():
            item["text_target"] = str(item.get("text") or "")
        copied.append(item)
    try:
        from ez_prompt_enhance.client import _close_llm
        from ez_prompt_enhance.client import complete
    except Exception as exc:  # noqa: BLE001 — fail-soft
        _log(f"prompt enhance client unavailable: {exc}")
        return copied, "llama.cpp unavailable"
    payload = {
        "source_language": source_language,
        "target_language": target_language,
        "turns": [
            {
                "id": t["id"],
                "speaker": t["speaker"],
                "text": t.get("text") or "",
            }
            for t in turns
        ],
    }
    system = load_translate_prompt()
    try:
        rewritten, reason = complete(system, json.dumps(payload, ensure_ascii=False))
    finally:
        try:
            _close_llm()
        except Exception as exc:  # noqa: BLE001 — unload is best-effort
            _log(f"writer unload failed: {exc}")
    if not (rewritten or "").strip():
        return copied, reason or "passthrough"
    parsed = parse_payload(rewritten)
    by_id = {int(t["id"]): t for t in parsed["turns"]}
    merged = []
    for turn in turns:
        item = dict(turn)
        hit = by_id.get(int(turn["id"]))
        if hit and str(hit.get("text_target") or "").strip():
            item["text_target"] = hit["text_target"]
        elif not str(item.get("text_target") or "").strip():
            item["text_target"] = str(item.get("text") or "")
        merged.append(item)
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


def synthesize_turn(
    text: str,
    language: str,
    ref_wav: str,
    engine: str,
) -> tuple[list[float], int]:
    """Clone one line. Tests inject ``tts_hook``."""
    hook = tts_hook
    if hook is not None:
        return hook(text, language, ref_wav, engine)
    _log(
        f"{engine} extra not used without a runtime install; returning silence"
    )
    return [], SAMPLE_RATE


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
    del speed  # reserved for engine-specific TTS speed
    turns = list(payload.get("turns") or [])
    if not turns:
        return list(samples), rate, "no turns"
    refs = _extract_refs(samples, rate, turns, dest / "speakers")
    lang = language_name(payload.get("target_language") or "es")
    clones: list[dict[str, Any]] = []
    render_dir = dest / "render"
    render_dir.mkdir(parents=True, exist_ok=True)
    flags: list[str] = []
    for i, turn in enumerate(turns):
        nxt_t0 = turns[i + 1]["t0"] if i + 1 < len(turns) else (len(samples) / rate)
        spill = max(0.0, float(nxt_t0) - float(turn["t1"]))
        spoken = str(turn.get("text_target") or turn.get("text") or "").strip()
        ref = refs.get(str(turn["speaker"]))
        pcm: list[float] = []
        sr = rate
        if spoken:
            pcm, sr = synthesize_turn(
                spoken,
                lang,
                str(ref) if ref else "",
                engine if engine in ENGINES else ENGINE_CHATTERBOX,
            )
            if sr != rate and pcm:
                from .align import resample_linear

                pcm = resample_linear(pcm, int(round(len(pcm) * rate / sr)))
                sr = rate
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
    mix = build_timeline(samples, clones, rate, keep_bed=keep_bed)
    room = collect_room_tone(samples, turns, rate)
    mix, lock_flags = lock_duration(mix, len(samples), room=room, rate=rate)
    if spoken_disclosure:
        flags.append("disclosure sidecar")
    write_wav(dest / "ez_dub_mix.wav", mix, rate)
    write_wav(dest / "ez_dub_yt.wav", mix, rate)
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
    status = "ok"
    if lock_flags.get("trimmed"):
        flags.append("duration trimmed")
    if flags:
        status = "; ".join(flags)
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
    if name == STAGE_RENDER and widget_payload and widget_payload.get("turns"):
        payload = dict(widget_payload)
        payload["stage"] = STAGE_RENDER
        payload["target_language"] = target_language
        return payload, "pinned widget"
    if not enhance and widget_payload and widget_payload.get("turns"):
        payload = dict(widget_payload)
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
    turns = analyze_pcm(
        samples,
        rate,
        max_speakers=max_speakers,
        language=source_language,
        wav_path=wav,
    )
    turns, reason = translate_turns(
        turns, target_language, source_language, enhance=enhance
    )
    payload = {
        "target_language": target_language,
        "source_language": source_language,
        "stage": name,
        "status": reason,
        "turns": turns,
    }
    write_json(dest / "turns.json", turns)
    write_json(dest / "translation.json", payload)
    save_state(
        dest,
        {
            "slug": dest.name,
            "stage": "translate",
            "status": reason or "ok",
            "source_language": source_language,
            "target_language": target_language,
            "error": None,
            "flags": [],
        },
    )
    return payload, reason
