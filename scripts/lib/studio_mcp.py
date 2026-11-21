#!/usr/bin/env python3
"""Occupancy-aware studio MCP (stdlib JSON-RPC).

Typed tools: occupancy, lab-template discovery, clone/stamp/save into _user/.
No execute_code, no telemetry, no Queue, no Comfy Cloud.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from mcp_runtime import (
    JsonRpcRequest,
    JsonRpcResponse,
    ToolArgs,
    ToolCatalogEntry,
    ToolResult,
    ToolSpec,
    call_tool as _runtime_call_tool,
    handle_rpc as _runtime_handle_rpc,
    list_tools as _runtime_list_tools,
    main_cli,
    serve_stdio as _runtime_serve_stdio,
)

if TYPE_CHECKING:
    from ez_common import Json, JsonObject

# MCP protocol identity (JSON-RPC initialize.serverInfo).
PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "ez-studio"
SERVER_VERSION = "1"


def _repo_root() -> Path:
    """Return the repository root (parent of ``scripts/``).

    Returns:
        Absolute repo path.
    """
    return Path(__file__).resolve().parents[2]


def _ensure_custom_nodes_path() -> None:
    """Prepend ``custom_nodes/`` so ez_studio_forge imports resolve."""
    custom = str(_repo_root() / "custom_nodes")
    if custom not in sys.path:
        sys.path.insert(0, custom)


_ensure_custom_nodes_path()


def _output_dir() -> Path:
    """Return COMFY_OUTPUT_DIR (host occupancy root).

    Returns:
        Output directory path.
    """
    return Path(os.environ.get("COMFY_OUTPUT_DIR", "/mnt/comfy-output"))


def occupancy_status() -> JsonObject:
    """Read occupancy JSON from COMFY_OUTPUT_DIR.

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
    return {
        "version": 1,
        "mode": "idle",
        "compose": False,
        "parked": False,
        "blender_pid": 0,
        "mcp_pid": 0,
        "llm_pid": 0,
    }


def tool_occupancy_status(_args: ToolArgs) -> ToolResult:
    """MCP tool: read occupancy JSON.

    Args:
        _args: Unused tool arguments.

    Returns:
        ``{ok, occupancy}``.
    """
    return {"ok": True, "occupancy": occupancy_status()}


def tool_search_templates(args: ToolArgs) -> ToolResult:
    """MCP tool: search shipped lab Apps and studio-block ids.

    Args:
        args: Optional ``query``/``q``, ``occupancy``, ``lane``.

    Returns:
        ``{ok, templates, count}``.
    """
    from ez_studio_forge.pipeline import list_templates

    rows = list_templates(
        query=str(args.get("query") or args.get("q") or ""),
        occupancy=str(args.get("occupancy") or ""),
        lane=str(args.get("lane") or ""),
    )
    return {"ok": True, "templates": rows, "count": len(rows)}


def tool_get_template(args: ToolArgs) -> ToolResult:
    """MCP tool: describe one lab App or studio-block.

    Args:
        args: ``stem``, ``id``, or ``template``.

    Returns:
        Template description payload, or an ``ok`` false error that names
        ``search_templates`` as the tool that lists the real ids.
    """
    from ez_studio_forge.pipeline import describe_template

    stem = str(args.get("stem") or args.get("id") or args.get("template") or "")
    payload = describe_template(stem)
    if not payload.get("ok"):
        detail = payload.get("error") or f"unknown template {stem!r}"
        return {
            "ok": False,
            "error": (
                f"{detail}. Pass stem as a lab App id such as "
                "photos/still-draft or a studio-block id such as "
                "klein-t2i-backbone; search_templates lists every id this "
                "stack ships."
            ),
        }
    return payload


def tool_describe_app(args: ToolArgs) -> ToolResult:
    """MCP tool: alias of get_template for lab Apps.

    Args:
        args: ``stem`` (required by schema).

    Returns:
        Template description payload.
    """
    return tool_get_template(args)


