"""Render jobstore for the editing lane: ``edit/jobs/<job_id>.json``.

Rows follow the :data:`~ez_edit.protocol.JobState` lifecycle
``pending -> running -> ok/failed`` on the same file-per-job shape as
``ez_film.jobstore``. Server rows run exactly one ffmpeg argv (built by
:func:`ez_edit.edl.ffmpeg_command`) through the injected
:class:`~ez_common.protocols.SubprocessRunner`; a missing ffmpeg fails the row
with a message that names the binary. Client rows are handed to the open
browser panel and stay ``pending`` until :func:`claim_next_client_job` and
:func:`complete_client_job` move them.

Subprocess, PATH lookup, and clock are all injectable, so tests never touch
ffmpeg or the wall clock.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import uuid
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast, get_args

from ez_common.protocols import CompletedProc, SubprocessRunner

from .edl import ffmpeg_command
from .protocol import (
    JOBS_SUBDIR,
    OUTPUTS_SUBDIR,
    Clip,
    EditProject,
    ExecMode,
    JobKind,
    JobRecord,
    JobState,
)

JOB_STATES: tuple[JobState, ...] = get_args(JobState)
"""Runtime vocabulary for the row lifecycle."""

EXEC_MODES: tuple[ExecMode, ...] = get_args(ExecMode)
"""Runtime vocabulary for where a render runs."""

SERVER_KIND: JobKind = "render_server"
"""Row kind for an on-Spark ffmpeg render."""

CLIENT_KIND: JobKind = "exec_client"
"""Row kind for a browser WebCodecs render."""

MISSING_FFMPEG_MESSAGE = (
    "ffmpeg not found on PATH - install ffmpeg in the Comfy image "
    "(apt-get install -y ffmpeg) or render in client mode"
)
"""Failed-row message when the PATH lookup finds no ffmpeg."""

CLIENT_WAIT_MESSAGE = "queued for the browser panel (WebCodecs)"
"""Pending-row message for a client-mode render."""

CLIENT_ID_MESSAGE = "client render needs a client_id to be claimed"
"""Failed-row message for a client render with no owner."""

RUNNING_MESSAGE = "rendering"
"""Running-row message for a server render."""

CLAIMED_MESSAGE = "claimed by the browser panel"
"""Running-row message once a browser claims a client render."""

OUTPUT_TAIL_CHARS = 240
"""How much ffmpeg stderr is kept in a failure message."""

SLUG_RE = re.compile(r"[^a-zA-Z0-9._-]+")
"""Characters not allowed in a row id or filename segment."""


def _stamp(now: Callable[[], str] | None) -> str:
    """Current UTC ISO-8601 stamp, or the injected clock.

    Args:
        now: Clock callable, or ``None`` for the real clock.

    Returns:
        ISO-8601 UTC timestamp.
    """
    if now is not None:
        return now()
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _slug(value: object, default: str) -> str:
    """Keep an id usable as a filename segment.

    Args:
        value: Candidate id.
        default: Fallback when empty after sanitizing.

    Returns:
        Safe, non-empty segment.
    """
    cleaned = SLUG_RE.sub("-", str(value or "").strip()).strip(".-")
    return cleaned or default


def jobs_dir(edit_dir: Path | str) -> Path:
    """``<edit_dir>/jobs`` directory.

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.

    Returns:
        Jobstore directory path.
    """
    return Path(edit_dir) / JOBS_SUBDIR


def job_path(edit_dir: Path | str, job_id: str) -> Path:
    """``<edit_dir>/jobs/<job_id>.json``.

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.
        job_id: Row id.

    Returns:
        Row file path (not necessarily created).
    """
    return jobs_dir(edit_dir) / f"{_slug(job_id, 'job')}.json"


def renders_dir(edit_dir: Path | str) -> Path:
    """``<edit_dir>/renders`` directory.

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.

    Returns:
        Renders directory path.
    """
    return Path(edit_dir) / OUTPUTS_SUBDIR


def render_path(edit_dir: Path | str, project_id: str, job_id: str) -> Path:
    """``<edit_dir>/renders/<project_id>-<job_id>.mp4``.

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.
        project_id: Project id.
        job_id: Row id.

    Returns:
        Server mp4 path.
    """
    name = f"{_slug(project_id, 'project')}-{_slug(job_id, 'job')}.mp4"
    return renders_dir(edit_dir) / name


def _as_row(data: Mapping[str, Any]) -> JobRecord:
    """Coerce a parsed row file into a :class:`~ez_edit.protocol.JobRecord`.

    Args:
        data: Parsed JSON object.

    Returns:
        Row record with every field present and stringified.
    """
    return JobRecord(
        id=str(data.get("id") or ""),
        kind=cast(JobKind, str(data.get("kind") or SERVER_KIND)),
        project_id=str(data.get("project_id") or ""),
        state=cast(JobState, str(data.get("state") or "pending")),
        mode=cast(ExecMode, str(data.get("mode") or "server")),
        message=str(data.get("message") or ""),
        out_path=str(data.get("out_path") or ""),
        created_at=str(data.get("created_at") or ""),
        updated_at=str(data.get("updated_at") or ""),
        client_id=str(data.get("client_id") or ""),
    )


def write_job(edit_dir: Path | str, row: JobRecord) -> None:
    """Persist one row (temp file + replace, like the film jobstore).

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.
        row: Row to serialize.
    """
    folder = jobs_dir(edit_dir)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{_slug(row['id'], 'job')}.json"
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def read_job(edit_dir: Path | str, job_id: str) -> JobRecord:
    """Read one row.

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.
        job_id: Row id.

    Returns:
        Row record.

    Raises:
        FileNotFoundError: No such row file.
        ValueError: Row file is not a JSON object with an id.
    """
    path = job_path(edit_dir, job_id)
    if not path.is_file():
        raise FileNotFoundError(f"missing edit job {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not data.get("id"):
        raise ValueError(f"invalid edit job {path}")
    return _as_row(data)


def list_jobs(edit_dir: Path | str, project_id: str = "") -> list[JobRecord]:
    """Read every row, oldest first, optionally one project only.

    Unreadable or malformed row files are skipped rather than failing the
    listing (a half-written row must not hide the rest).

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.
        project_id: Filter, or ``""`` for all projects.

    Returns:
        Rows sorted by ``created_at`` then id.
    """
    folder = jobs_dir(edit_dir)
    if not folder.is_dir():
        return []
    rows: list[JobRecord] = []
    for path in sorted(folder.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict):
            continue
        row = _as_row(data)
        if project_id and row["project_id"] != project_id:
            continue
        rows.append(row)
    return sorted(rows, key=lambda row: (row["created_at"], row["id"]))


def tick_job(
    edit_dir: Path | str,
    job_id: str,
    *,
    state: JobState | None = None,
    message: str = "",
    out_path: str | None = None,
    now: Callable[[], str] | None = None,
) -> JobRecord:
    """Advance one row and persist it.

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.
        job_id: Row id.
        state: New state, or ``None`` to leave it.
        message: Progress or failure line (empty keeps the old one).
        out_path: Rendered path (``None`` keeps the old one).
        now: Clock callable.

    Returns:
        Updated row.

    Raises:
        FileNotFoundError: No such row.
        ValueError: ``state`` is outside the vocabulary.
    """
    row = read_job(edit_dir, job_id)
    if state is not None:
        if state not in JOB_STATES:
            raise ValueError(f"bad job state {state!r}")
        row["state"] = state
    if message:
        row["message"] = message
    if out_path is not None:
        row["out_path"] = out_path
    row["updated_at"] = _stamp(now)
    write_job(edit_dir, row)
    return row


def _new_row(
    *,
    project_id: str,
    kind: JobKind,
    mode: ExecMode,
    client_id: str,
    message: str,
    now: Callable[[], str] | None,
) -> JobRecord:
    """Fresh pending row.

    Args:
        project_id: Project the row belongs to.
        kind: Row kind.
        mode: Where the render runs.
        client_id: Browser owner (empty for server rows).
        message: Pending message.
        now: Clock callable.

    Returns:
        Pending row (id from ``uuid4``).
    """
    stamp = _stamp(now)
    return JobRecord(
        id=uuid.uuid4().hex[:12],
        kind=kind,
        project_id=project_id,
        state="pending",
        mode=mode,
        message=message,
        out_path="",
        created_at=stamp,
        updated_at=stamp,
        client_id=client_id,
    )


def _count(project: Mapping[str, Any], field: str) -> int:
    """Size of a project list field, tolerating junk.

    Args:
        project: Edit project record.
        field: Field name.

    Returns:
        Entry count (0 when missing or not a list).
    """
    raw = project.get(field)
    return len(raw) if isinstance(raw, (list, tuple)) else 0


def _deferred_text_planes(project: Mapping[str, Any]) -> str:
    """Message suffix naming the text planes the browser draws.

    Args:
        project: Edit project record.

    Returns:
        ``"; 2 text planes render in client mode"`` or an empty string.
    """
    planes = _count(project, "overlays") + _count(project, "captions")
    if not planes:
        return ""
    return f"; {planes} text planes render in client mode"


def _safe_source(raw: object, root: Path) -> Path:
    """Resolve a clip source inside the Comfy output root.

    Args:
        raw: Source value from the project.
        root: ``${COMFY_OUTPUT_DIR}`` (parent of the edit dir).

    Returns:
        Absolute path under ``root``.

    Raises:
        ValueError: Empty source, or it escapes ``root``.
    """
    text = str(raw or "").strip()
    if not text:
        raise ValueError("clip has no source")
    candidate = Path(text)
    if not candidate.is_absolute():
        candidate = root / candidate
    base = Path(root).resolve()
    resolved = candidate.resolve()
    if base not in resolved.parents:
        raise ValueError(f"clip source {text} is outside {base}")
    return resolved


def _vetted_project(project: Mapping[str, Any], root: Path) -> EditProject:
    """Copy a project with every clip source resolved inside ``root``.

    Args:
        project: Edit project record.
        root: ``${COMFY_OUTPUT_DIR}`` (parent of the edit dir).

    Returns:
        Project copy whose clip sources are absolute and vetted.

    Raises:
        ValueError: A clip is not a mapping or its source escapes ``root``.
    """
    raw_clips = project.get("clips")
    entries = list(raw_clips) if isinstance(raw_clips, (list, tuple)) else []
    clips: list[Clip] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise ValueError("clip must be a mapping")
        clip = dict(entry)
        clip["source"] = str(_safe_source(entry.get("source"), root))
        clips.append(cast(Clip, clip))
    out: dict[str, Any] = dict(project)
    out["clips"] = clips
    return cast(EditProject, out)


def _proc_tail(proc: object) -> str:
    """Last lines of ffmpeg output, whitespace-collapsed.

    Args:
        proc: Completed-process-shaped object.

    Returns:
        Short failure detail for the row message.
    """
    text = str(getattr(proc, "stderr", "") or getattr(proc, "stdout", "") or "")
    flat = " ".join(text.split())
    return flat[-OUTPUT_TAIL_CHARS:] if flat else "no output"


def _default_runner(
    argv: list[str],
    *,
    check: bool,
    capture_output: bool,
    text: bool,
) -> CompletedProc:
    """Call the real ``subprocess.run`` through the seam.

    The ``subprocess.run`` overload set is wider than the seam, so this
    adapter pins the text-mode shape once for mypy and pyright.

    Args:
        argv: Command vector.
        check: Raise on non-zero.
        capture_output: Capture stdout/stderr.
        text: Decode as text.

    Returns:
        Completed process with text-mode fields.
    """
    return cast(
        CompletedProc,
        subprocess.run(argv, check=check, capture_output=capture_output, text=text),
    )


def _run_server_render(
    edit_dir: Path | str,
    project: Mapping[str, Any],
    job_id: str,
    *,
    runner: SubprocessRunner | None,
    which: Callable[[str], str | None],
    now: Callable[[], str] | None,
) -> JobRecord:
    """Run one server ffmpeg render and land the row.

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.
        project: Edit project record.
        job_id: Row id (already persisted as pending).
        runner: ``subprocess.run`` seam, or ``None`` for the real one.
        which: PATH lookup.
        now: Clock callable.

    Returns:
        Final row (``ok`` or ``failed``).
    """
    row = tick_job(edit_dir, job_id, state="running", message=RUNNING_MESSAGE, now=now)
    ffmpeg_bin = which("ffmpeg")
    if not ffmpeg_bin:
        return tick_job(
            edit_dir,
            job_id,
            state="failed",
            message=MISSING_FFMPEG_MESSAGE,
            now=now,
        )
    out = render_path(edit_dir, row["project_id"], job_id)
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        vetted = _vetted_project(project, Path(edit_dir).resolve().parent)
        argv = ffmpeg_command(vetted, out, ffmpeg_bin=ffmpeg_bin)
        run: SubprocessRunner = runner if runner is not None else _default_runner
        proc = run(argv, check=False, capture_output=True, text=True)
    except (ValueError, OSError) as exc:
        return tick_job(
            edit_dir,
            job_id,
            state="failed",
            message=f"{type(exc).__name__}: {exc}",
            now=now,
        )
    returncode = int(getattr(proc, "returncode", 1) or 0)
    if returncode != 0:
        return tick_job(
            edit_dir,
            job_id,
            state="failed",
            message=f"ffmpeg exited {returncode}: {_proc_tail(proc)}",
            now=now,
        )
    if not out.is_file():
        return tick_job(
            edit_dir,
            job_id,
            state="failed",
            message=f"ffmpeg produced no output at {out}",
            now=now,
        )
    note = _deferred_text_planes(project)
    relative = out.relative_to(Path(edit_dir).resolve()).as_posix()
    return tick_job(
        edit_dir,
        job_id,
        state="ok",
        message=f"rendered {_count(project, 'clips')} clips{note}",
        out_path=relative,
        now=now,
    )


def start_render(
    edit_dir: Path | str,
    project: Mapping[str, Any],
    *,
    mode: ExecMode,
    client_id: str = "",
    runner: SubprocessRunner | None = None,
    which: Callable[[str], str | None] = shutil.which,
    now: Callable[[], str] | None = None,
) -> JobRecord:
    """Open a render row and (server mode) run it to completion.

    Server mode writes ``pending -> running -> ok/failed`` and invokes ffmpeg
    once through ``runner``. Client mode writes a pending row for the browser
    panel and never touches ffmpeg; without a ``client_id`` nothing can claim
    it, so the row fails with that reason.

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.
        project: Edit project record.
        mode: ``server`` or ``client``.
        client_id: Browser exec queue owner (client mode).
        runner: ``subprocess.run`` seam (tests inject a fake).
        which: PATH lookup for ffmpeg (tests inject a fake).
        now: Clock callable (tests inject a fixed stamp).

    Returns:
        The row as written (final state for server mode).

    Raises:
        ValueError: ``mode`` is outside the vocabulary.
    """
    if mode not in EXEC_MODES:
        raise ValueError(f"bad render mode {mode!r}")
    project_id = str(project.get("id") or "")
    if mode == "client":
        row = _new_row(
            project_id=project_id,
            kind=CLIENT_KIND,
            mode=mode,
            client_id=client_id,
            message=CLIENT_WAIT_MESSAGE,
            now=now,
        )
        write_job(edit_dir, row)
        if not client_id:
            return tick_job(
                edit_dir, row["id"], state="failed", message=CLIENT_ID_MESSAGE, now=now
            )
        return row
    row = _new_row(
        project_id=project_id,
        kind=SERVER_KIND,
        mode=mode,
        client_id=client_id,
        message="",
        now=now,
    )
    write_job(edit_dir, row)
    return _run_server_render(
        edit_dir,
        project,
        row["id"],
        runner=runner,
        which=which,
        now=now,
    )


def claim_next_client_job(edit_dir: Path | str, client_id: str) -> JobRecord | None:
    """Claim the oldest pending client row for one browser.

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.
        client_id: Browser queue owner.

    Returns:
        The row, now ``running``, or ``None`` when the queue is empty.
    """
    if not client_id:
        return None
    for row in list_jobs(edit_dir):
        if (
            row["kind"] == CLIENT_KIND
            and row["state"] == "pending"
            and row["client_id"] == client_id
        ):
            return tick_job(
                edit_dir, row["id"], state="running", message=CLAIMED_MESSAGE
            )
    return None


def complete_client_job(
    edit_dir: Path | str,
    job_id: str,
    *,
    ok: bool,
    out_path: str = "",
    message: str = "",
    now: Callable[[], str] | None = None,
) -> JobRecord:
    """Land a browser render: ``running -> ok/failed``.

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.
        job_id: Row id.
        ok: Whether the WebCodecs encode produced a file.
        out_path: Rendered path relative to the edit dir (required when ok).
        message: Progress or failure line.
        now: Clock callable.

    Returns:
        Updated row.

    Raises:
        FileNotFoundError: No such row.
        ValueError: Row is not a client row, or ``out_path`` is unsafe/empty.
    """
    row = read_job(edit_dir, job_id)
    if row["kind"] != CLIENT_KIND:
        raise ValueError(f"job {job_id} is {row['kind']}, not {CLIENT_KIND}")
    if ok:
        row["state"] = "ok"
        row["out_path"] = _safe_client_out(out_path)
        row["message"] = message or "rendered in the browser"
    else:
        row["state"] = "failed"
        row["out_path"] = ""
        row["message"] = message or "browser render failed"
    row["updated_at"] = _stamp(now)
    write_job(edit_dir, row)
    return row


def _safe_client_out(out_path: str) -> str:
    """Vet a browser-reported output path.

    Args:
        out_path: Path relative to the edit dir.

    Returns:
        POSIX relative path.

    Raises:
        ValueError: Empty, absolute, or containing ``..``.
    """
    text = (out_path or "").strip()
    if not text:
        raise ValueError("client render needs an out_path")
    candidate = Path(text)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"unsafe client output path {out_path!r}")
    return candidate.as_posix()
