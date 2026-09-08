"""App Mode stamp helper: lab_app_mode + linearData contracts.

Hermetic: stdlib + in-memory copies of seeded graphs. Does not write workflows.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from _lab_paths import lab_json
from _stamp_app_mode import (
    DEFAULT_WIDGET_DESCRIPTIONS,
    HIDDEN_APP_WIDGETS,
    STAMP_SPECS,
    infer_suite_inputs,
    stamp_app_mode,
)

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
        widget_id, widget_name = entry[0], entry[1]
        node_id_s, name = widget_id.split(":", 1)
        node = by_id[int(node_id_s)]
        assert name == widget_name
        assert node is not None
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
    assert names == ["value"] * 18


def test_prompt_forge_keeps_three_family_prompts_first() -> None:
    names = _widget_names(_load("prompt-forge-lab-example.json"))
    assert names[:3] == ["prompt", "prompt", "prompt"]
    assert "mode" in names
    assert "duration_hint" in names
    assert "audio_notes" in names


def test_widget_help_text_has_no_banned_models() -> None:
    blob = json.dumps(DEFAULT_WIDGET_DESCRIPTIONS)
    for needle in ("MiniMax", "klein-9b", "FLUX.2-dev", "Seedance", "Kling"):
        assert needle not in blob
