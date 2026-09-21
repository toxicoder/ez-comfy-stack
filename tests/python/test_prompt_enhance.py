"""Hermetic tests for ez_prompt_enhance (no Comfy, no network, no GGUF)."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import types
from collections.abc import Iterator
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
    EZContextJoin,
    EZDreamXPromptEnhance,
    EZKleinPromptEnhance,
    EZLongCatPromptEnhance,
    EZLTXPromptEnhance,
    EZNegativePromptEnhance,
    EZPromptBundle,
    EZPromptJoin,
    EZSamplePrompt,
    EZWanPromptEnhance,
    EZZimagePromptEnhance,
    NODE_CLASS_MAPPINGS,
    sanitize_instrumental_lyrics,
)
from ez_prompt_enhance.samples import CUSTOM as SAMPLE_CUSTOM  # noqa: E402


def _enh_prompt(values: list) -> str:
    if len(values) >= 7:
        return str(values[1])
    return str(values[0])


def _enh_flag(values: list) -> object:
    if len(values) >= 7:
        return values[2]
    return values[1]


def _enh_mode(values: list) -> object:
    if len(values) >= 7:
        return values[3]
    return values[2]


def _enh_style(values: list) -> object:
    if len(values) >= 7:
        return values[5] if len(values) == 7 else values[-2]
    return values[-1]


def _no_network_pip(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["pip", "install", *args],
        returncode=1,
        stdout="",
        stderr="test: pip disabled",
    )


def _sidecar_down(*_args: object, **_kwargs: object) -> object:
    raise TimeoutError("sidecar down")


@pytest.fixture(autouse=True)
def _reset_llama_runtime(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Reset llama.cpp state and block host pip (hermetic)."""
    client.reset_llama_runtime_for_tests()
    monkeypatch.setattr(client, "_pip_install", _no_network_pip)
    monkeypatch.setattr(client, "_urlopen_sidecar", _sidecar_down)
    yield
    client.reset_llama_runtime_for_tests()


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
    assert "shot size" in klein.lower()
    assert "cinema rack" in klein.lower()
    assert "rembrandt" in klein.lower() or "golden hour" in klein.lower()
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
    assert "cinema rack" in wan_t2v.lower()
    assert "pan left" in wan_t2v.lower() or "wan_token" in wan_t2v.lower()
    wan_i2v = client.load_system_prompt("wan_i2v")
    assert "Motion + Camera" in wan_i2v
    assert "audio" in wan_i2v.lower()
    assert "new objects" in wan_i2v.lower()
    assert "fixed camera" in wan_i2v.lower()
    ltx_t2v = client.load_system_prompt("ltx_t2v")
    assert "present" in ltx_t2v.lower()
    assert "quotation" in ltx_t2v.lower()
    assert "interleaved" in ltx_t2v.lower()
    assert "visual-style" in ltx_t2v.lower()
    ltx_i2v = client.load_system_prompt("ltx_i2v")
    assert "first frame" in ltx_i2v.lower()
    assert "camera motion" in ltx_i2v.lower()
    assert "new objects" in ltx_i2v.lower()
    swap = client.load_system_prompt("klein_text_swap")
    assert "lettering" in swap.lower()
    assert "spell" in swap.lower()
    assert "typeface" in swap.lower()
    assert "cinema rack" not in swap.lower()
    bg_swap = client.load_system_prompt("klein_background_swap")
    assert "ground" in bg_swap.lower()
    assert "environment" in bg_swap.lower()
    assert "photographed place" in bg_swap.lower()
    assert "texel" in bg_swap.lower() or "texture-pack" in bg_swap.lower()
    assert "generic cube biome" in bg_swap.lower()
    assert "minecraft" not in bg_swap.lower()
    bg_edit = client.load_system_prompt("klein_background_edit")
    assert "cartoon" in bg_edit.lower()
    assert "environment" in bg_edit.lower()
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
    assert "interior wall" in ident_l
    assert "paste" in ident_l
    assert "window" in ident_l
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
    assert "empty-body" in ace_inst.lower() or "inside the brackets" in ace_inst.lower()
    for stem in ("negative_klein", "negative_wan", "negative_ltx"):
        neg = client.load_system_prompt(stem)
        assert "comma" in neg.lower() or "comma-separated" in neg.lower()
        assert "positive" in neg.lower()
        assert "watermark" in neg.lower() or "artifact" in neg.lower()
    ltx_neg = client.load_system_prompt("negative_ltx")
    assert "audio" in ltx_neg.lower() or "foley" in ltx_neg.lower()
    klein_neg = client.load_system_prompt("negative_klein")
    assert "base" in klein_neg.lower()
    assert "five fingers" in klein.lower()
    assert "extra fingers" in client.load_system_prompt("negative_wan").lower()
    assert "fused fingers" in client.load_system_prompt("negative_wan").lower()
    assert "do not write the duration" in ltx_t2v.lower()
    ltx_neg_l = ltx_neg.lower()
    assert "ethnicity" not in ltx_neg_l
    assert "wrong hand count" in ltx_neg_l
    wan_t2v_l = wan_t2v.lower()
    assert "a14b" in wan_t2v_l
    s2v = client.load_system_prompt("wan_s2v")
    assert "wav" in s2v.lower()
    assert "lip-sync" in s2v.lower() or "lip sync" in s2v.lower()
    iclora = client.load_system_prompt("ltx_iclora")
    assert "depth" in iclora.lower() or "canny" in iclora.lower()
    assert "control type" in iclora.lower() or "pose" in iclora.lower()
    zimage = client.load_system_prompt("zimage_t2i")
    assert "five fingers" in zimage.lower()
    assert "Qwen3-4B" in zimage
    assert "<|im_start|>" in zimage
    assert "80" in zimage and "250" in zimage
    assert "negative" in zimage.lower()
    long_t2v = client.load_system_prompt("longcat_t2v")
    assert "scene" in long_t2v.lower()
    assert "cfg" in long_t2v.lower()
    long_i2v = client.load_system_prompt("longcat_i2v")
    assert "still" in long_i2v.lower() or "start image" in long_i2v.lower()
    long_vc = client.load_system_prompt("longcat_vc")
    assert "continuation" in long_vc.lower() or "previous" in long_vc.lower()
    dreamx = client.load_system_prompt("dreamx_i2v")
    assert "first frame" in dreamx.lower()
    assert "audio" in dreamx.lower() or "acoustic" in dreamx.lower()
    z_neg = client.load_system_prompt("negative_zimage")
    assert "comma" in z_neg.lower()
    assert "watermark" in z_neg.lower() or "artifact" in z_neg.lower()
    lc_neg = client.load_system_prompt("negative_longcat")
    assert "overexposed" in lc_neg.lower() or "static" in lc_neg.lower()
    dx_neg = client.load_system_prompt("negative_dreamx")
    assert "audio" in dx_neg.lower() or "foley" in dx_neg.lower()
    s2v_neg = client.load_system_prompt("negative_wan_s2v")
    assert "wav" in s2v_neg.lower()
    assert client.NEGATIVE_FAMILIES == (
        "klein",
        "wan",
        "ltx",
        "zimage",
        "longcat",
        "dreamx",
        "s2v",
    )


_ALLOWED_STYLE_FAMILIES = frozenset(
    {"photography", "illustration", "animation_3d", "fine_art", "genre"}
)
_FIRST_FIFTY_STYLE_IDS = (
    "photorealistic",
    "cinematic_film_still",
    "documentary_photography",
    "analog_35mm_film",
    "analog_120_medium_format",
    "polaroid_instant",
    "golden_hour_photography",
    "overcast_natural_light",
    "studio_product_photography",
    "editorial_fashion_photography",
    "street_photography",
    "architectural_photography",
    "anime",
    "manga_screentone",
    "cartoon",
    "western_comic_book",
    "saturday_morning_cartoon",
    "storybook_illustration",
    "watercolor_illustration",
    "gouache_illustration",
    "ink_and_wash",
    "colored_pencil",
    "charcoal_sketch",
    "line_art",
    "cel_shaded",
    "risograph_print",
    "3d_feature_animation",
    "pixar_like_3d",
    "claymation",
    "stop_motion",
    "unreal_engine_cinematic",
    "isometric_3d",
    "low_poly",
    "voxel",
    "oil_painting",
    "impressionist_painting",
    "cubist",
    "art_nouveau",
    "ukiyo_e_woodblock",
    "baroque_oil",
    "digital_matte_painting",
    "concept_art",
    "cyberpunk",
    "solarpunk",
    "film_noir",
    "1970s_grain",
    "vaporwave",
    "pixel_art",
    "papercraft",
    "blueprint_technical_drawing",
)


