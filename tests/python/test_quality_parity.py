"""Shipped-graph drift check for the Quality tier table.

Every ``workflows/_lab`` graph carries one EZQuality combo. The tier table in
custom_nodes/ez_quality/presets.py is what that combo writes, so a graph can
drift two ways: it records a combo value the node no longer offers, or it holds
widgets no tier would produce and the operator sees a level the graph is not
actually on. This walks the tree once (parsed a single time per process) and
checks the recorded value, the family the node infers, and the loaders the
family's tiers would write.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from _lab_paths import lab_graph_paths, lab_rel_of
from _wire_quality import QUALITY_TYPE

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_quality.presets import (  # noqa: E402
    CLIP_NAME_INDEX,
    KSAMPLER_CFG_INDEX,
    KSAMPLER_STEPS_INDEX,
    QUALITY_CHOICES,
    QUALITY_CUSTOM,
    QUALITY_FAMILY_KLEIN3,
    QUALITY_LAB,
    UNET_NAME_INDEX,
    VAE_NAME_INDEX,
    family_owned_fields,
    infer_occupancy,
    is_klein3_clip,
    is_klein3_unet,
    match_tier,
)

# presets.py indexes the name widgets; CLIPLoader[1] is the clip type slot that
# the klein tiers pin to flux2, and it has no named constant of its own.
CLIP_TYPE_WIDGET_INDEX = 1

# Per overlay field: the node type holding the widget and its widgets_values
# slot. A tier that writes a field needs that widget present to write it.
FIELD_HOSTS: dict[str, tuple[str, int]] = {
    "steps": ("KSampler", KSAMPLER_STEPS_INDEX),
    "cfg": ("KSampler", KSAMPLER_CFG_INDEX),
    "unet_name": ("UNETLoader", UNET_NAME_INDEX),
    "clip_name": ("CLIPLoader", CLIP_NAME_INDEX),
    "clip_type": ("CLIPLoader", CLIP_TYPE_WIDGET_INDEX),
    "vae_name": ("VAELoader", VAE_NAME_INDEX),
}

_ROWS: list[tuple[str, Path, dict[str, Any]]] | None = None


def _lab_rows() -> list[tuple[str, Path, dict[str, Any]]]:
    """Return ``(lab_rel, path, graph)`` for every shipped graph, parsed once.

    Undecodable or non-object JSON is skipped the way the other lab walkers
    skip it; other tests own what the tree must contain.

    Args:
        None.

    Returns:
        Rows sorted by path.
    """
    global _ROWS
    if _ROWS is None:
        rows: list[tuple[str, Path, dict[str, Any]]] = []
        for path in lab_graph_paths():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if not isinstance(data, dict):
                continue
            rows.append((lab_rel_of(path), path, data))
        rows.sort(key=lambda row: row[1].as_posix())
        _ROWS = rows
    return _ROWS


def _nodes(graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Node dicts of a graph, ignoring malformed entries.

    Args:
        graph: Serialized Comfy graph.

    Returns:
        Node dicts in file order.
    """
    raw = graph.get("nodes")
    if not isinstance(raw, list):
        return []
    return [node for node in raw if isinstance(node, dict)]


def _widget(nodes: list[dict[str, Any]], node_type: str, index: int) -> Any:
    """First widget value for ``node_type`` at ``index``.

    Args:
        nodes: Graph nodes.
        node_type: Node type to read.
        index: widgets_values slot.

    Returns:
        Widget value, or None when the node or slot is absent.
    """
    for node in nodes:
        if node.get("type") != node_type:
            continue
        values = node.get("widgets_values")
        if isinstance(values, list) and len(values) > index:
            return values[index]
    return None


