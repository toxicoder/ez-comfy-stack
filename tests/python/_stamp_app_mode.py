"""Reusable ComfyUI App Mode stamp for lab graphs.

Not imported by pytest collection (leading underscore). Tests import
``stamp_app_mode``. Builders call it after writing extra.lab_profile /
lab_note / lab_description.

Official persist: extra.linearData = {inputs, outputs}
  LinearInput = [widgetId, widgetName, config?]
  widgetId = "{node.id}:{widgetName}" when the node exists
Lab contract: extra.lab_app_mode
Do not require extra.linearMode (upstream does not write it; lab sugar only).
"""

from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

FRONTEND_MIN = "1.41.13"
LANES = ("inspire", "produce", "audio", "film", "dcc")
OCCUPANCIES = ("llm", "klein", "wan", "ltx", "audio", "film", "none")
DEFAULT_VIEWS = ("app", "graph")
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

NodeRef = int | str
InputSpec = tuple[NodeRef, str] | tuple[NodeRef, str, Mapping[str, Any] | None]


def _banned_hit(blob: str) -> str | None:
    for needle in BANNED:
        if needle in blob:
            return needle
    return None


def _assert_clean(payload: Any, *, where: str) -> None:
    hit = _banned_hit(json.dumps(payload, default=str))
    if hit is not None:
        raise ValueError(f"banned string {hit!r} in {where}")


def _find_nodes(graph: dict, ref: NodeRef) -> list[dict]:
    nodes = list(graph.get("nodes") or [])
    if isinstance(ref, int) or (isinstance(ref, str) and ref.isdigit()):
        nid = int(ref)
        return [n for n in nodes if int(n["id"]) == nid]
    titled = [n for n in nodes if n.get("title") == ref]
    if titled:
        return titled
    return [n for n in nodes if n.get("type") == ref]


def _resolve_node(graph: dict, ref: NodeRef, *, kind: str) -> dict:
    hits = _find_nodes(graph, ref)
    if not hits:
        raise ValueError(f"missing {kind} node {ref!r}")
    if len(hits) > 1:
        raise ValueError(f"ambiguous {kind} node {ref!r} ({len(hits)} matches)")
    return hits[0]


def _parse_input(spec: InputSpec) -> tuple[NodeRef, str, Mapping[str, Any] | None]:
    if not isinstance(spec, (tuple, list)) or len(spec) < 2:
        raise ValueError(f"invalid input spec {spec!r}")
    node_ref, widget_name = spec[0], spec[1]
    if not isinstance(widget_name, str) or not widget_name:
        raise ValueError(f"missing widget name for node {node_ref!r}")
    config = spec[2] if len(spec) > 2 else None
    return node_ref, widget_name, config


def stamp_app_mode(
    graph: dict,
    *,
    inputs: Sequence[InputSpec],
    outputs: Sequence[NodeRef],
    lane: str,
    occupancy: str,
    handoff: Sequence[str] = (),
    default_view: str = "app",
    enhance_off_identity: bool = False,
) -> dict:
    """Write extra.lab_app_mode and extra.linearData. Preserve other extra keys.

    Args:
        graph: Serialized Comfy graph (mutated in place).
        inputs: (node title|id|unique type, widgetName[, config]).
        outputs: Node title|id|unique type for SaveImage / VHS_VideoCombine.
        lane: inspire | produce | audio | film | dcc.
        occupancy: llm | klein | wan | ltx | audio | film | none.
        handoff: Downstream app ids (workflow stems).
        default_view: app | graph.
        enhance_off_identity: True when the identity/bible enhance toggle is off.

    Returns:
        The same graph dict.

    Raises:
        ValueError: missing/ambiguous node, bad lane/occupancy, or banned string.
    """
    if lane not in LANES:
        raise ValueError(f"invalid lane {lane!r}")
    if occupancy not in OCCUPANCIES:
        raise ValueError(f"invalid occupancy {occupancy!r}")
    if default_view not in DEFAULT_VIEWS:
        raise ValueError(f"invalid default_view {default_view!r}")

    _assert_clean(
        {
            "lane": lane,
            "occupancy": occupancy,
            "default_view": default_view,
            "handoff": list(handoff),
            "inputs": list(inputs),
            "outputs": list(outputs),
        },
        where="stamp labels",
    )

    linear_inputs: list[list] = []
    for spec in inputs:
        node_ref, widget_name, config = _parse_input(spec)
        node = _resolve_node(graph, node_ref, kind="input")
        widget_id = f"{node['id']}:{widget_name}"
        entry: list = [widget_id, widget_name]
        if config:
            entry.append(dict(config))
        linear_inputs.append(entry)

    linear_outputs: list[int] = []
    for ref in outputs:
        node = _resolve_node(graph, ref, kind="output")
        linear_outputs.append(int(node["id"]))

    extra = graph.setdefault("extra", {})
    extra["lab_app_mode"] = {
        "enabled": True,
        "default_view": default_view,
        "frontend_min": FRONTEND_MIN,
        "lane": lane,
        "occupancy": occupancy,
        "enhance_off_identity": bool(enhance_off_identity),
        "handoff": [str(item) for item in handoff],
    }
    extra["linearData"] = {
        "inputs": linear_inputs,
        "outputs": linear_outputs,
    }
    if default_view == "app":
        extra["linearMode"] = True
    else:
        extra.pop("linearMode", None)

    _assert_clean(extra["lab_app_mode"], where="lab_app_mode")
    _assert_clean(extra["linearData"], where="linearData")
    return graph
