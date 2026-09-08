"""Shipped lab graphs live only under workflows/_lab/<allowed_lane>/."""

from __future__ import annotations

from pathlib import Path

from _lab_paths import ALLOWED_LANES, LAB_ROOT, WF, lab_example_paths, lane_for_stem

ROOT = Path(__file__).resolve().parents[2]


def test_every_lab_example_lives_under_allowed_lane() -> None:
    paths = lab_example_paths()
    assert len(paths) >= 8
    for path in paths:
        rel = path.relative_to(LAB_ROOT)
        lane = rel.parts[0]
        assert lane in ALLOWED_LANES, path
        assert path.name.endswith("-lab-example.json")
        assert lane_for_stem(str(rel)) == lane


def test_no_lab_example_json_outside_lab_tree() -> None:
    stray = [
        p
        for p in WF.rglob("*-lab-example.json")
        if "_lab" not in p.relative_to(WF).parts
    ]
    assert stray == [], stray


def test_shot_yaml_stays_in_workflows_shorts() -> None:
    shorts = WF / "shorts"
    for name in ("go-see.shots.yaml", "still-here.shots.yaml", "switchyard.shots.yaml"):
        assert (shorts / name).is_file(), name
    assert not list(shorts.glob("*.json"))


def test_quality_notice_not_json() -> None:
    notice = WF / "quality" / "ltx-2.5" / "NOTICE.md"
    assert notice.is_file()
    assert not list((WF / "quality").rglob("*.json"))


def test_no_workflows_apps_directory() -> None:
    assert not (WF / "apps").exists()
