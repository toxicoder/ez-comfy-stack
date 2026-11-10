"""Unit tests for docker/seed_clay_inputs.py (container LoadImage backstop).

Hermetic: stdlib PNG writer only. No Blender, Comfy, or network.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pytest
import seed_clay_inputs as seed


def test_seed_writes_ten_distinct_valid_plates(tmp_path: Path) -> None:
    dest = tmp_path / "input"
    written = seed.seed_clay_inputs(dest)
    names = [path.name for path in written]
    assert names == [f"ez_house_clay_{i:02d}.png" for i in range(1, 11)]
    first = dest / "ez_house_clay_01.png"
    second = dest / "ez_house_clay_02.png"
    tenth = dest / "ez_house_clay_10.png"
    assert seed.png_size(first) == (1024, 1280)
    assert seed.png_size(tenth) == (1024, 1280)
    assert seed.clay_plate_valid(first)
    assert first.read_bytes() != second.read_bytes()
    assert seed.plate_rgb(0) != seed.plate_rgb(9)


def test_seed_skips_valid_and_replaces_wrong_size(tmp_path: Path) -> None:
    dest = tmp_path / "input"
    dest.mkdir()
    keep = dest / "ez_house_clay_01.png"
    seed.write_solid_png(keep, 1024, 1280, (10, 20, 30))
    before = keep.read_bytes()
    bad = dest / "ez_house_clay_02.png"
    seed.write_solid_png(bad, 8, 8, (1, 2, 3))
    written = seed.seed_clay_inputs(dest)
    assert len(written) == 10
    assert keep.read_bytes() == before
    assert seed.clay_plate_valid(dest / "ez_house_clay_02.png")
    assert seed.png_size(dest / "ez_house_clay_02.png") == (1024, 1280)


def test_png_size_rejects_garbage(tmp_path: Path) -> None:
    junk = tmp_path / "nope.bin"
    junk.write_bytes(b"not a png")
    assert seed.png_size(junk) is None
    assert seed.clay_plate_valid(junk) is False
    missing = tmp_path / "missing.png"
    assert seed.png_size(missing) is None


def test_write_rgb_png_rejects_bad_length(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="rgb buffer"):
        seed.write_rgb_png(tmp_path / "x.png", 2, 2, b"short")


def test_seed_ok_when_models_dir_is_elsewhere(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    models = tmp_path / "models"
    models.mkdir()
    monkeypatch.setenv("MODELS_DIR", str(models))
    dest = tmp_path / "input"
    written = seed.seed_clay_inputs(dest)
    assert len(written) == 10
    assert seed.clay_plate_valid(dest / "ez_house_clay_01.png")


def test_refuses_models_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    models = tmp_path / "models"
    models.mkdir()
    monkeypatch.setenv("MODELS_DIR", str(models))
    with pytest.raises(ValueError, match="MODELS_DIR"):
        seed.seed_clay_inputs(models / "input")
    monkeypatch.delenv("MODELS_DIR")
    monkeypatch.setenv("MODELS_ROOT", str(models))
    with pytest.raises(ValueError, match="MODELS_DIR"):
        seed.seed_clay_inputs(models / "blocked")


def test_main_success_and_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    dest = tmp_path / "in"
    assert seed.main([str(dest)]) == 0
    assert "10 plates" in capsys.readouterr().out
    models = tmp_path / "models"
    models.mkdir()
    monkeypatch.setenv("MODELS_DIR", str(models))
    assert seed.main([str(models / "nope")]) == 1
    assert "failed" in capsys.readouterr().err


def test_main_default_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["seed_clay_inputs.py"])
    called: dict[str, Path] = {}

    def _fake_seed(path: str | Path) -> list[Path]:
        called["path"] = Path(path)
        return [tmp_path / "ez_house_clay_01.png"]

    monkeypatch.setattr(seed, "seed_clay_inputs", _fake_seed)
    monkeypatch.setattr(seed, "seed_example_input", lambda _p: None)
    assert seed.main() == 0
    assert called["path"] == Path("/inputs")
    assert "plates ready" in capsys.readouterr().out


def test_module_main_entrypoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dest = tmp_path / "cli"
    monkeypatch.setattr(
        sys,
        "argv",
        ["seed_clay_inputs.py", str(dest)],
    )
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(
            str(
                Path(__file__).resolve().parents[2] / "docker" / "seed_clay_inputs.py"
            ),
            run_name="__main__",
        )
    assert exc.value.code == 0
    assert (dest / "ez_house_clay_10.png").is_file()


def test_clay_copy_name() -> None:
    assert seed.clay_copy_name(0) == "ez_house_clay_01.png"
    assert seed.clay_copy_name(9) == "ez_house_clay_10.png"


def test_main_writes_example_plate(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    dest = tmp_path / "in"
    assert seed.main([str(dest)]) == 0
    out = capsys.readouterr().out
    assert "wrote example.png" in out
    assert seed.png_size(dest / "example.png") == (
        seed.EXAMPLE_WIDTH,
        seed.EXAMPLE_HEIGHT,
    )


def test_example_keeps_operator_plate(tmp_path: Path) -> None:
    dest = tmp_path / "in"
    dest.mkdir()
    plate = dest / "example.png"
    seed.write_solid_png(plate, 64, 64, (1, 2, 3))
    before = plate.read_bytes()
    assert seed.seed_example_input(dest) is None
    assert plate.read_bytes() == before


def test_example_replaces_corrupt_file(tmp_path: Path) -> None:
    dest = tmp_path / "in"
    dest.mkdir()
    (dest / "example.png").write_bytes(b"not a png")
    assert seed.example_png_valid(dest / "example.png") is False  # noqa: SLF001
    written = seed.seed_example_input(dest)
    assert written is not None
    assert seed.png_size(written) == (seed.EXAMPLE_WIDTH, seed.EXAMPLE_HEIGHT)


def test_example_refuses_models_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    models = tmp_path / "models"
    models.mkdir()
    monkeypatch.delenv("MODELS_DIR", raising=False)
    monkeypatch.setenv("MODELS_ROOT", str(models))
    with pytest.raises(ValueError, match="MODELS_DIR"):
        seed.seed_example_input(models / "blocked")


def test_example_pixels_are_deterministic_gradient() -> None:
    width, height = 8, 8
    data = seed.example_pixels(width, height)  # noqa: SLF001
    assert len(data) == width * height * 3
    top = data[0:3]
    bottom = data[(height - 1) * width * 3 : (height - 1) * width * 3 + 3]
    assert top != bottom
    assert seed.example_pixels(width, height) == data  # noqa: SLF001
