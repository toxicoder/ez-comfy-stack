"""Hermetic tests for ez_music (no Comfy, no network, no GGUF)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

import ez_music  # noqa: E402
from ez_music import nodes  # noqa: E402
from ez_music.diss_examples import (  # noqa: E402
    DISS_DURATION_S,
    DISS_EXAMPLES,
    NILL_VOICE,
    format_diss_lyrics,
    nill_tags,
)
from ez_music.edm_examples import (  # noqa: E402
    DRIVE_LOCK,
    DRIVE_TREAT_LOCK,
    DROP_WEIGHT_NEEDLES,
    EDM_DURATION_S,
    EDM_EXAMPLES,
    drive_tags,
    format_edm_score,
)
from ez_music.nodes import (  # noqa: E402
    DRAFT_LYRICS,
    EZRapLyrics,
    FULL_LYRICS,
    NODE_CLASS_MAPPINGS,
    load_writer_prompt,
)

LIVING_MC_NEEDLES = ("Drake", "Kendrick", "Eminem", "Suno", "Udio", "Bill Nye")
LIVING_EDM_NEEDLES = (
    "Avicii",
    "Skrillex",
    "Deadmau5",
    "Tiësto",
    "Tiesto",
    "Garrix",
    "Guetta",
    "Marshmello",
    "Suno",
    "Udio",
)


def test_pack_imports_without_extra_pip() -> None:
    assert ez_music.NODE_CLASS_MAPPINGS == NODE_CLASS_MAPPINGS
    assert set(NODE_CLASS_MAPPINGS) == {"EZRapLyrics"}
    cls = NODE_CLASS_MAPPINGS["EZRapLyrics"]
    assert cls.CATEGORY == "ez-comfy/music"
    spec = cls.INPUT_TYPES()
    assert spec["required"]["enhance"][1]["default"] is True
    assert spec["required"]["enhance"][1]["label_on"] == "On"
    assert spec["required"]["enhance"][1]["label_off"] == "Off"
    assert "[verse]" in spec["required"]["lyrics"][1]["default"]
    assert "[chorus]" in spec["required"]["lyrics"][1]["default"]


def test_seed_lyrics_have_sections() -> None:
    assert "[verse]" in DRAFT_LYRICS
    assert "[chorus]" in DRAFT_LYRICS
    assert "[verse]" in FULL_LYRICS
    assert "[chorus]" in FULL_LYRICS
    assert "[outro]" in FULL_LYRICS
    for needle in LIVING_MC_NEEDLES:
        assert needle not in DRAFT_LYRICS
        assert needle not in FULL_LYRICS


EXPECTED_NILL_BYE_TITLES = (
    "lab coat lecture",
    "peer review",
    "in his feels",
    "fake cool",
    "hypothesis vs rumor",
    "control group",
    "sample size",
    "placebo",
    "error bars",
    "lab notebook",
    "office hours",
    "grant denied",
    "contamination",
    "double blind",
    "replicate or retract",
    "citation needed",
    "p-hacking",
    "null result",
    "expired reagent",
    "lab safety",
    "rumor mill",
    "gym selfie",
    "rented drip",
    "clout diet",
    "mood forecast",
    "algorithm",
    "story time",
    "caption vs data",
    "energy drink",
    "campfire rumor",
    "false drop",
    "velvet rope",
    "fog machine",
    "guest list",
    "sparkler science",
    "bottle service",
    "strobe claim",
    "amen rumor",
    "wobble alibi",
    "supersaw flex",
    "laser show",
    "two-step alibi",
    "jersey bounce",
    "kick-split myth",
    "uplifting rumor",
)
SPOKEN_WORD_TITLES = frozenset({"peer review", "grant denied", "story time"})
VARIETY_EDM_NEEDLES = (
    "trap",
    "808",
    "edm",
    "house",
    "techno",
    "trance",
    "dubstep",
    "drum and bass",
    "jersey",
    "phonk",
    "hardstyle",
    "garage",
    "future bass",
    "electro",
)
TRAP_EDM_GENRES = (
    "trap",
    "phonk",
    "rage",
    "house",
    "techno",
    "drum and bass",
    "dubstep",
    "future bass",
    "electro",
    "garage",
    "jersey club",
    "hardstyle",
    "trance",
)


def test_nill_tags_lock_dry_booth_voice() -> None:
    tags = nill_tags("jazz hop", "brushed drums", bpm=90)
    assert tags == (
        "jazz hop, brushed drums, male rap vocals, dry booth, no autotune, 90 bpm"
    )


def test_format_diss_lyrics_requires_three_verses() -> None:
    with pytest.raises(ValueError, match="at least 3 verses"):
        format_diss_lyrics(
            intro="yeah",
            verses=("one", "two"),
            chorus="hook",
            outro="cut",
        )


def test_nill_bye_diss_examples_are_original_180s() -> None:
    assert DISS_DURATION_S == 180.0
    assert len(DISS_EXAMPLES) == 45
    prefixes: list[str] = []
    stems: list[str] = []
    seeds: list[int] = []
    series_counts = {"lab": 0, "variety": 0, "trap-edm": 0}
    spoken_titles: set[str] = set()
    for ex in DISS_EXAMPLES:
        assert ex["duration"] == DISS_DURATION_S
        lyrics = ex["lyrics"]
        assert "[verse]" in lyrics
        assert "[chorus]" in lyrics
        assert "[outro]" in lyrics
        assert lyrics.count("[verse]") >= 3
        assert lyrics.count("[chorus]") >= 3
        assert "Nill Bye" in lyrics
        assert "Rake" in lyrics
        assert str(ex["bpm"]) in ex["tags"]
        assert ex["stem"].startswith("music-rap-nill-bye-")
        assert ex["stem"].endswith("-lab-example")
        assert ex["prefix"].startswith("ez_rap_nill_")
        assert ex["series"] in series_counts
        series_counts[ex["series"]] += 1
        if ex["series"] != "lab":
            for token in NILL_VOICE.split(", "):
                assert token in ex["tags"], (ex["stem"], token)
        if ex["series"] == "variety":
            low = ex["tags"].lower()
            for needle in VARIETY_EDM_NEEDLES:
                assert needle not in low, (ex["stem"], needle)
        if ex["series"] == "trap-edm":
            low = ex["tags"].lower()
            assert any(genre in low for genre in TRAP_EDM_GENRES), ex["stem"]
        for needle in LIVING_MC_NEEDLES:
            assert needle not in lyrics
            assert needle not in ex["tags"]
            assert needle not in ex["description"]
        prefixes.append(ex["prefix"])
        stems.append(ex["stem"])
        seeds.append(int(ex["seed"]))
        if "[spoken word]" in lyrics:
            spoken_titles.add(ex["title"])
    assert len(set(prefixes)) == 45
    assert len(set(stems)) == 45
    assert series_counts == {"lab": 15, "variety": 15, "trap-edm": 15}
    assert spoken_titles == SPOKEN_WORD_TITLES
    assert any(seed != 42 for seed in seeds)
    assert tuple(ex["title"] for ex in DISS_EXAMPLES) == EXPECTED_NILL_BYE_TITLES
    assert "Rake walks in with a club report" in DISS_EXAMPLES[0]["lyrics"]
    assert "Peer review time" in DISS_EXAMPLES[1]["lyrics"]
    assert "Rake in his feels like a full-time job" in DISS_EXAMPLES[2]["lyrics"]
    assert "Rake talk club like a uniform" in DISS_EXAMPLES[3]["lyrics"]
    assert "Hypothesis: Rake is cool" in DISS_EXAMPLES[4]["lyrics"]


EXPECTED_DRIVE_THROUGH_TITLES = (
    "night window",
    "open lane",
    "exit seven",
    "skyline pass",
    "on-ramp",
    "tunnel bass",
    "wide open",
    "overpass",
    "second wave",
    "freight pulse",
    "keep going",
    "horizon kick",
    "clean wreckage",
    "heart lane",
    "dawn receipt",
)
DRIVE_TREAT_TITLES = frozenset({"wide open", "second wave"})


def _valid_edm_sections() -> list[tuple[str, str]]:
    return [
        ("intro", "kick in"),
        ("inst", "heavy drop\nstacked bass"),
        ("inst", "harder drop\nwreck hats"),
        ("outro", "blend out"),
    ]


def _score_labels(lyrics: str) -> tuple[str, ...]:
    labels: list[str] = []
    for line in lyrics.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            labels.append(stripped[1:-1])
    return tuple(labels)


def _drop_blocks(lyrics: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    for line in lyrics.splitlines():
        if line.startswith("[") and current:
            blocks.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        blocks.append("\n".join(current))
    return [block for block in blocks if "drop" in block.lower()]


def test_drive_tags_lock_instrumental_bed() -> None:
    tags = drive_tags("future bass", "supersaw", bpm=148)
    assert tags == (
        "future bass, supersaw, instrumental, no vocals, no singing, "
        "original composition, 148 bpm"
    )
    for token in DRIVE_LOCK.split(", "):
        assert token in tags


def test_drive_tags_lock_vocal_treat() -> None:
    tags = drive_tags("big room", "festival", bpm=150, treat=True)
    assert tags == (
        "big room, festival, sparse vocal chop, DJ shout, no rap, "
        "original composition, 150 bpm"
    )
    for token in DRIVE_TREAT_LOCK.split(", "):
        assert token in tags
    assert "no vocals" not in tags
    assert "no singing" not in tags


def test_format_edm_score_requires_weighted_drops() -> None:
    sections = _valid_edm_sections()
    sections[1] = ("inst", "named drop\nno weight")
    with pytest.raises(ValueError, match="weight needle"):
        format_edm_score(*sections)


def test_format_edm_score_requires_two_drops() -> None:
    sections = _valid_edm_sections()
    sections[1] = ("inst", "hats only")
    with pytest.raises(ValueError, match="two named drops"):
        format_edm_score(*sections)


def test_format_edm_score_rejects_unknown_label() -> None:
    sections = _valid_edm_sections()
    sections[0] = ("verse", "bars")
    with pytest.raises(ValueError, match="unknown score label"):
        format_edm_score(*sections)


def test_format_edm_score_rejects_empty_body() -> None:
    sections = _valid_edm_sections()
    sections[0] = ("intro", "   ")
    with pytest.raises(ValueError, match="body is empty"):
        format_edm_score(*sections)


def test_format_edm_score_rejects_short_score() -> None:
    with pytest.raises(ValueError, match="at least three sections"):
        format_edm_score(
            ("inst", "heavy drop\nstacked bass"),
            ("outro", "cut"),
        )


def test_format_edm_score_allows_chorus_treat() -> None:
    score = format_edm_score(
        ("intro", "mix in"),
        ("chorus", "hands up"),
        ("inst", "heavy drop\nstacked kick"),
        ("inst", "harder drop\nmainstage wreck"),
        ("outro", "blend out"),
    )
    assert "[chorus]" in score
    assert "[verse]" not in score
    assert score.count("drop") >= 2


def test_drive_through_edm_examples_are_original_180s() -> None:
    assert EDM_DURATION_S == 180.0
    assert len(EDM_EXAMPLES) == 15
    prefixes: list[str] = []
    stems: list[str] = []
    bpms: list[int] = []
    signatures: list[tuple[str, ...]] = []
    triple_drops = 0
    treat_titles: list[str] = []
    for ex in EDM_EXAMPLES:
        assert ex["duration"] == EDM_DURATION_S
        assert ex["series"] == "drive-through"
        lyrics = ex["lyrics"]
        assert "[outro]" in lyrics
        assert "[inst]" in lyrics
        assert "[verse]" not in lyrics
        assert "[spoken word]" not in lyrics
        assert "Drive-through" in lyrics
        labels = _score_labels(lyrics)
        assert labels[-1] == "outro"
        signatures.append(labels)
        drops = _drop_blocks(lyrics)
        assert len(drops) >= 2, (ex["stem"], len(drops))
        if len(drops) >= 3:
            triple_drops += 1
        for block in drops:
            low = block.lower()
            assert any(needle in low for needle in DROP_WEIGHT_NEEDLES), (
                ex["stem"],
                block,
            )
        treat = ex["title"] in DRIVE_TREAT_TITLES
        if treat:
            assert "[chorus]" in lyrics
            assert lyrics.count("[chorus]") == 1
            assert ex["ace_mode"] == "vocal"
            for token in DRIVE_TREAT_LOCK.split(", "):
                assert token in ex["tags"], (ex["stem"], token)
            treat_titles.append(ex["title"])
        else:
            assert "[chorus]" not in lyrics
            assert "[intro]" in lyrics or labels[0] == "inst"
            assert ex["ace_mode"] == "instrumental"
            for token in DRIVE_LOCK.split(", "):
                assert token in ex["tags"], (ex["stem"], token)
        assert "rave" in ex["tags"]
        assert str(ex["bpm"]) in ex["tags"]
        assert ex["stem"].startswith("music-edm-drive-through-")
        assert ex["stem"].endswith("-lab-example")
        assert ex["prefix"].startswith("ez_edm_drive_")
        for needle in (*LIVING_MC_NEEDLES, *LIVING_EDM_NEEDLES):
            assert needle not in lyrics
            assert needle not in ex["tags"]
            assert needle not in ex["description"]
        prefixes.append(ex["prefix"])
        stems.append(ex["stem"])
        bpms.append(int(ex["bpm"]))
    assert len(set(prefixes)) == 15
    assert len(set(stems)) == 15
    assert min(bpms) >= 140
    assert max(bpms) >= 170
    assert sum(1 for bpm in bpms if bpm >= 145) >= 12
    assert triple_drops >= 4
    assert len(set(signatures)) >= 8
    for left, right in zip(signatures, signatures[1:]):
        assert left != right
    assert frozenset(treat_titles) == DRIVE_TREAT_TITLES
    assert tuple(ex["title"] for ex in EDM_EXAMPLES) == EXPECTED_DRIVE_THROUGH_TITLES
    assert "four on the floor" in EDM_EXAMPLES[0]["lyrics"]
    assert "full send drop" in EDM_EXAMPLES[1]["lyrics"]
    assert "filter mix-in" in EDM_EXAMPLES[2]["lyrics"]


def test_writer_prompt_forbids_living_mcs() -> None:
    prompt = load_writer_prompt()
    blob = prompt.lower()
    assert "living" in blob
    assert "song title" in blob or "existing song" in blob
    assert "famous" in blob and "hook" in blob
    assert "in the style of" in blob


def test_lyrics_enhance_off_passthrough() -> None:
    with patch("ez_prompt_enhance.client.complete") as complete:
        out = EZRapLyrics().run(DRAFT_LYRICS, False)
    complete.assert_not_called()
    assert out["result"][0] == DRAFT_LYRICS
    assert out["ui"]["passthrough"][0] == "enhance off"


def test_lyrics_missing_gguf_passthrough() -> None:
    with (
        patch("ez_prompt_enhance.client.complete", return_value=("", "GGUF missing")),
        patch("ez_prompt_enhance.client._close_llm"),
    ):
        out = EZRapLyrics().run(DRAFT_LYRICS, True)
    assert out["result"][0] == DRAFT_LYRICS
    assert "GGUF missing" in out["ui"]["passthrough"][0]
