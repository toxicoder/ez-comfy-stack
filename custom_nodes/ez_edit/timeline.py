"""Pure timeline reducer for the editing lane.

Every timeline mutation the agent or the browser panel can request goes
through :func:`apply_ops`: one ordered list of ``EditOp`` records in, one new
``EditProject`` out. The reducer never mutates its input, never touches the
network or the GPU, and stamps ``updated_at`` from an injected clock so tests
are deterministic. Persistence is one JSON file per project under
``<edit_dir>/projects/<id>.json``, written atomically (tmp + ``os.replace``).

Record shapes and vocabularies come from :mod:`ez_edit.protocol` (the pinned
seam) and are never redefined here; this module adds validation and storage
only. Path containment under ``${COMFY_OUTPUT_DIR}`` is enforced here only in
the pure, filesystem-free half (media paths must be relative and must not
traverse); the routes layer owns the on-disk containment check.
"""

from __future__ import annotations

import copy
import json
import os
import string
import uuid
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, TypeAlias, TypeVar, cast, get_args

from .protocol import (
    PROJECTS_SUBDIR,
    Caption,
    Clip,
    EditProject,
    Overlay,
    OverlayKind,
    OpName,
    Transition,
    TransitionKind,
)

if TYPE_CHECKING:
    from ez_common import Json, JsonMap

Clock: TypeAlias = Callable[[], datetime] | str
"""Injected time source: zero-arg callable returning a datetime, or a stamp."""

# --- Vocabularies derived from the pinned seam ------------------------------

OP_NAMES: frozenset[str] = frozenset(get_args(OpName))
"""Every op the reducer accepts (single source: ``protocol.OpName``)."""

TRANSITION_KINDS: frozenset[str] = frozenset(get_args(TransitionKind))
"""Accepted transition kinds (single source: ``protocol.TransitionKind``)."""

OVERLAY_KINDS: frozenset[str] = frozenset(get_args(OverlayKind))
"""Accepted overlay kinds (single source: ``protocol.OverlayKind``)."""

# --- Defaults ----------------------------------------------------------------

DEFAULT_TITLE = "Untitled edit"
"""Title used when ``project_create`` omits one."""

DEFAULT_FPS = 24.0
"""Frame rate used when ``project_create`` omits one."""

DEFAULT_WIDTH = 1920
"""Frame width used when ``project_create`` omits one."""

DEFAULT_HEIGHT = 1080
"""Frame height used when ``project_create`` omits one."""

ID_LENGTH = 12
"""Hex characters of ``uuid4`` used for a generated project id."""

ID_ALPHABET = "-_"
"""Extra characters allowed in a project id besides ASCII alphanumerics."""

ID_ALLOWED = frozenset(string.ascii_letters + string.digits + ID_ALPHABET)
"""Every character a project id may carry, so an id is always filename-safe."""

# --- Argument allow-lists ----------------------------------------------------
# An unknown key is a caller bug, not a hint: refusing it beats silently
# dropping an argument the agent believed it had set.

CREATE_KEYS = frozenset({"id", "title", "fps", "width", "height"})
"""Allowed ``project_create`` args."""

ADD_CLIP_KEYS = frozenset({"clip"})
"""Allowed ``add_clip`` args."""

CLIP_ID_KEYS = frozenset({"clip_id"})
"""Allowed ``remove_clip`` args."""

TRIM_KEYS = frozenset({"clip_id", "in_s", "out_s"})
"""Allowed ``trim_clip`` args."""

MOVE_KEYS = frozenset({"clip_id", "index"})
"""Allowed ``move_clip`` args."""

TRANSITION_KEYS = frozenset({"clip_id", "kind", "duration_s"})
"""Allowed ``set_transition`` args."""

GAIN_KEYS = frozenset({"clip_id", "gain"})
"""Allowed ``set_gain`` args."""

ADD_OVERLAY_KEYS = frozenset({"overlay"})
"""Allowed ``add_overlay`` args."""

OVERLAY_ID_KEYS = frozenset({"overlay_id"})
"""Allowed ``remove_overlay`` args."""

ADD_CAPTION_KEYS = frozenset({"caption"})
"""Allowed ``add_caption`` args."""

CAPTION_ID_KEYS = frozenset({"caption_id"})
"""Allowed ``remove_caption`` args."""

TITLE_KEYS = frozenset({"title"})
"""Allowed ``set_title`` args."""

CLEAR_KEYS: frozenset[str] = frozenset()
"""Allowed ``clear`` args (none)."""

CLIP_KEYS = frozenset(
    {"id", "source", "label", "in_s", "out_s", "track", "gain", "transition"}
)
"""Keys accepted inside a ``Clip`` argument."""

CLIP_REQUIRED = frozenset({"id", "source", "in_s", "out_s"})
"""Keys a ``Clip`` argument must carry (the rest have defaults)."""

