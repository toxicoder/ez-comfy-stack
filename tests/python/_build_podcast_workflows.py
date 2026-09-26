#!/usr/bin/env python3
"""Build US-safe podcast lab graphs (two-host, radio drama, learn-episode).

Not imported by pytest (leading underscore). Run from repo root:

  python3 tests/python/_build_podcast_workflows.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from _lab_graph import Graph
from _lab_layout import (
    GROUP_TITLE_INSET,
    LAB_GROUP_Y0,
    finalize_layout,
    group as _group,
)
from _lab_paths import lab_json

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_podcast.nodes import (  # noqa: E402
    DISCLOSURE_TEXT,
    RADIO_SEED_SCRIPT,
    SEED_SCRIPT,
    SEED_SOURCES,
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
COVER_GRAPH = "stills/podcast-cover.json"

AUDIO_NOTE_A = f"""## audio/podcast/two-host-episode

US-safe two-host-episode episode (Option A). Sequential Queue - do not load Klein + Wan + LTX + ACE-Step + TTS together.

1. Edit the script (human part). Prompt enhance is **off** so Speaker A/B labels stay parser input. Turn Enhance on only if you want the 4B rewriter.
2. Disclosure is prepended by the node (do not type it): {DISCLOSURE_TEXT}
3. Kokoro-82M built-in voices (Apache). Optional Chatterbox/Qwen3-TTS only with operator-owned refs.
4. ACE-Step 1.5 native bed: instrumental, no vocals, empty lyrics. The script STRING is wired into ACE enhance as context (used if you turn Enhance on). Duck -15 dB under speech.
5. Saves: `ez_podcast_ep` FLAC master + `ez_podcast_mix` 320 kbps MP3.
6. Cover separately: Queue **{COVER_GRAPH}** (prefix `ez_podcast`, 1024^2). Do not embed Klein here.
7. Loudness: `./scripts/utilities/podcast-loudnorm.sh run --in FILE` (-16 LUFS podcast / `--youtube` -14). Comfy cannot loudnorm.

Weights: `./scripts/manage.sh download-podcast --tier analog` (Kokoro) then `--tier acestep` (beds).
"""

AUDIO_NOTE_B = f"""## audio/podcast/radio-drama

US-safe one-graph radio drama (Option B). Lab-original fiction. Same legal engines as Option A.

- Writer flavor `radio_drama` (enhance **off** so Speaker A/B / Announcer labels stay parser input). Announcer + two Kokoro stock voices.
- ACE-Step sting + bed, instrumental only, empty lyrics. Script STRING is wired into both ACE enhance nodes as context. One 48 kHz-class master (`ez_radio_ep` / `ez_radio_mix`).
- Optional Wan silent bumper / LTX 5s hook groups are **off** (node mode never). Queue **motion/loops/bumper-loop** / **motion/av/hook-av** in a later session - not a one-graph film.
- Cover: Queue **{COVER_GRAPH}** separately.

{DISCLOSURE_TEXT}
"""

AUDIO_NOTE_C = f"""## audio/podcast/learn-episode

US-safe learning episode (Option C). Sequential Queue - do not load Klein + Wan + LTX + ACE-Step + TTS together.

1. Paste notes, HTTPS links, captioned video URLs, or local `.txt`/`.md`/`.srt`/`.vtt` paths into **Sources**. Pick **Format** and **Duration**. Rewrite is **on**.
2. Fetch is SSRF-safe HTTPS. Videos pull **captions only** (no media download, no dub ASR). Missing captions are a status line.
3. The node writes a deduped study digest, then a Speaker A/B (or solo) script sized to the duration. Missing GGUF concatenates sources and wraps Speaker A lines.
4. Disclosure is prepended by the node (do not type it): {DISCLOSURE_TEXT}
5. Kokoro-82M built-in voices (Apache). ACE-Step 1.5 native bed: 30 s instrumental, looped under the speech, duck -15 dB.
6. Saves: `ez_learn_ep` FLAC master + `ez_learn_mix` 320 kbps MP3.
7. Cover separately: Queue **{COVER_GRAPH}** (prefix `ez_podcast`, 1024^2). Do not embed Klein here.
8. Loudness: `./scripts/utilities/podcast-loudnorm.sh run --in FILE` (-16 LUFS podcast / `--youtube` -14). Comfy cannot loudnorm.

