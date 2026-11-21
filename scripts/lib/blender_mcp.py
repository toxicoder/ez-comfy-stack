#!/usr/bin/env python3
"""Occupancy-aware Blender MCP (stdlib JSON-RPC). No execute_code, no telemetry.

Tools wrap occupancy.sh and host ``blender --background``. Live bpy tools
require blender-desk (or compose down), and only while that desk has a live
sidecar - :mod:`ez_common.occupancy` decides, so an orphaned record cannot
refuse forever. Never in the Docker image.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, NotRequired, TypedDict, cast

from mcp_runtime import (
    JsonRpcRequest,
    JsonRpcResponse,
    ToolArgs,
    ToolCatalogEntry,
    ToolNumber,
    ToolResult,
    ToolSpec,
    call_tool as _runtime_call_tool,
    handle_rpc as _runtime_handle_rpc,
    list_tools as _runtime_list_tools,
    main_cli,
    serve_stdio as _runtime_serve_stdio,
)

if TYPE_CHECKING:
    from ez_common import Json, JsonObject, Occupancy

# MCP protocol identity (JSON-RPC initialize.serverInfo).
PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "ez-blender"
SERVER_VERSION = "1"


class BlenderRunResult(TypedDict):
    """One host subprocess payload returned by a Blender MCP tool."""

    ok: bool
    """True when the subprocess exited 0."""

    returncode: NotRequired[int]
    """Process exit status (absent on a refusal that never ran)."""

    stdout: NotRequired[str]
    """Stripped stdout."""

    stderr: NotRequired[str]
    """Stripped stderr."""

    error: NotRequired[str]
    """Refusal text when the tool never ran."""

    mode: NotRequired[str]
    """Occupancy mode entered (``occupancy_enter``)."""

    name: NotRequired[str]
    """Object name added (``create_primitive``)."""

    kind: NotRequired[str]
    """Primitive kind added (``create_primitive``)."""

    path: NotRequired[str]
    """Export destination (``export_glb``)."""


def _repo_root() -> Path:
    """Return the repository root (parent of ``scripts/``).

    Returns:
        Absolute repo path.
    """
    return Path(__file__).resolve().parents[2]


_LLM_DESK_MODE = "llm-desk"
"""Desk mode whose claim is the host llama-server holding the GPU."""


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


def _ensure_custom_nodes_path() -> None:
    """Prepend ``custom_nodes/`` so the shared occupancy reader resolves."""
    custom = str(_repo_root() / "custom_nodes")
    if custom not in sys.path:
        sys.path.insert(0, custom)


def _occupancy_view(state: JsonObject) -> Occupancy:
    """Read one occupancy mapping through the shared policy.

    The mode string alone cannot tell a live desk from a record its sidecar
    left behind; :mod:`ez_common.occupancy` is the one reader that weighs the
    holder PIDs against the liveness map the host stamps into the file.

    Args:
        state: Mapping from :func:`occupancy_status`.

    Returns:
        The shared immutable read.
    """
    _ensure_custom_nodes_path()
    from ez_common import occupancy

    return occupancy.parse_state(state)


def _desk_recovery_command() -> str:
    """Build the documented host command that takes the desk.

    Returns:
        Copy-pasteable ``//:manage`` command naming the verb, not a process.
    """
    _ensure_custom_nodes_path()
    from ez_common import occupancy

    return occupancy.recovery_command("blender-desk")


def occupancy_status() -> JsonObject:
    """Read occupancy JSON (file, or occupancy.sh --json).

    Returns:
        Occupancy mapping (JSON boundary).
    """
    path = _output_dir() / ".occupancy.json"
    if path.is_file():
        try:
            data: Json = json.loads(path.read_text(encoding="utf-8"))
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
                parsed: Json = json.loads(proc.stdout)
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
        "llm_pid": 0,
    }


def desk_allowed() -> bool:
    """True when bpy tools may run (parked blender-desk, or compose down).

    The decision is taken against the shared reader: a heavy mode owns the GPU,
    a live ``llm-desk`` sidecar is itself the GPU job, and any other desk claim
    counts only while its sidecar lives. A record left behind by a killed
    Blender or a host reboot therefore reads as released instead of refusing
    forever, while a live holder still refuses.

    Returns:
        Whether live bpy tools are allowed.
    """
    state = occupancy_status()
    view = _occupancy_view(state)
    if view.is_heavy:
        return False
    if view.mode == _LLM_DESK_MODE and view.holder_live:
        return False
    parked = bool(state.get("parked"))
    compose = bool(state.get("compose") or state.get("compose_live"))
    return parked or not compose


def _require_desk() -> BlenderRunResult | None:
    """Return an error payload when blender-desk is not occupied.

    Returns:
        Error mapping, or None when bpy tools may run.
    """
    if desk_allowed():
        return None
    return {
        "ok": False,
        "error": (
            "Comfy is a heavy GPU job - take the desk first: "
            f"{_desk_recovery_command()}"
        ),
    }


def _run_occupancy_enter(mode: str, yes: bool) -> BlenderRunResult:
    """Run ``occupancy.sh enter MODE``.

    Args:
        mode: Occupancy mode (idle, blender-desk, klein, ...).
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


