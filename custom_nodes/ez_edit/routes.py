"""Fail-soft PromptServer routes for the editing lane (``/ez_edit/*``).

The browser panel, the host MCP server, and the built-in agent all reach the
lane through these endpoints. The shape mirrors
``custom_nodes/ez_outputs/routes.py`` exactly: an optional ``aiohttp`` import,
an optional ``server.PromptServer`` (both absent under plain pytest), pure
``handle_*`` functions that take a dict plus a :class:`LaneDeps` seam bundle,
and thin ``async def`` wrappers registered on the PromptServer routes table.

Payloads are always ``{ok, ...}`` with a JSON status. ``EZ_EDIT_ENABLED=0``
refuses every route with ``{ok: false, error: "disabled"}`` at 403; the check
runs inside each handler on every request, so toggling the env var needs no
restart and no registration shortcut.

Business logic is not duplicated here: project/import/render/job/EDL work goes
through :mod:`ez_edit.dispatch` (the same functions the agent's dispatcher
calls), and the chat turn goes through :func:`ez_edit.agent.run_turn` with the
dispatcher injected. Every seam a test needs - subprocess runner, PATH lookup,
transport, sleeper, occupancy reader, LLM client, clock - is injectable.
"""

from __future__ import annotations

import inspect
import os
import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable, NamedTuple, TypeAlias

from . import agent, dispatch, generate_clip, render_server, timeline
from .protocol import EDIT_DIR_NAME, ENV_ENABLED, JobRecord

JsonResponder: TypeAlias = Callable[..., Any]
"""``aiohttp.web.json_response``-shaped ``(payload, status=)`` factory."""

DEFAULT_OUTPUT_DIR = "/outputs"
"""Container output bind used when ``COMFY_OUTPUT_DIR`` is unset."""

DISABLED_ERROR = "disabled"
"""Error string every route reports while the lane is disabled."""

DISABLED_STATUS = 403
"""Status every route reports while the lane is disabled."""

MAX_CLAIMS_PER_POLL = 8
"""Most browser exec rows claimed by one ``exec/pending`` poll."""

TurnFn: TypeAlias = Callable[..., agent.AgentTurn]
"""``agent.run_turn``-shaped seam (tests inject a fake turn)."""

Payload = tuple[int, dict[str, Any]]
"""One ``(status, payload)`` route reply."""

ROUTE_METHODS: dict[str, str] = {
    "/ez_edit/state": "GET",
    "/ez_edit/job": "GET",
    "/ez_edit/exec/pending": "GET",
    "/ez_edit/local_tools/pending": "GET",
    "/ez_edit/ops": "POST",
    "/ez_edit/import": "POST",
    "/ez_edit/render": "POST",
    "/ez_edit/chat": "POST",
    "/ez_edit/exec/result": "POST",
    "/ez_edit/local_tools/sync": "POST",
    "/ez_edit/local_tools/result": "POST",
    "/ez_edit/generate_clip": "POST",
    "/ez_edit/export_edl": "POST",
}
"""Route path -> method, the table ``register_routes`` attaches."""


class LaneDeps(NamedTuple):
    """Everything the handlers touch, injected (built by :func:`make_deps`)."""

    environ: Mapping[str, str]
    """Environ the request is answered under (``EZ_EDIT_ENABLED`` live-read)."""

    edit_dir: Path
    """``${COMFY_OUTPUT_DIR}/edit`` directory."""

    registry: dispatch.ClientRegistry
    """Browser panel / local-tool registry."""

    runners: dispatch.RunnerKit
    """Injectable seams (``subprocess``, ``which``, ``urlopen``, ``sleeper``,
    ``occupancy``, ``generate``, ``graph_file``, ``local_timeout_s``)."""

    llm: Any | None = None
    """Agent completion client; ``None`` lets :mod:`ez_edit.agent` build one."""

    dispatch_fn: dispatch.DispatchFn | None = None
    """Tool dispatcher for chat; ``None`` builds one from the seams."""

    turn_fn: TurnFn | None = None
    """Agent turn callable; ``None`` uses :func:`ez_edit.agent.run_turn`."""

    now: dispatch.ClockFn | None = None
    """ISO-8601 stamp seam handed to the reducer and the jobstore."""


