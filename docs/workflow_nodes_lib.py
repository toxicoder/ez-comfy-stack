"""Shared encyclopedia helpers and combo catalogs.

Widget builders (`_s` / `_w` / `_n`) and Comfy combo lists used by family
modules. The façade `workflow_nodes.encyclopedia()` concatenates families.
"""

from __future__ import annotations

from typing import Any

# ComfyUI v0.37.0 combo catalogs, ACE language/key, and image scale/crop.
_SAMPLER_CHOICES: list[tuple[str, str]] = [
    ("euler", "First-order ODE. Lab default for Klein, LTX, ACE, and most stills. Fast and stable at CFG 1.0."),
    ("euler_cfg_pp", "Euler with CFG++. Rarely needed on distilled Klein (CFG is already 1.0)."),
    ("euler_ancestral", "Adds ancestral noise each step. More variation; weaker exact seed lock."),
    ("euler_ancestral_cfg_pp", "Ancestral Euler with CFG++."),
    ("heun", "Second-order Heun. Slower, sometimes smoother; not a lab default."),
    ("heunpp2", "Higher-order Heun variant."),
    ("exp_heun_2_x0", "Exponential Heun (x0 prediction)."),
    ("exp_heun_2_x0_sde", "Exponential Heun SDE. Extra stochasticity."),
    ("dpm_2", "DPM-Solver-2. Two function evals per step."),
    ("dpm_2_ancestral", "Ancestral DPM-2."),
    ("lms", "Linear multistep. Older; keep for experiments only."),
    ("dpm_fast", "Fast DPM. Coarse, good for previews."),
    ("dpm_adaptive", "Adaptive DPM. Step count is a hint, not a hard budget."),
    ("dpmpp_2s_ancestral", "DPM++ 2S ancestral. Common SD1.5 pick; not a Klein default."),
    ("dpmpp_2s_ancestral_cfg_pp", "DPM++ 2S ancestral with CFG++."),
    ("dpmpp_sde", "DPM++ SDE. Stochastic, slower."),
    ("dpmpp_sde_gpu", "DPM++ SDE on GPU noise."),
    ("dpmpp_2m", "DPM++ 2M. Smooth; often used on SD-family, not distilled Klein."),
    ("dpmpp_2m_cfg_pp", "DPM++ 2M with CFG++."),
    ("dpmpp_2m_sde", "DPM++ 2M SDE."),
    ("dpmpp_2m_sde_gpu", "DPM++ 2M SDE GPU noise."),
    ("dpmpp_2m_sde_heun", "DPM++ 2M SDE Heun."),
    ("dpmpp_2m_sde_heun_gpu", "DPM++ 2M SDE Heun GPU."),
    ("dpmpp_3m_sde", "DPM++ 3M SDE."),
    ("dpmpp_3m_sde_gpu", "DPM++ 3M SDE GPU."),
    ("ddpm", "Classic DDPM. Slow; do not use on 121-frame LTX."),
    ("lcm", "Latent Consistency. Needs an LCM-tuned model; not lab Klein/Wan/LTX."),
    ("ipndm", "iPNDM multistep."),
    ("ipndm_v", "iPNDM (v-prediction)."),
    ("deis", "DEIS multistep."),
    ("cfgpp_ud10_ab", "CFG++ UD10 AB. Added in ComfyUI 0.35; not a lab default."),
    ("res_multistep", "Res multistep. Some turbo recipes."),
    ("res_multistep_cfg_pp", "Res multistep CFG++."),
    ("res_multistep_ancestral", "Ancestral res multistep."),
    ("res_multistep_ancestral_cfg_pp", "Ancestral res multistep CFG++."),
    ("gradient_estimation", "Gradient-estimation sampler."),
    ("gradient_estimation_cfg_pp", "Gradient-estimation CFG++."),
    ("er_sde", "ER-SDE sampler."),
    ("seeds_2", "SEEDS-2."),
    ("seeds_3", "SEEDS-3."),
    ("sa_solver", "SA-Solver."),
    ("sa_solver_pece", "SA-Solver PECE."),
    ("ddim", "DDIM. Deterministic; not a lab default."),
    ("uni_pc", "UniPC. Lab Wan 5B silent graphs use this with CFG 5."),
    ("uni_pc_bh2", "UniPC BH2 variant."),
]

