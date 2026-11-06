"""Queue the package generate-cutaway graph and land a ``generate_clip`` row.

The editing agent asks for a silent-motion cutaway through
``edit_generate_clip``. This module loads the pack-local graph
(``custom_nodes/ez_edit/graphs/generate-cutaway.json``), patches the prompt
text plus the length/frame-rate widgets, POSTs it to the ComfyUI queue, polls
``/history/<prompt_id>``, and records the whole attempt as one
:data:`~ez_edit.protocol.JobKind` ``generate_clip`` row in the lane jobstore.

Heavy GPU work is XOR with every other tenant, so the queue is refused unless
occupancy is idle, unknown (first run / pytest), or the llm-desk mode.

Sockets, sleeps, the clock, the graph file, and the occupancy read are all
injectable, so the pytest lane never opens a socket, never sleeps, and never
needs ComfyUI installed.

Note on graph shape: the shipped file is the ComfyUI *frontend* (litegraph)
serialisation - ``{"nodes": [...], "links": [...]}`` - because that is what
the lane's operator previews on the canvas. Widget writes are driven by its
``extra.lab_edit.widgets`` map (patch name -> node id + widget name, indexed
through :data:`WIDGET_SCHEMA`); the node ``title``/type heuristics answer only
for a graph that carries no such map. The graph is posted verbatim under the
``prompt`` key.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
import uuid
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Protocol, TypeAlias, cast

from . import agent, protocol, render_server
from .protocol import JobKind, JobRecord

if TYPE_CHECKING:
    from ez_common import Json

UrlopenFn: TypeAlias = Callable[[urllib.request.Request, float], object]
"""``urllib.request.urlopen``-shaped seam (tests inject a fake transport)."""


class HttpReply(Protocol):
    """One HTTP response the transport seam hands back."""

    def read(self) -> bytes | str:
        """Read the whole body.

        Returns:
            Response bytes or text.
        """
        ...

    def __enter__(self) -> "HttpReply":
        """Enter the response context.

        Returns:
            The readable response.
        """
        ...

    def __exit__(self, *args: object) -> bool | None:
        """Leave the response context.

        Args:
            *args: Exception detail the context manager receives.

        Returns:
            Whether an exception was swallowed.
        """
        ...

SleeperFn: TypeAlias = Callable[[float], None]
"""``time.sleep``-shaped seam (tests inject a no-op counter)."""

ClockFn: TypeAlias = Callable[[], str]
"""Clock seam returning an ISO-8601 stamp."""

OccupancyFn: TypeAlias = Callable[[], str]
"""Occupancy seam returning the current mode string."""

GENERATE_KIND: JobKind = "generate_clip"
"""Jobstore row kind for a queued cutaway generation."""

GRAPH_DIR_NAME = "graphs"
"""Pack subdirectory holding queueable graphs."""

GRAPH_FILE_NAME = "generate-cutaway.json"
"""Silent-motion cutaway graph the agent may queue."""

QUEUE_PATH = "/prompt"
"""ComfyUI queue endpoint."""

HISTORY_PATH_FMT = "/history/{prompt_id}"
"""ComfyUI history endpoint template."""

DEFAULT_COMFY_ORIGIN = "http://host.docker.internal"
"""In-container default origin (ComfyUI publishes on the host bridge)."""

DEFAULT_COMFY_PORT = "8188"
"""ComfyUI port used when ``COMFY_PORT`` is unset."""

ENV_COMFY_PORT = "COMFY_PORT"
"""Environment key for the ComfyUI port."""

QUEUE_TIMEOUT_S = 30.0
"""Socket timeout for the queue POST."""

HISTORY_TIMEOUT_S = 5.0
"""Socket timeout for one history poll."""

DEFAULT_POLL_S = 1.0
"""Seconds between history polls."""

DEFAULT_POLL_TIMEOUT_S = 600.0
"""Seconds to wait for the graph to land in history."""

HEAVY_OK_OCCUPANCY = frozenset({"idle", "unknown", "llm-desk"})
"""Modes in which a heavy generate_clip queue is allowed."""

OCCUPANCY_REFUSAL_FMT = (
    "occupancy is {mode}; generate_clip needs the GPU - release the heavy "
    "job (occupancy enter idle) before generating a cutaway"
)
"""Failed-row message when occupancy holds the Spark."""

GRAPH_MISSING_FMT = "generate-cutaway graph is missing at {path}"
"""Failed-row message when the package graph file is not on disk."""

GRAPH_INVALID_FMT = "generate-cutaway graph at {path} is not a graph object"
"""Failed-row message when the package graph file is unreadable JSON."""

NO_OUTPUT_MESSAGE = "generated cutaway {prompt_id} (no file reported by history)"
"""Ok-row message when history reports no artefact name."""

OUTPUT_MESSAGE = "generated cutaway {name}"
"""Ok-row message when history names the artefact."""

TIMEOUT_MESSAGE = "timed out waiting for prompt {prompt_id} in history"
"""Failed-row message when history never lists the prompt id."""

PROMPT_TITLES = ("prompt (cutaway)", "prompt", "positive")
"""Node titles (lower-cased) that carry the positive prompt text."""

NEGATIVE_HINTS = ("negative", "neg ")
"""Title fragments that mark a prompt node as the negative one."""

LENGTH_TITLES = ("video size & length", "size & length", "length")
"""Node titles (lower-cased) that carry the frame count."""

FPS_TITLES = ("save cutaway (mp4)", "save cutaway", "save video", "video combine")
"""Node titles (lower-cased) that carry the frame rate."""

PROMPT_TYPE_HINT = "cliptextencode"
"""Node-type fragment used when no prompt title matches."""

LATENT_TYPE_HINT = "latent"
"""Node-type fragment used when no length title matches."""

FRAMES_INDEX = 2
"""Widget index that holds ``length`` on the lane's latent-video nodes."""