def lane_enabled(environ: Mapping[str, str]) -> bool:
    """Whether the editing lane answers at all.

    Args:
        environ: Environ mapping for the request.

    Returns:
        False when ``EZ_EDIT_ENABLED`` is exactly ``0``.
    """
    return str(environ.get(ENV_ENABLED, "1")).strip() != "0"


def make_deps(
    environ: Mapping[str, str] | None = None, **overrides: Any
) -> LaneDeps:
    """Build the handler seam bundle.

    Args:
        environ: Environ for ``COMFY_OUTPUT_DIR`` and the enabled flag;
            ``None`` reads ``os.environ`` (production).
        overrides: Field replacements (tests inject fakes, registries, clocks).

    Returns:
        Bundle ready for any ``handle_*`` function.
    """
    env: Mapping[str, str] = os.environ if environ is None else environ
    root = str(env.get("COMFY_OUTPUT_DIR") or DEFAULT_OUTPUT_DIR).strip() or DEFAULT_OUTPUT_DIR
    edit_dir = Path(root) / EDIT_DIR_NAME
    deps = LaneDeps(
        environ=env,
        edit_dir=edit_dir,
        registry=dispatch.ClientRegistry(edit_dir),
        runners={},
    )
    if not overrides:
        return deps
    return deps._replace(**overrides)


def _ok(**payload: Any) -> Payload:
    """Successful reply.

    Args:
        **payload: Response fields besides ``ok``.

    Returns:
        ``(200, {ok: true, ...})``.
    """
    return 200, {"ok": True, **payload}


def _err(message: str, *, status: int = 400, **extra: Any) -> Payload:
    """Refused reply.

    Args:
        message: Human reason line.
        status: HTTP status.
        **extra: Extra fields (``reason`` for a refusal).

    Returns:
        ``(status, {ok: false, error, ...})``.
    """
    return status, {"ok": False, "error": str(message), **extra}


def _disabled() -> Payload:
    """Lane switched off reply.

    Returns:
        ``(403, {ok: false, error: "disabled"})``.
    """
    return _err(DISABLED_ERROR, status=DISABLED_STATUS)


def _text(args: Mapping[str, Any], key: str, default: str = "") -> str:
    """One string field of a request mapping.

    Args:
        args: Query or body mapping.
        key: Field name.
        default: Value when absent or null.

    Returns:
        Stringified value.
    """
    raw = args.get(key, default)
    return str(raw if raw is not None else default).strip()


def _number(args: Mapping[str, Any], key: str, default: float) -> float:
    """One numeric field of a request mapping.

    Args:
        args: Query or body mapping.
        key: Field name.
        default: Value when absent or not a number.

    Returns:
        Float value.
    """
    try:
        return float(args.get(key, default))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _flag(args: Mapping[str, Any], key: str, default: bool = True) -> bool:
    """One boolean field of a request mapping.

    Args:
        args: Query or body mapping.
        key: Field name.
        default: Value when absent.

    Returns:
        Truthiness of the field (``"0"``/``"false"`` are false).
    """
    if key not in args:
        return default
    raw = args.get(key)
    if isinstance(raw, str):
        return raw.strip().lower() not in ("", "0", "false", "no")
    return bool(raw)


def _row_reply(row: JobRecord) -> Payload:
    """Reply for a jobstore row: ``ok`` follows the row state.

    Args:
        row: The row a render or generate call landed.

    Returns:
        ``(200, {ok: true, job})``, or ``(200, {ok: false, job, error})`` for
        a failed row (the request itself succeeded; the job did not).
    """
    if row["state"] == "failed":
        return 200, {"ok": False, "job": row, "error": row["message"]}
    return _ok(job=row)


