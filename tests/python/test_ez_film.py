"""Hermetic tests for ez_film (no Comfy, no network, no ffmpeg binary)."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

import ez_film  # noqa: E402
from ez_film import concat as film_concat  # noqa: E402
from ez_film import nodes as film_nodes  # noqa: E402
from ez_film.concat import (  # noqa: E402
    LOUDNORM_FILTER,
    audio_acrossfade_filter,
    concat_list_line,
    ffmpeg_audio_acrossfade_argv,
    ffmpeg_mux_copy_argv,
    ffmpeg_stitch_argv,
    ffmpeg_video_copy_argv,
    probe_audio_hz,
    probe_has_audio,
    publish_path,
    resolve_shot_path,
    stitch_film,
)
from ez_film.nodes import EZFilmConcat, EZUnloadModels, NODE_CLASS_MAPPINGS  # noqa: E402
from ez_film.shots import (  # noqa: E402
    DEFAULT_CAP_SECONDS,
    SHOT_COUNT,
    film_slug,
    parse_shots_yaml,
)

SHORTS = ROOT / "workflows" / "shorts"


def test_pack_imports_without_comfy() -> None:
    assert ez_film.NODE_CLASS_MAPPINGS == NODE_CLASS_MAPPINGS
    assert set(NODE_CLASS_MAPPINGS) == {"EZUnloadModels", "EZFilmConcat"}
    assert EZUnloadModels.CATEGORY == "ez-comfy/film"
    assert EZFilmConcat.CATEGORY == "ez-comfy/film"
    assert EZFilmConcat.OUTPUT_NODE is True
    spec = EZFilmConcat.INPUT_TYPES()
    assert spec["required"]["film"][0] == ["go-see", "still-here", "switchyard"]
    assert spec["required"]["cap_seconds"][1]["default"] == 90.0
    assert spec["required"]["xfade_cs"][1]["default"] == 0
    for index in range(1, 19):
        assert spec["required"][f"shot_{index:02d}"][0] == "VHS_FILENAMES"


def test_film_slug_and_publish_path(tmp_path: Path) -> None:
    assert film_slug("go-see") == "gosee"
    assert film_slug("still-here") == "stillhere"
    assert film_slug("switchyard") == "switchyard"
    with pytest.raises(ValueError):
        film_slug("nope")
    assert publish_path("go-see", tmp_path) == tmp_path / "ez_gosee_90s.mp4"


def test_parse_go_see_yaml() -> None:
    parsed = parse_shots_yaml((SHORTS / "go-see.shots.yaml").read_text(encoding="utf-8"))
    assert parsed["meta"]["film"] == "go-see"
    assert parsed["meta"]["total_shots"] == "18"
    assert "olive windbreaker" in parsed["identity"]
    assert len(parsed["shots"]) == 18
    first = parsed["shots"][0]
    assert first["load_from"] == "identity"
    assert "The start image holds" in first["ltx_i2v"]
    assert "No music and no score." in first["ltx_i2v"]
    assert "breath" in first["ltx_i2v"]
    assert "audio" not in first["wan_i2v"].lower()
    assert "score" not in first["wan_i2v"].lower()


def test_resolve_shot_path_payloads() -> None:
    assert resolve_shot_path("/tmp/a.mp4") == "/tmp/a.mp4"
    assert resolve_shot_path(Path("/tmp/b.mp4")) == "/tmp/b.mp4"
    assert resolve_shot_path((True, ["/tmp/c.mp4"])) == "/tmp/c.mp4"
    assert resolve_shot_path(["/tmp/d.mp4", "/tmp/e.mp4"]) == "/tmp/d.mp4"
    assert resolve_shot_path({"filename": "/tmp/f.mp4"}) == "/tmp/f.mp4"
    with pytest.raises(ValueError):
        resolve_shot_path(None)
    with pytest.raises(ValueError):
        resolve_shot_path("")
    with pytest.raises(ValueError):
        resolve_shot_path([])


def test_concat_list_escapes_quotes() -> None:
    assert concat_list_line("/tmp/a.mp4") == "file '/tmp/a.mp4'"
    assert "\\'" in concat_list_line("/tmp/o's.mp4")


def test_ffmpeg_argv_has_cap_aac_loudnorm() -> None:
    argv = ffmpeg_stitch_argv("/tmp/list.txt", "/tmp/out.mp4", 90.0, "ffmpeg")
    assert argv == [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        "/tmp/list.txt",
        "-t",
        "90.0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-ar",
        "48000",
        "-ac",
        "2",
        "-b:a",
        "192k",
        "-af",
        LOUDNORM_FILTER,
        "/tmp/out.mp4",
    ]


def test_audio_acrossfade_filter_and_xfade_argv() -> None:
    two = audio_acrossfade_filter(2, 0.10)
    assert "acrossfade=d=0.10" in two
    assert LOUDNORM_FILTER in two
    assert "[a]" in two
    eighteen = audio_acrossfade_filter(18, 0.10)
    assert eighteen.count("acrossfade=") == 17
    with pytest.raises(ValueError, match="at least 2"):
        audio_acrossfade_filter(1, 0.10)
    shots = [f"/tmp/s{i:02d}.mp4" for i in range(18)]
    audio_argv = ffmpeg_audio_acrossfade_argv(shots, "/tmp/a.m4a", "ffmpeg", 0.10)
    assert audio_argv.count("-i") == 18
    assert "acrossfade" in audio_argv[audio_argv.index("-filter_complex") + 1]
    video_argv = ffmpeg_video_copy_argv("/tmp/list.txt", "/tmp/v.mp4", 90.0, "ffmpeg")
    assert "-an" in video_argv
    assert "-c:v" in video_argv and video_argv[video_argv.index("-c:v") + 1] == "copy"
    mux = ffmpeg_mux_copy_argv("/tmp/v.mp4", "/tmp/a.m4a", "/tmp/out.mp4", 90.0, "ffmpeg")
    assert mux[mux.index("-c:v") + 1] == "copy"
    assert mux[mux.index("-c:a") + 1] == "copy"


def test_stitch_film_runs_ffmpeg_and_checks_cap(tmp_path: Path) -> None:
    shots = [str(tmp_path / f"s{i:02d}.mp4") for i in range(18)]
    out = str(tmp_path / "ez_gosee_90s.mp4")
    captured: list[list[str]] = []

    def fake_run(argv, **_kwargs):
        captured.append(list(argv))
        Path(argv[-1]).write_bytes(b"mp4")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    with patch.object(film_concat, "probe_seconds", return_value=90.0):
        stitch_film(shots, out, 90.0, ffmpeg="ffmpeg", run=fake_run)
    assert captured
    assert "-t" in captured[0]
    assert LOUDNORM_FILTER in captured[0]
    assert Path(out).is_file()

    with patch.object(film_concat, "probe_seconds", return_value=91.0):
        with pytest.raises(RuntimeError, match="exceeds cap"):
            stitch_film(shots, out, 90.0, ffmpeg="ffmpeg", run=fake_run)

    with pytest.raises(ValueError, match="expected 18"):
        stitch_film(shots[:3], out, 90.0, ffmpeg="ffmpeg", run=fake_run)


def test_stitch_film_xfade_requires_audio_and_runs_three_steps(
    tmp_path: Path,
) -> None:
    shots = [str(tmp_path / f"s{i:02d}.mp4") for i in range(18)]
    for path in shots:
        Path(path).write_bytes(b"mp4")
    out = str(tmp_path / "ez_gosee_90s.mp4")
    captured: list[list[str]] = []

    def fake_run(argv, **_kwargs):
        captured.append(list(argv))
        Path(argv[-1]).write_bytes(b"out")
        return SimpleNamespace(returncode=0, stdout="audio\n", stderr="")

    with patch.object(film_concat, "probe_has_audio", return_value=False):
        with pytest.raises(RuntimeError, match="requires audio"):
            stitch_film(
                shots, out, 90.0, ffmpeg="ffmpeg", run=fake_run, xfade_cs=10
            )

    captured.clear()
    with (
        patch.object(film_concat, "probe_has_audio", return_value=True),
        patch.object(film_concat, "probe_audio_hz", return_value=48000),
        patch.object(film_concat, "probe_seconds", return_value=90.0),
    ):
        stitch_film(shots, out, 90.0, ffmpeg="ffmpeg", run=fake_run, xfade_cs=10)
    assert len(captured) == 3
    assert "-an" in captured[0]
    assert "acrossfade" in captured[1][captured[1].index("-filter_complex") + 1]
    assert captured[2][captured[2].index("-c:v") + 1] == "copy"

    with pytest.raises(ValueError, match="0–50"):
        stitch_film(shots, out, 90.0, ffmpeg="ffmpeg", run=fake_run, xfade_cs=99)

    captured.clear()

    def fail_run(argv, **_kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="boom")

    with pytest.raises(RuntimeError, match="ffmpeg stitch failed"):
        stitch_film(shots, out, 90.0, ffmpeg="ffmpeg", run=fail_run)

    with (
        patch.object(film_concat, "probe_has_audio", return_value=True),
        patch.object(film_concat, "probe_audio_hz", return_value=44100),
        patch.object(film_concat, "probe_seconds", return_value=90.0),
    ):
        with pytest.raises(RuntimeError, match="44100"):
            stitch_film(
                shots, out, 90.0, ffmpeg="ffmpeg", run=fake_run, xfade_cs=10
            )


def test_probe_has_audio_and_hz() -> None:
    def fake_run(argv, **_kwargs):
        joined = " ".join(str(a) for a in argv)
        if "codec_type" in joined:
            return SimpleNamespace(returncode=0, stdout="audio\n", stderr="")
        if "sample_rate" in joined:
            return SimpleNamespace(returncode=0, stdout="48000\n", stderr="")
        return SimpleNamespace(returncode=1, stdout="", stderr="")

    assert probe_has_audio("/tmp/a.mp4", ffprobe="ffprobe", run=fake_run) is True
    assert probe_audio_hz("/tmp/a.mp4", ffprobe="ffprobe", run=fake_run) == 48000

    def empty_run(argv, **_kwargs):
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    assert probe_has_audio("/tmp/a.mp4", ffprobe="ffprobe", run=empty_run) is False
    assert probe_audio_hz("/tmp/a.mp4", ffprobe="ffprobe", run=empty_run) is None

    def boom_run(argv, **_kwargs):
        raise OSError("no ffprobe")

    assert probe_has_audio("/tmp/a.mp4", ffprobe="ffprobe", run=boom_run) is False

    def bad_hz(argv, **_kwargs):
        return SimpleNamespace(returncode=0, stdout="nope\n", stderr="")

    assert probe_audio_hz("/tmp/a.mp4", ffprobe="ffprobe", run=bad_hz) is None

    def fail_code(argv, **_kwargs):
        return SimpleNamespace(returncode=1, stdout="audio\n", stderr="")

    assert probe_has_audio("/tmp/a.mp4", ffprobe="ffprobe", run=fail_code) is False

    with patch.object(film_concat, "find_ffprobe", return_value=None):
        assert probe_has_audio("/tmp/a.mp4") is False


def test_unload_passthrough() -> None:
    image = object()
    with patch.object(film_nodes, "_unload_models", return_value="unloaded") as unload:
        out = EZUnloadModels().run(image)
    unload.assert_called_once()
    assert out == (image,)


def test_film_concat_node(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    shots = {f"shot_{i:02d}": str(tmp_path / f"s{i:02d}.mp4") for i in range(1, 19)}
    for path in shots.values():
        Path(path).write_bytes(b"x")

    def fake_stitch(paths, out_mp4, cap, xfade_cs=0):
        assert len(paths) == SHOT_COUNT
        assert cap == DEFAULT_CAP_SECONDS
        assert xfade_cs == 0
        Path(out_mp4).write_bytes(b"out")
        return out_mp4

    with patch.object(film_nodes, "stitch_film", side_effect=fake_stitch):
        packed = EZFilmConcat().run("go-see", 90.0, **shots)
    assert packed["result"][0].endswith("ez_gosee_90s.mp4")
    assert packed["ui"]["gifs"][0]["filename"] == "ez_gosee_90s.mp4"
    assert packed["ui"]["gifs"][0]["format"] == "video/h264-mp4"
