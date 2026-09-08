"""Prompt Forge and Beat Sheet: no-UNET inspire Apps."""

from __future__ import annotations

import json
from pathlib import Path

from _lab_paths import lab_json

ROOT = Path(__file__).resolve().parents[2]

BANNED = ("MiniMax", "MiniMaxH3", "minimax_h3", "klein-9b", "FLUX.2-dev", "Seedance", "Kling")
HEAVY = ("UNETLoader", "VAELoader", "KSampler", "VAEDecode")
YAML_KEYS = (
    "film",
    "slug",
    "frames: 120",
    "fps: 24",
    "duration_s: 5.00",
    "beats: 6",
    "shots_per_beat: 3",
    "total_shots: 18",
    "publish_cap_s: 90.00",
    "print: ltx",
    "identity_seed",
    "identity_enhance: true",
    "identity_look",
    "load_from: identity",
    "_last",
)


def _load(stem: str) -> dict:
    path = lab_json(stem)
    assert path.is_file(), stem
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_no_overlap(graph: dict, pad: float = 20) -> None:
    boxes: list[tuple[int, str, float, float, float, float]] = []
    for node in graph["nodes"]:
        x, y = node["pos"]
        size = node.get("size", [200, 100])
        if isinstance(size, dict):
            width, height = float(size.get("0", 200)), float(size.get("1", 100))
        else:
            width, height = float(size[0]), float(size[1])
        boxes.append(
            (node["id"], node["type"], x - pad, y - pad, x + width + pad, y + height + pad)
        )
    hits = []
    for i, a in enumerate(boxes):
        for b in boxes[i + 1 :]:
            if a[2] < b[4] and a[4] > b[2] and a[3] < b[5] and a[5] > b[3]:
                hits.append(f"{a[0]}({a[1]}) vs {b[0]}({b[1]})")
    assert not hits, hits


def test_prompt_forge_has_no_unet_and_stamps_llm() -> None:
    graph = _load("prompt-forge-lab-example")
    assert graph["id"] == "prompt-forge-lab-example"
    types = {n.get("type") for n in graph["nodes"]}
    for heavy in HEAVY:
        assert heavy not in types, heavy
    assert "EZKleinPromptEnhance" in types
    assert "EZWanPromptEnhance" in types
    assert "EZLTXPromptEnhance" in types
    blob = json.dumps(graph)
    for needle in BANNED:
        assert needle not in blob
    assert "1280×720" not in blob and "1280x720" not in blob
    assert "MODELS_DIR" not in blob
    extra = graph["extra"]
    assert extra["lab_app_mode"]["enabled"] is True
    assert extra["lab_app_mode"]["lane"] == "inspire"
    assert extra["lab_app_mode"]["occupancy"] == "llm"
    assert "klein-still-draft-lab-example" in extra["lab_app_mode"]["handoff"]
    _assert_no_overlap(graph)


def test_character_draft_is_t2i_without_reference() -> None:
    graph = _load("klein-character-draft-lab-example")
    assert graph["extra"]["lab_app_mode"]["lane"] == "inspire"
    assert graph["extra"]["lab_app_mode"]["occupancy"] == "klein"
    assert "klein-character-tweak-lab-example" in graph["extra"]["lab_app_mode"]["handoff"]
    enh = next(n for n in graph["nodes"] if n.get("type") == "EZKleinPromptEnhance")
    assert enh["widgets_values"][2] == "t2i"
    assert enh["widgets_values"][1] is True
    latent = next(n for n in graph["nodes"] if n.get("type") == "EmptyFlux2LatentImage")
    assert latent["widgets_values"][:2] == [1024, 1280]
    save = next(n for n in graph["nodes"] if n.get("type") == "SaveImage")
    assert save["widgets_values"][0] == "ez_character"
    assert not any(n.get("type") == "ReferenceLatent" for n in graph["nodes"])
    names = [entry[1] for entry in graph["extra"]["linearData"]["inputs"]]
    assert names[0] == "prompt"
    assert "style" in names
    assert "shot" not in names
    _assert_no_overlap(graph)


def test_character_tweak_wires_reference_latent() -> None:
    graph = _load("klein-character-tweak-lab-example")
    assert graph["extra"]["lab_app_mode"]["occupancy"] == "klein"
    enh = next(n for n in graph["nodes"] if n.get("type") == "EZKleinPromptEnhance")
    assert enh["widgets_values"][2] == "edit"
    assert any(n.get("type") == "VAEEncode" for n in graph["nodes"])
    assert any(n.get("type") == "ReferenceLatent" for n in graph["nodes"])
    load = next(n for n in graph["nodes"] if n.get("type") == "LoadImage")
    assert load["title"].lower().startswith("character")
    save = next(n for n in graph["nodes"] if n.get("type") == "SaveImage")
    assert save["widgets_values"][0] == "ez_character_tweak"
    names = [entry[1] for entry in graph["extra"]["linearData"]["inputs"]]
    assert names[0] == "prompt"
    assert "image" in names
    sampler = next(n for n in graph["nodes"] if n.get("type") == "KSampler")
    by_id = {int(n["id"]): n for n in graph["nodes"]}
    pos = next(i for i in sampler["inputs"] if i.get("name") == "positive")
    src = by_id[next(int(link[1]) for link in graph["links"] if int(link[0]) == int(pos["link"]))]
    assert src["type"] == "ReferenceLatent"
    _assert_no_overlap(graph)


def test_beat_sheet_documents_yaml_contract_and_has_no_unet() -> None:
    graph = _load("beat-sheet-lab-example")
    assert graph["id"] == "beat-sheet-lab-example"
    types = {n.get("type") for n in graph["nodes"]}
    for heavy in HEAVY:
        assert heavy not in types, heavy
    primitives = [n for n in graph["nodes"] if n.get("type") == "PrimitiveNode"]
    assert len(primitives) == 18
    ltx = [n for n in graph["nodes"] if n.get("type") == "EZLTXPromptEnhance"]
    assert len(ltx) == 18
    assert all(n["widgets_values"][1] is True for n in ltx)
    note = graph["extra"]["lab_note"]
    blob = json.dumps(graph)
    for key in YAML_KEYS:
        assert key in blob, key
    assert "go-see.shots.yaml" in note or "shots.yaml" in note
    assert "paste" in note.lower()
    assert graph["extra"]["lab_app_mode"]["occupancy"] == "none"
    assert graph["extra"]["lab_app_mode"]["lane"] == "inspire"
    handoff = graph["extra"]["lab_app_mode"]["handoff"]
    assert "film-go-see-90s-run-lab-example" in handoff
    assert "1280×720" not in blob and "1280x720" not in blob
    assert "MODELS_DIR" not in blob
    for needle in BANNED:
        assert needle not in blob
    _assert_no_overlap(graph)
