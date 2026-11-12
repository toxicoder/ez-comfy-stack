"""Deterministic ringtone synthesis in pure Python (stdlib only).

A motif is a tuple of ``(pitch, duration_s, velocity)`` steps; ``pitch``
``None`` is a rest. Rendering is integer-index math over a precomputed
additive wavetable, so the same inputs always produce bit-identical
samples - no numpy, no RNG, no clock. Encoding to WAV / AAC / Ogg is
:mod:`ez_tones.pack` work over ffmpeg.

No node classes here: other packs and the operator CLI import this
module directly.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal, TypeAlias

A4_MIDI = 69
"""MIDI note number tuned to :data:`A4_HZ`."""

A4_HZ = 440.0
"""Concert pitch in Hz (equal temperament)."""

DEFAULT_SAMPLE_RATE = 44100
"""Rate the exporter renders at when the operator does not pick one."""

ALLOWED_SAMPLE_RATES: tuple[int, ...] = (44100, 48000)
"""Sample rates Android tone packs are shipped at."""

PEAK_CEILING = 0.89
"""Normalisation target for a rendered motif, linear (about -1 dBFS)."""

FADE_MS = 6.0
"""Fade-in and fade-out ramp in ms; equal ramps leave a clean loop seam."""

WAVETABLE_LEN = 2048
"""Samples in one period of a precomputed additive waveform."""

DECAY_K = 4.0
"""Exponent of the decay stage: higher collapses the tail toward sustain."""

STEREO_SPREAD_MS = 0.7
"""Pre-delay of the right channel, ms, for a light stereo spread."""

NoteStep: TypeAlias = tuple[int | None, float, float]
"""One motif step: ``(pitch_or_None, duration_s, velocity)``."""

Motif: TypeAlias = tuple[NoteStep, ...]
"""A whole motif as an immutable step list."""

Timbre: TypeAlias = Literal[
    "sine", "bell", "pluck", "marimba", "glass", "woody", "synth"
]
"""Voiced waveforms the synthesiser knows."""


@dataclass(frozen=True)
class Voice:
    """Envelope shape and harmonic content of one timbre.

    Attributes:
        attack_ms: Linear attack ramp in ms.
        decay_ms: Exponential decay toward sustain, in ms.
        sustain: Level held between decay and release, 0..1.
        release_ms: Linear release to silence, in ms.
        harmonics: Relative amplitude of partials 1..N.
    """

    attack_ms: float
    decay_ms: float
    sustain: float
    release_ms: float
    harmonics: tuple[float, ...]


# Odd-only tables read as a soft square; a zero entry keeps a partial out
# without changing the partial index the rest of the list refers to.
_VOICES: dict[Timbre, Voice] = {
    "sine": Voice(4.0, 60.0, 0.55, 40.0, (1.0,)),
    "bell": Voice(1.0, 900.0, 0.02, 260.0, (1.0, 0.42, 0.30, 0.18, 0.11)),
    "pluck": Voice(1.0, 180.0, 0.05, 90.0, (1.0, 0.55, 0.28, 0.12, 0.05)),
    "marimba": Voice(2.0, 240.0, 0.10, 70.0, (1.0, 0.0, 0.22, 0.0, 0.06)),
    "glass": Voice(1.0, 700.0, 0.06, 220.0, (1.0, 0.0, 0.34, 0.0, 0.20, 0.0, 0.09)),
    "woody": Voice(3.0, 140.0, 0.08, 60.0, (1.0, 0.30, 0.0, 0.10, 0.0, 0.04)),
    "synth": Voice(8.0, 120.0, 0.62, 90.0, (1.0, 0.0, 0.55, 0.0, 0.33, 0.0, 0.20)),
}

TIMBRES: tuple[Timbre, ...] = tuple(_VOICES)
"""Every timbre :func:`render_motif` accepts."""


def midi_to_hz(pitch: int) -> float:
    """Equal-tempered frequency of one MIDI note.

    Args:
        pitch: MIDI note number (69 is A4).

    Returns:
        Frequency in Hz.
    """
    return A4_HZ * math.pow(2.0, (pitch - A4_MIDI) / 12.0)


def hz_to_midi(freq: float) -> int:
    """Nearest MIDI note for a frequency.

    Args:
        freq: Frequency in Hz.

    Returns:
        Rounded MIDI note number.

    Raises:
        ValueError: ``freq`` is not positive.
    """
    if freq <= 0.0:
        raise ValueError(f"freq must be > 0, got {freq}")
    return int(round(A4_MIDI + 12.0 * math.log2(freq / A4_HZ)))


def ms_to_samples(ms: float, sample_rate: int) -> int:
    """Convert a millisecond length to a whole sample count.

    Args:
        ms: Length in milliseconds.
        sample_rate: Samples per second.

    Returns:
        Sample count, never negative.
    """
    return max(0, int(round(ms * sample_rate / 1000.0)))


@lru_cache(maxsize=None)
def _wavetable(harmonics: tuple[float, ...]) -> tuple[float, ...]:
    """One period of an additive waveform, peak-normalised.

    Args:
        harmonics: Relative amplitude of partials 1..N.

    Returns:
        :data:`WAVETABLE_LEN` samples in ``[-1, 1]``.
    """
    table = [0.0] * WAVETABLE_LEN
    for order, amp in enumerate(harmonics, start=1):
        if amp == 0.0:
            continue
        step = 2.0 * math.pi * order / WAVETABLE_LEN
        for index in range(WAVETABLE_LEN):
            table[index] += amp * math.sin(step * index)
    peak = max(abs(value) for value in table)
    if peak > 0.0:
        return tuple(value / peak for value in table)
    return tuple(table)


def additive_wave(
    freq: float,
    harmonics: Sequence[float],
    count: int,
    sample_rate: int,
) -> list[float]:
    """Render a pitched additive tone with linear-interpolated wavetables.

    Args:
        freq: Fundamental in Hz.
        harmonics: Relative amplitude of partials 1..N.
        count: Samples to produce.
        sample_rate: Samples per second.

    Returns:
        ``count`` samples in ``[-1, 1]``; empty when ``count`` is not positive.

    Raises:
        ValueError: ``freq`` is not positive, or sits at or above Nyquist.
    """
    if count <= 0:
        return []
    if freq <= 0.0:
        raise ValueError(f"freq must be > 0, got {freq}")
    if freq * 2.0 >= sample_rate:
        raise ValueError(f"freq {freq} is at or above Nyquist for {sample_rate} Hz")
    table = _wavetable(tuple(harmonics))
    out = [0.0] * count
    last = WAVETABLE_LEN - 1
    phase_step = freq * WAVETABLE_LEN / sample_rate
    phase = 0.0
    for index in range(count):
        slot = int(phase)
        frac = phase - slot
        above = table[slot + 1] if slot < last else table[0]
        out[index] = table[slot] + frac * (above - table[slot])
        phase += phase_step
        if phase >= WAVETABLE_LEN:
            phase -= WAVETABLE_LEN
    return out


def adsr_envelope(
    count: int,
    sample_rate: int,
    attack_ms: float,
    decay_ms: float,
    sustain: float,
    release_ms: float,
) -> list[float]:
    """Build an attack / decay / sustain / release gain curve.

    A note too short to hold all three ramps gets one smooth arc, which is
    what keeps percussive steps click-free.

    Args:
        count: Samples the envelope covers.
        sample_rate: Samples per second.
        attack_ms: Linear attack ramp in ms.
        decay_ms: Exponential decay toward sustain, in ms.
        sustain: Held level, 0..1.
        release_ms: Linear release to silence, in ms.

    Returns:
        ``count`` gain values in ``[0, 1]``.
    """
    if count <= 0:
        return []
    attack = ms_to_samples(attack_ms, sample_rate)
    decay = ms_to_samples(decay_ms, sample_rate)
    release = ms_to_samples(release_ms, sample_rate)
    if attack + decay + release >= count:
        return [math.sin(math.pi * (index + 0.5) / count) for index in range(count)]
    level = min(max(sustain, 0.0), 1.0)
    out = [0.0] * count
    for index in range(attack):
        out[index] = (index + 1) / (attack + 1)
    for index in range(decay):
        ramp = (index + 1) / decay
        out[attack + index] = level + (1.0 - level) * math.exp(-DECAY_K * ramp)
    hold = count - attack - decay - release
    body = level + (1.0 - level) * math.exp(-DECAY_K)
    for index in range(hold):
        out[attack + decay + index] = body
    tail = attack + decay + hold
    for index in range(release):
        out[tail + index] = body * (1.0 - (index + 1) / (release + 1))
    return out


def voice_for(timbre: Timbre) -> Voice:
    """Look up the envelope and harmonics of one timbre.

    Args:
        timbre: Timbre name.

    Returns:
        The :class:`Voice` that renders it.

    Raises:
        ValueError: ``timbre`` is not one of :data:`TIMBRES`.
    """
    voice = _VOICES.get(timbre)
    if voice is None:
        raise ValueError(f"unknown timbre {timbre!r} (use one of {TIMBRES})")
    return voice


def render_note(
    pitch: int,
    duration_s: float,
    velocity: float,
    timbre: Timbre,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> list[float]:
    """Render one pitched note, envelope applied.

    Args:
        pitch: MIDI note number.
        duration_s: Note length in seconds.
        velocity: 0..1 gain for the note.
        timbre: Timbre name.
        sample_rate: Samples per second.

    Returns:
        Mono samples for this note only (may be empty).
    """
    voice = voice_for(timbre)
    count = ms_to_samples(duration_s * 1000.0, sample_rate)
    wave = additive_wave(midi_to_hz(pitch), voice.harmonics, count, sample_rate)
    env = adsr_envelope(
        count,
        sample_rate,
        voice.attack_ms,
        voice.decay_ms,
        voice.sustain,
        voice.release_ms,
    )
    gain = min(max(velocity, 0.0), 1.0)
    return [wave[i] * env[i] * gain for i in range(count)]


def normalise(samples: Sequence[float], ceiling: float = PEAK_CEILING) -> list[float]:
    """Scale a frame so its peak lands on ``ceiling``.

    Args:
        samples: Mono PCM.
        ceiling: Target peak, linear; clamped to ``[0, 1]`` so nothing clips.

    Returns:
        Scaled copy; empty and silent frames are returned unchanged.
    """
    if not samples:
        return []
    peak = max(abs(float(value)) for value in samples)
    if peak <= 0.0:
        return [float(value) for value in samples]
    target = min(max(ceiling, 0.0), 1.0)
    scale = target / peak
    return [float(value) * scale for value in samples]


def apply_fades(
    samples: Sequence[float],
    sample_rate: int,
    fade_ms: float = FADE_MS,
) -> list[float]:
    """Apply equal raised-cosine ramps to both ends of a frame.

    Identical ramps at head and tail are what make a loop point clean: the
    seam always sits between two near-silent samples.

    Args:
        samples: Mono PCM.
        sample_rate: Samples per second.
        fade_ms: Ramp length in ms, halved when the frame is shorter.

    Returns:
        Faded copy.
    """
    total = len(samples)
    if total == 0:
        return []
    out = [float(value) for value in samples]
    ramp_len = min(ms_to_samples(fade_ms, sample_rate), total // 2)
    for index in range(ramp_len):
        gain = 0.5 - 0.5 * math.cos(math.pi * (index + 1) / (ramp_len + 1))
        out[index] *= gain
        out[total - 1 - index] *= gain
    return out


def interleave(
    samples: Sequence[float],
    channels: int,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> list[float]:
    """Expand mono PCM to interleaved frames for ffmpeg.

    The right channel carries a sub-millisecond pre-delay, which is enough
    width to keep a tone from sounding pinned to the centre.

    Args:
        samples: Mono PCM.
        channels: 1 for mono, 2 for stereo.
        sample_rate: Samples per second.

    Returns:
        ``count * channels`` samples.

    Raises:
        ValueError: ``channels`` is neither 1 nor 2.
    """
    if channels == 1:
        return [float(value) for value in samples]
    if channels != 2:
        raise ValueError(f"channels must be 1 or 2, got {channels}")
    lead = ms_to_samples(STEREO_SPREAD_MS, sample_rate)
    right = [0.0] * lead + [float(value) for value in samples]
    out: list[float] = []
    for index, value in enumerate(samples):
        out.append(float(value))
        out.append(right[index])
    return out


def render_motif(
    motif: Motif,
    timbre: Timbre,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> list[float]:
    """Render a whole motif to mono PCM, normalised and click-free.

    Args:
        motif: Steps to play in order; ``pitch`` ``None`` is a rest.
        timbre: Timbre every pitched step uses.
        sample_rate: Samples per second.

    Returns:
        Mono samples in ``[-1, 1]``; empty for an empty motif.
    """
    out: list[float] = []
    for pitch, duration_s, velocity in motif:
        count = ms_to_samples(duration_s * 1000.0, sample_rate)
        if pitch is None:
            out.extend([0.0] * count)
            continue
        out.extend(render_note(pitch, duration_s, velocity, timbre, sample_rate))
    return apply_fades(normalise(out), sample_rate)


def motif_duration(motif: Motif) -> float:
    """Total seconds a motif occupies.

    Args:
        motif: Steps to add up.

    Returns:
        Sum of the step durations, rounded to milliseconds.
    """
    return round(sum(duration for _, duration, _ in motif), 3)
