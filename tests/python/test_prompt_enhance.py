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


def test_strip_fences_quotes_and_think() -> None:
    fenced = "```text\nA cyberpunk tech wizard stands on a rooftop terrace.\n```"
    assert client.strip_model_wrapping(fenced) == "A cyberpunk tech wizard stands on a rooftop terrace."
    assert client.strip_model_wrapping('"A cyberpunk tech wizard."') == "A cyberpunk tech wizard."
    think = "<think>plan the shot</think>\nA cyberpunk tech wizard stands on a rooftop terrace."
    assert client.strip_model_wrapping(think) == "A cyberpunk tech wizard stands on a rooftop terrace."


def test_web_directory_and_preview_js() -> None:
    assert ez_prompt_enhance.WEB_DIRECTORY == "./js"
    js = ROOT / "custom_nodes" / "ez_prompt_enhance" / "js" / "ez_prompt_enhance.js"
    body = js.read_text(encoding="utf-8")
    assert "onExecuted" in body
    assert "EZKleinPromptEnhance" in body
    assert "EZWanPromptEnhance" in body
    assert "EZLTXPromptEnhance" in body
    assert "CLIP prompt" in body
    assert "serialize" in body


def test_enhance_false_skips_llm() -> None:
    with patch.object(client, "complete") as complete:
        out = client.enhance_prompt("sys", "user", enhance=False, fallback="lazy bike")
    assert out.text == "lazy bike"
    assert out.reason == client.REASON_ENHANCE_OFF
    assert out.preview.startswith("[passthrough: enhance off]")
    complete.assert_not_called()


