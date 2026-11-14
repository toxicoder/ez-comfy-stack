"""Audio-finish App: occupancy audio, no UNET, stem-mix handoff.

The App is a desk in front of a host verb, so the two invariants that matter are
that nothing on the canvas pretends to run the mix, and that every App row the
panel shows is a control the graph actually reads.
"""

from __future__ import annotations

import json
import re
from typing import Any

import pytest

from _build_audio_finish import (
    FILM_ID,
    PREFIX_ROOT,
    PREFIX_SAFE,
    PREFIX_TITLE,
    SHOT_ID,
    _safe_prefix_fragment,
    _wire_prefix,
    stem_mix_prefix,
)
from _lab_paths import lab_json
from _stamp_app_mode import NODE_MODE_BYPASS

BANNED = ("MiniMax", "MiniMaxH3", "minimax_h3", "klein-9b", "FLUX.2-dev", "Wav2Lip")
HEAVY = ("UNETLoader", "VAELoader", "KSampler", "VAEDecode")
PREFIX = "ez_stem_mix_gosee_01"


def _graph() -> dict[str, Any]:
    """Return the shipped stem-mix graph.

    Returns:
        Parsed ``workflows/_lab/audio/stem-mix.json``.
    """
    data: dict[str, Any] = json.loads(lab_json("audio/stem-mix.json").read_text(encoding="utf-8"))
    return data


def _node_by_id(graph: dict[str, Any], node_id: int) -> dict[str, Any]:
    """Return one node row by id.

    Args:
        graph: Parsed stem-mix graph.
        node_id: Comfy node id.

    Returns:
        The node row.

    Raises:
        StopIteration: the graph has no node with that id.
    """
    return next(node for node in graph["nodes"] if int(node["id"]) == node_id)


def _save_audio(graph: dict[str, Any]) -> dict[str, Any]:
    """Return the graph's ``SaveAudio`` row.

    Args:
        graph: Parsed stem-mix graph.

    Returns:
        The save node.

    Raises:
        StopIteration: the graph writes no audio.
    """
    return next(node for node in graph["nodes"] if node.get("type") == "SaveAudio")


def test_audio_finish_app_contract() -> None:
    graph = _graph()
    assert graph["id"] == "stem-mix"
    assert graph["extra"].get("lab_rel") == "audio/stem-mix"
    types = {n.get("type") for n in graph["nodes"]}
    for heavy in HEAVY:
        assert heavy not in types
    assert "SaveAudio" in types
    extra = graph["extra"]
    assert extra["lab_app_mode"]["occupancy"] == "audio"
    assert extra["lab_app_mode"]["lane"] == "audio"
    blob = json.dumps(graph)
    for needle in BANNED:
        assert needle not in blob, needle
    assert "stem-mix" in extra["lab_note"]
    assert "I=-14" in extra["lab_note"] or "loudnorm" in extra["lab_note"]
    primitives = [n for n in graph["nodes"] if n.get("type") == "PrimitiveNode"]
    assert len(primitives) == 1
    assert primitives[0]["title"] == PREFIX_TITLE
    assert _save_audio(graph)["widgets_values"][0] == PREFIX
    assert extra["lab_app_mode"]["default_view"] == "app"
    assert "1280x720" not in blob and "1280x720" not in blob


def test_no_yes_no_stem_rows_survive() -> None:
    """The Include DX / FX / MX rows are gone: the host verb takes paths.

    The note is allowed to explain why they went; a node or an App row that
    still asks for a yes/no stem is not.
    """
    graph = _graph()
    titles = {str(node.get("title") or "") for node in graph["nodes"]}
    assert not [title for title in titles if title.lower().startswith("include ")]
    rows = graph["extra"]["linearData"]["inputs"]
    row_labels = {
        str(row[2].get("label") or "") if len(row) > 2 else str(row[1]) for row in rows
    }
    assert not [label for label in row_labels if "include" in label.lower()]


