"""Tag FLAC/MP3/WAV with album metadata and optional cover art.

Hermetic at import: stdlib only. mutagen is lazy inside stamp_audio_file.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# AI comment, art-mode ids, and cover filenames.
AI_DISCLOSURE = (
    "AI generated audio (ACE-Step). Human rewrite required before release. "
    "Not a clone of a living artist."
)
ART_MODES = ("skip", "upload", "generate")
COVER_NAMES = ("cover.jpg", "cover.jpeg", "cover.png", "cover.webp")


@dataclass(frozen=True)
class AudioMeta:
    """Album tags written onto a master and its sidecar.

    Attributes:
        artist: Act name.
        album: Album title.
        title: Track title.
        track: One-based track number.
        tracktotal: Album track count.
        year: Release year.
        art_mode: ``skip``, ``upload``, or ``generate``.
        comment: AI-disclosure comment stamped on the file.
    """

    artist: str
    album: str
    title: str
    track: int
    tracktotal: int
    year: int
    art_mode: str = "skip"
    comment: str = AI_DISCLOSURE

    def track_label(self) -> str:
        """Format ``track/tracktotal`` for Vorbis and ID3.

        Returns:
            ``N/M`` with a minimum total of 1.
        """
        total = int(self.tracktotal) if int(self.tracktotal) > 0 else 1
        return f"{int(self.track)}/{total}"


def _log(message: str) -> None:
    """Write an ez_music status line to stderr.

    Args:
        message: Human status without a trailing newline.
    """
    print(f"[ez_music] {message}", file=sys.stderr)


def sidecar_path(audio_path: Path) -> Path:
    """JSON next to an audio master.

    Args:
        audio_path: Tagged audio file.

    Returns:
        ``<audio>.<suffix>.meta.json``.
    """
    return audio_path.with_suffix(audio_path.suffix + ".meta.json")


def write_sidecar(audio_path: Path, meta: AudioMeta, *, cover: Path | None) -> Path:
    """Write a sidecar JSON with tags and optional cover path.

    Args:
        audio_path: Tagged audio file.
        meta: Album fields.
        cover: Cover image when included.
    Returns:
        Sidecar path.
    """
    payload: dict[str, Any] = asdict(meta)
    payload["cover"] = str(cover) if cover is not None else None
    dest = sidecar_path(audio_path)
    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return dest


def resolve_cover(
    *,
    art_mode: str,
    upload: Path | None,
    album_dir: Path,
) -> Path | None:
    """Pick cover art for skip / upload / generate.

    Args:
        art_mode: ``skip``, ``upload``, or ``generate``.
        upload: Operator-supplied image (upload mode).
        album_dir: ``albums/<Artist>/<Album>`` (generate looks here).
    Returns:
        Cover path, or None when skip.
    Raises:
        ValueError: unknown mode, upload missing, or generate missing cover.
    """
    mode = (art_mode or "skip").strip().lower()
    if mode not in ART_MODES:
        raise ValueError(f"unknown album art mode {art_mode!r}")
    if mode == "skip":
        return None
    if mode == "upload":
        if upload is None or not Path(upload).is_file():
            raise ValueError("album art upload requires an image file")
        return Path(upload)
    for name in COVER_NAMES:
        candidate = album_dir / name
        if candidate.is_file():
            return candidate
    raise ValueError(
        f"album art generate needs {album_dir / 'cover.jpg'} "
        "(Queue cover.json or album-render --art generate first)"
    )


def _picture_mime(path: Path) -> str:
    """Guess a cover-art MIME type from the file suffix.

    Args:
        path: Cover image path.

    Returns:
        ``image/jpeg``, ``image/png``, or ``image/webp``.
    """
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    return "image/jpeg"


def _stamp_flac(path: Path, meta: AudioMeta, cover: Path | None) -> None:
    """Write Vorbis comments and optional picture onto a FLAC.

    Args:
        path: FLAC master.
        meta: Album fields.
        cover: Optional cover image.
    """
    from mutagen.flac import FLAC, Picture

    audio = FLAC(str(path))
    audio["artist"] = meta.artist
    audio["album"] = meta.album
    audio["title"] = meta.title
    audio["tracknumber"] = meta.track_label()
    audio["albumartist"] = meta.artist
    audio["date"] = str(meta.year)
    audio["comment"] = meta.comment
    audio.clear_pictures()
    if cover is not None:
        picture = Picture()
        picture.type = 3
        picture.mime = _picture_mime(cover)
        picture.desc = "Cover"
        picture.data = cover.read_bytes()
        audio.add_picture(picture)
    audio.save()


def _stamp_id3(path: Path, meta: AudioMeta, cover: Path | None) -> None:
    """Write ID3 frames and optional APIC onto MP3 or WAV.

    Args:
        path: MP3 or WAV master.
        meta: Album fields.
        cover: Optional cover image.
    """
    from mutagen.id3 import ID3
    from mutagen.id3._frames import APIC, COMM, TALB, TDRC, TIT2, TPE1, TPE2, TRCK
    from mutagen.id3._util import ID3NoHeaderError

    try:
        tags = ID3(str(path))
    except ID3NoHeaderError:
        tags = ID3()
    tags.delall("APIC")
    tags["TPE1"] = TPE1(encoding=3, text=meta.artist)
    tags["TPE2"] = TPE2(encoding=3, text=meta.artist)
    tags["TALB"] = TALB(encoding=3, text=meta.album)
    tags["TIT2"] = TIT2(encoding=3, text=meta.title)
    tags["TRCK"] = TRCK(encoding=3, text=meta.track_label())
    tags["TDRC"] = TDRC(encoding=3, text=str(meta.year))
    tags["COMM"] = COMM(encoding=3, lang="eng", desc="", text=meta.comment)
    if cover is not None:
        tags["APIC"] = APIC(
            encoding=3,
            mime=_picture_mime(cover),
            type=3,
            desc="Cover",
            data=cover.read_bytes(),
        )
    tags.save(str(path))


def stamp_audio_file(path: Path, meta: AudioMeta, cover: Path | None = None) -> Path:
    """Write Vorbis/ID3 tags when mutagen can parse the file.

    Args:
        path: FLAC, MP3, or WAV master.
        meta: Album fields.
        cover: Optional image (skipped when None).
    Returns:
        Sidecar path.
    Raises:
        FileNotFoundError: audio path missing.
    """
    audio = Path(path)
    if not audio.is_file():
        raise FileNotFoundError(str(audio))
    suffix = audio.suffix.lower()
    try:
        if suffix == ".flac":
            _stamp_flac(audio, meta, cover)
        elif suffix in {".mp3", ".wav"}:
            _stamp_id3(audio, meta, cover)
        else:
            _log(f"skip tags for unsupported suffix {suffix}")
    except ImportError as exc:
        _log(f"mutagen unavailable: {exc}")
    except Exception as exc:  # noqa: BLE001 — fail-soft around SaveAudio
        _log(f"tag stamp failed for {audio.name}: {exc}")
    return write_sidecar(audio, meta, cover=cover)


def album_dir_from_env(artist: str, album: str, *, output_dir: Path | None = None) -> Path:
    """``${COMFY_OUTPUT_DIR}/albums/<Artist>/<Album>``.

    Args:
        artist: Act name.
        album: Album title.
        output_dir: Override (tests).
    Returns:
        Directory path (created).
    """
    from .naming import album_output_dir

    if output_dir is None:
        try:
            from ez_common import output_root

            output_dir = output_root(default="output")
        except Exception:  # noqa: BLE001 — pytest / missing Comfy
            env = (os.environ.get("COMFY_OUTPUT_DIR") or "").strip()
            if env:
                output_dir = Path(env)
            else:
                try:
                    import folder_paths  # type: ignore[import-not-found]

                    output_dir = Path(folder_paths.get_output_directory())
                except Exception:  # noqa: BLE001 — pytest / missing Comfy
                    output_dir = Path("output")
    dest = output_dir / album_output_dir(artist, album)
    dest.mkdir(parents=True, exist_ok=True)
    return dest