def _run_blender(script: str, blend: str | None = None) -> BlenderRunResult:
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


def tool_occupancy_status(_args: ToolArgs) -> ToolResult:
    """MCP tool: read occupancy JSON.

    Args:
        _args: Unused tool arguments.

    Returns:
        ``{ok, occupancy}``.
    """
    return {"ok": True, "occupancy": occupancy_status()}


def tool_occupancy_enter(args: ToolArgs) -> ToolResult:
    """MCP tool: enter an occupancy mode (does not start Compose).

    Args:
        args: ``mode`` (required), optional ``yes``.

    Returns:
        Occupancy-enter payload or error.
    """
    mode = str(args.get("mode") or "")
    yes = bool(args.get("yes") or False)
    if not mode:
        return {
            "ok": False,
            "error": (
                "occupancy_enter needs a mode: one of idle, blender-desk, "
                "klein, trellis, wan, or ltx (blender-desk for a bpy or dump "
                "tool). occupancy_status shows the mode the host holds now."
            ),
        }
    return _run_occupancy_enter(mode, yes)


def tool_scene_info(args: ToolArgs) -> ToolResult:
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


def tool_create_primitive(args: ToolArgs) -> ToolResult:
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
        return {
            "ok": False,
            "error": (
                f"create_primitive cannot add kind {kind!r}; it takes one of "
                f"{', '.join(sorted(allowed))}. scene_info lists what the "
                "scene already holds if you were checking for a clash."
            ),
        }
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


def tool_set_camera(args: ToolArgs) -> ToolResult:
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


def tool_keyframe_object(args: ToolArgs) -> ToolResult:
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
    frame = int(cast(ToolNumber, args.get("frame") or 1))
    if not name:
        return {
            "ok": False,
            "error": (
                "keyframe_object needs the name of an object that is already "
                "in the scene; pass it exactly as scene_info lists it (Blender "
                "names such as Cube or Camera)."
            ),
        }
    script = (
        "import bpy; "
        f"obj = bpy.data.objects.get({name!r}); "
        "assert obj is not None; "
        f"obj.keyframe_insert(data_path='location', frame={frame}); "
        "print('ok')"
    )
    return _run_blender(script)


