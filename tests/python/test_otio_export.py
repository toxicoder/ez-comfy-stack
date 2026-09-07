"""Hermetic OTIO JSON export from a jobstore fixture."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "custom_nodes"))

from ez_film.jobstore import compile_film, mark_shot, save_state  # noqa: E402
from ez_film.otio_export import build_timeline, write_otio  # noqa: E402
from ez_film.shots import SHOT_COUNT  # noqa: E402

SHORTS = ROOT / "workflows" / "shorts"


def test_otio_eighteen_ok_clips(tmp_path: Path) -> None:
    yaml_text = (SHORTS / "go-see.shots.yaml").read_text(encoding="utf-8")
    dest = tmp_path / "films" / "gosee"
    state = compile_film(yaml_text, dest)
    for i in range(1, SHOT_COUNT + 1):
        sid = f"{i:02d}"
        mp4 = dest / "shots" / f"{sid}.mp4"
        mp4.write_bytes(b"fake")
        mark_shot(state, sid, "ok", mp4=f"shots/{sid}.mp4")
    save_state(dest, state)
    path = write_otio(dest)
    assert path == dest / "publish" / "gosee.otio"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["OTIO_SCHEMA"] == "Timeline.1"
    clips = data["tracks"]["children"][0]["children"]
    assert len(clips) == 18
    assert clips[0]["name"] == "01"
    assert clips[11]["media_reference"]["target_url"] == "shots/12.mp4"
    dur = clips[0]["source_range"]["duration"]
    assert dur["value"] == 120
    assert dur["rate"] == 24.0


def test_otio_skips_pending(tmp_path: Path) -> None:
    yaml_text = (SHORTS / "go-see.shots.yaml").read_text(encoding="utf-8")
    dest = tmp_path / "gosee"
    compile_film(yaml_text, dest)
    timeline = build_timeline(dest)
    assert timeline["tracks"]["children"][0]["children"] == []
