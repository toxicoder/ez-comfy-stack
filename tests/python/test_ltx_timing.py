"""Hermetic tests for ez_film.ltx_timing."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "custom_nodes"))

from ez_film.ltx_timing import (  # noqa: E402
    DURATION_HEAD_S,
    ltx_decoded_frames,
    ltx_frames_for_duration,
    preflight_duration_s,
    snap_ltx_frames,
    validate_ltx_frames,
)


def test_five_seconds_is_121() -> None:
    assert ltx_frames_for_duration(5.00) == 121
    assert validate_ltx_frames(121) == 121


def test_snap_120_to_121_not_vae_floor() -> None:
    assert snap_ltx_frames(120) == 121
    assert snap_ltx_frames(121) == 121
    assert snap_ltx_frames(113) == 113
    assert snap_ltx_frames(97) == 97
    with pytest.raises(ValueError, match=">= 1"):
        snap_ltx_frames(0)


def test_vae_floors_illegal_120_to_113() -> None:
    assert ltx_decoded_frames(120) == 113
    assert ltx_decoded_frames(121) == 121
    assert abs(113 / 24 - 4.708333) < 1e-6
    with pytest.raises(ValueError, match=">= 1"):
        ltx_decoded_frames(0)


def test_duration_head_is_1_plus_8n_and_odd() -> None:
    expected = {5.00: 121, 8.00: 193, 10.00: 241, 12.00: 289}
    for dur in DURATION_HEAD_S:
        frames = ltx_frames_for_duration(dur)
        assert frames == expected[dur], (dur, frames)
        assert frames % 2 == 1
        assert (frames - 1) % 8 == 0
        assert preflight_duration_s(dur) == dur


def test_refuse_even_and_30s() -> None:
    with pytest.raises(ValueError, match="even"):
        validate_ltx_frames(120)
    with pytest.raises(ValueError, match="1\\+8n"):
        validate_ltx_frames(125)
    with pytest.raises(ValueError, match="30/60/90"):
        preflight_duration_s(30.0)
    with pytest.raises(ValueError):
        ltx_frames_for_duration(0)
