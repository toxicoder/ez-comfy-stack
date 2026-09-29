"""Hermetic tests for the ez_music fs helpers (output dir, suffixes, JSON)."""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_music import fs  # noqa: E402
from ez_music.fs import AUDIO_SUFFIXES, FLAC_SUFFIXES, ID3_SUFFIXES, output_dir, write_json


def test_suffix_tuples_compose_the_pack_constant() -> None:
    assert AUDIO_SUFFIXES == (".flac", ".mp3", ".wav")
    assert FLAC_SUFFIXES + ID3_SUFFIXES == AUDIO_SUFFIXES


def test_output_dir_prefers_shared_ez_common(tmp_path: Path) -> None:
    dest = tmp_path / "shared"
    import ez_common

    original = ez_common.output_root

    def _shared(*, default: str | Path | None = None) -> Path:
        assert default == str(tmp_path)
        return dest

    ez_common.output_root = _shared  # type: ignore[assignment]
    try:
        assert output_dir(default=tmp_path) == dest
    finally:
        ez_common.output_root = original  # type: ignore[assignment]


def test_output_dir_falls_back_to_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom(*, default: str | Path | None = None) -> Path:
        raise RuntimeError("no root")

    monkeypatch.setattr("ez_common.output_root", _boom)
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path / "env-out"))
    assert output_dir(default=tmp_path) == tmp_path / "env-out"


def test_output_dir_falls_back_to_folder_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom(*, default: str | Path | None = None) -> Path:
        raise RuntimeError("no root")

    monkeypatch.setattr("ez_common.output_root", _boom)
    monkeypatch.delenv("COMFY_OUTPUT_DIR", raising=False)
    folder = types.SimpleNamespace(get_output_directory=lambda: str(tmp_path / "comfy"))
    monkeypatch.setitem(sys.modules, "folder_paths", folder)
    assert output_dir(default=tmp_path) == tmp_path / "comfy"


def test_output_dir_falls_back_to_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom(*, default: str | Path | None = None) -> Path:
        raise RuntimeError("no root")

    monkeypatch.setattr("ez_common.output_root", _boom)
    monkeypatch.delenv("COMFY_OUTPUT_DIR", raising=False)
    monkeypatch.delitem(sys.modules, "folder_paths", raising=False)
    assert output_dir(default=tmp_path / "fallback") == tmp_path / "fallback"


def test_write_json_matches_sidecar_formatting(tmp_path: Path) -> None:
    target = tmp_path / "01.wav.meta.json"
    payload = {"artist": "Nill Bye", "track": 1, "cover": None}
    returned = write_json(target, payload)
    assert returned == target
    assert target.read_text(encoding="utf-8") == json.dumps(payload, indent=2) + "\n"


def test_pack_and_metadata_share_the_fs_constant() -> None:
    from ez_music import pack
    from ez_music.metadata import album_dir_from_env

    assert pack.AUDIO_SUFFIXES is AUDIO_SUFFIXES
    assert fs.AUDIO_SUFFIXES is AUDIO_SUFFIXES
    assert callable(album_dir_from_env)


def _without_ez_common() -> tuple[str, ...]:
    """Make ``ez_common`` unimportable and drop it from ``sys.path``.

    Returns:
        The ``sys.path`` entries removed, for restoration by the caller.
    """
    sys.modules["ez_common"] = None  # type: ignore[assignment]
    removed = tuple(p for p in sys.path if Path(p).resolve() == CUSTOM.resolve())
    sys.path[:] = [p for p in sys.path if p not in removed]
    return removed


def _restore_ez_common(removed: tuple[str, ...]) -> None:
    """Undo :func:`_without_ez_common`.

    Args:
        removed: Entries previously removed from ``sys.path``.
    """
    sys.modules.pop("ez_common", None)
    for entry in removed:
        if entry not in sys.path:
            sys.path.insert(0, entry)


def test_log_falls_back_when_ez_common_missing(capsys: pytest.CaptureFixture[str]) -> None:
    import ez_music.metadata as metadata
    import ez_music.nodes as nodes

    removed = _without_ez_common()
    try:
        nodes._log("nodes fallback")
        metadata._log("metadata fallback")
    finally:
        _restore_ez_common(removed)
    err = capsys.readouterr().err
    assert "[ez_music] nodes fallback\n" in err
    assert "[ez_music] metadata fallback\n" in err


def test_log_delegates_to_shared_node_log(monkeypatch: pytest.MonkeyPatch) -> None:
    import ez_common
    import ez_music.nodes as nodes

    seen: list[tuple[str, str]] = []
    monkeypatch.setattr(
        ez_common,
        "node_log",
        lambda prefix, message: seen.append((prefix, message)),
    )
    nodes._log("delegated")
    assert seen == [("ez_music", "delegated")]


def test_path_helper_falls_back_when_ez_common_missing() -> None:
    import ez_music.nodes as nodes

    removed = _without_ez_common()
    saved = list(sys.path)
    try:
        sys.path[:] = [p for p in sys.path if Path(p).resolve() != CUSTOM.resolve()]
        nodes._ensure_lab_custom_nodes_path()
        assert Path(sys.path[0]).resolve() == CUSTOM.resolve()
    finally:
        sys.path[:] = saved
        _restore_ez_common(removed)


def test_path_helper_delegates_to_ez_common(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ez_common
    import ez_music.nodes as nodes

    seen: list[Path] = []
    monkeypatch.setattr(
        ez_common,
        "ensure_custom_nodes_path",
        lambda *, anchor=None: seen.append(Path(str(anchor))),
    )
    nodes._ensure_lab_custom_nodes_path()
    assert seen == [CUSTOM.resolve()]
