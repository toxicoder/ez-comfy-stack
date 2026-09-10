#!/usr/bin/env python3
"""Build US-safe ACE-Step music lab graphs (rap draft/full, diss, EDM).

Not imported by pytest (leading underscore). Run from repo root:

  python3 tests/python/_build_music_workflows.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from _lab_layout import GROUP_TITLE_INSET, LAB_GROUP_Y0, ensure_group_title_inset, group as _group
from _lab_paths import LAB_ROOT, lab_dest
from _stamp_app_mode import stamp_suite_graph
from _wire_prompt_enhance import _rewrite_enhance_blurb

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_music.diss_examples import (  # noqa: E402
    BOOM_BAP_TAGS_88,
    DISS_EXAMPLES,
    LOFI_TAGS,
    TRAP_TAGS,
    DissExample,
)
from ez_music.edm_examples import EDM_EXAMPLES, EdmExample  # noqa: E402
from ez_music.nodes import DRAFT_LYRICS, FULL_LYRICS  # noqa: E402

ACE_CKPT = "ace_step_1.5_turbo_aio.safetensors"
ACE_TAGS = BOOM_BAP_TAGS_88
COVER_THUMB = "klein-thumbnail-lab-example.json"
COVER_PODCAST = "klein-podcast-cover-lab-example.json"

DRAFT_NOTE = f"""## music-rap-draft-lab-example

US-safe rap **draft** (first Queue, same role as klein-still-draft). Native ACE-Step 1.5 turbo AIO. Sequential Queue — do not load Klein + Wan + LTX + ACE-Step together.

1. Weights: `./scripts/manage.sh download-music --tier turbo` (same AIO dest as `download-podcast --tier acestep`; ~10 GB, opt-in, not `download-models`).
2. Prompt enhance is **off** so tags, BPM, language, and `[verse]`/`[chorus]` stay as written. Turn Enhance on only if you want the 4B rewriter.
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
3. Prompt enhance is **off** so the canned bars stay as written. Turn Enhance on only if you want the 4B rewriter. Edit lyrics before Queue. Human rewrite required before any release.
4. Original lyrics only. No living-artist names. No famous-hook paraphrases. No “in the style of <living artist>”.
5. ACE-Step vocal is an invented timbre, not a clone.
6. Saves: `ez_rap_full` FLAC + 320 kbps MP3.
7. Cover: sequential Queue **{COVER_THUMB}** / **{COVER_PODCAST}**. Do not embed Klein.
8. Do not co-resident with LTX / Wan / Klein on this Spark.