def tool_apply_slots(args: ToolArgs) -> ToolResult:
    """MCP tool: clone a lab graph and patch named slots (no disk write).

    Args:
        args: ``stem`` (required), optional ``slots`` object.

    Returns:
        Cloned graph payload or error.
    """
    from ez_studio_forge.pipeline import ForgeError, apply_slots, clone_template

    stem = str(args.get("stem") or args.get("template") or "")
    slots = args.get("slots") or {}
    if not isinstance(slots, dict):
        return {
            "ok": False,
            "error": (
                "slots must be a JSON object keyed by widget name or App Mode "
                f"label, for example {SLOT_EXAMPLE}; got "
                f"{type(slots).__name__} instead. Call get_template for "
                f"{stem!r} first to read the widget names that stem exposes."
            ),
        }
    try:
        origin, graph = clone_template(stem)
        apply_slots(graph, slots)
    except ForgeError as exc:
        return {
            "ok": False,
            "error": (
                f"apply_slots could not patch {stem!r}: {exc}. Run "
                "search_templates to list the lab App ids this stack ships, "
                "then get_template to read the slot names one id exposes."
            ),
        }
    extra = graph.get("extra") or {}
    return {
        "ok": True,
        "template": origin,
        "graph": graph,
        "widgets": list((extra.get("linearData") or {}).get("inputs") or [])
        if isinstance(extra, dict)
        else [],
    }


def tool_validate_workflow(args: ToolArgs) -> ToolResult:
    """MCP tool: check banned strings, Vue-corrected renderer, linear ids.

    Args:
        args: Optional ``stem``, ``graph``, ``slug``.

    Returns:
        ``{ok, errors}``.
    """
    from ez_studio_forge.pipeline import clone_template, validate_workflow

    stem = str(args.get("stem") or args.get("template") or "")
    graph = args.get("graph")
    if not isinstance(graph, dict):
        if not stem:
            return {
                "ok": False,
                "error": (
                    "pass either graph (a serialized Comfy graph object) or "
                    "stem (a lab App id such as photos/still-draft); "
                    "search_templates lists the ids this stack ships."
                ),
            }
        try:
            _origin, graph = clone_template(stem)
        except Exception as exc:  # noqa: BLE001
            return {
                "ok": False,
                "error": (
                    f"validate_workflow could not load {stem!r} to check it: "
                    f"{exc}. Run search_templates to list the lab App ids this "
                    "stack ships, or pass graph yourself."
                ),
            }
    errors = validate_workflow(
        graph,
        slug=str(args.get("slug") or ""),
    )
    return {"ok": not errors, "errors": errors}


def _save_from_args(args: ToolArgs, *, force_app: bool | None) -> ToolResult:
    """Clone, stamp, and write a lab graph into live ``_user/``.

    Args:
        args: ``stem``/``template``, ``slug``, optional slots/overwrite/as_app.
        force_app: True forces App view; False forces workflow; None uses args.

    Returns:
        Save payload or ForgeError mapping.
    """
    from ez_studio_forge.pipeline import (
        ForgeError,
        apply_slots,
        clone_template,
        restamp_identity,
        save_workflow,
        slugify,
        validate_slug,
    )

    stem = str(args.get("stem") or args.get("template") or "")
    slug = str(args.get("slug") or "")
    raw_slots = args.get("slots")
    slots = raw_slots if isinstance(raw_slots, dict) else {}
    overwrite = bool(args.get("overwrite") or False)
    try:
        origin, graph = clone_template(stem)
        if slots:
            apply_slots(graph, slots)
        clean = validate_slug(slug or slugify(origin.replace("/", "-")))
        restamp_identity(graph, origin=origin, slug=clean)
        if force_app is True:
            mode = graph.setdefault("extra", {}).setdefault("lab_app_mode", {})
            if isinstance(mode, dict):
                mode["default_view"] = "app"
                mode["enabled"] = True
            graph["extra"]["linearMode"] = True
            as_app = True
        elif force_app is False:
            as_app = False
        else:
            as_app = bool(args.get("as_app", True))
        dest = save_workflow(graph, slug=clean, as_app=as_app, overwrite=overwrite)
    except ForgeError as exc:
        slug_note = f" as {slug!r}" if slug else ""
        return {
            "ok": False,
            "error": (
                f"save_workflow/create_app could not write {stem!r}"
                f"{slug_note}: {exc}. Run search_templates for a lab App id "
                "that exists, get_template for the slot names it exposes, and "
                "pass slug as lowercase letters, digits, and hyphens such as "
                "mcp-mug. Set overwrite true to replace a file you saved."
            ),
        }
    return {
        "ok": True,
        "path": str(dest),
        "template": origin,
        "slug": clean,
        "as_app": as_app,
    }


