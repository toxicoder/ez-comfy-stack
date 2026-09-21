"""Song-plan compiler: bar math, vocal re-section, EDM arcs, album spread."""

from __future__ import annotations

import re
from typing import cast

import pytest

from ez_music.song_plan import (
    DURATION_MAX,
    DURATION_MIN,
    EDM_FORMS,
    MOTIFS,
    VOCAL_FORMS,
    SongPlan,
    _bars_for_target,
    _chunks,
    _expand_vocal_roles,
    _fallback_form,
    _marker,
    _split_bridge,
    _split_counts,
    _unique_duration,
    arrange_edm,
    arrange_vocal,
    assign_album_plans,
    beats_per_bar,
    demo_draft_lyrics,
    demo_draft_seconds,
    demo_full_lyrics,
    demo_full_seconds,
    duration_seconds,
    keyscale_for,
    meter_for,
    rack_form_entries,
    validate_keyscale,
)

def _as_plan(plan: SongPlan, **overrides: object) -> SongPlan:
    merged: dict[str, object] = dict(plan)
    merged.update(overrides)
    return cast(SongPlan, merged)


_ACE_MARKERS = (
    "intro",
    "verse",
    "pre-chorus",
    "chorus",
    "bridge",
    "inst",
    "breakdown",
    "build-up",
    "drop",
    "outro",
    "spoken word",
)


def _vocal_source() -> str:
    return (
        "[intro]\nhello booth\n\n"
        "[verse]\nalpha one\nalpha two\n\n"
        "[chorus]\nhook one\nhook two\nhook three\n\n"
        "[verse]\nbeta one\nbeta two\nbeta three\n\n"
        "[chorus]\nhook one\nhook two\nhook three\n\n"
        "[verse]\ngamma one\ngamma two\ngamma three\n\n"
        "[chorus]\nhook one\nhook two\nhook three\n\n"
        "[outro]\ncut the mic"
    )


def _roles(lyrics: str) -> list[str]:
    found: list[str] = []
    for line in lyrics.splitlines():
        matched = re.match(r"^\[([^\]]+)\]", line.strip())
        if matched:
            found.append(matched.group(1).split(" - ", 1)[0].strip())
    return found


def _bodies(lyrics: str, role: str) -> list[str]:
    parts = re.split(r"\n\s*\n", lyrics.strip())
    out: list[str] = []
    for part in parts:
        lines = [line for line in part.splitlines() if line.strip()]
        if not lines:
            continue
        head = lines[0]
        if not head.startswith("["):
            continue
        label = head[1:-1].split(" - ", 1)[0].strip() if head.endswith("]") else ""
        if label == role:
            out.append("\n".join(lines[1:]))
    return out


def test_bar_math_and_clamp() -> None:
    assert beats_per_bar("4") == 4
    assert duration_seconds(bars=8, meter="4", bpm=88, clamp=False) == 22
    assert duration_seconds(bars=1, meter="4", bpm=200, clamp=True) == DURATION_MIN
    assert duration_seconds(bars=400, meter="4", bpm=60, clamp=True) == DURATION_MAX
    with pytest.raises(ValueError, match="unknown meter"):
        beats_per_bar("5")
    with pytest.raises(ValueError, match="bpm"):
        duration_seconds(bars=8, meter="4", bpm=0)
    with pytest.raises(ValueError, match="keyscale"):
        validate_keyscale("H minor")
    assert validate_keyscale("C minor") == "C minor"


def test_meter_follows_the_bed() -> None:
    assert meter_for("festival trap", 3, "trap-edm") == "4"
    assert meter_for("folk ballad", 1, "variety") == "4"
    assert meter_for("folk ballad", 3, "variety") == "6"
    assert meter_for("folk ballad", 6, "variety") == "3"
    assert meter_for("brass band", 2, "variety") == "4"
    assert meter_for("brass band", 4, "variety") == "2"
    assert meter_for("industrial hip-hop", 4, "civic") == "2"
    assert meter_for("boom bap", 2, "lab") == "4"
    assert meter_for("boom-bap", 5, "lab") == "6"
    assert meter_for("jazz hop", 5, "variety") == "6"
    assert meter_for("lo-fi hip-hop", 1, "lab") == "4"
    assert meter_for("synthwave pads", 4, "variety") == "4"


