"""Hermetic tests for :mod:`ez_edit.routes` (the ``/ez_edit/*`` lane).

No aiohttp, no PromptServer, no socket, no ffmpeg, no sleep: routes are
attached to a stand-in table that captures every registration, requests are
plain objects with ``query`` / ``json``, and every seam the handlers touch
(subprocess runner, PATH lookup, ComfyUI transport, sleeper, occupancy reader,
LLM client, clock) is injected through :class:`ez_edit.routes.LaneDeps` over a
tmp ``COMFY_OUTPUT_DIR``.
"""

from __future__ import annotations

import asyncio
import builtins
import json
import sys
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Literal, Mapping

import pytest
from ez_edit import agent, dispatch, generate_clip, render_server, routes, timeline
from ez_edit.protocol import EditProject
from ez_edit.routes import ROUTE_METHODS, LaneDeps, make_deps

FAKE_FFMPEG = "/usr/bin/ffmpeg"
FAKE_FFPROBE = "/usr/bin/ffprobe"
PROMPT = "a brass desk lamp turning slowly on a concrete plinth"
ALL_HANDLERS: tuple[tuple[str, Callable[..., tuple[int, object]]], ...] = (
    ("state", routes.handle_state),
    ("ops", routes.handle_ops),
    ("import", routes.handle_import),
    ("render", routes.handle_render),
    ("job", routes.handle_job),
    ("chat", routes.handle_chat),
    ("exec_pending", routes.handle_exec_pending),
    ("exec_result", routes.handle_exec_result),
    ("local_sync", routes.handle_local_sync),
    ("local_pending", routes.handle_local_pending),
    ("local_result", routes.handle_local_result),
    ("generate_clip", routes.handle_generate_clip),
    ("export_edl", routes.handle_export_edl),
)
"""Every pure handler, by name, so the disabled lane can be swept in one pass."""


def _env(tmp_path: Path, **extra: str) -> dict[str, str]:
    """Environ one request is answered under.

    Args:
        tmp_path: pytest tmp directory standing in for the output root.
        **extra: Environ overrides (``EZ_EDIT_ENABLED``, ``EZ_EDIT_COMFY_URL``).

    Returns:
        Environ mapping for :func:`ez_edit.routes.make_deps`.
    """
    env = {"COMFY_OUTPUT_DIR": str(tmp_path), "EZ_EDIT_ENABLED": "1"}
    env.update(extra)
    return env


def _deps(tmp_path: Path, *, enabled: bool = True, **overrides: Any) -> LaneDeps:
    """Seam bundle over a tmp output root.

    Args:
        tmp_path: pytest tmp directory.
        enabled: Whether the lane answers (``EZ_EDIT_ENABLED``).
        **overrides: LaneDeps field replacements (fakes, clocks, runners).

    Returns:
        Bundle ready for any ``handle_*`` function.
    """
    env_extra = dict(overrides.pop("environ", None) or {})
    env = _env(tmp_path, EZ_EDIT_ENABLED="1" if enabled else "0", **env_extra)
    return make_deps(env, **overrides)


def _edit_dir(tmp_path: Path) -> Path:
    """``<tmp>/edit`` (created).

    Args:
        tmp_path: pytest tmp directory.

    Returns:
        The edit dir.
    """
    folder = tmp_path / "edit"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _seed_project(edit_dir: Path, title: str = "Reel") -> EditProject:
    """Persist one project through the reducer.

    Args:
        edit_dir: Edit dir.
        title: Project title.

    Returns:
        The stored project.
    """
    project = timeline.apply_ops(None, [{"op": "project_create", "args": {"title": title}}])
    timeline.save_project(edit_dir, project)
    return project


def _media_file(tmp_path: Path, name: str = "clip.mp4") -> Path:
    """Write a dummy media file under the output root.

    Args:
        tmp_path: pytest tmp directory.
        name: File name.

    Returns:
        Written path.
    """
    folder = tmp_path / "media"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / name
    target.write_bytes(b"\x00\x00\x00\x18ftypmp42fake")
    return target


class FakeRunner:
    """``subprocess.run`` stand-in that records argv and fakes the outcome."""

    def __init__(
        self,
        *,
        returncode: int = 0,
        stdout: str = "4.0",
        stderr: str = "",
        create_output: bool = False,
        boom: Exception | None = None,
    ) -> None:
        """Seed the fake outcome.

        Args:
            returncode: Exit code to report.
            stdout: Captured stdout.
            stderr: Captured stderr.
            create_output: Write the last argv element (ffmpeg success).
            boom: Exception to raise instead of answering.
        """
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.create_output = create_output
        self.boom = boom
        self.calls: list[list[str]] = []

    def __call__(
        self, argv: list[str], *, check: bool, capture_output: bool, text: bool
    ) -> Any:
        """Pretend to run ``argv``.

        Args:
            argv: Command vector.
            check: Unused (never raises).
            capture_output: Unused.
            text: Unused.

        Returns:
            Completed-process stand-in.
        """
        del check, capture_output, text
        self.calls.append(list(argv))
        if self.boom is not None:
            raise self.boom
        if self.create_output:
            Path(argv[-1]).parent.mkdir(parents=True, exist_ok=True)
            Path(argv[-1]).write_bytes(b"mp4")
        return SimpleNamespace(
            returncode=self.returncode, stdout=self.stdout, stderr=self.stderr
        )


class _Response:
    """``urlopen`` response stand-in (context manager plus ``read``)."""

    def __init__(self, body: str) -> None:
        """Store the body.

        Args:
            body: Text body ``read`` returns.
        """
        self._body = body

    def __enter__(self) -> "_Response":
        """Enter the context.

        Returns:
            Self.
        """
        return self

    def __exit__(self, *_args: object) -> Literal[False]:
        """Leave the context.

        Args:
            *_args: Exception detail (ignored).

        Returns:
            False (never swallow).
        """
        return False

    def read(self) -> bytes:
        """Return the body.

        Returns:
            Encoded body bytes.
        """
        return self._body.encode("utf-8")


