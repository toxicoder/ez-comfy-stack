"""Cheap, bounded metadata probes for one Outputs sidebar row.

Hermetic: stdlib only, and Comfy is optional. Still dimensions and ComfyUI's
embedded prompt come from the file header; video and audio use ``ffprobe`` only
when ``shutil.which`` finds it, always under a hard timeout. A probe is allowed
to cost a card its detail line and nothing else: every entry point returns an
empty result instead of raising, so a truncated, unreadable, or exotic file
still lists. Lines are cached by ``(path, mtime, size)`` so a refresh
re-reads nothing.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import zlib
from pathlib import Path
from typing import Mapping

from ez_common.json_value import Json, JsonMap

from .catalog import OutputRow

FFPROBE_TIMEOUT_S = 1.5
"""Hard wall-clock cap on one ``ffprobe`` call."""

HEADER_BYTES = 32768
"""Bytes read from the head of a file when parsing a header."""

TEXT_BYTES = 4194304
"""Bytes scanned for PNG text chunks (ComfyUI embeds the whole prompt graph)."""

CACHE_MAX = 400
"""Row detail lines held in memory before the oldest is dropped."""

SIDECAR_SUFFIX = ".meta.json"
"""``ez_music`` album-tag sidecar suffix (``song.flac.meta.json``)."""

LINES_MAX = 4
"""Detail lines a card may carry, so one probe cannot flood the payload."""

DUB_ROOT = "dubs"
"""Output folder that holds ``dubs/<slug>/`` dub job directories."""

MIDI_NOTE = "MIDI sequence - opens in a DAW"
"""Plain-language card line for a ``.mid``."""

MESH_NOTE = "{kind} - opens in Blender, no in-browser preview"
"""Plain-language card line for a 3D mesh."""

PROMPT_CHARS = 140
"""Longest prompt text a card line carries."""

_CACHE: dict[tuple[str, float, int], list[str]] = {}
"""``(path, mtime, size) -> detail lines``; bounded by :data:`CACHE_MAX`."""

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
"""Signature that opens every PNG; bytes 16-24 then carry the IHDR size."""

JPEG_MAGIC = b"\xff\xd8\xff"
"""Start-of-image marker that opens every JPEG."""

GIF_MAGICS = (b"GIF87a", b"GIF89a")
"""The two GIF version headers; both keep their size at bytes 6-10."""

_CHUNK_SKIP = 12
"""Chunk overhead: 4 length bytes, 4 type bytes, 4 CRC bytes."""

# ComfyUI's SaveImage writes the graph as a `prompt` chunk; the keys below are
# the ones a still's producing prompt can hide behind.
_PROMPT_CHUNKS = ("prompt", "workflow")
"""PNG text-chunk keywords a producing ComfyUI graph can sit behind."""

_SAMPLER_HINTS = ("ksampler", "sampler", "kdiffusion")
"""Lowercase class-name fragments whose node carries the seed."""

_TAG_KEYS = ("artist", "album", "title")
"""Tags that make up an audio card's credit line, in the order shown."""

_STILL_KEYS = ("source_still", "source_image", "input_image", "still", "image")
"""Sidecar keys a mesh manifest can name its source still under."""


def clear_cache() -> None:
    """Drop every cached detail line (tests and a root switch).

    Returns:
        Nothing.
    """
    _CACHE.clear()


def _read_prefix(path: Path, limit: int) -> bytes:
    """Read at most ``limit`` bytes from the head of ``path``.

    Args:
        path: File to read.
        limit: Max byte count.

    Returns:
        Bytes, or ``b""`` when the file is missing or unreadable.
    """
    try:
        with path.open("rb") as handle:
            return handle.read(limit)
    except OSError:
        return b""


def _read_json(path: Path) -> Json | None:
    """Parse one sidecar, or return ``None`` when it is absent or malformed.

    Args:
        path: Sidecar path.

    Returns:
        Parsed JSON value, or ``None``. Callers narrow it.
    """
    try:
        parsed: Json = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError):
        return None
    return parsed


def _int_from(raw: Json) -> int | None:
    """Coerce a scalar to a positive int, or ``None``.

    Args:
        raw: Value from a header, ffprobe, or a sidecar.

    Returns:
        Positive int, or ``None`` for bools, junk, and non-positive values.
    """
    if isinstance(raw, bool) or not isinstance(raw, (int, float, str)):
        return None
    try:
        value = int(float(raw))
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _float_from(raw: Json) -> float | None:
    """Coerce a scalar to a positive float, or ``None``.

    Args:
        raw: Value from a header or ffprobe.

    Returns:
        Positive float, or ``None``.
    """
    if isinstance(raw, bool) or not isinstance(raw, (int, float, str)):
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if value > 0.0 else None