def test_style_catalog_is_unique() -> None:
    styles = client.load_styles()
    assert len(styles) == 300
    assert len(set(styles)) == 300
    assert "none" not in styles
    ids = client.style_ids()
    assert ids[0] == "none"
    assert len(ids) == 301
    assert tuple(list(styles)[:50]) == _FIRST_FIFTY_STYLE_IDS
    labels: list[str] = []
    medium_heads: list[str] = []
    suffixes: list[str] = []
    for sid, entry in styles.items():
        assert re.fullmatch(r"[a-z0-9][a-z0-9_]*", sid), sid
        label = str(entry["label"]).strip()
        assert label, sid
        labels.append(label.casefold())
        family = str(entry["family"]).strip()
        assert family in _ALLOWED_STYLE_FAMILIES, sid
        for field in _STYLE_WOVEN_FIELDS:
            blob = str(entry[field]).strip()
            assert blob, sid
            lower = blob.lower()
            assert "no photoreal" not in lower
            for brand in _BANNED_STYLE_BRANDS:
                assert brand not in lower, f"{sid}.{field} has {brand}"
        head = str(entry["medium"]).split(".")[0].strip()
        assert len(head) >= 8, sid
        medium_heads.append(head.casefold())
        suffixes.append(str(entry["suffix"]).strip().casefold())
        must = entry["must_include"]
        conflicts = entry["conflicts"]
        assert isinstance(must, list) and len(must) >= 2, sid
        assert isinstance(conflicts, list) and conflicts, sid
        for phrase in must:
            assert str(phrase).strip()
            lower = str(phrase).lower()
            for brand in _BANNED_STYLE_BRANDS:
                assert brand not in lower, f"{sid} must_include has {brand}"
    assert len(labels) == len(set(labels))
    assert len(medium_heads) == len(set(medium_heads))
    assert len(suffixes) == len(set(suffixes))
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


_KLEIN_NEG_SEED = (
    "game-engine cutscene, Pixar rounded cartoon, illustration, muddy textures, "
    "melted geometry, duplicate limbs, watermarks, oversharpen halos, muddy blacks"
)


def test_complement_negative_drops_look_fights_keeps_artifacts() -> None:
    watercolor = (
        "Transparent watercolor on paper. A rooftop terrace at golden hour, "
        "wet-into-wet blooms and paper tooth."
    )
    out = client.complement_negative(_KLEIN_NEG_SEED, watercolor)
    lower = out.lower()
    assert "illustration" not in lower
    assert "watermark" in lower
    assert "melted geometry" in lower
    photoreal = (
        "Still photograph from a real camera, captured in the moment. "
        "A rooftop terrace, physically plausible light, material microdetail."
    )
    photo = client.complement_negative(_KLEIN_NEG_SEED, photoreal)
    photo_l = photo.lower()
    assert "illustration" in photo_l
    assert "pixar" in photo_l
    assert "watermark" in photo_l
    empty = client.complement_negative(_KLEIN_NEG_SEED, "")
    assert empty == _KLEIN_NEG_SEED
    assert client.complement_negative("", watercolor) == ""
    pixar = (
        "Stylized feature 3D with appealing proportions. A rooftop, "
        "soft global illumination."
    )
    pix = client.complement_negative(_KLEIN_NEG_SEED, pixar).lower()
    assert "pixar" not in pix
    assert "watermark" in pix
    hands = client.complement_negative(
        "extra fingers, watermark",
        "She closes her fingers around the cup.",
    )
    assert "extra fingers" in hands.lower()
    assert "watermark" in hands.lower()
    six = client.complement_negative(
        "extra fingers, watermark",
        "A six-fingered hand rests on the table.",
    )
    assert "extra fingers" not in six.lower()
    assert "watermark" in six.lower()
    held = client.complement_negative(
        "static, watermark",
        "The subject is completely still, no motion.",
    )
    assert "static" not in held.lower()
    assert "watermark" in held.lower()
    user = client.compose_negative_user("illustration, watermarks", watercolor)
    assert user.startswith("POSITIVE:")
    assert "NEGATIVE SEED:" in user
    assert "illustration, watermarks" in user
    assert "Transparent watercolor" in user


def test_negative_prompt_enhance_uses_positive_context() -> None:
    node = EZNegativePromptEnhance()
    types = node.INPUT_TYPES()
    assert types["required"]["enhance"][1]["default"] is True
    assert types["required"]["family"][0] == [
        "klein",
        "wan",
        "ltx",
        "zimage",
        "longcat",
        "dreamx",
        "s2v",
    ]
    assert types["optional"]["positive"][1]["forceInput"] is True
    assert node.OUTPUT_NODE is True
    watercolor = "Transparent watercolor on paper. A rooftop, wet-into-wet, paper tooth."
    off = node.run(_KLEIN_NEG_SEED, False, "klein", watercolor)
    assert off["ui"]["passthrough"][0] == "enhance off"
    assert "illustration" not in off["result"][0].lower()
    assert "watermark" in off["result"][0].lower()
    with patch(
        "ez_prompt_enhance.nodes.complete",
        return_value=("illustration, watermarks", None),
    ) as mock:
        on = node.run(_KLEIN_NEG_SEED, True, "wan", watercolor)
    assert mock.call_args.kwargs.get("max_tokens") == 200
    system, user = mock.call_args[0][0], mock.call_args[0][1]
    assert "POSITIVE:" in user
    assert "NEGATIVE SEED:" in user
    assert _KLEIN_NEG_SEED.split(",")[0] in user or "game-engine" in user
    assert "watermark" in system.lower() or "artifact" in system.lower()
    assert "illustration" not in on["result"][0].lower()
    assert "watermark" in on["result"][0].lower()
    with patch(
        "ez_prompt_enhance.nodes.complete",
        return_value=("", "GGUF missing"),
    ):
        miss = node.run(_KLEIN_NEG_SEED, True, "ltx", watercolor)
    assert miss["ui"]["passthrough"][0]
    assert "watermark" in miss["result"][0].lower()
    assert "illustration" not in miss["result"][0].lower()


def test_strip_fences_quotes_and_think() -> None:
    fenced = "```text\nA techno wizard stands on a rooftop terrace.\n```"
    assert client.strip_model_wrapping(fenced) == "A techno wizard stands on a rooftop terrace."
    assert client.strip_model_wrapping('"A techno wizard."') == "A techno wizard."
    think = "<think>plan the shot</think>\nA techno wizard stands on a rooftop terrace."
    assert client.strip_model_wrapping(think) == "A techno wizard stands on a rooftop terrace."


