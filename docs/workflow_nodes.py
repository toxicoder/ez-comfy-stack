"""Hand-authored encyclopedia of every Comfy node type used in workflows/_lab.

Widget order matches lab JSON ``widgets_values`` (list index or VHS dict key).
Combo lists are ComfyUI v0.34.6 INPUT_TYPES, lab ez_* INPUT_TYPES, or the ACE
encoder contract in tests/python/_ace_widgets_contract.py.

Do not invent sampler/CLIP/VHS values. Lab-specific generation effects live
in ``lab_notes`` and each widget's ``generation`` field.
"""

from __future__ import annotations

from typing import Any

# ComfyUI v0.34.6 comfy.samplers.SAMPLER_NAMES
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
            "Lab ships C minor on ACE graphs. Changing key reshapes harmony; keep vocal graphs in one key per album unless you mean a new arrangement."
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
        typ: Comfy type string (``IMAGE``, ``LATENT``, …).
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
        typ: Comfy widget type (``STRING``, ``INT``, …).
        rng: Human-readable range, when applicable.
        desc: Operator-facing description.
        gen: How the value is produced (seed, file, …).
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


def encyclopedia() -> dict[str, Any]:
    """Return the node encyclopedia keyed by Comfy type.

    Returns:
        Mapping of node type → spec.
    """
    ksampler_widgets = [
        _w(
            "seed",
            index=0,
            typ="INT",
            rng="0 … 2^64-1; lab 42",
            desc="Random seed for the noise tensor.",
            gen="Same seed + same graph ≈ same picture or clip. Lab locks 42 on smokes so drafts are comparable.",
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
            rng="1–10000; Klein distilled 4; LTX 20; Wan 20; ACE 8; TRELLIS 12",
            desc="Denoising iterations.",
            gen="More steps refine detail with diminishing returns. Distilled Klein is authored at 4 — raising steps is slower, not a quality knob. Do not raise LTX/Wan toward a 90 s denoise.",
        ),
        _w(
            "cfg",
            index=3,
            typ="FLOAT",
            rng="0–100; Klein/LTX/ACE 1.0; Wan 5; TRELLIS 7.5",
            desc="Classifier-free guidance scale.",
            gen="Distilled Klein is CFG 1.0 — raising CFG is the wrong quality lever (use the Positive prompt, resolution, or still-hero). Wan silent 5B uses CFG 5. TRELLIS structure uses 7.5. At CFG 1.0 Comfy skips the negative pass.",
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
            rng="0–1; lab 1.0",
            desc="Fraction of the latent to replace with denoised signal.",
            gen="1.0 is full generation (T2I / T2V / ACE). Values below 1 keep structure from an encoded start image (Klein edit / clay). Lab I2V uses dedicated latent nodes, not denoise<1 on empty noise.",
        ),
    ]

    vhs_full = [
        _w("frame_rate", key="frame_rate", typ="FLOAT", rng="lab 24 (GIF 12/16)", desc="Output frames per second.", gen="24 fps is the lab motion/AV printer. GIF loops use 12. Changing fps without changing frame count changes duration."),
        _w("loop_count", key="loop_count", typ="INT", rng="0 = infinite in players that honor it", desc="How many times the file loops.", gen="0 is the lab default (play once / player default)."),
        _w("filename_prefix", key="filename_prefix", typ="STRING", desc="Save prefix under the output folder.", gen="Lab prefixes start with ez_. The host file is ${COMFY_OUTPUT_DIR}/<prefix>_*.mp4 (or .gif)."),
        _w("format", key="format", typ="COMBO", desc="Container / codec.", gen="video/h264-mp4 is every lab clip except wan/gif-loop (image/gif).", choices=[("video/h264-mp4", "H.264 MP4. Lab default; save_output must stay true."), ("image/gif", "Animated GIF. wan/gif-loop only.")]),
        _w("pix_fmt", key="pix_fmt", typ="COMBO", rng="yuv420p", desc="Pixel format for H.264.", gen="yuv420p plays everywhere. Other formats can break QuickTime/YouTube."),
        _w("crf", key="crf", typ="INT", rng="lab 18", desc="H.264 constant-rate-factor. Lower is bigger/cleaner.", gen="18 is the lab visually-lossless-ish setting. Raising CRF shrinks files and adds blockiness."),
        _w("save_metadata", key="save_metadata", typ="BOOLEAN", desc="Embed workflow JSON in the file.", gen="true keeps provenance on the MP4."),
        _w("trim_to_audio", key="trim_to_audio", typ="BOOLEAN", desc="Cut picture to audio length.", gen="Lab false except when you mean to lock to a bed. ltx/a2v muxes the original wav instead."),
        _w("pingpong", key="pingpong", typ="BOOLEAN", desc="Play frames forward then reverse.", gen="true on wan/gif-loop, bumper-loop, sticker-loop. false on 5 s narrative prints."),
        _w("save_output", key="save_output", typ="BOOLEAN", desc="Write the file to disk.", gen="Lab video graphs require true. After Queue, open the node for the inline preview."),
    ]
    vhs_short = [
        _w("frame_rate", key="frame_rate", typ="FLOAT", desc="Output fps.", gen="Unused bumper previews on podcast graphs may sit at 16."),
        _w("loop_count", key="loop_count", typ="INT", desc="Loop count.", gen="0 default."),
        _w("filename_prefix", key="filename_prefix", typ="STRING", desc="Save prefix.", gen="Preview-only groups can stay unwired."),
        _w("format", key="format", typ="COMBO", desc="Container.", gen="video/h264-mp4 on unused bumper groups.", choices=[("video/h264-mp4", "H.264 MP4."), ("image/gif", "GIF.")]),
        _w("pingpong", key="pingpong", typ="BOOLEAN", desc="Ping-pong.", gen="true on unused bumper groups so a later enable still loops."),
        _w("save_output", key="save_output", typ="BOOLEAN", desc="Write the file.", gen="Keep true if you enable the group."),
    ]

    nodes: dict[str, Any] = {
        "KSampler": _n(
            "KSampler",
            "Denoise a latent for N steps at a CFG, sampler, and scheduler.",
            lab="Distilled Klein is CFG 1.0 / 4 steps / euler / simple. Raising CFG is not a quality knob. Wan 5B uses uni_pc and CFG 5. LTX distilled uses euler / simple / CFG 1.0 / 20 steps. ACE-Step uses 8 steps / CFG 1.0 / euler. TRELLIS uses 12 steps / CFG 7.5 / euler / normal.",
            sockets=[
                _s("model", "MODEL", "in", "UNET / transformer after any ModelSampling* patch."),
                _s("positive", "CONDITIONING", "in", "What to include (CLIP / ACE / LTX prompt)."),
                _s("negative", "CONDITIONING", "in", "What to avoid. Distilled Klein ignores this well — put constraints in the positive."),
                _s("latent_image", "LATENT", "in", "Noise canvas or encoded start image / video / audio latent."),
                _s("LATENT", "LATENT", "out", "Denoised latent for VAE decode."),
            ],
            widgets=ksampler_widgets,
        ),
        "UNETLoader": _n(
            "Load Diffusion Model",
            "Load a standalone transformer/UNET from diffusion_models/.",
            lab="Lab files: flux-2-klein-4b-fp8.safetensors, wan2.2_ti2v_5B_fp16.safetensors, ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors. weight_dtype stays default.",
            sockets=[_s("MODEL", "MODEL", "out", "Denoiser weights.")],
            widgets=[
                _w("unet_name", index=0, desc="Checkpoint filename under MODELS_DIR diffusion_models.", gen="Wrong family = Queue error or a melted picture. Do not swap Klein 9B / FLUX.2-dev / MiniMax."),
                _w("weight_dtype", index=1, typ="COMBO", rng="default", desc="Cast at load.", gen="default keeps the file's dtype (Klein FP8, LTX INT8-convrot, Wan FP16).", choices=_WEIGHT_DTYPE),
            ],
        ),
        "CLIPLoader": _n(
            "Load CLIP",
            "Load a text encoder. The type combo must match the UNET family.",
            lab="Lab types: flux2 (Qwen3-4B), wan (UMT5), ltxv (Gemma4-with-proj). Wrong type is a Queue error, not a bad prompt. MiniMax type is banned.",
            sockets=[_s("CLIP", "CLIP", "out", "Text encoder for CLIPTextEncode / ACE / LTX.")],
            widgets=[
                _w("clip_name", index=0, desc="Filename under text_encoders.", gen="Must match the family (qwen_3_4b, umt5_xxl, gemma4-12b-with-proj)."),
                _w("type", index=1, typ="COMBO", desc="CLIPType enum. Picks tokenizer + template.", gen="flux2 wraps Klein strings in a Qwen chat template — do not paste <|im_start|>. wan is UMT5. ltxv is Gemma4-with-proj.", choices=_CLIP_TYPES),
                _w("device", index=2, typ="COMBO", rng="default", desc="Where to load the encoder.", gen="default uses GPU. cpu is a debug escape hatch.", choices=_DEVICE),
            ],
        ),
        "VAELoader": _n(
            "Load VAE",
            "Load the autoencoder that maps pixels ↔ latents (and LTX audio).",
            lab="Do not mix families: flux2-vae, wan2.2_vae, ltx-2.5-video-vae-bf16, ltx-2.5-audio-vae-bf16.",
            sockets=[_s("VAE", "VAE", "out", "Encoder/decoder.")],
            widgets=[_w("vae_name", index=0, desc="Filename under vae/.", gen="Wrong VAE = color trash or a shape error.")],
        ),
        "CheckpointLoaderSimple": _n(
            "Load Checkpoint",
            "Load a single-file checkpoint that bundles MODEL + CLIP + VAE.",
            lab="ACE-Step 1.5 turbo AIO (ace_step_1.5_turbo_aio.safetensors) on every music graph.",
            sockets=[
                _s("MODEL", "MODEL", "out", "ACE denoiser (then ModelSamplingAuraFlow)."),
                _s("CLIP", "CLIP", "out", "ACE text encoder."),
                _s("VAE", "VAE", "out", "ACE audio VAE."),
            ],
            widgets=[_w("ckpt_name", index=0, desc="Filename under checkpoints/.", gen="Lab music is the turbo AIO. XL is opt-in via download-music --tier xl — swap only if you meant to.")],
        ),
        "CLIPVisionLoader": _n(
            "Load CLIP Vision",
            "Load an image encoder for TRELLIS.2 conditioning.",
            lab="Lab: dino_v3_vit_l.safetensors. Occupancy trellis.",
            sockets=[_s("CLIP_VISION", "CLIP_VISION", "out", "Vision tower.")],
            widgets=[_w("clip_name", index=0, desc="Vision checkpoint filename.", gen="DINOv3 ViT-L is the TRELLIS.2 pair. A text CLIP will not work here.")],
        ),
        "CLIPTextEncode": _n(
            "CLIP Text Encode",
            "Turn a prompt string into CONDITIONING for the sampler.",
            lab="The dim CLIP box after Queue is this string. Prompt Enhance nodes rewrite it when Enhance is on.",
            sockets=[
                _s("clip", "CLIP", "in", "Matching family encoder."),
                _s("text", "STRING", "in", "Often wired from Prompt Enhance so the widget is a preview."),
                _s("CONDITIONING", "CONDITIONING", "out", "Positive or negative cond."),
            ],
            widgets=[_w("text", index=0, typ="STRING", desc="Prompt encoded by CLIP.", gen="Klein: sentences, subject → place → light → camera. Wan I2V: motion + one camera only. LTX: present-tense paragraph with audio interleaved. Distilled Klein quality lives here, not in CFG.")],
        ),
        "EmptyFlux2LatentImage": _n(
            "Empty Flux.2 Latent",
            "Allocate a Klein / Flux.2 still latent (width × height × batch).",
            lab="Draft 768×432 batch 2. Hero / LTX feeders 1280×704. Portrait 1024×1280 or 768×1280. 1280×720 is OK for thumbnails, not for LTX feeders.",
            sockets=[_s("LATENT", "LATENT", "out", "Noise canvas for KSampler.")],
            widgets=[
                _w("width", index=0, typ="INT", rng="lab 768 / 1280 / 1024 / 432…", desc="Latent pixel width.", gen="Sets the still's width. Match the intended platform (16:9, 9:16, 1:1, 4:5)."),
                _w("height", index=1, typ="INT", desc="Latent pixel height.", gen="1280×704 is the LTX VAE grid (÷32). 1280×720 is not."),
                _w("batch_size", index=2, typ="INT", rng="draft 2; others 1", desc="How many stills in one Queue.", gen="Draft uses 2 for a cheap fork. Heroes stay 1."),
            ],
        ),
        "EmptyLTXVLatentVideo": _n(
            "Empty LTX Latent Video",
            "Allocate a T2V LTX video latent (no start image).",
            lab="Width/height must be ÷32. Length must be 1+8n (121 for ~5 s). ez_ltx_spatial snaps illegal values.",
            sockets=[_s("LATENT", "LATENT", "out", "Video latent (then concat with audio latent).")],
            widgets=[
                _w("width", index=0, typ="INT", rng="1280 (landscape) / 768 (shorts)", desc="Frame width.", gen="÷32. 1280×720 will snap to 704."),
                _w("height", index=1, typ="INT", rng="704 / 1280", desc="Frame height.", gen="704 is the lab landscape printer."),
                _w("length", index=2, typ="INT", rng="121 = 1+8n", desc="Frame count.", gen="121 @ 24 fps ≈ 5.04 s. 120 is illegal on LTX (snaps to 121). Do not type 241."),
            ],
        ),
        "Wan22ImageToVideoLatent": _n(
            "Wan 2.2 Image to Video Latent",
            "Build a Wan 5B I2V latent from a start image (or empty for T2V).",
            lab="Smoke 832×480 × 121 frames. Shot graphs use 120 frames for concat. GIF 49 frames. VACE join 17 frames (1+8n).",
            sockets=[
                _s("vae", "VAE", "in", "wan2.2_vae."),
                _s("start_image", "IMAGE", "in", "Optional. T2V graphs leave LoadImage bypassed."),
                _s("LATENT", "LATENT", "out", "Video latent for KSampler."),
            ],
            widgets=[
                _w("width", index=0, typ="INT", rng="832 landscape / 480 portrait", desc="Frame width.", gen="832×480 is the Wan 5B smoke size. Larger melts GB10."),
                _w("height", index=1, typ="INT", desc="Frame height.", gen="Swap for 9:16 shorts (480×832)."),
                _w("length", index=2, typ="INT", rng="121 smoke / 120 shot / 49 GIF / 17 VACE", desc="Frame count.", gen="Duration = length / fps. 121 @ 24 fps is the 5 s smoke. Shot graphs use 120 so concat-shots stays 5.00 s."),
                _w("batch_size", index=3, typ="INT", rng="1", desc="Clips per Queue.", gen="Stay 1 on GB10."),
            ],
        ),
        "EmptyAceStep1.5LatentAudio": _n(
            "Empty ACE-Step 1.5 Latent Audio",
            "Allocate an ACE-Step audio latent for N seconds.",
            lab="Draft 32 s, full 96 s, album takes 180 s. seconds is also a socket from PrimitiveNode so App Duration stays in one place.",
            sockets=[
                _s("seconds", "FLOAT", "in", "Wired from Song Duration primitive on music graphs."),
                _s("LATENT", "LATENT", "out", "Audio latent for KSampler."),
            ],
            widgets=[
                _w("seconds", index=0, typ="FLOAT", rng="32 / 96 / 180 lab", desc="Duration in seconds.", gen="Longer latents cost RAM/time linearly. Stay at the seeded length unless you have headroom."),
                _w("batch_size", index=1, typ="INT", rng="1", desc="Takes per Queue.", gen="Stay 1."),
            ],
        ),
        "EmptyTrellis2LatentStructure": _n(
            "Empty TRELLIS.2 Latent Structure",
            "Allocate a TRELLIS.2 structure latent (batch only).",
            lab="Occupancy trellis. Unload Klein first.",
            sockets=[_s("LATENT", "LATENT", "out", "Structure noise.")],
            widgets=[_w("batch_size", index=0, typ="INT", rng="1", desc="Meshes per Queue.", gen="Stay 1 on GB10.")],
        ),
        "ModelSamplingSD3": _n(
            "ModelSamplingSD3",
            "Patch a model with SD3-style flow-matching shift.",
            lab="Wan 5B graphs use shift 8.",
            sockets=[
                _s("model", "MODEL", "in", "Wan UNET."),
                _s("MODEL", "MODEL", "out", "Shifted model for KSampler."),
            ],
            widgets=[_w("shift", index=0, typ="FLOAT", rng="8 (lab Wan)", desc="Flow-matching shift.", gen="8 is the Wan 2.2 TI2V lab value. Changing it moves the noise schedule; do not copy SD3 defaults blindly.")],
        ),
        "ModelSamplingAuraFlow": _n(
            "ModelSamplingAuraFlow",
            "Patch ACE-Step with AuraFlow sampling shift.",
            lab="Every ACE graph uses shift 3.",
            sockets=[
                _s("model", "MODEL", "in", "ACE checkpoint MODEL."),
                _s("MODEL", "MODEL", "out", "Shifted ACE denoiser."),
            ],
            widgets=[_w("shift", index=0, typ="FLOAT", rng="3 (lab ACE)", desc="AuraFlow shift.", gen="3 is the ACE-Step 1.5 lab value. Higher shift changes timing/attack of the beat.")],
        ),
        "ConditioningZeroOut": _n(
            "Conditioning Zero Out",
            "Replace a conditioning with zeros (unconditional / empty negative).",
            lab="ACE graphs zero the negative so CFG 1.0 stays a true uncond skip.",
            sockets=[
                _s("conditioning", "CONDITIONING", "in", "Usually an unused negative encode."),
                _s("CONDITIONING", "CONDITIONING", "out", "Zeroed cond for KSampler.negative."),
            ],
        ),
        "ReferenceLatent": _n(
            "Reference Latent",
            "Pack an encoded image latent into positive conditioning (Klein edit).",
            lab="character-tweak, clay, dream-house-clay, before-after, time-of-day edits. denoise on those KSamplers stays 1.0; the reference owns structure.",
            sockets=[
                _s("conditioning", "CONDITIONING", "in", "Positive CLIP cond."),
                _s("latent", "LATENT", "in", "VAE-encoded start still."),
                _s("CONDITIONING", "CONDITIONING", "out", "Positive with reference latent attached."),
            ],
        ),
        "VAEDecode": _n(
            "VAE Decode",
            "Decode image/video latents to pixels.",
            sockets=[
                _s("samples", "LATENT", "in", "KSampler output (video or still)."),
                _s("vae", "VAE", "in", "Matching family VAE."),
                _s("IMAGE", "IMAGE", "out", "Frames or still."),
            ],
        ),
        "VAEEncode": _n(
            "VAE Encode",
            "Encode pixels to a latent (Klein edit / clay).",
            sockets=[
                _s("pixels", "IMAGE", "in", "Start still."),
                _s("vae", "VAE", "in", "flux2-vae."),
                _s("LATENT", "LATENT", "out", "Reference latent."),
            ],
        ),
        "VAEDecodeAudio": _n(
            "VAE Decode Audio",
            "Decode an ACE audio latent to AUDIO.",
            sockets=[
                _s("samples", "LATENT", "in", "ACE KSampler output."),
                _s("vae", "VAE", "in", "ACE VAE from the AIO checkpoint."),
                _s("AUDIO", "AUDIO", "out", "Waveform for SaveAudio."),
            ],
        ),
        "LoadImage": _n(
            "Load Image",
            "Load a still from Comfy input/ (or upload).",
            lab="I2V / edit graphs default example.png until you pick ez_still_*.png. App Mode shows Start image only when this node is wired.",
            sockets=[
                _s("IMAGE", "IMAGE", "out", "RGB still."),
                _s("MASK", "MASK", "out", "Alpha if present."),
            ],
            widgets=[
                _w("image", index=0, desc="Filename in input/.", gen="Point at the Klein still you just saved (ez_still_draft_*.png, ez_character_*.png, first.png)."),
                _w("upload", index=1, typ="COMBO", rng="image", desc="Upload widget type.", gen="Leave image. This is the choose-file control, not a generation knob."),
            ],
        ),
        "LoadAudio": _n(
            "Load Audio",
            "Load a wav/mp3 from input/.",
            lab="ltx/a2v-5s defaults ez_a2v_bed.wav. Drop the file in ${COMFY_OUTPUT_DIR}/input.",
            sockets=[_s("AUDIO", "AUDIO", "out", "Waveform for LTXVAudioVAEEncode.")],
            widgets=[_w("audio", index=0, desc="Filename in input/.", gen="The original wav is muxed into the MP4 (no audio VAE decode on a2v).")],
        ),
        "SaveImage": _n(
            "Save Image",
            "Write PNG stills under the output folder.",
            sockets=[_s("images", "IMAGE", "in", "Decoded still or last-frame.")],
            widgets=[_w("filename_prefix", index=0, desc="Save prefix.", gen="Lab prefixes start with ez_. Last-frame savers on shot graphs feed concat-shots.")],
        ),
        "SaveAudio": _n(
            "Save Audio",
            "Write a FLAC/wav master.",
            lab="Music graphs pair this with SaveAudioMP3 and EZAudioMetadata. Stem mix uses ez_stem_mix.",
            sockets=[_s("audio", "AUDIO", "in", "Decoded ACE or mix.")],
            widgets=[_w("filename_prefix", index=0, desc="Save stem.", gen="Album tracks use NN - Song Title. Tags come from EZAudioMetadata.")],
        ),
        "SaveAudioMP3": _n(
            "Save Audio (MP3)",
            "Write an MP3 copy of the same take.",
            sockets=[_s("audio", "AUDIO", "in", "Same AUDIO as SaveAudio.")],
            widgets=[
                _w("filename_prefix", index=0, desc="Save stem (match FLAC).", gen="Same NN - Song Title as the FLAC."),
                _w("quality", index=1, typ="COMBO", rng="320k", desc="Bitrate preset.", gen="320k is the lab master. Lower bitrates are smaller and harsher on hats.", choices=[("320k", "Lab default."), ("192k", "Smaller, more artifacts."), ("128k", "Preview only.")]),
            ],
        ),
        "ImageScale": _n(
            "Upscale Image",
            "Resize a still to a target width/height.",
            lab="dcc/klein/from-clay-plates scales one clay into 704 / 1:1 / 4:5 / 9:16.",
            sockets=[
                _s("image", "IMAGE", "in", "Source still."),
                _s("IMAGE", "IMAGE", "out", "Scaled still."),
            ],
            widgets=[
                _w("upscale_method", index=0, typ="COMBO", rng="lanczos", desc="Resample filter.", gen="lanczos is the lab plate scaler.", choices=_UPSCALE),
                _w("width", index=1, typ="INT", desc="Target width.", gen="Must match the plate (1280, 1024, 768)."),
                _w("height", index=2, typ="INT", desc="Target height.", gen="704 for LTX feeders; 1280 for 4:5 / 9:16."),
                _w("crop", index=3, typ="COMBO", rng="center", desc="Crop mode.", gen="center keeps the subject in frame when aspect changes.", choices=_CROP),
            ],
        ),
        "ImageFromBatch": _n(
            "Image From Batch",
            "Pick one frame out of a decoded video batch.",
            lab="Last-frame savers: index 120 on 121-frame LTX (0-based last), 119 on 120-frame Wan shots.",
            sockets=[
                _s("image", "IMAGE", "in", "Decoded frame batch."),
                _s("IMAGE", "IMAGE", "out", "Single frame."),
            ],
            widgets=[
                _w("batch_index", index=0, typ="INT", rng="120 (LTX 121) / 119 (Wan 120)", desc="0-based frame index.", gen="Must be length-1 for the last frame. Off-by-one here breaks shot continuity."),
                _w("length", index=1, typ="INT", rng="1", desc="How many frames to take.", gen="Stay 1 (one still)."),
            ],
        ),
        "PrimitiveNode": _n(
            "Primitive",
            "A typed constant (string or float) with seed-style control.",
            lab="Music Duration (FLOAT) and Prompt Forge Context (STRING). widgets[1] is always control_after_generate.",
            sockets=[_s("value", "FLOAT|STRING", "out", "Wired into duration / context / lyrics.")],
            widgets=[
                _w("value", index=0, typ="FLOAT|STRING", desc="The constant.", gen="FLOAT seconds drive ACE latent length. STRING context is bible/research for Enhance."),
                _w("control_after_generate", index=1, typ="COMBO", rng="fixed", desc="Whether the primitive mutates after Queue.", gen="fixed keeps duration/context pinned.", choices=_SEED_CONTROL),
            ],
        ),
        "Note": _n(
            "Note",
            "On-canvas operator note (not executed).",
            lab="Every lab graph has one. Purpose, models, sampler, occupancy, run steps.",
            widgets=[_w("text", index=0, desc="Markdown-ish operator note.", gen="Does not affect pixels. Read it before Queue.")],
        ),
        "MarkdownNote": _n(
            "Markdown Note",
            "Rendered markdown note (90s shot maps).",
            widgets=[_w("text", index=0, desc="Markdown body.", gen="Does not affect pixels. 90s films put the beat table here.")],
        ),
        "VHS_VideoCombine": _n(
            "VHS Video Combine",
            "Encode frames (and optional audio) to MP4 or GIF.",
            lab="Lab clips set save_output true. After Queue open the node for preview. GIF graphs use image/gif + pingpong.",
            sockets=[
                _s("images", "IMAGE", "in", "Decoded frames."),
                _s("audio", "AUDIO", "in", "LTX decoded audio or unused."),
                _s("meta_batch", "VHS_BatchManager", "in", "Optional batch manager (unwired)."),
                _s("vae", "VAE", "in", "Optional (unwired)."),
                _s("Filenames", "VHS_FILENAMES", "out", "Path list for EZFilmConcat."),
            ],
            widgets=vhs_full,
            variants=[{"widgets": vhs_short}],
        ),
        "TextEncodeAceStepAudio1.5": _n(
            "ACE-Step 1.5 Text Encode",
            "Pack tags, lyrics, BPM, key, and duration into ACE conditioning.",
            lab="15 widgets including control_after_generate after seed (see _ace_widgets_contract.py). Vocal graphs language=en; instrumental unknown. generate_audio_codes stays true.",
            origin="comfy-extras",
            sockets=[
                _s("clip", "CLIP", "in", "ACE CLIP from the AIO checkpoint."),
                _s("tags", "STRING", "in", "Often wired from EZAceStepPromptEnhance."),
                _s("lyrics", "STRING", "in", "Wired lyrics / [inst]."),
                _s("duration", "FLOAT", "in", "Same seconds as the empty latent."),
                _s("CONDITIONING", "CONDITIONING", "out", "Positive for KSampler."),
            ],
            widgets=[
                _w("tags", index=0, desc="Genre-first tags, BPM last.", gen="ACE reads tags as the arrangement. Keep dry-booth vocal tags on Nill Bye; Drive-through is warped bass, no rap vocal."),
                _w("lyrics", index=1, desc="Sectioned lyrics or [inst] cues.", gen="Non-empty lines under a section are sung. Instrumental graphs must keep cues inside [brackets]."),
                _w("seed", index=2, typ="INT", desc="ACE encoder seed (audio-codes LLM).", gen="Independent from KSampler seed. Lab locks it with the take."),
                _w("control_after_generate", index=3, typ="COMBO", rng="fixed", desc="Seed control.", gen="fixed on every lab take.", choices=_SEED_CONTROL),
                _w("bpm", index=4, typ="INT", rng="10–300", desc="Tempo written into the codes.", gen="Must match the tags' BPM. Mismatch makes the vocal drift the grid."),
                _w("duration", index=5, typ="FLOAT", desc="Seconds (duplicated on the latent).", gen="Keep in lockstep with EmptyAceStep1.5LatentAudio / Primitive."),
                _w("timesignature", index=6, typ="COMBO", rng="4", desc="Beats per bar.", gen="4 is lab 4/4. 3 is waltz; 6 is 6/8.", choices=[("2", "2/4."), ("3", "3/4."), ("4", "Lab 4/4."), ("6", "6/8.")]),
                _w("language", index=7, typ="COMBO", rng="en / unknown", desc="Lyric language.", gen="en for sung English. unknown for instrumental (do not leave en on a no-vocal take).", choices_from="ace_language"),
                _w("keyscale", index=8, typ="COMBO", rng="C minor", desc="Musical key.", gen="Lab C minor. Changing key is a new arrangement, not a mix tweak.", choices_from="ace_keyscale"),
                _w("generate_audio_codes", index=9, typ="BOOLEAN", rng="true", desc="Run the ACE LLM that drafts audio codes.", gen="true = higher quality, slower. Off only if you pass a reference timbre (lab graphs do not)."),
                _w("cfg_scale", index=10, typ="FLOAT", rng="2.0", desc="Guidance inside audio-code generation.", gen="2.0 is the ACE default. Higher follows tags/lyrics more tightly and can sound rigid."),
                _w("temperature", index=11, typ="FLOAT", rng="0.85", desc="Sampling temperature for audio codes.", gen="Lower = more deterministic. Higher = wilder fills."),
                _w("top_p", index=12, typ="FLOAT", rng="0.9", desc="Nucleus sampling.", gen="0.9 is the lab default."),
                _w("top_k", index=13, typ="INT", rng="0 = off", desc="Top-k token cap.", gen="0 disables top-k (lab)."),
                _w("min_p", index=14, typ="FLOAT", rng="0.0", desc="Minimum probability floor.", gen="0.0 disables min-p (lab)."),
            ],
        ),
        "LTXVImgToVideo": _n(
            "LTX Image to Video",
            "Condition LTX on a start image and allocate the video latent.",
            lab="÷32 spatial, length 1+8n. 1280×704×121 is the lab printer. Shorts 768×1280. Some shot graphs still store 120 and rely on ez_ltx_spatial to snap.",
            origin="comfy-extras",
            sockets=[
                _s("positive", "CONDITIONING", "in", "LTX prompt cond."),
                _s("negative", "CONDITIONING", "in", "Negative cond."),
                _s("vae", "VAE", "in", "ltx-2.5-video-vae."),
                _s("image", "IMAGE", "in", "Start still (Klein feeder)."),
                _s("positive", "CONDITIONING", "out", "Image-conditioned positive."),
                _s("negative", "CONDITIONING", "out", "Image-conditioned negative."),
                _s("latent", "LATENT", "out", "Video latent."),
            ],
            widgets=[
                _w("width", index=0, typ="INT", rng="1280 / 768", desc="Frame width.", gen="Must be ÷32. 720p width is fine; height 720 is not."),
                _w("height", index=1, typ="INT", rng="704 / 1280", desc="Frame height.", gen="704 not 720. Shorts 1280."),
                _w("length", index=2, typ="INT", rng="121", desc="Frame count.", gen="1+8n. 121 @ 24 fps ≈ 5.04 s. Do not type a 90 s length."),
                _w("batch_size", index=3, typ="INT", rng="1", desc="Clips per Queue.", gen="Stay 1."),
            ],
        ),
        "LTXVConditioning": _n(
            "LTX Conditioning",
            "Stamp frame-rate onto LTX positive/negative cond.",
            origin="comfy-extras",
            sockets=[
                _s("positive", "CONDITIONING", "in", "Prompt cond."),
                _s("negative", "CONDITIONING", "in", "Negative cond."),
                _s("positive", "CONDITIONING", "out", "FPS-stamped positive."),
                _s("negative", "CONDITIONING", "out", "FPS-stamped negative."),
            ],
            widgets=[_w("frame_rate", index=0, typ="FLOAT", rng="24.0", desc="Frames per second written into cond.", gen="Must match VHS frame_rate (24). Mismatch makes motion too fast/slow.")],
        ),
        "LTXVConcatAVLatent": _n(
            "LTX Concat AV Latent",
            "Join video + audio latents into one joint AV latent for the sampler.",
            origin="comfy-extras",
            sockets=[
                _s("video_latent", "LATENT", "in", "Video latent."),
                _s("audio_latent", "LATENT", "in", "Empty or encoded audio latent."),
                _s("latent", "LATENT", "out", "Joint AV latent."),
            ],
        ),
        "LTXVSeparateAVLatent": _n(
            "LTX Separate AV Latent",
            "Split a joint AV latent after sampling.",
            origin="comfy-extras",
            sockets=[
                _s("av_latent", "LATENT", "in", "KSampler output."),
                _s("video_latent", "LATENT", "out", "Picture latent → VAEDecode."),
                _s("audio_latent", "LATENT", "out", "Audio latent → LTXVAudioVAEDecode (not on a2v)."),
            ],
        ),
        "LTXVAudioVAEDecode": _n(
            "LTX Audio VAE Decode",
            "Decode LTX audio latent to AUDIO for the MP4 mux.",
            lab="Skipped on ltx/a2v-5s (original wav is muxed).",
            origin="comfy-extras",
            sockets=[
                _s("samples", "LATENT", "in", "Audio latent."),
                _s("audio_vae", "VAE", "in", "ltx-2.5-audio-vae-bf16."),
                _s("Audio", "AUDIO", "out", "World bed / dialogue stem."),
            ],
        ),
        "LTXVAudioVAEEncode": _n(
            "LTX Audio VAE Encode",
            "Encode a wav into the LTX audio latent (A2V freeze).",
            origin="comfy-extras",
            sockets=[
                _s("audio", "AUDIO", "in", "LoadAudio wav."),
                _s("audio_vae", "VAE", "in", "Audio VAE."),
                _s("Latent", "LATENT", "out", "Frozen audio latent concatenated before sample."),
            ],
        ),
        "LTXVEmptyLatentAudio": _n(
            "Empty LTX Audio Latent",
            "Allocate a silent/world-audio latent matching video length.",
            origin="comfy-extras",
            sockets=[
                _s("audio_vae", "VAE", "in", "Audio VAE (sets latent channels)."),
                _s("Latent", "LATENT", "out", "Empty audio latent."),
            ],
            widgets=[
                _w("frames", index=0, typ="INT", rng="121", desc="Must match video length.", gen="Mismatch with LTXVImgToVideo length breaks concat."),
                _w("frame_rate", index=1, typ="FLOAT", rng="24.0", desc="Audio timeline fps.", gen="Keep 24 with the rest of the printer."),
                _w("batch_size", index=2, typ="INT", rng="1", desc="Clips per Queue.", gen="Stay 1."),
            ],
        ),
        "LTXVAddGuide": _n(
            "LTX Add Guide",
            "Pin a still onto a latent frame (first-last-frame).",
            lab="ltx/flf-5s uses index 0 then -1 on the video latent before audio concat.",
            origin="comfy-extras",
            sockets=[
                _s("positive", "CONDITIONING", "in", "Cond in."),
                _s("negative", "CONDITIONING", "in", "Cond in."),
                _s("vae", "VAE", "in", "Video VAE."),
                _s("latent", "LATENT", "in", "Video latent."),
                _s("image", "IMAGE", "in", "Guide still."),
                _s("positive", "CONDITIONING", "out", "Guided positive."),
                _s("negative", "CONDITIONING", "out", "Guided negative."),
                _s("latent", "LATENT", "out", "Latent with guide frame."),
            ],
            widgets=[
                _w("frame_idx", index=0, typ="INT", rng="0 first / -1 last", desc="Which frame to pin.", gen="0 is the first frame. -1 is the last. Values in between pin mid-shot."),
                _w("strength", index=1, typ="FLOAT", rng="1.0", desc="How hard to pin.", gen="1.0 locks the still. Lower lets motion drift off the guide."),
            ],
        ),
        "LTXVModalityGuidance": _n(
            "LTX Modality Guidance",
            "Couple audio and video during sampling (dialogue graphs).",
            lab="ltx/dialogue-5s uses 3.0 / 0 / 1. Mouths still will not lip-sync; this only tightens A/V coupling.",
            origin="comfy-extras",
            sockets=[
                _s("model", "MODEL", "in", "LTX UNET."),
                _s("MODEL", "MODEL", "out", "Patched model."),
            ],
            widgets=[
                _w("strength", index=0, typ="FLOAT", rng="3.0", desc="A/V coupling strength.", gen="Higher ties picture motion to the audio latent. Too high can freeze faces."),
                _w("start", index=1, typ="FLOAT", rng="0–1, lab 0", desc="Fraction of steps to start coupling.", gen="0 = from the first step."),
                _w("end", index=2, typ="FLOAT", rng="0–1, lab 1", desc="Fraction of steps to stop coupling.", gen="1 = through the last step."),
            ],
        ),
        "LTXVCropGuides": _n(
            "LTX Crop Guides",
            "Crop guide metadata off the latent after FLF pins.",
            origin="comfy-extras",
            sockets=[
                _s("positive", "CONDITIONING", "in", "Guided cond."),
                _s("negative", "CONDITIONING", "in", "Guided cond."),
                _s("latent", "LATENT", "in", "Guided latent."),
                _s("positive", "CONDITIONING", "out", "Clean cond."),
                _s("negative", "CONDITIONING", "out", "Clean cond."),
                _s("latent", "LATENT", "out", "Latent ready to concat with audio."),
            ],
        ),
        "AudioAdjustVolume": _n(
            "Audio Adjust Volume",
            "Gain an AUDIO tensor in dB.",
            lab="Podcast duck −15 dB on the ACE bed under Kokoro speech.",
            sockets=[
                _s("audio", "AUDIO", "in", "Bed or sting."),
                _s("AUDIO", "AUDIO", "out", "Gained audio."),
            ],
            widgets=[_w("volume_db", index=0, typ="FLOAT", rng="lab −15", desc="Gain in decibels.", gen="Negative ducks the bed. −15 dB is the lab podcast duck (same idea as host stem-mix.sh).")],
        ),
        "AudioMerge": _n(
            "Audio Merge",
            "Mix two AUDIO tensors.",
            sockets=[
                _s("audio1", "AUDIO", "in", "Speech or sting."),
                _s("audio2", "AUDIO", "in", "Bed."),
                _s("AUDIO", "AUDIO", "out", "Mix."),
            ],
            widgets=[
                _w(
                    "merge_method",
                    index=0,
                    typ="COMBO",
                    rng="overlay",
                    desc="How to combine overlapping samples.",
                    gen="overlay keeps both (lab podcast mix). add can clip. mean quiets both.",
                    choices=[
                        ("overlay", "Layer both (lab)."),
                        ("add", "Sum. Can clip."),
                        ("mean", "Average. Quieter."),
                    ],
                )
            ],
        ),
        "AudioConcat": _n(
            "Audio Concat",
            "Play two AUDIO tensors in sequence.",
            sockets=[
                _s("audio1", "AUDIO", "in", "First clip (sting)."),
                _s("audio2", "AUDIO", "in", "Second clip (bed)."),
                _s("AUDIO", "AUDIO", "out", "Sting then bed."),
            ],
            widgets=[
                _w(
                    "method",
                    index=0,
                    typ="COMBO",
                    rng="after",
                    desc="Order.",
                    gen="after = audio1 then audio2 (lab sting then bed).",
                    choices=[("after", "audio1 then audio2 (lab)."), ("before", "audio2 then audio1.")],
                )
            ],
        ),
        "Trellis2Conditioning": _n(
            "TRELLIS.2 Conditioning",
            "Encode a still with CLIP Vision into TRELLIS positive/negative.",
            origin="comfy-extras",
            sockets=[
                _s("clip_vision_model", "CLIP_VISION", "in", "DINOv3 ViT-L."),
                _s("image", "IMAGE", "in", "Klein still."),
                _s("positive", "CONDITIONING", "out", "Shape/texture positive."),
                _s("negative", "CONDITIONING", "out", "Negative."),
            ],
        ),
        "Trellis2ShapeStage": _n(
            "TRELLIS.2 Shape Stage",
            "Sample structure from a voxel latent.",
            origin="comfy-extras",
            sockets=[
                _s("positive", "CONDITIONING", "in", "Vision cond."),
                _s("negative", "CONDITIONING", "in", "Negative."),
                _s("voxel", "LATENT", "in", "Structure decode voxels."),
                _s("positive", "CONDITIONING", "out", "Pass-through."),
                _s("negative", "CONDITIONING", "out", "Pass-through."),
                _s("LATENT", "LATENT", "out", "Shape latent."),
            ],
        ),
        "Trellis2UpsampleStage": _n(
            "TRELLIS.2 Upsample Stage",
            "Upsample the shape latent toward 512.",
            lab="Lab widget 512. download-3d --tier trellis2.",
            origin="comfy-extras",
            sockets=[
                _s("positive", "CONDITIONING", "in", "Cond."),
                _s("negative", "CONDITIONING", "in", "Cond."),
                _s("shape_latent", "LATENT", "in", "Shape latent."),
                _s("vae", "VAE", "in", "TRELLIS VAE."),
                _s("positive", "CONDITIONING", "out", "Cond."),
                _s("negative", "CONDITIONING", "out", "Cond."),
                _s("LATENT", "LATENT", "out", "Upsampled shape."),
            ],
            widgets=[_w("resolution", index=0, typ="COMBO", rng="512", desc="Target structure resolution.", gen="512 is the lab INT8 mesh. Lower is faster and blockier.", choices=[("512", "Lab default."), ("256", "Faster, coarser.")])],
        ),
        "Trellis2TextureStage": _n(
            "TRELLIS.2 Texture Stage",
            "Sample voxel colors for the mesh.",
            origin="comfy-extras",
            sockets=[
                _s("positive", "CONDITIONING", "in", "Cond."),
                _s("negative", "CONDITIONING", "in", "Cond."),
                _s("shape_latent", "LATENT", "in", "Shape."),
                _s("positive", "CONDITIONING", "out", "Cond."),
                _s("negative", "CONDITIONING", "out", "Cond."),
                _s("LATENT", "LATENT", "out", "Texture latent."),
            ],
        ),
        "VaeDecodeStructureTrellis2": _n(
            "TRELLIS.2 Decode Structure",
            "Decode structure latent to voxels.",
            origin="comfy-extras",
            sockets=[
                _s("samples", "LATENT", "in", "Structure latent."),
                _s("vae", "VAE", "in", "TRELLIS VAE."),
                _s("voxel", "LATENT", "out", "Voxel grid."),
            ],
            widgets=[_w("resolution", index=0, typ="COMBO", rng="32", desc="Voxel grid size.", gen="32 is the lab structure decode.", choices=[("32", "Lab default.")])],
        ),
        "VaeDecodeShapeTrellis": _n(
            "TRELLIS Decode Shape",
            "Decode shape latent to a mesh.",
            origin="comfy-extras",
            sockets=[
                _s("samples", "LATENT", "in", "Shape latent."),
                _s("vae", "VAE", "in", "VAE."),
                _s("mesh", "MESH", "out", "Untextured mesh."),
                _s("shape_subdivides", "SHAPE_SUBDIVIDES", "out", "Subdivision payload for texture decode."),
            ],
        ),
        "VaeDecodeTextureTrellis": _n(
            "TRELLIS Decode Texture",
            "Decode texture latent to voxel colors.",
            origin="comfy-extras",
            sockets=[
                _s("samples", "LATENT", "in", "Texture latent."),
                _s("vae", "VAE", "in", "VAE."),
                _s("shape_subdivides", "SHAPE_SUBDIVIDES", "in", "From shape decode."),
                _s("voxel_colors", "VOXEL_COLORS", "out", "Colors for PaintMesh."),
            ],
        ),
        "PaintMesh": _n(
            "Paint Mesh",
            "Apply voxel colors onto the mesh.",
            origin="comfy-extras",
            sockets=[
                _s("mesh", "MESH", "in", "Shape mesh."),
                _s("voxel_colors", "VOXEL_COLORS", "in", "Decoded colors."),
                _s("mesh", "MESH", "out", "Painted mesh."),
            ],
        ),
        "MeshToFile3D": _n(
            "Mesh to File 3D",
            "Write a GLB/mesh file.",
            lab="optional/klein/trellis2 may leave the path empty (Comfy default). dcc/trellis/from-klein-still writes assets/objects/_lab-mug/mesh.",
            origin="comfy-extras",
            sockets=[
                _s("mesh", "MESH", "in", "Painted mesh."),
                _s("model_3d", "MODEL_3D", "out", "File handle."),
            ],
            widgets=[],
            variants=[
                {
                    "widgets": [
                        _w("filename_prefix", index=0, desc="Output stem under the output folder.", gen="Lab mug pack uses assets/objects/_lab-mug/mesh."),
                    ]
                }
            ],
        ),
    }

    # ez_prompt_enhance
    nodes["EZKleinPromptEnhance"] = _n(
        "Klein Prompt Enhance",
        "Rewrite a lazy still/edit prompt for Klein 4B with on-box Qwen3-4B-Instruct.",
        origin="ez_prompt_enhance",
        lab="Enhance on for lazy CLIP printers; off for authored recipes. Style ignored when it would fight an I2V start frame (not used here). Occupancy llm for the GGUF, then klein for the UNET.",
        sockets=[
            _s("prompt", "STRING", "in", "Optional override of the widget (usually unwired)."),
            _s("context", "STRING", "in", "Bible/research. Ignored when Enhance is off."),
            _s("prompt", "STRING", "out", "String CLIP actually encodes."),
        ],
        widgets=[
            _w("sample", index=0, typ="COMBO", rng="custom", desc="Lab sample prompt or Custom.", gen="Custom keeps the textarea. Picking a sample fills and locks the Prompt. Python combo is the union of every catalog so Comfy accepts place recipes (Cliff villa on dream-house); JS still filters the App dropdown to this graph."),
            _w("prompt", index=1, desc="Lazy sentence or authored still prompt.", gen="When Enhance is on, the GGUF expands this into Klein-native sentences."),
            _w("enhance", index=2, typ="BOOLEAN", rng="on for lazy printers", desc="Run the rewriter.", gen="Off = encode the widget as-is (plus style suffix if set)."),
            _w("mode", index=3, typ="COMBO", rng="t2i / edit / identity", desc="System prompt flavor.", gen="t2i = new still. edit = change an existing still. identity = camera-free bible (identity-sheet).", choices=[("t2i", "New still."), ("edit", "Klein-edit / clay / tweak."), ("identity", "Camera-free identity bible.")]),
            _w("duration_hint", index=4, desc="Framing hint (YouTube 16:9 still, Instagram 4:5, …).", gen="Steers aspect language in the rewrite. Does not set the latent size — EmptyFlux2LatentImage does."),
            _w("style", index=5, typ="COMBO", rng="none", desc="Look reference woven into the CLIP prompt.", gen="none = off. Dropdown wins over style words already in the source. Hidden on I2V graphs.", choices_from="styles"),
            _w("catalog", index=6, desc="Sample-catalog id (graph stem).", gen="Internal. Leave as stamped so sample dropdowns resolve."),
        ],
    )
    nodes["EZWanPromptEnhance"] = _n(
        "Wan Prompt Enhance",
        "Rewrite a lazy prompt for Wan 2.2 TI2V-5B (silent).",
        origin="ez_prompt_enhance",
        sockets=[
            _s("prompt", "STRING", "in", "Optional."),
            _s("context", "STRING", "in", "Bible/research. Ignored when Enhance is off."),
            _s("prompt", "STRING", "out", "Motion string for CLIP."),
        ],
        widgets=[
            _w("sample", index=0, typ="COMBO", rng="custom", desc="Sample or Custom.", gen="Custom keeps the textarea."),
            _w("prompt", index=1, desc="Lazy motion sentence.", gen="I2V rewrites to motion + one camera only. Do not prompt audio — Wan is silent."),
            _w("enhance", index=2, typ="BOOLEAN", desc="Run the rewriter.", gen="Off on authored camera-verb graphs (orbit, push-in, gif-loop)."),
            _w("mode", index=3, typ="COMBO", desc="System flavor.", gen="i2v is the smoke. t2v when LoadImage is bypassed. flf / vace / s2v for those opt-in graphs.", choices=[("t2v", "Text to silent video."), ("i2v", "Start image owns look; prompt is motion."), ("flf", "First-last-frame."), ("vace", "VACE join."), ("s2v", "Speech-to-video; wav owns lip-sync.")]),
            _w("duration_hint", index=4, rng="5 seconds, 24 fps", desc="Duration/fps hint for the rewriter.", gen="Does not change latent length — Wan22ImageToVideoLatent does."),
            _w("style", index=5, typ="COMBO", rng="none", desc="Look reference. Ignored on I2V.", gen="Start frame owns look on I2V.", choices_from="styles"),
            _w("catalog", index=6, desc="Sample-catalog id.", gen="Leave as stamped."),
        ],
    )
    nodes["EZLTXPromptEnhance"] = _n(
        "LTX Prompt Enhance",
        "Rewrite a lazy prompt for LTX-2.5 (present-tense paragraph, audio interleaved).",
        origin="ez_prompt_enhance",
        lab="Off on 90s films, talking-head, authored showcase. On for generic 5 s printers.",
        sockets=[_s("prompt", "STRING", "out", "Paragraph CLIP encodes.")],
        widgets=[
            _w("sample", index=0, typ="COMBO", rng="custom", desc="Sample or Custom.", gen="Custom keeps the textarea."),
            _w("prompt", index=1, desc="Lazy sentence or authored LTX paragraph.", gen="I2V: start image holds look; prompt is motion + world SFX. Dialogue belongs in \"quotes\" only if you asked for speech."),
            _w("enhance", index=2, typ="BOOLEAN", desc="Run the rewriter.", gen="Off keeps authored film/shot text pinned."),
            _w("mode", index=3, typ="COMBO", desc="t2v vs i2v vs iclora system prompt.", gen="i2v when a start still is wired. iclora describes look, not the control type.", choices=[("t2v", "Text to AV."), ("i2v", "Start still owns look."), ("iclora", "Union Control look/materials; guide owns blocking.")]),
            _w("duration_hint", index=4, rng="5 seconds, 24 fps", desc="Duration hint.", gen="Does not set 121 frames — LTXVImgToVideo does."),
            _w("audio_notes", index=5, desc="World SFX / no-score policy.", gen="Lab 5 s printers ask for world SFX matching the start image, no score."),
            _w("style", index=6, typ="COMBO", rng="none", desc="Look reference. Ignored on I2V.", gen="Start frame owns look.", choices_from="styles"),
            _w("catalog", index=7, desc="Sample-catalog id.", gen="Leave as stamped."),
        ],
    )
    nodes["EZNegativePromptEnhance"] = _n(
        "Negative Prompt Enhance",
        "Rewrite a negative CLIP seed so it does not fight the positive.",
        origin="ez_prompt_enhance",
        sockets=[
            _s("positive", "STRING", "in", "Positive CLIP string as context."),
            _s("prompt", "STRING", "out", "Negative string."),
        ],
        widgets=[
            _w("prompt", index=0, desc="Negative seed (artifacts, not style).", gen="FLUX-family models do not use negatives well. Keep this short; put constraints in the positive."),
            _w("enhance", index=1, typ="BOOLEAN", desc="Rewrite using the positive as context.", gen="Stops canned 'illustration / Pixar' terms from fighting a cartoon-positive."),
            _w("family", index=2, typ="COMBO", desc="Which negative family.", gen="Must match the UNET on the canvas.", choices=[("klein", "Klein stills."), ("wan", "Wan silent."), ("ltx", "LTX AV."), ("zimage", "Z-Image Turbo (CFG 1; list is documentation)."), ("longcat", "LongCat-Video."), ("dreamx", "DreamX-Creator AV."), ("s2v", "Wan S2V; wav owns speech.")]),
        ],
    )
    nodes["EZZimagePromptEnhance"] = _n(
        "Z-Image Prompt Enhance",
        "Rewrite a lazy still prompt for Z-Image Turbo (Qwen3-4B chat wrap).",
        origin="ez_prompt_enhance",
        lab="Turbo ignores a separate negative CLIP. Exclusions stay in the positive. No z_image_turbo UNET on lab graphs.",
        sockets=[
            _s("prompt", "STRING", "in", "Optional override of the widget."),
            _s("context", "STRING", "in", "Bible/research. Ignored when Enhance is off."),
            _s("prompt", "STRING", "out", "String CLIP actually encodes."),
        ],
        widgets=[
            _w("sample", index=0, typ="COMBO", rng="custom", desc="Lab sample prompt or Custom.", gen="Custom keeps the textarea."),
            _w("prompt", index=1, desc="Lazy sentence or authored still prompt.", gen="When Enhance is on, the GGUF expands this into Z-Image sentences with in-prompt constraints."),
            _w("enhance", index=2, typ="BOOLEAN", rng="on", desc="Run the rewriter.", gen="Off = encode the widget as-is (plus style suffix if set)."),
            _w("duration_hint", index=3, desc="Framing hint (YouTube 16:9 still, …).", gen="Steers aspect language. Does not set the latent size."),
            _w("style", index=4, typ="COMBO", rng="none", desc="Look reference woven into the CLIP prompt.", gen="none = off. Dropdown wins over style words already in the source.", choices_from="styles"),
            _w("catalog", index=5, desc="Sample-catalog id (graph stem).", gen="Internal. Leave as stamped."),
        ],
    )
    nodes["EZLongCatPromptEnhance"] = _n(
        "LongCat Prompt Enhance",
        "Rewrite a lazy prompt for LongCat-Video (T2V / I2V / continuation).",
        origin="ez_prompt_enhance",
        lab="No native audio. Standard CFG ~4; distilled CFG 1 ignores negatives. Optional stub preview on optional/longcat-video.",
        sockets=[
            _s("prompt", "STRING", "in", "Optional."),
            _s("context", "STRING", "in", "Bible/research. Ignored when Enhance is off."),
            _s("prompt", "STRING", "out", "Motion string for CLIP."),
        ],
        widgets=[
            _w("sample", index=0, typ="COMBO", rng="custom", desc="Sample or Custom.", gen="Custom keeps the textarea."),
            _w("prompt", index=1, desc="Lazy motion sentence.", gen="T2V is scene+motion+camera. I2V extends the still. vc continues previous frames."),
            _w("enhance", index=2, typ="BOOLEAN", desc="Run the rewriter.", gen="Off pins the widget text."),
            _w("mode", index=3, typ="COMBO", desc="System flavor.", gen="t2v on the stub. i2v / vc when start frames exist.", choices=[("t2v", "Text to video."), ("i2v", "Start image owns look."), ("vc", "Continue previous frames.")]),
            _w("duration_hint", index=4, rng="5 seconds, 30 fps", desc="Duration/fps hint for the rewriter.", gen="Does not change latent length."),
            _w("style", index=5, typ="COMBO", rng="none", desc="Look reference. Ignored on I2V/vc.", gen="Start frames own look on I2V/vc.", choices_from="styles"),
            _w("catalog", index=6, desc="Sample-catalog id.", gen="Leave as stamped."),
        ],
    )
    nodes["EZDreamXPromptEnhance"] = _n(
        "DreamX Prompt Enhance",
        "Rewrite a lazy first-frame+text prompt for DreamX-Creator (UMT5, joint AV).",
        origin="ez_prompt_enhance",
        lab="First frame owns look. Paragraph is visual dynamics plus interleaved acoustic events. No DreamX UNET on lab graphs — Prompt Forge preview only.",
        sockets=[
            _s("prompt", "STRING", "in", "Optional."),
            _s("context", "STRING", "in", "Bible/research. Ignored when Enhance is off."),
            _s("prompt", "STRING", "out", "AV paragraph."),
        ],
        widgets=[
            _w("sample", index=0, typ="COMBO", rng="custom", desc="Sample or Custom.", gen="Custom keeps the textarea."),
            _w("prompt", index=1, desc="Lazy sentence or authored AV paragraph.", gen="Do not restate the start-image look. Name motion and sound."),
            _w("enhance", index=2, typ="BOOLEAN", desc="Run the rewriter.", gen="Off pins the widget text."),
            _w("duration_hint", index=3, rng="5 seconds, 24 fps", desc="Duration hint.", gen="Lab takes are about 5 s at 24 fps."),
            _w("audio_notes", index=4, desc="World SFX / no-score policy.", gen="Interleave with the action; do not dump a trailer."),
            _w("style", index=5, typ="COMBO", rng="none", desc="Look reference. Ignored (start image owns look).", gen="Start frame owns look.", choices_from="styles"),
            _w("catalog", index=6, desc="Sample-catalog id.", gen="Leave as stamped."),
        ],
    )
    nodes["EZAceStepPromptEnhance"] = _n(
        "ACE-Step Prompt Enhance",
        "Rewrite ACE tags (genre first) and lyrics. Instrumental mode forces [inst].",
        origin="ez_prompt_enhance",
        lab="Enhance off on authored album takes. Instrumental sanitizes lyrics into bracket cues.",
        sockets=[
            _s("lyrics", "STRING", "in", "Optional lyrics override (EZRapLyrics)."),
            _s("tags", "STRING", "out", "Tags for the ACE encoder."),
            _s("lyrics", "STRING", "out", "Lyrics / [inst] for the ACE encoder."),
        ],
        widgets=[
            _w("sample", index=0, typ="COMBO", rng="custom", desc="Sample or Custom.", gen="Custom keeps authored tags/lyrics."),
            _w("tags", index=1, desc="Genre-first tags.", gen="Keep vocal identity tags stable across an album. Drive-through is not rap-over-club."),
            _w("lyrics", index=2, desc="Sectioned lyrics.", gen="Enhance off on catalog takes so exclusive verses stay pinned."),
            _w("enhance", index=3, typ="BOOLEAN", rng="false on albums", desc="Run the rewriter.", gen="On only when you typed a lazy hook and want the GGUF to expand it."),
            _w("mode", index=4, typ="COMBO", desc="Vocal vs instrumental sanitizer.", gen="instrumental forces no-vocals tags and [inst] lyrics.", choices=[("vocal", "Nill Bye / rap-draft / rap-full."), ("instrumental", "Drive-through EDM.")]),
            _w("catalog", index=5, desc="Sample-catalog id.", gen="Leave as stamped."),
        ],
    )
    nodes["EZPromptJoin"] = _n(
        "Prompt Join",
        "Join a shared identity paragraph with a shot-specific camera line.",
        origin="ez_prompt_enhance",
        sockets=[
            _s("identity", "STRING", "in", "World bible / character lock."),
            _s("prompt", "STRING", "out", "Joined prompt for CLIP / Enhance."),
        ],
        widgets=[
            _w("shot", index=0, desc="Shot card (camera, room, action).", gen="lock=view front-loads this so Klein sees a new camera in the same place."),
            _w("inventory", index=1, desc="Locked object list.", gen="Keeps mugs/coats from mutating across a pack."),
            _w("lock", index=2, typ="COMBO", rng="view", desc="What stays pinned.", gen="view = new camera, same place (dream-house, storyboard). state = same camera, new light/grade (time-of-day, color-moods).", choices=[("view", "New camera, same world."), ("state", "Same framing, new light/grade/action.")]),
        ],
    )
    nodes["EZContextJoin"] = _n(
        "Context Join",
        "Pack labeled desk fields into one context STRING for rewriter nodes.",
        origin="ez_prompt_enhance",
        sockets=[
            _s("a", "STRING", "in", "Logline."),
            _s("b", "STRING", "in", "Script."),
            _s("c", "STRING", "in", "Audio policy."),
            _s("d", "STRING", "in", "Score."),
            _s("context", "STRING", "out", "Labeled block for Enhance context."),
        ],
        widgets=[
            _w("label_a", index=0, rng="Logline", desc="Label for field A.", gen="Empty values are omitted."),
            _w("label_b", index=1, rng="Script", desc="Label for field B.", gen="Beat-sheet default Script."),
            _w("label_c", index=2, rng="Audio policy", desc="Label for field C.", gen="Keeps no-score / world-SFX policy in every card rewrite."),
            _w("label_d", index=3, rng="Score", desc="Label for field D.", gen="Optional."),
        ],
    )
    nodes["EZCinemaRack"] = _n(
        "Cinema Rack",
        "Pick one cinematography technique per axis and splice a Klein / Wan / LTX prompt.",
        origin="ez_prompt_enhance",
        lab="Deterministic. No LLM. Recipe fills empty axes. Wan emits one camera verb. I2V drops look. Editing omitted on stills. Style on downstream Enhance stays none.",
        sockets=[
            _s("prompt", "STRING", "out", "Spliced prompt for CLIP / Enhance."),
            _s("notes", "STRING", "out", "Dropped conflicts and Wan camera token."),
        ],
        widgets=[
            _w("subject", index=0, desc="Who or what is in the shot.", gen="Front-loaded except on I2V (start image owns identity)."),
            _w("flavor", index=1, typ="COMBO", rng="klein", desc="Family renderer.", gen="klein stills freeze motion axes. wan_t2v appends one camera token. i2v drops look.", choices=[("klein", "Still sentences."), ("klein_edit", "Edit still."), ("klein_identity", "Camera-free bible."), ("wan_t2v", "Look + one camera."), ("wan_i2v", "Motion + camera only."), ("ltx_t2v", "Present tense + foley."), ("ltx_i2v", "I2V AV; look dropped.")]),
            _w("recipe", index=2, typ="COMBO", rng="none", desc="Named splice.", gen="Fills axes that are still none. Explicit picks win."),
            _w("framing_shot_size", index=3, typ="COMBO", rng="none", desc="Shot size.", gen="How much of the subject fills the frame. Catalog under generated/cinema."),
            _w("camera_angles", index=4, typ="COMBO", rng="none", desc="Camera angle.", gen="Height and subject-relative angle. Catalog under generated/cinema."),
            _w("camera_movement", index=5, typ="COMBO", rng="none", desc="Camera move.", gen="The single Wan camera verb. Catalog under generated/cinema."),
            _w("lenses_optics", index=6, typ="COMBO", rng="none", desc="Lens and optic.", gen="Focal length and optic character. Catalog under generated/cinema."),
            _w("composition", index=7, typ="COMBO", rng="none", desc="Composition.", gen="Where masses sit in the frame. Catalog under generated/cinema."),
            _w("lighting", index=8, typ="COMBO", rng="none", desc="Lighting.", gen="Key quality, direction, and motivation. Catalog under generated/cinema."),
            _w("color_film_look", index=9, typ="COMBO", rng="none", desc="Color and film look.", gen="Grade and photochemical grammar, no stock names. Catalog under generated/cinema."),
            _w("time_motion", index=10, typ="COMBO", rng="none", desc="Time and motion.", gen="Shutter and temporal grammar. Catalog under generated/cinema."),
            _w("in_camera_optical", index=11, typ="COMBO", rng="none", desc="In-camera / optical.", gen="Flare, zoom, and in-camera tricks. Catalog under generated/cinema."),
            _w("editing_transitions", index=12, typ="COMBO", rng="none", desc="Editing.", gen="Named cuts. Omitted on Klein stills. Catalog under generated/cinema."),
            _w("atmosphere_weather", index=13, typ="COMBO", rng="none", desc="Atmosphere.", gen="Air, precip, ground. LTX interleaves foley. Catalog under generated/cinema."),
            _w("genre_looks", index=14, typ="COMBO", rng="none", desc="Genre grammar.", gen="Genre lighting and texture, not a titled film. Catalog under generated/cinema."),
            _w("viral_looks", index=15, typ="COMBO", rng="none", desc="Short-form hook.", gen="Platform-agnostic hook grammar. Catalog under generated/cinema."),
        ],
    )
    nodes["EZSamplePrompt"] = _n(
        "Sample Prompt",
        "STRING source with a sample-prompt combo plus Custom textarea.",
        origin="ez_prompt_enhance",
        sockets=[_s("prompt", "STRING", "out", "Resolved prompt.")],
        widgets=[
            _w("sample", index=0, typ="COMBO", rng="custom", desc="Sample or Custom.", gen="Custom uses the textarea as typed."),
            _w("prompt", index=1, desc="Custom textarea.", gen="Ignored when a sample is selected."),
            _w("catalog", index=2, desc="Catalog id (inspire/prompt-forge).", gen="Leave as stamped."),
        ],
    )
    nodes["EZRapLyrics"] = _n(
        "Rap Lyrics",
        "Draft original rap lyrics via the on-box GGUF. Forbids living-MC names.",
        origin="ez_music",
        sockets=[
            _s("context", "STRING", "in", "Optional. Ignored when Enhance is off."),
            _s("lyrics", "STRING", "out", "Sectioned lyrics for ACE."),
        ],
        widgets=[
            _w("sample", index=0, typ="COMBO", rng="custom", desc="Sample or Custom.", gen="Custom keeps authored bars."),
            _w("lyrics", index=1, desc="Sectioned lyrics.", gen="Human rewrite required before any release. Catalog takes keep Enhance off."),
            _w("enhance", index=2, typ="BOOLEAN", rng="false on albums", desc="Run the lyrics writer.", gen="On only for a lazy draft. Off pins exclusive verses."),
            _w("catalog", index=3, desc="Catalog id.", gen="Leave as stamped."),
        ],
    )
    nodes["EZAudioMetadata"] = _n(
        "Audio Metadata",
        "Stamp artist/album/title tags and optional cover on saved audio.",
        origin="ez_music",
        sockets=[
            _s("audio", "AUDIO", "in", "Pass-through AUDIO."),
            _s("cover", "IMAGE", "in", "Optional. Unwired so App Queue does not require a file."),
            _s("audio", "AUDIO", "out", "Same AUDIO; files on disk get tags."),
        ],
        widgets=[
            _w("artist", index=0, desc="ID3/Vorbis artist.", gen="Nill Bye vs Drive-through."),
            _w("album", index=1, desc="Album title.", gen="Must match the folder album-slug display name."),
            _w("title", index=2, desc="Track title.", gen="Pairs with SaveAudio stem NN - Song Title."),
            _w("track", index=3, typ="INT", rng="1–99", desc="Track number.", gen="Numbered takes 01–20."),
            _w("tracktotal", index=4, typ="INT", desc="Album track count.", gen="15 or 20 depending on the album."),
            _w("year", index=5, typ="INT", rng="2026", desc="Tag year.", gen="Does not affect audio."),
            _w("art_mode", index=6, typ="COMBO", rng="skip", desc="Cover art policy.", gen="skip on every audio Queue (Cover LoadImage is bypassed). generate is klein occupancy — later session. upload: graph view, Ctrl+B Cover image, then wire.", choices=[("skip", "Lab default. No cover required."), ("upload", "Un-bypass Cover image and wire the socket."), ("generate", "Use cover.jpg from the album folder (klein session).")]),
            _w("prefix", index=7, desc="SaveAudio stem to stamp.", gen="Must match SaveAudio / SaveAudioMP3."),
        ],
    )
    nodes["EZAlbumPack"] = _n(
        "Album Pack",
        "Write <Album>.m3u and <Album>.zip under albums/<Artist>/<Album>/.",
        origin="ez_music",
        sockets=[_s("zip_path", "STRING", "out", "Zip path or empty on failure.")],
        widgets=[
            _w("artist", index=0, desc="Artist folder.", gen="Drive-through or Nill Bye."),
            _w("album", index=1, desc="Album folder display name.", gen="Queue tracks first (or album-render). CPU only."),
        ],
    )
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
            _w("target_language", index=2, typ="COMBO", rng="es", desc="Target ISO code.", gen="es is the lab smoke. Clone CFG auto 0 on EN→ES.", choices=dub_langs),
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
            _w("cfg_weight", index=4, typ="FLOAT", rng="−1.0 = auto", desc="Clone CFG.", gen="−1 auto. Lab auto 0 on EN→ES."),
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
        lab="Queue once. xfade_cs is audio-only acrossfade; 0 is a hard cut. go-see ships xfade_cs 8.",
        sockets=[
            *[_s(f"shot_{i:02d}", "VHS_FILENAMES", "in", f"Shot {i:02d} MP4.") for i in range(1, 19)],
            _s("disclosure", "STRING", "in", "EZFilmDisclosure text."),
            _s("path", "STRING", "out", "ez_<slug>_90s.mp4 path."),
        ],
        widgets=[
            _w("film", index=0, typ="COMBO", desc="Film slug.", gen="Picks output name and shot-map. Must match the graph.", choices=[("go-see", "Parkour 90s."), ("still-here", "Household morning 90s."), ("switchyard", "Night freight-yard 90s.")]),
            _w("cap_seconds", index=1, typ="FLOAT", rng="90.0 max", desc="Hard duration cap.", gen="Stay 90. Longer fights the product rule (no 90 s denoise; this is a stitch cap)."),
            _w("xfade_cs", index=2, typ="INT", rng="0–50; 10 = 0.10 s", desc="Audio-only acrossfade in centiseconds.", gen="0 = hard cut (still-here, switchyard). 8 = 0.08 s audio cross on go-see. Picture stays cut-only so duration stays on picture."),
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
            _w("template", index=2, typ="COMBO", rng="auto", desc="Lab graph to clone.", gen="auto uses the GGUF planner or a keyword heuristic. Pin klein/ig-square to skip."),
            _w("slug", index=3, desc="Filename stem.", gen="Live _user/<slug>.app.json. Lowercase letters, digits, hyphen."),
            _w("as_app", index=4, typ="BOOLEAN", rng="true", desc="Write an App.", gen="true writes *.app.json for the Apps sidebar."),
            _w("overwrite", index=5, typ="BOOLEAN", rng="false", desc="Replace existing.", gen="false refuses an existing _user file."),
            _w("catalog", index=6, desc="Catalog id.", gen="Leave as stamped."),
        ],
    )
    return nodes
