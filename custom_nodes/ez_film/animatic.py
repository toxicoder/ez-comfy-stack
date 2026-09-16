"""Cheap film animatic: clay.mp4 or held stills, 90s cap (stdlib import)."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from .shots import DEFAULT_CAP_SECONDS, SHOT_COUNT, parse_shots_yaml

# Still-hold duration matching the 5.00 s picture contract.
HOLD_SECONDS = 5.00
RunFn = Callable[..., Any]


def find_ffmpeg() -> str | None:
    """Resolve ffmpeg on PATH, or None.

    Returns:
        Executable path, or None.
    """
    return shutil.which("ffmpeg")


def _run(
    argv: list[str],
    *,
    run: RunFn = subprocess.run,
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess with captured text output.

    Args:
        argv: Command vector.
        run: ``subprocess.run`` or a test double.

    Returns:
        Completed process (not checked).
    """
    return run(argv, check=False, capture_output=True, text=True)


def shot_sources(
    parsed: dict[str, Any],
    guides: Path,
    stills: Path | None = None,
) -> list[dict[str, str]]:
    """Pick clay.mp4 when present, else a still to hold for 5.00s.

    Args:
        parsed: Parsed shot-sheet dict (``shots`` list).
        guides: ``guides/<slug>/`` pack root.
        stills: Optional ``stills/<id>.png`` directory.

    Returns:
        Per-shot dicts with ``id``, ``kind``, and ``path``.
    """
    rows: list[dict[str, str]] = []
    for index, shot in enumerate(parsed["shots"], start=1):
        sid = f"{index:02d}"
        pack = guides / sid
        clay = pack / "clay.mp4"
        first = pack / "first.png"
        look = stills / f"{sid}.png" if stills is not None else None
        if clay.is_file():
            rows.append({"id": sid, "kind": "clay", "path": str(clay)})
        elif look is not None and look.is_file():
            rows.append({"id": sid, "kind": "still", "path": str(look)})
        elif first.is_file():
            rows.append({"id": sid, "kind": "still", "path": str(first)})
        else:
            rows.append({"id": sid, "kind": "missing", "path": ""})
    return rows


def concat_argv(concat_list: Path, dest: Path, cap: float) -> list[str]:
    """ffmpeg concat demuxer, video-only, hard 90s cap.

    Args:
        concat_list: Concat demuxer list file.
        dest: Destination MP4.
        cap: ffmpeg ``-t`` cap in seconds.

    Returns:
        ffmpeg argument vector.
    """
    return [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_list),
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-t",
        f"{cap:.2f}",
        str(dest),
    ]


def write_concat_list(rows: list[dict[str, str]], dest: Path) -> None:
    """Write ffmpeg concat demuxer list (still rows loop 5.00s).

    Args:
        rows: Shot source rows from :func:`shot_sources`.
        dest: Concat list path to write.
    """
    lines: list[str] = []
    for row in rows:
        path = row["path"].replace("'", r"'\''")
        lines.append(f"file '{path}'")
        if row["kind"] == "still":
            lines.append(f"duration {HOLD_SECONDS:.2f}")
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_animatic(
    yaml_text: str,
    dest: Path,
    *,
    guides: Path,
    stills: Path | None = None,
    cap: float = DEFAULT_CAP_SECONDS,
    ffmpeg: str | None = None,
    run: RunFn = subprocess.run,
) -> dict[str, Any]:
    """Write films/<slug>/publish/animatic.mp4 from clay or held stills.

    Args:
        yaml_text: Film bible YAML contents.
        dest: ``films/<slug>/`` jobstore directory.
        guides: ``guides/<slug>/`` pack root.
        stills: Optional stills directory.
        cap: Publish duration cap.
        ffmpeg: Override ffmpeg path.
        run: Override ``subprocess.run``.

    Returns:
        Animatic report dict (``ok``, ``path``, ``defects``).
    """
    parsed = parse_shots_yaml(yaml_text)
    slug = str(parsed["meta"]["slug"])
    rows = shot_sources(parsed, guides, stills)
    missing = [r["id"] for r in rows if r["kind"] == "missing"]
    report: dict[str, Any] = {
        "ok": False,
        "slug": slug,
        "path": None,
        "shots": len(rows),
        "missing": missing,
        "cap_s": cap,
        "defects": [],
    }
    if len(rows) != SHOT_COUNT:
        report["defects"].append(f"shot count {len(rows)} (need {SHOT_COUNT})")
    if missing:
        report["defects"].append("missing sources: " + ",".join(missing))
    exe = ffmpeg or find_ffmpeg()
    if not exe:
        report["defects"].append("ffmpeg missing")
    if report["defects"]:
        return report
    assert exe is not None
    publish = dest / "publish"
    publish.mkdir(parents=True, exist_ok=True)
    concat_list = publish / "animatic.concat.txt"
    write_concat_list(rows, concat_list)
    out = publish / "animatic.mp4"
    argv = concat_argv(concat_list, out, cap)
    argv[0] = exe
    print(f"[ez_film] animatic {len(rows)} shots → {out}", file=sys.stderr)
    proc = _run(argv, run=run)
    if proc.returncode != 0:
        report["defects"].append(
            f"ffmpeg rc={proc.returncode} {(proc.stderr or '')[-200:]}"
        )
        return report
    report["ok"] = True
    report["path"] = str(out)
    (publish / "animatic.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def _cli(argv: list[str] | None = None) -> int:
    """Parse argv and build a 90s animatic.

    Args:
        argv: Argument vector, or None for ``sys.argv``.

    Returns:
        Process exit code.
    """
    parser = argparse.ArgumentParser(prog="ez_film.animatic")
    parser.add_argument("--yaml", required=True)
    parser.add_argument("--dest", required=True, help="films/<slug>/")
    parser.add_argument("--guides", required=True, help="guides/<slug>/")
    parser.add_argument("--stills", default="", help="optional stills/<id>.png dir")
    args = parser.parse_args(argv)
    text = Path(args.yaml).read_text(encoding="utf-8")
    stills = Path(args.stills) if args.stills else None
    report = build_animatic(
        text, Path(args.dest), guides=Path(args.guides), stills=stills
    )
    print(json.dumps(report))
    if not report["ok"]:
        for line in report["defects"]:
            print(line, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
