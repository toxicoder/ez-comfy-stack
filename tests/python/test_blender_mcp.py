"""In-tree Blender MCP: typed tools, occupancy, no execute_code."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "lib"))

import blender_mcp as mcp  # noqa: E402


def test_tools_are_typed_and_have_no_execute_code() -> None:
    names = [t["name"] for t in mcp.list_tools()]
    assert "occupancy_status" in names
    assert "create_primitive" in names
    assert "export_glb" in names
    assert "execute_code" not in names
    assert "execute_blender_code" not in names
    blob = json.dumps(mcp.list_tools())
    assert "telemetry" not in blob.lower()
    assert "hyper3d" not in blob.lower()
    assert "hunyuan" not in blob.lower()


def test_occupancy_status_reads_state_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    payload = {
        "version": 1,
        "mode": "blender-desk",
        "compose": True,
        "parked": True,
        "blender_pid": 0,
        "mcp_pid": 0,
    }
    (tmp_path / ".occupancy.json").write_text(json.dumps(payload), encoding="utf-8")
    result = mcp.call_tool("occupancy_status", {})
    assert result["ok"] is True
    assert result["occupancy"]["mode"] == "blender-desk"
    assert result["occupancy"]["parked"] is True


def test_desk_allowed_parked_and_refuses_heavy(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    (tmp_path / ".occupancy.json").write_text(
        json.dumps({"mode": "blender-desk", "parked": True, "compose": True}),
        encoding="utf-8",
    )
    assert mcp.desk_allowed() is True
    (tmp_path / ".occupancy.json").write_text(
        json.dumps({"mode": "ltx", "parked": False, "compose": True}),
        encoding="utf-8",
    )
    assert mcp.desk_allowed() is False
    blocked = mcp.call_tool("create_primitive", {"kind": "cube"})
    assert blocked["ok"] is False
    assert "blender-desk" in blocked["error"]


def test_create_primitive_rejects_unknown_kind(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    (tmp_path / ".occupancy.json").write_text(
        json.dumps({"mode": "blender-desk", "parked": True, "compose": True}),
        encoding="utf-8",
    )
    result = mcp.call_tool("create_primitive", {"kind": "suzanne"})
    assert result["ok"] is False


def test_export_glb_refuses_models_dir(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    (tmp_path / ".occupancy.json").write_text(
        json.dumps({"mode": "idle", "parked": False, "compose": False}),
        encoding="utf-8",
    )
    result = mcp.call_tool("export_glb", {"path": "/mnt/models/evil.glb"})
    assert result["ok"] is False
    assert "MODELS_DIR" in result["error"]


def test_occupancy_enter_requires_mode() -> None:
    result = mcp.call_tool("occupancy_enter", {})
    assert result["ok"] is False


def test_unknown_tool_and_rpc_call(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    (tmp_path / ".occupancy.json").write_text(
        json.dumps({"mode": "blender-desk", "parked": True, "compose": True}),
        encoding="utf-8",
    )
    assert mcp.call_tool("nope", {})["ok"] is False
    ping = mcp.handle_rpc({"jsonrpc": "2.0", "id": 3, "method": "ping"})
    assert ping is not None
    called = mcp.handle_rpc(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "occupancy_status", "arguments": {}},
        }
    )
    assert called is not None
    assert called["result"]["isError"] is False
    missing = mcp.handle_rpc({"jsonrpc": "2.0", "id": 5, "method": "nope"})
    assert missing is not None
    assert "error" in missing


def test_jsonrpc_initialize_and_tools_list() -> None:
    init = mcp.handle_rpc(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    )
    assert init is not None
    assert init["result"]["serverInfo"]["name"] == "ez-blender"
    listed = mcp.handle_rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    assert listed is not None
    names = [t["name"] for t in listed["result"]["tools"]]
    assert "occupancy_enter" in names
    assert mcp.handle_rpc({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None


def test_main_list_tools_and_call(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    (tmp_path / ".occupancy.json").write_text(
        json.dumps({"mode": "blender-desk", "parked": True}),
        encoding="utf-8",
    )
    assert mcp.main(["--help"]) == 0
    assert mcp.main(["--list-tools"]) == 0
    out = capsys.readouterr().out
    assert "occupancy_status" in out
    assert mcp.main(["--call", "occupancy_status"]) == 0
    assert mcp.main(["--nope"]) == 1
    assert mcp.main(["--call"]) == 1


def test_bpy_tools_fail_without_blender(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("PATH", str(tmp_path / "bin"))
    (tmp_path / "bin").mkdir()
    (tmp_path / ".occupancy.json").write_text(
        json.dumps({"mode": "blender-desk", "parked": True, "compose": True}),
        encoding="utf-8",
    )
    assert mcp.call_tool("scene_info", {})["ok"] is False
    assert mcp.call_tool("set_camera", {"location": [0, 1, 2]})["ok"] is False
    assert mcp.call_tool("keyframe_object", {"name": "Cube"})["ok"] is False
    cube = mcp.call_tool("create_primitive", {"kind": "cube", "name": "box"})
    assert cube["ok"] is False
    glb = mcp.call_tool("export_glb", {"path": str(tmp_path / "assets" / "x.glb")})
    assert glb["ok"] is False
    assert mcp.call_tool("keyframe_object", {})["ok"] is False


def test_source_has_no_execute_handler() -> None:
    text = (ROOT / "scripts" / "lib" / "blender_mcp.py").read_text(encoding="utf-8")
    assert "def execute_code" not in text
    assert "DISABLE_TELEMETRY" not in text
    assert "hyper3d" not in text.lower()
