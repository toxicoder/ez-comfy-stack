"""Shared stdlib JSON-RPC loop for occupancy-aware MCP servers.

Each ``*_mcp.py`` keeps ``SERVER_NAME``, ``TOOLS``, and tool functions.
This module owns list/call/handle/stdio/CLI so the three servers do not
copy the same 155 lines. ``ToolSpec`` stays a TypedDict (dict literals);
``ToolHandler`` is a Protocol (the behavioral seam). The JSON-RPC
vocabulary (``JsonRpcRequest`` / ``JsonRpcResponse``) is declared once
here so every server speaks one pinned wire type.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Protocol, TypeAlias, TypedDict, cast

if TYPE_CHECKING:
    from ez_common import Json, JsonMap, JsonObject

# MCP protocol identity (JSON-RPC initialize.serverInfo).
PROTOCOL_VERSION = "2024-11-05"
SERVER_VERSION = "1"

RpcId: TypeAlias = str | int | None
"""JSON-RPC request id: a string, a number, or null for notifications."""

JsonSchema: TypeAlias = Mapping[str, object]
"""One JSON Schema body.

Stays an open map (rung 4): ``edit_mcp._spec`` copies it out of the pinned
``CatalogSchema`` TypedDict with ``dict()``, whose member join is ``object``.
"""

ToolArgs: TypeAlias = Mapping[str, object]
"""One ``tools/call`` arguments object as it came off the wire.

Stays an open map (rung 4): handlers hand members straight to ``int()`` /
``float()``, which no ``Json`` member satisfies, so a ``JsonMap`` alias would
cost a new ``cast`` at :data:`PRODUCTION_CAST_BUDGET`.
"""

ToolResult: TypeAlias = Mapping[str, object]
"""One tool payload: ``ok`` plus whatever that tool chose to return.

Stays an open map (rung 4): handlers return values that are not JSON nodes,
including ``list[str]`` and TypedDict records such as ``BlenderRunResult``.
"""

ToolNumber: TypeAlias = str | int | float
"""A parsed JSON value that ``int()`` and ``float()`` can coerce."""


class ToolHandler(Protocol):
    """One MCP tool implementation."""

    def __call__(self, args: ToolArgs, /) -> ToolResult:
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
    """Human-facing summary shown by ``tools/list``."""

    inputSchema: JsonSchema
    """JSON Schema body for the tool arguments."""

    handler: ToolHandler
    """Implementation dispatched by ``tools/call``."""


class ToolCatalogEntry(TypedDict):
    """One ``tools/list`` row (a tool spec without its handler)."""

    name: str
    """Public tool id."""

    description: str
    """Human-facing summary."""

    inputSchema: JsonSchema
    """JSON Schema body for the tool arguments."""


class JsonRpcRequest(TypedDict, total=False):
    """One inbound JSON-RPC 2.0 message (every key is optional per spec)."""

    jsonrpc: str
    """Protocol marker; the loop does not gate on it."""

    id: RpcId
    """Request id. Absent or null means a notification."""

    method: str
    """Method name (``initialize``, ``ping``, ``tools/*``, notifications)."""

    params: JsonMap
    """Method parameters (``name``/``arguments`` for tools/call)."""


class RpcError(TypedDict):
    """One JSON-RPC error object."""

    code: int
    """JSON-RPC error code (``-32601`` here for method not found)."""

    message: str
    """Error text."""


class RpcServerInfo(TypedDict):
    """The ``initialize`` ``serverInfo`` block."""

    name: str
    """Server id (``ez-edit``, ``ez-blender``, ...)."""

    version: str
    """Server version string."""


class RpcCapabilities(TypedDict):
    """The ``initialize`` ``capabilities`` block (only tools is offered)."""

    tools: JsonObject
    """Empty object: tool discovery carries no options."""


class RpcContent(TypedDict):
    """One MCP content block inside a ``tools/call`` result."""

    type: str
    """Content kind (``text`` here)."""

    text: str
    """JSON-encoded tool payload."""


class RpcResultSet(TypedDict, total=False):
    """Every ``result`` key this loop emits; one method fills one group."""

    protocolVersion: str
    """Negotiated MCP protocol version (initialize)."""

    capabilities: RpcCapabilities
    """Advertised capabilities (initialize)."""

    serverInfo: RpcServerInfo
    """Server identity (initialize)."""

    tools: list[ToolCatalogEntry]
    """Tool rows (tools/list)."""

    content: list[RpcContent]
    """Content blocks (tools/call)."""

    isError: bool
    """True when the tool payload reported ``ok`` false (tools/call)."""


class JsonRpcResponse(TypedDict, total=False):
    """One outbound JSON-RPC 2.0 response."""

    jsonrpc: str
    """Protocol marker (always ``2.0``)."""

    id: RpcId
    """Echoed request id."""

    result: RpcResultSet
    """Success payload (absent on error)."""

    error: RpcError
    """Error object (absent on success)."""


def list_tools(tools: Mapping[str, ToolSpec]) -> list[ToolCatalogEntry]:
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
    arguments: ToolArgs | None = None,
) -> ToolResult:
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


def rpc_result(msg_id: RpcId, result: RpcResultSet) -> JsonRpcResponse:
    """Build a JSON-RPC 2.0 success envelope.

    Args:
        msg_id: Request id (string, number, or null).
        result: Method result payload.

    Returns:
        JSON-RPC response object.
    """
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def rpc_error(msg_id: RpcId, code: int, message: str) -> JsonRpcResponse:
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
    message: JsonRpcRequest,
    *,
    tools: Mapping[str, ToolSpec],
    server_name: str,
    server_version: str = SERVER_VERSION,
    protocol_version: str = PROTOCOL_VERSION,
) -> JsonRpcResponse | None:
    """Handle one JSON-RPC message. Notifications return None.

    Args:
        message: Parsed JSON-RPC request (JSON boundary; read with ``get``).
        tools: Server tool table.
        server_name: ``serverInfo.name`` for initialize.
        server_version: ``serverInfo.version``.
        protocol_version: MCP protocol version string.

    Returns:
        Response object, or None for notifications.
    """
    method = str(message.get("method") or "")
    msg_id = message.get("id")
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
    handle: Callable[[JsonRpcRequest], JsonRpcResponse | None],
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
            parsed: Json = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(parsed, dict):
            continue
        # The line is unvalidated JSON; the handler reads every key with
        # .get(), so the object is a request record for this loop's purposes.
        reply = handle(cast(JsonRpcRequest, parsed))
        if reply is not None:
            sys.stdout.write(json.dumps(reply) + "\n")
            sys.stdout.flush()


def main_cli(
    argv: list[str] | None,
    *,
    tools: Mapping[str, ToolSpec],
    prog: str,
    usage_extra: str,
    handle: Callable[[JsonRpcRequest], JsonRpcResponse | None],
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
        payload: ToolArgs = {}
        if len(args) >= 3:
            payload = json.loads(args[2])
        result = call_tool(tools, args[1], payload)
        json.dump(result, sys.stdout)
        sys.stdout.write("\n")
        return 0 if result.get("ok", True) else 1
    sys.stderr.write(f"unknown arg: {args[0]}\n")
    return 1
