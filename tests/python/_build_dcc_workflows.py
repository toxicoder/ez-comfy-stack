#!/usr/bin/env python3
"""Build P0 DCC lab graphs from existing Klein / LTX envelopes.

Run from repo root:
  python3 tests/python/_build_dcc_workflows.py
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from _stamp_app_mode import stamp_suite_graph

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "workflows"
DCC = WF / "dcc"

KLEIN_NOTE = """## klein-from-clay-lab-example

Klein 4B **edit** of a DCC clay first frame (guide pack ``first.png``). Enhance **on**. Seed **42**. Size **1280x704** (LTX VAE grid — not 1280x720).

LoadImage: clay ``first.png`` from ``guides/<slug>/<shot>/``. Prefix ``ez_clay_hero``.

Unload before LTX. Do not Queue this graph and a DCC dump in one session (occupancy).

Prompt: inventory + look. Motion comes later from the pack. Official clay is Workbench / unshaded, not Cycles beauty.
"""

LTX_NOTE = """## ltx-iclora-depth-5s-lab-example

Lab envelope for Path B depth-guided 5.00s print. LTX canvas 1280x704 (width/height must be divisible by 32; 720 and 1080 are invalid). **120 frames @ 24 fps**. MagCache **off**. Distilled transformer only.

This tree does **not** vendor Lightricks UUID subgraphs. Queue the official Templates graph:

  Templates → LTX-2.5 → LTX-2.5_ICLoRA_Union_Control_Distilled.json

Depth is wired by default. LoRA (opt-in, not download-models):

  ./scripts/manage.sh download-ltx --tier iclora
  ltx-2.3-22b-ic-lora-union-control-ref0.5.safetensors
  (Lightricks/LTX-2.3-22b-IC-LoRA-Union-Control — official 2.5 graph widgets this 2.3 Union file)

Refuse 19B Union. Do not pair IC-LoRA with a dev transformer.

This envelope keeps the lab 5.00s / INT8-convrot / EZFilmDisclosure contract so print-shot can grow ``--from-guide`` later. LoadImage: guide ``first.png``. Wire depth.mp4 in the Templates graph.

