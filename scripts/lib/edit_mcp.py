#!/usr/bin/env python3
"""Host-side thin client of the ComfyUI ``/ez_edit`` routes (stdlib JSON-RPC).

The fourth in-tree MCP server: it runs on the host and exposes one typed tool
per :data:`custom_nodes/ez_edit/protocol.py::TOOL_CATALOG` name. Every thin
handler performs exactly one HTTP call to the matching route in
``custom_nodes/ez_edit/routes.py`` and hands the route payload straight back,
so the lane's business logic (timeline reducer, jobstore, occupancy gates)
stays in the container and the host agent, the panel, and this server all
speak one pinned vocabulary.

``_TOOL_CATALOG`` below is a deliberate mirror of the protocol catalog
(``scripts/lib`` does not import ``custom_nodes``); drift is a pytest failure,
not a comment. Typed tools only: no execute_code, no telemetry, no arbitrary
fetch_url. This server never queues a graph itself.
"""

from __future__ import annotations

import http.client
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict, cast

if TYPE_CHECKING:
    from ez_common import Json, JsonObject

from mcp_runtime import (
    JsonRpcRequest,
    JsonRpcResponse,
    ToolArgs,
    ToolCatalogEntry,
    ToolHandler,
    ToolNumber,
    ToolResult,
    ToolSpec,
    call_tool as _runtime_call_tool,
    handle_rpc as _runtime_handle_rpc,
    list_tools as _runtime_list_tools,
    main_cli,
    serve_stdio as _runtime_serve_stdio,
)

# MCP protocol identity (JSON-RPC initialize.serverInfo).
PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "ez-edit"
SERVER_VERSION = "1"

ENV_COMFY_URL = "EZ_EDIT_COMFY_URL"
"""ComfyUI origin override (mirrors ``protocol.ENV_COMFY_URL``)."""

ENV_COMFY_PORT = "COMFY_PORT"
"""Host Comfy port used when ``EZ_EDIT_COMFY_URL`` is unset."""

ENV_OUTPUT_DIR = "COMFY_OUTPUT_DIR"
"""Host occupancy root that holds ``.occupancy.json``."""

DEFAULT_COMFY_PORT = "8188"
"""Port default shared with ``occupancy_comfy_url``."""

DEFAULT_OUTPUT_DIR = "/mnt/comfy-output"
"""Host output bind used when ``COMFY_OUTPUT_DIR`` is unset."""

OCCUPANCY_FILE_NAME = ".occupancy.json"
"""Occupancy state file name under the output dir."""

UNKNOWN_OCCUPANCY = "unknown"
"""Occupancy mode reported when the state file cannot be read."""

REQUEST_TIMEOUT_S = 30.0
"""Socket timeout for one route call (renders are queued, not awaited)."""

UNREACHABLE_PREFIX = "comfyui unreachable:"
"""Error prefix when no socket could be opened to the ComfyUI origin."""

INVALID_JSON_ERROR = "comfyui returned invalid JSON"
"""Error text when a route replies with a non-JSON body."""

NON_OBJECT_ERROR = "comfyui returned a non-object reply"
"""Error text when a route replies with JSON that is not an object."""

class CatalogSchema(TypedDict, total=False):
    """One parameter schema authored alongside the mirrored catalog."""

    type: str
    """Always ``object`` for a tool argument object."""

    properties: JsonObject
    """Per-parameter JSON Schema bodies."""

    required: list[str]
    """Parameter names a call must carry."""


class ProtocolCatalogEntry(TypedDict):
    """One mirrored row of ``custom_nodes/ez_edit/protocol.py::TOOL_CATALOG``."""

    description: str
    """Human-facing tool summary."""

    parameters: CatalogSchema
    """JSON Schema for the tool arguments."""


