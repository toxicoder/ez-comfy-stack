#!/usr/bin/env python3
"""Build US-safe ACE-Step music lab graphs (rap draft/full, diss, EDM).

Not imported by pytest (leading underscore). Run from repo root:

  python3 tests/python/_build_music_workflows.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from _lab_layout import (
    GROUP_TITLE_INSET,
    LAB_GROUP_Y0,
    finalize_layout,
    group as _group,
)
from _lab_paths import LAB_ROOT, apply_lab_identity, lab_dest, lab_json, write_lab_graph
from _stamp_app_mode import NODE_MODE_BYPASS, stamp_suite_graph
from _wire_prompt_enhance import enable_lab_graph
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
from ez_music.albums import AlbumInfo, album_rel, shipped_albums  # noqa: E402
from ez_music.edm_examples import EDM_EXAMPLES, EdmExample  # noqa: E402
from ez_music.naming import album_output_dir  # noqa: E402
from ez_music.nodes import DRAFT_LYRICS, FULL_LYRICS  # noqa: E402

ACE_CKPT = "ace_step_1.5_turbo_aio.safetensors"
ACE_TAGS = BOOM_BAP_TAGS_88
COVER_THUMB = "klein/thumbnail.json"
COVER_PODCAST = "klein/podcast-cover.json"

DRAFT_NOTE = f"""## audio/music/rap-draft

US-safe rap **draft** (first Queue, same role as klein-still-draft). Native ACE-Step 1.5 turbo AIO. Sequential Queue — do not load Klein + Wan + LTX + ACE-Step together.

1. Weights: `./scripts/manage.sh download-music --tier turbo` (same AIO dest as `download-podcast --tier acestep`; ~10 GB, opt-in, not `download-models`).
2. Prompt enhance is **off** so tags, BPM, language, and `[verse]`/`[chorus]` stay as written. Turn Enhance on only if you want the 4B rewriter.
3. **Rap lyrics** owns the bars; ACE-Step Prompt Enhance owns tags. Lyrics are wired into ACE. Section tags `[verse]` / `[chorus]` / `[spoken word]` are vocal hints operators may add.
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

FULL_NOTE = f"""## audio/music/rap-full

US-safe rap **full track**. Same model and sampler as the draft (8 steps, cfg 1, euler, simple). Duration 96 s.

1. Queue **audio/music/rap-draft** first. Then this graph.
2. Weights: `./scripts/manage.sh download-music --tier turbo` (shared AIO with podcast acestep).
3. Prompt enhance is **off** so the canned bars stay as written. Turn Enhance on only if you want the 4B rewriter. Edit **Rap lyrics** before Queue (wired into ACE). Human rewrite required before any release.
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
    del pad
    finalize_layout(graph)


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
        rel = str(extra.pop("lab_rel", self.graph_id))
        graph = {
            "id": Path(rel).name,
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
        apply_lab_identity(graph, rel)
        enable_lab_graph(graph)
        stamp_suite_graph(graph)
        extra = graph.setdefault("extra", {})
        extra["lab_note"] = _rewrite_enhance_blurb(str(extra.get("lab_note") or ""))
        for node in graph["nodes"]:
            if node.get("type") != "Note":
                continue
            values = node.get("widgets_values") or [""]
            node["widgets_values"] = [_rewrite_enhance_blurb(str(values[0]))]
            break
        finalize_layout(graph)
        return graph


def _ace_widgets(
    lyrics: str,
    duration: float,
    seed: int = 42,
    *,
    tags: str = ACE_TAGS,
    bpm: int = 88,
    language: str = "en",
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
        language,
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
            2: [40, 252],
            3: [40, 412],
            4: [40, 600],
            5: [500, 80],
            6: [500, 572],
            7: [948, 80],
            8: [948, 212],
            9: [1340, 80],
            10: [1340, 212],
            11: [1340, 554],
            12: [1340, 896],
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


def _diss_cast(ex: DissExample) -> str:
    """One-line cast for a Nill Bye diss lab note.

    Arguments:
        ex: Catalog take.
    Returns:
        Cast sentence for the graph note.
    """
    if ex["series"] in {"civic", "civic-club"}:
        return (
            "Fictional MC **Nill Bye** (science guy) roasting public-record "
            "satire of Texas Gov. **Greg Abbott**. Abbott is a satire target, "
            "not a vocal identity"
        )
    if ex["series"] in {"federal", "federal-club"}:
        return (
            "Fictional MC **Nill Bye** (science guy) roasting public-record "
            "satire of **Donald Trump**. Trump is a satire target, "
            "not a vocal identity"
        )
    if ex["series"] in {"progress", "progress-club"}:
        return (
            "Fictional MC **Nill Bye** (science guy) on public-record "
            "**fixes**: methods, statutes, and measurement. No roast target"
        )
    return (
        "Fictional MCs **Nill Bye** (science guy) vs **Rake** (in his feels)"
    )


def _diss_note(ex: DissExample) -> str:
    duration_s = int(ex["duration"])
    kind = "progress" if ex["series"] in {"progress", "progress-club"} else "diss"
    return f"""## {ex["stem"]}

