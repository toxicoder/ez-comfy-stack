"""The shared Drive-through album builder keeps every hour identical.

These tests pin ``ez_music.edm_album`` at full coverage and replay each
album module with a spying row builder, so a template change cannot
silently re-layout, re-title, or re-seed a shipped take.
"""

from __future__ import annotations

import importlib
import pathlib
from collections.abc import Callable
from typing import cast

import pytest

from ez_music import edm_album
from ez_music.edm_album import (
    AFTERPARTY_PHASE,
    BASS_PHASE,
    DRIVE_THROUGH_PHASE,
    EDM_LAYOUTS,
    HEADLINER_PHASE,
    MY_CODER_PHASE,
    SECRET_HOMAGE_PHASE,
    DriveRowBuilder,
    DriveRowSpec,
    build_album,
    drive_slug,
    layout_cycle,
    title_from_slug,
)
from ez_music.edm_examples import EDM_EXAMPLES, EdmExampleRow
from ez_music.edm_drive_through import EDM_DRIVE_THROUGH
from ez_music.edm_drive_through_afterparty import EDM_DRIVE_THROUGH_AFTERPARTY
from ez_music.edm_drive_through_bass import EDM_DRIVE_THROUGH_BASS
from ez_music.edm_drive_through_headliner import EDM_DRIVE_THROUGH_HEADLINER
from ez_music.edm_drive_through_my_coder import EDM_DRIVE_THROUGH_MY_CODER
from ez_music.edm_drive_through_secret_homage import EDM_DRIVE_THROUGH_SECRET_HOMAGE

# Fields ``_ex`` copies through untouched, so a replay can assert them.
_PASSTHROUGH = ("slug", "title", "seed", "phase", "recipe", "layout")

# One builder call, logged field by field.
RowLog = list[dict[str, object]]


def _logger(seen: RowLog, real: Callable[..., EdmExampleRow]) -> DriveRowBuilder[EdmExampleRow]:
    """Wrap a row builder so every ``build_album`` call is logged.

    Args:
        seen: Argument log to fill.
        real: The builder to defer to after logging.

    Returns:
        A row builder ``build_album`` can use as ``row_for``.
    """

    def _row(
        slug: str,
        title: str,
        bpm: int,
        seed: int,
        phase: int,
        take: str,
        lyrics: str,
        *,
        recipe: str,
        picks: dict[str, str] | None = None,
        layout: str = "column",
    ) -> EdmExampleRow:
        """Log the call, then defer to the wrapped builder.

        Args:
            slug: Kebab title.
            title: Operator-facing take name.
            bpm: Tempo.
            seed: Fixed seed.
            phase: Live-set hour index.
            take: Lab description blurb.
            lyrics: Arrangement score.
            recipe: Audio Rack recipe id.
            picks: Axis overrides.
            layout: Comfy placement name.

        Returns:
            Whatever the wrapped builder returned.
        """
        seen.append(
            {
                "slug": slug,
                "title": title,
                "bpm": bpm,
                "seed": seed,
                "phase": phase,
                "take": take,
                "lyrics": lyrics,
                "recipe": recipe,
                "picks": picks,
                "layout": layout,
            }
        )
        return real(
            slug,
            title,
            bpm,
            seed,
            phase,
            take,
            lyrics,
            recipe=recipe,
            picks=picks,
            layout=layout,
        )

    return _row


def _collector() -> tuple[RowLog, DriveRowBuilder[EdmExampleRow]]:
    """Capture rows handed to a builder instead of building them.

    Returns:
        A fresh argument log and a builder that fills it and returns an
        empty row.
    """
    seen: RowLog = []
    return seen, _logger(seen, lambda *_args, **_kwargs: cast(EdmExampleRow, {}))


def _take(**overrides: object) -> DriveRowSpec:
    """One minimal authored take with fields replaced.

    Args:
        overrides: Fields to set on the take.

    Returns:
        A ``DriveRowSpec`` for ``build_album``.
    """
    take: DriveRowSpec = {
        "slug": str(overrides.get("slug", "night-window")),
        "bpm": int(str(overrides.get("bpm", 145))),
        "seed": int(str(overrides.get("seed", 193))),
        "take": str(overrides.get("take", "night-window hybrid trap warp")),
        "lyrics": str(overrides.get("lyrics", "[drop - heavy warped drop]")),
        "recipe": str(overrides.get("recipe", "rec_drive_through_drop")),
    }
    title = overrides.get("title")
    if title is not None:
        take["title"] = str(title)
    picks = overrides.get("picks")
    if isinstance(picks, dict):
        take["picks"] = {str(key): str(value) for key, value in picks.items()}
    layout = overrides.get("layout")
    if layout is not None:
        take["layout"] = str(layout)
    return take


