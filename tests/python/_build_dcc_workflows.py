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

from _lab_layout import GROUP_TITLE_INSET, group as _group, ensure_group_title_inset
from _lab_paths import lab_dest, lab_json
from _stamp_app_mode import stamp_suite_graph

KLEIN_NOTE = """## klein-from-clay-lab-example

Klein 4B **edit** of a DCC clay first frame (guide pack ``first.png``). Enhance **on**. Seed **42**. Size **1280x704** (LTX VAE grid — not 1280x720).

LoadImage: clay ``first.png`` from ``guides/<slug>/<shot>/``. Prefix ``ez_clay_hero``.

After Queue, overlay-qc the look against clay (host ffmpeg; compose may stay up):

  ./scripts/manage.sh overlay-qc --film <slug> --shot <id> --look PATH

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

Stop Klein first. After print, stop LTX and run audio-finish / stem-mix (occupancy audio). Joint AV is a world bed, not a master.

LTX Community License: $10M COMPANY cap, disclose AI-generated media, do not strip provenance, do not distill.
"""

CANNY_STILL_NOTE = """## klein-from-canny-lab-example

Klein 4B **edit** of a DCC line-art plate (guide pack ``canny/`` first frame, or still ``canny.png``). Enhance **on**. Seed **42**. Size **1280x704**.

LoadImage: ``canny.png`` (copy from ``guides/<slug>/<shot>/canny/`` or ``blender-stills --install-inputs``). Prefix ``ez_canny_hero``.

Keep the silhouette and camera from the line art. Finish materials and light. Do not redesign layout.

Unload before LTX. Occupancy: klein. Handoff: ltx-iclora-canny-5s.
"""

CLAY_PLATES_NOTE = """## klein-from-clay-plates-lab-example

One clay still, four Klein **edit** plates. Enhance **on**. Seed **42**. Ctrl+B unused SHOT groups.

Prefixes and sizes:
- ez_clay_pack_hero 1280x704 (LTX feeder)
- ez_clay_pack_packshot 1024x1024 (1:1)
- ez_clay_pack_ig 1024x1280 (Instagram 4:5)
- ez_clay_pack_shorts 768x1280 (9:16 / LTX portrait)

LoadImage: clay ``first.png``. Each plate scales the clay to its latent. Occupancy: klein.
Handoff: wan-i2v-5s / wan-shorts-i2v / ltx-iclora-depth-shorts.
"""

LTX_CANNY_NOTE = """## ltx-iclora-canny-5s-lab-example

Lab envelope for Path B **canny**-guided 5.00s print. LTX canvas 1280x704 (width/height must be divisible by 32; 720 and 1080 are invalid). **120 frames @ 24 fps**. MagCache **off**. Distilled transformer only.

This tree does **not** vendor Lightricks UUID subgraphs. Queue the official Templates graph:

  Templates → LTX-2.5 → LTX-2.5_ICLoRA_Union_Control_Distilled.json

Switch the annotator to **canny**. Wire ``canny.mp4`` from the guide pack. LoRA (opt-in, not download-models):

  ./scripts/manage.sh download-ltx --tier iclora
  ltx-2.3-22b-ic-lora-union-control-ref0.5.safetensors

Refuse 19B Union. Do not pair IC-LoRA with a dev transformer.

LoadImage: guide ``first.png``. Stop Klein first. After print, audio-finish / stem-mix.

LTX Community License: $10M COMPANY cap, disclose AI-generated media, do not strip provenance, do not distill.
"""

LTX_SHORTS_NOTE = """## ltx-iclora-depth-shorts-lab-example

Lab envelope for Path B depth-guided **portrait** 5.00s print. LTX canvas **768x1280** (width/height must be divisible by 32; 720 and 1080 are invalid). **120 frames @ 24 fps**. MagCache **off**. Distilled transformer only.

Dump the pack with:

  ./scripts/manage.sh export-guides --film SLUG --shot ID --width 768 --height 1280 --print ltx-iclora-depth

Queue Templates → LTX-2.5 → LTX-2.5_ICLoRA_Union_Control_Distilled.json. Depth default. Opt-in ``download-ltx --tier iclora``. Refuse 19B Union.

Prefix ``ez_iclora_depth_shorts``. Occupancy: ltx. Handoff: audio-finish.
"""

WAN_FLF_GUIDE_NOTE = """## wan-flf-from-guide-lab-example

Silent Fun InP first-last-frame from a DCC guide pack. LoadImage ``first.png`` and ``last.png``. MagCache **off**. Opt-in:

  ./scripts/manage.sh download-wan --tier fun-inp

Unload LTX first. Occupancy: wan. This is a continuity draft, not the LTX AV print.

Prefix ``ez_flf_guide``. 832x480, 121 frames (Wan 5B / Fun InP default). The pack is 1280x704; the latent node resizes.
"""

STAY_IN_COMFY = (
    "Stay on :8188 after a dump: klein-from-guide-loader-lab-example / "
    "ltx-iclora-from-guide-loader-lab-example / trellis-from-klein-still-lab-example "
    "(EZDCCLoadGuideStill + OccupancyGate). The LoadImage + --install-inputs path "
    "on this graph still works."
)