Canned style swaps (tags widget only):
- trap: {TRAP_TAGS}
- lo-fi: {LOFI_TAGS}
"""


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
        stamp_suite_graph(graph)
        extra = graph.setdefault("extra", {})
        extra["lab_note"] = _rewrite_enhance_blurb(str(extra.get("lab_note") or ""))
        for node in graph["nodes"]:
            if node.get("type") != "Note":
                continue
            values = node.get("widgets_values") or [""]
            node["widgets_values"] = [_rewrite_enhance_blurb(str(values[0]))]
            break
        ensure_group_title_inset(graph)
        _assert_no_overlap(graph)
        return graph


def _ace_widgets(
    lyrics: str,
    duration: float,
    seed: int = 42,
    *,
    tags: str = ACE_TAGS,
    bpm: int = 88,
) -> list:
    # seed is followed by control_after_generate (native TextEncodeAceStepAudio1.5).
    return [
        tags,
        lyrics,
        seed,
        "fixed",
        bpm,
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


def _sampler_widgets(seed: int = 42) -> list:
    return [seed, "fixed", 8, 1.0, "euler", "simple", 1.0]


# Node ids 1-12 stay fixed. Values are [x, y] for each layout.
# Groups: (id, title, x, y, w, h). Color is applied at dump.
_ACE_LAYOUTS: dict[str, tuple[dict[int, list[float]], list[tuple]]] = {
    "column": (
        {
            1: [40, 80],
            2: [40, 220],
            3: [40, 380],
            4: [40, 520],
            5: [500, 80],
            6: [500, 520],
            7: [940, 80],
            8: [940, 180],
            9: [1340, 80],
            10: [1340, 180],
            11: [1340, 300],
            12: [1340, 440],
        },
        [
            (1, "MODEL", 20, LAB_GROUP_Y0, 420, 280),
            (2, "DURATION", 20, 380 - GROUP_TITLE_INSET, 420, 300),
            (3, "PROMPT", 480, LAB_GROUP_Y0, 820, 1000),
            (4, "OUTPUT", 1320, LAB_GROUP_Y0, 500, 940),
        ],
    ),
    "wide-stage": (
        {
            1: [40, 80],
            2: [40, 220],
            3: [40, 380],
            4: [40, 520],
            5: [660, 80],
            6: [660, 520],
            7: [1140, 80],
            8: [1140, 180],
            9: [1680, 80],
            10: [1680, 180],
            11: [1680, 300],
            12: [1680, 440],
        },
        [
            (1, "MODEL", 20, LAB_GROUP_Y0, 420, 280),
            (2, "DURATION", 20, 380 - GROUP_TITLE_INSET, 420, 300),
            (3, "PROMPT", 640, LAB_GROUP_Y0, 860, 1000),
            (4, "OUTPUT", 1660, LAB_GROUP_Y0, 500, 940),
        ],
    ),
    "stacked-tower": (
        {
            1: [40, 80],
            2: [40, 220],
            3: [40, 380],
            4: [40, 520],
            5: [40, 680],
            6: [40, 1080],
            7: [480, 680],
            8: [480, 780],
            9: [920, 80],
            10: [920, 180],
            11: [920, 300],
            12: [920, 440],
        },
        [
            (1, "MODEL", 20, LAB_GROUP_Y0, 420, 280),
            (2, "DURATION", 20, 380 - GROUP_TITLE_INSET, 420, 300),
            (3, "PROMPT", 20, 680 - GROUP_TITLE_INSET, 820, 900),
            (4, "OUTPUT", 900, LAB_GROUP_Y0, 500, 940),
        ],
    ),
    "prompt-left": (
        {
            1: [900, 80],
            2: [900, 220],
            3: [900, 380],
            4: [900, 520],
            5: [40, 80],
            6: [40, 520],
            7: [480, 80],
            8: [480, 180],
            9: [1400, 80],
            10: [1400, 180],
            11: [1400, 300],
            12: [1400, 440],
        },
        [
            (1, "MODEL", 880, LAB_GROUP_Y0, 420, 280),
            (2, "DURATION", 880, 380 - GROUP_TITLE_INSET, 420, 300),
            (3, "PROMPT", 20, LAB_GROUP_Y0, 820, 1000),
            (4, "OUTPUT", 1380, LAB_GROUP_Y0, 500, 940),
        ],
    ),
    "output-rail": (
        {
            1: [580, 80],
            2: [580, 220],
            3: [580, 380],
            4: [580, 520],
            5: [1060, 80],
            6: [1060, 520],
            7: [1500, 80],
            8: [1500, 180],
            9: [40, 80],
            10: [40, 180],
            11: [40, 300],
            12: [40, 440],
        },
        [
            (1, "MODEL", 560, LAB_GROUP_Y0, 420, 280),
            (2, "DURATION", 560, 380 - GROUP_TITLE_INSET, 420, 300),
            (3, "PROMPT", 1040, LAB_GROUP_Y0, 820, 1000),
            (4, "OUTPUT", 20, LAB_GROUP_Y0, 500, 940),
        ],
    ),
}


def _ace_layout(name: str) -> tuple[dict[int, list[float]], list[tuple]]:
    """Return node positions and group boxes for one ACE graph layout.

    Arguments:
        name: Layout key (column, wide-stage, stacked-tower, prompt-left,
            output-rail).
    Returns:
        (node_id -> [x, y], group tuples).
    Raises:
        ValueError: unknown layout name.
    """
    if name not in _ACE_LAYOUTS:
        raise ValueError(f"unknown ACE layout {name}")
    return _ACE_LAYOUTS[name]


def _diss_note(ex: DissExample) -> str:
    duration_s = int(ex["duration"])
    return f"""## {ex["stem"]}

US-safe rap **{duration_s} s diss** take: **{ex["title"]}**. Fictional MCs **Nill Bye** (science guy) vs **Rake** (in his feels). Native ACE-Step 1.5 turbo AIO. Queue this graph **on its own** — draft-first is the generic lane, not a prerequisite. Occupancy **audio** only; a longer Queue is expected.

1. Weights: `./scripts/manage.sh download-music --tier turbo` (same AIO dest as `download-podcast --tier acestep`; ~10 GB, opt-in, not `download-models`).
2. Prompt enhance is **off** so tags, BPM, language, and `[verse]`/`[chorus]` stay as written. Turn Enhance on only if you want the 4B rewriter.
3. Tags vs lyrics: tags are genre/instrument/vocal hints; lyrics are the bars. Section tags `[verse]` / `[chorus]` / `[spoken word]` are vocal hints operators may add.
4. Original lyrics only. No “in the style of <living artist>”. No living-MC names. No famous-hook paraphrases.
5. ACE-Step vocal is an **invented** identity, not a cloned MC.
6. Sampler: 8 steps, cfg 1, euler, simple. Duration {duration_s} s, bpm {ex["bpm"]}, language en, timesignature 4, generate_audio_codes true. Seed {ex["seed"]}.
7. Saves: `{ex["prefix"]}` FLAC master + 320 kbps MP3 under `${{COMFY_OUTPUT_DIR}}`.
8. Cover separately: Queue **{COVER_THUMB}** or **{COVER_PODCAST}**. Do not embed Klein here.
9. Human rewrite the lyrics before any release. Prompts are not authorship (USCO Part 2 / Thaler).
10. Do not co-resident with LTX / Wan / Klein on this Spark.

