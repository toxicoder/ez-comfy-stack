#!/usr/bin/env python3
"""Build the US-safe dub-localize lab graph.

Not imported by pytest (leading underscore). Run from repo root:

  python3 tests/python/_build_dub_workflows.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from _lab_layout import LAB_GROUP_Y0, ensure_group_title_inset, group as _group
from _lab_paths import lab_dest
from _stamp_app_mode import stamp_suite_graph

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_dub.nodes import DISCLOSURE_TEXT, SEED_SCRIPT, SOURCE_NONE  # noqa: E402

DUB_NOTE = f"""## dub-localize-lab-example

US-safe multi-speaker clone-and-translate (YouTube / podcast localization). Occupancy **audio** — stop Klein / Wan / LTX first.

1. **I have rights** must be on. Queue refuses otherwise. Clone only recordings you own or have speaker consent to translate.
2. **Source file**: pick wav/mp4/mkv already in `${{COMFY_OUTPUT_DIR}}/input` (container `/inputs`), or **Upload media**. Optional **Source URL** for http(s) (`yt-dlp`). Host helper: `./scripts/utilities/dub-fetch.sh run --url URL` then reload the App so the file appears in the dropdown.
3. First Queue is **Stage analyze** (default): faster-whisper segments become turns, speakers cluster with Chatterbox `ve.pt`, same-speaker turns closer than 0.35 s merge, per-speaker clone refs write under `dubs/<slug>/speakers/` (6–10 s, one clean take when possible), then per-turn GGUF translate. After Queue, **Dub status** lists speaker/turn counts and `translated N/M`. Edit `text_target` in the JSON. Turn Rewrite translation **off**, set Stage **render**, Queue again. Missing llama.cpp / GGUF with Rewrite translation **on** is blocking (empty mix, empty `text_target`) — Queue does not clone English as the target. Do not ship Stage **all** blindly.
4. Chatterbox Multilingual V3 (MIT, PerTh on) — ISO `language_id` (`es`, not `Spanish`). **Clone CFG** auto is 0 on EN→ES (less English accent); 0.5 same-language. Pitch-preserving duration lock. Needs the complete snapshot (`ve.pt`, `s3gen.pt`, T3 V3, tokenizer JSON, `conds.pt`), not t3-only `comfy/tts`, and a wheel whose `from_local` accepts `t3_model=v3` (GitHub pin, not PyPI 0.1.7). Qwen3-TTS Base clones from the same refs (`download-podcast --tier qwen3tts`). Missing ASR/clone/llama.cpp: empty mix + **Dub status** (never the original recording). Clone lines longer than 300 characters are split.
5. MLA master is the duration-locked job-dir WAV `${{COMFY_OUTPUT_DIR}}/dubs/<slug>/ez_dub_yt.wav`. Optional `ez_dub_yt_48k.mp3` (48 kHz / 320k) is fail-soft in the job dir. Comfy `ez_dub_yt_*.mp3` is a 24 kHz preview — not the 320k master. Job dir also has mix WAV, SRT, speaker refs, `qc.json`, and disclosure sidecars.
6. YouTube Studio: Languages → Add language → upload `ez_dub_yt.wav` (audio-only, same length). Flip the synthetic/altered-content toggle. MLA eligibility varies by channel. Spoken bumper default **off**; sidecar is always written (localized `ez_dub.disclosure.txt` + English `ez_dub.disclosure.en.txt`). If you turn the bumper on, it overlays `ez_dub_mix.wav` only — it does not eat t=0 speech on the YT wav.
7. Loudness is in-graph raise-to-peak plus optional ffmpeg −14 LUFS (`loudnorm`). `./scripts/utilities/podcast-loudnorm.sh run --in FILE --target youtube` remains an operator fallback, not required.
8. No lip-sync. No celebrity refs.

Disclosure sidecar: {DISCLOSURE_TEXT}

