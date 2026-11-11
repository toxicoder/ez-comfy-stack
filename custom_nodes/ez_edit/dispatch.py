"""Tool dispatcher for the editing agent, plus the browser client registry.

:func:`build_dispatch` returns the ``(name, args) -> {"ok", "text"}`` handler
the agent loop calls for every tool the model asks for. Static tools from
:data:`~ez_edit.protocol.TOOL_CATALOG` map onto the lane's own modules
(:mod:`ez_edit.timeline`, :mod:`ez_edit.render_server`, :mod:`ez_edit.edl`,
:mod:`ez_edit.generate_clip`); a name that starts with
:data:`~ez_edit.protocol.LOCAL_TOOL_PREFIX` is a laptop-local MCP tool the
browser must execute, so it is queued under ``edit/clients/<client_id>/`` and
polled until the panel answers or the wait times out.

The same helpers back the PromptServer routes, so the panel and the agent
cannot drift apart: one implementation of import, ops, render, job, and EDL
semantics lives here.

Everything environmental is injectable - the ``subprocess``/``which`` pair for
ffprobe, the transport and sleeper for the ComfyUI queue, the occupancy reader,
and the clock - so pytest stays hermetic (no ffmpeg, no socket, no sleep).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
import uuid
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Callable, NamedTuple, Protocol, TypeAlias, cast, get_args

from ez_common.protocols import CompletedProc, SubprocessRunner

from . import agent, edl, generate_clip, protocol, render_server, timeline
from .protocol import (
    CLIENTS_SUBDIR,
    PROJECTS_SUBDIR,
    Clip,
    EditProject,
    ExecMode,
    JobRecord,
    LocalCall,
    LocalToolDef,
    ProjectState,
)

if TYPE_CHECKING:
    from ez_common import Json, JsonList, JsonMap, JsonObject

DispatchFn: TypeAlias = Callable[[str, "JsonMap"], "JsonObject"]
"""``(name, args) -> {"ok", "text"}`` executor handed to the agent loop."""

RunnerKit: TypeAlias = Mapping[str, object]
"""Injectable seams: ``subprocess``, ``which``, ``urlopen``, ``sleeper``,
``occupancy``, ``clock``, ``environ``, ``generate``, ``local_timeout_s``,
``local_poll_s`` (all optional; production defaults when absent)."""

ClockFn: TypeAlias = Callable[[], str]
"""Clock seam returning an ISO-8601 stamp."""

SleeperFn: TypeAlias = Callable[[float], None]
"""``time.sleep``-shaped seam."""

class GenerateFn(Protocol):
    """``generate_clip``-shaped seam (``kit["generate"]`` override in tests).

    The kit hands the keyword arguments through untouched, so the seam only
    has to accept the lane defaults :func:`_tool_generate_clip` passes.
    """

    def __call__(self, edit_dir: Path | str, **kwargs: object) -> JobRecord:
        """Queue one cutaway and land its row.

        Args:
            edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.
            **kwargs: ``generate_clip`` keyword seams.

        Returns:
            The landed jobstore row.
        """
        ...

WhichFn: TypeAlias = Callable[[str], "str | None"]
"""``shutil.which``-shaped PATH lookup."""

ClientEntry = NamedTuple("ClientEntry", [("client_id", str), ("tool", LocalToolDef)])
"""One synced local tool and the browser client that advertised it."""

Answer = NamedTuple("Answer", [("ok", bool), ("text", str)])
"""A browser's answer to one relayed local tool call."""

TOOLS_FILE_NAME = "tools.json"
"""Per-client file holding the tools the panel discovered."""

CALLS_SUBDIR = "calls"
"""Per-client subdirectory holding relayed call rows."""

CALL_PENDING = "pending"
"""Call row state the panel still has to answer."""

CALL_ANSWERED = "answered"
"""Call row state once the panel posted its result."""

LOCAL_CALL_TIMEOUT_S = 30.0
"""Seconds the agent waits for a browser to answer a local tool call."""

LOCAL_POLL_S = 0.5
"""Seconds between local call result polls."""

LOCAL_TEXT_LIMIT = 4000
"""How much tool text the registry keeps (keeps rows small)."""

FFPROBE_MISSING_MESSAGE = (
    "ffprobe not found on PATH - install ffmpeg in the Comfy image "
    "(apt-get install -y ffmpeg) before importing media"
)
"""Refusal line when the PATH lookup finds no ffprobe."""

FFPROBE_FAILED_FMT = "ffprobe could not probe {path}: {detail}"
"""Refusal line template for a failed or unparsable probe."""

BAD_LOCAL_NAME_MESSAGE = "bad local tool name {name!r} (want local__<server_id>__<tool>)"
"""Refusal line for a malformed ``local__`` tool name."""

NO_LOCAL_CLIENT_MESSAGE = (
    "no connected browser panel has synced the tool {name!r} - open the Edit "
    "panel and press Discover on its MCP server"
)
"""Refusal line when nobody advertised the local tool."""

UNANSWERED_MESSAGE = "the browser panel did not answer {name!r} within {timeout}s"
"""Refusal line when the local call timed out."""