_SCHEDULER_CHOICES: list[tuple[str, str]] = [
    ("simple", "Even sigma spacing. Lab default for Klein, Wan, LTX, and ACE."),
    ("normal", "Linear timestep schedule. TRELLIS structure/texture stages use this."),
    ("karras", "Karras sigmas. Often sharper on SD-family; not the lab default."),
    ("exponential", "Exponential sigma decay."),
    ("sgm_uniform", "SGM uniform. SD3-family default; Wan uses ModelSamplingSD3 shift instead."),
    ("ddim_uniform", "Uniform DDIM schedule."),
    ("beta", "Beta-distribution timesteps."),
    ("linear_quadratic", "Linear then quadratic (Mochi-style)."),
    ("kl_optimal", "KL-optimal sigma curve."),
]

_SEED_CONTROL: list[tuple[str, str]] = [
    ("fixed", "Keep this seed on the next Queue. Lab default for reproducible stills and 5 s prints."),
    ("increment", "Add 1 after Queue. Use for a sequence of variations."),
    ("decrement", "Subtract 1 after Queue."),
    ("randomize", "Draw a new seed after Queue. Exploration only."),
]

_CLIP_TYPES: list[tuple[str, str]] = [
    ("flux2", "Klein 4B / Qwen3-4B text encoder. Lab stills."),
    ("wan", "Wan 2.2 UMT5-XXL. Lab silent motion."),
    ("ltxv", "LTX-2.5 Gemma4-with-proj. Lab AV."),
    ("ace", "ACE-Step text encoder. Music graphs use CheckpointLoaderSimple instead."),
    ("stable_diffusion", "SD1.x CLIP. Not a lab default."),
    ("stable_cascade", "Stable Cascade CLIP."),
    ("sd3", "SD3 CLIP stack."),
    ("stable_audio", "Stable Audio T5."),
    ("mochi", "Mochi T5."),
    ("pixart", "PixArt."),
    ("cosmos", "Cosmos T5."),
    ("lumina2", "Lumina-2 Gemma."),
    ("hidream", "HiDream."),
    ("chroma", "Chroma."),
    ("omnigen2", "OmniGen2."),
    ("qwen_image", "Qwen-Image."),
    ("hunyuan_image", "Hunyuan image."),
    ("ovis", "Ovis."),
    ("longcat_image", "LongCat image. Optional stub only."),
    ("cogvideox", "CogVideoX T5."),
    ("lens", "Lens."),
    ("pixeldit", "PixelDit."),
    ("ideogram4", "Ideogram."),
    ("boogu", "Boogu."),
    ("krea2", "Krea."),
    ("joyimage", "JoyImage Qwen3-VL."),
    ("mage", "Mage."),
    ("minimax", "MiniMax. Banned in this studio (US Excluded Territory). Do not pick."),
]

_WEIGHT_DTYPE: list[tuple[str, str]] = [
    ("default", "Load weights as stored. Lab UNETLoader always uses this."),
    ("fp8_e4m3fn", "Cast to FP8 e4m3fn. Can save memory; may shift Klein/LTX quality."),
    ("fp8_e4m3fn_fast", "FP8 e4m3fn with fast optimizations."),
    ("fp8_e5m2", "Cast to FP8 e5m2."),
]

_DEVICE: list[tuple[str, str]] = [
    ("default", "Load on the Comfy compute device (GPU). Lab default."),
    ("cpu", "Force CPU. Much slower; only for debugging a CLIP load."),
]

