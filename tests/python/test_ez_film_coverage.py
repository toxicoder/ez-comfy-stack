"""Hermetic line coverage for remaining ez_film misses (no ffmpeg/GPU/network)."""

from __future__ import annotations

import argparse
import os
import re
import runpy
import struct
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))
if str(ROOT / "scripts" / "lib") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "lib"))

import guide_pack as gp  # noqa: E402
from ez_film import accept as acc  # noqa: E402
from ez_film import animatic as an  # noqa: E402
from ez_film import concat as film_concat  # noqa: E402
from ez_film import jobstore as js  # noqa: E402
from ez_film import nodes as film_nodes  # noqa: E402
from ez_film import otio_export as otio  # noqa: E402
from ez_film import overlay as ov  # noqa: E402
from ez_film import shots as sh  # noqa: E402
from ez_film import stems as st  # noqa: E402
from ez_film.concat import (  # noqa: E402
    assert_clip_master_duration,
    assert_master_duration,
    copy_publish_master,
    encoder_missing,
    probe_audio_seconds,
    probe_wh,
    stitch_clips,
    stitch_film,
    validate_stitch_stems,
)
from ez_film.nodes import (  # noqa: E402
    EZClipConcat,
    EZClipLastFrame,
    EZFilmConcat,
    EZFilmDisclosure,
    EZUnloadModels,
)

SHORTS = ROOT / "workflows" / "shorts"


def _go_see_yaml() -> str:
    return (SHORTS / "go-see.shots.yaml").read_text(encoding="utf-8")


def _compile(tmp_path: Path) -> Path:
    dest = tmp_path / "films" / "gosee"
    js.compile_film(_go_see_yaml(), dest)
    return dest


def _eighteen(tmp_path: Path) -> list[str]:
    shots = [str(tmp_path / f"s{i:02d}.mp4") for i in range(18)]
    for path in shots:
        Path(path).write_bytes(b"mp4")
    return shots


def _proc(stdout: str = "", stderr: str = "", rc: int = 0) -> SimpleNamespace:
    return SimpleNamespace(returncode=rc, stdout=stdout, stderr=stderr)


def _cover_main(mod: str, monkeypatch: pytest.MonkeyPatch) -> None:
    sys.modules.pop(mod, None)
    monkeypatch.setattr(sys, "argv", [mod, "--help"])
    with pytest.raises(SystemExit):
        runpy.run_module(mod, run_name="__main__")



def test_unload_models_comfy_torch_and_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mm = types.ModuleType("comfy.model_management")
    mm.unload_all_models = lambda: None  # type: ignore[attr-defined]
    mm.soft_empty_cache = lambda: None  # type: ignore[attr-defined]
    comfy = types.ModuleType("comfy")
    monkeypatch.setitem(sys.modules, "comfy", comfy)
    monkeypatch.setitem(sys.modules, "comfy.model_management", mm)

    class _Cuda:
        @staticmethod
        def is_available() -> bool:
            return True

        @staticmethod
        def empty_cache() -> None:
            return None

    torch_mod = types.ModuleType("torch")
    torch_mod.cuda = _Cuda()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "torch", torch_mod)
    assert film_nodes._unload_models() == "unloaded"  # noqa: SLF001

    mm_plain = types.ModuleType("comfy.model_management")
    mm_plain.unload_all_models = lambda: None  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "comfy.model_management", mm_plain)
    assert film_nodes._unload_models() == "unloaded"  # noqa: SLF001

    def _boom() -> None:
        raise RuntimeError("no comfy")

    mm_plain.unload_all_models = _boom  # type: ignore[attr-defined]
    assert film_nodes._unload_models() == "skipped"  # noqa: SLF001

    monkeypatch.setitem(sys.modules, "torch", None)
    assert film_nodes._unload_models() == "skipped"  # noqa: SLF001

    spec = EZUnloadModels.INPUT_TYPES()
    assert spec["required"]["image"][0] == "IMAGE"
    disc = EZFilmDisclosure.INPUT_TYPES()
    assert disc["required"]["text"][0] == "STRING"
    node = EZFilmDisclosure()
    assert node.run("")[0] == film_nodes.FILM_DISCLOSURE
    assert node.run("extra credit")[0].endswith("extra credit")


def test_film_concat_node_refuses_empty_and_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    shots = {f"shot_{i:02d}": str(tmp_path / f"s{i:02d}.mp4") for i in range(1, 19)}
    with pytest.raises(RuntimeError, match="missing or unreadable"):
        EZFilmConcat().run("go-see", 90.0, 0, disclosure="", act=0, **shots)
    empty = tmp_path / "s01.mp4"
    empty.write_bytes(b"")
    shots["shot_01"] = str(empty)
    for index in range(2, 19):
        Path(shots[f"shot_{index:02d}"]).write_bytes(b"x")
    with pytest.raises(RuntimeError, match="missing or unreadable"):
        EZFilmConcat().run("go-see", 90.0, 0, disclosure="", act=0, **shots)


def test_output_directory_fallbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "ez_common", None)
    fake_fp = SimpleNamespace(get_output_directory=lambda: "/from-folder-paths")
    monkeypatch.setitem(sys.modules, "folder_paths", fake_fp)
    assert film_concat.output_directory() == Path("/from-folder-paths")

    monkeypatch.setitem(sys.modules, "folder_paths", None)
    original = Path.is_dir

    def outputs_exist(self: Path) -> bool:
        if str(self) == "/outputs":
            return True
        return original(self)

    monkeypatch.setattr(Path, "is_dir", outputs_exist)
    assert film_concat.output_directory() == Path("/outputs")

    def outputs_missing(self: Path) -> bool:
        if str(self) == "/outputs":
            return False
        return original(self)

    monkeypatch.setattr(Path, "is_dir", outputs_missing)
    monkeypatch.setenv("COMFY_OUTPUT_DIR", "/mnt/from-env")
    assert film_concat.output_directory() == Path("/mnt/from-env")

    monkeypatch.delenv("COMFY_OUTPUT_DIR", raising=False)
    assert film_concat.output_directory() == Path("output")


def test_find_ffmpeg_path_imageio_and_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(film_concat.shutil, "which", lambda _n: "/usr/bin/ffmpeg")
    assert film_concat.find_ffmpeg() == "/usr/bin/ffmpeg"

    monkeypatch.setattr(film_concat.shutil, "which", lambda _n: None)
    fake = types.ModuleType("imageio_ffmpeg")
    fake.get_ffmpeg_exe = lambda: "/opt/imageio/ffmpeg"  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "imageio_ffmpeg", fake)
    assert film_concat.find_ffmpeg() == "/opt/imageio/ffmpeg"

    fake.get_ffmpeg_exe = lambda: ""  # type: ignore[attr-defined]
    with pytest.raises(RuntimeError, match="ffmpeg not on PATH"):
        film_concat.find_ffmpeg()

    monkeypatch.setitem(sys.modules, "imageio_ffmpeg", None)
    with pytest.raises(RuntimeError, match="ffmpeg not on PATH"):
        film_concat.find_ffmpeg()


