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


EXISTING_LOADIMAGE_STEMS = (
    "klein-from-clay-lab-example",
    "klein-from-canny-lab-example",
    "klein-from-clay-plates-lab-example",
    "ltx-iclora-depth-5s-lab-example",
    "ltx-iclora-canny-5s-lab-example",
    "ltx-iclora-depth-shorts-lab-example",
    "wan-flf-from-guide-lab-example",
)
LOADER_STEMS = (
    "klein-from-guide-loader-lab-example",
    "ltx-iclora-from-guide-loader-lab-example",
    "trellis-from-klein-still-lab-example",
)
DCC_STEMS = EXISTING_LOADIMAGE_STEMS + LOADER_STEMS


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


def test_existing_seven_keep_loadimage_and_point_at_loaders() -> None:
    for stem in EXISTING_LOADIMAGE_STEMS:
        graph = _load(f"{stem}.json")
        types = {n.get("type") for n in graph["nodes"]}
        assert "LoadImage" in types, stem
        assert "EZDCCLoadGuideStill" not in types, stem
        note = (graph.get("extra") or {}).get("lab_note", "")
        assert "klein-from-guide-loader-lab-example" in note, stem


def test_klein_from_guide_loader_contract() -> None:
    graph = _load("klein-from-guide-loader-lab-example.json")
    extra = graph["extra"]
    assert extra["lab_dcc"]["prefix"] == "ez_guide_hero"
    assert extra["lab_dcc"]["size"] == [1280, 704]
    assert extra["lab_dcc"]["seed"] == 42
    assert extra["lab_app_mode"]["occupancy"] == "klein"
    assert extra["lab_app_mode"]["lane"] == "dcc"
    types = {n.get("type") for n in graph["nodes"]}
    assert "EZDCCLoadGuideStill" in types
    assert "EZDCCOccupancyGate" in types
    assert "LoadImage" not in types
    load = next(n for n in graph["nodes"] if n.get("type") == "EZDCCLoadGuideStill")
    assert load["widgets_values"][:3] == ["go-see", "12", "first"]
    save = next(n for n in graph["nodes"] if n.get("type") == "SaveImage")
    assert save["widgets_values"][0] == "ez_guide_hero"
    titles = {n.get("title") for n in graph["nodes"]}
    assert any(isinstance(t, str) and "klein" in t.lower() for t in titles)
    blob = json.dumps(graph)
    assert "1280x720" not in blob
    assert "Pixal3D" not in blob
    assert "FLUX.2-dev" not in blob


def test_ltx_iclora_from_guide_loader_contract() -> None:
    graph = _load("ltx-iclora-from-guide-loader-lab-example.json")
    extra = graph["extra"]
    assert extra["lab_iclora"]["magcache"] is False
    assert extra["lab_iclora"]["distilled_only"] is True
    assert extra["lab_iclora"]["prefix"] == "ez_iclora_guide"
    assert extra["lab_app_mode"]["occupancy"] == "ltx"
    types = {n.get("type") for n in graph["nodes"]}
    assert "EZDCCLoadGuideStill" in types
    assert "EZDCCLoadGuideVideo" in types
    assert "EZDCCOccupancyGate" in types
    assert "MagCache" not in types
    assert "LoadImage" not in types
    video = next(n for n in graph["nodes"] if n.get("type") == "EZDCCLoadGuideVideo")
    assert video["widgets_values"][:3] == ["go-see", "12", "depth"]
    note = extra["lab_note"]
    assert "download-ltx --tier iclora" in note
    assert "Templates" in note
    blob = json.dumps(graph)
    assert "19B" in extra["lab_note"] or "19b" not in blob.lower()
    assert "Pixal3D" not in blob
    assert "No 1280x720" in extra["lab_note"]
    latent = next(
        n
        for n in graph["nodes"]
        if n.get("type") in {"LTXVImgToVideo", "EmptyLTXVLatentVideo"}
    )
    values = latent.get("widgets_values") or []
    if len(values) >= 2:
        assert int(values[0]) != 1280 or int(values[1]) != 720


def test_trellis_from_klein_still_contract() -> None:
    graph = _load("trellis-from-klein-still-lab-example.json")
    extra = graph["extra"]
    assert extra["lab_app_mode"]["occupancy"] == "trellis"
    assert extra["lab_app_mode"]["lane"] == "dcc"
    assert extra["lab_dcc"]["plate"] == "mug"
    assert extra["lab_dcc"]["prefix"] == "assets/objects/_lab-mug/"
    types = {n.get("type") for n in graph["nodes"]}
    assert "EZDCCLoadStillPack" in types
    assert "EZDCCOccupancyGate" in types
    assert "MeshToFile3D" in types
    assert "LoadImage" not in types
    load = next(n for n in graph["nodes"] if n.get("type") == "EZDCCLoadStillPack")
    assert load["widgets_values"][:3] == ["go-see", "mug", "first"]
    blob = json.dumps(graph)
    assert "assets/objects/_lab-mug/" in blob
    assert "download-3d --tier trellis2" in extra["lab_note"]
    assert "Pixal3D" not in blob
    assert "asset-new" not in blob
    assert "Preview 3D" in extra["lab_note"] or "Load 3D" in extra["lab_note"]
