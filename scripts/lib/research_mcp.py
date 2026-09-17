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
from typing import Any, Mapping

from mcp_runtime import (
    ToolSpec,
    call_tool as _runtime_call_tool,
    handle_rpc as _runtime_handle_rpc,
    list_tools as _runtime_list_tools,
    main_cli,
    serve_stdio as _runtime_serve_stdio,
)

# MCP protocol identity (JSON-RPC initialize.serverInfo).
PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "ez-research"
SERVER_VERSION = "1"


def _repo_root() -> Path:
    """Return the repository root (parent of ``scripts/``).

    Returns:
        Absolute repo path.
    """
    return Path(__file__).resolve().parents[2]


def _ensure_custom_nodes_path() -> None:
    """Prepend ``custom_nodes/`` so ez_research imports resolve."""
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


def _lab_root() -> Path:
    """Return workflows/_lab.

    Returns:
        Lab graph root.
    """
    return _repo_root() / "workflows" / "_lab"


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


def _linear_labels(extra: Mapping[str, Any]) -> list[str]:
    """Collect App widget labels from extra.linearData.inputs.

    Args:
        extra: Graph ``extra`` mapping.

    Returns:
        Widget labels in linear order.
    """
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
    """Load one unique lab graph by stem or _lab-relative id.

    Args:
        stem: File stem, lab_rel, or ``_lab/...`` path.

    Returns:
        ``(path, graph)`` or None when missing/ambiguous/invalid JSON.
    """
    text = str(stem or "").replace("\\", "/").strip().lstrip("./")
    text = text.removeprefix("_lab/")
    if text.endswith(".json"):
        text = text[: -len(".json")]
    if not text:
        return None
    root = _lab_root()
    if "/" in text:
        path = root / f"{text}.json"
        hits = [path] if path.is_file() else []
    else:
        name = f"{text}.json"
        hits = sorted(p for p in root.rglob(name) if p.is_file())
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
    """MCP tool: read occupancy JSON.

    Args:
        _args: Unused tool arguments.

    Returns:
        ``{ok, occupancy}``.
    """
    return {"ok": True, "occupancy": occupancy_status()}


def tool_list_lab_apps(_args: dict[str, Any]) -> dict[str, Any]:
    """MCP tool: list shipped lab Apps.

    Args:
        _args: Unused tool arguments.

    Returns:
        ``{ok, apps, count}``.
    """
    apps: list[dict[str, Any]] = []
    root = _lab_root()
    if not root.is_dir():
        return {"ok": True, "apps": [], "count": 0}
    for path in sorted(root.rglob("*.json")):
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
        lab_rel = str(extra.get("lab_rel") or rel.with_suffix("").as_posix())
        apps.append(
            {
                "id": lab_rel,
                "lane": lane,
                "occupancy": mode.get("occupancy"),
                "handoff": list(mode.get("handoff") or []),
                "description": str(extra.get("lab_description") or ""),
            }
        )
    return {"ok": True, "apps": apps, "count": len(apps)}


def tool_describe_app(args: dict[str, Any]) -> dict[str, Any]:
    """MCP tool: describe one lab App.

    Args:
        args: ``stem`` or ``id``.

    Returns:
        App metadata or ``ok`` false.
    """
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
        "id": str(extra.get("lab_rel") or data.get("id") or path.stem),
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
    """MCP tool: one-turn creative-process chat.

    Args:
        args: ``message`` (required), optional ``history``, ``web_search``.

    Returns:
        Chat payload with brief path.
    """
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
    """MCP tool: SSRF-safe HTTPS search.

    Args:
        args: ``query`` or ``q``.

    Returns:
        Hits and formatted sources.
    """
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
    """MCP tool: planner + search subagents + synthesizer.

    Args:
        args: ``message`` (required), optional history/web_search/subagents.

    Returns:
        Research payload with brief path.
    """
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


# Typed MCP tool table (names are the public tool ids).
TOOLS: dict[str, ToolSpec] = {
    "occupancy_status": {
        "description": "Read GB10 occupancy mode, parked flag, and PIDs.",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": tool_occupancy_status,
    },
    "list_lab_apps": {
        "description": (
            "List shipped lab Apps (id, lane, occupancy, handoff)."
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
    """List MCP tools without handlers.

    Returns:
        ``{name, description, inputSchema}`` rows.
    """
    return _runtime_list_tools(TOOLS)


def call_tool(
    name: str, arguments: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Dispatch a named MCP tool.

    Args:
        name: Tool id.
        arguments: JSON-object arguments (JSON boundary).

    Returns:
        Tool payload (``ok`` false on unknown tool).
    """
    return _runtime_call_tool(TOOLS, name, arguments)


def handle_rpc(message: dict[str, Any]) -> dict[str, Any] | None:
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
        prog="research_mcp.py",
        usage_extra=(
            "Occupancy-aware research MCP. No execute_code. No telemetry."
        ),
        handle=handle_rpc,
    )


if __name__ == "__main__":
    raise SystemExit(main())
