#!/usr/bin/env python3
"""Occupancy-aware studio MCP (stdlib JSON-RPC).

Typed tools: occupancy, lab-template discovery, clone/stamp/save into _user/.
No execute_code, no telemetry, no Queue, no Comfy Cloud.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Mapping, TypedDict, cast

# MCP protocol identity (JSON-RPC initialize.serverInfo).
PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "ez-studio"
SERVER_VERSION = "1"

RpcId = str | int | None
ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


class ToolSpec(TypedDict):
    """One MCP tool: description, JSON Schema, handler."""

    description: str
    inputSchema: dict[str, Any]
    handler: ToolHandler


def _repo_root() -> Path:
    """Return the repository root (parent of ``scripts/``).

    Returns:
        Absolute repo path.
    """
    return Path(__file__).resolve().parents[2]


def _ensure_custom_nodes_path() -> None:
    """Prepend ``custom_nodes/`` so ez_studio_forge imports resolve."""
    custom = str(_repo_root() / "custom_nodes")
    if custom not in sys.path:
        sys.path.insert(0, custom)


_ensure_custom_nodes_path()


def _output_dir() -> Path:
    """Return COMFY_OUTPUT_DIR (host occupancy root).

    Returns:
        Output directory path.
    """
    return Path(os.environ.get("COMFY_OUTPUT_DIR", "/mnt/comfy-output"))


def occupancy_status() -> dict[str, Any]:
    """Read occupancy JSON from COMFY_OUTPUT_DIR.

    Returns:
        Occupancy mapping (JSON boundary).
    """
    path = _output_dir() / ".occupancy.json"
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
    return {
        "version": 1,
        "mode": "idle",
        "compose": False,
        "parked": False,
        "blender_pid": 0,
        "mcp_pid": 0,
        "llm_pid": 0,
    }


def tool_occupancy_status(_args: dict[str, Any]) -> dict[str, Any]:
    """MCP tool: read occupancy JSON.

    Args:
        _args: Unused tool arguments.

    Returns:
        ``{ok, occupancy}``.
    """
    return {"ok": True, "occupancy": occupancy_status()}


def tool_search_templates(args: dict[str, Any]) -> dict[str, Any]:
    """MCP tool: search shipped lab Apps and studio-block ids.

    Args:
        args: Optional ``query``/``q``, ``occupancy``, ``lane``.

    Returns:
        ``{ok, templates, count}``.
    """
    from ez_studio_forge.pipeline import list_templates

    rows = list_templates(
        query=str(args.get("query") or args.get("q") or ""),
        occupancy=str(args.get("occupancy") or ""),
        lane=str(args.get("lane") or ""),
    )
    return {"ok": True, "templates": rows, "count": len(rows)}


def tool_get_template(args: dict[str, Any]) -> dict[str, Any]:
    """MCP tool: describe one lab App or studio-block.

    Args:
        args: ``stem``, ``id``, or ``template``.

    Returns:
        Template description payload.
    """
    from ez_studio_forge.pipeline import describe_template

    stem = str(args.get("stem") or args.get("id") or args.get("template") or "")
    return describe_template(stem)


def tool_describe_app(args: dict[str, Any]) -> dict[str, Any]:
    """MCP tool: alias of get_template for lab Apps.

    Args:
        args: ``stem`` (required by schema).

    Returns:
        Template description payload.
    """
    return tool_get_template(args)


def tool_apply_slots(args: dict[str, Any]) -> dict[str, Any]:
    """MCP tool: clone a lab graph and patch named slots (no disk write).

    Args:
        args: ``stem`` (required), optional ``slots`` object.

    Returns:
        Cloned graph payload or error.
    """
    from ez_studio_forge.pipeline import ForgeError, apply_slots, clone_template

    stem = str(args.get("stem") or args.get("template") or "")
    slots = args.get("slots") or {}
    if not isinstance(slots, dict):
        return {"ok": False, "error": "slots must be an object"}
    try:
        origin, graph = clone_template(stem)
        apply_slots(graph, slots)
    except ForgeError as exc:
        return {"ok": False, "error": str(exc)}
    extra = graph.get("extra") or {}
    return {
        "ok": True,
        "template": origin,
        "graph": graph,
        "widgets": list((extra.get("linearData") or {}).get("inputs") or [])
        if isinstance(extra, dict)
        else [],
    }


def tool_validate_workflow(args: dict[str, Any]) -> dict[str, Any]:
    """MCP tool: check banned strings, Vue-corrected renderer, linear ids.

    Args:
        args: Optional ``stem``, ``graph``, ``slug``.

    Returns:
        ``{ok, errors}``.
    """
    from ez_studio_forge.pipeline import clone_template, validate_workflow

    stem = str(args.get("stem") or args.get("template") or "")
    graph = args.get("graph")
    if not isinstance(graph, dict):
        if not stem:
            return {"ok": False, "error": "missing graph or stem"}
        try:
            _origin, graph = clone_template(stem)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}
    errors = validate_workflow(
        graph,
        slug=str(args.get("slug") or ""),
    )
    return {"ok": not errors, "errors": errors}


def _save_from_args(args: dict[str, Any], *, force_app: bool | None) -> dict[str, Any]:
    """Clone, stamp, and write a lab graph into live ``_user/``.

    Args:
        args: ``stem``/``template``, ``slug``, optional slots/overwrite/as_app.
        force_app: True forces App view; False forces workflow; None uses args.

    Returns:
        Save payload or ForgeError mapping.
    """
    from ez_studio_forge.pipeline import (
        ForgeError,
        apply_slots,
        clone_template,
        restamp_identity,
        save_workflow,
        slugify,
        validate_slug,
    )

    stem = str(args.get("stem") or args.get("template") or "")
    slug = str(args.get("slug") or "")
    slots = args.get("slots") if isinstance(args.get("slots"), dict) else {}
    overwrite = bool(args.get("overwrite") or False)
    try:
        origin, graph = clone_template(stem)
        if slots:
            apply_slots(graph, slots)
        clean = validate_slug(slug or slugify(origin.replace("/", "-")))
        restamp_identity(graph, origin=origin, slug=clean)
        if force_app is True:
            mode = graph.setdefault("extra", {}).setdefault("lab_app_mode", {})
            if isinstance(mode, dict):
                mode["default_view"] = "app"
                mode["enabled"] = True
            graph["extra"]["linearMode"] = True
            as_app = True
        elif force_app is False:
            as_app = False
        else:
            as_app = bool(args.get("as_app", True))
        dest = save_workflow(
            graph, slug=clean, as_app=as_app, overwrite=overwrite
        )
    except ForgeError as exc:
        return {"ok": False, "error": str(exc)}
    return {
        "ok": True,
        "path": str(dest),
        "template": origin,
        "slug": clean,
        "as_app": as_app,
    }


def tool_save_workflow(args: dict[str, Any]) -> dict[str, Any]:
    """MCP tool: clone a lab graph into live ``_user/`` (never writes ``_lab``).

    Args:
        args: ``stem`` and ``slug`` (required), optional as_app/overwrite/slots.

    Returns:
        Save payload or error.
    """
    return _save_from_args(args, force_app=None)


def tool_create_app(args: dict[str, Any]) -> dict[str, Any]:
    """MCP tool: clone a lab graph into live ``_user/`` as an App.

    Args:
        args: ``stem`` and ``slug`` (required), optional overwrite/slots.

    Returns:
        Save payload or error.
    """
    return _save_from_args(args, force_app=True)


def tool_generate_app(args: dict[str, Any]) -> dict[str, Any]:
    """MCP tool: pick a lab template from a brief and write ``_user/``.

    Args:
        args: ``brief`` (required), optional template/slug/as_app/overwrite/slots.

    Returns:
        Generate payload (may include ``error``).
    """
    from ez_studio_forge.pipeline import generate_app

    brief = str(args.get("brief") or args.get("prompt") or args.get("message") or "")
    template = str(args.get("template") or "auto")
    slug = str(args.get("slug") or "")
    as_app = args.get("as_app")
    overwrite = bool(args.get("overwrite") or False)
    slots = args.get("slots") if isinstance(args.get("slots"), dict) else None
    result = generate_app(
        brief,
        template=template,
        slug=slug,
        as_app=as_app,
        overwrite=overwrite,
        slots=slots,
    )
    payload: dict[str, Any] = {
        "ok": result.ok,
        "path": result.path,
        "template": result.template,
        "occupancy": result.occupancy,
        "widgets": result.widgets,
        "slug": result.slug,
        "as_app": result.as_app,
        "reason": result.reason,
        "status": result.status,
    }
    if result.error:
        payload["error"] = result.error
    return payload


# Typed MCP tool table (names are the public tool ids).
TOOLS: dict[str, ToolSpec] = {
    "occupancy_status": {
        "description": "Read GB10 occupancy mode, parked flag, and PIDs.",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": tool_occupancy_status,
    },
    "search_templates": {
        "description": (
            "Search shipped lab Apps and studio-block ids "
            "(id, occupancy, widgets, kind)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "occupancy": {"type": "string"},
                "lane": {"type": "string"},
            },
        },
        "handler": tool_search_templates,
    },
    "get_template": {
        "description": (
            "Describe one lab App or studio-block: occupancy, widgets, handoff."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"stem": {"type": "string"}},
            "required": ["stem"],
        },
        "handler": tool_get_template,
    },
    "describe_app": {
        "description": "Alias of get_template for lab Apps.",
        "inputSchema": {
            "type": "object",
            "properties": {"stem": {"type": "string"}},
            "required": ["stem"],
        },
        "handler": tool_describe_app,
    },
    "apply_slots": {
        "description": (
            "Clone a lab graph and patch widgets_values for named slots. "
            "Does not write disk."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "stem": {"type": "string"},
                "slots": {"type": "object"},
            },
            "required": ["stem"],
        },
        "handler": tool_apply_slots,
    },
    "validate_workflow": {
        "description": (
            "Check banned strings, Vue-corrected renderer, integer linear ids."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "stem": {"type": "string"},
                "graph": {"type": "object"},
                "slug": {"type": "string"},
            },
        },
        "handler": tool_validate_workflow,
    },
    "save_workflow": {
        "description": (
            "Clone a lab graph into live _user/. Never writes _lab. No Queue."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "stem": {"type": "string"},
                "slug": {"type": "string"},
                "as_app": {"type": "boolean"},
                "overwrite": {"type": "boolean"},
                "slots": {"type": "object"},
            },
            "required": ["stem", "slug"],
        },
        "handler": tool_save_workflow,
    },
    "create_app": {
        "description": (
            "Clone a lab graph into live _user/ as an App (*.app.json)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "stem": {"type": "string"},
                "slug": {"type": "string"},
                "overwrite": {"type": "boolean"},
                "slots": {"type": "object"},
            },
            "required": ["stem", "slug"],
        },
        "handler": tool_create_app,
    },
    "generate_app": {
        "description": (
            "Pick a lab template from a brief, clone, stamp, write _user/. "
            "CPU GGUF or keyword heuristic. Does not Queue Comfy."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "brief": {"type": "string"},
                "template": {"type": "string"},
                "slug": {"type": "string"},
                "as_app": {"type": "boolean"},
                "overwrite": {"type": "boolean"},
                "slots": {"type": "object"},
            },
            "required": ["brief"],
        },
        "handler": tool_generate_app,
    },
}


def list_tools() -> list[dict[str, Any]]:
    """List MCP tools without handlers.

    Returns:
        ``{name, description, inputSchema}`` rows.
    """
    return [
        {
            "name": name,
            "description": spec["description"],
            "inputSchema": spec["inputSchema"],
        }
        for name, spec in TOOLS.items()
    ]


def call_tool(name: str, arguments: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Dispatch a named MCP tool.

    Args:
        name: Tool id.
        arguments: JSON-object arguments (JSON boundary).

    Returns:
        Tool payload (``ok`` false on unknown tool).
    """
    spec = TOOLS.get(name)
    if spec is None:
        return {"ok": False, "error": f"unknown tool {name}"}
    handler: ToolHandler = spec["handler"]
    return handler(dict(arguments or {}))