def test_phase_constants_are_the_live_set_hours() -> None:
    assert (
        DRIVE_THROUGH_PHASE,
        BASS_PHASE,
        HEADLINER_PHASE,
        AFTERPARTY_PHASE,
        SECRET_HOMAGE_PHASE,
        MY_CODER_PHASE,
    ) == (0, 1, 2, 3, 4, 5)


def test_layouts_match_the_catalog_lock() -> None:
    from ez_music import edm_examples

    assert EDM_LAYOUTS == edm_examples.EDM_LAYOUTS
    assert set(layout_cycle(5)) == set(EDM_LAYOUTS)


def test_title_from_slug_spaces_hyphened_words() -> None:
    assert title_from_slug("dawn-receipt") == "dawn receipt"
    assert title_from_slug("on-ramp") == "on ramp"
    assert title_from_slug("plain") == "plain"


def test_layout_cycle_walks_the_placement_order() -> None:
    assert layout_cycle(0) == ()
    assert layout_cycle(1) == ("column",)
    assert layout_cycle(5) == (
        "column",
        "wide-stage",
        "stacked-tower",
        "prompt-left",
        "output-rail",
    )
    assert layout_cycle(2, offset=1) == ("wide-stage", "stacked-tower")
    assert layout_cycle(6)[-1] == "column"
    assert layout_cycle(6)[:5] == layout_cycle(5)
    for offset in range(len(EDM_LAYOUTS)):
        assert set(layout_cycle(5, offset=offset)) == set(EDM_LAYOUTS)


def test_build_album_defaults_title_picks_and_layout() -> None:
    seen, row_for = _collector()
    rows = build_album([_take()], phase=DRIVE_THROUGH_PHASE, row_for=row_for)
    assert rows == ({},)
    assert seen == [
        {
            "slug": "night-window",
            "title": "night window",
            "bpm": 145,
            "seed": 193,
            "phase": DRIVE_THROUGH_PHASE,
            "take": "night-window hybrid trap warp",
            "lyrics": "[drop - heavy warped drop]",
            "recipe": "rec_drive_through_drop",
            "picks": None,
            "layout": "column",
        }
    ]


def test_build_album_keeps_explicit_title_and_picks() -> None:
    seen, row_for = _collector()
    picks = {"bass_low_end": "bass_reese"}
    build_album([_take(title="on-ramp", picks=picks)], phase=BASS_PHASE, row_for=row_for)
    assert seen[0]["title"] == "on-ramp"
    assert seen[0]["picks"] == picks
    assert seen[0]["phase"] == BASS_PHASE


def test_build_album_hands_the_builder_a_copy_of_the_picks() -> None:
    seen, row_for = _collector()
    picks = {"bass_low_end": "bass_reese"}
    build_album([_take(picks=picks)], phase=BASS_PHASE, row_for=row_for)
    assert seen[0]["picks"] == picks
    assert seen[0]["picks"] is not picks


def test_build_album_uses_the_album_layout_sequence() -> None:
    seen, row_for = _collector()
    build_album(
        [_take(slug="a"), _take(slug="b")],
        phase=HEADLINER_PHASE,
        row_for=row_for,
        layouts=("wide-stage", "prompt-left"),
    )
    assert [row["layout"] for row in seen] == ["wide-stage", "prompt-left"]
    assert [row["slug"] for row in seen] == ["a", "b"]


def test_build_album_row_layout_overrides_the_sequence() -> None:
    seen, row_for = _collector()
    build_album(
        [_take(layout="output-rail")],
        phase=AFTERPARTY_PHASE,
        row_for=row_for,
        layouts=layout_cycle(1),
    )
    assert seen[0]["layout"] == "output-rail"


def test_build_album_row_layout_overrides_the_default_placement() -> None:
    seen, row_for = _collector()
    build_album([_take(layout="prompt-left")], phase=SECRET_HOMAGE_PHASE, row_for=row_for)
    assert seen[0]["layout"] == "prompt-left"


def test_build_album_builds_nothing_for_an_empty_table() -> None:
    seen, row_for = _collector()
    assert build_album((), phase=BASS_PHASE, row_for=row_for) == ()
    assert seen == []


