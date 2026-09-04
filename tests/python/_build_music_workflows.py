#!/usr/bin/env python3
"""Build US-safe ACE-Step rap lab graphs (draft + full).

Not imported by pytest (leading underscore). Run from repo root:

  python3 tests/python/_build_music_workflows.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_music.nodes import DRAFT_LYRICS, FULL_LYRICS  # noqa: E402

WF = ROOT / "workflows"

ACE_CKPT = "ace_step_1.5_turbo_aio.safetensors"
ACE_TAGS = (
    "boom bap, hip-hop, dusty drums, vinyl crackle, dry snare, sampled piano "
    "stab, upright bass, male rap vocals, dry booth, no autotune, 88 bpm"
)
COVER_THUMB = "klein-thumbnail-lab-example.json"
COVER_PODCAST = "klein-podcast-cover-lab-example.json"
TRAP_TAGS = (
    "trap, 808 bass, rapid hi-hats, dark pads, male rap vocals, half-time, 140 bpm"
)
LOFI_TAGS = (
    "lo-fi hip-hop, dusty drums, rhodes, vinyl crackle, laid-back male rap vocals, 86 bpm"
)

DRAFT_NOTE = f"""## music-rap-draft-lab-example

US-safe rap **draft** (first Queue, same role as klein-still-draft). Native ACE-Step 1.5 turbo AIO. Sequential Queue — do not load Klein + Wan + LTX + ACE-Step together.

1. Weights: `./scripts/manage.sh download-music --tier turbo` (same AIO dest as `download-podcast --tier acestep`; ~10 GB, opt-in, not `download-models`).
2. Leave **Enhance** off so Queue works offline. Edit the lyrics widget (human part).
3. Tags vs lyrics: tags are genre/instrument/vocal hints; lyrics are the bars. Section tags `[verse]` / `[chorus]` / `[spoken word]` are vocal hints operators may add.
4. Original lyrics only. No “in the style of <living artist>”. No living-MC names. No famous-hook paraphrases.
5. ACE-Step vocal is an **invented** identity, not a cloned MC.
6. Sampler: 8 steps, cfg 1, euler, simple. Duration 32 s, bpm 88, language en, timesignature 4, generate_audio_codes true.
7. Saves: `ez_rap_draft` FLAC master + 320 kbps MP3 under `${{COMFY_OUTPUT_DIR}}`.
8. Cover separately: Queue **{COVER_THUMB}** or **{COVER_PODCAST}**. Do not embed Klein here.
9. Human rewrite the lyrics before any release. Prompts are not authorship (USCO Part 2 / Thaler).

Beat-only pass: keep boom-bap tags, append instrumental, no vocals, and replace lyrics with [inst].

Canned style swaps (tags widget only — not extra files):
- trap: {TRAP_TAGS}
- lo-fi: {LOFI_TAGS}
"""

FULL_NOTE = f"""## music-rap-full-lab-example

US-safe rap **full track**. Same model and sampler as the draft (8 steps, cfg 1, euler, simple). Duration 96 s.

1. Queue **music-rap-draft-lab-example** first. Then this graph.
2. Weights: `./scripts/manage.sh download-music --tier turbo` (shared AIO with podcast acestep).
3. Leave **Enhance** off. Edit lyrics before Queue. Human rewrite required before any release.
4. Original lyrics only. No living-artist names. No famous-hook paraphrases. No “in the style of <living artist>”.
5. ACE-Step vocal is an invented timbre, not a clone.
6. Saves: `ez_rap_full` FLAC + 320 kbps MP3.
7. Cover: sequential Queue **{COVER_THUMB}** / **{COVER_PODCAST}**. Do not embed Klein.
8. Do not co-resident with LTX / Wan / Klein on this Spark.