ACE_LANGUAGE_CHOICES: list[dict[str, str]] = [
    {"id": code, "description": desc}
    for code, desc in [
        ("en", "English lyrics. Lab vocal graphs."),
        ("unknown", "No lyric language. Lab instrumental / Drive-through graphs."),
        ("ja", "Japanese."),
        ("zh", "Chinese."),
        ("yue", "Cantonese."),
        ("es", "Spanish."),
        ("de", "German."),
        ("fr", "French."),
        ("pt", "Portuguese."),
        ("ru", "Russian."),
        ("it", "Italian."),
        ("ko", "Korean."),
        ("ar", "Arabic."),
        ("hi", "Hindi."),
        ("id", "Indonesian."),
        ("vi", "Vietnamese."),
        ("th", "Thai."),
        ("tr", "Turkish."),
        ("pl", "Polish."),
        ("nl", "Dutch."),
        ("sv", "Swedish."),
        ("uk", "Ukrainian."),
        ("he", "Hebrew."),
        ("fa", "Persian."),
        ("cs", "Czech."),
        ("el", "Greek."),
        ("hu", "Hungarian."),
        ("ro", "Romanian."),
        ("fi", "Finnish."),
        ("da", "Danish."),
        ("no", "Norwegian."),
        ("ms", "Malay."),
        ("ta", "Tamil."),
        ("te", "Telugu."),
        ("bn", "Bengali."),
        ("ur", "Urdu."),
        ("pa", "Punjabi."),
        ("tl", "Tagalog."),
        ("sw", "Swahili."),
        ("az", "Azerbaijani."),
        ("bg", "Bulgarian."),
        ("ca", "Catalan."),
        ("hr", "Croatian."),
        ("ht", "Haitian Creole."),
        ("is", "Icelandic."),
        ("la", "Latin."),
        ("lt", "Lithuanian."),
        ("ne", "Nepali."),
        ("sa", "Sanskrit."),
        ("sk", "Slovak."),
        ("sr", "Serbian."),
    ]
]

_ROOTS = ["C", "C#", "Db", "D", "D#", "Eb", "E", "F", "F#", "Gb", "G", "G#", "Ab", "A", "A#", "Bb", "B"]
ACE_KEYSCALE_CHOICES: list[dict[str, str]] = [
    {
        "id": f"{root} {qual}",
        "description": (
            "Rap Apps stay C minor. Catalog takes set a key per song. Drive-through walks fifths so a live set still mixes."
            if root == "C" and qual == "minor"
            else f"{qual.capitalize()} key of {root}."
        ),
    }
    for qual in ("major", "minor")
    for root in _ROOTS
]

_UPSCALE: list[tuple[str, str]] = [
    ("lanczos", "Lab clay-plate scaler. Sharp, good for stills."),
    ("nearest-exact", "Nearest neighbor. Blocky; pixel-art only."),
    ("bilinear", "Smooth bilinear. Softer than lanczos."),
    ("area", "Area filter. Downscales cleanly."),
    ("bicubic", "Bicubic. Softer than lanczos."),
]

_CROP: list[tuple[str, str]] = [
    ("center", "Center crop after resize. Lab plates."),
    ("disabled", "No crop. May letterbox or stretch depending on the node."),
]


def _s(name: str, typ: str, direction: str, desc: str) -> dict[str, str]:
    """Build a socket spec.

    Args:
        name: Socket label as shown in ComfyUI.
        typ: Comfy type string (``IMAGE``, ``LATENT``, ...).
        direction: ``in`` or ``out``.
        desc: Operator-facing description.

    Returns:
        Encyclopedia socket mapping.
    """
    return {"name": name, "type": typ, "dir": direction, "description": desc}