def test_keys_cycle_by_family() -> None:
    assert keyscale_for("drive-through", "", 1) == "A minor"
    assert keyscale_for("drive-through", "", 3) == "E minor"
    assert keyscale_for("progress", "", 1) == "C major"
    assert keyscale_for("progress-club", "", 2) == "G major"
    assert keyscale_for("lab", "", 1) == "A minor"
    assert validate_keyscale(keyscale_for("civic", "frozen-ercot", 4))


def test_split_helpers() -> None:
    assert _split_counts(3, 2) == [2, 1]
    assert _split_counts(3, 0) == []
    assert _split_bridge(["only"]) == (["only"], [])
    assert _split_bridge(["keep", "move"]) == (["keep"], ["move"])
    assert _split_bridge(["a", "b", "c", "d"]) == (["a", "b"], ["c", "d"])
    assert _chunks(["a"], 0) == []
    assert _chunks(["a", "b", "c"], 2) == [["a", "c"], ["b"]]
    with pytest.raises(ValueError, match="no sections"):
        from ez_music.song_plan import _apportion

        _apportion(8, 0)
    assert _fallback_form(("v_spoken",), "") == "v_spoken"
    with pytest.raises(ValueError, match="unknown section"):
        _marker("solo", "")
    assert _marker("verse", "") == "[verse]"
    assert _marker("drop", "warped wall") == "[drop - warped wall]"
    bars, dur = _bars_for_target(176, "4", 90, 2)
    assert DURATION_MIN <= dur <= DURATION_MAX
    assert bars >= 2
    exact_bars, exact = _bars_for_target(120, "4", 96, 4)
    assert exact == 96
    assert exact_bars > 0
    forced, _forced_dur = _unique_duration(120, "4", 96, 4, set(range(DURATION_MIN, DURATION_MAX + 1)))
    assert forced >= 4


def test_vocal_bridge_keeps_verse_order_and_moves_the_tail() -> None:
    plans = assign_album_plans(
        family="lab",
        album_slug="",
        bpms=[88, 88, 92],
        tags=["boom bap", "folk ballad", "brass band"],
        lyrics=[_vocal_source(), _vocal_source(), "[spoken word]\nyo\n\n" + _vocal_source()],
        kind="vocal",
    )
    explicit = _as_plan(
        plans[0],
        form_id="v_bridge",
        sections=[
            {"role": role, "bars": 4, "pattern": pattern}
            for role, pattern in _expand_vocal_roles("v_bridge", 3, half_time=False)
        ],
    )
    lyrics = arrange_vocal(_vocal_source(), explicit)
    verse_text = "\n".join(_bodies(lyrics, "verse"))
    bridge_text = "\n".join(_bodies(lyrics, "bridge"))
    assert "alpha one" in verse_text
    assert verse_text.index("alpha one") < verse_text.index("beta one")
    assert verse_text.index("beta one") < verse_text.index("gamma one")
    assert "gamma two" in bridge_text
    assert "gamma three" in bridge_text
    assert "gamma two" not in verse_text
    assert "hook one\nhook two\nhook three" in lyrics
    assert lyrics.count("[chorus]") >= 1


def test_vocal_short_form_does_not_drop_lines() -> None:
    plan: SongPlan = {
        "form_id": "v_short",
        "sections": [
            {"role": role, "bars": 4, "pattern": pattern}
            for role, pattern in _expand_vocal_roles("v_short", 3, half_time=False)
        ],
        "meter": "4",
        "keyscale": "C minor",
        "duration_s": 80,
        "bpm": 88,
        "bucket": "short",
    }
    lyrics = arrange_vocal(_vocal_source(), plan)
    blob = "\n".join(_bodies(lyrics, "verse"))
    assert "alpha one" in blob and "beta one" in blob and "gamma one" in blob
    assert "[pre-chorus]" in lyrics
    assert _roles(lyrics).count("chorus") == 1