def _rpc_result(msg_id: RpcId, result: object) -> dict[str, Any]:
    """Build a JSON-RPC 2.0 success envelope.

    Args:
        msg_id: Request id (string, number, or null).
        result: Method result payload.

    Returns:
        JSON-RPC response object.
    """
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _rpc_error(msg_id: RpcId, code: int, message: str) -> dict[str, Any]:
    """Build a JSON-RPC 2.0 error envelope.

    Args:
        msg_id: Request id (string, number, or null).
        code: JSON-RPC error code.
        message: Error text.

    Returns:
        JSON-RPC error object.
    """
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def handle_rpc(message: dict[str, Any]) -> dict[str, Any] | None:
    """Handle one JSON-RPC message. Notifications return None.

    Args:
        message: Parsed JSON-RPC request (JSON boundary).

    Returns:
        Response object, or None for notifications.
    """
    method = str(message.get("method") or "")
    msg_id = cast(RpcId, message.get("id"))
    params = message.get("params") or {}
    if method == "notifications/initialized":
        return None
    if method == "initialize":
        return _rpc_result(
            msg_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        )
    if method == "ping":
        return _rpc_result(msg_id, {})
    if method == "tools/list":
        return _rpc_result(msg_id, {"tools": list_tools()})
    if method == "tools/call":
        name = str(params.get("name") or "")
        arguments = params.get("arguments") or {}
        payload = call_tool(name, arguments if isinstance(arguments, dict) else {})
        text = json.dumps(payload)
        return _rpc_result(
            msg_id,
            {"content": [{"type": "text", "text": text}], "isError": not payload.get("ok", True)},
        )
    if msg_id is None:
        return None
    return _rpc_error(msg_id, -32601, f"method not found: {method}")