def test_build_album_rejects_a_short_layout_sequence() -> None:
    _, row_for = _collector()
    with pytest.raises(ValueError, match="phase 5 needs 2 layouts, got 1"):
        build_album(
            [_take(slug="a"), _take(slug="b")],
            phase=MY_CODER_PHASE,
            row_for=row_for,
            layouts=("column",),
        )


def test_build_album_rejects_an_unknown_default_placement() -> None:
    _, row_for = _collector()
    with pytest.raises(ValueError, match="take 0 of phase 0 has layout 'flyover'"):
        build_album([_take(layout="flyover")], phase=DRIVE_THROUGH_PHASE, row_for=row_for)


def test_build_album_rejects_an_unknown_sequenced_layout() -> None:
    _, row_for = _collector()
    with pytest.raises(ValueError, match="take 1 of phase 3 has layout 'overpass'"):
        build_album(
            [_take(slug="a"), _take(slug="b")],
            phase=AFTERPARTY_PHASE,
            row_for=row_for,
            layouts=("column", "overpass"),
        )


def test_builder_seam_admits_any_row_shape() -> None:
    """The Protocol seam is generic, so a caller can build its own shape."""
    labels = {"a": "01", "b": "02"}

    def _label(
        slug: str,
        title: str,
        bpm: int,
        seed: int,
        phase: int,
        take: str,
        lyrics: str,
        *,
        recipe: str,
        picks: dict[str, str] | None = None,
        layout: str = "column",
    ) -> str:
        """Fold one take into a track label.

        Args:
            slug: Kebab title.
            title: Operator-facing take name.
            bpm: Tempo.
            seed: Fixed seed.
            phase: Live-set hour index.
            take: Lab description blurb.
            lyrics: Arrangement score.
            recipe: Audio Rack recipe id.
            picks: Axis overrides.
            layout: Comfy placement name.

        Returns:
            ``NN title bpm layout`` for that take.
        """
        del take, lyrics, recipe, picks
        return f"{labels[slug]} {title} {bpm} {layout} {seed} {phase}"

    out: tuple[str, ...] = build_album(
        [_take(slug="a"), _take(slug="b")],
        phase=MY_CODER_PHASE,
        row_for=_label,
        layouts=layout_cycle(2),
    )
    assert out == ("01 a 145 column 193 5", "02 b 145 wide-stage 193 5")


def test_every_hour_has_the_shipped_shape() -> None:
    hours = (
        (DRIVE_THROUGH_PHASE, EDM_DRIVE_THROUGH, 15),
        (BASS_PHASE, EDM_DRIVE_THROUGH_BASS, 15),
        (HEADLINER_PHASE, EDM_DRIVE_THROUGH_HEADLINER, 15),
        (AFTERPARTY_PHASE, EDM_DRIVE_THROUGH_AFTERPARTY, 20),
        (SECRET_HOMAGE_PHASE, EDM_DRIVE_THROUGH_SECRET_HOMAGE, 20),
        (MY_CODER_PHASE, EDM_DRIVE_THROUGH_MY_CODER, 16),
    )
    for phase, rows, expected in hours:
        assert len(rows) == expected, phase
        assert {row["phase"] for row in rows} == {phase}
        assert {row["layout"] for row in rows} <= EDM_LAYOUTS
        assert all(row["recipe"].startswith("rec_drive_") for row in rows)


def test_coder_album_is_the_only_one_carrying_tokens() -> None:
    assert all("code_tokens" in row for row in EDM_DRIVE_THROUGH_MY_CODER)
    assert not any("code_tokens" in row for row in EDM_DRIVE_THROUGH + EDM_DRIVE_THROUGH_BASS)


