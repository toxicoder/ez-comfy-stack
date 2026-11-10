"""Read-only catalog of the ``workflows/_lab`` lanes the console can browse.

The console never edits a graph and never copies ``_lab`` into ``_user``: this
module only reports what is on disk so the operator can pick one and then hand
off to the ComfyUI UI, or ask ``studio-mcp`` to clone it into the live
``_user`` folder. The lane titles mirror ``LANE_REGISTRY`` in
``tests/python/_lab_paths.py``, which stays the single definition of the browse
order; ``tests/python/test_tui_lanes.py`` fails if the two drift.

A malformed or unreadable graph is skipped rather than raised: a lane with one
broken file still has to be browsable on a remote box where re-running a
generator is not the fastest fix.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ez_common import Json, JsonMap

LAB_SUBPATH = "workflows/_lab"
"""Path, relative to the repo root, where promoted graphs live."""

USER_SUBPATH = "workflows/_user"
"""Path the operator loads live graphs from; the console only names it."""

_LANE_ROWS: tuple[tuple[str, int, str, str], ...] = (
    (
        "photos",
        10,
        "Photos",
        "Single images: drafts, edits, product shots, and channel art.",
    ),
    (
        "video",
        20,
        "Video",
        "Short clips, silent or with audio, from a still you already like.",
    ),
    (
        "social",
        30,
        "Social",
        "Platform-shaped posts for a channel or shop, sized per surface.",
    ),
    (
        "business",
        40,
        "Business",
        "Client work by vertical, from listing photos to ad packs.",
    ),
    (
        "film",
        50,
        "Film",
        "Narrative shorts, act by act, plus the cut tools that finish them.",
    ),
    (
        "audio",
        60,
        "Audio",
        "Music, podcasts, dubbing, and whole albums.",
    ),
    (
        "3d",
        70,
        "3D",
        "Meshes and turntables built from a still you already like.",
    ),
    (
        "guides",
        80,
        "Control guides",
        "Depth, canny, and clay passes that steer a generation.",
    ),
    (
        "labs",
        90,
        "Labs",
        "Writers' room tools, and opt-in model families you add on purpose.",
    ),
)
"""Lane id, order, title, and blurb, mirrored from ``_lab_paths.LANE_REGISTRY``."""


@dataclass(frozen=True)
class Lane:
    """One browsable lane and how many graphs it currently holds.

    Attributes:
        lane_id: Directory name under ``workflows/_lab``.
        order: Browse order, lowest first.
        title: Operator-facing name.
        description: One-line blurb.
        graph_count: Graphs found on disk.
    """

    lane_id: str
    order: int
    title: str
    description: str
    graph_count: int = 0


@dataclass(frozen=True)
class Graph:
    """One promoted lab graph, as far as the console needs to know it.

    Attributes:
        lane_id: Lane the file sits in.
        rel_id: ``extra.lab_rel``, the unique id other tools address it by.
        title: Filename stem, the label an operator recognises.
        description: ``extra.lab_description``.
        occupancy: Which occupancy desk the graph expects.
        handoff: Graph ids the graph suggests next.
        default_view: ComfyUI view it opens in.
        path: Absolute path to the JSON file.
    """

    lane_id: str
    rel_id: str
    title: str
    description: str
    occupancy: str
    handoff: tuple[str, ...] = field(default_factory=tuple)
    default_view: str = ""
    path: Path = Path(LAB_SUBPATH)


def lab_root(repo_root: Path) -> Path:
    """Directory the promoted graphs live in.

    Args:
        repo_root: Repository checkout.

    Returns:
        The ``workflows/_lab`` directory path, whether or not it exists.
    """
    return repo_root / LAB_SUBPATH


def lane_ids() -> tuple[str, ...]:
    """Lane ids in browse order.

    Returns:
        One id per lane.
    """
    return tuple(row[0] for row in _LANE_ROWS)


def lanes(repo_root: Path) -> tuple[Lane, ...]:
    """Every lane with its live graph count.

    A lane whose directory is missing reads as empty rather than erroring, so a
    partial checkout still browses.

    Args:
        repo_root: Repository checkout.

    Returns:
        Lanes in browse order.
    """
    rows: list[Lane] = []
    for lane_id, order, title, description in _LANE_ROWS:
        directory = lab_root(repo_root) / lane_id
        count = 0
        if directory.is_dir():
            count = sum(1 for path in directory.rglob("*.json") if path.is_file())
        rows.append(
            Lane(
                lane_id=lane_id,
                order=order,
                title=title,
                description=description,
                graph_count=count,
            )
        )
    return tuple(rows)


def graphs(repo_root: Path, lane_id: str) -> tuple[Graph, ...]:
    """Every graph in one lane, sorted by id.

    Args:
        repo_root: Repository checkout.
        lane_id: Lane directory name.

    Returns:
        Graphs sorted by :attr:`Graph.rel_id`; empty for an unknown lane.
    """
    directory = lab_root(repo_root) / lane_id
    if not directory.is_dir():
        return ()
    found: list[Graph] = []
    for path in sorted(directory.rglob("*.json")):
        if not path.is_file():
            continue
        graph = _read_graph(path, lane_id)
        if graph is not None:
            found.append(graph)
    return tuple(sorted(found, key=lambda item: item.rel_id))


def all_graphs(repo_root: Path) -> tuple[Graph, ...]:
    """Every graph across every lane, in lane then id order.

    Returns:
        All readable graphs.

    Args:
        repo_root: Repository checkout.
    """
    rows: list[Graph] = []
    for lane in lanes(repo_root):
        rows.extend(graphs(repo_root, lane.lane_id))
    return tuple(rows)


def find_graph(repo_root: Path, rel_id: str) -> Graph | None:
    """Look one graph up by its ``lab_rel`` id.

    Args:
        repo_root: Repository checkout.
        rel_id: The id other tools address the graph by, ``photos/background-swap``.

    Returns:
        The graph, or None when no file carries that id.
    """
    for graph in all_graphs(repo_root):
        if graph.rel_id == rel_id:
            return graph
    return None


def search_graphs(repo_root: Path, query: str) -> tuple[Graph, ...]:
    """Filter graphs by a case-insensitive substring over id, title, and blurb.

    Args:
        repo_root: Repository checkout.
        query: Words to match; empty matches everything.

    Returns:
        Matching graphs in lane then id order.
    """
    needle = query.strip().lower()
    rows = all_graphs(repo_root)
    if not needle:
        return rows
    return tuple(
        graph
        for graph in rows
        if needle in f"{graph.rel_id} {graph.title} {graph.description}".lower()
    )


def _read_graph(path: Path, lane_id: str) -> Graph | None:
    """Parse one graph file into a :class:`Graph`.

    Args:
        path: The ``.json`` file.
        lane_id: Lane directory it came from.

    Returns:
        The graph, or None when the file is unreadable or not an object.
    """
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(parsed, dict):
        return None
    doc: JsonMap = parsed
    extra = doc.get("extra")
    extra_map: JsonMap = extra if isinstance(extra, dict) else {}
    app_mode = extra_map.get("lab_app_mode")
    mode_map: JsonMap = app_mode if isinstance(app_mode, dict) else {}
    rel = _text(extra_map.get("lab_rel")) or f"{lane_id}/{path.stem}"
    handoff = mode_map.get("handoff")
    handoff_ids = (
        tuple(item for item in handoff if isinstance(item, str))
        if isinstance(handoff, list)
        else ()
    )
    return Graph(
        lane_id=lane_id,
        rel_id=rel,
        title=path.stem,
        description=_text(extra_map.get("lab_description")),
        occupancy=_text(mode_map.get("occupancy")),
        handoff=handoff_ids,
        default_view=_text(mode_map.get("default_view")),
        path=path,
    )


def _text(value: Json) -> str:
    """Coerce a parsed JSON value to a trimmed string.

    Args:
        value: Whatever came out of the document.

    Returns:
        The string form, or empty for anything non-scalar.
    """
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return ""


def user_folder_hint() -> str:
    """Where live private graphs live, for the hand-off pane.

    Returns:
        A path fragment an operator can paste into ComfyUI's workflow browser.
    """
    return f"${{COMFY_OUTPUT_DIR}}/comfy-user/default/workflows/{USER_SUBPATH.lstrip('/')}"


def is_lane(value: str) -> bool:
    """Whether a string names a real lane.

    Args:
        value: Candidate lane id.

    Returns:
        True when the id is one of the nine lanes.
    """
    return value in set(lane_ids())
