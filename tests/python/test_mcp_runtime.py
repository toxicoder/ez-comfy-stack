"""Shared MCP JSON-RPC runtime (facade used by blender/studio/research)."""

from __future__ import annotations

import io
import json
import sys
from typing import Any, cast

import mcp_runtime as rt
import pytest


def _ok(args: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, "echo": dict(args)}


def _fail(args: dict[str, Any]) -> dict[str, Any]:
    del args
    return {"ok": False, "error": "nope"}


TOOLS: dict[str, rt.ToolSpec] = {
    "echo": {
        "description": "Echo arguments.",
        "inputSchema": {"type": "object"},
        "handler": _ok,
    },
    "fail": {
        "description": "Always fail.",
        "inputSchema": {"type": "object"},
        "handler": _fail,
    },
}


def _handle(message: dict[str, Any]) -> dict[str, Any] | None:
    return rt.handle_rpc(message, tools=TOOLS, server_name="ez-test")


def test_list_and_call_tools() -> None:
    rows = rt.list_tools(TOOLS)
    assert [row["name"] for row in rows] == ["echo", "fail"]
    assert "handler" not in rows[0]
    assert rt.call_tool(TOOLS, "echo", {"a": 1})["echo"] == {"a": 1}
    assert rt.call_tool(TOOLS, "missing")["ok"] is False
    assert rt.call_tool(TOOLS, "echo")["echo"] == {}


def test_handle_rpc_methods() -> None:
    init = _handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert init is not None
    assert init["result"]["serverInfo"]["name"] == "ez-test"
    ping = _handle({"jsonrpc": "2.0", "id": 2, "method": "ping"})
    assert ping is not None
    listed = _handle({"jsonrpc": "2.0", "id": 3, "method": "tools/list"})
    assert listed is not None
    names = [t["name"] for t in listed["result"]["tools"]]
    assert "echo" in names
    called = _handle(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "echo", "arguments": {"k": "v"}},
        }
    )
    assert called is not None
    assert called["result"]["isError"] is False
    nonempty_list = _handle(
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "echo", "arguments": ["not", "a", "dict"]},
        }
    )
    assert nonempty_list is not None
    payload = json.loads(nonempty_list["result"]["content"][0]["text"])
    assert payload["echo"] == {}
    failed = _handle(
        {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {"name": "fail", "arguments": {}},
        }
    )
    assert failed is not None
    assert failed["result"]["isError"] is True
    assert _handle({"method": "notifications/initialized"}) is None
    assert _handle({"method": "nope"}) is None
    missing = _handle({"jsonrpc": "2.0", "id": 7, "method": "nope"})
    assert missing is not None
    assert missing["error"]["code"] == -32601


def test_serve_stdio_skips_junk(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(
            "\nnot-json\n[1,2]\n"
            '{"jsonrpc":"2.0","id":1,"method":"ping"}\n'
            '{"method":"notifications/initialized"}\n'
        ),
    )
    rt.serve_stdio(_handle)
    out = capsys.readouterr().out.strip().splitlines()
    assert json.loads(out[0])["id"] == 1


def test_main_cli_paths(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    assert (
        rt.main_cli(
            ["--help"],
            tools=TOOLS,
            prog="test_mcp.py",
            usage_extra="No execute_code. No telemetry.",
            handle=_handle,
        )
        == 0
    )
    err = capsys.readouterr().err
    assert "test_mcp.py" in err
    assert "No execute_code" in err
    assert (
        rt.main_cli(
            ["--list-tools"],
            tools=TOOLS,
            prog="test_mcp.py",
            usage_extra="x",
            handle=_handle,
        )
        == 0
    )
    assert "echo" in capsys.readouterr().out
    assert (
        rt.main_cli(
            ["--call", "echo", '{"z":1}'],
            tools=TOOLS,
            prog="test_mcp.py",
            usage_extra="x",
            handle=_handle,
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["ok"] is True
    assert (
        rt.main_cli(
            ["--call"],
            tools=TOOLS,
            prog="test_mcp.py",
            usage_extra="x",
            handle=_handle,
        )
        == 1
    )
    assert (
        rt.main_cli(
            ["--call", "fail"],
            tools=TOOLS,
            prog="test_mcp.py",
            usage_extra="x",
            handle=_handle,
        )
        == 1
    )
    assert (
        rt.main_cli(
            ["--nope"],
            tools=TOOLS,
            prog="test_mcp.py",
            usage_extra="x",
            handle=_handle,
        )
        == 1
    )
    monkeypatch.setattr(sys, "argv", ["test_mcp.py", "--stdio"])
    assert (
        rt.main_cli(
            None,
            tools=TOOLS,
            prog="test_mcp.py",
            usage_extra="x",
            handle=_handle,
        )
        == 0
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    assert (
        rt.main_cli(
            [],
            tools=TOOLS,
            prog="test_mcp.py",
            usage_extra="x",
            handle=_handle,
        )
        == 0
    )
    assert (
        rt.main_cli(
            ["stdio"],
            tools=TOOLS,
            prog="test_mcp.py",
            usage_extra="x",
            handle=_handle,
        )
        == 0
    )


def test_rpc_helpers_and_handler_protocol() -> None:
    assert rt.rpc_result(1, {"ok": True})["id"] == 1
    err = rt.rpc_error(2, -32601, "missing")
    assert err["error"]["code"] == -32601
    cast(Any, rt.ToolHandler.__call__)(_ok, {"a": 1})
