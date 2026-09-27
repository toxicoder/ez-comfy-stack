"""Beat-aligned join for multi-pass ACE-Step takes.

A Drive-through take renders as several ACE passes that are stitched
into one master here. The join is beat-aligned: every pass spans a whole
number of bars and adjacent passes share an overlap of whole bars. Each
seam splits the signal at a crossover: the sub band hands off with
weights that sum to one, so two in-phase 808s neither stack to double
level nor null, and the mid band crosses over the same window with
constant-amplitude weights, so the seam never clicks and never dumps a
clipping step into the master. The module stays hermetic: no ComfyUI
import and no torch import at module load - torch is consulted lazily,
only when packing the master back into a Comfy AUDIO dict.
"""

from __future__ import annotations

import math
from typing import Any

# One bar is four quarter-note beats, so a bar lasts 4 * 60 / bpm
# seconds: near 1.4 s at the Drive-through tempos. This is the same bar
# the arranger counts its 2-bar cells in.
BAR_BEATS = 4.0

# A pass is on the bar grid when its length is within this many seconds
# of a whole number of bars. ACE-Step renders on 5 Hz latent frames
# (0.2 s each), so the tolerance carries half a frame of slack.
GRID_TOL_S = 0.12

# Rate stamped on the fallback AUDIO payloads when no rate is known.
FALLBACK_SAMPLE_RATE = 44100

# Highest audio_XX socket the joiner node exposes.
MAX_JOIN_SEGMENTS = 8


def bar_seconds(bpm: float) -> float:
    """Duration of one bar at this tempo.

    Args:
        bpm: Tempo in beats per minute.

    Returns:
        Seconds per bar.

    Raises:
        ValueError: bpm is not a positive tempo.
    """
    if bpm <= 0:
        raise ValueError(f"bpm must be positive, got {bpm}")
    return BAR_BEATS * 60.0 / float(bpm)


def overlap_seconds(bars: float, bpm: float) -> float:
    """Duration of an overlap of whole bars at this tempo.

    Args:
        bars: Overlap measured in bars.
        bpm: Tempo in beats per minute.

    Returns:
        Seconds of overlap.
    """
    return float(bars) * bar_seconds(bpm)


def _as_pcm(payload: Any) -> list[float]:
    """Flatten any Comfy waveform shape to 1-D PCM.

    Handles torch and numpy tensors (through ``detach``/``cpu`` and
    ``tolist``), nested lists of any depth, and bare scalars.

    Args:
        payload: Waveform value from an AUDIO dict.

    Returns:
        A plain list of floats.

    Raises:
        ValueError: the payload is not a recognisable waveform.
    """
    if payload is None:
        return []
    if hasattr(payload, "detach") and hasattr(payload, "cpu"):
        payload = payload.detach().cpu()
    if hasattr(payload, "tolist"):
        payload = payload.tolist()
    if isinstance(payload, (list, tuple)):
        out: list[float] = []
        for item in payload:
            out.extend(_as_pcm(item))
        return out
    if isinstance(payload, bool):
        raise ValueError(f"waveform is not audio: {payload!r}")
    if isinstance(payload, (int, float)):
        return [float(payload)]
    raise ValueError(f"waveform is not audio: {payload!r}")


def pack_audio(samples: list[float], sample_rate: int) -> dict[str, Any]:
    """Wrap PCM in a Comfy AUDIO dict, using torch when it is present.

    Args:
        samples: 1-D PCM.
        sample_rate: Rate to stamp; anything at or below zero falls back
            to ``FALLBACK_SAMPLE_RATE``.

    Returns:
        ``{"waveform", "sample_rate"}`` with a tensor waveform when
        torch is importable, otherwise nested lists.
    """
    rate = sample_rate if sample_rate > 0 else FALLBACK_SAMPLE_RATE
    try:
        import torch

        tensor = torch.as_tensor(samples, dtype=torch.float32).unsqueeze(0)
    except Exception:  # noqa: BLE001 - any torch absence falls back
        return {"waveform": [[list(samples)]], "sample_rate": rate}
    return {"waveform": tensor, "sample_rate": rate}


# Cascaded second-order Butterworth sections per pass of the crossover.
_XOVER_SECTIONS = 1

# Pad length for the mirror-padded zero-phase filter, in corner periods.
_XOVER_PAD_PERIODS = 6


