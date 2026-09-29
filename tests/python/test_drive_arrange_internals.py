"""Internals split out of the song-form compiler, plus arranger freeze proofs.

``drive_arrange.py`` is the My Coder lyric corpus: ``code_score._bounds``
stretches the twelve ``_ARRANGER`` groups over lines 1..EOF, so every token
of that file is a shipped take's cue words and the arranger stays
byte-identical until the 16 my-coder graphs are re-baked. The helpers here
therefore live in ``song_plan.py``, which no coder group reads, and the two
arranger cases the refactor brief asked for are pinned as evidence instead:
the survivor-index pair is shown to agree, and the drop-language rule is
shown not to be substitutable.
"""

from __future__ import annotations

from typing import Any

import pytest

from ez_music import drive_arrange as arrange
from ez_music import song_plan as plan
from ez_music.song_plan import (
    EDM_FORMS,
    VOCAL_FORMS,
    SongSection,
    _edm_marker_body,
    _edm_role_indices,
    _is_drop_cue,
    _min_bars_for,
    _album_spoken_flags,
    _emit_vocal_section,
    _place_drop_cues,
    _place_fill_cues,
    _render_blocks,
    _track_plan,
    _with_spoken_first,
    arrange_edm,
    arrange_vocal,
    assign_album_plans,
)

_SECTION_SOURCE = """[intro]
yeah
local signal

[verse]
line one
line two
line three

[chorus]
hook one
hook two
hook three

[spoken]
said plain

[outro]
walk it back
"""

_EDM_SOURCE = """[drop - heavy warped drop, chest-sub 808]

[inst - rapid hi-hats, pocket snare]
"""

_EDM_TREAT_SOURCE = """[chorus]
chop here

[drop - heavy warped drop, chest-sub 808]

[inst - rapid hi-hats, pocket snare]
"""


def _section(role: str, pattern: str = "", bars: int = 4) -> SongSection:
    """One planned section for a helper-level test.

    Args:
        role: ACE role.
        pattern: Pattern clause.
        bars: Bar count.

    Returns:
        The section dict.
    """
    return {"role": role, "bars": bars, "pattern": pattern}


def _vocal_plan(roles: list[str]) -> plan.SongPlan:
    """A vocal plan with the given roles in order.

    Args:
        roles: Section roles.

    Returns:
        A plan usable by ``arrange_vocal``.
    """
    return {
        "form_id": "v_break",
        "sections": [_section(role) for role in roles],
        "meter": "4",
        "keyscale": "A minor",
        "duration_s": 120,
        "bpm": 88,
        "bucket": "standard",
    }


def _edm_plan(roles: list[str], patterns: dict[str, str] | None = None) -> plan.SongPlan:
    """An EDM plan with the given roles in order.

    Args:
        roles: Section roles.
        patterns: Pattern clause per role.

    Returns:
        A plan usable by ``arrange_edm``.
    """
    clauses = patterns or {}
    return {
        "form_id": "e_build",
        "sections": [_section(role, clauses.get(role, "")) for role in roles],
        "meter": "4",
        "keyscale": "A minor",
        "duration_s": 120,
        "bpm": 168,
        "bucket": "standard",
    }


def test_album_spoken_flags_detect_from_lyrics_when_absent() -> None:
    """No caller flags means the spoken marker in the text decides."""
    assert _album_spoken_flags(["[spoken word]\nyo", "[verse]\nhey"], None) == [True, False]


def test_album_spoken_flags_copy_the_caller_list() -> None:
    """Caller flags win, and the caller's list is not the returned object."""
    given = [False]
    assert _album_spoken_flags(["[spoken word]\nyo"], given) == [False]
    assert _album_spoken_flags([], given) is not given
    given.append(True)
    assert _album_spoken_flags(["[verse]\nhey"], None) == [False]


def test_min_bars_uses_the_template_width_for_both_kinds() -> None:
    """Two bars per template section, for EDM forms and vocal forms alike."""
    assert _min_bars_for("e_tool", "edm", 0) == 2 * len(plan._EDM_TEMPLATES["e_tool"])
    assert _min_bars_for("v_once", "vocal", 2) >= 2
    assert _min_bars_for("v_once", "vocal", 4) > _min_bars_for("v_once", "vocal", 1)