def test_vocal_half_time_second_chorus_and_leftover_verse() -> None:
    roles = _expand_vocal_roles("v_half", 2, half_time=True)
    chorus_patterns = [pattern for role, pattern in roles if role == "chorus"]
    assert chorus_patterns[-1] == "half-time drums"
    plan: SongPlan = {
        "form_id": "v_half",
        "sections": [{"role": "verse", "bars": 4, "pattern": ""}],
        "meter": "4",
        "keyscale": "A minor",
        "duration_s": 80,
        "bpm": 88,
        "bucket": "short",
    }
    lyrics = arrange_vocal(_vocal_source(), plan)
    assert lyrics.count("[verse]") == 3
    with pytest.raises(ValueError, match="needs a verse"):
        arrange_vocal("[intro]\nonly\n", plan)
    with pytest.raises(ValueError, match="unknown section"):
        arrange_vocal(
            _vocal_source(),
            _as_plan(plan, sections=[{"role": "solo", "bars": 4, "pattern": ""}]),
        )
    with pytest.raises(ValueError, match="unknown vocal form"):
        _expand_vocal_roles("v_nope", 2, half_time=False)


def test_vocal_skips_empty_optional_sections() -> None:
    bare = "[verse]\none line only\n\n[chorus]\nhook"
    plan: SongPlan = {
        "form_id": "v_bridge",
        "sections": [
            {"role": "intro", "bars": 4, "pattern": ""},
            {"role": "verse", "bars": 4, "pattern": ""},
            {"role": "pre", "bars": 4, "pattern": ""},
            {"role": "bridge", "bars": 4, "pattern": ""},
            {"role": "spoken", "bars": 4, "pattern": ""},
            {"role": "outro", "bars": 4, "pattern": ""},
            {"role": "inst", "bars": 4, "pattern": ""},
            {"role": "chorus", "bars": 4, "pattern": ""},
        ],
        "meter": "4",
        "keyscale": "C minor",
        "duration_s": 90,
        "bpm": 88,
        "bucket": "short",
    }
    lyrics = arrange_vocal(bare, plan)
    assert "[intro]" not in lyrics
    assert "[spoken word]" not in lyrics
    assert "[outro]" not in lyrics
    assert "[bridge]" not in lyrics
    assert "[inst - pocket snare, hats only]" in lyrics
    assert "[pre-chorus]\nhook" in lyrics
    empty_hook = _as_plan(
        plan,
        sections=[
            {"role": "verse", "bars": 4, "pattern": ""},
            {"role": "verse", "bars": 4, "pattern": ""},
            {"role": "chorus", "bars": 4, "pattern": ""},
            {"role": "pre", "bars": 4, "pattern": ""},
            {"role": "spoken", "bars": 4, "pattern": ""},
        ],
    )
    no_hook = arrange_vocal("[verse]\nonly line\n\n[spoken word]\nyo there", empty_hook)
    assert no_hook.count("[verse]") == 1
    assert "[chorus]" not in no_hook
    assert "[pre-chorus]" not in no_hook
    assert "[spoken word]\nyo there" in no_hook


def test_edm_arc_is_not_always_drop_first() -> None:
    source = (
        "[drop - heavy warped drop, chest-sub 808]\n\n"
        "[inst - rapid hi-hats, 808 slide]\n\n"
        "[drop - harder growl drop, stacked wreck]\n\n"
        "[outro - kick holds, rapid hi-hats]"
    )
    plans = assign_album_plans(
        family="drive-through",
        album_slug="hour-1",
        bpms=[150] * 15,
        tags=["warped hybrid-trap, 150 bpm"] * 15,
        lyrics=[source] * 15,
        kind="edm",
    )
    assert len({plan["form_id"] for plan in plans}) >= 8
    assert len({plan["duration_s"] for plan in plans}) >= 8
    assert len({plan["keyscale"] for plan in plans}) >= 4
    for plan in plans:
        assert DURATION_MIN <= plan["duration_s"] <= DURATION_MAX
        assert plan["meter"] == "4"
    for left, right in zip(plans, plans[1:]):
        assert left["form_id"] != right["form_id"]
    built = arrange_edm(source, plans[1], treat=False)
    assert "[verse]" not in built
    assert "grid " not in built
    assert built.strip().endswith("]")
    labels = _roles(built)
    assert labels[-1] == "outro"
    assert "drop" in labels
    drop_first = next(plan for plan in plans if plan["form_id"] == "e_drop_first")
    assert _roles(arrange_edm(source, drop_first))[0] == "drop"
    assert any(_roles(arrange_edm(source, plan))[0] != "drop" for plan in plans)


