#!/usr/bin/env python3
"""Build US-safe podcast lab graphs (audio-first + radio drama).

Not imported by pytest (leading underscore). Run from repo root:

  python3 tests/python/_build_podcast_workflows.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_podcast.nodes import (  # noqa: E402
    DISCLOSURE_TEXT,
    RADIO_SEED_SCRIPT,
    SEED_SCRIPT,
)

WF = ROOT / "workflows"

ACE_CKPT = "ace_step_1.5_turbo_aio.safetensors"
ACE_BED_TAGS = (
    "instrumental lo-fi bed, warm analog keys, light drums, no vocals, instrumental"
)
ACE_STING_TAGS = (
    "short instrumental sting, analog keys hit, no vocals, instrumental"
)
ACE_NEG_TAGS = "vocals, singing, choir, rap"
COVER_GRAPH = "klein-podcast-cover-lab-example.json"

AUDIO_NOTE_A = f"""## podcast-audio-first-lab-example

US-safe audio-first episode (Option A). Sequential Queue — do not load Klein + Wan + LTX + ACE-Step + TTS together.

1. Edit the script (human part). Enhance defaults **off** so Queue works offline.
2. Disclosure is prepended by the node (do not type it): {DISCLOSURE_TEXT}
3. Kokoro-82M built-in voices (Apache). Optional Chatterbox/Qwen3-TTS only with operator-owned refs.
4. ACE-Step 1.5 native bed: instrumental, no vocals, empty lyrics. Duck −15 dB under speech.
5. Saves: `ez_podcast_ep` FLAC master + `ez_podcast_mix` 320 kbps MP3.
6. Cover separately: Queue **{COVER_GRAPH}** (prefix `ez_podcast`, 1024²). Do not embed Klein here.
7. Loudness: `./scripts/utilities/podcast-loudnorm.sh run --in FILE` (−16 LUFS podcast / `--youtube` −14). Comfy cannot loudnorm.

Weights: `./scripts/manage.sh download-podcast --tier analog` (Kokoro) then `--tier acestep` (beds).
"""

AUDIO_NOTE_B = f"""## podcast-radio-drama-lab-example

US-safe one-graph radio drama (Option B). Lab-original fiction. Same legal engines as Option A.

- Writer flavor `radio_drama` (enhance **off**). Announcer + two Kokoro stock voices.
- ACE-Step sting + bed, instrumental only, empty lyrics. One 48 kHz-class master (`ez_radio_ep` / `ez_radio_mix`).
- Optional Wan silent bumper / LTX 5s hook groups are **off** (node mode never). Queue **wan-bumper-loop-lab-example** / **ltx-hook-av-lab-example** in a later session — not a one-graph film.
- Cover: Queue **{COVER_GRAPH}** separately.

{DISCLOSURE_TEXT}
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

    def out(self, name: str, ltype: str, links: list[int] | None = None) -> dict:
        return {"name": name, "type": ltype, "links": links if links is not None else [], "slot_index": 0}

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
        _assert_no_overlap(graph)
        return graph


def _ace_widgets(tags: str, duration: float, seed: int = 42) -> list:
    return [
        tags,
        "",
        seed,
        90,
        duration,
        "4",
        "en",
        "C major",
        False,
        2.0,
        0.85,
        0.9,
        0,
        0.0,
    ]


def _sampler_widgets() -> list:
    return [42, "fixed", 8, 1.0, "euler", "simple", 1.0]