LENGTH_WIDGET_KEYS = ("length", "frames", "num_frames")
"""Dict-widget keys that hold a frame count."""

FPS_WIDGET_KEYS = ("frame_rate", "fps", "video_frame_rate")
"""Dict-widget keys that hold a frame rate."""

MIN_FRAMES = 1
"""Smallest frame count the patch will write."""

LAB_EDIT_KEY = "lab_edit"
"""Graph ``extra`` section the lane generator stamps for the agent."""

WIDGETS_MAP_KEY = "widgets"
"""Patch-name -> ``{"node": id, "widget": name}`` map inside that section."""

MAP_PROMPT_KEY = "prompt"
"""Map key naming the widget that carries the live prompt text."""

MAP_LENGTH_KEY = "length"
"""Map key naming the widget that carries the frame count."""

MAP_FPS_KEY = "fps"
"""Map key naming the widget that carries the output frame rate."""

WIDGET_SCHEMA: dict[str, tuple[str, ...]] = {
    "EZWanPromptEnhance": (
        "sample",
        "prompt",
        "enhance",
        "mode",
        "duration_hint",
        "style",
        "catalog",
    ),
    "Wan22ImageToVideoLatent": ("width", "height", "length", "batch"),
    "VHS_VideoCombine": (
        "frame_rate",
        "loop_count",
        "filename_prefix",
        "format",
        "pix_fmt",
        "crf",
        "save_metadata",
        "trim_to_audio",
        "pingpong",
        "save_output",
    ),
}
"""Widget order per node type (each node's ``INPUT_TYPES`` key order), so a
patch-map reference can be written into a list widget by index."""


class GenerateClipError(RuntimeError):
    """The queue or history round-trip failed on the wire."""


class GraphUnavailable(RuntimeError):
    """The package graph file is missing or is not readable JSON."""


def comfy_base(environ: Mapping[str, str] | None = None) -> str:
    """Origin of the ComfyUI queue this module posts to.

    Args:
        environ: Injected environ; ``None`` reads ``os.environ``.

    Returns:
        ``EZ_EDIT_COMFY_URL`` when set (trailing slashes trimmed), else
        ``http://host.docker.internal:<COMFY_PORT>`` with port 8188 default.
    """
    env: Mapping[str, str] = _environ(environ)
    override = str(env.get(protocol.ENV_COMFY_URL) or "").strip().rstrip("/")
    if override:
        return override
    port = str(env.get(ENV_COMFY_PORT) or DEFAULT_COMFY_PORT).strip()
    return f"{DEFAULT_COMFY_ORIGIN}:{port or DEFAULT_COMFY_PORT}"


