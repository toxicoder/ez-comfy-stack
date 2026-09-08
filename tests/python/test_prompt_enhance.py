"""Hermetic tests for ez_prompt_enhance (no Comfy, no network, no GGUF)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

import ez_prompt_enhance  # noqa: E402
from ez_prompt_enhance import client  # noqa: E402
from ez_prompt_enhance.nodes import (  # noqa: E402
    EZAceStepPromptEnhance,
    EZKleinPromptEnhance,
    EZLTXPromptEnhance,
    EZPromptJoin,
    EZWanPromptEnhance,
    NODE_CLASS_MAPPINGS,
)


_STYLE_WOVEN_FIELDS = ("medium", "light", "color", "texture", "camera", "suffix")
_BANNED_STYLE_BRANDS = (
    "kodak",
    "portra",
    "sony",
    "canon",
    "leica",
    "hasselblad",
    "pixar",
    "unreal",
    "lumen",
    "ghibli",
)


def test_system_prompts_encode_model_rules() -> None:
    klein = client.load_system_prompt("klein_t2i")
    assert "Qwen3-4B" in klein
    assert "<|im_start|>" in klein
    assert "sentences" in klein.lower()
    assert "inventory" in klein.lower()
    assert "visual-style" in klein.lower()
    edit = client.load_system_prompt("klein_edit")
    assert "identity" in edit.lower()
    assert "massing" in edit.lower() or "do not add" in edit.lower()
    assert "visual-style" in edit.lower()
    assert "medium" in edit.lower() and "grade" in edit.lower()
    assert "camera" in edit.lower() and "framing" in edit.lower()
    wan_t2v = client.load_system_prompt("wan_t2v")
    assert "80" in wan_t2v and "120" in wan_t2v
    assert "audio" in wan_t2v.lower()
    assert "visual-style" in wan_t2v.lower()
    wan_i2v = client.load_system_prompt("wan_i2v")
    assert "Motion + Camera" in wan_i2v
    assert "audio" in wan_i2v.lower()
    assert "new objects" in wan_i2v.lower()
    ltx_t2v = client.load_system_prompt("ltx_t2v")
    assert "present" in ltx_t2v.lower()
    assert "quotation" in ltx_t2v.lower()
    assert "interleaved" in ltx_t2v.lower()
    assert "visual-style" in ltx_t2v.lower()
    ltx_i2v = client.load_system_prompt("ltx_i2v")
    assert "first frame" in ltx_i2v.lower()
    assert "camera motion" in ltx_i2v.lower()
    assert "new objects" in ltx_i2v.lower()
    ident = client.load_system_prompt("klein_identity")
    assert "camera-free" in ident.lower()
    assert "lens" in ident.lower()
    assert "150" in ident
    assert "invent" in ident.lower()
    assert "visual-style" in ident.lower()
    ident_l = ident.lower()
    assert "surround" in ident_l or "landscape" in ident_l
    assert "fixture" in ident_l or "lantern" in ident_l
    assert "adjacen" in ident_l
    flf = client.load_system_prompt("wan_flf")
    assert "first-last" in flf.lower() or "first last" in flf.lower() or "end frame" in flf.lower()
    assert "audio" in flf.lower()
    vace = client.load_system_prompt("wan_vace")
    assert "join" in vace.lower() or "seam" in vace.lower()
    ace_tags = client.load_system_prompt("ace_tags")
    assert "genre first" in ace_tags.lower() or "genre is always first" in ace_tags.lower()
    ace_inst = client.load_system_prompt("ace_instrumental")
    assert "instrumental" in ace_inst.lower()
    assert "no vocals" in ace_inst.lower()


def test_style_catalog_is_fifty_unique() -> None:
    styles = client.load_styles()
    assert len(styles) == 50
    assert len(set(styles)) == 50
    assert "none" not in styles
    ids = client.style_ids()
    assert ids[0] == "none"
    assert len(ids) == 51
    for sid, entry in styles.items():
        assert entry["label"].strip()
        assert entry["family"].strip()
        for field in _STYLE_WOVEN_FIELDS:
            blob = str(entry[field]).strip()
            assert blob, sid
            lower = blob.lower()
            assert "no photoreal" not in lower
            for brand in _BANNED_STYLE_BRANDS:
                assert brand not in lower, f"{sid}.{field} has {brand}"
        must = entry["must_include"]
        conflicts = entry["conflicts"]
        assert isinstance(must, list) and len(must) >= 2, sid
        assert isinstance(conflicts, list) and conflicts, sid
        for phrase in must:
            assert str(phrase).strip()
            lower = str(phrase).lower()
            for brand in _BANNED_STYLE_BRANDS:
                assert brand not in lower, f"{sid} must_include has {brand}"
    assert client.style_llm_block("none") == ""
    assert client.format_style_instruction("none", "klein") == ""
    assert client.style_suffix("photorealistic")
    pixar_blob = " ".join(str(styles["pixar_like_3d"][k]) for k in _STYLE_WOVEN_FIELDS).lower()
    unreal_blob = " ".join(
        str(styles["unreal_engine_cinematic"][k]) for k in _STYLE_WOVEN_FIELDS
    ).lower()
    assert "pixar" not in pixar_blob
    assert "unreal" not in unreal_blob
    assert "stylized feature 3d" in pixar_blob
    assert "real-time cinematic 3d" in unreal_blob


def test_format_style_instruction_override_and_flavor() -> None:
    klein = client.format_style_instruction("anime", "klein")
    assert "Visual style (mandatory" in klein
    assert "wins" in klein.lower()
    assert "Japanese anime" in klein
    assert "cel-shaded" in klein.lower() or "cel color" in klein.lower()
    assert "150" in klein
    edit = client.format_style_instruction("watercolor_illustration", "klein_edit")
    assert "identity" in edit.lower()
    assert "inventory" in edit.lower()
    assert "transparent watercolor" in edit.lower()
    wan = client.format_style_instruction("anime", "wan")
    assert "Stylization" in wan
    assert "2D anime" in wan
    ltx = client.format_style_instruction("oil_painting", "ltx")
    assert "coherent light" in ltx.lower()
    assert "oil painting" in ltx.lower()


def test_ensure_style_details_appends_when_missing() -> None:
    bare = "A red bicycle on a hill."
    filled = client.ensure_style_details(bare, "watercolor_illustration")
    assert "transparent watercolor" in filled.lower() or "wet-into-wet" in filled.lower()
    already = "A bicycle as transparent watercolor with paper tooth."
    kept = client.ensure_style_details(already, "watercolor_illustration")
    assert "transparent watercolor" in kept.lower()
    assert client.ensure_style_details(bare, "none") == bare


def test_apply_style_to_prompt_overrides_lab_3d() -> None:
    src = "A HD 3D game-engine pre-rendered cutscene still of a rooftop."
    out = client.apply_style_to_prompt(src, "watercolor_illustration")
    lower = out.lower()
    assert "transparent watercolor" in lower
    assert "game-engine" not in lower
    anime = client.apply_style_to_prompt(src, "anime")
    assert "japanese anime" in anime.lower() or "cel-shaded" in anime.lower()
    assert "game-engine" not in anime.lower()
    assert client.apply_style_to_prompt(src, "none") == src
    photo = "A photoreal still of a tropical rooftop."
    painted = client.apply_style_to_prompt(photo, "watercolor_illustration")
    assert "photoreal still" not in painted.lower()
    assert "transparent watercolor" in painted.lower() or "wet-into-wet" in painted.lower()


def test_strip_fences_quotes_and_think() -> None:
    fenced = "```text\nA techno wizard stands on a rooftop terrace.\n```"
    assert client.strip_model_wrapping(fenced) == "A techno wizard stands on a rooftop terrace."
    assert client.strip_model_wrapping('"A techno wizard."') == "A techno wizard."
    think = "<think>plan the shot</think>\nA techno wizard stands on a rooftop terrace."
    assert client.strip_model_wrapping(think) == "A techno wizard stands on a rooftop terrace."


def test_view_packs_are_camera_roles_without_lab_identity() -> None:
    nouns = (
        "penthouse",
        "sand linen",
        "techno wizard",
        "data-staff",
        "three-bay",
        "linen sofa",
    )
    names = (
        "place_10",
        "place_4",
        "character_sheet",
        "storyboard_6",
        "camera_angles",
        "lighting_3",
        "time_of_day_4",
        "color_moods_4",
    )
    for name in names:
        pack = client.load_view_pack(name)
        assert pack, name
        for card in pack:
            blob = f"{card['label']} {card['shot']}".lower()
            for noun in nouns:
                assert noun not in blob, (name, noun, card["label"])
    pack10 = client.load_view_pack("place_10")
    assert len(pack10) == 10
    labels = [card["label"] for card in pack10]
    assert labels == [
        "01 exterior",
        "02 entrance",
        "03 lounge",
        "04 kitchen",
        "05 dining",
        "06 bath",
        "07 bedroom",
        "08 terrace",
        "09 drone",
        "10 nook",
    ]
    blobs = {card["label"]: card["shot"].lower() for card in pack10}
    three_quarter = [
        lab for lab, text in blobs.items() if "three-quarter" in text and "ground-level" in text
    ]
    assert three_quarter == ["01 exterior"]
    assert "dusk" in blobs["01 exterior"]
    assert "establishing" in blobs["01 exterior"] or "only" in blobs["01 exterior"]
    assert "entrance" in blobs["02 entrance"] and "way in" in blobs["02 entrance"]
    assert "behind the camera" in blobs["02 entrance"]
    assert "seating" in blobs["03 lounge"] and "main opening" in blobs["03 lounge"]
    toward_opening = [
        lab
        for lab, text in blobs.items()
        if "toward the main opening" in text
        or "looks out that opening" in text
        or "out the main opening" in text
    ]
    assert toward_opening == ["03 lounge"]
    assert "kitchen" in blobs["04 kitchen"]
    assert "cabinets" in blobs["04 kitchen"] or "work surface" in blobs["04 kitchen"]
    assert "behind the camera" in blobs["04 kitchen"]
    assert "dining" in blobs["05 dining"]
    assert "out of frame" in blobs["05 dining"]
    assert "bathroom" in blobs["06 bath"] or "bathing" in blobs["06 bath"]
    assert "frosted" in blobs["06 bath"] or "opaque" in blobs["06 bath"]
    assert "bedroom" in blobs["07 bedroom"] and "bedding" in blobs["07 bedroom"]
    assert "headboard" in blobs["07 bedroom"]
    assert "along" in blobs["08 terrace"]
    assert "overhead" in blobs["09 drone"] or "drone" in blobs["09 drone"]
    assert "looking down" in blobs["09 drone"] or "roof" in blobs["09 drone"]
    assert "corner" in blobs["10 nook"] or "planted" in blobs["10 nook"]
    assert "sliver" in blobs["10 nook"]
    joined_cards = " ".join(blobs.values())
    assert "just inside" not in joined_cards
    assert "daylight exterior" not in joined_cards
    assert "night exterior" not in joined_cards
    assert blobs["03 lounge"] != blobs["04 kitchen"]
    assert blobs["05 dining"] != blobs["08 terrace"]


def test_studio_app_chrome_pack_exists() -> None:
    pack = ROOT / "custom_nodes" / "ez_studio_app"
    js = pack / "js" / "ez_studio_app.js"
    init = (pack / "__init__.py").read_text(encoding="utf-8")
    body = js.read_text(encoding="utf-8")
    assert "WEB_DIRECTORY" in init
    assert "ez_studio_app.chrome" in body
    assert "Rewrite prompt" in body
    assert "lab_app_mode" in body
    assert "execution_start" in body
    assert "SaveImage" in body
    assert "EZFilmConcat" in body


def test_web_directory_and_preview_js() -> None:
    assert ez_prompt_enhance.WEB_DIRECTORY == "./js"
    js = ROOT / "custom_nodes" / "ez_prompt_enhance" / "js" / "ez_prompt_enhance.js"
    body = js.read_text(encoding="utf-8")
    assert "onExecuted" in body
    assert "EZKleinPromptEnhance" in body
    assert "EZWanPromptEnhance" in body
    assert "EZLTXPromptEnhance" in body
    assert "EZAceStepPromptEnhance" in body
    assert "EZRapLyrics" in body
    assert "EZPodcastScript" in body
    assert "EZDubScript" in body
    assert "onNodeCreated" in body
    assert "CLIP prompt" in body
    assert "Enhance status" in body
    assert "passthrough" in body
    assert "serialize" in body
    assert "[passthrough:" not in body


def _isolate_gguf_roots(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Point every GGUF search root at an empty temp tree.

    Args:
        monkeypatch: Pytest env helper.
        tmp_path: Isolated directory.

    Returns:
        The models root used for snapshot / comfy/llm candidates.
    """
    models = tmp_path / "models"
    models.mkdir()
    monkeypatch.setenv("MODELS_ROOT", str(models))
    monkeypatch.setenv("MODELS_DIR", str(models))
    monkeypatch.setenv("COMFY_HOME", str(tmp_path / "ComfyUI"))
    monkeypatch.delenv("EZ_LLM_GGUF", raising=False)
    return models


