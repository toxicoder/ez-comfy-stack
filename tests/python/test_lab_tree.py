"""Shipped lab graphs live only under workflows/_lab/<allowed_lane>/."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from _lab_ids import OLD_TO_REL, rel_id
from _lab_paths import (
    ALLOWED_LANES,
    LANE_BY_ID,
    LANE_REGISTRY,
    LAB_ROOT,
    WF,
    cached_lab_graph_map,
    lab_dest,
    lab_graph_paths,
    lab_json,
    lane_for_stem,
    lane_meta,
    lane_specs,
    load_lab_graph,
)
from _audit_lab_graphs import audit_lab_graphs

ROOT = Path(__file__).resolve().parents[2]


def test_rel_id_maps_old_stems() -> None:
    assert rel_id("klein-still-draft-lab-example") == "stills/still-draft"
    assert rel_id("klein-still-draft-lab-example.json") == "stills/still-draft"
    assert rel_id("wan-i2v-5s-lab-example") == "motion/silent/still-to-video-5s"
    assert rel_id("ltx-i2v-5s-lab-example") == "motion/av/still-to-video-8s"
    assert rel_id("stills/still-draft") == "stills/still-draft"
    assert rel_id("audio/music/rap-draft") == "audio/music/rap-draft"
    assert len(OLD_TO_REL) >= 60


def test_lab_graph_paths_ignores_untracked_scratch() -> None:
    """Pytest must not collect BATS leftovers such as ``stills/my-hook.json``."""
    scratch = LAB_ROOT / "stills" / "ci-scratch-hook.json"
    scratch.write_text("{}\n", encoding="utf-8")
    try:
        paths = lab_graph_paths()
        assert scratch not in paths
        assert any(path.name == "still-draft.json" for path in paths)
    finally:
        scratch.unlink(missing_ok=True)


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
        extra = load_lab_graph(path).get("extra") or {}
        if extra.get("lab_rel"):
            assert extra["lab_rel"] == rel.with_suffix("").as_posix()


def test_lane_registry_is_the_one_lane_list() -> None:
    """Every browsable lane comes from LANE_REGISTRY, in a stated order."""
    assert tuple(spec.id for spec in LANE_REGISTRY) == ALLOWED_LANES
    assert [spec.id for spec in lane_specs()] == sorted(
        (spec.id for spec in LANE_REGISTRY),
        key=lambda lane: (LANE_BY_ID[lane].order, lane),
    )
    assert len({spec.id for spec in LANE_REGISTRY}) == len(LANE_REGISTRY)
    assert len({spec.order for spec in LANE_REGISTRY}) == len(LANE_REGISTRY)
    for spec in LANE_REGISTRY:
        assert spec.title.strip() == spec.title and spec.title
        assert spec.description.strip() == spec.description and spec.description
        assert spec.id == spec.id.strip().lower()
        assert "/" not in spec.id and spec.id not in {".", ".."}


def test_every_shipped_lane_is_registered() -> None:
    """A folder under ``_lab`` with no registry entry is a navigation defect."""
    lanes = {path.relative_to(LAB_ROOT).parts[0] for path in lab_graph_paths()}
    assert lanes, "no lab graphs found"
    for lane in sorted(lanes):
        assert lane_meta(lane) is not None, lane
        assert lane in ALLOWED_LANES, lane


def test_lane_meta_resolves_and_rejects_unknown() -> None:
    """The registry answers for a known lane and says nothing for a stray."""
    assert lane_meta("stills") is LANE_BY_ID["stills"]
    assert lane_meta("  stills  ") is LANE_BY_ID["stills"]
    assert lane_meta("no-such-lane") is None
    assert lane_meta("") is None


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
    assert slugs == {
        "hour-1",
        "hour-2",
        "headliner",
        "afterparty",
        "secret-homage",
        "my-coder",
    }
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
    assert lab_json("still-to-video-5s").parent.name == "silent"
    assert lab_json("still-to-video-8s").parent.name == "av"
    assert lab_json("motion/silent/still-to-video-5s").parent.name == "silent"
    assert lab_json("motion/av/still-to-video-8s").parent.name == "av"
    assert lab_json("still-draft").parent.name == "stills"
    assert lab_json("klein/still-draft").parent.name == "stills"
    assert lab_json("wan/still-to-video-5s").parent.name == "silent"


def test_cached_lab_graphs_and_auditor() -> None:
    cache = cached_lab_graph_map()
    assert len(cache) >= 8
    sample = next(iter(cache))
    assert load_lab_graph(sample) is cache[sample]
    other = cached_lab_graph_map(root=WF)
    assert len(other) >= 8
    count = audit_lab_graphs(LAB_ROOT)
    assert count == len(cache)