def _parse_rate(raw: Json) -> float | None:
    """Parse an ffprobe frame rate (``24`` or ``24000/1001``).

    Args:
        raw: ``avg_frame_rate`` value.

    Returns:
        Frames per second, or ``None`` for a zero or unknown rate.
    """
    text = str(raw or "").strip()
    if not text or text == "0":
        return None
    if "/" in text:
        left, _, right = text.partition("/")
        top = _float_from(left)
        bottom = _float_from(right)
        if top is None or bottom is None:
            return None
        return top / bottom
    return _float_from(text)


def image_dimensions(path: Path) -> tuple[int, int] | None:
    """Return pixel dimensions parsed from the file header alone.

    Args:
        path: Still file.

    Returns:
        ``(width, height)``, or ``None`` when the header is unknown, short, or
        truncated. Never raises.
    """
    head = _read_prefix(path, HEADER_BYTES)
    if head.startswith(PNG_MAGIC):
        if len(head) < 24:
            return None
        return (
            int.from_bytes(head[16:20], "big"),
            int.from_bytes(head[20:24], "big"),
        )
    if head.startswith(JPEG_MAGIC):
        return _jpeg_dimensions(head)
    if head[:6] in GIF_MAGICS:
        if len(head) < 10:
            return None
        return (
            int.from_bytes(head[6:8], "little"),
            int.from_bytes(head[8:10], "little"),
        )
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return _webp_dimensions(head)
    return None


