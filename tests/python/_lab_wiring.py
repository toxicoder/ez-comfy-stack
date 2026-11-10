"""Static wiring contract between the nodes of one shipped lab graph.

ComfyUI resolves a graph only at Queue time. A link row that disagrees with the
slot bookkeeping, a link whose type does not match its socket pair, a required
sampler input left unwired, or an App with no terminal node all land green in
the UI and die on the GPU box after the operator pressed Run. ComfyUI stores
every one of those facts twice - once in the ``links`` table and once inside
each node's ``inputs`` / ``outputs`` slots - and trusts both at load. This
module proves the two agree offline. The companion ``_lab_node_catalog`` gate
covers class names and widget widths; this one covers the wiring.
"""

from __future__ import annotations

import functools
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from _lab_paths import ROOT

# Classes that write a file or a visible preview. Every shipped App needs at
# least one, or the graph burns GPU time and produces nothing to show. For
# first-party ez_* nodes the authoritative marker is OUTPUT_NODE = True in the
# class body, harvested below instead of duplicated here.
TERMINAL_TYPES = frozenset(
    {
        "PreviewAudio",
        "PreviewImage",
        "SaveAnimatedPNG",
        "SaveAnimatedWEBP",
        "SaveAudio",
        "SaveAudioMP3",
        "SaveGLB",
        "SaveImage",
        "SaveWEBM",
        "VHS_VideoCombine",
    }
)

_CLASS_DEF = re.compile(r"^class\s+(\w+)", re.MULTILINE)
_OUTPUT_NODE = re.compile(r"^\s*OUTPUT_NODE\s*=\s*True\b", re.MULTILINE)


