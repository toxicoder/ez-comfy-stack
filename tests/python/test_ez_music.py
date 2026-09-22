"""Hermetic tests for ez_music (no Comfy, no network, no GGUF)."""

from __future__ import annotations

import re
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
    nill_output_prefix,
    nill_tags,
)
from ez_music.drive_arrange import DRIVE_BPM_CHOICES, _SPATIAL, lift_drive_bpm  # noqa: E402
from ez_music.edm_examples import (  # noqa: E402
    BANNED_STYLE_NEEDLES,
    BASS_NEEDLES,
    BED_CUT_NEEDLES,
    DRIVE_LOCK,
    DRIVE_TREAT_LOCK,
    DROP_WEIGHT_NEEDLES,
    EDM_DURATION_S,
    EDM_EXAMPLES,
    EDM_LAYOUTS,
    FORBIDDEN_SCORE_NEEDLES,
    HEADLINER_BOUNCE_NEEDLES,
    HIGH_PITCH_NEEDLES,
    HIPHOP_DRUM_NEEDLES,
    MOTION_NEEDLES,
    PAUSE_ONLY_TOKENS,
    PEDAL_BASS_NEEDLE,
    QUIET_NEEDLES,
    SECRET_HOMAGE_NEEDLES,
    SUB_WEIGHT_NEEDLES,
    WARP_NEEDLES,
    _ex,
    _uniquify_score,
    drive_tags,
    format_edm_score,
)
from ez_music.song_plan import duration_seconds  # noqa: E402
from ez_music.albums import (  # noqa: E402
    DRIVE_THROUGH_ALBUMS,
    NILL_BYE_ALBUMS,
    album_rel,
    drive_album_for_phase,
    nill_album_for_series,
    shipped_albums,
)
from ez_music.naming import (  # noqa: E402
    DRIVE_THROUGH_ARTIST,
    NILL_BYE_ARTIST,
    album_output_dir,
    music_output_prefix,
    title_case_song,
)
from ez_music.nodes import (  # noqa: E402
    DRAFT_LYRICS,
    EZAlbumPack,
    EZAudioMetadata,
    EZRapLyrics,
    FULL_LYRICS,
    NODE_CLASS_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS,
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
    "Rezz",
    "Tipper",
    "Subtronics",
    "LSDream",
    "GRiZ",
    "Zeds Dead",
    "Electric Forest",
    "Suno",
    "Udio",
)


def test_pack_imports_without_extra_pip() -> None:
    assert ez_music.NODE_CLASS_MAPPINGS == NODE_CLASS_MAPPINGS
    assert set(NODE_CLASS_MAPPINGS) == {
        "EZRapLyrics",
        "EZAudioMetadata",
        "EZAlbumPack",
    }
    cls = NODE_CLASS_MAPPINGS["EZRapLyrics"]
    assert cls.CATEGORY == "ez-comfy/music"  # type: ignore[attr-defined]
    spec = cls.INPUT_TYPES()  # type: ignore[attr-defined]
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
    "frozen ercot",
    "abject failure",
    "six week clock",
    "no-bid wire",
    "gavel theater",
    "property hymn",
    "voucher raid",
    "uninsured blues",
    "locked stacks",
    "mask order",
    "mid decade map",
    "rack tax",
    "wudu letter",
    "fourth term",
    "campus cordon",
    "lone star tab",
    "river buoy",
    "bus receipt",
    "guard detail",
    "chase wreck",
    "frequency drop",
    "permitless",
    "trigger clock",
    "disaster stamp",
    "windmill blame",
    "yass primary",
    "hold request",
    "sharia plank",
    "invasion hymn",
    "demolish hook",
    "thirty four counts",
    "one eighty seven",
    "eleven seven eighty",
    "fake electors",
    "bathroom boxes",
    "statement of worth",
    "university tab",
    "ukraine hold",
    "travel memo",
    "zero tolerance",
    "census question",
    "paris walkout",
    "emoluments suite",
    "seven fifty",
    "carroll tab",
    "pardon flood",
    "ieepa wreck",
    "gold card",
    "memecoin tab",
    "east wing wreck",
    "metro surge",
    "due process",
    "kennedy plaque",
    "birthright order",
    "cook firing",
    "inspector purge",
    "law firm order",
    "visa ticket",
    "shadow docket",
    "immunity hymn",
    "winterize wells",
    "registered report",
    "named uncertainty",
    "scif only",
    "hearing first",
    "keep the match",
    "honest census",
    "paris seat",
    "qualified divest",
    "return pdf",
    "casework screen",
    "district door",
    "levy in code",
    "fourteenth clause",
    "one college",
    "duty switch",
    "article one",
    "for-cause lock",
    "ig notice",
    "counsel stays",
    "prevailing wage",
    "merits syllabus",
    "unofficial sort",
    "clemency file",
    "congress the wing",
    "tie the island",
    "decade lines",
    "ratepayer bus",
    "open quad",
    "wrench the tap",
)
SPOKEN_WORD_TITLES = frozenset(
    {
        "peer review",
        "grant denied",
        "story time",
        "abject failure",
        "disaster stamp",
        "one eighty seven",
        "pardon flood",
        "registered report",
        "duty switch",
    }
)
RAKE_SERIES = frozenset({"lab", "variety", "trap-edm"})
CIVIC_SERIES = frozenset({"civic", "civic-club"})
FEDERAL_SERIES = frozenset({"federal", "federal-club"})
PROGRESS_SERIES = frozenset({"progress", "progress-club"})
DISABILITY_NEEDLES = (
    "wheelchair",
    "paralyzed",
    "paralysis",
    "paraplegic",
    "cripple",
    "crippled",
    "disabled",
    "disability",
    "oak tree",
    "1984",
)
PUNCH_DOWN_NEEDLES = (
    "caliphate",
    "fiqh",
    "jihad",
    "theocracy",
    "illegals",
    "illegal alien",
    "terror noun",
    "apartheid plumbing",
)
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


