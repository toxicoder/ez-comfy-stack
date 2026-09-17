"""ez_* pack encyclopedia rows (podcast, dub, film, DCC).

Helpers and combo catalogs live in :mod:`workflow_nodes_lib`.
"""

from __future__ import annotations

from typing import Any

from workflow_nodes_lib import _n, _s, _w

def pack_nodes() -> dict[str, Any]:
    """Podcast, dub, film, DCC, research, quality, forge.

    Returns:
        Node specs keyed by type.
    """
    nodes: dict[str, Any] = {}
    nodes["EZPodcastScript"] = _n(
        "Podcast Script",
        "Draft Speaker A/B (and Announcer) lines via the on-box GGUF.",
        origin="ez_podcast",
        sockets=[_s("script", "STRING", "out", "Labeled script for TTS.")],
        widgets=[
            _w("sample", index=0, typ="COMBO", rng="custom", desc="Sample or Custom.", gen="Custom keeps authored turns."),
            _w("prompt", index=1, desc="Speaker A/B script.", gen="Keep hosts original. No celebrity refs."),
            _w("enhance", index=2, typ="BOOLEAN", rng="false on seeded graphs", desc="Run the writer.", gen="Off pins the canned lab script."),
            _w("flavor", index=3, typ="COMBO", desc="Two-host vs radio drama.", gen="radio_drama allows Announcer lines.", choices=[("podcast_two_host", "Two-host episode (lab podcast)."), ("radio_drama", "Radio drama with announcer.")]),
            _w("catalog", index=4, desc="Catalog id.", gen="Leave as stamped."),
        ],
    )
    nodes["EZPodcastDisclosure"] = _n(
        "Podcast Disclosure",
        "Prepend the fixed synthesized-voices bumper. Operators cannot edit the string.",
        origin="ez_podcast",
        sockets=[
            _s("script", "STRING", "in", "Episode script."),
            _s("script", "STRING", "out", "Disclosure + script."),
        ],
    )
    nodes["EZKokoroTTS"] = _n(
        "Kokoro TTS",
        "Two-host (plus optional announcer) TTS. Kokoro-82M stock voices by default.",
        origin="ez_podcast",
        lab="Never ships celebrity WAVs. Empty clone refs fall back to Kokoro.",
        sockets=[
            _s("script", "STRING", "in", "Labeled script."),
            _s("audio", "AUDIO", "out", "Speech stem."),
        ],
        widgets=[
            _w("speaker_a_voice", index=0, typ="COMBO", rng="af_heart / af_bella", desc="Kokoro voice A.", gen="Stock voices only. Changing voice changes timbre, not the script."),
            _w("speaker_b_voice", index=1, typ="COMBO", rng="am_michael", desc="Kokoro voice B.", gen="Keep A/B distinct so the mix reads as two hosts."),
            _w("announcer_voice", index=2, typ="COMBO", rng="bm_george", desc="Announcer voice.", gen="Used when include_announcer is on."),
            _w("include_announcer", index=3, typ="BOOLEAN", desc="Speak Announcer lines.", gen="true on radio-drama; false on two-host podcast."),
            _w("backend", index=4, typ="COMBO", rng="kokoro", desc="TTS engine.", gen="kokoro is the lab default. chatterbox/qwen3tts need operator-owned refs.", choices=[("kokoro", "Kokoro-82M ONNX/CPU (lab)."), ("chatterbox", "Opt-in clone. Empty ref falls back."), ("qwen3tts", "Opt-in clone. Empty ref falls back.")]),
            _w("speaker_a_ref", index=5, desc="Optional clone reference path.", gen="Leave empty. Do not paste celebrity WAVs."),
            _w("speaker_b_ref", index=6, desc="Optional clone reference path.", gen="Leave empty."),
            _w("speed", index=7, typ="FLOAT", rng="0.5–1.5, lab 1.0", desc="Speaking rate.", gen="1.0 is natural. Faster shrinks the episode and can clip diction."),
        ],
    )
    dub_langs = [
        ("es", "Spanish (lab default target)."),
        ("en", "English."),
        ("ar", "Arabic."),
        ("da", "Danish."),
        ("de", "German."),
        ("el", "Greek."),
        ("fi", "Finnish."),
        ("fr", "French."),
        ("he", "Hebrew."),
        ("hi", "Hindi."),
        ("it", "Italian."),
        ("ja", "Japanese."),
        ("ko", "Korean."),
        ("ms", "Malay."),
        ("nl", "Dutch."),
        ("no", "Norwegian."),
        ("pl", "Polish."),
        ("pt", "Portuguese."),
        ("ru", "Russian."),
        ("sv", "Swedish."),
        ("sw", "Swahili."),
        ("tr", "Turkish."),
        ("zh", "Chinese."),
    ]
    nodes["EZDubIngest"] = _n(
        "Dub ingest (file or URL)",
        "Extract audio from input/ or a URL. Queue refuses unless I have rights is on.",
        origin="ez_dub",
        sockets=[
            _s("job_id", "STRING", "out", "Job slug."),
            _s("audio", "AUDIO", "out", "Short preview AUDIO (full wav is on disk)."),
        ],
        widgets=[
            _w("source", index=0, typ="COMBO", rng="(none)", desc="File in Comfy input/.", gen="Pick a file or leave (none) and use source_url."),
            _w("have_rights", index=1, typ="BOOLEAN", rng="false", desc="Rights gate.", gen="Queue refuses unless true. Not legal advice."),
            _w("job_slug", index=2, rng="episode", desc="Job folder name.", gen="Sanitized slug under the dub jobstore."),
            _w("source_url", index=3, desc="Optional http(s) URL.", gen="Empty unless you ingest from the network."),
        ],
    )
    nodes["EZDubScript"] = _n(
        "Dub transcript + translate",
        "Diarize + ASR + on-box GGUF translation. Widget JSON is the human edit surface.",
        origin="ez_dub",
        sockets=[
            _s("job_id", "STRING", "in", "From ingest."),
            _s("script", "STRING", "out", "Translation JSON."),
        ],
        widgets=[
            _w("prompt", index=0, desc="Editable translation JSON.", gen="Turn Enhance off to pin widget text after a human rewrite."),
            _w("enhance", index=1, typ="BOOLEAN", desc="Rewrite translation via GGUF.", gen="Off pins your edits."),
            _w("target_language", index=2, typ="COMBO", rng="es", desc="Target ISO code.", gen="es is the lab smoke. Clone CFG auto 0.3 on EN→ES.", choices=dub_langs),
            _w("source_language", index=3, typ="COMBO", rng="auto", desc="Source language.", gen="auto detects. Pin en if ASR mis-detects.", choices=[("auto", "Detect.")] + dub_langs),
            _w("max_speakers", index=4, typ="INT", rng="0–12, 0 = auto", desc="Diarize cap.", gen="0 lets the pipeline decide."),
            _w("stage", index=5, typ="COMBO", rng="all", desc="Analyze vs render vs both.", gen="all analyzes then clones. render skips ASR. analyze stops after JSON.", choices=[("all", "Analyze then clone (lab)."), ("analyze", "ASR/translate only."), ("render", "Skip ASR; clone widget JSON.")]),
        ],
    )
    nodes["EZDubRender"] = _n(
        "Dub clone + mix",
        "Zero-shot clone, duration-lock, mix, SRT, disclosure sidecar.",
        origin="ez_dub",
        sockets=[
            _s("script", "STRING", "in", "Translation JSON."),
            _s("job_id", "STRING", "in", "Job slug."),
            _s("audio", "AUDIO", "out", "Mix (empty on analyze stage)."),
        ],
        widgets=[
            _w("engine", index=0, typ="COMBO", rng="chatterbox-ml", desc="Clone engine.", gen="chatterbox-ml is the lab default. qwen3tts is opt-in.", choices=[("chatterbox-ml", "Lab default."), ("qwen3tts", "Opt-in Qwen3-TTS.")]),
            _w("keep_bed", index=1, typ="BOOLEAN", rng="true", desc="Keep source bed under the clone.", gen="true duration-locks to the source (YouTube Languages)."),
            _w("spoken_disclosure", index=2, typ="BOOLEAN", rng="false", desc="Overlay a spoken bumper on the mix wav.", gen="Off: mix starts on speech. YT wav stays source-timed either way."),
            _w("speed", index=3, typ="FLOAT", rng="0.5–1.5, 1.0", desc="Clone speaking rate.", gen="Stay near 1.0 or the duration lock fights you."),
            _w("cfg_weight", index=4, typ="FLOAT", rng="−1.0 = auto", desc="Clone CFG.", gen="−1 auto. Lab auto 0.3 on EN→ES (retry 0.5)."),
            _w("exaggeration", index=5, typ="FLOAT", rng="0.25–2.0, 0.5", desc="Chatterbox exaggeration.", gen="0.5 is the lab default. Higher is cartoon-emotive."),
        ],
    )
    nodes["EZFilmDisclosure"] = _n(
        "LTX AI-media disclosure",
        "Prepend the LTX Community License AI-media disclosure. Idempotent. Not legal advice.",
        origin="ez_film",
        sockets=[_s("text", "STRING", "out", "Disclosure (+ optional extra).")],
        widgets=[_w("text", index=0, desc="Optional extra line after the stock disclosure.", gen="Empty = stock sentence only. Do not strip provenance.")],
    )
    nodes["EZUnloadModels"] = _n(
        "Unload models",
        "Pass-through IMAGE that unloads diffusion models first.",
        origin="ez_film",
        lab="Keeps Klein 4B and LTX-2.5 from sitting in memory together on 90s one-click films.",
        sockets=[
            _s("image", "IMAGE", "in", "Identity still."),
            _s("image", "IMAGE", "out", "Same still after unload."),
        ],
    )
    nodes["EZFilmConcat"] = _n(
        "Save 90s film (MP4)",
        "Concat 18 LTX 5.00 s MP4s, cap 90 s, H.264 CRF 18 + AAC + loudnorm + faststart.",
        origin="ez_film",
        lab="Queue once. xfade_cs is audio-only acrossfade; 0 is a hard cut. go-see ships xfade_cs 8. act=0 is a 90s film master; act=1–5 writes ez_<slug>_actN_90s.mp4.",
        sockets=[
            *[_s(f"shot_{i:02d}", "VHS_FILENAMES", "in", f"Shot {i:02d} MP4.") for i in range(1, 19)],
            _s("disclosure", "STRING", "in", "EZFilmDisclosure text."),
            _s("path", "STRING", "out", "Published MP4 path."),
        ],
        widgets=[
            _w("film", index=0, typ="COMBO", desc="Film id.", gen="Picks output name and shot-map. Must match the graph.", choices=[("go-see", "Parkour 90s."), ("still-here", "Household morning 90s."), ("switchyard", "Night freight-yard 90s."), ("tide-table", "Dawn skiff 7.5 min."), ("night-oven", "Bakery 7.5 min."), ("glasshouse", "Storm glasshouse 7.5 min."), ("last-lane", "Night two-lane 7.5 min."), ("breakwater", "Storm-wall walk 7.5 min.")]),
            _w("cap_seconds", index=1, typ="FLOAT", rng="90.0 max", desc="Hard duration cap for this 18-shot stitch.", gen="Stay 90. This is a stitch cap, not a denoise length. 7.5 min masters are host concat of 90 stems."),
            _w("xfade_cs", index=2, typ="INT", rng="0–50; 10 = 0.10 s", desc="Audio-only acrossfade in centiseconds.", gen="0 = hard cut (still-here, switchyard). 8 = 0.08 s audio cross on go-see / last-lane / breakwater. Picture stays cut-only so duration stays on picture."),
            _w("act", index=3, typ="INT", rng="0–5", desc="0 = 90s film master; 1–5 = act master for a 7.5 min film.", gen="Festival shorts Queue five act graphs, then concat-shots.sh writes ez_<slug>_450s.mp4."),
        ],
    )
    nodes["EZDCCLoadGuideStill"] = _n(
        "Load guide still",
        "Load clay/depth/canny/first/last from guides/<slug>/<shot_id>/. Fail-closed QC.",
        origin="ez_dcc",
        sockets=[
            _s("image", "IMAGE", "out", "Still."),
            _s("mask", "MASK", "out", "Alpha."),
            _s("metadata", "STRING", "out", "Shot JSON."),
        ],
        widgets=[
            _w("slug", index=0, rng="go-see", desc="Guide-pack slug.", gen="Must exist under ${COMFY_OUTPUT_DIR}/guides/."),
            _w("shot_id", index=1, rng="12", desc="Shot folder.", gen="Matches blender-guide dump ids."),
            _w("layer", index=2, typ="COMBO", rng="first", desc="Which PNG.", gen="first/last are RGB plates. clay/depth/canny are guides. Depth is mist 0–1 (near=white).", choices=[("first", "First-frame RGB."), ("last", "Last-frame RGB."), ("clay", "Clay beauty."), ("depth", "Depth mist."), ("canny", "Canny edges.")]),
        ],
    )
    nodes["EZDCCLoadGuideVideo"] = _n(
        "Load guide video path",
        "Absolute clay.mp4 / depth.mp4 / canny.mp4 at 24 fps. Does not decode 120 frames.",
        origin="ez_dcc",
        sockets=[
            _s("path", "STRING", "out", "Absolute mp4 path."),
            _s("fps", "INT", "out", "24."),
        ],
        widgets=[
            _w("slug", index=0, desc="Guide-pack slug.", gen="Same as the still loader."),
            _w("shot_id", index=1, desc="Shot folder.", gen="Same as the still loader."),
            _w("layer", index=2, typ="COMBO", rng="clay / depth / canny", desc="Which mp4.", gen="IC-LoRA envelopes wire depth.mp4 or canny.mp4.", choices=[("clay", "Clay mp4."), ("depth", "Depth mp4 (lab IC-LoRA)."), ("canny", "Canny mp4.")]),
        ],
    )
    nodes["EZDCCLoadStillPack"] = _n(
        "Load still pack",
        "Load a blender-stills plate from guides/<slug>/stills/<plate>/.",
        origin="ez_dcc",
        sockets=[
            _s("image", "IMAGE", "out", "Plate."),
            _s("mask", "MASK", "out", "Alpha."),
            _s("metadata", "STRING", "out", "Pack JSON."),
        ],
        widgets=[
            _w("slug", index=0, rng="go-see", desc="Pack slug.", gen="guides/<slug>/stills/."),
            _w("plate", index=1, rng="mug", desc="Plate id.", gen="Lab TRELLIS mug uses plate=mug."),
            _w("layer", index=2, typ="COMBO", rng="first", desc="Which layer.", gen="first is the RGB hero. depth/canny/normal are workbench passes.", choices=[("first", "RGB hero."), ("rgb", "RGB alias."), ("depth", "Depth."), ("canny", "Canny."), ("normal", "Normals.")]),
        ],
    )
    nodes["EZDCCOccupancyGate"] = _n(
        "Occupancy gate",
        "Pass-through IMAGE that fail-closes on occupancy XOR. Does not start Compose.",
        origin="ez_dcc",
        lab="Missing .occupancy.json passes. idle / blender-desk / llm-desk / mismatch fail.",
        sockets=[
            _s("image", "IMAGE", "in", "Still to gate."),
            _s("image", "IMAGE", "out", "Same still if occupancy matches."),
        ],
        widgets=[
            _w("required_mode", index=0, typ="COMBO", desc="Heavy GPU mode that must already be entered.", gen="klein / wan / ltx / trellis. Pick the family you are about to Queue.", choices=[("klein", "Klein 4B stills."), ("trellis", "TRELLIS.2."), ("wan", "Wan 5B."), ("ltx", "LTX-2.5.")]),
        ],
    )
    nodes["EZCreativeResearch"] = _n(
        "Creative research",
        "Creative-process chat with optional web search and sequential research subagents. No UNET.",
        origin="ez_research",
        lab="Occupancy llm. Handoff Prompt Forge. Fail-soft without a GGUF. Not Comfy Cloud's In-App Agent.",
        sockets=[_s("reply", "STRING", "out", "Assistant reply / brief.")],
        widgets=[
            _w("sample", index=0, typ="COMBO", rng="custom", desc="Sample question or Custom.", gen="Custom uses the Message box."),
            _w("prompt", index=1, desc="Message.", gen="One widget, then Queue. Not a streaming chat box."),
            _w("mode", index=2, typ="COMBO", rng="research", desc="Chat vs planner+search.", gen="research runs subagents. chat is a single turn.", choices=[("chat", "Single-turn chat."), ("research", "Planner + sequential subagents (lab).")]),
            _w("web_search", index=3, typ="BOOLEAN", rng="true", desc="Allow web search.", gen="true uses the research MCP. Off stays on-box."),
            _w("subagents", index=4, typ="INT", rng="1–3, lab 2", desc="How many research subagents.", gen="2 is the lab default. 3 is slower."),
            _w("history", index=5, desc="Prior turns.", gen="Paste if you continue a desk session."),
            _w("catalog", index=6, desc="Catalog id.", gen="Leave as stamped."),
        ],
    )
    nodes["EZQuality"] = _n(
        "Quality",
        "Workflow-global Lab / Draft / High combo. JS overlays family-specific sampler and Klein UNET widgets.",
        origin="ez_quality",
        lab="Default lab leaves authored widgets. Draft is faster. High is slower. Distilled Klein High without Klein base keeps CFG 1.0. Never selects banned weights. Not --tier quality.",
        sockets=[_s("quality", "STRING", "out", "Selected quality id (lab, draft, high).")],
        widgets=[
            _w(
                "quality",
                index=0,
                typ="COMBO",
                rng="lab",
                desc="Lab default, Draft (faster), or High (slower).",
                gen="Family-specific overlays on steps, CFG, and Klein 4B UNET. Does not change size, length, CLIP, or VAE. Klein base High needs download-image --tier base.",
                choices=[
                    ("lab", "Authored lab widgets. Default."),
                    ("draft", "Faster: fewer steps. Klein stays CFG 1.0 distilled when already distilled."),
                    ("high", "Slower: more steps. Klein base 4B + CFG 3.5 when that UNET is on disk; else extra distilled steps at CFG 1.0."),
                ],
            ),
        ],
    )
    nodes["EZAppForge"] = _n(
        "App Forge",
        "Clone a shipped lab graph into live _user/ as a new App. No UNET.",
        origin="ez_studio_forge",
        lab="Occupancy llm. Does not Queue the result. Does not write _lab. Keyword heuristic if GGUF is missing. Path D: studio-mcp. Not Comfy Cloud MCP.",
        sockets=[_s("path", "STRING", "out", "Written _user path or error.")],
        widgets=[
            _w("sample", index=0, typ="COMBO", rng="custom", desc="Sample brief or Custom.", gen="Custom uses the Brief box."),
            _w("prompt", index=1, desc="Brief.", gen="What the new App should make. Template auto picks a lab graph."),
            _w("template", index=2, typ="COMBO", rng="auto", desc="Lab graph to clone.", gen="auto uses the GGUF planner or a keyword heuristic. Pin klein/instagram-square to skip."),
            _w("slug", index=3, desc="Filename stem.", gen="Live _user/<slug>.app.json. Lowercase letters, digits, hyphen."),
            _w("as_app", index=4, typ="BOOLEAN", rng="true", desc="Write an App.", gen="true writes *.app.json for the Apps sidebar."),
            _w("overwrite", index=5, typ="BOOLEAN", rng="false", desc="Replace existing.", gen="false refuses an existing _user file."),
            _w("catalog", index=6, desc="Catalog id.", gen="Leave as stamped."),
        ],
    )
    return nodes
