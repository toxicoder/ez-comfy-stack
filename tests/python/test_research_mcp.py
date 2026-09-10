"""In-tree research MCP: typed tools, occupancy, no execute_code."""

from __future__ import annotations

import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "lib"))
sys.path.insert(0, str(ROOT / "custom_nodes"))

import research_mcp as mcp  # noqa: E402
from ez_research.pipeline import ResearchResult  # noqa: E402
from ez_research.search import SearchHit  # noqa: E402


def test_tools_are_typed_and_have_no_execute_code() -> None:
    names = [t["name"] for t in mcp.list_tools()]
    assert names == [
        "occupancy_status",
        "list_lab_apps",
        "describe_app",
        "chat",
        "web_search",
        "research",
    ]
    assert "execute_code" not in names
    blob = json.dumps(mcp.list_tools())
    assert "telemetry" not in blob.lower()
    assert "execute_code" not in blob


def test_unknown_tool_errors() -> None:
    result = mcp.call_tool("execute_code", {"code": "1"})
    assert result["ok"] is False
    assert "unknown" in result["error"]


def test_occupancy_status_reads_state_file(tmp_path: Path, monkeypatch) -> None:
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


def test_list_lab_apps_includes_inspire() -> None:
    result = mcp.call_tool("list_lab_apps", {})
    assert result["ok"] is True
    assert result["count"] >= 2
    ids = {row["id"] for row in result["apps"]}
    assert "prompt-forge-lab-example" in ids
    assert "research-chat-lab-example" in ids
    research = next(r for r in result["apps"] if r["id"] == "research-chat-lab-example")
    assert research["lane"] == "inspire"
    assert research["occupancy"] == "llm"


def test_describe_app_research_chat() -> None:
    result = mcp.call_tool("describe_app", {"stem": "research-chat-lab-example"})
    assert result["ok"] is True
    assert result["occupancy"] == "llm"
    assert "prompt-forge-lab-example" in result["handoff"]
    assert "Message" in result["widgets"]
    assert result["lab_mcp"]["server"] == "research-mcp"
    assert "research" in result["lab_mcp"]["tools"]
    missing = mcp.call_tool("describe_app", {"stem": "no-such-app"})
    assert missing["ok"] is False


def test_chat_and_research_tools(monkeypatch) -> None:
    monkeypatch.setattr(
        "ez_research.pipeline.run_chat",
        lambda message, history="", web_search=False: ResearchResult(
            "hello", "", "ok", []
        ),
    )
    monkeypatch.setattr(
        "ez_research.pipeline.run_research",
        lambda message, history="", web_search=True, subagents=2: ResearchResult(
            "brief", "src", "ok", ["q"]
        ),
    )
    monkeypatch.setattr("ez_research.pipeline.write_brief", lambda *_a, **_k: None)
    chat = mcp.call_tool("chat", {"message": "hi"})
    assert chat["ok"] is True
    assert chat["text"] == "hello"
    research = mcp.call_tool("research", {"message": "look"})
    assert research["ok"] is True
    assert research["queries"] == ["q"]


def test_web_search_tool(monkeypatch) -> None:
    monkeypatch.setattr(
        "ez_research.search.search_web",
        lambda query, limit=5, fetch_bodies=False: [
            SearchHit("T", "https://en.wikipedia.org/wiki/T", "s")
        ],
    )
    result = mcp.call_tool("web_search", {"query": "key light"})
    assert result["ok"] is True
    assert result["hits"][0]["title"] == "T"


def test_handle_rpc_tools_list_and_call() -> None:
    listed = mcp.handle_rpc({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert listed is not None
    names = [t["name"] for t in listed["result"]["tools"]]
    assert "research" in names
    init = mcp.handle_rpc({"jsonrpc": "2.0", "id": 2, "method": "initialize"})
    assert init is not None
    assert init["result"]["serverInfo"]["name"] == "ez-research"
    ping = mcp.handle_rpc({"jsonrpc": "2.0", "id": 3, "method": "ping"})
    assert ping is not None
    note = mcp.handle_rpc({"method": "notifications/initialized"})
    assert note is None
    unknown = mcp.handle_rpc({"jsonrpc": "2.0", "id": 4, "method": "nope"})
    assert unknown is not None
    assert unknown["error"]["code"] == -32601


def test_main_list_tools_and_help(capsys) -> None:
    assert mcp.main(["--help"]) == 0
    assert mcp.main(["--list-tools"]) == 0
    out = capsys.readouterr().out
    assert "occupancy_status" in out
    assert mcp.main(["--nope"]) == 1
    assert mcp.main(["--call"]) == 1


def test_handle_rpc_tools_call_occupancy(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    (tmp_path / ".occupancy.json").write_text(
        json.dumps({"mode": "wan"}),
        encoding="utf-8",
    )
    reply = mcp.handle_rpc(
        {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "tools/call",
            "params": {"name": "occupancy_status", "arguments": {}},
        }
    )
    assert reply is not None
    body = json.loads(reply["result"]["content"][0]["text"])
    assert body["occupancy"]["mode"] == "wan"


def test_serve_stdio_ping(monkeypatch, capsys) -> None:
    import io

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


def test_main_stdio_empty(monkeypatch) -> None:
    import io

    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    assert mcp.main([]) == 0


def test_main_call_occupancy(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    (tmp_path / ".occupancy.json").write_text(
        json.dumps({"mode": "idle", "parked": False}),
        encoding="utf-8",
    )
    assert mcp.main(["--call", "occupancy_status"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