def test_title_case_song_and_output_prefix() -> None:
    assert title_case_song("lab coat lecture") == "Lab Coat Lecture"
    assert title_case_song("p-hacking") == "P-Hacking"
    assert title_case_song("on-ramp") == "On-Ramp"
    assert title_case_song("two-step alibi") == "Two-Step Alibi"
    assert title_case_song("hypothesis vs rumor") == "Hypothesis vs Rumor"
    assert title_case_song("replicate or retract") == "Replicate or Retract"
    assert music_output_prefix("lab coat lecture", 1) == "01 - Lab Coat Lecture"
    assert music_output_prefix("night window", 15) == "15 - Night Window"
    with pytest.raises(ValueError, match="empty"):
        title_case_song("  ")
    with pytest.raises(ValueError, match="track"):
        music_output_prefix("lab coat lecture", 0)


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
    assert len(DISS_EXAMPLES) == 135
    prefixes: list[str] = []
    stems: list[str] = []
    seeds: list[int] = []
    series_counts = {
        "lab": 0,
        "variety": 0,
        "trap-edm": 0,
        "civic": 0,
        "civic-club": 0,
        "federal": 0,
        "federal-club": 0,
        "progress": 0,
        "progress-club": 0,
    }
    phase_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0}
    spoken_titles: set[str] = set()
    series_phase = {
        "lab": 0,
        "variety": 1,
        "trap-edm": 2,
        "civic": 3,
        "civic-club": 4,
        "federal": 5,
        "federal-club": 6,
        "progress": 7,
        "progress-club": 8,
    }
    albums: dict[str, list] = {}
    for ex in DISS_EXAMPLES:
        assert 64.0 <= float(ex["duration"]) <= 210.0
        assert ex["form_id"]
        assert ex["meter"] in {"2", "3", "4", "6"}
        assert ex["keyscale"]
        if ex["series"] in {"trap-edm", "civic-club", "federal-club", "progress-club"}:
            assert ex["meter"] == "4", ex["stem"]
        lyrics = ex["lyrics"]
        assert "[verse]" in lyrics
        assert "[chorus]" in lyrics or "[chorus -" in lyrics
        assert "[outro]" in lyrics
        assert lyrics.count("[verse]") >= 1
        assert "Nill Bye" in lyrics
        albums.setdefault(str(ex["album_slug"]), []).append(ex)
        if ex["series"] in CIVIC_SERIES:
            assert "Abbott" in lyrics
            assert "Rake" not in lyrics
        elif ex["series"] in FEDERAL_SERIES:
            assert "Trump" in lyrics
            assert "Rake" not in lyrics
            assert "Abbott" not in lyrics
        elif ex["series"] in PROGRESS_SERIES:
            assert "Rake" not in lyrics
            assert "Abbott" not in lyrics
            assert "Trump" not in lyrics
            assert "diss" not in ex["description"]
            assert "roast" not in ex["description"]
            assert "progress" in ex["description"]
        else:
            assert ex["series"] in RAKE_SERIES
            assert "Rake" in lyrics
        assert str(ex["bpm"]) in ex["tags"]
        assert ex["stem"] == f"{ex['track']:02d}-{ex['slug']}"
        assert not ex["stem"].endswith("-lab-example")
        assert ex["series"] in series_counts
        assert ex["phase"] == series_phase[ex["series"]]
        assert ex["album"] == NILL_BYE_ALBUMS[ex["series"]]["title"]
        assert ex["artist"] == NILL_BYE_ARTIST
        assert ex["track"] >= 1
        assert ex["tracktotal"] == 15
        assert ex["prefix"] == nill_output_prefix(ex["title"], ex["track"])
        assert ex["prefix"] == f"{ex['track']:02d} - {title_case_song(ex['title'])}"
        assert ex["rel"] == album_rel("nill-bye", ex["album_slug"], ex["stem"])
        series_counts[ex["series"]] += 1
        phase_counts[ex["phase"]] += 1
        if ex["series"] != "lab":
            for token in NILL_VOICE.split(", "):
                assert token in ex["tags"], (ex["stem"], token)
        if ex["series"] in {"variety", "civic", "federal", "progress"}:
            low = ex["tags"].lower()
            for needle in VARIETY_EDM_NEEDLES:
                assert needle not in low, (ex["stem"], needle)
        if ex["series"] in {
            "trap-edm",
            "civic-club",
            "federal-club",
            "progress-club",
        }:
            low = ex["tags"].lower()
            assert any(genre in low for genre in TRAP_EDM_GENRES), ex["stem"]
        for needle in LIVING_MC_NEEDLES:
            assert needle not in lyrics
            assert needle not in ex["tags"]
            assert needle not in ex["description"]
        low_lyrics = lyrics.lower()
        for needle in DISABILITY_NEEDLES:
            assert needle not in low_lyrics, (ex["stem"], needle)
        if (
            ex["series"] in CIVIC_SERIES
            or ex["series"] in FEDERAL_SERIES
            or ex["series"] in PROGRESS_SERIES
        ):
            for needle in PUNCH_DOWN_NEEDLES:
                assert needle not in low_lyrics, (ex["stem"], needle)
        prefixes.append(ex["prefix"])
        stems.append(ex["stem"])
        seeds.append(int(ex["seed"]))
        if "[spoken word]" in lyrics:
            spoken_titles.add(ex["title"])
    assert len(set(prefixes)) == 135
    assert len(set(stems)) == 135
    assert series_counts == {
        "lab": 15,
        "variety": 15,
        "trap-edm": 15,
        "civic": 15,
        "civic-club": 15,
        "federal": 15,
        "federal-club": 15,
        "progress": 15,
        "progress-club": 15,
    }
    assert phase_counts == {
        0: 15,
        1: 15,
        2: 15,
        3: 15,
        4: 15,
        5: 15,
        6: 15,
        7: 15,
        8: 15,
    }
    for slug, rows in albums.items():
        assert len({row["form_id"] for row in rows}) >= 8, slug
        assert len({row["duration"] for row in rows}) >= 8, slug
        assert len({row["keyscale"] for row in rows}) >= 4, slug
        forms = [str(row["form_id"]) for row in rows]
        assert all(forms[i] != forms[i + 1] for i in range(len(forms) - 1)), slug
    assert spoken_titles == SPOKEN_WORD_TITLES
    assert any(seed != 42 for seed in seeds)
    assert tuple(ex["title"] for ex in DISS_EXAMPLES) == EXPECTED_NILL_BYE_TITLES
    assert "Rake walks in with a club report" in DISS_EXAMPLES[0]["lyrics"]
    assert "Peer review time" in DISS_EXAMPLES[1]["lyrics"]
    assert "Rake in his feels like a full-time job" in DISS_EXAMPLES[2]["lyrics"]
    assert "Rake talk club like a uniform" in DISS_EXAMPLES[3]["lyrics"]
    assert "Hypothesis: Rake is cool" in DISS_EXAMPLES[4]["lyrics"]
    civic = [ex for ex in DISS_EXAMPLES if ex["series"] == "civic"]
    civic_club = [ex for ex in DISS_EXAMPLES if ex["series"] == "civic-club"]
    federal = [ex for ex in DISS_EXAMPLES if ex["series"] == "federal"]
    federal_club = [ex for ex in DISS_EXAMPLES if ex["series"] == "federal-club"]
    assert civic[0]["title"] == "frozen ercot"
    assert "Uri" in civic[0]["lyrics"]
    assert civic_club[0]["title"] == "lone star tab"
    assert (
        "Lone Star" in civic_club[0]["lyrics"]
        or "lone star" in civic_club[0]["lyrics"].lower()
    )
    assert federal[0]["title"] == "thirty four counts"
    assert (
        "thirty-four" in federal[0]["lyrics"].lower()
        or "thirty four" in federal[0]["lyrics"].lower()
    )
    assert federal_club[0]["title"] == "pardon flood"
    assert "pardon" in federal_club[0]["lyrics"].lower()
    progress = [ex for ex in DISS_EXAMPLES if ex["series"] == "progress"]
    progress_club = [ex for ex in DISS_EXAMPLES if ex["series"] == "progress-club"]
    assert progress[0]["title"] == "winterize wells"
    assert "NERC" in progress[0]["lyrics"] or "nerc" in progress[0]["lyrics"].lower()
    assert progress_club[0]["title"] == "duty switch"
    assert "switch" in progress_club[0]["lyrics"].lower()


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
    "rumble strip",
    "low lane",
    "warm merge",
    "colour span",
    "garage ticket",
    "liquid grade",
    "jump bay",
    "psy median",
    "groove mile",
    "donk ramp",
    "bounce booth",
    "toll growl",
    "night oil",
    "chest pass",
    "sunrise sub",
    "lantern merge",
    "firefly lane",
    "canopy bounce",
    "grove wreck",
    "moss sub",
    "fern stack",
    "pollen kick",
    "cedar growl",
    "moon ramp",
    "trail bounce",
    "dew wreck",
    "sap stack",
    "glade split",
    "root chest",
    "ember crest",
    "brake fade",
    "diesel hum",
    "axle grind",
    "weigh station",
    "black ice",
    "high beams",
    "chain hook",
    "grit plate",
    "steel grate",
    "rest bay",
    "haul crate",
    "night splice",
    "torque bay",
    "spare drum",
    "oil pan",
    "curb check",
    "last exit",
    "asphalt heart",
    "clutch slam",
    "trailer hitch",
    "hush lane",
    "cipher lock",
    "ghost dock",
    "sealed ramp",
    "fog vault",
    "dummy light",
    "quiet wreck",
    "off ledger",
    "back alley",
    "cellar kick",
    "hidden booth",
    "coded sub",
    "shadow coil",
    "mute pyro",
    "unlisted row",
    "night cipher",
    "blank stencil",
    "blind stamp",
    "cold cache",
    "secret homage",
    "lift tempo",
    "fit window",
    "plan album",
    "arrange score",
    "salt menu",
    "ban list",
    "cue bed",
    "pick role",
    "donor lane",
    "fit edits",
    "compose",
    "check form",
    "splice tags",
    "catalog row",
    "score format",
    "finalize album",
)
DRIVE_TREAT_TITLES = frozenset({"wide open", "second wave"})


