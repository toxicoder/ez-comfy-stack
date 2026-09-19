"""In-tree studio MCP: typed tools, occupancy, no execute_code."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "lib"))
sys.path.insert(0, str(ROOT / "custom_nodes"))

import studio_mcp as mcp  # noqa: E402


def test_tools_are_typed_and_have_no_execute_code() -> None:
    names = [t["name"] for t in mcp.list_tools()]
    assert names == [
        "occupancy_status",
        "search_templates",
        "get_template",
        "describe_app",
        "apply_slots",
        "validate_workflow",
        "save_workflow",
        "create_app",
        "generate_app",
    ]
    assert "execute_code" not in names
    assert "run_workflow" not in names
    blob = json.dumps(mcp.list_tools())
    assert "telemetry" not in blob.lower()
    assert "execute_code" not in blob


def test_unknown_tool_errors() -> None:
    result = mcp.call_tool("execute_code", {"code": "1"})
    assert result["ok"] is False
    assert "unknown" in result["error"]


def test_occupancy_status_reads_state_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    payload = {
        "version": 1,
        "mode": "klein",
        "compose": True,
        "parked": False,
        "blender_pid": 0,
        "mcp_pid": 0,
    }
    (tmp_path / ".occupancy.json").write_text(json.dumps(payload), encoding="utf-8")
    result = mcp.call_tool("occupancy_status", {})
    assert result["ok"] is True
    assert result["occupancy"]["mode"] == "klein"


def test_search_templates_includes_inspire() -> None:
    result = mcp.call_tool("search_templates", {"query": "inspire"})
    assert result["ok"] is True
    ids = {row["id"] for row in result["templates"]}
    assert "inspire/prompt-forge" in ids
    assert "inspire/research-chat" in ids
    assert "inspire/app-forge" in ids
    blocks = mcp.call_tool("search_templates", {"query": "klein-t2i"})
    block_ids = {row["id"] for row in blocks["templates"]}
    assert "klein-t2i-backbone" in block_ids


def test_get_template_still_draft() -> None:
    result = mcp.call_tool("get_template", {"stem": "stills/still-draft"})
    assert result["ok"] is True
    assert result["occupancy"] == "klein"
    assert "Prompt" in result["widgets"]
    missing = mcp.call_tool("describe_app", {"stem": "no-such-app"})
    assert missing["ok"] is False


def test_generate_app_tool(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    result = mcp.call_tool(
        "generate_app",
        {
            "brief": "a chipped cobalt mug",
            "template": "stills/still-draft",
            "slug": "mcp-mug",
            "as_app": True,
        },
    )
    assert result["ok"] is True, result
    assert Path(result["path"]).is_file()
    assert result["template"] == "stills/still-draft"
    assert result["occupancy"] == "klein"


def test_create_app_and_validate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    created = mcp.call_tool(
        "create_app",
        {
            "stem": "stills/instagram-square",
            "slug": "mcp-ig",
            "slots": {"prompt": "square mug still"},
        },
    )
    assert created["ok"] is True, created
    assert created["path"].endswith("mcp-ig.app.json")
    valid = mcp.call_tool("validate_workflow", {"stem": "stills/still-draft"})
    assert valid["ok"] is True


def test_handle_rpc_tools_list_and_call() -> None:
    listed = mcp.handle_rpc({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert listed is not None
    names = [t["name"] for t in listed["result"]["tools"]]
    assert "generate_app" in names
    init = mcp.handle_rpc({"jsonrpc": "2.0", "id": 2, "method": "initialize"})
    assert init is not None
    assert init["result"]["serverInfo"]["name"] == "ez-studio"
    ping = mcp.handle_rpc({"jsonrpc": "2.0", "id": 3, "method": "ping"})
    assert ping is not None
    note = mcp.handle_rpc({"method": "notifications/initialized"})
    assert note is None
    unknown = mcp.handle_rpc({"jsonrpc": "2.0", "id": 4, "method": "nope"})
    assert unknown is not None
    assert unknown["error"]["code"] == -32601


def test_main_list_tools_and_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert mcp.main(["--help"]) == 0
    assert mcp.main(["--list-tools"]) == 0
    out = capsys.readouterr().out
    assert "occupancy_status" in out
    assert mcp.main(["--nope"]) == 1
    assert mcp.main(["--call"]) == 1


def test_serve_stdio_ping(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO('{"jsonrpc":"2.0","id":1,"method":"ping"}\n\nnot-json\n'),
    )
    mcp.serve_stdio()
    out = capsys.readouterr().out.strip()
    payload = json.loads(out)
    assert payload["id"] == 1
    assert payload["result"] == {}


def test_main_call_occupancy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    (tmp_path / ".occupancy.json").write_text(
        json.dumps({"mode": "idle", "parked": False}),
        encoding="utf-8",
    )
    assert mcp.main(["--call", "occupancy_status"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True


def test_ensure_custom_nodes_path_inserts() -> None:
    custom = str(ROOT / "custom_nodes")
    saved = sys.path[:]
    try:
        while custom in sys.path:
            sys.path.remove(custom)
        mcp._ensure_custom_nodes_path()
        assert custom in sys.path
    finally:
        sys.path[:] = saved


def test_occupancy_invalid_and_non_object(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    (tmp_path / ".occupancy.json").write_text("not-json", encoding="utf-8")
    assert mcp.occupancy_status()["mode"] == "idle"
    (tmp_path / ".occupancy.json").write_text("[1, 2]", encoding="utf-8")
    assert mcp.occupancy_status()["mode"] == "idle"


def test_apply_slots_and_validate_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    bad_slots = mcp.call_tool(
        "apply_slots", {"stem": "stills/still-draft", "slots": [1]}
    )
    assert bad_slots["ok"] is False
    ok_slots = mcp.call_tool(
        "apply_slots",
        {"stem": "stills/still-draft", "slots": {"prompt": "mcp slot"}},
    )
    assert ok_slots["ok"] is True
    err = mcp.call_tool("apply_slots", {"stem": "no-such", "slots": {}})
    assert err["ok"] is False
    missing = mcp.call_tool("validate_workflow", {})
    assert missing["ok"] is False
    boom = mcp.call_tool("validate_workflow", {"stem": "no-such"})
    assert boom["ok"] is False
    graph_ok = mcp.call_tool(
        "validate_workflow",
        {"graph": {"extra": {"workflowRendererVersion": "Vue-corrected"}}},
    )
    assert graph_ok["ok"] is True


def test_save_and_generate_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    missing = mcp.call_tool("save_workflow", {"stem": "no-such", "slug": "x"})
    assert missing["ok"] is False
    saved = mcp.call_tool(
        "save_workflow",
        {
            "stem": "stills/still-draft",
            "slug": "save-mug",
            "as_app": False,
            "slots": {"prompt": "saved"},
        },
    )
    assert saved["ok"] is True
    assert saved["as_app"] is False
    forced = mcp._save_from_args(
        {"stem": "stills/still-draft", "slug": "force-graph"},
        force_app=False,
    )
    assert forced["ok"] is True
    assert forced["as_app"] is False
    failed = mcp.call_tool("generate_app", {"brief": "x", "template": "no-such"})
    assert failed["ok"] is False
    assert "error" in failed
    reply = mcp.handle_rpc(
        {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {
                "name": "generate_app",
                "arguments": {"brief": "x", "template": "no-such"},
            },
        }
    )
    assert reply is not None
    assert reply["result"]["isError"] is True
    assert mcp.handle_rpc({"method": "nope"}) is None
    called = mcp.handle_rpc(
        {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {"name": "occupancy_status", "arguments": []},
        }
    )
    assert called is not None


def test_serve_stdio_skips_non_object(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO('[1]\n{"jsonrpc":"2.0","id":2,"method":"ping"}\n'),
    )
    mcp.serve_stdio()
    out = capsys.readouterr().out.strip().splitlines()
    payload = json.loads(out[-1])
    assert payload["id"] == 2


def test_main_call_with_json_and_stdio(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    assert mcp.main(["--stdio"]) == 0
    assert mcp.main(["stdio"]) == 0
    assert (
        mcp.main(["--call", "get_template", json.dumps({"stem": "stills/still-draft"})])
        == 0
    )
    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert payload["ok"] is True