NESTED_TRANSITION_KEYS = frozenset({"kind", "duration_s"})
"""Keys accepted inside a nested ``Transition``."""

OVERLAY_KEYS = frozenset(
    {"id", "kind", "at_s", "dur_s", "text", "source", "x", "y", "size"}
)
"""Keys accepted inside an ``Overlay`` argument."""

OVERLAY_REQUIRED = frozenset({"id", "kind", "at_s", "dur_s"})
"""Keys an ``Overlay`` argument must carry."""

CAPTION_KEYS = frozenset({"id", "at_s", "dur_s", "text"})
"""Keys accepted inside a ``Caption`` argument."""


class TimelineError(ValueError):
    """One op, id, or argument could not be applied to the project.

    Raised by :func:`apply_ops` and the loaders so a caller can catch one type
    and surface the message verbatim to the panel or the agent.
    """


_Row = TypeVar("_Row", bound=Mapping[str, object])
"""One record of a project row list (clip, overlay, or caption).

The list is mutated in place, so the helpers that filter it stay generic
instead of widening every caller to a common row type.
"""


# --- Small validators --------------------------------------------------------


def _require(value: Mapping[str, object], key: str, where: str) -> object:
    """Return ``value[key]`` or refuse.

    Args:
        value: Argument mapping.
        key: Required key.
        where: Human location used in the message.

    Returns:
        The stored value.

    Raises:
        TimelineError: When ``key`` is absent.
    """
    if key not in value:
        raise TimelineError(f"{where}: missing argument '{key}'")
    return value[key]


def _check_keys(
    value: Mapping[str, object], allowed: frozenset[str], where: str
) -> None:
    """Refuse unknown keys in one argument mapping.

    Args:
        value: Argument mapping.
        allowed: Keys the op accepts.
        where: Human location used in the message.

    Raises:
        TimelineError: When an unexpected key is present.
    """
    extra = sorted(str(key) for key in value if key not in allowed)
    if extra:
        raise TimelineError(f"{where}: unknown argument(s) {', '.join(extra)}")


def _as_str(value: object, field: str, where: str) -> str:
    """Coerce a required string argument.

    Args:
        value: Raw value.
        field: Field name for the message.
        where: Human location used in the message.

    Returns:
        The string value.

    Raises:
        TimelineError: When ``value`` is not a string.
    """
    if not isinstance(value, str):
        raise TimelineError(f"{where}: {field} must be a string (got {value!r})")
    return value


def _as_float(value: object, field: str, where: str) -> float:
    """Coerce a required numeric argument to ``float``.

    Args:
        value: Raw value.
        field: Field name for the message.
        where: Human location used in the message.

    Returns:
        The value as a float.

    Raises:
        TimelineError: When ``value`` is not a number (bools included).
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TimelineError(f"{where}: {field} must be a number (got {value!r})")
    return float(value)


def _as_int(value: object, field: str, where: str) -> int:
    """Coerce a required integer argument.

    Args:
        value: Raw value.
        field: Field name for the message.
        where: Human location used in the message.

    Returns:
        The value as an int.

    Raises:
        TimelineError: When ``value`` is not an int (bools included).
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise TimelineError(f"{where}: {field} must be an integer (got {value!r})")
    return int(value)


def _check_source(source: str, where: str) -> None:
    """Refuse absolute or traversing media paths without touching the disk.

    The routes layer resolves paths under ``${COMFY_OUTPUT_DIR}``; this is the
    pure half that keeps ``..``, ``~``, and absolute paths out of a stored
    project in the first place.

    Args:
        source: Media path as supplied by the caller.
        where: Human location used in the message.

    Raises:
        TimelineError: When the path is empty, absolute, traversing, or uses
            backslashes.
    """
    text = source.strip()
    if not text:
        raise TimelineError(f"{where}: source must not be empty")
    if "\\" in text:
        raise TimelineError(f"{where}: source must use '/' separators (got {source!r})")
    path = PurePosixPath(text)
    if path.is_absolute():
        raise TimelineError(f"{where}: source must be relative to the output dir")
    if ".." in path.parts:
        raise TimelineError(f"{where}: source must not traverse upward (got {source!r})")
    if any(part.startswith("~") for part in path.parts):
        raise TimelineError(f"{where}: source must not use '~' (got {source!r})")


def _check_window(in_s: float, out_s: float, where: str) -> None:
    """Validate a clip source window.

    Args:
        in_s: Source in-point seconds.
        out_s: Source out-point seconds.
        where: Human location used in the message.

    Raises:
        TimelineError: When ``in_s`` is negative or ``out_s`` does not exceed
            it.
    """
    if in_s < 0:
        raise TimelineError(f"{where}: in_s must be >= 0 (got {in_s})")
    if out_s <= in_s:
        raise TimelineError(
            f"{where}: out_s must exceed in_s (in_s={in_s}, out_s={out_s})"
        )