def _valid_edm_sections() -> list[tuple[str, str]]:
    return [
        ("inst", "heavy warped drop\nstacked 808"),
        ("inst", "trap hats roll\n808 slide"),
        ("inst", "harder growl drop\nwreck hats"),
        ("outro", "kick holds\nhats roll"),
    ]


def _block_body(block: str) -> str:
    return "\n".join(line for line in block.splitlines() if not line.startswith("["))


def _block_cues(block: str) -> str:
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            inner = stripped[1:-1]
            if " - " in inner:
                return inner.split(" - ", 1)[1]
            return inner
    return _block_body(block)


def _score_labels(lyrics: str) -> tuple[str, ...]:
    labels: list[str] = []
    for line in lyrics.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            inner = stripped[1:-1]
            labels.append(inner.split(" - ", 1)[0].split(",", 1)[0].strip())
    return tuple(labels)


def _drive_shape(lyrics: str) -> tuple[tuple[str, int], ...]:
    """Role and bar count of every bracket except the DJ chop.

    Args:
        lyrics: Shipped ACE score.

    Returns:
        ``(role, bars)`` pairs. Also rejects a repeated musical cue.
    """
    found: list[tuple[str, int]] = []
    musics: list[str] = []
    for line in lyrics.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("[") and stripped.endswith("]")):
            continue
        inner = stripped[1:-1]
        role, _sep, body = inner.partition(" - ")
        role = role.strip()
        if role == "chorus":
            continue
        match = re.search(r"(\d+) bars$", body)
        assert match, stripped
        music = re.sub(r", \d+ bars$", "", body)
        found.append((role, int(match.group(1))))
        musics.append(music)
    assert len(musics) == len(set(musics))
    return tuple(found)