def _jpeg_dimensions(head: bytes) -> tuple[int, int] | None:
    """Walk JPEG segments to the first start-of-frame marker.

    Args:
        head: Head bytes of a JPEG.

    Returns:
        ``(width, height)``, or ``None`` when no SOF marker is in range.
    """
    at = 2
    total = len(head)
    while at + 9 < total:
        if head[at] != 0xFF:
            at += 1
            continue
        marker = head[at + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            at += 2
            continue
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            return (
                int.from_bytes(head[at + 7 : at + 9], "big"),
                int.from_bytes(head[at + 5 : at + 7], "big"),
            )
        span = int.from_bytes(head[at + 2 : at + 4], "big")
        if span < 2:
            return None
        at += 2 + span
    return None


def _webp_dimensions(head: bytes) -> tuple[int, int] | None:
    """Read WebP dimensions from a VP8 or VP8L chunk.

    Args:
        head: Head bytes of a WebP.

    Returns:
        ``(width, height)``, or ``None`` for a chunk this probe does not read.
    """
    fourcc = head[12:16]
    if fourcc == b"VP8 " and len(head) >= 30:
        return (
            int.from_bytes(head[26:28], "little") & 0x3FFF,
            int.from_bytes(head[28:30], "little") & 0x3FFF,
        )
    if fourcc == b"VP8L" and len(head) >= 25:
        bits = int.from_bytes(head[21:25], "little")
        return ((bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1)
    return None


def png_text_chunks(path: Path) -> dict[str, str]:
    """Return the ``keyword -> text`` map of a PNG's text chunks.

    Reads at most :data:`TEXT_BYTES`, so a huge embedded workflow costs a
    bounded read. Chunks that are truncated or not decodable are skipped.

    Args:
        path: PNG file.

    Returns:
        Decoded text chunks; empty when the file carries none.
    """
    head = _read_prefix(path, TEXT_BYTES)
    found: dict[str, str] = {}
    if not head.startswith(PNG_MAGIC):
        return found
    at = len(PNG_MAGIC)
    total = len(head)
    while at + _CHUNK_SKIP <= total:
        size = int.from_bytes(head[at : at + 4], "big")
        kind = head[at + 4 : at + 8]
        body = head[at + 8 : at + 8 + size]
        if len(body) < size:
            break
        at += _CHUNK_SKIP + size
        if kind == b"IEND":
            break
        if kind not in (b"tEXt", b"iTXt", b"zTXt"):
            continue
        decoded = _decode_text_chunk(kind, body)
        if decoded is not None:
            found[decoded[0]] = decoded[1]
    return found


def _decode_text_chunk(kind: bytes, body: bytes) -> tuple[str, str] | None:
    """Decode one PNG text chunk.

    Args:
        kind: ``tEXt``, ``iTXt``, or ``zTXt``.
        body: Chunk payload.

    Returns:
        ``(keyword, text)``, or ``None`` when the chunk is malformed, its
        deflate stream is broken, or its text is not UTF-8. A skipped chunk
        costs the card its prompt line, never the row.
    """
    keyword, _, rest = body.partition(b"\x00")
    if not keyword:
        return None
    try:
        name = keyword.decode("latin-1")
        if kind == b"tEXt":
            return (name, rest.decode("latin-1"))
        if kind == b"zTXt":
            # Byte 0 is the compression method; only deflate is defined.
            return (name, zlib.decompress(rest[1:]).decode("utf-8"))
        # iTXt: flag, method, language tag, translated keyword, then text.
        parts = rest[2:].split(b"\x00", 2)
        if len(parts) < 3:
            return None
        payload = parts[2]
        if rest[:1] == b"\x01":
            payload = zlib.decompress(payload)
        return (name, payload.decode("utf-8"))
    except (UnicodeDecodeError, zlib.error):
        return None


def prompt_metadata(chunks: Mapping[str, str]) -> tuple[str, int | None]:
    """Pull the producing prompt text and seed out of a ComfyUI graph dump.

    Args:
        chunks: Decoded PNG text chunks (see :func:`png_text_chunks`).

    Returns:
        ``(prompt, seed)``; either half is empty or ``None`` when the graph
        does not carry it. Never raises.
    """
    raw = ""
    for key in _PROMPT_CHUNKS:
        candidate = chunks.get(key)
        if isinstance(candidate, str) and candidate.strip():
            raw = candidate
            break
    if not raw:
        return ("", None)
    try:
        graph = json.loads(raw)
    except ValueError:
        return ("", None)
    if not isinstance(graph, dict):
        return ("", None)
    text = ""
    seed: int | None = None
    for node in graph.values():
        if not isinstance(node, dict):
            continue
        inputs = node.get("inputs")
        if not isinstance(inputs, dict):
            continue
        class_type = str(node.get("class_type") or "").lower()
        if seed is None and any(hint in class_type for hint in _SAMPLER_HINTS):
            seed = _int_from(inputs.get("seed"))
        if not text:
            value = inputs.get("prompt")
            if isinstance(value, str) and value.strip():
                text = " ".join(value.split())
        if text and seed is not None:
            break
    if len(text) > PROMPT_CHARS:
        text = text[: PROMPT_CHARS - 3].rstrip() + "..."
    return (text, seed)


def ffprobe_payload(path: Path) -> JsonMap | None:
    """Run ``ffprobe`` once for one file, or return ``None``.

    Args:
        path: Media file.

    Returns:
        Parsed ``ffprobe`` JSON object, or ``None`` when the binary is absent,
        the run times out, it fails, or its output is not JSON.
    """
    exe = shutil.which("ffprobe")
    if not exe:
        return None
    argv = [
        exe,
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    try:
        proc = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=FFPROBE_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if getattr(proc, "returncode", 1) != 0:
        return None
    try:
        parsed: Json = json.loads(getattr(proc, "stdout", "") or "")
    except ValueError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _streams(payload: JsonMap | None) -> list[JsonMap]:
    """Return the stream list of one ffprobe payload.

    Args:
        payload: ffprobe output or ``None``.

    Returns:
        Mapping rows only.
    """
    raw = payload.get("streams") if isinstance(payload, dict) else None
    if not isinstance(raw, list):
        return []
    rows: list[JsonMap] = [row for row in raw if isinstance(row, dict)]
    return rows


def _first_stream(streams: list[JsonMap], codec_type: str) -> JsonMap:
    """Return the first stream of one codec type.

    Args:
        streams: ffprobe stream rows.
        codec_type: ``video`` or ``audio``.

    Returns:
        The stream, or an empty dict when there is none.
    """
    for row in streams:
        if row.get("codec_type") == codec_type:
            return row
    return {}


def _duration_seconds(payload: JsonMap, stream: JsonMap) -> float | None:
    """Return the clip duration from the format or a stream.

    Args:
        payload: ffprobe output.
        stream: The stream whose duration is the fallback.

    Returns:
        Seconds, or ``None``.
    """
    fmt = payload.get("format")
    if isinstance(fmt, dict):
        value = _float_from(fmt.get("duration"))
        if value is not None:
            return value
    return _float_from(stream.get("duration"))


def _duration_text(seconds: float) -> str:
    """Format a duration for a card line.

    Args:
        seconds: Clip length.

    Returns:
        ``12.4 s`` under a minute, else ``3:02``.
    """
    if seconds < 60.0:
        return f"{seconds:.1f} s"
    whole = int(round(seconds))
    return f"{whole // 60}:{whole % 60:02d}"


def _rate_text(sample_rate: int) -> str:
    """Format a sample rate for a card line.

    Args:
        sample_rate: Hertz.

    Returns:
        ``44.1 kHz``, ``48 kHz``, or ``22050 Hz``.
    """
    if sample_rate % 1000 == 0:
        return f"{sample_rate // 1000} kHz"
    return f"{sample_rate / 1000:.1f} kHz"


def _audio_tags(path: Path, stream: JsonMap) -> str:
    """Return the ``Artist - Album - Track`` line music already stamps.

    The ``ez_music`` sidecar is tried first so the line survives without
    ``ffprobe``; ffprobe tags are the fallback.

    Args:
        path: Audio master.
        stream: ffprobe audio stream (may be empty).

    Returns:
        Card line, or ``""`` when neither source carries the tags.
    """
    sidecar = _read_json(path.with_suffix(path.suffix + SIDECAR_SUFFIX))
    tags: JsonMap = sidecar if isinstance(sidecar, dict) else {}
    if not any(str(tags.get(key) or "").strip() for key in _TAG_KEYS):
        raw = stream.get("tags")
        tags = raw if isinstance(raw, dict) else {}
    parts = [str(tags.get(key) or "").strip() for key in _TAG_KEYS]
    parts = [part for part in parts if part]
    return " - ".join(parts)


def _still_lines(path: Path) -> list[str]:
    """Card lines for a still: dimensions, then prompt and seed when present.

    Args:
        path: Image file.

    Returns:
        Zero to three lines.
    """
    lines: list[str] = []
    size = image_dimensions(path)
    if size is not None:
        lines.append(f"{size[0]} x {size[1]}")
    text, seed = prompt_metadata(png_text_chunks(path))
    if seed is not None:
        lines.append(f"seed {seed}")
    if text:
        lines.append(f'"{text}"')
    return lines


def _video_lines(path: Path) -> list[str]:
    """Card lines for a video: dimensions, duration, frame rate, audio track.

    Args:
        path: Video file.

    Returns:
        Zero to three lines.
    """
    payload = ffprobe_payload(path)
    streams = _streams(payload)
    video = _first_stream(streams, "video")
    lines: list[str] = []
    width = _int_from(video.get("width"))
    height = _int_from(video.get("height"))
    if width is not None and height is not None:
        lines.append(f"{width} x {height}")
    seconds = _duration_seconds(payload or {}, video)
    rate = _parse_rate(video.get("avg_frame_rate"))
    facts: list[str] = []
    if seconds is not None:
        facts.append(_duration_text(seconds))
    if rate is not None:
        facts.append(f"{rate:g} fps")
    if facts:
        lines.append(" at ".join(facts))
    if video:
        has_audio = bool(_first_stream(streams, "audio"))
        lines.append("audio track" if has_audio else "silent - no audio track")
    return lines


def _audio_lines(path: Path, rel: str) -> list[str]:
    """Card lines for audio, and for a dub job's master in particular.

    Args:
        path: Audio file.
        rel: Path relative to the output root.

    Returns:
        Zero to four lines.
    """
    if rel.startswith(f"{DUB_ROOT}/"):
        dub = _dub_lines(path.parent)
        if dub:
            return dub
    payload = ffprobe_payload(path)
    stream = _first_stream(_streams(payload), "audio")
    lines: list[str] = []
    seconds = _duration_seconds(payload or {}, stream)
    if seconds is not None:
        lines.append(_duration_text(seconds))
    sample_rate = _int_from(stream.get("sample_rate"))
    if sample_rate is not None:
        lines.append(_rate_text(sample_rate))
    tags = _audio_tags(path, stream)
    if tags:
        lines.append(tags)
    return lines


def _midi_lines(path: Path) -> list[str]:
    """Card lines for a MIDI file: what it is, then the track count.

    Args:
        path: ``.mid`` file.

    Returns:
        One or two lines.
    """
    lines = [MIDI_NOTE]
    head = _read_prefix(path, 14)
    if head[:4] == b"MThd" and len(head) >= 14:
        tracks = int.from_bytes(head[10:12], "big")
        if tracks > 0:
            lines.append(f"{tracks} tracks")
    return lines


def _mesh_lines(path: Path, suffix: str) -> list[str]:
    """Card lines for a 3D mesh, plus the source still a graph may stamp.

    Args:
        path: Mesh file.
        suffix: Lowercase suffix including the dot.

    Returns:
        One or two lines.
    """
    lines = [MESH_NOTE.format(kind=suffix.lstrip(".").upper() or "MESH")]
    for sidecar in (
        path.with_suffix(path.suffix + ".json"),
        path.with_suffix(".json"),
    ):
        data = _read_json(sidecar)
        if not isinstance(data, dict):
            continue
        for key in _STILL_KEYS:
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return lines + [f"from {Path(value.replace(chr(92), '/')).name}"]
    return lines


def _report_lines(path: Path) -> list[str]:
    """Card lines for a QC report: the verdict, then the rules that fired.

    Args:
        path: ``qc.json``.

    Returns:
        Zero to two lines.
    """
    data = _read_json(path)
    if not isinstance(data, dict):
        return []
    checks = data.get("checks")
    rows = [row for row in checks if isinstance(row, dict)] if isinstance(checks, list) else []
    rules = [str(row.get("rule") or "").strip() for row in rows]
    rules = [rule for rule in rules if rule]
    verdict = "QC pass" if data.get("ok") else "QC fail"
    warned = [row for row in rows if str(row.get("level") or "") == "warn"]
    if data.get("ok") and warned:
        verdict = f"QC pass - {len(warned)} warning(s)"
    if rules:
        return [verdict, "; ".join(rules[:3])]
    return [verdict]


def _language_label(code: Json) -> str:
    """Human name for one dub language widget value.

    Args:
        code: ISO code, ``auto``, or a name.

    Returns:
        English language name, ``source`` for auto/empty, or the raw code when
        the dub pack is not importable.
    """
    text = str(code or "").strip().lower()
    if not text or text == "auto":
        return "source"
    try:
        from ez_dub.pipeline import LANG_NAMES
    except Exception:  # noqa: BLE001 - ez_dub is optional in this pack
        return text
    return LANG_NAMES.get(text[:2], text)


def _dub_lines(job_dir: Path) -> list[str]:
    """Card lines for one dub job: languages, then the QC verdict.

    Args:
        job_dir: ``dubs/<slug>`` directory.

    Returns:
        One or two lines, or ``[]`` when the job carries no state.
    """
    state = _read_json(job_dir / "state.json")
    if not isinstance(state, dict):
        return []
    if "source_language" not in state and "target_language" not in state:
        return []
    source = _language_label(state.get("source_language"))
    target = _language_label(state.get("target_language"))
    lines = [f"dub: {source} -> {target}"]
    verdict = _report_lines(job_dir / "qc.json")
    if verdict:
        lines.append("dub " + verdict[0])
    return lines


def _probe_row(root: Path, path: Path, row: OutputRow) -> list[str]:
    """Dispatch one row to its kind's probe.

    Args:
        root: Output root.
        path: File path under ``root``.
        row: Catalog row.

    Returns:
        Detail lines.
    """
    kind = str(row.get("kind") or "")
    if kind == "image":
        return _still_lines(path)
    if kind == "video":
        return _video_lines(path)
    if kind == "audio":
        return _audio_lines(path, str(row.get("rel") or ""))
    if kind == "midi":
        return _midi_lines(path)
    if kind == "model3d":
        return _mesh_lines(path, str(row.get("suffix") or ".glb"))
    if kind == "report":
        return _report_lines(path)
    return []


def detail_lines(root: Path, row: OutputRow) -> list[str]:
    """Return the card lines for one row, cached by ``(path, mtime, size)``.

    A probe that raises costs the card its lines and nothing else: the row
    still lists.

    Args:
        root: Output root the row's ``rel`` is relative to.
        row: Catalog row (``rel``, ``kind``, ``suffix``, ``mtime``, ``size``).

    Returns:
        At most :data:`LINES_MAX` human lines; empty when nothing was learned.
    """
    path = Path(root) / str(row.get("rel") or "")
    key = (
        str(path),
        _float_from(row.get("mtime")) or 0.0,
        _int_from(row.get("size")) or 0,
    )
    cached = _CACHE.get(key)
    if cached is not None:
        return list(cached)
    try:
        lines = _probe_row(Path(root), path, row)[:LINES_MAX]
    except Exception:  # noqa: BLE001 - a bad probe must never break the list
        lines = []
    if len(_CACHE) >= CACHE_MAX:
        _CACHE.pop(next(iter(_CACHE)), None)
    _CACHE[key] = list(lines)
    return list(lines)