def test_with_spoken_first_prepends_only_when_needed() -> None:
    """A spoken take without a spoken section opens on one; nothing else does."""
    fill = [_section("verse"), _section("chorus")]
    assert _with_spoken_first(fill, "vocal", False) == fill
    assert _with_spoken_first(fill, "edm", True) == fill
    assert _with_spoken_first([_section("spoken"), _section("verse")], "vocal", True) == [
        _section("spoken"),
        _section("verse"),
    ]
    moved = _with_spoken_first(fill, "vocal", True)
    assert moved[0] == {"role": "spoken", "bars": 4, "pattern": ""}
    assert moved[1:] == fill


def test_with_spoken_first_leaves_the_input_list_alone() -> None:
    """Prepending builds a new list; the dealt sections are untouched."""
    fill = [_section("verse")]
    _with_spoken_first(fill, "vocal", True)
    assert fill == [_section("verse")]


def test_track_plan_owns_meter_key_and_unique_duration() -> None:
    """One track's plan comes together from the shared seams."""
    used: set[int] = set()
    result = _track_plan(
        family="drive-through",
        album_slug="hour-1",
        index=0,
        bpm=168,
        tag="chest-sub, trap drums",
        lyric="[verse]\nline",
        form_id="e_tool",
        kind="edm",
        has_spoken=False,
        used=used,
    )
    assert result["form_id"] == "e_tool"
    assert result["meter"] == "4"
    assert result["bpm"] == 168
    assert result["bucket"] == plan.BUCKETS[0]
    assert result["keyscale"] in plan.KEYSCALES
    assert result["duration_s"] in used
    assert [section["role"] for section in result["sections"]] == [
        role for role, _pattern in plan._EDM_TEMPLATES["e_tool"]
    ]


def test_track_plan_prepends_spoken_for_a_vocal_take() -> None:
    """The spoken block rides in front of a vocal take that lost the marker."""
    used: set[int] = set()
    result = _track_plan(
        family="trap-edm",
        album_slug="peer-review",
        index=1,
        bpm=88,
        tag="boom bap",
        lyric="[verse]\nline one\nline two\nline three",
        form_id="v_once",
        kind="vocal",
        has_spoken=True,
        used=used,
    )
    assert result["sections"][0]["role"] == "spoken"
    assert result["duration_s"] in used


def test_assign_album_plans_matches_the_rolled_shape() -> None:
    """The split-out seams still agree with the plan contract."""
    plans = assign_album_plans(
        family="drive-through",
        album_slug="hour-1",
        bpms=[168, 172, 176],
        tags=["chest-sub"] * 3,
        lyrics=["[verse]\na\nb\nc"] * 3,
        kind="edm",
    )
    assert len(plans) == 3
    assert len({int(p["duration_s"]) for p in plans}) == 3
    for entry in plans:
        assert entry["form_id"] in EDM_FORMS
        assert entry["sections"]
        assert sum(int(s["bars"]) for s in entry["sections"]) >= 2 * len(entry["sections"])


def test_assign_album_plans_vocal_spoken_take_opens_spoken() -> None:
    """A spoken rap take keeps the spoken block even on another form."""
    plans = assign_album_plans(
        family="trap-edm",
        album_slug="peer-review",
        bpms=[88, 90, 92, 96],
        tags=["boom bap", "lo-fi", "folk", "brass"],
        lyrics=["[spoken word]\nsay it\n[verse]\na\nb\nc"] * 4,
        kind="vocal",
    )
    assert len(plans) == 4
    for entry in plans:
        assert entry["form_id"] in VOCAL_FORMS
    assert any(p["sections"][0]["role"] == "spoken" for p in plans)


def test_assign_album_plans_short_lists_are_tolerated() -> None:
    """Missing tag and lyric rows fall back to empty, not IndexError."""
    plans = assign_album_plans(
        family="trap-edm",
        album_slug="peer-review",
        bpms=[88, 90],
        tags=[],
        lyrics=[],
        spoken=[True],
        kind="vocal",
    )
    assert len(plans) == 2


def test_render_blocks_joins_or_empties() -> None:
    """A marker with no lines renders nothing at all."""
    assert _render_blocks("[verse]", ["a", "", "b"]) == "[verse]\na\nb"
    assert _render_blocks("[verse]", [" ", ""]) == ""


