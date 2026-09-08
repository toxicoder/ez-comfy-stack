#!/usr/bin/env python3
"""Build ez_studio_blocks subgraph blueprints from shipped lab graphs.

Run from repo root:
  python3 tests/python/_build_studio_blocks.py
"""

from __future__ import annotations

import json
from pathlib import Path

from _lab_paths import ROOT, lab_json
from _stamp_app_mode import BANNED, occupancy_stanza

PACK = ROOT / "custom_nodes" / "ez_studio_blocks" / "subgraphs"

KLEIN_UUID = "7c3e9b10-6a21-4f0a-9c11-00000000aa01"
WAN_UUID = "7c3e9b10-6a21-4f0a-9c11-00000000aa02"
LTX_AV_UUID = "7c3e9b10-6a21-4f0a-9c11-00000000aa03"
LTX_SHOT_UUID = "7c3e9b10-6a21-4f0a-9c11-00000000aa04"

SPECS = (
    (
        "klein-t2i-backbone",
        KLEIN_UUID,
        "klein",
        "klein-still-draft-lab-example.json",
        (
            ("prompt", "STRING"),
            ("negative", "STRING"),
            ("seed", "INT"),
            ("width", "INT"),
            ("height", "INT"),
            ("steps", "INT"),
            ("enhance", "BOOLEAN"),
        ),
        (("IMAGE", "IMAGE"),),
    ),
    (
        "wan-i2v-5s",
        WAN_UUID,
        "wan",
        "wan-i2v-5s-lab-example.json",
        (
            ("image", "IMAGE"),
            ("prompt", "STRING"),
            ("seed", "INT"),
            ("frames", "INT"),
            ("fps", "FLOAT"),
        ),
        (("IMAGE", "IMAGE"),),
    ),
    (
        "ltx-av-5s",
        LTX_AV_UUID,
        "ltx",
        "ltx-i2v-5s-lab-example.json",
        (
            ("image", "IMAGE"),
            ("prompt", "STRING"),
            ("seed", "INT"),
            ("width", "INT"),
            ("height", "INT"),
            ("frames", "INT"),
        ),
        (("IMAGE", "IMAGE"),),
    ),
    (
        "ltx-film-shot",
        LTX_SHOT_UUID,
        "film",
        "ltx-i2v-shot-lab-example.json",
        (
            ("image", "IMAGE"),
            ("prompt", "STRING"),
            ("seed", "INT"),
            ("shot_index", "INT"),
            ("prefix", "STRING"),
        ),
        (("IMAGE", "IMAGE"), ("Filenames", "VHS_FILENAMES")),
    ),
)


def _assert_clean(payload: object, *, where: str) -> None:
    blob = json.dumps(payload)
    for needle in BANNED:
        if needle in blob:
            raise ValueError(f"banned string {needle!r} in {where}")


def _ensure_occupancy_note(nodes: list[dict], occupancy: str) -> None:
    stanza = occupancy_stanza(occupancy)
    for node in nodes:
        if node.get("type") != "Note":
            continue
        values = node.get("widgets_values") or [""]
        text = str(values[0])
        if "Occupancy:" not in text:
            node["widgets_values"] = [f"{text.rstrip()}\n\n{stanza}\n"]
        return
    nodes.append(
        {
            "id": max((int(n["id"]) for n in nodes), default=0) + 1,
            "type": "Note",
            "pos": [40, 40],
            "size": [400, 120],
            "flags": {},
            "order": 0,
            "mode": 0,
            "title": "Occupancy",
            "widgets_values": [stanza],
        }
    )


def wrap_blueprint(
    name: str,
    uuid: str,
    occupancy: str,
    source: str,
    inputs: tuple[tuple[str, str], ...],
    outputs: tuple[tuple[str, str], ...],
) -> dict:
    src = json.loads(lab_json(source).read_text(encoding="utf-8"))
    nodes = json.loads(json.dumps(src.get("nodes") or []))
    _ensure_occupancy_note(nodes, occupancy)
    subgraph = {
        "id": uuid,
        "name": name,
        "version": 1,
        "revision": int(src.get("revision") or 1),
        "config": {},
        "extra": {"lab_occupancy": occupancy},
        "groups": src.get("groups") or [],
        "inputs": [{"name": n, "type": t} for n, t in inputs],
        "outputs": [{"name": n, "type": t} for n, t in outputs],
        "widgets": [],
        "nodes": nodes,
        "links": src.get("links") or [],
    }
    root_node = {
        "id": 1,
        "type": uuid,
        "pos": [100, 100],
        "size": [280, 160],
        "flags": {},
        "order": 0,
        "mode": 0,
        "inputs": [{"name": n, "type": t, "link": None} for n, t in inputs],
        "outputs": [{"name": n, "type": t, "links": []} for n, t in outputs],
        "properties": {"Node name for S&R": name},
        "widgets_values": [],
        "title": name,
    }
    graph = {
        "id": f"ez-studio-blocks-{name}",
        "revision": 1,
        "last_node_id": 1,
        "last_link_id": 0,
        "nodes": [root_node],
        "links": [],
        "groups": [],
        "definitions": {"subgraphs": [subgraph]},
        "version": 0.4,
        "extra": {
            "lab_occupancy": occupancy,
            "lab_note": occupancy_stanza(occupancy),
        },
    }
    _assert_clean(graph, where=name)
    return graph


def build_all() -> None:
    PACK.mkdir(parents=True, exist_ok=True)
    for name, uuid, occupancy, source, inputs, outputs in SPECS:
        graph = wrap_blueprint(name, uuid, occupancy, source, inputs, outputs)
        path = PACK / f"{name}.json"
        path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    build_all()