def _environ(environ: Mapping[str, str] | None) -> Mapping[str, str]:
    """Return the caller's environ or the process environment.

    Args:
        environ: Injected mapping (pytest), or ``None`` for ``os.environ``.

    Returns:
        Mapping used for every lookup in this module.
    """
    return os.environ if environ is None else environ


def graph_path() -> Path:
    """Path of the package generate-cutaway graph.

    Returns:
        ``<pack>/graphs/generate-cutaway.json`` (may not exist yet).
    """
    return Path(__file__).resolve().parent / GRAPH_DIR_NAME / GRAPH_FILE_NAME


def _stamp(now: ClockFn | None) -> str:
    """Current UTC ISO-8601 stamp, or the injected clock.

    Args:
        now: Clock callable, or ``None`` for the real clock.

    Returns:
        ISO-8601 UTC timestamp.
    """
    if now is not None:
        return now()
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _nodes(graph: Mapping[str, object]) -> list[dict[str, object]]:
    """Frontend-format node list of a graph, safe to patch in place.

    Widget containers are copied so a patch never mutates the caller's graph
    (the queue payload is rebuilt from the copy).

    Args:
        graph: Parsed graph object.

    Returns:
        The node dicts (empty when the graph carries none).
    """
    raw = graph.get("nodes")
    if not isinstance(raw, (list, tuple)):
        return []
    nodes: list[dict[str, object]] = []
    for node in raw:
        if not isinstance(node, dict):
            continue
        copy = dict(node)
        widgets = copy.get("widgets_values")
        if isinstance(widgets, (dict, list)):
            copy["widgets_values"] = type(widgets)(widgets)
        nodes.append(copy)
    return nodes


def _title(node: Mapping[str, object]) -> str:
    """Lower-cased title of a node (type as the fallback).

    Args:
        node: Frontend node dict.

    Returns:
        Title text, lower-cased; the node type when no title is set.
    """
    text = str(node.get("title") or node.get("type") or "").strip().lower()
    return text


def _is_negative(node: Mapping[str, object]) -> bool:
    """Whether a node title marks the negative prompt.

    Args:
        node: Frontend node dict.

    Returns:
        True when the title names a negative prompt.
    """
    title = _title(node)
    return any(hint in title for hint in NEGATIVE_HINTS)


def _find_prompt_node(nodes: list[dict[str, object]]) -> dict[str, object] | None:
    """Pick the node whose first widget carries the prompt text.

    Titles win (``Prompt (cutaway)`` in the shipped graph); otherwise the
    first non-negative ``CLIPTextEncode``-shaped node is used so a re-saved
    graph still patches.

    Args:
        nodes: Frontend node dicts.

    Returns:
        The prompt node, or ``None`` when the graph has none.
    """
    for node in nodes:
        title = _title(node)
        if _is_negative(node):
            continue
        if any(hint in title for hint in PROMPT_TITLES):
            return node
    for node in nodes:
        if _is_negative(node):
            continue
        if PROMPT_TYPE_HINT in str(node.get("type") or "").lower():
            return node
    return None


def _find_length_node(nodes: list[dict[str, object]]) -> dict[str, object] | None:
    """Pick the node that carries the frame count.

    Args:
        nodes: Frontend node dicts.

    Returns:
        The length node, or ``None`` when the graph has none.
    """
    for node in nodes:
        if any(hint in _title(node) for hint in LENGTH_TITLES):
            return node
    for node in nodes:
        if LATENT_TYPE_HINT in str(node.get("type") or "").lower():
            return node
    return None


def _find_fps_node(nodes: list[dict[str, object]]) -> dict[str, object] | None:
    """Pick the node that carries the output frame rate.

    Args:
        nodes: Frontend node dicts.

    Returns:
        The mux node, or ``None`` when the graph has none.
    """
    for node in nodes:
        if any(hint in _title(node) for hint in FPS_TITLES):
            return node
    return None


def _set_length(node: dict[str, object], frames: int) -> bool:
    """Write ``frames`` into a length node's widgets.

    Dict widgets use the named keys; list widgets use
    :data:`FRAMES_INDEX` (the ``length`` slot of the lane's latent-video
    nodes, which are ``width, height, length, batch``).

    Args:
        node: Node dict to patch in place.
        frames: Frame count to write.

    Returns:
        True when a widget was patched.
    """
    widgets = node.get("widgets_values")
    if isinstance(widgets, dict):
        for key in LENGTH_WIDGET_KEYS:
            if key in widgets:
                widgets[key] = frames
                return True
        return False
    if isinstance(widgets, list) and len(widgets) > FRAMES_INDEX:
        widgets[FRAMES_INDEX] = frames
        return True
    return False


