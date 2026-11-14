"""Tests for :mod:`_retire_combo_copy`, the retired-control copy pass."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from _lab_paths import lab_graph_paths
from _retire_combo_copy import (
    CONTENT_WIDGET_TYPES,
    RETIRED_COPY,
    copy_surfaces,
    retire_all,
    retired_copy,
    retired_phrases,
    retire_combo_copy,
)

JsonMap = dict[str, Any]


def _note(text: str, node_id: int = 1) -> JsonMap:
    return {
        "id": node_id,
        "type": "Note",
        "widgets_values": [text],
        "inputs": [],
        "outputs": [],
    }


def _lyric(text: str, node_id: int = 2) -> JsonMap:
    return {
        "id": node_id,
        "type": "EZRapLyrics",
        "widgets_values": [text],
        "inputs": [],
        "outputs": [],
    }


def _graph(*nodes: JsonMap, **extra: str) -> JsonMap:
    graph: JsonMap = {
        "nodes": list(nodes),
        "links": [],
        "groups": [],
        "last_node_id": max((n["id"] for n in nodes), default=0),
        "last_link_id": 0,
    }
    if extra:
        graph["extra"] = dict(extra)
    return graph


def test_the_table_is_a_table() -> None:
    assert RETIRED_COPY
    for retired, replacement in RETIRED_COPY:
        assert retired and replacement
        assert retired != replacement
        assert retired_phrases(replacement) == ()


def test_the_combo_pairs_name_the_retired_control() -> None:
    """Copy about the retired control must stop naming it, and only that copy.

    One pair carries no ``Quality`` at all: it retires a sentence that named a
    weight the ladder refuses to write. Everything else is the control's name.
    """
    combo_pairs = [(r, n) for r, n in RETIRED_COPY if "Quality" in r]
    assert len(combo_pairs) >= len(RETIRED_COPY) - 1
    for _, replacement in combo_pairs:
        assert "Quality" not in replacement


def test_the_table_holds_no_duplicate_left_hand_side() -> None:
    lefts = [retired for retired, _ in RETIRED_COPY]
    assert len(lefts) == len(set(lefts))


def test_the_longest_sentence_is_replaced_before_its_parts() -> None:
    """The tier-table sentence must not be shredded by a shorter pair."""
    table_row = next(
        retired for retired, _ in RETIRED_COPY if "Klein 9B base." in retired
    )
    rewritten = _retire_text(table_row)
    assert "ultra" not in rewritten
    assert "max =" not in rewritten
    assert retired_phrases(rewritten) == ()


def _retire_text(text: str) -> str:
    """Run the pass's own swap over one string."""
    from _retire_combo_copy import _retire

    return _retire(text)


@pytest.mark.parametrize(("retired", "replacement"), RETIRED_COPY)
def test_each_pair_converges(retired: str, replacement: str) -> None:
    assert _retire_text(retired) == replacement
    assert retired_phrases(replacement) == ()


@pytest.mark.parametrize(("retired", "replacement"), RETIRED_COPY)
def test_the_pass_is_idempotent(retired: str, replacement: str) -> None:
    once = _retire_text(retired)
    assert _retire_text(once) == once
    assert replacement in once


def test_a_clean_string_is_returned_unchanged() -> None:
    text = "Detail does not change size. Load a still, then Queue."
    assert _retire_text(text) == text
    assert retired_phrases(text) == ()


def test_a_sentence_is_replaced_wherever_it_sits() -> None:
    text = (
        "## photos/text-swap\n\nKlein 4B lettering swap. For tiny or dense type, "
        "set Quality **High** (Klein base if `download-image --tier base` is on "
        "disk).\n\nHandoff: none."
    )
    rewritten = _retire_text(text)
    assert "Detail **Final**" in rewritten
    assert "Quality" not in rewritten
    assert rewritten.startswith("## photos/text-swap")
    assert rewritten.endswith("Handoff: none.")


def test_surfaces_cover_captions_and_both_widget_shapes() -> None:
    node: JsonMap = {
        "id": 1,
        "type": "UNETLoader",
        "title": "Image model - Quality swaps within the Klein stack",
        "title_mode": None,
        "widgets_values": ["Quality does not change size.", {"body": "Quality"}],
    }
    labels = [label for label, _ in copy_surfaces(node)]
    assert ".title" in labels
    assert ".widgets_values[0]" in labels
    assert ".widgets_values[1].body" in labels