def tool_save_workflow(args: ToolArgs) -> ToolResult:
    """MCP tool: clone a lab graph into live ``_user/`` (never writes ``_lab``).

    Args:
        args: ``stem`` and ``slug`` (required), optional as_app/overwrite/slots.

    Returns:
        Save payload or error.
    """
    return _save_from_args(args, force_app=None)


def tool_create_app(args: ToolArgs) -> ToolResult:
    """MCP tool: clone a lab graph into live ``_user/`` as an App.

    Args:
        args: ``stem`` and ``slug`` (required), optional overwrite/slots.

    Returns:
        Save payload or error.
    """
    return _save_from_args(args, force_app=True)


def tool_generate_app(args: ToolArgs) -> ToolResult:
    """MCP tool: pick a lab template from a brief and write ``_user/``.

    Args:
        args: ``brief`` (required), optional template/slug/as_app/overwrite/slots.

    Returns:
        Generate payload (may include ``error``).
    """
    from ez_studio_forge.pipeline import generate_app

    brief = str(args.get("brief") or args.get("prompt") or args.get("message") or "")
    template = str(args.get("template") or "auto")
    slug = str(args.get("slug") or "")
    as_app = args.get("as_app")
    overwrite = bool(args.get("overwrite") or False)
    raw_slots = args.get("slots")
    slots = raw_slots if isinstance(raw_slots, dict) else None
    result = generate_app(
        brief,
        template=template,
        slug=slug,
        as_app=as_app,
        overwrite=overwrite,
        slots=slots,
    )
    payload: dict[str, object] = {
        "ok": result.ok,
        "path": result.path,
        "template": result.template,
        "occupancy": result.occupancy,
        "widgets": result.widgets,
        "slug": result.slug,
        "as_app": result.as_app,
        "reason": result.reason,
        "status": result.status,
    }
    if result.error:
        payload["error"] = result.error
    return payload


# Shared argument docs: the same value means the same thing in every tool.
SLOT_EXAMPLE = '{"prompt": "a chipped cobalt mug on a linen cloth", "seed": 7}'

_STEM_DOC = (
    "Lab App id relative to workflows/_lab, written <lane>/<name> with no "
    ".json suffix, for example photos/still-draft or "
    "labs/assist/prompt-forge. A unique bare file stem such as still-draft "
    "resolves too. Run search_templates for the ids this stack ships."
)
_TEMPLATE_STEM_DOC = (
    "Lab App id relative to workflows/_lab, written <lane>/<name> with no "
    ".json suffix, for example photos/still-draft; or a studio-block "
    "blueprint id such as klein-t2i-backbone. Run search_templates for the "
    "ids this stack ships."
)
_SLOTS_DOC = (
    "JSON object of widget values to patch, keyed by widget name or by its "
    f"App Mode label, for example {SLOT_EXAMPLE}. get_template lists the "
    "widget names a stem exposes; a key that matches no widget errors the "
    "call rather than being dropped."
)
_SLUG_DOC = (
    "Filesystem stem for the file written into live workflows/_user: letters, "
    "digits, and hyphens, starting with a letter or digit, at most 48 "
    "characters, written lowercase such as mcp-mug. No slashes and no '..'. "
    "An App lands as _user/<slug>.app.json, a graph as _user/<slug>.json. "
    "Leave it empty to derive one from the template name."
)
_AS_APP_DOC = (
    "True, the default, writes an App (_user/<slug>.app.json) so Comfy's Apps "
    "sidebar lists it and App Mode renders the widgets as a form; false "
    "writes a plain graph (_user/<slug>.json) that opens in graph view."
)
_OVERWRITE_DOC = (
    "True replaces the _user file already saved under this slug, or its "
    ".json/.app.json sibling; false, the default, refuses instead of "
    "overwriting what the operator saved."
)