def test_concat_helpers_probe_validate_and_copy(tmp_path: Path) -> None:
    assert film_concat._sibling_video("/tmp/clip.mp4") is None  # noqa: SLF001
    assert film_concat._path_strings(None) == []  # noqa: SLF001
    assert film_concat._path_strings(object()) == []  # noqa: SLF001
    assert encoder_missing("libx264 encoder not found in this build") is True

    publish = tmp_path / "films" / "gosee" / "publish"
    publish.mkdir(parents=True)
    src = tmp_path / "ez_gosee_90s.mp4"
    src.write_bytes(b"master")
    with patch.object(film_concat.shutil, "copy2", side_effect=OSError("disk")):
        assert copy_publish_master(str(src), "go-see", tmp_path) is None

    def empty_run(_argv: list[str], **_k: object) -> SimpleNamespace:
        return _proc(stdout="")

    assert probe_wh("x.mp4", ffprobe="ffprobe", run=empty_run) is None

    def no_comma(_argv: list[str], **_k: object) -> SimpleNamespace:
        return _proc(stdout="1280\n")

    assert probe_wh("x.mp4", ffprobe="ffprobe", run=no_comma) is None

    def bad_ints(_argv: list[str], **_k: object) -> SimpleNamespace:
        return _proc(stdout="wide,tall\n")

    assert probe_wh("x.mp4", ffprobe="ffprobe", run=bad_ints) is None

    def audio_then_format(argv: list[str], **_k: object) -> SimpleNamespace:
        joined = " ".join(str(a) for a in argv)
        if "stream=duration" in joined:
            return _proc(stdout="not-a-float\n")
        return _proc(stdout="5.00\n")

    assert (
        probe_audio_seconds("x.mp4", ffprobe="ffprobe", run=audio_then_format) == 5.00
    )

    def empty_duration(_argv: list[str], **_k: object) -> SimpleNamespace:
        return _proc(stdout="")

    assert film_concat.probe_seconds("x.mp4", ffprobe="ffprobe", run=empty_duration) is None

    def bad_duration(_argv: list[str], **_k: object) -> SimpleNamespace:
        return _proc(stdout="nope\n")

    assert film_concat.probe_seconds("x.mp4", ffprobe="ffprobe", run=bad_duration) is None


def test_validate_stitch_stems_fail_closed(tmp_path: Path) -> None:
    shots = _eighteen(tmp_path)
    with pytest.raises(ValueError, match="expected 18"):
        validate_stitch_stems(shots[:2], ffprobe="ffprobe")
    with patch.object(film_concat, "find_ffprobe", return_value=None):
        with pytest.raises(RuntimeError, match="ffprobe required"):
            validate_stitch_stems(shots)
    missing = list(shots)
    missing[0] = "  "
    with pytest.raises(RuntimeError, match="missing shot"):
        validate_stitch_stems(missing, ffprobe="ffprobe")
    Path(shots[0]).write_bytes(b"")
    with pytest.raises(RuntimeError, match="empty shot"):
        validate_stitch_stems(shots, ffprobe="ffprobe")
    Path(shots[0]).write_bytes(b"mp4")

    def sized(argv: list[str], **_k: object) -> SimpleNamespace:
        joined = " ".join(str(a) for a in argv)
        if "width,height" in joined:
            return _proc(stdout="1920,1080\n")
        if "format=duration" in joined:
            return _proc(stdout="5.00\n")
        if "codec_type" in joined:
            return _proc(stdout="audio\n")
        return _proc(stdout="5.00\n")

    with pytest.raises(RuntimeError, match="shot size"):
        validate_stitch_stems(shots, ffprobe="ffprobe", run=sized)

    def silent(argv: list[str], **_k: object) -> SimpleNamespace:
        joined = " ".join(str(a) for a in argv)
        if "width,height" in joined:
            return _proc(stdout="1280,704\n")
        if "codec_type" in joined:
            return _proc(stdout="video\n")
        return _proc(stdout="5.00\n")

    with pytest.raises(RuntimeError, match="missing audio"):
        validate_stitch_stems(shots, ffprobe="ffprobe", run=silent)

    class _ShortIter(list[str]):
        def __iter__(self) -> object:  # type: ignore[override]
            for index, item in enumerate(list.__iter__(self)):
                if index >= 17:
                    return
                yield item

    short = _ShortIter(shots)
    with (
        patch.object(film_concat, "probe_seconds", return_value=5.00),
        patch.object(film_concat, "probe_wh", return_value=(1280, 704)),
        patch.object(film_concat, "probe_has_audio", return_value=True),
    ):
        with pytest.raises(RuntimeError, match="expected 18 valid"):
            validate_stitch_stems(short, ffprobe="ffprobe")


def test_clip_concat_missing_unreadable_and_disclosure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    node = EZClipConcat()
    with pytest.raises(RuntimeError, match="missing or unreadable clip_01"):
        node.run("ez_clip_chain", 600.0, 0, clip_01=None)
    with pytest.raises(RuntimeError, match="missing or unreadable clip_01"):
        node.run("ez_clip_chain", 600.0, 0, clip_01="")
    missing = tmp_path / "gone.mp4"
    with pytest.raises(RuntimeError, match="missing or unreadable clip_01"):
        node.run("ez_clip_chain", 600.0, 0, clip_01=str(missing))
    empty = tmp_path / "empty.mp4"
    empty.write_bytes(b"")
    with pytest.raises(RuntimeError, match="missing or unreadable clip_01"):
        node.run("ez_clip_chain", 600.0, 0, clip_01=str(empty))
    with pytest.raises(RuntimeError, match="missing or unreadable clip_01"):
        node.run("ez_clip_chain", 600.0, 0, clip_01={"x": "y"})

    clip_01 = tmp_path / "c01.mp4"
    clip_01.write_bytes(b"x")

    def fake_stitch(
        paths: list[str], out_mp4: str, cap: float, xfade_cs: int = 0
    ) -> str:
        Path(out_mp4).write_bytes(b"out")
        return out_mp4

    with patch.object(film_nodes, "stitch_clips", side_effect=fake_stitch):
        with patch.object(film_nodes, "copy_publish_master") as copy_pub:
            packed = node.run(
                "ez_clip_chain",
                600.0,
                0,
                clip_01=str(clip_01),
                clip_02=[],
                disclosure="LTX note",
            )
    copy_pub.assert_not_called()
    assert packed["result"][0].endswith("ez_clip_chain.mp4")
    sidecar = tmp_path / "ez_clip_chain.disclosure.txt"
    assert sidecar.is_file()
    assert "LTX note" in sidecar.read_text(encoding="utf-8")
    last_spec = EZClipLastFrame.INPUT_TYPES()
    assert last_spec["required"]["image"][0] == "IMAGE"


