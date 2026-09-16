"""In-tree research MCP: typed tools, occupancy, no execute_code."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

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


def test_list_lab_apps_includes_inspire() -> None:
    result = mcp.call_tool("list_lab_apps", {})
    assert result["ok"] is True
    assert result["count"] >= 2
    ids = {row["id"] for row in result["apps"]}
    assert "inspire/prompt-forge" in ids
    assert "inspire/cinema-rack" in ids
    assert "inspire/research-chat" in ids
    research = next(r for r in result["apps"] if r["id"] == "inspire/research-chat")
    assert research["lane"] == "inspire"
    assert research["occupancy"] == "llm"


def test_describe_app_research_chat() -> None:
    result = mcp.call_tool("describe_app", {"stem": "inspire/research-chat"})
    assert result["ok"] is True
    assert result["occupancy"] == "llm"
    assert "inspire/prompt-forge" in result["handoff"]
    assert "Message" in result["widgets"]
    assert result["lab_mcp"]["server"] == "research-mcp"
    assert "research" in result["lab_mcp"]["tools"]
    missing = mcp.call_tool("describe_app", {"stem": "no-such-app"})
    assert missing["ok"] is False


def test_chat_and_research_tools(monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_web_search_tool(monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_main_list_tools_and_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert mcp.main(["--help"]) == 0
    assert mcp.main(["--list-tools"]) == 0
    out = capsys.readouterr().out
    assert "occupancy_status" in out
    assert mcp.main(["--nope"]) == 1
    assert mcp.main(["--call"]) == 1


def test_handle_rpc_tools_call_occupancy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_serve_stdio_ping(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
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


def test_main_stdio_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    import io

    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    assert mcp.main([]) == 0


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


def test_lab_app_discovery_edges(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(mcp, "_lab_root", lambda: tmp_path / "missing-lab")
    empty = mcp.call_tool("list_lab_apps", {})
    assert empty["apps"] == []
    lab = tmp_path / "lab" / "inspire"
    lab.mkdir(parents=True)
    (lab / "bad.json").write_text("{", encoding="utf-8")
    (lab / "array.json").write_text("[1]", encoding="utf-8")
    (lab / "extra-list.json").write_text(
        json.dumps({"id": "x", "extra": [1, 2]}), encoding="utf-8"
    )
    (lab / "mode-list.json").write_text(
        json.dumps(
            {
                "id": "y",
                "extra": {
                    "lab_app_mode": [1],
                    "lab_mcp": [1],
                    "lab_rel": "inspire/y",
                },
            }
        ),
        encoding="utf-8",
    )
    (lab / "ok.json").write_text(
        json.dumps(
            {
                "id": "ok",
                "extra": {
                    "lab_rel": "inspire/ok",
                    "lab_app_mode": {"lane": "inspire", "occupancy": "llm"},
                    "linearData": {
                        "inputs": [
                            "skip",
                            ["only"],
                            ["w", "Message"],
                            ["w", "x", {"label": "Hi"}],
                            ["w", "y", "not-dict"],
                        ]
                    },
                    "lab_mcp": {"server": "research-mcp", "tools": ["chat"]},
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mcp, "_lab_root", lambda: tmp_path / "lab")
    monkeypatch.setattr(mcp, "_repo_root", lambda: tmp_path)
    listed = mcp.call_tool("list_lab_apps", {})
    ids = {row["id"] for row in listed["apps"]}
    assert "inspire/ok" in ids
    assert mcp._load_lab_graph("") is None
    assert mcp._load_lab_graph("inspire/ok.json") is not None
    assert mcp._load_lab_graph("_lab/inspire/ok") is not None
    assert mcp._load_lab_graph("ok") is not None
    assert mcp._load_lab_graph("bad") is None
    assert mcp._load_lab_graph("array") is None
    described = mcp.call_tool("describe_app", {"stem": "inspire/ok"})
    assert described["ok"] is True
    assert "Hi" in described["widgets"]
    assert "Message" in described["widgets"]
    extra_list = mcp.call_tool("describe_app", {"id": "inspire/extra-list"})
    assert extra_list["ok"] is True
    mode_list = mcp.call_tool("describe_app", {"stem": "inspire/mode-list"})
    assert mode_list["ok"] is True
    no_linear = mcp._linear_labels({"linearData": {"inputs": "nope"}})
    assert no_linear == []


def test_linear_labels_when_linear_not_dict() -> None:
    assert mcp._linear_labels({"linearData": "nope"}) == []


def test_serve_stdio_skips_non_object(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO("[1]\n\n"))
    mcp.serve_stdio()
    assert capsys.readouterr().out == ""
    assert mcp.handle_rpc({"method": "nope"}) is None
    assert mcp.main(["--call", "list_lab_apps", "{}"]) in {0, 1}
