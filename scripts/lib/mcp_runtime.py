"""Shared stdlib JSON-RPC loop for occupancy-aware MCP servers.

Each ``*_mcp.py`` keeps ``SERVER_NAME``, ``TOOLS``, and tool functions.
This module owns list/call/handle/stdio/CLI so the three servers do not
copy the same 155 lines. ``ToolSpec`` stays a TypedDict (dict literals);
``ToolHandler`` is a Protocol (the behavioral seam).
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable, Mapping
from typing import Any, Protocol, TypedDict, cast

# MCP protocol identity (JSON-RPC initialize.serverInfo).
PROTOCOL_VERSION = "2024-11-05"
SERVER_VERSION = "1"

RpcId = str | int | None


class ToolHandler(Protocol):
    """One MCP tool implementation."""

    def __call__(self, args: dict[str, Any], /) -> dict[str, Any]:
        """Handle a tools/call arguments object.

        Args:
            args: JSON-object arguments (JSON boundary). Positional-only so
                handlers may name the parameter ``args`` or ``_args``.

        Returns:
            Tool payload (``ok`` false on handled errors).
        """
        ...


class ToolSpec(TypedDict):
    """One MCP tool: description, JSON Schema, handler."""

    description: str
    inputSchema: dict[str, Any]
    handler: ToolHandler


def list_tools(tools: Mapping[str, ToolSpec]) -> list[dict[str, Any]]:
    """List MCP tools without handlers.

    Args:
        tools: Server tool table.

    Returns:
        ``{name, description, inputSchema}`` rows.
    """
    return [
        {
            "name": name,
            "description": spec["description"],
            "inputSchema": spec["inputSchema"],
        }
        for name, spec in tools.items()
    ]


def call_tool(
    tools: Mapping[str, ToolSpec],
    name: str,
    arguments: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Dispatch a named MCP tool.

    Args:
        tools: Server tool table.
        name: Tool id.
        arguments: JSON-object arguments (JSON boundary).

    Returns:
        Tool payload (``ok`` false on unknown tool).
    """
    spec = tools.get(name)
    if spec is None:
        return {"ok": False, "error": f"unknown tool {name}"}
    handler: ToolHandler = spec["handler"]
    return handler(dict(arguments or {}))


def rpc_result(msg_id: RpcId, result: object) -> dict[str, Any]:
    """Build a JSON-RPC 2.0 success envelope.

    Args:
        msg_id: Request id (string, number, or null).
        result: Method result payload.

    Returns:
        JSON-RPC response object.
    """
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def rpc_error(msg_id: RpcId, code: int, message: str) -> dict[str, Any]:
    """Build a JSON-RPC 2.0 error envelope.

    Args:
        msg_id: Request id (string, number, or null).
        code: JSON-RPC error code.
        message: Error text.

    Returns:
        JSON-RPC error object.
    """
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def handle_rpc(
    message: dict[str, Any],
    *,
    tools: Mapping[str, ToolSpec],
    server_name: str,
    server_version: str = SERVER_VERSION,
    protocol_version: str = PROTOCOL_VERSION,
) -> dict[str, Any] | None:
    """Handle one JSON-RPC message. Notifications return None.

    Args:
        message: Parsed JSON-RPC request (JSON boundary).
        tools: Server tool table.
        server_name: ``serverInfo.name`` for initialize.
        server_version: ``serverInfo.version``.
        protocol_version: MCP protocol version string.

    Returns:
        Response object, or None for notifications.
    """
    method = str(message.get("method") or "")
    msg_id = cast(RpcId, message.get("id"))
    params = message.get("params") or {}
    if method == "notifications/initialized":
        return None
    if method == "initialize":
        return rpc_result(
            msg_id,
            {
                "protocolVersion": protocol_version,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": server_name, "version": server_version},
            },
        )
    if method == "ping":
        return rpc_result(msg_id, {})
    if method == "tools/list":
        return rpc_result(msg_id, {"tools": list_tools(tools)})
    if method == "tools/call":
        name = str(params.get("name") or "")
        arguments = params.get("arguments") or {}
        payload = call_tool(
            tools, name, arguments if isinstance(arguments, dict) else {}
        )
        text = json.dumps(payload)
        return rpc_result(
            msg_id,
            {
                "content": [{"type": "text", "text": text}],
                "isError": not payload.get("ok", True),
            },
        )
    if msg_id is None:
        return None
    return rpc_error(msg_id, -32601, f"method not found: {method}")


def serve_stdio(
    handle: Callable[[dict[str, Any]], dict[str, Any] | None],
) -> None:
    """Serve JSON-RPC on stdin/stdout (one JSON object per line).

    Args:
        handle: Bound ``handle_rpc`` for this server.
    """
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
        reply = handle(message)
        if reply is not None:
            sys.stdout.write(json.dumps(reply) + "\n")
            sys.stdout.flush()


def main_cli(
    argv: list[str] | None,
    *,
    tools: Mapping[str, ToolSpec],
    prog: str,
    usage_extra: str,
    handle: Callable[[dict[str, Any]], dict[str, Any] | None],
) -> int:
    """CLI: --stdio | --list-tools | --call TOOL [JSON].

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).
        tools: Server tool table.
        prog: Script filename in usage lines.
        usage_extra: Second help line (no execute_code / telemetry notes).
        handle: Bound ``handle_rpc``.

    Returns:
        Process status.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("--stdio", "stdio"):
        serve_stdio(handle)
        return 0
    if args[0] in ("-h", "--help", "help"):
        sys.stderr.write(
            f"Usage: {prog} [--stdio] | --list-tools | --call TOOL [JSON]\n"
            f"  {usage_extra}\n"
        )
        return 0
    if args[0] == "--list-tools":
        json.dump(list_tools(tools), sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    if args[0] == "--call":
        if len(args) < 2:
            sys.stderr.write(f"{prog} --call TOOL [JSON args]\n")
            return 1
        payload: dict[str, Any] = {}
        if len(args) >= 3:
            payload = json.loads(args[2])
        result = call_tool(tools, args[1], payload)
        json.dump(result, sys.stdout)
        sys.stdout.write("\n")
        return 0 if result.get("ok", True) else 1
    sys.stderr.write(f"unknown arg: {args[0]}\n")
    return 1