def tool_export_glb(args: ToolArgs) -> ToolResult:
    """MCP tool: export GLB under COMFY_OUTPUT_DIR/assets.

    Args:
        args: Optional ``path``.

    Returns:
        Blender run payload (includes ``path``) or error.
    """
    blocked = _require_desk()
    if blocked:
        return blocked
    default = str(_output_dir() / "assets" / "objects" / "mcp-export.glb")
    dest_s = str(args.get("path") or default)
    if "models" in Path(dest_s).parts and "assets" not in Path(dest_s).parts:
        return {
            "ok": False,
            "error": (
                f"export_glb refused {dest_s!r}: a path under a models "
                "directory would drop a dump into MODELS_DIR, which holds "
                f"shipped weights only. Write under the assets folder instead, "
                f"for example {default}."
            ),
        }
    script = (
        "import bpy; "
        f"bpy.ops.export_scene.gltf(filepath={dest_s!r}, export_format='GLB'); "
        f"print({dest_s!r})"
    )
    result = _run_blender(script)
    result["path"] = dest_s
    return result


def _run_utility(script_name: str, extra: list[str]) -> BlenderRunResult:
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


def tool_export_guides(args: ToolArgs) -> ToolResult:
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


def tool_blender_stills(args: ToolArgs) -> ToolResult:
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


def tool_house_views(args: ToolArgs) -> ToolResult:
    """MCP tool: dump Instagram 4:5 greybox stills + GLB.

    Args:
        args: Optional ``slug``.

    Returns:
        house-views.sh payload.
    """
    slug = str(args.get("slug") or "lab-penthouse")
    return _run_utility("house-views.sh", ["--slug", slug])


# Shared argument docs: the same value means the same thing in every tool.
_BLEND_DOC = (
    "Path to a host .blend file opened before the run, for example "
    "/home/me/blender/go-see.blend. Omit it to use Blender's default startup "
    "scene. The file is read from the host filesystem, not from inside the "
    "Comfy image."
)
"""Doc for the optional ``blend`` argument the bpy and dump tools share."""

_FILM_DOC = (
    "Film slug the pack is filed under, for example go-see; it becomes the "
    "<film> segment of the dump folder under COMFY_OUTPUT_DIR/guides. Pass "
    "the slug the studio-ui film board already shows for the film rather than "
    "inventing a new one."
)
"""Doc for the ``film`` argument both host dump tools share."""