def _set_fps(node: dict[str, object], fps: float) -> bool:
    """Write ``fps`` into a mux node's widgets.

    Args:
        node: Node dict to patch in place.
        fps: Frame rate to write.

    Returns:
        True when a widget was patched.
    """
    widgets = node.get("widgets_values")
    if isinstance(widgets, dict):
        for key in FPS_WIDGET_KEYS:
            if key in widgets:
                widgets[key] = fps
                return True
        return False
    if isinstance(widgets, list):
        for index, value in enumerate(widgets):
            if isinstance(value, float):
                widgets[index] = fps
                return True
    return False


def _widgets_map(graph: Mapping[str, object]) -> Mapping[str, object] | None:
    """The graph's agent patch map (``extra.lab_edit.widgets``).

    Args:
        graph: Graph object about to be patched.

    Returns:
        Patch-name -> ``{"node": id, "widget": name}`` mapping, or ``None``
        when the graph carries no usable map (the lane generator writes one
        into every promoted graph; a hand-saved copy may not have it).
    """
    extra = graph.get("extra")
    lab_edit = extra.get(LAB_EDIT_KEY) if isinstance(extra, Mapping) else None
    widgets = lab_edit.get(WIDGETS_MAP_KEY) if isinstance(lab_edit, Mapping) else None
    return widgets if isinstance(widgets, Mapping) and widgets else None


def _node_by_id(
    nodes: list[dict[str, object]], node_id: object
) -> dict[str, object] | None:
    """Find one node by the id the patch map wrote (int or text).

    Args:
        nodes: Frontend node dicts.
        node_id: Id as the map spells it.

    Returns:
        The node, or ``None`` when no node carries that id.
    """
    wanted = str(node_id or "").strip()
    if not wanted:
        return None
    for node in nodes:
        if str(node.get("id")) == wanted:
            return node
    return None


def _write_widget(node: dict[str, object], widget: str, value: object) -> bool:
    """Write one widget by name, indexed through :data:`WIDGET_SCHEMA`.

    Dict widgets are written by key; list widgets at the index the node type's
    schema gives the widget name.

    Args:
        node: Node dict to patch in place.
        widget: Widget name as the patch map spells it.
        value: Value to write.

    Returns:
        True when the named widget was found and written.
    """
    if not widget:
        return False
    widgets = node.get("widgets_values")
    if isinstance(widgets, dict):
        if widget in widgets:
            widgets[widget] = value
            return True
        return False
    if not isinstance(widgets, list):
        return False
    order = WIDGET_SCHEMA.get(str(node.get("type") or ""))
    if order is None or widget not in order:
        return False
    index = order.index(widget)
    if index < len(widgets):
        widgets[index] = value
        return True
    return False


def _patch_from_map(
    nodes: list[dict[str, object]],
    widget_map: Mapping[str, object],
    key: str,
    value: object,
) -> bool:
    """Apply the patch one map key names, if the graph can resolve it.

    Args:
        nodes: Frontend node dicts (patched in place).
        widget_map: ``extra.lab_edit.widgets`` mapping.
        key: Patch name (``prompt`` / ``length`` / ``fps``).
        value: Value to write.

    Returns:
        True when the named widget was written.
    """
    entry = widget_map.get(key)
    if not isinstance(entry, Mapping):
        return False
    node = _node_by_id(nodes, entry.get("node"))
    if node is None:
        return False
    return _write_widget(node, str(entry.get("widget") or "").strip(), value)


