"""Hermetic tests for the ez_edit timeline reducer (no GPU, network, or ffmpeg).

Covers :mod:`ez_edit.timeline` end to end: record validation, every op in the
pinned vocabulary, every ``TimelineError`` branch, and the one-JSON-file-per-
project store under ``<edit_dir>/projects``. Clocks are injected so stamps are
deterministic; every path goes through ``tmp_path``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from ez_edit import timeline
from ez_edit.protocol import OpName
from ez_edit.timeline import (
    TimelineError,
    apply_ops,
    load_project,
    most_recent,
    new_project,
    project_index,
    save_project,
)

STAMP = "2026-01-02T03:04:05+00:00"
"""Fixed ISO-8601 UTC stamp injected wherever the reducer stamps time."""


def _utc_clock() -> datetime:
    """Return a fixed aware UTC datetime.

    Returns:
        The datetime matching :data:`STAMP`.
    """
    return datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)


def _raw(value: object) -> Any:
    """Loosen one value's static type so tests can feed malformed records.

    Args:
        value: Value to hand to the reducer as ``Any``.

    Returns:
        The same value.
    """
    return value


def _clip(clip_id: str = "c0", **overrides: Any) -> dict[str, Any]:
    """Build a valid clip argument with optional overrides.

    Args:
        clip_id: Clip id.
        **overrides: Fields to add or replace.

    Returns:
        Clip argument mapping.
    """
    clip: dict[str, Any] = {
        "id": clip_id,
        "source": f"clips/{clip_id}.mp4",
        "in_s": 0.0,
        "out_s": 2.0,
    }
    clip.update(overrides)
    return clip


def _overlay(overlay_id: str = "o0", **overrides: Any) -> dict[str, Any]:
    """Build a valid text-overlay argument with optional overrides.

    Args:
        overlay_id: Overlay id.
        **overrides: Fields to add or replace.

    Returns:
        Overlay argument mapping.
    """
    overlay: dict[str, Any] = {
        "id": overlay_id,
        "kind": "text",
        "at_s": 0.0,
        "dur_s": 1.0,
        "text": "hello",
    }
    overlay.update(overrides)
    return overlay


def _caption(caption_id: str = "k0", **overrides: Any) -> dict[str, Any]:
    """Build a valid caption argument with optional overrides.

    Args:
        caption_id: Caption id.
        **overrides: Fields to add or replace.

    Returns:
        Caption argument mapping.
    """
    caption: dict[str, Any] = {
        "id": caption_id,
        "at_s": 0.5,
        "dur_s": 1.5,
        "text": "line one",
    }
    caption.update(overrides)
    return caption


def _seeded(clip_count: int = 3, *, project_id: str = "p1") -> Any:
    """Build a project carrying ``clip_count`` clips.

    Args:
        clip_count: How many clips to add.
        project_id: Project id.

    Returns:
        Project record (typed ``Any`` so callers may pass malformed shapes).
    """
    ops: list[dict[str, Any]] = [
        {"op": "project_create", "args": {"id": project_id}}
    ]
    ops.extend(
        {"op": "add_clip", "args": {"clip": _clip(f"c{i}")}} for i in range(clip_count)
    )
    return apply_ops(None, ops, clock=STAMP)


def _edit_dir(tmp_path: Path) -> Path:
    """Return an edit root under ``tmp_path``.

    Args:
        tmp_path: Pytest scratch directory.

    Returns:
        Directory path (may not exist yet).
    """
    return tmp_path / "edit"


# --- Vocabulary derived from the pinned seam --------------------------------


def test_vocabularies_mirror_protocol() -> None:
    from typing import get_args

    from ez_edit.protocol import OverlayKind, TransitionKind

    assert timeline.OP_NAMES == frozenset(get_args(OpName))
    assert timeline.TRANSITION_KINDS == frozenset(get_args(TransitionKind))
    assert timeline.OVERLAY_KINDS == frozenset(get_args(OverlayKind))


def test_handlers_cover_every_op_but_create() -> None:
    assert set(timeline.HANDLERS) == timeline.OP_NAMES - {"project_create"}
    for name, handler in timeline.HANDLERS.items():
        assert callable(handler), name


def test_new_project_id_is_short_hex() -> None:
    generated = timeline.new_project_id()
    assert len(generated) == timeline.ID_LENGTH
    assert all(ch in "0123456789abcdef" for ch in generated)


# --- new_project -----------------------------------------------------------


def test_new_project_defaults() -> None:
    project = new_project(clock=_utc_clock)
    assert project["title"] == timeline.DEFAULT_TITLE
    assert project["fps"] == timeline.DEFAULT_FPS
    assert project["width"] == timeline.DEFAULT_WIDTH
    assert project["height"] == timeline.DEFAULT_HEIGHT
    assert project["clips"] == []
    assert project["overlays"] == []
    assert project["captions"] == []
    assert project["updated_at"] == STAMP
    assert len(project["id"]) == timeline.ID_LENGTH


def test_new_project_explicit_fields() -> None:
    project = new_project(
        "Launch reel", fps=30.0, width=1280, height=720, project_id="launch-01_2"
    )
    assert project["id"] == "launch-01_2"
    assert project["title"] == "Launch reel"
    assert (project["fps"], project["width"], project["height"]) == (30.0, 1280, 720)


def test_new_project_blank_id_generates_one() -> None:
    assert len(new_project(project_id="")["id"]) == timeline.ID_LENGTH


def test_new_project_wall_clock_stamp_is_utc_iso() -> None:
    stamp = new_project()["updated_at"]
    assert datetime.fromisoformat(stamp).tzinfo is not None


@pytest.mark.parametrize(
    ("kwargs", "fragment"),
    [
        ({"title": 7}, "title must be a string"),
        ({"fps": "24"}, "fps must be a number"),
        ({"fps": True}, "fps must be a number"),
        ({"fps": 0}, "fps must be > 0"),
        ({"width": "1920"}, "width must be an integer"),
        ({"width": True}, "width must be an integer"),
        ({"width": 0}, "width must be > 0"),
        ({"height": None}, "height must be an integer"),
        ({"height": -1}, "height must be > 0"),
        ({"project_id": "bad/id"}, "invalid project id"),
        ({"project_id": " "}, "invalid project id"),
        ({"project_id": "caf\xe9"}, "invalid project id"),
        ({"project_id": 5}, "id must be a string"),
    ],
)
def test_new_project_refuses_bad_arguments(
    kwargs: dict[str, Any], fragment: str
) -> None:
    with pytest.raises(TimelineError, match=fragment):
        new_project(**_raw(kwargs))


@pytest.mark.parametrize(
    ("clock", "fragment"),
    [
        ("", "stamp string must not be empty"),
        ("   ", "stamp string must not be empty"),
    ],
)
def test_new_project_refuses_blank_clock(clock: str, fragment: str) -> None:
    with pytest.raises(TimelineError, match=fragment):
        new_project(clock=_raw(clock))


def test_stamp_accepts_naive_and_aware_datetimes() -> None:
    naive = new_project(clock=lambda: datetime(2026, 5, 6, 7, 8, 9))
    assert naive["updated_at"] == "2026-05-06T07:08:09+00:00"
    aware = new_project(
        clock=lambda: datetime(2026, 5, 6, 9, 8, 9, tzinfo=timezone.utc)
    )
    assert aware["updated_at"] == "2026-05-06T09:08:09+00:00"


# --- apply_ops: dispatch and project_create --------------------------------


def test_apply_ops_creates_project_from_scratch() -> None:
    project = apply_ops(
        None,
        [
            {
                "op": "project_create",
                "args": {"id": "p1", "title": "T", "fps": 25.0, "width": 640, "height": 360},
            }
        ],
        clock=STAMP,
    )
    assert project["id"] == "p1"
    assert project["title"] == "T"
    assert (project["fps"], project["width"], project["height"]) == (25.0, 640, 360)
    assert project["updated_at"] == STAMP


def test_apply_ops_create_defaults_and_generated_id() -> None:
    project = apply_ops(None, [{"op": "project_create"}], clock=STAMP)
    assert project["title"] == timeline.DEFAULT_TITLE
    assert project["fps"] == timeline.DEFAULT_FPS
    assert len(project["id"]) == timeline.ID_LENGTH


def test_apply_ops_missing_args_key_is_accepted() -> None:
    project = apply_ops(None, [{"op": "project_create", "args": None}], clock=STAMP)
    assert project["updated_at"] == STAMP


def test_apply_ops_stamps_with_injected_callable_clock() -> None:
    project = apply_ops(None, [{"op": "project_create"}], clock=_utc_clock)
    assert project["updated_at"] == STAMP


def test_apply_ops_wall_clock_stamp_when_no_clock() -> None:
    project = apply_ops(None, [{"op": "project_create"}])
    assert datetime.fromisoformat(project["updated_at"]).tzinfo is not None


def test_apply_ops_empty_list_keeps_project_and_restamps() -> None:
    project = _seeded(2)
    stamped = apply_ops(project, [], clock=STAMP)
    assert stamped["clips"] == project["clips"]
    assert stamped["updated_at"] == STAMP


def test_apply_ops_does_not_mutate_the_input_project() -> None:
    project = _seeded(2)
    before = json.loads(json.dumps(project))
    result = apply_ops(
        project,
        [
            {"op": "add_clip", "args": {"clip": _clip("c9")}},
            {"op": "set_title", "args": {"title": "Renamed"}},
        ],
        clock=STAMP,
    )
    assert project == before
    assert result is not project
    assert result["title"] == "Renamed"
    assert len(result["clips"]) == 3


def test_apply_ops_failure_leaves_the_input_untouched() -> None:
    project = _seeded(2)
    before = json.loads(json.dumps(project))
    with pytest.raises(TimelineError, match="ops\\[2\\]"):
        apply_ops(
            project,
            [
                {"op": "add_clip", "args": {"clip": _clip("c9")}},
                {"op": "set_title", "args": {"title": "Ghost"}},
                {"op": "remove_clip", "args": {"clip_id": "nope"}},
            ],
            clock=STAMP,
        )
    assert project == before


@pytest.mark.parametrize(
    ("seeded", "ops", "fragment"),
    [
        (False, [], "empty list with no project"),
        (False, [{"op": "clear"}], "no project - start the list with project_create"),
        (
            False,
            [{"op": "project_create"}, {"op": "project_create"}],
            "project_create needs no existing project",
        ),
        (False, [{"op": "nope"}], "unknown op 'nope'"),
        (False, [{"op": 3}], "op must be a string"),
        (False, [{}], "missing argument 'op'"),
        (False, _raw(["clear"]), "op must be an object"),
        (False, _raw([42]), "op must be an object"),
        (False, [{"op": "clear", "args": []}], "args must be an object"),
        (False, [{"op": "clear", "args": "x"}], "args must be an object"),
        (False, [{"op": "clear", "args": 5}], "args must be an object"),
        (False, [{"op": "clear", "args": 0}], "args must be an object"),
        (True, [{"op": "add_clip"}], "missing argument 'clip'"),
        (
            True,
            [{"op": "add_clip", "args": {"clip": _clip(), "extra": 1}}],
            "unknown argument",
        ),
        (True, [{"op": "set_title", "args": {}}], "missing argument 'title'"),
        (True, [{"op": "set_title", "args": 7}], "args must be an object"),
    ],
)
def test_apply_ops_dispatch_errors(seeded: bool, ops: Any, fragment: str) -> None:
    project = _seeded(0) if seeded else None
    with pytest.raises(TimelineError, match=fragment):
        apply_ops(project, ops, clock=STAMP)


@pytest.mark.parametrize("key", ["name", "fpsx", "widths", "heights", "titles"])
def test_op_create_rejects_unknown_keys(key: str) -> None:
    with pytest.raises(TimelineError, match=f"unknown argument\\(s\\) {key}"):
        apply_ops(None, [{"op": "project_create", "args": {key: 1}}])


@pytest.mark.parametrize(
    ("args", "fragment"),
    [
        ({"id": "bad id"}, "invalid project id"),
        ({"id": 5}, "id must be a string"),
        ({"fps": "24"}, "fps must be a number"),
        ({"fps": -1}, "fps must be > 0"),
        ({"width": 1.5}, "width must be an integer"),
        ({"width": 0}, "width must be > 0"),
        ({"height": None}, "height must be an integer"),
        ({"height": 0}, "height must be > 0"),
        ({"title": 1}, "title must be a string"),
    ],
)
def test_op_create_rejects_bad_arguments(args: dict[str, Any], fragment: str) -> None:
    with pytest.raises(TimelineError, match=fragment):
        apply_ops(None, [{"op": "project_create", "args": _raw(args)}])


# --- add_clip --------------------------------------------------------------


def test_add_clip_fills_defaults() -> None:
    project = apply_ops(
        _seeded(0), [{"op": "add_clip", "args": {"clip": _clip("a")}}], clock=STAMP
    )
    assert project["clips"] == [
        {
            "id": "a",
            "source": "clips/a.mp4",
            "label": "",
            "in_s": 0.0,
            "out_s": 2.0,
            "track": 0,
            "gain": 1.0,
            "transition": None,
        }
    ]


def test_add_clip_keeps_supplied_fields_and_nested_transition() -> None:
    project = apply_ops(
        _seeded(1),
        [
            {
                "op": "add_clip",
                "args": {
                    "clip": _clip(
                        "b",
                        label="B roll",
                        track=2,
                        gain=0.5,
                        transition={"kind": "wipe", "duration_s": 0.7},
                    )
                },
            }
        ],
        clock=STAMP,
    )
    clip = project["clips"][1]
    assert clip["label"] == "B roll"
    assert clip["track"] == 2
    assert clip["gain"] == 0.5
    assert clip["transition"] == {"kind": "wipe", "duration_s": 0.7}


def test_add_clip_rejects_duplicate_id() -> None:
    with pytest.raises(TimelineError, match="clip id 'c0' already exists"):
        apply_ops(_seeded(1), [{"op": "add_clip", "args": {"clip": _clip("c0")}}])


@pytest.mark.parametrize("value", ["nope", 5, None, ["x"]])
def test_add_clip_rejects_non_object(value: Any) -> None:
    with pytest.raises(TimelineError, match="clip must be an object"):
        apply_ops(_seeded(0), [{"op": "add_clip", "args": {"clip": _raw(value)}}])


@pytest.mark.parametrize("key", ["id", "source", "in_s", "out_s"])
def test_add_clip_requires_core_fields(key: str) -> None:
    clip = _clip("a")
    del clip[key]
    with pytest.raises(TimelineError, match=f"clip missing '{key}'"):
        apply_ops(_seeded(0), [{"op": "add_clip", "args": {"clip": clip}}])


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"bogus": 1}, "unknown argument"),
        ({"id": ""}, "clip id must not be empty"),
        ({"id": 3}, "id must be a string"),
        ({"source": 3}, "source must be a string"),
        ({"label": 3}, "label must be a string"),
        ({"track": 1.5}, "track must be an integer"),
        ({"track": True}, "track must be an integer"),
        ({"track": -1}, "track must be >= 0"),
        ({"gain": "loud"}, "gain must be a number"),
        ({"gain": -0.1}, "gain must be >= 0"),
        ({"in_s": "0"}, "in_s must be a number"),
        ({"out_s": None}, "out_s must be a number"),
        ({"in_s": -1.0}, "in_s must be >= 0"),
        ({"in_s": 3.0, "out_s": 3.0}, "out_s must exceed in_s"),
        ({"in_s": 4.0, "out_s": 2.0}, "out_s must exceed in_s"),
        ({"source": ""}, "source must not be empty"),
        ({"source": "   "}, "source must not be empty"),
        ({"source": "clips\\a.mp4"}, "must use '/' separators"),
        ({"source": "/etc/passwd"}, "must be relative to the output dir"),
        ({"source": "clips/../../etc/passwd"}, "must not traverse upward"),
        ({"source": "~/secret.mp4"}, "must not use '~'"),
        ({"source": "clips/~x.mp4"}, "must not use '~'"),
    ],
)
def test_add_clip_rejects_bad_fields(overrides: dict[str, Any], fragment: str) -> None:
    with pytest.raises(TimelineError, match=fragment):
        apply_ops(_seeded(0), [{"op": "add_clip", "args": {"clip": _clip("a", **overrides)}}])


@pytest.mark.parametrize(
    ("transition", "fragment"),
    [
        ("fade", "transition must be an object"),
        ({}, "missing argument 'kind'"),
        ({"kind": "fade"}, "missing argument 'duration_s'"),
        ({"kind": "fade", "duration_s": 1.0, "extra": 1}, "unknown argument"),
        ({"kind": "dissolve", "duration_s": 1.0}, "kind must be one of"),
        ({"kind": 1, "duration_s": 1.0}, "kind must be a string"),
        ({"kind": "fade", "duration_s": "1"}, "duration_s must be a number"),
        ({"kind": "fade", "duration_s": 0}, "duration_s must be > 0 for fade"),
        ({"kind": "wipe", "duration_s": -1}, "duration_s must be > 0 for wipe"),
    ],
)
def test_add_clip_rejects_bad_nested_transition(
    transition: Any, fragment: str
) -> None:
    with pytest.raises(TimelineError, match=fragment):
        apply_ops(
            _seeded(0),
            [{"op": "add_clip", "args": {"clip": _clip("a", transition=_raw(transition))}}],
        )


def test_add_clip_cut_transition_forces_zero_duration() -> None:
    project = apply_ops(
        _seeded(0),
        [
            {
                "op": "add_clip",
                "args": {
                    "clip": _clip("a", transition={"kind": "cut", "duration_s": 4.0})
                },
            }
        ],
        clock=STAMP,
    )
    assert project["clips"][0]["transition"] == {"kind": "cut", "duration_s": 0.0}


# --- remove_clip -----------------------------------------------------------


def test_remove_clip_drops_the_row() -> None:
    project = apply_ops(
        _seeded(3), [{"op": "remove_clip", "args": {"clip_id": "c1"}}], clock=STAMP
    )
    assert [clip["id"] for clip in project["clips"]] == ["c0", "c2"]


@pytest.mark.parametrize(
    ("args", "fragment"),
    [
        ({}, "missing argument 'clip_id'"),
        ({"clip_id": 5}, "clip_id must be a string"),
        ({"clip_id": "nope"}, "unknown clip id 'nope'"),
        ({"clip_id": "c0", "junk": 1}, "unknown argument"),
    ],
)
def test_remove_clip_errors(args: dict[str, Any], fragment: str) -> None:
    with pytest.raises(TimelineError, match=fragment):
        apply_ops(_seeded(2), [{"op": "remove_clip", "args": _raw(args)}])


# --- trim_clip -------------------------------------------------------------


def test_trim_clip_moves_in_point_only() -> None:
    project = apply_ops(
        _seeded(1), [{"op": "trim_clip", "args": {"clip_id": "c0", "in_s": 1.0}}], clock=STAMP
    )
    assert (project["clips"][0]["in_s"], project["clips"][0]["out_s"]) == (1.0, 2.0)


def test_trim_clip_moves_out_point_only() -> None:
    project = apply_ops(
        _seeded(1), [{"op": "trim_clip", "args": {"clip_id": "c0", "out_s": 1.5}}], clock=STAMP
    )
    assert (project["clips"][0]["in_s"], project["clips"][0]["out_s"]) == (0.0, 1.5)


def test_trim_clip_moves_both_points() -> None:
    project = apply_ops(
        _seeded(1),
        [{"op": "trim_clip", "args": {"clip_id": "c0", "in_s": 0.5, "out_s": 1.5}}],
        clock=STAMP,
    )
    assert (project["clips"][0]["in_s"], project["clips"][0]["out_s"]) == (0.5, 1.5)


@pytest.mark.parametrize(
    ("args", "fragment"),
    [
        ({"clip_id": "c0"}, "pass in_s and/or out_s"),
        ({"in_s": 1.0}, "missing argument 'clip_id'"),
        ({"clip_id": "nope", "in_s": 1.0}, "unknown clip id 'nope'"),
        ({"clip_id": "c0", "in_s": "1"}, "in_s must be a number"),
        ({"clip_id": "c0", "out_s": True}, "out_s must be a number"),
        ({"clip_id": "c0", "in_s": -0.5}, "in_s must be >= 0"),
        ({"clip_id": "c0", "out_s": 0.0}, "out_s must exceed in_s"),
        ({"clip_id": "c0", "in_s": 1.0, "extra": 2}, "unknown argument"),
    ],
)
def test_trim_clip_errors(args: dict[str, Any], fragment: str) -> None:
    with pytest.raises(TimelineError, match=fragment):
        apply_ops(_seeded(1), [{"op": "trim_clip", "args": _raw(args)}])


# --- move_clip -------------------------------------------------------------


def test_move_clip_reorders_forward_and_backward() -> None:
    forward = apply_ops(
        _seeded(3), [{"op": "move_clip", "args": {"clip_id": "c2", "index": 0}}], clock=STAMP
    )
    assert [clip["id"] for clip in forward["clips"]] == ["c2", "c0", "c1"]
    backward = apply_ops(
        _seeded(3), [{"op": "move_clip", "args": {"clip_id": "c0", "index": 2}}], clock=STAMP
    )
    assert [clip["id"] for clip in backward["clips"]] == ["c1", "c2", "c0"]


def test_move_clip_to_its_own_index_is_a_no_op() -> None:
    project = apply_ops(
        _seeded(3), [{"op": "move_clip", "args": {"clip_id": "c1", "index": 1}}], clock=STAMP
    )
    assert [clip["id"] for clip in project["clips"]] == ["c0", "c1", "c2"]


@pytest.mark.parametrize(
    ("args", "fragment"),
    [
        ({"clip_id": "nope", "index": 0}, "unknown clip id 'nope'"),
        ({"clip_id": "c0"}, "missing argument 'index'"),
        ({"index": 0}, "missing argument 'clip_id'"),
        ({"clip_id": "c0", "index": -1}, "index -1 out of range 0..2"),
        ({"clip_id": "c0", "index": 3}, "index 3 out of range 0..2"),
        ({"clip_id": "c0", "index": 0.0}, "index must be an integer"),
        ({"clip_id": "c0", "index": True}, "index must be an integer"),
        ({"clip_id": 1, "index": 0}, "clip_id must be a string"),
        ({"clip_id": "c0", "index": 0, "junk": 1}, "unknown argument"),
    ],
)
def test_move_clip_errors(args: dict[str, Any], fragment: str) -> None:
    with pytest.raises(TimelineError, match=fragment):
        apply_ops(_seeded(3), [{"op": "move_clip", "args": _raw(args)}])


# --- set_track --------------------------------------------------------------


def test_set_track_moves_a_clip_onto_another_plane() -> None:
    project = apply_ops(
        _seeded(2),
        [{"op": "set_track", "args": {"clip_id": "c1", "track": 2}}],
        clock=STAMP,
    )
    assert [clip["track"] for clip in project["clips"]] == [0, 2]


def test_set_track_can_drop_a_clip_back_to_the_base_plane() -> None:
    raised = apply_ops(
        _seeded(1),
        [{"op": "set_track", "args": {"clip_id": "c0", "track": 3}}],
        clock=STAMP,
    )
    lowered = apply_ops(
        raised, [{"op": "set_track", "args": {"clip_id": "c0", "track": 0}}], clock=STAMP
    )
    assert lowered["clips"][0]["track"] == 0


def test_set_track_leaves_the_clip_order_alone() -> None:
    project = apply_ops(
        _seeded(3),
        [{"op": "set_track", "args": {"clip_id": "c0", "track": 1}}],
        clock=STAMP,
    )
    assert [clip["id"] for clip in project["clips"]] == ["c0", "c1", "c2"]


@pytest.mark.parametrize(
    ("args", "fragment"),
    [
        ({}, "missing argument 'clip_id'"),
        ({"clip_id": "nope", "track": 1}, "unknown clip id 'nope'"),
        ({"clip_id": "c0"}, "missing argument 'track'"),
        ({"clip_id": "c0", "track": -1}, "track must be >= 0"),
        ({"clip_id": "c0", "track": 1.5}, "track must be an integer"),
        ({"clip_id": "c0", "track": "1"}, "track must be an integer"),
        ({"clip_id": "c0", "track": True}, "track must be an integer"),
        ({"clip_id": "c0", "track": 1, "junk": 0}, "unknown argument"),
    ],
)
def test_set_track_errors(args: dict[str, Any], fragment: str) -> None:
    with pytest.raises(TimelineError, match=fragment):
        apply_ops(_seeded(2), [{"op": "set_track", "args": _raw(args)}])


# --- set_transition --------------------------------------------------------


def test_set_transition_sets_fade_on_a_later_clip() -> None:
    project = apply_ops(
        _seeded(2),
        [{"op": "set_transition", "args": {"clip_id": "c1", "kind": "fade", "duration_s": 0.4}}],
        clock=STAMP,
    )
    assert project["clips"][1]["transition"] == {"kind": "fade", "duration_s": 0.4}


def test_set_transition_cut_clears_the_duration() -> None:
    project = apply_ops(
        _seeded(2),
        [{"op": "set_transition", "args": {"clip_id": "c1", "kind": "cut", "duration_s": 9.0}}],
        clock=STAMP,
    )
    assert project["clips"][1]["transition"] == {"kind": "cut", "duration_s": 0.0}


@pytest.mark.parametrize(
    ("args", "fragment"),
    [
        ({"clip_id": "c0", "kind": "fade", "duration_s": 1.0}, "first clip has no entering transition"),
        ({"clip_id": "nope", "kind": "fade", "duration_s": 1.0}, "unknown clip id 'nope'"),
        ({"kind": "fade", "duration_s": 1.0}, "missing argument 'clip_id'"),
        ({"clip_id": "c1", "duration_s": 1.0}, "missing argument 'kind'"),
        ({"clip_id": "c1", "kind": "fade"}, "missing argument 'duration_s'"),
        ({"clip_id": "c1", "kind": "blur", "duration_s": 1.0}, "kind must be one of"),
        ({"clip_id": "c1", "kind": "fade", "duration_s": 0}, "duration_s must be > 0 for fade"),
        ({"clip_id": "c1", "kind": "fade", "duration_s": 1, "junk": 2}, "unknown argument"),
    ],
)
def test_set_transition_errors(args: dict[str, Any], fragment: str) -> None:
    with pytest.raises(TimelineError, match=fragment):
        apply_ops(_seeded(2), [{"op": "set_transition", "args": _raw(args)}])


# --- set_gain --------------------------------------------------------------


def test_set_gain_updates_one_clip() -> None:
    project = apply_ops(
        _seeded(2), [{"op": "set_gain", "args": {"clip_id": "c1", "gain": 0.25}}], clock=STAMP
    )
    assert project["clips"][1]["gain"] == 0.25
    assert project["clips"][0]["gain"] == 1.0


@pytest.mark.parametrize(
    ("args", "fragment"),
    [
        ({"clip_id": "c0"}, "missing argument 'gain'"),
        ({"gain": 1.0}, "missing argument 'clip_id'"),
        ({"clip_id": "nope", "gain": 1.0}, "unknown clip id 'nope'"),
        ({"clip_id": "c0", "gain": "1.0"}, "gain must be a number"),
        ({"clip_id": "c0", "gain": True}, "gain must be a number"),
        ({"clip_id": "c0", "gain": -0.5}, "gain must be >= 0"),
        ({"clip_id": "c0", "gain": 0}, None),
    ],
)
def test_set_gain_cases(args: dict[str, Any], fragment: str | None) -> None:
    if fragment is None:
        project = apply_ops(_seeded(1), [{"op": "set_gain", "args": _raw(args)}], clock=STAMP)
        assert project["clips"][0]["gain"] == 0.0
        return
    with pytest.raises(TimelineError, match=fragment):
        apply_ops(_seeded(1), [{"op": "set_gain", "args": _raw(args)}])


# --- overlays --------------------------------------------------------------


def test_add_text_overlay_fills_defaults() -> None:
    project = apply_ops(
        _seeded(0), [{"op": "add_overlay", "args": {"overlay": _overlay("o1")}}], clock=STAMP
    )
    assert project["overlays"] == [
        {
            "id": "o1",
            "kind": "text",
            "at_s": 0.0,
            "dur_s": 1.0,
            "text": "hello",
            "source": "",
            "x": 0.0,
            "y": 0.0,
            "size": 0.1,
        }
    ]


def test_add_image_overlay_with_layout() -> None:
    project = apply_ops(
        _seeded(0),
        [
            {
                "op": "add_overlay",
                "args": {
                    "overlay": _overlay(
                        "logo",
                        kind="image",
                        text="",
                        source="overlays/logo.png",
                        x=0.5,
                        y=0.25,
                        size=0.2,
                    )
                },
            }
        ],
        clock=STAMP,
    )
    assert project["overlays"][0]["source"] == "overlays/logo.png"
    assert (project["overlays"][0]["x"], project["overlays"][0]["size"]) == (0.5, 0.2)


def test_add_overlay_rejects_duplicate_id() -> None:
    with pytest.raises(TimelineError, match="overlay id 'o1' already exists"):
        apply_ops(
            _seeded(0),
            [
                {"op": "add_overlay", "args": {"overlay": _overlay("o1")}},
                {"op": "add_overlay", "args": {"overlay": _overlay("o1", text="again")}},
            ],
        )


@pytest.mark.parametrize("value", ["nope", 5, None, []])
def test_add_overlay_rejects_non_object(value: Any) -> None:
    with pytest.raises(TimelineError, match="overlay must be an object"):
        apply_ops(_seeded(0), [{"op": "add_overlay", "args": {"overlay": _raw(value)}}])


@pytest.mark.parametrize("key", ["id", "kind", "at_s", "dur_s"])
def test_add_overlay_requires_core_fields(key: str) -> None:
    overlay = _overlay("o1")
    del overlay[key]
    with pytest.raises(TimelineError, match=f"overlay missing '{key}'"):
        apply_ops(_seeded(0), [{"op": "add_overlay", "args": {"overlay": overlay}}])


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"bogus": 1}, "unknown argument"),
        ({"id": ""}, "overlay id must not be empty"),
        ({"id": 3}, "id must be a string"),
        ({"kind": 3}, "kind must be a string"),
        ({"kind": "sticker"}, "kind must be one of"),
        ({"at_s": "0"}, "at_s must be a number"),
        ({"at_s": -1.0}, "at_s must be >= 0"),
        ({"dur_s": "1"}, "dur_s must be a number"),
        ({"dur_s": 0}, "dur_s must be > 0"),
        ({"text": 3}, "text must be a string"),
        ({"source": 3}, "source must be a string"),
        ({"x": 1.5}, "x must be within 0..1"),
        ({"x": -0.1}, "x must be within 0..1"),
        ({"y": 2.0}, "y must be within 0..1"),
        ({"y": -0.5}, "y must be within 0..1"),
        ({"size": 0.0}, "size must be within 0..1"),
        ({"size": 1.5}, "size must be within 0..1"),
    ],
)
def test_add_overlay_rejects_bad_fields(
    overrides: dict[str, Any], fragment: str
) -> None:
    with pytest.raises(TimelineError, match=fragment):
        apply_ops(
            _seeded(0), [{"op": "add_overlay", "args": {"overlay": _overlay("o1", **overrides)}}]
        )


@pytest.mark.parametrize(
    ("overlay", "fragment"),
    [
        (_overlay("o", text=""), "text overlays need text"),
        (_overlay("o", text="   "), "text overlays need text"),
        (_overlay("o", source="overlays/a.png"), "text overlays must not carry source"),
        (
            {"id": "o", "kind": "image", "at_s": 0.0, "dur_s": 1.0},
            "image overlays need source",
        ),
        (
            {"id": "o", "kind": "image", "at_s": 0.0, "dur_s": 1.0, "source": "  "},
            "image overlays need source",
        ),
        (
            {
                "id": "o",
                "kind": "image",
                "at_s": 0.0,
                "dur_s": 1.0,
                "source": "a.png",
                "text": "hi",
            },
            "image overlays must not carry text",
        ),
        (
            {"id": "o", "kind": "image", "at_s": 0.0, "dur_s": 1.0, "source": "/a.png"},
            "must be relative to the output dir",
        ),
        (
            {"id": "o", "kind": "image", "at_s": 0.0, "dur_s": 1.0, "source": "../a.png"},
            "must not traverse upward",
        ),
        (
            {"id": "o", "kind": "image", "at_s": 0.0, "dur_s": 1.0, "source": "a\\b.png"},
            "must use '/' separators",
        ),
        (
            {"id": "o", "kind": "image", "at_s": 0.0, "dur_s": 1.0, "source": "~/a.png"},
            "must not use '~'",
        ),
    ],
)
def test_add_overlay_kind_payload_rules(overlay: dict[str, Any], fragment: str) -> None:
    with pytest.raises(TimelineError, match=fragment):
        apply_ops(_seeded(0), [{"op": "add_overlay", "args": {"overlay": _raw(overlay)}}])


def test_remove_overlay_drops_the_row() -> None:
    project = apply_ops(
        _seeded(0),
        [
            {"op": "add_overlay", "args": {"overlay": _overlay("o1")}},
            {"op": "add_overlay", "args": {"overlay": _overlay("o2")}},
            {"op": "remove_overlay", "args": {"overlay_id": "o1"}},
        ],
        clock=STAMP,
    )
    assert [row["id"] for row in project["overlays"]] == ["o2"]


@pytest.mark.parametrize(
    ("args", "fragment"),
    [
        ({}, "missing argument 'overlay_id'"),
        ({"overlay_id": 5}, "overlay_id must be a string"),
        ({"overlay_id": "nope"}, "unknown overlay id 'nope'"),
        ({"overlay_id": "o1", "junk": 1}, "unknown argument"),
    ],
)
def test_remove_overlay_errors(args: dict[str, Any], fragment: str) -> None:
    project = apply_ops(
        _seeded(0), [{"op": "add_overlay", "args": {"overlay": _overlay("o1")}}], clock=STAMP
    )
    with pytest.raises(TimelineError, match=fragment):
        apply_ops(project, [{"op": "remove_overlay", "args": _raw(args)}])


# --- captions --------------------------------------------------------------


def test_add_caption_appends_validated_row() -> None:
    project = apply_ops(
        _seeded(0), [{"op": "add_caption", "args": {"caption": _caption("k1")}}], clock=STAMP
    )
    assert project["captions"] == [
        {"id": "k1", "at_s": 0.5, "dur_s": 1.5, "text": "line one"}
    ]


def test_add_caption_rejects_duplicate_id() -> None:
    with pytest.raises(TimelineError, match="caption id 'k1' already exists"):
        apply_ops(
            _seeded(0),
            [
                {"op": "add_caption", "args": {"caption": _caption("k1")}},
                {"op": "add_caption", "args": {"caption": _caption("k1", text="again")}},
            ],
        )


@pytest.mark.parametrize("value", ["nope", 5, None, []])
def test_add_caption_rejects_non_object(value: Any) -> None:
    with pytest.raises(TimelineError, match="caption must be an object"):
        apply_ops(_seeded(0), [{"op": "add_caption", "args": {"caption": _raw(value)}}])


@pytest.mark.parametrize("key", ["id", "at_s", "dur_s", "text"])
def test_add_caption_requires_every_field(key: str) -> None:
    caption = _caption("k1")
    del caption[key]
    with pytest.raises(TimelineError, match=f"caption missing '{key}'"):
        apply_ops(_seeded(0), [{"op": "add_caption", "args": {"caption": caption}}])


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"bogus": 1}, "unknown argument"),
        ({"id": ""}, "caption id must not be empty"),
        ({"id": 3}, "id must be a string"),
        ({"text": 3}, "text must be a string"),
        ({"text": "   "}, "caption text must not be empty"),
        ({"at_s": "0.5"}, "at_s must be a number"),
        ({"at_s": -1.0}, "at_s must be >= 0"),
        ({"dur_s": "1.5"}, "dur_s must be a number"),
        ({"dur_s": 0.0}, "dur_s must be > 0"),
    ],
)
def test_add_caption_rejects_bad_fields(
    overrides: dict[str, Any], fragment: str
) -> None:
    with pytest.raises(TimelineError, match=fragment):
        apply_ops(
            _seeded(0), [{"op": "add_caption", "args": {"caption": _caption("k1", **overrides)}}]
        )


def test_remove_caption_drops_the_row() -> None:
    project = apply_ops(
        _seeded(0),
        [
            {"op": "add_caption", "args": {"caption": _caption("k1")}},
            {"op": "add_caption", "args": {"caption": _caption("k2")}},
            {"op": "remove_caption", "args": {"caption_id": "k2"}},
        ],
        clock=STAMP,
    )
    assert [row["id"] for row in project["captions"]] == ["k1"]


@pytest.mark.parametrize(
    ("args", "fragment"),
    [
        ({}, "missing argument 'caption_id'"),
        ({"caption_id": 5}, "caption_id must be a string"),
        ({"caption_id": "nope"}, "unknown caption id 'nope'"),
        ({"caption_id": "k1", "junk": 1}, "unknown argument"),
    ],
)
def test_remove_caption_errors(args: dict[str, Any], fragment: str) -> None:
    project = apply_ops(
        _seeded(0), [{"op": "add_caption", "args": {"caption": _caption("k1")}}], clock=STAMP
    )
    with pytest.raises(TimelineError, match=fragment):
        apply_ops(project, [{"op": "remove_caption", "args": _raw(args)}])


# --- set_title and clear ---------------------------------------------------


def test_set_title_updates_the_project() -> None:
    project = apply_ops(
        _seeded(0), [{"op": "set_title", "args": {"title": "Spring cut"}}], clock=STAMP
    )
    assert project["title"] == "Spring cut"


@pytest.mark.parametrize(
    ("args", "fragment"),
    [
        ({}, "missing argument 'title'"),
        ({"title": ""}, "title must not be empty"),
        ({"title": "   "}, "title must not be empty"),
        ({"title": 5}, "title must be a string"),
        ({"title": "x", "junk": 1}, "unknown argument"),
    ],
)
def test_set_title_errors(args: dict[str, Any], fragment: str) -> None:
    with pytest.raises(TimelineError, match=fragment):
        apply_ops(_seeded(0), [{"op": "set_title", "args": _raw(args)}])


def test_clear_drops_every_content_list() -> None:
    full = apply_ops(
        _seeded(2),
        [
            {"op": "add_overlay", "args": {"overlay": _overlay("o1")}},
            {"op": "add_caption", "args": {"caption": _caption("k1")}},
        ],
        clock=STAMP,
    )
    project = apply_ops(full, [{"op": "clear"}], clock=STAMP)
    assert project["clips"] == []
    assert project["overlays"] == []
    assert project["captions"] == []
    assert project["id"] == full["id"]
    assert project["title"] == full["title"]


def test_clear_refuses_arguments() -> None:
    with pytest.raises(TimelineError, match="unknown argument"):
        apply_ops(_seeded(1), [{"op": "clear", "args": {"keep": True}}])


# --- Multi-op stories ------------------------------------------------------


def test_multi_op_story_builds_a_whole_timeline() -> None:
    project = apply_ops(
        None,
        [
            {"op": "project_create", "args": {"id": "reel", "title": "Reel", "fps": 30.0}},
            {"op": "add_clip", "args": {"clip": _clip("a")}},
            {"op": "add_clip", "args": {"clip": _clip("b", gain=0.5)}},
            {"op": "add_clip", "args": {"clip": _clip("c", track=1)}},
            {"op": "move_clip", "args": {"clip_id": "c", "index": 0}},
            {"op": "trim_clip", "args": {"clip_id": "b", "in_s": 0.5, "out_s": 1.5}},
            {"op": "set_transition", "args": {"clip_id": "b", "kind": "fade", "duration_s": 0.3}},
            {"op": "set_gain", "args": {"clip_id": "a", "gain": 2.0}},
            {"op": "remove_clip", "args": {"clip_id": "c"}},
            {"op": "add_overlay", "args": {"overlay": _overlay("o1")}},
            {"op": "add_caption", "args": {"caption": _caption("k1")}},
            {"op": "set_title", "args": {"title": "Reel v2"}},
        ],
        clock=STAMP,
    )
    assert [clip["id"] for clip in project["clips"]] == ["a", "b"]
    assert project["clips"][1]["transition"] == {"kind": "fade", "duration_s": 0.3}
    assert project["clips"][1]["in_s"] == 0.5
    assert project["clips"][0]["gain"] == 2.0
    assert [row["id"] for row in project["overlays"]] == ["o1"]
    assert [row["id"] for row in project["captions"]] == ["k1"]
    assert project["title"] == "Reel v2"
    assert project["updated_at"] == STAMP


# --- Persistence -----------------------------------------------------------


def test_save_and_load_round_trip(tmp_path: Path) -> None:
    edit_dir = _edit_dir(tmp_path)
    project = apply_ops(
        None,
        [
            {"op": "project_create", "args": {"id": "p1", "title": "Reel"}},
            {"op": "add_clip", "args": {"clip": _clip("a")}},
            {"op": "add_overlay", "args": {"overlay": _overlay("o1")}},
            {"op": "add_caption", "args": {"caption": _caption("k1")}},
        ],
        clock=STAMP,
    )
    save_project(edit_dir, project)
    path = edit_dir / "projects" / "p1.json"
    assert path.is_file()
    assert list((edit_dir / "projects").glob("*.tmp")) == []
    assert json.loads(path.read_text(encoding="utf-8"))["id"] == "p1"
    assert load_project(edit_dir, "p1") == project


def test_save_project_drops_top_level_unknown_keys(tmp_path: Path) -> None:
    edit_dir = _edit_dir(tmp_path)
    project = _seeded(1)
    loose = json.loads(json.dumps(project))
    loose["surprise"] = "x"
    save_project(edit_dir, _raw(loose))
    assert load_project(edit_dir, "p1") == project


def test_save_project_refuses_unknown_keys_inside_a_row(tmp_path: Path) -> None:
    edit_dir = _edit_dir(tmp_path)
    loose = json.loads(json.dumps(_seeded(1)))
    loose["clips"][0]["surprise"] = "y"
    with pytest.raises(TimelineError, match="project clip: unknown argument"):
        save_project(edit_dir, _raw(loose))


@pytest.mark.parametrize(
    ("mutate", "fragment"),
    [
        (lambda p: p.pop("clips"), "clips must be a list"),
        (lambda p: p.__setitem__("clips", {}), "clips must be a list"),
        (lambda p: p.__setitem__("overlays", None), "overlays must be a list"),
        (lambda p: p.__setitem__("captions", "k"), "captions must be a list"),
        (lambda p: p.pop("id"), "missing argument 'id'"),
        (lambda p: p.__setitem__("id", "bad id"), "invalid project id"),
        (lambda p: p.__setitem__("id", 5), "id must be a string"),
        (lambda p: p.__setitem__("title", 5), "title must be a string"),
        (lambda p: p.__setitem__("fps", "30"), "fps must be a number"),
        (lambda p: p.__setitem__("width", "1920"), "width must be an integer"),
        (lambda p: p.__setitem__("height", None), "height must be an integer"),
        (lambda p: p.__setitem__("updated_at", 5), "updated_at must be a string"),
        (
            lambda p: p["clips"].append(json.loads(json.dumps(p["clips"][0]))),
            "duplicate clip id",
        ),
    ],
)
def test_save_project_refuses_malformed_records(
    tmp_path: Path, mutate: Any, fragment: str
) -> None:
    edit_dir = _edit_dir(tmp_path)
    project = _seeded(1)
    broken = json.loads(json.dumps(project))
    mutate(broken)
    with pytest.raises(TimelineError, match=fragment):
        save_project(edit_dir, _raw(broken))
    assert not (edit_dir / "projects" / "p1.json").exists()


def test_save_project_refuses_an_id_that_could_escape(tmp_path: Path) -> None:
    edit_dir = _edit_dir(tmp_path)
    for bad in ("../evil", "a/b", ""):
        project = _seeded(0)
        project["id"] = bad
        with pytest.raises(TimelineError, match="invalid project id"):
            save_project(edit_dir, project)
    assert not (edit_dir / "projects").exists()


def test_load_project_missing_file(tmp_path: Path) -> None:
    edit_dir = _edit_dir(tmp_path)
    with pytest.raises(TimelineError, match="missing project"):
        load_project(edit_dir, "ghost")


@pytest.mark.parametrize("bad_id", ["../escape", "a/b", "", " ", "caf\xe9", 7])
def test_load_project_refuses_bad_ids(tmp_path: Path, bad_id: Any) -> None:
    fragment = "id must be a string" if isinstance(bad_id, int) else "invalid project id"
    with pytest.raises(TimelineError, match=fragment):
        load_project(_edit_dir(tmp_path), _raw(bad_id))


def test_load_project_rejects_broken_json(tmp_path: Path) -> None:
    edit_dir = _edit_dir(tmp_path)
    path = edit_dir / "projects" / "p1.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(TimelineError, match="invalid project json"):
        load_project(edit_dir, "p1")


def test_load_project_rejects_non_utf8_bytes(tmp_path: Path) -> None:
    edit_dir = _edit_dir(tmp_path)
    path = edit_dir / "projects" / "p1.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xff\xfe{\x00")
    with pytest.raises(TimelineError, match="unreadable project file"):
        load_project(edit_dir, "p1")


@pytest.mark.parametrize(
    ("payload", "fragment"),
    [
        ("[]", "project must be an object"),
        ({"clips": {}}, "clips must be a list"),
        ({"clips": [], "overlays": {}}, "overlays must be a list"),
        ({"clips": [], "overlays": [], "captions": {}}, "captions must be a list"),
        ({"clips": [], "overlays": [], "captions": []}, "missing argument 'id'"),
        (
            {"id": "p1", "clips": [], "overlays": [], "captions": [], "fps": "x"},
            "fps must be a number",
        ),
        (
            {"id": "p1", "clips": [], "overlays": [], "captions": [], "width": 1.5},
            "width must be an integer",
        ),
        (
            {"id": "p1", "clips": [1], "overlays": [], "captions": []},
            "clip must be an object",
        ),
        (
            {
                "id": "p1",
                "clips": [],
                "overlays": [{"id": "o", "kind": "text", "at_s": 0, "dur_s": 1}],
                "captions": [],
            },
            "text overlays need text",
        ),
        (
            {
                "id": "p1",
                "clips": [],
                "overlays": [],
                "captions": [{"id": "k", "at_s": 0, "dur_s": 1, "text": "  "}],
            },
            "caption text must not be empty",
        ),
    ],
)
def test_load_project_rejects_malformed_records(
    tmp_path: Path, payload: Any, fragment: str
) -> None:
    edit_dir = _edit_dir(tmp_path)
    path = edit_dir / "projects" / "p1.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    text = payload if isinstance(payload, str) else json.dumps(payload)
    path.write_text(text, encoding="utf-8")
    with pytest.raises(TimelineError, match=fragment):
        load_project(edit_dir, "p1")


def test_load_project_accepts_a_minimal_record_and_fills_defaults(
    tmp_path: Path,
) -> None:
    edit_dir = _edit_dir(tmp_path)
    path = edit_dir / "projects" / "p1.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"id": "p1", "clips": [], "overlays": [], "captions": []}),
        encoding="utf-8",
    )
    project = load_project(edit_dir, "p1")
    assert project["title"] == ""
    assert project["fps"] == timeline.DEFAULT_FPS
    assert project["width"] == timeline.DEFAULT_WIDTH
    assert project["height"] == timeline.DEFAULT_HEIGHT
    assert project["updated_at"] == ""


def test_load_project_surfaces_row_validation_location(tmp_path: Path) -> None:
    edit_dir = _edit_dir(tmp_path)
    path = edit_dir / "projects" / "p1.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "id": "p1",
                "clips": [_clip("a", transition="fade")],
                "overlays": [],
                "captions": [],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(TimelineError, match="clip transition: transition must be"):
        load_project(edit_dir, "p1")


def test_project_index_empty_without_a_folder(tmp_path: Path) -> None:
    assert project_index(_edit_dir(tmp_path)) == []


def test_project_index_sorts_by_id_and_skips_other_files(tmp_path: Path) -> None:
    edit_dir = _edit_dir(tmp_path)
    for name in ("p2", "p1", "p10"):
        save_project(edit_dir, _seeded(1, project_id=name))
    (edit_dir / "projects" / "notes.txt").write_text("noise", encoding="utf-8")
    assert [project["id"] for project in project_index(edit_dir)] == ["p1", "p10", "p2"]


def test_project_index_refuses_a_corrupt_row(tmp_path: Path) -> None:
    edit_dir = _edit_dir(tmp_path)
    save_project(edit_dir, _seeded(1, project_id="p1"))
    (edit_dir / "projects" / "p2.json").write_text("[1,2", encoding="utf-8")
    with pytest.raises(TimelineError, match="invalid project json"):
        project_index(edit_dir)


def test_project_index_refuses_an_unreadable_row(tmp_path: Path) -> None:
    edit_dir = _edit_dir(tmp_path)
    save_project(edit_dir, _seeded(1, project_id="p1"))
    (edit_dir / "projects" / "p2.json").mkdir(parents=True)
    with pytest.raises(TimelineError, match="unreadable project file"):
        project_index(edit_dir)


def test_project_index_refuses_duplicate_row_ids(tmp_path: Path) -> None:
    edit_dir = _edit_dir(tmp_path)
    path = edit_dir / "projects"
    path.mkdir(parents=True)
    duplicate = json.loads(json.dumps(_seeded(2)))
    duplicate["overlays"] = [
        _overlay("o1"),
        _overlay("o2", text="other"),
    ]
    duplicate["overlays"][1]["id"] = "o1"
    duplicate["captions"] = [_caption("k1"), _caption("k1")]
    path.joinpath("p1.json").write_text(json.dumps(duplicate), encoding="utf-8")
    with pytest.raises(TimelineError, match="duplicate overlay id 'o1'"):
        project_index(edit_dir)
    duplicate["overlays"][1]["id"] = "o2"
    path.joinpath("p1.json").write_text(json.dumps(duplicate), encoding="utf-8")
    with pytest.raises(TimelineError, match="duplicate caption id 'k1'"):
        project_index(edit_dir)


def test_most_recent_none_without_projects(tmp_path: Path) -> None:
    assert most_recent(_edit_dir(tmp_path)) is None


def test_most_recent_picks_the_newest_stamp(tmp_path: Path) -> None:
    edit_dir = _edit_dir(tmp_path)
    stamps = {
        "p1": "2026-01-01T00:00:00+00:00",
        "p2": "2026-03-01T00:00:00+00:00",
        "p3": "2026-02-01T00:00:00+00:00",
    }
    for name, stamp in stamps.items():
        ops = [{"op": "project_create", "args": {"id": name}}]
        save_project(edit_dir, apply_ops(None, ops, clock=stamp))
    newest = most_recent(edit_dir)
    assert newest is not None
    assert newest["id"] == "p2"


def test_most_recent_breaks_stamp_ties_by_id(tmp_path: Path) -> None:
    edit_dir = _edit_dir(tmp_path)
    for name in ("aaa", "zzz"):
        ops = [{"op": "project_create", "args": {"id": name}}]
        save_project(edit_dir, apply_ops(None, ops, clock=STAMP))
    newest = most_recent(edit_dir)
    assert newest is not None
    assert newest["id"] == "zzz"
