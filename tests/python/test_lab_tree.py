"""Shipped lab graphs live only under workflows/_lab/<allowed_lane>/."""

from __future__ import annotations

from pathlib import Path

import pytest

from _lab_paths import (
    ALLOWED_LANES,
    LAB_ROOT,
    WF,
    lab_dest,
    lab_example_paths,
    lane_for_stem,
)

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


def test_nill_bye_graphs_live_under_audio_nill_bye_phase() -> None:
    artist = LAB_ROOT / "audio" / "nill-bye"
    audio = LAB_ROOT / "audio"
    hits = [
        path
        for path in lab_example_paths()
        if path.name.startswith("music-rap-nill-bye-")
    ]
    assert hits
    phases: set[str] = set()
    for path in hits:
        assert path.parent.parent == artist, path
        assert path.parent.name.startswith("phase"), path
        phases.add(path.parent.name)
    assert phases == {"phase0", "phase1", "phase2"}
    stray = list(artist.glob("music-rap-nill-bye-*-lab-example.json"))
    assert stray == [], stray
    stray_audio = list(audio.glob("music-rap-nill-bye-*-lab-example.json"))
    assert stray_audio == [], stray_audio


def test_drive_through_graphs_live_under_audio_drive_through_phase() -> None:
    artist = LAB_ROOT / "audio" / "drive-through"
    audio = LAB_ROOT / "audio"
    hits = [
        path
        for path in lab_example_paths()
        if path.name.startswith("music-edm-drive-through-")
    ]
    assert hits
    phases: set[str] = set()
    for path in hits:
        assert path.parent.parent == artist, path
        assert path.parent.name.startswith("phase"), path
        phases.add(path.parent.name)
    assert phases == {"phase0", "phase1", "phase2", "phase3"}
    stray = list(artist.glob("music-edm-drive-through-*-lab-example.json"))
    assert stray == [], stray
    stray_audio = list(audio.glob("music-edm-drive-through-*-lab-example.json"))
    assert stray_audio == [], stray_audio


def test_lab_dest_nested_subdir() -> None:
    path = lab_dest(
        "music-rap-nill-bye-lab-coat-lab-example.json",
        subdir="nill-bye/phase0",
    )
    assert path == (
        LAB_ROOT
        / "audio"
        / "nill-bye"
        / "phase0"
        / "music-rap-nill-bye-lab-coat-lab-example.json"
    )
    edm = lab_dest(
        "music-edm-drive-through-open-lane-lab-example.json",
        subdir="drive-through/phase0",
    )
    assert edm == (
        LAB_ROOT
        / "audio"
        / "drive-through"
        / "phase0"
        / "music-edm-drive-through-open-lane-lab-example.json"
    )


def test_lab_dest_rejects_bad_subdir() -> None:
    for bad in ("..", ".", "/abs", "foo/../bar"):
        with pytest.raises(ValueError, match="subdir"):
            lab_dest("music-rap-draft-lab-example.json", subdir=bad)