def test_stitch_clips_count_image_audio_and_fallback(tmp_path: Path) -> None:
    out = str(tmp_path / "ez_clip_chain.mp4")
    with pytest.raises(ValueError, match="expected 1-24 clips, found 0"):
        stitch_clips([], out, 600.0, ffmpeg="ffmpeg")
    too_many = [str(tmp_path / f"x{i:02d}.mp4") for i in range(25)]
    for path in too_many:
        Path(path).write_bytes(b"mp4")
    with pytest.raises(ValueError, match="expected 1-24 clips, found 25"):
        stitch_clips(too_many, out, 600.0, ffmpeg="ffmpeg")

    png = tmp_path / "still.png"
    png.write_bytes(b"png")
    with pytest.raises(RuntimeError, match="image, not an MP4"):
        stitch_clips([str(png)], out, 600.0, ffmpeg="ffmpeg")

    missing = tmp_path / "nope.mp4"
    with pytest.raises(RuntimeError, match="unreadable clip"):
        stitch_clips([str(missing)], out, 600.0, ffmpeg="ffmpeg", ffprobe="ffprobe")

    empty = tmp_path / "empty.mp4"
    empty.write_bytes(b"")
    with pytest.raises(RuntimeError, match="empty clip"):
        stitch_clips([str(empty)], out, 600.0, ffmpeg="ffmpeg", ffprobe="ffprobe")

    stem = tmp_path / "c00.mp4"
    stem.write_bytes(b"mp4")

    def refuse_run(argv: list[str], **_k: object) -> SimpleNamespace:
        raise AssertionError(f"ffmpeg should not run: {argv}")

    with (
        patch.object(film_concat, "probe_seconds", return_value=8.00),
        patch.object(film_concat, "probe_wh", return_value=(1280, 704)),
        patch.object(film_concat, "probe_has_audio", return_value=False),
    ):
        with pytest.raises(RuntimeError, match="clip missing audio"):
            stitch_clips(
                [str(stem)], out, 600.0, ffmpeg="ffmpeg", ffprobe="ffprobe",
                run=refuse_run,
            )

    with (
        patch.object(film_concat, "probe_seconds", return_value=None),
        patch.object(film_concat, "probe_wh", return_value=(1280, 704)),
        patch.object(film_concat, "probe_has_audio", return_value=True),
    ):
        with pytest.raises(RuntimeError, match="clip duration None"):
            stitch_clips(
                [str(stem)], out, 600.0, ffmpeg="ffmpeg", ffprobe="ffprobe",
                run=refuse_run,
            )

    with (
        patch.object(film_concat, "probe_seconds", return_value=8.00),
        patch.object(film_concat, "probe_wh", return_value=None),
        patch.object(film_concat, "probe_has_audio", return_value=True),
    ):
        with pytest.raises(RuntimeError, match="clip size mismatch"):
            stitch_clips(
                [str(stem)], out, 600.0, ffmpeg="ffmpeg", ffprobe="ffprobe",
                run=refuse_run,
            )

    captured: list[list[str]] = []

    def fail_then_ok(argv: list[str], **_k: object) -> SimpleNamespace:
        captured.append(list(argv))
        if len(captured) == 1:
            return _proc(stderr="Unknown encoder 'libx264'", rc=1)
        Path(str(argv[-1])).write_bytes(b"out")
        return _proc()

    with (
        patch.object(film_concat, "probe_seconds", return_value=8.00),
        patch.object(film_concat, "probe_wh", return_value=(1280, 704)),
        patch.object(film_concat, "probe_has_audio", return_value=True),
        patch.object(film_concat, "probe_audio_seconds", return_value=8.00),
    ):
        stitch_clips(
            [str(stem)], out, 600.0, ffmpeg="ffmpeg", ffprobe="ffprobe",
            run=fail_then_ok,
        )
    assert len(captured) == 2
    assert captured[0][captured[0].index("-c:v") + 1] == "libx264"
    assert captured[1][captured[1].index("-c:v") + 1] == "copy"
    assert "-t" not in captured[1]


def test_assert_clip_master_duration_gates(tmp_path: Path) -> None:
    out = tmp_path / "master.mp4"
    out.write_bytes(b"mp4")
    with patch.object(film_concat, "find_ffprobe", return_value=None):
        with pytest.raises(RuntimeError, match="ffprobe required"):
            assert_clip_master_duration(str(out), 16.0, 600.0, 2)
        assert not out.exists()
    out.write_bytes(b"mp4")
    with patch.object(film_concat, "probe_seconds", return_value=None):
        with pytest.raises(RuntimeError, match="unreadable"):
            assert_clip_master_duration(
                str(out), 16.0, 600.0, 2, ffprobe="ffprobe", run=lambda *a, **k: _proc()
            )
        assert not out.exists()
    out.write_bytes(b"mp4")
    with (
        patch.object(film_concat, "probe_seconds", return_value=16.5),
        patch.object(film_concat, "probe_has_audio", return_value=True),
        patch.object(film_concat, "probe_audio_seconds", return_value=16.5),
    ):
        with pytest.raises(RuntimeError, match="off sum"):
            assert_clip_master_duration(str(out), 16.0, 600.0, 2, ffprobe="ffprobe")
    out.write_bytes(b"mp4")
    with (
        patch.object(film_concat, "probe_seconds", return_value=15.5),
        patch.object(film_concat, "probe_has_audio", return_value=True),
        patch.object(film_concat, "probe_audio_seconds", return_value=15.5),
    ):
        with pytest.raises(RuntimeError, match="off sum"):
            assert_clip_master_duration(str(out), 16.0, 600.0, 2, ffprobe="ffprobe")
        assert not out.exists()
    out.write_bytes(b"mp4")
    with (
        patch.object(film_concat, "probe_seconds", return_value=16.0),
        patch.object(film_concat, "probe_has_audio", return_value=True),
        patch.object(film_concat, "probe_audio_seconds", return_value=16.0),
    ):
        with pytest.raises(RuntimeError, match="exceeds cap"):
            assert_clip_master_duration(str(out), 16.0, 15.8, 2, ffprobe="ffprobe")
        assert not out.exists()
    out.write_bytes(b"mp4")
    with (
        patch.object(film_concat, "probe_seconds", return_value=16.0),
        patch.object(film_concat, "probe_has_audio", return_value=False),
    ):
        with pytest.raises(RuntimeError, match="missing audio"):
            assert_clip_master_duration(str(out), 16.0, 600.0, 2, ffprobe="ffprobe")
    out.write_bytes(b"mp4")
    with (
        patch.object(film_concat, "probe_seconds", return_value=16.0),
        patch.object(film_concat, "probe_has_audio", return_value=True),
        patch.object(film_concat, "probe_audio_seconds", return_value=15.0),
    ):
        with pytest.raises(RuntimeError, match="audio duration"):
            assert_clip_master_duration(str(out), 16.0, 600.0, 2, ffprobe="ffprobe")
        assert not out.exists()
    out.write_bytes(b"mp4")
    with (
        patch.object(film_concat, "probe_seconds", return_value=16.0),
        patch.object(film_concat, "probe_has_audio", return_value=True),
        patch.object(film_concat, "probe_audio_seconds", return_value=16.0),
    ):
        assert_clip_master_duration(str(out), 16.0, 600.0, 2, ffprobe="ffprobe")
        assert out.exists()
    with patch.object(film_concat, "find_ffprobe", return_value=None):

        def _injected(argv: list[str], **_k: object) -> SimpleNamespace:
            joined = " ".join(str(a) for a in argv)
            if "codec_type" in joined:
                return _proc(stdout="audio\n")
            if "format=duration" in joined or "stream=duration" in joined:
                return _proc(stdout="16.00\n")
            return _proc()

        assert_clip_master_duration(str(out), 16.0, 600.0, 2, run=_injected)