# Mirror of custom_nodes/ez_edit/protocol.py::TOOL_CATALOG (pinned seam).
# tests/python/test_edit_mcp.py parses the protocol file with ast and fails
# on any drift; never edit one side alone.
_TOOL_CATALOG: dict[str, ProtocolCatalogEntry] = {
    "edit_get_state": {
        "description": "Return the current edit project (clips, overlays, "
        "captions) and its recent jobs. Pass project_id or empty for the "
        "most recently updated project.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "default": ""},
            },
        },
    },
    "edit_list_projects": {
        "description": "List every saved edit project as a summary row "
        "(id, title, fps, width, height, clip count, updated_at), newest "
        "first. Use it to find a project_id for the other tools.",
        "parameters": {"type": "object", "properties": {}},
    },
    "edit_import": {
        "description": "Import a media file already under the Comfy output "
        "dir as a clip (probes duration with ffprobe). Returns the clip.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "label": {"type": "string", "default": ""},
                "track": {"type": "integer", "default": 0},
            },
            "required": ["path"],
        },
    },
    "edit_apply_ops": {
        "description": "Apply an ordered list of timeline ops to a project "
        "and return the new project. Ops: project_create, add_clip, "
        "remove_clip, trim_clip, move_clip, set_track, set_transition, "
        "set_gain, add_overlay, remove_overlay, add_caption, "
        "remove_caption, set_title, clear. Unknown ops and ids fail the "
        "whole call.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "default": ""},
                "ops": {"type": "array", "items": {"type": "object"}},
            },
            "required": ["ops"],
        },
    },
    "edit_render": {
        "description": "Render a project. mode=server runs ffmpeg on the "
        "Spark (mp4, CPU); mode=client queues the timeline for the open "
        "browser panel to render with WebCodecs (webm on the laptop). "
        "Returns the job id - poll edit_job_status.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "default": ""},
                "mode": {"type": "string", "enum": ["server", "client"]},
                "client_id": {"type": "string", "default": ""},
            },
            "required": ["mode"],
        },
    },
    "edit_job_status": {
        "description": "Return one jobstore row by id.",
        "parameters": {
            "type": "object",
            "properties": {"job_id": {"type": "string"}},
            "required": ["job_id"],
        },
    },
    "edit_generate_clip": {
        "description": "Queue the editing-lane generate-cutaway graph "
        "(silent motion) to create a new clip from a text prompt. Heavy "
        "GPU job - refused unless occupancy allows. Returns the job id.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "duration_s": {"type": "number", "default": 5.0},
                "fps": {"type": "number", "default": 24.0},
            },
            "required": ["prompt"],
        },
    },
    "edit_export_edl": {
        "description": "Write the project as an edit decision list under "
        "the edit dir and return its path. format=json is this lane's own "
        "handoff document; format=cmx writes CMX 3600 text that DaVinci "
        "Resolve, Premiere, Kdenlive, and Shotcut import.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "default": ""},
                "format": {
                    "type": "string",
                    "enum": ["json", "cmx"],
                    "default": "json",
                },
            },
        },
    },
    "occupancy_status": {
        "description": "Return the current GPU occupancy mode string.",
        "parameters": {"type": "object", "properties": {}},
    },
}

ROUTES: dict[str, tuple[str, str]] = {
    "edit_get_state": ("GET", "/ez_edit/state"),
    "edit_list_projects": ("GET", "/ez_edit/projects"),
    "edit_import": ("POST", "/ez_edit/import"),
    "edit_apply_ops": ("POST", "/ez_edit/ops"),
    "edit_render": ("POST", "/ez_edit/render"),
    "edit_job_status": ("GET", "/ez_edit/job"),
    "edit_generate_clip": ("POST", "/ez_edit/generate_clip"),
    "edit_export_edl": ("POST", "/ez_edit/export_edl"),
}
"""Thin tool id -> (method, path) of the one route it calls."""


def _comfy_base() -> str:
    """Return the ComfyUI origin for route calls.

    Returns:
        ``EZ_EDIT_COMFY_URL`` when set, else ``http://127.0.0.1:<COMFY_PORT>``
        with port defaulting to 8188.
    """
    override = str(os.environ.get(ENV_COMFY_URL) or "").strip().rstrip("/")
    if override:
        return override
    port = str(os.environ.get(ENV_COMFY_PORT) or DEFAULT_COMFY_PORT).strip()
    return f"http://127.0.0.1:{port or DEFAULT_COMFY_PORT}"


def _output_dir() -> Path:
    """Return COMFY_OUTPUT_DIR (host occupancy root).

    Returns:
        Output directory path.
    """
    return Path(os.environ.get(ENV_OUTPUT_DIR, DEFAULT_OUTPUT_DIR))