# Identity nouns that place_10 shots must not bake in. Labels may still
# name camera stations (tower, foyer, kitchen); CLIP text is camera-only.
PLACE_10_IDENTITY_LEAKS = (
    "dusk",
    "elevator",
    "stone",
    "unmarked tower",
    "canyon",
    "neighboring",
    "skyline",
    "roofs",
    "frosted",
    "opaque",
    "cook wall",
    "headboard",
    "lantern",
    "planting",
    "master",
    "crown",
    "street",
    "city",
    "cabinet",
    "bedding",
    "desk",
    "shelf",
    "seating",
    "warm practical",
    "teak",
    "linen",
    "marble",
    "sofa",
    "tub",
    "villa",
    "cabin",
    "cottage",
    "mansion",
    "loft",
    "bungalow",
    "penthouse",
    "walnut",
    "oak",
    "brass",
    "concrete",
    "stucco",
)
PLACE_10_JOIN_CAP = 220


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
        "01 tower",
        "02 foyer",
        "03 lounge",
        "04 kitchen",
        "05 dining",
        "06 bedroom",
        "07 bath",
        "08 terrace",
        "09 drone",
        "10 study",
    ]
    blobs = {card["label"]: card["shot"].lower() for card in pack10}
    for lab, text in blobs.items():
        for leak in PLACE_10_IDENTITY_LEAKS:
            assert leak not in text, (lab, leak)
        assert "instagram 4:5" in text
        assert "24mm" in text or "35mm" in text
    assert "ground-level" not in blobs["01 tower"]
    assert "three-quarter" not in blobs["01 tower"]
    assert "tower" not in blobs["01 tower"]
    assert "looking up" in blobs["01 tower"]
    assert "establishing" in blobs["01 tower"]
    assert "arrival" in blobs["01 tower"]
    assert "lower third" in blobs["01 tower"]
    assert "vertical" in blobs["01 tower"]
    assert "unoccupied" in blobs["01 tower"]
    assert "surroundings are only what the bible named" in blobs["01 tower"]
    assert "24mm" in blobs["01 tower"]
    assert "way in" in blobs["02 foyer"]
    assert "behind the camera" in blobs["02 foyer"]
    assert "threshold" in blobs["02 foyer"]
    assert "depth" in blobs["02 foyer"]
    assert "entrance hall" in blobs["02 foyer"]
    assert "arrival corridor" in blobs["02 foyer"]
    assert "unoccupied" in blobs["02 foyer"]
    assert "24mm" in blobs["02 foyer"]
    assert "bible named" in blobs["03 lounge"]
    assert "main opening" in blobs["03 lounge"]
    assert "living hall" in blobs["03 lounge"]
    assert "near field" in blobs["03 lounge"]
    assert "far plane" in blobs["03 lounge"]
    assert "unoccupied" in blobs["03 lounge"]
    assert "backdrop is only what the bible named for this room" in blobs["03 lounge"]
    toward_opening = [
        lab
        for lab, text in blobs.items()
        if "toward the main opening" in text
        or "looks out that opening" in text
        or "out the main opening" in text
    ]
    assert toward_opening == ["03 lounge"]
    assert "kitchen" in blobs["04 kitchen"]
    assert "cook line" in blobs["04 kitchen"]
    assert "cook room" in blobs["04 kitchen"]
    assert "counters" in blobs["04 kitchen"]
    assert "cooking appliances" in blobs["04 kitchen"]
    assert "interior only" in blobs["04 kitchen"]
    assert "bible named for this room" in blobs["04 kitchen"]
    assert "dining hall" in blobs["05 dining"]
    assert "seated-height" in blobs["05 dining"]
    assert "along the table" in blobs["05 dining"]
    assert "chairs" in blobs["05 dining"]
    assert "end wall" in blobs["05 dining"]
    assert "interior only" in blobs["05 dining"]
    assert "bible named for this room" in blobs["05 dining"]
    assert "bedroom" in blobs["06 bedroom"]
    assert "sleep chamber" in blobs["06 bedroom"]
    assert "standing at the foot" in blobs["06 bedroom"]
    assert "the bed the bible named" in blobs["06 bedroom"]
    assert "interior only" in blobs["06 bedroom"]
    assert "bible named for this room" in blobs["06 bedroom"]
    assert "bath" in blobs["07 bath"]
    assert "small wet room" in blobs["07 bath"]
    assert "enclosed" in blobs["07 bath"]
    assert "fixtures" in blobs["07 bath"]
    assert "closer" in blobs["07 bath"]
    assert "interior only" in blobs["07 bath"]
    assert "bible named for this room" in blobs["07 bath"]
    assert "along" in blobs["08 terrace"]
    assert "outdoor" in blobs["08 terrace"]
    assert "open-air" in blobs["08 terrace"]
    assert "sky overhead" in blobs["08 terrace"]
    assert "near field" in blobs["08 terrace"]
    assert "unoccupied" in blobs["08 terrace"]
    assert "surroundings are only what the bible named" in blobs["08 terrace"]
    assert "overhead" in blobs["09 drone"]
    assert "looking down" in blobs["09 drone"]
    assert "straight-down" in blobs["09 drone"]
    assert "plan still" in blobs["09 drone"]
    assert "unoccupied" in blobs["09 drone"]
    assert "surroundings are only what the bible named" in blobs["09 drone"]
    assert "study" in blobs["10 study"]
    assert "writing room" in blobs["10 study"]
    assert "writing surface" in blobs["10 study"]
    assert "storage wall" in blobs["10 study"]
    assert "closer" in blobs["10 study"]
    assert "interior only" in blobs["10 study"]
    assert "bible named for this room" in blobs["10 study"]
    for lab in ("04 kitchen", "05 dining", "06 bedroom", "07 bath", "10 study"):
        assert "interior only" in blobs[lab]
        assert "bible named for this room" in blobs[lab]
        assert "35mm" in blobs[lab]
        assert "unoccupied" in blobs[lab]
    kitchen = blobs["04 kitchen"]
    study = blobs["10 study"]
    assert "cook line" not in study
    assert "cooking appliances" not in study
    assert "writing surface" not in kitchen
    assert "storage wall" not in kitchen
    assert "sleep chamber" not in kitchen
    assert "dining hall" not in kitchen
    joined_cards = " ".join(blobs.values())
    assert "just inside" not in joined_cards
    assert "daylight exterior" not in joined_cards
    assert "night exterior" not in joined_cards
    assert "nook" not in joined_cards
    assert "fills the entire backdrop" not in joined_cards
    assert "not a second facade" not in joined_cards
    assert "floor, walls, and ceiling" not in joined_cards
    assert "work volume" not in joined_cards
    assert "work wall" not in joined_cards
    assert "living volume" not in joined_cards
    assert "gathering volume" not in joined_cards
    assert "private volume" not in joined_cards
    shots = [card["shot"] for card in pack10]
    assert len(set(shots)) == 10
    interiors = [
        blobs["04 kitchen"],
        blobs["05 dining"],
        blobs["06 bedroom"],
        blobs["07 bath"],
        blobs["10 study"],
    ]
    assert len(set(interiors)) == 5
    assert blobs["03 lounge"] != blobs["04 kitchen"]
    assert blobs["05 dining"] != blobs["08 terrace"]
    assert blobs["02 foyer"] != blobs["03 lounge"]
    assert blobs["06 bedroom"] != blobs["10 study"]


def test_place_10_shots_stay_generic_when_identity_swaps() -> None:
    cabin = (
        "A photoreal still of a one-room unmarked cedar cabin by a lake, "
        "hip roof, gravel path, one wood stove. Unmarked home, empty of lettering."
    )
    pack10 = client.load_view_pack("place_10")
    assert pack10
    for card in pack10:
        shot = card["shot"]
        shot_l = shot.lower()
        for leak in PLACE_10_IDENTITY_LEAKS:
            assert leak not in shot_l, (card["label"], leak)
        assert "cedar" not in shot_l
        assert "lake" not in shot_l
        joined = client.join_prompt(cabin, shot, "", "view")
        assert joined.startswith(shot)
        assert cabin in joined
        assert "cedar cabin" in joined.lower()
        assert len(joined.split()) <= PLACE_10_JOIN_CAP, (
            card["label"],
            len(joined.split()),
        )


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
    assert "EZClipConcat" in body


def test_web_directory_and_preview_js() -> None:
    assert ez_prompt_enhance.WEB_DIRECTORY == "./js"
    js = ROOT / "custom_nodes" / "ez_prompt_enhance" / "js" / "ez_prompt_enhance.js"
    body = js.read_text(encoding="utf-8")
    assert "onExecuted" in body
    assert "EZKleinPromptEnhance" in body
    assert "EZWanPromptEnhance" in body
    assert "EZLTXPromptEnhance" in body
    assert "EZNegativePromptEnhance" in body
    assert "EZAceStepPromptEnhance" in body
    assert "EZRapLyrics" in body
    assert "EZPodcastScript" in body
    assert "EZAppForge" in body
    assert "EZDubScript" not in body
    assert "_ezSampleLabels" in body
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
    assert "CPU wheel pip failed" in out.status
    assert "docker exec" in out.status
    assert "--force-reinstall" in out.status
    assert client.LLAMA_CPP_CPU_VERSION in out.status
    assert "restart" not in out.status
    assert "rebuild" not in out.status


