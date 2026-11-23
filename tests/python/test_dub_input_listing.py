"""Dub source listing: recursive, relative, and wider than the explorer.

Hermetic: a temp input tree only, no Comfy, no ffmpeg, no network.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_dub.media import (  # noqa: E402
    INPUT_MEDIA_SUFFIXES,
    MEDIA_SUFFIXES,
    SOURCE_NONE,
    list_input_media,
    resolve_media_source,
    source_combo_options,
)


def _touch(root: Path, rel: str) -> Path:
    """Create an empty media file at ``rel`` under root, parents included."""
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"data")
    return path


def test_input_suffix_set_widens_the_explorer_set() -> None:
    """The picker takes the phone/camera formats ingest already handles."""
    for suffix in (".mov", ".m4a", ".aac", ".webm"):
        assert suffix in INPUT_MEDIA_SUFFIXES
    assert MEDIA_SUFFIXES <= INPUT_MEDIA_SUFFIXES
    # The explorer's own classification is left alone for the Outputs tab.
    assert ".mov" not in MEDIA_SUFFIXES
    assert ".aac" not in MEDIA_SUFFIXES


def test_listing_is_recursive_with_root_relative_paths(tmp_path: Path) -> None:
    """A drop the upload widget filed in a subfolder is still a pick."""
    _touch(tmp_path, "clip.mp4")
    _touch(tmp_path, "camera/A_roll.mov")
    _touch(tmp_path, "camera/deep/take.m4a")
    _touch(tmp_path, "bed.aac")
    _touch(tmp_path, "notes.txt")

    assert list_input_media(tmp_path) == [
        "bed.aac",
        "camera/A_roll.mov",
        "camera/deep/take.m4a",
        "clip.mp4",
    ]


def test_listing_skips_hidden_and_directories(tmp_path: Path) -> None:
    """Dotfiles and dot-folders stay out of the combo, as before."""
    _touch(tmp_path, "keep.wav")
    _touch(tmp_path, ".hidden.wav")
    _touch(tmp_path, ".cache/inner.wav")
    (tmp_path / "media.wav").mkdir()

    assert list_input_media(tmp_path) == ["keep.wav"]


def test_listing_sorts_case_insensitively(tmp_path: Path) -> None:
    """Case never reorders the menu a saved graph stores by name."""
    for rel in ("Bravo.mp3", "alpha.mp3", "Charlie.wav"):
        _touch(tmp_path, rel)

    assert list_input_media(tmp_path) == ["alpha.mp3", "Bravo.mp3", "Charlie.wav"]


def test_listing_of_a_missing_root_is_empty(tmp_path: Path) -> None:
    """A box with no input folder yet loads an empty menu, not an error."""
    assert list_input_media(tmp_path / "input") == []


def test_combo_offers_none_then_relative_picks(tmp_path: Path) -> None:
    """The menu keeps its empty first value and lists nested picks."""
    _touch(tmp_path, "clip.mp4")
    _touch(tmp_path, "camera/A_roll.mov")

    options = source_combo_options(tmp_path)

    assert options == [SOURCE_NONE, "camera/A_roll.mov", "clip.mp4"]


def test_subfolder_pick_resolves_again(tmp_path: Path) -> None:
    """A reload keeps a nested pick loadable, which is the whole point."""
    _touch(tmp_path, "camera/A_roll.mov")

    picked = source_combo_options(tmp_path)[1]

    assert resolve_media_source(picked, input_dir=tmp_path) == str(
        tmp_path / "camera" / "A_roll.mov"
    )