def handle_state(args: Mapping[str, Any], *, deps: LaneDeps) -> Payload:
    """Serve ``GET /ez_edit/state``.

    Args:
        args: Query fields (``project_id`` optional; empty = newest project).
        deps: Seam bundle.

    Returns:
        ``(200, {ok, project, jobs, enabled})``, 403 while disabled, or 400
        when the named project is missing or malformed.
    """
    if not lane_enabled(deps.environ):
        return _disabled()
    try:
        state = dispatch.project_state(deps.edit_dir, _text(args, "project_id"))
    except timeline.TimelineError as exc:
        return _err(str(exc))
    return _ok(project=state["project"], jobs=state["jobs"], enabled=True)


def handle_ops(args: Mapping[str, Any], *, deps: LaneDeps) -> Payload:
    """Serve ``POST /ez_edit/ops``.

    Args:
        args: Body fields (``project_id`` optional, ``ops`` list).
        deps: Seam bundle.

    Returns:
        ``(200, {ok, project})``, 403 while disabled, or 400 with the reducer
        reason.
    """
    if not lane_enabled(deps.environ):
        return _disabled()
    raw_ops = args.get("ops")
    if not isinstance(raw_ops, (list, tuple)):
        return _err("ops must be a list")
    try:
        project = dispatch.apply_ops_to(
            deps.edit_dir,
            project_id=_text(args, "project_id"),
            ops=list(raw_ops),
            clock=deps.now,
        )
    except timeline.TimelineError as exc:
        return _err(str(exc))
    return _ok(project=project)


def handle_import(args: Mapping[str, Any], *, deps: LaneDeps) -> Payload:
    """Serve ``POST /ez_edit/import``.

    The file is probed with ffprobe through the injected runner seam, and the
    path must resolve under ``COMFY_OUTPUT_DIR``.

    Args:
        args: Body fields (``path``, ``label``, ``track``).
        deps: Seam bundle.

    Returns:
        ``(200, {ok, clip})``, 403 while disabled, or 400 with the refusal
        reason (path traversal, missing file, probe failure).
    """
    if not lane_enabled(deps.environ):
        return _disabled()
    try:
        clip = dispatch.import_clip(
            deps.edit_dir,
            path=args.get("path"),
            label=_text(args, "label"),
            track=int(_number(args, "track", 0.0)),
            runner=deps.runners.get("subprocess"),
            which=deps.runners.get("which") or shutil.which,
            clock=deps.now,
        )
    except (dispatch.DispatchError, timeline.TimelineError, OSError) as exc:
        return _err(str(exc))
    return _ok(clip=clip)


def handle_render(args: Mapping[str, Any], *, deps: LaneDeps) -> Payload:
    """Serve ``POST /ez_edit/render``.

    ``mode=server`` runs ffmpeg inline through the injected runner seam;
    ``mode=client`` leaves a pending row for the browser panel to claim.

    Args:
        args: Body fields (``project_id``, ``mode``, ``client_id``).
        deps: Seam bundle.

    Returns:
        ``(200, {ok, job})`` (``ok`` follows the row state), 403 while
        disabled, or 400 for a bad mode or an unrenderable project.
    """
    if not lane_enabled(deps.environ):
        return _disabled()
    try:
        row = dispatch.start_render_job(
            deps.edit_dir,
            project_id=_text(args, "project_id"),
            mode=_text(args, "mode", "server"),
            client_id=_text(args, "client_id"),
            runner=deps.runners.get("subprocess"),
            which=deps.runners.get("which") or shutil.which,
            clock=deps.now,
        )
    except (dispatch.DispatchError, timeline.TimelineError, ValueError) as exc:
        return _err(str(exc))
    return _row_reply(row)


def handle_job(args: Mapping[str, Any], *, deps: LaneDeps) -> Payload:
    """Serve ``GET /ez_edit/job``.

    Args:
        args: Query fields (``id`` or ``job_id``).
        deps: Seam bundle.

    Returns:
        ``(200, {ok, job})``, 403 while disabled, or 400 when the row is
        missing or malformed.
    """
    if not lane_enabled(deps.environ):
        return _disabled()
    job_id = _text(args, "id") or _text(args, "job_id")
    if not job_id:
        return _err("job id is required")
    try:
        row = dispatch.job_row(deps.edit_dir, job_id)
    except (FileNotFoundError, ValueError) as exc:
        return _err(str(exc))
    return _ok(job=row)


