"""Clay overlay QC (hermetic: stdlib PNG + fake ffmpeg)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "lib"))
sys.path.insert(0, str(ROOT / "custom_nodes"))

import guide_pack as gp  # noqa: E402
from ez_film import overlay as ov  # noqa: E402


def test_png_size_and_blend_argv(tmp_path: Path) -> None:
    clay = tmp_path / "first.png"
    look = tmp_path / "look.png"
    gp.write_solid_png(clay, 1280, 704, (180, 180, 180))
    gp.write_solid_png(look, 1280, 704, (40, 80, 120))
    assert ov.png_size(clay) == (1280, 704)
    overlay = tmp_path / "overlay.png"
    argv = ov.blend_argv(clay, look, overlay)
    assert "blend=all_expr=" in " ".join(argv)
    assert str(clay) in argv
    assert ov.parse_psnr("n:1 average:19.2 min:10 max:40") == 19.2
    assert ov.parse_psnr("nope") is None


def test_overlay_qc_refuses_wrong_size(tmp_path: Path) -> None:
    clay = tmp_path / "first.png"
    look = tmp_path / "look.png"
    gp.write_solid_png(clay, 1280, 704, (180, 180, 180))
    gp.write_solid_png(look, 1280, 720, (40, 80, 120))
    dest = tmp_path / "guides" / "gosee" / "12"
    report = ov.overlay_qc(clay, look, dest, ffmpeg="/usr/bin/ffmpeg")
    assert report["ok"] is False
    assert any("720" in d or "size" in d for d in report["defects"])


def test_overlay_qc_missing_clay(tmp_path: Path) -> None:
    look = tmp_path / "look.png"
    gp.write_solid_png(look, 1280, 704, (40, 80, 120))
    dest = tmp_path / "out"
    report = ov.overlay_qc(tmp_path / "missing.png", look, dest, ffmpeg="/usr/bin/ffmpeg")
    assert report["ok"] is False
    assert any("missing clay" in d for d in report["defects"])


def test_overlay_qc_happy_fake_ffmpeg(tmp_path: Path) -> None:
    clay = tmp_path / "first.png"
    look = tmp_path / "look.png"
    gp.write_solid_png(clay, 1280, 704, (180, 180, 180))
    gp.write_solid_png(look, 1280, 704, (40, 80, 120))
    dest = tmp_path / "guides" / "gosee" / "12"

    def fake_run(argv, **_kwargs):
        joined = " ".join(argv)
        if "blend=" in joined:
            Path(argv[-1]).write_bytes(clay.read_bytes())
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(
            returncode=0, stdout="", stderr="n:1 average:21.5 min:10 max:40\n"
        )

    report = ov.overlay_qc(
        clay, look, dest, ffmpeg="/usr/bin/ffmpeg", run=fake_run
    )
    assert report["ok"] is True
    assert report["score"] == 21.5
    assert Path(report["overlay"]).is_file()
    saved = json.loads((dest / "score.json").read_text(encoding="utf-8"))
    assert saved["ok"] is True


def test_overlay_cli_missing_ffmpeg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    clay = tmp_path / "first.png"
    look = tmp_path / "look.png"
    gp.write_solid_png(clay, 1280, 704, (180, 180, 180))
    gp.write_solid_png(look, 1280, 704, (40, 80, 120))
    monkeypatch.setattr(ov, "find_ffmpeg", lambda: None)
    assert ov._cli(["--clay", str(clay), "--look", str(look), "--dest", str(tmp_path)]) == 1  # noqa: SLF001
