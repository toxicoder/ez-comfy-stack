"""In-tree studio MCP: typed tools, occupancy, no execute_code.

Also pins the catalog invariant both MCP servers share: every inputSchema
argument carries a description and every tool description says what a call
returns, so a model or operator reading ``tools/list`` is never handed a
bare ``{"type": "string"}``.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "lib"))
sys.path.insert(0, str(ROOT / "custom_nodes"))

import research_mcp as research  # noqa: E402
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


def test_occupancy_status_reads_state_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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
    result = mcp.call_tool("search_templates", {"query": "labs/assist"})
    assert result["ok"] is True
    ids = {row["id"] for row in result["templates"]}
    assert "labs/assist/prompt-forge" in ids
    assert "labs/assist/research-chat" in ids
    assert "labs/assist/app-forge" in ids
    blocks = mcp.call_tool("search_templates", {"query": "klein-t2i"})
    block_ids = {row["id"] for row in blocks["templates"]}
    assert "klein-t2i-backbone" in block_ids


def test_get_template_still_draft() -> None:
    result = mcp.call_tool("get_template", {"stem": "photos/still-draft"})
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
            "template": "photos/still-draft",
            "slug": "mcp-mug",
            "as_app": True,
        },
    )
    assert result["ok"] is True, result
    assert Path(result["path"]).is_file()
    assert result["template"] == "photos/still-draft"
    assert result["occupancy"] == "klein"


def test_create_app_and_validate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    created = mcp.call_tool(
        "create_app",
        {
            "stem": "photos/instagram-square",
            "slug": "mcp-ig",
            "slots": {"prompt": "square mug still"},
        },
    )
    assert created["ok"] is True, created
    assert created["path"].endswith("mcp-ig.app.json")
    valid = mcp.call_tool("validate_workflow", {"stem": "photos/still-draft"})
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


def test_serve_stdio_ping(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
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


def test_main_call_occupancy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
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
        "apply_slots", {"stem": "photos/still-draft", "slots": [1]}
    )
    assert bad_slots["ok"] is False
    ok_slots = mcp.call_tool(
        "apply_slots",
        {"stem": "photos/still-draft", "slots": {"prompt": "mcp slot"}},
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
            "stem": "photos/still-draft",
            "slug": "save-mug",
            "as_app": False,
            "slots": {"prompt": "saved"},
        },
    )
    assert saved["ok"] is True
    assert saved["as_app"] is False
    forced = mcp._save_from_args(
        {"stem": "photos/still-draft", "slug": "force-graph"},
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


def test_serve_stdio_skips_non_object(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO('[1]\n{"jsonrpc":"2.0","id":2,"method":"ping"}\n'),
    )
    mcp.serve_stdio()
    out = capsys.readouterr().out.strip().splitlines()
    payload = json.loads(out[-1])
    assert payload["id"] == 2


def test_main_call_with_json_and_stdio(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    assert mcp.main(["--stdio"]) == 0
    assert mcp.main(["stdio"]) == 0
    assert (
        mcp.main(["--call", "get_template", json.dumps({"stem": "photos/still-draft"})])
        == 0
    )
    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert payload["ok"] is True


_MIN_ARG_DOC = 30
"""Shortest argument description that still reads as guidance."""

_MIN_ERROR_DOC = 60
"""Shortest error that says what to pass instead of only what broke."""


def _argument_docs(tool_name: str, spec: Any) -> dict[str, str]:
    """Collect the argument descriptions of one tool's ``inputSchema``.

    Args:
        tool_name: Tool id, used in failure messages.
        spec: One row of a server's ``TOOLS`` table.

    Returns:
        ``{argument name: description}`` for every declared property.

    Raises:
        AssertionError: A property is not a mapping, or has no string
            description.
    """
    properties = spec["inputSchema"].get("properties") or {}
    assert isinstance(properties, dict), f"{tool_name} properties"
    docs: dict[str, str] = {}
    for prop_name, prop in properties.items():
        assert isinstance(prop, dict), f"{tool_name}.{prop_name} shape"
        text = prop.get("description")
        assert isinstance(text, str), f"{tool_name}.{prop_name} has no description"
        docs[str(prop_name)] = text
    return docs


def _refusal(server: Any, tool: str, args: dict[str, Any], subject: str) -> str:
    """Call a tool that must refuse and return its operator-facing error.

    Args:
        server: The MCP module under test.
        tool: Tool id to call.
        args: Arguments that must make it refuse.
        subject: Text the error has to repeat back (bad value or key).

    Returns:
        The error string.

    Raises:
        AssertionError: The call succeeded, or the error is bare text that
            names neither the bad input nor another tool to try instead.
    """
    result = server.call_tool(tool, args)
    assert result["ok"] is False, result
    error = str(result["error"])
    assert len(error) >= _MIN_ERROR_DOC, f"{tool}: {error!r}"
    assert subject in error, f"{tool}: {error!r}"
    assert any(name in error for name in server.TOOLS), f"{tool}: {error!r}"
    return error


@pytest.mark.parametrize("server", [mcp, research], ids=["studio", "research"])
def test_every_tool_documents_its_arguments_and_its_return(server: Any) -> None:
    for name, spec in server.TOOLS.items():
        assert "Returns:" in spec["description"], f"{name} never says what it returns"
        docs = _argument_docs(name, spec)
        for prop_name, text in docs.items():
            assert len(text) >= _MIN_ARG_DOC, f"{name}.{prop_name}: {text!r}"
        required = spec["inputSchema"].get("required") or []
        assert isinstance(required, list)
        assert set(required) <= set(docs), f"{name} requires an undocumented argument"


def test_studio_stem_arguments_point_at_the_listing_tool() -> None:
    for name, spec in mcp.TOOLS.items():
        for arg, text in _argument_docs(name, spec).items():
            if arg in ("stem", "template"):
                assert "search_templates" in text, f"{name}.{arg}: {text!r}"


def test_research_app_id_argument_points_at_the_listing_tool() -> None:
    docs = _argument_docs("describe_app", research.TOOLS["describe_app"])
    assert "list_lab_apps" in docs["stem"], docs["stem"]


def test_studio_refusals_say_what_to_pass_and_who_could_have_helped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    slots = _refusal(
        mcp, "apply_slots", {"stem": "photos/still-draft", "slots": ["prompt"]}, "slots"
    )
    assert "get_template" in slots, slots
    patch = _refusal(mcp, "apply_slots", {"stem": "no-such", "slots": {}}, "no-such")
    assert "get_template" in patch, patch
    both = _refusal(mcp, "validate_workflow", {}, "graph")
    assert "stem" in both, both
    _refusal(mcp, "validate_workflow", {"stem": "no-such"}, "no-such")
    _refusal(mcp, "get_template", {"stem": "no-such"}, "no-such")
    _refusal(mcp, "describe_app", {"stem": "no-such"}, "no-such")
    saved = _refusal(mcp, "save_workflow", {"stem": "no-such", "slug": "x"}, "no-such")
    assert "search_templates" in saved, saved
    _refusal(mcp, "create_app", {"stem": "no-such", "slug": "x"}, "no-such")
    no_slug = _refusal(mcp, "save_workflow", {"stem": "no-such"}, "no-such")
    assert "overwrite" in no_slug, no_slug


def test_research_refusal_points_at_list_lab_apps() -> None:
    error = _refusal(research, "describe_app", {"stem": "no-such-app"}, "no-such-app")
    assert "list_lab_apps" in error, error
