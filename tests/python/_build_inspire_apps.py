"""Build no-UNET inspire Apps: Prompt Forge and Beat Sheet.

Not imported by pytest (leading underscore). Run from repo root:

  python3 tests/python/_build_inspire_apps.py
"""

from __future__ import annotations

import json
from pathlib import Path

from _lab_layout import (
    GROUP_TITLE_INSET,
    LAB_GROUP_Y0,
    LAB_NODE_Y0,
    ensure_group_title_inset,
    group as _group,
)
from _lab_theme import LAZY_FORGE
from _stamp_app_mode import stamp_suite_graph

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "workflows"

LAZY = LAZY_FORGE

FORGE_NOTE = """## prompt-forge-lab-example

Prompt Forge — rewrite a lazy sentence for Klein, Wan, and LTX. No UNET, no VAE, no KSampler.

Occupancy: llm — stop nothing GPU. One GB10 job.
Uses the on-box Qwen3-4B-Instruct GGUF (CPU, n_gpu_layers=0). No new download flag.

1. Type a lazy sentence (or leave the canned line).
2. Set family mode (t2i / i2v / t2v), style, and aspect / duration hint on each enhance node.
3. Queue. Each Enhance node previews the rewritten STRING.
4. Copy the family you need into **klein-still-draft-lab-example** (Spark Still).

Turn Enhance off to pin the widget text.
"""

BEAT_NOTE = """## beat-sheet-lab-example

Beat Sheet v1 — 6 beats × enter / traverse / exit (18 STRING widgets). Occupancy: none — stop nothing GPU.

This graph does not print video. Paste the filled cards into host YAML:

  workflows/shorts/<slug>.shots.yaml

The entrypoint does **not** copy YAML. Edit on the host. Then Queue **film-go-see-90s-run-lab-example** (or still-here / switchyard).

go-see.shots.yaml contract (keep these keys):

  film
  slug
  frames: 120
  fps: 24
  duration_s: 5.00
  beats: 6
  shots_per_beat: 3
  total_shots: 18
  publish_cap_s: 90.00
  print: ltx
  identity_seed
  identity_enhance: true
  identity_look
  shots[]{beat, shot, prefix, load_from, ltx_i2v, wan_i2v}

Shot 1 of beat 1 load_from: identity
Later shots load_from: <prev_prefix>_last
Example: ez_gosee_b1_s1 then ez_gosee_b1_s1_last.

Do not type a 30/60/90 s denoise. One print is 5.00 s (120 frames @ 24 fps).
"""

SHOT_ROLES = ("enter", "traverse", "exit")


def _assert_no_overlap(graph: dict, pad: float = 20) -> None:
    boxes: list[tuple[int, str, float, float, float, float]] = []
    for node in graph["nodes"]:
        x, y = node["pos"]
        size = node.get("size", [200, 100])
        if isinstance(size, dict):
            width, height = float(size.get("0", 200)), float(size.get("1", 100))
        else:
            width, height = float(size[0]), float(size[1])
        boxes.append(
            (node["id"], node["type"], x - pad, y - pad, x + width + pad, y + height + pad)
        )
    for i, a in enumerate(boxes):
        for b in boxes[i + 1 :]:
            if a[2] < b[4] and a[4] > b[2] and a[3] < b[5] and a[5] > b[3]:
                raise SystemExit(f"overlap {a[0]}({a[1]}) vs {b[0]}({b[1]})")


def _dump(path: Path, graph: dict) -> None:
    stamp_suite_graph(graph)
    ensure_group_title_inset(graph)
    _assert_no_overlap(graph)
    path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


def _node(
    nid: int,
    ntype: str,
    pos: list[float],
    size: list[float],
    title: str,
    widgets: list,
    order: int,
    outputs: list | None = None,
) -> dict:
    return {
        "id": nid,
        "type": ntype,
        "pos": pos,
        "size": size,
        "flags": {},
        "order": order,
        "mode": 0,
        "inputs": [],
        "outputs": outputs or [],
        "properties": {"Node name for S&R": ntype},
        "widgets_values": widgets,
        "title": title,
    }


def _str_out() -> list[dict]:
    return [{"name": "prompt", "type": "STRING", "links": None, "slot_index": 0}]


