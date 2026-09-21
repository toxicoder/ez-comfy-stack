"""Hermetic tests for ez_film (no Comfy, no network, no ffmpeg binary)."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

import ez_film  # noqa: E402
from ez_film import concat as film_concat  # noqa: E402
from ez_film import nodes as film_nodes  # noqa: E402
from ez_film.accept import (  # noqa: E402
    SPEECH_RATIO_MIN,
    accept_master,
    parse_astats_peak_db,
    parse_astats_rms_db,
    parse_sustained_nonsilence_s,
    probe_speech_band_ratio,
    world_only_speech_defects,
)
from ez_film.concat import (  # noqa: E402
    AUDIO_FILTER,
    CLIP_CAP_DEFAULT_S,
    CLIP_CAP_MAX_S,
    CLIP_COUNT_MAX,
    LOUDNORM_FILTER,
    LTX_120_DECODED_FRAMES,
    MOVFLAGS,
    PAD_HOLD_FRAMES,
    audio_acrossfade_filter,
    concat_list_line,
    copy_publish_master,
    encoder_missing,
    ffmpeg_audio_acrossfade_argv,
    ffmpeg_clip_stitch_argv,
    ffmpeg_clip_stitch_copy_argv,
    ffmpeg_mux_copy_argv,
    ffmpeg_pad_stem_argv,
    ffmpeg_stitch_argv,
    ffmpeg_stitch_copy_argv,
    ffmpeg_video_copy_argv,
    is_ltx_120_floor_duration,
    normalize_stitch_stem,
    probe_audio_hz,
    probe_has_audio,
    publish_path,
    resolve_shot_path,
    stitch_clips,
    stitch_film,
    validate_stitch_stems,
    write_disclosure_sidecar,
    write_preview_html,
)
from ez_film.nodes import (  # noqa: E402
    EZClipConcat,
    EZClipLastFrame,
    EZFilmConcat,
    EZFilmDisclosure,
    EZUnloadModels,
    FILM_DISCLOSURE,
    NODE_CLASS_MAPPINGS,
)
from ez_film.shots import (  # noqa: E402
    DEFAULT_CAP_SECONDS,
    SHOT_COUNT,
    film_slug,
    parse_shots_yaml,
)

SHORTS = ROOT / "workflows" / "shorts"


def test_pack_imports_without_comfy() -> None:
    assert ez_film.NODE_CLASS_MAPPINGS == NODE_CLASS_MAPPINGS
    assert set(NODE_CLASS_MAPPINGS) == {
        "EZUnloadModels",
        "EZFilmConcat",
        "EZFilmDisclosure",
        "EZClipLastFrame",
        "EZClipConcat",
    }
    assert ez_film.WEB_DIRECTORY == "./js"
    assert EZUnloadModels.CATEGORY == "ez-comfy/film"
    assert EZFilmConcat.CATEGORY == "ez-comfy/film"
    assert EZClipLastFrame.CATEGORY == "ez-comfy/film"
    assert EZClipConcat.CATEGORY == "ez-comfy/film"
    assert EZFilmConcat.OUTPUT_NODE is True
    assert EZClipConcat.OUTPUT_NODE is True
    spec = EZFilmConcat.INPUT_TYPES()
    assert spec["required"]["film"][0][0] == "go-see"
    assert "tide-table" in spec["required"]["film"][0]
    assert "act" in spec["required"]
    assert spec["required"]["cap_seconds"][1]["default"] == 90.0
    assert spec["required"]["xfade_cs"][1]["default"] == 0
    for index in range(1, 19):
        assert spec["required"][f"shot_{index:02d}"][0] == "VHS_FILENAMES"
    assert spec["optional"]["disclosure"][0] == "STRING"
    clip_spec = EZClipConcat.INPUT_TYPES()
    assert clip_spec["required"]["clip_01"][0] == "VHS_FILENAMES"
    assert clip_spec["required"]["prefix"][1]["default"] == "ez_clip_chain"
    assert clip_spec["required"]["cap_seconds"][1]["default"] == CLIP_CAP_DEFAULT_S
    assert clip_spec["required"]["cap_seconds"][1]["default"] == 600.0
    assert clip_spec["required"]["cap_seconds"][1]["max"] == CLIP_CAP_MAX_S
    assert clip_spec["required"]["cap_seconds"][1]["max"] == 1800.0
    assert clip_spec["required"]["xfade_cs"][1]["default"] == 0
    assert "clip_01" not in clip_spec["optional"]
    for index in range(2, CLIP_COUNT_MAX + 1):
        assert clip_spec["optional"][f"clip_{index:02d}"][0] == "VHS_FILENAMES"
    assert "clip_25" not in clip_spec["optional"]
    assert clip_spec["optional"]["disclosure"][0] == "STRING"
    last_spec = EZClipLastFrame.INPUT_TYPES()
    assert last_spec["required"]["image"][0] == "IMAGE"
    assert EZClipLastFrame.RETURN_TYPES == ("IMAGE",)
    assert EZClipLastFrame.RETURN_NAMES == ("last_frame",)
    assert EZClipConcat.RETURN_TYPES == ("STRING",)
    assert EZClipConcat.RETURN_NAMES == ("path",)
    js = ROOT / "custom_nodes" / "ez_film" / "js" / "ez_film_preview.js"
    body = js.read_text(encoding="utf-8")
    assert "EZFilmConcat" in body
    assert "EZClipConcat" in body
    assert "onExecuted" in body
    assert "Film ready" in body
    assert "Clip chain ready" in body
    assert 'const PREVIEW_TYPES = new Set(["EZFilmConcat", "EZClipConcat"]);' in body
    assert (
        'nodeData.name === "EZClipConcat" ? "Clip chain ready" : "Film ready"'
        in body
    )
    assert "download" in body.lower()
    studio = (
        ROOT / "custom_nodes" / "ez_studio_app" / "js" / "ez_studio_app.js"
    ).read_text(encoding="utf-8")
    save_types = studio.split("const SAVE_TYPES = new Set([", 1)[1].split("]);", 1)[0]
    assert '"EZFilmConcat"' in save_types
    assert '"EZClipConcat"' in save_types


def test_write_disclosure_sidecar(tmp_path: Path) -> None:
    mp4 = tmp_path / "ez_gosee_90s.mp4"
    mp4.write_bytes(b"fake")
    assert write_disclosure_sidecar(str(mp4), "") is None
    assert not (tmp_path / "ez_gosee_90s.disclosure.txt").exists()
    sidecar = write_disclosure_sidecar(str(mp4), "  " + FILM_DISCLOSURE + "  ")
    assert sidecar is not None
    text = sidecar.read_text(encoding="utf-8")
    assert text.startswith(FILM_DISCLOSURE)
    assert text.endswith("\n")


def test_film_disclosure_idempotent() -> None:
    assert "LTX Community License" in FILM_DISCLOSURE
    assert "Wav2Lip" not in FILM_DISCLOSURE
    node = EZFilmDisclosure()
    first = node.run("go-see")[0]
    assert first.startswith(FILM_DISCLOSURE)
    assert node.run(first)[0] == first


def test_film_slug_and_publish_path(tmp_path: Path) -> None:
    assert film_slug("go-see") == "gosee"
    assert film_slug("still-here") == "stillhere"
    assert film_slug("switchyard") == "switchyard"
    assert film_slug("tide-table") == "tidetable"
    with pytest.raises(ValueError):
        film_slug("nope")
    assert publish_path("go-see", tmp_path) == tmp_path / "ez_gosee_90s.mp4"
    assert publish_path("tide-table", tmp_path) == tmp_path / "ez_tidetable_450s.mp4"


def test_parse_go_see_yaml() -> None:
    parsed = parse_shots_yaml((SHORTS / "go-see.shots.yaml").read_text(encoding="utf-8"))
    assert parsed["meta"]["film"] == "go-see"
    assert parsed["meta"]["total_shots"] == "18"
    assert "storm-cloak" in parsed["identity"]
    assert "ink-black" in parsed["identity"]
    assert "olive windbreaker" not in parsed["identity"]
    assert "body-cam" in parsed["identity"]
    assert len(parsed["shots"]) == 18
    first = parsed["shots"][0]
    assert first["load_from"] == "identity"
    assert "The start image holds" in first["ltx_i2v"]
    assert "No music and no score." in first["ltx_i2v"]
    assert "breath" in first["ltx_i2v"]
    assert "audio" not in first["wan_i2v"].lower()
    assert "score" not in first["wan_i2v"].lower()


def test_concat_output_directory_prefers_container(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", "/mnt/comfy-output")
    sys.modules.pop("folder_paths", None)
    original = Path.is_dir

    def fake_is_dir(self: Path) -> bool:
        if str(self) == "/outputs":
            return True
        return original(self)

    monkeypatch.setattr(Path, "is_dir", fake_is_dir)
    assert film_concat.output_directory() == Path("/outputs")


def test_resolve_shot_path_payloads() -> None:
    assert resolve_shot_path("/tmp/a.mp4") == "/tmp/a.mp4"
    assert resolve_shot_path(Path("/tmp/b.mp4")) == "/tmp/b.mp4"
    assert resolve_shot_path((True, ["/tmp/c.mp4"])) == "/tmp/c.mp4"
    assert resolve_shot_path(["/tmp/d.mp4", "/tmp/e.mp4"]) == "/tmp/e.mp4"
    assert resolve_shot_path({"filename": "/tmp/f.mp4"}) == "/tmp/f.mp4"
    png = "/outputs/ez_gosee_b1_s1_ltx_video_00006.png"
    silent = "/outputs/ez_gosee_b1_s1_ltx_video_00006.mp4"
    muxed = "/outputs/ez_gosee_b1_s1_ltx_video_00006-audio.mp4"
    assert resolve_shot_path((True, [png, silent, muxed])) == muxed
    assert resolve_shot_path((True, [png, silent])) == silent
    with pytest.raises(ValueError, match="no MP4"):
        resolve_shot_path((True, [png]))
    with pytest.raises(ValueError):
        resolve_shot_path(None)
    with pytest.raises(ValueError):
        resolve_shot_path("")
    with pytest.raises(ValueError):
        resolve_shot_path([])
    with pytest.raises(ValueError, match="unusable"):
        resolve_shot_path(1)
    with pytest.raises(ValueError, match="no filename"):
        resolve_shot_path({"x": "y"})


def test_resolve_shot_path_png_sibling_audio(tmp_path: Path) -> None:
    png = tmp_path / "ez_gosee_b1_s1_ltx_video_00006.png"
    silent = tmp_path / "ez_gosee_b1_s1_ltx_video_00006.mp4"
    muxed = tmp_path / "ez_gosee_b1_s1_ltx_video_00006-audio.mp4"
    png.write_bytes(b"png")
    silent.write_bytes(b"silent")
    muxed.write_bytes(b"audio")
    assert resolve_shot_path(str(png)) == str(muxed)
    muxed.unlink()
    assert resolve_shot_path(str(png)) == str(silent)


def test_concat_list_escapes_quotes() -> None:
    assert concat_list_line("/tmp/a.mp4") == "file '/tmp/a.mp4'"
    assert "\\'" in concat_list_line("/tmp/o's.mp4")


def test_ffmpeg_argv_has_cap_aac_loudnorm() -> None:
    argv = ffmpeg_stitch_argv("/tmp/list.txt", "/tmp/out.mp4", 90.0, "ffmpeg")
    assert argv[argv.index("-t") + 1] == "90.0"
    assert argv[argv.index("-c:v") + 1] == "libx264"
    assert argv[argv.index("-c:a") + 1] == "aac"
    assert argv[argv.index("-af") + 1] == f"{AUDIO_FILTER},apad"
    assert LOUDNORM_FILTER in AUDIO_FILTER
    assert argv[argv.index("-movflags") + 1] == MOVFLAGS
    assert "+faststart" in MOVFLAGS
    copy_argv = ffmpeg_stitch_copy_argv("/tmp/list.txt", "/tmp/out.mp4", 90.0, "ffmpeg")
    assert copy_argv[copy_argv.index("-c:v") + 1] == "copy"
    assert copy_argv[copy_argv.index("-af") + 1] == f"{AUDIO_FILTER},apad"
    assert copy_argv[copy_argv.index("-movflags") + 1] == MOVFLAGS
    assert encoder_missing("Unknown encoder 'libx264'") is True
    assert encoder_missing("ok") is False


def test_audio_acrossfade_filter_and_xfade_argv() -> None:
    two = audio_acrossfade_filter(2, 0.10)
    assert "acrossfade=d=0.10:o=0" in two
    assert LOUDNORM_FILTER in two
    assert "[a]" in two
    assert two.count("atrim=duration=5.00") == 2
    assert ",apad,atrim=duration=90.00" in two
    eighteen = audio_acrossfade_filter(18, 0.10)
    assert eighteen.count("acrossfade=") == 17
    assert eighteen.count("acrossfade=d=0.10:o=0") == 17
    assert eighteen.count("atrim=duration=5.00") == 18
    assert ",apad,atrim=duration=90.00" in eighteen
    go_see = audio_acrossfade_filter(18, 0.08)
    assert go_see.count("acrossfade=d=0.08:o=0") == 17
    assert go_see.count("atrim=duration=5.00") == 18
    with pytest.raises(ValueError, match="at least 2"):
        audio_acrossfade_filter(1, 0.10)
    shots = [f"/tmp/s{i:02d}.mp4" for i in range(18)]
    audio_argv = ffmpeg_audio_acrossfade_argv(shots, "/tmp/a.m4a", "ffmpeg", 0.10)
    assert audio_argv.count("-i") == 18
    filt = audio_argv[audio_argv.index("-filter_complex") + 1]
    assert "acrossfade=d=0.10:o=0" in filt
    assert filt.count("atrim=duration=5.00") == 18
    assert ",apad,atrim=duration=90.00" in filt
    video_argv = ffmpeg_video_copy_argv("/tmp/list.txt", "/tmp/v.mp4", 90.0, "ffmpeg")
    assert "-an" in video_argv
    assert "-c:v" in video_argv and video_argv[video_argv.index("-c:v") + 1] == "libx264"
    mux = ffmpeg_mux_copy_argv("/tmp/v.mp4", "/tmp/a.m4a", "/tmp/out.mp4", 90.0, "ffmpeg")
    assert mux[mux.index("-c:v") + 1] == "copy"
    assert mux[mux.index("-c:a") + 1] == "copy"
    assert mux[mux.index("-movflags") + 1] == MOVFLAGS


def test_stitch_film_runs_ffmpeg_and_checks_cap(tmp_path: Path) -> None:
    shots = [str(tmp_path / f"s{i:02d}.mp4") for i in range(18)]
    for path in shots:
        Path(path).write_bytes(b"mp4")
    out = str(tmp_path / "ez_gosee_90s.mp4")
    captured: list[list[str]] = []

    def fake_run(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        captured.append(list(argv))
        Path(argv[-1]).write_bytes(b"mp4")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    with patch.object(film_concat, "validate_stitch_stems", return_value=None):
        with (
            patch.object(film_concat, "probe_seconds", return_value=90.0),
            patch.object(film_concat, "probe_has_audio", return_value=True),
            patch.object(film_concat, "probe_audio_seconds", return_value=90.0),
        ):
            stitch_film(shots, out, 90.0, ffmpeg="ffmpeg", run=fake_run)
    assert captured
    assert "-t" in captured[0]
    assert any(LOUDNORM_FILTER in str(part) for part in captured[0])
    assert captured[0][captured[0].index("-c:v") + 1] == "libx264"
    assert captured[0][captured[0].index("-movflags") + 1] == MOVFLAGS
    assert Path(out).is_file()

    with patch.object(film_concat, "validate_stitch_stems", return_value=None):
        with (
            patch.object(film_concat, "probe_seconds", return_value=91.0),
            patch.object(film_concat, "probe_has_audio", return_value=True),
            patch.object(film_concat, "probe_audio_seconds", return_value=91.0),
        ):
            with pytest.raises(RuntimeError, match="exceeds cap"):
                stitch_film(shots, out, 90.0, ffmpeg="ffmpeg", run=fake_run)

    with pytest.raises(ValueError, match="expected 18"):
        stitch_film(shots[:3], out, 90.0, ffmpeg="ffmpeg", run=fake_run)

    with pytest.raises(ValueError, match="expected 18"):
        stitch_film(shots[:17], out, 90.0, ffmpeg="ffmpeg", run=fake_run)

    shots[0] = str(tmp_path / "ez_gosee_b1_s1_ltx_video_00006.png")
    with pytest.raises(RuntimeError, match="image, not an MP4"):
        stitch_film(shots, out, 90.0, ffmpeg="ffmpeg", run=fake_run)


def test_stitch_film_refuses_missing_stem_and_short_master(tmp_path: Path) -> None:
    shots = [str(tmp_path / f"s{i:02d}.mp4") for i in range(18)]
    for path in shots[:-1]:
        Path(path).write_bytes(b"mp4")
    out = str(tmp_path / "ez_gosee_90s.mp4")

    def fake_run(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        joined = " ".join(str(a) for a in argv)
        if "width,height" in joined:
            return SimpleNamespace(returncode=0, stdout="1280,704\n", stderr="")
        if "format=duration" in joined or "stream=duration" in joined:
            return SimpleNamespace(returncode=0, stdout="5.00\n", stderr="")
        if "codec_type" in joined:
            return SimpleNamespace(returncode=0, stdout="audio\n", stderr="")
        Path(argv[-1]).write_bytes(b"mp4")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    with pytest.raises(RuntimeError, match="unreadable shot"):
        stitch_film(shots, out, 90.0, ffmpeg="ffmpeg", ffprobe="ffprobe", run=fake_run)
    assert not Path(out).exists()

    for path in shots:
        Path(path).write_bytes(b"mp4")
    Path(out).write_bytes(b"short")
    with patch.object(film_concat, "validate_stitch_stems", return_value=None):
        with (
            patch.object(film_concat, "probe_seconds", return_value=84.79),
            patch.object(film_concat, "probe_has_audio", return_value=True),
            patch.object(film_concat, "probe_audio_seconds", return_value=84.79),
        ):
            with pytest.raises(RuntimeError, match="short of cap"):
                stitch_film(shots, out, 90.0, ffmpeg="ffmpeg", run=fake_run)
    assert not Path(out).exists()


def test_stitch_film_xfade_requires_audio_and_runs_three_steps(
    tmp_path: Path,
) -> None:
    shots = [str(tmp_path / f"s{i:02d}.mp4") for i in range(18)]
    for path in shots:
        Path(path).write_bytes(b"mp4")
    out = str(tmp_path / "ez_gosee_90s.mp4")
    captured: list[list[str]] = []

    def fake_run(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        captured.append(list(argv))
        Path(argv[-1]).write_bytes(b"out")
        return SimpleNamespace(returncode=0, stdout="audio\n", stderr="")

    with patch.object(film_concat, "validate_stitch_stems", return_value=None):
        with patch.object(film_concat, "probe_has_audio", return_value=False):
            with pytest.raises(RuntimeError, match="requires audio"):
                stitch_film(
                    shots, out, 90.0, ffmpeg="ffmpeg", run=fake_run, xfade_cs=10
                )

    captured.clear()
    with (
        patch.object(film_concat, "validate_stitch_stems", return_value=None),
        patch.object(film_concat, "probe_has_audio", return_value=True),
        patch.object(film_concat, "probe_audio_hz", return_value=48000),
        patch.object(film_concat, "probe_seconds", return_value=90.0),
        patch.object(film_concat, "probe_audio_seconds", return_value=90.0),
    ):
        stitch_film(shots, out, 90.0, ffmpeg="ffmpeg", run=fake_run, xfade_cs=10)
    assert len(captured) == 3
    assert "-an" in captured[0]
    filt = captured[1][captured[1].index("-filter_complex") + 1]
    assert "acrossfade=d=0.10:o=0" in filt
    assert filt.count("atrim=duration=5.00") == 18
    assert ",apad,atrim=duration=90.00" in filt
    assert captured[2][captured[2].index("-c:v") + 1] == "copy"

    with pytest.raises(ValueError, match="0–50"):
        stitch_film(shots, out, 90.0, ffmpeg="ffmpeg", run=fake_run, xfade_cs=99)

    captured.clear()

    def fail_run(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(returncode=1, stdout="", stderr="boom")

    with patch.object(film_concat, "validate_stitch_stems", return_value=None):
        with pytest.raises(RuntimeError, match="ffmpeg stitch failed"):
            stitch_film(shots, out, 90.0, ffmpeg="ffmpeg", run=fail_run)

    with (
        patch.object(film_concat, "validate_stitch_stems", return_value=None),
        patch.object(film_concat, "probe_has_audio", return_value=True),
        patch.object(film_concat, "probe_audio_hz", return_value=44100),
        patch.object(film_concat, "probe_seconds", return_value=90.0),
        patch.object(film_concat, "probe_audio_seconds", return_value=90.0),
    ):
        with pytest.raises(RuntimeError, match="44100"):
            stitch_film(
                shots, out, 90.0, ffmpeg="ffmpeg", run=fake_run, xfade_cs=10
            )


def test_probe_has_audio_and_hz() -> None:
    def fake_run(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        joined = " ".join(str(a) for a in argv)
        if "codec_type" in joined:
            return SimpleNamespace(returncode=0, stdout="audio\n", stderr="")
        if "sample_rate" in joined:
            return SimpleNamespace(returncode=0, stdout="48000\n", stderr="")
        return SimpleNamespace(returncode=1, stdout="", stderr="")

    assert probe_has_audio("/tmp/a.mp4", ffprobe="ffprobe", run=fake_run) is True
    assert probe_audio_hz("/tmp/a.mp4", ffprobe="ffprobe", run=fake_run) == 48000

    def empty_run(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    assert probe_has_audio("/tmp/a.mp4", ffprobe="ffprobe", run=empty_run) is False
    assert probe_audio_hz("/tmp/a.mp4", ffprobe="ffprobe", run=empty_run) is None


def test_ltx_120_floor_pad_argv() -> None:
    assert LTX_120_DECODED_FRAMES == 113
    assert PAD_HOLD_FRAMES == 7
    assert is_ltx_120_floor_duration(113 / 24) is True
    assert is_ltx_120_floor_duration(4.708333) is True
    assert is_ltx_120_floor_duration(5.00) is False
    assert is_ltx_120_floor_duration(5.041667) is False
    assert is_ltx_120_floor_duration(3.0) is False
    argv = ffmpeg_pad_stem_argv("/in.mp4", "/out.pad.mp4", "ffmpeg")
    assert "tpad=stop_mode=clone:stop=7" in argv[argv.index("-filter_complex") + 1]
    assert "apad=" in argv[argv.index("-filter_complex") + 1]
    assert argv[argv.index("-t") + 1] == "5.00"
    assert argv[argv.index("-c:v") + 1] == "libx264"


def test_normalize_pads_113_and_validate_refuses_3s(tmp_path: Path) -> None:
    src = tmp_path / "ez_gosee_b1_s1_ltx_video_00001-audio.mp4"
    src.write_bytes(b"mp4")
    padded_written: list[str] = []

    def fake_run(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        joined = " ".join(str(a) for a in argv)
        dest = str(argv[-1])
        if "tpad" in joined:
            Path(dest).write_bytes(b"padded")
            padded_written.append(dest)
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if "width,height" in joined:
            return SimpleNamespace(returncode=0, stdout="1280,704\n", stderr="")
        if "codec_type" in joined:
            return SimpleNamespace(returncode=0, stdout="audio\n", stderr="")
        if "format=duration" in joined or "stream=duration" in joined:
            if ".pad.mp4" in dest or Path(dest).name.endswith(".pad.mp4"):
                return SimpleNamespace(returncode=0, stdout="5.00\n", stderr="")
            if Path(dest).read_bytes() == b"padded":
                return SimpleNamespace(returncode=0, stdout="5.00\n", stderr="")
            return SimpleNamespace(returncode=0, stdout="4.708333\n", stderr="")
        Path(dest).write_bytes(b"out")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    temps: list[str] = []
    out = normalize_stitch_stem(
        str(src), ffmpeg="ffmpeg", ffprobe="ffprobe", run=fake_run, temps=temps
    )
    assert padded_written
    assert out == padded_written[0]
    assert temps == [out]
    Path(out).unlink(missing_ok=True)

    shots = [str(tmp_path / f"s{i:02d}.mp4") for i in range(18)]
    for path in shots:
        Path(path).write_bytes(b"mp4")

    def three_run(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        joined = " ".join(str(a) for a in argv)
        if "width,height" in joined:
            return SimpleNamespace(returncode=0, stdout="1280,704\n", stderr="")
        if "codec_type" in joined:
            return SimpleNamespace(returncode=0, stdout="audio\n", stderr="")
        if "format=duration" in joined or "stream=duration" in joined:
            return SimpleNamespace(returncode=0, stdout="3.00\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    with pytest.raises(RuntimeError, match="shot duration"):
        validate_stitch_stems(shots, ffprobe="ffprobe", run=three_run)

    def legal_121_run(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        joined = " ".join(str(a) for a in argv)
        if "width,height" in joined:
            return SimpleNamespace(returncode=0, stdout="1280,704\n", stderr="")
        if "codec_type" in joined:
            return SimpleNamespace(returncode=0, stdout="audio\n", stderr="")
        if "format=duration" in joined or "stream=duration" in joined:
            return SimpleNamespace(returncode=0, stdout="5.041667\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    validate_stitch_stems(shots, ffprobe="ffprobe", run=legal_121_run)


def test_stitch_film_pads_113_frame_stems(tmp_path: Path) -> None:
    shots = [str(tmp_path / f"s{i:02d}.mp4") for i in range(18)]
    for path in shots:
        Path(path).write_bytes(b"mp4")
    out = str(tmp_path / "ez_gosee_90s.mp4")
    captured: list[str] = []

    def fake_run(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        joined = " ".join(str(a) for a in argv)
        dest = str(argv[-1])
        captured.append(joined)
        if "tpad" in joined:
            Path(dest).write_bytes(b"padded")
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if "width,height" in joined:
            return SimpleNamespace(returncode=0, stdout="1280,704\n", stderr="")
        if "codec_type" in joined:
            return SimpleNamespace(returncode=0, stdout="audio\n", stderr="")
        if "sample_rate" in joined:
            return SimpleNamespace(returncode=0, stdout="48000\n", stderr="")
        if "format=duration" in joined or "stream=duration" in joined:
            if dest == out:
                return SimpleNamespace(returncode=0, stdout="90.00\n", stderr="")
            if ".pad.mp4" in dest or (
                Path(dest).is_file() and Path(dest).read_bytes() == b"padded"
            ):
                return SimpleNamespace(returncode=0, stdout="5.00\n", stderr="")
            return SimpleNamespace(returncode=0, stdout="4.708333\n", stderr="")
        Path(dest).write_bytes(b"master")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    stitch_film(shots, out, 90.0, ffmpeg="ffmpeg", ffprobe="ffprobe", run=fake_run)
    assert any("tpad=stop_mode=clone:stop=7" in line for line in captured)
    assert Path(out).is_file()
    assert not list(tmp_path.glob("*.pad.mp4"))

    def boom_run(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        raise OSError("no ffprobe")

    assert probe_has_audio("/tmp/a.mp4", ffprobe="ffprobe", run=boom_run) is False

    def bad_hz(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(returncode=0, stdout="nope\n", stderr="")

    assert probe_audio_hz("/tmp/a.mp4", ffprobe="ffprobe", run=bad_hz) is None

    def fail_code(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(returncode=1, stdout="audio\n", stderr="")

    assert probe_has_audio("/tmp/a.mp4", ffprobe="ffprobe", run=fail_code) is False

    with patch.object(film_concat, "find_ffprobe", return_value=None):
        assert probe_has_audio("/tmp/a.mp4") is False


def test_assert_master_duration_hermetic_without_path_ffprobe(
    tmp_path: Path,
) -> None:
    """CI runners have no ffprobe; injected ``run`` must still validate."""
    out = tmp_path / "ok.mp4"
    out.write_bytes(b"mp4")
    with patch.object(film_concat, "find_ffprobe", return_value=None):
        with pytest.raises(RuntimeError, match="ffprobe required"):
            film_concat.assert_master_duration(str(out), 90.0)

        def _injected(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
            joined = " ".join(str(a) for a in argv)
            if "codec_type" in joined:
                return SimpleNamespace(returncode=0, stdout="audio\n", stderr="")
            if "format=duration" in joined or "stream=duration" in joined:
                return SimpleNamespace(returncode=0, stdout="90.00\n", stderr="")
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        film_concat.assert_master_duration(str(out), 90.0, run=_injected)


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

    def fake_stitch(paths: list[str], out_mp4: str, cap: float, xfade_cs: int = 0) -> str:
        assert len(paths) == SHOT_COUNT
        assert cap == DEFAULT_CAP_SECONDS
        assert xfade_cs == 0
        Path(out_mp4).write_bytes(b"out")
        return out_mp4

    with patch.object(film_nodes, "stitch_film", side_effect=fake_stitch):
        packed = EZFilmConcat().run("go-see", 90.0, 0, disclosure="", act=0, **shots)
    assert packed["result"][0].endswith("ez_gosee_90s.mp4")
    assert packed["ui"]["gifs"][0]["filename"] == "ez_gosee_90s.mp4"
    assert packed["ui"]["gifs"][0]["format"] == "video/h264-mp4"
    assert packed["ui"]["gifs"][0]["type"] == "output"
    assert packed["ui"]["gifs"][0]["subfolder"] == ""
    assert packed["ui"]["gifs"][0]["frame_rate"] == 24
    html = tmp_path / "ez_gosee_90s.html"
    assert html.is_file()
    text = html.read_text(encoding="utf-8")
    assert "<video" in text
    assert "download" in text
    assert "ez_gosee_90s.mp4" in text


def test_film_concat_node_picks_vhs_audio_mp4(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    shots: dict[str, object] = {}
    expected: list[str] = []
    for index in range(1, 19):
        prefix = tmp_path / f"ez_gosee_b1_s{index:02d}_ltx_video_00006"
        png = prefix.with_suffix(".png")
        silent = prefix.with_suffix(".mp4")
        muxed = tmp_path / f"{prefix.name}-audio.mp4"
        png.write_bytes(b"png")
        silent.write_bytes(b"silent")
        muxed.write_bytes(b"audio")
        shots[f"shot_{index:02d}"] = (True, [str(png), str(silent), str(muxed)])
        expected.append(str(muxed))

    captured: list[list[str]] = []

    def fake_stitch(paths: list[str], out_mp4: str, cap: float, xfade_cs: int = 0) -> str:
        captured.append(list(paths))
        assert cap == DEFAULT_CAP_SECONDS
        assert xfade_cs == 8
        Path(out_mp4).write_bytes(b"out")
        return out_mp4

    with patch.object(film_nodes, "stitch_film", side_effect=fake_stitch):
        packed = EZFilmConcat().run("go-see", 90.0, 8, disclosure="", act=0, **shots)
    assert captured == [expected]
    assert packed["result"][0].endswith("ez_gosee_90s.mp4")


class _FakeImage:
    """Numpy-like IMAGE batch with ``.shape`` and slice ``__getitem__``."""

    def __init__(self, frames: list[object], height: int = 8, width: int = 8) -> None:
        self.frames = list(frames)
        self.shape = (len(self.frames), height, width, 3)

    def __getitem__(self, key: object) -> _FakeImage:
        if isinstance(key, slice):
            sliced = self.frames[key]
            return _FakeImage(sliced, self.shape[1], self.shape[2])
        raise TypeError("expected slice")


def test_clip_last_frame_empty_and_passthrough() -> None:
    with pytest.raises(ValueError, match="empty IMAGE batch; cannot extract last frame"):
        EZClipLastFrame().run(None)
    with pytest.raises(ValueError, match="empty IMAGE batch; cannot extract last frame"):
        EZClipLastFrame().run(object())
    empty = _FakeImage([])
    assert empty.shape[0] == 0
    with pytest.raises(ValueError, match="empty IMAGE batch; cannot extract last frame"):
        EZClipLastFrame().run(empty)
    single = _FakeImage(["only"])
    out = EZClipLastFrame().run(single)[0]
    assert isinstance(out, _FakeImage)
    assert out.shape[0] == 1
    assert out.frames == ["only"]
    batch = _FakeImage(["a", "b", "c"])
    last = EZClipLastFrame().run(batch)[0]
    assert isinstance(last, _FakeImage)
    assert last.shape[0] == 1
    assert last.frames == ["c"]


def test_clip_concat_collect_until_gap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    clip_01 = tmp_path / "c01.mp4"
    clip_03 = tmp_path / "c03.mp4"
    clip_01.write_bytes(b"x")
    clip_03.write_bytes(b"x")
    node = EZClipConcat()
    with pytest.raises(
        RuntimeError, match="missing clip_02; refusing to stitch with a hole"
    ):
        node.run("ez_clip_chain", 600.0, 0, clip_01=str(clip_01), clip_03=str(clip_03))

    captured: list[list[str]] = []

    def fake_stitch(
        paths: list[str], out_mp4: str, cap: float, xfade_cs: int = 0
    ) -> str:
        captured.append(list(paths))
        assert cap == CLIP_CAP_DEFAULT_S
        assert xfade_cs == 0
        Path(out_mp4).write_bytes(b"out")
        return out_mp4

    with patch.object(film_nodes, "stitch_clips", side_effect=fake_stitch):
        packed = node.run("ez_clip_chain", 600.0, 0, clip_01=str(clip_01))
    assert captured == [[str(clip_01)]]
    assert packed["result"][0].endswith("ez_clip_chain.mp4")
    assert packed["ui"]["gifs"][0]["filename"] == "ez_clip_chain.mp4"
    assert packed["ui"]["gifs"][0]["format"] == "video/h264-mp4"
    assert packed["ui"]["gifs"][0]["type"] == "output"
    assert packed["ui"]["gifs"][0]["subfolder"] == ""
    assert packed["ui"]["gifs"][0]["frame_rate"] == 24
    assert (tmp_path / "ez_clip_chain.html").is_file()
    assert not (tmp_path / "films").exists()

    captured.clear()
    with patch.object(film_nodes, "stitch_clips", side_effect=fake_stitch):
        node.run("ez_clip_chain", 600.0, 0, clip_01=str(clip_01), clip_02=None)
    assert captured == [[str(clip_01)]]

    clip_02 = tmp_path / "c02.mp4"
    clip_02.write_bytes(b"x")
    captured.clear()
    with patch.object(film_nodes, "stitch_clips", side_effect=fake_stitch):
        packed = node.run(
            "ez_clip_chain", 600.0, 0, clip_01=str(clip_01), clip_02=str(clip_02)
        )
    assert captured == [[str(clip_01), str(clip_02)]]
    assert packed["result"][0].endswith("ez_clip_chain.mp4")


def test_clip_concat_xfade_refused_before_ffmpeg(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    with pytest.raises(
        RuntimeError, match=r"clip xfade not in v1; use xfade_cs=0 \(hard cut\)"
    ):
        EZClipConcat().run("ez_clip_chain", 600.0, 1, clip_01=None)


def test_ffmpeg_clip_stitch_argv_omits_cap_and_apad() -> None:
    argv = ffmpeg_clip_stitch_argv("/tmp/list.txt", "/tmp/out.mp4", "ffmpeg")
    assert "-t" not in argv
    assert "600" not in argv
    assert argv[argv.index("-f") + 1] == "concat"
    assert argv[argv.index("-r") + 1] == "24"
    assert argv[argv.index("-c:v") + 1] == "libx264"
    assert argv[argv.index("-af") + 1] == AUDIO_FILTER
    assert ",apad" not in argv[argv.index("-af") + 1]
    assert argv[argv.index("-movflags") + 1] == MOVFLAGS
    copy_argv = ffmpeg_clip_stitch_copy_argv("/tmp/list.txt", "/tmp/out.mp4", "ffmpeg")
    assert copy_argv[copy_argv.index("-c:v") + 1] == "copy"
    assert "-t" not in copy_argv
    assert copy_argv[copy_argv.index("-af") + 1] == AUDIO_FILTER
    assert ",apad" not in copy_argv[copy_argv.index("-af") + 1]


def _write_clip_mp4s(tmp_path: Path, count: int) -> list[str]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    paths = [str(tmp_path / f"c{i:02d}.mp4") for i in range(count)]
    for path in paths:
        Path(path).write_bytes(b"mp4")
    return paths


def test_stitch_clips_duration_head_size_cap_and_sum(tmp_path: Path) -> None:
    illegal = _write_clip_mp4s(tmp_path, 1)
    out = str(tmp_path / "ez_clip_chain.mp4")

    def refuse_run(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        raise AssertionError(f"ffmpeg should not run: {argv}")

    with (
        patch.object(film_concat, "probe_seconds", return_value=7.71),
        patch.object(film_concat, "probe_wh", return_value=(1280, 704)),
        patch.object(film_concat, "probe_has_audio", return_value=True),
    ):
        with pytest.raises(
            RuntimeError,
            match=r"clip duration 7.71s is not in \(5.00, 8.00, 10.00, 12.00\)",
        ):
            stitch_clips(
                illegal, out, 600.0, ffmpeg="ffmpeg", ffprobe="ffprobe", run=refuse_run
            )

    pair = _write_clip_mp4s(tmp_path / "size", 2)

    def size_wh(path: str, **_kwargs: Any) -> tuple[int, int]:
        if path.endswith("c00.mp4"):
            return (1280, 704)
        return (768, 1280)

    with (
        patch.object(film_concat, "probe_seconds", return_value=8.00),
        patch.object(film_concat, "probe_wh", side_effect=size_wh),
        patch.object(film_concat, "probe_has_audio", return_value=True),
    ):
        with pytest.raises(RuntimeError, match="clip size mismatch"):
            stitch_clips(
                pair, out, 600.0, ffmpeg="ffmpeg", ffprobe="ffprobe", run=refuse_run
            )

    four = _write_clip_mp4s(tmp_path / "cap", 4)
    captured: list[list[str]] = []

    def capture_run(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        captured.append(list(argv))
        Path(str(argv[-1])).write_bytes(b"mp4")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    with (
        patch.object(film_concat, "probe_seconds", return_value=8.00),
        patch.object(film_concat, "probe_wh", return_value=(1280, 704)),
        patch.object(film_concat, "probe_has_audio", return_value=True),
    ):
        with pytest.raises(
            RuntimeError, match=r"clip concat duration 32.0s exceeds cap 30.0s"
        ):
            stitch_clips(
                four, out, 30.0, ffmpeg="ffmpeg", ffprobe="ffprobe", run=capture_run
            )
    assert captured == []

    stems = _write_clip_mp4s(tmp_path / "sum", 2)
    master = str(tmp_path / "sum" / "ez_clip_chain.mp4")

    def probe_sum(path: str, **_kwargs: Any) -> float:
        if path == master:
            return 16.0834
        return 8.0417

    with (
        patch.object(film_concat, "probe_seconds", side_effect=probe_sum),
        patch.object(film_concat, "probe_wh", return_value=(768, 1280)),
        patch.object(film_concat, "probe_has_audio", return_value=True),
        patch.object(film_concat, "probe_audio_seconds", return_value=16.0834),
    ):
        stitch_clips(
            stems, master, 600.0, ffmpeg="ffmpeg", ffprobe="ffprobe", run=capture_run
        )
    assert captured
    argv = captured[0]
    assert "-t" not in argv
    assert "-t" not in [str(part) for part in argv]
    joined = " ".join(str(part) for part in argv)
    assert "-t 600" not in joined
    assert ",apad" not in joined
    assert argv[argv.index("-f") + 1] == "concat"
    assert argv[argv.index("-r") + 1] == "24"
    assert argv[argv.index("-c:v") + 1] == "libx264"
    assert AUDIO_FILTER in argv
    assert argv[argv.index("-af") + 1] == AUDIO_FILTER
    assert argv[argv.index("-movflags") + 1] == MOVFLAGS
    assert Path(master).is_file()

    with pytest.raises(
        RuntimeError, match=r"clip xfade not in v1; use xfade_cs=0 \(hard cut\)"
    ):
        stitch_clips(
            stems, master, 600.0, ffmpeg="ffmpeg", ffprobe="ffprobe", run=refuse_run,
            xfade_cs=10,
        )


def test_write_preview_html_and_x264_fallback(tmp_path: Path) -> None:
    mp4 = tmp_path / "ez_gosee_90s.mp4"
    mp4.write_bytes(b"mp4")
    sidecar = write_preview_html(str(mp4))
    assert sidecar == tmp_path / "ez_gosee_90s.html"
    assert copy_publish_master(str(mp4), "go-see", tmp_path) is None
    publish = tmp_path / "films" / "gosee" / "publish"
    publish.mkdir(parents=True)
    copied = copy_publish_master(str(mp4), "go-see", tmp_path)
    assert copied is not None
    assert copied == publish / "master.mp4"
    assert copied.is_file()
    shots = [str(tmp_path / f"s{i:02d}.mp4") for i in range(18)]
    out = str(tmp_path / "out.mp4")
    captured: list[list[str]] = []

    def fail_then_ok(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        captured.append(list(argv))
        if len(captured) == 1:
            return SimpleNamespace(
                returncode=1, stdout="", stderr="Unknown encoder 'libx264'"
            )
        Path(argv[-1]).write_bytes(b"out")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    for path in shots:
        Path(path).write_bytes(b"mp4")
    with (
        patch.object(film_concat, "validate_stitch_stems", return_value=None),
        patch.object(film_concat, "probe_seconds", return_value=90.0),
        patch.object(film_concat, "probe_has_audio", return_value=True),
        patch.object(film_concat, "probe_audio_seconds", return_value=90.0),
    ):
        stitch_film(shots, out, 90.0, ffmpeg="ffmpeg", run=fail_then_ok)
    assert len(captured) == 2
    assert captured[0][captured[0].index("-c:v") + 1] == "libx264"
    assert captured[1][captured[1].index("-c:v") + 1] == "copy"
    assert captured[1][captured[1].index("-movflags") + 1] == MOVFLAGS


ASTATS_SPEECH = (
    "[Parsed_astats_0 @ 0x1] Overall\n"
    "RMS level dB: -16.00\n"
    "Peak level dB: -12.00\n"
)
ASTATS_FULL = (
    "[Parsed_astats_0 @ 0x1] Overall\n"
    "RMS level dB: -16.50\n"
    "Peak level dB: -11.00\n"
)
ASTATS_FOLEY_SPEECH = (
    "[Parsed_astats_0 @ 0x1] Overall\n"
    "RMS level dB: -32.00\n"
    "Peak level dB: -28.00\n"
)
ASTATS_FOLEY_FULL = (
    "[Parsed_astats_0 @ 0x1] Overall\n"
    "RMS level dB: -18.00\n"
    "Peak level dB: -10.00\n"
)
SILENCE_TALKING = "silence_start: 0.00\nsilence_end: 0.10 | silence_duration: 0.10\n"
SILENCE_FOLEY = (
    "silence_start: 0.00\n"
    "silence_end: 4.80 | silence_duration: 4.80\n"
)
SILENCE_FOLEY_MASTER = (
    "silence_start: 0.00\n"
    "silence_end: 89.90 | silence_duration: 89.90\n"
)


def test_speech_band_parsers_and_ratio(tmp_path: Path) -> None:
    assert parse_astats_rms_db(ASTATS_SPEECH) == -16.00
    assert parse_astats_peak_db(ASTATS_SPEECH) == -12.00
    assert parse_sustained_nonsilence_s(SILENCE_TALKING, 5.00) == pytest.approx(4.90)
    assert parse_sustained_nonsilence_s(SILENCE_FOLEY, 5.00) == 0.0
    shot = tmp_path / "talk.mp4"
    shot.write_bytes(b"x")

    def talking_run(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        joined = " ".join(str(a) for a in argv)
        if "silencedetect" in joined:
            return SimpleNamespace(returncode=0, stdout="", stderr=SILENCE_TALKING)
        if "highpass" in joined:
            return SimpleNamespace(returncode=0, stdout="", stderr=ASTATS_SPEECH)
        return SimpleNamespace(returncode=0, stdout="", stderr=ASTATS_FULL)

    ratio = probe_speech_band_ratio(shot, ffmpeg="ffmpeg", run=talking_run)
    assert ratio is not None
    assert ratio >= SPEECH_RATIO_MIN
    defects = world_only_speech_defects(
        shot, "01", duration_s=5.00, ffmpeg="ffmpeg", run=talking_run
    )
    assert defects
    assert any("speech-band" in line for line in defects)

    def foley_run(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        joined = " ".join(str(a) for a in argv)
        if "silencedetect" in joined:
            return SimpleNamespace(returncode=0, stdout="", stderr=SILENCE_FOLEY)
        if "highpass" in joined:
            return SimpleNamespace(returncode=0, stdout="", stderr=ASTATS_FOLEY_SPEECH)
        return SimpleNamespace(returncode=0, stdout="", stderr=ASTATS_FOLEY_FULL)

    assert world_only_speech_defects(
        shot, "01", duration_s=5.00, ffmpeg="ffmpeg", run=foley_run
    ) == []


def test_accept_master_scripts_ffprobe(tmp_path: Path) -> None:
    master = tmp_path / "ez_gosee_90s.mp4"
    master.write_bytes(b"x")

    def talking_run(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        joined = " ".join(str(a) for a in argv)
        if "format=duration" in joined or "stream=duration" in joined:
            return SimpleNamespace(returncode=0, stdout="90.00\n", stderr="")
        if "width,height" in joined:
            return SimpleNamespace(returncode=0, stdout="1280,704\n", stderr="")
        if "r_frame_rate" in joined:
            return SimpleNamespace(returncode=0, stdout="24/1\n", stderr="")
        if "codec_type" in joined:
            return SimpleNamespace(returncode=0, stdout="audio\n", stderr="")
        if "silencedetect" in joined:
            return SimpleNamespace(returncode=0, stdout="", stderr=SILENCE_TALKING)
        if "highpass" in joined:
            return SimpleNamespace(returncode=0, stdout="", stderr=ASTATS_SPEECH)
        if "astats" in joined:
            return SimpleNamespace(returncode=0, stdout="", stderr=ASTATS_FULL)
        return SimpleNamespace(returncode=1, stdout="", stderr="")

    defects = accept_master(
        master, ffprobe="ffprobe", ffmpeg="ffmpeg", run=talking_run
    )
    assert any("speech-band" in line for line in defects)

    def clean_run(argv: list[str], **_kwargs: Any) -> SimpleNamespace:
        joined = " ".join(str(a) for a in argv)
        if "format=duration" in joined or "stream=duration" in joined:
            return SimpleNamespace(returncode=0, stdout="90.00\n", stderr="")
        if "width,height" in joined:
            return SimpleNamespace(returncode=0, stdout="1280,704\n", stderr="")
        if "r_frame_rate" in joined:
            return SimpleNamespace(returncode=0, stdout="24/1\n", stderr="")
        if "codec_type" in joined:
            return SimpleNamespace(returncode=0, stdout="audio\n", stderr="")
        if "silencedetect" in joined:
            return SimpleNamespace(returncode=0, stdout="", stderr=SILENCE_FOLEY_MASTER)
        if "highpass" in joined:
            return SimpleNamespace(returncode=0, stdout="", stderr=ASTATS_FOLEY_SPEECH)
        if "astats" in joined:
            return SimpleNamespace(returncode=0, stdout="", stderr=ASTATS_FOLEY_FULL)
        return SimpleNamespace(returncode=1, stdout="", stderr="")

    assert accept_master(
        master, ffprobe="ffprobe", ffmpeg="ffmpeg", run=clean_run
    ) == []
