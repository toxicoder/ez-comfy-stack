"""Insert EZOptionalImage + EZKleinRefCanvas on Klein T2I lab graphs.

Not collected by pytest. Builders and one-shot wiring import
``wire_optional_ref``.
"""

from __future__ import annotations

from typing import Any

OPTIONAL_TYPE = "EZOptionalImage"
CANVAS_TYPE = "EZKleinRefCanvas"
LATENT_TYPE = "EmptyFlux2LatentImage"
SAMPLER_TYPE = "KSampler"
VAE_TYPE = "VAELoader"

# Positional widgets_values, in INPUT_TYPES widget order. The first entry is the
# frozen "filename" picker; the toggle sits next to it so the off state is visible.
OPT_WIDGETS: list[Any] = ["", True, "", ""]
CANVAS_WIDGETS: list[Any] = [False, 3]
# ComfyUI recomputes node height from the widget list at load, so the stored
# size stays at the layout the lane collision test was tuned against.
OPT_SIZE: list[float] = [360.0, 120.0]
CANVAS_SIZE: list[float] = [360.0, 140.0]

REF_TOGGLE = "use_references"
REF_TOGGLE_LABEL = "Use reference stills"
REF_TOGGLE_DESCRIPTION = (
    "Turn off to run text-to-image without clearing your picks. Any new pick "
    "turns it back on."
)


def _next_id(graph: dict[str, Any], key: str) -> int:
    """Return the next integer id for nodes or links.

    Args:
        graph: Serialized graph.
        key: ``last_node_id`` or ``last_link_id``.

    Returns:
        Next id.
    """
    last = int(graph.get(key) or 0)
    return last + 1


def _link_map(graph: dict[str, Any]) -> dict[int, list[Any]]:
    """Index links by id.

    Args:
        graph: Serialized graph.

    Returns:
        link id -> link row.
    """
    return {int(row[0]): row for row in graph.get("links") or []}


def wire_optional_ref(graph: dict[str, Any]) -> dict[str, Any]:
    """Rewire EmptyFlux2LatentImage through an optional Klein reference canvas.

    Skip edit graphs that already use ReferenceLatent, and graphs that already
    have EZKleinRefCanvas.

    Args:
        graph: Serialized Comfy graph (mutated).

    Returns:
        The same graph dict.
    """
    types = {str(node.get("type") or "") for node in graph.get("nodes") or []}
    if CANVAS_TYPE in types or OPTIONAL_TYPE in types:
        return graph
    if "ReferenceLatent" in types:
        return graph
    latent = next((n for n in graph["nodes"] if n.get("type") == LATENT_TYPE), None)
    sampler = next((n for n in graph["nodes"] if n.get("type") == SAMPLER_TYPE), None)
    vae = next((n for n in graph["nodes"] if n.get("type") == VAE_TYPE), None)
    if latent is None or sampler is None or vae is None:
        return graph
    links = graph.setdefault("links", [])
    latent_out = None
    for row in links:
        if int(row[1]) == int(latent["id"]) and row[5] == "LATENT":
            latent_out = row
            break
    if latent_out is None:
        return graph
    opt_id = _next_id(graph, "last_node_id")
    canvas_id = opt_id + 1
    graph["last_node_id"] = canvas_id
    pos_l = latent.get("pos") or [948, 544]
    opt_node: dict[str, Any] = {
        "id": opt_id,
        "type": OPTIONAL_TYPE,
        "pos": [-400.0, 400.0],
        "size": list(OPT_SIZE),
        "flags": {},
        "order": int(latent.get("order") or 0) + 1,
        "mode": 0,
        "inputs": [],
        "outputs": [
            {"name": "image", "type": "IMAGE", "links": [], "slot_index": 0},
            {"name": "count", "type": "INT", "links": None, "slot_index": 1},
            {"name": "has_image", "type": "BOOLEAN", "links": [], "slot_index": 2},
        ],
        "properties": {"Node name for S&R": OPTIONAL_TYPE},
        "widgets_values": list(OPT_WIDGETS),
        "title": "Example / reference (optional)",
    }
    canvas_node: dict[str, Any] = {
        "id": canvas_id,
        "type": CANVAS_TYPE,
        "pos": [-400.0, 720.0],
        "size": list(CANVAS_SIZE),
        "flags": {},
        "order": int(latent.get("order") or 0) + 2,
        "mode": 0,
        "inputs": [
            {"name": "latent", "type": "LATENT", "link": None},
            {"name": "vae", "type": "VAE", "link": None},
            {"name": "image", "type": "IMAGE", "link": None},
            {"name": "has_image", "type": "BOOLEAN", "link": None},
        ],
        "outputs": [
            {"name": "latent", "type": "LATENT", "links": [], "slot_index": 0},
            {"name": "image", "type": "IMAGE", "links": None, "slot_index": 1},
        ],
        "properties": {"Node name for S&R": CANVAS_TYPE},
        "widgets_values": list(CANVAS_WIDGETS),
        "title": "Optional Klein ref",
    }
    graph["nodes"].append(opt_node)
    graph["nodes"].append(canvas_node)
    link_latent = _next_id(graph, "last_link_id")
    link_vae = link_latent + 1
    link_img = link_vae + 1
    link_flag = link_img + 1
    link_out = link_flag + 1
    graph["last_link_id"] = link_out
    sampler_slot = int(latent_out[4])
    latent_out[3] = canvas_id
    latent_out[4] = 0
    canvas_node["inputs"][0]["link"] = int(latent_out[0])
    vae_out = next(
        slot
        for slot in vae["outputs"]
        if isinstance(slot, dict) and slot.get("name") == "VAE"
    )
    vae_links = vae_out.setdefault("links", [])
    if vae_links is None:
        vae_links = []
        vae_out["links"] = vae_links
    vae_links.append(link_vae)
    canvas_node["inputs"][1]["link"] = link_vae
    links.append([link_vae, int(vae["id"]), 0, canvas_id, 1, "VAE"])
    opt_node["outputs"][0]["links"] = [link_img]
    canvas_node["inputs"][2]["link"] = link_img
    links.append([link_img, opt_id, 0, canvas_id, 2, "IMAGE"])
    opt_node["outputs"][2]["links"] = [link_flag]
    canvas_node["inputs"][3]["link"] = link_flag
    links.append([link_flag, opt_id, 2, canvas_id, 3, "BOOLEAN"])
    canvas_node["outputs"][0]["links"] = [link_out]
    samp_in = next(i for i in sampler["inputs"] if i.get("name") == "latent_image")
    samp_in["link"] = link_out
    links.append([link_out, canvas_id, 0, int(sampler["id"]), sampler_slot, "LATENT"])
    _stamp_panel_inputs(graph, opt_id)
    return graph


