"""Shared records, op vocabulary, and tool catalog for the editing lane.

This module is the pinned seam for the whole lane: the in-container agent
(``agent.py``), the PromptServer routes (``routes.py``), the browser panel
(``js/ez_edit_panel.js``), and the host MCP server
(``scripts/lib/edit_mcp.py``) all speak these shapes and nothing wider.

Keep it declarative: TypedDicts for JSON records, ``Literal`` vocabularies,
constants, and the tool catalog. Behavioral seams live in
``ez_common.protocols`` (Protocol), not here. No functions, no I/O, stdlib
only - pack import stays hermetic for pytest.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

# --- Storage layout (all under ${COMFY_OUTPUT_DIR}) -------------------------

EDIT_DIR_NAME = "edit"
"""Directory under the Comfy output root that holds every edit artifact."""

PROJECTS_SUBDIR = "projects"
"""Subdirectory for ``projects/<project_id>.json`` (one file per project)."""

JOBS_SUBDIR = "jobs"
"""Subdirectory for ``jobs/<job_id>.json`` (jobstore rows)."""

CLIENTS_SUBDIR = "clients"
"""Subdirectory for ``clients/<client_id>/`` browser exec queues."""

OUTPUTS_SUBDIR = "renders"
"""Subdirectory for rendered files (server mp4, client webm)."""

# --- Environment keys -------------------------------------------------------

ENV_ENABLED = "EZ_EDIT_ENABLED"
"""``0`` hides the panel and refuses routes (default on)."""

ENV_LLM_URL = "EZ_AGENT_LLM_URL"
"""OpenAI-compatible base, e.g. ``http://host.docker.internal:30001/v1``."""

ENV_MODEL = "EZ_AGENT_MODEL"
"""Model id served by the agent-model sidecar (default below)."""

ENV_TIMEOUT_S = "EZ_AGENT_TIMEOUT_S"
"""Per-completion HTTP timeout seconds (default below)."""

ENV_MAX_STEPS = "EZ_AGENT_MAX_STEPS"
"""Tool-loop step budget per user turn (default below)."""

ENV_COMFY_URL = "EZ_EDIT_COMFY_URL"
"""ComfyUI origin used for Queue (generate_clip) - loopback defaults."""

DEFAULT_LLM_URL_PORT = "30001"
"""Co-tenant port; 30000 stays owned by ``llm-sidecar.sh``."""

DEFAULT_MODEL = "Qwen3.8-Flash-Next"
"""API model id of the TensorFold recipe (authors' recipe, pinned by us)."""

DEFAULT_MAX_STEPS = 8
"""Max LLM round-trips per chat turn before the loop refuses."""

DEFAULT_TIMEOUT_S = 120.0
"""Default per-call timeout for the agent completion client."""

SIDECAR_OK_OCCUPANCY = frozenset(
    {"llm-desk", "llm", "idle", "unknown", "blender-desk", "none"}
)
"""Occupancy modes in which calling the agent LLM is allowed."""

# --- Vocabularies -----------------------------------------------------------

OpName = Literal[
    "project_create",
    "add_clip",
    "remove_clip",
    "trim_clip",
    "move_clip",
    "set_transition",
    "set_gain",
    "add_overlay",
    "remove_overlay",
    "add_caption",
    "remove_caption",
    "set_title",
    "clear",
]
"""The complete timeline mutation vocabulary (pure reducer ops only)."""

TransitionKind = Literal["cut", "fade", "wipe"]
"""Transition entering a clip; ``cut`` means no transition."""

OverlayKind = Literal["text", "image"]
"""Overlay primitive drawn above the video plane."""

JobKind = Literal["render_server", "exec_client", "generate_clip"]
"""Jobstore row kinds: server ffmpeg, browser WebCodecs, Comfy Queue."""

JobState = Literal["pending", "running", "ok", "failed"]
"""Jobstore lifecycle states (mirrors ez_film jobstore statuses)."""

ExecMode = Literal["server", "client"]
"""Where the render runs: ffmpeg on the Spark, WebCodecs in the browser."""

# --- JSON records -----------------------------------------------------------


class Transition(TypedDict):
    """Transition entering a clip."""

    kind: TransitionKind
    duration_s: float
    """Seconds of overlap for fade/wipe (0.0 for cut)."""


class Clip(TypedDict):
    """One source clip placed on a track."""

    id: str
    source: str
    """Path under ``${COMFY_OUTPUT_DIR}`` (never absolute-outside; checked)."""
    label: str
    in_s: float
    """Source in-point seconds."""
    out_s: float
    """Source out-point seconds (must exceed ``in_s``)."""
    track: int
    """Video track index (0 = base plane, higher = above)."""
    gain: float
    """Audio gain multiplier for this clip (1.0 = unchanged)."""
    transition: Transition | None
    """Transition entering this clip from the previous one, or None."""


class Overlay(TypedDict):
    """Text or image primitive composited above the video plane."""

    id: str
    kind: OverlayKind
    at_s: float
    """Timeline start seconds."""
    dur_s: float
    """Visible duration seconds."""
    text: str
    """Text content (empty when kind is ``image``)."""
    source: str
    """Image path under ``${COMFY_OUTPUT_DIR}`` (empty when kind is ``text``)."""
    x: float
    """Left position, 0..1 of frame width."""
    y: float
    """Top position, 0..1 of frame height."""
    size: float
    """Font height (text) or width (image), 0..1 of frame height/width."""


