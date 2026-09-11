"""Picture-lock stem mix: DX / FX / BG / MX → duck → YouTube loudnorm."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

DUCK_DB = -15.0
LOUDNORM = "loudnorm=I=-14:LRA=11:TP=-1.5"
AAC_BITRATE = "192k"
AAC_RATE = "48000"
LUFS_TARGET = -14.0
LUFS_TOL = 2.0
RunFn = Callable[..., Any]


def find_ffmpeg() -> str | None:
    """Resolve ffmpeg on PATH, or None."""
    return shutil.which("ffmpeg")


def _run(
    argv: list[str],
    *,
    run: RunFn = subprocess.run,
) -> subprocess.CompletedProcess[str]:
    return run(argv, check=False, capture_output=True, text=True)


def mix_filter(
    *,
    has_dx: bool,
    bed_count: int,
    duck_db: float = DUCK_DB,
) -> str:
    """Build filter_complex for optional DX plus ducked beds.

    Bed inputs are numbered after DX (or from 0 when no DX). Empty DX skips duck.
    """
    if bed_count < 1:
        raise ValueError("need at least one bed stem (BG/FX/MX)")
    if has_dx:
        parts: list[str] = []
        ducked: list[str] = []
        for index in range(bed_count):
            label = f"b{index}"
            parts.append(f"[{index + 1}:a]volume={duck_db}dB[{label}]")
            ducked.append(f"[{label}]")
        mix_n = bed_count + 1
        parts.append(
            "[0:a]"
            + "".join(ducked)
            + f"amix=inputs={mix_n}:duration=first:dropout_transition=0,"
            + LOUDNORM
            + "[a]"
        )
        return ";".join(parts)
    if bed_count == 1:
        return f"[0:a]{LOUDNORM}[a]"
    labels = "".join(f"[{i}:a]" for i in range(bed_count))
    return (
        f"{labels}amix=inputs={bed_count}:duration=first:dropout_transition=0,"
        f"{LOUDNORM}[a]"
    )


def mix_argv(
    stems: list[Path],
    dest: Path,
    *,
    has_dx: bool,
    duck_db: float = DUCK_DB,
    video: Path | None = None,
) -> list[str]:
    """ffmpeg argv: mix stems, optional video stream-copy, YouTube loudnorm."""
    if not stems:
        raise ValueError("no stems")
    argv = ["ffmpeg", "-y"]
    if video is not None:
        argv.extend(["-i", str(video)])
    for path in stems:
        argv.extend(["-i", str(path)])
    filt = mix_filter(has_dx=has_dx, bed_count=len(stems) - (1 if has_dx else 0), duck_db=duck_db)
    audio_offset = 1 if video is not None else 0
    if audio_offset:
        remapped = filt
        # Shift [N:a] labels by one because input 0 is video.
        for index in range(len(stems) - 1, -1, -1):
            remapped = remapped.replace(f"[{index}:a]", f"[{index + audio_offset}:a]")
        filt = remapped
        argv.extend(
            [
                "-filter_complex",
                filt,
                "-map",
                "0:v:0",
                "-map",
                "[a]",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                AAC_BITRATE,
                "-ar",
                AAC_RATE,
                str(dest),
            ]
        )
        return argv
    argv.extend(
        [
            "-filter_complex",
            filt,
            "-map",
            "[a]",
            "-c:a",
            "aac",
            "-b:a",
            AAC_BITRATE,
            "-ar",
            AAC_RATE,
            str(dest),
        ]
    )
    return argv


def parse_lufs(stderr: str) -> float | None:
    """Parse ffmpeg loudnorm JSON I from stderr."""
    match = None
    text = stderr or ""
    start = text.rfind("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            data = {}
        raw = data.get("input_i") or data.get("output_i")
        if raw is not None:
            try:
                return float(raw)
            except (TypeError, ValueError):
                return None
    import re

    match = re.search(r'"input_i"\s*:\s*"?(-?[0-9.]+)"?', text)
    if not match:
        return None
    return float(match.group(1))


def lufs_in_band(value: float | None, *, target: float = LUFS_TARGET, tol: float = LUFS_TOL) -> bool:
    """True when measured LUFS is within YouTube −14 ± 2."""
    if value is None:
        return False
    return abs(value - target) <= tol


def mix_stems(
    dest_dir: Path,
    *,
    dx: Path | None = None,
    bg: Path | None = None,
    fx: Path | None = None,
    mx: Path | None = None,
    video: Path | None = None,
    duck_db: float = DUCK_DB,
    ffmpeg: str | None = None,
    run: RunFn = subprocess.run,
) -> dict[str, Any]:
    """Write stems mix under dest_dir/mix.m4a (or mix.mp4 with video)."""
    beds = [p for p in (bg, fx, mx) if p is not None]
    report: dict[str, Any] = {
        "ok": False,
        "path": None,
        "has_dx": bool(dx),
        "beds": len(beds),
        "duck_db": duck_db,
        "defects": [],
    }
    if dx is not None and not dx.is_file():
        report["defects"].append(f"missing DX {dx}")
    for path in beds:
        if not path.is_file():
            report["defects"].append(f"missing bed {path}")
    if dx is None and not beds:
        report["defects"].append("no stems")
    if dx is not None and not beds:
        report["defects"].append("DX without a bed — pass BG from the LTX print")
    exe = ffmpeg or find_ffmpeg()
    if not exe:
        report["defects"].append("ffmpeg missing")
    if report["defects"]:
        return report
    assert exe is not None
    dest_dir.mkdir(parents=True, exist_ok=True)
    out = dest_dir / ("mix.mp4" if video is not None else "mix.m4a")
    ordered: list[Path] = []
    has_dx = dx is not None
    if dx is not None:
        ordered.append(dx)
    ordered.extend(beds)
    argv = mix_argv(ordered, out, has_dx=has_dx, duck_db=duck_db, video=video)
    argv[0] = exe
    print(f"[ez_film] stem mix → {out}", file=sys.stderr)
    proc = _run(argv, run=run)
    if proc.returncode != 0:
        report["defects"].append(
            f"ffmpeg rc={proc.returncode} {(proc.stderr or '')[-200:]}"
        )
        return report
    report["ok"] = True
    report["path"] = str(out)
    (dest_dir / "mix.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ez_film.stems")
    parser.add_argument("--dest", required=True, help="films/<slug>/stems/<id>/")
    parser.add_argument("--dx", default="")
    parser.add_argument("--bg", default="")
    parser.add_argument("--fx", default="")
    parser.add_argument("--mx", default="")
    parser.add_argument("--video", default="")
    parser.add_argument("--duck-db", type=float, default=DUCK_DB)
    args = parser.parse_args(argv)
    report = mix_stems(
        Path(args.dest),
        dx=Path(args.dx) if args.dx else None,
        bg=Path(args.bg) if args.bg else None,
        fx=Path(args.fx) if args.fx else None,
        mx=Path(args.mx) if args.mx else None,
        video=Path(args.video) if args.video else None,
        duck_db=args.duck_db,
    )
    print(json.dumps(report))
    if not report["ok"]:
        for line in report["defects"]:
            print(line, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