def test_stitch_clips_ez_common_import_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stem = tmp_path / "c00.mp4"
    stem.write_bytes(b"mp4")
    out = str(tmp_path / "ez_clip_chain.mp4")

    def fake_run(argv: list[str], **_k: object) -> SimpleNamespace:
        Path(str(argv[-1])).write_bytes(b"out")
        return _proc()

    custom = os.path.abspath(str(CUSTOM))
    monkeypatch.setattr(
        sys,
        "path",
        [p for p in list(sys.path) if os.path.abspath(p) != custom],
    )
    with (
        patch.object(film_concat, "probe_seconds", return_value=8.00),
        patch.object(film_concat, "probe_wh", return_value=(1280, 704)),
        patch.object(film_concat, "probe_has_audio", return_value=True),
        patch.object(film_concat, "probe_audio_seconds", return_value=8.00),
    ):
        stitch_clips(
            [str(stem)], out, 600.0, ffmpeg="ffmpeg", ffprobe="ffprobe", run=fake_run
        )
    assert any(os.path.abspath(p) == custom for p in sys.path)

    monkeypatch.setitem(sys.modules, "ez_common", None)
    with (
        patch.object(film_concat, "probe_seconds", return_value=8.00),
        patch.object(film_concat, "probe_wh", return_value=(1280, 704)),
        patch.object(film_concat, "probe_has_audio", return_value=True),
        patch.object(film_concat, "probe_audio_seconds", return_value=8.00),
        patch.object(film_concat, "find_ffmpeg", return_value="ffmpeg"),
        patch.object(film_concat, "find_ffprobe", return_value=None),
    ):
        stitch_clips(
            [str(stem)], out, 600.0, ffmpeg=None, ffprobe=None, run=fake_run
        )

    with pytest.raises(RuntimeError, match="missing clip file"):
        stitch_clips(
            ["  "], out, 600.0, ffmpeg="ffmpeg", ffprobe="ffprobe", run=fake_run
        )
    with patch.object(film_concat, "find_ffprobe", return_value=None):
        with pytest.raises(RuntimeError, match="ffprobe required to validate clips"):
            stitch_clips([str(stem)], out, 600.0, ffmpeg="ffmpeg")

    def boom_run(argv: list[str], **_k: object) -> SimpleNamespace:
        return _proc(stderr="boom", rc=1)

    with (
        patch.object(film_concat, "probe_seconds", return_value=8.00),
        patch.object(film_concat, "probe_wh", return_value=(1280, 704)),
        patch.object(film_concat, "probe_has_audio", return_value=True),
    ):
        with pytest.raises(RuntimeError, match="ffmpeg stitch failed"):
            stitch_clips(
                [str(stem)], out, 600.0, ffmpeg="ffmpeg", ffprobe="ffprobe",
                run=boom_run,
            )

    def default_run(argv: list[str], **_k: object) -> SimpleNamespace:
        Path(str(argv[-1])).write_bytes(b"out")
        return _proc()

    monkeypatch.setattr(film_concat.subprocess, "run", default_run)
    with (
        patch.object(film_concat, "probe_seconds", return_value=8.00),
        patch.object(film_concat, "probe_wh", return_value=(1280, 704)),
        patch.object(film_concat, "probe_has_audio", return_value=True),
        patch.object(film_concat, "probe_audio_seconds", return_value=8.00),
    ):
        stitch_clips([str(stem)], out, 600.0, ffmpeg="ffmpeg", ffprobe="ffprobe")


def test_assert_master_duration_unreadable_silent_skew(tmp_path: Path) -> None:
    out = tmp_path / "master.mp4"
    out.write_bytes(b"mp4")
    with patch.object(film_concat, "probe_seconds", return_value=None):
        with pytest.raises(RuntimeError, match="unreadable"):
            assert_master_duration(str(out), 90.0, ffprobe="ffprobe", run=lambda *a, **k: _proc())
        assert not out.exists()
    out.write_bytes(b"mp4")
    with (
        patch.object(film_concat, "probe_seconds", return_value=90.0),
        patch.object(film_concat, "probe_has_audio", return_value=False),
    ):
        with pytest.raises(RuntimeError, match="missing audio"):
            assert_master_duration(str(out), 90.0, ffprobe="ffprobe")
    out.write_bytes(b"mp4")
    with (
        patch.object(film_concat, "probe_seconds", return_value=90.0),
        patch.object(film_concat, "probe_has_audio", return_value=True),
        patch.object(film_concat, "probe_audio_seconds", return_value=80.0),
    ):
        with pytest.raises(RuntimeError, match="audio duration"):
            assert_master_duration(str(out), 90.0, ffprobe="ffprobe")


def test_stitch_film_ez_common_import_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shots = _eighteen(tmp_path)
    out = str(tmp_path / "ez_gosee_90s.mp4")

    def fake_run(argv: list[str], **_k: object) -> SimpleNamespace:
        Path(str(argv[-1])).write_bytes(b"out")
        return _proc()

    custom = os.path.abspath(str(CUSTOM))
    monkeypatch.setattr(
        sys,
        "path",
        [p for p in list(sys.path) if os.path.abspath(p) != custom],
    )
    with (
        patch.object(film_concat, "validate_stitch_stems", return_value=None),
        patch.object(film_concat, "probe_seconds", return_value=90.0),
        patch.object(film_concat, "probe_has_audio", return_value=True),
        patch.object(film_concat, "probe_audio_seconds", return_value=90.0),
    ):
        stitch_film(shots, out, 90.0, ffmpeg="ffmpeg", run=fake_run)
    assert any(os.path.abspath(p) == custom for p in sys.path)

    monkeypatch.setitem(sys.modules, "ez_common", None)
    with (
        patch.object(film_concat, "validate_stitch_stems", return_value=None),
        patch.object(film_concat, "probe_seconds", return_value=90.0),
        patch.object(film_concat, "probe_has_audio", return_value=True),
        patch.object(film_concat, "probe_audio_seconds", return_value=90.0),
    ):
        stitch_film(shots, out, 90.0, ffmpeg="ffmpeg", run=fake_run)


