"""Ingest: resolve local/URL media, extract mono wav, rights-gated job dir."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from .align import SAMPLE_RATE
from .jobstore import dub_dir, save_state
from .rights import require_rights

# Ingest widgets and media suffixes.
SOURCE_NONE = "(none)"
AUDIO_SUFFIXES = (".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac")
VIDEO_SUFFIXES = (".mp4", ".mkv", ".mov", ".webm")
MEDIA_SUFFIXES = AUDIO_SUFFIXES + VIDEO_SUFFIXES


def is_url(source: object) -> bool:
    """True when the widget looks like an http(s) URL.

    Args:
        source: Combo value, path, or URL.

    Returns:
        Whether ingest should fetch with yt-dlp.
    """
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

    Args:
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

    Args:
        root: Override directory (tests).
    Returns:
        Non-empty list so the node can load with an empty input folder.
    """
    return [SOURCE_NONE, *list_input_media(root)]


def _strip_annotated_name(name: str) -> str:
    """Drop a Comfy `` [input]`` annotation from a combo value.

    Args:
        name: Combo basename, possibly annotated.

    Returns:
        Basename without the `` [input]`` suffix.
    """
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

    Args:
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


def fetch_url(url: str, dest_dir: Path) -> Path:
    """Download media with yt-dlp (or a test hook).

    Args:
        url: http(s) URL the operator owns or is licensed to fetch.
        dest_dir: Job directory.
    Returns:
        Path to a local media file.
    Raises:
        FileNotFoundError: yt-dlp missing or download failed.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    from . import pipeline as _pl
    hook = _pl.fetch_hook
    if hook is not None:
        return hook(url, dest_dir)
    out_tmpl = str(dest_dir / "download.%(ext)s")
    code, err = _pl._run(
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
    """ffmpeg-extract mono 16-bit PCM to dest (never copy a WAV as-is).

    Args:
        src: Local media path.
        dest: Destination wav path.
        rate: Target sample rate.
    """
    from . import pipeline as _pl
    dest.parent.mkdir(parents=True, exist_ok=True)
    code, err = _pl._run(
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

    Args:
        source: Existing path or http(s) URL.
        have_rights: Rights attestation widget.
        slug: Job folder name.
        root: Override output root (tests).

    Returns:
        ``(job_dir, status)``.
    """
    require_rights(have_rights)
    dest = dub_dir(slug, root=root)
    dest.mkdir(parents=True, exist_ok=True)
    text = (source if isinstance(source, str) else str(source or "")).strip()
    if not text:
        raise FileNotFoundError("empty source")
    from . import pipeline as _pl

    if is_url(text):
        media = _pl.fetch_url(text, dest)
    else:
        media = Path(text).expanduser()
        if not media.is_file():
            raise FileNotFoundError(f"source missing: {media}")
    wav = dest / "source.wav"
    _pl.extract_audio(media, wav)
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