def test_resolve_gguf_path_prefers_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    models = _isolate_gguf_roots(monkeypatch, tmp_path)
    snap = models / client.SNAPSHOT_DIR / client.GGUF_FILENAME
    snap.parent.mkdir(parents=True)
    snap.write_bytes(b"snap")
    custom = tmp_path / "custom.gguf"
    custom.write_bytes(b"env")
    monkeypatch.setenv("EZ_LLM_GGUF", str(custom))
    assert client.resolve_gguf_path() == str(custom)


def test_resolve_gguf_path_uses_snapshot_when_link_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    models = _isolate_gguf_roots(monkeypatch, tmp_path)
    snap = models / client.SNAPSHOT_DIR / client.GGUF_FILENAME
    snap.parent.mkdir(parents=True)
    snap.write_bytes(b"snap")
    assert Path(client.resolve_gguf_path()) == snap


def test_resolve_gguf_path_uses_comfy_llm_link(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    models = _isolate_gguf_roots(monkeypatch, tmp_path)
    linked = models / "comfy" / "llm" / client.GGUF_FILENAME
    linked.parent.mkdir(parents=True)
    linked.write_bytes(b"link")
    assert Path(client.resolve_gguf_path()) == linked


def test_enhance_false_skips_llm() -> None:
    with patch.object(client, "complete") as complete:
        out = client.enhance_prompt("sys", "user", enhance=False, fallback="lazy bike")
    assert out.text == "lazy bike"
    assert out.reason == client.REASON_ENHANCE_OFF
    assert out.preview == "lazy bike"
    assert out.status == "enhance off"
    complete.assert_not_called()


def test_missing_gguf_passthrough(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _isolate_gguf_roots(monkeypatch, tmp_path)
    monkeypatch.setenv("EZ_LLM_GGUF", str(tmp_path / "missing.gguf"))
    client._close_llm()
    with patch.object(client, "_generate") as gen:
        out = client.enhance_prompt("sys", "user", enhance=True, fallback="lazy bike")
    assert out.text == "lazy bike"
    assert out.reason == client.REASON_GGUF_MISSING
    assert out.preview == "lazy bike"
    assert "download-models" in out.status
    assert "[passthrough:" not in out.preview
    gen.assert_not_called()


def test_missing_llama_import_passthrough(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    gguf = tmp_path / "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
    gguf.write_bytes(b"fake")
    monkeypatch.setenv("EZ_LLM_GGUF", str(gguf))
    client._close_llm()
    with patch.dict(sys.modules, {"llama_cpp": None}):
        out = client.enhance_prompt("sys", "user", enhance=True, fallback="lazy bike")
    assert out.text == "lazy bike"
    assert out.reason == client.REASON_LLAMA_UNAVAILABLE


def test_empty_model_output_passthrough(monkeypatch: pytest.MonkeyPatch) -> None:
    with patch.object(client, "complete", return_value=("", client.REASON_EMPTY)):
        out = client.enhance_prompt("sys", "user", enhance=True, fallback="lazy bike")
    assert out.text == "lazy bike"
    assert out.reason == client.REASON_EMPTY
    assert out.preview == "lazy bike"
    assert "timeout or empty" in out.status


def test_success_strips_fences() -> None:
    with patch.object(
        client,
        "complete",
        return_value=("A photoreal still of a techno wizard.", None),
    ) as complete:
        out = client.enhance_prompt("sys", "hero still", enhance=True, fallback="hero still")
    assert out.text == "A photoreal still of a techno wizard."
    assert out.reason is None
    assert out.preview == out.text
    complete.assert_called_once()


def test_generate_uses_temperature_zero() -> None:
    class _FakeLlama:
        def create_chat_completion(self, **kwargs: object) -> dict:
            assert kwargs["temperature"] == 0
            assert kwargs["max_tokens"] == 800
            return {"choices": [{"message": {"content": "```\nrewritten\n```"}}]}

    assert client._generate(_FakeLlama(), "sys", "user") == "rewritten"


def test_n_gpu_layers_refused_without_allow(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EZ_LLM_N_GPU_LAYERS", "99")
    monkeypatch.delenv("EZ_LLM_ALLOW_GPU", raising=False)
    assert client._n_gpu_layers() == 0
    monkeypatch.setenv("EZ_LLM_ALLOW_GPU", "1")
    assert client._n_gpu_layers() == 99


def test_lab_graphs_use_model_native_prompts_and_enhance_nodes() -> None:
    from _lab_paths import lab_json

    draft = json.loads(lab_json("klein-still-draft-lab-example.json").read_text(encoding="utf-8"))
    hero = json.loads(lab_json("klein-still-hero-lab-example.json").read_text(encoding="utf-8"))
    klein_d = next(n for n in draft["nodes"] if n.get("type") == "EZKleinPromptEnhance")
    klein_h = next(n for n in hero["nodes"] if n.get("type") == "EZKleinPromptEnhance")
    assert klein_d["widgets_values"][0] == klein_h["widgets_values"][0]
    assert klein_d["widgets_values"][1] is True
    assert klein_h["widgets_values"][1] is True
    assert klein_d["widgets_values"][-1] == "none"
    wan_t = json.loads(lab_json("wan-t2v-5s-lab-example.json").read_text(encoding="utf-8"))
    wan_i = json.loads(lab_json("wan-i2v-5s-lab-example.json").read_text(encoding="utf-8"))
    ltx_t = json.loads(lab_json("ltx-t2v-5s-lab-example.json").read_text(encoding="utf-8"))
    ltx_i = json.loads(lab_json("ltx-i2v-5s-lab-example.json").read_text(encoding="utf-8"))
    wan_tp = next(n for n in wan_t["nodes"] if n.get("type") == "EZWanPromptEnhance")["widgets_values"][0]
    wan_ip = next(n for n in wan_i["nodes"] if n.get("type") == "EZWanPromptEnhance")["widgets_values"][0]
    ltx_tp = next(n for n in ltx_t["nodes"] if n.get("type") == "EZLTXPromptEnhance")["widgets_values"][0]
    ltx_ip = next(n for n in ltx_i["nodes"] if n.get("type") == "EZLTXPromptEnhance")["widgets_values"][0]
    assert "dollies" in wan_tp.lower() or "dolly" in wan_tp.lower()
    assert "score" not in wan_tp.lower()
    assert "start-image" in wan_ip.lower() or "start image" in wan_ip.lower()
    assert "score" not in wan_ip.lower()
    assert "YouTube 16:9 still:" not in wan_tp
    assert "wind" in ltx_tp.lower() or "traffic" in ltx_tp.lower()
    assert "no score" in ltx_ip.lower() or "no music" in ltx_ip.lower()
    assert not any(
        n.get("type") == "CLIPTextEncode" and n.get("title") == "Positive"
        for n in wan_i["nodes"]
    )


def test_ez_prompt_join_identity_and_shot() -> None:
    join = EZPromptJoin()
    view = join.run("Cedar house on a still lake.", "Golden-hour facade, 24mm.")
    assert view[0].startswith("Golden-hour facade, 24mm.")
    assert "Cedar house on a still lake." in view[0]
    assert "different camera" in view[0]
    assert "walkthrough" in view[0]
    assert "Same building" in view[0]
    assert "furniture placement" in view[0]
    assert "outlook that camera would see" in view[0]
    assert "sky, and background" not in view[0]
    trimmed = join.run("  House.  ", "  Dusk deck.  ")[0]
    assert trimmed.startswith("Dusk deck.")
    assert "House." in trimmed
    only = join.run("Identity only.", "")
    assert only[0].startswith("Identity only.")
    assert "different camera" in only[0]
    shot_only = join.run("", "Shot only.")[0]
    assert shot_only.startswith("Shot only.")
    assert "different camera" in shot_only
    assert join.run("  ", "  ") == ("",)
    locked = join.run("Cabin.", "Dawn deck.", "cedar siding, hip roof")
    assert locked[0].startswith("Dawn deck.")
    assert "Cabin." in locked[0]
    assert "Locked inventory (do not change): cedar siding, hip roof." in locked[0]
    assert "different camera" in locked[0]
    assert locked[0].endswith("cedar siding, hip roof.")
    state = join.run("Cabin.", "Warm key.", "mug", "state")
    assert state[0].startswith("Cabin.")
    assert "camera framing" in state[0]
    assert "The shot names the only change." in state[0]
    assert "mug" in state[0]
    assert state[0].endswith("Warm key.")
    types = EZPromptJoin.INPUT_TYPES()["required"]["lock"][0]
    assert types[0] == "view"
    assert "state" in types


def test_app_lab_graphs_wire_join_and_enhance() -> None:
    from _lab_paths import lab_json

    still = json.loads(lab_json("klein-still-daily-lab-example.json").read_text(encoding="utf-8"))
    gif = json.loads(lab_json("wan-gif-loop-lab-example.json").read_text(encoding="utf-8"))
    house = json.loads(lab_json("klein-dream-house-lab-example.json").read_text(encoding="utf-8"))
    klein = next(n for n in still["nodes"] if n.get("type") == "EZKleinPromptEnhance")
    assert klein["widgets_values"][1] is True
    assert klein["widgets_values"][-1] == "none"
    assert "photoreal still" in klein["widgets_values"][0]
    assert "techno wizard" in klein["widgets_values"][0]
    wan = next(n for n in gif["nodes"] if n.get("type") == "EZWanPromptEnhance")
    assert wan["widgets_values"][2] == "i2v"
    motion = wan["widgets_values"][0].lower()
    assert "dolly" not in motion
    assert "walk" not in motion
    ident = next(n for n in house["nodes"] if n.get("type") == "EZKleinPromptEnhance")
    ident_text = ident["widgets_values"][0]
    ident_l = ident_text.lower()
    assert "photoreal still" in ident_l
    assert "warm-glass" in ident_l
    assert "crown penthouse" in ident_l
    assert "wraparound terrace" in ident_l
    assert "three-bay" in ident_l
    assert "teak" in ident_l
    assert "fern" in ident_l or "living wall" in ident_l
    assert "coral-teal" in ident_l
    assert "lounge" in ident_l
    assert "lantern" in ident_l or "path light" in ident_l
    assert "bay" in ident_l
    assert "24mm" not in ident_l
    assert "golden-hour" not in ident_l and "golden hour" not in ident_l
    assert "cedar" not in ident_l
    assert "cabin" not in ident_l
    assert "lake" not in ident_l
    assert "no logos, no text" not in ident_text
    assert ident["widgets_values"][1] is True
    assert ident["widgets_values"][2] == "identity"
    assert ident["widgets_values"][3] == "Instagram 4:5 still"
    assert ident["widgets_values"][4] == "none"
    joins = [n for n in house["nodes"] if n.get("type") == "EZPromptJoin"]
    assert len(joins) == 10
    join_titles = [n["title"] for n in sorted(joins, key=lambda n: n["id"])]
    assert join_titles == [
        "SHOT 01 exterior",
        "SHOT 02 entrance",
        "SHOT 03 lounge",
        "SHOT 04 kitchen",
        "SHOT 05 dining",
        "SHOT 06 bath",
        "SHOT 07 bedroom",
        "SHOT 08 terrace",
        "SHOT 09 drone",
        "SHOT 10 nook",
    ]
    assert "cook wall" in ident_l
    positives = {
        n["title"]: n["widgets_values"][0]
        for n in house["nodes"]
        if n.get("type") == "CLIPTextEncode" and str(n.get("title", "")).startswith("Positive")
    }
    banned = (
        "pier",
        "courtyard",
        "pavilion",
        "two-story",
        "a-frame",
        "glass box",
        "outdoor kitchen",
        "outdoor tub",
        "cedar",
        "alpine",
        "gravel",
        "chimney",
        "hip roof",
        "live-action",
    )
    hidden_nouns = (
        "penthouse",
        "sand linen",
        "techno wizard",
        "data-staff",
        "three-bay",
        "linen sofa",
        "stone tub",
    )
    inventories = set()
    assert "linen sofa" in ident_l
    for i, join in enumerate(sorted(joins, key=lambda n: n["id"])):
        shot = join["widgets_values"][0]
        inventory = join["widgets_values"][1]
        lock = join["widgets_values"][2]
        inventories.add(inventory)
        assert lock == "view"
        assert inventory.strip() == ""
        shot_l = shot.lower()
        assert not any(noun in shot_l for noun in hidden_nouns)
        joined = client.join_prompt(ident_text, shot, inventory, lock)
        assert joined.startswith(shot)
        assert ident_text in joined
        assert len(joined.split()) <= 180
        assert not any(b in shot_l for b in banned)
        text = positives[f"Positive {i + 1:02d}"]
        assert text.startswith(shot)
        assert ident_text in text
        assert "different camera" in text
        assert "walkthrough" in text
        assert "outlook that camera would see" in text
        assert "sky, and background" not in text
        assert "linen sofa" in text
        assert len(text.split()) <= 180
    assert inventories == {""}
    assert sum(1 for n in house["nodes"] if n.get("type") == "VAEEncode") == 0
    assert sum(1 for n in house["nodes"] if n.get("type") == "ReferenceLatent") == 0
    by_id = {n["id"]: n for n in house["nodes"]}
    incoming: dict[tuple[int, int], list] = {}
    for link in house["links"]:
        incoming.setdefault((link[3], link[4]), []).append(link)
    for i in range(10):
        ks_id = 12 + i * 5
        pos_src = by_id[incoming[(ks_id, 1)][0][1]]["type"]
        lat_src = by_id[incoming[(ks_id, 3)][0][1]]["type"]
        assert lat_src == "EmptyFlux2LatentImage"
        assert pos_src == "CLIPTextEncode"


def test_node_mappings_modes_preview_and_style() -> None:
    assert set(NODE_CLASS_MAPPINGS) == {
        "EZKleinPromptEnhance",
        "EZWanPromptEnhance",
        "EZLTXPromptEnhance",
        "EZPromptJoin",
        "EZAceStepPromptEnhance",
    }
    klein = EZKleinPromptEnhance()
    wan = EZWanPromptEnhance()
    ltx = EZLTXPromptEnhance()
    assert klein.OUTPUT_NODE is True
    assert klein.INPUT_TYPES()["required"]["enhance"][1]["default"] is True
    styles = klein.INPUT_TYPES()["required"]["style"][0]
    assert styles[0] == "none"
    assert len(styles) == 51
    off = klein.run("A techno wizard.", False, "t2i", "YouTube 16:9 still")
    assert off["result"] == ("A techno wizard.",)
    assert off["ui"]["text"][0] == "A techno wizard."
    assert "[passthrough:" not in off["ui"]["text"][0]
    assert off["ui"]["passthrough"][0] == "enhance off"
    styled_off = klein.run("A rooftop.", False, "t2i", "", "photorealistic")
    assert "Photoreal photograph" in styled_off["result"][0]
    assert "[passthrough:" not in styled_off["result"][0]
    assert "[passthrough:" not in styled_off["ui"]["text"][0]
    with patch.object(
        client,
        "complete",
        return_value=("rewritten-klein", None),
    ) as mock:
        on = klein.run("bike", True, "edit", "", "none")
    assert on["result"] == ("rewritten-klein",)
    assert on["ui"]["text"][0] == "rewritten-klein"
    system = mock.call_args[0][0]
    assert "identity" in system.lower()
    with patch.object(client, "complete", return_value=("rewritten-style", None)) as mock:
        klein.run("photoreal 85mm portrait of a bike", True, "t2i", "", "anime")
    user = mock.call_args[0][1]
    assert "only look" in mock.call_args[0][0].lower()
    assert "Visual style (mandatory" in user
    assert "Japanese anime" in user
    assert "wins" in user.lower()
    assert "photoreal 85mm portrait of a bike" in user
    assert "Replace clauses" in user
    with patch.object(
        client,
        "complete",
        return_value=("A HD 3D game-engine pre-rendered cutscene still of a rooftop.", None),
    ):
        missing = klein.run("bike", True, "t2i", "", "watercolor_illustration")
    water = missing["result"][0].lower()
    assert "transparent watercolor" in water or "wet-into-wet" in water
    assert "game-engine" not in water
    with patch.object(client, "complete", return_value=("", client.REASON_GGUF_MISSING)):
        passthrough = klein.run("lazy bike", True, "t2i", "", "photorealistic")
    assert "photoreal" in passthrough["result"][0].lower() or "still photograph" in passthrough[
        "result"
    ][0].lower()
    assert "[passthrough:" not in passthrough["ui"]["text"][0]
    assert "download-models" in passthrough["ui"]["passthrough"][0]
    with patch.object(
        client,
        "complete",
        return_value=("A red bicycle on a hill.", None),
    ):
        hill = klein.run("bike", True, "t2i", "", "watercolor_illustration")
    assert "transparent watercolor" in hill["result"][0].lower() or "wet-into-wet" in hill[
        "result"
    ][0].lower()
    with patch.object(
        client,
        "complete",
        return_value=("A bicycle as transparent watercolor on paper tooth.", None),
    ):
        kept = klein.run("bike", True, "t2i", "", "watercolor_illustration")
    assert "transparent watercolor" in kept["result"][0].lower()
    assert "bicycle" in kept["result"][0].lower()
    with patch.object(client, "complete", return_value=("same mug watercolor", None)) as mock:
        klein.run("photoreal product shot of the same mug", True, "edit", "", "watercolor_illustration")
    edit_system = mock.call_args[0][0]
    edit_user = mock.call_args[0][1]
    assert "identity" in edit_system.lower()
    assert "visual-style" in edit_system.lower()
    assert "transparent watercolor" in edit_user.lower()
    assert "inventory" in edit_user.lower()
    with patch.object(client, "complete", return_value=("rewritten-wan", None)) as mock:
        wan.run("push in", True, "i2v", "5 seconds, 24 fps", "anime")
    wan_user = mock.call_args[0][1]
    assert "Motion + Camera" in mock.call_args[0][0]
    assert "Visual style" not in wan_user
    with patch.object(client, "complete", return_value=("rewritten-wan-t2v", None)) as mock:
        wan.run("a cat walks", True, "t2v", "5 seconds, 24 fps", "anime")
    wan_t2v_user = mock.call_args[0][1]
    assert "Visual style (mandatory" in wan_t2v_user
    assert "2D anime" in wan_t2v_user
    with patch.object(client, "complete", return_value=("rewritten-ltx", None)) as mock:
        ltx.run("bike moves", True, "t2v", "5 seconds, 24 fps", "wind, no score")
    user = mock.call_args[0][1]
    assert "Audio notes: wind, no score" in user
    assert "Duration / framing: 5 seconds, 24 fps" in user
    with patch.object(client, "complete", return_value=("rewritten-ltx-style", None)) as mock:
        ltx.run("bike moves", True, "t2v", "5 seconds, 24 fps", "wind", "oil_painting")
    ltx_user = mock.call_args[0][1]
    assert "oil painting" in ltx_user.lower()
    assert "coherent light" in ltx_user.lower()
    klein_modes = klein.INPUT_TYPES()["required"]["mode"][0]
    assert "identity" in klein_modes
    wan_modes = wan.INPUT_TYPES()["required"]["mode"][0]
    assert wan_modes == ["t2v", "i2v", "flf", "vace"]
    with patch.object(client, "complete", return_value=("bible", None)) as mock:
        ident_out = klein.run("cedar cabin", True, "identity", "", "anime")
    ident_clip = ident_out["result"][0].lower()
    assert "bible" in ident_clip
    assert "japanese anime" in ident_clip or "cel" in ident_clip
    assert "camera-free" in mock.call_args[0][0].lower()
    assert "Visual style" in mock.call_args[0][1]
    with patch.object(client, "complete", return_value=("flf-motion", None)) as mock:
        wan.run("between frames", True, "flf", "5 seconds, 24 fps", "anime")
    assert "end frame" in mock.call_args[0][0].lower() or "first-last" in mock.call_args[0][0].lower()
    assert "Visual style" not in mock.call_args[0][1]


def test_ace_step_enhance_node_defaults_and_modes() -> None:
    ace = EZAceStepPromptEnhance()
    spec = ace.INPUT_TYPES()["required"]
    assert spec["enhance"][1]["default"] is True
    assert spec["mode"][0] == ["vocal", "instrumental"]
    off = ace.run("boom bap, 88 bpm", "[verse]\nhi", False, "vocal")
    assert off["result"] == ("boom bap, 88 bpm", "[verse]\nhi")
    assert off["ui"]["passthrough"][0] == "enhance off"
    inst_off = ace.run("lo-fi keys", "", False, "instrumental")
    assert "instrumental" in inst_off["result"][0].lower()
    assert inst_off["result"][1] == "[inst]"
    with patch("ez_prompt_enhance.nodes.complete", side_effect=[("boom bap, dusty drums, 88 bpm", None), ("[verse]\nrewritten", None)]):
        with patch("ez_prompt_enhance.nodes._close_llm"):
            on = ace.run("lazy beat", "[verse]\nhi", True, "vocal")
    assert on["result"][0].startswith("boom bap")
    assert "[verse]" in on["result"][1]
    with patch("ez_prompt_enhance.nodes.complete", return_value=("lo-fi, warm keys, instrumental, no vocals", None)):
        with patch("ez_prompt_enhance.nodes._close_llm"):
            bed = ace.run("lo-fi bed", "", True, "instrumental")
    assert "instrumental" in bed["result"][0].lower()
    assert bed["result"][1] == "[inst]"


def test_lab_graphs_wire_enhance_on_every_positive_prompt() -> None:
    """Every lab CLIP/ACE positive prompt comes from an EZ enhance node, enhance on.

    go-see pins Enhance off so the body-cam bible is encoded as written.
    """
    skip_ids = {"longcat-video-lab-example"}
    pin_off_ids = {"film-go-see-90s-run-lab-example"}
    enhance_types = {
        "EZKleinPromptEnhance",
        "EZWanPromptEnhance",
        "EZLTXPromptEnhance",
        "EZAceStepPromptEnhance",
        "EZRapLyrics",
        "EZPodcastScript",
    }
    encoder_types = {"CLIPTextEncode", "TextEncodeAceStepAudio1.5"}
    wf_root = ROOT / "workflows"
    missing: list[str] = []
    for path in sorted(wf_root.rglob("*-lab-example.json")):
        graph = json.loads(path.read_text(encoding="utf-8"))
        gid = str(graph.get("id") or path.stem)
        if gid in skip_ids:
            continue
        by_id = {int(n["id"]): n for n in graph["nodes"]}
        links = {int(link[0]): link for link in graph.get("links") or []}
        for node in graph["nodes"]:
            ntype = node.get("type")
            if ntype in enhance_types:
                values = node.get("widgets_values") or []
                flag = values[1] if ntype != "EZAceStepPromptEnhance" else (
                    values[2] if len(values) > 2 else True
                )
                if ntype == "EZAceStepPromptEnhance":
                    flag = values[2] if len(values) > 2 else True
                if gid in pin_off_ids:
                    if flag is not False:
                        missing.append(
                            f"{path.name}: {ntype}#{node['id']} enhance={flag!r}"
                        )
                elif flag is not True:
                    missing.append(f"{path.name}: {ntype}#{node['id']} enhance={flag!r}")
            if ntype not in encoder_types:
                continue
            title = str(node.get("title") or "")
            if "neg" in title.lower():
                continue
            if ntype == "CLIPTextEncode":
                text_inp = next(
                    (i for i in node.get("inputs") or [] if i.get("name") == "text"),
                    None,
                )
                if text_inp is None or text_inp.get("link") is None:
                    missing.append(f"{path.name}: CLIP {title!r} has no text link")
                    continue
                src = by_id.get(int(links[int(text_inp["link"])][1]))
                if src is None:
                    missing.append(f"{path.name}: CLIP {title!r} missing text source")
                    continue
                if src.get("type") in enhance_types:
                    continue
                if src.get("type") == "EZPromptJoin":
                    ident_inp = next(
                        (i for i in src.get("inputs") or [] if i.get("name") == "identity"),
                        None,
                    )
                    ident_src = None
                    if ident_inp and ident_inp.get("link") is not None:
                        ident_src = by_id.get(int(links[int(ident_inp["link"])][1]))
                    if ident_src and ident_src.get("type") in enhance_types:
                        continue
                missing.append(
                    f"{path.name}: CLIP {title!r} fed by {src.get('type')}"
                )
            elif ntype == "TextEncodeAceStepAudio1.5":
                tags_inp = next(
                    (i for i in node.get("inputs") or [] if i.get("name") == "tags"),
                    None,
                )
                lyrics_inp = next(
                    (i for i in node.get("inputs") or [] if i.get("name") == "lyrics"),
                    None,
                )
                linked = False
                for inp in (tags_inp, lyrics_inp):
                    if inp and inp.get("link") is not None:
                        src = by_id.get(int(links[int(inp["link"])][1]))
                        if src and src.get("type") in enhance_types:
                            linked = True
                if not linked:
                    missing.append(f"{path.name}: ACE encoder {title!r} not fed by enhance")
    assert not missing, "\n".join(missing[:40])