def serve_stdio() -> None:
    """Serve JSON-RPC on stdin/stdout (one JSON object per line)."""
    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(message, dict):
            continue
        reply = handle_rpc(message)
        if reply is not None:
            sys.stdout.write(json.dumps(reply) + "\n")
            sys.stdout.flush()


def main(argv: list[str] | None = None) -> int:
    """CLI: --stdio | --list-tools | --call TOOL [JSON].

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Process status.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("--stdio", "stdio"):
        serve_stdio()
        return 0
    if args[0] in ("-h", "--help", "help"):
        sys.stderr.write(
            "Usage: studio_mcp.py [--stdio] | --list-tools | --call TOOL [JSON]\n"
            "  Occupancy-aware studio MCP. No execute_code. No telemetry. No Queue.\n"
        )
        return 0
    if args[0] == "--list-tools":
        json.dump(list_tools(), sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    if args[0] == "--call":
        if len(args) < 2:
            sys.stderr.write("studio_mcp.py --call TOOL [JSON args]\n")
            return 1
        payload: dict[str, Any] = {}
        if len(args) >= 3:
            payload = json.loads(args[2])
        result = call_tool(args[1], payload)
        json.dump(result, sys.stdout)
        sys.stdout.write("\n")
        return 0 if result.get("ok", True) else 1
    sys.stderr.write(f"unknown arg: {args[0]}\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