def build_audio_first() -> dict:
    g = Graph("podcast-audio-first-lab-example")
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
        "EZPodcastScript",
        [500, 80],
        [420, 280],
        "ez_podcast_script",
        [SEED_SCRIPT, False, "podcast_two_host"],
        outputs=[g.out("script", "STRING", [])],
    )
    g.add(
        3,
        "EZPodcastDisclosure",
        [500, 400],
        [420, 80],
        "Disclosure bumper",
        [],
        inputs=[g.inp("script", "STRING")],
        outputs=[g.out("script", "STRING", [])],
    )
    g.add(
        4,
        "EZKokoroTTS",
        [500, 520],
        [420, 300],
        "ez_podcast_voice",
        ["af_heart", "am_michael", "bm_george", False, "kokoro", "", "", 1.0],
        inputs=[g.inp("script", "STRING")],
        outputs=[g.out("audio", "AUDIO", [])],
    )
    g.add(
        5,
        "TextEncodeAceStepAudio1.5",
        [40, 220],
        [400, 360],
        "ez_podcast_bed",
        _ace_widgets(ACE_BED_TAGS, 30.0),
        inputs=[g.inp("clip", "CLIP")],
        outputs=[g.out("CONDITIONING", "CONDITIONING", [])],
    )
    g.add(
        6,
        "TextEncodeAceStepAudio1.5",
        [40, 620],
        [400, 280],
        "ACE negative",
        _ace_widgets(ACE_NEG_TAGS, 30.0, seed=7),
        inputs=[g.inp("clip", "CLIP")],
        outputs=[g.out("CONDITIONING", "CONDITIONING", [])],
    )
    g.add(
        7,
        "EmptyAceStep1.5LatentAudio",
        [1440, 80],
        [320, 80],
        "Bed length (seconds)",
        [30.0, 1],
        outputs=[g.out("LATENT", "LATENT", [])],
    )
    g.add(
        8,
        "KSampler",
        [1440, 200],
        [320, 262],
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
        [1440, 510],
        [280, 60],
        "ACE decode",
        [],
        inputs=[g.inp("samples", "LATENT"), g.inp("vae", "VAE")],
        outputs=[g.out("AUDIO", "AUDIO", [])],
    )
    g.add(
        10,
        "AudioAdjustVolume",
        [1440, 610],
        [280, 80],
        "Duck bed −15 dB",
        [-15],
        inputs=[g.inp("audio", "AUDIO")],
        outputs=[g.out("AUDIO", "AUDIO", [])],
    )
    g.add(
        11,
        "AudioMerge",
        [1860, 80],
        [320, 120],
        "ez_podcast_mix overlay",
        ["overlay"],
        inputs=[g.inp("audio1", "AUDIO"), g.inp("audio2", "AUDIO")],
        outputs=[g.out("AUDIO", "AUDIO", [])],
    )
    g.add(
        12,
        "SaveAudio",
        [1860, 240],
        [320, 80],
        "FLAC master",
        ["ez_podcast_ep"],
        inputs=[g.inp("audio", "AUDIO")],
    )
    g.add(
        13,
        "SaveAudioMP3",
        [1860, 360],
        [320, 100],
        "MP3 320k",
        ["ez_podcast_mix", "320k"],
        inputs=[g.inp("audio", "AUDIO")],
    )
    g.add(
        14,
        "Note",
        [1860, 500],
        [400, 420],
        "Operator note",
        [AUDIO_NOTE_A],
    )
    g.link(2, 0, 3, 0, "STRING")
    g.link(3, 0, 4, 0, "STRING")
    g.link(1, 1, 5, 0, "CLIP")
    g.link(1, 1, 6, 0, "CLIP")
    g.link(1, 0, 8, 0, "MODEL")
    g.link(5, 0, 8, 1, "CONDITIONING")
    g.link(6, 0, 8, 2, "CONDITIONING")
    g.link(7, 0, 8, 3, "LATENT")
    g.link(8, 0, 9, 0, "LATENT")
    g.link(1, 2, 9, 1, "VAE")
    g.link(9, 0, 10, 0, "AUDIO")
    g.link(4, 0, 11, 0, "AUDIO")
    g.link(10, 0, 11, 1, "AUDIO")
    g.link(11, 0, 12, 0, "AUDIO")
    g.link(11, 0, 13, 0, "AUDIO")
    return g.dump(
        {
            "lab_profile": "us-safe-podcast",
            "lab_note": AUDIO_NOTE_A,
            "lab_description": "US-safe audio-first episode: Kokoro TTS + ACE-Step instrumental bed + mix",
            "ds": {"scale": 1, "offset": [0, 0]},
            "groups": [
                _group(1, "MODEL", 20, 40, 440, 900, "#3f789e"),
                _group(2, "PROMPT", 480, 40, 460, 820, "#3f789e"),
                _group(3, "SETTINGS", 1420, 40, 400, 700, "#a1309b"),
                _group(4, "OUTPUT", 1840, 40, 440, 920, "#3f789e"),
            ],
        }
    )


