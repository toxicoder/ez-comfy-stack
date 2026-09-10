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


DCC_STEMS = (
    "klein-from-clay-lab-example",
    "klein-from-canny-lab-example",
    "klein-from-clay-plates-lab-example",
    "ltx-iclora-depth-5s-lab-example",
    "ltx-iclora-canny-5s-lab-example",
    "ltx-iclora-depth-shorts-lab-example",
    "wan-flf-from-guide-lab-example",
)


def test_dcc_graphs_exist_and_ids() -> None:
    for stem in DCC_STEMS:
        graph = _load(f"{stem}.json")
        assert graph.get("id") == stem
        extra = graph.get("extra") or {}
        assert extra.get("lab_note", "").strip()
        assert extra.get("lab_app_mode", {}).get("lane") == "dcc"
        blob = json.dumps(graph)
        for needle in BANNED:
            assert needle not in blob, (stem, needle)
        assert lab_json(f"{stem}.json").parent.name == "dcc"


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
    assert "overlay-qc" in extra["lab_note"]
    assert extra["lab_app_mode"]["handoff"] == [
        "ltx-iclora-depth-5s-lab-example",
        "wan-i2v-5s-lab-example",
    ]


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
    assert extra["lab_app_mode"]["handoff"] == ["audio-finish-lab-example"]
    assert extra["lab_app_mode"]["occupancy"] == "ltx"


def test_dockerfile_still_has_no_dcc_binaries() -> None:
    text = DOCKERFILE.read_text(encoding="utf-8").lower()
    for needle in ("blender", "godot", "nvdiffrast", "nvdiffrec", "krita", "opentoonz"):
        assert needle not in text, needle


def test_klein_from_canny_contract() -> None:
    graph = _load("klein-from-canny-lab-example.json")
    extra = graph["extra"]
    assert extra["lab_dcc"]["prefix"] == "ez_canny_hero"
    assert extra["lab_dcc"]["guide"] == "canny"
    save = next(n for n in graph["nodes"] if n.get("type") == "SaveImage")
    assert save["widgets_values"][0] == "ez_canny_hero"
    load = next(n for n in graph["nodes"] if n.get("type") == "LoadImage")
    assert load["widgets_values"][0] == "canny.png"
    assert extra["lab_app_mode"]["occupancy"] == "klein"
    assert extra["lab_app_mode"]["handoff"] == ["ltx-iclora-canny-5s-lab-example"]


def test_klein_from_clay_plates_contract() -> None:
    graph = _load("klein-from-clay-plates-lab-example.json")
    extra = graph["extra"]
    plates = extra["lab_dcc"]["plates"]
    assert [p["id"] for p in plates] == ["hero", "packshot", "ig", "shorts"]
    prefixes = [
        n["widgets_values"][0]
        for n in graph["nodes"]
        if n.get("type") == "SaveImage"
    ]
    assert "ez_clay_pack_hero" in prefixes
    assert "ez_clay_pack_packshot" in prefixes
    assert "ez_clay_pack_ig" in prefixes
    assert "ez_clay_pack_shorts" in prefixes
    sizes = {
        tuple(n["widgets_values"][:2])
        for n in graph["nodes"]
        if n.get("type") == "EmptyFlux2LatentImage"
    }
    assert (1280, 704) in sizes
    assert (1024, 1024) in sizes
    assert (1024, 1280) in sizes
    assert (768, 1280) in sizes
    assert any(n.get("type") == "ImageScale" for n in graph["nodes"])
    assert extra["lab_app_mode"]["occupancy"] == "klein"


def test_ltx_iclora_canny_and_shorts_contract() -> None:
    canny = _load("ltx-iclora-canny-5s-lab-example.json")
    ic = canny["extra"]["lab_iclora"]
    assert ic["canny_default"] is True
    assert ic["depth_default"] is False
    assert ic["distilled_only"] is True
    assert ic["magcache"] is False
    assert not any(n.get("type") == "MagCache" for n in canny["nodes"])
    shorts = _load("ltx-iclora-depth-shorts-lab-example.json")
    sic = shorts["extra"]["lab_iclora"]
    assert sic["size"] == [768, 1280]
    latent = next(n for n in shorts["nodes"] if n.get("type") == "LTXVImgToVideo")
    assert latent["widgets_values"][0] == 768
    assert latent["widgets_values"][1] == 1280
    assert shorts["extra"]["lab_app_mode"]["occupancy"] == "ltx"


def test_wan_flf_from_guide_contract() -> None:
    graph = _load("wan-flf-from-guide-lab-example.json")
    extra = graph["extra"]
    assert extra["lab_dcc"]["first"] == "first.png"
    assert extra["lab_dcc"]["last"] == "last.png"
    assert extra["lab_dcc"]["magcache"] is False
    assert "lab_magcache" not in extra
    assert not any(n.get("type") == "MagCache" for n in graph["nodes"])
    titles = {n.get("title") for n in graph["nodes"]}
    assert "Guide first.png" in titles
    assert "Guide last.png" in titles
    latent = next(n for n in graph["nodes"] if n.get("type") == "Wan22ImageToVideoLatent")
    names = [inp.get("name") for inp in latent.get("inputs") or []]
    assert "end_image" in names
    end = next(inp for inp in latent["inputs"] if inp.get("name") == "end_image")
    assert end.get("link") is not None
    assert extra["lab_app_mode"]["occupancy"] == "wan"
    assert extra["lab_app_mode"]["lane"] == "dcc"


def test_export_script_parses() -> None:
    for name in ("export_guide_pack.py", "export_still_pack.py", "workbench_passes.py"):
        path = ROOT / "tools" / "blender" / name
        ast.parse(path.read_text(encoding="utf-8"))


def test_iclora_not_in_download_models_help() -> None:
    help_text = (ROOT / "scripts" / "manage.sh").read_text(encoding="utf-8")
    # cmd_help download-models paragraph must not list iclora as a default pack.
    start = help_text.find("download-models")
    chunk = help_text[start : start + 800]
    assert "iclora" not in chunk
    assert "export-guides" in help_text
    assert "blender-stills" in help_text
    assert "house-views" in help_text
