"""ComfyUI nodes for US-safe multi-speaker clone-and-translate dubs."""

from __future__ import annotations

from typing import Any

from .align import SAMPLE_RATE
from .audio import audio_from_pcm, empty_audio, read_wav
from .jobstore import dub_dir, record_ingest_failure, sanitize_slug
from .pipeline import (
    DISCLOSURE_TEXT,  # noqa: F401 — re-exported for tests and graph builder
    ENGINE_CHATTERBOX,
    ENGINES,
    LANG_CODES,
    SOURCE_LANG_WIDGET,
    SOURCE_NONE,
    STAGE_ALL,
    STAGE_ANALYZE,
    STAGE_RENDER,
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
from .turns import dumps_payload, parse_payload

SEED_TURNS: list[dict[str, Any]] = []
SEED_SCRIPT = dumps_payload(
    {
        "target_language": "es",
        "source_language": "auto",
        "stage": STAGE_ANALYZE,
        "status": "",
        "turns": SEED_TURNS,
    }
)


def _pack_text(text: str, status: str) -> dict:
    return {
        "ui": {"text": (text,), "passthrough": (status,)},
        "result": (text,),
    }


def _pack_audio(samples: Any, rate: int, status: str) -> dict:
    audio = audio_from_pcm(samples, rate) if samples else empty_audio(rate)
    return {
        "ui": {"text": (status,), "passthrough": (status,)},
        "result": (audio,),
    }


class EZDubIngest:
    """Local file or URL ingest. Refuses Queue without rights."""

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {
            "required": {
                "source": (source_combo_options(), {"default": SOURCE_NONE}),
                "have_rights": ("BOOLEAN", {"default": False}),
                "job_slug": (
                    "STRING",
                    {"default": "episode", "dynamicPrompts": False},
                ),
                "source_url": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                        "dynamicPrompts": False,
                    },
                ),
            }
        }

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

    def run(self, source, have_rights=False, job_slug="episode", source_url=""):
        slug = sanitize_slug(job_slug)
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
        except Exception as exc:  # noqa: BLE001 — fail-soft
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
    def INPUT_TYPES(cls) -> dict:
        return {
            "required": {
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": SEED_SCRIPT,
                        "dynamicPrompts": False,
                    },
                ),
                "enhance": (
                    "BOOLEAN",
                    {"default": True, "label_on": "On", "label_off": "Off"},
                ),
                "target_language": (list(TARGET_LANG_WIDGET), {"default": "es"}),
                "source_language": (list(SOURCE_LANG_WIDGET), {"default": "auto"}),
                "max_speakers": (
                    "INT",
                    {"default": 0, "min": 0, "max": 12, "step": 1},
                ),
                "stage": (list(STAGES), {"default": STAGE_ANALYZE}),
            },
            "optional": {
                "job_id": (
                    "STRING",
                    {"forceInput": True, "dynamicPrompts": False},
                ),
            },
        }

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
        prompt,
        enhance=True,
        target_language="es",
        source_language="auto",
        max_speakers=0,
        stage=STAGE_ANALYZE,
        job_id="",
    ):
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
    def INPUT_TYPES(cls) -> dict:
        return {
            "required": {
                "script": (
                    "STRING",
                    {"multiline": True, "forceInput": True, "dynamicPrompts": False},
                ),
                "engine": (list(ENGINES), {"default": ENGINE_CHATTERBOX}),
                "keep_bed": ("BOOLEAN", {"default": True}),
                "spoken_disclosure": ("BOOLEAN", {"default": False}),
                "speed": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 1.5, "step": 0.05},
                ),
                "cfg_weight": (
                    "FLOAT",
                    {
                        "default": -1.0,
                        "min": -1.0,
                        "max": 1.0,
                        "step": 0.05,
                    },
                ),
                "exaggeration": (
                    "FLOAT",
                    {
                        "default": 0.5,
                        "min": 0.25,
                        "max": 2.0,
                        "step": 0.05,
                    },
                ),
            },
            "optional": {
                "job_id": (
                    "STRING",
                    {"forceInput": True, "dynamicPrompts": False},
                ),
            },
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/dub"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Zero-shot clone (Chatterbox Multilingual V3 or Qwen3-TTS) with "
        "PerTh on. Cross-lang CFG auto is 0. Writes duration-locked YT WAV + "
        "SRT + disclosure sidecars. Spoken bumper (off by default) overlays "
        "the mix wav only."
    )

    def run(
        self,
        script,
        engine=ENGINE_CHATTERBOX,
        keep_bed=True,
        spoken_disclosure=False,
        speed=1.0,
        cfg_weight=-1.0,
        exaggeration=0.5,
        job_id="",
    ):
        payload = parse_payload(script)
        if payload.get("stage") == STAGE_ANALYZE:
            return _pack_audio([], SAMPLE_RATE, "analyze only — set Stage to render")
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
        turns: list[dict[str, Any]] | None = None,
    ) -> tuple[list[float], str]:
        """Overlay a localized bumper without changing duration (mix wav only)."""
        return apply_spoken_disclosure(
            samples,
            rate,
            language=language,
            engine=engine if engine in ENGINES else ENGINE_CHATTERBOX,
            ref_wav=ref_wav,
            turns=turns or [],
            synthesize=synthesize_turn,
        )


NODE_CLASS_MAPPINGS: dict[str, Any] = {
    "EZDubIngest": EZDubIngest,
    "EZDubScript": EZDubScript,
    "EZDubRender": EZDubRender,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EZDubIngest": "Dub ingest (file or URL)",
    "EZDubScript": "Dub transcript + translate",
    "EZDubRender": "Dub clone + mix",
}