Beat-only pass: append instrumental, no vocals, and replace lyrics with [inst].
"""


def _edm_note(ex: EdmExample) -> str:
    duration_s = int(ex["duration"])
    treat = ex["ace_mode"] == "vocal"
    if treat:
        score_blurb = (
            "Live rave-set take. Sparse DJ vocal chop in one short chorus "
            "block; bed and drops stay `[inst]`. Not a rap verse."
        )
        mode_blurb = (
            "Keep App **Vocal / instrumental** on vocal so the shout renders. "
            "`[inst]` lines are instrument cues so ACE does not sing the bed."
        )
        labels_blurb = "`[inst]` / `[intro]` / `[outro]` and the one chorus chop"
    else:
        score_blurb = (
            "Live rave-set take. Instrumental arrangement score in `[inst]` "
            "blocks: dance-floor flow unique to this take, heavy drops, "
            "mix-in/out. Vocals are a rare DJ treat on other graphs, not here."
        )
        mode_blurb = (
            "Keep App **Vocal / instrumental** on instrumental so ACE does "
            "not sing the score."
        )
        labels_blurb = "`[inst]` / `[intro]` / `[outro]`"
    return f"""## {ex["stem"]}

US-safe EDM **{duration_s} s** take: **{ex["title"]}**. Fictional act **Drive-through** (hardcore, pure of heart). Native ACE-Step 1.5 turbo AIO. {score_blurb} Queue this graph **on its own** — draft-first is the generic rap lane, not a prerequisite. Occupancy **audio** only; a longer Queue is expected.