def _section_blocks(lyrics: str) -> list[str]:
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
    return blocks


def _drop_blocks(lyrics: str) -> list[str]:
    return [block for block in _section_blocks(lyrics) if "drop" in block.lower()]


def _hits_needles(text: str, needles: tuple[str, ...]) -> bool:
    low = text.lower()
    return any(needle in low for needle in needles)


def test_drive_tags_lock_instrumental_bed() -> None:
    tags = drive_tags(bpm=148)
    tags_low = tags.lower()
    lifted = lift_drive_bpm(148)
    for token in DRIVE_LOCK.split(", "):
        assert token in tags_low
    assert f"{lifted} bpm" in tags_low
    assert "148 bpm" not in tags_low
    assert "rave" in tags_low
    assert "warped hybrid-trap" in tags_low
    assert "bass boosted" in tags_low
    assert "no brass" in tags_low
    assert "no horns" in tags_low
    assert "wide low-mid" in tags_low


def test_drive_tags_lock_vocal_treat() -> None:
    tags = drive_tags(bpm=150, treat=True)
    tags_low = tags.lower()
    lifted = lift_drive_bpm(150)
    for token in DRIVE_TREAT_LOCK.split(", "):
        assert token.lower() in tags_low
    assert "no vocals" not in tags_low
    assert "no singing" not in tags_low
    assert f"{lifted} bpm" in tags_low
    assert "bass boosted" in tags_low
    assert "no brass" in tags_low
    assert "no trumpets" in tags_low


def test_format_edm_score_requires_weighted_drops() -> None:
    sections = _valid_edm_sections()
    sections[1] = ("inst", "named drop\nno weight")
    with pytest.raises(ValueError, match="weight needle"):
        format_edm_score(*sections)


def test_format_edm_score_requires_two_drops() -> None:
    sections = _valid_edm_sections()
    sections[2] = ("inst", "trap hats roll\n808 slide")
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


def test_edm_example_rejects_unknown_layout() -> None:
    with pytest.raises(ValueError, match="unknown layout"):
        _ex(
            "nope",
            "nope",
            150,
            2,
            0,
            "nope",
            format_edm_score(*_valid_edm_sections()),
            recipe="rec_drive_through_drop",
            layout="diagonal",
        )


def test_format_edm_score_rejects_short_score() -> None:
    with pytest.raises(ValueError, match="at least three sections"):
        format_edm_score(
            ("inst", "heavy drop\nstacked bass"),
            ("outro", "cut"),
        )