def test_emit_vocal_section_verse_pops_the_queue_in_order() -> None:
    """Verses are consumed front-first, and an empty queue skips the marker."""
    queue: list[list[str]] = [["one"], ["two"]]
    first = _emit_vocal_section(_section("verse", "hats"), queue, {}, {})
    assert first == "[verse - hats]\none"
    _emit_vocal_section(_section("verse"), queue, {}, {})
    assert queue == []
    assert _emit_vocal_section(_section("verse"), queue, {}, {}) == ""


def test_emit_vocal_section_line_roles_use_the_pool() -> None:
    """Chorus, pre and bridge come from the line pool and drop when empty."""
    pool = {"chorus": ["hook"], "pre": ["hook"], "bridge": []}
    assert _emit_vocal_section(_section("chorus", "x"), [], pool, {}) == "[chorus - x]\nhook"
    assert _emit_vocal_section(_section("pre", ""), [], pool, {}) == "[pre-chorus]\nhook"
    assert _emit_vocal_section(_section("bridge"), [], pool, {}) == ""


def test_emit_vocal_section_text_roles_keep_the_raw_body() -> None:
    """Intro, outro and spoken ship their stripped text, blanks included."""
    raw = {"intro": "yeah\n\nlocal", "outro": "", "spoken": "said plain"}
    assert _emit_vocal_section(_section("intro", "filter"), [], {}, raw) == (
        "[intro - filter]\nyeah\n\nlocal"
    )
    assert _emit_vocal_section(_section("outro"), [], {}, raw) == ""
    assert _emit_vocal_section(_section("spoken", "ignored"), [], {}, raw) == (
        "[spoken word]\nsaid plain"
    )


def test_emit_vocal_section_instrumentals_are_bare_markers() -> None:
    """Inst and breakdown take a planned pattern or the hats-only default."""
    assert _emit_vocal_section(_section("inst", "pocket snare"), [], {}, {}) == (
        "[inst - pocket snare]"
    )
    assert _emit_vocal_section(_section("breakdown"), [], {}, {}) == "[breakdown - hats only]"


def test_emit_vocal_section_rejects_a_role_it_does_not_emit() -> None:
    """An unknown role is a plan bug, not a silent skip."""
    with pytest.raises(ValueError, match="unknown section role"):
        _emit_vocal_section(_section("solo"), [], {}, {})


def test_arrange_vocal_ships_every_written_shape() -> None:
    """Every role the arranger knows renders, in plan order, once each."""
    out = arrange_vocal(
        _SECTION_SOURCE,
        _vocal_plan(
            ["spoken", "intro", "verse", "pre", "chorus", "bridge", "inst", "breakdown", "outro"]
        ),
    )
    heads = [line for line in out.splitlines() if line.startswith("[")]
    assert heads == [
        "[spoken word]",
        "[intro]",
        "[verse]",
        "[pre-chorus]",
        "[chorus]",
        "[bridge]",
        "[inst - pocket snare, hats only]",
        "[breakdown - hats only]",
        "[outro]",
    ]
    assert out.count("hook one") == 2
    assert "said plain" in out
    assert "yeah\nlocal signal" in out
    assert "walk it back" in out
    assert out.count("[verse]") == 1


def test_arrange_vocal_extra_verses_stay_separate_markers() -> None:
    """Verses the template did not ask for still ship, in order, unmerged."""
    source = "[verse]\nalpha one\nbeta two\n\n[verse]\ngamma three\ndelta four\n\n[verse]\nepsilon five\n"
    out = arrange_vocal(source, _vocal_plan(["verse"]))
    assert out.count("[verse]") == 3
    assert out.index("alpha one") < out.index("gamma three") < out.index("epsilon five")
    assert "\nbeta two\n" in out and "\ndelta four\n" in out


def test_arrange_vocal_needs_a_verse() -> None:
    """A source with no verse cannot be re-sectioned."""
    with pytest.raises(ValueError, match="needs a verse"):
        arrange_vocal("[chorus]\nhook", _vocal_plan(["verse"]))


def test_arrange_vocal_drops_roles_with_nothing_to_place() -> None:
    """A planned bridge or outro with no lines leaves no marker behind."""
    out = arrange_vocal("[verse]\nonly line", _vocal_plan(["verse", "bridge", "outro"]))
    assert out == "[verse]\nonly line"


def test_edm_role_indices_splits_the_lanes() -> None:
    """Drop positions and fill positions are disjoint and ascending."""
    sections = [_section(r) for r in ("build-up", "drop", "inst", "drop", "outro")]
    drops, others = _edm_role_indices(sections)
    assert drops == [1, 3]
    assert others == [0, 2, 4]
    assert set(drops).isdisjoint(others)
    assert _edm_role_indices([]) == ([], [])


