"""Deterministic audio/music splice for Audio Rack.

Hermetic stdlib. Loads JSON catalogs from ``audio/`` and composes ACE-Step
tags plus lyrics form. No LLM.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Catalog paths, combo sentinels, flavor ids, widget axes, and lazy JSON caches.
AUDIO_DIR = Path(__file__).resolve().parent
AXES_PATH = AUDIO_DIR / "axes.json"
RECIPES_PATH = AUDIO_DIR / "recipes.json"
NONE = "none"

# Audio flavor ids (ACE vocal, ACE instrumental, podcast bed).
FLAVOR_ACE_VOCAL = "ace_vocal"
FLAVOR_ACE_INSTRUMENTAL = "ace_instrumental"
FLAVOR_PODCAST_BED = "podcast_bed"

FLAVORS = (
    FLAVOR_ACE_VOCAL,
    FLAVOR_ACE_INSTRUMENTAL,
    FLAVOR_PODCAST_BED,
)

INSTRUMENTAL_TAGS = "instrumental, no vocals"
DEFAULT_INST_FORM = "[inst]"

# Operator widget order (production desk). Splice order lives on axes.json.
WIDGET_AXIS_ORDER = (
    "genre_style",
    "tempo_groove",
    "drums_rhythm",
    "bass_low_end",
    "harmony_mode",
    "instruments_texture",
    "vocal_identity",
    "arrangement_form",
    "mix_production",
    "space_ambience",
    "sound_design_fx",
    "mood_energy",
    "use_case",
)

_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,47}$")

_AXES: dict[str, dict[str, Any]] | None = None
_CATALOGS: dict[str, list[dict[str, Any]]] | None = None
_BY_ID: dict[str, dict[str, Any]] | None = None
_RECIPES: dict[str, dict[str, Any]] | None = None


@dataclass(frozen=True)
class DroppedPick:
    """One technique dropped by conflict or flavor filter."""

    technique_id: str
    reason: str


@dataclass(frozen=True)
class SpliceResult:
    """Composed ACE tags, lyrics form, and audit trail."""

    tags: str
    lyrics: str
    used: tuple[str, ...] = ()
    dropped: tuple[DroppedPick, ...] = ()
    notes: str = ""
    bpm: str = ""


def _collapse_spaces(text: str) -> str:
    """Fold runs of space and extra blank lines.

    Args:
        text: Raw clause text.

    Returns:
        Stripped text with compact whitespace.
    """
    cleaned = re.sub(r"[ \t]+", " ", text)
    cleaned = re.sub(r" +([,.;:])", r"\1", cleaned)
    cleaned = re.sub(r"\s+\n", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _as_bool(value: object, default: bool = True) -> bool:
    """Parse a catalog flag.

    Args:
        value: JSON bool, number, or yes/no string.
        default: Fallback when ``value`` is None or unrecognized.

    Returns:
        Parsed boolean.
    """
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        cleaned = value.strip().lower()
        if cleaned in {"1", "true", "yes", "on"}:
            return True
        if cleaned in {"0", "false", "no", "off"}:
            return False
    return default


def _string_list(entry: dict[str, Any], field: str) -> list[str]:
    """Read a string or list-of-strings catalog field.

    Args:
        entry: Technique object.
        field: Key such as ``conflicts``.

    Returns:
        Non-empty stripped strings.
    """
    raw = entry.get(field) or []
    if isinstance(raw, str):
        return [raw.strip()] if raw.strip() else []
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        text = str(item).strip()
        if text:
            out.append(text)
    return out


def _load_json(path: Path) -> Any:
    """Read a UTF-8 JSON file.

    Args:
        path: Catalog path under ``audio/``.

    Returns:
        Parsed JSON value.
    """
    return json.loads(path.read_text(encoding="utf-8"))


def load_axes() -> dict[str, dict[str, Any]]:
    """Load axis metadata (id -> fields).

    Returns:
        Axis id to metadata mapping, file order preserved.
    """
    global _AXES
    if _AXES is None:
        raw = _load_json(AXES_PATH)
        if not isinstance(raw, dict):
            raise ValueError("axes.json must be an object")
        axes: dict[str, dict[str, Any]] = {}
        for key, value in raw.items():
            if not isinstance(value, dict):
                raise ValueError(f"axis {key} must be an object")
            axes[str(key)] = dict(value)
        _AXES = axes
    return _AXES


def axis_ids() -> tuple[str, ...]:
    """Return axis ids in widget order.

    Returns:
        The 13 Audio Rack axis ids.
    """
    axes = load_axes()
    ordered = [aid for aid in WIDGET_AXIS_ORDER if aid in axes]
    extra = [aid for aid in axes if aid not in ordered]
    return tuple(ordered + extra)


def _catalog_path(axis_id: str) -> Path:
    """Resolve the JSON file for one axis.

    Args:
        axis_id: Axis key from ``axes.json``.

    Returns:
        Path next to this module.
    """
    meta = load_axes().get(axis_id) or {}
    filename = str(meta.get("file") or f"{axis_id}.json")
    return AUDIO_DIR / filename


def load_axis(axis_id: str) -> list[dict[str, Any]]:
    """Load one axis catalog (list of technique objects).

    Args:
        axis_id: Axis key from axes.json.

    Returns:
        Technique dicts in file order.

    Raises:
        KeyError: unknown axis.
        ValueError: catalog is not a list of objects.
    """
    if axis_id not in load_axes():
        raise KeyError(f"unknown audio axis {axis_id!r}")
    catalogs = _ensure_catalogs()
    return catalogs[axis_id]


def _ensure_catalogs() -> dict[str, list[dict[str, Any]]]:
    """Load every axis catalog once and index techniques by id.

    Returns:
        Axis id to technique list mapping (cached).
    """
    global _CATALOGS, _BY_ID
    if _CATALOGS is not None and _BY_ID is not None:
        return _CATALOGS
    catalogs: dict[str, list[dict[str, Any]]] = {}
    by_id: dict[str, dict[str, Any]] = {}
    for axis_id, meta in load_axes().items():
        path = _catalog_path(axis_id)
        raw = _load_json(path) if path.is_file() else []
        if not isinstance(raw, list):
            raise ValueError(f"{path.name} must be a list")
        rows: list[dict[str, Any]] = []
        for item in raw:
            if not isinstance(item, dict):
                raise ValueError(f"{path.name} entries must be objects")
            entry = dict(item)
            entry["axis"] = axis_id
            entry["_splice_order"] = int(meta.get("splice_order") or 0)
            entry["_vocal_include"] = _as_bool(meta.get("vocal_include"), True)
            entry["_instrumental_include"] = _as_bool(
                meta.get("instrumental_include"), True
            )
            entry["_podcast_include"] = _as_bool(meta.get("podcast_include"), True)
            entry["_bpm_axis"] = bool(meta.get("bpm_axis"))
            entry["_form_axis"] = bool(meta.get("form_axis"))
            entry["_vocal_axis"] = bool(meta.get("vocal_axis"))
            tid = str(entry.get("id") or "").strip()
            if tid:
                by_id[tid] = entry
            rows.append(entry)
        catalogs[axis_id] = rows
    _CATALOGS = catalogs
    _BY_ID = by_id
    return catalogs


def technique(technique_id: str) -> dict[str, Any] | None:
    """Return one technique by id, or None.

    Args:
        technique_id: Catalog id.

    Returns:
        Technique dict including axis metadata, or None.
    """
    _ensure_catalogs()
    assert _BY_ID is not None
    key = str(technique_id or "").strip()
    if not key or key == NONE:
        return None
    return _BY_ID.get(key)


def combo_ids(axis_id: str) -> list[str]:
    """Combo choices for one axis: none first, then catalog ids.

    Args:
        axis_id: Axis key.

    Returns:
        Combo strings.
    """
    rows = load_axis(axis_id)
    ids = [str(row.get("id") or "").strip() for row in rows]
    return [NONE, *[item for item in ids if item]]


def load_recipes() -> dict[str, dict[str, Any]]:
    """Load named starter splices.

    Returns:
        Recipe id to object mapping.
    """
    global _RECIPES
    if _RECIPES is None:
        if not RECIPES_PATH.is_file():
            _RECIPES = {}
            return _RECIPES
        raw = _load_json(RECIPES_PATH)
        if not isinstance(raw, list):
            raise ValueError("recipes.json must be a list")
        recipes: dict[str, dict[str, Any]] = {}
        for item in raw:
            if not isinstance(item, dict):
                continue
            rid = str(item.get("id") or "").strip()
            if rid:
                recipes[rid] = dict(item)
        _RECIPES = recipes
    return _RECIPES


def recipe_combo_ids() -> list[str]:
    """Combo choices for recipes: none first.

    Returns:
        Recipe ids with none first.
    """
    return [NONE, *load_recipes().keys()]


def apply_recipe(recipe_id: str, picks: dict[str, str]) -> dict[str, str]:
    """Fill empty axis picks from a named recipe. Explicit picks win.

    Args:
        recipe_id: Recipe id or none.
        picks: Axis id -> technique id (may include none).

    Returns:
        New picks mapping.
    """
    out = {key: str(value or NONE).strip() or NONE for key, value in picks.items()}
    rid = str(recipe_id or "").strip()
    if not rid or rid == NONE:
        return out
    recipe = load_recipes().get(rid)
    if not recipe:
        return out
    axes = recipe.get("axes") or {}
    if not isinstance(axes, dict):
        return out
    for axis_id in axis_ids():
        current = out.get(axis_id, NONE)
        if current and current != NONE:
            continue
        fill = str(axes.get(axis_id) or "").strip()
        if fill and fill != NONE:
            out[axis_id] = fill
    return out


def reset_audio_caches_for_tests() -> None:
    """Drop loaded catalogs so tests can swap files."""
    global _AXES, _CATALOGS, _BY_ID, _RECIPES
    _AXES = None
    _CATALOGS = None
    _BY_ID = None
    _RECIPES = None


def _normalize_pick(value: object) -> str:
    """Coerce a combo pick to a catalog id or ``none``.

    Args:
        value: Widget value.

    Returns:
        Stripped id, or ``none`` when empty.
    """
    raw = value if isinstance(value, str) else str(value or NONE)
    cleaned = raw.strip() or NONE
    return cleaned


def _is_instrumental(flavor: str) -> bool:
    """True for ACE instrumental and podcast-bed flavors.

    Args:
        flavor: Splice flavor id.

    Returns:
        Whether vocals are omitted.
    """
    return flavor in {FLAVOR_ACE_INSTRUMENTAL, FLAVOR_PODCAST_BED}


def _is_podcast(flavor: str) -> bool:
    """True for the podcast-bed flavor.

    Args:
        flavor: Splice flavor id.

    Returns:
        Whether podcast-bed filters apply.
    """
    return flavor == FLAVOR_PODCAST_BED


def _vocal_ok(entry: dict[str, Any]) -> bool:
    """Whether a technique may appear on ACE vocal splices.

    Args:
        entry: Technique object.

    Returns:
        ``vocal_ok`` flag, default True.
    """
    return _as_bool(entry.get("vocal_ok"), True)


def _instrumental_ok(entry: dict[str, Any]) -> bool:
    """Whether a technique may appear on ACE instrumental splices.

    Args:
        entry: Technique object.

    Returns:
        ``instrumental_ok`` flag, default True.
    """
    return _as_bool(entry.get("instrumental_ok"), True)


def _podcast_ok(entry: dict[str, Any]) -> bool:
    """Whether a technique may appear on podcast-bed splices.

    Args:
        entry: Technique object.

    Returns:
        ``podcast_ok`` flag, default True.
    """
    return _as_bool(entry.get("podcast_ok"), True)


def _flavor_keeps(entry: dict[str, Any], flavor: str) -> str:
    """Return empty if kept, else drop reason.

    Args:
        entry: Selected technique (with axis metadata).
        flavor: Splice flavor id.

    Returns:
        Empty string when the pick survives, otherwise an operator reason.
    """
    if _is_instrumental(flavor) and bool(entry.get("_vocal_axis")):
        return "vocal omitted on instrumental"
    if not bool(entry.get("_vocal_include", True)) and flavor == FLAVOR_ACE_VOCAL:
        return "not a vocal-axis technique"
    if (
        not bool(entry.get("_instrumental_include", True))
        and flavor == FLAVOR_ACE_INSTRUMENTAL
    ):
        return "vocal omitted on instrumental"
    if not bool(entry.get("_podcast_include", True)) and _is_podcast(flavor):
        return "vocal omitted on instrumental"
    if flavor == FLAVOR_ACE_VOCAL and not _vocal_ok(entry):
        return "not a vocal technique"
    if flavor == FLAVOR_ACE_INSTRUMENTAL and not _instrumental_ok(entry):
        return "not an instrumental technique"
    if _is_podcast(flavor) and not _podcast_ok(entry):
        return "not a podcast-bed technique"
    return ""


def _resolve_conflicts(
    entries: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[DroppedPick]]:
    """Later splice-order wins when two picks conflict.

    Args:
        entries: Selected techniques, any order.

    Returns:
        Survivors and dropped picks.
    """
    ordered = sorted(entries, key=lambda row: int(row.get("_splice_order") or 0))
    dropped: list[DroppedPick] = []
    kept: list[dict[str, Any]] = []
    for entry in ordered:
        tid = str(entry.get("id") or "")
        conflicts = set(_string_list(entry, "conflicts"))
        losers: list[int] = []
        conflicted = False
        for idx, other in enumerate(kept):
            oid = str(other.get("id") or "")
            other_conflicts = set(_string_list(other, "conflicts"))
            if tid in other_conflicts or oid in conflicts:
                losers.append(idx)
                conflicted = True
        if conflicted:
            for idx in reversed(losers):
                loser = kept.pop(idx)
                dropped.append(
                    DroppedPick(
                        str(loser.get("id") or ""),
                        f"conflicts with {tid}",
                    )
                )
        kept.append(entry)
    return kept, dropped


def _join_tags(parts: list[str]) -> str:
    """Join tag fragments, comma-split, casefold-deduped.

    Args:
        parts: Tag fragments in splice order.

    Returns:
        One comma-separated ACE tags line.
    """
    seen: set[str] = set()
    out: list[str] = []
    for part in parts:
        for frag in part.split(","):
            item = " ".join(str(frag).split()).strip().strip(",")
            key = item.lower()
            if not item or key in seen:
                continue
            seen.add(key)
            out.append(item)
    return ", ".join(out)


def _bpm_token(entry: dict[str, Any]) -> str:
    """BPM token for a tempo-axis technique.

    Args:
        entry: Technique object.

    Returns:
        ``bpm`` field, else empty.
    """
    token = str(entry.get("bpm") or "").strip()
    if token:
        return token
    if bool(entry.get("_bpm_axis")):
        tags = str(entry.get("tags") or "")
        match = re.search(r"\b(\d{2,3})\s*bpm\b", tags, flags=re.I)
        if match:
            return f"{match.group(1)} bpm"
    return ""


def _lyrics_form(entry: dict[str, Any], flavor: str) -> str:
    """Return the lyrics skeleton for a form-axis technique.

    Args:
        entry: Technique object.
        flavor: Splice flavor id.

    Returns:
        Form text, or empty when this is not a form axis.
    """
    if not bool(entry.get("_form_axis")):
        return ""
    if _is_instrumental(flavor):
        inst = str(entry.get("lyrics_form_inst") or "").strip()
        return inst or DEFAULT_INST_FORM
    return str(entry.get("lyrics_form") or "").strip()


def _force_instrumental_tags(tags: str) -> str:
    """Ensure instrumental ACE tags include no-vocals needles.

    Args:
        tags: Joined tags line.

    Returns:
        Tags with ``instrumental, no vocals`` appended when missing.
    """
    blob = tags.lower()
    extra: list[str] = []
    if "instrumental" not in blob:
        extra.append("instrumental")
    if "no vocals" not in blob:
        extra.append("no vocals")
    if not extra:
        return tags
    if tags.strip():
        return f"{tags.rstrip(', ')}, {', '.join(extra)}"
    return INSTRUMENTAL_TAGS


def splice(
    picks: dict[str, str] | None = None,
    *,
    flavor: str = FLAVOR_ACE_VOCAL,
    brief: str = "",
    recipe: str = NONE,
) -> SpliceResult:
    """Compose selected techniques into ACE tags and lyrics form.

    Args:
        picks: Axis id -> technique id. Missing axes are none.
        flavor: ace_vocal / ace_instrumental / podcast_bed.
        brief: Optional lyrics seed. Ignored on instrumental flavors.
        recipe: Optional named splice; fills none axes only.

    Returns:
        SpliceResult with tags, lyrics, used ids, dropped reasons, and bpm.
    """
    flavor_key = str(flavor or FLAVOR_ACE_VOCAL).strip() or FLAVOR_ACE_VOCAL
    if flavor_key not in FLAVORS:
        flavor_key = FLAVOR_ACE_VOCAL
    raw_picks = {aid: NONE for aid in axis_ids()}
    if picks:
        for key, value in picks.items():
            if key in raw_picks:
                raw_picks[key] = _normalize_pick(value)
    raw_picks = apply_recipe(recipe, raw_picks)

    selected: list[dict[str, Any]] = []
    dropped: list[DroppedPick] = []
    for axis_id, tid in raw_picks.items():
        if not tid or tid == NONE:
            continue
        entry = technique(tid)
        if entry is None:
            dropped.append(DroppedPick(tid, "unknown technique"))
            continue
        selected.append(entry)

    kept, conflict_drops = _resolve_conflicts(selected)
    dropped.extend(conflict_drops)

    survivors: list[dict[str, Any]] = []
    for entry in kept:
        reason = _flavor_keeps(entry, flavor_key)
        if reason:
            dropped.append(DroppedPick(str(entry.get("id") or ""), reason))
            continue
        survivors.append(entry)
    survivors.sort(key=lambda row: int(row.get("_splice_order") or 0))

    tag_parts: list[str] = []
    form_parts: list[str] = []
    bpm = ""
    for entry in survivors:
        if bool(entry.get("_form_axis")):
            form = _lyrics_form(entry, flavor_key)
            if form:
                form_parts.append(form)
            continue
        fragment = str(entry.get("tags") or "").strip()
        if fragment:
            tag_parts.append(fragment)
        if bool(entry.get("_bpm_axis")):
            bpm = _bpm_token(entry)

    tags = _join_tags(tag_parts)
    if _is_instrumental(flavor_key):
        tags = _force_instrumental_tags(tags)

    brief_text = (brief or "").strip()
    if _is_instrumental(flavor_key):
        lyrics = "\n\n".join(form_parts).strip() or DEFAULT_INST_FORM
        if brief_text:
            dropped.append(DroppedPick("brief", "brief omitted on instrumental"))
    else:
        bits = [brief_text, *form_parts]
        lyrics = "\n\n".join(item for item in bits if item).strip()

    notes = "; ".join(f"{item.technique_id}: {item.reason}" for item in dropped)
    used = tuple(str(entry.get("id") or "") for entry in survivors if entry.get("id"))
    return SpliceResult(
        tags=tags,
        lyrics=lyrics,
        used=used,
        dropped=tuple(dropped),
        notes=notes,
        bpm=bpm,
    )


def format_notes(result: SpliceResult) -> str:
    """Operator-facing one-line notes.

    Args:
        result: Splice output.

    Returns:
        Notes string, or empty.
    """
    bits: list[str] = []
    if result.bpm:
        bits.append(f"BPM: {result.bpm}")
    if result.notes:
        bits.append(result.notes)
    return "; ".join(bits)


def validate_id(value: str) -> bool:
    """Return True when value matches the catalog id regex.

    Args:
        value: Candidate id.

    Returns:
        Whether the id is legal.
    """
    return bool(_ID_RE.fullmatch(value or ""))


def bpm_tokens() -> tuple[str, ...]:
    """Unique BPM tokens from the tempo axis.

    Returns:
        Tokens in first-seen catalog order. Empty when the axis is missing.
    """
    try:
        rows = load_axis("tempo_groove")
    except KeyError:
        return ()
    seen: set[str] = set()
    ordered: list[str] = []
    for row in rows:
        token = _bpm_token(row)
        if not token or token in seen:
            continue
        seen.add(token)
        ordered.append(token)
    return tuple(ordered)


def recipe_axis_exemplars() -> dict[str, dict[str, Any]]:
    """First recipe fill per axis (recipe file order).

    Returns:
        Axis id to technique dict. Axes the recipes never fill are omitted.
    """
    out: dict[str, dict[str, Any]] = {}
    for recipe in load_recipes().values():
        axes = recipe.get("axes") or {}
        if not isinstance(axes, dict):
            continue
        for axis_id, raw_id in axes.items():
            key = str(axis_id or "").strip()
            if not key or key in out:
                continue
            entry = technique(str(raw_id or "").strip())
            if entry is None:
                continue
            out[key] = entry
    return out


def _clip_clause(text: str, limit: int = 18) -> str:
    """Keep an exemplar clause short enough for the 4B context.

    Args:
        text: Catalog clause.
        limit: Maximum word count.

    Returns:
        Original text, or a truncated clause ending in an ellipsis.
    """
    cleaned = _collapse_spaces(text)
    words = cleaned.split()
    if len(words) <= limit:
        return cleaned
    return " ".join(words[:limit]).rstrip(".,;:") + "…"


def addendum_kind(system_name: str = "", mode: str = "") -> str:
    """Classify a Prompt Enhance stem/mode for the audio addendum.

    Args:
        system_name: Prompt file stem (``ace_tags``, ``klein_t2i``, …).
        mode: Optional node mode (``vocal``, ``instrumental``, …).

    Returns:
        One of ``skip``, ``vocal``, ``instrumental``, or ``lyrics``.
    """
    name = (system_name or "").strip().lower()
    mode_key = (mode or "").strip().lower()
    if name.startswith("ace_lyrics") or name == "ace_lyrics":
        return "lyrics"
    if name.startswith("ace_instrumental") or mode_key == "instrumental":
        return "instrumental"
    if name.startswith("ace_"):
        return "vocal"
    return "skip"


def audio_language_addendum(system_name: str = "", mode: str = "") -> str:
    """Compact Audio Rack language block for ACE Prompt Enhance.

    Generated from live catalogs so labels, recipes, and BPM tokens cannot
    drift. Exemplar clauses are truncated. Visual stems return empty.

    Args:
        system_name: Prompt file stem.
        mode: Optional node mode.

    Returns:
        Addendum text, or empty for non-ACE stems.
    """
    kind = addendum_kind(system_name, mode)
    if kind == "skip":
        return ""
    axes = load_axes()
    labels = [str(axes[aid].get("label") or aid) for aid in axis_ids() if aid in axes]
    recipe_labels = [
        str(row.get("label") or row.get("id") or "").strip()
        for row in load_recipes().values()
    ]
    recipe_labels = [item for item in recipe_labels if item]
    lines = [
        "Audio Rack language (professional music production; no living artists):",
        "Axes in splice order: " + "; ".join(labels) + ".",
        (
            "Write ACE-Step tags as comma-separated English. Genre first, then "
            "mood, two or three specific instruments, vocal type, production, "
            "BPM last. Prefer catalog labels. Not tag soup such as cinematic, "
            "8k, fire beat."
        ),
        (
            "Do not name living artists, living MCs, celebrity producers, or "
            "existing song titles. Do not write in the style of a living person."
        ),
        (
            "When the user's intent matches a named recipe, use that package's "
            "language adapted to their brief. Never import a second vocal "
            "identity or a second BPM."
        ),
    ]
    if recipe_labels:
        lines.append("Recipes: " + "; ".join(recipe_labels) + ".")
    exemplars = recipe_axis_exemplars()
    example_lines: list[str] = []
    for axis_id in axis_ids():
        entry = exemplars.get(axis_id)
        if entry is None:
            continue
        axis_label = str((axes.get(axis_id) or {}).get("label") or axis_id)
        clause = _clip_clause(str(entry.get("clause") or ""))
        if not clause:
            continue
        example_lines.append(f"- {axis_label}: {clause}")
    if example_lines:
        lines.append("Example clauses (adapt; do not copy scenery):")
        lines.extend(example_lines)
    if kind == "instrumental":
        lines.append(
            "Instrumental: always include the tags instrumental and no vocals. "
            "Structure belongs as empty-body markers such as [inst], [drop], "
            "[outro]. ACE-Step sings any free-text under a section marker."
        )
    elif kind == "lyrics":
        lines.append(
            "Lyrics: keep section tags the operator used. Short percussive "
            "lines, about 6–10 syllables. Original bars only."
        )
    else:
        lines.append(
            "Vocal tags: keep one vocal identity (dry booth, no autotune unless "
            "asked). Exactly one BPM. Do not emit lyrics or [verse] in tags."
        )
    tokens = bpm_tokens()
    if tokens:
        lines.append(
            "BPM tokens (exactly one when tempo is named): "
            + ", ".join(tokens)
            + "."
        )
    return "\n".join(lines)