@pytest.mark.parametrize(
    ("module_name", "export", "expected"),
    [
        ("edm_drive_through", "EDM_DRIVE_THROUGH", EDM_DRIVE_THROUGH),
        ("edm_drive_through_bass", "EDM_DRIVE_THROUGH_BASS", EDM_DRIVE_THROUGH_BASS),
        (
            "edm_drive_through_headliner",
            "EDM_DRIVE_THROUGH_HEADLINER",
            EDM_DRIVE_THROUGH_HEADLINER,
        ),
        (
            "edm_drive_through_afterparty",
            "EDM_DRIVE_THROUGH_AFTERPARTY",
            EDM_DRIVE_THROUGH_AFTERPARTY,
        ),
        (
            "edm_drive_through_secret_homage",
            "EDM_DRIVE_THROUGH_SECRET_HOMAGE",
            EDM_DRIVE_THROUGH_SECRET_HOMAGE,
        ),
        (
            "edm_drive_through_my_coder",
            "EDM_DRIVE_THROUGH_MY_CODER",
            EDM_DRIVE_THROUGH_MY_CODER,
        ),
    ],
)
def test_the_take_table_builds_the_shipped_rows(
    module_name: str,
    export: str,
    expected: tuple[EdmExampleRow, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reloading an album with a spy builder replays its data exactly.

    Args:
        module_name: Album module name without the package.
        export: Name of the album's exported row tuple.
        expected: The shipped partial rows for that hour.
        monkeypatch: Restores ``edm_examples._ex`` after the replay.

    Raises:
        AssertionError: a replayed row differs from the shipped one.
    """
    from ez_music import edm_examples

    seen: RowLog = []
    monkeypatch.setattr(edm_examples, "_ex", _logger(seen, edm_examples._ex))
    module = importlib.import_module(f"ez_music.{module_name}")
    importlib.reload(module)
    built: tuple[EdmExampleRow, ...] = getattr(module, export)
    assert built == expected
    assert len(seen) == len(expected)
    for logged, shipped in zip(seen, built):
        fields = cast("dict[str, object]", logged)
        values = cast("dict[str, object]", shipped)
        for field in _PASSTHROUGH:
            assert fields[field] == values[field], (module_name, shipped["slug"], field)


def test_catalog_holds_every_hour_in_order() -> None:
    assert len(EDM_EXAMPLES) == 101
    assert len({row["stem"] for row in EDM_EXAMPLES}) == 101
    assert [row["phase"] for row in EDM_EXAMPLES] == [
        phase
        for phase, count in (
            (DRIVE_THROUGH_PHASE, 15),
            (BASS_PHASE, 15),
            (HEADLINER_PHASE, 15),
            (AFTERPARTY_PHASE, 20),
            (SECRET_HOMAGE_PHASE, 20),
            (MY_CODER_PHASE, 16),
        )
        for _track in range(count)
    ]
    assert [row["track"] for row in EDM_EXAMPLES[:15]] == list(range(1, 16))
    coder = [row for row in EDM_EXAMPLES if row["album_slug"] == "my-coder"]
    assert len(coder) == 16
    assert all(row.get("code_tokens") for row in coder)


def test_build_album_rejects_a_stem_pasted_into_the_table() -> None:
    _, row_for = _collector()
    with pytest.raises(ValueError, match=r"take 0 of phase 1 has stem '07-night-window'"):
        build_album(
            [_take(slug="07-night-window")],
            phase=BASS_PHASE,
            row_for=row_for,
        )
    with pytest.raises(ValueError, match="has stem 'music-edm-drive-through-x-lab-example'"):
        build_album(
            [_take(slug="music-edm-drive-through-x-lab-example")],
            phase=BASS_PHASE,
            row_for=row_for,
        )


def test_drive_slug_strips_the_legacy_affixes() -> None:
    assert drive_slug("music-edm-drive-through-", "07-night-window") == "night-window"
    assert (
        drive_slug("music-edm-drive-through-", "music-edm-drive-through-x-lab-example")
        == "x"
    )
    assert drive_slug("music-edm-drive-through-", "brake-fade") == "brake-fade"
    assert drive_slug("music-rap-", "3-take") == "take"
    assert drive_slug("music-rap-", "9single") == "9single"


def test_edm_examples_stays_the_catalog_owner() -> None:
    """The catalog module still exports every symbol the coder path parses.

    Raises:
        AssertionError: a frozen ``edm_examples`` symbol went missing.
    """
    from ez_music import edm_examples

    frozen: tuple[str, ...] = (
        "_tempo_id",
        "_splice_drive",
        "drive_tags",
        "_desc",
        "_ex",
        "_cues_from_body",
        "_uniquify_score",
        "_spell_score_body",
        "format_edm_score",
        "drive_slug_from_stem",
        "finalize_drive_album",
        "_catalog",
        "FORBIDDEN_SCORE_NEEDLES",
        "HIGH_PITCH_NEEDLES",
        "EDM_LAYOUTS",
        "EDM_DURATION_S",
    )
    for name in frozen:
        assert hasattr(edm_examples, name), name
    assert edm_examples.EDM_DURATION_S == 180.0


def test_edm_album_is_a_leaf_module() -> None:
    """Nothing pulls back into the catalog through the shared library.

    Raises:
        AssertionError: the leaf grew a first-party import.
    """
    source = pathlib.Path(edm_album.__file__).read_text(encoding="utf-8")
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith(("from .", "from ez_music", "import ez_music")):
            raise AssertionError(f"leaf imports a first-party module: {stripped}")