def _check_unit(value: float, field: str, where: str) -> None:
    """Require a normalized 0..1 layout coordinate.

    Args:
        value: Coordinate to check.
        field: Field name for the message.
        where: Human location used in the message.

    Raises:
        TimelineError: When the value falls outside 0..1.
    """
    if value < 0.0 or value > 1.0:
        raise TimelineError(f"{where}: {field} must be within 0..1 (got {value})")


def _safe_project_id(project_id: object, where: str) -> str:
    """Validate a project id before it becomes part of a filename.

    Args:
        project_id: Candidate id.
        where: Human location used in the message.

    Returns:
        The id as a string.

    Raises:
        TimelineError: When the id is empty or holds anything outside
            ``[A-Za-z0-9_-]``.
    """
    text = _as_str(project_id, "id", where)
    if not text or not all(ch in ID_ALLOWED for ch in text):
        raise TimelineError(f"{where}: invalid project id {project_id!r}")
    return text


def new_project_id() -> str:
    """Generate a short project id.

    Returns:
        Twelve hex characters from ``uuid4``.
    """
    return uuid.uuid4().hex[:ID_LENGTH]


def _stamp(clock: Clock | None) -> str:
    """Render the ``updated_at`` value for one apply.

    Args:
        clock: Literal stamp string, a zero-arg callable returning a datetime
            (naive datetimes read as UTC), or None for the wall clock.

    Returns:
        ISO-8601 UTC text.

    Raises:
        TimelineError: When a clock string is blank.
    """
    if isinstance(clock, str):
        text = clock.strip()
        if not text:
            raise TimelineError("clock: stamp string must not be empty")
        return text
    moment = clock() if clock is not None else datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).isoformat()


def _checked_shape(
    fps: object, width: object, height: object, where: str
) -> tuple[float, int, int]:
    """Coerce and range-check the project shape.

    Args:
        fps: Candidate frame rate.
        width: Candidate frame width.
        height: Candidate frame height.
        where: Human location used in the message.

    Returns:
        ``(fps, width, height)`` as number, int, int.

    Raises:
        TimelineError: When a value has the wrong type or is not positive.
    """
    checked_fps = _as_float(fps, "fps", where)
    checked_width = _as_int(width, "width", where)
    checked_height = _as_int(height, "height", where)
    if checked_fps <= 0:
        raise TimelineError(f"{where}: fps must be > 0 (got {checked_fps})")
    if checked_width <= 0:
        raise TimelineError(f"{where}: width must be > 0 (got {checked_width})")
    if checked_height <= 0:
        raise TimelineError(f"{where}: height must be > 0 (got {checked_height})")
    return checked_fps, checked_width, checked_height


def _shell(
    *,
    project_id: str,
    title: str,
    fps: float,
    width: int,
    height: int,
    updated_at: str,
) -> EditProject:
    """Build one project record with empty content lists.

    Args:
        project_id: Project id.
        title: Project title.
        fps: Frame rate.
        width: Frame width.
        height: Frame height.
        updated_at: ISO-8601 UTC stamp.

    Returns:
        New project record.
    """
    return {
        "id": project_id,
        "title": title,
        "fps": fps,
        "width": width,
        "height": height,
        "clips": [],
        "overlays": [],
        "captions": [],
        "updated_at": updated_at,
    }


def new_project(
    title: str = DEFAULT_TITLE,
    *,
    fps: float = DEFAULT_FPS,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    project_id: str = "",
    clock: Clock | None = None,
) -> EditProject:
    """Create a project record (no I/O).

    Args:
        title: Project title.
        fps: Frame rate; must be positive.
        width: Frame width in pixels; must be positive.
        height: Frame height in pixels; must be positive.
        project_id: Explicit id, or empty to generate ``uuid4`` hex.
        clock: Injected clock (see :func:`_stamp`).

    Returns:
        New project record with empty clips/overlays/captions.

    Raises:
        TimelineError: When a dimension is not positive or the id is unusable.
    """
    where = "project_create"
    checked_fps, checked_width, checked_height = _checked_shape(
        fps, width, height, where
    )
    pid = _safe_project_id(project_id, where) if project_id else new_project_id()
    return _shell(
        project_id=pid,
        title=_as_str(title, "title", where),
        fps=checked_fps,
        width=checked_width,
        height=checked_height,
        updated_at=_stamp(clock),
    )