def test_llama_oserror_import_passthrough(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    gguf = tmp_path / "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
    gguf.write_bytes(b"fake")
    monkeypatch.setenv("EZ_LLM_GGUF", str(gguf))
    client._close_llm()

    class _Boom(types.ModuleType):
        def __getattr__(self, name: str) -> object:
            raise OSError("libllama.so")

    with patch.dict(sys.modules, {"llama_cpp": _Boom("llama_cpp")}):
        out = client.enhance_prompt("sys", "user", enhance=True, fallback="lazy bike")
    assert out.text == "lazy bike"
    assert out.reason == client.REASON_LLAMA_UNAVAILABLE


def test_llama_runtimeerror_import_passthrough(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    gguf = tmp_path / "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
    gguf.write_bytes(b"fake")
    monkeypatch.setenv("EZ_LLM_GGUF", str(gguf))
    client.reset_llama_runtime_for_tests()

    class _Boom(types.ModuleType):
        def __getattr__(self, name: str) -> object:
            raise RuntimeError(
                "Failed to load shared library 'libllama.so': "
                "libc.musl-aarch64.so.1: cannot open shared object file"
            )

    def _pip(args: list[str]) -> subprocess.CompletedProcess[str]:
        del args
        return subprocess.CompletedProcess(
            args=["pip", "install"],
            returncode=0,
            stdout="Requirement already satisfied: llama-cpp-python==0.3.35",
            stderr="",
        )

    monkeypatch.setattr(client, "_pip_install", _pip)
    monkeypatch.setattr(client, "_forget_llama_module", lambda: None)
    with patch.dict(sys.modules, {"llama_cpp": _Boom("llama_cpp")}):
        out = client.enhance_prompt("sys", "user", enhance=True, fallback="lazy bike")
    assert out.text == "lazy bike"
    assert out.reason == client.REASON_LLAMA_UNAVAILABLE
    assert "libllama" in out.status
    assert "force-reinstall" in out.status
    assert "CPU wheel pip failed" not in out.status


def test_llama_typeerror_retries_without_chat_format(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    gguf = tmp_path / "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
    gguf.write_bytes(b"fake")
    monkeypatch.setenv("EZ_LLM_GGUF", str(gguf))
    client._close_llm()
    calls: list[dict[str, object]] = []

    class _FakeLlama:
        def __init__(self, **kwargs: object) -> None:
            calls.append(dict(kwargs))
            if "chat_format" in kwargs:
                raise TypeError("unexpected keyword argument 'chat_format'")

    fake = types.ModuleType("llama_cpp")
    setattr(fake, "Llama", _FakeLlama)
    with patch.dict(sys.modules, {"llama_cpp": fake}):
        handle, reason = client._get_llama()
    client._close_llm()
    assert reason is None
    assert handle is not None
    assert len(calls) == 2
    assert calls[0].get("chat_format") == "chatml"
    assert "chat_format" not in calls[1]


def test_llama_constructor_error_is_load_failed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    gguf = tmp_path / "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
    gguf.write_bytes(b"fake")
    monkeypatch.setenv("EZ_LLM_GGUF", str(gguf))
    client._close_llm()

    class _BoomLlama:
        def __init__(self, **kwargs: object) -> None:
            del kwargs
            raise RuntimeError("jinja generation tag")

    fake = types.ModuleType("llama_cpp")
    setattr(fake, "Llama", _BoomLlama)
    with patch.dict(sys.modules, {"llama_cpp": fake}):
        handle, reason = client._get_llama()
    client._close_llm()
    assert handle is None
    assert reason == client.REASON_LLM_LOAD_FAILED
    assert client.status_for_reason(reason) == "GGUF failed to load"


def test_llama_cpp_direct_wheel_url_is_manylinux() -> None:
    url = client.llama_cpp_direct_wheel_url()
    assert url.startswith("https://github.com/abetlen/llama-cpp-python/releases/")
    assert client.LLAMA_CPP_CPU_VERSION in url
    assert "manylinux" in url
    assert "cu12" not in url
    assert "cu13" not in url


def test_llama_cpp_direct_wheel_pip_args_force_reinstall() -> None:
    args = client.llama_cpp_direct_wheel_pip_args()
    assert "--force-reinstall" in args
    assert "--no-deps" in args
    assert "--only-binary=:all:" in args
    joined = " ".join(args)
    assert "github.com/abetlen/llama-cpp-python" in joined
    assert "manylinux" in joined
    assert "musllinux" not in joined
    assert "cu12" not in joined
    assert "cu13" not in joined


def test_status_for_reason_llama_points_at_force_reinstall() -> None:
    text = client.status_for_reason(client.REASON_LLAMA_UNAVAILABLE)
    assert "llama.cpp unavailable" in text
    assert "Llama did not import" in text
    assert "CPU wheel pip failed" not in text
    assert "docker exec" in text
    assert "--force-reinstall" in text
    assert "--no-deps" in text
    assert "github.com/abetlen/llama-cpp-python" in text
    assert "restart" not in text
    assert "rebuild" not in text
    assert "cu12" not in text
    assert "cu13" not in text


def test_heal_llama_cpp_tries_index_then_direct_wheel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def _pip(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(list(args))
        return subprocess.CompletedProcess(
            args=["pip", "install", *args],
            returncode=1,
            stdout="",
            stderr="ERROR: No matching distribution found for llama-cpp-python",
        )

    monkeypatch.setattr(client, "_pip_install", _pip)
    err = client._heal_llama_cpp_cpu()
    assert "No matching distribution" in err
    assert len(calls) == 2
    assert "--index-url" in calls[0]
    assert client.LLAMA_CPP_CPU_INDEX in calls[0]
    assert client.PYPI_SIMPLE_INDEX in calls[0]
    assert client.LLAMA_CPP_CPU_PKG in calls[0]
    assert "--only-binary=:all:" in calls[0]
    joined = " ".join(calls[0])
    assert "cu12" not in joined
    assert "cu13" not in joined
    assert "--force-reinstall" in calls[1]
    assert "--no-deps" in calls[1]
    assert any("github.com/abetlen/llama-cpp-python" in item for item in calls[1])


def test_heal_llama_cpp_force_reinstalls_when_pip_already_satisfied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def _pip(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(list(args))
        return subprocess.CompletedProcess(
            args=["pip", "install", *args],
            returncode=0,
            stdout="Requirement already satisfied: llama-cpp-python==0.3.35",
            stderr="",
        )

    monkeypatch.setattr(client, "_pip_install", _pip)
    monkeypatch.setattr(client, "_forget_llama_module", lambda: None)
    with patch.dict(sys.modules, {"llama_cpp": None}):
        err = client._heal_llama_cpp_cpu()
    assert err
    assert "import failed after pip" in err or "llama_cpp" in err
    assert len(calls) == 2
    assert "--index-url" in calls[0]
    assert "--force-reinstall" in calls[1]
    assert "--no-deps" in calls[1]
    assert "--only-binary=:all:" in calls[1]
    assert any("github.com/abetlen/llama-cpp-python" in item for item in calls[1])
    joined = " ".join(calls[1])
    assert "cu12" not in joined
    assert "cu13" not in joined
    status = client.llama_cpp_unavailable_status()
    assert "CPU wheel pip failed" not in status
    assert "Llama import failed" in status or "import failed" in status
    assert "--force-reinstall" in status


def test_get_llama_heals_cpu_wheel_then_loads(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    gguf = tmp_path / "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
    gguf.write_bytes(b"fake")
    monkeypatch.setenv("EZ_LLM_GGUF", str(gguf))
    client.reset_llama_runtime_for_tests()
    fake = types.ModuleType("llama_cpp")

    class _FakeLlama:
        def __init__(self, **kwargs: object) -> None:
            del kwargs

    setattr(fake, "Llama", _FakeLlama)

    def _heal() -> str:
        sys.modules["llama_cpp"] = fake
        return ""

    monkeypatch.setattr(client, "_heal_llama_cpp_cpu", _heal)
    with patch.dict(sys.modules, {"llama_cpp": None}):
        handle, reason = client._get_llama()
    client._close_llm()
    assert reason is None
    assert handle is not None


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


def test_generate_honors_max_tokens() -> None:
    class _FakeLlama:
        def create_chat_completion(self, **kwargs: object) -> dict:
            assert kwargs["max_tokens"] == 256
            return {"choices": [{"message": {"content": "hola"}}]}

    assert client._generate(_FakeLlama(), "sys", "user", 256) == "hola"


def test_generate_honors_temperature() -> None:
    class _FakeLlama:
        def create_chat_completion(self, **kwargs: object) -> dict:
            assert kwargs["temperature"] == 0.3
            assert kwargs["max_tokens"] == 512
            return {"choices": [{"message": {"content": "Bienvenidos"}}]}

    assert client._generate(_FakeLlama(), "sys", "user", 512, 0.3) == "Bienvenidos"


def test_complete_passes_timeout_and_temperature(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    class _Handle:
        pass

    def _fake_get_llama() -> tuple[object, None]:
        return _Handle(), None

    def _fake_generate(
        llm: object,
        system: str,
        user: str,
        max_tokens: int = 800,
        temperature: float = 0.0,
    ) -> str:
        del llm, system, user
        seen["max_tokens"] = max_tokens
        seen["temperature"] = temperature
        return "Hola"

    monkeypatch.setattr(client, "_get_llama", _fake_get_llama)
    monkeypatch.setattr(client, "_generate", _fake_generate)
    text, reason = client.complete(
        "sys",
        "user",
        max_tokens=512,
        temperature=0.3,
        timeout_s=120,
    )
    assert text == "Hola"
    assert reason is None
    assert seen["max_tokens"] == 512
    assert seen["temperature"] == 0.3


def test_timeout_and_thread_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EZ_LLM_TIMEOUT_S", raising=False)
    monkeypatch.delenv("EZ_LLM_N_THREADS", raising=False)
    assert client.DEFAULT_TIMEOUT_S == 180
    assert client.DEFAULT_N_THREADS == 8
    assert client._timeout_s() == 180
    assert client._n_threads() == 8
    monkeypatch.setenv("EZ_LLM_TIMEOUT_S", "90")
    monkeypatch.setenv("EZ_LLM_N_THREADS", "12")
    assert client._timeout_s() == 90
    assert client._n_threads() == 12
    monkeypatch.setenv("EZ_LLM_TIMEOUT_S", "nope")
    monkeypatch.setenv("EZ_LLM_N_THREADS", "0")
    assert client._timeout_s() == 180
    assert client._n_threads() == 8


def _write_occupancy(tmp_path: Path, mode: str) -> None:
    payload = {"version": 1, "mode": mode, "parked": False, "llm_pid": 0}
    (tmp_path / ".occupancy.json").write_text(json.dumps(payload), encoding="utf-8")


def test_n_gpu_layers_occupancy_cpu_force_and_allow_off(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    _write_occupancy(tmp_path, "ltx")
    monkeypatch.setenv("EZ_LLM_N_GPU_LAYERS", "99")
    monkeypatch.setenv("EZ_LLM_ALLOW_GPU", "1")
    assert client._n_gpu_layers() == 0
    monkeypatch.delenv("EZ_LLM_ALLOW_GPU", raising=False)
    monkeypatch.delenv("EZ_LLM_N_GPU_LAYERS", raising=False)
    _write_occupancy(tmp_path, "idle")
    monkeypatch.setenv("EZ_LLM_ALLOW_GPU", "0")
    assert client._n_gpu_layers() == 0
    monkeypatch.delenv("EZ_LLM_ALLOW_GPU", raising=False)
    assert client._n_gpu_layers() == 99


def test_sidecar_used_when_occupancy_llm(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    _write_occupancy(tmp_path, "llm")
    calls: list[str] = []

    class _Resp:
        def __init__(self, payload: bytes) -> None:
            self._payload = payload

        def read(self) -> bytes:
            return self._payload

        def __enter__(self) -> _Resp:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

    def _open(request: object, timeout: float) -> _Resp:
        del timeout
        url = str(getattr(request, "full_url", "") or request)
        calls.append(url)
        if "/v1/models" in url:
            return _Resp(b'{"data":[{"id":"qwen36-35b-a3b"}]}')
        payload = {"choices": [{"message": {"content": "gpu-sidecar"}}]}
        return _Resp(json.dumps(payload).encode("utf-8"))

    monkeypatch.setattr(client, "_urlopen_sidecar", _open)
    text, reason = client.complete("sys", "user")
    assert text == "gpu-sidecar"
    assert reason is None
    assert any("/v1/models" in item for item in calls)


def test_sidecar_skipped_when_occupancy_ltx(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    _write_occupancy(tmp_path, "ltx")
    called = {"n": 0}

    def _open(*_args: object, **_kwargs: object) -> object:
        called["n"] += 1
        raise AssertionError("sidecar must not be probed during ltx")

    monkeypatch.setattr(client, "_urlopen_sidecar", _open)
    assert client.sidecar_occupancy_ok() is False
    text, reason = client.complete("sys", "user")
    assert called["n"] == 0
    assert text == ""
    assert reason == client.REASON_GGUF_MISSING


def test_sidecar_base_url_uses_host_gateway_in_container(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("EZ_LLM_SIDECAR_URL", raising=False)
    monkeypatch.setenv("MODELS_ROOT", "/models")
    monkeypatch.setenv("EZ_LLM_SIDECAR_PORT", "30000")
    assert "host.docker.internal" in client.sidecar_base_url()
    monkeypatch.delenv("MODELS_ROOT", raising=False)
    assert "127.0.0.1" in client.sidecar_base_url()


def test_lab_graphs_use_model_native_prompts_and_enhance_nodes() -> None:
    from _lab_paths import lab_json

    draft = json.loads(lab_json("stills/still-draft.json").read_text(encoding="utf-8"))
    hero = json.loads(lab_json("stills/still-hero.json").read_text(encoding="utf-8"))
    klein_d = next(n for n in draft["nodes"] if n.get("type") == "EZKleinPromptEnhance")
    klein_h = next(n for n in hero["nodes"] if n.get("type") == "EZKleinPromptEnhance")
    assert _enh_prompt(klein_d["widgets_values"]) == _enh_prompt(klein_h["widgets_values"])
    assert _enh_flag(klein_d["widgets_values"]) is True
    assert _enh_flag(klein_h["widgets_values"]) is True
    assert klein_d["widgets_values"][0] == SAMPLE_CUSTOM
    wan_t = json.loads(lab_json("motion/silent/text-to-video-5s.json").read_text(encoding="utf-8"))
    wan_i = json.loads(lab_json("motion/silent/still-to-video-5s.json").read_text(encoding="utf-8"))
    ltx_t = json.loads(lab_json("motion/av/text-to-video-8s.json").read_text(encoding="utf-8"))
    ltx_i = json.loads(lab_json("motion/av/still-to-video-8s.json").read_text(encoding="utf-8"))
    wan_tp = _enh_prompt(next(n for n in wan_t["nodes"] if n.get("type") == "EZWanPromptEnhance")["widgets_values"])
    wan_ip = _enh_prompt(next(n for n in wan_i["nodes"] if n.get("type") == "EZWanPromptEnhance")["widgets_values"])
    ltx_tp = _enh_prompt(next(n for n in ltx_t["nodes"] if n.get("type") == "EZLTXPromptEnhance")["widgets_values"])
    ltx_ip = _enh_prompt(next(n for n in ltx_i["nodes"] if n.get("type") == "EZLTXPromptEnhance")["widgets_values"])
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
    closer = "This still is only the room and backdrop the shot names."
    assert view[0].count(closer) == 2
    assert view[0].endswith(closer)
    assert "outlook that camera would see" not in view[0]
    assert "sky, and background" not in view[0]
    trimmed = join.run("  House.  ", "  Dusk deck.  ")[0]
    assert trimmed.startswith("Dusk deck.")
    assert "House." in trimmed
    only = join.run("Identity only.", "")
    assert only[0].startswith("Identity only.")
    assert "different camera" in only[0]
    assert only[0].count(closer) == 1
    shot_only = join.run("", "Shot only.")[0]
    assert shot_only.startswith("Shot only.")
    assert "different camera" in shot_only
    assert join.run("  ", "  ") == ("",)
    locked = join.run("Cabin.", "Dawn deck.", "cedar siding, hip roof")
    assert locked[0].startswith("Dawn deck.")
    assert "Cabin." in locked[0]
    assert "Locked inventory (do not change): cedar siding, hip roof." in locked[0]
    assert "different camera" in locked[0]
    assert locked[0].count(closer) == 2
    assert locked[0].endswith(closer)
    state = join.run("Cabin.", "Warm key.", "mug", "state")
    assert state[0].startswith("Cabin.")
    assert "camera framing" in state[0]
    assert "The shot names the only change." in state[0]
    assert "mug" in state[0]
    assert state[0].endswith("Warm key.")
    assert closer not in state[0]
    types = EZPromptJoin.INPUT_TYPES()["required"]["lock"][0]
    assert types[0] == "view"
    assert "state" in types


def test_app_lab_graphs_wire_join_and_enhance() -> None:
    from _lab_paths import lab_json

    still = json.loads(lab_json("stills/still-daily.json").read_text(encoding="utf-8"))
    gif = json.loads(lab_json("motion/loops/gif-loop.json").read_text(encoding="utf-8"))
    house = json.loads(lab_json("stills/dream-house.json").read_text(encoding="utf-8"))
    klein = next(n for n in still["nodes"] if n.get("type") == "EZKleinPromptEnhance")
    assert _enh_flag(klein["widgets_values"]) is True
    assert klein["widgets_values"][0] == SAMPLE_CUSTOM
    assert "photoreal still" in _enh_prompt(klein["widgets_values"])
    assert "techno wizard" in _enh_prompt(klein["widgets_values"])
    wan = next(n for n in gif["nodes"] if n.get("type") == "EZWanPromptEnhance")
    assert _enh_mode(wan["widgets_values"]) == "i2v"
    motion = _enh_prompt(wan["widgets_values"]).lower()
    assert "dolly" not in motion
    assert "walk" not in motion
    ident = next(n for n in house["nodes"] if n.get("type") == "EZKleinPromptEnhance")
    ident_text = _enh_prompt(ident["widgets_values"])
    ident_l = ident_text.lower()
    assert "photoreal still" in ident_l
    assert "warm-glass" in ident_l
    assert "crown penthouse" in ident_l
    assert "full-floor" in ident_l
    assert "dense" in ident_l
    assert "skyscraper" in ident_l
    assert "wraparound terrace" in ident_l
    assert "three-bay" in ident_l
    assert "teak" in ident_l
    assert "coral-teal" in ident_l
    assert "lounge" in ident_l
    assert "study" in ident_l
    assert "lantern" in ident_l or "path light" in ident_l
    assert "bay" in ident_l
    assert "compact" not in ident_l
    assert "fern" not in ident_l
    assert "24mm" not in ident_l
    assert "golden-hour" not in ident_l and "golden hour" not in ident_l
    assert "cedar" not in ident_l
    assert "cabin" not in ident_l
    assert "lake" not in ident_l
    assert "no logos, no text" not in ident_text
    assert _enh_flag(ident["widgets_values"]) is True
    assert _enh_mode(ident["widgets_values"]) == "identity"
    assert ident["widgets_values"][4] == "Instagram 4:5 still"
    assert ident["widgets_values"][5] == "none"
    joins = [n for n in house["nodes"] if n.get("type") == "EZPromptJoin"]
    assert len(joins) == 10
    join_titles = [n["title"] for n in sorted(joins, key=lambda n: n["id"])]
    assert join_titles == [
        "SHOT 01 tower",
        "SHOT 02 foyer",
        "SHOT 03 lounge",
        "SHOT 04 kitchen",
        "SHOT 05 dining",
        "SHOT 06 bedroom",
        "SHOT 07 bath",
        "SHOT 08 terrace",
        "SHOT 09 drone",
        "SHOT 10 study",
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
        *PLACE_10_IDENTITY_LEAKS,
    )
    inventories = set()
    assert "linen sofa" in ident_l
    pack10 = client.load_view_pack("place_10")
    for i, join in enumerate(sorted(joins, key=lambda n: n["id"])):
        shot = join["widgets_values"][0]
        inventory = join["widgets_values"][1]
        lock = join["widgets_values"][2]
        inventories.add(inventory)
        assert lock == "view"
        assert inventory.strip() == ""
        assert shot == pack10[i]["shot"]
        shot_l = shot.lower()
        assert not any(noun in shot_l for noun in hidden_nouns)
        joined = client.join_prompt(ident_text, shot, inventory, lock)
        assert joined.startswith(shot)
        assert ident_text in joined
        assert len(joined.split()) <= 220
        assert not any(b in shot_l for b in banned)
        text = positives[f"Positive {i + 1:02d}"]
        assert text.startswith(shot)
        assert ident_text in text
        assert "different camera" in text
        assert "walkthrough" in text
        closer = "This still is only the room and backdrop the shot names."
        assert joined.count(closer) == 2
        assert text.count(closer) == 2
        assert "outlook that camera would see" not in text
        assert "sky, and background" not in text
        assert "linen sofa" in text
        assert len(text.split()) <= 220
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


def test_dream_house_graphs_use_place_10_shots() -> None:
    from _lab_paths import lab_json

    pack = [card["shot"] for card in client.load_view_pack("place_10")]
    for rel in ("stills/dream-house.json", "stills/dream-house-clay.json"):
        graph = json.loads(lab_json(rel).read_text(encoding="utf-8"))
        joins = sorted(
            [n for n in graph["nodes"] if n.get("type") == "EZPromptJoin"],
            key=lambda n: n["id"],
        )
        assert [n["widgets_values"][0] for n in joins] == pack, rel


def test_context_join_skips_empty_and_labels_blocks() -> None:
    node = EZContextJoin()
    types = node.INPUT_TYPES()
    assert types["required"]["a"][1]["forceInput"] is True
    assert types["optional"]["b"][1]["forceInput"] is True
    packed = node.run(
        "one-line premise",
        "Logline",
        "Script",
        "Audio policy",
        "Score",
        "spoken beats",
        "world-only",
        "",
    )
    text = packed[0]
    assert text.startswith("Logline:\none-line premise")
    assert "Script:\nspoken beats" in text
    assert "Audio policy:\nworld-only" in text
    assert "Score:" not in text
    empty = node.run("", "Logline")
    assert empty[0] == ""


def test_enhance_context_ignored_when_off_included_when_on() -> None:
    klein = EZKleinPromptEnhance()
    assert klein.INPUT_TYPES()["optional"]["context"][1]["forceInput"] is True
    off = klein.run(
        "A rooftop.",
        False,
        "t2i",
        "YouTube 16:9 still",
        "none",
        "bible: indigo-violet suede coat, no staff",
    )
    assert off["result"] == ("A rooftop.",)
    assert off["ui"]["passthrough"][0] == "enhance off"
    with patch.object(client, "complete", return_value=("rewritten", None)) as mock:
        klein.run(
            "lazy bike",
            True,
            "t2i",
            "YouTube 16:9 still",
            "none",
            "identity bible here",
        )
    user = mock.call_args[0][1]
    system = mock.call_args[0][0]
    assert "lazy bike" in user
    assert "Context:" in user
    assert "identity bible here" in user
    assert "Context block" in system or "supporting bible" in system.lower()
    wan = EZWanPromptEnhance()
    with patch.object(client, "complete", return_value=("motion", None)) as mock:
        wan.run("push in", True, "i2v", "5 seconds, 24 fps", "none", "keep the dark indigo-violet suede coat")
    wan_system = mock.call_args[0][0]
    assert "start frame owns look" in wan_system.lower() or "do not restate look" in wan_system.lower()
    ace = EZAceStepPromptEnhance()
    assert ace.INPUT_TYPES()["optional"]["context"][1]["forceInput"] is True
    inst_off = ace.run("lo-fi keys", "", False, "instrumental", "episode about fans")
    assert inst_off["ui"]["passthrough"][0] == "enhance off"
    assert "episode about fans" not in inst_off["result"][0]


def test_node_mappings_modes_preview_and_style() -> None:
    assert set(NODE_CLASS_MAPPINGS) == {
        "EZImageDescribe",
        "EZBackgroundCast",
        "EZKleinPromptEnhance",
        "EZWanPromptEnhance",
        "EZLTXPromptEnhance",
        "EZZimagePromptEnhance",
        "EZLongCatPromptEnhance",
        "EZDreamXPromptEnhance",
        "EZNegativePromptEnhance",
        "EZPromptBundle",
        "EZPromptJoin",
        "EZAceStepPromptEnhance",
        "EZContextJoin",
        "EZSamplePrompt",
        "EZCinemaRack",
        "EZAudioRack",
    }
    klein = EZKleinPromptEnhance()
    wan = EZWanPromptEnhance()
    ltx = EZLTXPromptEnhance()
    assert klein.OUTPUT_NODE is True
    enhance = klein.INPUT_TYPES()["required"]["enhance"][1]
    assert enhance["default"] is True
    assert enhance["label_on"] == "On"
    assert enhance["label_off"] == "Off"
    assert wan.INPUT_TYPES()["required"]["enhance"][1]["label_on"] == "On"
    assert ltx.INPUT_TYPES()["required"]["enhance"][1]["label_off"] == "Off"
    modes = klein.INPUT_TYPES()["required"]["mode"][0]
    assert modes == [
        "t2i",
        "edit",
        "identity",
        "text_swap",
        "background_swap",
        "background_edit",
    ]
    styles = klein.INPUT_TYPES()["required"]["style"][0]
    assert styles[0] == "none"
    assert len(styles) == 301
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
    with patch.object(
        client,
        "complete",
        return_value=("rewritten-swap", None),
    ) as mock_swap:
        swapped = klein.run("OPEN", True, "text_swap", "match the source still", "none")
    assert swapped["result"] == ("rewritten-swap",)
    swap_system = mock_swap.call_args[0][0]
    assert "lettering" in swap_system.lower()
    assert "spell" in swap_system.lower()
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
    assert wan_modes == ["t2v", "i2v", "flf", "vace", "s2v"]
    ltx_modes = ltx.INPUT_TYPES()["required"]["mode"][0]
    assert ltx_modes == ["t2v", "i2v", "iclora"]
    zimage = EZZimagePromptEnhance()
    longcat = EZLongCatPromptEnhance()
    dreamx = EZDreamXPromptEnhance()
    assert zimage.OUTPUT_NODE is True
    assert longcat.INPUT_TYPES()["required"]["mode"][0] == ["t2v", "i2v", "vc"]
    assert "audio_notes" in dreamx.INPUT_TYPES()["required"]
    with patch.object(client, "complete", return_value=("z-still", None)) as mock:
        zimage.run("a mug", True, "YouTube 16:9 still")
    assert "Z-Image" in mock.call_args[0][0] or "Qwen3-4B" in mock.call_args[0][0]
    with patch.object(client, "complete", return_value=("lc-t2v", None)) as mock:
        longcat.run("a car", True, "t2v", "5 seconds, 30 fps")
    assert "LongCat" in mock.call_args[0][0]
    with patch.object(client, "complete", return_value=("dx-av", None)) as mock:
        dreamx.run("wind on sand", True, "5 seconds, 24 fps", "wind, no score")
    assert "DreamX" in mock.call_args[0][0]
    with patch.object(client, "complete", return_value=("s2v-talk", None)) as mock:
        wan.run("talking head", True, "s2v", "audio length")
    assert "S2V" in mock.call_args[0][0] or "wav" in mock.call_args[0][0].lower()
    with patch.object(client, "complete", return_value=("iclora-look", None)) as mock:
        ltx.run("ornate brick", True, "iclora", "5 seconds, 24 fps")
    assert "IC-LoRA" in mock.call_args[0][0] or "control" in mock.call_args[0][0].lower()
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


def test_sanitize_instrumental_lyrics_folds_free_text() -> None:
    assert sanitize_instrumental_lyrics("") == "[inst]"
    assert sanitize_instrumental_lyrics("[inst]") == "[inst]"
    assert (
        sanitize_instrumental_lyrics("[inst]\nheavy warped drop\ntrap hats roll")
        == "[inst - heavy warped drop, trap hats roll]"
    )
    assert (
        sanitize_instrumental_lyrics("[drop - warped 808]\ngrid 193 0")
        == "[drop - warped 808, grid 193 0]"
    )


def test_opt_in_enhance_flavors_and_modes() -> None:
    """Z-Image / LongCat / DreamX / IC-LoRA / S2V system prompts and modes."""
    assert client.flavor_for_system("zimage_t2i") == "zimage"
    assert client.flavor_for_system("dreamx_i2v") == client.FLAVOR_LTX
    assert client.flavor_for_system("longcat_t2v") == client.FLAVOR_WAN
    assert client.flavor_for_system("longcat_i2v") == client.FLAVOR_WAN
    assert client.flavor_for_system("ltx_iclora") == client.FLAVOR_LTX
    zimage = EZZimagePromptEnhance()
    assert "prompt" in zimage.INPUT_TYPES()["required"]
    longcat = EZLongCatPromptEnhance()
    dreamx = EZDreamXPromptEnhance()
    ltx = EZLTXPromptEnhance()
    with patch.object(client, "complete", return_value=("lc-i2v", None)) as mock:
        longcat.run("breeze", True, "i2v", "5 seconds, 30 fps")
    assert "still" in mock.call_args[0][0].lower() or "start" in mock.call_args[0][0].lower()
    with patch.object(client, "complete", return_value=("lc-vc", None)) as mock:
        longcat.run("next beat", True, "vc", "5 seconds, 30 fps")
    assert "continuation" in mock.call_args[0][0].lower() or "previous" in mock.call_args[0][0].lower()
    with patch.object(client, "complete", return_value=("iclora-look", None)) as mock:
        ltx.run("ornate brick", True, "iclora", "5 seconds, 24 fps")
    assert "control" in mock.call_args[0][0].lower() or "IC-LoRA" in mock.call_args[0][0]
    with patch.object(client, "complete", return_value=("ltx-i2v", None)) as mock:
        ltx.run("from the first frame", True, "i2v", "5 seconds, 24 fps")
    assert "first frame" in mock.call_args[0][0].lower()
    with patch.object(client, "complete", return_value=("z-styled", None)) as mock:
        zimage.run("a mug", True, "YouTube 16:9 still", "anime")
    assert "Visual style" in mock.call_args[0][1]
    off = dreamx.run("wind", False, "5 seconds, 24 fps")
    assert off["ui"]["passthrough"][0] == "enhance off"


def test_ace_step_enhance_node_defaults_and_modes() -> None:
    ace = EZAceStepPromptEnhance()
    spec = ace.INPUT_TYPES()["required"]
    assert spec["enhance"][1]["default"] is True
    assert spec["enhance"][1]["label_on"] == "On"
    assert spec["enhance"][1]["label_off"] == "Off"
    assert spec["mode"][0] == ["vocal", "instrumental"]
    off = ace.run("boom bap, 88 bpm", "[verse]\nhi", False, "vocal")
    assert off["result"] == ("boom bap, 88 bpm", "[verse]\nhi")
    assert off["ui"]["passthrough"][0] == "enhance off"
    inst_off = ace.run("lo-fi keys", "", False, "instrumental")
    assert "instrumental" in inst_off["result"][0].lower()
    assert inst_off["result"][1] == "[inst]"
    sung = ace.run(
        "hybrid trap, instrumental, no vocals",
        "[inst]\nheavy warped drop\ntrap hats roll",
        False,
        "instrumental",
    )
    assert sung["result"][1] == "[inst - heavy warped drop, trap hats roll]"
    assert "\nheavy" not in sung["result"][1]
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
    """Every lab CLIP/ACE positive prompt comes from an EZ enhance node.

    Authored/structured graphs pin Enhance off; lazy CLIP printers stay on.
    """
    from _wire_prompt_enhance import enhance_pin_off

    from _lab_paths import lab_graph_paths

    skip_ids = {"audio/stem-mix"}
    enhance_types = {
        "EZKleinPromptEnhance",
        "EZWanPromptEnhance",
        "EZLTXPromptEnhance",
        "EZZimagePromptEnhance",
        "EZLongCatPromptEnhance",
        "EZDreamXPromptEnhance",
        "EZNegativePromptEnhance",
        "EZAceStepPromptEnhance",
        "EZRapLyrics",
        "EZPodcastScript",
        "EZPodcastLearn",
    }
    pos_enhance_types = enhance_types - {"EZNegativePromptEnhance"}
    encoder_types = {"CLIPTextEncode", "TextEncodeAceStepAudio1.5"}
    missing: list[str] = []
    from _lab_paths import load_lab_graph

    for path in lab_graph_paths():
        graph = load_lab_graph(path)
        extra = graph.get("extra") or {}
        gid = str(extra.get("lab_rel") or graph.get("id") or path.stem)
        if gid in skip_ids or gid.startswith("services/"):
            continue
        pin_off = enhance_pin_off(gid)
        by_id = {int(n["id"]): n for n in graph["nodes"]}
        links = {int(link[0]): link for link in graph.get("links") or []}
        for node in graph["nodes"]:
            ntype = node.get("type")
            if ntype in enhance_types:
                values = node.get("widgets_values") or []
                if ntype == "EZNegativePromptEnhance":
                    flag = values[1] if len(values) > 1 else True
                    if flag is not True:
                        missing.append(
                            f"{path.name}: {ntype}#{node['id']} enhance={flag!r}"
                        )
                    continue
                elif ntype == "EZAceStepPromptEnhance":
                    flag = (
                        values[3]
                        if len(values) >= 6
                        else values[2] if len(values) > 2 else True
                    )
                elif ntype == "EZPodcastLearn":
                    flag = (
                        values[5]
                        if len(values) >= 7
                        else values[4] if len(values) > 4 else True
                    )
                else:
                    flag = (
                        values[2]
                        if len(values) >= 4
                        else values[1] if len(values) > 1 else True
                    )
                if gid == "audio/podcast/learn-episode" and ntype == "EZAceStepPromptEnhance":
                    if flag is not False:
                        missing.append(
                            f"{path.name}: {ntype}#{node['id']} enhance={flag!r}"
                        )
                    continue
                if pin_off:
                    if flag is not False:
                        missing.append(
                            f"{path.name}: {ntype}#{node['id']} enhance={flag!r}"
                        )
                elif flag is not True:
                    missing.append(f"{path.name}: {ntype}#{node['id']} enhance={flag!r}")
            if ntype not in encoder_types:
                continue
            title = str(node.get("title") or "")
            if ntype == "CLIPTextEncode" and "neg" in title.lower():
                text_inp = next(
                    (i for i in node.get("inputs") or [] if i.get("name") == "text"),
                    None,
                )
                if text_inp is None or text_inp.get("link") is None:
                    missing.append(f"{path.name}: CLIP {title!r} has no text link")
                    continue
                src = by_id.get(int(links[int(text_inp["link"])][1]))
                if src is None or src.get("type") != "EZNegativePromptEnhance":
                    missing.append(
                        f"{path.name}: CLIP {title!r} fed by "
                        f"{None if src is None else src.get('type')}"
                    )
                    continue
                pos_inp = next(
                    (i for i in src.get("inputs") or [] if i.get("name") == "positive"),
                    None,
                )
                has_pos_enhance = any(
                    n.get("type") in pos_enhance_types for n in graph["nodes"]
                )
                if has_pos_enhance:
                    if pos_inp is None or pos_inp.get("link") is None:
                        missing.append(
                            f"{path.name}: negative enhance #{src['id']} missing positive"
                        )
                    else:
                        pos_src = by_id.get(int(links[int(pos_inp["link"])][1]))
                        allowed = pos_enhance_types | {
                            "EZPromptJoin",
                            "EZPromptBundle",
                        }
                        if pos_src is None or pos_src.get("type") not in allowed:
                            missing.append(
                                f"{path.name}: negative enhance #{src['id']} "
                                f"positive from {None if pos_src is None else pos_src.get('type')}"
                            )
                continue
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


def test_negative_enhance_reads_final_positive_and_stays_on() -> None:
    """Negative rewrite stays on and reads the CLIP string, including services."""
    from _lab_paths import lab_graph_paths, load_lab_graph
    from _wire_prompt_enhance import _linked_node, _sampler_pairs

    missing: list[str] = []
    for path in lab_graph_paths():
        graph = load_lab_graph(path)
        extra = graph.get("extra") or {}
        gid = str(extra.get("lab_rel") or path.stem)
        families: set[str] = set()
        neg_nodes = [
            node
            for node in graph["nodes"]
            if node.get("type") == "EZNegativePromptEnhance"
        ]
        for node in neg_nodes:
            values = node.get("widgets_values") or []
            if len(values) < 2 or values[1] is not True:
                missing.append(f"{gid}: enhance flag {values!r}")
            if len(values) > 2:
                families.add(str(values[2]))
        linear = (extra.get("linearData") or {}).get("inputs") or []
        stamped = []
        by_id = {int(node["id"]): node for node in graph["nodes"]}
        for entry in linear:
            if not isinstance(entry, list) or len(entry) < 2 or entry[1] != "enhance":
                continue
            node = by_id.get(int(entry[0]))
            if node is None or node.get("type") != "EZNegativePromptEnhance":
                continue
            label = ""
            if len(entry) > 2 and isinstance(entry[2], dict):
                label = str(entry[2].get("label") or "")
            stamped.append(label)
        if neg_nodes and linear:
            if len(stamped) != len(families):
                missing.append(f"{gid}: stamped {stamped} families {families}")
            if len(families) == 1 and stamped != ["Rewrite negative"]:
                missing.append(f"{gid}: label {stamped}")
            if len(families) > 1 and len(stamped) > 2:
                missing.append(f"{gid}: too many negative toggles {stamped}")
        if gid.startswith("films/"):
            bundles = [
                node for node in graph["nodes"] if node.get("type") == "EZPromptBundle"
            ]
            if len(bundles) != 1:
                missing.append(f"{gid}: bundles {len(bundles)}")
        for pair in _sampler_pairs(graph):
            src = pair["pos_src"]
            neg = pair["neg_src"]
            if not isinstance(src, dict) or not isinstance(neg, dict):
                missing.append(f"{gid}: sampler missing text source")
                continue
            fed = _linked_node(graph, neg, "positive")
            if src.get("type") == "EZPromptJoin":
                if fed is None or int(fed["id"]) != int(src["id"]):
                    missing.append(f"{gid}: join not fed to its negative")
            elif gid.startswith("films/") and src.get("type") == "EZLTXPromptEnhance":
                if fed is None or fed.get("type") != "EZPromptBundle":
                    missing.append(f"{gid}: LTX negative missing bundle")
            elif fed is None or int(fed["id"]) != int(src["id"]):
                missing.append(
                    f"{gid}: {src.get('type')} fed by "
                    f"{None if fed is None else fed.get('type')}"
                )
    assert not missing, "\n".join(missing[:30])


def test_prompt_bundle_joins_nonempty_slots() -> None:
    bundle = EZPromptBundle()
    optional = bundle.INPUT_TYPES()["optional"]
    assert len(optional) == 24
    assert optional["text_01"][1]["forceInput"] is True
    assert bundle.run() == ("",)
    assert bundle.run(text_01="  one  ", text_02=" ", text_03="two") == ("one\n\ntwo",)
    assert bundle.run(text_02=12) == ("12",)


def test_enhance_policy_keeps_negative_on_when_positive_is_off() -> None:
    from _wire_prompt_enhance import apply_enhance_policy

    graph = {
        "id": "films/go-see",
        "extra": {
            "lab_rel": "films/go-see",
            "lab_note": "Prompt enhance is on by default.\n",
        },
        "nodes": [
            {
                "type": "EZLTXPromptEnhance",
                "widgets_values": [
                    "custom",
                    "shot",
                    True,
                    "i2v",
                    "5 seconds, 24 fps",
                    "",
                    "none",
                    "films/go-see",
                ],
            },
            {
                "type": "EZNegativePromptEnhance",
                "widgets_values": ["watermark", False, "ltx"],
            },
        ],
    }
    apply_enhance_policy(graph)
    nodes = graph["nodes"]
    assert isinstance(nodes, list)
    ltx_node = nodes[0]
    neg_node = nodes[1]
    assert isinstance(ltx_node, dict)
    assert isinstance(neg_node, dict)
    ltx_values = ltx_node["widgets_values"]
    neg_values = neg_node["widgets_values"]
    assert isinstance(ltx_values, list)
    assert isinstance(neg_values, list)
    assert ltx_values[2] is False
    assert neg_values[1] is True