# Typed MCP tool table (names are the public tool ids).
TOOLS: dict[str, ToolSpec] = {
    "occupancy_status": {
        "description": (
            "Read GB10 occupancy mode, parked flag, and PIDs, so a caller can "
            "tell whether the Blender desk is free. "
            "Returns: {ok, occupancy}, where occupancy is the host record "
            "read from COMFY_OUTPUT_DIR/.occupancy.json, or the host occupancy "
            "helper when that file is missing or unreadable: mode (idle, "
            "blender-desk, klein, trellis, wan, or ltx), compose, parked, and "
            "the blender/mcp/llm pids. An all-idle record comes back when the "
            "host has never recorded a mode."
        ),
        "inputSchema": {"type": "object", "properties": {}},
        "handler": tool_occupancy_status,
    },
    "occupancy_enter": {
        "description": (
            "Enter an occupancy mode so host Blender can take the GPU. Does "
            "not start Compose. "
            "Returns: {ok, returncode, stderr, mode} from the host occupancy "
            "helper, with ok false and the helper's own stderr when the mode "
            "was refused, or {ok: false, error} that repeats the accepted "
            "modes and points at occupancy_status when mode came in empty."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "description": (
                        "Exact occupancy mode to claim: idle, blender-desk, "
                        "klein, trellis, wan, or ltx. blender-desk is the one "
                        "a bpy or dump tool needs, because it parks Comfy "
                        "without stopping Compose. occupancy_status shows the "
                        "mode the host holds right now."
                    ),
                },
                "yes": {
                    "type": "boolean",
                    "description": (
                        "True passes --yes so the host helper skips its "
                        "interactive confirm, which a stdio agent cannot "
                        "answer; false, the default, lets the helper prompt "
                        "and wait for a keyboard."
                    ),
                },
            },
            "required": ["mode"],
        },
        "handler": tool_occupancy_enter,
    },
    "scene_info": {
        "description": (
            "List object names in the current Blender scene. Run it before "
            "any tool that has to name an object. "
            "Returns: {ok, returncode, stdout, stderr} where stdout is the "
            'JSON line {"objects": ["Cube", "Camera"]}, or '
            "{ok: false, error} naming the command that takes the desk while "
            "Comfy holds the GPU and naming blender-install when the host has "
            "no blender binary."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"blend": {"type": "string", "description": _BLEND_DOC}},
        },
        "handler": tool_scene_info,
    },
    "create_primitive": {
        "description": (
            "Add a Workbench primitive to the scene. "
            "Returns: {ok, returncode, stdout, stderr, name, kind} naming what "
            "it added, or {ok: false, error} that repeats the kind it rejected "
            "and lists the kinds it takes, or names the command that takes the "
            "desk while Comfy holds the GPU."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "kind": {
                    "type": "string",
                    "description": (
                        "Which primitive to add, exactly one of cube, "
                        "uv_sphere, cylinder, plane, or cone; cube when "
                        "omitted. Anything else is refused with that list "
                        "repeated. scene_info shows what the scene already "
                        "holds before you add to it."
                    ),
                },
                "name": {
                    "type": "string",
                    "description": (
                        "Name given to the new object, any text such as Mug; "
                        "the kind is used when you omit it. scene_info lists "
                        "the names already taken, and keyframe_object is the "
                        "tool that must match one of them exactly."
                    ),
                },
            },
        },
        "handler": tool_create_primitive,
    },
    "set_camera": {
        "description": (
            "Move the scene Camera to [x, y, z], creating it when the scene "
            "has none. "
            "Returns: {ok, returncode, stdout, stderr} with stdout naming the "
            "camera object, or {ok: false, error} naming the command that "
            "takes the desk while Comfy holds the GPU. A location that is not "
            "three numbers is replaced by the default rather than raising."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": (
                        "Three numbers [x, y, z] in Blender metres, for "
                        "example [0, -8, 2] for a front three-quarter shot. "
                        "Shorter than three numbers, or not a list at all, is "
                        "silently replaced by that same default, so a typo "
                        "moves the camera instead of failing."
                    ),
                }
            },
        },
        "handler": tool_set_camera,
    },
    "keyframe_object": {
        "description": (
            "Insert a location keyframe on a named object at one frame. "
            "Returns: {ok, returncode, stdout, stderr} with stdout ok when the "
            "key landed; an object the scene does not have makes the Blender "
            "run fail with its traceback in stderr, and the call is refused "
            "with {ok: false, error} before it runs when name is empty or "
            "Comfy holds the GPU."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": (
                        "Exact name of an object already in the scene, "
                        "matched against Blender's own object names such as "
                        "Cube or Camera. scene_info lists the names that "
                        "exist; an unknown name fails the run."
                    ),
                },
                "frame": {
                    "type": "integer",
                    "description": (
                        "Whole-number timeline frame to key, for example 1 or "
                        "120; frame 1 when omitted. It keys the object's "
                        "location only, so move it first with set_camera."
                    ),
                },
            },
            "required": ["name"],
        },
        "handler": tool_keyframe_object,
    },
    "export_glb": {
        "description": (
            "Export the scene as a GLB under COMFY_OUTPUT_DIR/assets (never "
            "MODELS_DIR). "
            "Returns: {ok, returncode, stdout, stderr, path} with path the "
            "file it wrote, or {ok: false, error} that repeats the refused "
            "path when it points into a models directory and names the assets "
            "folder to use instead, or names the command that takes the desk."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "Absolute host path the GLB is written to, under "
                        "COMFY_OUTPUT_DIR/assets, for example "
                        "/mnt/comfy-output/assets/objects/mug.glb; that "
                        "default mcp-export.glb file is used when you omit "
                        "it. A path under a models directory is refused: "
                        "MODELS_DIR holds shipped weights only."
                    ),
                }
            },
        },
        "handler": tool_export_glb,
    },
    "export_guides": {
        "description": (
            "Dump a 5.00s clay/depth/canny guide pack for one shot (host "
            "blender-guide.sh). "
            "Returns: {ok, returncode, stdout, stderr} from the host utility, "
            "stderr carrying its own log line naming the folder it wrote under "
            "COMFY_OUTPUT_DIR/guides/<film>/<shot>, or {ok: false, error} "
            "naming the command that takes the desk while Comfy holds the GPU."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "film": {"type": "string", "description": _FILM_DOC},
                "shot": {
                    "type": "string",
                    "description": (
                        "Shot id used as the guide folder name, digits only, "
                        "such as 12 or 07; the host utility zero-pads it to "
                        "two digits for the last segment of "
                        "COMFY_OUTPUT_DIR/guides/<film>/<shot>. Anything with "
                        "a letter in it fails the run with 'shot id must be "
                        "numeric'."
                    ),
                },
                "blend": {"type": "string", "description": _BLEND_DOC},
            },
        },
        "handler": tool_export_guides,
    },
    "blender_stills": {
        "description": (
            "Dump a creator still pack: one frame of clay, depth, and canny "
            "(host blender-stills.sh). "
            "Returns: {ok, returncode, stdout, stderr} from the host utility, "
            "stderr carrying its own log line naming the folder it wrote under "
            "COMFY_OUTPUT_DIR/guides/<film>/stills/<plate>, or "
            "{ok: false, error} naming the command that takes the desk while "
            "Comfy holds the GPU."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "film": {"type": "string", "description": _FILM_DOC},
                "plate": {
                    "type": "string",
                    "description": (
                        "Plate name the still pack is filed under, for example "
                        "mug; it becomes the last segment of "
                        "COMFY_OUTPUT_DIR/guides/<film>/stills/<plate> and "
                        "should match the plate the .blend scene actually "
                        "renders, so the dump is not overwritten blind."
                    ),
                },
                "size": {
                    "type": "string",
                    "description": (
                        "Frame size written as WxH, for example 1024x1024. The "
                        "host utility accepts 1280x704, 768x1280, 1024x1280, "
                        "1024x1024, and 1280x720 (a thumb size, not an LTX "
                        "size); omit it for the utility default."
                    ),
                },
                "blend": {"type": "string", "description": _BLEND_DOC},
            },
        },
        "handler": tool_blender_stills,
    },
    "house_views": {
        "description": (
            "Dump Instagram 4:5 greybox stills plus a GLB of a house scene "
            "(host house-views.sh). "
            "Returns: {ok, returncode, stdout, stderr} from the host utility, "
            "stderr carrying its own log line naming the folder it wrote under "
            "COMFY_OUTPUT_DIR/assets/sets/<slug>, or {ok: false, error} naming "
            "the command that takes the desk while Comfy holds the GPU."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "slug": {
                    "type": "string",
                    "description": (
                        "House scene slug, the folder name the stills and the "
                        "GLB are written under, for example lab-penthouse (the "
                        "default). Pass the slug the scene ships under rather "
                        "than a title typed by an operator, or the utility "
                        "dumps a folder of that name and finds nothing to "
                        "render."
                    ),
                }
            },
        },
        "handler": tool_house_views,
    },
}


def list_tools() -> list[ToolCatalogEntry]:
    """List MCP tools without handlers.

    Returns:
        ``{name, description, inputSchema}`` rows.
    """
    return _runtime_list_tools(TOOLS)


def call_tool(name: str, arguments: ToolArgs | None = None) -> ToolResult:
    """Dispatch a named MCP tool.

    Args:
        name: Tool id.
        arguments: JSON-object arguments (JSON boundary).

    Returns:
        Tool payload (``ok`` false on unknown tool).
    """
    return _runtime_call_tool(TOOLS, name, arguments)


def handle_rpc(message: JsonRpcRequest) -> JsonRpcResponse | None:
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
        usage_extra=("Occupancy-aware Blender MCP. No execute_code. No telemetry."),
        handle=handle_rpc,
    )


if __name__ == "__main__":
    raise SystemExit(main())
