"""Drive-through arranger: stanza fit, tempo snap, and score bans."""

from __future__ import annotations

import pytest

from ez_music import drive_arrange as arrange
from ez_music.drive_arrange import (
    DRIVE_BPM_CHOICES,
    RECIPE_LINES,
    arrange_drive,
    fit_drive_sections,
    lift_drive_bpm,
    plan_drive_album,
)
from ez_music.edm_examples import FORBIDDEN_SCORE_NEEDLES, HIGH_PITCH_NEEDLES
from ez_music.song_plan import SongPlan, SongSection, duration_seconds


def _section(role: str, bars: int, cue: str) -> SongSection:
    return {"role": role, "bars": bars, "pattern": f"{cue}, {bars} bars"}


def _opening() -> list[SongSection]:
    return [
        _section("build-up", 4, "snare roll, mono chest-sub, rapid hi-hats, build"),
        _section("drop", 8, "heavy warped drop, mono chest-sub, rapid hi-hats, first"),
        _section("outro", 4, "kick pattern flip, chest-sub, rapid hi-hats, end"),
    ]


def test_lift_drive_bpm_snaps_onto_catalog_tempos() -> None:
    assert lift_drive_bpm(140) == 165
    assert lift_drive_bpm(90) == 165
    assert lift_drive_bpm(176) == 176
    assert lift_drive_bpm(220) == 176
    values = [lift_drive_bpm(bpm) for bpm in range(140, 177)]
    assert values == sorted(values)
    assert set(values) <= set(DRIVE_BPM_CHOICES)


def test_recipe_lines_avoid_brass_and_high_pitch() -> None:
    needles = (*FORBIDDEN_SCORE_NEEDLES, *HIGH_PITCH_NEEDLES, "brass", "horn", "stab")
    for line in RECIPE_LINES.values():
        low = line.lower()
        for needle in needles:
            if needle == "mute":
                assert "mute" not in low.replace("muted", "")
                continue
            assert needle not in low, (line, needle)


def test_fit_adds_stanzas_without_resizing() -> None:
    opening = _opening()
    fitted = fit_drive_sections(opening, bpm=165, salt=3)
    assert fitted[0] is opening[0]
    assert fitted[1] is opening[1]
    assert fitted[-1] is opening[2]
    assert opening[0]["bars"] == 4
    assert opening[1]["bars"] == 8
    assert len(fitted) > 3
    seconds = duration_seconds(
        bars=sum(int(section["bars"]) for section in fitted),
        meter="4",
        bpm=165,
        clamp=False,
    )
    assert 150 <= seconds <= 480


def test_fit_drops_tail_stanzas_without_resizing() -> None:
    opening = _opening()
    body = [
        _section("inst", 12, f"rapid hi-hats, mono chest-sub, wide mids, lane {index}")
        for index in range(28)
    ]
    original = [opening[0], opening[1], *body, opening[2]]
    fitted = fit_drive_sections(original, bpm=165, salt=9)
    assert fitted[0] is original[0]
    assert fitted[1] is original[1]
    assert fitted[-1] is original[-1]
    assert len(fitted) < len(original)
    assert all(section in original for section in fitted)
    seconds = duration_seconds(
        bars=sum(int(section["bars"]) for section in fitted),
        meter="4",
        bpm=165,
        clamp=False,
    )
    assert seconds <= 480