def test_edm_treat_breakdown_and_fallbacks() -> None:
    source = "[inst - rapid hi-hats]\n\n[chorus]\nhey"
    plan = assign_album_plans(
        family="drive-through",
        album_slug="treats",
        bpms=[150],
        tags=["color bass"],
        lyrics=[source],
        kind="edm",
    )[0]
    from ez_music.song_plan import _EDM_TEMPLATES

    plan = _as_plan(
        plan,
        form_id="e_build",
        sections=[
            {
                "role": role,
                "bars": 8,
                "pattern": "muted stab" if pattern == "motif" else pattern,
            }
            for role, pattern in _EDM_TEMPLATES["e_build"]
        ],
    )
    treated = arrange_edm(source, plan, treat=True, bounce=True)
    assert treated.count("[chorus]") == 1
    assert "\nhey" in treated
    assert "[verse]" not in treated
    assert "heavy" in treated
    assert "warped" in treated or "warp" in treated
    quiet = arrange_edm("[drop - heavy growl drop]", plan, treat=False, bounce=True)
    assert "chest-sub 808" in quiet or "808" in quiet
    assert "filter down" in quiet or "muted stab" in quiet
    no_chop = arrange_edm("[inst - kick holds]", plan, treat=True)
    assert "[chorus]" not in no_chop
    assert arrange_edm("   ", plan).startswith("[")
    messy = arrange_edm(
        "just words\n\n\n\n[chorus]\n\n[outro - kick holds, grid 1 0]",
        plan,
        treat=False,
    )
    assert "[outro -" in messy
    assert "grid" not in messy


def test_album_spread_and_determinism() -> None:
    bpms = [140 + (index % 7) for index in range(20)]
    tags = ["boom bap"] * 20
    lyrics = [_vocal_source()] * 20
    kwargs = dict(
        family="lab",
        album_slug="peer-review",
        bpms=bpms,
        tags=tags,
        lyrics=lyrics,
        kind="vocal",
    )
    first = assign_album_plans(**kwargs)  # type: ignore[arg-type]
    second = assign_album_plans(**kwargs)  # type: ignore[arg-type]
    assert [plan["form_id"] for plan in first] == [plan["form_id"] for plan in second]
    assert len({plan["duration_s"] for plan in first}) >= 8
    assert len({plan["form_id"] for plan in first}) >= 8
    assert len({plan["keyscale"] for plan in first}) >= 4
    durations = [plan["duration_s"] for plan in first]
    assert any(right - left > 0 for left, right in zip(durations, durations[1:]))
    assert any(right - left < 0 for left, right in zip(durations, durations[1:]))
    spoken = assign_album_plans(
        family="lab",
        album_slug="",
        bpms=[88],
        tags=["boom bap"],
        lyrics=["[spoken word]\nyo\n\n" + _vocal_source()],
        spoken=[],
        kind="vocal",
    )
    assert spoken[0]["form_id"] != "v_spoken"
    assert spoken[0]["form_id"] in VOCAL_FORMS


def test_demos_and_rack_skeletons() -> None:
    draft = demo_draft_lyrics()
    full = demo_full_lyrics()
    assert "[verse]" in draft and "[chorus]" in draft
    assert "[intro]" not in draft
    assert "[pre-chorus]" in full and "[outro]" in full
    assert demo_draft_seconds() == duration_seconds(bars=18, meter="4", bpm=88, clamp=False)
    assert demo_full_seconds() > 120
    rows = rack_form_entries()
    assert len(rows) >= 100
    ids = [row["id"] for row in rows]
    assert len(ids) == len(set(ids))
    assert all(re.fullmatch(r"frm_[a-z0-9_]+", row["id"]) for row in rows)
    for row in rows:
        for field in ("lyrics_form", "lyrics_form_inst"):
            text = str(row[field])
            assert "[form-" not in text
            for line in text.splitlines():
                if not line.startswith("["):
                    continue
                label = line[1:-1].split(" - ", 1)[0]
                assert label in _ACE_MARKERS
    assert any(row["id"].startswith("frm_e_") for row in rows)
    assert any("breakdown" in row["lyrics_form"] for row in rows)
    assert len(MOTIFS) == 3
    assert set(EDM_FORMS)