def handle_chat(args: Mapping[str, Any], *, deps: LaneDeps) -> Payload:
    """Serve ``POST /ez_edit/chat`` (one agent turn).

    Args:
        args: Body fields (``message``, ``history``, ``client_id``).
        deps: Seam bundle.

    Returns:
        ``(200, {ok, reply, trace, history, client_id})``, 403 while disabled,
        400 for an empty message or an occupancy refusal (with ``reason``),
        500 when the loop itself blew up.
    """
    if not lane_enabled(deps.environ):
        return _disabled()
    message = _text(args, "message")
    if not message:
        return _err("message is required")
    raw_history = args.get("history")
    history = (
        [dict(row) for row in raw_history if isinstance(row, Mapping)]
        if isinstance(raw_history, list)
        else None
    )
    turn_fn: TurnFn = agent.run_turn if deps.turn_fn is None else deps.turn_fn
    dispatcher = (
        deps.dispatch_fn
        if deps.dispatch_fn is not None
        else dispatch.build_dispatch(
            deps.edit_dir, runners=deps.runners, client_registry=deps.registry
        )
    )
    client_id = _text(args, "client_id")
    try:
        turn = turn_fn(
            message,
            history=history,
            llm=deps.llm,
            dispatch=dispatcher,
        )
    except agent.AgentRefused as exc:
        return _err(str(exc), status=400, reason="refused")
    except Exception as exc:  # noqa: BLE001 - a model crash is a 5xx, not a traceback page
        return _err(f"agent turn failed: {exc}", status=500)
    return _ok(
        reply=str(turn.get("reply") or ""),
        trace=list(turn.get("trace") or []),
        history=list(turn.get("history") or []),
        client_id=client_id,
    )


def handle_exec_pending(args: Mapping[str, Any], *, deps: LaneDeps) -> Payload:
    """Serve ``GET /ez_edit/exec/pending`` (claim this panel's render rows).

    Args:
        args: Query fields (``client_id``).
        deps: Seam bundle.

    Returns:
        ``(200, {ok, jobs})`` with each row moved to ``running``, 403 while
        disabled, or 400 without a client id.
    """
    if not lane_enabled(deps.environ):
        return _disabled()
    client_id = _text(args, "client_id")
    if not client_id:
        return _err("client_id is required")
    claimed: list[JobRecord] = []
    while len(claimed) < MAX_CLAIMS_PER_POLL:
        row = render_server.claim_next_client_job(deps.edit_dir, client_id)
        if row is None:
            break
        claimed.append(row)
    return _ok(jobs=claimed)


def handle_exec_result(args: Mapping[str, Any], *, deps: LaneDeps) -> Payload:
    """Serve ``POST /ez_edit/exec/result``.

    Args:
        args: Body fields (``job_id``, ``ok``, ``out_path``, ``message``).
        deps: Seam bundle.

    Returns:
        ``(200, {ok, job})``, 403 while disabled, or 400 when the row is
        missing, is not a client row, or names an unsafe output.
    """
    if not lane_enabled(deps.environ):
        return _disabled()
    job_id = _text(args, "job_id")
    if not job_id:
        return _err("job_id is required")
    try:
        row = render_server.complete_client_job(
            deps.edit_dir,
            job_id,
            ok=_flag(args, "ok", False),
            out_path=_text(args, "out_path"),
            message=_text(args, "message"),
            now=deps.now,
        )
    except (FileNotFoundError, ValueError) as exc:
        return _err(str(exc))
    return _ok(job=row)


