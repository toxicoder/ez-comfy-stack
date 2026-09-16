"""In-tree Blender MCP: typed tools, occupancy, no execute_code."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

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


def test_blender_bin_honors_blender_bin_and_well_known(
    tmp_path: Path, monkeypatch
) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.delenv("BLENDER_BIN", raising=False)
    monkeypatch.setenv("PATH", str(empty))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("LAB_HERMETIC", "1")
    (tmp_path / "home").mkdir()
    assert mcp._blender_bin() is None

    off = tmp_path / "offpath" / "blender"
    off.parent.mkdir()
    off.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    off.chmod(0o755)
    monkeypatch.setenv("BLENDER_BIN", str(off))
    assert mcp._blender_bin() == str(off)

    monkeypatch.delenv("BLENDER_BIN", raising=False)
    local_bin = tmp_path / "home" / ".local" / "bin" / "blender"
    local_bin.parent.mkdir(parents=True)
    local_bin.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    local_bin.chmod(0o755)
    assert mcp._blender_bin() == str(local_bin)


def test_well_known_blender_paths_skip_system_when_hermetic(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.delenv("LAB_HERMETIC", raising=False)
    live = {str(p) for p in mcp._well_known_blender_paths()}
    assert "/usr/bin/blender" in live
    assert "/opt/blender/blender" in live
    monkeypatch.setenv("LAB_HERMETIC", "1")
    hermetic = {str(p) for p in mcp._well_known_blender_paths()}
    assert "/usr/bin/blender" not in hermetic
    assert str(tmp_path / "home" / ".local" / "bin" / "blender") in hermetic


def test_bpy_tools_fail_without_blender(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("PATH", str(tmp_path / "bin"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("LAB_HERMETIC", "1")
    monkeypatch.delenv("BLENDER_BIN", raising=False)
    (tmp_path / "bin").mkdir()
    (tmp_path / "home").mkdir()
    (tmp_path / ".occupancy.json").write_text(
        json.dumps({"mode": "blender-desk", "parked": True, "compose": True}),
        encoding="utf-8",
    )
    missed = mcp.call_tool("scene_info", {})
    assert missed["ok"] is False
    assert "blender-install" in missed["error"]
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


def _park_desk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    (tmp_path / ".occupancy.json").write_text(
        json.dumps({"mode": "blender-desk", "parked": True, "compose": True}),
        encoding="utf-8",
    )


def test_occupancy_bin_default_and_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("EZ_OCCUPANCY_BIN", raising=False)
    default = mcp._occupancy_bin()
    assert default.name == "occupancy.sh"
    override = tmp_path / "occ.sh"
    override.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    override.chmod(0o755)
    monkeypatch.setenv("EZ_OCCUPANCY_BIN", str(override))
    assert mcp._occupancy_bin() == override


def test_occupancy_status_falls_back_to_script(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    occ = tmp_path / "occ.sh"
    occ.write_text(
        "#!/usr/bin/env bash\necho '{\"mode\":\"from-sh\",\"parked\":true}'\n",
        encoding="utf-8",
    )
    occ.chmod(0o755)
    monkeypatch.setenv("EZ_OCCUPANCY_BIN", str(occ))
    (tmp_path / ".occupancy.json").write_text("not-json", encoding="utf-8")
    assert mcp.occupancy_status()["mode"] == "from-sh"
    occ.write_text("#!/usr/bin/env bash\necho '[1,2]'\n", encoding="utf-8")
    occ.chmod(0o755)
    assert mcp.occupancy_status()["mode"] == "idle"
    occ.write_text("#!/usr/bin/env bash\necho not-json\n", encoding="utf-8")
    occ.chmod(0o755)
    assert mcp.occupancy_status()["mode"] == "idle"
    occ.write_text("#!/usr/bin/env bash\nexit 2\n", encoding="utf-8")
    occ.chmod(0o755)
    assert mcp.occupancy_status()["mode"] == "idle"
    (tmp_path / ".occupancy.json").write_text("[1]", encoding="utf-8")
    assert mcp.occupancy_status()["mode"] == "idle"


def test_occupancy_enter_runs_script(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    occ = tmp_path / "occ.sh"
    occ.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    occ.chmod(0o755)
    monkeypatch.setenv("EZ_OCCUPANCY_BIN", str(occ))
    yes = mcp.call_tool("occupancy_enter", {"mode": "idle", "yes": True})
    assert yes["ok"] is True
    no = mcp.call_tool("occupancy_enter", {"mode": "klein"})
    assert no["ok"] is True


def test_is_executable_oserror(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "blender"
    target.write_text("x", encoding="utf-8")

    def boom(_path: object, _mode: int) -> bool:
        raise OSError("stat")

    monkeypatch.setattr(os, "access", boom)
    assert mcp._is_executable(target) is False


def test_blender_bin_which(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bindir = tmp_path / "bin"
    bindir.mkdir()
    blender = bindir / "blender"
    blender.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    blender.chmod(0o755)
    monkeypatch.setenv("PATH", str(bindir))
    monkeypatch.delenv("BLENDER_BIN", raising=False)
    monkeypatch.setenv("LAB_HERMETIC", "1")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()
    assert mcp._blender_bin() == str(blender)


def test_bpy_tools_with_fake_blender(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _park_desk(tmp_path, monkeypatch)
    fake = tmp_path / "blender"
    fake.write_text("#!/usr/bin/env bash\necho ok\nexit 0\n", encoding="utf-8")
    fake.chmod(0o755)
    monkeypatch.setenv("BLENDER_BIN", str(fake))
    scene = mcp.call_tool("scene_info", {"blend": str(tmp_path / "x.blend")})
    assert scene["ok"] is True
    cube = mcp.call_tool("create_primitive", {"kind": "cube", "name": "box"})
    assert cube["ok"] is True
    cam = mcp.call_tool("set_camera", {"location": [1, 2, 3]})
    assert cam["ok"] is True
    cam_default = mcp.call_tool("set_camera", {"location": "bad"})
    assert cam_default["ok"] is True
    key = mcp.call_tool("keyframe_object", {"name": "Cube", "frame": 2})
    assert key["ok"] is True
    glb = mcp.call_tool("export_glb", {})
    assert glb["ok"] is True
    assert "mcp-export.glb" in glb["path"]


def test_utility_tools_fake_subprocess(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _park_desk(tmp_path, monkeypatch)

    def fake_run(cmd: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, 0, stdout="dumped", stderr="")

    monkeypatch.setattr(mcp.subprocess, "run", fake_run)
    guides = mcp.call_tool(
        "export_guides", {"film": "go-see", "shot": "12", "blend": "a.blend"}
    )
    assert guides["ok"] is True
    stills = mcp.call_tool(
        "blender_stills",
        {"film": "go-see", "plate": "mug", "size": "1024x1024", "blend": "b.blend"},
    )
    assert stills["ok"] is True
    house = mcp.call_tool("house_views", {"slug": "lab-penthouse"})
    assert house["ok"] is True


def test_utility_and_bpy_blocked_when_heavy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    (tmp_path / ".occupancy.json").write_text(
        json.dumps({"mode": "ltx", "parked": False, "compose": True}),
        encoding="utf-8",
    )
    assert mcp.call_tool("scene_info", {})["ok"] is False
    assert mcp.call_tool("set_camera", {})["ok"] is False
    assert mcp.call_tool("keyframe_object", {"name": "Cube"})["ok"] is False
    assert mcp.call_tool("export_glb", {"path": str(tmp_path / "x.glb")})["ok"] is False
    assert mcp.call_tool("export_guides", {})["ok"] is False


def test_handle_rpc_unknown_notification_and_stdio(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert mcp.handle_rpc({"method": "nope"}) is None
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(
            "\nnot-json\n[1,2]\n"
            '{"jsonrpc":"2.0","id":1,"method":"ping"}\n'
            '{"method":"notifications/initialized"}\n'
        ),
    )
    mcp.serve_stdio()
    out = capsys.readouterr().out.strip().splitlines()
    assert json.loads(out[0])["id"] == 1


def test_main_stdio_and_call_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    (tmp_path / ".occupancy.json").write_text(
        json.dumps({"mode": "idle"}), encoding="utf-8"
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
    assert mcp.main([]) == 0
    assert mcp.main(["--stdio"]) == 0
    assert mcp.main(["--call", "occupancy_status", "{}"]) == 0
    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert payload["ok"] is True
