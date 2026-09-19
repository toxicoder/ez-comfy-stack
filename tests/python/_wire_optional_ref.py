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
        link id → link row.
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
    opt_node = {
        "id": opt_id,
        "type": OPTIONAL_TYPE,
        "pos": [-400.0, 400.0],
        "size": [360.0, 120.0],
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
        "widgets_values": [""],
        "title": "Example / reference (optional)",
    }
    canvas_node = {
        "id": canvas_id,
        "type": CANVAS_TYPE,
        "pos": [-400.0, 720.0],
        "size": [360.0, 140.0],
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
        "widgets_values": [False],
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
    vae_out = next(s for s in vae["outputs"] if s.get("name") == "VAE")
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
    extra = graph.setdefault("extra", {})
    linear = extra.setdefault("linearData", {})
    inputs = linear.setdefault("inputs", [])
    if not any(row[1] == "filename" and row[0] == opt_id for row in inputs if len(row) > 1):
        inputs.append(
            [
                opt_id,
                "filename",
                {
                    "label": "Example / reference (optional)",
                    "description": "Optional still. Empty is valid — Queue without a file. When set, Klein uses it as a native reference.",
                },
            ]
        )
    return graph