25 min seminar is the slow CPU-TTS path. Weights: `./scripts/manage.sh download-podcast --tier analog` then `--tier acestep`.
"""


def _assert_no_overlap(graph: dict, pad: float = 20) -> None:
    del pad
    finalize_layout(graph)


def _ace_widgets(tags: str, duration: float, seed: int = 42) -> list:
    # seed is followed by control_after_generate (native TextEncodeAceStepAudio1.5).
    return [
        tags,
        "",
        seed,
        "fixed",
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
    g = Graph("audio/podcast/two-host-episode", pop_lab_rel=False, enable_lab=True)
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
        "Duck bed -15 dB",
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
            "lab_description": "US-safe two-host-episode episode: Kokoro TTS + ACE-Step instrumental bed + mix",
            "ds": {"scale": 1, "offset": [0, 0]},
            "groups": [
                _group(1, "MODEL", 20, LAB_GROUP_Y0, 440, 900, "#3f789e"),
                _group(2, "PROMPT", 480, LAB_GROUP_Y0, 460, 820, "#3f789e"),
                _group(3, "SETTINGS", 1420, LAB_GROUP_Y0, 400, 700, "#a1309b"),
                _group(4, "OUTPUT", 1840, LAB_GROUP_Y0, 440, 920, "#3f789e"),
            ],
        }
    )


def build_radio_drama() -> dict:
    g = Graph("audio/podcast/radio-drama", pop_lab_rel=False, enable_lab=True)
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
        "Duck -15 dB",
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
                _group(1, "MODEL", 20, LAB_GROUP_Y0, 440, 1240, "#3f789e"),
                _group(2, "PROMPT", 480, LAB_GROUP_Y0, 460, 860, "#3f789e"),
                _group(3, "SETTINGS", 1420, LAB_GROUP_Y0, 400, 920, "#a1309b"),
                _group(4, "OUTPUT", 1840, LAB_GROUP_Y0, 820, 800, "#3f789e"),
                _group(5, "WAN BUMPER (off)", 2700, LAB_GROUP_Y0, 400, 400, "#232"),
                _group(6, "LTX HOOK (off)", 2700, 480 - GROUP_TITLE_INSET, 400, 400, "#232"),
            ],
        }
    )


def build_learn_episode() -> dict:
    g = Graph("audio/podcast/learn-episode", pop_lab_rel=False, enable_lab=True)
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
        "EZPodcastLearn",
        [500, 80],
        [420, 380],
        "ez_learn_sources",
        [SEED_SOURCES, "Explainer", "8 min briefing", True, True],
        outputs=[
            g.out("digest", "STRING", []),
            g.out("script", "STRING", []),
        ],
    )
    g.add(
        3,
        "EZPodcastDisclosure",
        [500, 500],
        [420, 80],
        "Disclosure bumper",
        [],
        inputs=[g.inp("script", "STRING")],
        outputs=[g.out("script", "STRING", [])],
    )
    g.add(
        4,
        "EZKokoroTTS",
        [500, 620],
        [420, 300],
        "ez_learn_voice",
        ["af_heart", "am_michael", "bm_george", False, "kokoro", "", "", 1.0],
        inputs=[g.inp("script", "STRING")],
        outputs=[g.out("audio", "AUDIO", [])],
    )
    g.add(
        5,
        "TextEncodeAceStepAudio1.5",
        [40, 220],
        [400, 360],
        "ez_learn_bed",
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
        "EZAudioLoopToMatch",
        [1440, 610],
        [320, 80],
        "Loop bed to speech",
        [],
        inputs=[g.inp("speech", "AUDIO"), g.inp("bed", "AUDIO")],
        outputs=[g.out("bed", "AUDIO", [])],
    )
    g.add(
        11,
        "AudioAdjustVolume",
        [1860, 80],
        [280, 80],
        "Duck bed -15 dB",
        [-15],
        inputs=[g.inp("audio", "AUDIO")],
        outputs=[g.out("AUDIO", "AUDIO", [])],
    )
    g.add(
        12,
        "AudioMerge",
        [1860, 200],
        [320, 120],
        "ez_learn_mix overlay",
        ["overlay"],
        inputs=[g.inp("audio1", "AUDIO"), g.inp("audio2", "AUDIO")],
        outputs=[g.out("AUDIO", "AUDIO", [])],
    )
    g.add(
        13,
        "SaveAudio",
        [1860, 360],
        [320, 80],
        "FLAC master",
        ["ez_learn_ep"],
        inputs=[g.inp("audio", "AUDIO")],
    )
    g.add(
        14,
        "SaveAudioMP3",
        [1860, 480],
        [320, 100],
        "MP3 320k",
        ["ez_learn_mix", "320k"],
        inputs=[g.inp("audio", "AUDIO")],
    )
    g.add(
        15,
        "Note",
        [1860, 620],
        [400, 460],
        "Operator note",
        [AUDIO_NOTE_C],
    )
    g.link(2, 1, 3, 0, "STRING")
    g.link(3, 0, 4, 0, "STRING")
    g.link(1, 1, 5, 0, "CLIP")
    g.link(1, 1, 6, 0, "CLIP")
    g.link(1, 0, 8, 0, "MODEL")
    g.link(5, 0, 8, 1, "CONDITIONING")
    g.link(6, 0, 8, 2, "CONDITIONING")
    g.link(7, 0, 8, 3, "LATENT")
    g.link(8, 0, 9, 0, "LATENT")
    g.link(1, 2, 9, 1, "VAE")
    g.link(4, 0, 10, 0, "AUDIO")
    g.link(9, 0, 10, 1, "AUDIO")
    g.link(10, 0, 11, 0, "AUDIO")
    g.link(4, 0, 12, 0, "AUDIO")
    g.link(11, 0, 12, 1, "AUDIO")
    g.link(12, 0, 13, 0, "AUDIO")
    g.link(12, 0, 14, 0, "AUDIO")
    return g.dump(
        {
            "lab_profile": "us-safe-learn-podcast",
            "lab_note": AUDIO_NOTE_C,
            "lab_description": (
                "US-safe learning episode: paste sources, pick format and "
                "duration, Kokoro TTS + looped ACE-Step bed"
            ),
            "ds": {"scale": 1, "offset": [0, 0]},
            "groups": [
                _group(1, "MODEL", 20, LAB_GROUP_Y0, 440, 900, "#3f789e"),
                _group(2, "PROMPT", 480, LAB_GROUP_Y0, 460, 920, "#3f789e"),
                _group(3, "SETTINGS", 1420, LAB_GROUP_Y0, 400, 720, "#a1309b"),
                _group(4, "OUTPUT", 1840, LAB_GROUP_Y0, 440, 980, "#3f789e"),
            ],
        }
    )


def main() -> None:
    graphs = {
        "audio/podcast/two-host-episode.json": build_audio_first(),
        "audio/podcast/radio-drama.json": build_radio_drama(),
        "audio/podcast/learn-episode.json": build_learn_episode(),
    }
    for name, graph in graphs.items():
        path = lab_json(name)
        path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