def _transition_from(value: object, where: str) -> Transition:
    """Validate a nested transition record.

    Args:
        value: Raw transition value.
        where: Human location used in the message.

    Returns:
        Validated transition (``cut`` always carries a zero duration).

    Raises:
        TimelineError: When keys, kind, or duration are invalid.
    """
    if not isinstance(value, dict):
        raise TimelineError(f"{where}: transition must be an object")
    _check_keys(value, NESTED_TRANSITION_KEYS, where)
    kind = _as_str(_require(value, "kind", where), "kind", where)
    if kind not in TRANSITION_KINDS:
        raise TimelineError(f"{where}: kind must be one of {sorted(TRANSITION_KINDS)}")
    duration = _as_float(_require(value, "duration_s", where), "duration_s", where)
    if kind == "cut":
        duration = 0.0
    elif duration <= 0:
        raise TimelineError(f"{where}: duration_s must be > 0 for {kind}")
    return {"kind": cast(TransitionKind, kind), "duration_s": duration}


def _clip_from(value: object, where: str) -> Clip:
    """Validate a clip argument and fill optional fields.

    Args:
        value: Raw clip value.
        where: Human location used in the message.

    Returns:
        Validated clip.

    Raises:
        TimelineError: When a key, type, or range is invalid.
    """
    if not isinstance(value, dict):
        raise TimelineError(f"{where}: clip must be an object")
    _check_keys(value, CLIP_KEYS, where)
    for key in sorted(CLIP_REQUIRED):
        if key not in value:
            raise TimelineError(f"{where}: clip missing '{key}'")
    clip: Clip = {
        "id": _as_str(value["id"], "id", where),
        "source": _as_str(value["source"], "source", where),
        "label": _as_str(value.get("label", ""), "label", where),
        "in_s": _as_float(value["in_s"], "in_s", where),
        "out_s": _as_float(value["out_s"], "out_s", where),
        "track": _as_int(value.get("track", 0), "track", where),
        "gain": _as_float(value.get("gain", 1.0), "gain", where),
        "transition": None,
    }
    if not clip["id"]:
        raise TimelineError(f"{where}: clip id must not be empty")
    if clip["track"] < 0:
        raise TimelineError(f"{where}: track must be >= 0 (got {clip['track']})")
    if clip["gain"] < 0:
        raise TimelineError(f"{where}: gain must be >= 0 (got {clip['gain']})")
    _check_source(clip["source"], where)
    _check_window(clip["in_s"], clip["out_s"], where)
    raw = value.get("transition")
    if raw is not None:
        clip["transition"] = _transition_from(raw, f"{where} transition")
    return clip


def _overlay_from(value: object, where: str) -> Overlay:
    """Validate an overlay argument and fill optional fields.

    Args:
        value: Raw overlay value.
        where: Human location used in the message.

    Returns:
        Validated overlay.

    Raises:
        TimelineError: When a key, type, or range is invalid, or when the
            text/image payload disagrees with ``kind``.
    """
    if not isinstance(value, dict):
        raise TimelineError(f"{where}: overlay must be an object")
    _check_keys(value, OVERLAY_KEYS, where)
    for key in sorted(OVERLAY_REQUIRED):
        if key not in value:
            raise TimelineError(f"{where}: overlay missing '{key}'")
    kind = _as_str(value["kind"], "kind", where)
    if kind not in OVERLAY_KINDS:
        raise TimelineError(f"{where}: kind must be one of {sorted(OVERLAY_KINDS)}")
    overlay: Overlay = {
        "id": _as_str(value["id"], "id", where),
        "kind": cast(OverlayKind, kind),
        "at_s": _as_float(value["at_s"], "at_s", where),
        "dur_s": _as_float(value["dur_s"], "dur_s", where),
        "text": _as_str(value.get("text", ""), "text", where),
        "source": _as_str(value.get("source", ""), "source", where),
        "x": _as_float(value.get("x", 0.0), "x", where),
        "y": _as_float(value.get("y", 0.0), "y", where),
        "size": _as_float(value.get("size", 0.1), "size", where),
    }
    if not overlay["id"]:
        raise TimelineError(f"{where}: overlay id must not be empty")
    if overlay["at_s"] < 0:
        raise TimelineError(f"{where}: at_s must be >= 0 (got {overlay['at_s']})")
    if overlay["dur_s"] <= 0:
        raise TimelineError(f"{where}: dur_s must be > 0 (got {overlay['dur_s']})")
    _check_unit(overlay["x"], "x", where)
    _check_unit(overlay["y"], "y", where)
    if overlay["size"] <= 0 or overlay["size"] > 1:
        raise TimelineError(
            f"{where}: size must be within 0..1 (got {overlay['size']})"
        )
    if kind == "text":
        if not overlay["text"].strip():
            raise TimelineError(f"{where}: text overlays need text")
        if overlay["source"]:
            raise TimelineError(f"{where}: text overlays must not carry source")
    else:
        if not overlay["source"].strip():
            raise TimelineError(f"{where}: image overlays need source")
        if overlay["text"]:
            raise TimelineError(f"{where}: image overlays must not carry text")
        _check_source(overlay["source"], where)
    return overlay