def custom_output_node_types(root: Path) -> frozenset[str]:
    """Class names under ``root`` that ComfyUI treats as OUTPUT_NODE.

    Args:
        root: The ``custom_nodes/`` tree to harvest.

    Returns:
        Every first-party class whose body sets ``OUTPUT_NODE = True``.
    """
    types: set[str] = set()
    for path in sorted(root.rglob("*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        marks = [(m.group(1), m.start()) for m in _CLASS_DEF.finditer(text)]
        for index, (name, start) in enumerate(marks):
            end = marks[index + 1][1] if index + 1 < len(marks) else len(text)
            if _OUTPUT_NODE.search(text[start:end]):
                types.add(name)
    return frozenset(types)


@functools.lru_cache(maxsize=1)
def _terminal_types() -> frozenset[str]:
    return TERMINAL_TYPES | custom_output_node_types(ROOT / "custom_nodes")

# Input sockets ComfyUI marks required: the node raises at Queue when one is
# unwired. Kept to classes whose core semantics are settled, so the gate never
# needs an optionality debate to stay green.
REQUIRED_INPUTS: dict[str, frozenset[str]] = {
    "CLIPTextEncode": frozenset({"clip"}),
    "ConditioningZeroOut": frozenset({"conditioning"}),
    "KSampler": frozenset({"model", "positive", "negative", "latent_image"}),
    "ModelSamplingAuraFlow": frozenset({"model"}),
    "SaveImage": frozenset({"images"}),
    "VAEDecode": frozenset({"samples", "vae"}),
    "VAEEncode": frozenset({"pixels", "vae"}),
}

# widget_values index per class whose positional widgets gate a Queue-time
# range: KSampler per docs/workflow_nodes_lib.ksampler_widgets().
_SAMPLER_RANGES: tuple[tuple[str, int, float, float, bool], ...] = (
    # (label, widget index, low, high, exclusive_low)
    ("steps", 2, 1, 10_000, False),
    ("cfg", 3, 0.0, 100.0, False),
    ("denoise", 6, 0.0, 1.0, True),
)


def _is_number(value: Any) -> bool:
    """True for a real number, bools excluded (True is 1 under isinstance)."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _linked_widget_names(node: Mapping[str, Any]) -> set[str]:
    """Widget names a link overrides, so their stored values are inert.

    Args:
        node: One node dict.

    Returns:
        Names of widgets converted to inputs and currently fed by a link.
    """
    linked: set[str] = set()
    for slot in node.get("inputs") or []:
        if slot.get("link") is None:
            continue
        widget = slot.get("widget") or {}
        name = widget.get("name")
        if isinstance(name, str):
            linked.add(name)
    return linked


def _slot_has_link(slot: Mapping[str, Any]) -> bool:
    """True when an input slot is fed, via ``link`` or a stacked ``links``."""
    if slot.get("link") is not None:
        return True
    links = slot.get("links")
    return isinstance(links, list) and bool(links)


def _link_table_findings(
    graph: Mapping[str, Any],
    nodes: Mapping[Any, Mapping[str, Any]],
) -> tuple[list[str], set[Any]]:
    """Walk the link table and cross-check both sides' bookkeeping.

    Args:
        graph: A parsed lab graph dict.
        nodes: ``{node id: node dict}`` for the same graph.

    Returns:
        Findings plus the set of link ids the table declares.
    """
    problems: list[str] = []
    seen: set[Any] = set()
    for row in graph.get("links") or []:
        if not isinstance(row, (list, tuple)) or len(row) != 6:
            link_id = row[0] if isinstance(row, (list, tuple)) and row else "?"
            problems.append(f"link {link_id}: row is not a 6-field link")
            if isinstance(link_id, int):
                seen.add(link_id)
            continue
        link_id, origin_id, origin_slot, target_id, target_slot, link_type = row
        if link_id in seen:
            problems.append(f"link {link_id}: duplicate link id")
            continue
        seen.add(link_id)
        origin = nodes.get(origin_id)
        target = nodes.get(target_id)
        if origin is None:
            problems.append(f"link {link_id}: origin node {origin_id} does not exist")
            continue
        if target is None:
            problems.append(f"link {link_id}: target node {target_id} does not exist")
            continue
        if origin_id == target_id:
            problems.append(f"link {link_id}: node {origin_id} links to itself")
            continue
        outputs = origin.get("outputs") or []
        inputs = target.get("inputs") or []
        if not isinstance(origin_slot, int) or not 0 <= origin_slot < len(outputs):
            problems.append(
                f"link {link_id}: origin slot {origin_slot} out of range "
                f"on node {origin_id} ({len(outputs)} outputs)"
            )
            continue
        if not isinstance(target_slot, int) or not 0 <= target_slot < len(inputs):
            problems.append(
                f"link {link_id}: target slot {target_slot} out of range "
                f"on node {target_id} ({len(inputs)} inputs)"
            )
            continue
        out_slot = outputs[origin_slot]
        if link_id not in (out_slot.get("links") or []):
            problems.append(f"link {link_id}: absent from node {origin_id} output slot {origin_slot} links")
        in_slot = inputs[target_slot]
        if in_slot.get("link") != link_id:
            problems.append(f"link {link_id}: absent from node {target_id} input slot {target_slot}")
        for slot, role, node_id in ((out_slot, "output", origin_id), (in_slot, "input", target_id)):
            slot_type = slot.get("type")
            if isinstance(slot_type, str) and slot_type != link_type:
                problems.append(
                    f"link {link_id}: type {link_type} does not match "
                    f"node {node_id} {role} slot {origin_slot if role == 'output' else target_slot} "
                    f"type {slot_type}"
                )
    return problems, seen


def _slot_bookkeeping_findings(
    graph: Mapping[str, Any],
    table_ids: set[Any],
) -> list[str]:
    """Flag slot-side references the link table never declared."""
    problems: list[str] = []
    for node in graph.get("nodes") or []:
        node_id = node.get("id")
        for slot_index, slot in enumerate(node.get("inputs") or []):
            claimed = slot.get("link")
            if claimed is not None and claimed not in table_ids:
                problems.append(
                    f"node {node_id} input slot {slot_index} claims link {claimed} "
                    "that is not in the link table"
                )
        for slot_index, slot in enumerate(node.get("outputs") or []):
            for claimed in slot.get("links") or []:
                if claimed not in table_ids:
                    problems.append(
                        f"node {node_id} output slot {slot_index} claims link {claimed} "
                        "that is not in the link table"
                    )
    return problems


def _required_input_findings(graph: Mapping[str, Any]) -> list[str]:
    """Flag required sockets (per ComfyUI core semantics) left unwired."""
    problems: list[str] = []
    for node in graph.get("nodes") or []:
        required = REQUIRED_INPUTS.get(str(node.get("type") or ""))
        if not required:
            continue
        slots: dict[str, list[Mapping[str, Any]]] = {}
        for slot in node.get("inputs") or []:
            name = slot.get("name")
            if isinstance(name, str):
                slots.setdefault(name, []).append(slot)
        for name in sorted(required):
            candidates = slots.get(name) or []
            if not candidates:
                problems.append(f"node {node.get('id')} ({node.get('type')}): required input '{name}' has no slot")
            elif not any(_slot_has_link(slot) for slot in candidates):
                problems.append(f"node {node.get('id')} ({node.get('type')}): required input '{name}' is unwired")
    return problems


def _widget_findings(node: Mapping[str, Any]) -> list[str]:
    """Range and authoring checks on the widgets that gate a clean Queue.

    ``widgets_values`` arrives as a positional list in classic exports and as
    a name-keyed dict in newer frontend saves; the positional rules apply to
    the list shape only, the authoring rules read the dict by key.
    """
    problems: list[str] = []
    node_id = node.get("id")
    ntype = str(node.get("type") or "")
    raw = node.get("widgets_values")
    values: Sequence[Any] = raw if isinstance(raw, list) else []
    named: Mapping[str, Any] = raw if isinstance(raw, dict) else {}
    linked = _linked_widget_names(node)

    if ntype == "LoadImage" and "image" not in linked:
        first = named.get("image", values[0] if values else None)
        if not (isinstance(first, str) and first.strip()):
            problems.append(f"node {node_id} (LoadImage): image widget is not authored")
    if ntype == "KSampler" and len(values) == 7:
        for label, index, low, high, exclusive_low in _SAMPLER_RANGES:
            if label in linked:
                continue
            value = values[index]
            if _is_number(value) and not (value > low if exclusive_low else value >= low):
                problems.append(f"node {node_id} (KSampler): {label} must be >= {low}, got {value}")
            elif _is_number(value) and value > high:
                bound = "in (0, 1]" if exclusive_low else f"in [{low}, {high}]"
                problems.append(f"node {node_id} (KSampler): {label} must be {bound}, got {value}")
    if ntype == "EmptyFlux2LatentImage" and len(values) == 3:
        for label, index in (("width", 0), ("height", 1)):
            value = values[index]
            if label in linked or not _is_number(value):
                continue
            if value <= 0 or value % 8:
                problems.append(
                    f"node {node_id} (EmptyFlux2LatentImage): {label} {value} is off the 8 px latent grid"
                )
        batch = values[2]
        if "batch_size" not in linked and _is_number(batch) and batch < 1:
            problems.append(f"node {node_id} (EmptyFlux2LatentImage): batch_size must be >= 1, got {batch}")
    if ntype == "VHS_VideoCombine" and "filename_prefix" not in linked:
        prefix = named.get("filename_prefix", values[2] if len(values) > 2 else None)
        if not (isinstance(prefix, str) and prefix.strip()):
            problems.append(f"node {node_id} (VHS_VideoCombine): filename_prefix is not authored")
    return problems


def wiring_findings(graph: Mapping[str, Any]) -> list[str]:
    """Check one loaded graph for wiring defects.

    Args:
        graph: A parsed lab graph dict.

    Returns:
        One line per violation, naming the offending node or link id. Empty
        when the graph satisfies the contract.
    """
    problems: list[str] = []
    nodes: dict[Any, Mapping[str, Any]] = {}
    for node in graph.get("nodes") or []:
        node_id = node.get("id")
        if node_id in nodes:
            problems.append(f"duplicate node id {node_id}")
            continue
        nodes[node_id] = node
    table_findings, table_ids = _link_table_findings(graph, nodes)
    problems.extend(table_findings)
    problems.extend(_slot_bookkeeping_findings(graph, table_ids))
    problems.extend(_required_input_findings(graph))
    for node in graph.get("nodes") or []:
        problems.extend(_widget_findings(node))
    if not any(str(node.get("type") or "") in _terminal_types() for node in graph.get("nodes") or []):
        problems.append("graph has no terminal output node")
    return problems
