"""Clone shipped lab graphs into live _user/ Apps.

Template-first: never invent node types or coordinates. Occupancy llm for
the generator; cloned graphs keep the source occupancy. Fail-soft without a
GGUF (keyword heuristic). No Queue. Never writes workflows/_lab.
"""

from __future__ import annotations

import copy
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

# Prompt files, slug rules, banned strings, widget indexes, and template heuristics.
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_SLUG_CLEAN_RE = re.compile(r"[^a-z0-9]+")
AUTO = "auto"
BANNED = (
    "MiniMax",
    "MiniMaxH3",
    "minimax_h3",
    "klein-9b",
    "FLUX.2-dev",
    "Seedance",
    "Kling",
    "z_image_turbo",
)
RENDERER = "Vue-corrected"
MAX_SLUG = 48

CORE_WIDGET_INDEX: dict[str, dict[str, int]] = {
    "SaveImage": {"filename_prefix": 0},
    "KSampler": {
        "seed": 0,
        "steps": 2,
        "cfg": 3,
        "sampler_name": 4,
        "scheduler": 5,
        "denoise": 6,
    },
    "EmptyFlux2LatentImage": {"width": 0, "height": 1, "batch_size": 2},
    "CLIPTextEncode": {"text": 0},
}

EZ_WIDGET_ORDER: dict[str, tuple[str, ...]] = {
    "EZKleinPromptEnhance": (
        "sample",
        "prompt",
        "enhance",
        "mode",
        "duration_hint",
        "style",
        "catalog",
    ),
    "EZWanPromptEnhance": (
        "sample",
        "prompt",
        "enhance",
        "mode",
        "duration_hint",
        "style",
        "catalog",
    ),
    "EZLTXPromptEnhance": (
        "sample",
        "prompt",
        "enhance",
        "mode",
        "duration_hint",
        "audio_notes",
        "style",
        "catalog",
    ),
    "EZSamplePrompt": ("sample", "prompt", "catalog"),
    "EZCreativeResearch": (
        "sample",
        "prompt",
        "mode",
        "web_search",
        "subagents",
        "history",
        "catalog",
    ),
    "EZAppForge": (
        "sample",
        "prompt",
        "template",
        "slug",
        "as_app",
        "overwrite",
        "catalog",
    ),
    "EZCinemaRack": ("subject", "flavor", "recipe"),
    "EZAudioRack": ("brief", "flavor", "recipe"),
}

SLOT_ALIASES = {
    "prefix": "filename_prefix",
    "filename_prefix": "filename_prefix",
    "brief": "prompt",
    "message": "prompt",
}

# First matching substring wins. More specific tokens first.
_TEMPLATE_RULES: tuple[tuple[str, str], ...] = (
    ("pinterest", "creator/stills/pinterest-pin"),
    ("idea pin", "creator/stills/pinterest-story"),
    ("twitch overlay", "creator/stills/twitch-overlay"),
    ("starting soon", "creator/stills/twitch-starting"),
    ("spotify canvas", "creator/silent/spotify-canvas"),
    ("playlist cover", "creator/stills/spotify-playlist"),
    ("highlight", "creator/stills/instagram-highlight"),
    ("carousel", "creator/stills/instagram-carousel-5"),
    ("channel art", "creator/stills/youtube-channel-art"),
    ("channel icon", "creator/stills/youtube-channel-icon"),
    ("shorts thumb", "creator/stills/youtube-shorts-thumb"),
    ("audiogram", "creator/stills/audiogram-wide"),
    ("linkedin banner", "creator/stills/linkedin-banner"),
    ("zoom background", "creator/stills/zoom-bg"),
    ("merch", "creator/stills/merch-tee"),
    ("image studio", "stills/image-studio"),
    ("still studio", "stills/still-studio"),
    ("background swap", "stills/background-swap"),
    ("bg swap", "stills/background-swap"),
    ("face swap", "stills/image-studio"),
    ("creator mode", "stills/image-studio"),
    ("platform still", "stills/still-studio"),
    ("format still", "stills/still-studio"),
    ("instagram-square", "stills/instagram-square"),
    ("1:1", "stills/instagram-square"),
    ("square", "stills/instagram-square"),
    ("text swap", "stills/text-swap"),
    ("text-swap", "stills/text-swap"),
    ("replace text", "stills/text-swap"),
    ("relabel", "stills/text-swap"),
    ("lettering", "stills/text-swap"),
    ("thumbnail", "stills/thumbnail"),
    ("open-graph", "stills/open-graph"),
    ("og image", "stills/open-graph"),
    ("banner", "stills/banner-wide"),
    ("packshot", "stills/product-packshot"),
    ("sticker", "motion/loops/sticker-loop"),
    ("bumper", "motion/loops/bumper-loop"),
    ("gif", "motion/loops/gif-loop"),
    ("loop", "motion/loops/gif-loop"),
    ("dialogue", "motion/av/dialogue-12s"),
    ("podcast", "audio/podcast/two-host-episode"),
    ("learn podcast", "audio/podcast/learn-episode"),
    ("study podcast", "audio/podcast/learn-episode"),
    ("study mix", "audio/podcast/learn-episode"),
    ("rap", "audio/music/rap-draft"),
    ("ace-step", "audio/music/rap-draft"),
    ("beat-sheet", "inspire/beat-sheet"),
    ("beat sheet", "inspire/beat-sheet"),
    ("90s", "inspire/beat-sheet"),
    ("film", "inspire/beat-sheet"),
    ("a2v", "motion/av/audio-to-video-12s"),
    ("foley", "motion/av/still-to-video-12s"),
    ("silent", "motion/silent/still-to-video-5s"),
    ("i2v", "motion/silent/still-to-video-5s"),
    ("ltx", "motion/av/still-to-video-12s"),
    ("wan", "motion/silent/still-to-video-5s"),
    ("av", "motion/av/still-to-video-12s"),
    ("still", "stills/still-draft"),
    ("plate", "stills/still-draft"),
)

