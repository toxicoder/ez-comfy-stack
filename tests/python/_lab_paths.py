"""Resolve shipped lab JSON under workflows/_lab/<lane>/.

Not collected by pytest (leading underscore). Builders and tests import
``lab_json`` instead of hardcoding a folder.

Ids are ``_lab``-relative paths without ``.json`` (``stills/still-draft``,
``motion/silent/still-to-video-5s``). Basenames may collide across lanes; pass the relative
id when they do.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "workflows"
LAB_ROOT = WF / "_lab"
SHORTS_YAML = WF / "shorts"
_LAB_GRAPH_CACHE: dict[Path, dict[str, Any]] | None = None
_TRACKED_LAB_JSON: frozenset[str] | None = None
_TRACKED_LAB_JSON_LOADED = False
ALLOWED_LANES = (
    "stills",
    "motion",
    "creator",
    "services",
    "films",
    "dcc",
    "optional",
    "audio",
    "inspire",
)

# ComfyUI frontend ensureCorrectLayoutScale: "Vue" unprojects 1.2x (shrinks
# LiteGraph coords). "Vue-corrected" keeps canonical geometry; Vue scales in CSS.
WORKFLOW_RENDERER_VERSION = "Vue-corrected"


def _git_tracked_lab_json() -> frozenset[str] | None:
    """Git-tracked ``workflows/_lab/**/*.json`` paths, repo-relative.

    Parallel no-sandbox Bazel tests (``promote_workflow.bats``) may write scratch
    JSON into the live ``_lab`` tree. Pytest parametrize must ignore those files
    or it collects a path that is gone by the time the test runs.

    Returns:
        A frozenset of posix relative paths, or ``None`` when git cannot answer
        so callers fall back to a directory walk.
    """
    global _TRACKED_LAB_JSON, _TRACKED_LAB_JSON_LOADED
    if _TRACKED_LAB_JSON_LOADED:
        return _TRACKED_LAB_JSON
    import subprocess

    try:
        completed = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-z", "--", "workflows/_lab"],
            check=False,
            capture_output=True,
        )
    except OSError:
        _TRACKED_LAB_JSON_LOADED = True
        _TRACKED_LAB_JSON = None
        return None
    if completed.returncode != 0:
        _TRACKED_LAB_JSON_LOADED = True
        _TRACKED_LAB_JSON = None
        return None
    tracked = frozenset(
        part.replace("\\", "/")
        for part in completed.stdout.decode("utf-8", errors="replace").split("\0")
        if part.endswith(".json")
    )
    _TRACKED_LAB_JSON_LOADED = True
    _TRACKED_LAB_JSON = tracked
    return tracked


def lab_graph_paths(root: Path | None = None) -> list[Path]:
    """Every ``*.json`` under ``workflows/_lab``.

    The default tree (``root is None``) keeps only git-tracked files so a
    parallel BATS leftover cannot enter pytest parametrize.
    """
    base = LAB_ROOT if root is None else Path(root) / "_lab"
    if not base.is_dir():
        base = Path(root) if root is not None else LAB_ROOT
    if not base.is_dir():
        return []
    paths = sorted(path for path in base.rglob("*.json") if path.is_file())
    if root is not None:
        return paths
    tracked = _git_tracked_lab_json()
    if tracked is None:
        return paths
    kept: list[Path] = []
    root_resolved = ROOT.resolve()
    for path in paths:
        try:
            rel = path.resolve().relative_to(root_resolved).as_posix()
        except ValueError:
            continue
        if rel in tracked:
            kept.append(path)
    return kept


def lab_example_paths(root: Path | None = None) -> list[Path]:
    """Alias for ``lab_graph_paths`` (historical name)."""
    return lab_graph_paths(root)


def cached_lab_graph_map(*, root: Path | None = None) -> dict[Path, dict[str, Any]]:
    """Parse every default-tree lab graph once per process.

    Arguments:
        root: Optional workflows root. Non-default trees are not cached.
    Returns:
        Mapping of graph path to parsed dict (shared; treat as read-only).
    """
    global _LAB_GRAPH_CACHE
    if root is not None:
        base = Path(root) / "_lab"
        if not base.is_dir():
            base = Path(root)
        out: dict[Path, dict[str, Any]] = {}
        for path in lab_graph_paths(root):
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                out[path] = data
        return out
    if _LAB_GRAPH_CACHE is None:
        parsed: dict[Path, dict[str, Any]] = {}
        for path in lab_graph_paths():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                parsed[path] = data
        _LAB_GRAPH_CACHE = parsed
    return _LAB_GRAPH_CACHE


def load_lab_graph(path: Path) -> dict[str, Any]:
    """Return parsed JSON for a lab graph, using the process cache when possible.

    Arguments:
        path: Graph path under ``workflows/_lab``.
    Returns:
        Graph dict.
    """
    cache = cached_lab_graph_map()
    data = cache.get(path)
    if data is not None:
        return data
    resolved = path.resolve()
    for cached_path, cached in cache.items():
        if cached_path.resolve() == resolved:
            return cached
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise TypeError(f"lab graph {path} is not a JSON object")
    return loaded


def cached_lab_graph_rows() -> list[tuple[str, Path, dict[str, Any]]]:
    """Return ``(lab_rel, path, data)`` for every cached default-tree graph."""
    rows: list[tuple[str, Path, dict[str, Any]]] = []
    for path, data in cached_lab_graph_map().items():
        extra = data.get("extra") or {}
        lab_rel = extra.get("lab_rel")
        if not isinstance(lab_rel, str) or not lab_rel.strip():
            lab_rel = path.relative_to(LAB_ROOT).with_suffix("").as_posix()
        rows.append((str(lab_rel).strip(), path, data))
    rows.sort(key=lambda row: row[1].as_posix())
    return rows


def _lab_base(root: Path | None) -> Path:
    base = LAB_ROOT if root is None else Path(root) / "_lab"
    if not base.is_dir() and root is not None:
        return Path(root)
    return base


def lab_rel_of(path: Path, *, root: Path | None = None) -> str:
    """Return the ``_lab``-relative id for a JSON path."""
    base = _lab_base(root)
    rel = path.resolve().relative_to(base.resolve())
    return rel.with_suffix("").as_posix()


def lab_json(stem: str, *, root: Path | None = None) -> Path:
    """Return the unique ``_lab/**/<stem>.json`` path.

    ``stem`` may be a basename (``still-draft``), a file name, an old
    leftover relative path, or a lab-relative id (``motion/silent/still-to-video-5s``).
    """
    from _lab_ids import rel_id

    text = str(stem).replace("\\", "/").lstrip("./")
    text = text.removeprefix("_lab/")
    if text.endswith(".json"):
        text = text[: -len(".json")]
    text = rel_id(text)
    base = _lab_base(root)
    if "/" in text:
        path = base / f"{text}.json"
        if path.is_file():
            return path
        raise FileNotFoundError(f"no lab json named {text}.json under {base}")
    name = f"{text}.json"
    hits = sorted(p for p in base.rglob(name) if p.is_file())
    if not hits:
        raise FileNotFoundError(f"no lab json named {name} under {base}")
    if len(hits) > 1:
        rel = ", ".join(str(p.relative_to(base)) for p in hits)
        raise FileNotFoundError(f"ambiguous lab json {name}: {rel}")
    return hits[0]


def _subdir_parts(subdir: str) -> tuple[str, ...]:
    """Relative nested components under a lab lane.

    Arguments:
        subdir: Slash-separated relative path (``albums/nill-bye/peer-review``).
    Returns:
        Path parts to join under the lane directory.
    Raises:
        ValueError: empty, absolute, or ``.`` / ``..`` components.
    """
    extra = Path(str(subdir).strip())
    if extra.is_absolute():
        raise ValueError(f"invalid lab subdir {subdir!r}")
    parts = extra.parts
    if not parts:
        raise ValueError(f"invalid lab subdir {subdir!r}")
    for part in parts:
        if part in {".", ".."} or part.strip() == "" or "/" in part or "\\" in part:
            raise ValueError(f"invalid lab subdir {subdir!r}")
    return parts


def lab_dest(stem: str, *, lane: str | None = None, subdir: str | None = None) -> Path:
    """Path to write a lab graph. Creates the lane directory.

    ``stem`` may be a lab-relative id (``stills/still-draft``) or a
    basename. ``subdir`` is an optional relative path under the lane.
    """
    from _lab_ids import rel_id

    text = str(stem).replace("\\", "/").lstrip("./")
    text = text.removeprefix("_lab/")
    if text.endswith(".json"):
        text = text[: -len(".json")]
    text = rel_id(text)
    if "/" in text and (subdir is None or str(subdir).strip() == ""):
        dest = LAB_ROOT / f"{text}.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        return dest
    name = Path(text).name
    chosen = lane or lane_for_stem(text)
    if chosen not in ALLOWED_LANES:
        raise ValueError(f"invalid lab lane {chosen!r}")
    dest_dir = LAB_ROOT / chosen
    if subdir is not None and str(subdir).strip() != "":
        dest_dir = dest_dir.joinpath(*_subdir_parts(str(subdir)))
    dest = dest_dir / f"{name}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest


def stamp_nodes2(graph: dict[str, Any]) -> dict[str, Any]:
    """Mark a Comfy graph as Nodes 2.0 with canonical LiteGraph coordinates.

    Sets ``extra.workflowRendererVersion`` to ``Vue-corrected`` on the root
    graph and on each ``definitions.subgraphs[]`` extra. Does not rewrite
    node positions or sizes.

    Arguments:
        graph: Comfy workflow dict (mutated).
    Returns:
        ``graph``.
    """
    extra = graph.setdefault("extra", {})
    extra["workflowRendererVersion"] = WORKFLOW_RENDERER_VERSION
    definitions = graph.get("definitions")
    if isinstance(definitions, dict):
        for sub in definitions.get("subgraphs") or []:
            if isinstance(sub, dict):
                sub.setdefault("extra", {})["workflowRendererVersion"] = (
                    WORKFLOW_RENDERER_VERSION
                )
    return graph


def apply_lab_identity(graph: dict[str, Any], rel: str) -> dict[str, Any]:
    """Set ``id`` to the file stem and ``extra.lab_rel`` to the relative id."""
    from _lab_ids import rel_id

    clean = rel_id(str(rel).removesuffix(".json"))
    graph["id"] = Path(clean).name
    extra = graph.setdefault("extra", {})
    extra["lab_rel"] = clean
    stamp_nodes2(graph)
    return graph


def write_lab_graph(path: Path, graph: dict[str, Any]) -> Path:
    """Write graph JSON with ``id`` = stem and ``extra.lab_rel`` set.

    Arguments:
        path: Destination under ``workflows/_lab``.
        graph: Comfy graph dict (mutated).
    Returns:
        ``path``.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    apply_lab_identity(graph, lab_rel_of(path))
    from _lab_layout import ensure_node_spacing

    ensure_node_spacing(graph)
    path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    return path


def lane_for_stem(stem: str) -> str:
    """Sidebar lane for a lab filename or relative path."""
    from _lab_ids import rel_id

    rel = str(stem).replace("\\", "/").lstrip("./")
    rel = rel.removeprefix("_lab/")
    mapped = rel_id(rel)
    name = Path(mapped).name
    first = mapped.split("/", 1)[0]
    if first in ALLOWED_LANES:
        return first
    if (
        name.startswith("podcast-")
        or name.startswith("music-")
        or name.startswith("dub-")
        or name.startswith("audio-")
        or name.startswith("rap-")
        or name.startswith("album")
        or name.startswith("cover")
        or name[:1].isdigit()
    ):
        return "audio"
    if (
        name.startswith("prompt-forge")
        or name.startswith("beat-sheet")
        or name.startswith("research-chat")
        or name.startswith("cinema-rack")
        or name.startswith("audio-rack")
        or name.startswith("app-forge")
    ):
        return "inspire"
    raise ValueError(f"cannot map {stem!r} to a lab lane")
