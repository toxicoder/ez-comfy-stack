"""Shipped lab graphs live only under workflows/_lab/<allowed_lane>/."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from _lab_ids import OLD_TO_REL, rel_id
from _lab_paths import (
    ALLOWED_LANES,
    LAB_ROOT,
    WF,
    lab_dest,
    lab_graph_paths,
    lab_json,
    lane_for_stem,
)

ROOT = Path(__file__).resolve().parents[2]


def test_rel_id_maps_old_stems() -> None:
    assert rel_id("klein-still-draft-lab-example") == "klein/still-draft"
    assert rel_id("klein-still-draft-lab-example.json") == "klein/still-draft"
    assert rel_id("wan-i2v-5s-lab-example") == "wan/i2v-5s"
    assert rel_id("ltx-i2v-5s-lab-example") == "ltx/i2v-5s"
    assert rel_id("klein/still-draft") == "klein/still-draft"
    assert rel_id("audio/music/rap-draft") == "audio/music/rap-draft"
    assert len(OLD_TO_REL) >= 60


def test_every_lab_graph_lives_under_allowed_lane() -> None:
    paths = lab_graph_paths()
    assert len(paths) >= 8
    for path in paths:
        rel = path.relative_to(LAB_ROOT)
        lane = rel.parts[0]
        assert lane in ALLOWED_LANES, path
        assert path.name.endswith(".json")
        assert not path.name.endswith("-lab-example.json")
        assert lane_for_stem(str(rel)) == lane
        extra = json.loads(path.read_text(encoding="utf-8")).get("extra") or {}
        if extra.get("lab_rel"):
            assert extra["lab_rel"] == rel.with_suffix("").as_posix()


def test_no_lab_example_suffix() -> None:
    stray = list(WF.rglob("*-lab-example.json"))
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


def test_nill_bye_graphs_live_under_audio_albums() -> None:
    albums = LAB_ROOT / "audio" / "albums" / "nill-bye"
    hits = [
        path
        for path in lab_graph_paths()
        if "nill-bye" in path.parts and path.name[:1].isdigit()
    ]
    assert hits
    slugs = {path.parent.name for path in hits}
    assert slugs == {
        "peer-review",
        "citation-needed",
        "false-drop",
        "frozen-ercot",
        "lone-star-tab",
        "thirty-four-counts",
        "pardon-flood",
        "winterize-wells",
        "duty-switch",
    }
    for path in hits:
        assert path.parent.parent == albums, path
        assert (path.parent / "album.json").is_file()
        assert (path.parent / "cover.json").is_file()
    stray = list((LAB_ROOT / "audio" / "nill-bye").rglob("*.json")) if (
        LAB_ROOT / "audio" / "nill-bye"
    ).exists() else []
    assert stray == [], stray


def test_drive_through_graphs_live_under_audio_albums() -> None:
    albums = LAB_ROOT / "audio" / "albums" / "drive-through"
    hits = [
        path
        for path in lab_graph_paths()
        if "drive-through" in path.parts and path.name[:1].isdigit()
    ]
    assert hits
    slugs = {path.parent.name for path in hits}
    assert slugs == {"hour-1", "hour-2", "headliner", "afterparty", "secret-homage"}
    for path in hits:
        assert path.parent.parent == albums, path
        assert (path.parent / "album.json").is_file()
    stray = list((LAB_ROOT / "audio" / "drive-through").rglob("*.json")) if (
        LAB_ROOT / "audio" / "drive-through"
    ).exists() else []
    assert stray == [], stray


def test_lab_dest_nested_subdir() -> None:
    path = lab_dest("01-lab-coat.json", subdir="albums/nill-bye/peer-review")
    assert path == (
        LAB_ROOT
        / "audio"
        / "albums"
        / "nill-bye"
        / "peer-review"
        / "01-lab-coat.json"
    )
    rel = lab_dest("audio/albums/drive-through/hour-1/01-night-window")
    assert rel == (
        LAB_ROOT
        / "audio"
        / "albums"
        / "drive-through"
        / "hour-1"
        / "01-night-window.json"
    )


def test_lab_dest_rejects_bad_subdir() -> None:
    for bad in ("..", ".", "/abs", "foo/../bar"):
        with pytest.raises(ValueError, match="subdir"):
            lab_dest("rap-draft.json", subdir=bad)


def test_lab_json_ambiguous_i2v() -> None:
    with pytest.raises(FileNotFoundError, match="ambiguous"):
        lab_json("i2v-5s")
    assert lab_json("wan/i2v-5s").parent.name == "wan"
    assert lab_json("ltx/i2v-5s").parent.name == "ltx"
    assert lab_json("still-draft").parent.name == "klein"
