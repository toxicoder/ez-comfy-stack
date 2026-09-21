"""Comfy-core encyclopedia rows (samplers, loaders, I/O).

Helpers and combo catalogs live in :mod:`workflow_nodes_lib`.
"""

from __future__ import annotations

from typing import Any

from workflow_nodes_lib import (
    _CLIP_TYPES,
    _CROP,
    _DEVICE,
    _SEED_CONTROL,
    _UPSCALE,
    _WEIGHT_DTYPE,
    _n,
    _s,
    _w,
    ksampler_widgets,
)

def core_nodes() -> dict[str, Any]:
    """Comfy-core loaders, latents, VAE, image I/O, notes.

    Returns:
        Node specs keyed by type.
    """
    widgets = ksampler_widgets()
    return {
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
            widgets=widgets,
        ),
        "UNETLoader": _n(
            "Load Diffusion Model",
            "Load a standalone transformer/UNET from diffusion_models/.",
            lab="Lab files: flux-2-klein-4b-fp8.safetensors, wan2.2_ti2v_5B_fp16.safetensors, ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors. weight_dtype stays default.",
            sockets=[_s("MODEL", "MODEL", "out", "Denoiser weights.")],
            widgets=[
                _w("unet_name", index=0, desc="Checkpoint filename under MODELS_DIR diffusion_models.", gen="Wrong family = Queue error or a melted picture. Lab pins Apache Klein 4B. Klein 9B / FLUX.2-dev are opt-in NC. MiniMax is banned."),
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
            lab="Width/height must be ÷32. Length must be 1+8n (193 for ~8 s Apps; 121 for 5 s film printers). ez_ltx_spatial snaps illegal values.",
            sockets=[_s("LATENT", "LATENT", "out", "Video latent (then concat with audio latent).")],
            widgets=[
                _w("width", index=0, typ="INT", rng="1280 (landscape) / 768 (shorts)", desc="Frame width.", gen="÷32. 1280×720 will snap to 704."),
                _w("height", index=1, typ="INT", rng="704 / 1280", desc="Frame height.", gen="704 is the lab landscape printer."),
                _w("length", index=2, typ="INT", rng="193 Apps / 121 film = 1+8n", desc="Frame count.", gen="Standalone Apps default 193 @ 24 fps ≈ 8.04 s. Film printers stay 121 (~5.04 s). 120 is illegal (VAE floors to 113). Do not type a 30/60/90 s latent."),
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
            lab="motion/av/audio-to-video-8s defaults ez_a2v_bed.wav. Drop the file in ${COMFY_OUTPUT_DIR}/input.",
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
        "EZSnapImage": _n(
            "Snap image (div 16)",
            "Scale a still to the largest width and height that fit inside the source and are multiples of 16.",
            origin="ez_image",
            lab="stills/text-swap snaps the start image to the Flux.2 Klein VAE grid before VAEEncode. stills/background-swap also feeds EZEmptyFlux2FromImage.",
            sockets=[
                _s("image", "IMAGE", "in", "Source still."),
                _s("IMAGE", "IMAGE", "out", "Snapped still."),
            ],
            widgets=[],
        ),
        "EZEmptyFlux2FromImage": _n(
            "Empty Flux.2 from image",
            "Allocate an empty Flux.2 latent matching a still's snapped width and height.",
            origin="ez_image",
            lab="stills/background-swap uses this as KSampler.latent_image so the encoded source is only a ReferenceLatent.",
            sockets=[
                _s("image", "IMAGE", "in", "Snapped still."),
                _s("LATENT", "LATENT", "out", "Empty Flux.2 noise canvas (÷16, 128 channels)."),
            ],
            widgets=[],
        ),
        "EZImageUpscale": _n(
            "Upscale still",
            "Optional lanczos upscale after a still decode. none passes the tensor through.",
            origin="ez_image",
            lab="Wired before SaveImage on stills, creator stills, and DCC still plates. One App dropdown drives every output.",
            sockets=[
                _s("image", "IMAGE", "in", "Decoded still."),
                _s("IMAGE", "IMAGE", "out", "Possibly upscaled still."),
                _s("upscale", "STRING", "out", "Combo id for additional EZImageUpscale nodes."),
            ],
            widgets=[
                _w("upscale", index=0, typ="COMBO", rng="none / 2x / 4x / 4K", desc="Upscale mode.", gen="none is a passthrough. 2x and 4x are lanczos. 4K fits the still in a 3840×2160 box (portrait 2160×3840). No extra weights.", choices=[("none", "Pass through."), ("2x", "Double pixels."), ("4x", "Quadruple pixels."), ("4K", "Fit in a 4K box.")]),
            ],
        ),
        "EZMatchImageSize": _n(
            "Match image size",
            "Resize a still to another image's exact width and height.",
            origin="ez_image",
            lab="stills/text-swap restores the decode to the uploaded still's pixel size.",
            sockets=[
                _s("image", "IMAGE", "in", "Edited still."),
                _s("size_src", "IMAGE", "in", "Source still whose H×W is the target."),
                _s("IMAGE", "IMAGE", "out", "Edited still at source size."),
            ],
            widgets=[],
        ),
        "EZImageFormat": _n(
            "Format / platform",
            "Pick a Klein still canvas (aspect or named platform) and an optional Cinema Rack look recipe.",
            origin="ez_image",
            lab="stills/still-studio wires width/height/batch into EmptyFlux2LatentImage, hint into Enhance duration_hint, prefix into SaveImage, and look splice into Enhance context. Quality does not change size. Match input snaps aspect to a loaded still.",
            sockets=[
                _s("image", "IMAGE", "in", "Optional still used when Output size is Match input."),
                _s("width", "INT", "out", "Latent width (÷16)."),
                _s("height", "INT", "out", "Latent height (÷16)."),
                _s("batch", "INT", "out", "Batch size."),
                _s("hint", "STRING", "out", "Enhance duration / framing line."),
                _s("prefix", "STRING", "out", "SaveImage filename prefix."),
                _s("context", "STRING", "out", "Look-recipe splice for Enhance context."),
            ],
            widgets=[
                _w("format", index=0, typ="COMBO", rng="16:9 LTX feeder / platform jobs / Custom", desc="Aspect or named platform job.", gen="Preset writes pixels, save prefix, and Rewrite prompt framing. Custom uses Width × Height (snapped to ÷16, max 2048). Does not change Quality, CLIP, or VAE.", choices_from="image_formats"),
                _w("look", index=1, typ="COMBO", rng="none", desc="Optional Cinema Rack starter.", gen="none leaves look to Style + Prompt. A pick splices Klein still language into Enhance context. Full 13-axis desk is inspire/cinema-rack.", choices_from="cinema_recipes"),
                _w("width", index=2, typ="INT", rng="16–2048, step 16", desc="Custom width.", gen="Used when Format is Custom. Presets ignore this widget at Queue."),
                _w("height", index=3, typ="INT", rng="16–2048, step 16", desc="Custom height.", gen="Used when Format is Custom. Presets ignore this widget at Queue."),
                _w("batch_size", index=4, typ="INT", rng="1–4", desc="How many stills in one Run.", gen="Large canvases stay at 1."),
                _w("size_mode", index=5, typ="COMBO", rng="Match input / Force format", desc="Match a loaded still's aspect, or keep Format / platform.", gen="Match input (default) picks the nearest aspect catalog row when a still is loaded. Force format keeps the Format pick. No still: authored format. Quality does not change size."),
            ],
        ),
        "EZImageMode": _n(
            "Creator mode",
            "Pick one of 100 creator modes. Category filters Mode. Queue splices an instruction into Enhance context and selects t2i/edit/text_swap/identity/background_swap/background_edit plus a save prefix.",
            origin="ez_image",
            lab="stills/image-studio wires context into EZKleinPromptEnhance, enhance_mode into the Enhance mode widget, and prefix into SaveImage. Optional references stay optional.",
            sockets=[
                _s("context", "STRING", "in", "Optional look-recipe splice from EZImageFormat."),
                _s("context", "STRING", "out", "Mode instruction plus incoming look splice."),
                _s("enhance_mode", "COMBO", "out", "t2i, edit, identity, text_swap, background_swap, or background_edit — same combo as EZKleinPromptEnhance.mode."),
                _s("prefix", "STRING", "out", "SaveImage filename prefix."),
            ],
            widgets=[
                _w("category", index=0, typ="COMBO", rng="Generate / Scene / Subject / …", desc="Filter Creator mode.", gen="JS hides modes outside this category. Python run() uses Mode even if Category is stale.", choices_from="image_mode_categories"),
                _w("mode", index=1, typ="COMBO", rng="Photoreal still / Background swap / Change text / …", desc="Creator preset.", gen="Sets Enhance mode, save prefix, and a locked instruction. Empty reference stills never error.", choices_from="image_modes"),
            ],
        ),
        "EZOptionalImage": _n(
            "Optional reference stills",
            "Optional example or reference stills. Empty is valid — Queue without a file.",
            origin="ez_image",
            lab="Klein T2I Apps attach a present still via EZKleinRefCanvas. Upload or pick a file already on the drive; filename may be empty.",
            sockets=[
                _s("image", "IMAGE", "in", "Optional first still."),
                _s("image_2", "IMAGE", "in", "Optional second still."),
                _s("image_3", "IMAGE", "in", "Optional third still."),
                _s("image", "IMAGE", "out", "First present still, or empty."),
                _s("count", "INT", "out", "How many stills are present."),
                _s("has_image", "BOOLEAN", "out", "True when at least one still is present."),
            ],
            widgets=[
                _w("filename", index=0, typ="COMBO", rng="empty / input stills", desc="Upload or pick a still on the drive. Empty is valid.", gen="Empty Queues a T2I. A pick loads from input/. Choose from outputs copies a durable file into input/."),
            ],
        ),
        "EZKleinRefCanvas": _n(
            "Klein canvas (optional ref)",
            "Pass the empty Flux2 latent, or VAE-encode a still and attach ReferenceLatent.",
            origin="ez_image",
            lab="Fail-soft: empty still or encode errors pass the empty latent through. Never raises.",
            sockets=[
                _s("latent", "LATENT", "in", "Empty Flux2 canvas."),
                _s("vae", "VAE", "in", "Flux2 VAE."),
                _s("image", "IMAGE", "in", "Optional start still."),
                _s("has_image", "BOOLEAN", "in", "Presence flag from EZOptionalImage."),
                _s("latent", "LATENT", "out", "Empty or reference-attached latent."),
                _s("image", "IMAGE", "out", "The still, or empty."),
            ],
            widgets=[
                _w("has_image", index=0, typ="BOOLEAN", rng="false", desc="Presence flag when unwired.", gen="Lab graphs wire this from EZOptionalImage. Off = T2I."),
            ],
        ),
        "EZDescribeImage": _n(
            "Describe reference still",
            "Fail-soft caption for models that are not multimodal. Empty without VL weights.",
            origin="ez_image",
            lab="This stack returns an empty caption (no VL GGUF). Klein graphs use EZKleinRefCanvas instead.",
            sockets=[
                _s("image", "IMAGE", "in", "Optional still."),
                _s("caption", "STRING", "out", "Caption, or empty."),
            ],
            widgets=[
                _w("has_image", index=0, typ="BOOLEAN", rng="false", desc="Presence flag.", gen="Off or missing VL weights → empty string."),
            ],
        ),
        "EZVideoFormat": _n(
            "Format / platform (video)",
            "Pick a Wan or LTX clip canvas (aspect or named platform).",
            origin="ez_image",
            lab="Wan and LTX printers wire width/height into Wan22ImageToVideoLatent, LTXVImgToVideo, or EmptyLTXVLatentVideo. Hint feeds Enhance duration_hint on non-loop graphs. Duration writes LTX length (default 8 s). Quality does not change size. Match input snaps aspect to a loaded still.",
            sockets=[
                _s("image", "IMAGE", "in", "Optional still used when Output size is Match input."),
                _s("width", "INT", "out", "Latent width (Wan ÷16, LTX ÷32)."),
                _s("height", "INT", "out", "Latent height (Wan ÷16, LTX ÷32)."),
                _s("hint", "STRING", "out", "Enhance duration / framing line."),
                _s("prefix", "STRING", "out", "Optional filename prefix (often unwired)."),
            ],
            widgets=[
                _w("family", index=0, typ="COMBO", rng="Wan 5B / LTX-2.5", desc="Which VAE grid to use.", gen="Wan snaps ÷16 (max 1024). LTX snaps ÷32 (max 1280). App Mode hides this — occupancy already picks the model.", choices_from="video_families"),
                _w("format", index=1, typ="COMBO", rng="16:9 YouTube / 9:16 Shorts / Custom", desc="Aspect or named platform job.", gen="Preset writes pixels and Rewrite prompt framing. Custom uses Width × Height. Does not change Quality, length, CLIP, or VAE.", choices_from="video_formats"),
                _w("width", index=2, typ="INT", rng="16–1280", desc="Custom width.", gen="Used when Format is Custom. Presets ignore this widget at Queue. LTX Custom snaps 720→704."),
                _w("height", index=3, typ="INT", rng="16–1280", desc="Custom height.", gen="Used when Format is Custom. Presets ignore this widget at Queue."),
                _w("size_mode", index=4, typ="COMBO", rng="Match input / Force format", desc="Match a loaded still's aspect, or keep Format / platform.", gen="Match input (default) picks the nearest family aspect row when a still is loaded. Force format keeps the Format pick. Quality does not change size."),
                _w("duration_s", index=5, typ="COMBO", rng="5 / 8 / 10 / 12 seconds", desc="LTX clip length.", gen="Default 8 seconds (193 frames, 1+8n). Frontend writes latent length. Wan 5B stays 5 seconds. Film printers stay 5 seconds / 121."),
            ],
        ),
        "ImageScale": _n(
            "Upscale Image",
            "Resize a still to a target width/height.",
            lab="dcc/clay-plates scales one clay into 704 / 1:1 / 4:5 / 9:16.",
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
        )
    }