def patch_graph(
    graph: Mapping[str, object], *, prompt_text: str, duration_s: float, fps: float
) -> dict[str, object]:
    """Patch prompt text, frame count, and frame rate into a graph copy.

    The graph's own ``extra.lab_edit.widgets`` map is authoritative: each key
    names the node id and widget the agent must write, so the prompt lands on
    the enhance widget that actually feeds the CLIP encoder rather than on a
    frontend mirror below it. The title/type heuristics run only when the
    graph carries no usable map.

    Args:
        graph: Parsed graph object.
        prompt_text: Cutaway description for the positive prompt widget.
        duration_s: Requested clip length in seconds.
        fps: Requested frame rate.

    Returns:
        Graph copy with the three widgets patched where they were found.
    """
    frames = max(MIN_FRAMES, int(round(float(duration_s) * float(fps))))
    nodes = _nodes(graph)
    patched: dict[str, object] = dict(graph)
    widget_map = _widgets_map(patched)
    if widget_map is not None:
        _patch_from_map(nodes, widget_map, MAP_PROMPT_KEY, prompt_text)
        _patch_from_map(nodes, widget_map, MAP_LENGTH_KEY, frames)
        _patch_from_map(nodes, widget_map, MAP_FPS_KEY, float(fps))
    else:
        prompt_node = _find_prompt_node(nodes)
        length_node = _find_length_node(nodes)
        fps_node = _find_fps_node(nodes)
        if prompt_node is not None:
            _write_prompt(prompt_node, prompt_text)
        if length_node is not None:
            _set_length(length_node, frames)
        if fps_node is not None:
            _set_fps(fps_node, float(fps))
    patched["nodes"] = nodes
    return patched


def _write_prompt(node: dict[str, object], prompt_text: str) -> bool:
    """Write the prompt text into a prompt node's widgets.

    Args:
        node: Node dict to patch in place.
        prompt_text: Description to write.

    Returns:
        True when a widget was patched.
    """
    widgets = node.get("widgets_values")
    if isinstance(widgets, dict):
        for key in ("text", "prompt", "value"):
            if key in widgets:
                widgets[key] = prompt_text
                return True
        return False
    if isinstance(widgets, list):
        for index, value in enumerate(widgets):
            if isinstance(value, str):
                widgets[index] = prompt_text
                return True
        if not widgets:
            widgets.append(prompt_text)
            return True
    return False


def load_graph(*, path: Path | None = None) -> dict[str, object]:
    """Read the package graph file.

    Args:
        path: Graph file override (tests).

    Returns:
        Parsed graph object.

    Raises:
        GraphUnavailable: The file is missing, unreadable, or not an object
            with a node list.
    """
    target = graph_path() if path is None else path
    if not target.is_file():
        raise GraphUnavailable(GRAPH_MISSING_FMT.format(path=target))
    try:
        raw: object = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise GraphUnavailable(GRAPH_INVALID_FMT.format(path=target)) from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("nodes"), list):
        raise GraphUnavailable(GRAPH_INVALID_FMT.format(path=target))
    return raw


def _urlopen(request: urllib.request.Request, timeout: float) -> object:
    """Open one request (indirection so pytest can stub the transport).

    Args:
        request: Prepared request.
        timeout: Socket timeout seconds.

    Returns:
        Context-managed HTTP response.
    """
    return urllib.request.urlopen(request, timeout=timeout)  # noqa: S310 - loopback origin


def _sleep(seconds: float) -> None:
    """Sleep between history polls (indirection so pytest never waits).

    Args:
        seconds: Seconds to block.
    """
    time.sleep(seconds)


def _decode(raw: bytes | str) -> Json:
    """Decode one JSON response body.

    Args:
        raw: Response bytes or text.

    Returns:
        Parsed JSON value.

    Raises:
        ValueError: The body is not JSON.
    """
    text = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else str(raw)
    data: Json = json.loads(text)
    return data


def _open_json(
    url: str,
    *,
    payload: Mapping[str, object] | None,
    urlopen: UrlopenFn | None,
    timeout: float,
) -> Json:
    """Open one URL and decode its JSON body.

    Args:
        url: Absolute URL.
        payload: JSON body to POST, or ``None`` for GET.
        urlopen: Transport seam.
        timeout: Socket timeout seconds.

    Returns:
        Parsed JSON value.

    Raises:
        GenerateClipError: Any wire, decode, or HTTP failure.
    """
    data = None if payload is None else json.dumps(dict(payload)).encode("utf-8")
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method="GET" if data is None else "POST")
    opener = _urlopen if urlopen is None else urlopen
    try:
        with cast(HttpReply, opener(request, timeout)) as response:
            body = response.read()
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise GenerateClipError(f"{url}: {exc}") from exc
    try:
        return _decode(body)
    except ValueError as exc:
        raise GenerateClipError(f"{url}: invalid JSON reply: {exc}") from exc