EXEC_MODE_VALUES: tuple[str, ...] = get_args(ExecMode)
"""Render modes the lane accepts (mirrors :data:`~ez_edit.protocol.ExecMode`)."""


class DispatchError(ValueError):
    """A lane call the agent or a route must be told about in words."""


class ClientRegistry:
    """File-backed queue of browser panels and their relayed tool calls.

    Layout under the edit dir (pinned by ``CONTRACTS``):
    ``edit/clients/<client_id>/tools.json`` holds the tools the panel
    discovered from its laptop-loopback MCP servers, and
    ``edit/clients/<client_id>/calls/<call_id>.json`` is one
    :data:`~ez_edit.protocol.LocalCall` row the panel drains and answers.
    """

    def __init__(self, edit_dir: Path | str, *, clock: ClockFn | None = None) -> None:
        """Bind the registry to one edit dir.

        Args:
            edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.
            clock: Stamp seam (tests).
        """
        self.edit_dir = Path(edit_dir)
        self.clock = clock

    def clients_dir(self) -> Path:
        """``edit/clients`` directory.

        Returns:
            Clients root (not necessarily created).
        """
        return self.edit_dir / CLIENTS_SUBDIR

    def client_dir(self, client_id: str) -> Path:
        """``edit/clients/<client_id>`` with the id vetted as one segment.

        Args:
            client_id: Browser panel id.

        Returns:
            Client directory (not necessarily created).

        Raises:
            DispatchError: The id is empty or tries to leave the clients dir.
        """
        return self.clients_dir() / _safe_segment(client_id, "client_id")

    def _tools_file(self, client_id: str) -> Path:
        """``edit/clients/<client_id>/tools.json``.

        Args:
            client_id: Browser panel id.

        Returns:
            Tools file path.
        """
        return self.client_dir(client_id) / TOOLS_FILE_NAME

    def sync(self, client_id: str, tools: JsonList) -> int:
        """Store the tools one panel discovered.

        Args:
            client_id: Browser panel id.
            tools: Raw :data:`~ez_edit.protocol.LocalToolDef` rows.

        Returns:
            How many usable rows were stored.

        Raises:
            DispatchError: ``tools`` is not a list or the id is unsafe.
        """
        if not isinstance(tools, (list, tuple)):
            raise DispatchError("tools must be a list")
        rows: list[LocalToolDef] = []
        for raw in tools:
            entry = _as_tool_def(raw)
            if entry is not None:
                rows.append(entry)
        folder = self.client_dir(client_id)
        folder.mkdir(parents=True, exist_ok=True)
        document = {
            "client_id": str(client_id),
            "updated_at": _stamp(self.clock),
            "tools": rows,
        }
        path = self._tools_file(client_id)
        tmp = path.with_name(f"{path.name}.tmp")
        tmp.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        tmp.replace(path)
        return len(rows)

    def all_tools(self, client_id: str = "") -> list[ClientEntry]:
        """Every synced tool, with the client that advertised it.

        Args:
            client_id: Restrict to one panel (empty for all).

        Returns:
            Client/tool entries, newest file order stable by client id.
        """
        folder = self.clients_dir()
        if not folder.is_dir():
            return []
        files = (
            [self._tools_file(client_id)]
            if client_id
            else sorted(folder.glob("*/tools.json"))
        )
        entries: list[ClientEntry] = []
        for path in files:
            document = _read_json(path)
            if document is None:
                continue
            owner = str(document.get("client_id") or path.parent.name)
            raw_tools = document.get("tools")
            if not isinstance(raw_tools, (list, tuple)):
                continue
            for raw in raw_tools:
                entry = _as_tool_def(raw)
                if entry is not None:
                    entries.append(ClientEntry(client_id=owner, tool=entry))
        return entries

    def owner(self, server_id: str, name: str) -> ClientEntry | None:
        """Find the panel that advertised one local tool.

        Args:
            server_id: Laptop MCP server id.
            name: Tool name as the server reports it.

        Returns:
            The entry, or ``None`` when no panel synced it.
        """
        for entry in self.all_tools():
            if entry.tool["server_id"] == server_id and entry.tool["name"] == name:
                return entry
        return None

    def clients_for_tool(self, name: str) -> list[str]:
        """Client ids that synced a tool name.

        Args:
            name: Tool name (bare, without the ``local__`` envelope).

        Returns:
            Client ids in discovery order.
        """
        return [entry.client_id for entry in self.all_tools() if entry.tool["name"] == name]

    def _calls_dir(self, client_id: str) -> Path:
        """``edit/clients/<client_id>/calls``.

        Args:
            client_id: Browser panel id.

        Returns:
            Calls directory.
        """
        return self.client_dir(client_id) / CALLS_SUBDIR

    def enqueue(
        self,
        client_id: str,
        *,
        server_url: str,
        name: str,
        args: JsonMap,
    ) -> LocalCall:
        """Queue one call for the browser panel to execute.

        Args:
            client_id: Panel that owns the laptop server.
            server_url: Loopback MCP endpoint.
            name: Tool name on that server.
            args: Tool arguments.

        Returns:
            The queued :data:`~ez_edit.protocol.LocalCall` view.
        """
        folder = self._calls_dir(client_id)
        folder.mkdir(parents=True, exist_ok=True)
        stamp = _stamp(self.clock)
        call_args: JsonObject = dict(args or {})
        row: JsonObject = {
            "call_id": uuid.uuid4().hex[:12],
            "client_id": str(client_id),
            "server_url": str(server_url or ""),
            "name": str(name or ""),
            "args": call_args,
            "state": CALL_PENDING,
            "ok": False,
            "text": "",
            "created_at": stamp,
            "updated_at": stamp,
        }
        path = folder / f"{row['call_id']}.json"
        path.write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
        return LocalCall(
            call_id=str(row["call_id"]),
            server_url=str(row["server_url"]),
            name=str(row["name"]),
            args=dict(call_args),
        )

    def pending(self, client_id: str) -> list[LocalCall]:
        """Calls a panel still has to execute, oldest first.

        Args:
            client_id: Browser panel id.

        Returns:
            Pending :data:`~ez_edit.protocol.LocalCall` views.
        """
        folder = self._calls_dir(client_id)
        if not folder.is_dir():
            return []
        rows: list[tuple[str, LocalCall]] = []
        for path in sorted(folder.glob("*.json")):
            data = _read_json(path)
            if data is None or str(data.get("state") or "") != CALL_PENDING:
                continue
            rows.append(
                (
                    str(data.get("created_at") or ""),
                    LocalCall(
                        call_id=str(data.get("call_id") or path.stem),
                        server_url=str(data.get("server_url") or ""),
                        name=str(data.get("name") or ""),
                        args=dict(cast("JsonMap", data.get("args") or {})),
                    ),
                )
            )
        return [row for _, row in sorted(rows, key=lambda item: (item[0], item[1]["call_id"]))]

    def _call_file(self, call_id: str) -> Path | None:
        """Locate one call row by id.

        Args:
            call_id: Call id.

        Returns:
            Row path, or ``None`` when no client holds it.
        """
        text = str(call_id or "").strip()
        if not text or any(bad in text for bad in ("/", "\\", "..")):
            return None
        folder = self.clients_dir()
        if not folder.is_dir():
            return None
        for candidate in sorted(folder.glob(f"*/{CALLS_SUBDIR}/{text}.json")):
            if candidate.is_file():
                return candidate
        return None

    def submit_result(self, call_id: str, *, ok: bool, text: str) -> bool:
        """Record a panel's answer to one relayed call.

        Args:
            call_id: Call id.
            ok: Whether the laptop call succeeded.
            text: Result text (or the error line).

        Returns:
            True when the row was found and landed.
        """
        path = self._call_file(call_id)
        if path is None:
            return False
        data = _read_json(path)
        if data is None:
            return False
        data["state"] = CALL_ANSWERED
        data["ok"] = bool(ok)
        data["text"] = str(text or "")[:LOCAL_TEXT_LIMIT]
        data["updated_at"] = _stamp(self.clock)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return True

    def answer(self, call_id: str) -> Answer | None:
        """Read a panel's answer once it has landed.

        Args:
            call_id: Call id.

        Returns:
            The answer, or ``None`` while the call is still pending.
        """
        path = self._call_file(call_id)
        if path is None:
            return None
        data = _read_json(path)
        if data is None or str(data.get("state") or "") != CALL_ANSWERED:
            return None
        return Answer(ok=bool(data.get("ok")), text=str(data.get("text") or ""))

    def wait(
        self,
        call_id: str,
        *,
        sleeper: SleeperFn | None = None,
        timeout_s: float = LOCAL_CALL_TIMEOUT_S,
        poll_s: float = LOCAL_POLL_S,
    ) -> Answer | None:
        """Block until the panel answers one call or the wait times out.

        Args:
            call_id: Call id.
            sleeper: Sleep seam between polls.
            timeout_s: Total seconds to wait.
            poll_s: Seconds between polls.

        Returns:
            The answer, or ``None`` on timeout.
        """
        wait = _sleep if sleeper is None else sleeper
        polls = max(1, int(timeout_s // max(poll_s, 0.001)))
        for _ in range(polls):
            answer = self.answer(call_id)
            if answer is not None:
                return answer
            wait(poll_s)
        return self.answer(call_id)


def _stamp(now: ClockFn | None) -> str:
    """Current UTC ISO-8601 stamp, or the injected clock.

    Args:
        now: Clock callable, or ``None`` for the real clock.

    Returns:
        ISO-8601 UTC timestamp.
    """
    if now is not None:
        return now()
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _reducer_clock(now: ClockFn | None) -> timeline.Clock | None:
    """Rewrite the lane's ISO-stamp clock as the reducer's datetime clock.

    Args:
        now: Stamp seam (ISO-8601 text), or ``None`` for the reducer's wall clock.

    Returns:
        A clock :func:`ez_edit.timeline.apply_ops` accepts, or ``None``.

    Raises:
        timeline.TimelineError: The injected clock does not return ISO-8601.
    """
    if now is None:
        return None

    def _moment() -> datetime:
        """Read one datetime from the stamp seam.

        Returns:
            The stamp parsed back into a datetime.

        Raises:
            timeline.TimelineError: The stamp is not ISO-8601 text.
        """
        try:
            return datetime.fromisoformat(now())
        except ValueError as exc:
            raise timeline.TimelineError(f"clock: {exc}") from exc

    return _moment


def _sleep(seconds: float) -> None:
    """Sleep between polls (indirection so pytest never waits).

    Args:
        seconds: Seconds to block.
    """
    time.sleep(seconds)


def _read_json(path: Path) -> JsonObject | None:
    """Read one JSON object file, tolerating junk.

    Args:
        path: File path.

    Returns:
        Parsed object, or ``None`` when missing/unreadable/not an object.
    """
    try:
        data: Json = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _as_tool_def(raw: object) -> LocalToolDef | None:
    """Coerce one synced row into a :data:`~ez_edit.protocol.LocalToolDef`.

    Args:
        raw: Candidate row.

    Returns:
        The tool def, or ``None`` when it names no tool.
    """
    if not isinstance(raw, Mapping):
        return None
    name = str(raw.get("name") or "").strip()
    if not name:
        return None
    return LocalToolDef(
        server_id=str(raw.get("server_id") or "").strip(),
        server_url=str(raw.get("server_url") or "").strip(),
        name=name,
        description=str(raw.get("description") or ""),
        input_schema=dict(raw.get("input_schema") or {}),
    )


def _run(
    argv: list[str], *, check: bool, capture_output: bool, text: bool
) -> CompletedProc:
    """Run one command (indirection so pytest never spawns anything).

    Args:
        argv: Command vector.
        check: Raise on non-zero.
        capture_output: Capture stdout/stderr.
        text: Decode as text.

    Returns:
        Completed process.
    """
    return cast(
        CompletedProc,
        subprocess.run(argv, check=check, capture_output=capture_output, text=text),
    )


def output_root(edit_dir: Path | str) -> Path:
    """``${COMFY_OUTPUT_DIR}`` implied by an edit dir.

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.

    Returns:
        Resolved output root (parent of the edit dir).
    """
    return Path(edit_dir).resolve().parent


def resolve_project(edit_dir: Path | str, project_id: str = "") -> EditProject | None:
    """One project by id, or the most recently updated one.

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.
        project_id: Project id, or ``""`` for the newest.

    Returns:
        The project, or ``None`` when nothing exists yet and no id was asked
        for.

    Raises:
        timeline.TimelineError: The named project is missing or malformed.
    """
    folder = Path(edit_dir)
    if str(project_id or "").strip():
        return timeline.load_project(folder, str(project_id).strip())
    return timeline.most_recent(folder)


def require_project(edit_dir: Path | str, project_id: str = "") -> EditProject:
    """One project, refusing when the lane has none.

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.
        project_id: Project id, or ``""`` for the newest.

    Returns:
        The project.

    Raises:
        DispatchError: No project exists yet.
        timeline.TimelineError: The named project is missing or malformed.
    """
    project = resolve_project(edit_dir, project_id)
    if project is None:
        raise DispatchError(
            "no edit project exists yet - apply the project_create op first"
        )
    return project


def project_state(edit_dir: Path | str, project_id: str = "") -> ProjectState:
    """Project plus its jobstore rows (the state route payload).

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.
        project_id: Project id, or ``""`` for the newest.

    Returns:
        ``{project, jobs}`` with ``project`` ``None`` on a fresh install.

    Raises:
        timeline.TimelineError: The named project is missing or malformed.
    """
    project = resolve_project(edit_dir, project_id)
    wanted = str(project["id"]) if project is not None else str(project_id or "")
    return {
        "project": project,
        "jobs": render_server.list_jobs(edit_dir, wanted),
    }


def projects_index(edit_dir: Path | str) -> JsonObject:
    """One compact row per stored project (the projects route payload).

    An agent that was handed no ``project_id`` has no other way to discover
    what exists: the state route answers one project at a time.

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.

    Returns:
        ``{projects: [...]}``, newest ``updated_at`` first with ties broken by
        id, each row ``{id, title, fps, width, height, clips, updated_at}``
        where ``clips`` is a count rather than the clip list.

    Raises:
        timeline.TimelineError: A stored project is unparsable or malformed.
    """
    stored = timeline.project_index(Path(edit_dir))
    stored.sort(key=lambda project: project["id"])
    stored.sort(key=lambda project: project["updated_at"], reverse=True)
    return {
        "projects": [
            {
                "id": str(project["id"]),
                "title": str(project["title"]),
                "fps": float(project["fps"]),
                "width": int(project["width"]),
                "height": int(project["height"]),
                "clips": len(project["clips"]),
                "updated_at": str(project["updated_at"]),
            }
            for project in stored
        ]
    }


def apply_ops_to(
    edit_dir: Path | str,
    *,
    project_id: str = "",
    ops: Sequence[object],
    clock: ClockFn | None = None,
) -> EditProject:
    """Apply ops to a project and persist the result.

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.
        project_id: Project id, or ``""`` for the newest.
        ops: Ordered reducer ops.
        clock: Stamp seam handed to the reducer.

    Returns:
        The new project.

    Raises:
        timeline.TimelineError: An op, id, or value is invalid.
    """
    base = resolve_project(edit_dir, project_id)
    project = timeline.apply_ops(base, ops, clock=_reducer_clock(clock))
    timeline.save_project(Path(edit_dir), project)
    return project


def probe_duration(
    path: Path | str,
    *,
    runner: SubprocessRunner | None = None,
    which: WhichFn = shutil.which,
) -> float:
    """Media duration seconds through ffprobe.

    Args:
        path: Media file.
        runner: ``subprocess.run`` seam; ``None`` uses the module indirection.
        which: PATH lookup.

    Returns:
        Duration seconds (> 0).

    Raises:
        DispatchError: ffprobe is missing, failed, or reported no duration.
    """
    binary = which("ffprobe")
    if not binary:
        raise DispatchError(FFPROBE_MISSING_MESSAGE)
    run = _run if runner is None else runner
    argv = [
        str(binary),
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    proc = run(argv, check=False, capture_output=True, text=True)
    if int(getattr(proc, "returncode", 1) or 0) != 0:
        detail = str(getattr(proc, "stderr", "") or "").strip() or "no output"
        raise DispatchError(FFPROBE_FAILED_FMT.format(path=path, detail=detail))
    try:
        duration = float(str(getattr(proc, "stdout", "") or "").strip())
    except ValueError as exc:
        raise DispatchError(FFPROBE_FAILED_FMT.format(path=path, detail="no duration")) from exc
    if duration <= 0:
        raise DispatchError(FFPROBE_FAILED_FMT.format(path=path, detail="zero duration"))
    return duration


def safe_output_path(edit_dir: Path | str, raw: object) -> Path:
    """Resolve one caller-supplied path inside the Comfy output root.

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.
        raw: Path as supplied (absolute or relative to the output root).

    Returns:
        Resolved absolute path (not necessarily existing).

    Raises:
        DispatchError: Empty, or it resolves outside the output root.
    """
    text = str(raw or "").strip()
    if not text:
        raise DispatchError("path is required")
    root = output_root(edit_dir)
    candidate = Path(text)
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve()
    if root != resolved and root not in resolved.parents:
        raise DispatchError(f"{text} is outside {root}")
    return resolved


def import_clip(
    edit_dir: Path | str,
    *,
    path: object,
    label: str = "",
    track: int = 0,
    runner: SubprocessRunner | None = None,
    which: WhichFn = shutil.which,
    clock: ClockFn | None = None,
) -> Clip:
    """Probe one media file and add it as a clip to the current project.

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.
        path: Media path under the output root.
        label: Human clip label (file name when empty).
        track: Video track index.
        runner: ffprobe ``subprocess.run`` seam.
        which: PATH lookup for ffprobe.
        clock: Stamp seam handed to the reducer.

    Returns:
        The clip that was added (source relative to the output root).

    Raises:
        DispatchError: The path is unsafe or missing, or ffprobe failed.
        timeline.TimelineError: The clip or the target project is invalid.
    """
    resolved = safe_output_path(edit_dir, path)
    if not resolved.is_file():
        raise DispatchError(f"no such file under the output dir: {path}")
    duration = probe_duration(resolved, runner=runner, which=which)
    root = output_root(edit_dir)
    source = resolved.relative_to(root).as_posix()
    clip: Clip = {
        "id": uuid.uuid4().hex[:12],
        "source": source,
        "label": str(label or "").strip() or resolved.name,
        "in_s": 0.0,
        "out_s": round(duration, 3),
        "track": int(track),
        "gain": 1.0,
        "transition": None,
    }
    apply_ops_to(
        edit_dir,
        project_id="",
        ops=[{"op": "add_clip", "args": {"clip": dict(clip)}}],
        clock=clock,
    )
    return clip


def start_render_job(
    edit_dir: Path | str,
    *,
    project_id: str = "",
    mode: str = "server",
    client_id: str = "",
    runner: SubprocessRunner | None = None,
    which: WhichFn = shutil.which,
    clock: ClockFn | None = None,
) -> JobRecord:
    """Open a render row (server mode runs ffmpeg inline through ``runner``).

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.
        project_id: Project id, or ``""`` for the newest.
        mode: ``server`` or ``client``.
        client_id: Browser owner (client mode).
        runner: ffmpeg ``subprocess.run`` seam.
        which: PATH lookup for ffmpeg.
        clock: Stamp seam.

    Returns:
        The row as written (final state for server mode).

    Raises:
        DispatchError: ``mode`` is not a render mode.
        timeline.TimelineError / DispatchError: No project to render.
        edl.EdlError: The project cannot be rendered.
    """
    wanted = str(mode or "server").strip().lower()
    if wanted not in EXEC_MODE_VALUES:
        raise DispatchError(f"bad render mode {mode!r} (want server or client)")
    project = require_project(edit_dir, project_id)
    return render_server.start_render(
        edit_dir,
        project,
        mode=wanted,  # type: ignore[arg-type]
        client_id=str(client_id or ""),
        runner=runner,
        which=which,
        now=clock,
    )


def job_row(edit_dir: Path | str, job_id: str) -> JobRecord:
    """Read one jobstore row.

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.
        job_id: Row id.

    Returns:
        The row.

    Raises:
        FileNotFoundError: No such row (routes map this to 400).
        ValueError: The row file is malformed.
    """
    return render_server.read_job(edit_dir, job_id)


def _safe_segment(value: object, label: str) -> str:
    """Vet one caller-supplied path segment.

    Args:
        value: Candidate id.
        label: Field name used in the refusal.

    Returns:
        The trimmed id.

    Raises:
        DispatchError: Empty, or it tries to leave its directory.
    """
    text = str(value or "").strip()
    if not text:
        raise DispatchError(f"{label} is required")
    if any(bad in text for bad in ("/", "\\", "..")) or text.startswith("~"):
        raise DispatchError(f"unsafe {label} {value!r}")
    return text


def _edl_path(edit_dir: Path | str, project_id: str) -> Path:
    """``edit/projects/<id>.edl.json`` handoff path.

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.
        project_id: Project id.

    Returns:
        EDL path (not necessarily created).

    Raises:
        DispatchError: The project id is not a safe file name.
    """
    text = _safe_segment(project_id, "project_id")
    return Path(edit_dir) / PROJECTS_SUBDIR / f"{text}.edl.json"


def _cmx_path(edit_dir: Path | str, project_id: str) -> Path:
    """``edit/projects/<id>.edl`` CMX 3600 handoff path.

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.
        project_id: Project id.

    Returns:
        EDL path (not necessarily created).

    Raises:
        DispatchError: The project id is not a safe file name.
    """
    text = _safe_segment(project_id, "project_id")
    return Path(edit_dir) / PROJECTS_SUBDIR / f"{text}.edl"


def export_edl(
    edit_dir: Path | str, project_id: str = "", fmt: str = "json"
) -> JsonObject:
    """Write the project as an EDL handoff file.

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.
        project_id: Project id, or ``""`` for the newest.
        fmt: ``json`` for this lane's own handoff document, ``cmx`` for CMX
            3600 text an external NLE imports.

    Returns:
        ``{ok, path, project_id, clips, format}`` with ``path`` relative to
        the output root.

    Raises:
        edl.EdlError: The project cannot be described, or ``fmt`` is outside
            :data:`~ez_edit.edl.CMX_FORMATS`.
        DispatchError: No project, or an unsafe id.
    """
    if fmt not in edl.CMX_FORMATS:
        raise edl.EdlError(f"unknown edl format {fmt!r} (want json or cmx)")
    if str(project_id or "").strip():
        _safe_segment(project_id, "project_id")
    project = require_project(edit_dir, project_id)
    payload = edl.edl_payload(project)
    if fmt == "cmx":
        body = edl.cmx_edl(project)
        target = _cmx_path(edit_dir, str(project["id"]))
    else:
        body = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        target = _edl_path(edit_dir, str(project["id"]))
    root = output_root(edit_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f"{target.name}.tmp")
    tmp.write_text(body, encoding="utf-8")
    tmp.replace(target)
    relative = target.resolve().relative_to(root).as_posix()
    return {
        "ok": True,
        "path": relative,
        "project_id": str(project["id"]),
        "clips": len(payload["clips"]),
        "format": fmt,
    }


def read_occupancy(
    kit: RunnerKit, environ: Mapping[str, str] | None = None
) -> str:
    """Current GPU occupancy mode string.

    Args:
        kit: Seam bundle; ``occupancy`` overrides the file reader.
        environ: Environ handed to the file reader.

    Returns:
        Mode id (``unknown`` when the state file is missing).
    """
    reader = kit.get("occupancy")
    if callable(reader):
        return str(reader() or "").strip() or "unknown"
    env = environ if environ is not None else cast(
        "Mapping[str, str] | None", kit.get("environ")
    )
    return agent.read_occupancy_mode(environ=env)


def _done(value: object) -> JsonObject:
    """Successful tool result the model can read.

    Args:
        value: JSON-ready payload.

    Returns:
        ``{"ok": True, "text": <json>}``.
    """
    return {"ok": True, "text": json.dumps(value, default=str)}


def _fail(message: str) -> JsonObject:
    """Refused tool result the model can read.

    Args:
        message: Reason line.

    Returns:
        ``{"ok": False, "text": <message>}``.
    """
    return {"ok": False, "text": str(message)}


def _text(args: JsonMap, key: str, default: str = "") -> str:
    """One string argument.

    Args:
        args: Tool arguments.
        key: Argument name.
        default: Value when absent.

    Returns:
        Stringified value.
    """
    raw = args.get(key, default)
    return str(raw if raw is not None else default)


def _number(args: JsonMap, key: str, default: float) -> float:
    """One number argument, tolerant of stringified JSON.

    Args:
        args: Tool arguments.
        key: Argument name.
        default: Value when absent or not a number.

    Returns:
        Float value.
    """
    try:
        return float(args.get(key, default))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _tool_get_state(edit_dir: Path | str, args: JsonMap, kit: RunnerKit) -> JsonObject:
    """``edit_get_state``: project plus recent jobs.

    Args:
        edit_dir: Edit dir.
        args: Tool arguments.
        kit: Seam bundle.

    Returns:
        Tool result.
    """
    del kit
    return _done(project_state(edit_dir, _text(args, "project_id")))


def _tool_list_projects(
    edit_dir: Path | str, args: JsonMap, kit: RunnerKit
) -> JsonObject:
    """``edit_list_projects``: summary row per stored project.

    Args:
        edit_dir: Edit dir.
        args: Tool arguments (none).
        kit: Seam bundle.

    Returns:
        Tool result.
    """
    del args, kit
    return _done(projects_index(edit_dir))


def _tool_import(edit_dir: Path | str, args: JsonMap, kit: RunnerKit) -> JsonObject:
    """``edit_import``: probe a file and add it as a clip.

    Args:
        edit_dir: Edit dir.
        args: Tool arguments.
        kit: Seam bundle.

    Returns:
        Tool result.
    """
    clip = import_clip(
        edit_dir,
        path=args.get("path"),
        label=_text(args, "label"),
        track=int(_number(args, "track", 0.0)),
        runner=cast("SubprocessRunner | None", kit.get("subprocess")),
        which=cast("WhichFn | None", kit.get("which")) or shutil.which,
        clock=cast("ClockFn | None", kit.get("clock")),
    )
    return _done({"clip": clip, "source": clip["source"], "duration_s": clip["out_s"]})


def _tool_apply_ops(edit_dir: Path | str, args: JsonMap, kit: RunnerKit) -> JsonObject:
    """``edit_apply_ops``: run the reducer and persist.

    Args:
        edit_dir: Edit dir.
        args: Tool arguments.
        kit: Seam bundle.

    Returns:
        Tool result.
    """
    raw_ops = args.get("ops")
    ops = list(raw_ops) if isinstance(raw_ops, (list, tuple)) else []
    project = apply_ops_to(
        edit_dir,
        project_id=_text(args, "project_id"),
        ops=ops,
        clock=cast("ClockFn | None", kit.get("clock")),
    )
    return _done({"project": project, "clips": len(project["clips"])})


def _tool_render(edit_dir: Path | str, args: JsonMap, kit: RunnerKit) -> JsonObject:
    """``edit_render``: server or browser render.

    Args:
        edit_dir: Edit dir.
        args: Tool arguments.
        kit: Seam bundle.

    Returns:
        Tool result.
    """
    row = start_render_job(
        edit_dir,
        project_id=_text(args, "project_id"),
        mode=_text(args, "mode", "server"),
        client_id=_text(args, "client_id"),
        runner=cast("SubprocessRunner | None", kit.get("subprocess")),
        which=cast("WhichFn | None", kit.get("which")) or shutil.which,
        clock=cast("ClockFn | None", kit.get("clock")),
    )
    return {"ok": row["state"] != "failed", "text": json.dumps(row, default=str)}


def _tool_job_status(edit_dir: Path | str, args: JsonMap, kit: RunnerKit) -> JsonObject:
    """``edit_job_status``: read one row.

    Args:
        edit_dir: Edit dir.
        args: Tool arguments.
        kit: Seam bundle.

    Returns:
        Tool result.
    """
    del kit
    return _done(job_row(edit_dir, _text(args, "job_id")))


def _tool_generate_clip(
    edit_dir: Path | str, args: JsonMap, kit: RunnerKit
) -> JsonObject:
    """``edit_generate_clip``: queue the cutaway graph.

    Args:
        edit_dir: Edit dir.
        args: Tool arguments.
        kit: Seam bundle.

    Returns:
        Tool result.
    """
    injected = kit.get("generate")
    run_generate: GenerateFn = (
        cast("GenerateFn", injected)
        if callable(injected)
        else cast("GenerateFn", generate_clip.generate_clip)
    )
    row: JobRecord = run_generate(
        edit_dir,
        prompt=_text(args, "prompt"),
        duration_s=_number(args, "duration_s", 5.0),
        fps=_number(args, "fps", 24.0),
        project_id=_text(args, "project_id"),
        client_id=_text(args, "client_id"),
        urlopen=cast("generate_clip.UrlopenFn | None", kit.get("urlopen")),
        sleeper=cast("SleeperFn | None", kit.get("sleeper")),
        occupancy=None if "occupancy" not in kit else lambda: read_occupancy(kit),
        environ=cast("Mapping[str, str] | None", kit.get("environ")),
        now=cast("ClockFn | None", kit.get("clock")),
    )
    return {"ok": row["state"] != "failed", "text": json.dumps(row, default=str)}


def _tool_export_edl(edit_dir: Path | str, args: JsonMap, kit: RunnerKit) -> JsonObject:
    """``edit_export_edl``: write the handoff JSON or CMX EDL.

    Args:
        edit_dir: Edit dir.
        args: Tool arguments.
        kit: Seam bundle.

    Returns:
        Tool result.
    """
    del kit
    return _done(
        export_edl(
            edit_dir,
            _text(args, "project_id"),
            _text(args, "format", "json") or "json",
        )
    )


def _tool_occupancy(
    edit_dir: Path | str, args: JsonMap, kit: RunnerKit
) -> JsonObject:
    """``occupancy_status``: report the GPU mode string.

    Args:
        edit_dir: Edit dir.
        args: Tool arguments.
        kit: Seam bundle.

    Returns:
        Tool result.
    """
    del args, edit_dir
    return _done({"mode": read_occupancy(kit)})


STATIC_TOOLS: dict[
    str, Callable[[Path | str, JsonMap, RunnerKit], JsonObject]
] = {
    "edit_get_state": _tool_get_state,
    "edit_list_projects": _tool_list_projects,
    "edit_import": _tool_import,
    "edit_apply_ops": _tool_apply_ops,
    "edit_render": _tool_render,
    "edit_job_status": _tool_job_status,
    "edit_generate_clip": _tool_generate_clip,
    "edit_export_edl": _tool_export_edl,
    "occupancy_status": _tool_occupancy,
}
"""Static tool name -> handler(edit_dir, args, kit) -> ``{ok, text}``."""


def _parse_local_name(name: str) -> tuple[str, str] | None:
    """Split ``local__<server_id>__<tool>``.

    Args:
        name: Tool name the model asked for.

    Returns:
        ``(server_id, tool)``, or ``None`` when the name is malformed.
    """
    parts = str(name or "").split("__")
    if len(parts) != 3:
        return None
    head, server_id, tool = parts
    if head != protocol.LOCAL_TOOL_PREFIX.rstrip("_") or not server_id or not tool:
        return None
    return server_id, tool


def _run_local(
    registry: ClientRegistry, name: str, args: JsonMap, kit: RunnerKit
) -> JsonObject:
    """Queue one laptop-local MCP call on its browser panel and await the answer.

    Args:
        registry: Client registry (``edit/clients``).
        name: ``local__<server_id>__<tool>``.
        args: Tool arguments.
        kit: Seam bundle (``sleeper``, ``local_timeout_s``, ``local_poll_s``).

    Returns:
        Tool result: the panel's text, or the reason it never answered.
    """
    parsed = _parse_local_name(name)
    if parsed is None:
        return _fail(BAD_LOCAL_NAME_MESSAGE.format(name=name))
    server_id, tool_name = parsed
    entry = registry.owner(server_id, tool_name)
    if entry is None:
        return _fail(NO_LOCAL_CLIENT_MESSAGE.format(name=name))
    call = registry.enqueue(
        entry.client_id,
        server_url=entry.tool["server_url"],
        name=tool_name,
        args=args,
    )
    answer = registry.wait(
        call["call_id"],
        sleeper=cast("SleeperFn | None", kit.get("sleeper")),
        timeout_s=float(
            cast("float | str", kit.get("local_timeout_s", LOCAL_CALL_TIMEOUT_S))
        ),
        poll_s=float(
            cast("float | str", kit.get("local_poll_s", LOCAL_POLL_S))
        ),
    )
    if answer is None:
        return _fail(UNANSWERED_MESSAGE.format(timeout=LOCAL_CALL_TIMEOUT_S, name=name))
    return {"ok": answer.ok, "text": answer.text}


def build_dispatch(
    edit_dir: Path | str,
    *,
    runners: RunnerKit | None = None,
    client_registry: ClientRegistry | None = None,
) -> DispatchFn:
    """Build the agent's tool handler over one lane.

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.
        runners: Injectable seams (see :data:`RunnerKit`).
        client_registry: Registry override (tests, or a shared routes build).

    Returns:
        ``(name, args) -> {"ok", "text"}`` covering the static catalog plus
        browser-relayed ``local__`` tools. Unknown names, bad arguments, and
        lane errors come back as an ``ok`` false text line, never an exception
        the agent loop would have to guess about.
    """
    kit: RunnerKit = runners if runners is not None else {}
    registry = client_registry or ClientRegistry(
        edit_dir, clock=cast("ClockFn | None", kit.get("clock"))
    )

    def handler(name: str, args: JsonMap) -> JsonObject:
        """Execute one tool call.

        Args:
            name: Tool name from the model.
            args: Tool arguments.

        Returns:
            ``{"ok": bool, "text": str}``.
        """
        tool_args = dict(args) if isinstance(args, Mapping) else {}
        if str(name or "").startswith(protocol.LOCAL_TOOL_PREFIX):
            return _run_local(registry, str(name), tool_args, kit)
        tool = STATIC_TOOLS.get(str(name))
        if tool is None:
            return _fail(f"unknown tool: {name}")
        try:
            return tool(edit_dir, tool_args, kit)
        except (ValueError, OSError, FileNotFoundError) as exc:
            return _fail(f"{name}: {exc}")

    return handler
