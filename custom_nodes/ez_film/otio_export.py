"""Write a minimal OpenTimelineIO 1.0 JSON timeline (stdlib, no otio import).

Apache OTIO files are JSON. Host Kdenlive/Shotcut can import this without
baking opentimelineio into the Spark image torch layer.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .jobstore import DURATION_S, DURATION_TOL, load_state, shot_mp4
from .ltx_timing import FPS_DEFAULT


def _rational(frames: int, rate: int = FPS_DEFAULT) -> dict[str, Any]:
    return {"OTIO_SCHEMA": "RationalTime.1", "value": int(frames), "rate": float(rate)}


def _seconds_to_frames(seconds: float, rate: int = FPS_DEFAULT) -> int:
    return int(round(float(seconds) * int(rate)))


def build_timeline(
    dest: Path,
    *,
    fps: int = FPS_DEFAULT,
    duration_s: float = DURATION_S,
    tol: float = DURATION_TOL,
) -> dict[str, Any]:
    """Build an OTIO Timeline dict from ``films/<slug>/state.json``.

    Only ``ok`` shots with an mp4 path become clips. Missing files are skipped
    (accept-gate in Wave 4 fails closed before concat).
    """
    state = load_state(dest)
    slug = str(state.get("slug") or dest.name)
    rate = int(fps)
    clip_frames = _seconds_to_frames(duration_s, rate)
    children: list[dict[str, Any]] = []
    for row in state["shots"]:
        if row.get("status") != "ok":
            continue
        sid = str(row["id"])
        mp4 = dest / row["mp4"] if row.get("mp4") else shot_mp4(dest, sid)
        if not mp4.is_file():
            continue
        try:
            media = str(mp4.resolve().relative_to(dest.resolve()))
        except ValueError:
            media = str(mp4)
        children.append(
            {
                "OTIO_SCHEMA": "Clip.1",
                "name": sid,
                "source_range": {
                    "OTIO_SCHEMA": "TimeRange.1",
                    "start_time": _rational(0, rate),
                    "duration": _rational(clip_frames, rate),
                },
                "media_reference": {
                    "OTIO_SCHEMA": "ExternalReference.1",
                    "target_url": media,
                    "available_range": {
                        "OTIO_SCHEMA": "TimeRange.1",
                        "start_time": _rational(0, rate),
                        "duration": _rational(clip_frames, rate),
                    },
                },
            }
        )
    return {
        "OTIO_SCHEMA": "Timeline.1",
        "name": slug,
        "metadata": {
            "ez_film": {
                "slug": slug,
                "duration_s": duration_s,
                "duration_tol": tol,
                "fps": rate,
            }
        },
        "tracks": {
            "OTIO_SCHEMA": "Stack.1",
            "name": "tracks",
            "children": [
                {
                    "OTIO_SCHEMA": "Track.1",
                    "name": "picture",
                    "kind": "Video",
                    "children": children,
                }
            ],
        },
    }


def write_otio(dest: Path, path: Path | None = None) -> Path:
    """Write ``publish/<slug>.otio``. Returns the path."""
    timeline = build_timeline(dest)
    slug = str(timeline["name"])
    out = path or (dest / "publish" / f"{slug}.otio")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(timeline, indent=2) + "\n", encoding="utf-8")
    return out


def _cli(argv: list[str] | None = None) -> int:
    """CLI used by film-export-otio.sh."""
    parser = argparse.ArgumentParser(prog="ez_film.otio_export")
    parser.add_argument("--dest", required=True, help="films/<slug> directory")
    args = parser.parse_args(argv)
    dest = Path(args.dest)
    path = write_otio(dest)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