def test_missing_gguf_passthrough(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("EZ_LLM_GGUF", str(tmp_path / "missing.gguf"))
    client._close_llm()
    with patch.object(client, "_generate") as gen:
        out = client.enhance_prompt("sys", "user", enhance=True, fallback="lazy bike")
    assert out.text == "lazy bike"
    assert out.reason == client.REASON_GGUF_MISSING
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
    assert "timeout or empty" in out.preview


def test_success_strips_fences() -> None:
    with patch.object(
        client,
        "complete",
        return_value=("A HD 3D game-engine pre-rendered cutscene still of a cyberpunk tech wizard.", None),
    ) as complete:
        out = client.enhance_prompt("sys", "hero still", enhance=True, fallback="hero still")
    assert out.text == "A HD 3D game-engine pre-rendered cutscene still of a cyberpunk tech wizard."
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
    wf = ROOT / "workflows"
    draft = json.loads((wf / "klein-still-draft-lab-example.json").read_text(encoding="utf-8"))
    hero = json.loads((wf / "klein-still-hero-lab-example.json").read_text(encoding="utf-8"))
    klein_d = next(n for n in draft["nodes"] if n.get("type") == "EZKleinPromptEnhance")
    klein_h = next(n for n in hero["nodes"] if n.get("type") == "EZKleinPromptEnhance")
    assert klein_d["widgets_values"][0] == klein_h["widgets_values"][0]
    assert klein_d["widgets_values"][1] is True
    assert klein_d["widgets_values"][-1] == "none"
    wan_t = json.loads((wf / "wan-t2v-5s-lab-example.json").read_text(encoding="utf-8"))
    wan_i = json.loads((wf / "wan-i2v-5s-lab-example.json").read_text(encoding="utf-8"))
    ltx_t = json.loads((wf / "ltx-t2v-5s-lab-example.json").read_text(encoding="utf-8"))
    ltx_i = json.loads((wf / "ltx-i2v-5s-lab-example.json").read_text(encoding="utf-8"))
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
    assert view[0].startswith("Cedar house on a still lake.")
    assert "different camera" in view[0]
    assert view[0].endswith("Golden-hour facade, 24mm.")
    assert join.run("  House.  ", "  Dusk deck.  ")[0].endswith("Dusk deck.")
    only = join.run("Identity only.", "")
    assert "Identity only." in only[0]
    assert "different camera" in only[0]
    assert join.run("", "Shot only.")[0].endswith("Shot only.")
    assert join.run("  ", "  ") == ("",)
    locked = join.run("Cabin.", "Dawn deck.", "cedar siding, hip roof")
    assert "Locked inventory (do not change): cedar siding, hip roof." in locked[0]
    assert "different camera" in locked[0]
    assert locked[0].endswith("Dawn deck.")
    state = join.run("Cabin.", "Warm key.", "mug", "state")
    assert "camera framing" in state[0]
    assert "The shot names the only change." in state[0]
    assert "mug" in state[0]
    types = EZPromptJoin.INPUT_TYPES()["required"]["lock"][0]
    assert types[0] == "view"
    assert "state" in types


def test_app_lab_graphs_wire_join_and_enhance() -> None:
    wf = ROOT / "workflows"
    still = json.loads((wf / "klein-still-daily-lab-example.json").read_text(encoding="utf-8"))
    gif = json.loads((wf / "wan-gif-loop-lab-example.json").read_text(encoding="utf-8"))
    house = json.loads((wf / "klein-dream-house-lab-example.json").read_text(encoding="utf-8"))
    klein = next(n for n in still["nodes"] if n.get("type") == "EZKleinPromptEnhance")
    assert klein["widgets_values"][1] is True
    assert klein["widgets_values"][-1] == "none"
    assert "HD 3D game-engine pre-rendered cutscene still" in klein["widgets_values"][0]
    assert "tech wizard" in klein["widgets_values"][0]
    wan = next(n for n in gif["nodes"] if n.get("type") == "EZWanPromptEnhance")
    assert wan["widgets_values"][2] == "i2v"
    motion = wan["widgets_values"][0].lower()
    assert "dolly" not in motion
    assert "walk" not in motion
    ident = next(n for n in house["nodes"] if n.get("type") == "EZKleinPromptEnhance")
    ident_text = ident["widgets_values"][0]
    ident_l = ident_text.lower()
    assert "cedar" in ident_l
    assert "lake" in ident_l
    assert "compact" in ident_l
    assert "single-story" in ident_l
    assert "hip" in ident_l
    assert "chimney" in ident_l
    assert "two-bay" in ident_l
    assert "decks" in ident_l
    assert "gravel" in ident_l
    assert "24mm" not in ident_l
    assert "golden-hour" not in ident_l and "golden hour" not in ident_l
    assert "no logos, no text" not in ident_text
    assert ident["widgets_values"][1] is False
    assert ident["widgets_values"][2] == "t2i"
    assert ident["widgets_values"][3] == "Instagram 4:5 still"
    assert ident["widgets_values"][4] == "none"
    joins = [n for n in house["nodes"] if n.get("type") == "EZPromptJoin"]
    assert len(joins) == 10
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
    )
    inventories = set()
    for join in sorted(joins, key=lambda n: n["id"]):
        shot = join["widgets_values"][0]
        inventory = join["widgets_values"][1]
        lock = join["widgets_values"][2]
        inventories.add(inventory)
        assert lock == "view"
        assert "linen sofa" in inventory
        assert "island" in inventory
        assert "dining table" in inventory
        assert "bedding" in inventory
        assert "tub" in inventory
        assert "deck chairs" in inventory or "cedar deck" in inventory
        assert "same" in shot.lower() and "cabin" in shot.lower()
        joined = client.join_prompt(ident_text, shot, inventory, lock)
        assert len(joined.split()) <= 170
        title = join.get("title") or ""
        if "01" in title:
            assert "through" in shot.lower() or "shows the linen sofa" in shot.lower()
        if any(k in title for k in ("03 living", "04 kitchen", "05 dining", "06 bedroom", "07 bath")):
            assert "from inside" in shot.lower()
        if "03 living" in title:
            assert "sofa" in shot.lower()
        assert not any(b in shot.lower() for b in banned)
    assert len(inventories) == 1
    for text in positives.values():
        assert text.startswith(ident_text)
        assert "different camera" in text
        assert "linen sofa" in text
        assert len(text.split()) <= 170
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
    }
    klein = EZKleinPromptEnhance()
    wan = EZWanPromptEnhance()
    ltx = EZLTXPromptEnhance()
    assert klein.OUTPUT_NODE is True
    assert klein.INPUT_TYPES()["required"]["enhance"][1]["default"] is True
    styles = klein.INPUT_TYPES()["required"]["style"][0]
    assert styles[0] == "none"
    assert len(styles) == 51
    off = klein.run("A cyberpunk tech wizard.", False, "t2i", "YouTube 16:9 still")
    assert off["result"] == ("A cyberpunk tech wizard.",)
    assert off["ui"]["text"][0].startswith("[passthrough: enhance off]")
    styled_off = klein.run("A rooftop.", False, "t2i", "", "photorealistic")
    assert "Photoreal photograph" in styled_off["result"][0]
    assert "[passthrough:" not in styled_off["result"][0]
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
    assert passthrough["ui"]["text"][0].startswith("[passthrough:")
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
