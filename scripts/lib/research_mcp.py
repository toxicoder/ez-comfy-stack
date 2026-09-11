#!/usr/bin/env python3
"""Occupancy-aware creative research MCP (stdlib JSON-RPC).

Typed tools: occupancy, lab-app discovery, chat, web_search, research.
No execute_code, no telemetry, no arbitrary URL fetch.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Mapping

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "ez-research"
SERVER_VERSION = "1"

ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _ensure_custom_nodes_path() -> None:
    custom = str(_repo_root() / "custom_nodes")
    if custom not in sys.path:
        sys.path.insert(0, custom)


_ensure_custom_nodes_path()


def _output_dir() -> Path:
    return Path(os.environ.get("COMFY_OUTPUT_DIR", "/mnt/comfy-output"))


def _lab_root() -> Path:
    return _repo_root() / "workflows" / "_lab"


def occupancy_status() -> dict[str, Any]:
    """Read occupancy JSON from COMFY_OUTPUT_DIR."""
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


def _linear_labels(extra: Mapping[str, Any]) -> list[str]:
    linear = extra.get("linearData") or {}
    labels: list[str] = []
    inputs = linear.get("inputs") if isinstance(linear, dict) else None
    if not isinstance(inputs, list):
        return labels
    for entry in inputs:
        if not isinstance(entry, list) or len(entry) < 2:
            continue
        config = entry[2] if len(entry) > 2 and isinstance(entry[2], dict) else {}
        label = config.get("label") if isinstance(config, dict) else None
        labels.append(str(label or entry[1]))
    return labels


def _load_lab_graph(stem: str) -> tuple[Path, dict[str, Any]] | None:
    name = Path(str(stem or "")).name
    if not name:
        return None
    if not name.endswith(".json"):
        name = f"{name}.json"
    hits = sorted(p for p in _lab_root().rglob(name) if p.is_file())
    if len(hits) != 1:
        return None
    try:
        data = json.loads(hits[0].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return hits[0], data


def tool_occupancy_status(_args: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, "occupancy": occupancy_status()}


def tool_list_lab_apps(_args: dict[str, Any]) -> dict[str, Any]:
    apps: list[dict[str, Any]] = []
    root = _lab_root()
    if not root.is_dir():
        return {"ok": True, "apps": [], "count": 0}
    for path in sorted(root.rglob("*-lab-example.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        extra = data.get("extra") or {}
        if not isinstance(extra, dict):
            extra = {}
        mode = extra.get("lab_app_mode") or {}
        if not isinstance(mode, dict):
            mode = {}
        rel = path.relative_to(root)
        lane = str(mode.get("lane") or (rel.parts[0] if rel.parts else ""))
        apps.append(
            {
                "id": str(data.get("id") or path.stem),
                "lane": lane,
                "occupancy": mode.get("occupancy"),
                "handoff": list(mode.get("handoff") or []),
                "description": str(extra.get("lab_description") or ""),
            }
        )
    return {"ok": True, "apps": apps, "count": len(apps)}


def tool_describe_app(args: dict[str, Any]) -> dict[str, Any]:
    stem = str(args.get("stem") or args.get("id") or "")
    loaded = _load_lab_graph(stem)
    if loaded is None:
        return {"ok": False, "error": f"unknown app {stem}"}
    path, data = loaded
    extra = data.get("extra") or {}
    if not isinstance(extra, dict):
        extra = {}
    mode = extra.get("lab_app_mode") or {}
    if not isinstance(mode, dict):
        mode = {}
    mcp = extra.get("lab_mcp") or {}
    if not isinstance(mcp, dict):
        mcp = {}
    return {
        "ok": True,
        "id": str(data.get("id") or path.stem),
        "path": str(path.relative_to(_repo_root())),
        "lab_note": str(extra.get("lab_note") or ""),
        "description": str(extra.get("lab_description") or ""),
        "occupancy": mode.get("occupancy"),
        "lane": mode.get("lane"),
        "handoff": list(mode.get("handoff") or []),
        "widgets": _linear_labels(extra),
        "lab_mcp": mcp,
    }


def tool_chat(args: dict[str, Any]) -> dict[str, Any]:
    from ez_research.pipeline import run_chat, write_brief

    message = str(args.get("message") or args.get("prompt") or "")
    history = str(args.get("history") or "")
    web_search = bool(args.get("web_search") or False)
    result = run_chat(message, history=history, web_search=web_search)
    path = write_brief(result, message)
    return {
        "ok": True,
        "text": result.text,
        "sources": result.sources,
        "status": result.status,
        "queries": result.queries,
        "brief": str(path) if path else "",
    }


def tool_web_search(args: dict[str, Any]) -> dict[str, Any]:
    from ez_research.search import format_sources, search_web

    query = str(args.get("query") or args.get("q") or "")
    hits = search_web(query, limit=5, fetch_bodies=False)
    return {
        "ok": True,
        "query": query,
        "hits": [
            {"title": hit.title, "url": hit.url, "snippet": hit.snippet}
            for hit in hits
        ],
        "sources": format_sources(hits),
    }


def tool_research(args: dict[str, Any]) -> dict[str, Any]:
    from ez_research.pipeline import run_research, write_brief

    message = str(args.get("message") or args.get("prompt") or "")
    history = str(args.get("history") or "")
    web_search = args.get("web_search")
    do_search = True if web_search is None else bool(web_search)
    subagents = args.get("subagents", 2)
    result = run_research(
        message,
        history=history,
        web_search=do_search,
        subagents=subagents,
    )
    path = write_brief(result, message)
    return {
        "ok": True,
        "text": result.text,
        "sources": result.sources,
        "status": result.status,
        "queries": result.queries,
        "brief": str(path) if path else "",
    }


TOOLS: dict[str, dict[str, Any]] = {
    "occupancy_status": {
        "description": "Read GB10 occupancy mode, parked flag, and PIDs.",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": tool_occupancy_status,
    },
    "list_lab_apps": {
        "description": (
            "List shipped *-lab-example Apps (id, lane, occupancy, handoff)."
        ),
        "inputSchema": {"type": "object", "properties": {}},
        "handler": tool_list_lab_apps,
    },
    "describe_app": {
        "description": (
            "Describe one lab App: occupancy, widgets, handoff, lab_mcp."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"stem": {"type": "string"}},
            "required": ["stem"],
        },
        "handler": tool_describe_app,
    },
    "chat": {
        "description": (
            "One-turn creative-process chat (CPU Qwen3-4B). Optional web_search."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "history": {"type": "string"},
                "web_search": {"type": "boolean"},
            },
            "required": ["message"],
        },
        "handler": tool_chat,
    },
    "web_search": {
        "description": (
            "SSRF-safe HTTPS search (Wikipedia + DuckDuckGo). Titles, snippets, URLs."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        "handler": tool_web_search,
    },
    "research": {
        "description": (
            "Planner + sequential search subagents + synthesizer. Creative brief."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "history": {"type": "string"},
                "web_search": {"type": "boolean"},
                "subagents": {"type": "integer"},
            },
            "required": ["message"],
        },
        "handler": tool_research,
    },
}


def list_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "description": spec["description"],
            "inputSchema": spec["inputSchema"],
        }
        for name, spec in TOOLS.items()
    ]


def call_tool(name: str, arguments: Mapping[str, Any] | None = None) -> dict[str, Any]:
    spec = TOOLS.get(name)
    if spec is None:
        return {"ok": False, "error": f"unknown tool {name}"}
    handler: ToolHandler = spec["handler"]
    return handler(dict(arguments or {}))


def _rpc_result(msg_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _rpc_error(msg_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def handle_rpc(message: dict[str, Any]) -> dict[str, Any] | None:
    """Handle one JSON-RPC message. Notifications return None."""
    method = str(message.get("method") or "")
    msg_id = message.get("id")
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
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("--stdio", "stdio"):
        serve_stdio()
        return 0
    if args[0] in ("-h", "--help", "help"):
        sys.stderr.write(
            "Usage: research_mcp.py [--stdio] | --list-tools | --call TOOL [JSON]\n"
            "  Occupancy-aware research MCP. No execute_code. No telemetry.\n"
        )
        return 0
    if args[0] == "--list-tools":
        json.dump(list_tools(), sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    if args[0] == "--call":
        if len(args) < 2:
            sys.stderr.write("research_mcp.py --call TOOL [JSON args]\n")
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
