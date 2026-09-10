"""Stdlib WAV I/O and Comfy AUDIO packing. Torch is lazy."""

from __future__ import annotations

import struct
import wave
from pathlib import Path
from typing import Any

from .align import SAMPLE_RATE


def write_wav(path: Path | str, samples: list[float], rate: int) -> None:
    """Write mono 16-bit PCM WAV."""
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    sr = int(rate) or SAMPLE_RATE
    frames = bytearray()
    for value in samples:
        clipped = max(-1.0, min(1.0, float(value)))
        frames.extend(struct.pack("<h", int(clipped * 32767.0)))
    with wave.open(str(dest), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sr)
        handle.writeframes(bytes(frames))


def read_wav(path: Path | str) -> tuple[list[float], int]:
    """Read a WAV as mono float32-range samples.

    Arguments:
        path: Existing wav path.
    Returns:
        ``(samples, sample_rate)``. Multi-channel files are averaged.
    """
    with wave.open(str(path), "rb") as handle:
        channels = handle.getnchannels() or 1
        width = handle.getsampwidth()
        rate = handle.getframerate() or SAMPLE_RATE
        nframes = handle.getnframes()
        raw = handle.readframes(nframes)
    ints: list[int]
    if width == 2:
        count = len(raw) // 2
        unpacked = struct.unpack("<" + "h" * count, raw[: count * 2])
        ints = [int(v) for v in unpacked]
        scale = 32768.0
    elif width == 1:
        ints = [int(b) - 128 for b in raw]
        scale = 128.0
    else:
        # 24/32-bit: take little-endian 16-bit of each frame as a fallback.
        step = width
        ints = []
        for i in range(0, len(raw) - 1, step):
            ints.append(int(struct.unpack_from("<h", raw, i)[0]))
        scale = 32768.0
    if channels <= 1:
        return [float(v) / scale for v in ints], int(rate)
    mono: list[float] = []
    for i in range(0, len(ints) - channels + 1, channels):
        acc = 0.0
        for c in range(channels):
            acc += float(ints[i + c])
        mono.append(acc / channels / scale)
    return mono, int(rate)


def empty_audio(sample_rate: int = SAMPLE_RATE) -> dict[str, Any]:
    """Minimal AUDIO dict without importing torch at module load."""
    try:
        import torch

        wave_t = torch.zeros(1, 1, 1)
        return {"waveform": wave_t, "sample_rate": int(sample_rate)}
    except Exception:  # noqa: BLE001 — hermetic tests have no torch
        return {"waveform": [[[0.0]]], "sample_rate": int(sample_rate)}


def audio_from_pcm(samples: Any, sample_rate: int) -> dict[str, Any]:
    """Pack a 1-D PCM sequence as Comfy AUDIO."""
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