def _caption_from(value: object, where: str) -> Caption:
    """Validate a caption argument.

    Args:
        value: Raw caption value.
        where: Human location used in the message.

    Returns:
        Validated caption.

    Raises:
        TimelineError: When a key, type, or range is invalid.
    """
    if not isinstance(value, dict):
        raise TimelineError(f"{where}: caption must be an object")
    _check_keys(value, CAPTION_KEYS, where)
    for key in sorted(CAPTION_KEYS):
        if key not in value:
            raise TimelineError(f"{where}: caption missing '{key}'")
    caption: Caption = {
        "id": _as_str(value["id"], "id", where),
        "at_s": _as_float(value["at_s"], "at_s", where),
        "dur_s": _as_float(value["dur_s"], "dur_s", where),
        "text": _as_str(value["text"], "text", where),
    }
    if not caption["id"]:
        raise TimelineError(f"{where}: caption id must not be empty")
    if not caption["text"].strip():
        raise TimelineError(f"{where}: caption text must not be empty")
    if caption["at_s"] < 0:
        raise TimelineError(f"{where}: at_s must be >= 0 (got {caption['at_s']})")
    if caption["dur_s"] <= 0:
        raise TimelineError(f"{where}: dur_s must be > 0 (got {caption['dur_s']})")
    return caption


def _clip_at(project: EditProject, clip_id: str, where: str) -> int:
    """Index of one clip by id.

    Args:
        project: Project being edited.
        clip_id: Clip id.
        where: Human location used in the message.

    Returns:
        Index into ``project["clips"]``.

    Raises:
        TimelineError: When no clip carries that id.
    """
    for index, clip in enumerate(project["clips"]):
        if clip["id"] == clip_id:
            return index
    raise TimelineError(f"{where}: unknown clip id {clip_id!r}")


def _drop_by_id(items: list[_Row], item_id: str, where: str, noun: str) -> None:
    """Remove one row by id, in place.

    Args:
        items: Rows to filter.
        item_id: Row id.
        where: Human location used in the message.
        noun: Row noun for the message.

    Raises:
        TimelineError: When no row carries that id.
    """
    for index, item in enumerate(items):
        if item.get("id") == item_id:
            del items[index]
            return
    raise TimelineError(f"{where}: unknown {noun} id {item_id!r}")


# --- Op handlers -------------------------------------------------------------


def _op_create(args: JsonMap, where: str) -> EditProject:
    """Handle ``project_create``.

    Args:
        args: Op arguments (already allow-listed by the dispatcher).
        where: Human location used in the message.

    Returns:
        Fresh project; ``updated_at`` is filled in by :func:`apply_ops`.

    Raises:
        TimelineError: When an argument is invalid.
    """
    _check_keys(args, CREATE_KEYS, where)
    pid = _safe_project_id(args["id"], where) if "id" in args else new_project_id()
    fps, width, height = _checked_shape(
        args.get("fps", DEFAULT_FPS),
        args.get("width", DEFAULT_WIDTH),
        args.get("height", DEFAULT_HEIGHT),
        where,
    )
    return _shell(
        project_id=pid,
        title=_as_str(args.get("title", DEFAULT_TITLE), "title", where),
        fps=fps,
        width=width,
        height=height,
        updated_at="",
    )


def _op_add_clip(project: EditProject, args: JsonMap, where: str) -> None:
    """Handle ``add_clip``.

    Args:
        project: Project mutated in place.
        args: Op arguments.
        where: Human location used in the message.

    Raises:
        TimelineError: When the clip is invalid or its id is taken.
    """
    _check_keys(args, ADD_CLIP_KEYS, where)
    clip = _clip_from(_require(args, "clip", where), f"{where} clip")
    if any(existing["id"] == clip["id"] for existing in project["clips"]):
        raise TimelineError(f"{where}: clip id {clip['id']!r} already exists")
    project["clips"].append(clip)


def _op_remove_clip(project: EditProject, args: JsonMap, where: str) -> None:
    """Handle ``remove_clip``.

    Args:
        project: Project mutated in place.
        args: Op arguments.
        where: Human location used in the message.

    Raises:
        TimelineError: When the id is unknown.
    """
    _check_keys(args, CLIP_ID_KEYS, where)
    _drop_by_id(
        project["clips"],
        _as_str(_require(args, "clip_id", where), "clip_id", where),
        where,
        "clip",
    )


def _op_trim_clip(project: EditProject, args: JsonMap, where: str) -> None:
    """Handle ``trim_clip`` (``in_s`` and/or ``out_s``).

    Args:
        project: Project mutated in place.
        args: Op arguments.
        where: Human location used in the message.

    Raises:
        TimelineError: When the id is unknown, neither bound is given, or the
            resulting window is invalid.
    """
    _check_keys(args, TRIM_KEYS, where)
    clip_id = _as_str(_require(args, "clip_id", where), "clip_id", where)
    clip = project["clips"][_clip_at(project, clip_id, where)]
    has_in = "in_s" in args
    has_out = "out_s" in args
    if not has_in and not has_out:
        raise TimelineError(f"{where}: pass in_s and/or out_s")
    in_s = _as_float(args["in_s"], "in_s", where) if has_in else clip["in_s"]
    out_s = _as_float(args["out_s"], "out_s", where) if has_out else clip["out_s"]
    _check_window(in_s, out_s, where)
    clip["in_s"] = in_s
    clip["out_s"] = out_s


