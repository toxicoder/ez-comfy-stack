"""VHS and ACE-Step encyclopedia rows.

Helpers and combo catalogs live in :mod:`workflow_nodes_lib`.
"""

from __future__ import annotations

from typing import Any

from workflow_nodes_lib import (
    _SEED_CONTROL,
    _n,
    _s,
    _w,
    vhs_full,
    vhs_short,
)

def vhs_ace_nodes() -> dict[str, Any]:
    """VHS Video Combine and ACE-Step text encode.

    Returns:
        Node specs keyed by type.
    """
    full = vhs_full()
    short = vhs_short()
    return {
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
            widgets=full,
            variants=[{"widgets": short}],
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
                _w("bpm", index=4, typ="INT", rng="10-300", desc="Tempo written into the codes.", gen="Must match the tags' BPM. Mismatch makes the vocal drift the grid."),
                _w("duration", index=5, typ="FLOAT", desc="Seconds (duplicated on the latent).", gen="Keep in lockstep with EmptyAceStep1.5LatentAudio / Primitive."),
                _w("timesignature", index=6, typ="COMBO", rng="4", desc="Beats per bar.", gen="Rap Apps stay 4. Album takes may use 2, 3, or 6 when the bed is not a dance grid.", choices=[("2", "2/4."), ("3", "3/4."), ("4", "Lab 4/4."), ("6", "6/8.")]),
                _w("language", index=7, typ="COMBO", rng="en / unknown", desc="Lyric language.", gen="en for sung English. unknown for instrumental (do not leave en on a no-vocal take).", choices_from="ace_language"),
                _w("keyscale", index=8, typ="COMBO", rng="C minor", desc="Musical key.", gen="Rap Apps stay C minor. Catalog takes set a key per song (Drive-through walks fifths).", choices_from="ace_keyscale"),
                _w("generate_audio_codes", index=9, typ="BOOLEAN", rng="true", desc="Run the ACE LLM that drafts audio codes.", gen="true = higher quality, slower. Off only if you pass a reference timbre (lab graphs do not)."),
                _w("cfg_scale", index=10, typ="FLOAT", rng="2.0", desc="Guidance inside audio-code generation.", gen="2.0 is the ACE default. Higher follows tags/lyrics more tightly and can sound rigid."),
                _w("temperature", index=11, typ="FLOAT", rng="0.85", desc="Sampling temperature for audio codes.", gen="Lower = more deterministic. Higher = wilder fills."),
                _w("top_p", index=12, typ="FLOAT", rng="0.9", desc="Nucleus sampling.", gen="0.9 is the lab default."),
                _w("top_k", index=13, typ="INT", rng="0 = off", desc="Top-k token cap.", gen="0 disables top-k (lab)."),
                _w("min_p", index=14, typ="FLOAT", rng="0.0", desc="Minimum probability floor.", gen="0.0 disables min-p (lab)."),
            ],
        )
    }