def queue_prompt(
    graph: Mapping[str, object],
    *,
    client_id: str = "",
    base_url: str | None = None,
    urlopen: UrlopenFn | None = None,
    environ: Mapping[str, str] | None = None,
) -> str:
    """POST the patched graph to the ComfyUI queue.

    Args:
        graph: Patched graph object.
        client_id: Optional ComfyUI client id for progress routing.
        base_url: ComfyUI origin; ``None`` uses :func:`comfy_base`.
        urlopen: Transport seam.
        environ: Injected environ for the default origin.

    Returns:
        The ``prompt_id`` ComfyUI assigned.

    Raises:
        GenerateClipError: The queue failed or named no prompt id.
    """
    origin = comfy_base(environ) if base_url is None else base_url.rstrip("/")
    body: dict[str, object] = {"prompt": dict(graph)}
    if client_id:
        body["client_id"] = client_id
    data = _open_json(
        f"{origin}{QUEUE_PATH}",
        payload=body,
        urlopen=urlopen,
        timeout=QUEUE_TIMEOUT_S,
    )
    if not isinstance(data, dict) or not str(data.get("prompt_id") or ""):
        raise GenerateClipError(f"{origin}{QUEUE_PATH}: no prompt_id in reply")
    return str(data["prompt_id"])