def _op_move_clip(project: EditProject, args: JsonMap, where: str) -> None:
    """Handle ``move_clip`` (reorder the clip strip).

    Args:
        project: Project mutated in place.
        args: Op arguments.
        where: Human location used in the message.

    Raises:
        TimelineError: When the id is unknown or the index is out of bounds.
    """
    _check_keys(args, MOVE_KEYS, where)
    clip_id = _as_str(_require(args, "clip_id", where), "clip_id", where)
    index = _as_int(_require(args, "index", where), "index", where)
    clips = project["clips"]
    position = _clip_at(project, clip_id, where)
    last = len(clips) - 1
    if index < 0 or index > last:
        raise TimelineError(f"{where}: index {index} out of range 0..{last}")
    clips.insert(index, clips.pop(position))


def _op_set_transition(
    project: EditProject, args: JsonMap, where: str
) -> None:
    """Handle ``set_transition`` (the transition entering a clip).

    Args:
        project: Project mutated in place.
        args: Op arguments.
        where: Human location used in the message.

    Raises:
        TimelineError: When the id is unknown, the clip is first, the kind is
            outside the vocabulary, or the duration is invalid.
    """
    _check_keys(args, TRANSITION_KEYS, where)
    clip_id = _as_str(_require(args, "clip_id", where), "clip_id", where)
    position = _clip_at(project, clip_id, where)
    if position == 0:
        raise TimelineError(f"{where}: the first clip has no entering transition")
    kind = _require(args, "kind", where)
    duration = _require(args, "duration_s", where)
    project["clips"][position]["transition"] = _transition_from(
        {"kind": kind, "duration_s": duration}, f"{where} transition"
    )


def _op_set_gain(project: EditProject, args: JsonMap, where: str) -> None:
    """Handle ``set_gain``.

    Args:
        project: Project mutated in place.
        args: Op arguments.
        where: Human location used in the message.

    Raises:
        TimelineError: When the id is unknown or the gain is negative.
    """
    _check_keys(args, GAIN_KEYS, where)
    clip_id = _as_str(_require(args, "clip_id", where), "clip_id", where)
    clip = project["clips"][_clip_at(project, clip_id, where)]
    gain = _as_float(_require(args, "gain", where), "gain", where)
    if gain < 0:
        raise TimelineError(f"{where}: gain must be >= 0 (got {gain})")
    clip["gain"] = gain


def _op_add_overlay(project: EditProject, args: JsonMap, where: str) -> None:
    """Handle ``add_overlay``.

    Args:
        project: Project mutated in place.
        args: Op arguments.
        where: Human location used in the message.

    Raises:
        TimelineError: When the overlay is invalid or its id is taken.
    """
    _check_keys(args, ADD_OVERLAY_KEYS, where)
    overlay = _overlay_from(_require(args, "overlay", where), f"{where} overlay")
    if any(existing["id"] == overlay["id"] for existing in project["overlays"]):
        raise TimelineError(f"{where}: overlay id {overlay['id']!r} already exists")
    project["overlays"].append(overlay)


def _op_remove_overlay(
    project: EditProject, args: JsonMap, where: str
) -> None:
    """Handle ``remove_overlay``.

    Args:
        project: Project mutated in place.
        args: Op arguments.
        where: Human location used in the message.

    Raises:
        TimelineError: When the id is unknown.
    """
    _check_keys(args, OVERLAY_ID_KEYS, where)
    _drop_by_id(
        project["overlays"],
        _as_str(_require(args, "overlay_id", where), "overlay_id", where),
        where,
        "overlay",
    )


def _op_add_caption(project: EditProject, args: JsonMap, where: str) -> None:
    """Handle ``add_caption``.

    Args:
        project: Project mutated in place.
        args: Op arguments.
        where: Human location used in the message.

    Raises:
        TimelineError: When the caption is invalid or its id is taken.
    """
    _check_keys(args, ADD_CAPTION_KEYS, where)
    caption = _caption_from(_require(args, "caption", where), f"{where} caption")
    if any(existing["id"] == caption["id"] for existing in project["captions"]):
        raise TimelineError(f"{where}: caption id {caption['id']!r} already exists")
    project["captions"].append(caption)


