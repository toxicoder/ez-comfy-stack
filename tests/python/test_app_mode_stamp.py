"""App Mode stamp helper: lab_app_mode + linearData contracts.

Hermetic: stdlib + in-memory copies of seeded graphs. Does not write workflows.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from _stamp_app_mode import stamp_app_mode

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "workflows"


def _load(name: str) -> dict:
    return json.loads((WF / name).read_text(encoding="utf-8"))


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
        enhance_off_identity=True,
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
    assert mode["enhance_off_identity"] is True
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
