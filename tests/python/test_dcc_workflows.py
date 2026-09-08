"""P0 DCC lab graphs: Klein-from-clay + LTX IC-LoRA envelope."""

from __future__ import annotations

import ast
import json
from pathlib import Path

from _lab_paths import lab_json

ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = ROOT / "docker" / "Dockerfile"
BANNED = ("MiniMax", "MiniMaxH3", "minimax_h3", "klein-9b", "FLUX.2-dev", "Wav2Lip")


def _load(name: str) -> dict:
    path = lab_json(name)
    assert path.is_file(), path
    return json.loads(path.read_text(encoding="utf-8"))


def test_dcc_graphs_exist_and_ids() -> None:
    for stem in ("klein-from-clay-lab-example", "ltx-iclora-depth-5s-lab-example"):
        graph = _load(f"{stem}.json")
        assert graph.get("id") == stem
        extra = graph.get("extra") or {}
        assert extra.get("lab_note", "").strip()
        blob = json.dumps(graph)
        for needle in BANNED:
            assert needle not in blob, (stem, needle)


def test_klein_from_clay_contract() -> None:
    graph = _load("klein-from-clay-lab-example.json")
    extra = graph["extra"]
    assert extra["lab_dcc"]["enhance"] is True
    assert extra["lab_dcc"]["seed"] == 42
    assert extra["lab_dcc"]["size"] == [1280, 704]
    enhance = next(n for n in graph["nodes"] if n.get("type") == "EZKleinPromptEnhance")
    widgets = enhance["widgets_values"]
    assert widgets[1] is True
    assert widgets[2] == "edit"
    save = next(n for n in graph["nodes"] if n.get("type") == "SaveImage")
    assert save["widgets_values"][0] == "ez_clay_hero"
    latent = next(n for n in graph["nodes"] if n.get("type") == "EmptyFlux2LatentImage")
    assert latent["widgets_values"][0] == 1280
    assert latent["widgets_values"][1] == 704
    assert any(n.get("type") == "ReferenceLatent" for n in graph["nodes"])
    assert any(n.get("type") == "LoadImage" for n in graph["nodes"])
    note = extra["lab_note"].lower()
    assert "occupancy" in note
    assert "1280" in note and "704" in note


def test_ltx_iclora_envelope_contract() -> None:
    graph = _load("ltx-iclora-depth-5s-lab-example.json")
    extra = graph["extra"]
    ic = extra["lab_iclora"]
    assert ic["templates"] == "LTX-2.5_ICLoRA_Union_Control_Distilled.json"
    assert ic["lora"] == "ltx-2.3-22b-ic-lora-union-control-ref0.5.safetensors"
    assert ic["distilled_only"] is True
    assert ic["magcache"] is False
    assert ic["frames"] == 120
    assert ic["size"] == [1280, 704]
    assert extra["lab_disclosure"] == "LTX Community License"
    assert any(n.get("type") == "EZFilmDisclosure" for n in graph["nodes"])
    assert not any(n.get("type") == "MagCache" for n in graph["nodes"])
    blob = json.dumps(graph)
    assert "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors" in blob
    assert "19b" not in blob.lower() or "Refuse 19B" in extra["lab_note"]
    assert "download-ltx --tier iclora" in extra["lab_note"]
    assert "subgraph" in extra["lab_note"].lower() or "Templates" in extra["lab_note"]


def test_dockerfile_still_has_no_dcc_binaries() -> None:
    text = DOCKERFILE.read_text(encoding="utf-8").lower()
    for needle in ("blender", "godot", "nvdiffrast", "nvdiffrec", "krita", "opentoonz"):
        assert needle not in text, needle


def test_export_script_parses() -> None:
    path = ROOT / "tools" / "blender" / "export_guide_pack.py"
    ast.parse(path.read_text(encoding="utf-8"))


def test_iclora_not_in_download_models_help() -> None:
    help_text = (ROOT / "scripts" / "manage.sh").read_text(encoding="utf-8")
    # cmd_help download-models paragraph must not list iclora as a default pack.
    start = help_text.find("download-models")
    chunk = help_text[start : start + 800]
    assert "iclora" not in chunk
    assert "export-guides" in help_text
