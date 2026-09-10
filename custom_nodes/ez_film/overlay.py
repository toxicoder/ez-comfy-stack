"""Clay vs look-plate overlay QC (hermetic at import: stdlib only).

ffmpeg is resolved at call time. Size is the LTX VAE grid (1280x704).
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

PACK_WIDTH = 1280
PACK_HEIGHT = 704
RunFn = Callable[..., Any]


def png_size(path: Path) -> tuple[int, int] | None:
    """Read IHDR width x height, or None."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    if data[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", data[16:24])
    return int(width), int(height)


def find_ffmpeg() -> str | None:
    """Resolve ffmpeg on PATH, or None."""
    return shutil.which("ffmpeg")


def _run(
    argv: list[str],
    *,
    run: RunFn = subprocess.run,
) -> subprocess.CompletedProcess[str]:
    return run(argv, check=False, capture_output=True, text=True)


def blend_argv(clay: Path, look: Path, overlay: Path) -> list[str]:
    """ffmpeg 50% blend of clay first.png and look plate."""
    return [
        "ffmpeg",
        "-y",
        "-i",
        str(clay),
        "-i",
        str(look),
        "-filter_complex",
        "blend=all_expr='A*0.5+B*0.5'",
        "-frames:v",
        "1",
        str(overlay),
    ]


def psnr_argv(clay: Path, look: Path) -> list[str]:
    """ffmpeg PSNR of look vs clay (stats on stderr)."""
    return [
        "ffmpeg",
        "-i",
        str(look),
        "-i",
        str(clay),
        "-filter_complex",
        "psnr",
        "-f",
        "null",
        "-",
    ]


def parse_psnr(stderr: str) -> float | None:
    """Extract average PSNR from ffmpeg psnr filter stderr."""
    match = re.search(r"average:([0-9.]+)", stderr or "")
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def overlay_qc(
    clay: Path,
    look: Path,
    dest: Path,
    *,
    ffmpeg: str | None = None,
    run: RunFn = subprocess.run,
) -> dict[str, Any]:
    """Fail-closed overlay of clay first.png vs look plate.

    Writes overlay.png and score.json under dest. Human still picks;
    the score only ranks candidates.
    """
    defects: list[str] = []
    if not clay.is_file():
        defects.append(f"missing clay {clay}")
    if not look.is_file():
        defects.append(f"missing look {look}")
    clay_wh = png_size(clay) if clay.is_file() else None
    look_wh = png_size(look) if look.is_file() else None
    expected = (PACK_WIDTH, PACK_HEIGHT)
    if clay_wh is not None and clay_wh != expected:
        defects.append(f"clay size {clay_wh!r} (need {PACK_WIDTH}x{PACK_HEIGHT})")
    if look_wh is not None and look_wh != expected:
        defects.append(f"look size {look_wh!r} (need {PACK_WIDTH}x{PACK_HEIGHT})")
    if clay_wh and look_wh and clay_wh != look_wh:
        defects.append(f"size mismatch clay {clay_wh} vs look {look_wh}")
    exe = ffmpeg or find_ffmpeg()
    if not exe:
        defects.append("ffmpeg missing")
    report: dict[str, Any] = {
        "ok": False,
        "clay": str(clay),
        "look": str(look),
        "overlay": None,
        "score": None,
        "width": PACK_WIDTH,
        "height": PACK_HEIGHT,
        "defects": defects,
    }
    if defects:
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "score.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
        return report
    assert exe is not None
    dest.mkdir(parents=True, exist_ok=True)
    overlay = dest / "overlay.png"
    blend = blend_argv(clay, look, overlay)
    blend[0] = exe
    proc = _run(blend, run=run)
    if proc.returncode != 0 or not overlay.is_file():
        report["defects"].append(
            f"blend failed rc={proc.returncode} {(proc.stderr or '')[-200:]}"
        )
        (dest / "score.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
        return report
    psnr_cmd = psnr_argv(clay, look)
    psnr_cmd[0] = exe
    psnr_proc = _run(psnr_cmd, run=run)
    score = parse_psnr((psnr_proc.stderr or "") + (psnr_proc.stdout or ""))
    report["ok"] = True
    report["overlay"] = str(overlay)
    report["score"] = score
    (dest / "score.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ez_film.overlay")
    parser.add_argument("--clay", required=True, help="guide pack first.png")
    parser.add_argument("--look", required=True, help="Klein look plate PNG")
    parser.add_argument("--dest", required=True, help="guides/<slug>/<shot>/")
    args = parser.parse_args(argv)
    report = overlay_qc(Path(args.clay), Path(args.look), Path(args.dest))
    print(json.dumps(report))
    if not report["ok"]:
        for line in report["defects"]:
            print(line, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
