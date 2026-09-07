"""Wave 4 contracts: DFR extra, A14B hero, talking-head, identity, accept docs."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "workflows"


def test_film_graphs_carry_dfr_extra() -> None:
    for name in (
        "film-go-see-90s-run-lab-example.json",
        "film-still-here-90s-lab-example.json",
        "film-switchyard-90s-lab-example.json",
    ):
        extra = json.loads((WF / "shorts" / name).read_text(encoding="utf-8"))["extra"]
        assert extra["lab_dfr"]["print"] == "ltx"
        assert "Templates" in extra["lab_dfr"]["note"]


def test_a14b_hero_is_eight_step_magcache_off() -> None:
    graph = json.loads((WF / "optional" / "wan-i2v-a14b-lab-example.json").read_text(encoding="utf-8"))
    assert graph["id"] == "wan-i2v-a14b-lab-example"
    assert graph["extra"]["lab_a14b"]["steps"] == 8
    assert graph["extra"]["lab_a14b"]["magcache"] is False
    assert "lab_magcache" not in graph["extra"]
    sampler = next(n for n in graph["nodes"] if n.get("type") == "KSampler")
    assert int(sampler["widgets_values"][2]) == 8
    unet = next(n for n in graph["nodes"] if n.get("type") == "UNETLoader")
    assert "14B" in unet["widgets_values"][0]


def test_talking_head_graph() -> None:
    graph = json.loads((WF / "klein-talking-head-lab-example.json").read_text(encoding="utf-8"))
    assert graph["id"] == "klein-talking-head-lab-example"
    assert graph["extra"]["lab_talking_head"]["s2v_tier"] == "s2v"
    blob = json.dumps(graph)
    assert "Wav2Lip" not in blob
    assert "wav2lip" not in blob.lower()
    assert any(n.get("type") == "VHS_VideoCombine" for n in graph["nodes"])


def test_identity_sheet_seed_and_size() -> None:
    graph = json.loads((WF / "klein-identity-sheet-lab-example.json").read_text(encoding="utf-8"))
    assert graph["extra"]["lab_identity"]["seed"] == 42
    assert graph["extra"]["lab_identity"]["enhance"] is False
    prefixes = [n["widgets_values"][0] for n in graph["nodes"] if n.get("type") == "SaveImage"]
    assert "ez_identity_front" in prefixes
    assert "ez_identity_threequarter" in prefixes
    assert "ez_identity_profile" in prefixes
    for node in graph["nodes"]:
        if node.get("type") == "EmptyFlux2LatentImage":
            assert int(node["widgets_values"][0]) == 1280
            assert int(node["widgets_values"][1]) == 704
        if node.get("type") == "EZKleinPromptEnhance":
            assert node["widgets_values"][1] is False
        if node.get("type") == "KSampler":
            assert int(node["widgets_values"][0]) == 42
    blob = json.dumps(graph)
    assert "Front camera" in blob
    assert "Three-quarter camera" in blob
    assert "Profile camera" in blob
    assert "Hard golden key light" not in blob
    assert "NIGHT LAMP" not in blob


def test_longcat_lab_note_refuses_nccl() -> None:
    path = WF / "optional" / "longcat-video-lab-example.json"
    graph = json.loads(path.read_text(encoding="utf-8"))
    assert graph["id"] == "longcat-video-lab-example"
    note = graph["extra"]["lab_note"]
    assert "NCCL" in note
    assert "nvidia-dgx-spark-lab" in note
    assert graph["extra"]["lab_longcat"]["nccl"] is False


def test_notice_names_dfr() -> None:
    text = (WF / "quality" / "ltx-2.5" / "NOTICE.md").read_text(encoding="utf-8")
    assert "print: dfr" in text or "DFR" in text
    assert "templates/ltx-2.5/t2v-i2v-two-stage-distilled" in text
