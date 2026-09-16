"""Wave 4 contracts: DFR extra, A14B hero, talking-head, identity, accept docs."""

from __future__ import annotations

import json
from pathlib import Path

from _lab_layout import node_overlap_hits
from _lab_paths import lab_json

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "workflows"


def test_film_graphs_carry_dfr_extra() -> None:
    for name in (
        "shorts/go-see.json",
        "shorts/still-here.json",
        "shorts/switchyard.json",
    ):
        extra = json.loads(lab_json(name).read_text(encoding="utf-8"))["extra"]
        assert extra["lab_dfr"]["print"] == "ltx"
        assert "Templates" in extra["lab_dfr"]["note"]


def _overlap_hits(graph: dict) -> list[str]:
    return node_overlap_hits(graph)


def test_a14b_hero_is_eight_step_magcache_off() -> None:
    graph = json.loads(lab_json("optional/wan/still-to-video-a14b.json").read_text(encoding="utf-8"))
    assert graph["id"] == "still-to-video-a14b"
    assert graph["extra"].get("lab_rel") == "optional/wan/still-to-video-a14b"
    assert graph["extra"]["lab_a14b"]["steps"] == 8
    assert graph["extra"]["lab_a14b"]["magcache"] is False
    assert "lab_magcache" not in graph["extra"]
    sampler = next(n for n in graph["nodes"] if n.get("type") == "KSampler")
    assert int(sampler["widgets_values"][2]) == 8
    unets = [n for n in graph["nodes"] if n.get("type") == "UNETLoader"]
    files = [n["widgets_values"][0] for n in unets]
    assert any("high_noise" in f and "14B" in f for f in files)
    assert any("low_noise" in f and "14B" in f for f in files)
    high = next(n for n in unets if "high_noise" in n["widgets_values"][0])
    low = next(n for n in unets if "low_noise" in n["widgets_values"][0])
    assert high["outputs"][0]["links"]
    assert not low["outputs"][0]["links"]
    assert not _overlap_hits(graph), _overlap_hits(graph)


def test_talking_head_graph() -> None:
    graph = json.loads(lab_json("klein/talking-head.json").read_text(encoding="utf-8"))
    assert graph["id"] == "talking-head"
    assert graph["extra"].get("lab_rel") == "klein/talking-head"
    assert graph["extra"]["lab_talking_head"]["s2v_tier"] == "s2v"
    blob = json.dumps(graph)
    assert "Wav2Lip" not in blob
    assert "wav2lip" not in blob.lower()
    assert any(n.get("type") == "VHS_VideoCombine" for n in graph["nodes"])
    ltx = next(n for n in graph["nodes"] if n.get("type") == "EZLTXPromptEnhance")
    lv = ltx["widgets_values"]
    assert (lv[2] if len(lv) >= 8 else lv[1]) is False


def test_identity_sheet_seed_and_size() -> None:
    graph = json.loads(lab_json("klein/identity-sheet.json").read_text(encoding="utf-8"))
    assert graph["extra"]["lab_identity"]["seed"] == 42
    assert graph["extra"]["lab_identity"]["enhance"] is True
    prefixes = [n["widgets_values"][0] for n in graph["nodes"] if n.get("type") == "SaveImage"]
    assert "ez_identity_front" in prefixes
    assert "ez_identity_threequarter" in prefixes
    assert "ez_identity_profile" in prefixes
    for node in graph["nodes"]:
        if node.get("type") == "EmptyFlux2LatentImage":
            assert int(node["widgets_values"][0]) == 1280
            assert int(node["widgets_values"][1]) == 704
        if node.get("type") == "EZKleinPromptEnhance":
            values = node["widgets_values"]
            assert (values[2] if len(values) >= 7 else values[1]) is True
        if node.get("type") == "KSampler":
            assert int(node["widgets_values"][0]) == 42
    blob = json.dumps(graph)
    assert "Front camera" in blob
    assert "Three-quarter camera" in blob
    assert "Profile camera" in blob
    assert "Hard golden key light" not in blob
    assert "NIGHT LAMP" not in blob


def test_longcat_lab_note_refuses_nccl() -> None:
    path = lab_json("optional/longcat-video.json")
    graph = json.loads(path.read_text(encoding="utf-8"))
    assert graph["id"] == "longcat-video"
    assert graph["extra"].get("lab_rel") == "optional/longcat-video"
    note = graph["extra"]["lab_note"]
    assert "NCCL" in note
    assert "nvidia-dgx-spark-lab" in note
    assert graph["extra"]["lab_longcat"]["nccl"] is False


def test_notice_names_dfr() -> None:
    text = (WF / "quality" / "ltx-2.5" / "NOTICE.md").read_text(encoding="utf-8")
    assert "print: dfr" in text or "DFR" in text
    assert "templates/ltx-2.5/t2v-i2v-two-stage-distilled" in text
