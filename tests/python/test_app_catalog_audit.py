"""Gate: every shipped App graph under ``workflows/_lab`` reads as a working App.

Nobody reviews 703 generated graphs by eye, so this file reviews all of them on
every validate run. Each invariant is one test parametrized over every shipped
graph, and every failure message names the graph id, so a graph defect is a red
test rather than a broken App in front of an operator.

What the gate proves, one test per invariant:

1.  The ``links`` table and each node's ``inputs`` / ``outputs`` bookkeeping
    agree both ways - no dangling link in either direction.
2.  Link ids and node ids are unique and inside ``last_link_id`` /
    ``last_node_id``.
3.  The graph has a terminal node, and every live sampler has its four required
    inputs wired.
4.  Every node type is one the repo documents (``docs/workflow_nodes_*.py``,
    the source behind ``docs/reference/workflow-nodes.md``), and a type a single
    graph uses alone is held to that same list - the classic typo'd class.
5.  ``widgets_values`` is exactly as long as one of the node type's documented
    widget layouts, and a dict-shaped widget bag uses only documented keys.
6.  Every ``extra.linearData.inputs`` row names an existing node and a widget
    that node actually carries - a row pointing at a widget the node does not
    have is a dead control in the App panel.
7.  No row surfaces a control that does nothing: the node is neither bypassed
    nor an unlinked source.
8.  An image picker the App exposes feeds a live consumer.
9.  No two App rows carry the same operator-facing label.
10. Every ``extra.linearData.outputs`` entry names an existing node.
11. Every save prefix is authored, is not the ``ComfyUI`` default, and carries
    no absolute path, backslash, or ``%`` placeholder.
12. ``extra.lab_app_mode.lane`` is the folder lane (cheap duplicate of
    ``test_lab_tree.py``, kept because it costs nothing here).
13. ``extra.lab_app_mode.occupancy`` is a real occupancy, and the node types
    present agree with it.
14. Latent pixels sit on the family's divisibility grid (16 for Klein/Wan, 32
    for LTX).
15. A sampler's authored steps/CFG pair is a recipe this repo actually runs.
16. Every App carries a ``lab_description`` and a ``lab_note``, and the note
    names its occupancy family; :func:`test_note_names_its_handoff_target` asks
    it to name its handoff too.
17. Every ``extra.lab_app_mode.handoff`` id resolves to a shipped graph.
18. No banned or off-catalog weight filename is pinned in a widget.
19. At most one ``EZQuality`` per graph, recording a rung the ladder honors.
20. An image picker that reads nothing is a muted, declared opt-in with a free
    ``IMAGE`` slot waiting for it - no other shape of dead upload box ships.
21. An image picker that is live and wired has an App row, so every still the
    graph reads is one the operator can actually choose.
22. Operator-facing copy - node titles, string widgets, and the ``lab_*`` prose -
    never names the retired Quality combo, because the control the operator
    actually has is Detail (:data:`RETIRED_CONTROL_PHRASES`).

Nothing here hardcodes a rung name, a tier name, or a model family: the ladder
comes from ``ez_quality.presets``, the occupancy slots and the banned needles
from ``_stamp_app_mode``, the widget table from the node encyclopedia, and the
per-family node signature from the catalog itself (see :func:`_type_home`).
The one list this file writes out by hand is :data:`RETIRED_CONTROL_PHRASES`,
which names a control the repo has already removed, so there is nothing left to
read it from.

Every rule runs strict on every shipped graph: nothing here is xfailed,
skipped, or narrowed to a lane. What the first pass of this gate reported is
closed, and the way it was closed is part of the rule, not a suppression:

* :func:`test_save_prefix_is_safe_text` - the album lane's ``NN - Track Title``
  names are the deliverable, so they are a named exception
  (:data:`ALBUM_TRACK_PREFIX`) inside the rule. 251 graphs, 723 prefix values.
* :func:`test_sampler_recipe_is_a_recipe_this_repo_runs` - two samplers sit
  outside the band for a stated reason (:data:`DOCUMENTED_SAMPLER_RECIPES`) and
  skip themselves with that reason; the band still fails any other graph.
* :func:`test_note_names_its_handoff_target` - the stamper now writes a
  ``Handoff:`` line into the operator note for every stamped chain, so the 44
  unreadable chains are gone and the rule runs strict.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

import pytest

from _lab_families import LOADER_TYPES
from _lab_ids import rel_id
from _lab_paths import ROOT, cached_lab_graph_rows
from _lab_wiring import REQUIRED_INPUTS, TERMINAL_TYPES, custom_output_node_types
from _stamp_app_mode import (
    BANNED,
    NODE_MODE_BYPASS,
    OCCUPANCIES,
    STAMP_SPECS,
    display_label,
    linear_input_node_id,
)
from _strip_dead_pickers import dead_pickers
from ez_quality import presets
from workflow_nodes import encyclopedia

# ---------------------------------------------------------------------------
# The catalog, loaded once
# ---------------------------------------------------------------------------

ROWS: list[tuple[str, Path, dict[str, Any]]] = cached_lab_graph_rows()
"""``(lab_rel, path, graph)`` for every shipped graph, parsed once per process."""

GRAPHS: list[tuple[str, dict[str, Any]]] = [(rel, graph) for rel, _, graph in ROWS]
"""``(lab_rel, graph)`` pairs the invariants are parametrized over."""

GRAPH_IDS: list[str] = [rel for rel, _ in GRAPHS]
"""Graph ids used as pytest case ids, so a failure names the graph."""

MIN_GRAPHS = 700
"""Lower bound on the catalog, so the gate cannot pass by finding nothing."""

NOOP_OCCUPANCIES: tuple[str, ...] = ("none", "llm")
"""Occupancies that claim no GPU job and so carry no family claim."""

LATENT_GRID_BY_OCCUPANCY: dict[str, int] = {
    "klein": 16,
    "wan": 16,
    "ltx": 32,
    "film": 32,
}
"""Pixels a family's latent node must divide by, keyed by occupancy."""

PROSE_NODE_TYPES: frozenset[str] = frozenset({"Note", "MarkdownNote"})
"""Node types whose only widget is operator prose.

A note that names an off-catalog model is documentation of what the App refuses
to reach, so the pinned-weight gate reads loaders and samplers and leaves these
alone. The graph carries no other prose carrier.
"""

DISTILLED_NEEDLES: tuple[str, ...] = ("distilled", "turbo")
"""Filename needles that mark a loader's weight as the distilled twin.

Both appear in weight names the shipped catalog already pins, so the split
between a distilled and a base recipe is read off the catalog, not asserted.
"""

MAX_AUTHORED_STEPS_FOR_DISTILLED = 8
"""A sampler authored at or under this many steps is a distilled quick look."""

DISTILLED_CFG_CEILING = 1.5
"""Guidance a distilled checkpoint may be fed before it is off-recipe."""

BASE_CFG_FLOOR = 1.0
BASE_CFG_CEILING = 8.0
"""The guidance band a base checkpoint sampler is authored inside."""

SAFE_PREFIX = re.compile(r"^[a-z0-9_][a-z0-9_\-/.]*$")
"""The save-prefix shape this repo's output tooling resolves."""

ALBUM_TRACK_PREFIX = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9 ,._&'()!+-]*"
    r"(/[A-Za-z0-9][A-Za-z0-9 ,._&'()!+-]*)*$"
)
"""The one shape the album lane is allowed to save under: ``NN - Track Title``.

A catalog album is music, and the operator reads these names in a player and on
a cover, so the track number and human title are the deliverable, not a slug -
``01 - Brake Fade`` for a track, ``albums/Nill Bye/Peer Review/cover`` for an
album cover. That is the only exception, and it is narrow on purpose: still
ASCII, still no path separator other than ``/`` between named folders, still no
``%`` placeholder, and it is reachable only for graphs under ``audio/albums/``
(see :data:`ALBUM_LANE_PREFIX`).
"""

ALBUM_LANE_PREFIX = "audio/albums/"
"""Graphs whose save prefixes may follow :data:`ALBUM_TRACK_PREFIX`."""

DOCUMENTED_SAMPLER_RECIPES: dict[str, str] = {
    "3d/blockout-mesh": (
        "the TRELLIS shape stage is a guided proxy: 8 steps at CFG 7.5 is the "
        "recipe the node encyclopedia documents for a gray-box blockout"
    ),
    "labs/opt-in/still-to-video-a14b": (
        "an 8-step Lightning sampler at CFG 5 whose distillation rides a LoRA, "
        "so no weight name carries the distilled needle this rule reads"
    ),
}
"""Samplers this catalog deliberately ships outside the band, each with its why.

Named here instead of widened into the band, and instead of an ``xfail`` over the
whole rule: a new graph that drifts off the band still fails this gate.
"""

UNSAFE_PREFIX_CHARS: tuple[str, ...] = ("\\", "%")
"""Prefix characters that are a defect in any lane, not a style choice.

``/`` is a legal path separator, so an absolute path is caught by its leading
position in :func:`_prefix_defects` rather than by this list.
"""