1. Weights: `./scripts/manage.sh download-music --tier turbo` (same AIO dest as `download-podcast --tier acestep`; ~10 GB, opt-in, not `download-models`).
2. Prompt enhance is **off** so tags, BPM, language, and {labels_blurb} stay as written. Turn Enhance on only if you want the 4B rewriter.
3. Tags vs score: tags are genre/instrument hints; lyrics are the arrangement. {mode_blurb}
4. Original arrangements only. No “in the style of <living artist>”. No living-DJ names. No famous-hook paraphrases.
5. ACE-Step timbre is **invented**, not a cloned act.
6. Sampler: 8 steps, cfg 1, euler, simple. Duration {duration_s} s, bpm {ex["bpm"]}, language en, timesignature 4, generate_audio_codes true. Seed {ex["seed"]}.
7. Saves: `{ex["prefix"]}` FLAC master + 320 kbps MP3 under `${{COMFY_OUTPUT_DIR}}`.
8. Cover separately: Queue **{COVER_THUMB}** or **{COVER_PODCAST}**. Do not embed Klein here.
9. Human selection and edit before any release. Prompts are not authorship (USCO Part 2 / Thaler).
10. Do not co-resident with LTX / Wan / Klein on this Spark.
"""


def _build_ace(
    stem: str,
    duration: float,
    lyrics: str,
    prefix: str,
    note: str,
    description: str,
    *,
    tags: str = ACE_TAGS,
    bpm: int = 88,
    seed: int = 42,
    ace_mode: str = "vocal",
    enhance_title: str = "ez_rap_prompt",
    layout: str = "column",
) -> dict:
    pos, group_specs = _ace_layout(layout)
    g = Graph(stem)
    g.add(
        1,
        "CheckpointLoaderSimple",
        pos[1],
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
        pos[2],
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
        pos[3],
        [280, 82],
        "Song Duration",
        [duration, "fixed"],
        outputs=[prim_out],
        properties={"Run widget replace on values": False},
    )
    g.add(
        4,
        "EmptyAceStep1.5LatentAudio",
        pos[4],
        [320, 82],
        "Latent length (seconds)",
        [duration, 1],
        inputs=[g.inp("seconds", "FLOAT", widget="seconds")],
        outputs=[g.out("LATENT", "LATENT", [])],
    )
    g.add(
        5,
        "EZAceStepPromptEnhance",
        pos[5],
        [400, 360],
        enhance_title,
        [tags, lyrics, False, ace_mode],
        outputs=[
            g.out("tags", "STRING", []),
            g.out("lyrics", "STRING", []),
        ],
    )
    g.add(
        6,
        "TextEncodeAceStepAudio1.5",
        pos[6],
        [400, 420],
        "ACE tags + lyrics",
        _ace_widgets(lyrics, duration, seed, tags=tags, bpm=bpm),
        inputs=[
            g.inp("clip", "CLIP"),
            g.inp("tags", "STRING", widget="tags"),
            g.inp("lyrics", "STRING", widget="lyrics"),
            g.inp("duration", "FLOAT", widget="duration"),
        ],
        outputs=[g.out("CONDITIONING", "CONDITIONING", [])],
    )
    g.add(
        7,
        "ConditioningZeroOut",
        pos[7],
        [240, 46],
        "Negative (zero)",
        [],
        inputs=[g.inp("conditioning", "CONDITIONING")],
        outputs=[g.out("CONDITIONING", "CONDITIONING", [])],
    )
    g.add(
        8,
        "KSampler",
        pos[8],
        [330, 262],
        "ACE sampler",
        _sampler_widgets(seed),
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
        pos[9],
        [280, 60],
        "ACE decode",
        [],
        inputs=[g.inp("samples", "LATENT"), g.inp("vae", "VAE")],
        outputs=[g.out("AUDIO", "AUDIO", [])],
    )
    g.add(
        10,
        "SaveAudio",
        pos[10],
        [320, 80],
        "FLAC master",
        [prefix],
        inputs=[g.inp("audio", "AUDIO")],
    )
    g.add(
        11,
        "SaveAudioMP3",
        pos[11],
        [320, 100],
        "MP3 320k",
        [prefix, "320k"],
        inputs=[g.inp("audio", "AUDIO")],
    )
    g.add(
        12,
        "Note",
        pos[12],
        [440, 500],
        "Operator note",
        [note],
    )
    g.link(1, 0, 2, 0, "MODEL")
    g.link(2, 0, 8, 0, "MODEL")
    g.link(1, 1, 6, 0, "CLIP")
    g.link(5, 0, 6, 1, "STRING")
    g.link(5, 1, 6, 2, "STRING")
    g.link(3, 0, 4, 0, "FLOAT")
    g.link(3, 0, 6, 3, "FLOAT")
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
                _group(gid, title, x, y, w, h, "#3f789e")
                for gid, title, x, y, w, h in group_specs
            ],
        }
    )


def build_draft() -> dict:
    return _build_ace(
        "music-rap-draft-lab-example",
        32.0,
        DRAFT_LYRICS,
        "ez_rap_draft",
        DRAFT_NOTE,
        "US-safe rap draft: ACE-Step 1.5 turbo AIO, 32s boom-bap, invented vocal",
    )


def build_full() -> dict:
    return _build_ace(
        "music-rap-full-lab-example",
        96.0,
        FULL_LYRICS,
        "ez_rap_full",
        FULL_NOTE,
        "US-safe rap full track: ACE-Step 1.5 turbo AIO, 96s boom-bap, invented vocal",
    )


def build_diss(ex: DissExample) -> dict:
    return _build_ace(
        ex["stem"],
        float(ex["duration"]),
        ex["lyrics"],
        ex["prefix"],
        _diss_note(ex),
        ex["description"],
        tags=ex["tags"],
        bpm=int(ex["bpm"]),
        seed=int(ex["seed"]),
    )


def build_edm(ex: EdmExample) -> dict:
    return _build_ace(
        ex["stem"],
        float(ex["duration"]),
        ex["lyrics"],
        ex["prefix"],
        _edm_note(ex),
        ex["description"],
        tags=ex["tags"],
        bpm=int(ex["bpm"]),
        seed=int(ex["seed"]),
        ace_mode=ex["ace_mode"],
        enhance_title="ez_edm_prompt",
        layout=ex["layout"],
    )


def _clear_artist_root_json(artist: str) -> None:
    """Remove leftover *-lab-example.json at the artist folder root."""
    root = LAB_ROOT / "audio" / artist
    if not root.is_dir():
        return
    for path in root.glob("*-lab-example.json"):
        path.unlink()
        print(f"removed {path.relative_to(ROOT)}")


def main() -> None:
    _clear_artist_root_json("nill-bye")
    _clear_artist_root_json("drive-through")
    placements: list[tuple[str, dict, str | None]] = [
        ("music-rap-draft-lab-example.json", build_draft(), None),
        ("music-rap-full-lab-example.json", build_full(), None),
    ]
    for diss in DISS_EXAMPLES:
        placements.append(
            (
                f"{diss['stem']}.json",
                build_diss(diss),
                f"nill-bye/phase{diss['phase']}",
            )
        )
    for edm in EDM_EXAMPLES:
        placements.append(
            (
                f"{edm['stem']}.json",
                build_edm(edm),
                f"drive-through/phase{edm['phase']}",
            )
        )
    for name, graph, subdir in placements:
        path = lab_dest(name, subdir=subdir)
        path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
