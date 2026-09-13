"""Hermetic tests for album zip + m3u packing."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_music.pack import pack_album, write_m3u  # noqa: E402
from ez_music.nodes import EZAlbumPack  # noqa: E402


def _album_dir(tmp_path: Path, *, with_cover: bool) -> Path:
    dest = tmp_path / "albums" / "Nill Bye" / "Peer Review"
    dest.mkdir(parents=True)
    (dest / "01 - Lab Coat Lecture.flac").write_bytes(b"flac")
    (dest / "01 - Lab Coat Lecture.mp3").write_bytes(b"mp3")
    (dest / "02 - Peer Review.flac").write_bytes(b"flac")
    if with_cover:
        (dest / "cover.jpg").write_bytes(b"jpeg")
    return dest


def test_pack_album_includes_cover_when_present(tmp_path: Path) -> None:
    dest = _album_dir(tmp_path, with_cover=True)
    zip_path = pack_album(dest, album="Peer Review")
    assert zip_path == dest / "Peer Review.zip"
    names = set(zipfile.ZipFile(zip_path).namelist())
    assert "01 - Lab Coat Lecture.flac" in names
    assert "01 - Lab Coat Lecture.mp3" in names
    assert "02 - Peer Review.flac" in names
    assert "cover.jpg" in names
    assert "Peer Review.m3u" in names
    m3u = (dest / "Peer Review.m3u").read_text(encoding="utf-8")
    assert "01 - Lab Coat Lecture.flac" in m3u
    assert "#EXTALB:Peer Review" in m3u


def test_pack_album_skips_cover_when_absent(tmp_path: Path) -> None:
    dest = _album_dir(tmp_path, with_cover=False)
    zip_path = pack_album(dest, album="Peer Review")
    names = set(zipfile.ZipFile(zip_path).namelist())
    assert "cover.jpg" not in names
    assert "Peer Review.m3u" in names


def test_pack_album_refuses_empty(tmp_path: Path) -> None:
    dest = tmp_path / "empty"
    dest.mkdir()
    with pytest.raises(FileNotFoundError):
        pack_album(dest, album="Peer Review")
    with pytest.raises(ValueError, match="album"):
        pack_album(dest, album="  ")
    with pytest.raises(ValueError, match="album"):
        write_m3u(dest, album="")


def test_album_pack_node_empty_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    out = EZAlbumPack().run("Nill Bye", "Peer Review")
    assert out["result"][0] == ""
    assert "no audio" in out["ui"]["text"][0]


def test_album_pack_node_zips(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    dest = tmp_path / "albums" / "Nill Bye" / "Peer Review"
    dest.mkdir(parents=True)
    (dest / "01 - Lab Coat Lecture.flac").write_bytes(b"flac")
    out = EZAlbumPack().run("Nill Bye", "Peer Review")
    assert out["result"][0].endswith("Peer Review.zip")
    assert Path(out["result"][0]).is_file()