def test_accept_find_and_probe_error_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(acc.shutil, "which", lambda name: f"/bin/{name}")
    assert acc.find_ffprobe() == "/bin/ffprobe"
    assert acc.find_ffmpeg() == "/bin/ffmpeg"
    shot = tmp_path / "01.mp4"
    shot.write_bytes(b"x")

    def boom(*_a: object, **_k: object) -> SimpleNamespace:
        raise OSError("no probe")

    assert acc.probe_duration_s(shot, ffprobe="ffprobe", run=boom) is None
    assert acc.probe_duration_s(shot, ffprobe="ffprobe", run=lambda *_a, **_k: _proc("")) is None
    assert acc.probe_duration_s(shot, ffprobe="ffprobe", run=lambda *_a, **_k: _proc("nope")) is None
    assert acc.probe_wh(shot, ffprobe="ffprobe", run=boom) is None
    assert acc.probe_wh(shot, ffprobe="ffprobe", run=lambda *_a, **_k: _proc("")) is None
    assert acc.probe_wh(shot, ffprobe="ffprobe", run=lambda *_a, **_k: _proc("1280")) is None
    assert acc.probe_wh(shot, ffprobe="ffprobe", run=lambda *_a, **_k: _proc("a,b")) is None
    assert acc.probe_has_audio(shot, ffprobe="ffprobe", run=boom) is False
    assert acc.probe_lufs(shot, ffmpeg=None) is None
    missing = tmp_path / "missing.mp4"
    monkeypatch.setattr(acc.shutil, "which", lambda _n: "/bin/ffmpeg")
    assert acc.probe_lufs(missing, ffmpeg="ffmpeg") is None
    assert acc.probe_lufs(shot, ffmpeg="ffmpeg", run=boom) is None
    assert (
        acc.probe_lufs(
            shot,
            ffmpeg="ffmpeg",
            run=lambda *_a, **_k: _proc(stderr='{"input_i": "-14.0"}'),
        )
        == -14.0
    )
    assert acc.parse_astats_rms_db("nope") is None
    assert acc.parse_astats_peak_db("nope") is None
    monkeypatch.setattr(acc, "_RMS_DB_RE", re.compile(r"RMS level dB:\s*(\S+)"))
    assert acc.parse_astats_rms_db("RMS level dB: nope") is None
    monkeypatch.setattr(acc, "_PEAK_DB_RE", re.compile(r"Peak level dB:\s*(\S+)"))
    assert acc.parse_astats_peak_db("Peak level dB: nope") is None