# Typed MCP tool table (names are the public tool ids).
TOOLS: dict[str, ToolSpec] = {
    "occupancy_status": {
        "description": (
            "Read GB10 occupancy mode, parked flag, and PIDs. "
            "Returns: {ok, occupancy}, where occupancy is the host record: "
            "mode (idle, klein, wan, ltx, trellis, blender-desk, or "
            "llm-desk), compose, parked, and the blender/mcp/llm pids. An "
            "all-idle record is returned when no state file exists yet."
        ),
        "inputSchema": {"type": "object", "properties": {}},
        "handler": tool_occupancy_status,
    },
    "search_templates": {
        "description": (
            "Search shipped lab Apps and studio-block ids "
            "(id, occupancy, widgets, kind). This is the listing tool: run it "
            "before any tool that takes a stem. "
            "Returns: {ok, templates, count}; each template row carries id, "
            "kind (lab or block), lane, occupancy, handoff, description, "
            "widgets, and default_view (app or graph)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Case-insensitive substring matched against a lab "
                        "row's id, lane, occupancy, and description; a "
                        "studio-block row matches on its id alone. Example: "
                        "still, or klein-t2i. Omit it to list everything."
                    ),
                },
                "occupancy": {
                    "type": "string",
                    "description": (
                        "Exact occupancy class a lab App declares: klein "
                        "(stills), wan (silent motion), ltx (audio/video), "
                        "audio, trellis (3d), llm, or none. Example: klein. "
                        "Blocks declare none of these, so any value here "
                        "filters every block row out."
                    ),
                },
                "lane": {
                    "type": "string",
                    "description": (
                        "Exact lane, the first segment of a lab id: photos, "
                        "film, video, audio, social, business, 3d, guides, or "
                        "labs. Example: photos keeps photos/still-draft and "
                        "drops labs/assist/prompt-forge."
                    ),
                },
            },
        },
        "handler": tool_search_templates,
    },
    "get_template": {
        "description": (
            "Describe one lab App or studio-block: occupancy, widgets, "
            "handoff. "
            "Returns: {ok, id, kind, path, description, lab_note, occupancy, "
            "lane, handoff, widgets, lab_mcp, default_view} for that id, or "
            "{ok: false, error} pointing at search_templates when nothing "
            "matches."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "stem": {
                    "type": "string",
                    "description": _TEMPLATE_STEM_DOC,
                },
            },
            "required": ["stem"],
        },
        "handler": tool_get_template,
    },
    "describe_app": {
        "description": (
            "Alias of get_template for lab Apps. Use get_template when the id "
            "might be a studio-block blueprint; use this one when the id is "
            "already a lab App such as photos/still-draft, or when a lab "
            "graph's lab_mcp block names this tool. "
            "Returns: the same payload as get_template, or "
            "{ok: false, error} pointing at search_templates."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "stem": {
                    "type": "string",
                    "description": _STEM_DOC,
                },
            },
            "required": ["stem"],
        },
        "handler": tool_describe_app,
    },
    "apply_slots": {
        "description": (
            "Clone a lab graph and patch widgets_values for named slots. "
            "Does not write disk. "
            "Returns: {ok, template, graph, widgets} with the patched graph "
            "ready for validate_workflow, or {ok: false, error} that says what "
            "to pass and points at search_templates and get_template."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "stem": {"type": "string", "description": _STEM_DOC},
                "slots": {"type": "object", "description": _SLOTS_DOC},
            },
            "required": ["stem"],
        },
        "handler": tool_apply_slots,
    },
    "validate_workflow": {
        "description": (
            "Check banned strings, Vue-corrected renderer, integer linear ids. "
            "Run it on the graph apply_slots returned, before saving. "
            "Returns: {ok, errors} where errors lists the operator-fixable "
            "problems (empty when ok), or {ok: false, error} that says what to "
            "pass when neither graph nor a loadable stem came in."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "stem": {
                    "type": "string",
                    "description": (
                        _STEM_DOC
                        + " Cloned from the lab and then checked when graph is "
                        "left out."
                    ),
                },
                "graph": {
                    "type": "object",
                    "description": (
                        "A serialized Comfy (litegraph) graph, checked exactly "
                        "as passed: the top-level object holding nodes, links, "
                        "groups, and extra, for example "
                        '{"nodes": [], "links": null, "extra": '
                        '{"workflowRendererVersion": "Vue-corrected"}}. Pass '
                        "the graph apply_slots returned, or leave it out and "
                        "give stem."
                    ),
                },
                "slug": {
                    "type": "string",
                    "description": (
                        _SLUG_DOC + " Only its legality is checked here; "
                        "nothing is written."
                    ),
                },
            },
        },
        "handler": tool_validate_workflow,
    },
    "save_workflow": {
        "description": (
            "Clone a lab graph into live _user/. Never writes _lab. No Queue. "
            "Returns: {ok, path, template, slug, as_app} once the file is "
            "written, or {ok: false, error} that names search_templates, "
            "get_template, and the slug shape when the clone, a slot, or the "
            "save was refused."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "stem": {"type": "string", "description": _STEM_DOC},
                "slug": {"type": "string", "description": _SLUG_DOC},
                "as_app": {"type": "boolean", "description": _AS_APP_DOC},
                "overwrite": {"type": "boolean", "description": _OVERWRITE_DOC},
                "slots": {"type": "object", "description": _SLOTS_DOC},
            },
            "required": ["stem", "slug"],
        },
        "handler": tool_save_workflow,
    },
    "create_app": {
        "description": (
            "Clone a lab graph into live _user/ as an App (*.app.json). "
            "Returns: {ok, path, template, slug, as_app} with as_app always "
            "true, or {ok: false, error} that names search_templates, "
            "get_template, and the slug shape."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "stem": {"type": "string", "description": _STEM_DOC},
                "slug": {"type": "string", "description": _SLUG_DOC},
                "overwrite": {"type": "boolean", "description": _OVERWRITE_DOC},
                "slots": {"type": "object", "description": _SLOTS_DOC},
            },
            "required": ["stem", "slug"],
        },
        "handler": tool_create_app,
    },
    "generate_app": {
        "description": (
            "Pick a lab template from a brief, clone, stamp, write _user/. "
            "CPU GGUF or keyword heuristic. Does not Queue Comfy. "
            "Returns: {ok, path, template, occupancy, widgets, slug, as_app, "
            "reason, status}, plus error on an ok false refusal saying what "
            "failed (run search_templates for ids that exist)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "brief": {
                    "type": "string",
                    "description": (
                        "What the operator wants, in plain words: subject, "
                        "look, motion, sound. Example: a chipped cobalt mug on "
                        "linen, one soft key light, slow push-in. prompt and "
                        "message are accepted as synonyms."
                    ),
                },
                "template": {
                    "type": "string",
                    "description": (
                        "Lab App id to clone, or auto (the default) to let the "
                        "planner pick from the brief. Same shape as stem: "
                        "<lane>/<name> such as photos/still-draft, taken from "
                        "search_templates."
                    ),
                },
                "slug": {
                    "type": "string",
                    "description": (
                        _SLUG_DOC + " Leave it empty and the planner, or the "
                        "brief itself, picks one."
                    ),
                },
                "as_app": {
                    "type": "boolean",
                    "description": (
                        _AS_APP_DOC + " Omit it and the chosen graph's "
                        "default_view decides."
                    ),
                },
                "overwrite": {"type": "boolean", "description": _OVERWRITE_DOC},
                "slots": {
                    "type": "object",
                    "description": (
                        _SLOTS_DOC + " Merged on top of the slots the planner "
                        "already chose from the brief."
                    ),
                },
            },
            "required": ["brief"],
        },
        "handler": tool_generate_app,
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
        prog="studio_mcp.py",
        usage_extra=(
            "Occupancy-aware studio MCP. No execute_code. No telemetry. No Queue."
        ),
        handle=handle_rpc,
    )


if __name__ == "__main__":
    raise SystemExit(main())