def _has_widget(nodes: list[dict[str, Any]], node_type: str, index: int) -> bool:
    """True when a node of ``node_type`` carries a slot at ``index``.

    A null value still counts: the overlay writes into the slot whatever it
    holds, so the slot existing is what the tier row needs.

    Args:
        nodes: Graph nodes.
        node_type: Node type to look for.
        index: widgets_values slot.

    Returns:
        True when the overlay could write that field.
    """
    for node in nodes:
        if node.get("type") != node_type:
            continue
        values = node.get("widgets_values")
        if isinstance(values, list) and len(values) > index:
            return True
    return False


def _family(nodes: list[dict[str, Any]], graph: dict[str, Any]) -> str:
    """Family the Quality node uses: occupancy, upgraded by the FLUX 3 needles.

    Args:
        nodes: Graph nodes.
        graph: Serialized Comfy graph.

    Returns:
        A QUALITY_FAMILIES id, or an unknown id the tiers treat as a no-op.
    """
    extra = graph.get("extra") if isinstance(graph.get("extra"), dict) else {}
    mode = extra.get("lab_app_mode") if isinstance(extra, dict) else None
    occupancy = str((mode or {}).get("occupancy") or "").strip()
    if is_klein3_unet(str(_widget(nodes, "UNETLoader", UNET_NAME_INDEX) or "")) or (
        is_klein3_clip(str(_widget(nodes, "CLIPLoader", CLIP_NAME_INDEX) or ""))
    ):
        return QUALITY_FAMILY_KLEIN3
    return occupancy or infer_occupancy(graph)


def _observed(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    """Overlay fields as the shipped widgets hold them.

    Args:
        nodes: Graph nodes.

    Returns:
        Mapping of overlay field to widget value, None when no loader is wired.
    """
    return {
        field: _widget(nodes, host, index)
        for field, (host, index) in FIELD_HOSTS.items()
    }


def test_lab_tree_is_populated() -> None:
    """The drift checks below must iterate a real tree, never an empty glob."""
    assert len(_lab_rows()) >= 600


def test_every_graph_records_a_legal_quality() -> None:
    """Each shipped graph records one combo value the node still offers."""
    misses: list[str] = []
    for rel, _path, graph in _lab_rows():
        nodes = _nodes(graph)
        hits = [node for node in nodes if node.get("type") == QUALITY_TYPE]
        if len(hits) != 1:
            misses.append(f"{rel}: {len(hits)} {QUALITY_TYPE} nodes")
            continue
        recorded = _widget(hits, QUALITY_TYPE, 0)
        if recorded not in QUALITY_CHOICES:
            misses.append(f"{rel}: recorded quality {recorded!r}")
    assert not misses


def test_every_graph_reads_back_as_a_tier_or_lab() -> None:
    """Shipped widgets read back as a named tier or the authored lab defaults."""
    misses: list[str] = []
    for rel, _path, graph in _lab_rows():
        nodes = _nodes(graph)
        family = _family(nodes, graph)
        observed = _observed(nodes)
        matched = match_tier(observed, family=family, authored=observed)
        if matched not in QUALITY_CHOICES or matched == QUALITY_CUSTOM:
            misses.append(f"{rel}: family {family!r} matched {matched!r} {observed}")
            continue
        # A named level must win on its own; only a graph that matches no tier
        # may fall through to lab on its authored values.
        if family_owned_fields(family):
            bare = match_tier(observed, family=family)
            if (bare == QUALITY_CUSTOM) != (matched == QUALITY_LAB):
                misses.append(
                    f"{rel}: family {family!r} bare={bare!r} authored={matched!r}"
                )
    assert not misses


def test_every_sampler_ships_the_loaders_its_family_writes() -> None:
    """Every field a family tier writes has a widget to write into."""
    misses: list[str] = []
    for rel, _path, graph in _lab_rows():
        nodes = _nodes(graph)
        if not any(node.get("type") == "KSampler" for node in nodes):
            continue
        family = _family(nodes, graph)
        for field in family_owned_fields(family):
            host, index = FIELD_HOSTS[field]
            if not _has_widget(nodes, host, index):
                misses.append(
                    f"{rel}: {family!r} writes {field}, no {host}[{index}]"
                )
    assert not misses
