"""App Mode stamp helper: lab_app_mode + linearData contracts.

Hermetic: stdlib + in-memory copies of seeded graphs. Does not write workflows.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pytest

from _lab_paths import lab_json
from _stamp_app_mode import (
    DEFAULT_WIDGET_DESCRIPTIONS,
    HIDDEN_APP_WIDGETS,
    STAMP_SPECS,
    infer_suite_inputs,
    linear_input_node_id,
    stamp_app_mode,
    suite_json_paths,
    widget_config,
)

# ComfyUI_frontend v1.49.6 WidgetId: graphId:nodeId:name (three parts).
_FRONTEND_WIDGET_ID = re.compile(r"^[^:]+:[^:]+:[^:]+$")

ROOT = Path(__file__).resolve().parents[2]


def _load(name: str) -> dict:
    return json.loads(lab_json(name).read_text(encoding="utf-8"))


def test_klein_still_draft_stamp_keeps_lab_profile_and_note() -> None:
    graph = _load("klein-still-draft-lab-example.json")
    profile = graph["extra"]["lab_profile"]
    note = graph["extra"]["lab_note"]
    stamped = stamp_app_mode(
        graph,
        inputs=[
            ("Klein Prompt Enhance", "prompt"),
            ("Klein Prompt Enhance", "style"),
            ("Klein Prompt Enhance", "enhance"),
            ("Latent 768x432 batch 2", "width"),
            ("Latent 768x432 batch 2", "height"),
            ("KSampler", "seed"),
        ],
        outputs=["Save"],
        lane="inspire",
        occupancy="klein",
        enhance_off_identity=False,
        handoff=("klein-still-hero-lab-example", "wan-i2v-5s-lab-example"),
    )
    extra = stamped["extra"]
    assert extra["lab_profile"] == profile
    assert extra["lab_note"] == note
    mode = extra["lab_app_mode"]
    assert mode["enabled"] is True
    assert mode["default_view"] == "app"
    assert mode["frontend_min"] == "1.41.13"
    assert mode["lane"] == "inspire"
    assert mode["occupancy"] == "klein"
    assert mode["enhance_off_identity"] is False
    assert mode["handoff"] == [
        "klein-still-hero-lab-example",
        "wan-i2v-5s-lab-example",
    ]
    linear = extra["linearData"]
    by_id = {int(n["id"]): n for n in stamped["nodes"]}
    assert linear["inputs"]
    assert linear["outputs"]
    for entry in linear["inputs"]:
        node_id = linear_input_node_id(entry)
        widget_name = entry[1]
        assert isinstance(entry[0], int)
        assert ":" not in str(entry[0])
        assert node_id in by_id
        assert widget_name == entry[1]
    save = next(n for n in stamped["nodes"] if n.get("type") == "SaveImage")
    assert linear["outputs"] == [save["id"]]


def test_wan_video_stamp_resolves_vhs_output() -> None:
    graph = _load("wan-i2v-5s-lab-example.json")
    stamped = stamp_app_mode(
        copy.deepcopy(graph),
        inputs=[
            ("Wan Prompt Enhance", "prompt"),
            ("Wan Prompt Enhance", "enhance"),
            ("First frame", "image"),
        ],
        outputs=["VHS_VideoCombine"],
        lane="produce",
        occupancy="wan",
    )
    vhs = next(n for n in stamped["nodes"] if n.get("type") == "VHS_VideoCombine")
    assert stamped["extra"]["linearData"]["outputs"] == [vhs["id"]]
    assert stamped["extra"]["lab_app_mode"]["occupancy"] == "wan"
    mag = graph["extra"]["lab_magcache"]
    assert stamped["extra"]["lab_magcache"] == mag


def test_missing_node_stamp_raises() -> None:
    graph = _load("klein-still-draft-lab-example.json")
    with pytest.raises(ValueError, match="missing"):
        stamp_app_mode(
            graph,
            inputs=[("No Such Node", "prompt")],
            outputs=["Save"],
            lane="inspire",
            occupancy="klein",
        )


def test_banned_string_in_label_is_rejected() -> None:
    graph = _load("klein-still-draft-lab-example.json")
    with pytest.raises(ValueError, match="banned"):
        stamp_app_mode(
            copy.deepcopy(graph),
            inputs=[
                (
                    "Klein Prompt Enhance",
                    "prompt",
                    {"description": "MiniMax H3 is not allowed"},
                )
            ],
            outputs=["Save"],
            lane="inspire",
            occupancy="klein",
        )
    with pytest.raises(ValueError, match="banned"):
        stamp_app_mode(
            copy.deepcopy(graph),
            inputs=[("Klein Prompt Enhance", "prompt")],
            outputs=["Save"],
            lane="inspire",
            occupancy="klein",
            handoff=("klein-9b-lab-example",),
        )


def _widget_names(graph: dict) -> list[str]:
    spec = STAMP_SPECS[str(graph["id"])]
    return [entry[1] for entry in infer_suite_inputs(graph, spec)]


def test_still_draft_app_inputs_are_prompt_first_without_latent_size() -> None:
    names = _widget_names(_load("klein-still-draft-lab-example.json"))
    assert names[:4] == ["prompt", "style", "enhance", "seed"]
    assert "width" not in names
    assert "height" not in names
    assert "batch_size" not in names
    assert "shot" not in names
    assert "unet_name" not in names


def test_daily_still_exposes_latent_and_unet_after_prompt() -> None:
    names = _widget_names(_load("klein-still-daily-lab-example.json"))
    assert names[0] == "prompt"
    assert names.index("prompt") < names.index("seed")
    assert names.index("style") < names.index("enhance")
    assert "width" in names
    assert "height" in names
    assert "unet_name" in names
    assert "steps" in names
    assert "cfg" in names


def test_dream_house_hides_join_shots_and_keeps_one_prompt() -> None:
    names = _widget_names(_load("klein-dream-house-lab-example.json"))
    assert names.count("prompt") == 1
    assert names[0] == "prompt"
    for hidden in HIDDEN_APP_WIDGETS:
        assert hidden not in names
    assert "width" not in names


def test_beat_sheet_exposes_only_shot_cards() -> None:
    names = _widget_names(_load("beat-sheet-lab-example.json"))
    assert names == ["value"] * 22


def test_prompt_forge_keeps_three_family_prompts_first() -> None:
    names = _widget_names(_load("prompt-forge-lab-example.json"))
    assert names[:3] == ["prompt", "prompt", "prompt"]
    assert names.count("style") == 3
    assert names.count("enhance") == 3
    assert "audio_notes" in names
    assert "mode" not in names
    assert "duration_hint" not in names


def test_widget_help_text_has_no_banned_models() -> None:
    blob = json.dumps(DEFAULT_WIDGET_DESCRIPTIONS)
    for needle in ("MiniMax", "klein-9b", "FLUX.2-dev", "Seedance", "Kling"):
        assert needle not in blob


def _labels(graph: dict) -> list[str]:
    spec = STAMP_SPECS[str(graph["id"])]
    labels: list[str] = []
    for entry in infer_suite_inputs(graph, spec):
        name = entry[1]
        config = entry[2] if len(entry) > 2 else {}
        labels.append((config or {}).get("label") or name)
    return labels


def test_unwired_or_bypassed_loadimage_is_not_an_app_input() -> None:
    hero = _widget_names(_load("klein-still-hero-lab-example.json"))
    assert "image" not in hero
    thumb = _widget_names(_load("klein-thumbnail-lab-example.json"))
    assert "image" not in thumb
    t2v = _widget_names(_load("wan-t2v-5s-lab-example.json"))
    assert "image" not in t2v
    flf = _widget_names(_load("wan-flf-5s-lab-example.json"))
    assert flf.count("image") == 1
    vace = _widget_names(_load("wan-vace-join-lab-example.json"))
    assert vace.count("image") == 1


def test_wired_edit_and_i2v_keep_image() -> None:
    tweak = _widget_names(_load("klein-character-tweak-lab-example.json"))
    assert "image" in tweak
    i2v = _widget_names(_load("wan-i2v-5s-lab-example.json"))
    assert "image" in i2v
    clay = _widget_names(_load("klein-from-clay-lab-example.json"))
    assert "image" in clay


def test_i2v_hides_style_t2v_keeps_it() -> None:
    i2v = _widget_names(_load("wan-i2v-5s-lab-example.json"))
    assert "style" not in i2v
    ltx_i2v = _widget_names(_load("ltx-i2v-5s-lab-example.json"))
    assert "style" not in ltx_i2v
    t2v = _widget_names(_load("wan-t2v-5s-lab-example.json"))
    assert "style" in t2v
    ltx_t2v = _widget_names(_load("ltx-t2v-5s-lab-example.json"))
    assert "style" in ltx_t2v
    still = _widget_names(_load("klein-still-draft-lab-example.json"))
    assert "style" in still


def test_prompt_forge_keeps_style_on_i2v_family_encoders() -> None:
    names = _widget_names(_load("prompt-forge-lab-example.json"))
    assert names.count("style") == 3
    labels = _labels(_load("prompt-forge-lab-example.json"))
    assert "Klein prompt" in labels
    assert "Wan prompt" in labels
    assert "LTX prompt" in labels
    assert len(labels) == len(set(labels)), labels


def test_beat_sheet_labels_are_node_titles() -> None:
    graph = _load("beat-sheet-lab-example.json")
    labels = _labels(graph)
    titles = [
        n.get("title")
        for n in graph["nodes"]
        if n.get("type") == "PrimitiveNode"
    ]
    assert labels == titles
    assert len(set(labels)) == 22
    assert labels[:4] == ["Logline", "Script", "Audio policy", "Score"]


def test_music_exposes_duration_and_vocal_mode() -> None:
    names = _widget_names(_load("music-rap-draft-lab-example.json"))
    assert names[0] == "tags"
    assert "lyrics" in names
    assert "seconds" in names
    assert "mode" in names
    assert names.index("enhance") < names.index("seconds")
    labels = _labels(_load("music-rap-draft-lab-example.json"))
    assert "Duration (seconds)" in labels
    assert "Vocal / instrumental" in labels


def test_podcast_exposes_voices_and_hides_refs_and_bed_lyrics() -> None:
    names = _widget_names(_load("podcast-audio-first-lab-example.json"))
    assert "prompt" in names
    assert "tags" in names
    assert "seconds" in names
    assert "speaker_a_voice" in names
    assert "speaker_b_voice" in names
    assert "speed" in names
    assert "lyrics" not in names
    assert "backend" not in names
    assert "speaker_a_ref" not in names
    labels = _labels(_load("podcast-audio-first-lab-example.json"))
    assert "Script" in labels
    assert "Bed tags" in labels
    assert "Rewrite script" in labels
    assert "Rewrite bed" in labels
    assert len(labels) == len(set(labels)), labels
    radio = _widget_names(_load("podcast-radio-drama-lab-example.json"))
    assert radio.count("tags") == 2
    assert radio.count("seconds") == 2
    assert "announcer_voice" in radio
    assert "include_announcer" in radio
    assert "lyrics" not in radio
    radio_labels = _labels(_load("podcast-radio-drama-lab-example.json"))
    assert "Sting tags" in radio_labels
    assert "Bed tags" in radio_labels
    assert len(radio_labels) == len(set(radio_labels)), radio_labels


def test_widget_config_carries_label_and_prompt_height() -> None:
    cfg = widget_config("prompt")
    assert cfg is not None
    assert cfg["label"] == "Prompt"
    assert cfg["height"] == 140
    assert "description" in cfg


def _frontend_1496_keeps_input(stored_id: object, node_ids: set[int]) -> bool:
    """Keep/drop rule from ComfyUI_frontend v1.49.6 upgradeAndValidateInput.

    Three-part WidgetIds resolve by nodeId. A string that contains ':' but is
    not a WidgetId is treated as a subgraph locator and dropped when
    getNodeById('11:prompt') fails. Integer (or digit-string) node ids upgrade
    via getNodeById + widget name.
    """
    if isinstance(stored_id, str) and _FRONTEND_WIDGET_ID.match(stored_id):
        node_part = stored_id.split(":")[1]
        return node_part.lstrip("-").isdigit() and int(node_part) in node_ids
    if isinstance(stored_id, str) and ":" in stored_id:
        return False
    if isinstance(stored_id, bool) or stored_id is None:
        return False
    if isinstance(stored_id, int):
        return stored_id in node_ids
    if isinstance(stored_id, str) and stored_id.lstrip("-").isdigit():
        return int(stored_id) in node_ids
    return False


def test_linear_input_node_id_accepts_int_and_rejects_colon_join() -> None:
    assert linear_input_node_id([11, "prompt"]) == 11
    assert linear_input_node_id(["7", "seed"]) == 7
    with pytest.raises(ValueError, match="legacy"):
        linear_input_node_id(["11:prompt", "prompt"])
    with pytest.raises(ValueError, match="invalid"):
        linear_input_node_id([True, "prompt"])
    with pytest.raises(ValueError, match="invalid"):
        linear_input_node_id([])


def test_frontend_1496_drops_two_part_widget_ids() -> None:
    graph = _load("klein-still-draft-lab-example.json")
    node_ids = {int(n["id"]) for n in graph["nodes"]}
    enhance = next(
        n for n in graph["nodes"] if n.get("type") == "EZKleinPromptEnhance"
    )
    nid = int(enhance["id"])
    assert _frontend_1496_keeps_input(f"{nid}:prompt", node_ids) is False
    assert _frontend_1496_keeps_input(nid, node_ids) is True
    assert _frontend_1496_keeps_input(str(nid), node_ids) is True


def test_stamped_inputs_survive_frontend_1496_prune() -> None:
    graph = copy.deepcopy(_load("klein-still-draft-lab-example.json"))
    stamped = stamp_app_mode(
        graph,
        inputs=[
            ("Klein Prompt Enhance", "prompt"),
            ("Klein Prompt Enhance", "style"),
            ("Klein Prompt Enhance", "enhance"),
            ("KSampler", "seed"),
        ],
        outputs=["Save"],
        lane="inspire",
        occupancy="klein",
    )
    node_ids = {int(n["id"]) for n in stamped["nodes"]}
    inputs = stamped["extra"]["linearData"]["inputs"]
    kept = [
        entry for entry in inputs if _frontend_1496_keeps_input(entry[0], node_ids)
    ]
    assert [entry[1] for entry in kept] == ["prompt", "style", "enhance", "seed"]
    assert kept == inputs


def test_shipped_suite_inputs_survive_frontend_1496_prune() -> None:
    for path in suite_json_paths(ROOT / "workflows"):
        graph = json.loads(path.read_text(encoding="utf-8"))
        node_ids = {int(n["id"]) for n in graph["nodes"]}
        inputs = (graph.get("extra") or {}).get("linearData", {}).get("inputs") or []
        assert inputs, path.name
        kept = [
            entry
            for entry in inputs
            if _frontend_1496_keeps_input(entry[0], node_ids)
        ]
        assert kept == inputs, path.name
        for entry in inputs:
            assert linear_input_node_id(entry) in node_ids, (path.name, entry[0])