def test_accept_silence_speech_and_ffmpeg_af(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shot = tmp_path / "talk.mp4"
    shot.write_bytes(b"x")
    assert acc.parse_sustained_nonsilence_s("silence_start: 0.00\n", 0.0) == 0.0
    merged = acc.parse_sustained_nonsilence_s(
        "silence_start: 0.00\nsilence_end: 2.00\n"
        "silence_start: 1.00\nsilence_end: 3.00\n",
        5.00,
    )
    assert merged == pytest.approx(2.00)
    gapped = acc.parse_sustained_nonsilence_s(
        "silence_start: 0.00\nsilence_end: 0.10\n"
        "silence_start: 2.00\nsilence_end: 2.10\n",
        5.00,
    )
    assert gapped > 0.40
    monkeypatch.setattr(acc, "find_ffmpeg", lambda: None)
    assert acc._ffmpeg_af(shot, "astats") == ""  # noqa: SLF001
    assert acc._ffmpeg_af(tmp_path / "nope.mp4", "astats", ffmpeg="ffmpeg") == ""  # noqa: SLF001

    def boom(*_a: object, **_k: object) -> SimpleNamespace:
        raise OSError("ffmpeg")

    assert acc._ffmpeg_af(shot, "astats", ffmpeg="ffmpeg", run=boom) == ""  # noqa: SLF001

    real_rms = acc.parse_astats_rms_db
    rms_vals = iter([0.0, float("nan")])
    monkeypatch.setattr(acc, "parse_astats_rms_db", lambda _t: next(rms_vals))
    assert acc.probe_speech_band_ratio(shot, ffmpeg="ffmpeg", run=lambda *_a, **_k: _proc()) is None
    monkeypatch.setattr(acc, "parse_astats_rms_db", lambda _t: None)
    assert acc.probe_speech_band_ratio(shot, ffmpeg="ffmpeg", run=lambda *_a, **_k: _proc()) is None
    monkeypatch.setattr(acc, "parse_astats_rms_db", real_rms)

    real_dur = acc.probe_duration_s
    monkeypatch.setattr(acc, "probe_duration_s", lambda *_a, **_k: None)
    assert acc.probe_sustained_nonsilence_s(shot, ffmpeg="ffmpeg") is None
    monkeypatch.setattr(acc, "probe_duration_s", real_dur)

    def empty_silence(argv: list[str], **_k: object) -> SimpleNamespace:
        joined = " ".join(str(a) for a in argv)
        if "silencedetect" in joined:
            return _proc()
        return _proc(stderr="RMS level dB: -16.00\nPeak level dB: -12.00\n")

    assert (
        acc.probe_sustained_nonsilence_s(
            shot, duration_s=5.00, ffmpeg="ffmpeg", run=empty_silence
        )
        is None
    )
    defects = acc.world_only_speech_defects(
        shot, "01", duration_s=5.00, ffmpeg="ffmpeg", run=lambda *_a, **_k: _proc()
    )
    assert any("could not measure speech-band" in d for d in defects)
    peak_fail = acc.world_only_speech_defects(
        shot, "01", duration_s=5.00, ffmpeg="ffmpeg", run=empty_silence
    )
    assert any("peak/silence" in d for d in peak_fail)


def test_accept_fps_audio_master_shot_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shot = tmp_path / "01.mp4"
    shot.write_bytes(b"x")
    monkeypatch.setattr(acc, "find_ffprobe", lambda: None)
    assert acc.probe_fps(shot, ffprobe=None) is None
    assert acc.probe_fps(tmp_path / "missing.mp4", ffprobe="ffprobe") is None

    def boom(*_a: object, **_k: object) -> SimpleNamespace:
        raise OSError("x")

    assert acc.probe_fps(shot, ffprobe="ffprobe", run=boom) is None
    assert acc.probe_fps(shot, ffprobe="ffprobe", run=lambda *_a, **_k: _proc("")) is None
    assert acc.probe_fps(shot, ffprobe="ffprobe", run=lambda *_a, **_k: _proc("24/0")) is None
    assert acc.probe_fps(shot, ffprobe="ffprobe", run=lambda *_a, **_k: _proc("a/b")) is None
    assert acc.probe_fps(shot, ffprobe="ffprobe", run=lambda *_a, **_k: _proc("24.0")) == 24.0
    assert acc.probe_fps(shot, ffprobe="ffprobe", run=lambda *_a, **_k: _proc("nope")) is None
    monkeypatch.setattr(acc, "find_ffprobe", lambda: None)
    assert acc.probe_audio_duration_s(shot, ffprobe=None) is None
    assert acc.probe_audio_duration_s(tmp_path / "missing.mp4", ffprobe="ffprobe") is None
    assert acc.probe_audio_duration_s(shot, ffprobe="ffprobe", run=boom) is None

    def na_then_format(argv: list[str], **_k: object) -> SimpleNamespace:
        joined = " ".join(str(a) for a in argv)
        if "stream=duration" in joined:
            return _proc(stdout="not-a-float\n")
        return _proc(stdout="5.00\n")

    assert acc.probe_audio_duration_s(shot, ffprobe="ffprobe", run=na_then_format) == 5.00
    assert acc.accept_master(tmp_path / "missing.mp4") == [
        f"master: missing {tmp_path / 'missing.mp4'}"
    ]

    master = tmp_path / "master.mp4"
    master.write_bytes(b"x")
    monkeypatch.setattr(acc, "probe_duration_s", lambda *_a, **_k: 80.0)
    monkeypatch.setattr(acc, "probe_wh", lambda *_a, **_k: (640, 480))
    monkeypatch.setattr(acc, "probe_fps", lambda *_a, **_k: 12.0)
    monkeypatch.setattr(acc, "probe_has_audio", lambda *_a, **_k: False)
    monkeypatch.setattr(acc, "world_only_speech_defects", lambda *_a, **_k: [])
    defects = acc.accept_master(master, ffprobe="ffprobe", ffmpeg="ffmpeg")
    assert any("duration" in d for d in defects)
    assert any("size" in d for d in defects)
    assert any("fps" in d for d in defects)
    assert any("missing audio" in d for d in defects)
    monkeypatch.setattr(acc, "probe_duration_s", lambda *_a, **_k: 90.0)
    monkeypatch.setattr(acc, "probe_wh", lambda *_a, **_k: (1280, 704))
    monkeypatch.setattr(acc, "probe_fps", lambda *_a, **_k: 24.0)
    monkeypatch.setattr(acc, "probe_has_audio", lambda *_a, **_k: True)
    monkeypatch.setattr(acc, "probe_audio_duration_s", lambda *_a, **_k: 80.0)
    skew = acc.accept_master(master, ffprobe="ffprobe", ffmpeg="ffmpeg")
    assert any("audio duration" in d for d in skew)

    dest = _compile(tmp_path)
    row = {"id": "01", "status": "ok", "mp4": "shots/01.mp4", "backend": "ltx"}
    missing = acc.accept_shot(dest, row, ffprobe="ffprobe")
    assert any("missing" in d for d in missing)
    mp4 = dest / "shots" / "01.mp4"
    mp4.parent.mkdir(parents=True, exist_ok=True)
    mp4.write_bytes(b"x")
    monkeypatch.setattr(acc, "probe_duration_s", lambda *_a, **_k: 3.0)
    monkeypatch.setattr(acc, "probe_wh", lambda *_a, **_k: (1, 1))
    monkeypatch.setattr(acc, "probe_has_audio", lambda *_a, **_k: False)
    monkeypatch.setattr(acc, "world_only_speech_defects", lambda *_a, **_k: [])
    shot_defects = acc.accept_shot(dest, row, ffprobe="ffprobe")
    assert any("duration" in d for d in shot_defects)
    assert any("size" in d for d in shot_defects)
    assert any("missing audio" in d for d in shot_defects)

    state = js.load_state(dest)
    state["shots"] = state["shots"][:2]
    js.save_state(dest, state)
    report = acc.accept_film(dest)
    assert any("shot count" in d for d in report["defects"])

    dest2 = tmp_path / "films" / "other"
    dest2.mkdir(parents=True)
    (dest2 / "state.json").write_text("[]\n", encoding="utf-8")
    assert acc._cli(["--dest", str(tmp_path / "missing-store")]) == 1  # noqa: SLF001
    assert acc._cli(["--dest", str(dest2)]) == 1  # noqa: SLF001

    dest3 = _compile(tmp_path / "ok")
    state = js.load_state(dest3)
    for row in state["shots"]:
        sid = row["id"]
        path = dest3 / "shots" / f"{sid}.mp4"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x")
        js.mark_shot(state, sid, "ok", mp4=f"shots/{sid}.mp4", backend="ltx")
    js.save_state(dest3, state)
    monkeypatch.setattr(acc, "probe_duration_s", lambda *_a, **_k: 5.00)
    monkeypatch.setattr(acc, "probe_wh", lambda *_a, **_k: (1280, 704))
    monkeypatch.setattr(acc, "probe_has_audio", lambda *_a, **_k: True)
    monkeypatch.setattr(acc, "world_only_speech_defects", lambda *_a, **_k: [])
    assert acc._cli(["--dest", str(dest3)]) == 0  # noqa: SLF001


def test_animatic_count_ffmpeg_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(an.shutil, "which", lambda _n: "/usr/bin/ffmpeg")
    assert an.find_ffmpeg() == "/usr/bin/ffmpeg"
    real_parse = an.parse_shots_yaml
    real_sources = an.shot_sources
    monkeypatch.setattr(an, "parse_shots_yaml", lambda _t: {"meta": {"slug": "gosee"}, "shots": []})
    monkeypatch.setattr(an, "shot_sources", lambda *_a, **_k: [])
    report = an.build_animatic("x", tmp_path, guides=tmp_path, ffmpeg="/usr/bin/ffmpeg")
    assert any("shot count" in d for d in report["defects"])
    monkeypatch.setattr(an, "parse_shots_yaml", real_parse)
    monkeypatch.setattr(an, "shot_sources", real_sources)

    guides = tmp_path / "guides"
    for index in range(1, 19):
        pack = guides / f"{index:02d}"
        pack.mkdir(parents=True)
        (pack / "first.png").write_bytes(b"png")
    monkeypatch.setattr(an, "find_ffmpeg", lambda: None)
    report = an.build_animatic(
        _go_see_yaml(), tmp_path / "films" / "gosee", guides=guides, ffmpeg=None
    )
    assert any("ffmpeg missing" in d for d in report["defects"])

    def fail_run(_argv: list[str], **_k: object) -> SimpleNamespace:
        return _proc(stderr="boom", rc=1)

    report = an.build_animatic(
        _go_see_yaml(),
        tmp_path / "films" / "gosee2",
        guides=guides,
        ffmpeg="/usr/bin/ffmpeg",
        run=fail_run,
    )
    assert report["ok"] is False
    assert any("ffmpeg rc=" in d for d in report["defects"])

    monkeypatch.setattr(
        an,
        "build_animatic",
        lambda *_a, **_k: {"ok": True, "defects": []},
    )
    yaml_path = SHORTS / "go-see.shots.yaml"
    assert (
        an._cli(  # noqa: SLF001
            [
                "--yaml",
                str(yaml_path),
                "--dest",
                str(tmp_path),
                "--guides",
                str(guides),
                "--stills",
                str(tmp_path / "stills"),
            ]
        )
        == 0
    )
    monkeypatch.setattr(
        an,
        "build_animatic",
        lambda *_a, **_k: {"ok": False, "defects": ["missing sources"]},
    )
    assert (
        an._cli(  # noqa: SLF001
            ["--yaml", str(yaml_path), "--dest", str(tmp_path), "--guides", str(guides)]
        )
        == 1
    )


def test_jobstore_edges_cli_and_pins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert js.film_dir(tmp_path, "gosee") == tmp_path / "films" / "gosee"
    dest = _compile(tmp_path)
    (dest / "state.json").write_text("[]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid jobstore"):
        js.load_state(dest)

    dest = _compile(tmp_path / "ok")
    p = dest / "shots" / "01.mp4"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"x")
    monkeypatch.setattr(js.shutil, "which", lambda _n: "/usr/bin/ffprobe")

    def empty_run(*_a: object, **_k: object) -> SimpleNamespace:
        return _proc(stdout="  \n")

    monkeypatch.setattr(js.subprocess, "run", empty_run)
    assert js.probe_duration_s(p) is None
    assert js.duration_ok(p) is False
    assert js.file_sha(tmp_path / "missing.mp4") == ""
    assert js.list_takes(dest, "01") == []
    with pytest.raises(FileNotFoundError, match="missing take source"):
        js.record_take(dest, js.load_state(dest), "01", tmp_path / "nope.mp4")

    state = js.load_state(dest)
    js.mark_shot(state, "02", "skipped")
    js.save_state(dest, state)
    assert "02" not in js.resume_ids(dest, state)

    models = tmp_path / "models"
    comfy = models / "comfy"
    comfy.mkdir(parents=True)
    pin = comfy / ".lab-model-pins.json"
    pin.write_text("[]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid pins"):
        js.load_pins(models)
    pin.write_text('{"ltx": "", "wan": ""}\n', encoding="utf-8")
    js.require_pins(models)

    bad = _go_see_yaml().replace("slug: gosee", "slug: nope", 1)
    with pytest.raises(ValueError, match="slug mismatch"):
        js.compile_film(bad, tmp_path / "mismatch")

    dest = _compile(tmp_path / "cli")
    src = tmp_path / "raw.mp4"
    src.write_bytes(b"take")
    assert (
        js._cli(  # noqa: SLF001
            ["record-take", "--dest", str(dest), "--id", "01", "--src", str(src)]
        )
        == 0
    )
    assert js._cli(["promote", "--dest", str(dest), "--id", "01", "--take", "1"]) == 0  # noqa: SLF001

    orig = argparse.ArgumentParser.parse_args

    def _unknown(
        self: argparse.ArgumentParser,
        args: list[str] | None = None,
        namespace: argparse.Namespace | None = None,
    ) -> argparse.Namespace:
        ns = orig(self, args, namespace)
        assert ns is not None
        ns.cmd = "nope"
        return ns

    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", _unknown)
    assert js._cli(["get", "--dest", str(dest), "--id", "01"]) == 1  # noqa: SLF001


