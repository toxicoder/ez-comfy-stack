"""Duration-lock, overlap-safe mix, and room-tone pad. No numpy/torch."""

from __future__ import annotations

import math
import shutil
import struct
import subprocess
from collections.abc import Callable
from typing import Any

SAMPLE_RATE = 24000
MAX_SPEED = 1.25
MIN_STRETCH = 0.88
XFADE_MS = 30
STRETCH_WINDOW_S = 0.02
STRETCH_SEARCH_S = 0.005
ATEMPO_MIN = 0.5
ATEMPO_MAX = 2.0

# Tests inject this to keep fit_turn hermetic (no host ffmpeg).
stretch_hook: Callable[[list[float], int, int], list[float]] | None = None


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


def time_stretch(
    samples: list[float],
    out_len: int,
    rate: int = SAMPLE_RATE,
) -> list[float]:
    """Pitch-preserving WSOLA stretch to ``out_len`` samples.

    Linear resample changes pitch (chipmunk / helium). Output hop is
    fixed; input hop follows ``out_len / len(samples)``. Lag search is
    capped at 5 ms and indexed with the input hop. Short clips fall
    back to linear. Production prefers ffmpeg ``atempo`` via
    :func:`pitch_preserving_stretch`.

    Arguments:
        samples: Mono PCM.
        out_len: Desired length in samples.
        rate: Sample rate (window size is 20 ms).
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
    sr = int(rate) or SAMPLE_RATE
    win = max(32, int(round(STRETCH_WINDOW_S * sr)))
    if win % 2:
        win += 1
    hop_out = max(1, win // 2)
    if n < win or dest < win:
        return resample_linear(samples, dest)
    scale = dest / n
    hop_in = hop_out / scale if scale > 1e-8 else float(hop_out)
    n_grains = 1 + max(0, dest - win) // hop_out
    if n_grains < 2:
        return resample_linear(samples, dest)
    last_i = win - 1
    hann = [0.5 - 0.5 * math.cos(2.0 * math.pi * i / last_i) for i in range(win)]
    acc = [0.0] * dest
    wsum = [0.0] * dest
    search = max(1, int(round(STRETCH_SEARCH_S * sr)))
    overlap = max(1, win - hop_out)
    hop_in_i = max(1, int(round(hop_in)))
    prev_src = 0
    for grain in range(n_grains):
        natural = int(round(grain * hop_in))
        if natural < 0:
            natural = 0
        if natural + win > n:
            natural = max(0, n - win)
        src = natural
        if grain > 0:
            lo = max(0, natural - search)
            hi = min(n - win, natural + search)
            best = natural
            best_c = -1e18
            prev_tail = prev_src + hop_in_i
            if prev_tail + overlap > n:
                prev_tail = max(0, n - overlap)
            cand = lo
            while cand <= hi:
                corr = 0.0
                i = 0
                while i < overlap:
                    src_i = prev_tail + i
                    if src_i >= n:
                        break
                    corr += float(samples[src_i]) * float(samples[cand + i])
                    i += 1
                if corr > best_c:
                    best_c = corr
                    best = cand
                cand += 1
            src = best
        prev_src = src
        dst = grain * hop_out
        if dst + win > dest:
            dst = max(0, dest - win)
        for i in range(win):
            weight = hann[i]
            acc[dst + i] += float(samples[src + i]) * weight
            wsum[dst + i] += weight
    return [acc[i] / wsum[i] if wsum[i] > 1e-8 else 0.0 for i in range(dest)]


def _ffmpeg_atempo(
    samples: list[float], out_len: int, rate: int
) -> list[float] | None:
    """Pitch-preserving stretch via ffmpeg ``atempo``. None on miss/fail.

    Arguments:
        samples: Mono PCM.
        out_len: Desired length in samples.
        rate: Sample rate.
    Returns:
        PCM of length ``out_len``, or None when ffmpeg cannot run.
    """
    dest = int(out_len)
    n = len(samples)
    sr = int(rate) or SAMPLE_RATE
    if dest <= 0 or n <= 0 or sr < 1 or n == dest:
        return None
    if shutil.which("ffmpeg") is None:
        return None
    factor = n / dest
    if factor < ATEMPO_MIN or factor > ATEMPO_MAX:
        return None
    raw = b"".join(struct.pack("<f", float(value)) for value in samples)
    try:
        proc = subprocess.run(
            [
                "ffmpeg",
                "-nostdin",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "f32le",
                "-ar",
                str(sr),
                "-ac",
                "1",
                "-i",
                "pipe:0",
                "-filter:a",
                f"atempo={factor:.6f}",
                "-f",
                "f32le",
                "pipe:1",
            ],
            input=raw,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    if int(proc.returncode) != 0 or not proc.stdout:
        return None
    count = len(proc.stdout) // 4
    if count <= 0:
        return None
    unpacked = struct.unpack("<" + "f" * count, proc.stdout[: count * 4])
    pcm = [float(value) for value in unpacked]
    if len(pcm) == dest:
        return pcm
    return resample_linear(pcm, dest)


def pitch_preserving_stretch(
    samples: list[float],
    out_len: int,
    rate: int = SAMPLE_RATE,
) -> list[float]:
    """Stretch to ``out_len`` without changing pitch.

    Prefers ffmpeg ``atempo``, then WSOLA. Tests may set ``stretch_hook``.

    Arguments:
        samples: Mono PCM.
        out_len: Desired length in samples.
        rate: Sample rate.
    Returns:
        New list of length ``out_len`` (empty when out_len <= 0).
    """
    dest = int(out_len)
    n = len(samples)
    if dest <= 0:
        return []
    if n == 0:
        return [0.0] * dest
    if n == dest:
        return [float(x) for x in samples]
    hook = stretch_hook
    if hook is not None:
        return hook(samples, dest, int(rate) or SAMPLE_RATE)
    got = _ffmpeg_atempo(samples, dest, rate)
    if got is not None:
        return got
    return time_stretch(samples, dest, rate)


def fit_turn(
    synth: list[float],
    rate: int,
    window_s: float,
    spill_s: float = 0.0,
    max_speed: float = MAX_SPEED,
    min_stretch: float = MIN_STRETCH,
) -> tuple[list[float], dict[str, Any]]:
    """Fit a clone into ``window_s``, spilling only into the following gap.

    Never time-compress more than ``max_speed`` (default 1.25×). Overflow
    after that fade-trims the start of the sentence. ``min_stretch`` is
    accepted for call-site compatibility and is not stacked with max_speed.

    Arguments:
        synth: Synthesized PCM.
        rate: Sample rate.
        window_s: Original turn length in seconds.
        spill_s: Seconds of following gap that may be used.
        max_speed: Time-compression ceiling (pitch-preserving stretch).
        min_stretch: Ignored (legacy stacked floor). Cap is max_speed only.
    Returns:
        ``(pcm, flags)`` with speed/stretch/trimmed/padded/spill.
    """
    del min_stretch
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
    cap = float(max_speed) if max_speed else MAX_SPEED
    if cap < 1.0:
        cap = 1.0
    min_ok = max(1, int(math.ceil(n / cap)))
    flags["spill"] = max_len > target
    if max_len >= min_ok:
        flags["speed"] = n / max_len
        flags["stretch"] = max_len / n
        return pitch_preserving_stretch(synth, max_len, sr), flags
    flags["trimmed"] = True
    flags["speed"] = cap
    flags["stretch"] = 1.0 / cap
    stretched = pitch_preserving_stretch(synth, min_ok, sr)
    trimmed, _lock = lock_duration(stretched, max_len, room=None, rate=sr)
    return trimmed, flags


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