def occupancy_mode() -> str:
    """Read the GPU occupancy mode string from the state file.

    Returns:
        ``mode`` field of ``${COMFY_OUTPUT_DIR}/.occupancy.json``, or
        ``unknown`` when the file is missing, unreadable, invalid JSON, not an
        object, or carries an empty mode.
    """
    path = _output_dir() / OCCUPANCY_FILE_NAME
    try:
        data: Json = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return UNKNOWN_OCCUPANCY
    if not isinstance(data, dict):
        return UNKNOWN_OCCUPANCY
    mode = str(data.get("mode") or "").strip()
    return mode or UNKNOWN_OCCUPANCY


def _urlopen(
    request: urllib.request.Request, timeout: float
) -> http.client.HTTPResponse:
    """Indirection so pytest can stub HTTP (mirrors ``agent.AgentLLM._urlopen``).

    Args:
        request: Prepared request for one ``/ez_edit`` route.
        timeout: Socket timeout in seconds.

    Returns:
        Opened HTTP response (caller closes it).
    """
    # mypy's bundled typeshed leaves module-level urlopen untyped; an
    # http/https origin always yields an HTTPResponse.
    opened = urllib.request.urlopen(request, timeout=timeout)
    return cast(http.client.HTTPResponse, opened)


def _decode(raw: bytes | str) -> ToolResult:
    """Decode one route reply body.

    Args:
        raw: Response body.

    Returns:
        The JSON object, or an ``ok`` false payload when it is not one.
    """
    try:
        parsed: Json = json.loads(raw)
    except ValueError:
        return {"ok": False, "error": INVALID_JSON_ERROR}
    if not isinstance(parsed, dict):
        return {"ok": False, "error": NON_OBJECT_ERROR}
    return parsed


def _http_error_payload(path: str, exc: urllib.error.HTTPError) -> ToolResult:
    """Turn an HTTP error status into a tool payload.

    The route's own JSON body wins when it carries one (a disabled lane answers
    403 with ``{ok: false, error: "disabled"}``); otherwise the status line
    becomes the error text.

    Args:
        path: Route path (for the fallback message).
        exc: Raised HTTP error.

    Returns:
        ``ok`` false payload (JSON boundary).
    """
    try:
        body: Json = json.loads(exc.read())
    except (OSError, ValueError):
        body = None
    if isinstance(body, dict) and body:
        payload: JsonObject = dict(body)
        payload["ok"] = False
        payload["error"] = str(payload.get("error") or f"{path} -> HTTP {exc.code}")
        return payload
    return {"ok": False, "error": f"{path} -> HTTP {exc.code} {exc.reason}"}


def _http(
    method: str, path: str, body: dict[str, object] | None = None
) -> ToolResult:
    """Open one socket to one route and decode its reply.

    Args:
        method: ``GET`` or ``POST``.
        path: Route path, optionally with a query string.
        body: JSON object sent as the POST body (None for GET).

    Returns:
        Route reply object, or an ``ok`` false payload on any wire/JSON failure.
    """
    url = f"{_comfy_base()}{path}"
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with _urlopen(request, REQUEST_TIMEOUT_S) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        return _http_error_payload(path, exc)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return {"ok": False, "error": f"{UNREACHABLE_PREFIX} {exc}"}
    return _decode(raw)


def _int_arg(args: ToolArgs, key: str, default: int) -> int:
    """Read one integer argument across the loose JSON boundary.

    Args:
        args: Tool arguments.
        key: Parameter name.
        default: Value when the key is absent or not a number.

    Returns:
        Integer value for the request body.
    """
    try:
        return int(cast(ToolNumber, args.get(key, default)))
    except (TypeError, ValueError):
        return default


def _float_arg(args: ToolArgs, key: str, default: float) -> float:
    """Read one number argument across the loose JSON boundary.

    Args:
        args: Tool arguments.
        key: Parameter name.
        default: Value when the key is absent or not a number.

    Returns:
        Float value for the request body.
    """
    try:
        return float(cast(ToolNumber, args.get(key, default)))
    except (TypeError, ValueError):
        return default


def _is_empty(value: object) -> bool:
    """True when a required parameter carries no usable value.

    Args:
        value: Normalized request value.

    Returns:
        True for None, a blank string, or an empty list/dict.
    """
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict)):
        return not value
    return False