DEFAULT_TEMPLATE = "stills/still-draft"


class ForgeError(ValueError):
    """Operator-facing generation failure."""


@dataclass
class ForgeResult:
    """Saved (or dry-run) operator graph."""

    ok: bool
    path: str = ""
    template: str = ""
    occupancy: str = ""
    widgets: list[str] = field(default_factory=list)
    slug: str = ""
    as_app: bool = True
    reason: str = ""
    status: str = ""
    error: str = ""
    graph: dict[str, Any] | None = None


def _repo_root() -> Path:
    """Repository root (custom_nodes/ez_studio_forge → parents[2]).

    Returns:
        Absolute repo root.
    """
    return Path(__file__).resolve().parents[2]


def _output_dir() -> Path:
    """Operator output directory from env, defaulting to the host bind.

    Returns:
        ``COMFY_OUTPUT_DIR`` or ``/mnt/comfy-output``.
    """
    return Path(os.environ.get("COMFY_OUTPUT_DIR", "/mnt/comfy-output"))


def _lab_root() -> Path:
    """Shipped lab graph directory.

    Returns:
        ``workflows/_lab``.
    """
    return _repo_root() / "workflows" / "_lab"


def _blocks_root() -> Path:
    """Studio subgraph blueprint directory.

    Returns:
        ``custom_nodes/ez_studio_blocks/subgraphs``.
    """
    return _repo_root() / "custom_nodes" / "ez_studio_blocks" / "subgraphs"


def user_workflows_dir() -> Path:
    """Live operator graphs (never `_lab/`).

    Returns:
        ``_user`` workflows directory under the Comfy user tree.
    """
    return _output_dir() / "comfy-user" / "default" / "workflows" / "_user"


def load_prompt(name: str) -> str:
    """Load ``prompts/<name>.txt``.

    Args:
        name: Stem without ``.txt``.

    Returns:
        File contents stripped of trailing whitespace.
    """
    path = PROMPTS_DIR / f"{name}.txt"
    return path.read_text(encoding="utf-8").strip()


def _log(message: str) -> None:
    """Write a pack status line to stderr.

    Args:
        message: Text after the ``[ez_studio_forge]`` prefix.
    """
    print(f"[ez_studio_forge] {message}", file=sys.stderr)


