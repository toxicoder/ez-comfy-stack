"""Fail-closed accept gate before 90s concat (Wave 4.7).

Hermetic at import: stdlib only. ffprobe is resolved at call time.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from .jobstore import DURATION_S, DURATION_TOL, load_state, shot_mp4
from .shots import SHOT_COUNT, film_slug
from .stems import LUFS_TARGET, LUFS_TOL, lufs_in_band, parse_lufs

ACCEPT_WIDTH = 1280
ACCEPT_HEIGHT = 704
ACCEPT_FPS = 24.0
ACCEPT_FPS_TOL = 0.05
MASTER_DURATION_S = 90.00
MASTER_TOL_S = 0.10
AUDIO_SYNC_TOL_S = 0.050
# World-only speech-band gate (no neural VAD). Speech-shaped energy is
# 300–3400 Hz RMS within 8 dB of full-band, a peak above −18 dB, and a
# window longer than 0.40 s. Band-limited silencedetect then treats
# regions longer than 0.40 s as non-transients (not footfall/splash).
SPEECH_BAND_DB = 8.0
SPEECH_RATIO_MIN = 10 ** (-SPEECH_BAND_DB / 20.0)
SPEECH_PEAK_DB = -18.0
SPEECH_PEAK_WINDOW_S = 0.40
SILENCE_NOISE_DB = -32
SILENCE_MIN_S = 0.20
NONSILENCE_BUDGET_S = 1.2
SPEECH_BAND_FILTER = "highpass=f=300,lowpass=f=3400"
ASTATS_FILTER = "astats=metadata=1:reset=1"
_RMS_DB_RE = re.compile(r"RMS level dB:\s*([-+]?\d+(?:\.\d+)?)", re.I)
_PEAK_DB_RE = re.compile(r"Peak level dB:\s*([-+]?\d+(?:\.\d+)?)", re.I)
_SILENCE_START_RE = re.compile(r"silence_start:\s*([-+]?\d+(?:\.\d+)?)")
_SILENCE_END_RE = re.compile(r"silence_end:\s*([-+]?\d+(?:\.\d+)?)")
RunFn = Callable[..., Any]


def find_ffprobe() -> str | None:
    """Resolve ffprobe on PATH, or None."""
    return shutil.which("ffprobe")


def find_ffmpeg() -> str | None:
    """Resolve ffmpeg on PATH, or None."""
    return shutil.which("ffmpeg")


def _run(
    argv: list[str],
    *,
    run: RunFn = subprocess.run,
) -> subprocess.CompletedProcess[str]:
    return run(argv, check=False, capture_output=True, text=True)


def probe_duration_s(
    path: Path,
    *,
    ffprobe: str | None = None,
    run: RunFn = subprocess.run,
) -> float | None:
    """Format duration seconds, or None."""
    exe = ffprobe or find_ffprobe()
    if not exe or not path.is_file():
        return None
    try:
        proc = _run(
            [exe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
            run=run,
        )
    except OSError:
        return None
    text = (proc.stdout or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def probe_wh(
    path: Path,
    *,
    ffprobe: str | None = None,
    run: RunFn = subprocess.run,
) -> tuple[int, int] | None:
    """First video stream width×height, or None."""
    exe = ffprobe or find_ffprobe()
    if not exe or not path.is_file():
        return None
    try:
        proc = _run(
            [
                exe,
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height",
                "-of",
                "csv=p=0",
                str(path),
            ],
            run=run,
        )
    except OSError:
        return None
    text = (proc.stdout or "").strip()
    if not text or "," not in text:
        return None
    left, right = text.split(",", 1)
    try:
        return int(left), int(right)
    except ValueError:
        return None


def probe_has_audio(
    path: Path,
    *,
    ffprobe: str | None = None,
    run: RunFn = subprocess.run,
) -> bool:
    """True when stream 0 of type audio exists."""
    exe = ffprobe or find_ffprobe()
    if not exe or not path.is_file():
        return False
    try:
        proc = _run(
            [
                exe,
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=codec_type",
                "-of",
                "csv=p=0",
                str(path),
            ],
            run=run,
        )
    except OSError:
        return False
    return "audio" in (proc.stdout or "").lower()


def stem_mix_path(dest: Path, sid: str) -> Path | None:
    """Return stems/<id>/mix.m4a or mix.mp4 when present."""
    folder = dest / "stems" / sid
    for name in ("mix.mp4", "mix.m4a", "mix.wav"):
        path = folder / name
        if path.is_file():
            return path
    return None


def probe_lufs(
    path: Path,
    *,
    ffmpeg: str | None = None,
    run: RunFn = subprocess.run,
) -> float | None:
    """Measure integrated loudness via ffmpeg loudnorm JSON, or None."""
    exe = ffmpeg or shutil.which("ffmpeg")
    if not exe or not path.is_file():
        return None
    try:
        proc = _run(
            [
                exe,
                "-i",
                str(path),
                "-af",
                "loudnorm=I=-14:LRA=11:TP=-1.5:print_format=json",
                "-f",
                "null",
                "-",
            ],
            run=run,
        )
    except OSError:
        return None
    return parse_lufs((proc.stderr or "") + (proc.stdout or ""))


def parse_astats_rms_db(text: str) -> float | None:
    """Last astats RMS level dB (Overall), or None."""
    matches = _RMS_DB_RE.findall(text or "")
    if not matches:
        return None
    try:
        return float(matches[-1])
    except ValueError:
        return None


def parse_astats_peak_db(text: str) -> float | None:
    """Last astats Peak level dB (Overall), or None."""
    matches = _PEAK_DB_RE.findall(text or "")
    if not matches:
        return None
    try:
        return float(matches[-1])
    except ValueError:
        return None


def parse_sustained_nonsilence_s(text: str, duration_s: float) -> float:
    """Seconds of non-silence longer than ``SPEECH_PEAK_WINDOW_S``.

    Transients shorter than 0.40 s (footfall/splash) are ignored. No
    silencedetect events means the whole clip is treated as non-silence.
    """
    if duration_s <= 0:
        return 0.0
    starts = [float(x) for x in _SILENCE_START_RE.findall(text or "")]
    ends = [float(x) for x in _SILENCE_END_RE.findall(text or "")]
    silences: list[tuple[float, float]] = []
    for index, start in enumerate(starts):
        end = ends[index] if index < len(ends) else duration_s
        if end > start:
            silences.append((start, end))
    silences.sort()
    merged: list[tuple[float, float]] = []
    for start, end in silences:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    nonsilence = 0.0
    cursor = 0.0
    for start, end in merged:
        gap = start - cursor
        if gap > SPEECH_PEAK_WINDOW_S:
            nonsilence += gap
        cursor = max(cursor, end)
    tail = duration_s - cursor
    if tail > SPEECH_PEAK_WINDOW_S:
        nonsilence += tail
    return nonsilence


def _ffmpeg_af(
    path: Path,
    af: str,
    *,
    ffmpeg: str | None = None,
    run: RunFn = subprocess.run,
) -> str:
    """Run ffmpeg ``-af`` to null and return stderr+stdout, or empty."""
    exe = ffmpeg or find_ffmpeg()
    if not exe or not path.is_file():
        return ""
    try:
        proc = _run(
            [exe, "-i", str(path), "-af", af, "-f", "null", "-"],
            run=run,
        )
    except OSError:
        return ""
    return (proc.stderr or "") + (proc.stdout or "")


def probe_speech_band_ratio(
    path: Path,
    *,
    ffmpeg: str | None = None,
    run: RunFn = subprocess.run,
) -> float | None:
    """Speech-band RMS / full-band RMS, or None if unreadable.

    Speech band is 300–3400 Hz via ``highpass=f=300,lowpass=f=3400`` then
    astats. A ratio at or above ``SPEECH_RATIO_MIN`` (~0.398, 8 dB) means
    the mix is voice-shaped.
    """
    speech_text = _ffmpeg_af(
        path,
        f"{SPEECH_BAND_FILTER},{ASTATS_FILTER}",
        ffmpeg=ffmpeg,
        run=run,
    )
    full_text = _ffmpeg_af(path, ASTATS_FILTER, ffmpeg=ffmpeg, run=run)
    speech_db = parse_astats_rms_db(speech_text)
    full_db = parse_astats_rms_db(full_text)
    if speech_db is None or full_db is None:
        return None
    speech = 10 ** (speech_db / 20.0)
    full = 10 ** (full_db / 20.0)
    if full <= 0 or not math.isfinite(speech) or not math.isfinite(full):
        return None
    return speech / full


def probe_speech_peak_db(
    path: Path,
    *,
    ffmpeg: str | None = None,
    run: RunFn = subprocess.run,
) -> float | None:
    """Speech-band peak dBFS, or None."""
    text = _ffmpeg_af(
        path,
        f"{SPEECH_BAND_FILTER},{ASTATS_FILTER}",
        ffmpeg=ffmpeg,
        run=run,
    )
    return parse_astats_peak_db(text)


def probe_sustained_nonsilence_s(
    path: Path,
    *,
    duration_s: float | None = None,
    ffmpeg: str | None = None,
    ffprobe: str | None = None,
    run: RunFn = subprocess.run,
) -> float | None:
    """Band-limited non-silence longer than 0.40 s, or None."""
    dur = duration_s if duration_s is not None else probe_duration_s(
        path, ffprobe=ffprobe, run=run
    )
    if dur is None:
        return None
    af = (
        f"{SPEECH_BAND_FILTER},"
        f"silencedetect=noise={SILENCE_NOISE_DB}dB:d={SILENCE_MIN_S:.2f}"
    )
    text = _ffmpeg_af(path, af, ffmpeg=ffmpeg, run=run)
    if not text and dur > 0:
        # ffmpeg missing / failed — do not invent coverage.
        return None
    return parse_sustained_nonsilence_s(text, dur)


def world_only_speech_defects(
    path: Path,
    label: str,
    *,
    duration_s: float | None = None,
    ffmpeg: str | None = None,
    ffprobe: str | None = None,
    run: RunFn = subprocess.run,
) -> list[str]:
    """Defects when a world-only mix looks like sustained speech."""
    ratio = probe_speech_band_ratio(path, ffmpeg=ffmpeg, run=run)
    if ratio is None:
        return [f"{label}: could not measure speech-band"]
    peak = probe_speech_peak_db(path, ffmpeg=ffmpeg, run=run)
    sustained = probe_sustained_nonsilence_s(
        path,
        duration_s=duration_s,
        ffmpeg=ffmpeg,
        ffprobe=ffprobe,
        run=run,
    )
    if peak is None or sustained is None:
        return [f"{label}: could not measure speech-band peak/silence"]
    defects: list[str] = []
    if (
        ratio >= SPEECH_RATIO_MIN
        and peak > SPEECH_PEAK_DB
        and sustained > SPEECH_PEAK_WINDOW_S
    ):
        defects.append(
            f"{label}: speech-band ratio {ratio:.3f} with peak {peak:.1f} dB "
            f"over {sustained:.2f}s (world-only)"
        )
    if sustained > NONSILENCE_BUDGET_S:
        defects.append(
            f"{label}: sustained speech-band non-silence {sustained:.2f}s "
            f"(need ≤ {NONSILENCE_BUDGET_S}s transients)"
        )
    return defects


def probe_fps(
    path: Path,
    *,
    ffprobe: str | None = None,
    run: RunFn = subprocess.run,
) -> float | None:
    """First video stream frame rate, or None."""
    exe = ffprobe or find_ffprobe()
    if not exe or not path.is_file():
        return None
    try:
        proc = _run(
            [
                exe,
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=r_frame_rate",
                "-of",
                "csv=p=0",
                str(path),
            ],
            run=run,
        )
    except OSError:
        return None
    text = (proc.stdout or "").strip()
    if not text:
        return None
    token = text.split(",")[0].strip()
    if "/" in token:
        left, right = token.split("/", 1)
        try:
            denom = float(right)
            if denom == 0:
                return None
            return float(left) / denom
        except ValueError:
            return None
    try:
        return float(token)
    except ValueError:
        return None


def probe_audio_duration_s(
    path: Path,
    *,
    ffprobe: str | None = None,
    run: RunFn = subprocess.run,
) -> float | None:
    """Audio stream duration seconds, else format duration, or None."""
    exe = ffprobe or find_ffprobe()
    if not exe or not path.is_file():
        return None
    try:
        proc = _run(
            [
                exe,
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=duration",
                "-of",
                "csv=p=0",
                str(path),
            ],
            run=run,
        )
    except OSError:
        return None
    text = (proc.stdout or "").strip()
    token = text.split(",")[0].strip() if text else ""
    if token and token.upper() != "N/A":
        try:
            return float(token)
        except ValueError:
            pass
    return probe_duration_s(path, ffprobe=exe, run=run)


def accept_master(
    mp4: Path,
    *,
    ffprobe: str | None = None,
    ffmpeg: str | None = None,
    run: RunFn = subprocess.run,
    audio_policy: str = "world-only",
) -> list[str]:
    """Defects for a published 90s master (empty = pass)."""
    defects: list[str] = []
    if not mp4.is_file():
        return [f"master: missing {mp4}"]
    dur = probe_duration_s(mp4, ffprobe=ffprobe, run=run)
    if dur is None or abs(dur - MASTER_DURATION_S) > MASTER_TOL_S:
        defects.append(
            f"master: duration {dur!r} (need {MASTER_DURATION_S}±{MASTER_TOL_S})"
        )
    wh = probe_wh(mp4, ffprobe=ffprobe, run=run)
    if wh != (ACCEPT_WIDTH, ACCEPT_HEIGHT):
        defects.append(
            f"master: size {wh!r} (need {ACCEPT_WIDTH}x{ACCEPT_HEIGHT})"
        )
    fps = probe_fps(mp4, ffprobe=ffprobe, run=run)
    if fps is None or abs(fps - ACCEPT_FPS) > ACCEPT_FPS_TOL:
        defects.append(f"master: fps {fps!r} (need {ACCEPT_FPS})")
    if not probe_has_audio(mp4, ffprobe=ffprobe, run=run):
        defects.append("master: missing audio")
    else:
        audio_dur = probe_audio_duration_s(mp4, ffprobe=ffprobe, run=run)
        if audio_dur is None or (
            dur is not None and abs(audio_dur - dur) > AUDIO_SYNC_TOL_S
        ):
            defects.append(
                f"master: audio duration {audio_dur!r} vs video {dur!r} "
                f"(need within {AUDIO_SYNC_TOL_S * 1000:.0f} ms)"
            )
    if audio_policy == "world-only":
        defects.extend(
            world_only_speech_defects(
                mp4,
                "master",
                duration_s=dur,
                ffmpeg=ffmpeg,
                ffprobe=ffprobe,
                run=run,
            )
        )
    return defects


def accept_shot(
    dest: Path,
    row: dict[str, Any],
    *,
    ffprobe: str | None = None,
    ffmpeg: str | None = None,
    run: RunFn = subprocess.run,
    audio_policy: str = "world-only",
    probe_lufs_fn: Callable[..., float | None] | None = None,
) -> list[str]:
    """Return defect strings for one shot (empty = pass)."""
    sid = str(row.get("id") or "")
    defects: list[str] = []
    if row.get("status") != "ok":
        defects.append(f"{sid}: status {row.get('status')!r} (need ok)")
        return defects
    mp4 = dest / row["mp4"] if row.get("mp4") else shot_mp4(dest, sid)
    if not mp4.is_file():
        defects.append(f"{sid}: missing {mp4}")
        return defects
    dur = probe_duration_s(mp4, ffprobe=ffprobe, run=run)
    if dur is None or abs(dur - DURATION_S) > DURATION_TOL:
        defects.append(f"{sid}: duration {dur!r} (need {DURATION_S}±{DURATION_TOL})")
    wh = probe_wh(mp4, ffprobe=ffprobe, run=run)
    if wh != (ACCEPT_WIDTH, ACCEPT_HEIGHT):
        defects.append(f"{sid}: size {wh!r} (need {ACCEPT_WIDTH}x{ACCEPT_HEIGHT})")
    backend = str(row.get("backend") or "ltx")
    if backend != "wan" and not probe_has_audio(mp4, ffprobe=ffprobe, run=run):
        defects.append(f"{sid}: missing audio (LTX shots must mux world audio)")
    if audio_policy == "stems":
        mix = stem_mix_path(dest, sid)
        if mix is None:
            defects.append(f"{sid}: missing stem mix under stems/{sid}/")
        else:
            measurer = probe_lufs_fn or probe_lufs
            lufs = measurer(mix, run=run)
            if lufs is None or not lufs_in_band(lufs):
                defects.append(
                    f"{sid}: stem loudness {lufs!r} (need {LUFS_TARGET}±{LUFS_TOL} LUFS)"
                )
    elif audio_policy == "world-only" and backend != "wan":
        defects.extend(
            world_only_speech_defects(
                mp4,
                sid,
                duration_s=dur,
                ffmpeg=ffmpeg,
                ffprobe=ffprobe,
                run=run,
            )
        )
    return defects


def accept_film(
    dest: Path,
    *,
    ffprobe: str | None = None,
    ffmpeg: str | None = None,
    run: RunFn = subprocess.run,
    probe_lufs_fn: Callable[..., float | None] | None = None,
) -> dict[str, Any]:
    """Fail closed: all 18 shots ok, 5.00s, 1280×704, LTX audio present."""
    state = load_state(dest)
    defects: list[str] = []
    shots = list(state.get("shots") or [])
    audio_policy = str(state.get("audio_policy") or "world-only")
    if len(shots) != SHOT_COUNT:
        defects.append(f"shot count {len(shots)} (need {SHOT_COUNT})")
    for row in shots:
        defects.extend(
            accept_shot(
                dest,
                row,
                ffprobe=ffprobe,
                ffmpeg=ffmpeg,
                run=run,
                audio_policy=audio_policy,
                probe_lufs_fn=probe_lufs_fn,
            )
        )
    slug = str(state.get("slug") or "")
    master_candidates = [dest / "publish" / "master.mp4"]
    if slug:
        master_candidates.append(dest.parent.parent / f"ez_{slug}_90s.mp4")
    for candidate in master_candidates:
        if candidate.is_file():
            defects.extend(
                accept_master(
                    candidate,
                    ffprobe=ffprobe,
                    ffmpeg=ffmpeg,
                    run=run,
                    audio_policy=audio_policy,
                )
            )
            break
    report = {
        "film": state.get("film"),
        "slug": state.get("slug"),
        "ok": not defects,
        "defects": defects,
        "width": ACCEPT_WIDTH,
        "height": ACCEPT_HEIGHT,
        "duration_s": DURATION_S,
    }
    publish = dest / "publish"
    publish.mkdir(parents=True, exist_ok=True)
    (publish / "accept.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ez_film.accept")
    parser.add_argument("--dest", required=True, help="films/<slug> jobstore directory")
    args = parser.parse_args(argv)
    try:
        report = accept_film(Path(args.dest))
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(report))
    if not report["ok"]:
        for line in report["defects"]:
            print(line, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())


def film_dest(output_dir: Path, film: str) -> Path:
    """``${COMFY_OUTPUT_DIR}/films/<slug>``."""
    return Path(output_dir) / "films" / film_slug(film)