Canned style swaps (tags widget only):
- trap: {TRAP_TAGS}
- lo-fi: {LOFI_TAGS}
"""


def _group(gid: int, title: str, x: float, y: float, w: float, h: float, color: str) -> dict:
    return {
        "id": gid,
        "title": title,
        "bounding": [x, y, w, h],
        "color": color,
        "font_size": 24,
        "flags": {},
    }


def _assert_no_overlap(graph: dict, pad: float = 20) -> None:
    boxes: list[tuple[int, str, float, float, float, float]] = []
    for n in graph["nodes"]:
        x, y = n["pos"]
        s = n.get("size", [200, 100])
        if isinstance(s, dict):
            w, h = float(s.get("0", 200)), float(s.get("1", 100))
        else:
            w, h = float(s[0]), float(s[1])
        boxes.append((n["id"], n["type"], x - pad, y - pad, x + w + pad, y + h + pad))
    for i, a in enumerate(boxes):
        for b in boxes[i + 1 :]:
            if a[2] < b[4] and a[4] > b[2] and a[3] < b[5] and a[5] > b[3]:
                raise SystemExit(f"overlap {a[0]}({a[1]}) vs {b[0]}({b[1]})")


class Graph:
    def __init__(self, graph_id: str) -> None:
        self.graph_id = graph_id
        self.nodes: list[dict] = []
        self.links: list[list] = []
        self._lid = 0

    def add(
        self,
        nid: int,
        ntype: str,
        pos: list[float],
        size: list[float],
        title: str,
        widgets: list | dict,
        *,
        inputs: list | None = None,
        outputs: list | None = None,
        mode: int = 0,
        properties: dict | None = None,
    ) -> dict:
        node = {
            "id": nid,
            "type": ntype,
            "pos": pos,
            "size": size,
            "flags": {},
            "order": len(self.nodes),
            "mode": mode,
            "inputs": inputs or [],
            "outputs": outputs or [],
            "properties": properties or {"Node name for S&R": ntype},
            "widgets_values": widgets,
            "title": title,
        }
        self.nodes.append(node)
        return node

    def out(self, name: str, ltype: str, links: list[int] | None = None) -> dict:
        return {
            "name": name,
            "type": ltype,
            "links": links if links is not None else [],
            "slot_index": 0,
        }

    def inp(self, name: str, ltype: str, link: int | None = None, widget: str | None = None) -> dict:
        item: dict = {"name": name, "type": ltype, "link": link}
        if widget is not None:
            item["widget"] = {"name": widget}
        return item

    def link(self, src: int, src_slot: int, dst: int, dst_slot: int, ltype: str) -> int:
        self._lid += 1
        self.links.append([self._lid, src, src_slot, dst, dst_slot, ltype])
        dst_node = next(n for n in self.nodes if n["id"] == dst)
        dst_node["inputs"][dst_slot]["link"] = self._lid
        src_node = next(n for n in self.nodes if n["id"] == src)
        src_node["outputs"][src_slot]["links"].append(self._lid)
        return self._lid

    def dump(self, extra: dict) -> dict:
        graph = {
            "id": self.graph_id,
            "revision": 1,
            "last_node_id": max(n["id"] for n in self.nodes),
            "last_link_id": self._lid,
            "nodes": self.nodes,
            "links": self.links,
            "groups": extra.pop("groups"),
            "config": {},
            "extra": extra,
            "version": 0.4,
        }
        _assert_no_overlap(graph)
        return graph


def _ace_widgets(lyrics: str, duration: float, seed: int = 42) -> list:
    return [
        ACE_TAGS,
        lyrics,
        seed,
        88,
        duration,
        "4",
        "en",
        "C minor",
        True,
        2.0,
        0.85,
        0.9,
        0,
        0.0,
    ]


def _sampler_widgets() -> list:
    return [42, "fixed", 8, 1.0, "euler", "simple", 1.0]


def _build_rap(stem: str, duration: float, lyrics: str, prefix: str, note: str, description: str) -> dict:
    g = Graph(stem)
    g.add(
        1,
        "CheckpointLoaderSimple",
        [40, 80],
        [360, 100],
        "ACE-Step 1.5 turbo AIO",
        [ACE_CKPT],
        outputs=[
            g.out("MODEL", "MODEL", []),
            g.out("CLIP", "CLIP", []),
            g.out("VAE", "VAE", []),
        ],
    )
    g.add(
        2,
        "ModelSamplingAuraFlow",
        [40, 220],
        [330, 60],
        "AuraFlow sampling",
        [3],
        inputs=[g.inp("model", "MODEL")],
        outputs=[g.out("MODEL", "MODEL", [])],
    )
    prim_out = {
        "name": "FLOAT",
        "type": "FLOAT",
        "widget": {"name": "seconds"},
        "links": [],
        "slot_index": 0,
    }
    g.add(
        3,
        "PrimitiveNode",
        [40, 380],
        [280, 82],
        "Song Duration",
        [duration, "fixed"],
        outputs=[prim_out],
        properties={"Run widget replace on values": False},
    )
    g.add(
        4,
        "EmptyAceStep1.5LatentAudio",
        [40, 520],
        [320, 82],
        "Latent length (seconds)",
        [duration, 1],
        inputs=[g.inp("seconds", "FLOAT", widget="seconds")],
        outputs=[g.out("LATENT", "LATENT", [])],
    )
    g.add(
        5,
        "EZRapLyrics",
        [500, 80],
        [400, 280],
        "ez_rap_lyrics",
        [lyrics, False],
        outputs=[g.out("lyrics", "STRING", [])],
    )
    g.add(
        6,
        "TextEncodeAceStepAudio1.5",
        [500, 400],
        [400, 420],
        "ACE tags + lyrics",
        _ace_widgets(lyrics, duration),
        inputs=[
            g.inp("clip", "CLIP"),
            g.inp("lyrics", "STRING", widget="lyrics"),
            g.inp("duration", "FLOAT", widget="duration"),
        ],
        outputs=[g.out("CONDITIONING", "CONDITIONING", [])],
    )
    g.add(
        7,
        "ConditioningZeroOut",
        [940, 80],
        [240, 46],
        "Negative (zero)",
        [],
        inputs=[g.inp("conditioning", "CONDITIONING")],
        outputs=[g.out("CONDITIONING", "CONDITIONING", [])],
    )
    g.add(
        8,
        "KSampler",
        [940, 180],
        [330, 262],
        "ACE sampler",
        _sampler_widgets(),
        inputs=[
            g.inp("model", "MODEL"),
            g.inp("positive", "CONDITIONING"),
            g.inp("negative", "CONDITIONING"),
            g.inp("latent_image", "LATENT"),
        ],
        outputs=[g.out("LATENT", "LATENT", [])],
    )
    g.add(
        9,
        "VAEDecodeAudio",
        [1340, 80],
        [280, 60],
        "ACE decode",
        [],
        inputs=[g.inp("samples", "LATENT"), g.inp("vae", "VAE")],
        outputs=[g.out("AUDIO", "AUDIO", [])],
    )
    g.add(
        10,
        "SaveAudio",
        [1340, 180],
        [320, 80],
        "FLAC master",
        [prefix],
        inputs=[g.inp("audio", "AUDIO")],
    )
    g.add(
        11,
        "SaveAudioMP3",
        [1340, 300],
        [320, 100],
        "MP3 320k",
        [prefix, "320k"],
        inputs=[g.inp("audio", "AUDIO")],
    )
    g.add(
        12,
        "Note",
        [1340, 440],
        [440, 500],
        "Operator note",
        [note],
    )
    g.link(1, 0, 2, 0, "MODEL")
    g.link(2, 0, 8, 0, "MODEL")
    g.link(1, 1, 6, 0, "CLIP")
    g.link(5, 0, 6, 1, "STRING")
    g.link(3, 0, 4, 0, "FLOAT")
    g.link(3, 0, 6, 2, "FLOAT")
    g.link(6, 0, 8, 1, "CONDITIONING")
    g.link(6, 0, 7, 0, "CONDITIONING")
    g.link(7, 0, 8, 2, "CONDITIONING")
    g.link(4, 0, 8, 3, "LATENT")
    g.link(8, 0, 9, 0, "LATENT")
    g.link(1, 2, 9, 1, "VAE")
    g.link(9, 0, 10, 0, "AUDIO")
    g.link(9, 0, 11, 0, "AUDIO")
    return g.dump(
        {
            "lab_profile": "us-safe-music",
            "lab_note": note,
            "lab_description": description,
            "ds": {"scale": 1, "offset": [0, 0]},
            "groups": [
                _group(1, "MODEL", 20, 40, 420, 280, "#3f789e"),
                _group(2, "DURATION", 20, 340, 420, 300, "#3f789e"),
                _group(3, "PROMPT", 480, 40, 820, 900, "#3f789e"),
                _group(4, "OUTPUT", 1320, 40, 500, 940, "#3f789e"),
            ],
        }
    )


def build_draft() -> dict:
    return _build_rap(
        "music-rap-draft-lab-example",
        32.0,
        DRAFT_LYRICS,
        "ez_rap_draft",
        DRAFT_NOTE,
        "US-safe rap draft: ACE-Step 1.5 turbo AIO, 32s boom-bap, invented vocal",
    )


def build_full() -> dict:
    return _build_rap(
        "music-rap-full-lab-example",
        96.0,
        FULL_LYRICS,
        "ez_rap_full",
        FULL_NOTE,
        "US-safe rap full track: ACE-Step 1.5 turbo AIO, 96s boom-bap, invented vocal",
    )


def main() -> None:
    graphs = {
        "music-rap-draft-lab-example.json": build_draft(),
        "music-rap-full-lab-example.json": build_full(),
    }
    for name, graph in graphs.items():
        path = WF / name
        path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
