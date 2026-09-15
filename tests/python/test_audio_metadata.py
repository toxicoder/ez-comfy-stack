"""Hermetic tests for album tags and cover-art modes."""

from __future__ import annotations

import json
import sys
import wave
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_music.metadata import (  # noqa: E402
    AudioMeta,
    album_dir_from_env,
    resolve_cover,
    sidecar_path,
    stamp_audio_file,
    write_sidecar,
)


def _silence_wav(path: Path) -> Path:
    with wave.open(str(path), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(8000)
        handle.writeframes(b"\x00\x00" * 64)
    return path


def _meta(**kwargs: object) -> AudioMeta:
    fields = {
        "artist": "Nill Bye",
        "album": "Peer Review",
        "title": "Lab Coat Lecture",
        "track": 1,
        "tracktotal": 15,
        "year": 2026,
        "art_mode": "skip",
    }
    fields.update(kwargs)
    return AudioMeta(**fields)  # type: ignore[arg-type]


def test_resolve_cover_skip_upload_generate(tmp_path: Path) -> None:
    album = tmp_path / "albums" / "Nill Bye" / "Peer Review"
    album.mkdir(parents=True)
    assert resolve_cover(art_mode="skip", upload=None, album_dir=album) is None
    upload = tmp_path / "art.png"
    upload.write_bytes(b"\x89PNG\r\n\x1a\n")
    assert resolve_cover(art_mode="upload", upload=upload, album_dir=album) == upload
    with pytest.raises(ValueError, match="upload"):
        resolve_cover(art_mode="upload", upload=None, album_dir=album)
    with pytest.raises(ValueError, match="generate"):
        resolve_cover(art_mode="generate", upload=None, album_dir=album)
    cover = album / "cover.jpg"
    cover.write_bytes(b"jpeg")
    assert resolve_cover(art_mode="generate", upload=None, album_dir=album) == cover
    with pytest.raises(ValueError, match="unknown"):
        resolve_cover(art_mode="paint", upload=None, album_dir=album)


def test_stamp_wav_writes_sidecar_and_id3(tmp_path: Path) -> None:
    wav = _silence_wav(tmp_path / "01 - Lab Coat Lecture.wav")
    cover = tmp_path / "cover.png"
    cover.write_bytes(b"\x89PNG\r\n\x1a\n")
    meta = _meta(art_mode="upload")
    sidecar = stamp_audio_file(wav, meta, cover)
    assert sidecar == sidecar_path(wav)
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    assert payload["artist"] == "Nill Bye"
    assert payload["album"] == "Peer Review"
    assert payload["title"] == "Lab Coat Lecture"
    assert payload["track"] == 1
    assert payload["cover"].endswith("cover.png")
    from mutagen.id3 import ID3

    tags = ID3(str(wav))
    assert tags["TPE1"].text[0] == "Nill Bye"
    assert tags["TALB"].text[0] == "Peer Review"
    assert tags["TIT2"].text[0] == "Lab Coat Lecture"
    assert tags["TRCK"].text[0] == "1/15"


def test_stamp_skip_has_no_picture(tmp_path: Path) -> None:
    wav = _silence_wav(tmp_path / "track.wav")
    sidecar = stamp_audio_file(wav, _meta(art_mode="skip"), None)
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    assert payload["cover"] is None
    from mutagen.id3 import ID3

    tags = ID3(str(wav))
    assert "APIC" not in tags


def test_write_sidecar_and_album_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    wav = tmp_path / "x.wav"
    wav.write_bytes(b"xxxx")
    sidecar = write_sidecar(wav, _meta(), cover=None)
    assert sidecar.is_file()
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    sys.modules.pop("folder_paths", None)
    original = Path.is_dir

    def fake_is_dir(self: Path) -> bool:
        if str(self) == "/outputs":
            return False
        return original(self)

    monkeypatch.setattr(Path, "is_dir", fake_is_dir)
    dest = album_dir_from_env("Nill Bye", "Peer Review")
    assert dest == tmp_path / "albums" / "Nill Bye" / "Peer Review"
    assert dest.is_dir()


def test_album_dir_prefers_container_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dest = tmp_path / "outputs"
    dest.mkdir()
    monkeypatch.setenv("COMFY_OUTPUT_DIR", "/mnt/comfy-output")
    sys.modules.pop("folder_paths", None)
    monkeypatch.setattr("ez_common.output_root", lambda **_k: dest)
    album = album_dir_from_env("Nill Bye", "Peer Review")
    assert album == dest / "albums" / "Nill Bye" / "Peer Review"


def test_stamp_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        stamp_audio_file(tmp_path / "missing.wav", _meta())


def test_metadata_node_stamps_matching_prefix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from ez_music.nodes import EZAudioMetadata

    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    wav = _silence_wav(tmp_path / "01 - Lab Coat Lecture.wav")
    out = EZAudioMetadata().run(
        audio={"waveform": None, "sample_rate": 8000},
        artist="Nill Bye",
        album="Peer Review",
        title="Lab Coat Lecture",
        track=1,
        tracktotal=15,
        year=2026,
        art_mode="skip",
        prefix="01 - Lab Coat Lecture",
    )
    assert "tagged" in out["ui"]["text"][0]
    dest = tmp_path / "albums" / "Nill Bye" / "Peer Review" / wav.name
    assert dest.is_file()
    assert dest.with_suffix(dest.suffix + ".meta.json").is_file()


def test_metadata_node_generate_without_cover_reports(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from ez_music.nodes import EZAudioMetadata

    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    out = EZAudioMetadata().run(
        audio={},
        artist="Nill Bye",
        album="Peer Review",
        title="Lab Coat Lecture",
        art_mode="generate",
        prefix="missing-prefix",
    )
    assert "cover" in out["ui"]["text"][0].lower()