def handle_local_sync(args: Mapping[str, Any], *, deps: LaneDeps) -> Payload:
    """Serve ``POST /ez_edit/local_tools/sync``.

    Args:
        args: Body fields (``client_id``, ``tools``).
        deps: Seam bundle.

    Returns:
        ``(200, {ok, client_id, count})``, 403 while disabled, or 400 for a
        missing id, a non-list payload, or an unsafe id.
    """
    if not lane_enabled(deps.environ):
        return _disabled()
    client_id = _text(args, "client_id")
    if not client_id:
        return _err("client_id is required")
    try:
        count = deps.registry.sync(client_id, args.get("tools") or [])
    except dispatch.DispatchError as exc:
        return _err(str(exc))
    return _ok(client_id=client_id, count=count)


def handle_local_pending(args: Mapping[str, Any], *, deps: LaneDeps) -> Payload:
    """Serve ``GET /ez_edit/local_tools/pending``.

    Args:
        args: Query fields (``client_id``).
        deps: Seam bundle.

    Returns:
        ``(200, {ok, calls})``, 403 while disabled, or 400 without a client id
        or for an unsafe one.
    """
    if not lane_enabled(deps.environ):
        return _disabled()
    client_id = _text(args, "client_id")
    if not client_id:
        return _err("client_id is required")
    try:
        calls = deps.registry.pending(client_id)
    except dispatch.DispatchError as exc:
        return _err(str(exc))
    return _ok(calls=calls)


def handle_local_result(args: Mapping[str, Any], *, deps: LaneDeps) -> Payload:
    """Serve ``POST /ez_edit/local_tools/result`` (unblocks the dispatcher).

    Args:
        args: Body fields (``call_id``, ``ok``, ``text``).
        deps: Seam bundle.

    Returns:
        ``(200, {ok, call_id})``, 403 while disabled, or 400 for a missing or
        unknown call.
    """
    if not lane_enabled(deps.environ):
        return _disabled()
    call_id = _text(args, "call_id")
    if not call_id:
        return _err("call_id is required")
    if not deps.registry.submit_result(
        call_id, ok=_flag(args, "ok", False), text=_text(args, "text")
    ):
        return _err(f"unknown local tool call {call_id}")
    return _ok(call_id=call_id)


def handle_generate_clip(args: Mapping[str, Any], *, deps: LaneDeps) -> Payload:
    """Serve ``POST /ez_edit/generate_clip`` (queue the cutaway graph).

    Args:
        args: Body fields (``prompt``, ``duration_s``, ``fps``,
            ``project_id``, ``client_id``).
        deps: Seam bundle.

    Returns:
        ``(200, {ok, job})`` (``ok`` follows the row state; a refusal or a
        missing graph lands an ``ok`` false row), 403 while disabled, or 400
        without a prompt.
    """
    if not lane_enabled(deps.environ):
        return _disabled()
    prompt = _text(args, "prompt")
    if not prompt:
        return _err("prompt is required")
    row = generate_clip.generate_clip(
        deps.edit_dir,
        prompt=prompt,
        duration_s=_number(args, "duration_s", 5.0),
        fps=_number(args, "fps", 24.0),
        project_id=_text(args, "project_id"),
        client_id=_text(args, "client_id"),
        urlopen=deps.runners.get("urlopen"),
        sleeper=deps.runners.get("sleeper"),
        occupancy=deps.runners.get("occupancy"),
        environ=deps.environ,
        graph_file=deps.runners.get("graph_file"),
        poll_s=float(deps.runners.get("poll_s", generate_clip.DEFAULT_POLL_S)),
        timeout_s=float(
            deps.runners.get("poll_timeout_s", generate_clip.DEFAULT_POLL_TIMEOUT_S)
        ),
        now=deps.now,
    )
    return _row_reply(row)


def handle_export_edl(args: Mapping[str, Any], *, deps: LaneDeps) -> Payload:
    """Serve ``POST /ez_edit/export_edl``.

    Args:
        args: Body fields (``project_id``).
        deps: Seam bundle.

    Returns:
        ``(200, {ok, path, project_id, clips})``, 403 while disabled, or 400
        when there is nothing to export.
    """
    if not lane_enabled(deps.environ):
        return _disabled()
    try:
        payload = dispatch.export_edl(deps.edit_dir, _text(args, "project_id"))
    except ValueError as exc:
        return _err(str(exc))
    return _ok(**payload)