def poll_history(
    prompt_id: str,
    *,
    base_url: str | None = None,
    urlopen: UrlopenFn | None = None,
    sleeper: SleeperFn | None = None,
    poll_s: float = DEFAULT_POLL_S,
    timeout_s: float = DEFAULT_POLL_TIMEOUT_S,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Json]:
    """Poll ``/history/<prompt_id>`` until the entry shows up.

    Args:
        prompt_id: Id assigned by :func:`queue_prompt`.
        base_url: ComfyUI origin; ``None`` uses :func:`comfy_base`.
        urlopen: Transport seam.
        sleeper: Sleep seam between polls.
        poll_s: Seconds between polls.
        timeout_s: Total seconds to wait.
        environ: Injected environ for the default origin.

    Returns:
        The history entry, or ``{}`` when it never arrived (or the poll
        endpoint kept failing).
    """
    origin = comfy_base(environ) if base_url is None else base_url.rstrip("/")
    url = f"{origin}{HISTORY_PATH_FMT.format(prompt_id=prompt_id)}"
    wait = _sleep if sleeper is None else sleeper
    polls = max(1, int(timeout_s // max(poll_s, 0.001)))
    for _ in range(polls):
        try:
            data = _open_json(url, payload=None, urlopen=urlopen, timeout=HISTORY_TIMEOUT_S)
        except GenerateClipError:
            data = {}
        if isinstance(data, dict):
            entry = data.get(prompt_id)
            if isinstance(entry, dict):
                return entry
        wait(poll_s)
    return {}


def _artefact_name(entry: Mapping[str, Json]) -> str:
    """First saved-file name a history entry reports.

    Args:
        entry: History entry for one prompt id.

    Returns:
        ``subfolder/filename`` (or the bare name), or ``""`` when the graph
        reported none.
    """
    outputs = entry.get("outputs")
    if not isinstance(outputs, dict):
        return ""
    for node_output in outputs.values():
        if not isinstance(node_output, dict):
            continue
        for key in ("gifs", "images", "videos"):
            rows = node_output.get(key)
            if not isinstance(rows, list):
                continue
            for row in rows:
                if isinstance(row, dict) and str(row.get("filename") or ""):
                    folder = str(row.get("subfolder") or "").strip("/")
                    name = str(row["filename"])
                    return f"{folder}/{name}" if folder else name
    return ""


def new_generate_row(
    *, project_id: str, prompt: str, client_id: str = "", now: ClockFn | None = None
) -> JobRecord:
    """Fresh pending ``generate_clip`` row.

    Args:
        project_id: Project the cutaway is generated for.
        prompt: The text prompt (kept as the pending message).
        client_id: Panel that asked, when known.
        now: Clock seam.

    Returns:
        Pending row, not yet written.
    """
    stamp = _stamp(now)
    return JobRecord(
        id=uuid.uuid4().hex[:12],
        kind=GENERATE_KIND,
        project_id=project_id,
        state="pending",
        mode="server",
        message=(prompt.strip() or "generate cutaway")[:240],
        out_path="",
        created_at=stamp,
        updated_at=stamp,
        client_id=client_id,
    )


def generate_clip(
    edit_dir: Path | str,
    *,
    prompt: str,
    duration_s: float = 5.0,
    fps: float = 24.0,
    project_id: str = "",
    client_id: str = "",
    base_url: str | None = None,
    urlopen: UrlopenFn | None = None,
    sleeper: SleeperFn | None = None,
    now: ClockFn | None = None,
    occupancy: OccupancyFn | None = None,
    environ: Mapping[str, str] | None = None,
    graph_file: Path | None = None,
    poll_s: float = DEFAULT_POLL_S,
    timeout_s: float = DEFAULT_POLL_TIMEOUT_S,
) -> JobRecord:
    """Generate one cutaway clip and return its landed jobstore row.

    The row is written before any socket opens, so a crash or a refusal still
    leaves an ``ok`` false row the panel and the agent can read. Occupancy is
    checked first (heavy GPU XOR), then the graph is loaded and patched, then
    the queue and the history poll run.

    Args:
        edit_dir: ``${COMFY_OUTPUT_DIR}/edit`` directory.
        prompt: Text description of the cutaway.
        duration_s: Requested clip seconds.
        fps: Requested frame rate.
        project_id: Project the clip belongs to.
        client_id: Panel that asked.
        base_url: ComfyUI origin; ``None`` uses :func:`comfy_base`.
        urlopen: Transport seam.
        sleeper: Sleep seam.
        now: Clock seam.
        occupancy: Occupancy mode reader; ``None`` reads the state file.
        environ: Injected environ for the origin and the occupancy path.
        graph_file: Graph path override (tests, or a lane-local variant).
        poll_s: Seconds between history polls.
        timeout_s: Total history poll seconds.

    Returns:
        The final row (``ok`` or ``failed``).
    """
    read_mode: OccupancyFn = (
        (lambda: agent.read_occupancy_mode(environ=environ))
        if occupancy is None
        else occupancy
    )
    row = new_generate_row(project_id=project_id, prompt=prompt, client_id=client_id, now=now)
    render_server.write_job(edit_dir, row)
    mode = str(read_mode() or "").strip() or "unknown"
    if mode not in HEAVY_OK_OCCUPANCY:
        return render_server.tick_job(
            edit_dir,
            row["id"],
            state="failed",
            message=OCCUPANCY_REFUSAL_FMT.format(mode=mode),
            now=now,
        )
    target = graph_path() if graph_file is None else graph_file
    try:
        graph = load_graph(path=target)
        patched = patch_graph(graph, prompt_text=prompt, duration_s=duration_s, fps=fps)
    except GraphUnavailable as exc:
        return render_server.tick_job(
            edit_dir, row["id"], state="failed", message=str(exc), now=now
        )
    if not str(prompt or "").strip():
        return render_server.tick_job(
            edit_dir,
            row["id"],
            state="failed",
            message="generate_clip needs a prompt",
            now=now,
        )
    try:
        prompt_id = queue_prompt(
            patched,
            client_id=client_id,
            base_url=base_url,
            urlopen=urlopen,
            environ=environ,
        )
    except GenerateClipError as exc:
        return render_server.tick_job(
            edit_dir, row["id"], state="failed", message=f"queue failed: {exc}", now=now
        )
    render_server.tick_job(
        edit_dir,
        row["id"],
        state="running",
        message=f"queued prompt {prompt_id}",
        now=now,
    )
    entry = poll_history(
        prompt_id,
        base_url=base_url,
        urlopen=urlopen,
        sleeper=sleeper,
        poll_s=poll_s,
        timeout_s=timeout_s,
        environ=environ,
    )
    if not entry:
        return render_server.tick_job(
            edit_dir,
            row["id"],
            state="failed",
            message=TIMEOUT_MESSAGE.format(prompt_id=prompt_id),
            now=now,
        )
    name = _artefact_name(entry)
    return render_server.tick_job(
        edit_dir,
        row["id"],
        state="ok",
        message=OUTPUT_MESSAGE.format(name=name)
        if name
        else NO_OUTPUT_MESSAGE.format(prompt_id=prompt_id),
        out_path=name,
        now=now,
    )