def _as_bool(value: object) -> bool:
    """Coerce a Comfy widget value to bool.

    Args:
        value: BOOLEAN widget or loose truthy token.

    Returns:
        Parsed boolean.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def normalize_stem(stem: str) -> str:
    """Normalize a lab_rel / file stem to `_lab`-relative id.

    Args:
        stem: File stem, lab_rel, or path-like token.

    Returns:
        `_lab`-relative id without ``.json`` / ``.app.json``.
    """
    text = str(stem or "").replace("\\", "/").strip().lstrip("./")
    text = text.removeprefix("_lab/")
    if text.endswith(".app.json"):
        text = text[: -len(".app.json")]
    elif text.endswith(".json"):
        text = text[: -len(".json")]
    return text.strip()


def _banned_hit(blob: str) -> str | None:
    """Return the first banned needle found in ``blob``.

    Args:
        blob: JSON or text to scan.

    Returns:
        Matching needle, or None.
    """
    for needle in BANNED:
        if needle in blob:
            return needle
    return None


def slugify(text: str, fallback: str = "app") -> str:
    """Filesystem slug from a brief.

    Args:
        text: Brief or title.
        fallback: Used when ``text`` sanitizes empty.

    Returns:
        Lowercase hyphenated slug, at most ``MAX_SLUG`` characters.
    """
    raw = (text or fallback).lower()
    slug = _SLUG_CLEAN_RE.sub("-", raw).strip("-")
    if not slug:
        slug = fallback
    return slug[:MAX_SLUG]


def validate_slug(slug: str) -> str:
    """Return a legal slug or raise ForgeError.

    Args:
        slug: Candidate filesystem stem.

    Returns:
        Lowercased slug truncated to ``MAX_SLUG``.

    Raises:
        ForgeError: Empty, path-like, or illegal characters.
    """
    text = str(slug or "").strip().lower()
    if not text:
        raise ForgeError("missing slug")
    if ".." in text or "/" in text or "\\" in text:
        raise ForgeError(f"illegal slug {slug!r}")
    if not SLUG_RE.match(text):
        raise ForgeError(f"illegal slug {slug!r}")
    return text[:MAX_SLUG]


def load_lab_graph(stem: str) -> tuple[Path, dict[str, Any]] | None:
    """Load one shipped lab graph. None when missing or ambiguous.

    Args:
        stem: `_lab`-relative id or file stem.

    Returns:
        ``(path, graph)`` or None when missing, ambiguous, or invalid JSON.
    """
    text = normalize_stem(stem)
    if not text:
        return None
    root = _lab_root()
    if "/" in text:
        path = root / f"{text}.json"
        hits = [path] if path.is_file() else []
        if not hits:
            app = root / f"{text}.app.json"
            hits = [app] if app.is_file() else []
    else:
        name = f"{text}.json"
        hits = sorted(p for p in root.rglob(name) if p.is_file())
        if not hits:
            hits = sorted(p for p in root.rglob(f"{text}.app.json") if p.is_file())
    if len(hits) != 1:
        return None
    try:
        data = json.loads(hits[0].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return hits[0], data


def _linear_labels(extra: Mapping[str, Any]) -> list[str]:
    """Collect App-mode widget labels from ``extra.linearData``.

    Args:
        extra: Graph ``extra`` mapping.

    Returns:
        Label strings in linear order.
    """
    linear = extra.get("linearData") or {}
    labels: list[str] = []
    inputs = linear.get("inputs") if isinstance(linear, dict) else None
    if not isinstance(inputs, list):
        return labels
    for entry in inputs:
        if not isinstance(entry, list) or len(entry) < 2:
            continue
        config = entry[2] if len(entry) > 2 and isinstance(entry[2], dict) else {}
        label = config.get("label") if isinstance(config, dict) else None
        labels.append(str(label or entry[1]))
    return labels


def _occupancy_of(graph: Mapping[str, Any]) -> str:
    """Read occupancy from ``extra.lab_app_mode``.

    Args:
        graph: Serialized Comfy graph.

    Returns:
        Occupancy id, or empty string.
    """
    extra = graph.get("extra") or {}
    if not isinstance(extra, dict):
        return ""
    mode = extra.get("lab_app_mode") or {}
    if not isinstance(mode, dict):
        return ""
    return str(mode.get("occupancy") or "")


def _default_view(graph: Mapping[str, Any]) -> str:
    """Read App/graph default view from ``extra.lab_app_mode``.

    Args:
        graph: Serialized Comfy graph.

    Returns:
        ``app`` or ``graph``.
    """
    extra = graph.get("extra") or {}
    if not isinstance(extra, dict):
        return "graph"
    mode = extra.get("lab_app_mode") or {}
    if not isinstance(mode, dict):
        return "graph"
    view = str(mode.get("default_view") or "graph")
    return view if view in {"app", "graph"} else "graph"


def list_templates(
    *,
    query: str = "",
    occupancy: str = "",
    lane: str = "",
) -> list[dict[str, Any]]:
    """Shipped `_lab` graphs plus studio-block ids.

    Args:
        query: Optional substring filter across id/lane/occupancy/description.
        occupancy: Optional occupancy id filter.
        lane: Optional lane filter.

    Returns:
        Template row dicts (lab graphs and block blueprints).
    """
    q = query.strip().lower()
    occ = occupancy.strip().lower()
    lane_f = lane.strip().lower()
    rows: list[dict[str, Any]] = []
    root = _lab_root()
    if root.is_dir():
        for path in sorted(root.rglob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(data, dict):
                continue
            extra = data.get("extra") or {}
            if not isinstance(extra, dict):
                extra = {}
            mode = extra.get("lab_app_mode") or {}
            if not isinstance(mode, dict):
                mode = {}
            rel = path.relative_to(root)
            lab_rel = str(extra.get("lab_rel") or rel.with_suffix("").as_posix())
            row_lane = str(mode.get("lane") or (rel.parts[0] if rel.parts else ""))
            row_occ = str(mode.get("occupancy") or "")
            desc = str(extra.get("lab_description") or "")
            blob = " ".join([lab_rel, row_lane, row_occ, desc]).lower()
            if q and q not in blob:
                continue
            if occ and occ != row_occ.lower():
                continue
            if lane_f and lane_f != row_lane.lower():
                continue
            rows.append(
                {
                    "id": lab_rel,
                    "kind": "lab",
                    "lane": row_lane,
                    "occupancy": row_occ,
                    "handoff": list(mode.get("handoff") or []),
                    "description": desc,
                    "widgets": _linear_labels(extra),
                    "default_view": str(mode.get("default_view") or "graph"),
                }
            )
    blocks = _blocks_root()
    if blocks.is_dir():
        for path in sorted(blocks.glob("*.json")):
            bid = path.stem
            blob = bid.lower()
            if q and q not in blob:
                continue
            if occ or lane_f:
                continue
            rows.append(
                {
                    "id": bid,
                    "kind": "block",
                    "lane": "",
                    "occupancy": "",
                    "handoff": [],
                    "description": "Studio subgraph blueprint (not a Queue graph).",
                    "widgets": [],
                    "default_view": "graph",
                }
            )
    return rows


def template_combo_labels() -> list[str]:
    """App combo: auto plus every lab_rel.

    Returns:
        ``auto`` followed by shipped lab ids.
    """
    ids = [row["id"] for row in list_templates() if row.get("kind") == "lab"]
    return [AUTO, *ids]


def describe_template(stem: str) -> dict[str, Any]:
    """One lab App, or a studio-block id.

    Args:
        stem: `_lab`-relative id or block stem.

    Returns:
        Description mapping with ``ok`` True, or ``{"ok": False, "error": ...}``.
    """
    text = normalize_stem(stem)
    loaded = load_lab_graph(text)
    if loaded is not None:
        path, data = loaded
        extra = data.get("extra") or {}
        if not isinstance(extra, dict):
            extra = {}
        mode = extra.get("lab_app_mode") or {}
        if not isinstance(mode, dict):
            mode = {}
        mcp = extra.get("lab_mcp") or {}
        if not isinstance(mcp, dict):
            mcp = {}
        try:
            rel_path = str(path.relative_to(_repo_root()))
        except ValueError:
            rel_path = str(path)
        return {
            "ok": True,
            "id": str(extra.get("lab_rel") or data.get("id") or path.stem),
            "kind": "lab",
            "path": rel_path,
            "lab_note": str(extra.get("lab_note") or ""),
            "description": str(extra.get("lab_description") or ""),
            "occupancy": mode.get("occupancy"),
            "lane": mode.get("lane"),
            "handoff": list(mode.get("handoff") or []),
            "widgets": _linear_labels(extra),
            "lab_mcp": mcp,
            "default_view": str(mode.get("default_view") or "graph"),
        }
    block = _blocks_root() / f"{text}.json"
    if block.is_file():
        return {
            "ok": True,
            "id": text,
            "kind": "block",
            "path": str(block.relative_to(_repo_root())),
            "description": "Studio subgraph blueprint (not a Queue graph).",
            "occupancy": "",
            "lane": "",
            "handoff": [],
            "widgets": [],
            "lab_mcp": {},
            "default_view": "graph",
        }
    return {"ok": False, "error": f"unknown template {stem}"}


def _brief_has(brief: str, token: str) -> bool:
    """True when token appears in the brief without matching inside words.

    Args:
        brief: Operator brief.
        token: Heuristic token (may include spaces, colons, or hyphens).

    Returns:
        Whether the token matches as a whole word (or substring for punctuated tokens).
    """
    text = (brief or "").lower()
    needle = token.lower()
    if not needle:
        return False
    if any(ch in needle for ch in (":", "-", " ")):
        return needle in text
    return re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", text) is not None


def pick_template(brief: str, template: str = AUTO) -> str:
    """Resolve auto/heuristic or an explicit lab_rel.

    Args:
        brief: Operator brief used for keyword matching.
        template: Explicit lab_rel, or ``auto``.

    Returns:
        `_lab`-relative id.

    Raises:
        ForgeError: Explicit template is unknown.
    """
    requested = (template or AUTO).strip()
    if requested and requested.lower() not in {AUTO, "custom", ""}:
        rel = normalize_stem(requested)
        if load_lab_graph(rel) is None:
            raise ForgeError(f"unknown template {requested}")
        return rel
    for token, rel in _TEMPLATE_RULES:
        if _brief_has(brief, token) and load_lab_graph(rel) is not None:
            return rel
    return DEFAULT_TEMPLATE


def _widget_index(node: Mapping[str, Any], name: str) -> int | None:
    """Resolve a widget index from EZ order or core Comfy maps.

    Args:
        node: Serialized node.
        name: Widget name.

    Returns:
        Index into ``widgets_values``, or None.
    """
    ntype = str(node.get("type") or "")
    order = EZ_WIDGET_ORDER.get(ntype)
    if order and name in order:
        return order.index(name)
    core = CORE_WIDGET_INDEX.get(ntype)
    if core and name in core:
        return core[name]
    return None


def _nodes_by_id(graph: Mapping[str, Any]) -> dict[int, dict[str, Any]]:
    """Index graph nodes by integer id.

    Args:
        graph: Serialized Comfy graph.

    Returns:
        ``id → node`` mapping; invalid ids are skipped.
    """
    out: dict[int, dict[str, Any]] = {}
    for node in graph.get("nodes") or []:
        if not isinstance(node, dict):
            continue
        try:
            nid = int(node["id"])
        except (KeyError, TypeError, ValueError):
            continue
        out[nid] = node
    return out


def _set_widget_value(node: dict[str, Any], index: int, value: Any) -> None:
    """Write one ``widgets_values`` slot, preserving the current Python type.

    Args:
        node: Serialized node (mutated).
        index: Widget index.
        value: New value (coerced to the current type when possible).
    """
    values = node.get("widgets_values")
    if isinstance(values, dict):
        return
    if not isinstance(values, list):
        values = []
        node["widgets_values"] = values
    while len(values) <= index:
        values.append(None)
    current = values[index]
    if isinstance(current, bool):
        values[index] = _as_bool(value)
    elif isinstance(current, int) and not isinstance(current, bool):
        try:
            values[index] = int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            values[index] = value
    elif isinstance(current, float):
        try:
            values[index] = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            values[index] = value
    else:
        values[index] = value


def apply_slots(graph: dict[str, Any], slots: Mapping[str, Any] | None) -> dict[str, Any]:
    """Patch widgets_values for linearData names/labels and core Comfy widgets.

    Unknown keys raise ForgeError (no silent drop).

    Args:
        graph: Serialized Comfy graph (mutated).
        slots: Widget name/label → value.

    Returns:
        The same graph dict.

    Raises:
        ForgeError: Empty or unknown slot name.
    """
    if not slots:
        return graph
    extra = graph.get("extra") or {}
    if not isinstance(extra, dict):
        extra = {}
    linear = extra.get("linearData") or {}
    inputs = linear.get("inputs") if isinstance(linear, dict) else []
    if not isinstance(inputs, list):
        inputs = []
    nodes = _nodes_by_id(graph)
    for raw_key, value in slots.items():
        key = SLOT_ALIASES.get(str(raw_key).strip(), str(raw_key).strip())
        if not key:
            raise ForgeError("empty slot name")
        applied = 0
        for entry in inputs:
            if not isinstance(entry, list) or len(entry) < 2:
                continue
            try:
                nid = int(entry[0])
            except (TypeError, ValueError):
                continue
            widget_name = str(entry[1])
            config = entry[2] if len(entry) > 2 and isinstance(entry[2], dict) else {}
            label = str(config.get("label") or widget_name)
            if key not in {widget_name, label} and key.lower() not in {
                widget_name.lower(),
                label.lower(),
            }:
                continue
            node = nodes.get(nid)
            if node is None:
                continue
            index = _widget_index(node, widget_name)
            if index is None:
                continue
            _set_widget_value(node, index, value)
            applied += 1
        if applied == 0:
            for node in nodes.values():
                index = _widget_index(node, key)
                if index is None:
                    continue
                _set_widget_value(node, index, value)
                applied += 1
        if applied == 0:
            raise ForgeError(f"unknown slot {raw_key!r}")
    return graph


def restamp_identity(graph: dict[str, Any], *, origin: str, slug: str) -> dict[str, Any]:
    """Mark a clone as a generated `_user` graph. Keep source occupancy.

    Args:
        graph: Serialized Comfy graph (mutated).
        origin: Source lab_rel.
        slug: Destination stem.

    Returns:
        The same graph dict.
    """
    extra = graph.setdefault("extra", {})
    if not isinstance(extra, dict):
        extra = {}
        graph["extra"] = extra
    extra["lab_origin"] = origin
    extra["lab_rel"] = f"_user/{slug}"
    extra["lab_profile"] = f"_user/{slug}"
    extra["lab_generated"] = True
    extra["workflowRendererVersion"] = RENDERER
    graph["id"] = slug
    return graph


def validate_workflow(
    graph: Mapping[str, Any],
    *,
    dest: Path | None = None,
    slug: str = "",
) -> list[str]:
    """Return error strings. Empty means the graph may be written.

    Args:
        graph: Serialized Comfy graph.
        dest: Planned write path (refuses `_lab` and non-`_user`).
        slug: Optional slug to validate.

    Returns:
        Error messages; empty when the graph may be written.
    """
    errors: list[str] = []
    blob = json.dumps(graph, default=str)
    hit = _banned_hit(blob)
    if hit is not None:
        errors.append(f"banned string {hit!r}")
    extra = graph.get("extra") or {}
    if not isinstance(extra, dict):
        extra = {}
    renderer = str(extra.get("workflowRendererVersion") or "")
    if renderer != RENDERER:
        errors.append(f"workflowRendererVersion must be {RENDERER!r}")
    linear = extra.get("linearData") or {}
    inputs = linear.get("inputs") if isinstance(linear, dict) else None
    if isinstance(inputs, list):
        for entry in inputs:
            if not isinstance(entry, list) or not entry:
                continue
            stored = entry[0]
            if isinstance(stored, str) and ":" in stored:
                errors.append(f"colon widget id {stored!r}")
            elif not isinstance(stored, int) and not (
                isinstance(stored, str) and stored.lstrip("-").isdigit()
            ):
                errors.append(f"invalid linear input id {stored!r}")
    if slug:
        try:
            validate_slug(slug)
        except ForgeError as exc:
            errors.append(str(exc))
    if dest is not None:
        dest_s = str(dest.resolve()) if dest.exists() or dest.parent.exists() else str(dest)
        if "/_lab/" in dest_s.replace("\\", "/") or dest_s.endswith("/_lab"):
            errors.append("refusing to write under _lab")
        try:
            dest.resolve().relative_to(user_workflows_dir().resolve())
        except (ValueError, OSError):
            # dest parent may not exist yet; check lexical path
            if "_lab" in dest.parts:
                errors.append("refusing to write under _lab")
            user_parts = ("comfy-user", "default", "workflows", "_user")
            if tuple(dest.parts[-5:-1]) != user_parts and dest.parent.name != "_user":
                if "workflows" in dest.parts and "_user" not in dest.parts:
                    errors.append("refusing dest outside _user")
    return errors


def _dest_for(slug: str, as_app: bool) -> Path:
    """Destination path under live `_user/`.

    Args:
        slug: Validated stem.
        as_app: Write ``.app.json`` when true.

    Returns:
        Target file path.
    """
    suffix = ".app.json" if as_app else ".json"
    return user_workflows_dir() / f"{slug}{suffix}"


def _sibling_dest(slug: str, as_app: bool) -> Path:
    """The other suffix (``.json`` vs ``.app.json``) for the same slug.

    Args:
        slug: Validated stem.
        as_app: Current as_app flag.

    Returns:
        Sibling path with the opposite suffix.
    """
    return _dest_for(slug, not as_app)


def save_workflow(
    graph: dict[str, Any],
    *,
    slug: str,
    as_app: bool = True,
    overwrite: bool = False,
) -> Path:
    """Write `_user/<slug>.app.json` or `.json`. Never `_lab/`.

    Args:
        graph: Serialized Comfy graph.
        slug: Destination stem.
        as_app: Write ``.app.json`` when true.
        overwrite: Replace an existing file.

    Returns:
        Written path.

    Raises:
        ForgeError: Illegal slug, existing dest, or validation errors.
    """
    clean = validate_slug(slug)
    dest = _dest_for(clean, as_app)
    other = _sibling_dest(clean, as_app)
    if dest.exists() and not overwrite:
        raise ForgeError(f"already exists: {dest}")
    if other.exists() and not overwrite:
        raise ForgeError(f"already exists: {other}")
    errors = validate_workflow(graph, dest=dest, slug=clean)
    if errors:
        raise ForgeError("; ".join(errors))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    if overwrite and other.exists():
        other.unlink()
    return dest


def parse_plan(text: str) -> dict[str, Any] | None:
    """Parse planner JSON ``{template, slug, as_app, slots, reason}``.

    Args:
        text: Planner LLM output.

    Returns:
        Parsed object, or None when JSON is missing or not a dict.
    """
    blob = (text or "").strip()
    start = blob.find("{")
    end = blob.rfind("}")
    candidate = blob[start : end + 1] if start >= 0 and end > start else blob
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return data


def _complete(system: str, user: str) -> tuple[str, str]:
    """GPU sidecar / occupancy-aware 4B via prompt-enhance. Fail-soft.

    Args:
        system: System prompt.
        user: User message.

    Returns:
        ``(text, reason)``; empty text when llama.cpp is unavailable.
    """
    try:
        custom = str(_repo_root() / "custom_nodes")
        if custom not in sys.path:
            sys.path.insert(0, custom)
        from ez_prompt_enhance.client import complete as llama_complete

        text, reason = llama_complete(system, user, max_tokens=400, temperature=0.1)
        return (text or "").strip(), (reason or "")
    except Exception as exc:  # noqa: BLE001 — fail-soft
        _log(f"prompt enhance client unavailable: {exc}")
        return "", "llama.cpp unavailable"


def _plan_from_llm(brief: str) -> tuple[dict[str, Any] | None, str]:
    """Ask the planner GGUF for template/slug/slots.

    Args:
        brief: Operator brief.

    Returns:
        ``(plan, status)``; plan is None on passthrough.
    """
    catalog = [
        {"id": row["id"], "occupancy": row["occupancy"], "description": row["description"]}
        for row in list_templates()
        if row.get("kind") == "lab"
    ]
    user = (
        f"Brief:\n{brief.strip()}\n\n"
        f"Catalog (id, occupancy, description):\n{json.dumps(catalog[:80])}\n"
        "JSON only."
    )
    text, reason = _complete(load_prompt("planner"), user)
    plan = parse_plan(text) if text else None
    return plan, reason or ("ok" if plan else "llm passthrough")


def clone_template(stem: str) -> tuple[str, dict[str, Any]]:
    """Deep-copy a shipped lab graph. Blocks are refused.

    Args:
        stem: `_lab`-relative id.

    Returns:
        ``(origin_id, graph_copy)``.

    Raises:
        ForgeError: Unknown template or subgraph blueprint.
    """
    described = describe_template(stem)
    if not described.get("ok"):
        raise ForgeError(str(described.get("error") or f"unknown template {stem}"))
    if described.get("kind") == "block":
        raise ForgeError(f"{stem} is a subgraph blueprint, not a Queue graph")
    loaded = load_lab_graph(stem)
    if loaded is None:
        raise ForgeError(f"unknown template {stem}")
    _path, data = loaded
    origin = str(described.get("id") or normalize_stem(stem))
    return origin, copy.deepcopy(data)


def _planner_result(
    brief: str, requested: str, *, use_llm: bool
) -> tuple[dict[str, Any] | None, str, str]:
    """Run the GGUF planner or keep the keyword-heuristic status.

    Args:
        brief: Operator brief.
        requested: Template widget (``auto`` / lab_rel).
        use_llm: When false, skip the planner.

    Returns:
        ``(plan, status, reason)``.
    """
    if not (use_llm and requested.lower() in {AUTO, "custom", ""}):
        return None, "heuristic", "keyword heuristic"
    plan, llm_status = _plan_from_llm(brief)
    if plan is not None:
        return plan, llm_status or "ok", str(plan.get("reason") or "planner")
    return None, llm_status or "llm passthrough", "keyword heuristic"


def _choose_template(
    brief: str, requested: str, plan: dict[str, Any] | None
) -> str:
    """Pick a lab stem, preferring a valid planner template.

    Args:
        brief: Operator brief.
        requested: Template widget.
        plan: Planner JSON, or None.

    Returns:
        Template stem / lab_rel.
    """
    chosen = pick_template(brief, requested)
    if plan is not None and requested.lower() in {AUTO, "custom", ""}:
        planned = normalize_stem(str(plan.get("template") or ""))
        if planned and load_lab_graph(planned) is not None:
            return planned
    return chosen


def _merged_slots(
    graph: dict[str, Any],
    plan: dict[str, Any] | None,
    slots: Mapping[str, Any] | None,
    brief: str,
) -> dict[str, Any]:
    """Combine planner slots, operator slots, and a prompt fill.

    Args:
        graph: Cloned lab graph.
        plan: Planner JSON, or None.
        slots: Extra widget patches.
        brief: Operator brief.

    Returns:
        Slot mapping (possibly empty).
    """
    merged: dict[str, Any] = {}
    if plan is not None and isinstance(plan.get("slots"), dict):
        merged.update(plan["slots"])
    if slots:
        merged.update(dict(slots))
    extra = graph.get("extra") or {}
    labels = _linear_labels(extra if isinstance(extra, dict) else {})
    has_prompt = any(name.lower() in {"prompt", "brief", "message"} for name in labels)
    if brief and has_prompt and "prompt" not in merged and "Prompt" not in merged:
        merged["prompt"] = brief
    return merged


def _choose_slug(
    slug: str, plan: dict[str, Any] | None, brief: str, origin: str
) -> str:
    """Resolve a `_user` stem.

    Args:
        slug: Operator slug widget.
        plan: Planner JSON, or None.
        brief: Operator brief.
        origin: Template id.

    Returns:
        Validated slug.
    """
    want = slug or (str(plan.get("slug") or "") if plan is not None else "") or slugify(
        brief or origin.replace("/", "-")
    )
    return validate_slug(want)


def _choose_as_app(
    as_app: object, plan: dict[str, Any] | None, graph: Mapping[str, Any]
) -> bool:
    """Resolve whether to write ``.app.json``.

    Args:
        as_app: Widget value, or None for planner/default_view.
        plan: Planner JSON, or None.
        graph: Cloned lab graph.

    Returns:
        True when the dest should be an App.
    """
    if as_app is None:
        if plan is not None and "as_app" in plan:
            return _as_bool(plan.get("as_app"))
        return _default_view(graph) == "app"
    return _as_bool(as_app)


def _enable_app_mode(graph: dict[str, Any]) -> None:
    """Stamp App Mode extras on a cloned graph.

    Args:
        graph: Workflow dict (mutated).
    """
    mode = graph.setdefault("extra", {}).setdefault("lab_app_mode", {})
    if isinstance(mode, dict):
        mode["default_view"] = "app"
        mode["enabled"] = True
    graph["extra"]["linearMode"] = True


def generate_app(
    brief: str,
    *,
    template: str = AUTO,
    slug: str = "",
    as_app: object = None,
    overwrite: object = False,
    slots: Mapping[str, Any] | None = None,
    use_llm: bool = True,
) -> ForgeResult:
    """Pick a lab template, clone, apply slots, write `_user/`.

    Args:
        brief: Operator brief.
        template: Explicit lab_rel or ``auto``.
        slug: Destination stem; empty uses planner or slugify.
        as_app: Write ``.app.json`` when true; None uses planner/default_view.
        overwrite: Replace an existing `_user` graph.
        slots: Extra widget patches applied after the planner slots.
        use_llm: When false, skip the planner GGUF.

    Returns:
        ``ForgeResult`` with path on success or ``error`` on refusal.
    """
    text = (brief or "").strip()
    requested = (template or AUTO).strip() or AUTO
    plan, status, reason = _planner_result(text, requested, use_llm=use_llm)
    try:
        chosen = _choose_template(text, requested, plan)
        origin, graph = clone_template(chosen)
        merged = _merged_slots(graph, plan, slots, text)
        if merged:
            apply_slots(graph, merged)
        clean = _choose_slug(slug, plan, text, origin)
        want_app = _choose_as_app(as_app, plan, graph)
        restamp_identity(graph, origin=origin, slug=clean)
        if want_app:
            _enable_app_mode(graph)
        dest = save_workflow(
            graph,
            slug=clean,
            as_app=want_app,
            overwrite=_as_bool(overwrite),
        )
    except ForgeError as exc:
        return ForgeResult(ok=False, error=str(exc), status=status, reason=reason)
    widgets = _linear_labels(graph.get("extra") or {})
    return ForgeResult(
        ok=True,
        path=str(dest),
        template=origin,
        occupancy=_occupancy_of(graph),
        widgets=widgets,
        slug=clean,
        as_app=want_app,
        reason=reason,
        status=status,
        graph=graph,
    )