def test_place_drop_cues_weights_every_drop() -> None:
    """Each drop gets its dealt cues plus the weight and warp it needs."""
    cues = ["heavy warped drop", "rapid hi-hats", "chest-sub 808"]
    placed = _place_drop_cues([0, 1], cues, ["heavy warped drop"], bounce=True)
    assert sorted(placed) == [0, 1]
    for frags in placed.values():
        blob = " ".join(frags).lower()
        assert any(needle in blob for needle in plan._WEIGHT)
        assert any(needle in blob for needle in plan._WARP)
        assert any(needle in blob for needle in plan._BOUNCE)


def test_place_drop_cues_on_a_take_with_no_drops() -> None:
    """No drop sections means no drop cues dealt."""
    assert _place_drop_cues([], ["heavy warped drop"], [], bounce=False) == {}


def test_place_fill_cues_deals_the_fill_lane_in_order() -> None:
    """Each fill takes its round-robin group of non-drop cues."""
    sections = [_section("build-up"), _section("outro")]
    placed = _place_fill_cues([0, 1], sections, ["chest-sub"], ["rapid hi-hats", "kick flips"])
    assert placed == {0: ["rapid hi-hats"], 1: ["kick flips"]}


def test_place_fill_cues_backfills_an_empty_fill() -> None:
    """A fill with nothing dealt gets the rhythm donor for its lane."""
    placed = _place_fill_cues([0], [_section("build-up")], ["chest-sub"], [])
    assert placed == {0: ["rapid hi-hats, chest-sub"]}
    with_donor = _place_fill_cues([0], [_section("breakdown")], ["chest-sub"], ["snare roll"])
    assert with_donor == {0: ["snare roll"]}


def test_place_fill_cues_gives_a_flat_inst_its_low_end() -> None:
    """An inst whose cues carry no bass borrows one from the whole score."""
    sections = [_section("inst")]
    placed = _place_fill_cues([0], sections, ["808 slide"], ["snare roll"])
    assert placed == {0: ["snare roll", "808 slide"]}


def test_place_fill_cues_keeps_a_grounding_inst_untouched() -> None:
    """An inst already carrying a bass cue is not padded again."""
    sections = [_section("inst")]
    placed = _place_fill_cues([0], sections, ["chest-sub"], ["808 slide"])
    assert placed == {0: ["808 slide"]}


def test_place_fill_cues_falls_back_to_the_default_bass_cue() -> None:
    """With no low-end donor anywhere, the canonical chest-sub ships."""
    placed = _place_fill_cues([0], [_section("inst")], ["snare roll"], ["snare roll"])
    assert placed == {0: ["snare roll", "chest-sub"]}


def test_place_fill_cues_on_a_take_with_no_fills() -> None:
    """All-drop takes deal nothing to the fill lane."""
    assert _place_fill_cues([], [], ["chest-sub"], []) == {}


def test_edm_marker_body_rules() -> None:
    """The pattern clause closes the cue list, and an empty body still names one."""
    assert _edm_marker_body(_section("drop", "warped wall"), ["chest-sub"]) == (
        "[drop - chest-sub, warped wall]"
    )
    assert _edm_marker_body(_section("drop", "warped wall"), ["warped wall x"]) == (
        "[drop - warped wall x]"
    )
    assert _edm_marker_body(_section("inst", ""), ["", "808"]) == "[inst - 808]"
    assert _edm_marker_body(_section("outro", ""), []) == "[outro - kick holds]"
    assert _edm_marker_body(_section("outro", "filter down"), []) == "[outro - filter down]"


def test_arrange_edm_ships_the_whole_arc() -> None:
    """Drops stay weighted, fills stay clean, and a treat adds one chop."""
    out = arrange_edm(
        _EDM_TREAT_SOURCE,
        _edm_plan(["build-up", "drop", "inst", "outro"], {"build-up": "snare roll"}),
        treat=True,
    )
    heads = [line for line in out.splitlines() if line.startswith("[")]
    assert heads[0].startswith("[build-up")
    assert heads[1] == "[chorus]"
    assert out.count("[chorus]") == 1
    assert "chop here" in out
    assert any(head.startswith("[drop") for head in heads)
    instrumental = next(head for head in heads if head.startswith("[inst"))
    assert "drop" not in instrumental.lower()


