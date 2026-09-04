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
    concat_list_line,
    ffmpeg_stitch_argv,
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
    assert argv[0] == "ffmpeg"
    assert "-t" in argv
    assert argv[argv.index("-t") + 1] == "90.0"
    assert "-c:v" in argv and argv[argv.index("-c:v") + 1] == "copy"
    assert "-c:a" in argv and argv[argv.index("-c:a") + 1] == "aac"
    assert LOUDNORM_FILTER in argv
    assert argv[-1] == "/tmp/out.mp4"


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

    def fake_stitch(paths, out_mp4, cap):
        assert len(paths) == SHOT_COUNT
        assert cap == DEFAULT_CAP_SECONDS
        Path(out_mp4).write_bytes(b"out")
        return out_mp4

    with patch.object(film_nodes, "stitch_film", side_effect=fake_stitch):
        packed = EZFilmConcat().run("go-see", 90.0, **shots)
    assert packed["result"][0].endswith("ez_gosee_90s.mp4")
    assert packed["ui"]["gifs"][0]["filename"] == "ez_gosee_90s.mp4"
    assert packed["ui"]["gifs"][0]["format"] == "video/h264-mp4"
