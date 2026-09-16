"""Hermetic tests for the shipped film catalog and per-film stitch caps."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_film.catalog import (  # noqa: E402
    FILMS,
    LONG_CAP_SECONDS,
    LONG_FILMS,
    LONG_SHOT_COUNT,
    NINETY_S_FILMS,
    ONE_CLICK_SHOT_COUNT,
    _cli,
    film_acts,
    film_beats,
    film_publish_cap,
    film_slug,
    film_total_shots,
    master_filename,
)
from ez_film.concat import publish_path, stitch_film  # noqa: E402
from ez_film.jobstore import new_state, shot_id  # noqa: E402
from ez_film.nodes import EZFilmConcat  # noqa: E402
from ez_film.shots import SHOT_COUNT  # noqa: E402

SHORTS = ROOT / "workflows" / "shorts"


def test_catalog_splits_ninety_and_long() -> None:
    assert NINETY_S_FILMS == ("go-see", "still-here", "switchyard")
    assert LONG_FILMS == (
        "tide-table",
        "night-oven",
        "glasshouse",
        "last-lane",
        "breakwater",
    )
    assert set(FILMS) == set(NINETY_S_FILMS) | set(LONG_FILMS)
    for film in NINETY_S_FILMS:
        assert film_total_shots(film) == ONE_CLICK_SHOT_COUNT
        assert film_publish_cap(film) == 90.0
        assert film_acts(film) == 1
        assert film_beats(film) == 6
        assert master_filename(film) == f"ez_{film_slug(film)}_90s.mp4"
    for film in LONG_FILMS:
        assert film_total_shots(film) == LONG_SHOT_COUNT
        assert film_publish_cap(film) == LONG_CAP_SECONDS
        assert film_acts(film) == 5
        assert film_beats(film) == 30
        assert master_filename(film) == f"ez_{film_slug(film)}_450s.mp4"
        assert master_filename(film, act=1) == f"ez_{film_slug(film)}_act1_90s.mp4"
        assert master_filename(film, act=5) == f"ez_{film_slug(film)}_act5_90s.mp4"


def test_unknown_film_fails_closed() -> None:
    with pytest.raises(ValueError, match="unknown film"):
        film_slug("nope")
    assert _cli(["slug", "nope"]) == 1
    assert _cli(["ids"]) == 0


def test_shot_id_respects_total() -> None:
    assert shot_id(1, 1) == "01"
    assert shot_id(6, 3) == "18"
    with pytest.raises(ValueError):
        shot_id(7, 1)
    assert shot_id(7, 1, total=90) == "19"
    assert shot_id(30, 3, total=90) == "90"
    with pytest.raises(ValueError):
        shot_id(31, 1, total=90)


def test_new_state_uses_catalog_counts() -> None:
    ninety = new_state("go-see", "gosee")
    assert len(ninety["shots"]) == SHOT_COUNT
    assert ninety["total_shots"] == 18
    assert ninety["publish_cap_s"] == 90.0
    long = new_state("tide-table", "tidetable")
    assert len(long["shots"]) == 90
    assert long["shots"][-1]["id"] == "90"
    assert long["publish_cap_s"] == 450.0


def test_publish_path_act_and_long_cap(tmp_path: Path) -> None:
    assert publish_path("go-see", tmp_path) == tmp_path / "ez_gosee_90s.mp4"
    assert publish_path("tide-table", tmp_path) == tmp_path / "ez_tidetable_450s.mp4"
    assert (
        publish_path("tide-table", tmp_path, act=2)
        == tmp_path / "ez_tidetable_act2_90s.mp4"
    )


def test_ez_film_concat_has_act_widget() -> None:
    required = EZFilmConcat.INPUT_TYPES()["required"]
    assert "act" in required
    assert "tide-table" in required["film"][0]
    assert required["cap_seconds"][1]["max"] == 90.0
    assert required["act"][1]["max"] == 5


def test_stitch_film_accepts_expected_count(tmp_path: Path) -> None:
    shots = [str(tmp_path / f"s{i:02d}.mp4") for i in range(90)]
    for path in shots:
        Path(path).write_bytes(b"mp4")
    out = str(tmp_path / "ez_tidetable_450s.mp4")
    captured: list[list[str]] = []

    def fake_run(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        captured.append(list(argv))
        Path(argv[-1]).write_bytes(b"mp4")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    with patch("ez_film.concat.validate_stitch_stems", return_value=None):
        with (
            patch("ez_film.concat.probe_seconds", return_value=450.0),
            patch("ez_film.concat.probe_has_audio", return_value=True),
            patch("ez_film.concat.probe_audio_seconds", return_value=450.0),
        ):
            stitch_film(
                shots,
                out,
                450.0,
                ffmpeg="ffmpeg",
                run=fake_run,
                expected_count=90,
            )
    assert captured
    assert captured[0][captured[0].index("-t") + 1] == "450.0"
    with pytest.raises(ValueError, match="expected 90"):
        stitch_film(shots[:18], out, 450.0, expected_count=90)


def test_parse_rejects_catalog_mismatch() -> None:
    text = (SHORTS / "go-see.shots.yaml").read_text(encoding="utf-8")
    from ez_film.shots import parse_shots_yaml

    with pytest.raises(ValueError, match="slug mismatch"):
        parse_shots_yaml(text.replace("slug: gosee", "slug: nope", 1))
    with pytest.raises(ValueError, match="shot count mismatch"):
        parse_shots_yaml(text.replace("total_shots: 18", "total_shots: 17", 1))
    with pytest.raises(ValueError, match="shot count mismatch"):
        parse_shots_yaml(text.replace("beats: 6", "beats: 5", 1))
    with pytest.raises(ValueError, match="does not match catalog"):
        parse_shots_yaml(text.replace("publish_cap_s: 90.00", "publish_cap_s: 91.00", 1))
    with pytest.raises(ValueError, match="invalid shot-count meta"):
        parse_shots_yaml(text.replace("publish_cap_s: 90.00", "publish_cap_s: nope", 1))


def test_catalog_cli_fields(capsys: pytest.CaptureFixture[str]) -> None:
    from ez_film.catalog import film_id_for_slug, known_films

    assert known_films()[0] == "go-see"
    assert film_id_for_slug("tidetable") == "tide-table"
    assert film_id_for_slug("nope") is None
    assert _cli(["slug", "tide-table"]) == 0
    assert capsys.readouterr().out.strip() == "tidetable"
    assert _cli(["cap", "tide-table"]) == 0
    assert capsys.readouterr().out.strip() == "450.00"
    assert _cli(["shots", "breakwater"]) == 0
    assert capsys.readouterr().out.strip() == "90"
    assert _cli(["beats", "go-see"]) == 0
    assert capsys.readouterr().out.strip() == "6"
    assert _cli(["acts", "glasshouse"]) == 0
    assert capsys.readouterr().out.strip() == "5"
    assert _cli(["master", "night-oven", "--act", "3"]) == 0
    assert capsys.readouterr().out.strip() == "ez_nightoven_act3_90s.mp4"
    assert _cli(["master", "go-see"]) == 0
    assert capsys.readouterr().out.strip() == "ez_gosee_90s.mp4"
    assert _cli(["ids"]) == 0
    assert "tide-table" in capsys.readouterr().out
    assert _cli(["slug"]) == 1
    assert _cli(["slug", "nope"]) == 1
