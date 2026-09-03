"""Creator toolkit lab workflow contracts."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "workflows"

CREATORS = (
    ("klein-shorts-still-lab-example", "ez_shorts_still", False),
    ("wan-shorts-i2v-lab-example", "ez_shorts_wan_video", True),
    ("ltx-shorts-i2v-lab-example", "ez_shorts_ltx_video", True),
    ("klein-thumbnail-lab-example", "ez_thumbnail", False),
    ("klein-product-packshot-lab-example", "ez_packshot", False),
    ("klein-before-after-lab-example", "ez_before", False),
    ("klein-style-lock-lab-example", "ez_style_01", False),
    ("wan-bumper-loop-lab-example", "ez_bumper", True),
    ("ltx-broll-ambient-lab-example", "ez_broll_video", True),
    ("klein-storyboard-6up-lab-example", "ez_board_01", False),
    ("klein-endcard-cta-lab-example", "ez_endcard", False),
    ("klein-quote-bg-lab-example", "ez_quote_bg", False),
    ("klein-og-blog-lab-example", "ez_og", False),
    ("klein-podcast-cover-lab-example", "ez_podcast", False),
    ("klein-banner-wide-lab-example", "ez_banner", False),
    ("klein-ig-square-lab-example", "ez_ig_square", False),
    ("klein-hook-still-lab-example", "ez_hook_still", False),
    ("klein-lower-third-bg-lab-example", "ez_lowerthird", False),
    ("klein-food-tabletop-lab-example", "ez_tabletop", False),
    ("klein-lighting-trio-lab-example", "ez_light_01", False),
    ("klein-time-of-day-lab-example", "ez_tod_01", False),
    ("klein-camera-angles-lab-example", "ez_angle_wide", False),
    ("klein-color-moods-lab-example", "ez_mood_01", False),
    ("wan-orbit-i2v-lab-example", "ez_orbit_video", True),
    ("wan-push-in-i2v-lab-example", "ez_pushin_video", True),
    ("wan-parallax-i2v-lab-example", "ez_parallax_video", True),
    ("wan-sticker-loop-lab-example", "ez_sticker", True),
    ("ltx-weather-broll-lab-example", "ez_weather_video", True),
    ("ltx-interior-ambience-lab-example", "ez_interior_video", True),
    ("ltx-hook-av-lab-example", "ez_hook_video", True),
)

BANNED = ("MiniMax", "MiniMaxH3", "minimax_h3", "klein-9b", "FLUX.2-dev")


def test_creator_toolkit_files_and_prefixes() -> None:
    for stem, prefix, is_video in CREATORS:
        path = WF / f"{stem}.json"
        assert path.is_file(), stem
        text = path.read_text(encoding="utf-8")
        for needle in BANNED:
            assert needle not in text, (stem, needle)
        graph = json.loads(text)
        assert graph.get("id") == stem
        assert graph.get("extra", {}).get("lab_note", "").strip()
        assert graph.get("extra", {}).get("lab_description", "").strip()
        blob = json.dumps(graph)
        assert prefix in blob, (stem, prefix)
        vhs = [n for n in graph["nodes"] if n.get("type") == "VHS_VideoCombine"]
        if is_video:
            assert len(vhs) >= 1, stem
            for node in vhs:
                assert node["widgets_values"]["save_output"] is True
                assert str(node["widgets_values"]["filename_prefix"]).startswith("ez_")
                assert "preview" in (node.get("title") or "").lower()
        if any(n.get("type") == "LTXVSeparateAVLatent" for n in graph["nodes"]):
            assert any(n.get("type") == "LTXVAudioVAEDecode" for n in graph["nodes"]), stem
            for node in vhs:
                audio = next(i for i in node["inputs"] if i.get("name") == "audio")
                assert audio.get("link") is not None, stem


def test_vertical_shorts_sizes() -> None:
    still = json.loads((WF / "klein-shorts-still-lab-example.json").read_text(encoding="utf-8"))
    latent = next(n for n in still["nodes"] if n.get("type") == "EmptyFlux2LatentImage")
    assert latent["widgets_values"][0] == 432
    assert latent["widgets_values"][1] == 768
    wan = json.loads((WF / "wan-shorts-i2v-lab-example.json").read_text(encoding="utf-8"))
    wlat = next(n for n in wan["nodes"] if n.get("type") == "Wan22ImageToVideoLatent")
    assert wlat["widgets_values"][0] == 480
    assert wlat["widgets_values"][1] == 832


def test_before_after_and_storyboard_prefixes() -> None:
    before = json.loads((WF / "klein-before-after-lab-example.json").read_text(encoding="utf-8"))
    prefixes = {
        n["widgets_values"][0]
        for n in before["nodes"]
        if n.get("type") == "SaveImage"
    }
    assert "ez_before" in prefixes
    assert "ez_after" in prefixes
    board = json.loads((WF / "klein-storyboard-6up-lab-example.json").read_text(encoding="utf-8"))
    board_prefixes = {
        n["widgets_values"][0]
        for n in board["nodes"]
        if n.get("type") == "SaveImage"
    }
    assert board_prefixes == {f"ez_board_{i:02d}" for i in range(1, 7)}


def _save_prefixes(stem: str) -> set[str]:
    graph = json.loads((WF / f"{stem}.json").read_text(encoding="utf-8"))
    return {
        n["widgets_values"][0]
        for n in graph["nodes"]
        if n.get("type") == "SaveImage"
    }


def test_hook_still_is_vertical() -> None:
    still = json.loads((WF / "klein-hook-still-lab-example.json").read_text(encoding="utf-8"))
    latent = next(n for n in still["nodes"] if n.get("type") == "EmptyFlux2LatentImage")
    assert latent["widgets_values"][0] == 432
    assert latent["widgets_values"][1] == 768


def test_pack_v2_prefixes() -> None:
    assert _save_prefixes("klein-lighting-trio-lab-example") == {
        "ez_light_01",
        "ez_light_02",
        "ez_light_03",
    }
    assert _save_prefixes("klein-time-of-day-lab-example") == {
        f"ez_tod_{i:02d}" for i in range(1, 5)
    }
    assert _save_prefixes("klein-camera-angles-lab-example") == {
        "ez_angle_wide",
        "ez_angle_med",
        "ez_angle_close",
    }
    assert _save_prefixes("klein-color-moods-lab-example") == {
        f"ez_mood_{i:02d}" for i in range(1, 5)
    }