def _op_remove_caption(
    project: EditProject, args: JsonMap, where: str
) -> None:
    """Handle ``remove_caption``.

    Args:
        project: Project mutated in place.
        args: Op arguments.
        where: Human location used in the message.

    Raises:
        TimelineError: When the id is unknown.
    """
    _check_keys(args, CAPTION_ID_KEYS, where)
    _drop_by_id(
        project["captions"],
        _as_str(_require(args, "caption_id", where), "caption_id", where),
        where,
        "caption",
    )


def _op_set_title(project: EditProject, args: JsonMap, where: str) -> None:
    """Handle ``set_title``.

    Args:
        project: Project mutated in place.
        args: Op arguments.
        where: Human location used in the message.

    Raises:
        TimelineError: When the title is missing, blank, or not a string.
    """
    _check_keys(args, TITLE_KEYS, where)
    title = _as_str(_require(args, "title", where), "title", where)
    if not title.strip():
        raise TimelineError(f"{where}: title must not be empty")
    project["title"] = title


def _op_clear(project: EditProject, args: JsonMap, where: str) -> None:
    """Handle ``clear`` (drop clips, overlays, and captions).

    Args:
        project: Project mutated in place.
        args: Op arguments (must be empty).
        where: Human location used in the message.

    Raises:
        TimelineError: When any argument is passed.
    """
    _check_keys(args, CLEAR_KEYS, where)
    project["clips"] = []
    project["overlays"] = []
    project["captions"] = []


HANDLERS: dict[str, Callable[[EditProject, JsonMap, str], None]] = {
    "add_clip": _op_add_clip,
    "remove_clip": _op_remove_clip,
    "trim_clip": _op_trim_clip,
    "move_clip": _op_move_clip,
    "set_transition": _op_set_transition,
    "set_gain": _op_set_gain,
    "add_overlay": _op_add_overlay,
    "remove_overlay": _op_remove_overlay,
    "add_caption": _op_add_caption,
    "remove_caption": _op_remove_caption,
    "set_title": _op_set_title,
    "clear": _op_clear,
}
"""Op name -> mutation for every non-creating op (``project_create`` is special:
it replaces the project instead of editing one)."""


def _apply_one(
    project: EditProject | None, op: object, *, position: int
) -> EditProject:
    """Apply a single op and return the project.

    Args:
        project: Current project, or None before ``project_create``.
        op: One op record.
        position: Index within the ops list (for messages).

    Returns:
        The project after the op.

    Raises:
        TimelineError: When the op, its args, or a referenced id is invalid.
    """
    where = f"ops[{position}]"
    if not isinstance(op, dict):
        raise TimelineError(f"{where}: op must be an object")
    name = _as_str(_require(op, "op", where), "op", where)
    if name not in OP_NAMES:
        raise TimelineError(f"{where}: unknown op {name!r}")
    raw_args = op.get("args")
    if raw_args is None:
        raw_args = {}
    if not isinstance(raw_args, dict):
        got = type(raw_args).__name__
        raise TimelineError(f"{where}: args must be an object (got {got})")
    args: JsonMap = dict(raw_args)
    if name == "project_create":
        if project is not None:
            raise TimelineError(
                f"{where}: project_create needs no existing project"
            )
        return _op_create(args, where)
    if project is None:
        raise TimelineError(
            f"{where}: no project - start the list with project_create"
        )
    HANDLERS[name](project, args, where)
    return project


def apply_ops(
    project: EditProject | None,
    ops: Sequence[object],
    *,
    clock: Clock | None = None,
) -> EditProject:
    """Apply an ordered op list to a project (pure: the input is not mutated).

    Args:
        project: Project to edit, or None when the list starts with
            ``project_create``.
        ops: Ordered ``{"op": ..., "args": {...}}`` records.
        clock: Injected clock (see :func:`_stamp`).

    Returns:
        New project record stamped with ``updated_at``.

    Raises:
        TimelineError: When any op, id, or argument is invalid, or the list
            never creates a project.
    """
    result = copy.deepcopy(project) if project is not None else None
    for position, op in enumerate(ops):
        result = _apply_one(result, op, position=position)
    if result is None:
        raise TimelineError("ops: empty list with no project to edit")
    result["updated_at"] = _stamp(clock)
    return result


# --- Persistence -------------------------------------------------------------


def _projects_dir(edit_dir: Path) -> Path:
    """``<edit_dir>/projects``.

    Args:
        edit_dir: Edit root (``${COMFY_OUTPUT_DIR}/edit``).

    Returns:
        Projects directory path.
    """
    return Path(edit_dir) / PROJECTS_SUBDIR


def _project_path(edit_dir: Path, project_id: str) -> Path:
    """``<edit_dir>/projects/<id>.json``.

    Args:
        edit_dir: Edit root.
        project_id: Project id.

    Returns:
        Project file path.

    Raises:
        TimelineError: When the id could escape the projects directory.
    """
    safe = _safe_project_id(project_id, "project")
    return _projects_dir(edit_dir) / f"{safe}.json"


