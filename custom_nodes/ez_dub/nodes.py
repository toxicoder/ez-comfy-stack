"""ComfyUI nodes for US-safe multi-speaker clone-and-translate dubs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, TypedDict

from .align import SAMPLE_RATE
from .audio import audio_from_pcm, empty_audio, read_wav
from .jobstore import dub_dir, record_ingest_failure, sanitize_slug
from .pipeline import (
    DISCLOSURE_TEXT,  # noqa: F401 - re-exported for tests and graph builder
    ENGINE_CHATTERBOX,
    ENGINES,
    LANG_CODES,
    SOURCE_LANG_WIDGET,
    SOURCE_NONE,
    STAGE_ALL,
    STAGE_ANALYZE,
    STAGES,
    TARGET_LANG_WIDGET,
    analyze_job,
    apply_spoken_disclosure,
    ingest,
    missing_source_status,
    render_mix,
    resolve_media_source,
    source_combo_options,
    synthesize_turn,
)
from .rights import RightsError
from .turns import Turn, dumps_payload, parse_payload

if TYPE_CHECKING:
    from ez_common import ComfyInputTypes, ComfyReturn, JsonScalar, NodeRegistry

# Empty widget seed so the App translation field is valid JSON on first load.
SEED_TURNS: list[Turn] = []
SEED_SCRIPT = dumps_payload(
    {
        "target_language": "es",
        "source_language": "auto",
        "stage": STAGE_ALL,
        "status": "",
        "turns": SEED_TURNS,
    }
)


class DubUiBlocks(TypedDict):
    """Preview blocks an ez_dub output node renders.

    Attributes:
        text: Status body shown in the text preview.
        passthrough: Status token shown under the preview.
    """

    text: tuple[str, ...]
    """Status body shown in the text preview."""

    passthrough: tuple[str, ...]
    """Status token shown under the preview."""


class ComfyUiResult(TypedDict):
    """OUTPUT_NODE payload Comfy shows in the UI.

    ``result`` may hold AUDIO tensors; torch is not imported at pack load.
    """

    ui: DubUiBlocks
    result: ComfyReturn


def _pack_text(text: str, status: str) -> ComfyUiResult:
    """Pack a STRING OUTPUT_NODE result.

    Args:
        text: Widget JSON or status body.
        status: Short Dub status for the passthrough UI.

    Returns:
        Comfy ``ui``/``result`` mapping.
    """
    return {
        "ui": {"text": (text,), "passthrough": (status,)},
        "result": (text,),
    }


def _pack_audio(
    samples: Sequence[float], rate: int, status: str
) -> ComfyUiResult:
    """Pack an AUDIO OUTPUT_NODE result.

    Args:
        samples: Mono PCM or empty.
        rate: Sample rate.
        status: Short Dub status for the passthrough UI.

    Returns:
        Comfy ``ui``/``result`` mapping.
    """
    audio = audio_from_pcm(samples, rate) if samples else empty_audio(rate)
    return {
        "ui": {"text": (status,), "passthrough": (status,)},
        "result": (audio,),
    }


class EZDubIngest:
    """Local file or URL ingest. Refuses Queue without rights."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Comfy widget schema.

        Returns:
            Required ingest widgets.
        """
        return {
            "required": {
                "source": (
                    source_combo_options(),
                    {
                        "default": SOURCE_NONE,
                        "tooltip": "Pick the clip to dub from the media this "
                        "node lists out of the Comfy input folder "
                        "(COMFY_OUTPUT_DIR/input, container /inputs), or type "
                        "a path you own. Queue refuses while the pick stays "
                        "(none); dub-fetch run --url drops a new file there.",
                    },
                ),
                "have_rights": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Turn on to say you own or may license this "
                        "audio; Queue is refused while it stays off.",
                    },
                ),
                "job_slug": (
                    "STRING",
                    {
                        "default": "episode",
                        "dynamicPrompts": False,
                        "tooltip": "Job folder name under "
                        "COMFY_OUTPUT_DIR/dubs, so episode writes "
                        "dubs/episode/source.wav; ls $COMFY_OUTPUT_DIR/dubs "
                        "lists the jobs you already have. Use the same name "
                        "on all three Dub nodes, and blank falls back to "
                        "episode.",
                    },
                ),
                "source_url": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                        "dynamicPrompts": False,
                        "tooltip": "Optional http(s) address you have rights "
                        "to, fetched with yt-dlp instead of the pick above. "
                        "Leave empty to use Source file.",
                    },
                ),
            }
        }

    # Comfy node metadata (outputs, category, operator description).
    RETURN_TYPES = ("STRING", "AUDIO")
    RETURN_NAMES = ("job_id", "audio")
    FUNCTION = "run"
    CATEGORY = "ez-comfy/dub"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Extracts audio from a file in Comfy input/ (select or upload) "
        "or an optional http(s) URL. Queue refuses unless I have rights "
        "is on. No celebrity refs."
    )

    def run(
        self,
        source: str,
        have_rights: object = False,
        job_slug: object = "episode",
        source_url: str = "",
        **kwargs: object,
    ) -> ComfyUiResult:
        """Ingest a local file or URL into ``dubs/<slug>/source.wav``.

        Args:
            source: Combo basename, ``(none)``, or path.
            have_rights: Rights attestation widget.
            job_slug: Job folder name.
            source_url: Optional http(s) override.
            **kwargs: Extra Comfy widget keys (ignored).

        Returns:
            ``job_id`` plus a short AUDIO preview (tensor/list, no torch
            import at load).
        """
        del kwargs
        slug = sanitize_slug(
            job_slug if isinstance(job_slug, str) else "episode"
        )
        dest = dub_dir(slug)
        try:
            resolved = resolve_media_source(source, source_url)
            dest, status = ingest(resolved, have_rights, slug)
        except RightsError as exc:
            record_ingest_failure(dest, "rights refused", str(exc))
            return {
                "ui": {"text": (str(exc),), "passthrough": ("rights refused",)},
                "result": (slug, empty_audio()),
            }
        except Exception as exc:  # noqa: BLE001 - fail-soft
            record_ingest_failure(dest, str(exc), str(exc))
            return {
                "ui": {"text": (str(exc),), "passthrough": (str(exc),)},
                "result": (slug, empty_audio()),
            }
        wav = dest / "source.wav"
        if wav.is_file():
            samples, rate = read_wav(wav)
            audio = audio_from_pcm(samples[: rate * 3] if samples else [0.0], rate)
        else:
            audio = empty_audio()
        return {
            "ui": {"text": (status,), "passthrough": (status,)},
            "result": (dest.name, audio),
        }


class EZDubScript:
    """Diarize + ASR + translate. Widget JSON is the human edit surface."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Comfy widget schema.

        Returns:
            Required script widgets plus optional ``job_id``.
        """
        return {
            "required": {
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": SEED_SCRIPT,
                        "dynamicPrompts": False,
                        "tooltip": "The transcript this node rewrites: JSON "
                        "with one turn per spoken line, holding speaker, t0 "
                        "and t1 in seconds, text, and text_target. Edit "
                        "text_target between an analyze Queue and a render "
                        "Queue.",
                    },
                ),
                "enhance": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "label_on": "On",
                        "label_off": "Off",
                        "tooltip": "Off pins the JSON exactly as you typed it "
                        "and skips the on-box rewrite pass; on transcribes and "
                        "rewrites each line into text_target.",
                    },
                ),
                "target_language": (
                    list(TARGET_LANG_WIDGET),
                    {
                        "default": "es",
                        "tooltip": "Two-letter ISO code to dub into, es for "
                        "Spanish; a code outside the list falls back to es.",
                    },
                ),
                "source_language": (
                    list(SOURCE_LANG_WIDGET),
                    {
                        "default": "auto",
                        "tooltip": "Two-letter ISO code the source audio is "
                        "spoken in, or auto to detect it. Pin it, such as en, "
                        "when detection picks the wrong language.",
                    },
                ),
                "max_speakers": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 12,
                        "step": 1,
                        "tooltip": "Cap on how many distinct speakers the "
                        "diarizer may find, counted in whole people. 0 lets it "
                        "choose and caps at 8, so raise it to 4 only when "
                        "several voices blend into one.",
                    },
                ),
                "stage": (
                    list(STAGES),
                    {
                        "default": STAGE_ALL,
                        "tooltip": "all transcribes then clones, analyze stops "
                        "after the transcript so you can edit text_target, and "
                        "render skips transcribing and only mixes. First Queue "
                        "is all.",
                    },
                ),
            },
            "optional": {
                "job_id": (
                    "STRING",
                    {
                        "forceInput": True,
                        "dynamicPrompts": False,
                        "tooltip": "Wire the job_id out of Dub ingest so this "
                        "node edits that same dubs/<slug>/ job; unlinked it "
                        "uses the slug inside the JSON, else episode.",
                    },
                ),
            },
        }

    # Comfy node metadata (outputs, category, operator description).
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("script",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/dub"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Builds an editable translation JSON (diarize + ASR + on-box GGUF). "
        "Turn Rewrite translation off to pin widget text. Stage=render skips ASR."
    )

    def run(
        self,
        prompt: str,
        enhance: bool = True,
        target_language: str = "es",
        source_language: str = "auto",
        max_speakers: int = 0,
        stage: str = STAGE_ALL,
        job_id: str = "",
    ) -> ComfyUiResult:
        """Diarize, ASR, and translate into editable widget JSON.

        Args:
            prompt: Current widget JSON (pinned when enhance is off).
            enhance: When False, pin widget text and skip GGUF.
            target_language: ISO target.
            source_language: ISO source or ``auto``.
            max_speakers: Cluster cap; 0 means default.
            stage: ``all``, ``analyze``, or ``render``.
            job_id: Optional ingest slug.

        Returns:
            Packed script STRING plus Dub status.
        """
        widget = parse_payload(prompt)
        slug = sanitize_slug(job_id or widget.get("slug") or "episode")
        dest = dub_dir(slug)
        name = stage if stage in STAGES else STAGE_ALL
        tgt = target_language if target_language in LANG_CODES else "es"
        src = source_language if source_language in SOURCE_LANG_WIDGET else "auto"
        payload, reason = analyze_job(
            dest,
            target_language=tgt,
            source_language=src,
            max_speakers=int(max_speakers or 0),
            enhance=bool(enhance),
            stage=name,
            widget_payload=widget,
        )
        text = dumps_payload(payload)
        return _pack_text(text, reason or payload.get("status") or "")


class EZDubRender:
    """Clone, duration-lock, mix, SRT, disclosure sidecar."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Comfy widget schema.

        Returns:
            Required render widgets plus optional ``job_id``.
        """
        return {
            "required": {
                "script": (
                    "STRING",
                    {
                        "multiline": True,
                        "forceInput": True,
                        "dynamicPrompts": False,
                        "tooltip": "Wire the transcript JSON out of Dub "
                        "transcript and into here; this node only clones and "
                        "mixes, so it never transcribes again.",
                    },
                ),
                "engine": (
                    list(ENGINES),
                    {
                        "default": ENGINE_CHATTERBOX,
                        "tooltip": "Clone voice that speaks the dub: "
                        "chatterbox-ml is the shipped default, qwen3tts the "
                        "opt-in alternative. download-dub --tier clone "
                        "installs the first; the second needs download-podcast "
                        "--tier qwen3tts.",
                    },
                ),
                "keep_bed": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Keep the original bed under the gaps "
                        "between lines so the room tone carries; off leaves "
                        "those gaps silent.",
                    },
                ),
                "spoken_disclosure": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Overlay a localized AI-disclosure bumper "
                        "on the mix wav only; the written sidecar is there "
                        "either way. Off, and the mix starts on the first "
                        "spoken word.",
                    },
                ),
                "speed": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.5,
                        "max": 1.5,
                        "step": 0.05,
                        "tooltip": "Multiplier on the speaking rate, not a "
                        "length in seconds. 1.0 keeps the lab 1.25x "
                        "pitch-preserving lock, and a value above 1.0 is still "
                        "capped at that lock.",
                    },
                ),
                "cfg_weight": (
                    "FLOAT",
                    {
                        "default": -1.0,
                        "min": -1.0,
                        "max": 1.0,
                        "step": 0.05,
                        "tooltip": "Chatterbox guidance weight, 0.0 to 1.0: "
                        "-1 asks the engine, which lands on 0.3 for a "
                        "cross-language dub and 0.5 same-language. Raise it "
                        "toward 0.5 to keep more of the original accent; "
                        "qwen3tts ignores this knob.",
                    },
                ),
                "exaggeration": (
                    "FLOAT",
                    {
                        "default": 0.5,
                        "min": 0.25,
                        "max": 2.0,
                        "step": 0.05,
                        "tooltip": "Chatterbox expressiveness: 0.25 is flat, "
                        "0.5 neutral, 2.0 the most intense and the fastest. "
                        "qwen3tts ignores this knob.",
                    },
                ),
            },
            "optional": {
                "job_id": (
                    "STRING",
                    {
                        "forceInput": True,
                        "dynamicPrompts": False,
                        "tooltip": "Wire the job_id out of Dub ingest so the "
                        "mix lands in that same dubs/<slug>/ folder; unlinked "
                        "it writes to dubs/episode/.",
                    },
                ),
            },
        }

    # Comfy node metadata (outputs, category, operator description).
    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/dub"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Zero-shot clone (Chatterbox Multilingual V3 or Qwen3-TTS) with "
        "PerTh on. Cross-lang CFG auto is 0.3. Default speaking speed 1.0 uses "
        "the 1.25x pitch-preserving lock. Writes duration-locked YT WAV + "
        "SRT + disclosure sidecars. Spoken bumper (off by default) overlays "
        "the mix wav only. Off: mix starts on speech; YT wav stays source-timed."
    )

    def run(
        self,
        script: str,
        engine: str = ENGINE_CHATTERBOX,
        keep_bed: bool = True,
        spoken_disclosure: bool = False,
        speed: float = 1.0,
        cfg_weight: float | None = -1.0,
        exaggeration: float = 0.5,
        job_id: str = "",
    ) -> ComfyUiResult:
        """Clone, duration-lock, and mix.

        Args:
            script: Translation JSON from EZDubScript.
            engine: Clone engine id.
            keep_bed: Keep source in non-speech gaps.
            spoken_disclosure: Overlay a localized bumper on the mix wav.
            speed: Fit ceiling. ``1.0`` uses the lab 1.25x lock.
            cfg_weight: Chatterbox CFG; ``< 0`` means auto.
            exaggeration: Chatterbox exaggeration.
            job_id: Optional ingest slug.

        Returns:
            Packed AUDIO mix (tensor/list, no torch import at load).
        """
        payload = parse_payload(script)
        if payload.get("stage") == STAGE_ANALYZE:
            return _pack_audio([], SAMPLE_RATE, "analyze only - set Stage to render")
        slug = sanitize_slug(job_id or "episode")
        dest = dub_dir(slug)
        wav = dest / "source.wav"
        if not wav.is_file():
            return _pack_audio([], SAMPLE_RATE, missing_source_status(dest))
        samples, rate = read_wav(wav)
        mix, rate, status = render_mix(
            samples,
            rate,
            payload,
            dest,
            engine=engine if engine in ENGINES else ENGINE_CHATTERBOX,
            keep_bed=bool(keep_bed),
            spoken_disclosure=bool(spoken_disclosure),
            speed=float(speed) if speed else 1.0,
            exaggeration=float(exaggeration) if exaggeration else 0.5,
            cfg_weight=float(cfg_weight) if cfg_weight is not None else -1.0,
        )
        return _pack_audio(mix, rate, status)

    def _overlay_disclosure(
        self,
        samples: list[float],
        rate: int,
        engine: str,
        language: str = "es",
        ref_wav: str = "",
        turns: Sequence[Mapping[str, JsonScalar]] | None = None,
    ) -> tuple[list[float], str]:
        """Overlay a localized bumper without changing duration (mix wav only).

        Args:
            samples: Mix PCM.
            rate: Sample rate.
            engine: Clone engine id.
            language: Target language for the bumper.
            ref_wav: Speaker reference path.
            turns: JSON turns (leading gap).

        Returns:
            ``(mix, status)`` with unchanged length.
        """
        return apply_spoken_disclosure(
            samples,
            rate,
            language=language,
            engine=engine if engine in ENGINES else ENGINE_CHATTERBOX,
            ref_wav=ref_wav,
            turns=turns or [],
            synthesize=synthesize_turn,
        )


# Comfy pack registry.
NODE_CLASS_MAPPINGS: NodeRegistry = {
    "EZDubIngest": EZDubIngest,
    "EZDubScript": EZDubScript,
    "EZDubRender": EZDubRender,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EZDubIngest": "Dub ingest (file or URL)",
    "EZDubScript": "Dub transcript + translate",
    "EZDubRender": "Dub clone + mix",
}
