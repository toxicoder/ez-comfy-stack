"""PCM speech/DSP helpers for dub (onset, VAD, speech-like, crop).

Constants that tests monkeypatch on :mod:`ez_dub.pipeline` (currently
``ONSET_PAD_S``) are read from that module at call time.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

from .align import SAMPLE_RATE, lock_duration, rms
from .audio import write_wav

# Speech-like / onset / ref-trim knobs (unpatched; ONSET_PAD_S lives on pipeline).
VOICED_MIN_FRAC = 0.20
ZCR_NOISE_FRAC = 0.25
ZCR_SPEECH_MIN = 150.0
ZC_INTERVAL_CV_MIN = 0.18
ZC_INTERVAL_MIN_GAPS = 8
ENVELOPE_CV_MIN = 0.12
SPEECH_BAND_LO_HZ = 300.0
SPEECH_BAND_HI_HZ = 3400.0
SPEECH_BAND_MIN = 0.22
TONAL_FRAME_MS = 80
TONAL_CV_MAX = 0.08
TONAL_FRAME_MAX = 0.82
ONSET_ABS = 0.02
ONSET_REL = 0.12
ONSET_HOLD_S = 0.08
REF_MIN_RMS = 0.008
REF_SILENCE_RMS = 0.008
REF_XFADE_MS = 30
REF_PEAK = 0.89
REF_MIN_TURN_S = 0.8
REF_SINGLE_S = 6.0
REF_TARGET_S = 9.5
REF_MAX_S = 10.0
REF_PURITY_MIN_DIM = 8
REF_PURITY_COSINE = 0.55

# Reference-window selection: the clone prompt is the single biggest lever on
# voice similarity, so candidate windows are scored across the whole take and
# the best few are stitched. Chatterbox reads only the first 6 s for the
# speech-token prompt and the first 10 s for the vocoder reference, hence the
# ``REF_MAX_S`` cap and the ``REF_TARGET_S`` aim just under it.
REF_MIN_S = 4.0
REF_WINDOW_HOP_S = 1.0
REF_CLIP_RATIO_MAX = 0.02
REF_CLIP_FLOOR = 0.985
REF_TONAL_FRAME_MAX = 0.35
REF_SPEECH_BAND_MIN = 0.30
REF_VOICED_MIN_FRAC = 0.28
REF_NOISE_FLOOR_DB = -28.0
REF_HEAD_S = 2.0
REF_WEIGHT_VOICED = 0.18
REF_WEIGHT_BAND = 0.18
REF_WEIGHT_NOISE = 0.16
REF_WEIGHT_TONAL = 0.14
REF_WEIGHT_ENVELOPE = 0.10
REF_WEIGHT_ZC = 0.10
REF_WEIGHT_CLIP = 0.08
REF_WEIGHT_PURITY = 0.06
REF_ENVELOPE_CV_IDEAL = 0.60
REF_ZC_INTERVAL_CV_IDEAL = 0.60
REF_NOISE_DB_SPAN = 30.0
PCM_INT_RANGE = 1.5
EXPECTED_WORDS_PER_S = 2.7
TAIL_SLACK = 1.6


def cosine(left: list[float], right: list[float]) -> float:
    """Cosine similarity; 0 when either vector is empty/zero.

    Args:
        left: Embedding.
        right: Embedding.

    Returns:
        Cosine in ``[0, 1]`` for non-negative typical speaker vectors.
    """
    n = min(len(left), len(right))
    if n == 0:
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for i in range(n):
        a = float(left[i])
        b = float(right[i])
        dot += a * b
        na += a * a
        nb += b * b
    if na <= 0.0 or nb <= 0.0:
        return 0.0
    return dot / ((na ** 0.5) * (nb ** 0.5))


def cluster_embeddings(
    vectors: list[list[float]],
    max_speakers: int = 0,
    threshold: float = 0.55,
) -> list[str]:
    """Greedy nearest-centroid clustering.

    Args:
        vectors: One embedding per segment.
        max_speakers: 0 means cap at 8.
        threshold: Below this, start a new speaker (until the cap).
    Returns:
        Speaker ids ``spk00``… aligned with ``vectors``.
    """
    labels: list[str] = []
    centroids: list[tuple[str, list[float], int]] = []
    cap = int(max_speakers) if int(max_speakers) > 0 else 8
    cap = max(1, cap)
    for vector in vectors:
        if not centroids:
            centroids.append(("spk00", [float(x) for x in vector], 1))
            labels.append("spk00")
            continue
        best_i = 0
        best = -1.0
        for i, (_sid, mean, _count) in enumerate(centroids):
            score = cosine(vector, mean)
            if score > best:
                best = score
                best_i = i
        if best < threshold and len(centroids) < cap:
            sid = f"spk{len(centroids):02d}"
            centroids.append((sid, [float(x) for x in vector], 1))
            labels.append(sid)
            continue
        sid, mean, count = centroids[best_i]
        new_mean = [
            (m * count + float(x)) / (count + 1) for m, x in zip(mean, vector)
        ]
        centroids[best_i] = (sid, new_mean, count + 1)
        labels.append(sid)
    return labels


def energy_vad(
    samples: list[float],
    rate: int,
    frame_ms: int = 20,
    hop_ms: int = 10,
    thresh: float = 0.02,
    min_s: float = 0.3,
    pad_s: float = 0.05,
) -> list[tuple[float, float]]:
    """Energy VAD fallback when Silero is missing.

    Args:
        samples: Mono PCM.
        rate: Sample rate.
        frame_ms: Analysis frame size.
        hop_ms: Hop between frames.
        thresh: RMS threshold.
        min_s: Minimum span length.
        pad_s: Padding added around each span.

    Returns:
        List of ``(t0, t1)`` speech spans in seconds.
    """
    sr = int(rate) or SAMPLE_RATE
    n = len(samples)
    if n == 0:
        return []
    frame = max(1, int(sr * frame_ms / 1000))
    hop = max(1, int(sr * hop_ms / 1000))
    voiced: list[bool] = []
    i = 0
    while i + frame <= n:
        chunk = samples[i : i + frame]
        voiced.append(rms(chunk) >= thresh)
        i += hop
    if not voiced:
        return []
    spans: list[tuple[float, float]] = []
    start: int | None = None
    for idx, flag in enumerate(voiced):
        if flag and start is None:
            start = idx
        if not flag and start is not None:
            spans.append((start, idx))
            start = None
    if start is not None:
        spans.append((start, len(voiced)))
    out: list[tuple[float, float]] = []
    pad = float(pad_s)
    min_len = float(min_s)
    for a, b in spans:
        t0 = max(0.0, a * hop / sr - pad)
        t1 = min(n / sr, (b * hop + frame) / sr + pad)
        if t1 - t0 >= min_len:
            out.append((t0, t1))
    return out


def _slice_pcm(samples: list[float], rate: int, t0: float, t1: float) -> list[float]:
    """Copy a ``[t0, t1]`` window from ``samples``.

    Args:
        samples: Mono PCM.
        rate: Sample rate.
        t0: Start seconds.
        t1: End seconds.

    Returns:
        Slice, or ``[]`` when the window is empty.
    """
    sr = int(rate) or SAMPLE_RATE
    a = max(0, int(round(t0 * sr)))
    b = min(len(samples), int(round(t1 * sr)))
    if b <= a:
        return []
    return [float(x) for x in samples[a:b]]


def _frame_rms(
    pcm: list[float], rate: int, frame_ms: int = 20
) -> tuple[list[float], int]:
    """Non-overlapping frame RMS plus frame length in samples.

    Args:
        pcm: Mono PCM.
        rate: Sample rate.
        frame_ms: Frame size.

    Returns:
        ``(rms_per_frame, frame_length_samples)``.
    """
    sr = int(rate) or SAMPLE_RATE
    frame = max(1, int(sr * frame_ms / 1000))
    n = len(pcm)
    values: list[float] = []
    i = 0
    while i + frame <= n:
        values.append(rms(pcm[i : i + frame]))
        i += frame
    return values, frame


def _voiced_span(pcm: list[float], rate: int) -> tuple[int, int] | None:
    """Sample span of voiced audio plus onset pad, or None if none.

    Args:
        pcm: Mono PCM.
        rate: Sample rate.
    Returns:
        ``(start, end)`` exclusive-end indices, or None.
    """
    if not pcm:
        return None
    sr = int(rate) or SAMPLE_RATE
    frames, frame = _frame_rms(pcm, sr)
    n = len(pcm)
    if not frames:
        return (0, n) if rms(pcm) >= ONSET_ABS else None
    peak = max(frames)
    if peak < ONSET_ABS:
        return None
    thresh = max(ONSET_ABS, ONSET_REL * peak)
    hold = max(1, int(round(ONSET_HOLD_S * sr / frame)))
    if len(frames) < hold:
        return (0, n) if peak >= thresh else None

    def _first_hold(seq: list[float]) -> int | None:
        """Index of the first frame that starts an onset hold.

        Args:
            seq: Frame RMS values.

        Returns:
            Frame index, or None when no hold is found.
        """
        run = 0
        for i, value in enumerate(seq):
            if value >= thresh:
                run += 1
                if run >= hold:
                    return i - hold + 1
            else:
                run = 0
        return None

    start_f = _first_hold(frames)
    if start_f is None:
        return None
    end_rev = _first_hold(list(reversed(frames)))
    if end_rev is None:
        last_f = len(frames) - 1
    else:
        last_f = len(frames) - 1 - end_rev
    from . import pipeline as _pl
    pad = int(round(float(_pl.ONSET_PAD_S) * sr))
    start = max(0, start_f * frame - pad)
    end = min(n, (last_f + 1) * frame + pad)
    if end <= start:
        return None
    return start, end


def speech_onset_slice(pcm: list[float], rate: int) -> list[float]:
    """Drop leading/trailing near-silence using a relative onset.

    Absolute RMS 0.008 keeps PerTh-watermarked hush (~0.01). This uses
    ``max(ONSET_ABS, ONSET_REL * peak)`` and an 80 ms hold so watermark
    floor and clicks do not count as speech.

    Args:
        pcm: Mono clone PCM.
        rate: Sample rate.
    Returns:
        Sliced PCM, or ``[]`` when no voiced burst is found.
    """
    span = _voiced_span(pcm, rate)
    if span is None:
        return []
    start, end = span
    return [float(x) for x in pcm[start:end]]


def strip_leading_silence(pcm: list[float], rate: int) -> list[float]:
    """Drop a leading hush prefix. Keep the tail.

    Used when spoken disclosure is off so ``ez_dub_mix`` starts on speech.
    Does not change ``ez_dub_yt.wav``. No-op when no voiced burst is found
    (never returns empty for a non-empty mix).

    Args:
        pcm: Mono mix PCM.
        rate: Sample rate.
    Returns:
        PCM with leading near-silence removed, or a copy of ``pcm``.
    """
    if not pcm:
        return []
    span = _voiced_span(pcm, rate)
    if span is None:
        return [float(x) for x in pcm]
    start, _end = span
    if start <= 0:
        return [float(x) for x in pcm]
    return [float(x) for x in pcm[start:]]


def envelope_cv(pcm: list[float], rate: int, frame_ms: int = 20) -> float:
    """Coefficient of variation of 20 ms frame RMS.

    Steady tones sit near 0; speech has syllable-scale swings.

    Args:
        pcm: Mono PCM.
        rate: Sample rate.
        frame_ms: Frame size.
    Returns:
        ``std / mean``, or 1.0 when the clip is too short to judge.
    """
    frames, _frame = _frame_rms(pcm, rate, frame_ms)
    if len(frames) < 4:
        return 1.0
    mean = sum(frames) / len(frames)
    if mean < 1e-8:
        return 0.0
    acc = 0.0
    for value in frames:
        delta = value - mean
        acc += delta * delta
    return (acc / len(frames)) ** 0.5 / mean


def _trim_bounds(
    pcm: list[float], rate: int, thresh: float = REF_SILENCE_RMS
) -> tuple[int, int]:
    """Sample span after dropping leading and trailing silent frames.

    Args:
        pcm: Mono PCM.
        rate: Sample rate.
        thresh: Frame RMS below which a frame is silence.

    Returns:
        ``(start, end)`` exclusive-end indices. ``(0, 0)`` when ``pcm`` is
        empty. The whole clip when every frame is below ``thresh``.
    """
    if not pcm:
        return 0, 0
    sr = int(rate) or SAMPLE_RATE
    frame = max(1, int(sr * 0.02))
    n = len(pcm)

    def _voiced(index: int) -> bool:
        """True when the frame at ``index`` is above the silence RMS.

        Args:
            index: Sample offset.

        Returns:
            Whether that frame is voiced.
        """
        chunk = pcm[index : min(n, index + frame)]
        return rms(chunk) >= float(thresh)

    start = 0
    while start + frame <= n and not _voiced(start):
        start += frame
    end = n
    while end - frame >= start and not _voiced(end - frame):
        end -= frame
    if end <= start:
        return 0, n
    return start, end


def _trim_silence(
    pcm: list[float], rate: int, thresh: float = REF_SILENCE_RMS
) -> list[float]:
    """Drop leading and trailing frames below ``thresh`` RMS.

    Args:
        pcm: Mono PCM.
        rate: Sample rate.
        thresh: Frame RMS below which a frame is silence.

    Returns:
        Trimmed PCM, or a copy when the whole clip is below thresh.
    """
    start, end = _trim_bounds(pcm, rate, thresh)
    return [float(x) for x in pcm[start:end]]


def _concat_crossfade(
    chunks: list[list[float]], rate: int, xfade_ms: int = REF_XFADE_MS
) -> list[float]:
    """Join PCM chunks with an equal-power-ish linear crossfade.

    Args:
        chunks: PCM pieces in order.
        rate: Sample rate.
        xfade_ms: Crossfade length.

    Returns:
        Concatenated PCM.
    """
    if not chunks:
        return []
    sr = int(rate) or SAMPLE_RATE
    fade = max(1, int(sr * max(0, int(xfade_ms)) / 1000))
    out = [float(x) for x in chunks[0]]
    for chunk in chunks[1:]:
        if not chunk:
            continue
        piece = [float(x) for x in chunk]
        n = min(fade, len(out), len(piece))
        if n <= 0:
            out.extend(piece)
            continue
        for i in range(n):
            gain = i / n
            out[-n + i] = out[-n + i] * (1.0 - gain) + piece[i] * gain
        out.extend(piece[n:])
    return out


def _peak_normalize(pcm: list[float], peak: float = REF_PEAK) -> list[float]:
    """Scale so max abs sample is ``peak`` (no-op when already quieter).

    Args:
        pcm: Mono PCM.
        peak: Target peak magnitude.

    Returns:
        Scaled PCM (or a copy).
    """
    if not pcm:
        return []
    mag = max(abs(float(x)) for x in pcm)
    if mag <= 1e-8:
        return [float(x) for x in pcm]
    target = float(peak)
    if mag <= target:
        return [float(x) for x in pcm]
    scale = target / mag
    return [float(x) * scale for x in pcm]


def raise_to_peak(pcm: list[float], peak: float = REF_PEAK) -> list[float]:
    """Scale so max abs == peak. No-op on silence (mag < 1e-8).

    Args:
        pcm: Mono PCM.
        peak: Target peak magnitude.

    Returns:
        Scaled PCM (or a copy).
    """
    if not pcm:
        return []
    mag = max(abs(float(x)) for x in pcm)
    if mag < 1e-8:
        return [float(x) for x in pcm]
    scale = float(peak) / mag
    return [float(x) * scale for x in pcm]


def match_rms(pcm: list[float], target_rms: float) -> list[float]:
    """Scale pcm so rms(pcm) ~= target_rms, then cap with raise_to_peak.

    No-op if rms(pcm) < 1e-8 or target_rms < REF_MIN_RMS.

    Args:
        pcm: Clone PCM.
        target_rms: Desired RMS (usually the source window).

    Returns:
        Gain-matched PCM.
    """
    if not pcm:
        return []
    current = rms(pcm)
    if current < 1e-8 or float(target_rms) < REF_MIN_RMS:
        return [float(x) for x in pcm]
    scale = float(target_rms) / current
    scaled = [float(x) * scale for x in pcm]
    return raise_to_peak(scaled)


def _speaker_ref_text(ref: Path | str) -> str:
    """Transcript sidecar next to a speaker ref wav.

    Args:
        ref: Speaker ``.wav`` path.

    Returns:
        Sidecar text, or ``""`` when missing.
    """
    path = Path(ref)
    txt = path.with_suffix(".txt")
    if not txt.is_file():
        return ""
    return txt.read_text(encoding="utf-8").strip()


def _turn_rms(turn: dict[str, Any], pcm: list[float]) -> float:
    """Turn RMS from the mapping, else from ``pcm``.

    Args:
        turn: JSON turn mapping (may include ``rms``).
        pcm: Window PCM used when ``rms`` is missing.

    Returns:
        Non-negative RMS.
    """
    raw = turn.get("rms")
    try:
        value = float(raw) if raw is not None else 0.0
    except (TypeError, ValueError):
        value = 0.0
    if value > 0.0:
        return value
    return rms(pcm)


# Keys already logged for a rejected ``EZ_DUB_TUNE_*`` value.
_TUNE_WARNED: set[str] = set()


def tuned_float(suffix: str, default: float, low: float, high: float) -> float:
    """Read ``EZ_DUB_TUNE_<suffix>`` or return ``default``.

    Non-numeric and out-of-range values log once and fall back, so a bad
    override on the Spark cannot change the shipped knob silently.

    Args:
        suffix: Name after ``EZ_DUB_TUNE_``.
        default: Shipped value.
        low: Inclusive lower bound.
        high: Inclusive upper bound.

    Returns:
        Parsed value, or ``default``.
    """
    key = "EZ_DUB_TUNE_" + suffix
    raw = (os.environ.get(key) or "").strip()
    if not raw:
        return float(default)
    try:
        value = float(raw)
    except ValueError:
        _warn_tune(key, raw, default)
        return float(default)
    if value < float(low) or value > float(high):
        _warn_tune(key, raw, default)
        return float(default)
    return value


def _warn_tune(key: str, raw: str, default: float) -> None:
    """Log one ignored override per key.

    Args:
        key: Full environment variable name.
        raw: Rejected text.
        default: Value used instead.
    """
    if key in _TUNE_WARNED:
        return
    _TUNE_WARNED.add(key)
    from . import pipeline as _pl

    _pl._log(f"ignoring {key}={raw!r}; using {default}")


def _percentile(values: list[float], quantile: float) -> float:
    """Linear percentile of ``values``. 0 when ``values`` is empty.

    Args:
        values: Samples.
        quantile: Fraction in ``[0, 1]``.

    Returns:
        Interpolated order statistic.
    """
    if not values:
        return 0.0
    ordered = sorted(float(v) for v in values)
    if len(ordered) == 1:
        return ordered[0]
    pos = max(0.0, min(1.0, float(quantile))) * (len(ordered) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    frac = pos - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def _clipping_fraction(pcm: list[float], floor: float = REF_CLIP_FLOOR) -> float:
    """Fraction of samples at or above ``floor`` absolute amplitude.

    Args:
        pcm: Mono PCM.
        floor: Absolute sample level treated as clipped.

    Returns:
        Fraction in ``[0, 1]``.
    """
    if not pcm:
        return 0.0
    limit = float(floor)
    clipped = 0
    for raw in pcm:
        if abs(float(raw)) >= limit:
            clipped += 1
    return clipped / float(len(pcm))


def _noise_score(pcm: list[float], rate: int) -> float:
    """1 when the quiet frames sit under the noise-floor gate and peaks rise clear.

    The floor is the 10th-percentile frame RMS in dBFS. The span is the 90th
    minus that floor. A floor louder than ``REF_NOISE_FLOOR_DB`` scores 0.

    Args:
        pcm: Mono PCM.
        rate: Sample rate.

    Returns:
        Score in ``[0, 1]``.
    """
    frames, _frame = _frame_rms(pcm, rate, 20)
    if len(frames) < 4:
        return 0.0
    quiet = _percentile(frames, 0.10)
    loud = _percentile(frames, 0.90)
    if quiet <= 1e-8:
        floor_db = -80.0
        snr_db = 80.0 if loud > 1e-8 else 0.0
    else:
        floor_db = 20.0 * math.log10(quiet)
        snr_db = 20.0 * math.log10(max(loud, 1e-8) / quiet)
    gate = tuned_float("REF_NOISE_FLOOR_DB", REF_NOISE_FLOOR_DB, -80.0, 0.0)
    if floor_db > gate:
        return 0.0
    if snr_db <= 0.0:
        return 0.0
    if snr_db >= REF_NOISE_DB_SPAN:
        return 1.0
    return snr_db / REF_NOISE_DB_SPAN


def _unit_ratio(value: float, ideal: float) -> float:
    """Map ``value`` onto ``[0, 1]`` with saturation at ``ideal``.

    Args:
        value: Raw measure.
        ideal: Value that scores 1.

    Returns:
        Saturated ratio.
    """
    if value <= 0.0:
        return 0.0
    if value >= ideal:
        return 1.0
    return value / ideal


def _remove_dc_offset(pcm: list[float]) -> list[float]:
    """Subtract the mean when the clip actually crosses zero.

    A constant block (the crossfade fixture, a DC-biased take that never
    changes sign) is left alone so a later peak check still sees its level.

    Args:
        pcm: Mono PCM.

    Returns:
        DC-removed PCM, or a float copy when there is no zero crossing.
    """
    if not pcm:
        return []
    if not _zero_cross_indices(pcm):
        return [float(x) for x in pcm]
    mean = sum(float(x) for x in pcm) / float(len(pcm))
    return [float(x) - mean for x in pcm]


def _window_components(
    pcm: list[float], rate: int, purity: float
) -> dict[str, float]:
    """Normalised measures for one reference window. Each is in ``[0, 1]``.

    Args:
        pcm: Window PCM.
        rate: Sample rate.
        purity: Cosine of this speaker's embedding to the robust centroid.

    Returns:
        Component scores. Higher is a better clone prompt.
    """
    return {
        "voiced": max(0.0, min(1.0, voiced_fraction(pcm, rate))),
        "band": max(0.0, min(1.0, speech_band_ratio(pcm, rate))),
        "tonal": max(0.0, min(1.0, 1.0 - tonal_frame_fraction(pcm, rate))),
        "noise": _noise_score(pcm, rate),
        "envelope": _unit_ratio(envelope_cv(pcm, rate), REF_ENVELOPE_CV_IDEAL),
        "zc": _unit_ratio(zc_interval_cv(pcm), REF_ZC_INTERVAL_CV_IDEAL),
        "clip": max(0.0, min(1.0, 1.0 - _clipping_fraction(pcm))),
        "purity": max(0.0, min(1.0, float(purity))),
    }


def _window_score(components: dict[str, float]) -> float:
    """Weighted sum of :func:`_window_components`.

    Args:
        components: Normalised measures.

    Returns:
        Score in ``[0, 1]``.
    """
    return (
        REF_WEIGHT_VOICED * components["voiced"]
        + REF_WEIGHT_BAND * components["band"]
        + REF_WEIGHT_NOISE * components["noise"]
        + REF_WEIGHT_TONAL * components["tonal"]
        + REF_WEIGHT_ENVELOPE * components["envelope"]
        + REF_WEIGHT_ZC * components["zc"]
        + REF_WEIGHT_CLIP * components["clip"]
        + REF_WEIGHT_PURITY * components["purity"]
    )


def _reject_reason(components: dict[str, float]) -> str:
    """Hard-reject id, or ``""`` when the window may be a clone prompt.

    ``is_speech_like`` is applied by the caller; these gates are stricter
    than that check because a bad reference is reused for every line.

    Args:
        components: Normalised measures from :func:`_window_components`.

    Returns:
        ``clip``, ``tonal``, ``band``, ``unvoiced``, or ``""``.
    """
    clip_max = tuned_float("REF_CLIP_RATIO_MAX", REF_CLIP_RATIO_MAX, 0.0, 1.0)
    if (1.0 - components["clip"]) > clip_max:
        return "clip"
    tonal_max = tuned_float("REF_TONAL_FRAME_MAX", REF_TONAL_FRAME_MAX, 0.0, 1.0)
    if (1.0 - components["tonal"]) > tonal_max:
        return "tonal"
    band_min = tuned_float("REF_SPEECH_BAND_MIN", REF_SPEECH_BAND_MIN, 0.0, 1.0)
    if components["band"] < band_min:
        return "band"
    voiced_min = tuned_float("REF_VOICED_MIN_FRAC", REF_VOICED_MIN_FRAC, 0.0, 1.0)
    if components["voiced"] < voiced_min:
        return "unvoiced"
    return ""


def _assess_ref_window(
    pcm: list[float], rate: int, purity: float
) -> tuple[str, float, dict[str, float]]:
    """Score one window and name the gate that rejected it.

    Args:
        pcm: Window PCM.
        rate: Sample rate.
        purity: Speaker-centroid cosine.

    Returns:
        ``(reason, score, components)``. ``reason`` is empty when accepted.
        Rejected windows score 0.
    """
    components = _window_components(pcm, rate, purity)
    reason = _reject_reason(components)
    if not reason and not is_speech_like(pcm, rate):
        reason = "not_speech"
    score = 0.0 if reason else _window_score(components)
    return reason, score, components


def _iter_ref_spans(n: int, win: int, hop: int) -> list[tuple[int, int]]:
    """Sliding ``[start, end)`` spans of ``win`` samples across ``n``.

    A clip shorter than ``win`` is one span. The tail is included when the
    hop does not land on it.

    Args:
        n: Clip length in samples.
        win: Window length in samples.
        hop: Hop in samples.

    Returns:
        Spans in time order.
    """
    if n <= 0:
        return []
    if win <= 0 or n <= win:
        return [(0, n)]
    spans: list[tuple[int, int]] = []
    start = 0
    step = max(1, hop)
    while start + win <= n:
        spans.append((start, start + win))
        start += step
    tail = n - win
    if spans[-1][0] != tail:
        spans.append((tail, n))
    return spans


def _prepare_window_pcm(
    pcm: list[float], rate: int, start: int, end: int
) -> tuple[list[float], int, int] | None:
    """Drop a silent head, extending forward until ``REF_MIN_S`` when it fits.

    Args:
        pcm: Parent clip.
        rate: Sample rate.
        start: Window start index.
        end: Window end index.

    Returns:
        ``(samples, start, end)`` into ``pcm``, or None when the voiced span
        stays under ``REF_MIN_S``.
    """
    sr = int(rate) or SAMPLE_RATE
    min_n = max(1, int(round(tuned_float("REF_MIN_S", REF_MIN_S, 0.3, 10.0) * sr)))
    lo, hi = _trim_bounds(pcm[start:end], sr)
    if hi - lo >= min_n:
        abs_a = start + lo
        abs_b = start + hi
        return [float(x) for x in pcm[abs_a:abs_b]], abs_a, abs_b
    base = start + lo
    extra = min_n - (hi - lo)
    extended = min(len(pcm), start + hi + extra)
    if extended <= base:
        return None
    lo2, hi2 = _trim_bounds(pcm[base:extended], sr)
    if hi2 - lo2 < min_n:
        return None
    abs_a = base + lo2
    abs_b = base + hi2
    return [float(x) for x in pcm[abs_a:abs_b]], abs_a, abs_b


def _window_text(turn: dict[str, Any], t0: float, t1: float) -> str:
    """Transcript for the samples actually kept.

    Word timestamps (``words`` entries with ``t0``/``t1`` or ``start``/``end``)
    limit the text to words whose midpoint sits in ``[t0, t1]``. Without
    timestamps the whole turn text is kept.

    Args:
        turn: JSON turn mapping.
        t0: Window start in seconds.
        t1: Window end in seconds.

    Returns:
        Text that matches the window. Empty when every timestamped word
        falls outside it.
    """
    words = turn.get("words")
    if not isinstance(words, list) or not words:
        return str(turn.get("text") or "").strip()
    parts: list[str] = []
    saw_word = False
    for raw in words:
        if not isinstance(raw, dict):
            continue
        saw_word = True
        start_raw = raw.get("t0")
        if start_raw is None:
            start_raw = raw.get("start")
        end_raw = raw.get("t1")
        if end_raw is None:
            end_raw = raw.get("end")
        if start_raw is None or end_raw is None:
            continue
        try:
            ws = float(start_raw)
            we = float(end_raw)
        except (TypeError, ValueError):
            continue
        mid = (ws + we) / 2.0
        if mid < t0 or mid > t1:
            continue
        token = str(raw.get("text") or raw.get("word") or "").strip()
        if token:
            parts.append(token)
    if not saw_word:
        return str(turn.get("text") or "").strip()
    return " ".join(parts)


def _turn_purity(turn: dict[str, Any]) -> float:
    """Cosine of this turn to the robust speaker centroid, or 1 when unknown.

    Args:
        turn: Filtered turn mapping (may carry ``_embed`` and ``_centroid``).

    Returns:
        Similarity in ``[0, 1]``.
    """
    embed = turn.get("_embed")
    centroid = turn.get("_centroid")
    if not isinstance(embed, list) or not isinstance(centroid, list):
        return 1.0
    if not embed or not centroid:
        return 1.0
    return max(0.0, cosine(embed, centroid))


def _ref_windows(turn: dict[str, Any], rate: int) -> list[dict[str, Any]]:
    """Scored windows across one kept turn.

    Args:
        turn: Filtered turn mapping with ``_pcm``.
        rate: Sample rate.

    Returns:
        Window mappings (accepted and rejected).
    """
    pcm = list(turn.get("_pcm") or [])
    sr = int(rate) or SAMPLE_RATE
    n = len(pcm)
    if n == 0:
        return []
    target_s = tuned_float("REF_TARGET_S", REF_TARGET_S, 1.0, float(REF_MAX_S))
    hop_s = tuned_float("REF_WINDOW_HOP_S", REF_WINDOW_HOP_S, 0.05, 5.0)
    win = max(1, int(round(min(target_s, float(REF_MAX_S)) * sr)))
    hop = max(1, int(round(hop_s * sr)))
    t_base = float(turn.get("t0") or 0.0)
    purity = _turn_purity(turn)
    windows: list[dict[str, Any]] = []
    for start, end in _iter_ref_spans(n, win, hop):
        prepared = _prepare_window_pcm(pcm, sr, start, end)
        if prepared is None:
            continue
        piece, abs_a, abs_b = prepared
        t0 = t_base + abs_a / float(sr)
        t1 = t_base + abs_b / float(sr)
        reason, score, components = _assess_ref_window(piece, sr, purity)
        windows.append(
            {
                "pcm": piece,
                "t0": t0,
                "t1": t1,
                "score": score,
                "components": components,
                "reason": reason,
                "ok": reason == "",
                "turn": turn,
                "text": _window_text(turn, t0, t1),
            }
        )
    return windows


def _pick_ref_windows(
    windows: list[dict[str, Any]], target_samples: int
) -> list[dict[str, Any]]:
    """Best accepted window, or a short-window stitch up to ``target_samples``.

    A window of at least ``REF_SINGLE_S`` is used alone: that is long enough
    for both the 6 s token prompt and a start on the 10 s vocoder reference.

    Args:
        windows: Scored windows from one speaker.
        target_samples: Stitch budget.

    Returns:
        Chosen windows in score order. Empty when none were accepted.
    """
    accepted = [item for item in windows if item.get("ok")]
    accepted.sort(key=lambda item: float(item["score"]), reverse=True)
    if not accepted:
        return []
    best = accepted[0]
    if float(best["t1"]) - float(best["t0"]) >= REF_SINGLE_S:
        return [best]
    chosen: list[dict[str, Any]] = []
    total = 0
    for item in accepted:
        chosen.append(item)
        total += len(item["pcm"])
        if total >= target_samples:
            break
    return chosen


def _dominant_reject(windows: list[dict[str, Any]]) -> str:
    """Most common reject id, for the degraded sidecar.

    Args:
        windows: Scored windows.

    Returns:
        Reject id, or ``""`` when nothing was rejected.
    """
    counts: dict[str, int] = {}
    for item in windows:
        reason = str(item.get("reason") or "")
        if not reason:
            continue
        counts[reason] = counts.get(reason, 0) + 1
    if not counts:
        return ""
    ranked = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
    return ranked[0][0]


def _loudness_ref_chunks(
    candidates: list[dict[str, Any]], target_samples: int
) -> tuple[list[dict[str, Any]], list[list[float]]]:
    """Previous loudness ranking, used when every scored window is rejected.

    Args:
        candidates: Filtered turns with ``_pcm``.
        target_samples: Stitch budget for short turns.

    Returns:
        ``(turns used, pcm chunks)``.
    """
    ordered = sorted(
        candidates,
        key=lambda t: (
            (float(t["t1"]) - float(t["t0"]))
            * max(_turn_rms(t, list(t.get("_pcm") or [])), 1e-6)
        ),
        reverse=True,
    )
    best = ordered[0]
    best_dur = float(best["t1"]) - float(best["t0"])
    if best_dur >= REF_SINGLE_S:
        return [best], [list(best.get("_pcm") or [])]
    used: list[dict[str, Any]] = []
    chunks: list[list[float]] = []
    total = 0
    for turn in ordered:
        chunk = list(turn.get("_pcm") or [])
        if not chunk:
            continue
        used.append(turn)
        chunks.append(chunk)
        total += len(chunk)
        if total >= target_samples:
            break
    return used, chunks


def _join_ref_text(parts: list[str]) -> str:
    """Join window transcripts, dropping blanks and duplicates.

    Args:
        parts: Text fragments in pick order.

    Returns:
        Single line.
    """
    seen: list[str] = []
    for part in parts:
        text = str(part or "").strip()
        if text and text not in seen:
            seen.append(text)
    return " ".join(seen)


def _filter_ref_turns(
    group: list[dict[str, Any]],
    samples: list[float],
    rate: int,
) -> list[dict[str, Any]]:
    """Drop overlap, short, quiet, and (when VE-sized) off-centroid turns.

    Args:
        group: JSON turns for one speaker.
        samples: Source PCM.
        rate: Sample rate.

    Returns:
        Filtered turn mappings (may include ``_pcm``).
    """
    sr = int(rate) or SAMPLE_RATE
    kept: list[dict[str, Any]] = []
    vectors: list[list[float]] = []
    for turn in group:
        if turn.get("overlap"):
            continue
        dur = float(turn["t1"]) - float(turn["t0"])
        if dur < REF_MIN_TURN_S:
            continue
        chunk = _slice_pcm(samples, sr, float(turn["t0"]), float(turn["t1"]))
        if _turn_rms(turn, chunk) < REF_MIN_RMS:
            continue
        item = dict(turn)
        item["_pcm"] = chunk
        kept.append(item)
        from . import pipeline as _pl

        vectors.append(_pl.speaker_embed(chunk, sr))
    if len(kept) < 2:
        return kept
    if len(vectors[0]) < REF_PURITY_MIN_DIM:
        return kept
    dim = len(vectors[0])
    order = sorted(
        range(len(kept)),
        key=lambda i: _turn_rms(kept[i], list(kept[i].get("_pcm") or [])),
        reverse=True,
    )
    half = max(1, (len(order) + 1) // 2)
    centroid = [0.0] * dim
    for index in order[:half]:
        for i, value in enumerate(vectors[index][:dim]):
            centroid[i] += float(value)
    scale = 1.0 / float(len(order[:half]))
    centroid = [c * scale for c in centroid]
    pure: list[dict[str, Any]] = []
    for item, vector in zip(kept, vectors):
        item["_embed"] = [float(v) for v in vector]
        item["_centroid"] = centroid
        if cosine(vector, centroid) >= REF_PURITY_COSINE:
            pure.append(item)
    return pure or kept


def _extract_refs(
    samples: list[float],
    rate: int,
    turns: list[dict[str, Any]],
    dest: Path,
    max_s: float = REF_MAX_S,
) -> dict[str, Path]:
    """Build a scored ref wav, transcript, and ``.ref.json`` per speaker.

    Chatterbox reads the first 6 s as the speech-token prompt and the first
    10 s as the vocoder reference, so each speaker's wav is the best window
    (or a short-window stitch up to ``REF_TARGET_S``), not the loudest take.
    When every window fails the gates, the loudness ranking is written and
    the sidecar sets ``degraded``.

    Args:
        samples: Source PCM.
        rate: Sample rate.
        turns: JSON turns.
        dest: Speaker-ref directory.
        max_s: Hard cap on ref duration.

    Returns:
        Speaker id to wav path.
    """
    dest.mkdir(parents=True, exist_ok=True)
    by_spk: dict[str, list[dict[str, Any]]] = {}
    for turn in turns:
        by_spk.setdefault(str(turn["speaker"]), []).append(turn)
    refs: dict[str, Path] = {}
    sr = int(rate) or SAMPLE_RATE
    cap_s = max_s if max_s > 0 else REF_MAX_S
    cap = int(cap_s * sr)
    target = int(
        tuned_float("REF_TARGET_S", REF_TARGET_S, 1.0, float(REF_MAX_S)) * sr
    )
    for speaker, group in by_spk.items():
        candidates = _filter_ref_turns(group, samples, sr)
        if not candidates:
            continue
        windows: list[dict[str, Any]] = []
        for turn in candidates:
            windows.extend(_ref_windows(turn, sr))
        chosen = _pick_ref_windows(windows, target)
        score: float | None
        components: dict[str, Any]
        if chosen:
            chunks = [list(item["pcm"]) for item in chosen]
            notes = [str(item.get("text") or "") for item in chosen]
            best = chosen[0]
            score = float(best["score"])
            components = dict(best["components"])
            reject = ""
            degraded = False
            span_t0 = min(float(item["t0"]) for item in chosen)
            span_t1 = max(float(item["t1"]) for item in chosen)
        else:
            used, chunks = _loudness_ref_chunks(candidates, target)
            notes = [str(turn.get("text") or "") for turn in used]
            score = None
            components = {}
            reject = _dominant_reject(windows)
            degraded = True
            if used:
                span_t0 = min(float(turn["t0"]) for turn in used)
                span_t1 = max(float(turn["t1"]) for turn in used)
            else:
                span_t0 = 0.0
                span_t1 = 0.0
        pcm = _concat_crossfade(chunks, sr)
        pcm = _trim_silence(pcm, sr)
        pcm = _remove_dc_offset(pcm)
        if len(pcm) > cap:
            pcm = pcm[:cap]
        pcm = _peak_normalize(pcm)
        if not pcm:
            continue
        path = dest / f"{speaker}.wav"
        write_wav(path, pcm, sr)
        note = _join_ref_text(notes)
        if note:
            path.with_suffix(".txt").write_text(note + "\n", encoding="utf-8")
        payload = {
            "components": components,
            "degraded": degraded,
            "duration_s": round(len(pcm) / float(sr), 4),
            "reject": reject,
            "score": score,
            "speaker": speaker,
            "t0": span_t0,
            "t1": span_t1,
            "text": note,
        }
        path.with_suffix(".ref.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        refs[speaker] = path
    return refs


def ref_diagnostics(folder: Path) -> dict[str, Any]:
    """Load ``*.ref.json`` sidecars written beside speaker refs.

    Args:
        folder: Speaker-ref directory.

    Returns:
        Speaker id to sidecar mapping. Unreadable files are skipped.
    """
    found: dict[str, Any] = {}
    if not folder.is_dir():
        return found
    for path in sorted(folder.glob("*.ref.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            name = path.name[: -len(".ref.json")]
            found[name] = payload
    return found


def expected_speech_s(text: str) -> float:
    """Nominal spoken duration from word count (~160 wpm).

    Args:
        text: Clone line.

    Returns:
        Duration in seconds (at least 0.35 s).
    """
    words = len((text or "").split())
    return max(0.35, words / EXPECTED_WORDS_PER_S)


def normalize_clone_pcm(
    pcm: list[float], peak: float = REF_PEAK
) -> list[float]:
    """Rescale int-range PCM into [-peak, peak]. No-op when already in [-1.5, 1.5].

    Args:
        pcm: Clone PCM (may be int-range).
        peak: Target peak.

    Returns:
        Float PCM in about ``[-peak, peak]``.
    """
    if not pcm:
        return []
    mag = max(abs(float(x)) for x in pcm)
    if mag <= PCM_INT_RANGE:
        return [float(x) for x in pcm]
    scale = float(peak) / mag
    return [float(x) * scale for x in pcm]


def _zero_cross_indices(pcm: list[float]) -> list[int]:
    """Sample indices where the sign flips (zeros skipped, matching ZCR).

    Args:
        pcm: Mono PCM.

    Returns:
        Indices of zero crossings.
    """
    if len(pcm) < 2:
        return []
    out: list[int] = []
    prev = float(pcm[0])
    for i, raw in enumerate(pcm[1:], 1):
        cur = float(raw)
        if prev != 0.0 and cur != 0.0 and (prev >= 0.0) != (cur >= 0.0):
            out.append(i)
        prev = cur
    return out


def zero_crossing_rate(pcm: list[float], rate: int) -> float:
    """Zero-crossings per second. Noise sits near ``rate / 2``.

    Args:
        pcm: Mono PCM.
        rate: Sample rate.

    Returns:
        Zero-crossings per second.
    """
    if len(pcm) < 2:
        return 0.0
    dur = len(pcm) / float(int(rate) or SAMPLE_RATE)
    if dur <= 0.0:
        return 0.0
    return len(_zero_cross_indices(pcm)) / dur


def _one_pole_alpha(rate: int, cutoff_hz: float) -> float:
    """Smoothing coefficient for a 1-pole filter at ``cutoff_hz``.

    Args:
        rate: Sample rate.
        cutoff_hz: −3 dB frequency.

    Returns:
        Coefficient in ``(0, 1]``.
    """
    sr = float(max(1, int(rate) or SAMPLE_RATE))
    fc = max(1.0, float(cutoff_hz))
    dt = 1.0 / sr
    rc = 1.0 / (2.0 * math.pi * fc)
    return dt / (rc + dt)


def speech_band_ratio(pcm: list[float], rate: int) -> float:
    """Fraction of RMS in the 300–3400 Hz speech band (1-pole HP then LP).

    Vocoder moans sit below 300 Hz. Spoken formants and sibilants do not.

    Args:
        pcm: Mono PCM.
        rate: Sample rate.

    Returns:
        ``rms(band) / rms(full)``, or 0.0 when the clip is silent.
    """
    if not pcm:
        return 0.0
    full = rms(pcm)
    if full < 1e-8:
        return 0.0
    sr = int(rate) or SAMPLE_RATE
    hp_a = 1.0 - _one_pole_alpha(sr, SPEECH_BAND_LO_HZ)
    lp_a = _one_pole_alpha(sr, SPEECH_BAND_HI_HZ)
    prev_x = float(pcm[0])
    hp_y = 0.0
    lp_y = 0.0
    acc = 0.0
    for raw in pcm:
        x = float(raw)
        hp_y = hp_a * (hp_y + x - prev_x)
        prev_x = x
        lp_y = lp_y + lp_a * (hp_y - lp_y)
        acc += lp_y * lp_y
    band = (acc / len(pcm)) ** 0.5
    return band / full


def tonal_frame_fraction(pcm: list[float], rate: int) -> float:
    """Fraction of voiced 80 ms frames that look like a near-pure tone.

    A HiFT whale/moan is periodic in every frame. Speech mixes vowels with
    consonants, so the fraction stays lower.

    Args:
        pcm: Mono PCM.
        rate: Sample rate.

    Returns:
        Tonal voiced-frame fraction in ``[0, 1]``, or 0.0 when too short.
    """
    sr = int(rate) or SAMPLE_RATE
    frame = max(1, int(sr * TONAL_FRAME_MS / 1000))
    n = len(pcm)
    if n < frame * 2:
        return 0.0
    tonal = 0
    voiced = 0
    i = 0
    while i + frame <= n:
        chunk = pcm[i : i + frame]
        i += frame
        if rms(chunk) < REF_SILENCE_RMS:
            continue
        voiced += 1
        cv = zc_interval_cv(chunk)
        if cv < TONAL_CV_MAX:
            tonal += 1
    if voiced < 4:
        return 0.0
    return tonal / voiced


def zc_interval_cv(pcm: list[float]) -> float:
    """Coefficient of variation of zero-crossing gaps.

    A pure / AM tone has nearly constant period (CV near 0). Speech and
    modulated noise have irregular gaps.

    Args:
        pcm: Mono PCM.
    Returns:
        ``std / mean`` of successive ZC gaps, or 0.0 when too few gaps.
    """
    idxs = _zero_cross_indices(pcm)
    if len(idxs) < ZC_INTERVAL_MIN_GAPS + 1:
        return 0.0
    gaps = [float(idxs[i] - idxs[i - 1]) for i in range(1, len(idxs))]
    mean = sum(gaps) / len(gaps)
    if mean < 1e-8:
        return 0.0
    acc = 0.0
    for gap in gaps:
        delta = gap - mean
        acc += delta * delta
    return (acc / len(gaps)) ** 0.5 / mean


def voiced_fraction(
    pcm: list[float],
    rate: int,
    thresh: float = REF_SILENCE_RMS,
    frame_ms: int = 20,
) -> float:
    """Fraction of 20 ms frames whose RMS is at least ``thresh``.

    Args:
        pcm: Mono PCM.
        rate: Sample rate.
        thresh: Frame RMS threshold.
        frame_ms: Frame size.

    Returns:
        Voiced fraction in ``[0, 1]``.
    """
    sr = int(rate) or SAMPLE_RATE
    n = len(pcm)
    if n == 0:
        return 0.0
    frame = max(1, int(sr * frame_ms / 1000))
    voiced = 0
    total = 0
    i = 0
    while i + frame <= n:
        total += 1
        if rms(pcm[i : i + frame]) >= float(thresh):
            voiced += 1
        i += frame
    if total == 0:
        return 1.0 if rms(pcm) >= float(thresh) else 0.0
    return voiced / total


def is_speech_like(pcm: list[float], rate: int) -> bool:
    """False for silence, noise, a steady tone, or a PerTh/Chatterbox drone.

    Also rejects an F0-glide vocoder moan (whale): energy below the
    300–3400 Hz speech band, or almost every frame a near-pure tone.

    Args:
        pcm: Mono PCM.
        rate: Sample rate.
    Returns:
        True only when RMS, ZCR, voicing, envelope, ZC irregularity,
        speech-band energy, and frame tonality all look like speech.
    """
    if not pcm:
        return False
    if rms(pcm) < REF_MIN_RMS:
        return False
    sr = int(rate) or SAMPLE_RATE
    zcr = zero_crossing_rate(pcm, sr)
    if zcr > sr * ZCR_NOISE_FRAC:
        return False
    if zcr < ZCR_SPEECH_MIN:
        return False
    if voiced_fraction(pcm, sr) < VOICED_MIN_FRAC:
        return False
    if envelope_cv(pcm, sr) < ENVELOPE_CV_MIN:
        return False
    if zc_interval_cv(pcm) < ZC_INTERVAL_CV_MIN:
        return False
    if speech_band_ratio(pcm, sr) < SPEECH_BAND_MIN:
        return False
    return tonal_frame_fraction(pcm, sr) <= TONAL_FRAME_MAX


def crop_hallucination_tail(
    pcm: list[float], rate: int, text: str
) -> list[float]:
    """Onset-crop hush, then keep a prefix up to 1.6× expected spoken duration.

    Args:
        pcm: Clone PCM.
        rate: Sample rate.
        text: Target line (duration prior).

    Returns:
        Cropped PCM.
    """
    trimmed = speech_onset_slice(pcm, rate)
    if not trimmed:
        return trimmed
    cap = max(
        1,
        int(round(expected_speech_s(text) * TAIL_SLACK * (int(rate) or SAMPLE_RATE))),
    )
    if len(trimmed) <= cap:
        return trimmed
    out, _flags = lock_duration(trimmed, cap, room=None, rate=rate)
    return out
