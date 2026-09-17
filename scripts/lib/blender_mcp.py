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
from pathlib import Path
from typing import Any

from mcp_runtime import (
    ToolSpec,
    call_tool as _runtime_call_tool,
    handle_rpc as _runtime_handle_rpc,
    list_tools as _runtime_list_tools,
    main_cli,
    serve_stdio as _runtime_serve_stdio,
)

# MCP protocol identity (JSON-RPC initialize.serverInfo).
PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "ez-blender"
SERVER_VERSION = "1"


def _repo_root() -> Path:
    """Return the repository root (parent of ``scripts/``).

    Returns:
        Absolute repo path.
    """
    return Path(__file__).resolve().parents[2]


def _output_dir() -> Path:
    """Return COMFY_OUTPUT_DIR (host occupancy / asset dump root).

    Returns:
        Output directory path.
    """
    return Path(os.environ.get("COMFY_OUTPUT_DIR", "/mnt/comfy-output"))


def _occupancy_bin() -> Path:
    """Return the occupancy.sh path (EZ_OCCUPANCY_BIN override).

    Returns:
        Occupancy helper path.
    """
    override = os.environ.get("EZ_OCCUPANCY_BIN")
    if override:
        return Path(override)
    return _repo_root() / "scripts" / "utilities" / "occupancy.sh"


def occupancy_status() -> dict[str, Any]:
    """Read occupancy JSON (file, or occupancy.sh --json).

    Returns:
        Occupancy mapping (JSON boundary).
    """
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
    """True when bpy tools may run (parked blender-desk, or compose down).

    Returns:
        Whether live bpy tools are allowed.
    """
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
    """Return an error payload when blender-desk is not occupied.

    Returns:
        Error mapping, or None when bpy tools may run.
    """
    if desk_allowed():
        return None
    return {
        "ok": False,
        "error": "occupancy enter blender-desk first (Comfy is a heavy job)",
    }


def _run_occupancy_enter(mode: str, yes: bool) -> dict[str, Any]:
    """Run ``occupancy.sh enter MODE``.

    Args:
        mode: Occupancy mode (idle, blender-desk, klein, …).
        yes: Pass ``--yes`` (skip confirm).

    Returns:
        Tool payload with ok/returncode/stderr.
    """
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


def _is_executable(path: Path) -> bool:
    """True when path is a regular executable file.

    Args:
        path: Candidate binary.

    Returns:
        Whether the path is an executable file.
    """
    try:
        return path.is_file() and os.access(path, os.X_OK)
    except OSError:
        return False


def _well_known_blender_paths() -> tuple[Path, ...]:
    """Host locations besides PATH (never the Comfy image).

    Returns:
        Candidate blender binaries.
    """
    home = Path.home()
    paths: list[Path] = [
        home / ".local" / "bin" / "blender",
        home / ".local" / "opt" / "blender" / "blender",
    ]
    if os.environ.get("LAB_HERMETIC") != "1":
        paths.extend(
            (
                Path("/usr/bin/blender"),
                Path("/usr/local/bin/blender"),
                Path("/snap/bin/blender"),
                Path("/opt/blender/blender"),
            )
        )
    return tuple(paths)


def _blender_bin() -> str | None:
    """Resolve a host blender binary (BLENDER_BIN, PATH, well-known).

    Returns:
        Absolute path string, or None if missing.
    """
    override = os.environ.get("BLENDER_BIN", "").strip()
    if override:
        cand = Path(override)
        if _is_executable(cand):
            return str(cand)
    which = shutil.which("blender")
    if which:
        return which
    for cand in _well_known_blender_paths():
        if _is_executable(cand):
            return str(cand)
    return None


def _run_blender(script: str, blend: str | None = None) -> dict[str, Any]:
    """Run ``blender --background [--python-expr]``.

    Args:
        script: Python expression passed to ``--python-expr``.
        blend: Optional .blend path.

    Returns:
        Tool payload with ok/returncode/stdout/stderr.
    """
    binary = _blender_bin()
    if binary is None:
        return {
            "ok": False,
            "error": "blender not on PATH. ./scripts/manage.sh blender-install",
        }
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
    """MCP tool: read occupancy JSON.

    Args:
        _args: Unused tool arguments.

    Returns:
        ``{ok, occupancy}``.
    """
    return {"ok": True, "occupancy": occupancy_status()}