def test_every_live_app_row_is_a_control_the_graph_reads() -> None:
    """No App row is a dead control: each is linked, or a documented exception.

    A row is dead when its node is live, has output slots, and none of them
    carries a link, so what the operator typed reaches nothing. A writer with no
    output slot at all is exempt (its job is the file it writes), and a type the
    stamper records in ``extra.lab_optional_unwired`` is a documented exception -
    but this graph may not lean on that list to hide a dead row.
    """
    graph = _graph()
    nodes = {int(node["id"]): node for node in graph["nodes"]}
    rows = graph["extra"]["linearData"]["inputs"]
    unwired = {str(item) for item in graph["extra"].get("lab_optional_unwired") or []}
    assert rows, "the App panel shows no control at all"
    dead: list[str] = []
    leaning_on_marker: list[str] = []
    for entry in rows:
        node = nodes[int(entry[0])]
        assert int(node.get("mode") or 0) != NODE_MODE_BYPASS, f"row {entry!r} sits on bypass"
        outputs = node.get("outputs") or []
        if not outputs:
            continue
        if not any(slot.get("links") for slot in outputs):
            dead.append(f"{node['type']} {node['id']} '{node.get('title')}'")
            if str(node.get("type")) in unwired:
                leaning_on_marker.append(str(node["id"]))
    assert dead == []
    assert leaning_on_marker == []


def test_save_prefix_row_is_wired_into_the_writer() -> None:
    """The one App row is the save prefix, and it reaches SaveAudio."""
    graph = _graph()
    rows = graph["extra"]["linearData"]["inputs"]
    assert [(int(row[0]), row[1]) for row in rows] == [(2, "value")]
    assert rows[0][2]["label"] == PREFIX_TITLE
    save = _save_audio(graph)
    primitive = _node_by_id(graph, 2)
    assert primitive["widgets_values"][0] == PREFIX
    assert primitive["outputs"][0]["links"] == [1]
    link = next(row for row in graph["links"] if int(row[0]) == 1)
    assert link == [1, 2, 0, int(save["id"]), 1, "STRING"]
    prefix_slot = save["inputs"][1]
    assert prefix_slot["name"] == "filename_prefix"
    assert prefix_slot["link"] == 1
    assert prefix_slot["widget"] == {"name": "filename_prefix"}
    assert save["widgets_values"][0] == PREFIX


def test_prefix_is_the_shot_card_and_stays_path_safe() -> None:
    """The prefix names the film slug and shot id the host verb takes."""
    assert stem_mix_prefix(FILM_ID, SHOT_ID) == PREFIX
    assert PREFIX.startswith(f"{PREFIX_ROOT}_")
    graph = _graph()
    authored = [
        value
        for node in graph["nodes"]
        for value in (node.get("widgets_values") or [])
        if isinstance(value, str) and value.startswith(PREFIX_ROOT)
    ]
    assert authored, "no node authors the stem-mix prefix"
    for value in authored:
        assert re.fullmatch(PREFIX_SAFE, value), value


def test_prefix_sanitizer_folds_operator_text() -> None:
    """An operator entry is folded into path-safe text, not passed through raw."""
    assert _safe_prefix_fragment("Go See") == "go_see"
    assert _safe_prefix_fragment("  Shot 07  ") == "shot_07"
    assert _safe_prefix_fragment("//..//") == ""
    assert _safe_prefix_fragment("Take:03!") == "take03"
    assert stem_mix_prefix("go-see", "07 B") == "ez_stem_mix_gosee_07_b"
    with pytest.raises(ValueError, match="unknown film id"):
        stem_mix_prefix("not-a-film", "01")


def test_wire_prefix_refuses_a_source_with_no_output() -> None:
    """The helper cannot write a wire from a node that has nothing to send."""
    with pytest.raises(ValueError, match="no output slot"):
        _wire_prefix({"last_link_id": 0, "links": []}, {"id": 1, "outputs": []}, {"id": 2}, "ez_x")


def test_queue_is_not_how_the_app_is_run() -> None:
    """The note says the mix is a host verb and names the stem flags."""
    note = str(_graph()["extra"]["lab_note"])
    assert "Queue is not how this App is run" in note
    assert "bazelisk run //:manage -- stem-mix" in note
    for flag in ("--film", "--shot", "--bg", "--dx", "--fx", "--mx"):
        assert flag in note, flag
    assert "required" in note
    assert "--dest" not in note


def test_save_audio_audio_input_stays_honest() -> None:
    """No fake audio source is bolted on; the empty slot is stated, not hidden."""
    graph = _graph()
    save = _save_audio(graph)
    audio = save["inputs"][0]
    assert audio["name"] == "audio"
    assert audio["link"] is None
    assert graph["links"] == [[1, 2, 0, int(save["id"]), 1, "STRING"]]
    producers = [
        node
        for node in graph["nodes"]
        for slot in node.get("outputs") or []
        if slot.get("type") == "AUDIO"
    ]
    assert producers == []