def test_fit_refuses_a_duration_the_window_cannot_reach(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(arrange, "_seconds", lambda _sections, _bpm: 10)
    with pytest.raises(ValueError, match="outside"):
        fit_drive_sections(_opening(), bpm=165, salt=1)


def test_plan_collision_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    stub: SongPlan = {
        "form_id": "drv-stub",
        "sections": [_section("build-up", 4, "snare roll, mono chest-sub, rapid hi-hats")],
        "meter": "4",
        "keyscale": "A minor",
        "duration_s": 160,
        "bpm": 168,
        "bucket": "short",
    }
    monkeypatch.setattr(arrange, "_plan_one", lambda **_kwargs: stub)
    with pytest.raises(ValueError, match="collision"):
        plan_drive_album(
            "hour-1",
            [
                {"bpm": 168, "seed": 1, "lyrics": "[drop - heavy warped drop]", "recipe": ""},
                {"bpm": 168, "seed": 2, "lyrics": "[drop - heavy warped drop]", "recipe": ""},
            ],
        )


def test_arrange_drive_places_one_chop_after_the_first_drop() -> None:
    source = (
        "[drop - heavy warped drop, chest-sub]\n\n"
        "[chorus]\nhey\n\n"
        "[outro - kick pattern flip, chest-sub]"
    )
    plan = plan_drive_album(
        "hour-1",
        [
            {
                "bpm": 168,
                "seed": 11,
                "lyrics": source,
                "recipe": "rec_drive_riddim",
            }
        ],
    )[0]
    treated = arrange_drive(source, plan, treat=True)
    blocks = treated.split("\n\n")
    assert blocks[0].startswith("[build-up")
    assert blocks[1].startswith("[drop")
    assert blocks[2] == "[chorus]\nhey"
    assert treated.count("[chorus]") == 1
    plain = arrange_drive(source, plan, treat=False)
    assert "[chorus]" not in plain
    quiet = arrange_drive("[drop - heavy warped drop]", plan, treat=True)
    assert "[chorus]" not in quiet


def test_pick_helpers_and_cue_filters() -> None:
    assert arrange._pick_bars("build-up", 6, salt=1, index=3, before_outro=True) == 2
    saw_same = False
    saw_other = False
    for index in range(40):
        mixed = arrange._mix_int(1, index, 1)
        first = arrange._BODY_ROLES[mixed % len(arrange._BODY_ROLES)]
        chosen = arrange._pick_role(1, index, "drop")
        assert chosen != "drop"
        if first == "drop":
            saw_same = True
        else:
            saw_other = True
            assert chosen == first
    assert saw_same and saw_other
    assert arrange._music("fold bass, 8 bars") == "fold bass"
    assert arrange._music("plain cue") == "plain cue"
    assert arrange._blocked("brass fanfare")
    assert arrange._blocked("mute the bed")
    assert not arrange._blocked("muted low chest-sub")
    for role in ("drop", "build-up", "breakdown", "inst", "outro"):
        cue = arrange._cue_for(role, 2, 5, 0)
        assert not arrange._blocked(cue)
        assert "bass boosted" in cue
        assert "layers stay" in cue
        assert "sub stays" in cue
        assert "no gap" in cue
        assert "one-shot phrase" not in cue
        assert any(phrase in cue for phrase in arrange._SPATIAL)
        if role != "drop":
            assert "drop" not in cue


def test_unique_cue_skips_drop_words_on_a_fill(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def fake(_role: str, _n: int, _salt: int, _attempt: int) -> str:
        calls["n"] += 1
        if calls["n"] == 1:
            return "chest-sub drop"
        return "rapid hi-hats, mono chest-sub, wide low-mid"

    monkeypatch.setattr(arrange, "_cue_for", fake)
    assert arrange._unique_cue("inst", 0, 1, set()) == "rapid hi-hats, mono chest-sub, wide low-mid"


def test_unique_cue_exhausts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(arrange, "_cue_for", lambda *_args, **_kwargs: "pluck lead")
    with pytest.raises(ValueError, match="no unique cue"):
        arrange._unique_cue("inst", 0, 1, set())


def test_donor_queue_skips_bans_and_drop_words_on_fills() -> None:
    source = (
        "[drop - heavy warped drop, pluck, heavy warped drop, chest-sub]\n\n"
        "[inst - rapid hi-hats, 808 slide]"
    )
    queue = arrange._donor_queue(source)
    assert "pluck" not in queue
    assert queue.count("heavy warped drop") == 1
    assert arrange._take_donor(queue, "inst") != "heavy warped drop"
    assert arrange._take_donor([], "drop") == ""


def test_with_extras_keeps_rejects_and_appends() -> None:
    used = {"heavy warped drop, pluck"}
    kept = arrange._with_extras(
        "drop",
        "heavy warped drop",
        [],
        identity="pluck",
        pedal=False,
        used=used,
    )
    assert kept == "heavy warped drop"
    base = "heavy reese warped drop, mono chest-sub"
    merged = arrange._with_extras(
        "drop",
        base,
        ["low-mid bass"],
        identity="wobble bass",
        pedal=True,
        used=set(),
    )
    assert "wobble bass" in merged
    assert "dual-action pedal bass" in merged
    assert "low-mid bass" in merged
    again = arrange._with_extras(
        "drop",
        base,
        [],
        identity="",
        pedal=False,
        used={base + ", wobble bass"},
    )
    # No extras, so the base is returned rather than a duplicate merge.
    assert again == base
    duplicate = arrange._with_extras(
        "inst",
        "rapid hi-hats, mono chest-sub",
        [],
        identity="wobble bass",
        pedal=False,
        used={"rapid hi-hats, mono chest-sub, wobble bass"},
    )
    assert duplicate == "rapid hi-hats, mono chest-sub"


def test_drop_tail_removes_one_stanza() -> None:
    short = _opening()
    arrange._drop_tail(short)
    assert len(short) == 3
    long = [
        _section("build-up", 2, "snare roll, mono chest-sub, rapid hi-hats, a"),
        _section("drop", 2, "heavy warped drop, mono chest-sub, b"),
        _section("inst", 2, "rapid hi-hats, mono chest-sub, c"),
        _section("breakdown", 2, "rapid hi-hats, chest-sub pulse, d"),
        _section("outro", 2, "kick pattern flip, chest-sub, rapid hi-hats, e"),
    ]
    arrange._drop_tail(long)
    assert [section["role"] for section in long] == [
        "build-up",
        "drop",
        "inst",
        "outro",
    ]


def test_ensure_drops_promotes_one_fill_then_stops() -> None:
    sections = [
        _section("build-up", 2, "snare roll, mono chest-sub, rapid hi-hats, a"),
        _section("drop", 2, "heavy warped drop, mono chest-sub, b"),
        _section("inst", 2, "rapid hi-hats, mono chest-sub, wide mids, c"),
        _section("inst", 2, "offbeat hats, stacked 808, wide mids, d"),
        _section("outro", 2, "kick pattern flip, chest-sub, rapid hi-hats, e"),
    ]
    with pytest.raises(ValueError, match="third drop"):
        arrange._ensure_drops(sections, salt=4, used=set())
    assert sections[3]["role"] == "drop"
    assert sections[3]["bars"] == 2


def _two_bar_bed() -> list[SongSection]:
    return [
        _section("build-up", 2, "snare roll, mono chest-sub, rapid hi-hats, a"),
        _section("drop", 2, "heavy warped drop, mono chest-sub, b"),
        _section("inst", 2, "rapid hi-hats, mono chest-sub, wide mids, c"),
        _section("outro", 2, "kick pattern flip, chest-sub, rapid hi-hats, e"),
    ]


def test_rare_breakdown_is_one_two_bar_cell() -> None:
    sections = _two_bar_bed()
    skipped = _two_bar_bed()
    arrange._place_rare_breakdown(skipped, salt=1, used=set(), gate=1)
    assert [section["role"] for section in skipped] == [
        "build-up",
        "drop",
        "inst",
        "outro",
    ]
    empty = [
        _section("build-up", 2, "snare roll, a"),
        _section("drop", 2, "heavy warped drop, b"),
        _section("drop", 2, "harder warped drop, c"),
        _section("outro", 2, "kick pattern flip, d"),
    ]
    arrange._place_rare_breakdown(empty, salt=7, used=set(), gate=7)
    assert [section["role"] for section in empty].count("breakdown") == 0
    arrange._place_rare_breakdown(sections, salt=7, used=set(), gate=7)
    breakdowns = [section for section in sections if section["role"] == "breakdown"]
    assert len(breakdowns) == 1
    assert breakdowns[0]["bars"] == 2
    assert "bass boosted" in breakdowns[0]["pattern"]
    assert "no gap" in breakdowns[0]["pattern"]


def test_check_rejects_broken_shapes() -> None:
    def build(rows: list[tuple[str, int, str]]) -> list[SongSection]:
        return [_section(role, bars, cue) for role, bars, cue in rows]

    cases = [
        ([("inst", 2, "bed"), ("drop", 2, "heavy warped drop"), ("outro", 2, "end")], "opening build"),
        ([("build-up", 4, "snare roll"), ("drop", 2, "heavy warped drop"), ("outro", 2, "end")], "opening build"),
        ([("build-up", 2, "snare roll"), ("inst", 2, "rapid hi-hats"), ("outro", 2, "end")], "first drop"),
        ([("build-up", 2, "snare roll"), ("drop", 2, "heavy warped drop"), ("inst", 2, "end")], "outro must"),
        (
            [("build-up", 2, "snare roll"), ("drop", 2, "heavy warped drop"), ("outro", 4, "end")],
            "outro must",
        ),
        (
            [("build-up", 2, "snare roll"), ("drop", 4, "heavy warped drop"), ("outro", 2, "end")],
            "palette",
        ),
        (
            [
                ("build-up", 2, "snare roll, mono chest-sub"),
                ("drop", 2, "heavy warped drop"),
                ("inst", 2, "rapid hi-hats, body bass, one"),
                ("drop", 2, "harder warped drop, two"),
                ("inst", 2, "offbeat hats, fold bass, three"),
                ("outro", 2, "kick pattern flip, chest-sub"),
            ],
            "three drops",
        ),
        (
            [
                ("build-up", 2, "snare roll, mono chest-sub"),
                ("drop", 2, "heavy warped drop"),
                ("breakdown", 2, "rapid hi-hats, one"),
                ("drop", 2, "harder warped drop"),
                ("breakdown", 2, "offbeat hats, two"),
                ("drop", 2, "wreck warped drop"),
                ("outro", 2, "kick pattern flip, chest-sub"),
            ],
            "more than one breakdown",
        ),
    ]
    for rows, match in cases:
        with pytest.raises(ValueError, match=match):
            arrange._check(build(rows))
    repeated = build(
        [
            ("build-up", 2, "snare roll, mono chest-sub"),
            ("drop", 2, "same phrase"),
            ("inst", 2, "rapid hi-hats, body bass"),
            ("drop", 2, "same phrase"),
            ("inst", 2, "offbeat hats, fold bass"),
            ("drop", 2, "wreck warped drop, low chest-sub"),
            ("outro", 2, "kick pattern flip, chest-sub"),
        ]
    )
    with pytest.raises(ValueError, match="repeats"):
        arrange._check(repeated)
    banned = build(
        [
            ("build-up", 2, "pluck"),
            ("drop", 2, "heavy warped drop"),
            ("inst", 2, "rapid hi-hats, body bass"),
            ("drop", 2, "harder wobble warped drop"),
            ("inst", 2, "offbeat hats, fold bass"),
            ("drop", 2, "wreck warped drop, low chest-sub"),
            ("outro", 2, "kick pattern flip, chest-sub"),
        ]
    )
    with pytest.raises(ValueError, match="banned cue"):
        arrange._check(banned)
    spilled = build(
        [
            ("build-up", 2, "kick tightens, mono chest-sub"),
            ("drop", 2, "heavy warped drop"),
            ("inst", 2, "chest-sub drop"),
            ("drop", 2, "harder wobble warped drop"),
            ("inst", 2, "offbeat hats, fold bass"),
            ("drop", 2, "wreck warped drop, low chest-sub"),
            ("outro", 2, "kick pattern flip, chest-sub"),
        ]
    )
    with pytest.raises(ValueError, match="drop language"):
        arrange._check(spilled)
