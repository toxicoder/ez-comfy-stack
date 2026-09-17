"""Film MediaProbe / ConcatPipeline façade and Protocol stubs."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_film import concat as film_concat  # noqa: E402
from ez_film import probe, protocols  # noqa: E402
from ez_film.concat import ConcatPipeline, stitch_film  # noqa: E402


def _proc(stdout: str = "", rc: int = 0) -> SimpleNamespace:
    return SimpleNamespace(returncode=rc, stdout=stdout, stderr="")


def test_concat_reexports_probe() -> None:
    assert film_concat.probe_seconds is probe.probe_seconds
    assert film_concat.probe_has_audio is probe.probe_has_audio
    assert film_concat.probe_wh is probe.probe_wh
    assert film_concat.probe_audio_hz is probe.probe_audio_hz
    assert film_concat.probe_audio_seconds is probe.probe_audio_seconds
    assert film_concat.probe_fps is probe.probe_fps
    assert film_concat._ffprobe_csv is probe._ffprobe_csv  # noqa: SLF001
    assert film_concat.FfprobeMediaProbe is probe.FfprobeMediaProbe


def test_protocol_stubs_execute() -> None:
    dummy = object()
    cast(Any, protocols.MediaProbe.duration_s)(dummy, "x.mp4")
    cast(Any, protocols.MediaProbe.size_wh)(dummy, "x.mp4")
    cast(Any, protocols.MediaProbe.has_audio)(dummy, "x.mp4")
    cast(Any, protocols.MediaProbe.audio_hz)(dummy, "x.mp4")
    cast(Any, protocols.MediaProbe.audio_duration_s)(dummy, "x.mp4")
    cast(Any, protocols.MediaProbe.fps)(dummy, "x.mp4")
    cast(Any, protocols.FfmpegTools.ffmpeg)(dummy)
    cast(Any, protocols.FfmpegTools.ffprobe)(dummy)
    cast(Any, protocols.FfmpegRun.__dict__["__call__"])(dummy, ["ffmpeg"])


def test_concat_pipeline_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    pipe = ConcatPipeline(["a.mp4"] * 18, "out.mp4", 90.0, ffmpeg="/bin/ffmpeg")
    assert pipe._ffmpeg() == "/bin/ffmpeg"  # noqa: SLF001
    assert pipe._shot_count() == 18  # noqa: SLF001
    assert pipe._runner() is subprocess.run  # noqa: SLF001
    counted = ConcatPipeline(
        ["a.mp4"] * 18, "out.mp4", 90.0, expected_count=18
    )
    assert counted._shot_count() == 18  # noqa: SLF001
    monkeypatch.setattr(film_concat, "find_ffmpeg", lambda: "/usr/bin/ffmpeg")
    located = ConcatPipeline(["a.mp4"] * 18, "out.mp4", 90.0)
    assert located._ffmpeg() == "/usr/bin/ffmpeg"  # noqa: SLF001


def test_probe_fps_empty_csv_token() -> None:
    def comma(_argv: list[str], **_k: object) -> SimpleNamespace:
        return _proc(stdout=",\n")

    assert probe.probe_fps("x.mp4", ffprobe="ffprobe", run=comma) is None
    assert (
        probe.probe_fps(
            "x.mp4",
            ffprobe="ffprobe",
            run=lambda *_a, **_k: _proc(stdout="24/1\n"),
        )
        == 24.0
    )


def test_stitch_film_xfade_without_ez_common(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shots = [str(tmp_path / f"s{i:02d}.mp4") for i in range(18)]
    for path in shots:
        Path(path).write_bytes(b"mp4")
    out = str(tmp_path / "ez_gosee_90s.mp4")

    def fake_run(argv: list[str], **_k: object) -> SimpleNamespace:
        Path(str(argv[-1])).write_bytes(b"out")
        return _proc()

    monkeypatch.setitem(sys.modules, "ez_common", None)
    with (
        patch.object(film_concat, "validate_stitch_stems", return_value=None),
        patch.object(film_concat, "probe_has_audio", return_value=True),
        patch.object(film_concat, "probe_audio_hz", return_value=48000),
        patch.object(film_concat, "probe_seconds", return_value=90.0),
        patch.object(film_concat, "probe_audio_seconds", return_value=90.0),
    ):
        stitch_film(shots, out, 90.0, ffmpeg="ffmpeg", run=fake_run, xfade_cs=10)
    assert Path(out).is_file()
