"""PCM speech/DSP helpers for dub (onset, VAD, speech-like, crop).

Constants that tests monkeypatch on :mod:`ez_dub.pipeline` (currently
``ONSET_PAD_S``) are read from that module at call time.
"""

from __future__ import annotations

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
ONSET_ABS = 0.02
ONSET_REL = 0.12
ONSET_HOLD_S = 0.08
REF_MIN_RMS = 0.008
REF_SILENCE_RMS = 0.008
REF_XFADE_MS = 30
REF_PEAK = 0.89
REF_MIN_TURN_S = 0.8
REF_SINGLE_S = 6.0
REF_TARGET_S = 8.0
REF_MAX_S = 10.0
REF_PURITY_MIN_DIM = 8
REF_PURITY_COSINE = 0.55
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
    if not pcm:
        return []
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
        return [float(x) for x in pcm]
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
    if not vectors or len(vectors[0]) < REF_PURITY_MIN_DIM:
        return kept
    dim = len(vectors[0])
    centroid = [0.0] * dim
    for vector in vectors:
        for i, value in enumerate(vector[:dim]):
            centroid[i] += float(value)
    scale = 1.0 / len(vectors)
    centroid = [c * scale for c in centroid]
    pure: list[dict[str, Any]] = []
    for item, vector in zip(kept, vectors):
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
    """Build a 3–10 s clean ref wav (and transcript sidecar) per speaker.

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
    cap = int((max_s if max_s > 0 else REF_MAX_S) * sr)
    target = int(REF_TARGET_S * sr)
    for speaker, group in by_spk.items():
        candidates = _filter_ref_turns(group, samples, sr)
        if not candidates:
            continue
        ordered = sorted(
            candidates,
            key=lambda t: (
                (float(t["t1"]) - float(t["t0"]))
                * max(_turn_rms(t, t.get("_pcm") or []), 1e-6)
            ),
            reverse=True,
        )
        used: list[dict[str, Any]] = []
        chunks: list[list[float]] = []
        best = ordered[0]
        best_dur = float(best["t1"]) - float(best["t0"])
        if best_dur >= REF_SINGLE_S:
            used = [best]
            chunks = [list(best.get("_pcm") or [])]
        else:
            total = 0
            for turn in ordered:
                chunk = list(turn.get("_pcm") or [])
                if not chunk:
                    continue
                used.append(turn)
                chunks.append(chunk)
                total += len(chunk)
                if total >= target:
                    break
        pcm = _concat_crossfade(chunks, sr)
        pcm = _trim_silence(pcm, sr)
        if len(pcm) > cap:
            pcm = pcm[:cap]
        pcm = _peak_normalize(pcm)
        if not pcm:
            continue
        path = dest / f"{speaker}.wav"
        write_wav(path, pcm, sr)
        lines = [str(t.get("text") or "").strip() for t in used]
        note = " ".join(part for part in lines if part)
        if note:
            path.with_suffix(".txt").write_text(note + "\n", encoding="utf-8")
        refs[speaker] = path
    return refs


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

    Args:
        pcm: Mono PCM.
        rate: Sample rate.
    Returns:
        True only when RMS, ZCR, voicing, envelope, and ZC irregularity
        all look like speech (not a 60–120 Hz leftover tone).
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
    return zc_interval_cv(pcm) >= ZC_INTERVAL_CV_MIN


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
