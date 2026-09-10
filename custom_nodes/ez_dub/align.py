"""Duration-lock, overlap-safe mix, and room-tone pad. No numpy/torch."""

from __future__ import annotations

from typing import Any

SAMPLE_RATE = 24000
MAX_SPEED = 1.15
MIN_STRETCH = 0.88
XFADE_MS = 30


def rms(samples: list[float]) -> float:
    """Root-mean-square of a PCM list."""
    if not samples:
        return 0.0
    acc = 0.0
    for value in samples:
        acc += float(value) * float(value)
    return (acc / len(samples)) ** 0.5


def resample_linear(samples: list[float], out_len: int) -> list[float]:
    """Linear resample to ``out_len`` samples.

    Arguments:
        samples: Mono PCM.
        out_len: Desired length.
    Returns:
        New list of length ``out_len`` (empty when out_len <= 0).
    """
    n = len(samples)
    dest = int(out_len)
    if dest <= 0:
        return []
    if n == 0:
        return [0.0] * dest
    if n == dest:
        return [float(x) for x in samples]
    if dest == 1:
        return [float(samples[0])]
    out: list[float] = []
    last = n - 1
    for i in range(dest):
        pos = i * last / (dest - 1)
        lo = int(pos)
        hi = lo + 1 if lo < last else last
        frac = pos - lo
        out.append(float(samples[lo]) * (1.0 - frac) + float(samples[hi]) * frac)
    return out


def fit_turn(
    synth: list[float],
    rate: int,
    window_s: float,
    spill_s: float = 0.0,
    max_speed: float = MAX_SPEED,
    min_stretch: float = MIN_STRETCH,
) -> tuple[list[float], dict[str, Any]]:
    """Fit a clone into ``window_s``, spilling only into the following gap.

    Arguments:
        synth: Synthesized PCM.
        rate: Sample rate.
        window_s: Original turn length in seconds.
        spill_s: Seconds of following gap that may be used.
        max_speed: TTS speed ceiling.
        min_stretch: Time-stretch floor (below this, trim).
    Returns:
        ``(pcm, flags)`` with speed/stretch/trimmed/padded/spill.
    """
    flags: dict[str, Any] = {
        "speed": 1.0,
        "stretch": 1.0,
        "trimmed": False,
        "padded": False,
        "spill": False,
    }
    sr = int(rate) if rate else SAMPLE_RATE
    target = max(1, int(round(float(window_s) * sr)))
    max_len = target + max(0, int(round(float(spill_s) * sr)))
    n = len(synth)
    if n == 0:
        flags["padded"] = True
        return [0.0] * target, flags
    if n <= target:
        if n < target:
            flags["padded"] = True
            return [float(x) for x in synth] + [0.0] * (target - n), flags
        return [float(x) for x in synth], flags
    if n <= max_len:
        flags["spill"] = True
        return [float(x) for x in synth], flags
    min_len = max(1, int(round(n * float(min_stretch) / float(max_speed))))
    flags["speed"] = float(max_speed)
    flags["stretch"] = float(min_stretch)
    flags["spill"] = max_len > target
    if min_len > max_len:
        flags["trimmed"] = True
    return resample_linear(synth, max_len), flags


def lock_duration(
    mix: list[float],
    target_n: int,
    room: list[float] | None = None,
    rate: int = SAMPLE_RATE,
) -> tuple[list[float], dict[str, bool]]:
    """Pad or fade-trim so ``len(mix) == target_n``.

    Arguments:
        mix: Mixed PCM.
        target_n: Source sample count.
        room: Optional room-tone loop for padding.
        rate: Sample rate (fade length).
    Returns:
        ``(pcm, {padded, trimmed})``.
    """
    dest = max(0, int(target_n))
    n = len(mix)
    if n == dest:
        return [float(x) for x in mix], {"padded": False, "trimmed": False}
    if n < dest:
        pad = [float(x) for x in room] if room else [0.0]
        if not pad:
            pad = [0.0]
        extra: list[float] = []
        while n + len(extra) < dest:
            extra.extend(pad)
        return [float(x) for x in mix] + extra[: dest - n], {
            "padded": True,
            "trimmed": False,
        }
    out = [float(x) for x in mix[:dest]]
    fade = min(max(1, int(0.01 * int(rate or SAMPLE_RATE))), dest)
    if fade > 1:
        for i in range(fade):
            out[dest - fade + i] *= (fade - 1 - i) / (fade - 1)
    return out, {"padded": False, "trimmed": True}


def collect_room_tone(
    source: list[float],
    turns: list[dict[str, Any]],
    rate: int,
    want: int | None = None,
) -> list[float]:
    """PCM from non-speech gaps for padding (not digital silence)."""
    sr = int(rate) or SAMPLE_RATE
    need = int(want) if want else max(1, int(0.25 * sr))
    n = len(source)
    speech = [False] * n
    for turn in turns:
        a = max(0, int(round(float(turn.get("t0") or 0.0) * sr)))
        b = min(n, int(round(float(turn.get("t1") or 0.0) * sr)))
        for i in range(a, b):
            speech[i] = True
    gaps: list[float] = []
    for i, sample in enumerate(source):
        if not speech[i]:
            gaps.append(float(sample))
        if len(gaps) >= need:
            break
    if len(gaps) >= need:
        return gaps[:need]
    if gaps:
        while len(gaps) < need:
            gaps.extend(gaps[: max(1, need - len(gaps))])
        return gaps[:need]
    return [0.0] * need


def build_timeline(
    source: list[float],
    clones: list[dict[str, Any]],
    rate: int,
    keep_bed: bool = True,
    xfade_ms: int = XFADE_MS,
) -> list[float]:
    """Replace speech windows with clones; keep bed in gaps when requested.

    Arguments:
        source: Original mix PCM (defines duration).
        clones: Items with ``t0`` and ``pcm``.
        rate: Sample rate.
        keep_bed: When True, non-speech keeps ``source``.
        xfade_ms: Linear edge fade in milliseconds.
    Returns:
        Mix the same length as ``source``.
    """
    n = len(source)
    mix = [float(x) for x in source] if keep_bed else [0.0] * n
    sr = int(rate) or SAMPLE_RATE
    fade = max(1, int(sr * max(0, int(xfade_ms)) / 1000))
    for item in clones:
        pcm = [float(x) for x in (item.get("pcm") or [])]
        start = int(round(float(item.get("t0") or 0.0) * sr))
        length = len(pcm)
        if length == 0:
            continue
        for i, sample in enumerate(pcm):
            j = start + i
            if j < 0 or j >= n:
                continue
            gain = 1.0
            if i < fade:
                gain = i / fade
            remaining = length - 1 - i
            if remaining < fade:
                gain = min(gain, remaining / fade if fade else 1.0)
            bed = mix[j]
            mix[j] = bed * (1.0 - gain) + sample * gain
    return mix
