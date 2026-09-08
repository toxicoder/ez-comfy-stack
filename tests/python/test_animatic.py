"""Film animatic from clay or held stills (hermetic fake ffmpeg)."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "lib"))
sys.path.insert(0, str(ROOT / "custom_nodes"))

import guide_pack as gp  # noqa: E402
from ez_film import animatic as an  # noqa: E402

SHORTS = ROOT / "workflows" / "shorts"


def test_shot_sources_prefer_clay(tmp_path: Path) -> None:
    yaml_text = (SHORTS / "go-see.shots.yaml").read_text(encoding="utf-8")
    from ez_film.shots import parse_shots_yaml

    parsed = parse_shots_yaml(yaml_text)
    guides = tmp_path / "guides" / "gosee"
    stills = tmp_path / "stills"
    stills.mkdir()
    for i in range(1, 19):
        sid = f"{i:02d}"
        pack = guides / sid
        pack.mkdir(parents=True)
        gp.write_solid_png(pack / "first.png", 1280, 704, (120, 120, 120))
        gp.write_solid_png(stills / f"{sid}.png", 1280, 704, (10, 10, 10))
    (guides / "01" / "clay.mp4").write_bytes(b"x")
    rows = an.shot_sources(parsed, guides, stills)
    assert rows[0]["kind"] == "clay"
    assert rows[1]["kind"] == "still"
    assert len(rows) == 18


def test_animatic_missing_sources(tmp_path: Path) -> None:
    yaml_text = (SHORTS / "go-see.shots.yaml").read_text(encoding="utf-8")
    report = an.build_animatic(
        yaml_text,
        tmp_path / "films" / "gosee",
        guides=tmp_path / "guides" / "gosee",
        ffmpeg="/usr/bin/ffmpeg",
    )
    assert report["ok"] is False
    assert any("missing" in d for d in report["defects"])


def test_animatic_happy_fake_ffmpeg(tmp_path: Path) -> None:
    yaml_text = (SHORTS / "go-see.shots.yaml").read_text(encoding="utf-8")
    guides = tmp_path / "guides" / "gosee"
    dest = tmp_path / "films" / "gosee"
    for i in range(1, 19):
        pack = guides / f"{i:02d}"
        pack.mkdir(parents=True)
        gp.write_solid_png(pack / "first.png", 1280, 704, (120, 120, 120))

    def fake_run(argv, **_kwargs):
        Path(argv[-1]).write_bytes(b"mp4")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    report = an.build_animatic(
        yaml_text,
        dest,
        guides=guides,
        ffmpeg="/usr/bin/ffmpeg",
        run=fake_run,
    )
    assert report["ok"] is True
    assert Path(report["path"]).is_file()
    concat = (dest / "publish" / "animatic.concat.txt").read_text(encoding="utf-8")
    assert "duration 5.00" in concat
    argv = an.concat_argv(dest / "publish" / "animatic.concat.txt", dest / "publish" / "animatic.mp4", 90.0)
    assert "-t" in argv
    assert "90.00" in argv
