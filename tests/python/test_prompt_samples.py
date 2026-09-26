"""Sample-prompt catalogs and resolver (hermetic, no Comfy, no GGUF)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_prompt_enhance.samples import CUSTOM as SAMPLE_CUSTOM  # noqa: E402
from ez_prompt_enhance.samples import (  # noqa: E402
    SAMPLE_COUNT,
    SAMPLES_DIR,
    catalog_expected_count,
    album_hides_sample,
    catalog_for_rel,
    is_custom,
    list_catalog_ids,
    load_catalog,
    load_index,
    resolve_ace_sample,
    resolve_catalog,
    resolve_prompt,
    sample_combo_labels,
    sample_labels,
)

from _lab_paths import lab_example_paths, lab_rel_of  # noqa: E402
from _stamp_app_mode import BANNED  # noqa: E402

CAMERA_IP = (
    "Hardcore Henry",
    "Hardcore Harry",
    "Ilya Naishuller",
    "Adventure Mask",
    "Biting Elbows",
)

SKIP_SAMPLE_PREFIXES = (
    "audio/dub/",
    "audio/stem-mix",
    "dcc/still-to-mesh",
    "optional/trellis2",
    "optional/longcat",
    "inspire/cinema-rack",
    "inspire/audio-rack",
    "films/tide-table/",
    "films/night-oven/",
    "films/glasshouse/",
    "films/last-lane/",
    "films/breakwater/",
)


def test_each_catalog_has_twenty_unique_recipes() -> None:
    ids = list_catalog_ids()
    assert ids
    assert "index" not in ids
    assert catalog_expected_count("klein_t2i") == SAMPLE_COUNT
    assert catalog_expected_count("klein_background_swap") == 100
    for cid in ids:
        rows = load_catalog(cid)
        expected = catalog_expected_count(cid)
        assert len(rows) == expected, cid
        labels = [item.label for item in rows]
        slugs = [item.id for item in rows]
        assert len(set(labels)) == expected, cid
        assert len(set(slugs)) == expected, cid
        assert SAMPLE_CUSTOM not in {item.lower() for item in labels}
        assert sample_labels(cid)[-1] == SAMPLE_CUSTOM
        assert len(sample_labels(cid)) == expected + 1


def test_index_maps_in_scope_graphs() -> None:
    index = load_index()
    assert index
    catalog_ids = set(list_catalog_ids())
    for rel, cid in index.items():
        assert cid in catalog_ids, (rel, cid)
        assert not album_hides_sample(rel)


def test_album_tracks_hide_sample_covers_do_not() -> None:
    assert album_hides_sample("audio/albums/nill-bye/peer-review/01-lab-coat")
    assert album_hides_sample("audio/albums/drive-through/hour-1/album")
    assert not album_hides_sample("audio/albums/nill-bye/peer-review/cover")
    assert not album_hides_sample("audio/music/rap-draft")
    assert not album_hides_sample("stills/still-draft")
    assert catalog_for_rel("audio/albums/nill-bye/peer-review/cover") == "klein_t2i"
    assert catalog_for_rel("audio/albums/nill-bye/peer-review/01-lab-coat") == ""


def test_in_scope_lab_graphs_have_catalogs() -> None:
    index = load_index()
    missing: list[str] = []
    for path in lab_example_paths():
        rel = lab_rel_of(path)
        if album_hides_sample(rel):
            continue
        if rel.endswith("/album"):
            continue
        if any(rel.startswith(prefix) for prefix in SKIP_SAMPLE_PREFIXES):
            continue
        extra = json.loads(path.read_text(encoding="utf-8")).get("extra") or {}
        if extra.get("lab_stub") is True:
            continue
        mapped = catalog_for_rel(rel) or index.get(rel, "")
        if not mapped:
            missing.append(rel)
    assert missing == [], missing


def test_resolve_prompt_custom_and_sample() -> None:
    assert is_custom(SAMPLE_CUSTOM)
    assert is_custom("")
    assert not is_custom("Rooftop golden hour")
    custom = "type this instead"
    assert resolve_prompt("klein_t2i", SAMPLE_CUSTOM, custom) == custom
    rows = load_catalog("klein_t2i")
    first = rows[0]
    assert "techno wizard" in first.prompt
    assert (
        resolve_prompt("klein_t2i", first.label, "stale textarea") == first.prompt
    )
    assert resolve_prompt("klein_t2i", "not-a-real-sample", custom) == custom
    assert resolve_prompt("stills/still-draft", first.label, custom) == first.prompt


def test_resolve_ace_sample_fills_tags_and_lyrics() -> None:
    tags, lyrics = resolve_ace_sample(
        "rap_draft", SAMPLE_CUSTOM, "widget tags", "widget lyrics"
    )
    assert tags == "widget tags"
    assert lyrics == "widget lyrics"
    rows = load_catalog("rap_draft")
    first = rows[0]
    out_tags, out_lyrics = resolve_ace_sample(
        "rap_draft", first.label, "stale", "stale"
    )
    assert "boom bap" in out_tags
    assert "[verse]" in out_lyrics
    assert "living" not in out_lyrics.lower() or "MC" not in out_lyrics


def test_family_fallback_from_node_type() -> None:
    assert resolve_catalog("", node_type="EZKleinPromptEnhance", mode="t2i") == (
        "klein_t2i"
    )
    assert resolve_catalog("", node_type="EZKleinPromptEnhance", mode="text_swap") == (
        "klein_text_swap"
    )
    assert resolve_catalog("", node_type="EZWanPromptEnhance", mode="i2v") == (
        "wan_i2v"
    )
    assert resolve_catalog("", node_type="EZSamplePrompt") == "forge_lazy"


def test_catalogs_stay_clean_of_banned_strings() -> None:
    blob = ""
    for path in SAMPLES_DIR.glob("*.json"):
        blob += path.read_text(encoding="utf-8")
    for needle in BANNED:
        assert needle not in blob, needle
    for needle in CAMERA_IP:
        assert needle not in blob, needle


def test_cubic_block_world_rebuilds_the_photographed_place() -> None:
    """Cubic block world rebuilds this place as cubes and leaves people to paste."""
    rows = load_catalog("klein_background_swap")
    hit = next(item for item in rows if item.id == "voxel-block-world")
    assert hit.label == "Cubic block world"
    folded = hit.prompt.casefold()
    assert folded.startswith("rebuild this photographed place")
    assert "block study" in folded
    assert "cube water" in folded
    assert "stacked block walls" in folded
    assert "texel grid" in folded
    assert "empty of people" in folded
    assert "no person-shaped blocks" in folded
    assert "keep the subject" not in folded
    assert "minecraft" not in folded
    assert "mojang" not in folded
    assert len(hit.prompt.split()) < 100
    blob = "\n".join(item.prompt for item in rows)
    assert "replace only the background" not in blob.casefold()
    for item in rows:
        if item.id == "voxel-block-world":
            continue
        body = item.prompt.casefold()
        assert "entire environment" in body, item.id
        assert "ground or floor" in body, item.id


def test_klein_t2i_sample_one_matches_lab_canned() -> None:
    from _lab_theme import KLEIN_STILL

    first = load_catalog("klein_t2i")[0]
    assert first.prompt == KLEIN_STILL


def test_klein_sample_combo_accepts_place_catalog_labels() -> None:
    """Comfy validates sample against INPUT_TYPES, not the JS-filtered dropdown.

    HOUSE IDENTITY on stills/dream-house uses klein_place (Cliff villa). The
    Python combo used to be klein_t2i only, so Queue failed with
    'The value Cliff villa for HOUSE IDENTITY's sample is not available.'
    """
    from ez_prompt_enhance.nodes import EZAceStepPromptEnhance, EZKleinPromptEnhance

    place = sample_labels("klein_place")
    t2i = sample_labels("klein_t2i")
    assert "Cliff villa" in place
    assert "Cliff villa" not in t2i
    assert len(place) == SAMPLE_COUNT + 1
    assert place[-1] == SAMPLE_CUSTOM

    klein_combo = EZKleinPromptEnhance.INPUT_TYPES()["required"]["sample"]
    labels, opts = klein_combo
    assert opts["default"] == SAMPLE_CUSTOM
    assert labels[-1] == SAMPLE_CUSTOM
    assert "Cliff villa" in labels
    assert t2i[0] in labels
    union = sample_combo_labels("klein_t2i")
    assert union == labels
    assert union.index(t2i[0]) < union.index("Cliff villa")

    ace_labels = EZAceStepPromptEnhance.INPUT_TYPES()["required"]["sample"][0]
    rap_full = load_catalog("rap_full")[0].label
    assert rap_full in ace_labels

    cliff = resolve_prompt(
        "stills/dream-house",
        "Cliff villa",
        "stale textarea",
        node_type="EZKleinPromptEnhance",
        mode="identity",
    )
    assert "cliff villa" in cliff.lower()
    assert cliff != "stale textarea"


def test_visible_sample_labels_exclude_foreign_catalogs() -> None:
    """App dropdown is one catalog; Klein stills must not list Wan or place recipes."""
    place = sample_labels("klein_place")
    t2i = sample_labels("klein_t2i")
    wan = sample_labels("wan_i2v")
    assert "Cliff villa" in place
    assert "Cliff villa" not in t2i
    assert "Cliff villa" not in wan
    assert "Slow push-in" in wan
    assert "Slow push-in" not in t2i
    assert "Rooftop golden hour" in t2i
    assert "Rooftop golden hour" not in place
    assert place[-1] == SAMPLE_CUSTOM
    assert t2i[-1] == SAMPLE_CUSTOM
    assert wan[-1] == SAMPLE_CUSTOM


def test_index_graphs_visible_labels_match_catalog() -> None:
    """Every indexed lab graph resolves to a 20+Custom catalog, not the union."""
    index = load_index()
    for rel, cid in index.items():
        assert catalog_for_rel(rel) == cid, rel
        visible = sample_labels(cid)
        assert len(visible) == catalog_expected_count(cid) + 1, (rel, cid)
        assert visible[-1] == SAMPLE_CUSTOM


def test_catalog_for_rel_specialized_graphs() -> None:
    assert catalog_for_rel("stills/dream-house") == "klein_place"
    assert catalog_for_rel("stills/still-draft") == "klein_t2i"
    assert catalog_for_rel("stills/text-swap") == "klein_text_swap"
    assert catalog_for_rel("motion/loops/gif-loop") == "wan_loop"
    assert catalog_for_rel("inspire/app-forge") == "app_forge"


def test_enhance_node_sample_overrides_textarea() -> None:
    from ez_prompt_enhance.nodes import EZKleinPromptEnhance, EZSamplePrompt

    first = load_catalog("klein_t2i")[0]
    klein = EZKleinPromptEnhance()
    custom = klein.run(
        "stale textarea",
        False,
        "t2i",
        "YouTube 16:9 still",
        sample=SAMPLE_CUSTOM,
    )
    assert custom["result"][0] == "stale textarea"
    picked = klein.run(
        "stale textarea",
        False,
        "t2i",
        "YouTube 16:9 still",
        sample=first.label,
        catalog="klein_t2i",
    )
    assert picked["result"][0] == first.prompt
    types = klein.INPUT_TYPES()["required"]
    assert list(types)[0] == "sample"
    assert "catalog" in types
    desk = EZSamplePrompt()
    out = desk.run("typed", sample=SAMPLE_CUSTOM)
    assert out[0] == "typed"
    lazy = load_catalog("forge_lazy")[0]
    picked_desk = desk.run("typed", sample=lazy.label, catalog="forge_lazy")
    assert picked_desk[0] == lazy.prompt