LTX Community License: $10M COMPANY cap, disclose AI-generated media, do not strip provenance, do not distill.
"""


def _load(name: str) -> dict:
    return json.loads((WF / name).read_text(encoding="utf-8"))


def _save(graph: dict, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    stamp_suite_graph(graph)
    dest.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")


def build_klein_from_clay() -> dict:
    graph = _load("klein-still-hero-lab-example.json")
    graph["id"] = "klein-from-clay-lab-example"
    extra = graph.setdefault("extra", {})
    extra["lab_profile"] = "klein-from-clay-lab-example"
    extra["lab_note"] = KLEIN_NOTE
    extra["lab_description"] = "Klein 4B edit of DCC clay first.png. Enhance on. 1280x704. Seed 42."
    extra["lab_dcc"] = {
        "enhance": True,
        "mode": "edit",
        "seed": 42,
        "size": [1280, 704],
        "prefix": "ez_clay_hero",
    }
    for node in graph["nodes"]:
        ntype = node.get("type")
        if ntype == "EZKleinPromptEnhance":
            widgets = list(node.get("widgets_values") or [])
            while len(widgets) < 5:
                widgets.append("")
            widgets[0] = (
                "Keep the clay blocking, camera, and silhouette from the start image. "
                "Finish as a HD 3D game-engine pre-rendered cutscene still: PBR materials, "
                "cinematic three-point light, unmarked surfaces empty of lettering. "
                "Do not redesign layout."
            )
            widgets[1] = True
            widgets[2] = "edit"
            widgets[3] = "YouTube 16:9 still from clay"
            widgets[4] = "none"
            node["widgets_values"] = widgets
            node["title"] = "Klein Prompt Enhance (edit)"
        elif ntype == "SaveImage":
            node["widgets_values"] = ["ez_clay_hero"]
            node["title"] = "Save clay hero"
        elif ntype == "LoadImage":
            node["widgets_values"] = ["first.png", "image"]
            node["title"] = "Clay first.png (guide pack)"
        elif ntype == "KSampler":
            widgets = list(node.get("widgets_values") or [])
            if widgets:
                widgets[0] = 42
                widgets[1] = "fixed"
            node["widgets_values"] = widgets
        elif ntype == "EmptyFlux2LatentImage":
            node["widgets_values"] = [1280, 704, 1]
        elif ntype == "Note":
            node["widgets_values"] = [KLEIN_NOTE]
            node["title"] = "Operator note"
    # Wire LoadImage → VAEEncode → ReferenceLatent on the positive CLIP.
    max_id = max(int(n["id"]) for n in graph["nodes"])
    max_link = max(int(link[0]) for link in graph.get("links") or [ [0] ])
    load = next(n for n in graph["nodes"] if n.get("type") == "LoadImage")
    vae = next(n for n in graph["nodes"] if n.get("type") == "VAELoader")
    pos = next(n for n in graph["nodes"] if n.get("type") == "CLIPTextEncode" and n.get("title") != "Negative")
    sampler = next(n for n in graph["nodes"] if n.get("type") == "KSampler")
    encode_id = max_id + 1
    ref_id = max_id + 2
    link_img = max_link + 1
    link_vae = max_link + 2
    link_cond = max_link + 3
    link_lat = max_link + 4
    link_pos = max_link + 5
    graph["nodes"].append(
        {
            "id": encode_id,
            "type": "VAEEncode",
            "pos": [2180, 420],
            "size": [240, 80],
            "flags": {},
            "order": 20,
            "mode": 0,
            "inputs": [
                {"name": "pixels", "type": "IMAGE", "link": link_img},
                {"name": "vae", "type": "VAE", "link": link_vae},
            ],
            "outputs": [
                {"name": "LATENT", "type": "LATENT", "links": [link_lat], "slot_index": 0}
            ],
            "properties": {"Node name for S&R": "VAEEncode"},
            "widgets_values": [],
            "title": "Encode clay plate",
        }
    )
    graph["nodes"].append(
        {
            "id": ref_id,
            "type": "ReferenceLatent",
            "pos": [940, 80],
            "size": [280, 80],
            "flags": {},
            "order": 21,
            "mode": 0,
            "inputs": [
                {"name": "conditioning", "type": "CONDITIONING", "link": link_cond},
                {"name": "latent", "type": "LATENT", "link": link_lat, "shape": 7},
            ],
            "outputs": [
                {"name": "CONDITIONING", "type": "CONDITIONING", "links": [link_pos], "slot_index": 0}
            ],
            "properties": {"Node name for S&R": "ReferenceLatent"},
            "widgets_values": [],
            "title": "Positive + clay plate",
        }
    )
    # Rewire sampler positive from CLIP encode to ReferenceLatent.
    old_pos_link = None
    for inp in sampler.get("inputs") or []:
        if inp.get("name") == "positive":
            old_pos_link = inp.get("link")
            inp["link"] = link_pos
    graph["links"] = [link for link in graph.get("links") or [] if int(link[0]) != old_pos_link]
    for out in pos.get("outputs") or []:
        links = out.get("links")
        if isinstance(links, list) and old_pos_link in links:
            out["links"] = [lid for lid in links if lid != old_pos_link] + [link_cond]
        elif isinstance(links, list):
            out["links"] = list(links) + [link_cond]
    load_out = load["outputs"][0]
    load_links = load_out.get("links") or []
    if not isinstance(load_links, list):
        load_links = []
    load_out["links"] = list(load_links) + [link_img]
    vae_out = vae["outputs"][0]
    vae_links = vae_out.get("links") or []
    if not isinstance(vae_links, list):
        vae_links = []
    vae_out["links"] = list(vae_links) + [link_vae]
    graph["links"].extend(
        [
            [link_img, int(load["id"]), 0, encode_id, 0, "IMAGE"],
            [link_vae, int(vae["id"]), 0, encode_id, 1, "VAE"],
            [link_cond, int(pos["id"]), 0, ref_id, 0, "CONDITIONING"],
            [link_lat, encode_id, 0, ref_id, 1, "LATENT"],
            [link_pos, ref_id, 0, int(sampler["id"]), 1, "CONDITIONING"],
        ]
    )
    graph["last_node_id"] = ref_id
    graph["last_link_id"] = link_pos
    return graph


def build_ltx_iclora() -> dict:
    graph = copy.deepcopy(_load("ltx-i2v-shot-lab-example.json"))
    graph["id"] = "ltx-iclora-depth-5s-lab-example"
    extra = graph.setdefault("extra", {})
    extra["lab_profile"] = "ltx-iclora-depth-5s-lab-example"
    extra["lab_note"] = LTX_NOTE
    extra["lab_description"] = "LTX-2.5 IC-LoRA Union Control envelope, 120 frames, depth default"
    extra["lab_iclora"] = {
        "templates": "LTX-2.5_ICLoRA_Union_Control_Distilled.json",
        "lora": "ltx-2.3-22b-ic-lora-union-control-ref0.5.safetensors",
        "repo": "Lightricks/LTX-2.3-22b-IC-LoRA-Union-Control",
        "tier": "iclora",
        "distilled_only": True,
        "frames": 120,
        "size": [1280, 704],
        "depth_default": True,
        "magcache": False,
    }
    extra["lab_disclosure"] = "LTX Community License"
    extra.pop("lab_magcache", None)
    for node in graph["nodes"]:
        if node.get("type") == "Note":
            node["widgets_values"] = [LTX_NOTE]
            node["title"] = "Operator note"
        elif node.get("type") == "LoadImage":
            node["widgets_values"] = ["first.png", "image"]
            node["title"] = "Guide first.png"
        elif node.get("type") == "VHS_VideoCombine":
            widgets = node.get("widgets_values")
            if isinstance(widgets, dict):
                widgets["filename_prefix"] = "ez_iclora_depth"
            elif isinstance(widgets, list) and widgets:
                widgets[0] = "ez_iclora_depth"
            node["widgets_values"] = widgets
    max_id = max(int(n["id"]) for n in graph["nodes"])
    graph["nodes"].append(
        {
            "id": max_id + 1,
            "type": "EZFilmDisclosure",
            "pos": [40, 900],
            "size": [420, 120],
            "flags": {},
            "order": max_id + 1,
            "mode": 0,
            "inputs": [],
            "outputs": [
                {"name": "text", "type": "STRING", "links": None, "slot_index": 0}
            ],
            "properties": {"Node name for S&R": "EZFilmDisclosure"},
            "widgets_values": [""],
            "title": "LTX AI-media disclosure (end-card)",
        }
    )
    graph["last_node_id"] = max_id + 1
    blob = json.dumps(graph)
    if "MagCache" in blob and '"type": "MagCache"' in blob:
        raise SystemExit("iclora envelope must not include MagCache nodes")
    return graph


def main() -> int:
    klein = build_klein_from_clay()
    ltx = build_ltx_iclora()
    _save(klein, DCC / "klein-from-clay-lab-example.json")
    _save(ltx, DCC / "ltx-iclora-depth-5s-lab-example.json")
    print(f"wrote {DCC / 'klein-from-clay-lab-example.json'}")
    print(f"wrote {DCC / 'ltx-iclora-depth-5s-lab-example.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