KLEIN_NOTE = KLEIN_NOTE.rstrip() + "\n\n" + STAY_IN_COMFY + "\n"
LTX_NOTE = LTX_NOTE.rstrip() + "\n\n" + STAY_IN_COMFY + "\n"
CANNY_STILL_NOTE = CANNY_STILL_NOTE.rstrip() + "\n\n" + STAY_IN_COMFY + "\n"
CLAY_PLATES_NOTE = CLAY_PLATES_NOTE.rstrip() + "\n\n" + STAY_IN_COMFY + "\n"
LTX_CANNY_NOTE = LTX_CANNY_NOTE.rstrip() + "\n\n" + STAY_IN_COMFY + "\n"
LTX_SHORTS_NOTE = LTX_SHORTS_NOTE.rstrip() + "\n\n" + STAY_IN_COMFY + "\n"
WAN_FLF_GUIDE_NOTE = WAN_FLF_GUIDE_NOTE.rstrip() + "\n\n" + STAY_IN_COMFY + "\n"

KLEIN_LOADER_NOTE = """## klein-from-guide-loader-lab-example

Klein 4B **edit** of a guide-pack still loaded in-canvas (no LoadImage / --install-inputs). Enhance **on**. Seed **42**. Size **1280x704**. Prefix ``ez_guide_hero``.

Occupancy: **klein**. Wire: EZDCCLoadGuideStill ``layer=first`` → OccupancyGate → Klein envelope. Defaults: slug ``go-see``, shot_id ``12``.

```bash
./scripts/manage.sh occupancy enter blender-desk
./scripts/manage.sh export-guides --film go-see --shot 12 --blend /path/to/shot.blend --print ltx-iclora-depth
./scripts/manage.sh occupancy enter klein --yes
```

blender-desk fails the gate (park is for dumps). After Queue, overlay-qc. Path D: laptop dump, rsync ``guides/``, Spark Comfy. Stay on :8188.
"""

LTX_LOADER_NOTE = """## ltx-iclora-from-guide-loader-lab-example

Lab envelope for Path B depth-guided 5.00s print from in-canvas loaders. LTX canvas **1280x704** (width/height must be divisible by 32; 720 and 1080 are invalid). **120 frames @ 24 fps**. MagCache **off**. Distilled transformer only. Prefix ``ez_iclora_guide``.

Occupancy: **ltx**. EZDCCLoadGuideStill ``first`` → OccupancyGate. EZDCCLoadGuideVideo returns the ``depth.mp4`` path (do not decode 120 frames). This tree does **not** vendor Lightricks UUID subgraphs.

  Templates → LTX-2.5 → LTX-2.5_ICLoRA_Union_Control_Distilled.json

Opt-in: ``./scripts/manage.sh download-ltx --tier iclora``. Refuse 19B Union. No 1280x720. Stop Klein first.

LTX Community License: $10M COMPANY cap, disclose AI-generated media, do not strip provenance, do not distill.
"""

TRELLIS_LOADER_NOTE = """## trellis-from-klein-still-lab-example

Still pack plate → native TRELLIS.2 INT8 mesh (Comfy core nodes). Occupancy: **trellis**.

```bash
./scripts/manage.sh download-3d --tier trellis2
./scripts/manage.sh occupancy enter trellis --yes
```

EZDCCLoadStillPack slug ``go-see`` plate ``mug`` → OccupancyGate → EZUnloadModels → TRELLIS.2 INT8. Save under ``assets/objects/_lab-mug/`` (output tree, never MODELS_DIR). Do not mint an Asset Bible row from this graph.

No Preview3D / Load3D / Save3D types in-tree — inspect the GLB with core Load 3D / Preview 3D after Queue. Native INT8 only.
"""

CLAY_PLATES = (
    ("hero", "ez_clay_pack_hero", 1280, 704),
    ("packshot", "ez_clay_pack_packshot", 1024, 1024),
    ("ig", "ez_clay_pack_ig", 1024, 1280),
    ("shorts", "ez_clay_pack_shorts", 768, 1280),
)

CLAY_FINISH = (
    "Keep the clay blocking, camera, and silhouette from the start image. "
    "Finish as a photoreal still: physically plausible light, natural materials, "
    "unmarked surfaces empty of lettering. "
    "Do not redesign layout."
)
CANNY_FINISH = (
    "Keep the line-art silhouette, camera, and layout from the start image. "
    "Finish as a photoreal still inside those edges. Unmarked surfaces. "
    "Do not invent new geometry."
)


def _load(name: str) -> dict:
    return json.loads(lab_json(name).read_text(encoding="utf-8"))


