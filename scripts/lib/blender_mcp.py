#!/usr/bin/env python3
"""Occupancy-aware Blender MCP (stdlib JSON-RPC). No execute_code, no telemetry.

Tools wrap occupancy.sh and host ``blender --background``. Live bpy tools
require blender-desk (or compose down). Never in the Docker image.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Mapping

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "ez-blender"
SERVER_VERSION = "1"

ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _output_dir() -> Path:
    return Path(os.environ.get("COMFY_OUTPUT_DIR", "/mnt/comfy-output"))


def _occupancy_bin() -> Path:
    override = os.environ.get("EZ_OCCUPANCY_BIN")
    if override:
        return Path(override)
    return _repo_root() / "scripts" / "utilities" / "occupancy.sh"


def occupancy_status() -> dict[str, Any]:
    """Read occupancy JSON (file, or occupancy.sh --json)."""
    path = _output_dir() / ".occupancy.json"
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
    binary = _occupancy_bin()
    if binary.is_file():
        proc = subprocess.run(
            [str(binary), "status", "--json"],
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            try:
                parsed = json.loads(proc.stdout)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass
    return {
        "version": 1,
        "mode": "idle",
        "compose": False,
        "parked": False,
        "blender_pid": 0,
        "mcp_pid": 0,
    }


def desk_allowed() -> bool:
    """True when bpy tools may run (parked blender-desk, or compose down)."""
    state = occupancy_status()
    mode = str(state.get("mode") or "idle")
    parked = bool(state.get("parked"))
    compose = bool(state.get("compose") or state.get("compose_live"))
    if mode == "blender-desk" and (parked or not compose):
        return True
    if not compose and mode in ("idle", "blender-desk"):
        return True
    return False


def _require_desk() -> dict[str, Any] | None:
    if desk_allowed():
        return None
    return {
        "ok": False,
        "error": "occupancy enter blender-desk first (Comfy is a heavy job)",
    }


def _run_occupancy_enter(mode: str, yes: bool) -> dict[str, Any]:
    binary = _occupancy_bin()
    cmd = [str(binary), "enter", mode]
    if yes:
        cmd.append("--yes")
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stderr": (proc.stderr or "").strip(),
        "mode": mode,
    }


def _blender_bin() -> str | None:
    return shutil.which("blender")


def _run_blender(script: str, blend: str | None = None) -> dict[str, Any]:
    binary = _blender_bin()
    if binary is None:
        return {"ok": False, "error": "blender not on PATH"}
    cmd = [binary, "--background"]
    if blend:
        cmd.append(blend)
    cmd.extend(["--python-expr", script])
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": (proc.stdout or "").strip(),
        "stderr": (proc.stderr or "").strip(),
    }


def tool_occupancy_status(_args: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, "occupancy": occupancy_status()}


def tool_occupancy_enter(args: dict[str, Any]) -> dict[str, Any]:
    mode = str(args.get("mode") or "")
    yes = bool(args.get("yes") or False)
    if not mode:
        return {"ok": False, "error": "mode is required"}
    return _run_occupancy_enter(mode, yes)


def tool_scene_info(args: dict[str, Any]) -> dict[str, Any]:
    blocked = _require_desk()
    if blocked:
        return blocked
    blend = args.get("blend")
    script = (
        "import bpy, json; "
        "print(json.dumps({'objects': [o.name for o in bpy.data.objects]}))"
    )
    return _run_blender(script, str(blend) if blend else None)


def tool_create_primitive(args: dict[str, Any]) -> dict[str, Any]:
    blocked = _require_desk()
    if blocked:
        return blocked
    kind = str(args.get("kind") or "cube")
    name = str(args.get("name") or kind)
    allowed = {"cube", "uv_sphere", "cylinder", "plane", "cone"}
    if kind not in allowed:
        return {"ok": False, "error": f"kind must be one of {sorted(allowed)}"}
    op = {
        "cube": "primitive_cube_add",
        "uv_sphere": "primitive_uv_sphere_add",
        "cylinder": "primitive_cylinder_add",
        "plane": "primitive_plane_add",
        "cone": "primitive_cone_add",
    }[kind]
    script = (
        "import bpy; "
        f"bpy.ops.mesh.{op}(); "
        "obj = bpy.context.active_object; "
        f"obj.name = {name!r}; "
        f"print({name!r})"
    )
    result = _run_blender(script)
    result["name"] = name
    result["kind"] = kind
    return result


def tool_set_camera(args: dict[str, Any]) -> dict[str, Any]:
    blocked = _require_desk()
    if blocked:
        return blocked
    loc = args.get("location") or [0, -8, 2]
    if not isinstance(loc, list) or len(loc) < 3:
        loc = [0, -8, 2]
    script = (
        "import bpy; "
        "cam = bpy.data.objects.get('Camera') or bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera')); "
        f"cam.location = ({float(loc[0])}, {float(loc[1])}, {float(loc[2])}); "
        "print(cam.name)"
    )
    return _run_blender(script)


def tool_keyframe_object(args: dict[str, Any]) -> dict[str, Any]:
    blocked = _require_desk()
    if blocked:
        return blocked
    name = str(args.get("name") or "")
    frame = int(args.get("frame") or 1)
    if not name:
        return {"ok": False, "error": "name is required"}
    script = (
        "import bpy; "
        f"obj = bpy.data.objects.get({name!r}); "
        "assert obj is not None; "
        f"obj.keyframe_insert(data_path='location', frame={frame}); "
        "print('ok')"
    )
    return _run_blender(script)


def tool_export_glb(args: dict[str, Any]) -> dict[str, Any]:
    blocked = _require_desk()
    if blocked:
        return blocked
    dest = args.get("path")
    if not dest:
        dest = str(_output_dir() / "assets" / "objects" / "mcp-export.glb")
    dest_s = str(dest)
    if "models" in Path(dest_s).parts and "assets" not in Path(dest_s).parts:
        return {"ok": False, "error": "GLB must not land in MODELS_DIR"}
    script = (
        "import bpy; "
        f"bpy.ops.export_scene.gltf(filepath={dest_s!r}, export_format='GLB'); "
        f"print({dest_s!r})"
    )
    result = _run_blender(script)
    result["path"] = dest_s
    return result


def _run_utility(script_name: str, extra: list[str]) -> dict[str, Any]:
    blocked = _require_desk()
    if blocked:
        return blocked
    path = _repo_root() / "scripts" / "utilities" / script_name
    proc = subprocess.run(
        [str(path), *extra],
        check=False,
        capture_output=True,
        text=True,
    )
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stderr": (proc.stderr or "").strip(),
        "stdout": (proc.stdout or "").strip(),
    }


def tool_export_guides(args: dict[str, Any]) -> dict[str, Any]:
    film = str(args.get("film") or "go-see")
    shot = str(args.get("shot") or "12")
    extra = ["--film", film, "--shot", shot]
    if args.get("blend"):
        extra.extend(["--blend", str(args["blend"])])
    return _run_utility("blender-guide.sh", extra)


def tool_blender_stills(args: dict[str, Any]) -> dict[str, Any]:
    film = str(args.get("film") or "go-see")
    plate = str(args.get("plate") or "mug")
    extra = ["--film", film, "--plate", plate]
    if args.get("size"):
        extra.extend(["--size", str(args["size"])])
    if args.get("blend"):
        extra.extend(["--blend", str(args["blend"])])
    return _run_utility("blender-stills.sh", extra)


def tool_house_views(args: dict[str, Any]) -> dict[str, Any]:
    slug = str(args.get("slug") or "lab-penthouse")
    return _run_utility("house-views.sh", ["--slug", slug])


TOOLS: dict[str, dict[str, Any]] = {
    "occupancy_status": {
        "description": "Read GB10 occupancy mode, parked flag, and PIDs.",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": tool_occupancy_status,
    },
    "occupancy_enter": {
        "description": "Enter idle|blender-desk|klein|trellis|wan|ltx. Does not start Compose.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mode": {"type": "string"},
                "yes": {"type": "boolean"},
            },
            "required": ["mode"],
        },
        "handler": tool_occupancy_enter,
    },
    "scene_info": {
        "description": "List object names in the current Blender scene.",
        "inputSchema": {
            "type": "object",
            "properties": {"blend": {"type": "string"}},
        },
        "handler": tool_scene_info,
    },
    "create_primitive": {
        "description": "Add a Workbench primitive (cube, uv_sphere, cylinder, plane, cone).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kind": {"type": "string"},
                "name": {"type": "string"},
            },
        },
        "handler": tool_create_primitive,
    },
    "set_camera": {
        "description": "Set Camera location [x,y,z].",
        "inputSchema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "array",
                    "items": {"type": "number"},
                }
            },
        },
        "handler": tool_set_camera,
    },
    "keyframe_object": {
        "description": "Insert a location keyframe on a named object.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "frame": {"type": "integer"},
            },
            "required": ["name"],
        },
        "handler": tool_keyframe_object,
    },
    "export_glb": {
        "description": "Export GLB under COMFY_OUTPUT_DIR/assets (never MODELS_DIR).",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
        },
        "handler": tool_export_glb,
    },
    "export_guides": {
        "description": "Dump a 5.00s clay/depth/canny guide pack (host blender-guide.sh).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "film": {"type": "string"},
                "shot": {"type": "string"},
                "blend": {"type": "string"},
            },
        },
        "handler": tool_export_guides,
    },
    "blender_stills": {
        "description": "Dump a creator still pack (host blender-stills.sh).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "film": {"type": "string"},
                "plate": {"type": "string"},
                "size": {"type": "string"},
                "blend": {"type": "string"},
            },
        },
        "handler": tool_blender_stills,
    },
    "house_views": {
        "description": "Dump Instagram 4:5 greybox stills + GLB (host house-views.sh).",
        "inputSchema": {
            "type": "object",
            "properties": {"slug": {"type": "string"}},
        },
        "handler": tool_house_views,
    },
}


def list_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "description": spec["description"],
            "inputSchema": spec["inputSchema"],
        }
        for name, spec in TOOLS.items()
    ]


def call_tool(name: str, arguments: Mapping[str, Any] | None = None) -> dict[str, Any]:
    spec = TOOLS.get(name)
    if spec is None:
        return {"ok": False, "error": f"unknown tool {name}"}
    handler: ToolHandler = spec["handler"]
    return handler(dict(arguments or {}))


def _rpc_result(msg_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def _rpc_error(msg_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def handle_rpc(message: dict[str, Any]) -> dict[str, Any] | None:
    """Handle one JSON-RPC message. Notifications return None."""
    method = str(message.get("method") or "")
    msg_id = message.get("id")
    params = message.get("params") or {}
    if method == "notifications/initialized":
        return None
    if method == "initialize":
        return _rpc_result(
            msg_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        )
    if method == "ping":
        return _rpc_result(msg_id, {})
    if method == "tools/list":
        return _rpc_result(msg_id, {"tools": list_tools()})
    if method == "tools/call":
        name = str(params.get("name") or "")
        arguments = params.get("arguments") or {}
        payload = call_tool(name, arguments if isinstance(arguments, dict) else {})
        text = json.dumps(payload)
        return _rpc_result(
            msg_id,
            {"content": [{"type": "text", "text": text}], "isError": not payload.get("ok", True)},
        )
    if msg_id is None:
        return None
    return _rpc_error(msg_id, -32601, f"method not found: {method}")


def serve_stdio() -> None:
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
        reply = handle_rpc(message)
        if reply is not None:
            sys.stdout.write(json.dumps(reply) + "\n")
            sys.stdout.flush()


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("--stdio", "stdio"):
        serve_stdio()
        return 0
    if args[0] in ("-h", "--help", "help"):
        sys.stderr.write(
            "Usage: blender_mcp.py [--stdio] | --list-tools | --call TOOL [JSON]\n"
            "  Occupancy-aware Blender MCP. No execute_code. No telemetry.\n"
        )
        return 0
    if args[0] == "--list-tools":
        json.dump(list_tools(), sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    if args[0] == "--call":
        if len(args) < 2:
            sys.stderr.write("blender_mcp.py --call TOOL [JSON args]\n")
            return 1
        payload: dict[str, Any] = {}
        if len(args) >= 3:
            payload = json.loads(args[2])
        result = call_tool(args[1], payload)
        json.dump(result, sys.stdout)
        sys.stdout.write("\n")
        return 0 if result.get("ok", True) else 1
    sys.stderr.write(f"unknown arg: {args[0]}\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