def _missing_required(name: str, payload: ToolArgs) -> list[str]:
    """Catalog-required keys that one call leaves empty.

    Args:
        name: Tool id.
        payload: Normalized request parameters.

    Returns:
        Missing key names in catalog order (empty when the call is complete).
    """
    entry = _TOOL_CATALOG.get(name)
    parameters: CatalogSchema = entry["parameters"] if entry is not None else {}
    required = parameters.get("required") or []
    return [str(key) for key in required if _is_empty(payload.get(key))]


def _call_route(name: str, payload: ToolArgs) -> ToolResult:
    """Call the single route bound to a thin tool (the one HTTP funnel).

    Args:
        name: Thin tool id (a key of :data:`ROUTES`).
        payload: Request parameters (query string for GET, JSON body for POST).

    Returns:
        Route reply object, or an ``ok`` false payload for an incomplete call
        or any wire/JSON failure.
    """
    missing = _missing_required(name, payload)
    if missing:
        return {
            "ok": False,
            "error": f"{name}: missing required {', '.join(missing)}",
        }
    method, path = ROUTES[name]
    if method == "GET":
        query = {key: str(value) for key, value in payload.items()}
        suffix = f"?{urllib.parse.urlencode(query)}" if query else ""
        return _http("GET", f"{path}{suffix}")
    return _http("POST", path, body=dict(payload))


def tool_edit_get_state(args: ToolArgs) -> ToolResult:
    """MCP tool: current project plus its recent jobs.

    Args:
        args: ``project_id`` (empty selects the most recent project).

    Returns:
        ``{ok, project, jobs, enabled}`` from ``GET /ez_edit/state``.
    """
    return _call_route(
        "edit_get_state", {"project_id": str(args.get("project_id") or "")}
    )


def tool_edit_list_projects(args: ToolArgs) -> ToolResult:
    """MCP tool: summary row for every stored project.

    Args:
        args: Unused tool arguments.

    Returns:
        ``{ok, projects, enabled}`` from ``GET /ez_edit/projects``.
    """
    del args
    return _call_route("edit_list_projects", {})


def tool_edit_import(args: ToolArgs) -> ToolResult:
    """MCP tool: import an output-dir media file as a clip.

    Args:
        args: ``path`` (required), ``label``, ``track``.

    Returns:
        ``{ok, clip}`` from ``POST /ez_edit/import``.
    """
    return _call_route(
        "edit_import",
        {
            "path": str(args.get("path") or ""),
            "label": str(args.get("label") or ""),
            "track": _int_arg(args, "track", 0),
        },
    )


def tool_edit_apply_ops(args: ToolArgs) -> ToolResult:
    """MCP tool: apply ordered timeline ops to a project.

    Args:
        args: ``ops`` (required list), ``project_id``.

    Returns:
        ``{ok, project}`` from ``POST /ez_edit/ops``.
    """
    ops = args.get("ops")
    return _call_route(
        "edit_apply_ops",
        {
            "project_id": str(args.get("project_id") or ""),
            "ops": list(ops) if isinstance(ops, list) else [],
        },
    )


def tool_edit_render(args: ToolArgs) -> ToolResult:
    """MCP tool: queue a server or client render.

    Args:
        args: ``mode`` (required, ``server`` or ``client``), ``project_id``,
            ``client_id``.

    Returns:
        ``{ok, job}`` from ``POST /ez_edit/render``.
    """
    return _call_route(
        "edit_render",
        {
            "project_id": str(args.get("project_id") or ""),
            "mode": str(args.get("mode") or ""),
            "client_id": str(args.get("client_id") or ""),
        },
    )


def tool_edit_job_status(args: ToolArgs) -> ToolResult:
    """MCP tool: read one jobstore row.

    Args:
        args: ``job_id`` (required).

    Returns:
        ``{ok, job}`` from ``GET /ez_edit/job``.
    """
    return _call_route("edit_job_status", {"job_id": str(args.get("job_id") or "")})


