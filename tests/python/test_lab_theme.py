"""Lab canned prompts share one original superhero 3D-animation identity."""

from __future__ import annotations

import json
from pathlib import Path

from _lab_theme import KLEIN_STILL, KLEIN_STILL_DAILY, STYLE_LOCK, WAN_T2V

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "workflows"

BANNED = ("bicycle", "storefront", "main street")
LOCK = ("3D feature-animation", "teal-and-copper")

# Packs that already use a different subject (house, mug, 90s films).
EXEMPT = {
    "klein-dream-house-lab-example",
    "klein-style-lock-lab-example",
    "klein-product-packshot-lab-example",
    "klein-podcast-cover-lab-example",
    "klein-food-tabletop-lab-example",
    "klein-before-after-lab-example",
    "ltx-interior-ambience-lab-example",
    "film-go-see-90s-run-lab-example",
    "film-still-here-90s-lab-example",
    "film-switchyard-90s-lab-example",
    "wan-i2v-shot-lab-example",
    "ltx-i2v-shot-lab-example",
}


def _graphs() -> list[Path]:
    return sorted(WF.glob("**/*-lab-example.json"))


def test_theme_module_lens_split_and_lock() -> None:
    assert STYLE_LOCK in KLEIN_STILL
    assert "teal-and-copper" in KLEIN_STILL
    assert "24mm" in KLEIN_STILL
    assert "35mm" in KLEIN_STILL_DAILY
    assert "24mm" not in KLEIN_STILL_DAILY
    assert "dollies" in WAN_T2V.lower() or "dolly" in WAN_T2V.lower()
    assert "bicycle" not in KLEIN_STILL.lower()


def test_klein_draft_and_hero_lock_superhero_3d_identity() -> None:
    draft = json.loads((WF / "klein-still-draft-lab-example.json").read_text(encoding="utf-8"))
    hero = json.loads((WF / "klein-still-hero-lab-example.json").read_text(encoding="utf-8"))

    def pos(graph: dict) -> str:
        node = next(n for n in graph["nodes"] if n.get("type") == "EZKleinPromptEnhance")
        return str(node["widgets_values"][0])

    text = pos(draft)
    assert text == pos(hero)
    for needle in LOCK:
        assert needle in text
    assert "24mm" in text
    assert "no logos, no text" not in text
    for banned in BANNED:
        assert banned not in text.lower()


def test_lab_example_graphs_drop_bicycle_theme() -> None:
    hits: list[str] = []
    for path in _graphs():
        if path.stem in EXEMPT:
            continue
        blob = path.read_text(encoding="utf-8").lower()
        for banned in BANNED:
            if banned in blob:
                hits.append(f"{path.relative_to(ROOT)}: {banned!r}")
    assert hits == []


def test_exempt_packs_keep_their_own_subjects() -> None:
    house = (WF / "klein-dream-house-lab-example.json").read_text(encoding="utf-8").lower()
    assert "cedar" in house
    film = (WF / "shorts" / "film-go-see-90s-run-lab-example.json").read_text(encoding="utf-8").lower()
    assert "windbreaker" in film
    for path in _graphs():
        if path.stem not in EXEMPT:
            continue
        blob = path.read_text(encoding="utf-8").lower()
        for banned in BANNED:
            assert banned not in blob, (path.name, banned)