def _stamp_panel_inputs(graph: dict[str, Any], opt_id: int) -> None:
    """Add App Mode panel rows for the optional reference node.

    Globals:
        REF_TOGGLE: widget name of the mute toggle.
        REF_TOGGLE_LABEL: panel label for the toggle.
        REF_TOGGLE_DESCRIPTION: panel help text for the toggle.

    Arguments:
        graph: Serialized Comfy graph (mutated).
        opt_id: Node id of the EZOptionalImage node.

    Outputs:
        None. Appends [node id, widget, config] rows to extra.linearData.inputs
        and keeps the toggle directly after the filename row so the panel reads
        as one control group. Rows that already exist are left untouched.

    Returns:
        None.
    """
    extra = graph.setdefault("extra", {})
    linear = extra.setdefault("linearData", {})
    inputs = linear.setdefault("inputs", [])

    def _row_index(widget: str) -> int:
        for index, row in enumerate(inputs):
            if len(row) > 1 and row[0] == opt_id and row[1] == widget:
                return index
        return -1

    if _row_index("filename") < 0:
        inputs.append(
            [
                opt_id,
                "filename",
                {
                    "label": "Example / reference (optional)",
                    "description": "Optional still. Empty is valid - Queue without a file. When set, Klein uses it as a native reference.",
                },
            ]
        )
    if _row_index(REF_TOGGLE) < 0:
        toggle = [
            opt_id,
            REF_TOGGLE,
            {"label": REF_TOGGLE_LABEL, "description": REF_TOGGLE_DESCRIPTION},
        ]
        after = _row_index("filename")
        if after < 0:
            inputs.append(toggle)
        else:
            inputs.insert(after + 1, toggle)


def _merge_widgets(existing: list[Any], defaults: list[Any]) -> list[Any]:
    """Fill missing widget slots without overwriting what an operator set.

    Arguments:
        existing: Stored positional widgets_values, possibly shorter than the
            current node definition.
        defaults: Positional values for the current node definition.

    Returns:
        A list as long as defaults, keeping any stored value that is present.
    """
    merged: list[Any] = []
    for index, default in enumerate(defaults):
        if index < len(existing) and existing[index] is not None:
            merged.append(existing[index])
        else:
            merged.append(default)
    return merged


def refresh_optional_ref_widgets(graph: dict[str, Any]) -> bool:
    """Bring existing optional-ref nodes up to the current widget literals.

    Graphs committed before the reference card stored only the single filename
    picker, so their extra widgets sat at node-definition defaults and the mute
    toggle never reached the App Mode panel. Missing slots are filled from the
    current literals and a filename an operator already chose is kept, which
    keeps every lane identical to what wire_optional_ref emits today without
    discarding a set. Idempotent.

    Globals:
        OPT_WIDGETS: positional widgets for EZOptionalImage.
        CANVAS_WIDGETS: positional widgets for EZKleinRefCanvas.
        OPT_SIZE: node height that fits three pickers.
        CANVAS_SIZE: node height that fits the max_refs row.

    Arguments:
        graph: Serialized Comfy graph (mutated).

    Outputs:
        None.

    Returns:
        True when anything changed.
    """
    changed = False
    opt_id = None
    for node in graph.get("nodes") or []:
        ntype = str(node.get("type") or "")
        if ntype not in (OPTIONAL_TYPE, CANVAS_TYPE):
            continue
        widgets = OPT_WIDGETS if ntype == OPTIONAL_TYPE else CANVAS_WIDGETS
        size = OPT_SIZE if ntype == OPTIONAL_TYPE else CANVAS_SIZE
        if ntype == OPTIONAL_TYPE:
            opt_id = int(node["id"])
        merged = _merge_widgets(list(node.get("widgets_values") or []), list(widgets))
        if merged != list(node.get("widgets_values") or []):
            node["widgets_values"] = merged
            changed = True
        if list(node.get("size") or []) != list(size):
            node["size"] = list(size)
            changed = True
    if opt_id is not None:
        inputs = ((graph.get("extra") or {}).get("linearData") or {}).get("inputs") or []
        before = len(inputs)
        toggle_present = any(
            len(row) > 1 and row[0] == opt_id and row[1] == REF_TOGGLE for row in inputs
        )
        _stamp_panel_inputs(graph, opt_id)
        changed = changed or not toggle_present or before != len(inputs)
    return changed