def one_pole_lowpass(samples: list[float], sample_rate: int, cutoff_hz: float) -> list[float]:
    """Sub band of a signal below the crossover corner.

    A second-order Butterworth low-pass (Q = 1/sqrt(2)) run forward then
    backward over a mirror-padded buffer. Both choices matter: zero-phase
    filtering keeps the 808 in phase with itself, so the mid band formed
    as ``samples - low`` is a true complement; and the mirrored edges
    stop the filter from drooping over the first milliseconds, which the
    seam checks would read as a missing sub. At the Drive-through rates
    the double pass leaves 60 Hz near unity and erases everything above
    the corner, which is what keeps the sub hand-off honest.

    Args:
        samples: Input PCM.
        sample_rate: Input rate.
        cutoff_hz: -3 dB corner in hertz.

    Returns:
        The low band, the same length as the input.
    """
    if not samples:
        return []
    pad = max(8, int(round(_XOVER_PAD_PERIODS * sample_rate / cutoff_hz)))
    buffered = list(reversed(samples[:pad])) + samples + list(reversed(samples[-pad:]))
    w0 = 2.0 * math.pi * cutoff_hz / float(sample_rate)
    cos_w0 = math.cos(w0)
    alpha = math.sin(w0) / (2.0 * 0.7071067811865476)
    a0 = 1.0 + alpha
    b0 = (1.0 - cos_w0) / 2.0 / a0
    b1 = (1.0 - cos_w0) / a0
    b2 = b0
    a1 = -2.0 * cos_w0 / a0
    a2 = (1.0 - alpha) / a0

    def pass_once(values: list[float]) -> list[float]:
        """Run the biquad cascade once over a buffer from steady state.

        Each section's delay line starts loaded with the first sample
        instead of zero - the classic forward-backward initialisation.
        A filter at rest attacks over its settling time, and that attack
        would land on the seam as a half-level 808.

        Args:
            values: PCM to filter.

        Returns:
            The filtered PCM, same length.
        """
        low = values
        for _section in range(_XOVER_SECTIONS):
            seed = low[0]
            x1 = x2 = y1 = y2 = seed
            out: list[float] = []
            for sample in low:
                y = b0 * sample + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
                out.append(y)
                x2, x1 = x1, sample
                y2, y1 = y1, y
            low = out
        return low

    low = pass_once(pass_once(buffered)[::-1])[::-1]
    return low[pad : pad + len(samples)]


def mid_band(samples: list[float], low: list[float]) -> list[float]:
    """Mid and high band: the signal minus its low band.

    Args:
        samples: Input PCM.
        low: The low band of the same signal.

    Returns:
        ``samples - low``, elementwise.
    """
    return [s - l for s, l in zip(samples, low)]


def _quiet_index(samples: list[float], index: int, span: int) -> int:
    """Nearest sample to a zero crossing at or after a boundary.

    Args:
        samples: PCM to search.
        index: Nominal boundary index.
        span: How far past ``index`` the search may reach.

    Returns:
        Index of the smallest-magnitude sample in ``[index,
        index + span]``, clamped to the buffer.
    """
    if not samples:
        return index
    centre = max(0, min(index, len(samples) - 1))
    high = min(centre + max(0, span), len(samples) - 1)
    best = centre
    best_abs = abs(samples[best])
    for candidate in range(centre, high + 1):
        magnitude = abs(samples[candidate])
        if magnitude < best_abs:
            best = candidate
            best_abs = magnitude
    return best


def _seam_overlaps(
    parts: list[list[float]],
    overlap_bars: int | list[int],
    sample_rate: int,
    bpm: float,
) -> list[int]:
    """Normalise and validate the per-seam overlap in bars.

    Args:
        parts: Joined segments.
        overlap_bars: One bar count for every seam, or one entry per
            seam.
        sample_rate: Shared rate, for the seconds sanity check.
        bpm: Tempo, for the seconds sanity check.

    Returns:
        Per-seam overlap in bars.

    Raises:
        ValueError: the list length mismatches the seams, a count is
            negative, or an overlap would eat a whole pass.
    """
    seams = max(0, len(parts) - 1)
    if isinstance(overlap_bars, (list, tuple)):
        overlap = [int(bars) for bars in overlap_bars]
    else:
        overlap = [int(overlap_bars)] * seams
    if len(overlap) != seams:
        raise ValueError(
            f"overlap_bars needs one entry per seam: {len(overlap)} for {seams} seams"
        )
    bar = bar_seconds(bpm) * sample_rate
    tolerance = GRID_TOL_S * sample_rate
    windows = [int(round(bars * bar)) for bars in overlap]
    for index in range(seams):
        if overlap[index] < 0:
            raise ValueError(f"overlap_bars must be 0 or more, got {overlap[index]}")
        if windows[index] > min(len(parts[index]), len(parts[index + 1])) + tolerance:
            raise ValueError(
                f"overlap of {overlap[index]} bars eats segment {index + 1}"
            )
    for index in range(1, seams):
        if windows[index - 1] + windows[index] > len(parts[index]) + tolerance:
            raise ValueError(
                f"overlaps of {overlap[index - 1]} and {overlap[index]} bars "
                f"eat segment {index + 1}"
            )
    return overlap