def build_prompt_forge() -> dict:
    note_h = 300.0
    note_group_h = note_h + GROUP_TITLE_INSET
    enh_group_top = LAB_GROUP_Y0 + note_group_h
    enh_y = enh_group_top + GROUP_TITLE_INSET
    klein = _node(
        2,
        "EZKleinPromptEnhance",
        [40, enh_y],
        [420, 300],
        "Klein family",
        [LAZY, True, "t2i", "YouTube 16:9 still", "none"],
        1,
        _str_out(),
    )
    wan = _node(
        3,
        "EZWanPromptEnhance",
        [500, enh_y],
        [420, 300],
        "Wan family",
        [LAZY, True, "i2v", "5 seconds, 24 fps", "none"],
        2,
        _str_out(),
    )
    ltx = _node(
        4,
        "EZLTXPromptEnhance",
        [960, enh_y],
        [420, 380],
        "LTX family",
        [LAZY, True, "i2v", "5 seconds, 24 fps", "rooftop wind, no score", "none"],
        3,
        _str_out(),
    )
    note = _node(
        1,
        "Note",
        [40, LAB_NODE_Y0],
        [1340, note_h],
        "Operator note",
        [FORGE_NOTE],
        0,
    )
    graph = {
        "id": "prompt-forge-lab-example",
        "revision": 1,
        "last_node_id": 4,
        "last_link_id": 0,
        "nodes": [note, klein, wan, ltx],
        "links": [],
        "groups": [
            _group(1, "NOTE", 20, LAB_GROUP_Y0, 1380, note_group_h, "#3f789e"),
            _group(2, "KLEIN", 20, enh_group_top, 460, 300 + GROUP_TITLE_INSET, "#3f789e"),
            _group(3, "WAN", 480, enh_group_top, 460, 300 + GROUP_TITLE_INSET, "#3f789e"),
            _group(4, "LTX", 940, enh_group_top, 460, 380 + GROUP_TITLE_INSET, "#3f789e"),
        ],
        "config": {},
        "extra": {
            "lab_profile": "prompt-forge-lab-example",
            "lab_note": FORGE_NOTE,
            "lab_description": "No-UNET Prompt Forge: Klein + Wan + LTX enhance preview",
            "ds": {"scale": 1, "offset": [0, 0]},
        },
        "version": 0.4,
    }
    return graph


def build_beat_sheet() -> dict:
    note_h = 420.0
    card_w, card_h = 420.0, 160.0
    enh_h = 280.0
    gap = 40.0
    row_stride = card_h + enh_h + GROUP_TITLE_INSET + gap + 50.0
    cards_y0 = LAB_NODE_Y0 + note_h + 80.0
    nodes = [
        _node(
            1,
            "Note",
            [40, LAB_NODE_Y0],
            [1340, note_h],
            "Operator note",
            [BEAT_NOTE],
            0,
        )
    ]
    groups = [
        _group(
            1,
            "NOTE",
            20,
            LAB_GROUP_Y0,
            1380,
            note_h + GROUP_TITLE_INSET,
            "#3f789e",
        )
    ]
    nid = 2
    links: list[list] = []
    lid = 1
    for beat in range(1, 7):
        row_y = cards_y0 + (beat - 1) * row_stride
        group_top = row_y - GROUP_TITLE_INSET
        groups.append(
            _group(
                beat + 1,
                f"BEAT {beat}",
                20,
                group_top,
                1380,
                card_h + enh_h + 70 + GROUP_TITLE_INSET,
                "#3f789e",
            )
        )
        for col, role in enumerate(SHOT_ROLES):
            x = 40 + col * (card_w + gap)
            title = f"Beat {beat} {role}"
            placeholder = (
                f"{role} beat {beat} — paste into workflows/shorts/<slug>.shots.yaml"
            )
            prim_id = nid
            nodes.append(
                _node(
                    prim_id,
                    "PrimitiveNode",
                    [x, row_y],
                    [card_w, card_h],
                    title,
                    [placeholder, "fixed"],
                    nid - 1,
                    [
                        {
                            "name": "STRING",
                            "type": "STRING",
                            "links": [lid],
                            "widget": {"name": "value"},
                            "slot_index": 0,
                        }
                    ],
                )
            )
            nid += 1
            enh_id = nid
            nodes.append(
                _node(
                    enh_id,
                    "EZLTXPromptEnhance",
                    [x, row_y + card_h + 50],
                    [card_w, enh_h],
                    f"{title} LTX enhance",
                    [placeholder, True, "i2v", "5 seconds, 24 fps", "", "none"],
                    nid - 1,
                    _str_out(),
                )
            )
            nodes[-1]["inputs"] = [
                {
                    "name": "prompt",
                    "type": "STRING",
                    "link": lid,
                    "widget": {"name": "prompt"},
                }
            ]
            links.append([lid, prim_id, 0, enh_id, 0, "STRING"])
            lid += 1
            nid += 1
    graph = {
        "id": "beat-sheet-lab-example",
        "revision": 1,
        "last_node_id": nid - 1,
        "last_link_id": lid - 1,
        "nodes": nodes,
        "links": links,
        "groups": groups,
        "config": {},
        "extra": {
            "lab_profile": "beat-sheet-lab-example",
            "lab_note": BEAT_NOTE,
            "lab_description": "No-UNET beat sheet: 6 beats x enter/traverse/exit for shots.yaml",
            "ds": {"scale": 1, "offset": [0, 0]},
        },
        "version": 0.4,
    }
    return graph


def main() -> None:
    _dump(WF / "prompt-forge-lab-example.json", build_prompt_forge())
    _dump(WF / "beat-sheet-lab-example.json", build_beat_sheet())


if __name__ == "__main__":
    main()
