"""Fail-closed accept gate before 90s concat (Wave 4.7).

Hermetic at import: stdlib only. ffprobe is resolved at call time.
"""

from __future__ import annotations

import argparse
import json
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
RunFn = Callable[..., Any]


def find_ffprobe() -> str | None:
    """Resolve ffprobe on PATH, or None."""
    return shutil.which("ffprobe")


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


def accept_shot(
    dest: Path,
    row: dict[str, Any],
    *,
    ffprobe: str | None = None,
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
    return defects


def accept_film(
    dest: Path,
    *,
    ffprobe: str | None = None,
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
                run=run,
                audio_policy=audio_policy,
                probe_lufs_fn=probe_lufs_fn,
            )
        )
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
