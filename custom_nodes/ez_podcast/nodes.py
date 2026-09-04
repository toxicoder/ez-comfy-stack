"""ComfyUI nodes for US-safe local podcast script, disclosure, and TTS."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
DISCLOSURE_TEXT = (
    "Voices and music on this show are synthesized. The hosts are original "
    "characters, not recordings of real people."
)
SEED_SCRIPT = (
    "Speaker A: Welcome back to Local Signal. Today we stay on the machine in front of us.\n"
    "Speaker B: No cloud voices. No rented music. If the card dies, the show dies with it.\n"
    "Speaker A: That is the point. A small studio should own the weights and the cuts.\n"
    "Speaker B: Edit the script before you generate speech. The edit is the human part."
)
RADIO_SEED_SCRIPT = (
    "Announcer: Tonight on the machine-only hour: a story that never left the rack.\n"
    "Speaker A: The transmitter light is steady. We do not borrow a voice from the wire.\n"
    "Speaker B: If the card goes dark, the play ends. That is the bargain.\n"
    "Speaker A: Then say the line like you mean the cut, not the cloud.\n"
    "Speaker B: Cue the bed. Keep it instrumental. We own the silence between words.\n"
    "Announcer: End of scene. The hosts are invented. The mix is local."
)
FLAVOR_PODCAST = "podcast_two_host"
FLAVOR_RADIO = "radio_drama"
FLAVORS = (FLAVOR_PODCAST, FLAVOR_RADIO)
BACKEND_KOKORO = "kokoro"
BACKEND_CHATTERBOX = "chatterbox"
BACKEND_QWEN3TTS = "qwen3tts"
BACKENDS = (BACKEND_KOKORO, BACKEND_CHATTERBOX, BACKEND_QWEN3TTS)
KOKORO_VOICES = (
    "af_heart",
    "af_bella",
    "af_nicole",
    "af_sarah",
    "am_adam",
    "am_michael",
    "bf_emma",
    "bm_george",
    "bm_lewis",
)
DEFAULT_VOICE_A = "af_heart"
DEFAULT_VOICE_B = "am_michael"
DEFAULT_ANNOUNCER = "bm_george"
KOKORO_ONNX_NAME = "kokoro-v1.0.onnx"
KOKORO_VOICES_NAME = "voices-v1.0.bin"
SPEAKER_LINE = re.compile(
    r"^(Speaker A|Speaker B|Announcer)\s*:\s*(.+)$",
    re.IGNORECASE,
)
SAMPLE_RATE_KOKORO = 24000


def _log(message: str) -> None:
    print(f"[ez_podcast] {message}", file=sys.stderr)


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def load_writer_prompt(flavor: str) -> str:
    """Load a named writer system prompt from this pack.

    Arguments:
        flavor: ``podcast_two_host`` or ``radio_drama``.
    Returns:
        File contents stripped of trailing whitespace.
    Raises:
        FileNotFoundError if the prompt file is missing.
    """
    name = flavor if flavor in FLAVORS else FLAVOR_PODCAST
    path = PROMPTS_DIR / f"{name}.txt"
    return path.read_text(encoding="utf-8").strip()


def prepend_disclosure(script: str) -> str:
    """Put the fixed bumper on the first spoken line.

    Arguments:
        script: Operator or writer text (Speaker A/B lines).
    Returns:
        Disclosure paragraph, blank line, then the script. If the script
        already starts with the bumper, return it unchanged.
    """
    body = script if isinstance(script, str) else str(script or "")
    stripped = body.strip()
    if stripped.startswith(DISCLOSURE_TEXT):
        return stripped
    if not stripped:
        return DISCLOSURE_TEXT
    return f"{DISCLOSURE_TEXT}\n\n{stripped}"


def parse_speaker_turns(script: str) -> list[tuple[str, str]]:
    """Split a script into (role, text) turns.

    Arguments:
        script: Multiline Speaker A/B / Announcer lines.
    Returns:
        List of ``(speaker_a|speaker_b|announcer, spoken text)``.
        Unlabeled leftover lines attach to the previous turn, or to
        speaker_a when no turn has started.
    """
    text = script if isinstance(script, str) else str(script or "")
    turns: list[tuple[str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        match = SPEAKER_LINE.match(line)
        if match:
            role = match.group(1).strip().lower().replace(" ", "_")
            if role == "speaker_a":
                key = "speaker_a"
            elif role == "speaker_b":
                key = "speaker_b"
            else:
                key = "announcer"
            spoken = match.group(2).strip()
            if spoken:
                turns.append((key, spoken))
            continue
        if turns:
            prev_role, prev_text = turns[-1]
            turns[-1] = (prev_role, f"{prev_text} {line}")
        else:
            turns.append(("speaker_a", line))
    return turns


def resolve_tts_backend(backend: object, ref_a: object = "", ref_b: object = "") -> str:
    """Pick a backend. Empty operator refs always fall back to Kokoro built-ins.

    Arguments:
        backend: Requested id (kokoro / chatterbox / qwen3tts).
        ref_a: Optional owned reference path for speaker A.
        ref_b: Optional owned reference path for speaker B.
    Returns:
        One of BACKENDS. Unknown values become kokoro. Chatterbox and
        Qwen3-TTS without both refs become kokoro (no celebrity defaults).
    """
    raw = backend if isinstance(backend, str) else str(backend or BACKEND_KOKORO)
    name = raw.strip().lower() or BACKEND_KOKORO
    if name not in BACKENDS:
        return BACKEND_KOKORO
    if name == BACKEND_KOKORO:
        return BACKEND_KOKORO
    path_a = (ref_a if isinstance(ref_a, str) else str(ref_a or "")).strip()
    path_b = (ref_b if isinstance(ref_b, str) else str(ref_b or "")).strip()
    if not path_a and not path_b:
        return BACKEND_KOKORO
    return name


def _model_roots() -> list[str]:
    roots: list[str] = []
    for key in ("MODELS_ROOT", "MODELS_DIR"):
        value = (os.environ.get(key) or "").strip()
        if value and value not in roots:
            roots.append(value)
    for fallback in ("/models", "/mnt/models"):
        if fallback not in roots:
            roots.append(fallback)
    return roots


def resolve_kokoro_paths() -> tuple[str, str]:
    """First existing Kokoro ONNX + voices pair under comfy/onnx and comfy/tts.

    Returns:
        ``(onnx_path, voices_path)``. Missing files still return the first
        candidate so logs can name the expected location.
    """
    onnx_candidates: list[str] = []
    voice_candidates: list[str] = []
    for root in _model_roots():
        onnx_candidates.extend(
            [
                f"{root}/comfy/onnx/{KOKORO_ONNX_NAME}",
                f"{root}/comfy/tts/{KOKORO_ONNX_NAME}",
                f"{root}/onnx/{KOKORO_ONNX_NAME}",
            ]
        )
        voice_candidates.extend(
            [
                f"{root}/comfy/tts/{KOKORO_VOICES_NAME}",
                f"{root}/comfy/onnx/{KOKORO_VOICES_NAME}",
                f"{root}/tts/{KOKORO_VOICES_NAME}",
            ]
        )
    onnx = next((p for p in onnx_candidates if os.path.isfile(p)), onnx_candidates[0])
    voices = next((p for p in voice_candidates if os.path.isfile(p)), voice_candidates[0])
    return onnx, voices


def _pack_text(text: str, status: str) -> dict:
    return {
        "ui": {"text": (text,), "passthrough": (status,)},
        "result": (text,),
    }


def _empty_audio(sample_rate: int = SAMPLE_RATE_KOKORO) -> dict[str, Any]:
    """Minimal AUDIO dict without importing torch at module load."""
    try:
        import torch

        wave = torch.zeros(1, 1, 1)
        return {"waveform": wave, "sample_rate": int(sample_rate)}
    except Exception:  # noqa: BLE001 — hermetic tests have no torch
        return {"waveform": [[[0.0]]], "sample_rate": int(sample_rate)}


def _audio_from_pcm(samples: Any, sample_rate: int) -> dict[str, Any]:
    try:
        import torch

        tensor = torch.as_tensor(samples, dtype=torch.float32)
        if tensor.ndim == 1:
            tensor = tensor.unsqueeze(0).unsqueeze(0)
        elif tensor.ndim == 2:
            tensor = tensor.unsqueeze(0)
        return {"waveform": tensor, "sample_rate": int(sample_rate)}
    except Exception:  # noqa: BLE001 — fail-soft without torch
        return {"waveform": samples, "sample_rate": int(sample_rate)}


def _concat_pcm(chunks: list[Any]) -> Any:
    if not chunks:
        return [0.0]
    try:
        import numpy as np

        return np.concatenate([np.asarray(c, dtype="float32").reshape(-1) for c in chunks])
    except Exception:  # noqa: BLE001
        out: list[float] = []
        for chunk in chunks:
            if hasattr(chunk, "tolist"):
                out.extend(float(x) for x in chunk.tolist())
            else:
                out.extend(float(x) for x in list(chunk))
        return out


class EZPodcastScript:
    """Draft Speaker A/B lines via the on-box GGUF. Enhance defaults off."""

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
                "enhance": ("BOOLEAN", {"default": False}),
                "flavor": ([FLAVOR_PODCAST, FLAVOR_RADIO], {"default": FLAVOR_PODCAST}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("script",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/podcast"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Rewrites a two-host or radio-drama script with the on-box "
        "Qwen3-4B-Instruct GGUF. Enhance defaults off so Queue works offline. "
        "Missing GGUF passes the widget text through. Unloads the writer "
        "after a rewrite so TTS can run in the same Queue."
    )

    def run(self, prompt, enhance, flavor=FLAVOR_PODCAST):
        original = prompt if isinstance(prompt, str) else str(prompt)
        name = flavor if flavor in FLAVORS else FLAVOR_PODCAST
        if not _as_bool(enhance):
            return _pack_text(original, "enhance off")
        try:
            from ez_prompt_enhance.client import _close_llm
            from ez_prompt_enhance.client import complete
        except Exception as exc:  # noqa: BLE001 — fail-soft
            _log(f"prompt enhance client unavailable: {exc}")
            return _pack_text(original, "llama.cpp unavailable")
        system = load_writer_prompt(name)
        try:
            rewritten, reason = complete(system, original)
        finally:
            try:
                _close_llm()
            except Exception as exc:  # noqa: BLE001 — unload is best-effort
                _log(f"writer unload failed: {exc}")
        if not (rewritten or "").strip():
            return _pack_text(original, reason or "passthrough")
        return _pack_text(rewritten, "")


class EZPodcastDisclosure:
    """Fixed spoken bumper. Operators cannot edit the disclosure string."""

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {
            "required": {
                "script": (
                    "STRING",
                    {"multiline": True, "forceInput": True, "dynamicPrompts": False},
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("script",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/podcast"
    DESCRIPTION = (
        "Prepends the fixed line: Voices and music on this show are "
        "synthesized. The hosts are original characters, not recordings of "
        "real people."
    )

    def run(self, script):
        text = prepend_disclosure(script)
        return (text,)


class EZKokoroTTS:
    """Two-host (plus optional announcer) TTS. Kokoro built-ins by default."""

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        voices = list(KOKORO_VOICES)
        return {
            "required": {
                "script": (
                    "STRING",
                    {"multiline": True, "forceInput": True, "dynamicPrompts": False},
                ),
                "speaker_a_voice": (voices, {"default": DEFAULT_VOICE_A}),
                "speaker_b_voice": (voices, {"default": DEFAULT_VOICE_B}),
                "announcer_voice": (voices, {"default": DEFAULT_ANNOUNCER}),
                "include_announcer": ("BOOLEAN", {"default": False}),
                "backend": (list(BACKENDS), {"default": BACKEND_KOKORO}),
                "speaker_a_ref": (
                    "STRING",
                    {"default": "", "dynamicPrompts": False},
                ),
                "speaker_b_ref": (
                    "STRING",
                    {"default": "", "dynamicPrompts": False},
                ),
                "speed": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.5, "max": 1.5, "step": 0.05},
                ),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/podcast"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Kokoro-82M ONNX/CPU built-in voices (Apache 2.0). Optional "
        "Chatterbox or Qwen3-TTS only with operator-owned refs; empty refs "
        "fall back to Kokoro. Never ships celebrity WAVs."
    )

    def run(
        self,
        script,
        speaker_a_voice=DEFAULT_VOICE_A,
        speaker_b_voice=DEFAULT_VOICE_B,
        announcer_voice=DEFAULT_ANNOUNCER,
        include_announcer=False,
        backend=BACKEND_KOKORO,
        speaker_a_ref="",
        speaker_b_ref="",
        speed=1.0,
    ):
        chosen = resolve_tts_backend(backend, speaker_a_ref, speaker_b_ref)
        turns = parse_speaker_turns(script)
        if not _as_bool(include_announcer):
            turns = [(role, text) for role, text in turns if role != "announcer"]
        if not turns:
            _log("no speaker turns in script")
            return (_empty_audio(),)
        voice_map = {
            "speaker_a": speaker_a_voice or DEFAULT_VOICE_A,
            "speaker_b": speaker_b_voice or DEFAULT_VOICE_B,
            "announcer": announcer_voice or DEFAULT_ANNOUNCER,
        }
        if chosen != BACKEND_KOKORO:
            _log(
                f"{chosen} requested with operator refs; analog path still "
                "uses Kokoro when extras are missing"
            )
        chunks: list[Any] = []
        rate = SAMPLE_RATE_KOKORO
        for role, spoken in turns:
            pcm, rate = self._synthesize_turn(
                spoken,
                voice_map.get(role, DEFAULT_VOICE_A),
                chosen,
                float(speed) if speed else 1.0,
                speaker_a_ref if role == "speaker_a" else speaker_b_ref,
            )
            if pcm is not None:
                chunks.append(pcm)
        if not chunks:
            return (_empty_audio(rate),)
        return (_audio_from_pcm(_concat_pcm(chunks), rate),)

    def _synthesize_turn(
        self,
        text: str,
        voice: str,
        backend: str,
        speed: float,
        ref_wav: object,
    ) -> tuple[Any | None, int]:
        if backend in {BACKEND_CHATTERBOX, BACKEND_QWEN3TTS}:
            pcm = self._try_optional_backend(text, backend, ref_wav)
            if pcm is not None:
                return pcm, SAMPLE_RATE_KOKORO
        return self._synthesize_kokoro(text, voice, speed)

    def _try_optional_backend(
        self, text: str, backend: str, ref_wav: object
    ) -> Any | None:
        path = (ref_wav if isinstance(ref_wav, str) else str(ref_wav or "")).strip()
        if not path:
            return None
        _log(f"{backend} extra not used without a runtime install; falling back to Kokoro")
        return None

    def _synthesize_kokoro(
        self, text: str, voice: str, speed: float
    ) -> tuple[Any | None, int]:
        onnx, voices = resolve_kokoro_paths()
        if not os.path.isfile(onnx) or not os.path.isfile(voices):
            _log(
                f"Kokoro ONNX missing ({onnx}, {voices}) — run "
                "./scripts/manage.sh download-podcast --tier analog"
            )
            return None, SAMPLE_RATE_KOKORO
        try:
            from kokoro_onnx import Kokoro
        except ImportError:
            _log(
                "kokoro-onnx not installed — optional runtime: pip install "
                "kokoro-onnx onnxruntime (invalidates a baked venv layer if you rebuild)"
            )
            return None, SAMPLE_RATE_KOKORO
        try:
            tts = Kokoro(onnx, voices)
            samples, rate = tts.create(text, voice=voice, speed=speed)
        except Exception as exc:  # noqa: BLE001 — fail-soft
            _log(f"Kokoro synthesis failed: {exc}")
            return None, SAMPLE_RATE_KOKORO
        return samples, int(rate or SAMPLE_RATE_KOKORO)


NODE_CLASS_MAPPINGS = {
    "EZPodcastScript": EZPodcastScript,
    "EZPodcastDisclosure": EZPodcastDisclosure,
    "EZKokoroTTS": EZKokoroTTS,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EZPodcastScript": "Podcast Script",
    "EZPodcastDisclosure": "Podcast Disclosure",
    "EZKokoroTTS": "Kokoro TTS (two-host)",
}
