"""Loop a short instrumental bed under a longer speech stem.

Torch stays lazy. Hermetic tests pass nested-list AUDIO dicts.
"""

from __future__ import annotations

from typing import Any

# Fallback sample rate when an AUDIO dict omits it (Kokoro default).
DEFAULT_SAMPLE_RATE = 24000


def _as_pcm(waveform: Any) -> list[float]:
    """Flatten a Comfy waveform to a 1-D float list.

    Args:
        waveform: Torch tensor, numpy array, or nested lists.

    Returns:
        PCM samples.
    """
    if waveform is None:
        return []
    if hasattr(waveform, "detach") and hasattr(waveform, "cpu"):
        waveform = waveform.detach().cpu()
    if hasattr(waveform, "numpy"):
        try:
            waveform = waveform.numpy()
        except Exception:  # noqa: BLE001 — keep walking
            pass
    if hasattr(waveform, "reshape"):
        try:
            return [float(x) for x in waveform.reshape(-1).tolist()]
        except Exception:  # noqa: BLE001 — fall through
            pass
    if isinstance(waveform, (int, float)):
        return [float(waveform)]
    if isinstance(waveform, (list, tuple)):
        out: list[float] = []
        for item in waveform:
            out.extend(_as_pcm(item))
        return out
    try:
        return [float(waveform)]
    except (TypeError, ValueError):
        return []


def _sample_rate(audio: object) -> int:
    """Read sample_rate from an AUDIO dict.

    Args:
        audio: Comfy AUDIO mapping.

    Returns:
        Positive sample rate.
    """
    if isinstance(audio, dict):
        raw = audio.get("sample_rate", DEFAULT_SAMPLE_RATE)
        try:
            rate = int(raw)
        except (TypeError, ValueError):
            rate = DEFAULT_SAMPLE_RATE
        if rate > 0:
            return rate
    return DEFAULT_SAMPLE_RATE


def _waveform(audio: object) -> Any:
    """Return the waveform payload from an AUDIO dict.

    Args:
        audio: Comfy AUDIO mapping.

    Returns:
        Waveform object, or None.
    """
    if isinstance(audio, dict):
        return audio.get("waveform")
    return None


def pack_audio(samples: list[float], sample_rate: int) -> dict[str, Any]:
    """Pack PCM into a Comfy AUDIO dict. Torch is imported here only.

    Args:
        samples: 1-D PCM.
        sample_rate: Waveform sample rate.

    Returns:
        ``{"waveform", "sample_rate"}``.
    """
    rate = int(sample_rate) if int(sample_rate) > 0 else DEFAULT_SAMPLE_RATE
    body = samples if samples else [0.0]
    try:
        import torch

        tensor = torch.as_tensor(body, dtype=torch.float32)
        if tensor.ndim == 1:
            tensor = tensor.unsqueeze(0).unsqueeze(0)
        elif tensor.ndim == 2:
            tensor = tensor.unsqueeze(0)
        return {"waveform": tensor, "sample_rate": rate}
    except Exception:  # noqa: BLE001 — hermetic tests have no torch
        return {"waveform": [[[float(x) for x in body]]], "sample_rate": rate}


def loop_to_match(speech: object, bed: object) -> dict[str, Any]:
    """Repeat ``bed`` until it covers ``speech``, then trim.

    Args:
        speech: Speech AUDIO (length target).
        bed: Short instrumental AUDIO.

    Returns:
        Looped (or silent) bed AUDIO at the speech sample rate.
        Empty speech returns empty audio.
    """
    speech_pcm = _as_pcm(_waveform(speech))
    rate = _sample_rate(speech) or _sample_rate(bed)
    if not speech_pcm:
        return pack_audio([], rate)
    target = len(speech_pcm)
    bed_pcm = _as_pcm(_waveform(bed))
    if not bed_pcm:
        return pack_audio([0.0] * target, rate)
    if len(bed_pcm) >= target:
        return pack_audio(bed_pcm[:target], rate)
    loops = (target + len(bed_pcm) - 1) // len(bed_pcm)
    out: list[float] = []
    for _ in range(loops):
        out.extend(bed_pcm)
        if len(out) >= target:
            break
    return pack_audio(out[:target], rate)
