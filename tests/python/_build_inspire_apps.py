"""Build no-UNET inspire Apps: Prompt Forge, Beat Sheet, Research Chat.

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
from _lab_paths import lab_dest, lab_json
from _stamp_app_mode import stamp_suite_graph

ROOT = Path(__file__).resolve().parents[2]
WF = ROOT / "workflows"

LAZY = LAZY_FORGE

FORGE_NOTE = """## prompt-forge-lab-example

Prompt Forge — rewrite a lazy sentence for Klein, Wan, and LTX. No UNET, no VAE, no KSampler.

Occupancy: llm — graph label (not a CLI mode). Prefer GPU 35B:

  ./scripts/manage.sh occupancy enter llm-desk --yes

Falls back to on-box Qwen3-4B if the sidecar is down. CPU 4B is required next to Wan/LTX/TRELLIS.

1. Type a lazy sentence (or leave the canned line).
2. Set family mode (t2i / i2v / t2v), style, and aspect / duration hint on each enhance node.
3. Queue. Each Enhance node previews the rewritten STRING.
4. Copy the family you need into **klein-still-draft-lab-example** (Spark Still).

Turn Enhance off to pin the widget text.
"""

BEAT_NOTE = """## beat-sheet-lab-example

Script desk — 6 beats × enter / traverse / exit. Occupancy: none — stop nothing GPU.

This graph does not print video. Fill Logline, Script, Audio policy, Score, then the 18 cards
(`action | camera | world SFX | dialogue`). Write YAML on the host:

  ./scripts/manage.sh shot-sheet run --film <slug>

That writes `${COMFY_OUTPUT_DIR}/films/<slug>/shots.yaml`. The entrypoint does **not**
copy YAML. Do not overwrite `workflows/shorts/*.shots.yaml` unless `--lab-example`.

Next: klein-identity-sheet-lab-example, or export-guides if clay is required, then
klein-from-clay-lab-example.

Shot-card keys (defaults fail-closed):

  audio_policy: world-only | stems | a2v-lock
  score: none | acestep-instrumental
  clay: skip | required
  audio_lock: none | a2v
  camera: dolly in | tracking | fixed camera | …

Shot 1 of beat 1 load_from: identity. Later shots load_from: <prev_prefix>_last.

Do not type a 30/60/90 s denoise. One print is 5.00 s (120 frames @ 24 fps).
"""

RESEARCH_NOTE = """## research-chat-lab-example

Creative research desk — chat LLM with web search and sequential research
subagents. No UNET, no VAE, no KSampler.

Occupancy: llm — graph label (not a CLI mode). Prefer GPU 35B:

  ./scripts/manage.sh occupancy enter llm-desk --yes

Falls back to on-box Qwen3-4B if the sidecar is down. CPU 4B is required next to Wan/LTX/TRELLIS.
Web search is SSRF-safe HTTPS (Wikipedia + DuckDuckGo HTML). Fail-soft if the
network or GGUF is missing.

1. Type a question (look, camera, lighting, world, reference).
2. Mode **research** (planner + search subagents) or **chat** (one turn).
3. Queue. Read **Reply** and **Sources**. Copy prompt ingredients into
   **prompt-forge-lab-example**, then **klein-still-draft-lab-example**.

Laptop agents: `./scripts/manage.sh research-mcp --stdio` (Path D). Same
pipeline as this App. Does not queue Comfy. Does not refuse a GPU session.
"""

RESEARCH_MESSAGE = (
    "What lighting and camera language fits a night rooftop still of a techno "
    "wizard in a tropical city?"
)

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
    note_h = 460.0
    card_w, card_h = 420.0, 160.0
    desk_h = 140.0
    enh_h = 280.0
    gap = 40.0
    desk_y = LAB_NODE_Y0 + note_h + GROUP_TITLE_INSET + 20.0
    row_stride = card_h + enh_h + GROUP_TITLE_INSET + gap + 50.0
    cards_y0 = desk_y + desk_h + 80.0
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
        ),
        _group(
            2,
            "DESK",
            20,
            desk_y - GROUP_TITLE_INSET,
            1380,
            desk_h + GROUP_TITLE_INSET,
            "#3f789e",
        ),
    ]
    nid = 2
    desk_cards = (
        ("Logline", "One-line premise. Approve before any UNET."),
        ("Script", "Spoken and visual beats. Words are cheap; prints are not."),
        ("Audio policy", "world-only"),
        ("Score", "none"),
    )
    for col, (title, placeholder) in enumerate(desk_cards):
        x = 40 + col * (card_w + gap)
        nodes.append(
            _node(
                nid,
                "PrimitiveNode",
                [x, desk_y],
                [card_w, desk_h],
                title,
                [placeholder, "fixed"],
                nid - 1,
                [
                    {
                        "name": "STRING",
                        "type": "STRING",
                        "links": None,
                        "widget": {"name": "value"},
                        "slot_index": 0,
                    }
                ],
            )
        )
        nid += 1
    links: list[list] = []
    lid = 1
    for beat in range(1, 7):
        row_y = cards_y0 + (beat - 1) * row_stride
        group_top = row_y - GROUP_TITLE_INSET
        groups.append(
            _group(
                beat + 2,
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
                f"{role} beat {beat} — action | camera | world SFX | dialogue"
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
            "lab_description": "Script desk: logline, audio policy, 18 shot cards → shot-sheet YAML",
            "ds": {"scale": 1, "offset": [0, 0]},
        },
        "version": 0.4,
    }
    return graph


def build_research_chat() -> dict:
    note_h = 340.0
    note_group_h = note_h + GROUP_TITLE_INSET
    desk_group_top = LAB_GROUP_Y0 + note_group_h
    desk_y = desk_group_top + GROUP_TITLE_INSET
    desk_h = 420.0
    note = _node(
        1,
        "Note",
        [40, LAB_NODE_Y0],
        [720, note_h],
        "Operator note",
        [RESEARCH_NOTE],
        0,
    )
    desk = _node(
        2,
        "EZCreativeResearch",
        [40, desk_y],
        [720, desk_h],
        "Creative research",
        [RESEARCH_MESSAGE, "research", True, 2, ""],
        1,
        [{"name": "reply", "type": "STRING", "links": None, "slot_index": 0}],
    )
    graph = {
        "id": "research-chat-lab-example",
        "revision": 1,
        "last_node_id": 2,
        "last_link_id": 0,
        "nodes": [note, desk],
        "links": [],
        "groups": [
            _group(1, "NOTE", 20, LAB_GROUP_Y0, 760, note_group_h, "#3f789e"),
            _group(
                2,
                "RESEARCH",
                20,
                desk_group_top,
                760,
                desk_h + GROUP_TITLE_INSET,
                "#3f789e",
            ),
        ],
        "config": {},
        "extra": {
            "lab_profile": "research-chat-lab-example",
            "lab_note": RESEARCH_NOTE,
            "lab_description": (
                "No-UNET creative research chat: web search + sequential subagents"
            ),
            "lab_mcp": {
                "server": "research-mcp",
                "tools": ["chat", "web_search", "research"],
                "workflow": (
                    "workflows/_lab/inspire/research-chat-lab-example.json"
                ),
            },
            "ds": {"scale": 1, "offset": [0, 0]},
        },
        "version": 0.4,
    }
    return graph


def main() -> None:
    _dump(lab_json("prompt-forge-lab-example.json"), build_prompt_forge())
    _dump(lab_json("beat-sheet-lab-example.json"), build_beat_sheet())
    _dump(lab_dest("research-chat-lab-example.json"), build_research_chat())


if __name__ == "__main__":
    main()