class Caption(TypedDict):
    """Burned-in subtitle line on the caption plane."""

    id: str
    at_s: float
    dur_s: float
    text: str


class EditProject(TypedDict):
    """One editing project; persisted as ``projects/<id>.json``."""

    id: str
    title: str
    fps: float
    width: int
    height: int
    clips: list[Clip]
    overlays: list[Overlay]
    captions: list[Caption]
    updated_at: str
    """ISO-8601 UTC stamp written by the reducer on every apply."""


class EditOp(TypedDict):
    """One reducer instruction: op name plus op-specific args."""

    op: OpName
    args: dict[str, Any]


class JobRecord(TypedDict):
    """Jobstore row (file ``jobs/<id>.json``, one JSON object)."""

    id: str
    kind: JobKind
    project_id: str
    state: JobState
    mode: ExecMode
    message: str
    """Human line: progress text or failure reason."""
    out_path: str
    """Rendered file path under ``${COMFY_OUTPUT_DIR}`` when done, else ````."""
    created_at: str
    updated_at: str
    client_id: str
    """Browser exec queue owner (``exec_client`` jobs; empty otherwise)."""


class LocalToolDef(TypedDict):
    """A tool discovered from a laptop-local MCP server (browser-side)."""

    server_id: str
    """Stable short id derived from the URL (host + port)."""
    server_url: str
    """Streamable-HTTP MCP endpoint, always laptop-loopback for the user."""
    name: str
    description: str
    input_schema: dict[str, Any]


class LocalCall(TypedDict):
    """One queued call the browser must execute against its local server."""

    call_id: str
    server_url: str
    name: str
    args: dict[str, Any]


class ChatMessage(TypedDict, total=False):
    """OpenAI chat message as kept in agent history (tool fields optional)."""

    role: str
    content: str
    tool_calls: list[dict[str, Any]]
    tool_call_id: str


class ToolCallTrace(TypedDict):
    """One agent-loop step surfaced to the panel and logs."""

    name: str
    args: dict[str, Any]
    ok: bool
    summary: str


# --- Tool catalog (single source for agent + host MCP) ----------------------

TOOL_CATALOG: dict[str, dict[str, Any]] = {
    "edit_get_state": {
        "description": "Return the current edit project (clips, overlays, "
        "captions) and its recent jobs. Pass project_id or empty for the "
        "most recently updated project.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "default": ""},
            },
        },
    },
    "edit_import": {
        "description": "Import a media file already under the Comfy output "
        "dir as a clip (probes duration with ffprobe). Returns the clip.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "label": {"type": "string", "default": ""},
                "track": {"type": "integer", "default": 0},
            },
            "required": ["path"],
        },
    },
    "edit_apply_ops": {
        "description": "Apply an ordered list of timeline ops to a project "
        "and return the new project. Ops: project_create, add_clip, "
        "remove_clip, trim_clip, move_clip, set_transition, set_gain, "
        "add_overlay, remove_overlay, add_caption, remove_caption, "
        "set_title, clear. Unknown ops and ids fail the whole call.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "default": ""},
                "ops": {"type": "array", "items": {"type": "object"}},
            },
            "required": ["ops"],
        },
    },
    "edit_render": {
        "description": "Render a project. mode=server runs ffmpeg on the "
        "Spark (mp4, CPU); mode=client queues the timeline for the open "
        "browser panel to render with WebCodecs (webm on the laptop). "
        "Returns the job id - poll edit_job_status.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "default": ""},
                "mode": {"type": "string", "enum": ["server", "client"]},
                "client_id": {"type": "string", "default": ""},
            },
            "required": ["mode"],
        },
    },
    "edit_job_status": {
        "description": "Return one jobstore row by id.",
        "parameters": {
            "type": "object",
            "properties": {"job_id": {"type": "string"}},
            "required": ["job_id"],
        },
    },
    "edit_generate_clip": {
        "description": "Queue the editing-lane generate-cutaway graph "
        "(silent motion) to create a new clip from a text prompt. Heavy "
        "GPU job - refused unless occupancy allows. Returns the job id.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "duration_s": {"type": "number", "default": 5.0},
                "fps": {"type": "number", "default": 24.0},
            },
            "required": ["prompt"],
        },
    },
    "edit_export_edl": {
        "description": "Write the project as an EDL JSON file under the "
        "edit dir (handoff for Kdenlive/Shotcut paths) and return its path.",
        "parameters": {
            "type": "object",
            "properties": {"project_id": {"type": "string", "default": ""}},
        },
    },
    "occupancy_status": {
        "description": "Return the current GPU occupancy mode string.",
        "parameters": {"type": "object", "properties": {}},
    },
}
"""Name -> {description, parameters}: JSON Schema for every static tool.

The agent passes these to ``/v1/chat/completions`` as ``tools`` entries and
the host MCP server wraps them into ``mcp_runtime.ToolSpec`` handlers.
Local (laptop) MCP tools are named ``local__<server_id>__<tool>`` and are
merged at call time, never stored here.
"""

LOCAL_TOOL_PREFIX = "local__"
"""Prefix for browser-relayed laptop-local MCP tools."""