def tool_occupancy_enter(args: dict[str, Any]) -> dict[str, Any]:
    """MCP tool: enter an occupancy mode (does not start Compose).

    Args:
        args: ``mode`` (required), optional ``yes``.

    Returns:
        Occupancy-enter payload or error.
    """
    mode = str(args.get("mode") or "")
    yes = bool(args.get("yes") or False)
    if not mode:
        return {"ok": False, "error": "mode is required"}
    return _run_occupancy_enter(mode, yes)


def tool_scene_info(args: dict[str, Any]) -> dict[str, Any]:
    """MCP tool: list object names in the current Blender scene.

    Args:
        args: Optional ``blend`` path.

    Returns:
        Blender run payload or occupancy error.
    """
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
    """MCP tool: add a Workbench primitive.

    Args:
        args: Optional ``kind`` and ``name``.

    Returns:
        Blender run payload or error.
    """
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
    """MCP tool: set Camera location.

    Args:
        args: Optional ``location`` ``[x, y, z]``.

    Returns:
        Blender run payload or occupancy error.
    """
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
    """MCP tool: insert a location keyframe on a named object.

    Args:
        args: Required ``name``, optional ``frame``.

    Returns:
        Blender run payload or error.
    """
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
    """MCP tool: export GLB under COMFY_OUTPUT_DIR/assets.

    Args:
        args: Optional ``path``.

    Returns:
        Blender run payload (includes ``path``) or error.
    """
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
    """Run a host utility under ``scripts/utilities``.

    Args:
        script_name: Basename (e.g. ``blender-guide.sh``).
        extra: Extra argv after the script.

    Returns:
        Subprocess payload or occupancy error.
    """
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
    """MCP tool: dump a 5.00s clay/depth/canny guide pack.

    Args:
        args: Optional ``film``, ``shot``, ``blend``.

    Returns:
        blender-guide.sh payload.
    """
    film = str(args.get("film") or "go-see")
    shot = str(args.get("shot") or "12")
    extra = ["--film", film, "--shot", shot]
    if args.get("blend"):
        extra.extend(["--blend", str(args["blend"])])
    return _run_utility("blender-guide.sh", extra)


def tool_blender_stills(args: dict[str, Any]) -> dict[str, Any]:
    """MCP tool: dump a creator still pack.

    Args:
        args: Optional ``film``, ``plate``, ``size``, ``blend``.

    Returns:
        blender-stills.sh payload.
    """
    film = str(args.get("film") or "go-see")
    plate = str(args.get("plate") or "mug")
    extra = ["--film", film, "--plate", plate]
    if args.get("size"):
        extra.extend(["--size", str(args["size"])])
    if args.get("blend"):
        extra.extend(["--blend", str(args["blend"])])
    return _run_utility("blender-stills.sh", extra)


def tool_house_views(args: dict[str, Any]) -> dict[str, Any]:
    """MCP tool: dump Instagram 4:5 greybox stills + GLB.

    Args:
        args: Optional ``slug``.

    Returns:
        house-views.sh payload.
    """
    slug = str(args.get("slug") or "lab-penthouse")
    return _run_utility("house-views.sh", ["--slug", slug])


# Typed MCP tool table (names are the public tool ids).
TOOLS: dict[str, ToolSpec] = {
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
    """List MCP tools without handlers.

    Returns:
        ``{name, description, inputSchema}`` rows.
    """
    return _runtime_list_tools(TOOLS)


def call_tool(
    name: str, arguments: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Dispatch a named MCP tool.

    Args:
        name: Tool id.
        arguments: JSON-object arguments (JSON boundary).

    Returns:
        Tool payload (``ok`` false on unknown tool).
    """
    return _runtime_call_tool(TOOLS, name, arguments)


def handle_rpc(message: dict[str, Any]) -> dict[str, Any] | None:
    """Handle one JSON-RPC message. Notifications return None.

    Args:
        message: Parsed JSON-RPC request (JSON boundary).

    Returns:
        Response object, or None for notifications.
    """
    return _runtime_handle_rpc(
        message,
        tools=TOOLS,
        server_name=SERVER_NAME,
        server_version=SERVER_VERSION,
        protocol_version=PROTOCOL_VERSION,
    )


def serve_stdio() -> None:
    """Serve JSON-RPC on stdin/stdout (one JSON object per line)."""
    _runtime_serve_stdio(handle_rpc)


def main(argv: list[str] | None = None) -> int:
    """CLI: --stdio | --list-tools | --call TOOL [JSON].

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Process status.
    """
    return main_cli(
        argv,
        tools=TOOLS,
        prog="blender_mcp.py",
        usage_extra=(
            "Occupancy-aware Blender MCP. No execute_code. No telemetry."
        ),
        handle=handle_rpc,
    )


if __name__ == "__main__":
    raise SystemExit(main())
