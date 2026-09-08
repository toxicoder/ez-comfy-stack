"""Wave 1 graph contracts: App Mode extra, MagCache draft-only, Klein 704, FLF."""

from __future__ import annotations

import json
from pathlib import Path

from _lab_paths import lab_json

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "workflows"


def _load(name: str) -> dict:
    return json.loads(lab_json(name).read_text(encoding="utf-8"))


def test_app_mode_extra_on_lab_printers() -> None:
    for name in (
        "klein-still-draft-lab-example.json",
        "klein-still-hero-lab-example.json",
        "wan-i2v-5s-lab-example.json",
        "ltx-i2v-5s-lab-example.json",
    ):
        extra = _load(name)["extra"]["lab_app_mode"]
        assert extra["enabled"] is True
        assert extra["frontend_min"] == "1.41.13"


def test_identity_enhance_on() -> None:
    for name in (
        "klein-still-draft-lab-example.json",
        "klein-still-hero-lab-example.json",
    ):
        graph = _load(name)
        node = next(n for n in graph["nodes"] if n.get("type") == "EZKleinPromptEnhance")
        assert node["widgets_values"][1] is True


def test_klein_i2v_feeders_are_1280x704() -> None:
    for name in (
        "klein-still-hero-lab-example.json",
        "shorts/film-go-see-90s-run-lab-example.json",
        "shorts/film-still-here-90s-lab-example.json",
        "shorts/film-switchyard-90s-lab-example.json",
    ):
        graph = _load(name)
        hits = [
            n
            for n in graph["nodes"]
            if n.get("type") == "EmptyFlux2LatentImage"
        ]
        assert hits, name
        for node in hits:
            w, h = int(node["widgets_values"][0]), int(node["widgets_values"][1])
            assert (w, h) == (1280, 704), (name, w, h)


def test_magcache_draft_only() -> None:
    wan = _load("wan-i2v-5s-lab-example.json")
    mag = wan["extra"]["lab_magcache"]
    assert mag["enabled"] is True
    assert mag["magcache_thresh"] == 0.04
    assert mag["magcache_K"] == 3
    assert mag["start_step"] == 2
    ltx = _load("ltx-i2v-5s-lab-example.json")
    assert "lab_magcache" not in ltx.get("extra", {})
    flf = _load("wan-flf-5s-lab-example.json")
    assert "lab_magcache" not in flf.get("extra", {})
    assert not any(n.get("type") == "MagCache" for n in ltx["nodes"])


def test_fun_inp_flf_graph() -> None:
    graph = _load("wan-flf-5s-lab-example.json")
    assert graph["id"] == "wan-flf-5s-lab-example"
    titles = [n.get("title") for n in graph["nodes"]]
    assert "End frame (Fun InP)" in titles
    assert "fun-inp" in graph["extra"]["lab_note"]
    notice = WF / "quality" / "ltx-2.5" / "NOTICE.md"
    assert notice.is_file()
    text = notice.read_text(encoding="utf-8")
    assert "1 + 8n" in text or "1+8n" in text
    assert "5.00" in text
