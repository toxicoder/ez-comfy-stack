"""Lab canned prompts share one original photoreal techno-wizard identity."""

from __future__ import annotations

import json
from pathlib import Path

from _lab_paths import lab_json

from _lab_theme import (
    GOSEE_IDENTITY,
    GOSEE_LTX_I2V_01,
    GOSEE_WAN_I2V_01,
    HOUSE_IDENTITY,
    HOUSE_INVENTORY,
    KLEIN_STILL,
    KLEIN_STILL_DAILY,
    STYLE_LOCK,
    WAN_T2V,
)

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "workflows"
SHORTS = WF / "shorts"

BANNED = ("bicycle", "storefront", "main street")
OLD_THEME = (
    "superhero",
    "capelet",
    "flight suit",
    "starburst",
    "3D feature-animation",
    "feature-film 3D animation",
)
OLD_LOOK = (
    "neon-wet dusk",
    "volumetric haze",
    "tech-mage",
    "game-engine pre-rendered",
    "cyberpunk tech wizard",
    "tech wizard",
    "aurora ridge",
    "electric-cyan",
    "charcoal-glass",
)
LOCK = ("photoreal still", "techno wizard")

# Packs that already use a different subject (house is wizard-home; mug, 90s still-here/switchyard, DCC).
EXEMPT = {
    "klein-product-packshot-lab-example",
    "klein-podcast-cover-lab-example",
    "klein-food-tabletop-lab-example",
    "klein-before-after-lab-example",
    "ltx-interior-ambience-lab-example",
    "film-still-here-90s-lab-example",
    "film-switchyard-90s-lab-example",
    "klein-from-clay-lab-example",
    "ltx-iclora-depth-5s-lab-example",
}


def _graphs() -> list[Path]:
    return sorted(WF.glob("**/*-lab-example.json"))


def test_theme_module_lens_split_and_lock() -> None:
    assert STYLE_LOCK in KLEIN_STILL
    assert "techno wizard" in KLEIN_STILL
    assert "24mm" in KLEIN_STILL
    assert "35mm" in KLEIN_STILL_DAILY
    assert "24mm" not in KLEIN_STILL_DAILY
    assert "dollies" in WAN_T2V.lower() or "dolly" in WAN_T2V.lower()
    assert "bicycle" not in KLEIN_STILL.lower()
    assert "superhero" not in KLEIN_STILL.lower()
    assert "neon-wet" not in KLEIN_STILL.lower()
    assert "game-engine" not in KLEIN_STILL.lower()
    assert "hope" not in KLEIN_STILL.lower()
    assert "humanity" not in KLEIN_STILL.lower()
    assert "bright future" not in KLEIN_STILL.lower()


def test_theme_module_house_bible_is_camera_free_penthouse() -> None:
    ident = HOUSE_IDENTITY.lower()
    assert STYLE_LOCK.lower() in ident
    assert "warm-glass" in ident
    assert "crown penthouse" in ident
    assert "wraparound terrace" in ident
    assert "three-bay" in ident
    assert "lounge" in ident
    assert "lantern" in ident or "path light" in ident
    assert "bay" in ident
    assert "24mm" not in ident
    assert "golden-hour" not in ident
    assert "cedar" not in ident
    assert "cabin" not in ident
    inv = HOUSE_INVENTORY.lower()
    assert "linen sofa" in inv
    assert "data-staff" in inv
    assert "terrace chairs" in inv
    assert "lantern" in inv or "path light" in inv


def test_klein_draft_and_hero_lock_cutscene_identity() -> None:
    draft = json.loads(lab_json("klein-still-draft-lab-example.json").read_text(encoding="utf-8"))
    hero = json.loads(lab_json("klein-still-hero-lab-example.json").read_text(encoding="utf-8"))

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
    assert "superhero" not in text.lower()


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


def test_lab_example_graphs_drop_superhero_theme() -> None:
    hits: list[str] = []
    for path in _graphs():
        if path.stem in EXEMPT:
            continue
        blob = path.read_text(encoding="utf-8")
        lower = blob.lower()
        for banned in OLD_THEME:
            if banned.lower() in lower:
                hits.append(f"{path.relative_to(ROOT)}: {banned!r}")
    assert hits == []


def test_lab_identity_graphs_lock_techno_wizard() -> None:
    draft = lab_json("klein-still-draft-lab-example.json").read_text(encoding="utf-8")
    for needle in LOCK:
        assert needle in draft


def test_exempt_packs_keep_their_own_subjects() -> None:
    house = lab_json("klein-dream-house-lab-example.json").read_text(encoding="utf-8").lower()
    style = lab_json("klein-style-lock-lab-example.json").read_text(encoding="utf-8").lower()
    for blob in (house, style):
        assert "warm-glass" in blob
        assert "crown penthouse" in blob
        assert "three-bay" in blob
        assert "cedar" not in blob
        assert "alpine" not in blob
        assert "charcoal-glass" not in blob
    film = lab_json("film-go-see-90s-run-lab-example.json").read_text(encoding="utf-8").lower()
    assert "sun-washed teal" in film
    assert "parkour" in film
    assert "windbreaker" not in film
    assert "electric-cyan" not in film
    for path in _graphs():
        if path.stem not in EXEMPT:
            continue
        blob = path.read_text(encoding="utf-8").lower()
        for banned in BANNED:
            assert banned not in blob, (path.name, banned)


def test_wizard_graphs_drop_dusk_cutscene_look() -> None:
    hits: list[str] = []
    for path in _graphs():
        if path.stem in EXEMPT:
            continue
        if "dcc" in str(path.relative_to(WF)):
            continue
        blob = path.read_text(encoding="utf-8").lower()
        for banned in OLD_LOOK:
            if banned.lower() in blob:
                hits.append(f"{path.relative_to(ROOT)}: {banned!r}")
    assert hits == []


def test_gosee_yaml_matches_theme_module() -> None:
    yaml_text = (SHORTS / "go-see.shots.yaml").read_text(encoding="utf-8")
    collapsed_ident = " ".join(GOSEE_IDENTITY.split())
    collapsed_yaml = " ".join(yaml_text.split())
    assert collapsed_ident in collapsed_yaml
    assert " ".join(GOSEE_LTX_I2V_01.split()) in collapsed_yaml
    assert " ".join(GOSEE_WAN_I2V_01.split()) in collapsed_yaml
    assert "glacier" not in yaml_text.lower()
    assert "aurora" not in yaml_text.lower()
    assert "neon-wet" not in yaml_text.lower()
    assert "electric-cyan" not in yaml_text.lower()
    assert "hope" not in yaml_text.lower()
    assert "humanity" not in yaml_text.lower()