class FakeTransport:
    """Queue of JSON replies standing in for the ComfyUI queue."""

    def __init__(self, replies: list[Any]) -> None:
        """Seed the reply queue.

        Args:
            replies: Parsed JSON values handed back in order.
        """
        self.replies = list(replies)
        self.calls: list[tuple[str, Any]] = []

    def __call__(self, request: urllib.request.Request, timeout: float) -> Any:
        """Answer one request from the queue.

        Args:
            request: Prepared request.
            timeout: Socket timeout (unused).

        Returns:
            Response carrying the next reply.
        """
        del timeout
        self.calls.append((request.full_url, request.data))
        return _Response(json.dumps(self.replies.pop(0) if self.replies else {}))


class FakeLLM:
    """Completion client that always answers in plain text."""

    def __init__(self, reply: str = "the timeline is ready") -> None:
        """Seed the reply line.

        Args:
            reply: Assistant content the loop returns.
        """
        self.reply = reply
        self.turns = 0

    def chat(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """Complete one turn without tool calls.

        Args:
            messages: Chat transcript (system prompt first).
            tools: Tool specs (recorded by the count only).

        Returns:
            Assistant message.
        """
        del messages, tools
        self.turns += 1
        return {"content": self.reply}


class _Adder:
    """``routes.get`` / ``routes.post`` stand-in that records registrations."""

    def __init__(self) -> None:
        """Seed empty capture tables."""
        self.registered: list[tuple[str, str]] = []
        self.endpoints: dict[str, Callable[[Any], Any]] = {}

    def _decorator(self, method: str, path: str) -> Callable[[Any], Any]:
        """Return the decorator aiohttp would apply.

        Args:
            method: HTTP method.
            path: Route path.

        Returns:
            Decorator that records the endpoint.
        """

        def wrap(fn: Any) -> Any:
            """Store one endpoint.

            Args:
                fn: Endpoint coroutine function.

            Returns:
                The same endpoint.
            """
            self.registered.append((method, path))
            self.endpoints[path] = fn
            return fn

        return wrap

    def get(self, path: str) -> Callable[[Any], Any]:
        """Register a GET route.

        Args:
            path: Route path.

        Returns:
            Decorator that records the endpoint.
        """
        return self._decorator("GET", path)

    def post(self, path: str) -> Callable[[Any], Any]:
        """Register a POST route.

        Args:
            path: Route path.

        Returns:
            Decorator that records the endpoint.
        """
        return self._decorator("POST", path)


class _Request:
    """aiohttp request stand-in (``query`` mapping plus a ``json`` body)."""

    def __init__(
        self,
        query: Mapping[str, str] | None = None,
        body: Any = None,
        *,
        boom: bool = False,
        sync: bool = False,
    ) -> None:
        """Seed the query and body.

        Args:
            query: Query mapping for GET routes.
            body: Parsed JSON body for POST routes.
            boom: Raise from ``json`` (an unreadable body).
            sync: Answer ``json`` synchronously instead of awaiting.
        """
        self.query = dict(query or {})
        self._body = body
        self._boom = boom
        self._sync = sync

    def json(self) -> Any:
        """Return the body the way aiohttp does.

        Returns:
            The body, or an awaitable of it.

        Raises:
            ValueError: ``boom`` was requested.
        """
        if self._boom:
            raise ValueError("bad json")
        if self._sync:
            return self._body

        async def _read() -> Any:
            """Resolve the queued body.

            Returns:
                The body.
            """
            return self._body

        return _read()


def _respond(payload: dict[str, Any], *, status: int = 200) -> tuple[int, dict[str, Any]]:
    """``json_response`` stand-in.

    Args:
        payload: Response body.
        status: HTTP status.

    Returns:
        ``(status, payload)``.
    """
    return status, payload


# --- module helpers ---------------------------------------------------------


def test_lane_enabled_reads_the_flag() -> None:
    """Only an exact ``0`` (padded allowed) hides the lane."""
    assert routes.lane_enabled({}) is True
    assert routes.lane_enabled({"EZ_EDIT_ENABLED": "1"}) is True
    assert routes.lane_enabled({"EZ_EDIT_ENABLED": "0"}) is False
    assert routes.lane_enabled({"EZ_EDIT_ENABLED": " 0 "}) is False


def test_make_deps_builds_the_bundle_from_the_environ(tmp_path: Path) -> None:
    """The edit dir and the enabled flag come off the injected environ."""
    deps = make_deps(_env(tmp_path))
    assert deps.edit_dir == tmp_path / "edit"
    assert deps.environ["EZ_EDIT_ENABLED"] == "1"
    assert deps.registry.edit_dir == tmp_path / "edit"
    assert deps.runners == {}
    assert deps.llm is None
    assert deps.turn_fn is None


def test_make_deps_falls_back_to_the_container_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """No environ means os.environ, and a blank root means ``/outputs``."""
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    assert make_deps().edit_dir == tmp_path / "edit"
    monkeypatch.delenv("COMFY_OUTPUT_DIR", raising=False)
    assert make_deps({}).edit_dir == Path(routes.DEFAULT_OUTPUT_DIR) / "edit"
    blank = {"COMFY_OUTPUT_DIR": "   "}
    assert make_deps(blank).edit_dir == Path(routes.DEFAULT_OUTPUT_DIR) / "edit"


def test_make_deps_replaces_only_the_overrides(tmp_path: Path) -> None:
    """Overrides land on the named seam fields and nothing else."""
    registry = dispatch.ClientRegistry(_edit_dir(tmp_path))
    sleeper = lambda _seconds: None  # noqa: E731 - seam double compared by identity
    deps = _deps(tmp_path, registry=registry, runners={"sleeper": sleeper}, now=lambda: "now")
    assert deps.registry is registry
    assert deps.runners == {"sleeper": sleeper}
    assert deps.now is not None and deps.now() == "now"
    assert deps.edit_dir == tmp_path / "edit"


def test_reply_helpers_shape_every_payload() -> None:
    """``_ok``/``_err``/``_disabled``/``_row_reply`` always speak ``{ok, ...}``."""
    assert routes._ok(a=1) == (200, {"ok": True, "a": 1})
    assert routes._err("nope") == (400, {"ok": False, "error": "nope"})
    assert routes._err("no", status=403, reason="refused") == (
        403,
        {"ok": False, "error": "no", "reason": "refused"},
    )
    assert routes._disabled() == (403, {"ok": False, "error": "disabled"})
    row = _row(state="ok")
    assert routes._row_reply(row) == (200, {"ok": True, "job": row})
    bad = _row(state="failed", message="ffmpeg exploded")
    status, payload = routes._row_reply(bad)
    assert (status, payload["ok"], payload["error"]) == (200, False, "ffmpeg exploded")


def test_request_field_helpers_coerce_junk() -> None:
    """Text, number, and flag readers never raise on a junk body."""
    args: dict[str, Any] = {"name": "  tab1  ", "n": 2, "off": "0", "yes": True, "junk": "two"}
    assert routes._text(args, "name") == "tab1"
    assert routes._text(args, "missing") == ""
    assert routes._text({"x": None}, "x", "dflt") == "dflt"
    assert routes._number(args, "n", 5.0) == 2.0
    assert routes._number({"n": None}, "n", 5.0) == 5.0
    assert routes._number(args, "junk", 5.0) == 5.0
    assert routes._flag(args, "off") is False
    assert routes._flag(args, "yes") is True
    assert routes._flag(args, "absent") is True
    assert routes._flag(args, "absent", default=False) is False
    assert routes._flag({"off": ""}, "off") is False
    assert routes._flag({"off": "FALSE"}, "off") is False


def _row(**overrides: Any) -> Any:
    """One jobstore row for a reply assertion.

    Args:
        **overrides: Field replacements.

    Returns:
        A :data:`~ez_edit.protocol.JobRecord`-shaped dict.
    """
    row: dict[str, Any] = {
        "id": "job1",
        "kind": "render_server",
        "project_id": "p1",
        "state": "ok",
        "mode": "server",
        "message": "",
        "out_path": "edit/renders/p1-job1.mp4",
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "client_id": "",
    }
    row.update(overrides)
    return row


def test_disabled_lane_refuses_every_route(tmp_path: Path) -> None:
    """``EZ_EDIT_ENABLED=0`` answers 403 ``{ok: false, error: "disabled"}`` everywhere."""
    _seed_project(_edit_dir(tmp_path))
    deps = _deps(tmp_path, enabled=False)
    for name, handler in ALL_HANDLERS:
        status, payload = handler({"project_id": "p1", "message": "hi", "prompt": PROMPT}, deps=deps)
        assert (status, payload) == (403, {"ok": False, "error": "disabled"}), name


# --- state / ops ------------------------------------------------------------


def test_state_reports_project_and_jobs(tmp_path: Path) -> None:
    """``GET /ez_edit/state`` returns the project plus its rows and ``enabled``."""
    edit_dir = _edit_dir(tmp_path)
    project = _seed_project(edit_dir)
    dispatch.start_render_job(edit_dir, project_id=project["id"], mode="client", client_id="tab1")
    status, payload = routes.handle_state({"project_id": project["id"]}, deps=_deps(tmp_path))
    assert status == 200
    assert payload["ok"] is True and payload["enabled"] is True
    assert payload["project"]["id"] == project["id"]
    assert [row["kind"] for row in payload["jobs"]] == ["exec_client"]
    empty = routes.handle_state({}, deps=_deps(tmp_path / "fresh"))[1]
    assert empty["project"] is None and empty["jobs"] == []


def test_state_refuses_an_unknown_project(tmp_path: Path) -> None:
    """A project id nobody owns is a 400 with the reducer reason."""
    _seed_project(_edit_dir(tmp_path))
    status, payload = routes.handle_state({"project_id": "ghost"}, deps=_deps(tmp_path))
    assert status == 400 and payload["ok"] is False
    assert "ghost" in payload["error"]


def test_ops_apply_and_persist(tmp_path: Path) -> None:
    """``POST /ez_edit/ops`` runs the reducer and stores the result."""
    edit_dir = _edit_dir(tmp_path)
    deps = _deps(tmp_path, now=lambda: "2026-01-02T03:04:05+00:00")
    status, payload = routes.handle_ops(
        {"ops": [{"op": "project_create", "args": {"title": "Reel"}}]}, deps=deps
    )
    assert status == 200 and payload["ok"] is True
    project = payload["project"]
    assert project["title"] == "Reel"
    assert project["updated_at"] == "2026-01-02T03:04:05+00:00"
    assert timeline.load_project(edit_dir, project["id"])["title"] == "Reel"


def test_ops_refuse_a_non_list_and_a_junk_op(tmp_path: Path) -> None:
    """``ops`` must be a list, and a junk op is the reducer's 400."""
    _seed_project(_edit_dir(tmp_path))
    status, payload = routes.handle_ops({"ops": "nope"}, deps=_deps(tmp_path))
    assert (status, payload["error"]) == (400, "ops must be a list")
    status, payload = routes.handle_ops({"ops": ["junk"]}, deps=_deps(tmp_path))
    assert status == 400 and payload["ok"] is False


# --- import -----------------------------------------------------------------


def test_import_probes_and_lands_the_clip(tmp_path: Path) -> None:
    """``POST /ez_edit/import`` ffprobes through the runner seam."""
    edit_dir = _edit_dir(tmp_path)
    _seed_project(edit_dir)
    _media_file(tmp_path)
    runner = FakeRunner(stdout="6.5")
    status, payload = routes.handle_import(
        {"path": "media/clip.mp4", "label": " Bowl ", "track": "2"},
        deps=_deps(tmp_path, runners={"subprocess": runner, "which": lambda _n: FAKE_FFPROBE}),
    )
    assert status == 200 and payload["ok"] is True
    clip = payload["clip"]
    assert (clip["source"], clip["label"], clip["track"], clip["out_s"]) == (
        "media/clip.mp4",
        "Bowl",
        2,
        6.5,
    )
    assert runner.calls[0][0] == FAKE_FFPROBE


def test_import_refuses_traversal_a_missing_file_and_a_broken_probe(tmp_path: Path) -> None:
    """Path traversal, a missing file, and an OSErring probe are all 400s."""
    edit_dir = _edit_dir(tmp_path)
    _seed_project(edit_dir)
    deps = _deps(tmp_path, runners={"subprocess": FakeRunner(), "which": lambda _n: FAKE_FFPROBE})
    status, payload = routes.handle_import({"path": "../../etc/passwd"}, deps=deps)
    assert status == 400 and "outside" in payload["error"]
    status, payload = routes.handle_import({"path": "media/gone.mp4"}, deps=deps)
    assert status == 400 and "no such file" in payload["error"]
    status, payload = routes.handle_import({"path": ""}, deps=deps)
    assert (status, payload["error"]) == (400, "path is required")
    broken = _deps(
        tmp_path,
        runners={"subprocess": FakeRunner(boom=OSError("no such process")), "which": lambda _n: FAKE_FFPROBE},
    )
    _media_file(tmp_path)
    status, payload = routes.handle_import({"path": "media/clip.mp4"}, deps=broken)
    assert status == 400 and "no such process" in payload["error"]


# --- render / job -----------------------------------------------------------


def _clip_ready(tmp_path: Path, edit_dir: Path) -> EditProject:
    """Seed a project with one probed clip.

    Args:
        tmp_path: pytest tmp directory (holds the media file).
        edit_dir: Edit dir.

    Returns:
        The stored project.
    """
    project = _seed_project(edit_dir)
    _media_file(tmp_path)
    dispatch.import_clip(
        edit_dir, path="media/clip.mp4", runner=FakeRunner(stdout="4"), which=lambda _n: FAKE_FFPROBE
    )
    return project


def test_render_server_mode_runs_ffmpeg_once(tmp_path: Path) -> None:
    """``POST /ez_edit/render`` mode=server runs one argv and lands an ok row."""
    edit_dir = _edit_dir(tmp_path)
    _clip_ready(tmp_path, edit_dir)
    runner = FakeRunner(create_output=True)
    status, payload = routes.handle_render(
        {"mode": "server"}, deps=_deps(tmp_path, runners={"subprocess": runner, "which": lambda _n: FAKE_FFMPEG})
    )
    assert status == 200 and payload["ok"] is True
    assert payload["job"]["state"] == "ok" and payload["job"]["kind"] == "render_server"
    assert len(runner.calls) == 1 and runner.calls[0][0] == FAKE_FFMPEG


def test_render_reports_a_failed_row_as_ok_false(tmp_path: Path) -> None:
    """No ffmpeg on PATH is an ``ok`` false reply carrying the row."""
    edit_dir = _edit_dir(tmp_path)
    _clip_ready(tmp_path, edit_dir)
    status, payload = routes.handle_render(
        {"mode": "server"}, deps=_deps(tmp_path, runners={"which": lambda _n: None})
    )
    assert (status, payload["ok"]) == (200, False)
    assert payload["job"]["state"] == "failed"
    assert "ffmpeg" in payload["error"]


def test_render_client_mode_leaves_a_row_for_the_panel(tmp_path: Path) -> None:
    """mode=client writes a pending ``exec_client`` row owned by the panel."""
    edit_dir = _edit_dir(tmp_path)
    _clip_ready(tmp_path, edit_dir)
    status, payload = routes.handle_render(
        {"mode": "client", "client_id": "tab1"}, deps=_deps(tmp_path)
    )
    assert status == 200 and payload["ok"] is True
    assert (payload["job"]["kind"], payload["job"]["state"]) == ("exec_client", "pending")
    row_id = payload["job"]["id"]
    assert render_server.read_job(edit_dir, row_id)["client_id"] == "tab1"


def test_render_refuses_a_bad_mode_and_a_missing_project(tmp_path: Path) -> None:
    """A mode outside the vocabulary and an empty lane are both 400s."""
    edit_dir = _edit_dir(tmp_path)
    _clip_ready(tmp_path, edit_dir)
    status, payload = routes.handle_render({"mode": "cloud"}, deps=_deps(tmp_path))
    assert status == 400 and "bad render mode" in payload["error"]
    status, payload = routes.handle_render({"mode": "server"}, deps=_deps(tmp_path / "empty"))
    assert status == 400 and "no edit project" in payload["error"]


def test_job_reads_a_row_and_reports_a_missing_one(tmp_path: Path) -> None:
    """``GET /ez_edit/job`` accepts ``id`` or ``job_id`` and 400s on nothing."""
    edit_dir = _edit_dir(tmp_path)
    _clip_ready(tmp_path, edit_dir)
    row = dispatch.start_render_job(edit_dir, mode="client", client_id="tab1")
    deps = _deps(tmp_path)
    assert routes.handle_job({"id": row["id"]}, deps=deps) == (200, {"ok": True, "job": row})
    assert routes.handle_job({"job_id": row["id"]}, deps=deps)[0] == 200
    assert routes.handle_job({}, deps=deps) == (400, {"ok": False, "error": "job id is required"})
    status, payload = routes.handle_job({"id": "ghost"}, deps=deps)
    assert status == 400 and "ghost" in payload["error"]


def test_job_reports_a_malformed_row(tmp_path: Path) -> None:
    """A row file that is not JSON is a 400, not a traceback."""
    edit_dir = _edit_dir(tmp_path)
    _seed_project(edit_dir)
    jobs = render_server.jobs_dir(edit_dir)
    jobs.mkdir(parents=True, exist_ok=True)
    (jobs / "junk.json").write_text("not json", encoding="utf-8")
    status, payload = routes.handle_job({"id": "junk"}, deps=_deps(tmp_path))
    assert status == 400 and payload["ok"] is False


# --- chat -------------------------------------------------------------------


def test_chat_runs_one_turn_through_the_injected_loop(tmp_path: Path) -> None:
    """``POST /ez_edit/chat`` returns the reply, the trace, and the history."""
    _edit_dir(tmp_path)
    seen: dict[str, Any] = {}

    def turn(user_text: str, **kwargs: Any) -> agent.AgentTurn:
        """Record the call and answer with one tool trace.

        Args:
            user_text: The operator message.
            **kwargs: Seams the route passes.

        Returns:
            A finished agent turn.
        """
        seen["user_text"] = user_text
        seen.update(kwargs)
        return {
            "reply": "added two clips",
            "trace": [{"name": "edit_apply_ops", "args": {}, "ok": True, "summary": "ok"}],
            "history": [{"role": "user", "content": user_text}],
        }

    status, payload = routes.handle_chat(
        {"message": " cut the intro ", "client_id": "tab1"},
        deps=_deps(tmp_path, turn_fn=turn, dispatch_fn=lambda name, args: {"ok": True, "text": name}),
    )
    assert status == 200 and payload["ok"] is True
    assert payload["reply"] == "added two clips" and payload["client_id"] == "tab1"
    assert payload["trace"][0]["name"] == "edit_apply_ops"
    assert seen["user_text"] == "cut the intro"
    assert seen["dispatch"]("edit_get_state", {})["text"] == "edit_get_state"


def test_chat_carries_history_and_drops_junk_rows(tmp_path: Path) -> None:
    """Only mapping rows survive into the transcript the loop is handed."""
    _edit_dir(tmp_path)
    captured: list[Any] = []

    def turn(user_text: str, **kwargs: Any) -> agent.AgentTurn:
        """Capture the history and answer plainly.

        Args:
            user_text: The operator message.
            **kwargs: Seams the route passes.

        Returns:
            A finished agent turn.
        """
        captured.append(kwargs.get("history"))
        return {"reply": "ok", "trace": [], "history": []}

    status, payload = routes.handle_chat(
        {"message": "hi", "history": [{"role": "user", "content": "before"}, "junk", 7]},
        deps=_deps(tmp_path, turn_fn=turn),
    )
    assert status == 200 and payload["reply"] == "ok"
    assert payload["trace"] == [] and payload["history"] == [] and payload["client_id"] == ""
    assert captured[0] == [{"role": "user", "content": "before"}]
    absent = routes.handle_chat({"message": "hi"}, deps=_deps(tmp_path, turn_fn=turn))
    assert absent[1]["ok"] is True and captured[1] is None


def test_chat_uses_the_real_agent_loop_with_the_injected_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """With no turn seam the route drives :func:`ez_edit.agent.run_turn`."""
    _edit_dir(tmp_path)
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    monkeypatch.delenv("EZ_AGENT_MAX_STEPS", raising=False)
    llm = FakeLLM("two clips are in")
    status, payload = routes.handle_chat(
        {"message": "make a cutaway"}, deps=_deps(tmp_path, llm=llm)
    )
    assert status == 200 and payload["ok"] is True
    assert payload["reply"] == "two clips are in"
    assert llm.turns == 1
    assert [row["role"] for row in payload["history"]] == ["user", "assistant"]


def test_chat_reports_a_refusal_and_a_model_crash(tmp_path: Path) -> None:
    """An occupancy refusal is a 400 with ``reason``; a crash is a 500."""
    _edit_dir(tmp_path)

    def refuse(user_text: str, **kwargs: Any) -> agent.AgentTurn:
        """Raise the occupancy refusal.

        Args:
            user_text: The operator message.
            **kwargs: Seams (ignored).

        Returns:
            Never returns.

        Raises:
            agent.AgentRefused: Always.
        """
        del user_text, kwargs
        raise agent.AgentRefused("a heavy job owns the GPU")

    def crash(user_text: str, **kwargs: Any) -> agent.AgentTurn:
        """Blow up the way a broken model would.

        Args:
            user_text: The operator message.
            **kwargs: Seams (ignored).

        Returns:
            Never returns.

        Raises:
            RuntimeError: Always.
        """
        del user_text, kwargs
        raise RuntimeError("connection reset")

    status, payload = routes.handle_chat({"message": "hi"}, deps=_deps(tmp_path, turn_fn=refuse))
    assert (status, payload["ok"], payload["reason"]) == (400, False, "refused")
    assert "heavy job" in payload["error"]
    status, payload = routes.handle_chat({"message": "hi"}, deps=_deps(tmp_path, turn_fn=crash))
    assert status == 500 and payload["ok"] is False
    assert "connection reset" in payload["error"]


def test_chat_requires_a_message(tmp_path: Path) -> None:
    """An empty message never reaches the model."""
    _edit_dir(tmp_path)
    assert routes.handle_chat({"message": "   "}, deps=_deps(tmp_path)) == (
        400,
        {"ok": False, "error": "message is required"},
    )


# --- browser exec queue -----------------------------------------------------


def test_exec_pending_claims_this_panel_only(tmp_path: Path) -> None:
    """``GET /ez_edit/exec/pending`` moves this panel's rows to ``running``."""
    edit_dir = _edit_dir(tmp_path)
    _clip_ready(tmp_path, edit_dir)
    mine = dispatch.start_render_job(edit_dir, mode="client", client_id="tab1")
    dispatch.start_render_job(edit_dir, mode="client", client_id="tab2")
    status, payload = routes.handle_exec_pending({"client_id": "tab1"}, deps=_deps(tmp_path))
    assert status == 200 and payload["ok"] is True
    assert [row["id"] for row in payload["jobs"]] == [mine["id"]]
    assert payload["jobs"][0]["state"] == "running"
    again = routes.handle_exec_pending({"client_id": "tab1"}, deps=_deps(tmp_path))[1]
    assert again["jobs"] == []
    assert routes.handle_exec_pending({}, deps=_deps(tmp_path)) == (
        400,
        {"ok": False, "error": "client_id is required"},
    )


def test_exec_pending_caps_one_poll(tmp_path: Path) -> None:
    """One poll claims at most :data:`MAX_CLAIMS_PER_POLL` rows."""
    edit_dir = _edit_dir(tmp_path)
    _clip_ready(tmp_path, edit_dir)
    for _ in range(routes.MAX_CLAIMS_PER_POLL + 1):
        dispatch.start_render_job(edit_dir, mode="client", client_id="tab1")
    payload = routes.handle_exec_pending({"client_id": "tab1"}, deps=_deps(tmp_path))[1]
    assert len(payload["jobs"]) == routes.MAX_CLAIMS_PER_POLL
    left = routes.handle_exec_pending({"client_id": "tab1"}, deps=_deps(tmp_path))[1]
    assert len(left["jobs"]) == 1


def test_exec_result_lands_a_browser_render(tmp_path: Path) -> None:
    """``POST /ez_edit/exec/result`` closes a claimed row with its file."""
    edit_dir = _edit_dir(tmp_path)
    _clip_ready(tmp_path, edit_dir)
    row = dispatch.start_render_job(edit_dir, mode="client", client_id="tab1")
    routes.handle_exec_pending({"client_id": "tab1"}, deps=_deps(tmp_path))
    deps = _deps(tmp_path, now=lambda: "2026-01-03T00:00:00+00:00")
    status, payload = routes.handle_exec_result(
        {"job_id": row["id"], "ok": "true", "out_path": "renders/tab1.webm", "message": "done"},
        deps=deps,
    )
    assert status == 200 and payload["ok"] is True
    assert payload["job"]["state"] == "ok"
    assert payload["job"]["out_path"] == "renders/tab1.webm"
    assert payload["job"]["updated_at"] == "2026-01-03T00:00:00+00:00"
    failed = routes.handle_exec_result({"job_id": row["id"], "message": "codec died"}, deps=deps)[1]
    assert failed["job"]["state"] == "failed" and failed["job"]["message"] == "codec died"


def test_exec_result_refuses_a_missing_or_unsafe_row(tmp_path: Path) -> None:
    """No id, no row, a server row, and an escaping path are all 400s."""
    edit_dir = _edit_dir(tmp_path)
    _clip_ready(tmp_path, edit_dir)
    client_row = dispatch.start_render_job(edit_dir, mode="client", client_id="tab1")
    server_row = dispatch.start_render_job(
        edit_dir,
        mode="server",
        runner=FakeRunner(create_output=True),
        which=lambda _n: FAKE_FFMPEG,
    )
    deps = _deps(tmp_path)
    assert routes.handle_exec_result({}, deps=deps) == (
        400,
        {"ok": False, "error": "job_id is required"},
    )
    status, payload = routes.handle_exec_result({"job_id": "ghost", "ok": True}, deps=deps)
    assert status == 400 and "ghost" in payload["error"]
    status, payload = routes.handle_exec_result(
        {"job_id": server_row["id"], "ok": True, "out_path": "renders/x.webm"}, deps=deps
    )
    assert status == 400 and "not exec_client" in payload["error"]
    status, payload = routes.handle_exec_result(
        {"job_id": client_row["id"], "ok": True, "out_path": "../evil.webm"}, deps=deps
    )
    assert status == 400 and "unsafe client output path" in payload["error"]
    status, payload = routes.handle_exec_result({"job_id": client_row["id"], "ok": "1"}, deps=deps)
    assert status == 400 and "needs an out_path" in payload["error"]


# --- local MCP relay --------------------------------------------------------


def _tool_row(name: str = "read_file") -> dict[str, Any]:
    """One synced laptop tool definition.

    Args:
        name: Tool name on the laptop server.

    Returns:
        A :data:`~ez_edit.protocol.LocalToolDef`-shaped dict.
    """
    return {
        "server_id": "srv",
        "server_url": "http://127.0.0.1:7000/mcp",
        "name": name,
        "description": "Read a laptop file",
        "input_schema": {"type": "object"},
    }


def test_local_sync_stores_the_panel_tools(tmp_path: Path) -> None:
    """``POST /ez_edit/local_tools/sync`` keeps the usable rows."""
    deps = _deps(tmp_path)
    status, payload = routes.handle_local_sync(
        {"client_id": "tab1", "tools": [_tool_row(), {"nope": 1}]}, deps=deps
    )
    assert status == 200 and payload["ok"] is True
    assert (payload["client_id"], payload["count"]) == ("tab1", 1)
    assert deps.registry.all_tools("tab1")[0].tool["name"] == "read_file"
    empty = routes.handle_local_sync({"client_id": "tab1"}, deps=deps)[1]
    assert empty["count"] == 0


def test_local_sync_refuses_a_missing_id_and_junk_tools(tmp_path: Path) -> None:
    """No id, an escaping id, and a non-list payload are 400s."""
    deps = _deps(tmp_path)
    assert routes.handle_local_sync({"tools": []}, deps=deps) == (
        400,
        {"ok": False, "error": "client_id is required"},
    )
    status, payload = routes.handle_local_sync({"client_id": "a/b", "tools": []}, deps=deps)
    assert status == 400 and "unsafe client_id" in payload["error"]
    junk: Any = {"name": "read_file"}
    status, payload = routes.handle_local_sync({"client_id": "tab1", "tools": junk}, deps=deps)
    assert (status, payload["error"]) == (400, "tools must be a list")


def test_local_pending_lists_queued_calls(tmp_path: Path) -> None:
    """``GET /ez_edit/local_tools/pending`` hands the panel its queue."""
    deps = _deps(tmp_path)
    call = deps.registry.enqueue("tab1", server_url="http://127.0.0.1:7000/mcp", name="read_file", args={})
    status, payload = routes.handle_local_pending({"client_id": "tab1"}, deps=deps)
    assert status == 200 and payload["calls"] == [call]
    assert routes.handle_local_pending({}, deps=deps) == (
        400,
        {"ok": False, "error": "client_id is required"},
    )
    status, payload = routes.handle_local_pending({"client_id": "~x"}, deps=deps)
    assert status == 400 and "unsafe client_id" in payload["error"]


def test_local_result_unblocks_the_call(tmp_path: Path) -> None:
    """``POST /ez_edit/local_tools/result`` lands the panel's answer."""
    deps = _deps(tmp_path)
    call = deps.registry.enqueue("tab1", server_url="u", name="read_file", args={})
    status, payload = routes.handle_local_result(
        {"call_id": call["call_id"], "ok": "true", "text": " file body "}, deps=deps
    )
    assert status == 200 and payload["ok"] is True and payload["call_id"] == call["call_id"]
    answer = deps.registry.answer(call["call_id"])
    assert answer is not None and answer.ok and answer.text == "file body"


def test_local_result_requires_and_knows_a_call(tmp_path: Path) -> None:
    """A missing or unknown call id is a 400 naming the call."""
    deps = _deps(tmp_path)
    assert routes.handle_local_result({}, deps=deps) == (
        400,
        {"ok": False, "error": "call_id is required"},
    )
    status, payload = routes.handle_local_result({"call_id": "ghost"}, deps=deps)
    assert status == 400 and "unknown local tool call ghost" in payload["error"]


# --- generate_clip / export_edl --------------------------------------------


def test_generate_clip_queues_the_cutaway_graph(tmp_path: Path) -> None:
    """``POST /ez_edit/generate_clip`` queues the pack graph and lands an ok row."""
    edit_dir = _edit_dir(tmp_path)
    transport = FakeTransport(
        [
            {"prompt_id": "pid-1"},
            {"pid-1": {"outputs": {"12": {"gifs": [{"filename": "cut.mp4", "subfolder": "ez_edit"}]}}}},
        ]
    )
    deps = _deps(
        tmp_path,
        runners={
            "urlopen": transport,
            "sleeper": lambda _s: None,
            "occupancy": lambda: "idle",
            "graph_file": generate_clip.graph_path(),
        },
        now=lambda: "2026-01-04T00:00:00+00:00",
        environ={"EZ_EDIT_COMFY_URL": "http://127.0.0.1:8188"},
    )
    status, payload = routes.handle_generate_clip(
        {"prompt": PROMPT, "duration_s": "3", "fps": "30", "project_id": "p1", "client_id": "tab1"},
        deps=deps,
    )
    assert status == 200 and payload["ok"] is True
    row = payload["job"]
    assert (row["kind"], row["state"], row["out_path"]) == ("generate_clip", "ok", "ez_edit/cut.mp4")
    assert row["created_at"] == "2026-01-04T00:00:00+00:00"
    assert transport.calls[0][0] == "http://127.0.0.1:8188/prompt"
    posted = json.loads(transport.calls[0][1])
    assert any(PROMPT in json.dumps(node) for node in posted["prompt"]["nodes"])


def test_generate_clip_requires_a_prompt(tmp_path: Path) -> None:
    """An empty prompt is refused before a row or a socket exists."""
    _edit_dir(tmp_path)
    transport = FakeTransport([])
    deps = _deps(tmp_path, runners={"urlopen": transport})
    assert routes.handle_generate_clip({"prompt": "  "}, deps=deps) == (
        400,
        {"ok": False, "error": "prompt is required"},
    )
    assert transport.calls == []


def test_generate_clip_reports_a_refused_row(tmp_path: Path) -> None:
    """A heavy GPU tenant lands an ``ok`` false row and opens no socket."""
    _edit_dir(tmp_path)
    transport = FakeTransport([])
    deps = _deps(
        tmp_path,
        runners={
            "urlopen": transport,
            "sleeper": lambda _s: None,
            "occupancy": lambda: "wan",
            "graph_file": generate_clip.graph_path(),
            "poll_s": 0.0,
            "poll_timeout_s": 0.0,
        },
    )
    status, payload = routes.handle_generate_clip({"prompt": PROMPT}, deps=deps)
    assert (status, payload["ok"]) == (200, False)
    assert payload["job"]["state"] == "failed" and "occupancy is wan" in payload["error"]
    assert transport.calls == []


def test_export_edl_writes_the_handoff(tmp_path: Path) -> None:
    """``POST /ez_edit/export_edl`` returns the handoff path under the output root."""
    edit_dir = _edit_dir(tmp_path)
    _clip_ready(tmp_path, edit_dir)
    status, payload = routes.handle_export_edl({}, deps=_deps(tmp_path))
    assert status == 200 and payload["ok"] is True
    assert payload["path"].endswith(".edl.json") and payload["clips"] == 1
    assert (tmp_path / payload["path"]).is_file()


def test_export_edl_without_a_project(tmp_path: Path) -> None:
    """Nothing to describe is a 400 that names the missing project."""
    _edit_dir(tmp_path)
    status, payload = routes.handle_export_edl({}, deps=_deps(tmp_path))
    assert status == 400 and payload["ok"] is False


# --- request body reader ----------------------------------------------------


def test_read_json_body_survives_every_request_shape() -> None:
    """Missing, async, sync, and raising bodies all read as a usable value."""
    assert asyncio.run(routes._read_json_body(SimpleNamespace())) == {}
    assert asyncio.run(routes._read_json_body(_Request(body={"a": 1}))) == {"a": 1}
    assert asyncio.run(routes._read_json_body(_Request(body=["x"], sync=True))) == ["x"]
    assert asyncio.run(routes._read_json_body(_Request(boom=True))) == {}


# --- registration -----------------------------------------------------------


def test_register_routes_fails_soft_without_aiohttp_or_prompt_server(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No aiohttp, no PromptServer, no route table: every case says False."""
    adder = _Adder()
    monkeypatch.setitem(sys.modules, "aiohttp", None)
    assert routes.register_routes(server=SimpleNamespace(routes=adder)) is False
    assert adder.registered == []
    monkeypatch.delitem(sys.modules, "aiohttp", raising=False)
    assert routes.register_routes(server=SimpleNamespace()) is False
    assert routes.register_routes(server=SimpleNamespace(routes=None), json_response=_respond) is False
    assert routes.register_routes(server=SimpleNamespace(routes=SimpleNamespace()), json_response=_respond) is False
    half = SimpleNamespace(routes=SimpleNamespace(get=adder.get))
    assert routes.register_routes(server=half, json_response=_respond) is False

    real_import = builtins.__import__
    blocked = {"server": True}

    def _guarded_import(name: str, *args: Any, **kwargs: Any) -> Any:
        """Refuse the ``server`` import the way a bare pytest run does.

        Args:
            name: Module name.
            *args: Forwarded to the real import.
            **kwargs: Forwarded to the real import.

        Returns:
            Whatever the real import would return.

        Raises:
            ImportError: When ``server`` is asked for while blocked.
        """
        if blocked["server"] and name == "server":
            raise ImportError("no ComfyUI here")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _guarded_import)
    assert routes.register_routes(json_response=_respond) is False
    blocked["server"] = False
    monkeypatch.setitem(sys.modules, "server", SimpleNamespace())
    assert routes.register_routes(json_response=_respond) is False
    monkeypatch.setitem(
        sys.modules, "server", SimpleNamespace(PromptServer=SimpleNamespace(instance=None))
    )
    assert routes.register_routes(json_response=_respond) is False


def test_register_routes_uses_aiohttp_and_prompt_server_defaults(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With both optional imports faked in, the lane attaches itself for real."""
    adder = _Adder()
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setitem(
        sys.modules, "aiohttp", SimpleNamespace(web=SimpleNamespace(json_response=_respond))
    )
    monkeypatch.setitem(
        sys.modules, "server", SimpleNamespace(PromptServer=SimpleNamespace(instance=SimpleNamespace(routes=adder)))
    )
    assert routes.register_routes() is True
    assert sorted(path for _method, path in adder.registered) == sorted(ROUTE_METHODS)


def test_register_routes_registers_every_route_and_answers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Each path is attached with its method and answers through its handler."""
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    monkeypatch.delenv("EZ_EDIT_ENABLED", raising=False)
    adder = _Adder()
    assert routes.register_routes(server=SimpleNamespace(routes=adder), json_response=_respond) is True
    assert sorted(adder.registered) == sorted(
        (method, path) for path, method in ROUTE_METHODS.items()
    )

    edit_dir = _edit_dir(tmp_path)
    _clip_ready(tmp_path, edit_dir)

    async def _run() -> None:
        """Drive one GET and several POSTs through the registered endpoints."""
        listed = await adder.endpoints["/ez_edit/state"](_Request(query={"project_id": ""}))
        assert listed[0] == 200 and listed[1]["ok"] is True
        ops = await adder.endpoints["/ez_edit/ops"](
            _Request(body={"ops": [{"op": "set_title", "args": {"title": "Panel"}}]})
        )
        assert ops[0] == 200 and ops[1]["project"]["title"] == "Panel"
        bad_body = await adder.endpoints["/ez_edit/ops"](_Request(boom=True))
        assert (bad_body[0], bad_body[1]["error"]) == (400, "ops must be a list")
        not_dict = await adder.endpoints["/ez_edit/ops"](_Request(body=["x"], sync=True))
        assert (not_dict[0], not_dict[1]["error"]) == (400, "ops must be a list")
        no_json = await adder.endpoints["/ez_edit/export_edl"](SimpleNamespace(query={}))
        assert no_json[0] == 200 and no_json[1]["path"].endswith(".edl.json")
        job = await adder.endpoints["/ez_edit/job"](_Request(query={}))
        assert (job[0], job[1]["error"]) == (400, "job id is required")
        pending = await adder.endpoints["/ez_edit/local_tools/pending"](_Request(query={"client_id": "tab1"}))
        assert pending[0] == 200 and pending[1]["calls"] == []

    asyncio.run(_run())


def test_pack_import_survives_a_broken_route_registration(monkeypatch: pytest.MonkeyPatch) -> None:
    """``import ez_edit`` succeeds even when route registration raises (fail-soft)."""
    import importlib

    import ez_edit

    def _boom() -> None:
        raise RuntimeError("no PromptServer here")

    monkeypatch.setattr(routes, "register_routes", _boom)
    try:
        importlib.reload(ez_edit)
        assert ez_edit.NODE_CLASS_MAPPINGS == {}
        assert ez_edit.WEB_DIRECTORY == "./js"
    finally:
        monkeypatch.undo()
        importlib.reload(ez_edit)


def test_registered_routes_honour_the_disabled_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Flipping the env var between requests is enough to hide the lane."""
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    adder = _Adder()
    routes.register_routes(server=SimpleNamespace(routes=adder), json_response=_respond)
    monkeypatch.setenv("EZ_EDIT_ENABLED", "0")

    async def _run() -> None:
        """Answer one route of each method while disabled."""
        for path in ("/ez_edit/state", "/ez_edit/ops"):
            endpoint = adder.endpoints[path]
            reply = await (endpoint(_Request(query={})) if "state" in path else endpoint(_Request(body={})))
            assert reply == (403, {"ok": False, "error": "disabled"})

    asyncio.run(_run())