def test_overlay_png_blend_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert ov.png_size(tmp_path) is None
    junk = tmp_path / "x.bin"
    junk.write_bytes(b"not-a-png-file-at-all")
    assert ov.png_size(junk) is None
    fake_png = tmp_path / "ihdr.png"
    fake_png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"xxxx" + b"NOPE" + b"\x00" * 8)
    assert ov.png_size(fake_png) is None
    monkeypatch.setattr(ov.shutil, "which", lambda _n: "/usr/bin/ffmpeg")
    assert ov.find_ffmpeg() == "/usr/bin/ffmpeg"
    assert ov.parse_psnr("average:1.2.3") is None

    clay = tmp_path / "clay.png"
    look_missing = tmp_path / "missing-look.png"
    clay.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\rIHDR"
        + struct.pack(">II", 640, 704)
        + b"\x00" * 5
    )
    report = ov.overlay_qc(clay, look_missing, tmp_path / "out", ffmpeg="/usr/bin/ffmpeg")
    assert any("missing look" in d for d in report["defects"])
    assert any("clay size" in d for d in report["defects"])

    good_clay = tmp_path / "first.png"
    good_look = tmp_path / "look.png"
    gp.write_solid_png(good_clay, 1280, 704, (10, 10, 10))
    gp.write_solid_png(good_look, 1280, 704, (20, 20, 20))

    def fail_blend(_argv: list[str], **_k: object) -> SimpleNamespace:
        return _proc(stderr="blend boom", rc=1)

    dest = tmp_path / "qc"
    report = ov.overlay_qc(
        good_clay, good_look, dest, ffmpeg="/usr/bin/ffmpeg", run=fail_blend
    )
    assert any("blend failed" in d for d in report["defects"])

    monkeypatch.setattr(ov, "overlay_qc", lambda *_a, **_k: {"ok": True, "defects": []})
    assert (
        ov._cli(  # noqa: SLF001
            ["--clay", str(good_clay), "--look", str(good_look), "--dest", str(dest)]
        )
        == 0
    )


def test_otio_skips_missing_and_external_media(tmp_path: Path) -> None:
    dest = _compile(tmp_path)
    state = js.load_state(dest)
    js.mark_shot(state, "01", "ok", mp4="shots/01.mp4")
    outside = tmp_path / "outside.mp4"
    outside.write_bytes(b"x")
    js.mark_shot(state, "02", "ok", mp4=str(outside))
    js.save_state(dest, state)
    timeline = otio.build_timeline(dest)
    clips = timeline["tracks"]["children"][0]["children"]
    assert len(clips) == 1
    assert clips[0]["name"] == "02"
    assert clips[0]["media_reference"]["target_url"] == str(outside)
    assert otio._cli(["--dest", str(dest)]) == 0  # noqa: SLF001
    assert (dest / "publish" / "gosee.otio").is_file()