def _grid_check(parts: list[list[float]], sample_rate: int, bpm: float) -> None:
    """Require every pass to span a whole number of bars.

    A pass that misses the grid had its latent cut mid-bar, which the
    graph fixes upstream by rendering whole cells; the joiner reports it
    instead of hiding it.

    Args:
        parts: Joined segments.
        sample_rate: Shared rate.
        bpm: Tempo used for the grid.

    Raises:
        ValueError: a segment is off the grid; the message names it and
            states the measured delta in seconds.
    """
    bar = bar_seconds(bpm) * sample_rate
    tolerance = GRID_TOL_S * sample_rate
    for index, samples in enumerate(parts, 1):
        nearest = int(round(len(samples) / bar)) * bar
        delta = abs(len(samples) - nearest)
        if delta > tolerance:
            raise ValueError(
                f"segment {index} is off the bar grid by {delta / sample_rate:.2f} s"
            )


def join_pcm(
    parts: list[list[float]],
    sample_rate: int,
    bpm: float,
    overlap_bars: int | list[int],
    *,
    crossover_hz: float = 120.0,
) -> list[float]:
    """Stitch PCM passes into one master on the bar grid.

    Each seam overlaps the previous pass's tail with the next pass's
    head by whole bars. The signal splits at ``crossover_hz`` and both
    bands hand off with weights that sum to one at every sample, so two
    in-phase subs neither double nor null, no seam sample can exceed the
    louder side, and the hand-off cannot inject a clipping step.

    Args:
        parts: One PCM segment per ACE pass, in render order.
        sample_rate: Shared rate for every segment.
        bpm: Tempo that defines the bar grid and the overlaps.
        overlap_bars: Whole bars overlapped at each seam, either one int
            or one entry per seam. ``0`` is an exact butt join.
        crossover_hz: Sub/mid split for the hand-off.

    Returns:
        The joined master PCM.

    Raises:
        ValueError: the tempo, the overlap spec, or the bar grid is
            invalid.
    """
    bar_seconds(bpm)
    segments = [list(part) for part in parts]
    if not segments:
        return []
    overlap = _seam_overlaps(segments, overlap_bars, sample_rate, bpm)
    if len(segments) > 1:
        _grid_check(segments, sample_rate, bpm)
    if not any(overlap):
        stitched: list[float] = []
        for part in segments:
            stitched.extend(part)
        return stitched

    bar = bar_seconds(bpm) * sample_rate
    lows = [one_pole_lowpass(part, sample_rate, crossover_hz) for part in segments]
    mids = [mid_band(part, low) for part, low in zip(segments, lows)]

    out: list[float] = []
    head = 0
    for index in range(len(segments) - 1):
        prev, nxt = segments[index], segments[index + 1]
        prev_low, nxt_low = lows[index], lows[index + 1]
        prev_mid, nxt_mid = mids[index], mids[index + 1]
        window = int(round(overlap[index] * bar))
        tail = len(prev) - window
        out.extend(prev[head:tail])
        for step in range(window):
            weight = step / (window - 1) if window > 1 else 1.0
            # The sub sums with weights that total one so in-phase 808s
            # hand off at their own level; the mid crosses at equal
            # power so unrelated content holds its energy across the
            # seam instead of dipping 3 dB in the middle.
            sub = (1.0 - weight) * prev_low[tail + step] + weight * nxt_low[step]
            mid = (
                math.cos(math.pi * weight * 0.5) * prev_mid[tail + step]
                + math.sin(math.pi * weight * 0.5) * nxt_mid[step]
            )
            out.append(sub + mid)
        head = window
    out.extend(segments[-1][head:])
    return out


def join_audio(
    segments: list[dict[str, Any]],
    *,
    bpm: float,
    overlap_bars: int | list[int],
    crossover_hz: float = 120.0,
) -> dict[str, Any]:
    """Join Comfy AUDIO dicts into one master AUDIO.

    Args:
        segments: AUDIO payloads in render order.
        bpm: Tempo that defines the bar grid and the overlaps.
        overlap_bars: Whole bars overlapped at each seam.
        crossover_hz: Sub/mid split for the hand-off.

    Returns:
        One AUDIO dict. A single wired pass ships as-is; no passes at all
        become a one-sample silence at ``FALLBACK_SAMPLE_RATE``.

    Raises:
        ValueError: the segments disagree on sample rate, or the join
            parameters are invalid.
    """
    if not segments:
        return pack_audio([0.0], FALLBACK_SAMPLE_RATE)
    rates = set()
    for segment in segments:
        try:
            rates.add(int(segment["sample_rate"]))
        except (KeyError, TypeError):
            raise ValueError("every segment needs a sample_rate") from None
    if len(rates) > 1:
        raise ValueError(f"segments must share one sample rate: {sorted(rates)}")
    if len(segments) == 1:
        return segments[0]
    rate = rates.pop()
    parts = [_as_pcm(segment.get("waveform")) for segment in segments]
    master = join_pcm(parts, rate, bpm, overlap_bars, crossover_hz=crossover_hz)
    return pack_audio(master, rate)