def test_arrange_edm_with_no_sections_and_a_treat() -> None:
    """An empty plan with no chop renders nothing; with a chop, just the chop."""
    assert arrange_edm(_EDM_SOURCE, _edm_plan([]), treat=True) == ""
    assert arrange_edm("[chorus]\nchop here", _edm_plan([]), treat=True) == (
        "[chorus]\nchop here"
    )


def test_survivor_index_helpers_agree_at_the_shared_budget() -> None:
    """The pass and take fits are one algorithm at one budget, bar the message.

    Both share ``DRIVE_PASS_CHAR_BUDGET`` (``DRIVE_LYRICS_CHAR_BUDGET`` is an
    alias) and differ only in the ``ValueError`` text, which is why they can
    be one function once the coder corpus is re-baked.
    """
    assert arrange.DRIVE_LYRICS_CHAR_BUDGET == arrange.DRIVE_PASS_CHAR_BUDGET
    short = ["[build-up - hats]", "[drop - heavy warped drop]", "[outro - kick holds]"]
    assert arrange._pass_survivor_indices(short) == list(range(len(short)))
    assert arrange._window_survivor_indices(short) == list(range(len(short)))
    blocks = ["[build-up - " + "a" * 400 + "]"]
    blocks += [f"[inst - fill {k} " + "b" * 300 + "]" for k in range(30)]
    blocks += ["[drop - heavy warped drop " + "d" * 300 + "]" for _ in range(9)]
    blocks += ["[outro - " + "z" * 120 + "]"]
    assert arrange._pass_survivor_indices(blocks) == arrange._window_survivor_indices(blocks)


def test_survivor_index_helpers_differ_only_in_the_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The two messages are the only observable difference between them."""
    blocks = ["[build-up - " + "a" * 400 + "]"]
    blocks += ["[drop - heavy wreck drop " + "d" * 300 + "]" for _ in range(arrange._DROP_FLOOR)]
    blocks += ["[outro - " + "z" * 120 + "]"]
    full = len("\n\n".join(blocks))
    monkeypatch.setattr(arrange, "DRIVE_PASS_CHAR_BUDGET", full - 1)
    monkeypatch.setattr(arrange, "DRIVE_LYRICS_CHAR_BUDGET", full - 1)
    with pytest.raises(ValueError, match="drive pass cannot fit"):
        arrange._pass_survivor_indices(blocks)
    with pytest.raises(ValueError, match="drive score cannot fit"):
        arrange._window_survivor_indices(blocks)


def test_drop_language_rule_is_not_the_drop_needle_rule() -> None:
    """``_is_drop_cue`` also names weight cues, so the arranger's copies differ.

    The re-implementations in ``drive_arrange._unique_cue`` and
    ``_take_donor`` test the ``drop`` needle alone; swapping in
    ``song_plan._is_drop_cue`` would reclassify a ``heavy`` / ``wreck`` /
    ``harder`` / ``stacked`` / ``full send`` fill and revoice 101 takes.
    """
    assert _is_drop_cue("Heavy chest-sub") is True
    assert "drop" in "heavy drop"
    assert "drop" not in "heavy chest-sub"
    for needle in ("heavy", "wreck", "harder", "stacked", "full send"):
        assert _is_drop_cue(f"{needle} 808") is True
        assert ("drop" in f"{needle} 808".lower()) is False
    assert _is_drop_cue("rapid hi-hats") is False
    assert _is_drop_cue("DROP returns") is True


def test_arranger_locks_still_resolve() -> None:
    """Names the brief froze stay importable, including the dead ones."""
    frozen: dict[str, Any] = {
        "_MENU": arrange._MENU,
        "_PASS_CELL_MENU": arrange._PASS_CELL_MENU,
        "_compose": arrange._compose,
        "_fit_lyrics_window": arrange._fit_lyrics_window,
        "_band_of": arrange._band_of,
        "_menu_count": arrange._menu_count,
        "_archetype_seconds": arrange._archetype_seconds,
        "_take_span": arrange._take_span,
        "_LAYERS": arrange._LAYERS,
        "_SPATIAL": arrange._SPATIAL,
    }
    assert all(name.startswith("_") for name in frozen)
    assert arrange._parse_edm is plan._parse_edm
    assert plan.bar_aligned_seconds(bars=64, meter="4", bpm=165) > 0