US-safe rap **{duration_s} s {kind}** take: **{ex["title"]}**. {_diss_cast(ex)}. Native ACE-Step 1.5 turbo AIO. Queue this graph **on its own** — draft-first is the generic lane, not a prerequisite. Occupancy **audio** only; a longer Queue is expected.

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
            "Live bass-set take. One 1–2 word DJ chop in a single `[chorus]` "
            "block; bed and drops stay empty-body `[drop]` / `[inst]` markers. "
            "Not a rap verse."
        )
        mode_blurb = (
            "Keep App **Vocal / instrumental** on vocal so the shout renders. "
            "Bed markers stay empty-body so ACE does not sing the arrangement."
        )
        labels_blurb = "`[drop]` / `[inst]` / `[outro]` and the one chorus chop"
    else:
        score_blurb = (
            "Live bass-set take. Instrumental score is empty-body ACE "
            "markers (`[drop - cues]`, `[inst - cues]`, `[outro]`) so ACE "
            "does not sing production notes. Drop-first warped hybrid-trap, "
            "trap drums, no quiet dips. Vocals are a rare DJ treat on other "
            "graphs, not here."
        )
        mode_blurb = (
            "Keep App **Vocal / instrumental** on instrumental so ACE does "
            "not sing. Encoder language is `unknown`. Free-text lines under "
            "a marker are lyrics — keep cues inside the brackets."
        )
        labels_blurb = "`[drop]` / `[inst]` / `[outro]`"
    return f"""## {ex["stem"]}

US-safe EDM **{duration_s} s** take: **{ex["title"]}**. Fictional act **Drive-through** (hardcore, pure of heart). Native ACE-Step 1.5 turbo AIO. {score_blurb} Queue this graph **on its own** — draft-first is the generic rap lane, not a prerequisite. Occupancy **audio** only; a longer Queue is expected.

1. Weights: `./scripts/manage.sh download-music --tier turbo` (same AIO dest as `download-podcast --tier acestep`; ~10 GB, opt-in, not `download-models`).
2. Prompt enhance is **off** so tags, BPM, language, and {labels_blurb} stay as written. Turn Enhance on only if you want the 4B rewriter.
3. Tags vs score: tags are genre/instrument hints; lyrics are the arrangement. {mode_blurb}
4. Original arrangements only. No “in the style of <living artist>”. No living-DJ names. No famous-hook paraphrases.
5. ACE-Step timbre is **invented**, not a cloned act.
6. Sampler: 8 steps, cfg 1, euler, simple. Duration {duration_s} s, bpm {ex["bpm"]}, language {"en" if treat else "unknown"}, timesignature 4, generate_audio_codes true. Seed {ex["seed"]}.
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
    album_meta: dict | None = None,
    rap_writer: bool = False,
) -> dict:
    pos, group_specs = _ace_layout(layout)
    pos[13] = [2200, 80]
    pos[14] = [2200, 280]
    groups = list(group_specs)
    groups.append((5, "METADATA", 2180, LAB_GROUP_Y0, 420, 520))
    meta = album_meta or {
        "artist": "",
        "album": "Demos",
        "title": "Untitled",
        "track": 1,
        "tracktotal": 1,
        "year": 2026,
        "art_mode": "skip",
        "prefix": prefix,
    }
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
    ace_pos = list(pos[5])
    enc_pos = list(pos[6])
    if rap_writer:
        g.add(
            15,
            "EZRapLyrics",
            list(pos[5]),
            [400, 320],
            "Rap lyrics",
            [lyrics, False],
            outputs=[g.out("lyrics", "STRING", [])],
        )
        ace_pos = [pos[5][0], pos[5][1] + 380.0]
        if ace_pos[1] + 360.0 > enc_pos[1] - 40.0:
            enc_pos[1] = ace_pos[1] + 400.0
    ace_inputs = []
    if rap_writer:
        ace_inputs = [g.inp("lyrics", "STRING", widget="lyrics")]
    g.add(
        5,
        "EZAceStepPromptEnhance",
        ace_pos,
        [400, 360],
        enhance_title,
        [tags, lyrics, False, ace_mode],
        inputs=ace_inputs or None,
        outputs=[
            g.out("tags", "STRING", []),
            g.out("lyrics", "STRING", []),
        ],
    )
    g.add(
        6,
        "TextEncodeAceStepAudio1.5",
        enc_pos,
        [400, 420],
        "ACE tags + lyrics",
        _ace_widgets(
            lyrics,
            duration,
            seed,
            tags=tags,
            bpm=bpm,
            language="unknown" if ace_mode == "instrumental" else "en",
        ),
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
    g.add(
        13,
        "LoadImage",
        pos[13],
        [320, 80],
        "Cover image",
        ["cover.png", "image"],
        mode=NODE_MODE_BYPASS,
        outputs=[g.out("IMAGE", "IMAGE", []), g.out("MASK", "MASK", [])],
    )
    g.add(
        14,
        "EZAudioMetadata",
        pos[14],
        [360, 220],
        "Album metadata",
        [
            meta.get("artist", ""),
            meta.get("album", ""),
            meta.get("title", ""),
            int(meta.get("track", 1)),
            int(meta.get("tracktotal", 1)),
            int(meta.get("year", 2026)),
            meta.get("art_mode", "skip"),
            prefix,
        ],
        inputs=[
            g.inp("audio", "AUDIO"),
            g.inp("cover", "IMAGE"),
        ],
        outputs=[g.out("audio", "AUDIO", [])],
    )
    g.link(1, 0, 2, 0, "MODEL")
    g.link(2, 0, 8, 0, "MODEL")
    g.link(1, 1, 6, 0, "CLIP")
    g.link(5, 0, 6, 1, "STRING")
    g.link(5, 1, 6, 2, "STRING")
    if rap_writer:
        g.link(15, 0, 5, 0, "STRING")
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
    g.link(9, 0, 14, 0, "AUDIO")
    extra = {
        "lab_rel": stem if "/" in stem else f"audio/music/{stem}",
        "lab_profile": "us-safe-music",
        "lab_note": note,
        "lab_description": description,
        "lab_optional_unwired": ["LoadImage"],
        "lab_album": {
            "artist": meta.get("artist", ""),
            "album": meta.get("album", ""),
            "title": meta.get("title", ""),
            "track": int(meta.get("track", 1)),
            "tracktotal": int(meta.get("tracktotal", 1)),
            "year": int(meta.get("year", 2026)),
            "art_mode": meta.get("art_mode", "skip"),
        },
        "ds": {"scale": 1, "offset": [0, 0]},
        "groups": [
            _group(gid, title, x, y, w, h, "#3f789e")
            for gid, title, x, y, w, h in group_specs
        ],
    }
    return g.dump(extra)


def build_draft() -> dict:
    return _build_ace(
        "audio/music/rap-draft",
        32.0,
        DRAFT_LYRICS,
        "ez_rap_draft",
        DRAFT_NOTE,
        "US-safe rap draft: ACE-Step 1.5 turbo AIO, 32s boom-bap, invented vocal",
        rap_writer=True,
        album_meta={
            "artist": "Local",
            "album": "Demos",
            "title": "Rap Draft",
            "track": 1,
            "tracktotal": 1,
            "year": 2026,
            "art_mode": "skip",
        },
    )


def build_full() -> dict:
    return _build_ace(
        "audio/music/rap-full",
        96.0,
        FULL_LYRICS,
        "ez_rap_full",
        FULL_NOTE,
        "US-safe rap full track: ACE-Step 1.5 turbo AIO, 96s boom-bap, invented vocal",
        rap_writer=True,
        album_meta={
            "artist": "Local",
            "album": "Demos",
            "title": "Rap Full",
            "track": 1,
            "tracktotal": 1,
            "year": 2026,
            "art_mode": "skip",
        },
    )


def _catalog_meta(ex: DissExample | EdmExample) -> dict:
    return {
        "artist": ex["artist"],
        "album": ex["album"],
        "title": title_case(ex["title"]),
        "track": int(ex["track"]),
        "tracktotal": int(ex["tracktotal"]),
        "year": int(ex["year"]),
        "art_mode": "skip",
        "prefix": ex["prefix"],
    }


def title_case(title: str) -> str:
    from ez_music.naming import title_case_song

    return title_case_song(title)


def build_diss(ex: DissExample) -> dict:
    return _build_ace(
        ex["rel"],
        float(ex["duration"]),
        ex["lyrics"],
        ex["prefix"],
        _diss_note(ex),
        ex["description"],
        tags=ex["tags"],
        bpm=int(ex["bpm"]),
        seed=int(ex["seed"]),
        album_meta=_catalog_meta(ex),
        rap_writer=True,
    )


def build_edm(ex: EdmExample) -> dict:
    return _build_ace(
        ex["rel"],
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
        album_meta=_catalog_meta(ex),
    )


def _clear_legacy_artist_trees() -> None:
    """Remove pre-album artist folders (phaseN catalogs)."""
    import shutil

    for artist in ("nill-bye", "drive-through"):
        root = LAB_ROOT / "audio" / artist
        if root.is_dir():
            shutil.rmtree(root)
            print(f"removed {root.relative_to(ROOT)}")


def _node(graph: dict, ntype: str) -> dict:
    return next(n for n in graph["nodes"] if n.get("type") == ntype)


def build_cover(info: AlbumInfo) -> dict:
    """Klein 1024×1024 square still for one album cover."""
    graph = json.loads(lab_json("klein/instagram-square").read_text(encoding="utf-8"))
    rel = album_rel(info["artist_slug"], info["slug"], "cover")
    apply_lab_identity(graph, rel)
    prefix = f"albums/{info['artist']}/{info['title']}/cover"
    prompt = info["cover_prompt"]
    for node in graph["nodes"]:
        ntype = node.get("type")
        if ntype == "EZKleinPromptEnhance":
            values = list(node.get("widgets_values") or [])
            if values:
                values[0] = prompt
            node["widgets_values"] = values
        if ntype == "CLIPTextEncode" and "Positive" in str(node.get("title") or ""):
            node["widgets_values"] = [prompt]
        if ntype == "SaveImage":
            node["widgets_values"] = [prefix]
        if ntype == "EmptyFlux2LatentImage":
            node["widgets_values"] = [1024, 1024, 1]
        if ntype == "Note":
            node["widgets_values"] = [
                f"## {rel}\n\nAlbum cover for **{info['artist']} — {info['title']}**. "
                "Occupancy klein — stop ACE-Step / Wan / LTX. Queue this before "
                "album-render --art generate. Prefix "
                f"`{prefix}`.\n"
            ]
    extra = graph.setdefault("extra", {})
    extra["lab_profile"] = "us-safe-music-cover"
    extra["lab_note"] = graph["nodes"][-1]["widgets_values"][0] if graph["nodes"] else ""
    extra["lab_description"] = f"Album cover still for {info['artist']} / {info['title']}"
    extra["lab_album"] = {
        "artist": info["artist"],
        "album": info["title"],
        "album_slug": info["slug"],
        "role": "cover",
        "year": info["year"],
    }
    stamp_suite_graph(graph)
    return graph


def build_album(info: AlbumInfo, tracks: list[str]) -> dict:
    """Pack-only album App (zip + m3u). Full render is album-render CLI."""
    rel = album_rel(info["artist_slug"], info["slug"], "album")
    note = (
        f"## {rel}\n\n"
        f"Album **{info['title']}** by **{info['artist']}** "
        f"({len(tracks)} tracks).\n\n"
        "Queue this graph to zip whatever is already in "
        f"`${{COMFY_OUTPUT_DIR}}/{album_output_dir(info['artist'], info['title'])}/`.\n"
        "Generate the full album in one go:\n\n"
        f"`./scripts/manage.sh album-render --album {info['artist_slug']}/{info['slug']} "
        "--art skip|upload|generate`\n\n"
        "Occupancy: audio for tracks, klein first when --art generate. "
        "Do not co-resident Klein + ACE-Step.\n"
    )
    g = Graph(rel)
    g.add(
        1,
        "Note",
        [40, 80],
        [640, 420],
        "Operator note",
        [note],
    )
    g.add(
        2,
        "EZAlbumPack",
        [720, 80],
        [360, 120],
        "Pack album zip",
        [info["artist"], info["title"]],
        outputs=[g.out("zip_path", "STRING", [])],
    )
    extra = {
        "lab_rel": rel,
        "lab_profile": "us-safe-music-album",
        "lab_note": note,
        "lab_description": f"Pack {info['title']} zip + m3u",
        "lab_album": {
            "artist": info["artist"],
            "album": info["title"],
            "album_slug": info["slug"],
            "artist_slug": info["artist_slug"],
            "role": "album",
            "year": info["year"],
            "tracks": tracks,
            "cover_graph": album_rel(info["artist_slug"], info["slug"], "cover"),
        },
        "ds": {"scale": 1, "offset": [0, 0]},
        "groups": [
            _group(1, "NOTE", 20, LAB_GROUP_Y0, 680, 500, "#3f789e"),
            _group(2, "PACK", 700, LAB_GROUP_Y0, 400, 220, "#3f789e"),
        ],
    }
    return g.dump(extra)


def main() -> None:
    _clear_legacy_artist_trees()
    write_lab_graph(lab_dest("audio/music/rap-draft"), build_draft())
    write_lab_graph(lab_dest("audio/music/rap-full"), build_full())
    by_album: dict[tuple[str, str], list[str]] = {}
    for diss in DISS_EXAMPLES:
        write_lab_graph(lab_dest(diss["rel"]), build_diss(diss))
        key = (diss["artist_slug"], diss["album_slug"])
        by_album.setdefault(key, []).append(diss["stem"])
    for edm in EDM_EXAMPLES:
        write_lab_graph(lab_dest(edm["rel"]), build_edm(edm))
        key = ("drive-through", edm["album_slug"])
        by_album.setdefault(key, []).append(edm["stem"])
    for info in shipped_albums():
        key = (info["artist_slug"], info["slug"])
        tracks = by_album.get(key, [])
        write_lab_graph(
            lab_dest(album_rel(info["artist_slug"], info["slug"], "cover")),
            build_cover(info),
        )
        write_lab_graph(
            lab_dest(album_rel(info["artist_slug"], info["slug"], "album")),
            build_album(info, tracks),
        )
        print(f"wrote album {info['artist']} / {info['title']} ({len(tracks)} tracks)")


if __name__ == "__main__":
    main()
