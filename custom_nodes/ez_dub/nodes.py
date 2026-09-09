"""ComfyUI nodes for US-safe multi-speaker clone-and-translate dubs."""

from __future__ import annotations

from typing import Any

from .align import SAMPLE_RATE, fit_turn
from .audio import audio_from_pcm, empty_audio, read_wav
from .jobstore import dub_dir, output_root, sanitize_slug
from .pipeline import (
    DISCLOSURE_TEXT,
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
    ingest,
    render_mix,
    resolve_media_source,
    source_combo_options,
    synthesize_turn,
)
from .rights import RightsError
from .turns import dumps_payload, parse_payload

SEED_TURNS = [
    {
        "id": 1,
        "speaker": "spk00",
        "t0": 0.4,
        "t1": 2.8,
        "text": "Welcome back to the tape.",
        "text_target": "Bienvenidos de nuevo a la cinta.",
        "overlap": False,
        "rms": 0.1,
    },
    {
        "id": 2,
        "speaker": "spk01",
        "t0": 3.0,
        "t1": 6.2,
        "text": "Today we stay on the match in front of us.",
        "text_target": "Hoy nos quedamos en el partido que tenemos delante.",
        "overlap": False,
        "rms": 0.1,
    },
]
SEED_SCRIPT = dumps_payload(
    {
        "target_language": "es",
        "source_language": "en",
        "stage": STAGE_ALL,
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
        try:
            resolved = resolve_media_source(source, source_url)
            dest, status = ingest(resolved, have_rights, slug)
        except RightsError as exc:
            return {
                "ui": {"text": (str(exc),), "passthrough": ("rights refused",)},
                "result": ("", empty_audio()),
            }
        except Exception as exc:  # noqa: BLE001 — fail-soft
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
                "stage": (list(STAGES), {"default": STAGE_ALL}),
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
        stage=STAGE_ALL,
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
                "spoken_disclosure": ("BOOLEAN", {"default": True}),
                "speed": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 1.5, "step": 0.05},
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
        "PerTh on. Writes duration-locked WAV + SRT + disclosure.txt."
    )

    def run(
        self,
        script,
        engine=ENGINE_CHATTERBOX,
        keep_bed=True,
        spoken_disclosure=True,
        speed=1.0,
        job_id="",
    ):
        payload = parse_payload(script)
        if payload.get("stage") == STAGE_ANALYZE:
            return _pack_audio([], SAMPLE_RATE, "analyze only — set Stage to render")
        slug = sanitize_slug(job_id or "episode")
        dest = dub_dir(slug)
        wav = dest / "source.wav"
        if not wav.is_file():
            return _pack_audio([], SAMPLE_RATE, "missing source.wav")
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
        )
        if spoken_disclosure:
            self._overlay_disclosure(mix, rate, engine)
            from .audio import write_wav

            write_wav(dest / "ez_dub_mix.wav", mix, rate)
            write_wav(dest / "ez_dub_yt.wav", mix, rate)
            status = (status + "; spoken disclosure") if status else "spoken disclosure"
        return _pack_audio(mix, rate, status)

    def _overlay_disclosure(
        self,
        samples: list[float],
        rate: int,
        engine: str,
    ) -> None:
        """Fit a 3 s spoken bumper over the start without changing duration."""
        bumper, sr = synthesize_turn(
            DISCLOSURE_TEXT,
            "en",
            "",
            engine if engine in ENGINES else ENGINE_CHATTERBOX,
        )
        if not bumper:
            return
        if sr != rate:
            from .align import resample_linear

            bumper = resample_linear(bumper, int(round(len(bumper) * rate / max(sr, 1))))
        fitted, _flags = fit_turn(bumper, rate, 3.0, spill_s=0.0)
        fade = max(1, int(rate * 0.03))
        for i, sample in enumerate(fitted):
            if i >= len(samples):
                break
            gain = 1.0
            if i < fade:
                gain = i / fade
            remain = len(fitted) - 1 - i
            if remain < fade:
                gain = min(gain, remain / fade if fade else 1.0)
            samples[i] = samples[i] * (1.0 - gain) + sample * gain


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
