"""Lab workflow and App file stems stay short and readable.

Hermetic: stdlib + shipped JSON. No Docker, network, or GPU.
"""

from __future__ import annotations

import re

from _lab_ids import REL_RENAMES, rel_id, rewrite_lab_names, stem_renames
from _lab_paths import LAB_ROOT, lab_graph_paths, load_lab_graph

MAX_STEM = 24
SKIP_NAMES = frozenset({"album.json", "cover.json"})
BANNED_STEM = re.compile(
    r"^(?:ig|yt|tt|li|fb|og|pin)-"
    r"|^(?:i2v|t2v|flf|a2v)(?:-|$)"
    r"|-i2v$"
    r"|^iclora-"
    r"|^from-(?:clay|canny|guide|klein)"
    r"|^(?:localize|finish|audio-first)$"
)


def test_rel_renames_are_unique_short_and_stable() -> None:
    """Every alias is unique, under the stem cap, and idempotent via rel_id."""
    assert REL_RENAMES
    assert len(set(REL_RENAMES)) == len(REL_RENAMES)
    # Folder moves are many-to-one (cryptic + previous path -> job folder).
    assert len(set(REL_RENAMES.values())) <= len(REL_RENAMES)
    stems = stem_renames()
    assert stems
    for old, new in REL_RENAMES.items():
        assert old != new
        assert "/" in new
        assert rel_id(old) == new
        assert rel_id(new) == new
        assert rel_id(f"{old}.json") == new
        stem = new.rsplit("/", 1)[-1]
        assert 1 <= len(stem) <= MAX_STEM, (new, len(stem))
        assert BANNED_STEM.search(stem) is None, new


def test_rel_id_maps_legacy_example_stems() -> None:
    """*-lab-example stems land on the descriptive rel, not the cryptic hop."""
    assert rel_id("wan-i2v-5s-lab-example") == "motion/silent/still-to-video-5s"
    assert rel_id("ltx-i2v-5s-lab-example") == "motion/av/still-to-video-8s"
    assert rel_id("klein-ig-square-lab-example") == "stills/instagram-square"
    assert rel_id("klein-from-clay-lab-example") == "dcc/clay-hero"
    assert rel_id("dub-localize-lab-example") == "audio/dub/clone-translate"
    assert rel_id("audio-finish-lab-example") == "audio/stem-mix"
    assert rel_id("podcast-audio-first-lab-example") == "audio/podcast/two-host-episode"
    assert rel_id("klein/still-draft") == "stills/still-draft"
    assert rel_id("stills/still-draft") == "stills/still-draft"


def test_rewrite_skips_subgraph_and_print_mode_hyphens() -> None:
    """Printer blocks and Blender --print flags are not lab graph ids."""
    blob = (
        "subgraph wan-i2v-5s; print klein-from-clay; "
        "load wan/i2v-5s then dcc/klein/from-clay"
    )
    out = rewrite_lab_names(blob)
    assert "wan-i2v-5s" in out
    assert "klein-from-clay" in out
    assert "motion/silent/still-to-video-5s" in out
    assert "dcc/clay-hero" in out
    assert "wan/i2v-5s" not in out
    assert "dcc/klein/from-clay" not in out
    prose = "Clay to finish. Cache hits still finish in 0s. matte finish."
    assert rewrite_lab_names(prose) == prose
    assert rewrite_lab_names("Queue audio/finish then audio/dub/localize") == (
        "Queue audio/stem-mix then audio/dub/clone-translate"
    )


def test_lab_graph_stems_are_descriptive() -> None:
    """Shipped _lab JSON uses the new stems; old files are gone."""
    missing_new: list[str] = []
    leftover_old: list[str] = []
    for old, new in REL_RENAMES.items():
        if not (LAB_ROOT / f"{new}.json").is_file():
            missing_new.append(new)
        if (LAB_ROOT / f"{old}.json").is_file():
            leftover_old.append(old)
    assert missing_new == [], "missing renamed graphs:\n" + "\n".join(missing_new)
    assert leftover_old == [], "old stems still on disk:\n" + "\n".join(leftover_old)


def test_lab_stems_match_lab_rel_and_avoid_jargon() -> None:
    """Every catalog graph stem is readable; extra.lab_rel matches the path."""
    banned: list[str] = []
    mismatched: list[str] = []
    too_long: list[str] = []
    graphs = [
        path
        for path in lab_graph_paths()
        if path.is_file() and path.name not in SKIP_NAMES
    ]
    assert graphs
    for path in graphs:
        rel = path.relative_to(LAB_ROOT).with_suffix("").as_posix()
        stem = path.stem
        if BANNED_STEM.search(stem):
            banned.append(rel)
        if len(stem) > MAX_STEM:
            too_long.append(f"{rel} ({len(stem)})")
        extra = load_lab_graph(path).get("extra") or {}
        lab_rel = extra.get("lab_rel")
        if lab_rel != rel:
            mismatched.append(f"{rel} lab_rel={lab_rel!r}")
        graph_id = load_lab_graph(path).get("id")
        if graph_id != stem:
            mismatched.append(f"{rel} id={graph_id!r}")
        handoff = (extra.get("lab_app_mode") or {}).get("handoff") or []
        for item in handoff:
            mapped = rel_id(str(item))
            if mapped != item:
                mismatched.append(f"{rel} handoff {item!r} -> {mapped}")
    assert banned == [], "jargon stems still shipped:\n" + "\n".join(banned)
    assert too_long == [], "stems over 24 chars:\n" + "\n".join(too_long)
    assert mismatched == [], "id/lab_rel/handoff drift:\n" + "\n".join(mismatched)