def test_a_lyric_node_keeps_its_wording() -> None:
    text = "Same Oval photo, the million-dollar SKU, in quality we trust."
    node = _lyric(text)
    assert copy_surfaces(node) == []
    graph = _graph(node)
    assert retired_copy(graph) == []
    assert retire_combo_copy(graph) == 0
    assert graph["nodes"][0]["widgets_values"] == [text]
    assert "EZRapLyrics" in CONTENT_WIDGET_TYPES


def test_a_non_string_widget_survives_the_pass() -> None:
    node: JsonMap = {
        "id": 3,
        "type": "KSampler",
        "widgets_values": [42, "fixed", 1.0, {"sampler_name": "euler"}],
    }
    graph = _graph(node)
    assert retire_combo_copy(graph) == 0
    assert node["widgets_values"] == [42, "fixed", 1.0, {"sampler_name": "euler"}]


def test_a_missing_widget_list_is_not_invented() -> None:
    node: JsonMap = {"id": 4, "type": "EZSnapImage"}
    graph = _graph(node)
    assert copy_surfaces(node) == []
    assert retire_combo_copy(graph) == 0
    assert "widgets_values" not in node


def test_every_reported_surface_is_rewritten() -> None:
    stale = "Quality does not change size."
    graph = _graph(
        _note(f"Read me. {stale}"),
        {
            "id": 9,
            "type": "UNETLoader",
            "title": "Image model - Quality swaps within the Klein stack",
            "widgets_values": [],
        },
        lab_note=f"App note. {stale}",
        lab_description="Daily Klein 4B still; Quality swaps within the Klein stack",
    )
    before = retired_copy(graph)
    assert len(before) == 4
    assert retire_combo_copy(graph) == 4
    assert retired_copy(graph) == []
    assert "Detail" in graph["nodes"][0]["widgets_values"][0]
    assert graph["nodes"][1]["title"].endswith("Detail swaps within the Klein stack")
    assert "Detail" in graph["extra"]["lab_note"]
    assert graph["extra"]["lab_description"].startswith("Daily Klein 4B still; Detail")


def test_an_unrelated_extra_key_is_left_alone() -> None:
    graph = _graph(_note("clean"), lab_profile="Quality")
    assert retire_combo_copy(graph) == 0
    assert graph["extra"]["lab_profile"] == "Quality"


def test_a_broken_extra_value_is_skipped_not_crashed() -> None:
    graph = _graph(_note("clean"))
    graph["extra"] = {"lab_note": {"markdown": "Quality does not change size."}}
    assert retire_combo_copy(graph) == 0


def test_retire_all_writes_only_the_graph_that_changed(tmp_path: Path) -> None:
    stale = _graph(_note("Quality does not change size."))
    clean = _graph(_note("Detail does not change size."))
    dirty_dir = tmp_path / "photos"
    dirty_dir.mkdir(parents=True)
    dirty = dirty_dir / "a.json"
    clean_path = dirty_dir / "b.json"
    dirty.write_text(json.dumps(stale, indent=2) + "\n", encoding="utf-8")
    clean_path.write_text(json.dumps(clean, indent=2) + "\n", encoding="utf-8")
    dirty_bytes = dirty.read_bytes()
    clean_bytes = clean_path.read_bytes()

    assert retire_all(tmp_path) == 1

    assert dirty.read_bytes() != dirty_bytes
    assert clean_path.read_bytes() == clean_bytes
    reparsed = json.loads(dirty.read_text(encoding="utf-8"))
    assert retired_copy(reparsed) == []
    assert dirty.read_text(encoding="utf-8").endswith("}\n")


def test_retire_all_is_idempotent_over_the_catalog(tmp_path: Path) -> None:
    graph = _graph(
        _note(
            "Profile: Quality `flux3-fast` writes UNET "
            "`flux3-image-klein-int8-convrot.safetensors`, 16 steps, CFG 1.0."
        ),
        lab_note="Quality ultra/max may select opt-in Non-Commercial weights when "
        "those files are on disk (gated, not YouTube-ok).",
    )
    path = tmp_path / "g.json"
    path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    assert retire_all(tmp_path) == 2
    once = path.read_bytes()
    assert retire_all(tmp_path) == 0
    assert path.read_bytes() == once


def test_the_shipped_catalog_ships_no_retired_combo_copy() -> None:
    """No operator reads an instruction for a widget that no longer exists."""
    offenders = {
        str(path).split("_lab/")[-1].removesuffix(".json"): hits
        for path in lab_graph_paths()
        if (hits := retired_copy(json.loads(path.read_text(encoding="utf-8"))))
    }
    assert not offenders, json.dumps(offenders, indent=2)
