"""Zip an album output folder and write an M3U playlist."""

from __future__ import annotations

import zipfile
from pathlib import Path

from .metadata import COVER_NAMES

AUDIO_SUFFIXES = (".flac", ".mp3", ".wav")


def _audio_files(album_dir: Path) -> list[Path]:
    files: list[Path] = []
    for suffix in AUDIO_SUFFIXES:
        files.extend(sorted(album_dir.glob(f"*{suffix}")))
    return [path for path in files if path.is_file()]


def write_m3u(album_dir: Path, *, album: str) -> Path:
    """Write ``<Album>.m3u`` listing audio in track order.

    Arguments:
        album_dir: Folder with numbered masters.
        album: Playlist title (also the filename stem).
    Returns:
        M3U path.
    Raises:
        ValueError: empty album title.
        FileNotFoundError: album_dir missing.
    """
    title = album.strip()
    if title == "":
        raise ValueError("album is empty")
    if not album_dir.is_dir():
        raise FileNotFoundError(str(album_dir))
    dest = album_dir / f"{title}.m3u"
    lines = ["#EXTM3U", f"#EXTALB:{title}"]
    for path in _audio_files(album_dir):
        lines.append(path.name)
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dest


def pack_album(album_dir: Path, *, album: str) -> Path:
    """Zip audio, optional cover, sidecar JSON, and M3U.

    Arguments:
        album_dir: ``albums/<Artist>/<Album>``.
        album: Album title (zip stem).
    Returns:
        Zip path inside ``album_dir``.
    Raises:
        FileNotFoundError: no audio in the folder.
        ValueError: empty album title.
    """
    title = album.strip()
    if title == "":
        raise ValueError("album is empty")
    audio = _audio_files(album_dir)
    if not audio:
        raise FileNotFoundError(f"no audio in {album_dir}")
    m3u = write_m3u(album_dir, album=title)
    zip_path = album_dir / f"{title}.zip"
    members: list[Path] = list(audio)
    members.append(m3u)
    for name in COVER_NAMES:
        cover = album_dir / name
        if cover.is_file():
            members.append(cover)
    for sidecar in sorted(album_dir.glob("*.meta.json")):
        members.append(sidecar)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for member in members:
            zf.write(member, arcname=member.name)
    return zip_path