def _w(
    name: str,
    *,
    index: int | None = None,
    key: str | None = None,
    typ: str = "STRING",
    rng: str = "",
    desc: str = "",
    gen: str = "",
    choices: list[tuple[str, str]] | None = None,
    choices_from: str | None = None,
) -> dict[str, Any]:
    """Build a widget spec.

    Args:
        name: Widget label as shown in ComfyUI.
        index: List-storage index when widgets live in ``inputs`` lists.
        key: Dict-storage key when widgets live in ``inputs`` mappings.
        typ: Comfy widget type (``STRING``, ``INT``, ...).
        rng: Human-readable range, when applicable.
        desc: Operator-facing description.
        gen: How the value is produced (seed, file, ...).
        choices: Optional ``(id, description)`` pairs.
        choices_from: Optional named choice catalog.

    Returns:
        Encyclopedia widget mapping.
    """
    item: dict[str, Any] = {
        "name": name,
        "type": typ,
        "description": desc,
        "generation": gen,
    }
    if index is not None:
        item["storage"] = "list"
        item["index"] = index
    elif key is not None:
        item["storage"] = "dict"
        item["key"] = key
    if rng:
        item["range"] = rng
    if choices:
        item["choices"] = [{"id": cid, "description": cdesc} for cid, cdesc in choices]
    if choices_from:
        item["choices_from"] = choices_from
    return item