def test_format_edm_score_allows_chorus_treat() -> None:
    score = format_edm_score(
        ("inst", "heavy warped drop\nstacked kick"),
        ("chorus", "hey"),
        ("inst", "harder growl drop\nchest 808 wreck"),
        ("outro", "kick holds\nhats roll"),
    )
    assert "[chorus]" in score
    assert "[verse]" not in score
    assert score.count("drop") >= 2


def test_format_edm_score_requires_drop_first() -> None:
    sections = _valid_edm_sections()
    sections[0] = ("inst", "trap hats roll\n808 slide")
    with pytest.raises(ValueError, match="first section must be a drop"):
        format_edm_score(*sections)


def test_format_edm_score_requires_warp_on_drop() -> None:
    sections = _valid_edm_sections()
    sections[0] = ("inst", "heavy drop\nstacked 808")
    with pytest.raises(ValueError, match="warp needle"):
        format_edm_score(*sections)


def test_format_edm_score_rejects_forbidden_cues() -> None:
    sections = _valid_edm_sections()
    sections[1] = ("inst", "hats skip\nbass cut")
    with pytest.raises(ValueError, match="score forbids"):
        format_edm_score(*sections)


def test_format_edm_score_rejects_long_chorus() -> None:
    sections = _valid_edm_sections()
    sections.insert(1, ("chorus", "hands up now everybody"))
    with pytest.raises(ValueError, match="chorus chop is too long"):
        format_edm_score(*sections)


def test_uniquify_score_stamps_bed_keeps_chorus() -> None:
    score = format_edm_score(*_valid_edm_sections())
    stamped = _uniquify_score(193, score)
    assert "grid 193 0" in stamped
    treat = format_edm_score(
        ("inst", "heavy warped drop\nstacked kick"),
        ("chorus", "hey"),
        ("inst", "harder growl drop\nchest 808 wreck"),
        ("outro", "kick holds\nhats roll"),
    )
    stamped_treat = _uniquify_score(239, treat)
    assert "[chorus]\nhey" in stamped_treat
    assert "grid 239 1" not in stamped_treat.split("[chorus]")[1].split("[")[0]


def test_format_edm_score_rejects_multiline_chorus() -> None:
    sections = _valid_edm_sections()
    sections.insert(1, ("chorus", "hey\ngo"))
    with pytest.raises(ValueError, match="chorus must be one short chop"):
        format_edm_score(*sections)


