"""My Coder translates the Drive-through sources into cues."""

from __future__ import annotations

import pytest

from ez_music import code_score
from ez_music.code_score import (
    _GROUPS,
    authored_bpm,
    cell_cues,
    coder_spans,
    coder_tokens,
    performance_bpm,
    performance_recipe,
)
from ez_music.drive_arrange import DRIVE_BPM_CHOICES, RECIPE_LINES, _cue_for
from ez_music.edm_examples import EDM_EXAMPLES, EdmExample, finalize_drive_album
from ez_music.edm_drive_through import EDM_DRIVE_THROUGH
from ez_music.edm_drive_through_afterparty import EDM_DRIVE_THROUGH_AFTERPARTY
from ez_music.edm_drive_through_bass import EDM_DRIVE_THROUGH_BASS
from ez_music.edm_drive_through_headliner import EDM_DRIVE_THROUGH_HEADLINER
from ez_music.edm_drive_through_secret_homage import EDM_DRIVE_THROUGH_SECRET_HOMAGE


def test_spans_cover_the_coder_in_order() -> None:
    spans = coder_spans()
    assert len(spans) == 16
    assert tuple(span.slug for span in spans) == tuple(group[1] for group in _GROUPS)
    assert tuple(span.title for span in spans) == tuple(group[2] for group in _GROUPS)
    assert all(span.tokens for span in spans)
    assert tuple(token for span in spans for token in span.tokens) == coder_tokens()
    for span, group in zip(spans, _GROUPS):
        for name in group[3]:
            assert name in span.tokens, (span.slug, name)


def test_comments_are_skipped_and_gaps_attach_to_the_next_span() -> None:
    source = (
        "LABEL = 'kept-word'\n"
        "\n"
        "def alpha():\n"
        "    # hidden bell\n"
        "    return 3\n"
        "\n"
        "pending = 9\n"
        "\n"
        "def beta(name: str) -> str:\n"
        '    return f"lane {name} stays"\n'
    )
    bounds = code_score._bounds(source, (("alpha",), ("beta",)))
    assert bounds == ((1, 5), (6, 10))
    first = code_score._tokens_in(source, *bounds[0])
    second = code_score._tokens_in(source, *bounds[1])
    assert "bell" not in first
    assert "kept" in first and "word" in first
    assert "alpha" in first and "3" in first
    assert "pending" in second and "9" in second
    assert "lane" in second and "stays" in second
    assert "beta" in second


def test_missing_function_raises() -> None:
    with pytest.raises(ValueError, match="missing coder function"):
        code_score._bounds("x = 1\n", (("absent",),))
    assert code_score._bounds("x = 1\n", ()) == ()


def test_token_change_moves_that_cell_only() -> None:
    roles = ("inst", "inst", "drop")
    left = cell_cues(("alpha", "beta", "gamma"), roles)
    right = cell_cues(("alpha", "beta", "delta"), roles)
    again = cell_cues(("alpha", "beta", "gamma"), roles)
    assert left == again
    assert left[0] == right[0]
    assert left[1] == right[1]
    assert left[2] != right[2]


def test_banned_words_stay_out_of_the_cue() -> None:
    pluck = cell_cues(("pluck",), ("drop",))
    bell = cell_cues(("bell",), ("drop",))
    assert pluck != bell
    assert "pluck" not in pluck[0].lower()
    assert "bell" not in bell[0].lower()


def test_extra_cells_revoice_the_same_span() -> None:
    cues = cell_cues(("only",), ("inst", "drop"))
    assert len(cues) == 2
    assert cues[0] != cues[1]
    assert cell_cues((), ()) == ()
    assert len(cell_cues((), ("inst", "drop"))) == 2


def test_tempo_and_recipe_come_from_the_tokens() -> None:
    tokens = ("lift_drive_bpm", "return", "165")
    assert 140 <= authored_bpm(tokens) <= 176
    assert performance_bpm(tokens) in DRIVE_BPM_CHOICES
    assert performance_bpm(tokens) == performance_bpm(tokens)
    recipe = performance_recipe(tokens)
    assert recipe in RECIPE_LINES
    assert recipe != "rec_drive_dj_shout"


def test_fresh_cue_skips_drop_language_then_exhausts(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}
    real = _cue_for

    def fake(role: str, n: int, salt: int, attempt: int = 0) -> str:
        calls["n"] += 1
        if calls["n"] == 1 and role != "drop":
            return "heavy drop"
        return real(role, n, salt, attempt)

    monkeypatch.setattr(code_score, "_cue_for", fake)
    cues = cell_cues(("alpha",), ("inst",))
    assert "drop" not in cues[0]
    assert calls["n"] >= 2

    monkeypatch.setattr(code_score, "_cue_for", lambda *_args, **_kwargs: "pluck")
    with pytest.raises(ValueError, match="no code cue"):
        cell_cues(("alpha",), ("inst",))


def test_my_coder_scores_are_the_source() -> None:
    spans = coder_spans()
    rows = [ex for ex in EDM_EXAMPLES if ex["album_slug"] == "my-coder"]
    assert len(rows) == 16
    assert [ex["slug"] for ex in rows] == [span.slug for span in spans]
    assert [ex.get("code_tokens") for ex in rows] == [span.tokens for span in spans]
    for ex, span in zip(rows, spans):
        assert ex["bpm"] == performance_bpm(span.tokens)
        assert ex["recipe"] == performance_recipe(span.tokens)
        assert ex["ace_mode"] == "instrumental"
        assert ex["phase"] == 5
        roles: list[str] = []
        bodies: list[str] = []
        for line in ex["lyrics"].splitlines():
            stripped = line.strip()
            if not (stripped.startswith("[") and stripped.endswith("]")):
                continue
            inner = stripped[1:-1]
            role, _sep, body = inner.partition(" - ")
            roles.append(role.strip())
            bodies.append(body)
        cues = cell_cues(span.tokens, roles)
        for body, cue in zip(bodies, cues):
            assert body.startswith(cue + ", "), (ex["stem"], cue)


def test_span_count_must_match_the_seed_list(monkeypatch: pytest.MonkeyPatch) -> None:
    from ez_music.edm_drive_through_my_coder import _rows

    monkeypatch.setattr("ez_music.edm_drive_through_my_coder.coder_spans", lambda: ())
    with pytest.raises(ValueError, match="my coder spans"):
        _rows()


def test_earlier_albums_are_unchanged_by_the_coder_path() -> None:
    groups = (
        EDM_DRIVE_THROUGH,
        EDM_DRIVE_THROUGH_BASS,
        EDM_DRIVE_THROUGH_HEADLINER,
        EDM_DRIVE_THROUGH_AFTERPARTY,
        EDM_DRIVE_THROUGH_SECRET_HOMAGE,
    )
    finalized: list[EdmExample] = []
    for group in groups:
        finalized.extend(finalize_drive_album(group))
    head = [ex for ex in EDM_EXAMPLES if ex["phase"] < 5]
    assert len(head) == 85
    assert len(finalized) == 85
    for got, expected in zip(finalized, head):
        assert got["lyrics"] == expected["lyrics"]
        assert got["seed"] == expected["seed"]
        assert got["title"] == expected["title"]
        assert got["stem"] == expected["stem"]
        assert got["duration"] == expected["duration"]
        assert "code_tokens" not in got
        assert "code_tokens" not in expected
