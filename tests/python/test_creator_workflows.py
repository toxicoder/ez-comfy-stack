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