def test_drive_through_edm_examples_are_varied_lengths() -> None:
    assert EDM_DURATION_S == 180.0
    assert len(EDM_EXAMPLES) == 101
    prefixes: list[str] = []
    stems: list[str] = []
    seeds: list[int] = []
    bpms: list[int] = []
    signatures: list[tuple[str, ...]] = []
    phase4_core = 0
    pedal_rows = 0
    breakdown_takes = 0
    treat_titles: list[str] = []
    shapes: list[tuple[tuple[str, int], ...]] = []
    for ex in EDM_EXAMPLES:
        assert 150.0 <= float(ex["duration"]) <= 480.0
        assert int(ex["bpm"]) in DRIVE_BPM_CHOICES
        assert ex["meter"] == "4"
        assert ex["form_id"]
        assert ex["keyscale"]
        assert "grid " not in ex["lyrics"]
        assert ex["series"] == "drive-through"
        lyrics = ex["lyrics"]
        tags_low = ex["tags"].lower()
        lyrics_low = lyrics.lower()
        assert "[outro" in lyrics
        assert "[drop" in lyrics
        assert "[verse]" not in lyrics
        assert "[spoken word]" not in lyrics
        assert "Drive-through" not in lyrics
        assert "techno" not in tags_low, ex["stem"]
        assert "techno" not in lyrics_low, ex["stem"]
        for needle in ("brass", "horn", "trumpet", "trombone", "saxophone", "fanfare", "stab"):
            assert needle not in lyrics_low, (ex["stem"], needle)
        assert "no brass" in tags_low
        assert "no horns" in tags_low
        assert "no trumpets" in tags_low
        for needle in FORBIDDEN_SCORE_NEEDLES:
            if needle == "mute":
                assert "mute" not in lyrics_low.replace("muted", ""), (ex["stem"], needle)
                continue
            assert needle not in lyrics_low, (ex["stem"], needle)
            if needle in ("drive-through", "drive through"):
                continue
            assert needle not in tags_low, (ex["stem"], needle)
        for needle in HIGH_PITCH_NEEDLES:
            assert needle not in tags_low, (ex["stem"], needle)
            assert needle not in lyrics_low, (ex["stem"], needle)
        for needle in BANNED_STYLE_NEEDLES:
            assert needle not in tags_low, (ex["stem"], needle)
            assert needle not in lyrics_low, (ex["stem"], needle)
        for needle in QUIET_NEEDLES:
            if needle == "mute":
                assert "mute" not in lyrics_low.replace("muted", ""), (ex["stem"], needle)
                continue
            assert needle not in lyrics_low, (ex["stem"], needle)
        for needle in BED_CUT_NEEDLES:
            assert needle not in lyrics_low, (ex["stem"], needle)
        assert _hits_needles(ex["tags"], BASS_NEEDLES), (ex["stem"], ex["tags"])
        assert _hits_needles(lyrics, BASS_NEEDLES), (ex["stem"], lyrics)
        assert _hits_needles(ex["tags"], SUB_WEIGHT_NEEDLES), (ex["stem"], ex["tags"])
        assert _hits_needles(lyrics, SUB_WEIGHT_NEEDLES), (ex["stem"], lyrics)
        assert _hits_needles(ex["tags"], HIPHOP_DRUM_NEEDLES), (ex["stem"], ex["tags"])
        assert _hits_needles(lyrics, HIPHOP_DRUM_NEEDLES), (ex["stem"], lyrics)
        if PEDAL_BASS_NEEDLE in tags_low or PEDAL_BASS_NEEDLE in lyrics_low:
            pedal_rows += 1
        assert ex["layout"] in EDM_LAYOUTS, ex["stem"]
        labels = _score_labels(lyrics)
        assert labels[0] == "build-up"
        assert labels[1] == "drop"
        assert labels[-1] == "outro"
        assert len(set(labels)) >= 2, (ex["stem"], labels)
        signatures.append(labels)
        shape = _drive_shape(lyrics)
        assert shape[0] == ("build-up", 2)
        assert shape[1][0] == "drop" and shape[1][1] == 2
        assert shape[-1] == ("outro", 2)
        bar_counts = [bars for _role, bars in shape]
        assert all(count == 2 for count in bar_counts), ex["stem"]
        assert all(count * 4 * 60 / int(ex["bpm"]) < 5 for count in bar_counts), ex["stem"]
        breakdowns = sum(role == "breakdown" for role, _bars in shape)
        assert breakdowns <= 1, ex["stem"]
        breakdown_takes += breakdowns
        assert sum(role == "drop" for role, _bars in shape) >= 3, ex["stem"]
        for line in lyrics.splitlines():
            stripped = line.strip()
            if not stripped.startswith("[") or stripped.startswith("[chorus"):
                continue
            low = stripped.lower()
            assert "bass boosted" in low, (ex["stem"], stripped)
            assert "layers stay" in low, (ex["stem"], stripped)
            assert "sub stays" in low, (ex["stem"], stripped)
            assert "no gap" in low, (ex["stem"], stripped)
            assert "one-shot phrase" in low, (ex["stem"], stripped)
            assert any(phrase.lower() in low for phrase in _SPATIAL), (
                ex["stem"],
                stripped,
            )
        assert int(ex["duration"]) == duration_seconds(
            bars=sum(bar_counts),
            meter="4",
            bpm=int(ex["bpm"]),
            clamp=False,
        )
        shapes.append(shape)
        sections = _section_blocks(lyrics)
        drops = _drop_blocks(lyrics)
        assert len(drops) >= 3, (ex["stem"], len(drops))
        for block in drops:
            low = block.lower()
            assert any(needle in low for needle in DROP_WEIGHT_NEEDLES), (
                ex["stem"],
                block,
            )
            assert _hits_needles(block, WARP_NEEDLES), (ex["stem"], block)
        for block in sections:
            if not block.startswith("[inst"):
                continue
            if "drop" in block.lower():
                continue
            assert _hits_needles(block, MOTION_NEEDLES), (ex["stem"], block)
            assert _hits_needles(block, BASS_NEEDLES), (ex["stem"], block)
            body = _block_cues(block)
            tokens = set(body.lower().replace("\n", " ").replace(",", " ").split())
            assert tokens, (ex["stem"], block)
            assert not tokens <= PAUSE_ONLY_TOKENS, (ex["stem"], block)
        if ex["phase"] < 2:
            assert ex["layout"] == "column", ex["stem"]
        elif ex["phase"] == 2:
            assert int(ex["bpm"]) >= 148, ex["stem"]
            assert _hits_needles(ex["tags"], HEADLINER_BOUNCE_NEEDLES), (
                ex["stem"],
                ex["tags"],
            )
            assert _hits_needles(lyrics, HEADLINER_BOUNCE_NEEDLES), (
                ex["stem"],
                lyrics,
            )
            for block in drops:
                assert _hits_needles(block, HEADLINER_BOUNCE_NEEDLES), (
                    ex["stem"],
                    block,
                )
        elif ex["phase"] == 3:
            assert int(ex["bpm"]) >= 150, ex["stem"]
            assert ex["ace_mode"] == "instrumental", ex["stem"]
        elif ex["phase"] == 4:
            assert int(ex["bpm"]) >= 140, ex["stem"]
            assert ex["ace_mode"] == "instrumental", ex["stem"]
            if _hits_needles(ex["tags"], SECRET_HOMAGE_NEEDLES):
                phase4_core += 1
        elif ex["phase"] == 5:
            assert ex["ace_mode"] == "instrumental", ex["stem"]
            assert ex["album_slug"] == "my-coder", ex["stem"]
        else:
            raise AssertionError(ex["phase"])
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
            for line in lyrics.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                assert stripped.startswith("[") and stripped.endswith("]"), (
                    ex["stem"],
                    line,
                )
            assert ex["ace_mode"] == "instrumental"
            for token in DRIVE_LOCK.split(", "):
                assert token in ex["tags"], (ex["stem"], token)
        assert "rave" in ex["tags"]
        assert str(ex["bpm"]) in ex["tags"]
        assert ex["stem"] == f"{ex['track']:02d}-{ex['slug']}"
        assert not ex["stem"].endswith("-lab-example")
        assert ex["artist"] == DRIVE_THROUGH_ARTIST
        assert ex["album"] == DRIVE_THROUGH_ALBUMS[ex["phase"]]["title"]
        assert ex["prefix"] == music_output_prefix(ex["title"], ex["track"])
        assert ex["rel"] == album_rel("drive-through", ex["album_slug"], ex["stem"])
        for needle in (*LIVING_MC_NEEDLES, *LIVING_EDM_NEEDLES):
            assert needle not in lyrics
            assert needle not in ex["tags"]
            assert needle not in ex["description"]
        prefixes.append(ex["prefix"])
        stems.append(ex["stem"])
        seeds.append(int(ex["seed"]))
        bpms.append(int(ex["bpm"]))
    assert len(set(prefixes)) == 101
    assert len(set(stems)) == 101
    assert len(set(seeds)) == 101
    assert [ex["phase"] for ex in EDM_EXAMPLES] == (
        [0] * 15 + [1] * 15 + [2] * 15 + [3] * 20 + [4] * 20 + [5] * 16
    )
    phase2 = [ex for ex in EDM_EXAMPLES if ex["phase"] == 2]
    assert len(phase2) == 15
    assert min(int(ex["bpm"]) for ex in phase2) >= 148
    assert sum(1 for ex in phase2 if int(ex["bpm"]) >= 165) >= 4
    assert {ex["layout"] for ex in phase2} == EDM_LAYOUTS
    phase3 = [ex for ex in EDM_EXAMPLES if ex["phase"] == 3]
    assert len(phase3) == 20
    assert min(int(ex["bpm"]) for ex in phase3) >= 150
    assert {ex["layout"] for ex in phase3} == EDM_LAYOUTS
    phase4 = [ex for ex in EDM_EXAMPLES if ex["phase"] == 4]
    assert len(phase4) == 20
    assert min(int(ex["bpm"]) for ex in phase4) >= 140
    assert {ex["layout"] for ex in phase4} == EDM_LAYOUTS
    assert phase4_core >= 8
    assert pedal_rows >= 8
    assert min(bpms) >= 140
    assert max(bpms) >= 170
    assert sum(1 for bpm in bpms if bpm >= 145) >= 12
    assert len(set(signatures)) == 101
    assert len(shapes) == 101
    assert len(set(shapes)) == 101
    assert 8 <= breakdown_takes <= len(EDM_EXAMPLES) // 5
    for left, right in zip(shapes, shapes[1:]):
        assert left != right
    assert len({ex["lyrics"] for ex in EDM_EXAMPLES}) == 101
    for phase in (0, 1, 2, 3, 4, 5):
        rows = [ex for ex in EDM_EXAMPLES if ex["phase"] == phase]
        assert len({ex["form_id"] for ex in rows}) >= 8, phase
        assert len({ex["duration"] for ex in rows}) >= 8, phase
        assert len({ex["keyscale"] for ex in rows}) >= 4, phase
        lengths = [float(ex["duration"]) for ex in rows]
        assert max(lengths) - min(lengths) >= 180, phase
        assert max(lengths) >= 300, phase
    assert frozenset(treat_titles) == DRIVE_TREAT_TITLES
    assert tuple(ex["title"] for ex in EDM_EXAMPLES) == EXPECTED_DRIVE_THROUGH_TITLES
    assert "warped" in EDM_EXAMPLES[0]["lyrics"].lower()
    assert "wobble" in EDM_EXAMPLES[1]["lyrics"].lower()
    assert (
        "trap drums" in EDM_EXAMPLES[2]["tags"]
        or "rapid hi-hats" in EDM_EXAMPLES[2]["tags"]
    )


