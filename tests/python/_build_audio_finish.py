#!/usr/bin/env python3
"""Build the picture-lock audio-finish App (no UNET; occupancy audio).

Run from repo root:
  python3 tests/python/_build_audio_finish.py
"""

from __future__ import annotations

from pathlib import Path

from _lab_layout import (
    GROUP_TITLE_INSET,
    LAB_GROUP_Y0,
    LAB_NODE_Y0,
    ensure_group_title_inset,
    group as _group,
)
from _stamp_app_mode import stamp_suite_graph
from _build_inspire_apps import _assert_no_overlap, _node

NOTE = """## audio-finish-lab-example

Picture-lock stem mix. Occupancy **audio** — stop Klein / Wan / LTX first. ACE-Step
score is a later session if `score: acestep-instrumental`.

This canvas does not denoise video. Mix on the host:

  ./scripts/manage.sh stem-mix --film <slug> --shot <id> --bg PATH [--dx PATH]

Stems: BG = demuxed LTX world bed, FX = optional Templates LTX-2.5 T2A (same distilled
transformer; not a vendored subgraph), DX = Kokoro / Qwen3-TTS, MX = ACE-Step
instrumental. Duck beds −15 dB under DX. YouTube loudnorm I=-14.

A2V lock (talking-head): mix DX first, then Templates → LTX-2.5 A2V freeze. Mouths will
not match (banned lip-sync OSS stays out). Foley V2A LoRA is not in v1.

Do not start Docker. Do not co-resident ACE-Step with LTX.
"""


def build_audio_finish() -> dict:
    note_h = 420.0
    card_w, card_h = 300.0, 120.0
    gap = 48.0
    desk_y = LAB_NODE_Y0 + note_h + GROUP_TITLE_INSET + 20.0
    widgets = (
        ("Film slug", "go-see"),
        ("Shot id", "01"),
        ("Include DX", "no"),
        ("Include FX", "no"),
        ("Include MX", "no"),
    )
    nodes = [
        _node(
            1,
            "Note",
            [40, LAB_NODE_Y0],
            [1340, note_h],
            "Operator note",
            [NOTE],
            0,
        )
    ]
    nid = 2
    for col, (title, placeholder) in enumerate(widgets):
        x = 40 + col * (card_w + gap)
        nodes.append(
            _node(
                nid,
                "PrimitiveNode",
                [x, desk_y],
                [card_w, card_h],
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
    save_id = nid
    nodes.append(
        {
            "id": save_id,
            "type": "SaveAudio",
            "pos": [40, desk_y + card_h + 80],
            "size": [320, 80],
            "flags": {},
            "order": save_id - 1,
            "mode": 0,
            "inputs": [{"name": "audio", "type": "AUDIO", "link": None}],
            "outputs": [],
            "properties": {"Node name for S&R": "SaveAudio"},
            "widgets_values": ["ez_stem_mix"],
            "title": "Save stem mix (host stem-mix.sh)",
        }
    )
    graph = {
        "id": "audio-finish-lab-example",
        "revision": 1,
        "last_node_id": save_id,
        "last_link_id": 0,
        "nodes": nodes,
        "links": [],
        "groups": [
            _group(1, "NOTE", 20, LAB_GROUP_Y0, 1380, note_h + GROUP_TITLE_INSET, "#3f789e"),
            _group(
                2,
                "STEMS",
                20,
                desk_y - GROUP_TITLE_INSET,
                1660,
                card_h + GROUP_TITLE_INSET + 20,
                "#3f789e",
            ),
        ],
        "config": {},
        "extra": {
            "lab_profile": "audio-finish-lab-example",
            "lab_note": NOTE,
            "lab_description": "Picture-lock stem mix desk. Occupancy audio. Mix via stem-mix.sh.",
            "ds": {"scale": 1, "offset": [0, 0]},
        },
        "version": 0.4,
    }
    return graph


def main() -> None:
    graph = build_audio_finish()
    stamp_suite_graph(graph)
    ensure_group_title_inset(graph)
    _assert_no_overlap(graph)
    dest = Path(__file__).resolve().parents[2] / "workflows" / "_lab" / "audio" / "audio-finish-lab-example.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(__import__("json").dumps(graph, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {dest.relative_to(Path(__file__).resolve().parents[2])}")


if __name__ == "__main__":
    main()
