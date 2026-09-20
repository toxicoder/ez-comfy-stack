"""LTX-2.5 and audio encyclopedia rows.

Helpers and combo catalogs live in :mod:`workflow_nodes_lib`.
"""

from __future__ import annotations

from typing import Any

from workflow_nodes_lib import _n, _s, _w

def ltx_nodes() -> dict[str, Any]:
    """LTX-2.5 AV nodes and audio merge/concat.

    Returns:
        Node specs keyed by type.
    """
    return {
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
            lab="Skipped on motion/av/audio-to-video-12s (original wav is muxed).",
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
            lab="motion/av/first-last-12s uses index 0 then -1 on the video latent before audio concat.",
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
            lab="motion/av/dialogue-12s uses 3.0 / 0 / 1. Mouths still will not lip-sync; this only tightens A/V coupling.",
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
        )
    }