def test_drive_through_tags_are_audio_rack_splices() -> None:
    from ez_prompt_enhance import audio

    audio.reset_audio_caches_for_tests()
    for ex in EDM_EXAMPLES:
        treat = ex["ace_mode"] == "vocal"
        flavor = audio.FLAVOR_ACE_VOCAL if treat else audio.FLAVOR_ACE_INSTRUMENTAL
        result = audio.splice(ex["picks"], flavor=flavor, recipe=ex["recipe"])
        assert result.tags == ex["tags"], ex["stem"]
        assert str(ex["bpm"]) in result.tags
        assert result.tags.lower().count("bpm") == 1
        for tid in ex["picks"].values():
            assert audio.technique(tid) is not None, (ex["stem"], tid)
        if treat:
            assert "voc_dj_shout" in result.used
            assert "no vocals" not in result.tags.lower()
        else:
            assert "instrumental" in result.tags.lower()
            assert "no vocals" in result.tags.lower()


def test_drive_through_score_cues_use_catalog_language() -> None:
    unofficial = (
        "trap hats",
        "chest sub",
        "bass growl",
        "amen chops",
        "amen keep",
    )
    official_needles = (
        "rapid hi-hats",
        "trap drums",
        "chest-sub",
        "growl bass",
        "amen break",
        "warped bass",
        "wobble bass",
        "reese bass",
        "formant bass",
        "dual-action pedal bass",
        "stacked 808",
        "body bass",
        "fold bass",
        "dirty bass",
        "wave bass",
        "color bass",
        "riddim",
        "tearout",
        "brostep",
        "drumstep",
        "neuro bass",
        "festival trap",
        "warped hybrid-trap",
        "dirty dubstep",
    )
    for ex in EDM_EXAMPLES:
        low = ex["lyrics"].lower()
        for phrase in unofficial:
            assert phrase not in low, (ex["stem"], phrase)
        assert any(needle in low for needle in official_needles), ex["stem"]