def test_stems_filter_lufs_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(st.shutil, "which", lambda _n: "/usr/bin/ffmpeg")
    assert st.find_ffmpeg() == "/usr/bin/ffmpeg"
    multi = st.mix_filter(has_dx=False, bed_count=2)
    assert "amix=inputs=2" in multi
    dest = tmp_path / "mix.m4a"
    with pytest.raises(ValueError, match="no stems"):
        st.mix_argv([], dest, has_dx=False)
    bg = tmp_path / "bg.wav"
    dx = tmp_path / "dx.wav"
    bg.write_bytes(b"x")
    dx.write_bytes(b"x")
    video = tmp_path / "pic.mp4"
    video.write_bytes(b"x")
    argv = st.mix_argv([dx, bg], dest, has_dx=True, video=video)
    joined = " ".join(argv)
    assert "0:v:0" in joined
    assert "[1:a]" in joined
    assert st.parse_lufs("{not-json}") is None
    assert st.parse_lufs('{"input_i": "nope"}') is None
    assert st.parse_lufs('{"input_i": [1]}') is None
    assert st.parse_lufs('"input_i": "-13.1"') == -13.1
    assert st.parse_lufs("nope") is None

    report = st.mix_stems(
        tmp_path / "stems" / "01",
        dx=tmp_path / "missing-dx.wav",
        bg=tmp_path / "missing-bg.wav",
        ffmpeg="/usr/bin/ffmpeg",
    )
    assert any("missing DX" in d for d in report["defects"])
    assert any("missing bed" in d for d in report["defects"])
    monkeypatch.setattr(st, "find_ffmpeg", lambda: None)
    report = st.mix_stems(tmp_path / "stems" / "01", bg=bg, ffmpeg=None)
    assert any("ffmpeg missing" in d for d in report["defects"])

    def fail_run(_argv: list[str], **_k: object) -> SimpleNamespace:
        return _proc(stderr="mix fail", rc=1)

    report = st.mix_stems(
        tmp_path / "stems" / "02", bg=bg, ffmpeg="/usr/bin/ffmpeg", run=fail_run
    )
    assert any("ffmpeg rc=" in d for d in report["defects"])

    monkeypatch.setattr(st, "mix_stems", lambda *_a, **_k: {"ok": True, "defects": []})
    assert (
        st._cli(  # noqa: SLF001
            [
                "--dest",
                str(tmp_path / "stems" / "03"),
                "--dx",
                str(dx),
                "--bg",
                str(bg),
                "--fx",
                str(bg),
                "--mx",
                str(bg),
                "--video",
                str(video),
                "--duck-db",
                "-15",
            ]
        )
        == 0
    )
    monkeypatch.setattr(
        st, "mix_stems", lambda *_a, **_k: {"ok": False, "defects": ["no stems"]}
    )
    assert st._cli(["--dest", str(tmp_path / "stems" / "04")]) == 1  # noqa: SLF001


def test_shots_parse_emit_and_validation() -> None:
    from ez_film.prompt_enums import validate_camera, validate_foley

    with pytest.raises(ValueError, match="unknown camera"):
        validate_camera("crash zoom")
    with pytest.raises(ValueError, match="unknown foley"):
        validate_foley("orchestra swell")
    assert sh.print_template("ltx-iclora-depth") == sh.ICLORA_TEMPLATE
    assert sh.print_template("wan-flf") == sh.WAN_FLF_TEMPLATE
    assert sh.print_template("dcc-final") == sh.DCC_FINAL_TEMPLATE
    with pytest.raises(ValueError, match="print must be"):
        sh.print_template("nope")
    assert sh.normalize_camera("") == ""
    assert sh.normalize_camera("fixed") == "fixed camera"
    assert sh._block_field("ltx_i2v: |\n      hello\n\n      more\n", "ltx_i2v") == "hello"  # noqa: SLF001
    text = _go_see_yaml()
    with pytest.raises(ValueError, match="missing block"):
        sh.parse_shots_yaml(text.replace("    ltx_i2v: |\n", "    ltx_missing: |\n", 1))
    odd = re.sub(
        r"(    ltx_i2v: \|\n      The start image holds as the first frame\.[^\n]*\n)",
        r"\1   odd-indent\n",
        text,
        count=1,
    )
    parsed_odd = sh.parse_shots_yaml(odd)
    assert "odd-indent" not in parsed_odd["shots"][0]["ltx_i2v"]
    empty_block = re.sub(
        r"(    ltx_i2v: \|\n)(?:      .*\n)+",
        r"\1",
        text,
        count=1,
    )
    with pytest.raises(ValueError, match="empty block"):
        sh.parse_shots_yaml(empty_block)
    with pytest.raises(ValueError, match="audio_policy"):
        sh.parse_shots_yaml("audio_policy: karaoke\n" + text)
    scaffold = sh.scaffold_shot_sheet(text)
    assert "audio_policy: world-only" in scaffold
    with pytest.raises(ValueError, match="missing prefix"):
        sh.parse_shots_yaml(text.replace("    prefix: ez_gosee_b1_s1\n", "", 1))
    with pytest.raises(ValueError, match="unknown camera"):
        sh.parse_shots_yaml(text.replace("    camera: tracking\n", "    camera: crash zoom\n", 1))
    with pytest.raises(ValueError, match="print_mode"):
        mutated = text.replace(
            "    camera: tracking\n",
            "    camera: tracking\n    print_mode: nope\n",
            1,
        )
        sh.parse_shots_yaml(mutated)
    with pytest.raises(ValueError, match="missing meta"):
        sh.parse_shots_yaml(text.replace("frames: 121\n", "", 1))
    with pytest.raises(ValueError, match="print must be"):
        sh.parse_shots_yaml(text.replace("print: ltx", "print: nope", 1))
    with pytest.raises(ValueError, match="identity_seed"):
        sh.parse_shots_yaml(text.replace("identity_seed: 42", "identity_seed: 7", 1))
    with pytest.raises(ValueError, match="identity_enhance"):
        sh.parse_shots_yaml(
            text.replace("identity_enhance: false", "identity_enhance: maybe", 1)
        )
    with pytest.raises(ValueError, match="missing identity_look"):
        sh.parse_shots_yaml(text.replace("identity_look:", "identity_look_missing:", 1))
    assert "(empty)" in sh._emit_block("ltx_i2v", "", "    ")  # noqa: SLF001
    parsed = sh.parse_shots_yaml(text)
    parsed["shots"][0]["print_mode"] = "dfr"
    parsed["shots"][0]["look"] = "plate: terrace"
    out = sh.write_shots_yaml(parsed)
    assert "print_mode: dfr" in out
    assert "look:" in out
    again = sh.parse_shots_yaml(out)
    assert again["shots"][0]["print_mode"] == "dfr"
    assert again["shots"][0]["look"] == "plate: terrace"


@pytest.mark.parametrize(
    "mod",
    [
        "ez_film.accept",
        "ez_film.animatic",
        "ez_film.catalog",
        "ez_film.jobstore",
        "ez_film.overlay",
        "ez_film.otio_export",
        "ez_film.stems",
    ],
)
def test_module_main_help(mod: str, monkeypatch: pytest.MonkeyPatch) -> None:
    _cover_main(mod, monkeypatch)