def _save(graph: dict, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    stamp_suite_graph(graph)
    ensure_group_title_inset(graph)
    dest.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")


def _max_ids(graph: dict) -> tuple[int, int]:
    max_id = max(int(n["id"]) for n in graph["nodes"])
    max_link = 0
    for link in graph.get("links") or []:
        max_link = max(max_link, int(link[0]))
    return max_id, max_link


def _append_out_link(node: dict, slot: int, link_id: int) -> None:
    outs = node["outputs"][slot]
    links = outs.get("links")
    if not isinstance(links, list):
        links = []
    links.append(link_id)
    outs["links"] = links


def _add_link(
    graph: dict,
    link_id: int,
    from_id: int,
    from_slot: int,
    to_id: int,
    to_slot: int,
    ltype: str,
) -> None:
    graph.setdefault("links", []).append(
        [link_id, from_id, from_slot, to_id, to_slot, ltype]
    )


def _replace_load_image(
    graph: dict,
    *,
    ntype: str,
    title: str,
    widgets: list,
) -> dict:
    """Swap the first LoadImage for an ez_dcc loader. Keep IMAGE outbound links."""
    load = next(n for n in graph["nodes"] if n.get("type") == "LoadImage")
    old_links: list = []
    if load.get("outputs"):
        raw = load["outputs"][0].get("links") or []
        if isinstance(raw, list):
            old_links = list(raw)
    load["type"] = ntype
    load["title"] = title
    load["widgets_values"] = list(widgets)
    load["properties"] = {"Node name for S&R": ntype}
    load["inputs"] = []
    load["outputs"] = [
        {"name": "image", "type": "IMAGE", "links": old_links, "slot_index": 0},
        {"name": "mask", "type": "MASK", "links": None, "slot_index": 1},
        {"name": "metadata", "type": "STRING", "links": None, "slot_index": 2},
    ]
    return load


def _insert_occupancy_gate(
    graph: dict, *, source: dict, required_mode: str
) -> dict:
    """Insert EZDCCOccupancyGate on the source IMAGE output."""
    max_id, max_link = _max_ids(graph)
    gate_id = max_id + 1
    link_in = max_link + 1
    out = source["outputs"][0]
    old_links = [int(lid) for lid in (out.get("links") or []) if lid is not None]
    for link in graph.get("links") or []:
        if int(link[0]) in old_links:
            link[1] = gate_id
            link[2] = 0
    pos = source.get("pos") or [40, 40]
    gate = {
        "id": gate_id,
        "type": "EZDCCOccupancyGate",
        "pos": [int(pos[0]) + 360, int(pos[1])],
        "size": [280, 90],
        "flags": {},
        "order": gate_id,
        "mode": 0,
        "inputs": [{"name": "image", "type": "IMAGE", "link": link_in}],
        "outputs": [
            {
                "name": "image",
                "type": "IMAGE",
                "links": old_links,
                "slot_index": 0,
            }
        ],
        "properties": {"Node name for S&R": "EZDCCOccupancyGate"},
        "widgets_values": [required_mode],
        "title": f"Occupancy gate ({required_mode})",
    }
    graph["nodes"].append(gate)
    out["links"] = [link_in]
    _add_link(graph, link_in, int(source["id"]), 0, gate_id, 0, "IMAGE")
    graph["last_node_id"] = gate_id
    graph["last_link_id"] = max(int(graph.get("last_link_id") or 0), link_in)
    return gate


def _add_guide_video_node(graph: dict, *, layer: str = "depth") -> dict:
    """Unwired video-path loader (envelope only — do not decode frames)."""
    max_id, _max_link = _max_ids(graph)
    nid = max_id + 1
    node = {
        "id": nid,
        "type": "EZDCCLoadGuideVideo",
        "pos": [40, 720],
        "size": [320, 130],
        "flags": {},
        "order": nid,
        "mode": 0,
        "inputs": [],
        "outputs": [
            {"name": "path", "type": "STRING", "links": None, "slot_index": 0},
            {"name": "fps", "type": "INT", "links": None, "slot_index": 1},
        ],
        "properties": {"Node name for S&R": "EZDCCLoadGuideVideo"},
        "widgets_values": ["go-see", "12", layer],
        "title": "Load guide video path",
    }
    graph["nodes"].append(node)
    graph["last_node_id"] = nid
    return node


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
    clay_finish = (
        "Keep the clay blocking, camera, and silhouette from the start image. "
        "Finish as a photoreal still: physically plausible light, natural materials, "
        "unmarked surfaces empty of lettering. "
        "Do not redesign layout."
    )
    for node in graph["nodes"]:
        ntype = node.get("type")
        if ntype == "EZKleinPromptEnhance":
            widgets = list(node.get("widgets_values") or [])
            while len(widgets) < 5:
                widgets.append("")
            widgets[0] = clay_finish
            widgets[1] = True
            widgets[2] = "edit"
            widgets[3] = "YouTube 16:9 still from clay"
            widgets[4] = "none"
            node["widgets_values"] = widgets
            node["title"] = "Klein Prompt Enhance (edit)"
        elif ntype == "CLIPTextEncode" and node.get("title") != "Negative":
            node["widgets_values"] = [clay_finish]
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


def _retitle_note(graph: dict, text: str) -> None:
    extra = graph.setdefault("extra", {})
    extra["lab_note"] = text
    for node in graph["nodes"]:
        if node.get("type") == "Note":
            node["widgets_values"] = [text]
            node["title"] = "Operator note"


def build_klein_from_canny() -> dict:
    graph = build_klein_from_clay()
    graph["id"] = "klein-from-canny-lab-example"
    extra = graph.setdefault("extra", {})
    extra["lab_profile"] = "klein-from-canny-lab-example"
    extra["lab_description"] = (
        "Klein 4B edit of DCC canny.png. Enhance on. 1280x704. Seed 42."
    )
    extra["lab_dcc"] = {
        "enhance": True,
        "mode": "edit",
        "seed": 42,
        "size": [1280, 704],
        "prefix": "ez_canny_hero",
        "guide": "canny",
    }
    _retitle_note(graph, CANNY_STILL_NOTE)
    for node in graph["nodes"]:
        ntype = node.get("type")
        if ntype == "EZKleinPromptEnhance":
            widgets = list(node.get("widgets_values") or [])
            while len(widgets) < 5:
                widgets.append("")
            widgets[0] = CANNY_FINISH
            widgets[1] = True
            widgets[2] = "edit"
            widgets[3] = "YouTube 16:9 still from line art"
            widgets[4] = "none"
            node["widgets_values"] = widgets
        elif ntype == "CLIPTextEncode" and node.get("title") != "Negative":
            node["widgets_values"] = [CANNY_FINISH]
        elif ntype == "SaveImage":
            node["widgets_values"] = ["ez_canny_hero"]
            node["title"] = "Save canny hero"
        elif ntype == "LoadImage":
            node["widgets_values"] = ["canny.png", "image"]
            node["title"] = "Canny first.png (guide pack)"
        elif ntype == "VAEEncode":
            node["title"] = "Encode canny plate"
        elif ntype == "ReferenceLatent":
            node["title"] = "Positive + canny plate"
    return graph


def _insert_image_scale(graph: dict, width: int, height: int, title: str) -> int:
    """Rewire LoadImage → ImageScale → VAEEncode. Returns ImageScale id."""
    load = next(n for n in graph["nodes"] if n.get("type") == "LoadImage")
    encode = next(n for n in graph["nodes"] if n.get("type") == "VAEEncode")
    pix = next(inp for inp in encode["inputs"] if inp.get("name") == "pixels")
    old_link = pix.get("link")
    max_id, max_link = _max_ids(graph)
    scale_id = max_id + 1
    link_in = max_link + 1
    link_out = max_link + 2
    graph["nodes"].append(
        {
            "id": scale_id,
            "type": "ImageScale",
            "pos": [1880, 420],
            "size": [280, 130],
            "flags": {},
            "order": 19,
            "mode": 0,
            "inputs": [{"name": "image", "type": "IMAGE", "link": link_in}],
            "outputs": [
                {
                    "name": "IMAGE",
                    "type": "IMAGE",
                    "links": [link_out],
                    "slot_index": 0,
                }
            ],
            "properties": {"Node name for S&R": "ImageScale"},
            "widgets_values": ["lanczos", int(width), int(height), "center"],
            "title": title,
        }
    )
    graph["links"] = [link for link in graph.get("links") or [] if int(link[0]) != old_link]
    load_out = load["outputs"][0]
    load_links = [lid for lid in (load_out.get("links") or []) if lid != old_link]
    load_out["links"] = load_links + [link_in]
    pix["link"] = link_out
    _add_link(graph, link_in, int(load["id"]), 0, scale_id, 0, "IMAGE")
    _add_link(graph, link_out, scale_id, 0, int(encode["id"]), 0, "IMAGE")
    graph["last_node_id"] = scale_id
    graph["last_link_id"] = link_out
    return scale_id


def _append_clay_plate(
    graph: dict,
    *,
    label: str,
    prefix: str,
    width: int,
    height: int,
    y: int,
) -> None:
    load = next(n for n in graph["nodes"] if n.get("type") == "LoadImage")
    vae = next(n for n in graph["nodes"] if n.get("type") == "VAELoader")
    unet = next(n for n in graph["nodes"] if n.get("type") == "UNETLoader")
    pos = next(
        n
        for n in graph["nodes"]
        if n.get("type") == "CLIPTextEncode" and n.get("title") != "Negative"
    )
    neg = next(
        n
        for n in graph["nodes"]
        if n.get("type") == "CLIPTextEncode" and n.get("title") == "Negative"
    )
    max_id, max_link = _max_ids(graph)
    scale_id = max_id + 1
    encode_id = max_id + 2
    ref_id = max_id + 3
    lat_id = max_id + 4
    ks_id = max_id + 5
    dec_id = max_id + 6
    save_id = max_id + 7
    l_img = max_link + 1
    l_scale = max_link + 2
    l_vae = max_link + 3
    l_cond = max_link + 4
    l_lat = max_link + 5
    l_pos = max_link + 6
    l_model = max_link + 7
    l_neg = max_link + 8
    l_empty = max_link + 9
    l_dec = max_link + 10
    l_vae2 = max_link + 11
    l_save = max_link + 12
    x0 = 520
    graph["nodes"].extend(
        [
            {
                "id": scale_id,
                "type": "ImageScale",
                "pos": [x0, y],
                "size": [280, 130],
                "flags": {},
                "order": scale_id,
                "mode": 0,
                "inputs": [{"name": "image", "type": "IMAGE", "link": l_img}],
                "outputs": [
                    {"name": "IMAGE", "type": "IMAGE", "links": [l_scale], "slot_index": 0}
                ],
                "properties": {"Node name for S&R": "ImageScale"},
                "widgets_values": ["lanczos", width, height, "center"],
                "title": f"Scale {label}",
            },
            {
                "id": encode_id,
                "type": "VAEEncode",
                "pos": [x0 + 320, y],
                "size": [240, 80],
                "flags": {},
                "order": encode_id,
                "mode": 0,
                "inputs": [
                    {"name": "pixels", "type": "IMAGE", "link": l_scale},
                    {"name": "vae", "type": "VAE", "link": l_vae},
                ],
                "outputs": [
                    {"name": "LATENT", "type": "LATENT", "links": [l_lat], "slot_index": 0}
                ],
                "properties": {"Node name for S&R": "VAEEncode"},
                "widgets_values": [],
                "title": f"Encode {label}",
            },
            {
                "id": ref_id,
                "type": "ReferenceLatent",
                "pos": [x0 + 600, y],
                "size": [280, 80],
                "flags": {},
                "order": ref_id,
                "mode": 0,
                "inputs": [
                    {"name": "conditioning", "type": "CONDITIONING", "link": l_cond},
                    {"name": "latent", "type": "LATENT", "link": l_lat, "shape": 7},
                ],
                "outputs": [
                    {
                        "name": "CONDITIONING",
                        "type": "CONDITIONING",
                        "links": [l_pos],
                        "slot_index": 0,
                    }
                ],
                "properties": {"Node name for S&R": "ReferenceLatent"},
                "widgets_values": [],
                "title": f"Positive + {label}",
            },
            {
                "id": lat_id,
                "type": "EmptyFlux2LatentImage",
                "pos": [x0 + 920, y],
                "size": [280, 106],
                "flags": {},
                "order": lat_id,
                "mode": 0,
                "inputs": [],
                "outputs": [
                    {"name": "LATENT", "type": "LATENT", "links": [l_empty], "slot_index": 0}
                ],
                "properties": {"Node name for S&R": "EmptyFlux2LatentImage"},
                "widgets_values": [width, height, 1],
                "title": f"Size {width}x{height}",
            },
            {
                "id": ks_id,
                "type": "KSampler",
                "pos": [x0 + 1240, y],
                "size": [320, 262],
                "flags": {},
                "order": ks_id,
                "mode": 0,
                "inputs": [
                    {"name": "model", "type": "MODEL", "link": l_model},
                    {"name": "positive", "type": "CONDITIONING", "link": l_pos},
                    {"name": "negative", "type": "CONDITIONING", "link": l_neg},
                    {"name": "latent_image", "type": "LATENT", "link": l_empty},
                ],
                "outputs": [
                    {"name": "LATENT", "type": "LATENT", "links": [l_dec], "slot_index": 0}
                ],
                "properties": {"Node name for S&R": "KSampler"},
                "widgets_values": [42, "fixed", 4, 1.0, "euler", "simple", 1.0],
                "title": f"Sampler {label}",
            },
            {
                "id": dec_id,
                "type": "VAEDecode",
                "pos": [x0 + 1600, y],
                "size": [240, 46],
                "flags": {},
                "order": dec_id,
                "mode": 0,
                "inputs": [
                    {"name": "samples", "type": "LATENT", "link": l_dec},
                    {"name": "vae", "type": "VAE", "link": l_vae2},
                ],
                "outputs": [
                    {"name": "IMAGE", "type": "IMAGE", "links": [l_save], "slot_index": 0}
                ],
                "properties": {"Node name for S&R": "VAEDecode"},
                "widgets_values": [],
                "title": f"Decode {label}",
            },
            {
                "id": save_id,
                "type": "SaveImage",
                "pos": [x0 + 1880, y],
                "size": [280, 270],
                "flags": {},
                "order": save_id,
                "mode": 0,
                "inputs": [{"name": "images", "type": "IMAGE", "link": l_save}],
                "outputs": [],
                "properties": {"Node name for S&R": "SaveImage"},
                "widgets_values": [prefix],
                "title": f"Save {label}",
            },
        ]
    )
    _append_out_link(load, 0, l_img)
    _append_out_link(vae, 0, l_vae)
    _append_out_link(vae, 0, l_vae2)
    _append_out_link(unet, 0, l_model)
    _append_out_link(pos, 0, l_cond)
    _append_out_link(neg, 0, l_neg)
    _add_link(graph, l_img, int(load["id"]), 0, scale_id, 0, "IMAGE")
    _add_link(graph, l_scale, scale_id, 0, encode_id, 0, "IMAGE")
    _add_link(graph, l_vae, int(vae["id"]), 0, encode_id, 1, "VAE")
    _add_link(graph, l_cond, int(pos["id"]), 0, ref_id, 0, "CONDITIONING")
    _add_link(graph, l_lat, encode_id, 0, ref_id, 1, "LATENT")
    _add_link(graph, l_pos, ref_id, 0, ks_id, 1, "CONDITIONING")
    _add_link(graph, l_model, int(unet["id"]), 0, ks_id, 0, "MODEL")
    _add_link(graph, l_neg, int(neg["id"]), 0, ks_id, 2, "CONDITIONING")
    _add_link(graph, l_empty, lat_id, 0, ks_id, 3, "LATENT")
    _add_link(graph, l_dec, ks_id, 0, dec_id, 0, "LATENT")
    _add_link(graph, l_vae2, int(vae["id"]), 0, dec_id, 1, "VAE")
    _add_link(graph, l_save, dec_id, 0, save_id, 0, "IMAGE")
    graph["last_node_id"] = save_id
    graph["last_link_id"] = l_save
    groups = graph.setdefault("groups", [])
    groups.append(
        _group(
            20 + len(groups),
            f"SHOT {label}",
            x0 - 20,
            y - GROUP_TITLE_INSET,
            2200,
            340,
            "#3f789e",
        )
    )


def build_klein_from_clay_plates() -> dict:
    graph = build_klein_from_clay()
    graph["id"] = "klein-from-clay-plates-lab-example"
    extra = graph.setdefault("extra", {})
    extra["lab_profile"] = "klein-from-clay-plates-lab-example"
    extra["lab_description"] = (
        "Klein 4B edit of one clay still into four creator plates. Enhance on. Seed 42."
    )
    extra["lab_dcc"] = {
        "enhance": True,
        "mode": "edit",
        "seed": 42,
        "plates": [
            {"id": label, "prefix": prefix, "size": [width, height]}
            for label, prefix, width, height in CLAY_PLATES
        ],
    }
    _retitle_note(graph, CLAY_PLATES_NOTE)
    hero_w, hero_h = CLAY_PLATES[0][2], CLAY_PLATES[0][3]
    _insert_image_scale(graph, hero_w, hero_h, "Scale hero")
    for node in graph["nodes"]:
        if node.get("type") == "SaveImage":
            node["widgets_values"] = [CLAY_PLATES[0][1]]
            node["title"] = "Save hero"
        elif node.get("type") == "EmptyFlux2LatentImage":
            node["widgets_values"] = [hero_w, hero_h, 1]
            node["title"] = f"Size {hero_w}x{hero_h}"
    for i, (label, prefix, width, height) in enumerate(CLAY_PLATES[1:], start=1):
        _append_clay_plate(
            graph,
            label=label,
            prefix=prefix,
            width=width,
            height=height,
            y=80 + i * 380,
        )
    return graph


def _set_ltx_canvas(graph: dict, width: int, height: int) -> None:
    for node in graph["nodes"]:
        ntype = node.get("type")
        widgets = node.get("widgets_values")
        if ntype == "LTXVImgToVideo" and isinstance(widgets, list) and len(widgets) >= 2:
            widgets[0] = width
            widgets[1] = height
        elif ntype in {"EmptyLTXVLatentVideo", "LTXVEmptyLatentAudio"} and isinstance(
            widgets, list
        ):
            if widgets and isinstance(widgets[0], int) and widgets[0] in {1280, 768}:
                widgets[0] = width
            if len(widgets) > 1 and isinstance(widgets[1], int) and widgets[1] in {704, 1280}:
                widgets[1] = height


def _set_vhs_prefix(graph: dict, prefix: str) -> None:
    for node in graph["nodes"]:
        if node.get("type") != "VHS_VideoCombine":
            continue
        widgets = node.get("widgets_values")
        if isinstance(widgets, dict):
            widgets["filename_prefix"] = prefix
        elif isinstance(widgets, list) and widgets:
            widgets[0] = prefix
        node["widgets_values"] = widgets


def build_ltx_iclora_canny() -> dict:
    graph = build_ltx_iclora()
    graph["id"] = "ltx-iclora-canny-5s-lab-example"
    extra = graph.setdefault("extra", {})
    extra["lab_profile"] = "ltx-iclora-canny-5s-lab-example"
    extra["lab_description"] = (
        "LTX-2.5 IC-LoRA Union Control envelope, 120 frames, canny default"
    )
    extra["lab_iclora"] = dict(extra.get("lab_iclora") or {})
    extra["lab_iclora"]["depth_default"] = False
    extra["lab_iclora"]["canny_default"] = True
    extra["lab_iclora"]["guide"] = "canny.mp4"
    _retitle_note(graph, LTX_CANNY_NOTE)
    _set_vhs_prefix(graph, "ez_iclora_canny")
    return graph


def build_ltx_iclora_depth_shorts() -> dict:
    graph = build_ltx_iclora()
    graph["id"] = "ltx-iclora-depth-shorts-lab-example"
    extra = graph.setdefault("extra", {})
    extra["lab_profile"] = "ltx-iclora-depth-shorts-lab-example"
    extra["lab_description"] = (
        "LTX-2.5 IC-LoRA Union Control envelope, 768x1280, 120 frames, depth default"
    )
    extra["lab_iclora"] = dict(extra.get("lab_iclora") or {})
    extra["lab_iclora"]["size"] = [768, 1280]
    extra["lab_iclora"]["guide"] = "depth.mp4"
    extra["lab_iclora"]["portrait"] = True
    _retitle_note(graph, LTX_SHORTS_NOTE)
    _set_ltx_canvas(graph, 768, 1280)
    _set_vhs_prefix(graph, "ez_iclora_depth_shorts")
    return graph


def build_wan_flf_from_guide() -> dict:
    graph = copy.deepcopy(_load("wan-flf-5s-lab-example.json"))
    graph["id"] = "wan-flf-from-guide-lab-example"
    extra = graph.setdefault("extra", {})
    extra["lab_profile"] = "wan-flf-from-guide-lab-example"
    extra["lab_description"] = (
        "Wan Fun InP first-last-frame from guide first.png + last.png. MagCache off."
    )
    extra["lab_dcc"] = {
        "print": "wan-flf",
        "first": "first.png",
        "last": "last.png",
        "prefix": "ez_flf_guide",
        "magcache": False,
    }
    extra.pop("lab_magcache", None)
    _retitle_note(graph, WAN_FLF_GUIDE_NOTE)
    first = None
    last = None
    latent = None
    for node in graph["nodes"]:
        if node.get("type") == "LoadImage" and "End" not in str(node.get("title") or ""):
            node["widgets_values"] = ["first.png", "image"]
            node["title"] = "Guide first.png"
            first = node
        elif node.get("type") == "LoadImage":
            node["widgets_values"] = ["last.png", "image"]
            node["title"] = "Guide last.png"
            last = node
        elif node.get("type") == "Wan22ImageToVideoLatent":
            latent = node
        elif node.get("type") == "VHS_VideoCombine":
            widgets = node.get("widgets_values")
            if isinstance(widgets, dict):
                widgets["filename_prefix"] = "ez_flf_guide"
            elif isinstance(widgets, list) and widgets:
                widgets[0] = "ez_flf_guide"
            node["widgets_values"] = widgets
        elif node.get("type") == "SaveImage":
            node["widgets_values"] = ["ez_flf_guide_frame"]
    if first is None or last is None or latent is None:
        raise SystemExit("wan-flf-from-guide: missing first/last/latent nodes")
    inputs = latent.setdefault("inputs", [])
    end_inp = next((inp for inp in inputs if inp.get("name") == "end_image"), None)
    max_id, max_link = _max_ids(graph)
    link_end = max_link + 1
    if end_inp is None:
        inputs.append(
            {"name": "end_image", "shape": 7, "type": "IMAGE", "link": link_end}
        )
    else:
        end_inp["link"] = link_end
    end_slot = next(
        i for i, inp in enumerate(inputs) if inp.get("name") == "end_image"
    )
    last_out = last["outputs"][0]
    last_links = last_out.get("links")
    if not isinstance(last_links, list):
        last_links = []
    last_out["links"] = list(last_links) + [link_end]
    _add_link(graph, link_end, int(last["id"]), 0, int(latent["id"]), end_slot, "IMAGE")
    graph["last_link_id"] = link_end
    blob = json.dumps(graph)
    if '"type": "MagCache"' in blob:
        raise SystemExit("wan-flf-from-guide must not include MagCache nodes")
    return graph


def _set_filename_prefix(graph: dict, prefix: str) -> None:
    for node in graph["nodes"]:
        ntype = node.get("type")
        if ntype == "SaveImage":
            node["widgets_values"] = [prefix]
            node["title"] = f"Save {prefix}"
        elif ntype == "VHS_VideoCombine":
            widgets = node.get("widgets_values")
            if isinstance(widgets, dict):
                widgets = dict(widgets)
                widgets["filename_prefix"] = prefix
                node["widgets_values"] = widgets
            elif isinstance(widgets, list) and widgets:
                widgets = list(widgets)
                widgets[0] = prefix
                node["widgets_values"] = widgets


def build_klein_from_guide_loader() -> dict:
    graph = build_klein_from_clay()
    graph["id"] = "klein-from-guide-loader-lab-example"
    extra = graph.setdefault("extra", {})
    extra["lab_profile"] = "klein-from-guide-loader-lab-example"
    extra["lab_description"] = (
        "Klein 4B edit of EZDCCLoadGuideStill first.png. Enhance on. 1280x704. Seed 42."
    )
    extra["lab_dcc"] = {
        "enhance": True,
        "mode": "edit",
        "seed": 42,
        "size": [1280, 704],
        "prefix": "ez_guide_hero",
        "loader": "EZDCCLoadGuideStill",
        "layer": "first",
        "slug": "go-see",
        "shot_id": "12",
    }
    extra["lab_note"] = KLEIN_LOADER_NOTE
    _retitle_note(graph, KLEIN_LOADER_NOTE)
    _set_filename_prefix(graph, "ez_guide_hero")
    load = _replace_load_image(
        graph,
        ntype="EZDCCLoadGuideStill",
        title="Load guide still",
        widgets=["go-see", "12", "first"],
    )
    _insert_occupancy_gate(graph, source=load, required_mode="klein")
    return graph


def build_ltx_iclora_from_guide_loader() -> dict:
    graph = build_ltx_iclora()
    graph["id"] = "ltx-iclora-from-guide-loader-lab-example"
    extra = graph.setdefault("extra", {})
    extra["lab_profile"] = "ltx-iclora-from-guide-loader-lab-example"
    extra["lab_description"] = (
        "LTX-2.5 IC-LoRA envelope from EZDCCLoadGuideStill + depth video path."
    )
    ic = dict(extra.get("lab_iclora") or {})
    ic["prefix"] = "ez_iclora_guide"
    ic["loader"] = "EZDCCLoadGuideStill"
    ic["magcache"] = False
    ic["distilled_only"] = True
    extra["lab_iclora"] = ic
    extra["lab_dcc"] = {
        "slug": "go-see",
        "shot_id": "12",
        "layer": "first",
        "prefix": "ez_iclora_guide",
    }
    extra["lab_note"] = LTX_LOADER_NOTE
    _retitle_note(graph, LTX_LOADER_NOTE)
    _set_filename_prefix(graph, "ez_iclora_guide")
    load = _replace_load_image(
        graph,
        ntype="EZDCCLoadGuideStill",
        title="Load guide still",
        widgets=["go-see", "12", "first"],
    )
    _insert_occupancy_gate(graph, source=load, required_mode="ltx")
    _add_guide_video_node(graph, layer="depth")
    blob = json.dumps(graph)
    if '"type": "MagCache"' in blob:
        raise SystemExit("iclora loader envelope must not include MagCache nodes")
    return graph


def build_trellis_from_klein_still() -> dict:
    from _build_trellis_workflow import build_trellis

    graph = build_trellis()
    graph["id"] = "trellis-from-klein-still-lab-example"
    extra = graph.setdefault("extra", {})
    extra["lab_profile"] = "trellis-from-klein-still-lab-example"
    extra["lab_description"] = (
        "EZDCCLoadStillPack mug plate to native TRELLIS.2 INT8. Occupancy trellis."
    )
    extra["lab_dcc"] = {
        "slug": "go-see",
        "plate": "mug",
        "prefix": "assets/objects/_lab-mug/",
        "loader": "EZDCCLoadStillPack",
    }
    trellis = dict(extra.get("lab_trellis") or {})
    trellis["native_only"] = True
    trellis["output_prefix"] = "assets/objects/_lab-mug/"
    extra["lab_trellis"] = trellis
    extra["lab_note"] = TRELLIS_LOADER_NOTE
    _retitle_note(graph, TRELLIS_LOADER_NOTE)
    load = _replace_load_image(
        graph,
        ntype="EZDCCLoadStillPack",
        title="Load still pack",
        widgets=["go-see", "mug", "first"],
    )
    _insert_occupancy_gate(graph, source=load, required_mode="trellis")
    for node in graph["nodes"]:
        if node.get("type") == "MeshToFile3D":
            node["widgets_values"] = ["assets/objects/_lab-mug/mesh"]
            node["title"] = "Save GLB (_lab-mug)"
    if any(str(n.get("type") or "").lower().startswith("pixal") for n in graph["nodes"]):
        raise SystemExit("trellis loader must not include Pixal nodes")
    return graph


def main() -> int:
    klein = build_klein_from_clay()
    canny = build_klein_from_canny()
    plates = build_klein_from_clay_plates()
    ltx = build_ltx_iclora()
    ltx_canny = build_ltx_iclora_canny()
    ltx_shorts = build_ltx_iclora_depth_shorts()
    flf = build_wan_flf_from_guide()
    klein_loader = build_klein_from_guide_loader()
    ltx_loader = build_ltx_iclora_from_guide_loader()
    trellis_loader = build_trellis_from_klein_still()
    written = [
        ("klein-from-clay-lab-example.json", klein),
        ("klein-from-canny-lab-example.json", canny),
        ("klein-from-clay-plates-lab-example.json", plates),
        ("ltx-iclora-depth-5s-lab-example.json", ltx),
        ("ltx-iclora-canny-5s-lab-example.json", ltx_canny),
        ("ltx-iclora-depth-shorts-lab-example.json", ltx_shorts),
        ("wan-flf-from-guide-lab-example.json", flf),
        ("klein-from-guide-loader-lab-example.json", klein_loader),
        ("ltx-iclora-from-guide-loader-lab-example.json", ltx_loader),
        ("trellis-from-klein-still-lab-example.json", trellis_loader),
    ]
    for name, graph in written:
        dest = lab_dest(name, lane="dcc")
        _save(graph, dest)
        print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