def test_writer_prompt_forbids_living_mcs() -> None:
    prompt = load_writer_prompt()
    blob = prompt.lower()
    assert "living" in blob
    assert "song title" in blob or "existing song" in blob
    assert "famous" in blob and "hook" in blob
    assert "in the style of" in blob


def test_lyrics_enhance_off_passthrough() -> None:
    types = EZRapLyrics.INPUT_TYPES()
    assert types["optional"]["context"][1]["forceInput"] is True
    with patch("ez_prompt_enhance.client.complete") as complete:
        out = EZRapLyrics().run(DRAFT_LYRICS, False, "album theme")
    complete.assert_not_called()
    assert out["result"][0] == DRAFT_LYRICS
    assert out["ui"]["passthrough"][0] == "enhance off"


def test_lyrics_enhance_on_sends_context() -> None:
    with (
        patch(
            "ez_prompt_enhance.client.complete",
            return_value=("[verse]\nrewritten", None),
        ) as complete,
        patch("ez_prompt_enhance.client._close_llm"),
    ):
        out = EZRapLyrics().run(DRAFT_LYRICS, True, "own the booth")
    assert "[verse]" in out["result"][0]
    user = complete.call_args[0][1]
    assert DRAFT_LYRICS.splitlines()[0] in user or "[intro]" in user
    assert "Context:" in user
    assert "own the booth" in user


def test_lyrics_missing_gguf_passthrough() -> None:
    with (
        patch("ez_prompt_enhance.client.complete", return_value=("", "GGUF missing")),
        patch("ez_prompt_enhance.client._close_llm"),
    ):
        out = EZRapLyrics().run(DRAFT_LYRICS, True)
    assert out["result"][0] == DRAFT_LYRICS
    assert "GGUF missing" in out["ui"]["passthrough"][0]


def test_ensure_lab_custom_nodes_path_inserts_parent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys,
        "path",
        [p for p in sys.path if Path(p).resolve() != CUSTOM.resolve()],
    )
    nodes._ensure_lab_custom_nodes_path()
    assert Path(sys.path[0]).resolve() == CUSTOM.resolve()


def test_shipped_albums_and_output_dir() -> None:
    albums = shipped_albums()
    assert len(albums) == 15
    assert albums[0]["title"] == "Peer Review"
    assert albums[0]["slug"] == "peer-review"
    assert albums[8]["title"] == "Duty Switch"
    assert albums[9]["title"] == "Hour 1"
    assert albums[-2]["title"] == "Secret Homage"
    assert albums[-1]["title"] == "My Coder"
    assert album_output_dir(NILL_BYE_ARTIST, "Peer Review") == (
        "albums/Nill Bye/Peer Review"
    )
    with pytest.raises(ValueError, match="artist"):
        album_output_dir("  ", "Peer Review")
    with pytest.raises(ValueError, match="album"):
        album_output_dir(NILL_BYE_ARTIST, "  ")
    assert "no living person" in albums[0]["cover_prompt"]
    assert nill_album_for_series("lab")["slug"] == "peer-review"
    with pytest.raises(KeyError):
        nill_album_for_series("missing")
    assert drive_album_for_phase(4)["slug"] == "secret-homage"
    assert drive_album_for_phase(5)["slug"] == "my-coder"
    assert drive_album_for_phase(5)["title"] == "My Coder"
    with pytest.raises(KeyError):
        drive_album_for_phase(99)


def test_metadata_nodes_expose_art_mode() -> None:
    spec = EZAudioMetadata.INPUT_TYPES()
    assert spec["required"]["art_mode"][0] == ["skip", "upload", "generate"]
    assert spec["required"]["artist"][0] == "STRING"
    assert "cover" in spec["optional"]
    pack = EZAlbumPack.INPUT_TYPES()
    assert pack["required"]["album"][0] == "STRING"
    assert NODE_CLASS_MAPPINGS["EZAudioMetadata"].CATEGORY == "ez-comfy/music"  # type: ignore[attr-defined]
    assert NODE_DISPLAY_NAME_MAPPINGS["EZAlbumPack"] == "Pack album zip"