async def _read_json_body(request: object) -> Any:
    """Read a JSON body from an aiohttp-like request.

    Args:
        request: Object with an optional ``json`` callable (async or sync).

    Returns:
        Parsed body, or ``{}`` when missing or invalid.
    """
    json_fn = getattr(request, "json", None)
    if not callable(json_fn):
        return {}
    try:
        raw = json_fn()
        if inspect.isawaitable(raw):
            return await raw  # type: ignore[misc]
        return raw
    except Exception:  # noqa: BLE001 - empty or invalid body reads as {}
        return {}


def register_routes(
    *,
    server: object | None = None,
    json_response: Any | None = None,
) -> bool:
    """Attach ``/ez_edit/*`` when PromptServer (or a stand-in) exists.

    Args:
        server: Optional PromptServer stand-in with ``routes.get`` / ``post``.
        json_response: Optional ``(payload, status=)`` factory. Defaults to
            aiohttp ``web.json_response`` when that import works.

    Returns:
        True when routes were registered.
    """
    responder = json_response
    if responder is None:
        try:
            from aiohttp import web

            responder = web.json_response
        except Exception:  # noqa: BLE001 - optional in pytest
            return False
    inst = server
    if inst is None:
        try:
            server_mod = __import__("server")
            prompt_server = getattr(server_mod, "PromptServer", None)
            inst = getattr(prompt_server, "instance", None)
        except Exception:  # noqa: BLE001 - Comfy optional in pytest
            return False
        if inst is None:
            return False
    routes = getattr(inst, "routes", None)
    if routes is None:
        return False

    def make_get(handler: Callable[..., Payload]) -> Callable[[object], Any]:
        """Bind one pure handler to a ``async def(request)`` GET endpoint.

        Args:
            handler: Pure ``handle_*`` function.

        Returns:
            The endpoint aiohttp can register.
        """

        async def endpoint(request: object) -> object:
            """Serve the route from the request query.

            Args:
                request: aiohttp request with a ``query`` mapping.

            Returns:
                JSON response from ``handler``.
            """
            query = getattr(request, "query", {}) or {}
            status, payload = handler(dict(query), deps=make_deps())
            return responder(payload, status=status)

        return endpoint

    def make_post(handler: Callable[..., Payload]) -> Callable[[object], Any]:
        """Bind one pure handler to a ``async def(request)`` POST endpoint.

        Args:
            handler: Pure ``handle_*`` function.

        Returns:
            The endpoint aiohttp can register.
        """

        async def endpoint(request: object) -> object:
            """Serve the route from the request JSON body.

            Args:
                request: aiohttp request with a ``json`` callable.

            Returns:
                JSON response from ``handler``.
            """
            body = await _read_json_body(request)
            args = body if isinstance(body, dict) else {}
            status, payload = handler(args, deps=make_deps())
            return responder(payload, status=status)

        return endpoint

    handlers: dict[str, Callable[..., Payload]] = {
        "/ez_edit/state": handle_state,
        "/ez_edit/ops": handle_ops,
        "/ez_edit/import": handle_import,
        "/ez_edit/render": handle_render,
        "/ez_edit/job": handle_job,
        "/ez_edit/chat": handle_chat,
        "/ez_edit/exec/pending": handle_exec_pending,
        "/ez_edit/exec/result": handle_exec_result,
        "/ez_edit/local_tools/sync": handle_local_sync,
        "/ez_edit/local_tools/pending": handle_local_pending,
        "/ez_edit/local_tools/result": handle_local_result,
        "/ez_edit/generate_clip": handle_generate_clip,
        "/ez_edit/export_edl": handle_export_edl,
    }

    adder_get = getattr(routes, "get", None)
    adder_post = getattr(routes, "post", None)
    if adder_get is None or adder_post is None:
        return False
    for path, method in ROUTE_METHODS.items():
        handler = handlers[path]
        adder = adder_get if method == "GET" else adder_post
        adder(path)(make_get(handler) if method == "GET" else make_post(handler))
    return True