Weights: `./scripts/manage.sh download-dub --tier asr` then `--tier clone` (pip-installs faster-whisper, the llama-cpp-python CPU wheel, then the Chatterbox V3 GitHub zip --no-deps --force-reinstall so torch 2.14 stays). Queue self-heals a missing llama.cpp wheel (needed for `text_target`). Missing pack is not a doctor failure. On DGX Spark, faster-whisper uses the CPU CTranslate2 wheel.
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
            "properties": {"Node name for S&R": ntype},
            "widgets_values": widgets,
            "title": title,
        }
        self.nodes.append(node)
        return node

    def out(self, name: str, ltype: str, links: list[int] | None = None, slot: int = 0) -> dict:
        return {
            "name": name,
            "type": ltype,
            "links": links if links is not None else [],
            "slot_index": slot,
        }

    def inp(self, name: str, ltype: str, link: int | None = None) -> dict:
        return {"name": name, "type": ltype, "link": link}

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
        ensure_group_title_inset(graph)
        _assert_no_overlap(graph)
        return graph


def build_dub_localize() -> dict:
    g = Graph("dub-localize-lab-example")
    g.add(
        1,
        "EZDubIngest",
        [40, 80],
        [420, 260],
        "ez_dub_ingest",
        [SOURCE_NONE, False, "episode", ""],
        outputs=[
            g.out("job_id", "STRING", [], slot=0),
            g.out("audio", "AUDIO", [], slot=1),
        ],
    )
    g.add(
        2,
        "EZDubScript",
        [500, 80],
        [440, 360],
        "ez_dub_script",
        [SEED_SCRIPT, True, "es", "auto", 0, "analyze"],
        inputs=[g.inp("job_id", "STRING")],
        outputs=[g.out("script", "STRING", [])],
    )
    g.add(
        3,
        "EZDubRender",
        [500, 480],
        [440, 300],
        "ez_dub_voice",
        ["chatterbox-ml", True, False, 1.0, -1.0, 0.5],
        inputs=[g.inp("script", "STRING"), g.inp("job_id", "STRING")],
        outputs=[g.out("audio", "AUDIO", [])],
    )
    g.add(
        4,
        "SaveAudio",
        [1000, 80],
        [320, 80],
        "FLAC master",
        ["ez_dub_mix"],
        inputs=[g.inp("audio", "AUDIO")],
    )
    g.add(
        5,
        "SaveAudioMP3",
        [1000, 200],
        [320, 100],
        "YouTube preview MP3",
        ["ez_dub_yt", "320k"],
        inputs=[g.inp("audio", "AUDIO")],
    )
    g.add(
        6,
        "Note",
        [1000, 340],
        [420, 480],
        "Operator note",
        [DUB_NOTE],
    )
    g.link(1, 0, 2, 0, "STRING")
    g.link(2, 0, 3, 0, "STRING")
    g.link(1, 0, 3, 1, "STRING")
    g.link(3, 0, 4, 0, "AUDIO")
    g.link(3, 0, 5, 0, "AUDIO")
    return g.dump(
        {
            "lab_profile": "us-safe-dub",
            "lab_note": DUB_NOTE,
            "lab_description": (
                "US-safe multi-speaker dub: rights-gated ingest, diarize, "
                "translate, Chatterbox ML V3 clone, duration-locked YouTube track"
            ),
            "ds": {"scale": 1, "offset": [0, 0]},
            "groups": [
                _group(1, "INPUT", 20, LAB_GROUP_Y0, 460, 380, "#3f789e"),
                _group(2, "PROMPT", 480, LAB_GROUP_Y0, 480, 780, "#3f789e"),
                _group(3, "OUTPUT", 980, LAB_GROUP_Y0, 460, 860, "#3f789e"),
            ],
        }
    )


def main() -> None:
    graph = build_dub_localize()
    path = lab_dest("dub-localize-lab-example", lane="audio")
    path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