def _n(
    display: str,
    summary: str,
    *,
    lab: str = "",
    sockets: list[dict[str, str]] | None = None,
    widgets: list[dict[str, Any]] | None = None,
    origin: str = "comfy-core",
    variants: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a node spec.

    Args:
        display: Comfy display name.
        summary: One-line encyclopedia summary.
        lab: Lab-specific notes (empty when none).
        sockets: Socket specs from :func:`_s`.
        widgets: Widget specs from :func:`_w`.
        origin: Pack or core origin id.
        variants: Optional alternate class_type rows.

    Returns:
        Encyclopedia node mapping.
    """
    spec: dict[str, Any] = {
        "display_name": display,
        "origin": origin,
        "summary": summary,
        "lab_notes": lab,
        "sockets": sockets or [],
        "widgets": widgets or [],
    }
    if variants:
        spec["variants"] = variants
    return spec


def ksampler_widgets() -> list[dict[str, Any]]:
    """KSampler widget row shared by every sampler node spec.

    Returns:
        Seven widgets (seed through denoise).
    """
    return [
        _w(
            "seed",
            index=0,
            typ="INT",
            rng="0 ... 2^64-1; lab 42",
            desc="Random seed for the noise tensor.",
            gen="Same seed + same graph ~ same picture or clip. Lab locks 42 on smokes so drafts are comparable.",
        ),
        _w(
            "control_after_generate",
            index=1,
            typ="COMBO",
            rng="fixed (lab)",
            desc="What happens to seed after Queue.",
            gen="fixed keeps iteration honest while you change the prompt.",
            choices=_SEED_CONTROL,
        ),
        _w(
            "steps",
            index=2,
            typ="INT",
            rng="1-10000; Klein distilled 4; LTX 20; Wan 20; ACE 8; TRELLIS 12",
            desc="Denoising iterations.",
            gen="More steps refine detail with diminishing returns. Distilled Klein is authored at 4 - raising steps is slower, not a quality knob. Do not raise LTX/Wan toward a 90 s denoise.",
        ),
        _w(
            "cfg",
            index=3,
            typ="FLOAT",
            rng="0-100; Klein/LTX/ACE 1.0; Wan 5; TRELLIS 7.5",
            desc="Classifier-free guidance scale.",
            gen="Distilled Klein is CFG 1.0 - raising CFG is the wrong quality lever (use the Positive prompt, resolution, or still-hero). Wan silent 5B uses CFG 5. TRELLIS structure uses 7.5. At CFG 1.0 Comfy skips the negative pass.",
        ),
        _w(
            "sampler_name",
            index=4,
            typ="COMBO",
            rng="euler (most lab); uni_pc (Wan)",
            desc="ODE / SDE algorithm that removes noise.",
            gen="euler is the lab still/AV/ACE default. uni_pc is the Wan 5B silent default. Ancestral/SDE samplers add extra randomness and weaken seed lock.",
            choices=_SAMPLER_CHOICES,
        ),
        _w(
            "scheduler",
            index=5,
            typ="COMBO",
            rng="simple (most lab); normal (TRELLIS)",
            desc="How sigmas are spaced across steps.",
            gen="simple is even spacing and matches distilled Klein / LTX / ACE. normal is the TRELLIS pair. Do not copy karras from an SD1.5 recipe onto Klein.",
            choices=_SCHEDULER_CHOICES,
        ),
        _w(
            "denoise",
            index=6,
            typ="FLOAT",
            rng="0-1; lab 1.0",
            desc="Fraction of the latent to replace with denoised signal.",
            gen="1.0 is full generation (T2I / T2V / ACE). Values below 1 keep structure from an encoded start image (Klein edit / clay). Lab I2V uses dedicated latent nodes, not denoise<1 on empty noise.",
        ),
    ]


def vhs_full() -> list[dict[str, Any]]:
    """Full VHS_VideoCombine widget row (lab MP4 printers).

    Returns:
        Widget specs keyed for dict storage.
    """
    return [
        _w("frame_rate", key="frame_rate", typ="FLOAT", rng="lab 24 (GIF 12/16)", desc="Output frames per second.", gen="24 fps is the lab motion/AV printer. GIF loops use 12. Changing fps without changing frame count changes duration."),
        _w("loop_count", key="loop_count", typ="INT", rng="0 = infinite in players that honor it", desc="How many times the file loops.", gen="0 is the lab default (play once / player default)."),
        _w("filename_prefix", key="filename_prefix", typ="STRING", desc="Save prefix under the output folder.", gen="Lab prefixes start with ez_. The host file is ${COMFY_OUTPUT_DIR}/<prefix>_*.mp4 (or .gif)."),
        _w("format", key="format", typ="COMBO", desc="Container / codec.", gen="video/h264-mp4 is every lab clip except motion/loops/gif-loop (image/gif).", choices=[("video/h264-mp4", "H.264 MP4. Lab default; save_output must stay true."), ("image/gif", "Animated GIF. motion/loops/gif-loop only.")]),
        _w("pix_fmt", key="pix_fmt", typ="COMBO", rng="yuv420p", desc="Pixel format for H.264.", gen="yuv420p plays everywhere. Other formats can break QuickTime/YouTube."),
        _w("crf", key="crf", typ="INT", rng="lab 18", desc="H.264 constant-rate-factor. Lower is bigger/cleaner.", gen="18 is the lab visually-lossless-ish setting. Raising CRF shrinks files and adds blockiness."),
        _w("save_metadata", key="save_metadata", typ="BOOLEAN", desc="Embed workflow JSON in the file.", gen="true keeps provenance on the MP4."),
        _w("trim_to_audio", key="trim_to_audio", typ="BOOLEAN", desc="Cut picture to audio length.", gen="Lab false except when you mean to lock to a bed. ltx/a2v muxes the original wav instead."),
        _w("pingpong", key="pingpong", typ="BOOLEAN", desc="Play frames forward then reverse.", gen="true on motion/loops/gif-loop, bumper-loop, sticker-loop. false on 5 s narrative prints."),
        _w("save_output", key="save_output", typ="BOOLEAN", desc="Write the file to disk.", gen="Lab video graphs require true. After Queue, open the node for the inline preview."),
    ]


def vhs_short() -> list[dict[str, Any]]:
    """Short VHS variant used on unused bumper groups.

    Returns:
        Widget specs keyed for dict storage.
    """
    return [
        _w("frame_rate", key="frame_rate", typ="FLOAT", desc="Output fps.", gen="Unused bumper previews on podcast graphs may sit at 16."),
        _w("loop_count", key="loop_count", typ="INT", desc="Loop count.", gen="0 default."),
        _w("filename_prefix", key="filename_prefix", typ="STRING", desc="Save prefix.", gen="Preview-only groups can stay unwired."),
        _w("format", key="format", typ="COMBO", desc="Container.", gen="video/h264-mp4 on unused bumper groups.", choices=[("video/h264-mp4", "H.264 MP4."), ("image/gif", "GIF.")]),
        _w("pingpong", key="pingpong", typ="BOOLEAN", desc="Ping-pong.", gen="true on unused bumper groups so a later enable still loops."),
        _w("save_output", key="save_output", typ="BOOLEAN", desc="Write the file.", gen="Keep true if you enable the group."),
    ]