HOME_MIN_GRAPHS = 5
"""How many graphs must use a type before its occupancy home is trusted."""

HOME_MIN_SHARE = 0.95
"""How one-sided the occupancy spread must be to call a type family-owned."""

VIRTUAL_APP_WIDGETS: Mapping[str, frozenset[str]] = {
    "EZDubIngest": frozenset({"upload"}),
}
"""Widget names the App panel offers that the serialized node does not carry.

``_stamp_app_mode`` documents ``upload`` as an App button label only, so it is
not a broken row; anything else is.
"""

IMAGE_PICKER_TYPES: frozenset[str] = frozenset(
    {"LoadImage", "EZOptionalImage", "EZSnapImage"}
)
"""Node types that put a still in front of the operator.

The DCC loaders are matched by prefix in :func:`_is_image_picker`, because they
are named by the pack rather than listed here.
"""

PYTEST_PARAM = "lab_rel,graph"
"""Signature every parametrized invariant takes."""


@pytest.fixture(scope="session")
def graph_rows() -> list[tuple[str, Path, dict[str, Any]]]:
    """Return the whole catalog, parsed once for the session.

    Returns:
        ``(lab_rel, path, graph)`` rows from the process-wide graph cache.
    """
    return ROWS


# ---------------------------------------------------------------------------
# Tables derived from the catalog and the node encyclopedia
# ---------------------------------------------------------------------------

_ENCYCLOPEDIA: Mapping[str, Mapping[str, Any]] = encyclopedia()


def _documented_widgets(ntype: str) -> list[Mapping[str, Any]]:
    """Return every widget row documented for one node type.

    A node that ships more than one layout lists alternates under ``variants``;
    all of them are documented shapes a graph may legitimately store.

    Args:
        ntype: Comfy ``class_type``.

    Returns:
        Widget specs from the encyclopedia entry, widest layout last.
    """
    spec = _ENCYCLOPEDIA.get(ntype) or {}
    rows: list[Mapping[str, Any]] = list(spec.get("widgets") or [])
    for variant in spec.get("variants") or []:
        rows.extend(variant.get("widgets") or [])
    return rows


def _widget_layouts() -> dict[str, frozenset[int]]:
    """Return the documented ``widgets_values`` lengths per node type.

    Returns:
        ``{class_type: lengths}`` over every documented type, where a type with
        a second layout carries both lengths.
    """
    layouts: dict[str, frozenset[int]] = {}
    for ntype, spec in _ENCYCLOPEDIA.items():
        sizes: set[int] = {len(spec.get("widgets") or [])}
        for variant in spec.get("variants") or []:
            sizes.add(len(variant.get("widgets") or []))
        layouts[ntype] = frozenset(sizes)
    return layouts


def _widget_slots() -> dict[str, dict[str, tuple[Any, Any]]]:
    """Return ``(index, key)`` per documented widget name.

    Args:
        None.

    Returns:
        ``{class_type: {widget_name: (list_index, dict_key)}}``.
    """
    slots: dict[str, dict[str, tuple[Any, Any]]] = {}
    for ntype in _ENCYCLOPEDIA:
        table: dict[str, tuple[Any, Any]] = {}
        for row in _documented_widgets(ntype):
            name = str(row.get("name") or "")
            if name:
                table.setdefault(name, (row.get("index"), row.get("key")))
        slots[ntype] = table
    return slots


def _terminal_types() -> frozenset[str]:
    """Return the classes that end a lane by writing or previewing.

    Returns:
        The static terminal list plus every first-party class whose body marks
        ``OUTPUT_NODE = True``, harvested from ``custom_nodes/``.
    """
    return frozenset(TERMINAL_TYPES | custom_output_node_types(ROOT / "custom_nodes"))


def _sampler_types() -> frozenset[str]:
    """Return the sampler classes whose four conditioning inputs are required.

    Returns:
        Classes from ``_lab_wiring.REQUIRED_INPUTS`` that ask for ``model``,
        ``positive``, ``negative``, and ``latent_image``.
    """
    wanted = frozenset({"model", "positive", "negative", "latent_image"})
    return frozenset(t for t, required in REQUIRED_INPUTS.items() if wanted <= required)


def _latent_producer_types() -> frozenset[str]:
    """Return the classes that create a latent and document its pixel size.

    A producer has a ``LATENT`` output and no ``LATENT`` input, and the
    encyclopedia names both a ``width`` and a ``height`` widget for it. Anything
    else is skipped rather than guessed at.

    Args:
        None.

    Returns:
        Class names that author pixels.
    """
    found: set[str] = set()
    for ntype, spec in _ENCYCLOPEDIA.items():
        sockets = spec.get("sockets") or []
        outs = {str(s.get("type") or "").upper() for s in sockets if s.get("dir") == "out"}
        ins = {str(s.get("type") or "").upper() for s in sockets if s.get("dir") == "in"}
        names = {str(row.get("name") or "") for row in _documented_widgets(ntype)}
        if "LATENT" in outs and "LATENT" not in ins and {"width", "height"} <= names:
            found.add(ntype)
    return frozenset(found)


def _family_machinery_types() -> frozenset[str]:
    """Return the classes that decide which stack a graph runs.

    Loaders, samplers, and the latent nodes that author a family's pixels. Generic
    utility classes (a ``PrimitiveNode`` holding a string, ``ImageFromBatch``
    picking a frame) are deliberately out: they name no family, and reading a
    family into them would flag honest graphs.

    Args:
        None.

    Returns:
        Class names whose occupancy home the catalog can be asked about.
    """
    return frozenset(set(LOADER_TYPES) | set(SAMPLER_NODE_TYPES) | set(LATENT_PRODUCER_TYPES))


def _type_home(
    rows: Sequence[tuple[str, dict[str, Any]]],
    candidates: frozenset[str],
) -> dict[str, str]:
    """Return the occupancy each machinery type belongs to, read off the catalog.

    A type is family-owned when at least :data:`HOME_MIN_GRAPHS` graphs carry it
    and :data:`HOME_MIN_SHARE` of those uses sit under one heavy occupancy. That
    is how "an app claiming ``klein`` contains no LTX sampler" is enforced without
    naming one model in this file.

    Args:
        rows: The ``(lab_rel, graph)`` catalog.
        candidates: Only these classes are given a home.

    Returns:
        ``{class_type: occupancy}`` for the types with one clear home.
    """
    spread: dict[str, Counter[str]] = {}
    for rel, graph in rows:
        del rel
        occupancy = _occupancy(graph)
        if occupancy in NOOP_OCCUPANCIES:
            continue
        for ntype in {str(node.get("type") or "") for node in _nodes(graph)}:
            if ntype not in candidates:
                continue
            spread.setdefault(ntype, Counter())[occupancy] += 1
    homes: dict[str, str] = {}
    for ntype, counts in spread.items():
        total = sum(counts.values())
        if total < HOME_MIN_GRAPHS:
            continue
        home, share = counts.most_common(1)[0]
        if share / total >= HOME_MIN_SHARE:
            homes[ntype] = home
    return homes


# ---------------------------------------------------------------------------
# Small readers over one graph
# ---------------------------------------------------------------------------


