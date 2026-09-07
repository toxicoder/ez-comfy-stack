"""Hermetic tests for camera/foley enums and shot cards."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "custom_nodes"))

from ez_film.prompt_enums import (  # noqa: E402
    CAMERAS,
    shot_card,
    validate_camera,
    validate_foley,
)


def test_camera_and_foley_canonical() -> None:
    assert validate_camera(" Dolly In ") == "dolly in"
    assert validate_foley("Room  Tone") == "room tone"
    assert "fixed camera" in CAMERAS
    card = shot_card("12", camera="tracking", foley="glyph chime")
    assert card["id"] == "12"
    assert card["camera"] == "tracking"
    assert card["foley"] == "glyph chime"


def test_unknown_camera_fails() -> None:
    with pytest.raises(ValueError, match="unknown camera"):
        validate_camera("crash zoom")
    with pytest.raises(ValueError, match="unknown foley"):
        validate_foley("orchestra swell")
