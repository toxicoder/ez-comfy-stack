"""klein-dream-house-clay-lab-example: 3D clay persistence + Klein edit."""

from __future__ import annotations

import json

from _lab_paths import lab_json
from _stamp_app_mode import HIDDEN_APP_WIDGETS, STAMP_SPECS, infer_suite_inputs

BANNED = ("MiniMax", "MiniMaxH3", "minimax_h3", "klein-9b", "FLUX.2-dev", "Wav2Lip")


def _load() -> dict:
    path = lab_json("klein-dream-house-clay-lab-example.json")
    return json.loads(path.read_text(encoding="utf-8"))


def test_dream_house_clay_contract() -> None:
    graph = _load()
    assert graph["id"] == "klein-dream-house-clay-lab-example"
    extra = graph["extra"]
    assert extra["lab_profile"] == "klein-dream-house-clay-lab-example"
    assert extra["lab_app_mode"]["occupancy"] == "klein"
    assert extra["lab_app_mode"]["lane"] == "inspire"
    blob = json.dumps(graph)
    for needle in BANNED:
        assert needle not in blob
    latent = next(n for n in graph["nodes"] if n.get("type") == "EmptyFlux2LatentImage")
    assert latent["widgets_values"][0] == 1024
    assert latent["widgets_values"][1] == 1280
    refs = [n for n in graph["nodes"] if n.get("type") == "ReferenceLatent"]
    loads = [n for n in graph["nodes"] if n.get("type") == "LoadImage"]
    joins = [n for n in graph["nodes"] if n.get("type") == "EZPromptJoin"]
    saves = [n for n in graph["nodes"] if n.get("type") == "SaveImage"]
    assert len(refs) == 10
    assert len(loads) == 10
    assert len(joins) == 10
    assert len(saves) == 10
    prefixes = [s["widgets_values"][0] for s in saves]
    assert prefixes == [f"ez_dream_house_clay_{i:02d}" for i in range(1, 11)]
    names = [load["widgets_values"][0] for load in loads]
    assert names == [f"ez_house_clay_{i:02d}.png" for i in range(1, 11)]
    ident = next(n for n in graph["nodes"] if n.get("type") == "EZKleinPromptEnhance")
    assert ident["widgets_values"][2] == "identity"
    assert ident["widgets_values"][1] is True
    note = extra["lab_note"].lower()
    assert "house-views" in note
    assert "occupancy" in note
    assert "1024" in note and "1280" in note
    assert "klein-dream-house-lab-example" in extra["lab_note"]
    assert extra["lab_app_mode"]["handoff"] == [
        "wan-gif-loop-lab-example",
        "wan-bumper-loop-lab-example",
        "wan-sticker-loop-lab-example",
    ]


def test_dream_house_clay_hides_shots_and_images() -> None:
    graph = _load()
    spec = STAMP_SPECS["klein-dream-house-clay-lab-example"]
    assert spec.get("hide_images") is True
    names = [item[1] for item in infer_suite_inputs(graph, spec)]
    assert names.count("prompt") == 1
    assert "image" not in names
    for hidden in HIDDEN_APP_WIDGETS:
        assert hidden not in names
    assert "width" not in names
