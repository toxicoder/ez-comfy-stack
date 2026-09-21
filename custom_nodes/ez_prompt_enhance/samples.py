"""Lab sample-prompt catalogs for App Mode dropdowns.

Hermetic stdlib. JSON lives next to the frontend under ``js/samples/`` so
Comfy can serve it from WEB_DIRECTORY. Combo values are short labels;
``run()`` resolves a label to the full recipe unless the choice is Custom.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

# Sample catalog paths, combo sentinel, and node-type → family mapping.
CUSTOM = "custom"
SAMPLES_DIR = Path(__file__).resolve().parent / "js" / "samples"
INDEX_NAME = "index.json"
SAMPLE_COUNT = 30
"""Default recipe count for family catalogs (plus Custom)."""
BACKGROUND_SWAP_COUNT = 100
"""Recipe count for stills/background-swap."""


def catalog_expected_count(catalog_id: str) -> int:
    """Return the required recipe count for a catalog stem.

    Args:
        catalog_id: Catalog file stem.

    Returns:
        Integer count excluding Custom.
    """
    cid = catalog_id.strip() if isinstance(catalog_id, str) else str(catalog_id or "")
    if cid == "klein_background_swap":
        return BACKGROUND_SWAP_COUNT
    return SAMPLE_COUNT

# Node type + mode widget → default sample catalog stem.
_FAMILY_FOR_MODE: dict[tuple[str, str], str] = {
    ("EZKleinPromptEnhance", "t2i"): "klein_t2i",
    ("EZKleinPromptEnhance", "edit"): "klein_clay_edit",
    ("EZKleinPromptEnhance", "identity"): "klein_identity",
    ("EZKleinPromptEnhance", "text_swap"): "klein_text_swap",
    ("EZKleinPromptEnhance", "background_swap"): "klein_background_swap",
    ("EZKleinPromptEnhance", "background_edit"): "klein_background_edit",
    ("EZWanPromptEnhance", "t2v"): "wan_t2v",
    ("EZWanPromptEnhance", "i2v"): "wan_i2v",
    ("EZWanPromptEnhance", "flf"): "wan_flf",
    ("EZWanPromptEnhance", "vace"): "wan_vace",
    ("EZWanPromptEnhance", "s2v"): "wan_i2v",
    ("EZLTXPromptEnhance", "t2v"): "ltx_t2v",
    ("EZLTXPromptEnhance", "i2v"): "ltx_i2v",
    ("EZLTXPromptEnhance", "iclora"): "ltx_iclora",
    ("EZZimagePromptEnhance", "t2i"): "klein_t2i",
    ("EZLongCatPromptEnhance", "t2v"): "wan_t2v",
    ("EZLongCatPromptEnhance", "i2v"): "wan_i2v",
    ("EZLongCatPromptEnhance", "vc"): "wan_i2v",
    ("EZDreamXPromptEnhance", "i2v"): "ltx_i2v",
    ("EZAceStepPromptEnhance", "vocal"): "rap_draft",
    ("EZAceStepPromptEnhance", "instrumental"): "rap_draft",
    ("EZPodcastScript", "podcast_two_host"): "podcast_two_host",
    ("EZPodcastScript", "radio_drama"): "podcast_radio",
    ("EZPodcastLearn", ""): "podcast_learn",
    ("EZRapLyrics", ""): "rap_draft",
    ("EZCreativeResearch", ""): "research_chat",
    ("EZAppForge", ""): "app_forge",
    ("EZSamplePrompt", ""): "forge_lazy",
}


@dataclass(frozen=True)
class Sample:
    """One dropdown recipe.

    Attributes:
        id: Stable slug unique within a catalog.
        label: Combo value shown in the App.
        prompt: Full text for CLIP / script / logline widgets.
        tags: ACE-Step tags (empty on visual catalogs).
        lyrics: ACE-Step or rap lyrics (empty on visual catalogs).
    """

    id: str
    label: str
    prompt: str
    tags: str = ""
    lyrics: str = ""


def _as_str(value: object) -> str:
    """Coerce a widget value to a string.

    Args:
        value: Combo, textarea, or None.

    Returns:
        ``value`` when it is a ``str``, else ``str(value)`` or empty.
    """
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return str(value)


def _norm_choice(value: object) -> str:
    """Collapse whitespace on a combo choice.

    Args:
        value: Raw combo widget value.

    Returns:
        Stripped choice with internal runs of space folded to one.
    """
    return " ".join(_as_str(value).strip().split())


def album_hides_sample(lab_rel: str) -> bool:
    """True when Sample would overwrite an authored album track.

    Covers stay in-scope (Klein still). ``audio/music/rap-*`` is not under
    ``audio/albums/`` and keeps the dropdown.

    Args:
        lab_rel: Graph id such as ``audio/albums/nill-bye/peer-review/01-lab-coat``.

    Returns:
        True for album tracks and album zip graphs.
    """
    rel = _as_str(lab_rel).strip().replace("\\", "/")
    if not rel.startswith("audio/albums/"):
        return False
    if rel.endswith("/cover"):
        return False
    return True


@lru_cache(maxsize=1)
def load_index() -> dict[str, str]:
    """Return lab_rel → catalog id from ``index.json``.

    Returns:
        Mapping of graph ids to catalog stems. Empty when the file is missing.
    """
    path = SAMPLES_DIR / INDEX_NAME
    if not path.is_file():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return {}
    out: dict[str, str] = {}
    for key, value in raw.items():
        kid = _as_str(key).strip()
        cid = _as_str(value).strip()
        if kid and cid:
            out[kid] = cid
    return out


def catalog_exists(catalog_id: str) -> bool:
    """True when ``<catalog_id>.json`` is on disk.

    Args:
        catalog_id: Catalog stem (not Custom).

    Returns:
        Whether the catalog JSON file exists.
    """
    cid = _as_str(catalog_id).strip()
    if not cid or cid == CUSTOM:
        return False
    return (SAMPLES_DIR / f"{cid}.json").is_file()


def catalog_for_rel(lab_rel: str) -> str:
    """Map a lab-relative id (or a catalog id) to a catalog file stem.

    Args:
        lab_rel: ``stills/still-draft``, ``klein_t2i``, or empty.

    Returns:
        Catalog id, or empty when this graph has no sample catalog.
    """
    rel = _as_str(lab_rel).strip().replace("\\", "/")
    if not rel:
        return ""
    if album_hides_sample(rel):
        return ""
    if catalog_exists(rel):
        return rel
    mapped = load_index().get(rel, "")
    if mapped:
        return mapped
    if rel.endswith("/cover") and rel.startswith("audio/albums/"):
        return "klein_t2i"
    return ""


def family_catalog(node_type: str, mode: str = "") -> str:
    """Default catalog when the graph did not stamp ``catalog``.

    Args:
        node_type: Comfy class name.
        mode: Enhance / writer mode widget.

    Returns:
        Catalog id or empty.
    """
    ntype = _as_str(node_type).strip()
    kind = _as_str(mode).strip()
    if (ntype, kind) in _FAMILY_FOR_MODE:
        return _FAMILY_FOR_MODE[(ntype, kind)]
    if (ntype, "") in _FAMILY_FOR_MODE:
        return _FAMILY_FOR_MODE[(ntype, "")]
    return ""


def resolve_catalog(
    catalog: object,
    *,
    node_type: str = "",
    mode: str = "",
    lab_rel: str = "",
) -> str:
    """Pick a catalog id from widget, lab_rel, or node family.

    Args:
        catalog: Hidden ``catalog`` widget (lab_rel or catalog id).
        node_type: Comfy class name.
        mode: Enhance mode / podcast flavor.
        lab_rel: Graph extra.lab_rel when the widget is empty.

    Returns:
        Catalog id or empty.
    """
    raw = _as_str(catalog).strip()
    if raw:
        mapped = catalog_for_rel(raw)
        if mapped:
            return mapped
    rel = _as_str(lab_rel).strip()
    if rel:
        mapped = catalog_for_rel(rel)
        if mapped:
            return mapped
    return family_catalog(node_type, mode)


@lru_cache(maxsize=64)
def load_catalog(catalog_id: str) -> tuple[Sample, ...]:
    """Load one catalog. Missing or malformed files return empty.

    Args:
        catalog_id: Catalog stem.

    Returns:
        Frozen sample rows in file order, or an empty tuple.
    """
    cid = _as_str(catalog_id).strip()
    if not cid or cid == CUSTOM:
        return ()
    path = SAMPLES_DIR / f"{cid}.json"
    if not path.is_file():
        return ()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    if not isinstance(payload, list):
        return ()
    out: list[Sample] = []
    seen_ids: set[str] = set()
    seen_labels: set[str] = set()
    for item in payload:
        if not isinstance(item, dict):
            continue
        sid = _as_str(item.get("id")).strip()
        label = _norm_choice(item.get("label"))
        if not sid or not label or label.lower() == CUSTOM:
            continue
        if sid in seen_ids or label.lower() in seen_labels:
            continue
        seen_ids.add(sid)
        seen_labels.add(label.lower())
        out.append(
            Sample(
                id=sid,
                label=label,
                prompt=_as_str(item.get("prompt")),
                tags=_as_str(item.get("tags")),
                lyrics=_as_str(item.get("lyrics")),
            )
        )
    return tuple(out)


def list_catalog_ids() -> tuple[str, ...]:
    """Return catalog stems on disk (not ``index``).

    Returns:
        Sorted JSON stems under ``js/samples/``, excluding ``index.json``.
    """
    if not SAMPLES_DIR.is_dir():
        return ()
    names = []
    for path in sorted(SAMPLES_DIR.glob("*.json")):
        if path.name == INDEX_NAME:
            continue
        names.append(path.stem)
    return tuple(names)


def sample_labels(catalog_id: str) -> list[str]:
    """Combo values: catalog labels then Custom.

    Args:
        catalog_id: Catalog stem. Empty yields only Custom.

    Returns:
        Labels for a Comfy combo widget.
    """
    labels = [item.label for item in load_catalog(catalog_id)]
    if CUSTOM not in {item.lower() for item in labels}:
        labels.append(CUSTOM)
    elif CUSTOM not in labels:
        labels.append(CUSTOM)
    return labels


@lru_cache(maxsize=32)
def _sample_combo_labels_cached(preferred: str) -> tuple[str, ...]:
    """Cached union of every catalog label, preferred family first.

    Args:
        preferred: Catalog stem whose labels are listed first.

    Returns:
        Unique labels then Custom, preferred catalog first.
    """
    seen: set[str] = set()
    body: list[str] = []

    def add_label(label: str) -> None:
        """Append a unique non-Custom label.

        Args:
            label: Combo value from a catalog row.
        """
        key = label.lower()
        if not label or key == CUSTOM or key in seen:
            return
        seen.add(key)
        body.append(label)

    if preferred:
        for item in load_catalog(preferred):
            add_label(item.label)
    for catalog_id in list_catalog_ids():
        if catalog_id == preferred:
            continue
        for item in load_catalog(catalog_id):
            add_label(item.label)
    body.append(CUSTOM)
    return tuple(body)


def sample_combo_labels(preferred: str = "") -> list[str]:
    """Labels Comfy must accept on the sample combo.

    JS binds ``widget.options.values`` to one catalog so App Mode cannot
    show foreign recipes. The Python combo is the union of every catalog so
    a graph like ``stills/dream-house`` (``klein_place``) does not fail
    frontend validation when the App picks a place recipe such as Cliff villa.

    Args:
        preferred: Catalog stem whose labels come first (family default).

    Returns:
        Unique labels, preferred catalog first, then others, then Custom.
    """
    return list(_sample_combo_labels_cached(_as_str(preferred).strip()))


def _lookup(catalog_id: str, sample: str) -> Sample | None:
    """Find a sample by combo label or id.

    Args:
        catalog_id: Catalog stem already resolved.
        sample: Combo value (label or id).

    Returns:
        Matching ``Sample``, or None for Custom / miss.
    """
    choice = _norm_choice(sample)
    if not choice or choice.lower() == CUSTOM:
        return None
    for item in load_catalog(catalog_id):
        if item.label == choice or item.id == choice:
            return item
        if item.label.lower() == choice.lower():
            return item
    return None


def is_custom(sample: object) -> bool:
    """True when the combo is Custom or empty.

    Args:
        sample: Combo widget value.

    Returns:
        Whether Queue should use the textarea instead of a catalog row.
    """
    choice = _norm_choice(sample)
    return (not choice) or choice.lower() == CUSTOM


def resolve_prompt(
    catalog: object,
    sample: object,
    custom_text: object,
    *,
    node_type: str = "",
    mode: str = "",
    lab_rel: str = "",
) -> str:
    """Return the prompt string Queue should encode.

    Args:
        catalog: Hidden catalog widget.
        sample: Combo value (label, id, or Custom).
        custom_text: Textarea contents used when Custom or lookup fails.
        node_type: Comfy class name for family fallback.
        mode: Enhance mode.
        lab_rel: Graph id.

    Returns:
        Catalog prompt, or ``custom_text`` as a string.
    """
    fallback = _as_str(custom_text)
    if is_custom(sample):
        return fallback
    cid = resolve_catalog(
        catalog, node_type=node_type, mode=mode, lab_rel=lab_rel
    )
    hit = _lookup(cid, _as_str(sample))
    if hit is None:
        return fallback
    if hit.prompt.strip():
        return hit.prompt
    if hit.lyrics.strip():
        return hit.lyrics
    return fallback


def resolve_ace_sample(
    catalog: object,
    sample: object,
    tags: object,
    lyrics: object,
    *,
    node_type: str = "EZAceStepPromptEnhance",
    mode: str = "",
    lab_rel: str = "",
) -> tuple[str, str]:
    """Return ``(tags, lyrics)`` for ACE-Step / rap.

    Args:
        catalog: Hidden catalog widget.
        sample: Combo value.
        tags: Widget tags when Custom.
        lyrics: Widget lyrics when Custom.
        node_type: Comfy class name.
        mode: ``vocal`` or ``instrumental``.
        lab_rel: Graph id.

    Returns:
        Tags and lyrics pair.
    """
    fallback_tags = _as_str(tags)
    fallback_lyrics = _as_str(lyrics)
    if is_custom(sample):
        return fallback_tags, fallback_lyrics
    cid = resolve_catalog(
        catalog, node_type=node_type, mode=mode, lab_rel=lab_rel
    )
    hit = _lookup(cid, _as_str(sample))
    if hit is None:
        return fallback_tags, fallback_lyrics
    out_tags = hit.tags if hit.tags.strip() else fallback_tags
    out_lyrics = hit.lyrics if hit.lyrics.strip() else (
        hit.prompt if hit.prompt.strip() else fallback_lyrics
    )
    return out_tags, out_lyrics


def catalog_payload(catalog_id: str) -> list[dict[str, str]]:
    """JSON-shaped list for tests and the frontend dump.

    Args:
        catalog_id: Catalog stem.

    Returns:
        Sample dicts with id, label, prompt, and optional tags/lyrics.
    """
    rows: list[dict[str, str]] = []
    for item in load_catalog(catalog_id):
        row: dict[str, str] = {
            "id": item.id,
            "label": item.label,
            "prompt": item.prompt,
        }
        if item.tags:
            row["tags"] = item.tags
        if item.lyrics:
            row["lyrics"] = item.lyrics
        rows.append(row)
    return rows
