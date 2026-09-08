"""Stem mix filter graph (hermetic: no ffmpeg binary required)."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "custom_nodes"))

from ez_film import stems as st  # noqa: E402


def test_mix_filter_ducks_when_dx_present() -> None:
    ducked = st.mix_filter(has_dx=True, bed_count=2)
    assert "volume=-15.0dB" in ducked
    assert "amix=inputs=3" in ducked
    assert "loudnorm=I=-14" in ducked
    solo = st.mix_filter(has_dx=False, bed_count=1)
    assert "amix" not in solo
    assert "[0:a]loudnorm" in solo
    try:
        st.mix_filter(has_dx=False, bed_count=0)
    except ValueError:
        pass
    else:
        raise AssertionError("empty beds must fail")


def test_mix_argv_no_dx_skips_duck(tmp_path: Path) -> None:
    bg = tmp_path / "bg.wav"
    bg.write_bytes(b"x")
    dest = tmp_path / "mix.m4a"
    argv = st.mix_argv([bg], dest, has_dx=False)
    joined = " ".join(argv)
    assert "volume=-15" not in joined
    assert "loudnorm=I=-14" in joined
    dx = tmp_path / "dx.wav"
    dx.write_bytes(b"x")
    argv_dx = st.mix_argv([dx, bg], dest, has_dx=True)
    assert "volume=-15" in " ".join(argv_dx)


def test_lufs_band() -> None:
    assert st.lufs_in_band(-14.0)
    assert st.lufs_in_band(-12.1)
    assert not st.lufs_in_band(-20.0)
    assert not st.lufs_in_band(None)
    assert st.parse_lufs('{"input_i": "-13.8", "output_i": "-14.0"}') == -13.8


def test_mix_stems_fail_closed(tmp_path: Path) -> None:
    report = st.mix_stems(tmp_path / "stems" / "01", ffmpeg="/usr/bin/ffmpeg")
    assert report["ok"] is False
    dx = tmp_path / "dx.wav"
    dx.write_bytes(b"x")
    report = st.mix_stems(tmp_path / "stems" / "01", dx=dx, ffmpeg="/usr/bin/ffmpeg")
    assert any("bed" in d for d in report["defects"])


def test_mix_stems_happy_fake_ffmpeg(tmp_path: Path) -> None:
    bg = tmp_path / "bg.wav"
    dx = tmp_path / "dx.wav"
    bg.write_bytes(b"x")
    dx.write_bytes(b"x")
    dest = tmp_path / "stems" / "01"

    def fake_run(argv, **_kwargs):
        Path(argv[-1]).write_bytes(b"m4a")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    report = st.mix_stems(
        dest, dx=dx, bg=bg, ffmpeg="/usr/bin/ffmpeg", run=fake_run
    )
    assert report["ok"] is True
    assert Path(report["path"]).is_file()
    assert report["has_dx"] is True
    assert (dest / "mix.json").is_file()