def tool_edit_generate_clip(args: ToolArgs) -> ToolResult:
    """MCP tool: queue the generate-cutaway graph (heavy GPU, route-gated).

    Args:
        args: ``prompt`` (required), ``duration_s``, ``fps``.

    Returns:
        ``{ok, job}`` from ``POST /ez_edit/generate_clip``.
    """
    return _call_route(
        "edit_generate_clip",
        {
            "prompt": str(args.get("prompt") or ""),
            "duration_s": _float_arg(args, "duration_s", 5.0),
            "fps": _float_arg(args, "fps", 24.0),
        },
    )


def tool_edit_export_edl(args: ToolArgs) -> ToolResult:
    """MCP tool: write the project EDL for an external editor.

    Args:
        args: ``project_id``, ``format`` (``json`` or ``cmx``).

    Returns:
        ``{ok, path}`` from ``POST /ez_edit/export_edl``.
    """
    return _call_route(
        "edit_export_edl",
        {
            "project_id": str(args.get("project_id") or ""),
            "format": str(args.get("format") or "json"),
        },
    )


def tool_occupancy_status(_args: ToolArgs) -> ToolResult:
    """MCP tool: read the GPU occupancy mode (no HTTP).

    Args:
        _args: Unused tool arguments.

    Returns:
        ``{ok, mode}`` with ``unknown`` when the state file is unreadable.
    """
    return {"ok": True, "mode": occupancy_mode()}


def _spec(name: str, handler: ToolHandler) -> ToolSpec:
    """Wrap one mirrored catalog entry and its handler as an MCP tool.

    Args:
        name: Tool id (also the catalog key).
        handler: Handler for this tool.

    Returns:
        MCP tool spec (description and schema come from the catalog only).
    """
    entry = _TOOL_CATALOG[name]
    return {
        "description": str(entry["description"]),
        "inputSchema": dict(entry["parameters"]),
        "handler": handler,
    }


# Typed MCP tool table: exactly one tool per protocol.TOOL_CATALOG name.
TOOLS: dict[str, ToolSpec] = {
    "edit_get_state": _spec("edit_get_state", tool_edit_get_state),
    "edit_list_projects": _spec("edit_list_projects", tool_edit_list_projects),
    "edit_import": _spec("edit_import", tool_edit_import),
    "edit_apply_ops": _spec("edit_apply_ops", tool_edit_apply_ops),
    "edit_render": _spec("edit_render", tool_edit_render),
    "edit_job_status": _spec("edit_job_status", tool_edit_job_status),
    "edit_generate_clip": _spec("edit_generate_clip", tool_edit_generate_clip),
    "edit_export_edl": _spec("edit_export_edl", tool_edit_export_edl),
    "occupancy_status": _spec("occupancy_status", tool_occupancy_status),
}


def list_tools() -> list[ToolCatalogEntry]:
    """List MCP tools without handlers.

    Returns:
        ``{name, description, inputSchema}`` rows.
    """
    return _runtime_list_tools(TOOLS)


def call_tool(name: str, arguments: ToolArgs | None = None) -> ToolResult:
    """Dispatch a named MCP tool.

    Args:
        name: Tool id.
        arguments: JSON-object arguments (JSON boundary).

    Returns:
        Tool payload (``ok`` false on unknown tool or missing required args).
    """
    return _runtime_call_tool(TOOLS, name, arguments)


def handle_rpc(message: JsonRpcRequest) -> JsonRpcResponse | None:
    """Handle one JSON-RPC message. Notifications return None.

    Args:
        message: Parsed JSON-RPC request (JSON boundary).

    Returns:
        Response object, or None for notifications.
    """
    return _runtime_handle_rpc(
        message,
        tools=TOOLS,
        server_name=SERVER_NAME,
        server_version=SERVER_VERSION,
        protocol_version=PROTOCOL_VERSION,
    )


def serve_stdio() -> None:
    """Serve JSON-RPC on stdin/stdout (one JSON object per line)."""
    _runtime_serve_stdio(handle_rpc)


def main(argv: list[str] | None = None) -> int:
    """CLI: --stdio | --list-tools | --call TOOL [JSON].

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Process status.
    """
    return main_cli(
        argv,
        tools=TOOLS,
        prog="edit_mcp.py",
        usage_extra=(
            "Typed tools only; no execute_code, no telemetry, "
            "no arbitrary fetch_url."
        ),
        handle=handle_rpc,
    )


if __name__ == "__main__":
    raise SystemExit(main())