def _require_unique_ids(rows: list[_Row], where: str, noun: str) -> None:
    """Refuse duplicate ids within one row list.

    Args:
        rows: Validated rows of one kind.
        where: Human location used in the message.
        noun: Row noun for the message.

    Raises:
        TimelineError: When two rows share an id.
    """
    seen: set[str] = set()
    for row in rows:
        row_id = str(row["id"])
        if row_id in seen:
            raise TimelineError(f"{where}: duplicate {noun} id {row_id!r}")
        seen.add(row_id)


def _project_from(data: object, where: str) -> EditProject:
    """Validate one parsed project record.

    Args:
        data: Parsed JSON value.
        where: Human location used in the message.

    Returns:
        Rebuilt project record (unknown keys are dropped).

    Raises:
        TimelineError: When the record is not a usable project.
    """
    if not isinstance(data, dict):
        raise TimelineError(f"{where}: project must be an object")
    clips_value = data.get("clips")
    overlays_value = data.get("overlays")
    captions_value = data.get("captions")
    if not isinstance(clips_value, list):
        raise TimelineError(f"{where}: clips must be a list")
    if not isinstance(overlays_value, list):
        raise TimelineError(f"{where}: overlays must be a list")
    if not isinstance(captions_value, list):
        raise TimelineError(f"{where}: captions must be a list")
    project_id = _safe_project_id(_require(data, "id", where), where)
    clips = [_clip_from(clip, f"{where} clip") for clip in clips_value]
    _require_unique_ids(clips, where, "clip")
    overlays: list[Overlay] = [
        _overlay_from(overlay, f"{where} overlay") for overlay in overlays_value
    ]
    _require_unique_ids(overlays, where, "overlay")
    captions: list[Caption] = [
        _caption_from(caption, f"{where} caption") for caption in captions_value
    ]
    _require_unique_ids(captions, where, "caption")
    project = _shell(
        project_id=project_id,
        title=_as_str(data.get("title", ""), "title", where),
        fps=_as_float(data.get("fps", DEFAULT_FPS), "fps", where),
        width=_as_int(data.get("width", DEFAULT_WIDTH), "width", where),
        height=_as_int(data.get("height", DEFAULT_HEIGHT), "height", where),
        updated_at=_as_str(data.get("updated_at", ""), "updated_at", where),
    )
    project["clips"] = clips
    project["overlays"] = overlays
    project["captions"] = captions
    return project


def save_project(edit_dir: Path, project: EditProject) -> None:
    """Write one project atomically (tmp file plus ``os.replace``).

    The record is revalidated on the way out, so a malformed project can never
    reach disk.

    Args:
        edit_dir: Edit root.
        project: Project record to persist.

    Raises:
        TimelineError: When the record is not a usable project.
    """
    rebuilt = _project_from(project, "project")
    path = _project_path(edit_dir, rebuilt["id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(
        json.dumps(rebuilt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(tmp, path)


def load_project(edit_dir: Path, project_id: str) -> EditProject:
    """Read one project file.

    Args:
        edit_dir: Edit root.
        project_id: Project id.

    Returns:
        Validated project record.

    Raises:
        TimelineError: When the file is missing, unparsable, or malformed.
    """
    path = _project_path(edit_dir, project_id)
    if not path.is_file():
        raise TimelineError(f"missing project {path}")
    return _read_project_file(path, f"project {project_id}")


def _read_project_file(path: Path, where: str) -> EditProject:
    """Parse and validate one project JSON file.

    Args:
        path: Project file.
        where: Human location used in the message.

    Returns:
        Validated project record.

    Raises:
        TimelineError: When the JSON is broken, the file cannot be read as
            UTF-8 text, or the record is malformed.
    """
    try:
        data: Json = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TimelineError(f"invalid project json {path}: {exc}") from exc
    except (OSError, UnicodeDecodeError) as exc:
        raise TimelineError(f"unreadable project file {path}: {exc}") from exc
    return _project_from(data, where)


def project_index(edit_dir: Path) -> list[EditProject]:
    """Every stored project, sorted by file name (hence by id).

    Args:
        edit_dir: Edit root.

    Returns:
        Validated project records (empty when nothing is stored yet).

    Raises:
        TimelineError: When any project file is unparsable or malformed.
    """
    folder = _projects_dir(edit_dir)
    if not folder.is_dir():
        return []
    return [
        _read_project_file(path, f"project {path.name}")
        for path in sorted(folder.glob("*.json"))
    ]


def most_recent(edit_dir: Path) -> EditProject | None:
    """Project with the newest ``updated_at`` (the panel's default view).

    Args:
        edit_dir: Edit root.

    Returns:
        Newest project, or None when the index is empty.
    """
    projects = project_index(edit_dir)
    if not projects:
        return None
    return max(projects, key=lambda item: (item["updated_at"], item["id"]))
