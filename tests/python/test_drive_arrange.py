"""Drive-through arranger: two-bar cells, an early drop, 90-120 s.

The take's duration equals the rendered score's coverage - no unguided
tail. Beds rotate through the electric pool, stanzas stay thin early
and stack up late, and downbeat-only stanzas trade places with full
ones.
"""

from __future__ import annotations

import re
from typing import Any

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


def _rows(count: int) -> list[dict[str, Any]]:
    """Fixed plan inputs cycling every menu size and tempo."""
    seeds_bpms = (
        (11, 165),
        (12, 168),
        (13, 170),
        (14, 172),
        (15, 174),
        (16, 176),
        (17, 165),
        (18, 176),
        (19, 170),
        (20, 168),
        (21, 172),
        (22, 174),
        (23, 165),
        (24, 168),
        (25, 170),
    )
    return [
        {
            "bpm": bpm,
            "seed": seed,
            "lyrics": "drop - heavy warped drop, mono chest-sub, rapid hi-hats",
            "recipe": "rec_drive_through_drop",
        }
        for seed, bpm in seeds_bpms[:count]
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
    assert 90 <= seconds <= 120


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
    assert 90 <= seconds <= 120


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
    # The plan re-syncs its duration to the stanzas that ship.
    assert 90 <= plan["duration_s"] <= 120
    assert plan["bucket"] in ("short", "standard", "long")


def test_arrange_drive_fits_the_lyrics_window() -> None:
    rows: list[dict[str, Any]] = [
        {
            "bpm": bpm,
            "seed": seed,
            "lyrics": "drop - heavy warped drop, mono chest-sub, rapid hi-hats",
            "recipe": "rec_drive_through_drop",
        }
        for seed, bpm in (
            (11, 165),
            (12, 168),
            (13, 170),
            (14, 172),
            (15, 174),
            (16, 176),
            (17, 165),
            (18, 176),
        )
    ]
    plans = plan_drive_album("hour-1", rows)
    assert len(plans) == 8
    for plan in plans:
        score = arrange_drive(rows[0]["lyrics"], plan)
        assert len(score) <= arrange.DRIVE_LYRICS_CHAR_BUDGET, plan["form_id"]
        assert score.startswith("[build-up")
        assert score.endswith("2 bars]")
        assert "[outro" in score
        drops = sum(1 for line in score.splitlines() if line.startswith("[drop"))
        assert drops >= 5, plan["form_id"]


def test_fit_lyrics_window_trims_tail_keeps_structure() -> None:
    blocks = ["[build-up - kick tightens, mono chest-sub, rapid hi-hats, 2 bars]"]
    blocks.append("[drop - heavy warped drop, mono chest-sub, 2 bars]")
    for index in range(90):
        blocks.append(f"[inst - rapid hi-hats, body bass, low-mid bass melody, cell {index}, 2 bars]")
    for index in range(4):
        blocks.append(f"[drop - wreck wobble drop, low chest-sub, cell {index}, 2 bars]")
    blocks.append("[outro - kick pattern flip, chest-sub, rapid hi-hats, 2 bars]")
    out = arrange._fit_lyrics_window(list(blocks))
    kept = out.split("\n\n")
    assert len(out) <= arrange.DRIVE_LYRICS_CHAR_BUDGET
    assert kept[0] == blocks[0]
    assert kept[1] == blocks[1]
    assert kept[-1] == blocks[-1]
    assert sum(1 for block in kept if block.startswith("[drop")) == 5
    assert len(kept) < len(blocks)


def test_fit_lyrics_window_refuses_an_untrimmable_score() -> None:
    filler = "chest-sub, low-mid bass melody, trap drums denser, " * 40
    blocks = [
        f"[build-up - {filler}, 2 bars]",
        f"[inst - {filler}, 2 bars]",
        f"[drop - heavy reese warped drop, {filler}, 2 bars]",
        f"[drop - heavy wobble warped drop, {filler}, 2 bars]",
        f"[drop - heavy warped drop, {filler}, 2 bars]",
        f"[outro - {filler}, 2 bars]",
    ]
    with pytest.raises(ValueError, match="cannot fit"):
        arrange._fit_lyrics_window(blocks)
    assert len("\n\n".join(blocks)) > arrange.DRIVE_LYRICS_CHAR_BUDGET


def test_fit_sections_to_lyrics_mirrors_block_fit() -> None:
    sections = [
        SongSection(role="build-up", bars=2, pattern="chest-sub, 3D low-mid orbit, 2 bars"),
        SongSection(role="drop", bars=2, pattern="heavy reese warped drop, 2 bars"),
    ]
    sections.extend(
        SongSection(
            role="inst",
            bars=2,
            pattern=f"chest-sub, low-mid bass melody, trap drums denser, cell {index}, 2 bars",
        )
        for index in range(90)
    )
    sections.extend(
        [
            SongSection(role="drop", bars=2, pattern="wreck wobble warped drop, 2 bars"),
            SongSection(role="outro", bars=2, pattern="chest-sub, kick pattern flip, 2 bars"),
        ]
    )
    kept = arrange.fit_sections_to_lyrics(sections)
    blocks = [f"[{s['role']} - {s['pattern']}]" for s in sections]
    assert len(kept) < len(sections)
    assert len("\n\n".join(f"[{s['role']} - {s['pattern']}]" for s in kept)) <= arrange.DRIVE_LYRICS_CHAR_BUDGET
    assert kept[0] is sections[0]
    assert kept[1] is sections[1]
    assert kept[-1] is sections[-1]
    assert sum(1 for s in kept if s["role"] == "drop") == 2
    expected_roles = [
        blocks[i].strip()[1:].split(" - ")[0]
        for i in arrange._window_survivor_indices(blocks)
    ]
    assert [s["role"] for s in kept] == expected_roles


def test_pick_helpers_and_cue_filters() -> None:
    assert arrange._pick_bars("build-up", 6, salt=1, index=3, before_outro=True) == 2
    for index in range(200):
        assert arrange._pick_role(7, index, "inst") != "inst"
    drops_from_inst = sum(
        arrange._pick_role(7, index, "inst") == "drop" for index in range(200)
    )
    assert drops_from_inst >= 130
    drops_from_build = sum(
        arrange._pick_role(7, index, "build-up") == "drop" for index in range(200)
    )
    assert 60 <= drops_from_build <= 120
    assert arrange._music("fold bass, 8 bars") == "fold bass"
    assert arrange._music("plain cue") == "plain cue"
    assert arrange._blocked("brass fanfare")
    assert arrange._blocked("mute the bed")
    assert not arrange._blocked("muted low chest-sub")
    for role in ("drop", "build-up", "breakdown", "inst", "outro"):
        cue = arrange._cue_for(role, 2, 5, 0, depth=0.9)
        assert not arrange._blocked(cue)
        assert cue.split(", ")[0] in arrange._BEDS
        assert "bass boosted" not in cue
        assert "layers stay" not in cue
        assert "sub stays" not in cue
        assert "no gap" not in cue
        assert "one-shot phrase" not in cue
        assert any(phrase in cue for phrase in arrange._SPATIAL)
        assert any(phrase in cue for phrase in arrange._LAYERS)
        if role == "drop":
            weight_pattern = "|".join(arrange._WEIGHTS)
            warp_pattern = "|".join(arrange._WARPS)
            match = re.search(
                rf"\b({weight_pattern}) ({warp_pattern}) drop\b", cue
            )
            assert match, cue
        else:
            assert "drop" not in cue


def test_cue_for_depth_gates_slots() -> None:
    salt = 5
    early = arrange._cue_for("inst", 0, salt, 0, depth=0.1)
    assert len(early.split(", ")) == 4
    mid = arrange._cue_for("inst", 0, salt, 0)
    assert any(phrase in mid for phrase in arrange._SUBS)
    assert any(phrase in mid for phrase in arrange._MIDS)
    assert not any(phrase in mid for phrase in arrange._LAYERS)
    late = arrange._cue_for("inst", 0, salt, 0, depth=0.9)
    assert 7 <= len(late.split(", ")) <= 8
    assert any(phrase in late for phrase in arrange._LAYERS)
    # Drops render at full depth no matter what the caller passes.
    drop = arrange._cue_for("drop", 0, salt, 0, depth=0.1)
    assert len(drop.split(", ")) >= 8
    assert any(phrase in drop for phrase in arrange._LAYERS)


def test_cue_for_sparse_cue_shape() -> None:
    cue = arrange._cue_for("inst", 3, 5, 0, sparse=True)
    parts = cue.split(", ")
    assert len(parts) == 3
    assert parts[0] in arrange._BEDS
    assert parts[1] in arrange._SPATIAL
    assert parts[2] in arrange._SPARSE


def test_cue_for_lead_and_double_time_gates() -> None:
    salt = 5
    lead_n = next(n for n in range(40) if arrange._mix_int(salt, n, 5) % 5 < 3)
    plain_n = next(n for n in range(40) if arrange._mix_int(salt, n, 5) % 5 >= 3)
    lead_cue = arrange._cue_for("inst", lead_n, salt, 0, depth=0.9)
    assert arrange._slot(arrange._LEADS, lead_n, salt, 0, 7) in lead_cue
    plain_cue = arrange._cue_for("inst", plain_n, salt, 0, depth=0.9)
    assert not any(lead in plain_cue for lead in arrange._LEADS)
    # Leads never ride the outro.
    for n in (lead_n, plain_n):
        outro = arrange._cue_for("outro", n, salt, 0, depth=0.9)
        assert not any(lead in outro for lead in arrange._LEADS)
    fast_n = next(n for n in range(40) if arrange._mix_int(salt, n, 6) % 5 < 2)
    steady_n = next(n for n in range(40) if arrange._mix_int(salt, n, 6) % 5 >= 2)
    assert "double-time feel" in arrange._cue_for("drop", fast_n, salt, 0)
    assert "double-time feel" not in arrange._cue_for("drop", steady_n, salt, 0)


def test_cue_for_tempo_phrases_by_role() -> None:
    build = arrange._cue_for("build-up", 4, 5, 0, depth=0.9)
    assert any(phrase in build for phrase in arrange._TEMPO_PUSH)
    breakdown = arrange._cue_for("breakdown", 4, 5, 0, depth=0.9)
    assert "tempo dip" in breakdown
    for role in ("inst", "outro"):
        cue = arrange._cue_for(role, 4, 5, 0, depth=0.9)
        assert not any(phrase in cue for phrase in arrange._TEMPO_PUSH)
        assert "tempo dip" not in cue
        assert "double-time feel" not in cue


def test_unique_cue_skips_drop_words_on_a_fill(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def fake(_role: str, _n: int, _salt: int, _attempt: int, **_kw: Any) -> str:
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


def test_cue_with_donor_skips_extras_when_sparse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorded: dict[str, bool] = {}

    def fake_extras(
        _role: str,
        cue: str,
        _queue: list[str],
        *,
        identity: str,
        pedal: bool,
        used: set[str],
    ) -> str:
        recorded["called"] = True
        return cue

    monkeypatch.setattr(arrange, "_with_extras", fake_extras)
    cue = arrange._cue_with_donor("inst", 3, 5, set(), ["808 slide"], sparse=True)
    assert "called" not in recorded
    assert cue.split(", ")[2] in arrange._SPARSE
    plain = arrange._cue_with_donor("inst", 3, 5, set(), ["808 slide"])
    assert recorded["called"] is True
    assert plain != cue


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


def test_drop_target_scales_with_body() -> None:
    assert arrange._drop_target(0) == 5
    assert arrange._drop_target(9) == 5
    assert arrange._drop_target(28) == 10
    assert arrange._drop_target(43) == 15
    assert arrange._drop_target(90) == 30
    assert arrange._drop_target(160) == 30


def test_drop_cap_forces_role_switching(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(arrange, "_DROP_CAP", 0)

    def always_drop(_salt: int, _index: int, _prev: str) -> str:
        return "drop"

    monkeypatch.setattr(arrange, "_pick_role", always_drop)
    plan = plan_drive_album("hour-1", _rows(1))[0]
    sections = plan["sections"]
    # With the cap at zero every dealt drop flips to a fill, and the
    # drop floor is restored by promotions alone.
    drops = sum(section["role"] == "drop" for section in sections)
    assert drops >= arrange._DROP_FLOOR
    assert arrange._seconds(sections, int(plan["bpm"])) == plan["duration_s"]


def test_ensure_drops_promotes_fills_to_meet_floor_and_share() -> None:
    sections = [
        _section("build-up", 2, "snare roll, mono chest-sub, rapid hi-hats, a"),
        _section("drop", 2, "heavy warped drop, mono chest-sub, b"),
    ]
    sections.extend(
        _section(
            "inst", 2, f"rapid hi-hats, mono chest-sub, wide mids, cell {index}"
        )
        for index in range(12)
    )
    sections.append(
        _section("outro", 2, "kick pattern flip, chest-sub, rapid hi-hats, e")
    )
    arrange._ensure_drops(sections, salt=4, used=set())
    roles = [section["role"] for section in sections]
    drops = sum(role == "drop" for role in roles)
    body = len(roles) - 2
    assert drops >= 5
    assert drops >= arrange._drop_target(body)
    assert all(section["bars"] == 2 for section in sections)
    drop_run = 0
    max_drop_run = 0
    for role in roles:
        drop_run = drop_run + 1 if role == "drop" else 0
        max_drop_run = max(max_drop_run, drop_run)
    assert max_drop_run <= 2
    assert len({section["pattern"] for section in sections}) == len(sections)


def test_ensure_drops_refuses_without_legal_slots() -> None:
    sections = [
        _section("build-up", 2, "snare roll, mono chest-sub, a"),
        _section("drop", 2, "heavy warped drop, mono chest-sub, b"),
        _section("inst", 2, "rapid hi-hats, mono chest-sub, c"),
        _section("drop", 2, "harder wobble drop, mono chest-sub, d"),
        _section("inst", 2, "offbeat hats, mono chest-sub, e"),
        _section("drop", 2, "wreck reese drop, mono chest-sub, f"),
        _section("inst", 2, "ghost snare, mono chest-sub, g"),
        _section("drop", 2, "full send warped drop, mono chest-sub, h"),
        _section("outro", 2, "kick pattern flip, chest-sub, i"),
    ]
    with pytest.raises(ValueError, match="could not place a drive drop"):
        arrange._ensure_drops(sections, salt=1, used=set())


def test_ensure_sparse_noop_on_short_body() -> None:
    sections = [
        _section("build-up", 2, "bed one, 3D low-mid orbit"),
        _section("drop", 2, "heavy warped drop"),
    ]
    sections.extend(_section("inst", 2, f"fill {index}") for index in range(5))
    sections.append(_section("outro", 2, "end"))
    before = [section["pattern"] for section in sections]
    arrange._ensure_sparse(sections, salt=1, queue=[], used=set())
    assert [section["pattern"] for section in sections] == before


def test_ensure_sparse_keeps_existing_floor() -> None:
    sections = [
        _section("build-up", 2, "bed one, 3D low-mid orbit"),
        _section("drop", 2, "heavy warped drop"),
    ]
    sections.extend(_section("inst", 2, f"fill {index}") for index in range(18))
    sections.append(_section("outro", 2, "end"))
    for index in (3, 5, 7):
        sections[index] = _section(
            sections[index]["role"],
            2,
            arrange._cue_for("inst", index, 42, 0, sparse=True),
        )
    before = [section["pattern"] for section in sections]
    arrange._ensure_sparse(sections, salt=42, queue=[], used=set())
    assert [section["pattern"] for section in sections] == before


def test_ensure_sparse_backfills_to_three() -> None:
    sections = [
        _section("build-up", 2, "bed one, 3D low-mid orbit"),
        _section("drop", 2, "heavy warped drop"),
        _section("inst", 2, "fill a"),  # right-adjacent to sparse
        _section("inst", 2, arrange._cue_for("inst", 3, 7, 0, sparse=True)),
        _section("drop", 2, "harder wobble drop"),
        _section("inst", 2, arrange._cue_for("inst", 5, 7, 0, sparse=True)),
        _section("inst", 2, "fill b"),  # left-adjacent to sparse
    ]
    sections.extend(_section("inst", 2, f"fill {index}") for index in range(7, 22))
    sections.append(_section("outro", 2, "end"))
    assert sum(1 for section in sections if arrange._is_sparse(section)) == 2
    arrange._ensure_sparse(sections, salt=7, queue=[], used=set())
    assert sum(1 for section in sections if arrange._is_sparse(section)) == 3
    # The first eligible fill (index 7) converts; flanked and sparse ones stay.
    assert arrange._is_sparse(sections[7])
    assert not arrange._is_sparse(sections[2])
    assert not arrange._is_sparse(sections[6])
    assert sections[7]["role"] == "inst" and sections[7]["bars"] == 2
    flags = [arrange._is_sparse(section) for section in sections]
    assert not any(flag and prev for flag, prev in zip(flags, flags[1:]))
    patterns = [section["pattern"] for section in sections]
    assert len(set(patterns)) == len(patterns)


def test_ensure_sparse_refuses_when_no_legal_slot() -> None:
    sections = [
        _section("build-up", 2, "bed one, 3D low-mid orbit"),
        _section("drop", 2, "heavy warped drop"),
    ]
    sections.extend(_section("drop", 2, f"drop cell {index}") for index in range(8))
    sections.append(_section("inst", 2, arrange._cue_for("inst", 10, 9, 0, sparse=True)))
    sections.append(_section("inst", 2, "dense flanked left"))
    sections.append(_section("inst", 2, arrange._cue_for("inst", 12, 9, 0, sparse=True)))
    sections.append(_section("inst", 2, "dense flanked left"))
    sections.extend(_section("drop", 2, f"drop cell {index}") for index in range(8))
    sections.append(_section("outro", 2, "end"))
    assert sum(1 for section in sections if arrange._is_sparse(section)) == 2
    with pytest.raises(ValueError, match="no legal slot for a sparse stanza"):
        arrange._ensure_sparse(sections, salt=9, queue=[], used=set())


def _two_bar_bed() -> list[SongSection]:
    return [
        _section("build-up", 2, "snare roll, mono chest-sub, rapid hi-hats, a"),
        _section("drop", 2, "heavy warped drop, mono chest-sub, b"),
        _section("inst", 2, "rapid hi-hats, mono chest-sub, wide mids, c"),
        _section("outro", 2, "kick pattern flip, chest-sub, rapid hi-hats, e"),
    ]


def test_bucket_labels_map_duration_bands() -> None:
    assert arrange._bucket(90) == "short"
    assert arrange._bucket(99) == "short"
    assert arrange._bucket(100) == "standard"
    assert arrange._bucket(111) == "standard"
    assert arrange._bucket(112) == "long"
    assert arrange._bucket(120) == "long"


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
    assert breakdowns[0]["pattern"].split(", ")[0] in arrange._BEDS
    assert "no gap" not in breakdowns[0]["pattern"]


def test_music_keeps_unparseable_bar_suffix() -> None:
    # A trailing ", X bars" that is not a bar count stays verbatim.
    assert arrange._music("chest-sub, low bars") == "chest-sub, low bars"
    assert arrange._music("chest-sub, 2 barx") == "chest-sub, 2 barx"
    assert arrange._music("plain cue") == "plain cue"


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
            [
                ("build-up", 2, "snare roll"),
                ("drop", 2, "heavy warped drop"),
                ("inst", 3, "rapid hi-hats"),
                ("outro", 2, "end"),
            ],
            "palette",
        ),
        (
            [
                ("build-up", 2, "snare roll, mono chest-sub"),
                ("drop", 2, "heavy warped drop"),
                ("inst", 2, "rapid hi-hats, body bass, one"),
                ("drop", 2, "harder warped drop, two"),
                ("inst", 2, "offbeat hats, fold bass, three"),
                ("drop", 2, "wreck wobble drop, low chest-sub"),
                ("outro", 2, "kick pattern flip, chest-sub"),
            ],
            "at least five drops",
        ),
        (
            [
                ("build-up", 2, "snare roll, mono chest-sub"),
                ("drop", 2, "heavy warped drop"),
                ("inst", 2, "rapid hi-hats, body bass, one"),
                ("inst", 2, "offbeat hats, fold bass, two"),
                ("inst", 2, "ghost snare, body bass, three"),
                ("inst", 2, "triplet hats, fold bass, four"),
                ("inst", 2, "tight kick, body bass, five"),
                ("drop", 2, "harder warped drop, two"),
                ("inst", 2, "offbeat hats, fold bass, six"),
                ("inst", 2, "ghost snare, body bass, seven"),
                ("drop", 2, "stacked reese drop, mono chest-sub"),
                ("inst", 2, "triplet hats, fold bass, eight"),
                ("inst", 2, "tight kick, body bass, nine"),
                ("drop", 2, "wreck wobble drop, low chest-sub"),
                ("inst", 2, "offbeat hats, fold bass, ten"),
                ("inst", 2, "ghost snare, body bass, eleven"),
                ("drop", 2, "full send warped drop, chest-sub melody"),
                ("inst", 2, "triplet hats, fold bass, twelve"),
                ("inst", 2, "tight kick, body bass, thirteen"),
                ("outro", 2, "kick pattern flip, chest-sub"),
            ],
            "drop target below minimum",
        ),
        (
            [
                ("build-up", 2, "snare roll, mono chest-sub"),
                ("drop", 2, "heavy warped drop"),
                ("inst", 2, "rapid hi-hats, body bass, one"),
                ("inst", 2, "offbeat hats, fold bass, two"),
                ("inst", 2, "ghost snare, body bass, three"),
                ("drop", 2, "harder warped drop, four"),
                ("inst", 2, "triplet hats, fold bass, five"),
                ("inst", 2, "tight kick, body bass, six"),
                ("drop", 2, "stacked reese drop, mono chest-sub"),
                ("inst", 2, "offbeat hats, fold bass, seven"),
                ("inst", 2, "ghost snare, body bass, eight"),
                ("drop", 2, "wreck wobble drop, low chest-sub"),
                ("inst", 2, "triplet hats, fold bass, nine"),
                ("inst", 2, "tight kick, body bass, ten"),
                ("drop", 2, "full send warped drop, chest-sub melody"),
                ("outro", 2, "kick pattern flip, chest-sub"),
            ],
            "role run longer than two",
        ),
        (
            [
                ("build-up", 2, "snare roll, mono chest-sub"),
                ("drop", 2, "heavy warped drop"),
                ("inst", 2, "rapid hi-hats, body bass, one"),
                ("drop", 2, "harder warped drop, two"),
                ("breakdown", 2, "rapid hi-hats, three"),
                ("inst", 2, "offbeat hats, fold bass, four"),
                ("drop", 2, "stacked reese drop, mono chest-sub"),
                ("breakdown", 2, "offbeat hats, five"),
                ("inst", 2, "ghost snare, body bass, six"),
                ("drop", 2, "wreck wobble drop, low chest-sub"),
                ("drop", 2, "full send warped drop, chest-sub melody"),
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
            ("inst", 2, "ghost snare, body bass, one"),
            ("drop", 2, "stacked reese drop, mono chest-sub"),
            ("inst", 2, "triplet hats, fold bass, two"),
            ("drop", 2, "full send wobble drop, chest-sub melody"),
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
            ("inst", 2, "ghost snare, body bass, one"),
            ("drop", 2, "stacked reese drop, mono chest-sub"),
            ("inst", 2, "triplet hats, fold bass, two"),
            ("drop", 2, "full send wobble drop, chest-sub melody"),
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
            ("inst", 2, "ghost snare, body bass, one"),
            ("drop", 2, "stacked reese drop, mono chest-sub"),
            ("inst", 2, "triplet hats, fold bass, two"),
            ("drop", 2, "full send wobble drop, chest-sub melody"),
            ("outro", 2, "kick pattern flip, chest-sub"),
        ]
    )
    with pytest.raises(ValueError, match="drop language"):
        arrange._check(spilled)


def test_check_rejects_adjacent_and_missing_sparse() -> None:
    # 21 body stanzas: 9 drops, 12 fills, role runs at most two.
    base_rows: list[tuple[str, int, str]] = [
        ("build-up", 2, "snare roll, mono chest-sub"),
        ("drop", 2, "heavy warped drop"),
        ("inst", 2, "rapid hi-hats, body bass, one"),
        ("drop", 2, "harder wobble drop"),
        ("inst", 2, "offbeat hats, body bass, two"),
        ("drop", 2, "wreck reese drop"),
        ("inst", 2, "ghost snare, body bass, three"),
        ("drop", 2, "stacked warped drop"),
        ("inst", 2, "triplet hats, body bass, four"),
        ("drop", 2, "full send wobble drop"),
        ("inst", 2, "tight kick, body bass, five"),
        ("drop", 2, "heavy reese drop"),
        ("inst", 2, "offbeat hats, body bass, six"),
        ("inst", 2, "ghost snare, body bass, seven"),
        ("drop", 2, "harder reese drop"),
        ("inst", 2, "triplet hats, body bass, eight"),
        ("inst", 2, "tight kick, body bass, nine"),
        ("drop", 2, "wreck warped drop"),
        ("inst", 2, "offbeat hats, body bass, ten"),
        ("drop", 2, "stacked wobble drop"),
        ("inst", 2, "ghost snare, body bass, eleven"),
        ("inst", 2, "tight kick, body bass, twelve"),
        ("outro", 2, "kick pattern flip, chest-sub"),
    ]
    sections = [
        _section(role, bars, cue) for role, bars, cue in base_rows
    ]
    # No sparse stanzas at all, but the body has twenty stanzas.
    with pytest.raises(ValueError, match="at least three sparse"):
        arrange._check(sections)
    adjacent = [
        _section(role, bars, cue) for role, bars, cue in base_rows
    ]
    adjacent[12]["pattern"] = "chest-sub, 3D low-mid orbit, downbeat kick, 2 bars"
    adjacent[13]["pattern"] = (
        "FM warp sub, 3D low-mid orbit, kick only on downbeats, 2 bars"
    )
    with pytest.raises(ValueError, match="two adjacent"):
        arrange._check(adjacent)


def test_inserted_stanzas_are_dense() -> None:
    sections = [
        _section("build-up", 2, "snare roll, mono chest-sub, rapid hi-hats, a"),
        _section("drop", 2, "heavy warped drop, mono chest-sub, b"),
        _section("outro", 2, "kick pattern flip, chest-sub, rapid hi-hats, e"),
    ]
    arrange._insert(sections, salt=11, used=set())
    inserted = sections[-2]
    assert inserted["role"] in arrange._BODY_ROLES
    assert inserted["bars"] == 2
    cue = arrange._music(inserted["pattern"])
    assert any(phrase in cue for phrase in arrange._LAYERS), cue
    assert any(phrase in cue for phrase in arrange._SUBS), cue


def test_take_duration_matches_score_coverage() -> None:
    rows = _rows(10)
    for row, plan in zip(rows, plan_drive_album("hour-1", rows)):
        score = arrange_drive(row["lyrics"], plan)
        assert len(score) <= arrange.DRIVE_LYRICS_CHAR_BUDGET, plan["form_id"]
        bars: list[int] = []
        for line in score.splitlines():
            match = re.fullmatch(r"\[.* - .*, (\d+) bars\]", line.strip())
            if match:
                bars.append(int(match.group(1)))
        covered = duration_seconds(
            bars=sum(bars), meter="4", bpm=plan["bpm"], clamp=False
        )
        assert plan["duration_s"] == covered, plan["form_id"]
        assert 90 <= plan["duration_s"] <= 120, plan["form_id"]
        assert plan["bucket"] in ("short", "standard", "long")


def _catalog_rows() -> list[tuple[str, list[dict[str, Any]]]]:
    """Raw authored inputs for every Drive-through album, catalog order."""
    from ez_music.albums import drive_album_for_phase
    from ez_music.edm_drive_through import EDM_DRIVE_THROUGH
    from ez_music.edm_drive_through_afterparty import EDM_DRIVE_THROUGH_AFTERPARTY
    from ez_music.edm_drive_through_bass import EDM_DRIVE_THROUGH_BASS
    from ez_music.edm_drive_through_headliner import EDM_DRIVE_THROUGH_HEADLINER
    from ez_music.edm_drive_through_my_coder import EDM_DRIVE_THROUGH_MY_CODER
    from ez_music.edm_drive_through_secret_homage import (
        EDM_DRIVE_THROUGH_SECRET_HOMAGE,
    )

    groups = (
        EDM_DRIVE_THROUGH,
        EDM_DRIVE_THROUGH_BASS,
        EDM_DRIVE_THROUGH_HEADLINER,
        EDM_DRIVE_THROUGH_AFTERPARTY,
        EDM_DRIVE_THROUGH_SECRET_HOMAGE,
        EDM_DRIVE_THROUGH_MY_CODER,
    )
    out: list[tuple[str, list[dict[str, Any]]]] = []
    for phase, rows in enumerate(groups):
        out.append(
            (
                drive_album_for_phase(phase)["slug"],
                [
                    {
                        "bpm": example["bpm"],
                        "seed": example["seed"],
                        "lyrics": example["lyrics"],
                        "recipe": example["recipe"],
                    }
                    for example in rows
                ],
            )
        )
    return out


def test_beds_rotate_across_long_takes() -> None:
    for slug, rows in _catalog_rows():
        for plan in plan_drive_album(slug, rows):
            beds = [
                arrange._music(section["pattern"]).split(", ")[0]
                for section in plan["sections"]
            ]
            assert len(beds) >= 20, plan["form_id"]
            assert len(set(beds)) >= 3, plan["form_id"]
            top = max(beds.count(bed) for bed in set(beds))
            assert top / len(beds) <= 0.6, plan["form_id"]


def test_depth_ramp_and_cue_count_spread() -> None:
    for slug, rows in _catalog_rows():
        for plan in plan_drive_album(slug, rows):
            sections = plan["sections"]
            counts = [
                len(arrange._music(section["pattern"]).split(", "))
                for section in sections
            ]
            assert len(set(counts)) >= 3, plan["form_id"]
            # Drops always render at full depth and sparse stanzas are
            # intentionally thin, so the ramp is measured on dense fills.
            ramp = [
                count
                for count, section in zip(counts, sections)
                if section["role"] != "drop" and not arrange._is_sparse(section)
            ]
            third = len(ramp) // 3
            assert third >= 3, plan["form_id"]
            early = sum(ramp[:third]) / third
            late = sum(ramp[-third:]) / third
            assert late > early, plan["form_id"]


def test_sparse_stanzas_in_plans() -> None:
    for slug, rows in _catalog_rows():
        for plan in plan_drive_album(slug, rows):
            parts_list = [
                arrange._music(section["pattern"]).split(", ")
                for section in plan["sections"]
            ]
            sparse = [
                arrange._is_sparse(section)
                for section in plan["sections"]
            ]
            assert sum(sparse) >= 3, plan["form_id"]
            assert not any(a and b for a, b in zip(sparse, sparse[1:]))
            for parts, is_sparse in zip(parts_list, sparse):
                if not is_sparse:
                    continue
                assert parts[0] in arrange._BEDS
                assert parts[-1] in arrange._SPARSE
                assert ", ".join(parts[1:-1]) in arrange._SPATIAL


def test_tempo_phrases_follow_roles_in_plans() -> None:
    for slug, rows in _catalog_rows():
        for plan in plan_drive_album(slug, rows):
            for section in plan["sections"]:
                sparse = arrange._is_sparse(section)
                cue = section["pattern"].lower()
                if section["role"] == "build-up" and not sparse:
                    assert any(phrase in cue for phrase in arrange._TEMPO_PUSH)
                elif section["role"] == "breakdown" and not sparse:
                    assert "tempo dip" in cue
                elif section["role"] in ("inst", "outro"):
                    assert not any(phrase in cue for phrase in arrange._TEMPO_PUSH)
                    assert "tempo dip" not in cue


def test_pools_are_needle_safe() -> None:
    pools = (
        arrange._BEDS,
        arrange._SUBS,
        arrange._MIDS,
        arrange._LEADS,
        arrange._SPATIAL,
        arrange._LAYERS,
        arrange._SPARSE,
        arrange._TEMPO_PUSH,
    )
    for pool in pools:
        for phrase in pool:
            assert not arrange._blocked(phrase), phrase


def test_plans_and_scores_are_deterministic() -> None:
    rows = _rows(6)
    first = plan_drive_album("hour-9", rows)
    scores_first = [
        arrange_drive(rows[i]["lyrics"], plan, treat=i % 2 == 0)
        for i, plan in enumerate(first)
    ]
    second = plan_drive_album("hour-9", rows)
    scores_second = [
        arrange_drive(rows[i]["lyrics"], plan, treat=i % 2 == 0)
        for i, plan in enumerate(second)
    ]
    assert [plan["form_id"] for plan in first] == [
        plan["form_id"] for plan in second
    ]
    assert [plan["sections"] for plan in first] == [
        plan["sections"] for plan in second
    ]
    assert scores_first == scores_second