def build_radio_drama() -> dict:
    g = Graph("podcast-radio-drama-lab-example")
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
        "EZPodcastScript",
        [500, 80],
        [420, 300],
        "ez_radio_script",
        [RADIO_SEED_SCRIPT, False, "radio_drama"],
        outputs=[g.out("script", "STRING", [])],
    )
    g.add(
        3,
        "EZPodcastDisclosure",
        [500, 420],
        [420, 80],
        "Disclosure bumper",
        [],
        inputs=[g.inp("script", "STRING")],
        outputs=[g.out("script", "STRING", [])],
    )
    g.add(
        4,
        "EZKokoroTTS",
        [500, 540],
        [420, 320],
        "ez_radio_voice",
        ["af_bella", "am_michael", "bm_george", True, "kokoro", "", "", 1.0],
        inputs=[g.inp("script", "STRING")],
        outputs=[g.out("audio", "AUDIO", [])],
    )
    g.add(
        5,
        "TextEncodeAceStepAudio1.5",
        [40, 220],
        [400, 340],
        "ez_radio_sting",
        _ace_widgets(ACE_STING_TAGS, 4.0, seed=11),
        inputs=[g.inp("clip", "CLIP")],
        outputs=[g.out("CONDITIONING", "CONDITIONING", [])],
    )
    g.add(
        6,
        "TextEncodeAceStepAudio1.5",
        [40, 600],
        [400, 340],
        "ez_radio_bed",
        _ace_widgets(ACE_BED_TAGS, 40.0, seed=13),
        inputs=[g.inp("clip", "CLIP")],
        outputs=[g.out("CONDITIONING", "CONDITIONING", [])],
    )
    g.add(
        7,
        "TextEncodeAceStepAudio1.5",
        [40, 980],
        [400, 260],
        "ACE negative",
        _ace_widgets(ACE_NEG_TAGS, 40.0, seed=7),
        inputs=[g.inp("clip", "CLIP")],
        outputs=[g.out("CONDITIONING", "CONDITIONING", [])],
    )
    g.add(
        8,
        "EmptyAceStep1.5LatentAudio",
        [1440, 80],
        [320, 80],
        "Sting length",
        [4.0, 1],
        outputs=[g.out("LATENT", "LATENT", [])],
    )
    g.add(
        9,
        "EmptyAceStep1.5LatentAudio",
        [1440, 200],
        [320, 80],
        "Bed length",
        [40.0, 1],
        outputs=[g.out("LATENT", "LATENT", [])],
    )
    g.add(
        10,
        "KSampler",
        [1440, 320],
        [320, 262],
        "Sting sampler",
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
        11,
        "KSampler",
        [1440, 640],
        [320, 262],
        "Bed sampler",
        [43, "fixed", 8, 1.0, "euler", "simple", 1.0],
        inputs=[
            g.inp("model", "MODEL"),
            g.inp("positive", "CONDITIONING"),
            g.inp("negative", "CONDITIONING"),
            g.inp("latent_image", "LATENT"),
        ],
        outputs=[g.out("LATENT", "LATENT", [])],
    )
    g.add(
        12,
        "VAEDecodeAudio",
        [1860, 80],
        [280, 60],
        "Sting decode",
        [],
        inputs=[g.inp("samples", "LATENT"), g.inp("vae", "VAE")],
        outputs=[g.out("AUDIO", "AUDIO", [])],
    )
    g.add(
        13,
        "VAEDecodeAudio",
        [1860, 180],
        [280, 60],
        "Bed decode",
        [],
        inputs=[g.inp("samples", "LATENT"), g.inp("vae", "VAE")],
        outputs=[g.out("AUDIO", "AUDIO", [])],
    )
    g.add(
        14,
        "AudioConcat",
        [1860, 280],
        [300, 100],
        "Sting then bed",
        ["after"],
        inputs=[g.inp("audio1", "AUDIO"), g.inp("audio2", "AUDIO")],
        outputs=[g.out("AUDIO", "AUDIO", [])],
    )
    g.add(
        15,
        "AudioAdjustVolume",
        [1860, 420],
        [300, 80],
        "Duck −15 dB",
        [-15],
        inputs=[g.inp("audio", "AUDIO")],
        outputs=[g.out("AUDIO", "AUDIO", [])],
    )
    g.add(
        16,
        "AudioMerge",
        [1860, 540],
        [300, 120],
        "48 kHz-class mix",
        ["overlay"],
        inputs=[g.inp("audio1", "AUDIO"), g.inp("audio2", "AUDIO")],
        outputs=[g.out("AUDIO", "AUDIO", [])],
    )
    g.add(
        17,
        "SaveAudio",
        [2220, 80],
        [320, 80],
        "FLAC master",
        ["ez_radio_ep"],
        inputs=[g.inp("audio", "AUDIO")],
    )
    g.add(
        18,
        "SaveAudioMP3",
        [2220, 200],
        [320, 100],
        "MP3 320k",
        ["ez_radio_mix", "320k"],
        inputs=[g.inp("audio", "AUDIO")],
    )
    g.add(
        19,
        "Note",
        [2220, 340],
        [400, 420],
        "Operator note",
        [AUDIO_NOTE_B],
    )
    # Optional Wan bumper (never). Reuse silent-bumper pattern; Queue separately.
    g.add(
        30,
        "UNETLoader",
        [2720, 80],
        [360, 82],
        "Wan bumper (off)",
        ["wan2.2_ti2v_5B_fp16.safetensors", "default"],
        outputs=[g.out("MODEL", "MODEL", [])],
        mode=4,
    )
    g.add(
        31,
        "VHS_VideoCombine",
        [2720, 220],
        [320, 200],
        "ez_radio_bumper preview (off)",
        {
            "frame_rate": 16,
            "loop_count": 0,
            "filename_prefix": "ez_radio_bumper",
            "format": "video/h264-mp4",
            "pingpong": True,
            "save_output": True,
        },
        mode=4,
    )
    g.add(
        32,
        "UNETLoader",
        [2720, 480],
        [360, 82],
        "LTX hook (off)",
        ["ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors", "default"],
        outputs=[g.out("MODEL", "MODEL", [])],
        mode=4,
    )
    g.add(
        33,
        "VHS_VideoCombine",
        [2720, 620],
        [320, 200],
        "ez_radio_hook preview (off)",
        {
            "frame_rate": 24,
            "loop_count": 1,
            "filename_prefix": "ez_radio_hook",
            "format": "video/h264-mp4",
            "pingpong": False,
            "save_output": True,
        },
        mode=4,
    )
    g.link(2, 0, 3, 0, "STRING")
    g.link(3, 0, 4, 0, "STRING")
    g.link(1, 1, 5, 0, "CLIP")
    g.link(1, 1, 6, 0, "CLIP")
    g.link(1, 1, 7, 0, "CLIP")
    g.link(1, 0, 10, 0, "MODEL")
    g.link(5, 0, 10, 1, "CONDITIONING")
    g.link(7, 0, 10, 2, "CONDITIONING")
    g.link(8, 0, 10, 3, "LATENT")
    g.link(1, 0, 11, 0, "MODEL")
    g.link(6, 0, 11, 1, "CONDITIONING")
    g.link(7, 0, 11, 2, "CONDITIONING")
    g.link(9, 0, 11, 3, "LATENT")
    g.link(10, 0, 12, 0, "LATENT")
    g.link(1, 2, 12, 1, "VAE")
    g.link(11, 0, 13, 0, "LATENT")
    g.link(1, 2, 13, 1, "VAE")
    g.link(12, 0, 14, 0, "AUDIO")
    g.link(13, 0, 14, 1, "AUDIO")
    g.link(14, 0, 15, 0, "AUDIO")
    g.link(4, 0, 16, 0, "AUDIO")
    g.link(15, 0, 16, 1, "AUDIO")
    g.link(16, 0, 17, 0, "AUDIO")
    g.link(16, 0, 18, 0, "AUDIO")
    return g.dump(
        {
            "lab_profile": "us-safe-radio",
            "lab_note": AUDIO_NOTE_B,
            "lab_description": "US-safe radio drama: Kokoro cast + ACE-Step sting/bed; Wan/LTX bumpers off",
            "ds": {"scale": 1, "offset": [0, 0]},
            "groups": [
                _group(1, "MODEL", 20, 40, 440, 1240, "#3f789e"),
                _group(2, "PROMPT", 480, 40, 460, 860, "#3f789e"),
                _group(3, "SETTINGS", 1420, 40, 400, 920, "#a1309b"),
                _group(4, "OUTPUT", 1840, 40, 820, 800, "#3f789e"),
                _group(5, "WAN BUMPER (off)", 2700, 40, 400, 400, "#232"),
                _group(6, "LTX HOOK (off)", 2700, 460, 400, 400, "#232"),
            ],
        }
    )


def main() -> None:
    graphs = {
        "podcast-audio-first-lab-example.json": build_audio_first(),
        "podcast-radio-drama-lab-example.json": build_radio_drama(),
    }
    for name, graph in graphs.items():
        path = WF / name
        path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