def _nodes(graph: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return the node rows of a graph.

    Args:
        graph: Parsed lab JSON.

    Returns:
        The ``nodes`` list, empty when the key is missing.
    """
    nodes = graph.get("nodes")
    return list(nodes) if isinstance(nodes, list) else []


def _node_index(graph: Mapping[str, Any]) -> dict[int, dict[str, Any]]:
    """Return ``{node id: node}`` for a graph.

    Args:
        graph: Parsed lab JSON.

    Returns:
        Node rows keyed by their integer id.
    """
    index: dict[int, dict[str, Any]] = {}
    for node in _nodes(graph):
        node_id = node.get("id")
        if isinstance(node_id, int):
            index[node_id] = node
    return index


def _link_rows(graph: Mapping[str, Any]) -> list[Any]:
    """Return the link table of a graph.

    Args:
        graph: Parsed lab JSON.

    Returns:
        The ``links`` list, empty when the key is missing.
    """
    links = graph.get("links")
    return list(links) if isinstance(links, list) else []


def _link_map(graph: Mapping[str, Any]) -> dict[Any, Sequence[Any]]:
    """Return ``{link id: link row}`` for the rows this file can read.

    Args:
        graph: Parsed lab JSON.

    Returns:
        Six-field link rows keyed by link id.
    """
    return {
        row[0]: row
        for row in _link_rows(graph)
        if isinstance(row, (list, tuple)) and len(row) == 6
    }


def _extra(graph: Mapping[str, Any]) -> dict[str, Any]:
    """Return a graph's ``extra`` block.

    Args:
        graph: Parsed lab JSON.

    Returns:
        The ``extra`` mapping, empty when absent.
    """
    extra = graph.get("extra")
    return dict(extra) if isinstance(extra, Mapping) else {}


def _is_stub(graph: Mapping[str, Any]) -> bool:
    """True for a placeholder graph the App panel never lists.

    Args:
        graph: Parsed lab JSON.

    Returns:
        Whether ``extra.lab_stub`` marks the graph a stub.
    """
    return _extra(graph).get("lab_stub") is True


def _app_mode(graph: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return the lab App Mode stamp, or None for a non-App graph.

    Args:
        graph: Parsed lab JSON.

    Returns:
        ``extra.lab_app_mode`` when the graph is an enabled App, else None.
    """
    if _is_stub(graph):
        return None
    mode = _extra(graph).get("lab_app_mode")
    if not isinstance(mode, Mapping) or mode.get("enabled") is not True:
        return None
    return dict(mode)


def _occupancy(graph: Mapping[str, Any]) -> str:
    """Return the occupancy the graph claims, lowercased.

    Args:
        graph: Parsed lab JSON.

    Returns:
        ``extra.lab_app_mode.occupancy``, or ``""`` when the graph claims none.
    """
    mode = _app_mode(graph)
    if mode is None:
        return ""
    return str(mode.get("occupancy") or "").strip().lower()


def _linear_rows(graph: Mapping[str, Any]) -> tuple[list[Any], list[Any]]:
    """Return the App panel's input and output rows.

    Args:
        graph: Parsed lab JSON.

    Returns:
        ``(inputs, outputs)`` from ``extra.linearData``.
    """
    linear = _extra(graph).get("linearData")
    if not isinstance(linear, Mapping):
        return [], []
    inputs = linear.get("inputs")
    outputs = linear.get("outputs")
    return (
        list(inputs) if isinstance(inputs, list) else [],
        list(outputs) if isinstance(outputs, list) else [],
    )


def _mode(node: Mapping[str, Any]) -> int:
    """Return a node's LiteGraph mode as an int.

    Args:
        node: One node row.

    Returns:
        The mode, 0 when the node does not record one.
    """
    try:
        return int(node.get("mode") or 0)
    except (TypeError, ValueError):
        return 0


def _is_bypassed(node: Mapping[str, Any]) -> bool:
    """True when a node sits outside the live lane.

    Args:
        node: One node row.

    Returns:
        Whether the node carries the bypass mode.
    """
    return _mode(node) == NODE_MODE_BYPASS


def _slot_names(node: Mapping[str, Any]) -> set[str]:
    """Return every name one node answers to.

    Covers socket names, the widget names stacked onto converted-widget slots,
    the keys of a dict-shaped widget bag, and the names the encyclopedia
    documents for the class.

    Args:
        node: One node row.

    Returns:
        Names a ``linearData`` row may legitimately point at.
    """
    names: set[str] = set()
    for key in ("inputs", "outputs"):
        for slot in node.get(key) or []:
            if not isinstance(slot, Mapping):
                continue
            if isinstance(slot.get("name"), str):
                names.add(str(slot["name"]))
            widget = slot.get("widget")
            if isinstance(widget, Mapping) and isinstance(widget.get("name"), str):
                names.add(str(widget["name"]))
    values = node.get("widgets_values")
    if isinstance(values, Mapping):
        names.update(str(key) for key in values)
    names.update(WIDGET_SLOTS.get(str(node.get("type") or ""), {}))
    return names


def _widget_value(node: Mapping[str, Any], name: str) -> Any:
    """Return one widget's authored value.

    Args:
        node: One node row.
        name: Documented widget name.

    Returns:
        The stored value, or None when the node does not hold it.
    """
    slot = WIDGET_SLOTS.get(str(node.get("type") or ""), {}).get(name)
    if slot is None:
        return None
    index, key = slot
    values = node.get("widgets_values")
    if isinstance(values, Mapping):
        return values.get(str(key) if key is not None else name)
    if isinstance(values, list) and isinstance(index, int) and 0 <= index < len(values):
        return values[index]
    return None


def _widget_values_by_name(node: Mapping[str, Any]) -> list[tuple[str, Any]]:
    """Return every authored widget value a node holds, with its name.

    Args:
        node: One node row.

    Returns:
        ``(widget_name, value)`` pairs in documented order.
    """
    name = str(node.get("type") or "")
    return [(widget, _widget_value(node, widget)) for widget in WIDGET_SLOTS.get(name, {})]


def _output_is_wired(node: Mapping[str, Any], *, only: str | None = None) -> bool:
    """True when a node has a linked output slot.

    Args:
        node: One node row.
        only: Restrict the check to the slot with this name, uppercased.

    Returns:
        Whether at least one matching output slot carries a link id.
    """
    for slot in node.get("outputs") or []:
        if not isinstance(slot, Mapping):
            continue
        if only is not None and str(slot.get("name") or "").upper() != only:
            continue
        if slot.get("links"):
            return True
    return False


def _consumers(
    graph: Mapping[str, Any],
    node: Mapping[str, Any],
    *,
    output: str,
) -> list[dict[str, Any]]:
    """Return the live nodes one named output feeds.

    Args:
        graph: Parsed lab JSON.
        node: The producing node row.
        output: Output slot name, uppercased.

    Returns:
        Consumer node rows reached through that slot's link ids.
    """
    links = _link_map(graph)
    nodes = _node_index(graph)
    found: list[dict[str, Any]] = []
    for slot in node.get("outputs") or []:
        if not isinstance(slot, Mapping):
            continue
        if str(slot.get("name") or "").upper() != output:
            continue
        for link_id in slot.get("links") or []:
            row = links.get(link_id)
            if row is None:
                continue
            target = nodes.get(row[3]) if isinstance(row[3], int) else None
            if target is not None:
                found.append(target)
    return found


def _is_image_picker(ntype: str) -> bool:
    """True for a node that puts a still in front of the operator.

    Args:
        ntype: Comfy ``class_type``.

    Returns:
        Whether the class is a listed picker or a DCC guide loader.
    """
    return ntype in IMAGE_PICKER_TYPES or ntype.startswith("EZDCCLoad")


def _pinned_weight_names(graph: Mapping[str, Any]) -> list[tuple[str, str, str]]:
    """Return every filename a widget pins, with where it came from.

    Args:
        graph: Parsed lab JSON.

    Returns:
        ``(node_id, class_type, filename)`` per string widget that looks like a
        weight file.
    """
    found: list[tuple[str, str, str]] = []
    for node in _nodes(graph):
        ntype = str(node.get("type") or "")
        for widget, value in _widget_values_by_name(node):
            if not isinstance(value, str):
                continue
            text = value.strip().rsplit("/", 1)[-1]
            if text.lower().endswith((".safetensors", ".ckpt", ".pt", ".pth", ".gguf")):
                found.append((str(node.get("id")), f"{ntype}.{widget}", text))
    return found


def _prefix_values(graph: Mapping[str, Any]) -> list[tuple[str, str, str, Any]]:
    """Return every save prefix a graph authors.

    A prefix widget is any widget whose documented name ends in ``prefix``, so
    ``filename_prefix`` and the sidecar writers' ``prefix`` are both covered
    without a hand-kept list.

    Args:
        graph: Parsed lab JSON.

    Returns:
        ``(node_id, class_type, widget_name, value)`` per authored prefix.
    """
    found: list[tuple[str, str, str, Any]] = []
    for node in _nodes(graph):
        ntype = str(node.get("type") or "")
        for widget, value in _widget_values_by_name(node):
            if widget.endswith("prefix") and value is not None:
                found.append((str(node.get("id")), ntype, widget, value))
    return found


def _prefix_defects(text: str) -> list[str]:
    """Return why one save prefix cannot ship.

    Args:
        text: The prefix as authored.

    Returns:
        One phrase per defect; empty when the prefix is safe.
    """
    problems: list[str] = []
    if not text.strip():
        problems.append("empty")
    if text == "ComfyUI":
        problems.append("ComfyUI default")
    for char in UNSAFE_PREFIX_CHARS:
        if char in text:
            problems.append(f"contains {char!r}")
    if text.startswith("/"):
        problems.append("absolute path")
    if ".." in text.split("/"):
        problems.append("parent traversal")
    return problems


def _effective_label(node: Mapping[str, Any], name: str, config: Mapping[str, Any]) -> str:
    """Return the label the App panel shows for one widget row.

    Args:
        node: The row's node.
        name: The widget name the row targets.
        config: The persisted ``linearData`` widget config, when present.

    Returns:
        The stamped label, or the label the stamp would derive.
    """
    label = config.get("label")
    if isinstance(label, str) and label.strip():
        return label.strip()
    return display_label(node, name)


def _row_config(entry: Sequence[Any]) -> dict[str, Any]:
    """Return the persisted config of one ``linearData`` input row.

    Args:
        entry: ``[nodeId, widgetName, config?]``.

    Returns:
        The config mapping, empty when the row carries none.
    """
    if len(entry) > 2 and isinstance(entry[2], Mapping):
        return dict(entry[2])
    return {}


# ---------------------------------------------------------------------------
# Catalog-wide tables, built once from the parsed graphs above
# ---------------------------------------------------------------------------

WIDGET_LAYOUTS: dict[str, frozenset[int]] = _widget_layouts()
"""Documented ``widgets_values`` lengths per node class."""

WIDGET_SLOTS: dict[str, dict[str, tuple[Any, Any]]] = _widget_slots()
"""Documented widget slot per class and name."""

TERMINAL_NODE_TYPES: frozenset[str] = _terminal_types()
"""Classes that end a lane, harvested from core plus first-party OUTPUT_NODE."""

SAMPLER_NODE_TYPES: frozenset[str] = _sampler_types()
"""Classes whose four conditioning inputs must all be wired."""

LATENT_PRODUCER_TYPES: frozenset[str] = _latent_producer_types()
"""Classes that author the pixels a family then samples."""

FAMILY_MACHINERY_TYPES: frozenset[str] = _family_machinery_types()
"""Classes whose presence decides which stack a graph is claiming to run."""

TYPE_HOME: dict[str, str] = _type_home(GRAPHS, FAMILY_MACHINERY_TYPES)
"""Occupancy each family-owned node type belongs to, per the catalog."""

_TYPE_USE: Counter[str] = Counter(
    str(node.get("type") or "") for _, graph in GRAPHS for node in _nodes(graph)
)
"""How many graphs each node class appears in, across the whole catalog."""

TYPE_SINGLES: Mapping[str, frozenset[str]] = {
    rel: frozenset(
        str(node.get("type") or "")
        for node in _nodes(graph)
        if _TYPE_USE[str(node.get("type") or "")] == 1
    )
    for rel, graph in GRAPHS
}
"""Per graph, the node classes no other shipped graph also uses."""

SHIPPED_IDS: frozenset[str] = frozenset(rel for rel, _, _ in ROWS)
"""Every ``_lab``-relative graph id that ships."""

SHIPPED_STEMS: frozenset[str] = frozenset(rel.rsplit("/", 1)[-1] for rel, _, _ in ROWS)
"""Basenames of the shipped graphs, for a handoff written as a stem."""


# ---------------------------------------------------------------------------
# Guard: the gate must actually walk the catalog
# ---------------------------------------------------------------------------


def test_the_gate_walks_the_whole_catalog(graph_rows: list[tuple[str, Path, dict[str, Any]]]) -> None:
    """A broken helper would make every invariant below pass vacuously.

    Args:
        graph_rows: The session's parsed catalog.
    """
    assert len(graph_rows) >= MIN_GRAPHS, len(graph_rows)
    apps = [rel for rel, _, graph in graph_rows if _app_mode(graph) is not None]
    assert len(apps) >= MIN_GRAPHS, len(apps)
    assert len(WIDGET_LAYOUTS) > 80, len(WIDGET_LAYOUTS)
    assert "KSampler" in WIDGET_LAYOUTS
    assert SAMPLER_NODE_TYPES and "KSampler" in SAMPLER_NODE_TYPES, SAMPLER_NODE_TYPES
    assert LATENT_PRODUCER_TYPES, "no latent producer documented a size widget"
    assert TYPE_HOME, "the catalog named no family-owned node type"
    assert TERMINAL_NODE_TYPES & {"SaveImage", "SaveAudio"}, TERMINAL_NODE_TYPES


# ---------------------------------------------------------------------------
# Structural
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(PYTEST_PARAM, GRAPHS, ids=GRAPH_IDS)
def test_link_table_agrees_with_slot_bookkeeping(
    lab_rel: str, graph: dict[str, Any]
) -> None:
    """Every link row is six fields, and both sides of it agree.

    ComfyUI stores a wire twice, in the ``links`` table and inside the two
    nodes, and trusts both at load. A row that is not
    ``[id, origin_id, origin_slot, target_id, target_slot, type]``, a link whose
    node or slot is gone, or a slot that does not list its link back is a graph
    that queues an orphan or drops a tensor.

    The sixth field is normally the socket type string. The catalog also stores
    the combo list a converted-widget wire carries, so a list of strings that
    matches both slots is the shape this repo ships (``photos/image-studio``
    link 25) and is accepted; anything else is a defect.

    Args:
        lab_rel: ``_lab``-relative graph id.
        graph: Parsed lab JSON.
    """
    nodes = _node_index(graph)
    table_ids: set[Any] = set()
    for row in _link_rows(graph):
        if not isinstance(row, (list, tuple)) or len(row) != 6:
            pytest.fail(f"{lab_rel}: link row is not six fields: {row!r}")
        link_id, origin_id, origin_slot, target_id, target_slot, link_type = row
        assert link_id not in table_ids, f"{lab_rel}: duplicate link id {link_id}"
        table_ids.add(link_id)
        assert isinstance(origin_id, int) and isinstance(target_id, int), (
            f"{lab_rel}: link {link_id} does not name integer node ids: {row!r}"
        )
        origin = nodes.get(origin_id)
        target = nodes.get(target_id)
        assert origin is not None, f"{lab_rel}: link {link_id} names absent origin {origin_id}"
        assert target is not None, f"{lab_rel}: link {link_id} names absent target {target_id}"
        outputs = origin.get("outputs") or []
        inputs = target.get("inputs") or []
        assert isinstance(origin_slot, int) and 0 <= origin_slot < len(outputs), (
            f"{lab_rel}: link {link_id} origin slot {origin_slot} off "
            f"node {origin_id} ({len(outputs)} outputs)"
        )
        assert isinstance(target_slot, int) and 0 <= target_slot < len(inputs), (
            f"{lab_rel}: link {link_id} target slot {target_slot} off "
            f"node {target_id} ({len(inputs)} inputs)"
        )
        link_types_ok = isinstance(link_type, str) or (
            isinstance(link_type, list)
            and link_type
            and all(isinstance(item, str) for item in link_type)
        )
        assert link_types_ok, f"{lab_rel}: link {link_id} type is not a socket type: {link_type!r}"
        assert link_id in (outputs[origin_slot].get("links") or []), (
            f"{lab_rel}: link {link_id} missing from node {origin_id} "
            f"({origin.get('type')}) output slot {origin_slot}"
        )
        assert inputs[target_slot].get("link") == link_id, (
            f"{lab_rel}: link {link_id} missing from node {target_id} "
            f"({target.get('type')}) input slot {target_slot} "
            f"(slot says {inputs[target_slot].get('link')!r})"
        )

    for node_id, node in nodes.items():
        for slot_index, slot in enumerate(node.get("inputs") or []):
            if not isinstance(slot, Mapping):
                continue
            claimed = slot.get("link")
            if claimed is not None:
                assert claimed in table_ids, (
                    f"{lab_rel}: node {node_id} ({node.get('type')}) input slot "
                    f"{slot_index} claims link {claimed} the table never declared"
                )
        for slot_index, slot in enumerate(node.get("outputs") or []):
            if not isinstance(slot, Mapping):
                continue
            for claimed in slot.get("links") or []:
                assert claimed in table_ids, (
                    f"{lab_rel}: node {node_id} ({node.get('type')}) output slot "
                    f"{slot_index} claims link {claimed} the table never declared"
                )


@pytest.mark.parametrize(PYTEST_PARAM, GRAPHS, ids=GRAPH_IDS)
def test_link_and_node_ids_are_unique_inside_the_counters(
    lab_rel: str, graph: dict[str, Any]
) -> None:
    """Ids are unique and the graph's own counters still cover them.

    A node or link id above ``last_node_id`` / ``last_link_id`` is one the
    frontend reuses on the next paste, which silently welds two wires together.

    Args:
        lab_rel: ``_lab``-relative graph id.
        graph: Parsed lab JSON.
    """
    seen_nodes: dict[int, str] = {}
    for node in _nodes(graph):
        node_id = node.get("id")
        assert isinstance(node_id, int), f"{lab_rel}: node id is not an int: {node_id!r}"
        assert node_id not in seen_nodes, (
            f"{lab_rel}: node id {node_id} used by {seen_nodes[node_id]} "
            f"and {node.get('type')}"
        )
        seen_nodes[node_id] = str(node.get("type") or "?")

    seen_links: set[Any] = set()
    for row in _link_rows(graph):
        if not isinstance(row, (list, tuple)) or not row:
            continue
        link_id = row[0]
        assert link_id not in seen_links, f"{lab_rel}: duplicate link id {link_id}"
        seen_links.add(link_id)

    for label, counter, ids in (
        ("last_node_id", graph.get("last_node_id"), set(seen_nodes)),
        ("last_link_id", graph.get("last_link_id"), seen_links),
    ):
        assert isinstance(counter, int), f"{lab_rel}: {label} is not an int: {counter!r}"
        assert counter >= 0, f"{lab_rel}: {label} is negative: {counter}"
        numbered = [item for item in ids if isinstance(item, int)]
        if numbered:
            highest = max(numbered)
            assert highest <= counter, (
                f"{lab_rel}: {label} {counter} is below the highest id {highest}"
            )


@pytest.mark.parametrize(PYTEST_PARAM, GRAPHS, ids=GRAPH_IDS)
def test_graph_has_a_terminal_and_samplers_are_fed(
    lab_rel: str, graph: dict[str, Any]
) -> None:
    """One lane writes something, and no live sampler samples on an empty input.

    The terminal list is core's plus every first-party class that marks itself
    ``OUTPUT_NODE``; the sampler classes and their required sockets come from
    ``_lab_wiring.REQUIRED_INPUTS``. A bypassed sampler is out of the lane, so it
    is not asked to be wired.

    Args:
        lab_rel: ``_lab``-relative graph id.
        graph: Parsed lab JSON.
    """
    nodes = _nodes(graph)
    terminals = [
        str(node.get("id"))
        for node in nodes
        if str(node.get("type") or "") in TERMINAL_NODE_TYPES
    ]
    assert terminals, f"{lab_rel}: no terminal output node among {len(nodes)} nodes"

    for node in nodes:
        ntype = str(node.get("type") or "")
        if ntype not in SAMPLER_NODE_TYPES or _is_bypassed(node):
            continue
        slots: dict[str, list[Mapping[str, Any]]] = {}
        for slot in node.get("inputs") or []:
            if isinstance(slot, Mapping) and isinstance(slot.get("name"), str):
                slots.setdefault(str(slot["name"]), []).append(slot)
        for name in sorted(REQUIRED_INPUTS[ntype]):
            candidates = slots.get(name) or []
            assert candidates, (
                f"{lab_rel}: sampler {node.get('id')} ({ntype} "
                f"'{node.get('title')}') has no '{name}' input slot"
            )
            assert any(
                slot.get("link") is not None or slot.get("links")
                for slot in candidates
            ), (
                f"{lab_rel}: sampler {node.get('id')} ({ntype} "
                f"'{node.get('title')}') input '{name}' is unwired"
            )


@pytest.mark.parametrize(PYTEST_PARAM, GRAPHS, ids=GRAPH_IDS)
def test_node_types_are_known_to_the_reference(
    lab_rel: str, graph: dict[str, Any]
) -> None:
    """No graph queues a class the node reference never named.

    The allowed set is the encyclopedia behind ``docs/reference/workflow-nodes.md``
    (the same table ``_lab_node_catalog`` and the docs page read). A class used
    by exactly one graph is the classic silent-broken-graph bug: it resolves on
    nobody's machine and dies at Queue, so a singleton class is held to the same
    list as a common one and is called out by name.

    Args:
        lab_rel: ``_lab``-relative graph id.
        graph: Parsed lab JSON.
    """
    singleton = TYPE_SINGLES.get(lab_rel) or frozenset()
    for node in _nodes(graph):
        ntype = str(node.get("type") or "")
        assert ntype, f"{lab_rel}: node {node.get('id')} carries no type"
        if ntype in _ENCYCLOPEDIA:
            continue
        note = " (used by this graph alone)" if ntype in singleton else ""
        pytest.fail(f"{lab_rel}: node {node.get('id')} ({ntype}){note} is undocumented")


@pytest.mark.parametrize(PYTEST_PARAM, GRAPHS, ids=GRAPH_IDS)
def test_widget_values_match_a_documented_layout(
    lab_rel: str, graph: dict[str, Any]
) -> None:
    """Widget values fill exactly one documented layout for the class.

    ComfyUI maps ``widgets_values`` positionally, so a value list one entry too
    long or one entry short shifts every widget after it - a wrong weight, a
    wrong step count, a wrong denoise - with the graph still saving green. A node
    that ships two layouts (``MeshToFile3D``, ``VHS_VideoCombine``) may store
    either documented length, and a dict-shaped bag may only use documented keys.

    Args:
        lab_rel: ``_lab``-relative graph id.
        graph: Parsed lab JSON.
    """
    for node in _nodes(graph):
        ntype = str(node.get("type") or "")
        sizes = WIDGET_LAYOUTS.get(ntype)
        assert sizes is not None, f"{lab_rel}: node {node.get('id')} ({ntype}) is undocumented"
        values = node.get("widgets_values")
        if values is None:
            continue
        if isinstance(values, list):
            assert len(values) in sizes, (
                f"{lab_rel}: node {node.get('id')} ({ntype}) stores {len(values)} "
                f"widget values, documented layouts are {sorted(sizes)}"
            )
        elif isinstance(values, Mapping):
            documented = set(WIDGET_SLOTS.get(ntype, {}))
            keys = {str(key) for key in values}
            extra = sorted(keys - documented)
            assert not extra, (
                f"{lab_rel}: node {node.get('id')} ({ntype}) stores widget keys "
                f"{extra} the reference does not document"
            )
        else:
            pytest.fail(
                f"{lab_rel}: node {node.get('id')} ({ntype}) widgets_values is "
                f"{type(values).__name__}, not a list or a mapping"
            )


# ---------------------------------------------------------------------------
# App surface
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(PYTEST_PARAM, GRAPHS, ids=GRAPH_IDS)
def test_app_widget_rows_point_at_a_real_widget(
    lab_rel: str, graph: dict[str, Any]
) -> None:
    """Each ``linearData`` row names a node that exists and a widget it carries.

    A row that points at a widget the node does not have renders an App control
    bound to nothing: the operator types into it and the graph never sees it.

    ``EZDubIngest.upload`` is the one documented exception - an App button label,
    not a serialized widget.

    Args:
        lab_rel: ``_lab``-relative graph id.
        graph: Parsed lab JSON.
    """
    if _app_mode(graph) is None:
        pytest.skip(f"{lab_rel}: not an App graph")
    nodes = _node_index(graph)
    inputs, _outputs = _linear_rows(graph)
    for entry in inputs:
        try:
            node_id = linear_input_node_id(entry)
        except ValueError as exc:
            pytest.fail(f"{lab_rel}: unusable linearData input row {entry!r}: {exc}")
        node = nodes.get(node_id)
        assert node is not None, (
            f"{lab_rel}: linearData row {entry!r} points at node {node_id}, "
            f"which the graph does not have"
        )
        assert isinstance(entry[1], str) and entry[1], (
            f"{lab_rel}: linearData row {entry!r} names no widget"
        )
        widget = str(entry[1])
        allowed = _slot_names(node) | VIRTUAL_APP_WIDGETS.get(
            str(node.get("type") or ""), frozenset()
        )
        assert widget in allowed, (
            f"{lab_rel}: linearData row {entry!r} targets {node.get('type')} "
            f"'{node.get('title')}', which carries no widget '{widget}'. "
            f"Known: {sorted(allowed)}"
        )


@pytest.mark.parametrize(PYTEST_PARAM, GRAPHS, ids=GRAPH_IDS)
def test_no_app_row_surfaces_a_dead_control(
    lab_rel: str, graph: dict[str, Any]
) -> None:
    """A control the App shows must be a control the graph reads.

    Two shapes make a row dead: its node sits bypassed, so the lane never runs
    it, or its node is a source whose outputs all hold no link, so nothing reads
    what the widget sets. Terminal classes are exempt - their job is to write a
    file, not to feed a neighbour - and a node with no output slot at all is a
    widget holder the overlay reads, not a source.

    Args:
        lab_rel: ``_lab``-relative graph id.
        graph: Parsed lab JSON.
    """
    if _app_mode(graph) is None:
        pytest.skip(f"{lab_rel}: not an App graph")
    nodes = _node_index(graph)
    inputs, _outputs = _linear_rows(graph)
    for entry in inputs:
        try:
            node_id = linear_input_node_id(entry)
        except ValueError:
            continue
        node = nodes.get(node_id)
        if node is None:
            continue
        ntype = str(node.get("type") or "")
        label = _effective_label(node, str(entry[1] if len(entry) > 1 else "?"), _row_config(entry))
        assert not _is_bypassed(node), (
            f"{lab_rel}: App row '{label}' is on bypassed {ntype} {node_id}"
        )
        if ntype in TERMINAL_NODE_TYPES or not (node.get("outputs") or []):
            continue
        assert _output_is_wired(node), (
            f"{lab_rel}: App row '{label}' is on {ntype} {node_id}, whose every "
            f"output slot is unwired, so the control changes nothing"
        )


@pytest.mark.parametrize(PYTEST_PARAM, GRAPHS, ids=GRAPH_IDS)
def test_exposed_image_picker_feeds_a_live_consumer(
    lab_rel: str, graph: dict[str, Any]
) -> None:
    """An image picker the App offers must actually reach the sampler.

    The picker set is ``LoadImage``, ``EZOptionalImage``, ``EZSnapImage``, and the
    ``EZDCCLoad*`` guide loaders. A picker whose IMAGE output feeds nothing, or
    feeds only bypassed nodes, is an upload box that changes nothing.

    Args:
        lab_rel: ``_lab``-relative graph id.
        graph: Parsed lab JSON.
    """
    if _app_mode(graph) is None:
        pytest.skip(f"{lab_rel}: not an App graph")
    exposed, _outputs = _linear_rows(graph)
    exposed_ids = set()
    for entry in exposed:
        try:
            exposed_ids.add(linear_input_node_id(entry))
        except ValueError:
            continue
    for node in _nodes(graph):
        if not _is_image_picker(str(node.get("type") or "")):
            continue
        if node.get("id") not in exposed_ids:
            continue
        consumers = _consumers(graph, node, output="IMAGE")
        live = [consumer for consumer in consumers if not _is_bypassed(consumer)]
        assert live, (
            f"{lab_rel}: exposed {node.get('type')} {node.get('id')} "
            f"('{node.get('title')}') feeds {len(consumers)} consumers, none live"
        )


@pytest.mark.parametrize(PYTEST_PARAM, GRAPHS, ids=GRAPH_IDS)
def test_unwired_image_picker_is_a_declared_opt_in(
    lab_rel: str, graph: dict[str, Any]
) -> None:
    """A picker that reads nothing must be a muted opt-in with somewhere to go.

    Three conditions make an unwired picker honest, and all three have to hold:
    the graph declares the class in ``extra.lab_optional_unwired``, the node is
    muted so the canvas shows it switched off, and some other node still has a
    free ``IMAGE`` slot the operator could wire it into. The album ``Cover
    image`` loader beside ``EZAudioMetadata.cover`` is the shape this keeps.

    Anything else is an upload box that changes no pixel while the graph
    pretends to use it. :func:`~_strip_dead_pickers.dead_pickers` is the one
    definition of that shape, shared with the pass that deletes it, so the gate
    cannot drift away from the repair.

    Args:
        lab_rel: ``_lab``-relative graph id.
        graph: Parsed lab JSON.
    """
    assert dead_pickers(graph) == [], (
        f"{lab_rel}: image picker(s) {dead_pickers(graph)} are unmuted, feed "
        "nothing, and have no declared opt-in contract"
    )


@pytest.mark.parametrize(PYTEST_PARAM, GRAPHS, ids=GRAPH_IDS)
def test_wired_image_picker_is_on_the_panel(
    lab_rel: str, graph: dict[str, Any]
) -> None:
    """A still the graph reads is a still the operator can choose.

    The App panel is the only surface an operator has, so a picker that is live
    and wired but absent from ``linearData.inputs`` is an input the App cannot
    fill: the graph renders whatever filename the author left in the widget. The
    one named exception is a lane whose stamp spec sets ``hide_images`` - the
    clay-board app authors its reference stills and says so in
    ``test_dream_house_clay.py``.

    Args:
        lab_rel: ``_lab``-relative graph id.
        graph: Parsed lab JSON.
    """
    if _app_mode(graph) is None:
        pytest.skip(f"{lab_rel}: not an App graph")
    exposed, _outputs = _linear_rows(graph)
    exposed_ids = set()
    for entry in exposed:
        try:
            exposed_ids.add(linear_input_node_id(entry))
        except ValueError:
            continue
    hides_images = bool((STAMP_SPECS.get(lab_rel) or {}).get("hide_images"))
    for node in _nodes(graph):
        ntype = str(node.get("type") or "")
        if not _is_image_picker(ntype) or _is_bypassed(node):
            continue
        if not _output_is_wired(node):
            continue
        if not (node.get("widgets_values") or []):
            # A pass-through like EZSnapImage carries no widget at all, so there
            # is no control to put on the panel; it is wired or it is not.
            continue
        if ntype == "LoadImage" and hides_images:
            continue
        assert node.get("id") in exposed_ids, (
            f"{lab_rel}: {ntype} {node.get('id')} ('{node.get('title')}') feeds "
            "the render but has no App row, so the operator cannot choose it"
        )


@pytest.mark.parametrize(PYTEST_PARAM, GRAPHS, ids=GRAPH_IDS)
def test_app_widget_labels_are_unique(lab_rel: str, graph: dict[str, Any]) -> None:
    """No App shows the operator two controls with the same name.

    The label compared is the one the panel renders: the stamped
    ``linearData`` config label, falling back to what ``display_label`` derives.

    Args:
        lab_rel: ``_lab``-relative graph id.
        graph: Parsed lab JSON.
    """
    if _app_mode(graph) is None:
        pytest.skip(f"{lab_rel}: not an App graph")
    nodes = _node_index(graph)
    inputs, _outputs = _linear_rows(graph)
    seen: dict[str, str] = {}
    for entry in inputs:
        try:
            node_id = linear_input_node_id(entry)
        except ValueError:
            continue
        node = nodes.get(node_id)
        if node is None:
            continue
        name = str(entry[1] if len(entry) > 1 else "?")
        label = _effective_label(node, name, _row_config(entry))
        where = f"{node.get('type')} {node_id} '{name}'"
        assert label not in seen, (
            f"{lab_rel}: label '{label}' is used by both {seen[label]} and {where}"
        )
        seen[label] = where


@pytest.mark.parametrize(PYTEST_PARAM, GRAPHS, ids=GRAPH_IDS)
def test_app_output_rows_name_existing_nodes(
    lab_rel: str, graph: dict[str, Any]
) -> None:
    """``linearData.outputs`` points at nodes the graph actually has.

    Args:
        lab_rel: ``_lab``-relative graph id.
        graph: Parsed lab JSON.
    """
    if _app_mode(graph) is None:
        pytest.skip(f"{lab_rel}: not an App graph")
    nodes = _node_index(graph)
    _inputs, outputs = _linear_rows(graph)
    for entry in outputs:
        try:
            node_id = int(str(entry))
        except (TypeError, ValueError):
            pytest.fail(f"{lab_rel}: linearData output {entry!r} is not a node id")
        assert node_id in nodes, (
            f"{lab_rel}: linearData output {node_id} is not a node "
            f"(graph holds {sorted(nodes)})"
        )


# ---------------------------------------------------------------------------
# Graph hygiene
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(PYTEST_PARAM, GRAPHS, ids=GRAPH_IDS)
def test_save_prefix_is_authored_and_unambiguous(
    lab_rel: str, graph: dict[str, Any]
) -> None:
    """Every save prefix is written, is not the ComfyUI default, and is a path.

    This is the half of the prefix rule no lane can argue with: blank prefixes
    collide in the output folder, the ``ComfyUI`` default is the frontend's
    placeholder, and ``\\`` or ``%`` are not something this repo's output
    tooling resolves. The character-shape rule lives in
    :func:`test_save_prefix_is_safe_text`.

    Args:
        lab_rel: ``_lab``-relative graph id.
        graph: Parsed lab JSON.
    """
    for node_id, ntype, widget, value in _prefix_values(graph):
        assert isinstance(value, str), (
            f"{lab_rel}: {ntype} {node_id} {widget} is {type(value).__name__}: {value!r}"
        )
        problems = _prefix_defects(value)
        assert not problems, (
            f"{lab_rel}: {ntype} {node_id} {widget}={value!r} "
            f"({', '.join(problems)})"
        )


@pytest.mark.parametrize(PYTEST_PARAM, GRAPHS, ids=GRAPH_IDS)
def test_save_prefix_is_safe_text(lab_rel: str, graph: dict[str, Any]) -> None:
    """A save prefix is lowercase path-safe text, or an album track name.

    ``^[a-z0-9_][a-z0-9_\\-/.]*$``: no spaces, no absolute paths, no uppercase,
    and no ``%`` placeholder this repo does not expand. The one exception is the
    album lane, whose saved filename *is* the track listing the operator reads in
    a player (``01 - Brake Fade``); see :data:`ALBUM_TRACK_PREFIX`. Path hygiene
    runs over both shapes in :func:`test_save_prefix_is_authored_and_unambiguous`,
    so the exception buys readable words and no traversal.

    Args:
        lab_rel: ``_lab``-relative graph id.
        graph: Parsed lab JSON.
    """

    for node_id, ntype, widget, value in _prefix_values(graph):
        text = str(value)
        if SAFE_PREFIX.match(text):
            continue
        # The single sanctioned exception: a catalog album ships its track list,
        # and "01 - Brake Fade" is the deliverable. Everything else stays a slug.
        assert lab_rel.startswith(ALBUM_LANE_PREFIX) and ALBUM_TRACK_PREFIX.match(
            text
        ), f"{lab_rel}: {ntype} {node_id} {widget}={text!r} is not safe prefix text"


@pytest.mark.parametrize(PYTEST_PARAM, GRAPHS, ids=GRAPH_IDS)
def test_stamped_lane_is_the_folder(lab_rel: str, graph: dict[str, Any]) -> None:
    """``lab_app_mode.lane`` is the directory the graph sits in.

    Cheap duplicate of the same check in ``test_lab_tree.py``: this gate walks
    every graph anyway, and a lane that disagrees puts an App under a use case it
    is not in.

    Args:
        lab_rel: ``_lab``-relative graph id.
        graph: Parsed lab JSON.
    """
    mode = _app_mode(graph)
    if mode is None:
        pytest.skip(f"{lab_rel}: not an App graph")
    stamped = str(mode.get("lane") or "")
    folder = lab_rel.split("/", 1)[0]
    assert stamped == folder, f"{lab_rel}: lane stamp {stamped!r} is not the folder {folder!r}"


@pytest.mark.parametrize(PYTEST_PARAM, GRAPHS, ids=GRAPH_IDS)
def test_occupancy_is_real_and_matches_the_node_types(
    lab_rel: str, graph: dict[str, Any]
) -> None:
    """The occupancy claim is one of the repo's slots and agrees with the graph.

    The slot list is ``_stamp_app_mode.OCCUPANCIES``. The agreement half reads each
    stack-deciding class's home off the catalog (:func:`_type_home`), so an App
    claiming one family cannot load, sample, or author latents for another - with
    no model name written in this file. Generic utility classes are out of the
    candidate set, and the no-op slots (``none``, ``llm``) claim no family, which
    is why the writers'-room desks may host every family's rewrite node.

    Args:
        lab_rel: ``_lab``-relative graph id.
        graph: Parsed lab JSON.
    """
    mode = _app_mode(graph)
    if mode is None:
        pytest.skip(f"{lab_rel}: not an App graph")
    occupancy = _occupancy(graph)
    assert occupancy in OCCUPANCIES, (
        f"{lab_rel}: occupancy {occupancy!r} is not one of {OCCUPANCIES}"
    )
    if occupancy in NOOP_OCCUPANCIES:
        return
    for node in _nodes(graph):
        ntype = str(node.get("type") or "")
        home = TYPE_HOME.get(ntype)
        if home is None or home in NOOP_OCCUPANCIES:
            continue
        assert home == occupancy, (
            f"{lab_rel}: occupancy {occupancy!r} but the graph carries {ntype} "
            f"(node {node.get('id')}), which {home} graphs own"
        )


@pytest.mark.parametrize(PYTEST_PARAM, GRAPHS, ids=GRAPH_IDS)
def test_latent_pixels_sit_on_the_family_grid(
    lab_rel: str, graph: dict[str, Any]
) -> None:
    """Authored pixels on a latent node divide by what its family needs.

    Klein and Wan need 16, LTX needs 32; the latent nodes are the classes the
    encyclopedia shows creating a ``LATENT`` while documenting ``width`` and
    ``height``. A size widget a link drives is owned by the wiring, so it is
    left alone, as is any family this table does not cover.

    Args:
        lab_rel: ``_lab``-relative graph id.
        graph: Parsed lab JSON.
    """
    occupancy = _occupancy(graph)
    step = LATENT_GRID_BY_OCCUPANCY.get(occupancy)
    if step is None:
        pytest.skip(f"{lab_rel}: occupancy {occupancy!r} authors no pixel grid")
    for node in _nodes(graph):
        if str(node.get("type") or "") not in LATENT_PRODUCER_TYPES:
            continue
        driven = {
            str((slot.get("widget") or {}).get("name"))
            for slot in (node.get("inputs") or [])
            if isinstance(slot, Mapping) and slot.get("link") is not None
        }
        for widget in ("width", "height"):
            value = _widget_value(node, widget)
            if widget in driven or not isinstance(value, int) or isinstance(value, bool):
                continue
            assert value % step == 0, (
                f"{lab_rel}: {node.get('type')} {node.get('id')} {widget}={value} "
                f"is off the {step} px grid {occupancy} needs"
            )


@pytest.mark.parametrize(PYTEST_PARAM, GRAPHS, ids=GRAPH_IDS)
def test_sampler_recipe_is_a_recipe_this_repo_runs(
    lab_rel: str, graph: dict[str, Any]
) -> None:
    """A sampler's steps/CFG pair is one this repo runs on the Spark.

    A sampler authored at :data:`MAX_AUTHORED_STEPS_FOR_DISTILLED` steps or fewer
    is a quick look off a distilled weight, so guidance stays at or under
    :data:`DISTILLED_CFG_CEILING`; anything else is a base recipe and keeps
    guidance inside :data:`BASE_CFG_FLOOR`..:data:`BASE_CFG_CEILING`. Whether the
    graph feeds a distilled weight is read off the weight names it pins
    (:data:`DISTILLED_NEEDLES`), not off a hardcoded model name, and is reported
    with the failure so the reader can see which side of the split the graph is on.

    Outliers the catalog legitimately needs, listed here rather than absorbed into
    a wider band: ``3d/blockout-mesh`` runs the TRELLIS shape stage at 8 steps and
    CFG 7.5, which is the guided TRELLIS recipe the node encyclopedia documents, and
    ``labs/opt-in/still-to-video-a14b`` runs an 8-step Lightning sampler at CFG 5
    where the distillation rides a LoRA no weight name reveals. Both are the whole
    red baseline today; no graph breaks the base-recipe band at all.

    Args:
        lab_rel: ``_lab``-relative graph id.
        graph: Parsed lab JSON.
    """
    pinned = " ".join(name.lower() for _, _, name in _pinned_weight_names(graph))
    distilled = any(needle in pinned for needle in DISTILLED_NEEDLES)
    for node in _nodes(graph):
        if str(node.get("type") or "") not in SAMPLER_NODE_TYPES:
            continue
        steps = _widget_value(node, "steps")
        cfg = _widget_value(node, "cfg")
        if not isinstance(steps, (int, float)) or isinstance(steps, bool):
            continue
        if not isinstance(cfg, (int, float)) or isinstance(cfg, bool):
            continue
        where = f"{lab_rel}: sampler {node.get('id')} '{node.get('title')}'"
        if steps <= MAX_AUTHORED_STEPS_FOR_DISTILLED and float(cfg) > DISTILLED_CFG_CEILING:
            documented = DOCUMENTED_SAMPLER_RECIPES.get(lab_rel)
            if documented is not None:
                pytest.skip(f"{where}: documented recipe - {documented}")
        if steps <= MAX_AUTHORED_STEPS_FOR_DISTILLED:
            assert float(cfg) <= DISTILLED_CFG_CEILING, (
                f"{where} is authored at {steps} steps with CFG {cfg}; a distilled "
                f"quick look stays at or under {DISTILLED_CFG_CEILING} "
                f"(graph pins distilled weights: {distilled})"
            )
        assert BASE_CFG_FLOOR <= float(cfg) <= BASE_CFG_CEILING, (
            f"{where} is authored at CFG {cfg}, outside the "
            f"{BASE_CFG_FLOOR}..{BASE_CFG_CEILING} band a base recipe keeps"
        )


@pytest.mark.parametrize(PYTEST_PARAM, GRAPHS, ids=GRAPH_IDS)
def test_app_carries_a_description_and_a_note(
    lab_rel: str, graph: dict[str, Any]
) -> None:
    """Every App tells the operator what it makes, in prose that names its stack.

    ``lab_description`` and ``lab_note`` are the only prose the Apps panel shows,
    and the note has to name the family it runs (the occupancy id, or the stack
    word the Detail caption uses) so an operator picking from a browsed list is
    not choosing blind. The handoff half of the note rule lives in
    :func:`test_note_names_its_handoff_target`.

    Args:
        lab_rel: ``_lab``-relative graph id.
        graph: Parsed lab JSON.
    """
    mode = _app_mode(graph)
    if mode is None:
        pytest.skip(f"{lab_rel}: not an App graph")
    extra = _extra(graph)
    description = str(extra.get("lab_description") or "").strip()
    note = str(extra.get("lab_note") or "").strip()
    assert description, f"{lab_rel}: extra.lab_description is empty"
    assert note, f"{lab_rel}: extra.lab_note is empty"

    occupancy = _occupancy(graph)
    if occupancy in NOOP_OCCUPANCIES:
        return
    stack = str(presets.STACK_LABEL.get(occupancy) or "").lower().split()[0:1]
    words = {occupancy, *stack}
    low = note.lower()
    assert any(word in low for word in words if word), (
        f"{lab_rel}: lab_note never names its {occupancy!r} family: {note[:120]!r}"
    )


@pytest.mark.parametrize(PYTEST_PARAM, GRAPHS, ids=GRAPH_IDS)
def test_note_names_its_handoff_target(lab_rel: str, graph: dict[str, Any]) -> None:
    """The note points at the next graph the handoff chain names.

    A handoff is the App panel's "run this next"; the note is the prose that has
    to make that jump for the operator, so a stamped chain the note never mentions
    is a chain the operator cannot follow.

    Args:
        lab_rel: ``_lab``-relative graph id.
        graph: Parsed lab JSON.
    """
    mode = _app_mode(graph)
    if mode is None:
        pytest.skip(f"{lab_rel}: not an App graph")
    note = str(_extra(graph).get("lab_note") or "").strip()
    handoff = [str(item) for item in (mode.get("handoff") or [])]
    if not handoff:
        return
    low = note.lower()
    named = [
        item
        for item in handoff
        if item.rsplit("/", 1)[-1].removesuffix(".json").lower() in low
    ]
    assert named, (
        f"{lab_rel}: lab_note names none of its handoff ids {handoff}: "
        f"{note[:120]!r}"
    )


@pytest.mark.parametrize(PYTEST_PARAM, GRAPHS, ids=GRAPH_IDS)
def test_handoff_names_a_shipped_graph(lab_rel: str, graph: dict[str, Any]) -> None:
    """Every handoff id is a graph the catalog ships.

    A handoff is the App panel's "run this next" link; an id that drifted in a
    rename sends the operator to a graph that does not exist. Old spellings still
    resolve, through ``_lab_ids.rel_id``.

    Args:
        lab_rel: ``_lab``-relative graph id.
        graph: Parsed lab JSON.
    """
    mode = _app_mode(graph)
    if mode is None:
        pytest.skip(f"{lab_rel}: not an App graph")
    for item in mode.get("handoff") or []:
        text = str(item).strip().removesuffix(".json").removeprefix("_lab/")
        resolved = rel_id(text)
        candidates = {
            text,
            resolved,
            text.rsplit("/", 1)[-1],
            resolved.rsplit("/", 1)[-1],
        }
        assert candidates & set(SHIPPED_IDS) or candidates & set(SHIPPED_STEMS), (
            f"{lab_rel}: handoff {item!r} matches no shipped graph "
            f"(tried {sorted(candidates)})"
        )


@pytest.mark.parametrize(PYTEST_PARAM, GRAPHS, ids=GRAPH_IDS)
def test_no_banned_weight_is_pinned(lab_rel: str, graph: dict[str, Any]) -> None:
    """No widget pins a weight this studio refuses to ship.

    The needles are imported, never copied: ``_stamp_app_mode.BANNED`` for the
    studio's off-catalog list and ``ez_quality.presets`` for the banned UNET
    test. Only real filename widgets are read, so a note that discusses a banned
    model in prose is not a pinned weight.

    Args:
        lab_rel: ``_lab``-relative graph id.
        graph: Parsed lab JSON.
    """
    for node in _nodes(graph):
        ntype = str(node.get("type") or "")
        if ntype in PROSE_NODE_TYPES:
            continue
        for widget, value in _widget_values_by_name(node):
            if not isinstance(value, str) or not value.strip():
                continue
            text = value.strip()
            for needle in BANNED:
                assert needle.lower() not in text.lower(), (
                    f"{lab_rel}: {ntype} {node.get('id')} {widget} pins "
                    f"{text!r}, which names {needle!r}"
                )
            if widget.endswith(("_name", "name")) and presets.is_banned_unet(text):
                pytest.fail(
                    f"{lab_rel}: {ntype} {node.get('id')} {widget} pins the "
                    f"banned weight {text!r}"
                )


@pytest.mark.parametrize(PYTEST_PARAM, GRAPHS, ids=GRAPH_IDS)
def test_one_quality_node_recording_a_ladder_rung(
    lab_rel: str, graph: dict[str, Any]
) -> None:
    """At most one ``EZQuality`` per graph, holding a rung its family honors.

    Two quality nodes on one graph would each stamp the combo and fight over the
    same sampler widgets. The rung is judged only by the ladder: the family comes
    from ``presets.graph_family`` and legality from ``presets.tier_is_honored``,
    so a rung rename in the ladder moves this gate with it and no rung name is
    written here.

    Args:
        lab_rel: ``_lab``-relative graph id.
        graph: Parsed lab JSON.
    """
    quality_nodes = [
        node for node in _nodes(graph) if str(node.get("type") or "") == "EZQuality"
    ]
    assert len(quality_nodes) <= 1, (
        f"{lab_rel}: {len(quality_nodes)} EZQuality nodes "
        f"{[node.get('id') for node in quality_nodes]}"
    )
    if not quality_nodes:
        return
    node = quality_nodes[0]
    family = presets.graph_family(graph)
    tiers = presets.tiers_for_family(family)
    assert tiers, (
        f"{lab_rel}: EZQuality {node.get('id')} on family {family!r}, which "
        f"carries no rung - the combo would offer a level nothing can apply"
    )
    values = node.get("widgets_values")
    assert isinstance(values, list) and len(values) == 1, (
        f"{lab_rel}: EZQuality {node.get('id')} widgets_values is {values!r}, "
        f"expected one recorded rung"
    )
    rung = values[0]
    assert isinstance(rung, str) and rung.strip(), (
        f"{lab_rel}: EZQuality {node.get('id')} records no rung: {rung!r}"
    )
    assert presets.tier_is_honored(family, rung), (
        f"{lab_rel}: EZQuality {node.get('id')} records {rung!r}, which family "
        f"{family!r} does not honor ({tiers})"
    )


RETIRED_CONTROL_PHRASES: tuple[str, ...] = (
    "Quality combo",
    "Quality ladder",
    "Quality tiers",
    "Quality tier",
    "Quality profile",
    "Quality does not change size",
    "Quality never changes pixels",
    "Quality never swaps",
    "Quality swaps",
    "Quality left on",
    "Quality cannot drive",
    "set Quality",
    "Quality **High**",
    "Quality **Ultra**",
    "Quality **Max**",
    "Quality ultra/max",
    "(Quality flux3",
)
"""Sentences the retired Quality combo left behind in operator-facing copy.

The control is Detail. Any copy that names Quality is teaching an operator a
widget that no longer exists, and the ladder has no rung named high, ultra, max,
lab, or custom either.
"""

CONTENT_WIDGET_TYPES: frozenset[str] = frozenset(
    {
        "EZRapLyrics",
        "EZAceStepPromptEnhance",
        "TextEncodeAceStepAudio1.5",
    }
)
"""Node types whose string widgets hold authored content, not UI copy.

A lyric that happens to rhyme the word "quality" is a lyric, not an instruction
to an operator, so these types are out of scope for this rule.
"""

OPERATOR_EXTRA_KEYS: tuple[str, ...] = ("lab_description", "lab_note", "lab_graph_note")
"""The ``extra`` entries the Apps panel renders as prose."""


def _operator_copy(graph: Mapping[str, Any]) -> list[tuple[str, str]]:
    """Return every string an operator reads in this graph, with its origin.

    Covers the node titles the canvas shows, the string widgets the App panel
    fills, and the ``lab_*`` prose the Apps panel prints. Authored content on
    :data:`CONTENT_WIDGET_TYPES` nodes is skipped: those strings are the work
    the App makes, not instructions to the operator.

    Args:
        graph: Parsed lab JSON.

    Returns:
        ``(where, text)`` pairs, ``where`` naming the node class and id, or the
        ``extra.`` key, for each string found.
    """
    found: list[tuple[str, str]] = []
    for node in _nodes(graph):
        ntype = str(node.get("type") or "")
        node_id = node.get("id")
        for field in ("title", "title_mode"):
            value = node.get(field)
            if isinstance(value, str):
                found.append((f"{ntype} {node_id} {field}", value))
        if ntype in CONTENT_WIDGET_TYPES:
            continue
        values = node.get("widgets_values")
        if isinstance(values, list):
            for index, value in enumerate(values):
                if isinstance(value, str):
                    found.append((f"{ntype} {node_id} widgets_values[{index}]", value))
        elif isinstance(values, Mapping):
            for key, value in values.items():
                if isinstance(value, str):
                    found.append((f"{ntype} {node_id} widgets_values[{key!r}]", value))
    extra = _extra(graph)
    for key in OPERATOR_EXTRA_KEYS:
        value = extra.get(key)
        if isinstance(value, str):
            found.append((f"extra.{key}", value))
    return found


@pytest.mark.parametrize(PYTEST_PARAM, GRAPHS, ids=GRAPH_IDS)
def test_operator_text_never_names_the_retired_combo(
    lab_rel: str, graph: dict[str, Any]
) -> None:
    """No copy the operator reads names the combo this repo retired.

    The control the Apps panel offers is Detail; its rungs are whatever
    ``ez_quality.presets`` honors for the family. Graph Notes, node titles, and
    ``extra.lab_description`` still carry sentences the Quality combo wrote, and
    an operator who reads "set Quality **High**" looks for a widget that is gone.
    The match is case-sensitive on purpose: "quality of the still" is English,
    "Quality" as a control name is the defect.

    Args:
        lab_rel: ``_lab``-relative graph id.
        graph: Parsed lab JSON.
    """
    for where, text in _operator_copy(graph):
        for phrase in RETIRED_CONTROL_PHRASES:
            assert phrase not in text, (
                f"{lab_rel}: {where} names the retired Quality combo "
                f"({phrase!r}): {text[:160]!r}"
            )
