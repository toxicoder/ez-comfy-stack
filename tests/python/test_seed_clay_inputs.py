"""Unit tests for docker/seed_clay_inputs.py (container LoadImage backstop).

Hermetic: stdlib PNG writer only. No Blender, Comfy, or network. The drift test
reads the committed lab graphs, the same tree the other suites walk.
"""

from __future__ import annotations

import runpy
import struct
import sys
import wave
from pathlib import Path

import pytest
import seed_clay_inputs as seed
from _lab_paths import cached_lab_graph_rows

_AUDIO_LOADERS = {"LoadAudio", "LoadVideo", "VHS_LoadVideo", "VHS_LoadAudio"}
_AUDIO_SUFFIXES = (".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac", ".mov", ".webm")


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


def test_refuses_models_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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
    monkeypatch.setattr(seed, "seed_audio_bed_input", lambda _p: None)
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
            str(Path(__file__).resolve().parents[2] / "docker" / "seed_clay_inputs.py"),
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


def _bare_load_image_defaults() -> set[str]:
    """Every bare ``*.png`` LoadImage default across the shipped lab graphs."""
    names: set[str] = set()
    for _lab_rel, _path, data in cached_lab_graph_rows():
        pending: list[object] = [data]
        while pending:
            node = pending.pop()
            if isinstance(node, dict):
                if node.get("type") == "LoadImage":
                    widgets = node.get("widgets_values")
                    if isinstance(widgets, list) and widgets:
                        first = widgets[0]
                        if (
                            isinstance(first, str)
                            and first.lower().endswith(".png")
                            and "/" not in first
                            and "\\" not in first
                        ):
                            names.add(first)
                pending.extend(node.values())
            elif isinstance(node, list):
                pending.extend(node)
    return names


def test_placeholder_writes_every_table_plate(tmp_path: Path) -> None:
    dest = tmp_path / "input"
    written = seed.seed_placeholder_inputs(dest)
    assert [path.name for path in written] == [
        plate.name for plate in seed.PLACEHOLDER_PLATES
    ]
    blobs = set()
    for plate in seed.PLACEHOLDER_PLATES:
        path = dest / plate.name
        assert seed.png_size(path) == (plate.width, plate.height)
        assert seed.example_png_valid(path)
        blobs.add(path.read_bytes())
    assert len(blobs) == len(seed.PLACEHOLDER_PLATES)


def test_placeholder_table_is_unique_disjoint_and_varied() -> None:
    table = {plate.name for plate in seed.PLACEHOLDER_PLATES}
    owned = {seed.EXAMPLE_NAME} | {
        seed.clay_copy_name(index) for index in range(seed.CLAY_COUNT)
    }
    assert table.isdisjoint(owned)
    assert len(table) == len(seed.PLACEHOLDER_PLATES)
    assert len({(plate.width, plate.height) for plate in seed.PLACEHOLDER_PLATES}) > 1


def test_placeholder_keeps_operator_plate(tmp_path: Path) -> None:
    dest = tmp_path / "input"
    dest.mkdir()
    plate = dest / "cover.png"
    seed.write_solid_png(plate, 64, 64, (7, 8, 9))
    before = plate.read_bytes()
    written = seed.seed_placeholder_inputs(dest)
    assert plate.read_bytes() == before
    assert seed.png_size(plate) == (64, 64)
    assert "cover.png" not in [path.name for path in written]


def test_placeholder_replaces_corrupt_file(tmp_path: Path) -> None:
    dest = tmp_path / "input"
    seed.seed_placeholder_inputs(dest)
    (dest / "first.png").write_bytes(b"not a png")
    written = seed.seed_placeholder_inputs(dest)
    assert [path.name for path in written] == ["first.png"]
    assert seed.png_size(dest / "first.png") == (1280, 704)


def test_placeholder_is_idempotent(tmp_path: Path) -> None:
    dest = tmp_path / "input"
    assert len(seed.seed_placeholder_inputs(dest)) == len(seed.PLACEHOLDER_PLATES)
    assert seed.seed_placeholder_inputs(dest) == []


def test_placeholder_refuses_models_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    models = tmp_path / "models"
    models.mkdir()
    monkeypatch.setenv("MODELS_DIR", str(models))
    with pytest.raises(ValueError, match="MODELS_DIR"):
        seed.seed_placeholder_inputs(models / "blocked")


def test_seed_clay_inputs_seeds_placeholders_too(tmp_path: Path) -> None:
    dest = tmp_path / "input"
    written = seed.seed_clay_inputs(dest)
    assert [path.name for path in written] == [
        seed.clay_copy_name(index) for index in range(seed.CLAY_COUNT)
    ]
    for plate in seed.PLACEHOLDER_PLATES:
        assert seed.example_png_valid(dest / plate.name)


def test_placeholder_rgb_is_unique_per_plate() -> None:
    colors = [
        seed.placeholder_rgb(index) for index in range(len(seed.PLACEHOLDER_PLATES))
    ]
    assert len(set(colors)) == len(seed.PLACEHOLDER_PLATES)
    assert all(all(0 <= channel <= 255 for channel in color) for color in colors)


def test_placeholder_pixels_are_deterministic_and_distinct() -> None:
    width, height = 13, 9
    frames = [seed.placeholder_pixels(width, height, index) for index in range(8)]
    assert all(len(frame) == width * height * 3 for frame in frames)
    assert len(set(frames)) == len(frames)
    assert seed.placeholder_pixels(width, height, 3) == frames[3]
    stride = width * 3
    first_row = frames[0][0:stride]
    last_row = frames[0][(height - 1) * stride : height * stride]
    assert first_row != last_row
    band = {last_row[x * 3 : x * 3 + 3] for x in range(width)}
    assert len(band) > 1


def test_placeholder_table_matches_shipped_graphs() -> None:
    derived = _bare_load_image_defaults()
    already_seeded = {seed.EXAMPLE_NAME} | {
        seed.clay_copy_name(index) for index in range(seed.CLAY_COUNT)
    }
    table = {plate.name for plate in seed.PLACEHOLDER_PLATES}
    assert derived - already_seeded == table
    assert "cover.png" in table and "example.png" in derived


def test_main_reports_placeholder_plates(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    dest = tmp_path / "in"
    assert seed.main([str(dest)]) == 0
    out = capsys.readouterr().out
    assert f"{len(seed.PLACEHOLDER_PLATES)} placeholder plates in place" in out
    assert (dest / "cover.png").is_file()


def _bare_audio_defaults() -> set[str]:
    """Every bare audio filename a shipped lab graph defaults a loader to."""
    names: set[str] = set()
    for _lab_rel, _path, data in cached_lab_graph_rows():
        pending: list[object] = [data]
        while pending:
            node = pending.pop()
            if isinstance(node, dict):
                node_type = node.get("type")
                if isinstance(node_type, str) and node_type in _AUDIO_LOADERS:
                    widgets = node.get("widgets_values")
                    if isinstance(widgets, list) and widgets:
                        first = widgets[0]
                        if (
                            isinstance(first, str)
                            and first.lower().endswith(_AUDIO_SUFFIXES)
                            and "/" not in first
                            and "\\" not in first
                        ):
                            names.add(first)
                pending.extend(node.values())
            elif isinstance(node, list):
                pending.extend(node)
    return names


def test_audio_bed_is_written_once_and_is_a_real_wav(tmp_path: Path) -> None:
    dest = tmp_path / "input"
    written = seed.seed_audio_bed_input(dest)
    assert written is not None
    assert written.name == seed.AUDIO_BED_NAME == "ez_a2v_bed.wav"
    assert seed.wav_valid(written)
    with wave.open(str(written), "rb") as handle:
        assert handle.getnchannels() == 1
        assert handle.getsampwidth() == 2
        assert handle.getframerate() == seed.AUDIO_BED_RATE
        assert handle.getnframes() == seed.AUDIO_BED_RATE * seed.AUDIO_BED_SECONDS
    assert seed.seed_audio_bed_input(dest) is None


def test_audio_bed_is_audible_and_never_clips() -> None:
    frames = seed.audio_bed_frames(seed.AUDIO_BED_SECONDS, seed.AUDIO_BED_RATE)
    assert len(frames) == seed.AUDIO_BED_RATE * seed.AUDIO_BED_SECONDS * 2
    samples = struct.unpack(f"<{len(frames) // 2}h", frames)
    peak = max(abs(sample) for sample in samples)
    assert peak > 1000, "bed is inaudible"
    assert peak < 32767, "bed clips"
    # Ends fade out so a loop point does not click.
    assert abs(samples[-1]) < peak // 20


def test_audio_bed_keeps_the_operators_take(tmp_path: Path) -> None:
    dest = tmp_path / "input"
    dest.mkdir()
    keep = dest / seed.AUDIO_BED_NAME
    seed.write_pcm_wav(keep, b"\x00\x01\x02\x03" * 32, seed.AUDIO_BED_RATE)
    before = keep.read_bytes()
    assert seed.seed_audio_bed_input(dest) is None
    assert keep.read_bytes() == before


def test_audio_bed_replaces_a_corrupt_file(tmp_path: Path) -> None:
    dest = tmp_path / "input"
    dest.mkdir()
    junk = dest / seed.AUDIO_BED_NAME
    junk.write_bytes(b"not a wav")
    assert seed.wav_valid(junk) is False
    assert seed.seed_audio_bed_input(dest) is not None
    assert seed.wav_valid(junk)


def test_write_pcm_wav_rejects_an_odd_frame_count(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="16-bit"):
        seed.write_pcm_wav(tmp_path / "x.wav", b"\x00", seed.AUDIO_BED_RATE)


def test_audio_bed_refuses_models_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    models = tmp_path / "models"
    monkeypatch.setenv("MODELS_DIR", str(models))
    with pytest.raises(ValueError, match="refusing MODELS_DIR"):
        seed.seed_audio_bed_input(models / "input")


def test_main_seeds_the_audio_bed(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    dest = tmp_path / "in"
    assert seed.main([str(dest)]) == 0
    assert (dest / seed.AUDIO_BED_NAME).is_file()
    assert seed.AUDIO_BED_NAME in capsys.readouterr().out


def test_every_shipped_audio_default_is_seeded() -> None:
    """A graph may not default an audio loader at a file nothing writes."""
    assert _bare_audio_defaults() == seed.SEEDED_AUDIO_INPUTS
    assert seed.AUDIO_BED_NAME in seed.SEEDED_AUDIO_INPUTS


def _raw_wav(
    path: Path,
    *,
    sample_width: int = 2,
    channels: int = 1,
    rate: int = 48000,
    frames: int = 4800,
    fmt: int = 1,
) -> Path:
    """Write a RIFF/WAVE by hand so the test controls the format tag."""
    block_align = channels * sample_width
    data = bytes(frames * channels * sample_width)
    fmt_chunk = b"fmt " + struct.pack("<I", 16) + struct.pack(
        "<HHIIHH", fmt, channels, rate, rate * block_align, block_align, 8 * sample_width
    )
    data_chunk = b"data" + struct.pack("<I", len(data)) + data
    body = b"WAVE" + fmt_chunk + data_chunk
    path.write_bytes(b"RIFF" + struct.pack("<I", 4 + len(body)) + body)
    return path


@pytest.mark.parametrize(
    ("label", "kwargs"),
    [
        ("24-bit stereo DAW export", {"sample_width": 3, "channels": 2}),
        ("5.1 surround bed", {"sample_width": 2, "channels": 6}),
        ("32-bit float mixdown", {"sample_width": 4, "channels": 2, "fmt": 3}),
        ("mono 96 kHz master", {"sample_width": 2, "channels": 1, "rate": 96000}),
    ],
)
def test_audio_bed_keeps_every_real_wav_shape(
    tmp_path: Path, label: str, kwargs: dict[str, int]
) -> None:
    """A take the stdlib reader cannot judge is still the operator's file."""
    dest = tmp_path / "input"
    dest.mkdir()
    keep = _raw_wav(dest / seed.AUDIO_BED_NAME, **kwargs)
    before = keep.read_bytes()
    assert seed.seed_audio_bed_input(dest) is None, label
    assert keep.read_bytes() == before, label


def test_audio_bed_replaces_a_wav_with_no_frames(tmp_path: Path) -> None:
    """An empty data chunk is not a take, so the placeholder earns its place."""
    dest = tmp_path / "input"
    dest.mkdir()
    stub = _raw_wav(dest / seed.AUDIO_BED_NAME, frames=0)
    assert seed.wav_valid(stub) is False
    assert seed.seed_audio_bed_input(dest) is not None
    assert seed.wav_valid(stub)


def test_has_wave_magic_is_false_for_an_unreadable_path(tmp_path: Path) -> None:
    """A path that will not open has no header, so it is not a bed."""
    assert seed._has_wave_magic(tmp_path) is False  # noqa: SLF001 - a directory


def test_wav_valid_is_false_for_a_file_that_cannot_be_read(tmp_path: Path) -> None:
    """An unreadable bed is not evidence of audio; the seed takes its own."""
    dest = tmp_path / "input"
    dest.mkdir()
    bed = dest / seed.AUDIO_BED_NAME
    _raw_wav(bed)
    bed.chmod(0o000)
    try:
        assert seed.wav_valid(bed) is False
    finally:
        bed.chmod(0o644)


def test_main_reports_plates_when_only_the_bed_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A bed failure names the bed and keeps the plates' own line honest."""
    dest = tmp_path / "in"
    (dest / "input").mkdir(parents=True)

    def _boom(_path: str | Path) -> Path | None:
        raise IsADirectoryError("is a directory")

    monkeypatch.setattr(seed, "seed_audio_bed_input", _boom)
    assert seed.main([str(dest / "input")]) == 1
    captured = capsys.readouterr()
    assert "audio bed not seeded" in captured.err
    assert "plates ready" in captured.out
    assert seed.AUDIO_BED_NAME not in captured.out


def test_main_seeds_the_bed_when_a_plate_write_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A plate that will not write must not take the audio bed down with it."""
    dest = tmp_path / "in"

    def _boom(_path: str | Path) -> list[Path]:
        raise PermissionError(13, "Permission denied", str(dest / "cover.png"))

    monkeypatch.setattr(seed, "seed_clay_inputs", _boom)
    assert seed.main([str(dest)]) == 1
    assert (dest / seed.AUDIO_BED_NAME).is_file()
    assert (dest / seed.EXAMPLE_NAME).is_file()
    captured = capsys.readouterr()
    assert "failed: [Errno 13] Permission denied" in captured.err
    assert "cover.png" in captured.err
    # The plate stage never ran, so stdout must not claim plates it did not
    # write; the two stages that did run still say what they wrote.
    assert "plates ready" not in captured.out
    assert f"wrote {seed.AUDIO_BED_NAME}" in captured.out


def test_main_seeds_the_bed_when_the_example_plate_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The example plate is its own stage: it neither leads nor blocks the rest."""
    dest = tmp_path / "in"

    def _boom(_path: str | Path) -> Path | None:
        raise PermissionError(13, "Permission denied", str(dest / seed.EXAMPLE_NAME))

    monkeypatch.setattr(seed, "seed_example_input", _boom)
    assert seed.main([str(dest)]) == 1
    assert seed.clay_plate_valid(dest / seed.clay_copy_name(0))
    assert (dest / seed.PLACEHOLDER_PLATES[0].name).is_file()
    assert (dest / seed.AUDIO_BED_NAME).is_file()
    captured = capsys.readouterr()
    assert "failed: [Errno 13] Permission denied" in captured.err
    assert "10 plates ready" in captured.out
    assert f"wrote {seed.EXAMPLE_NAME}" not in captured.out


def test_main_keeps_every_plate_when_the_bed_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The mirror of the bed line: plates that landed are on disk, not just named."""
    dest = tmp_path / "in"

    def _boom(_path: str | Path) -> Path | None:
        raise PermissionError(13, "Permission denied", str(dest / seed.AUDIO_BED_NAME))

    monkeypatch.setattr(seed, "seed_audio_bed_input", _boom)
    assert seed.main([str(dest)]) == 1
    for index in range(seed.CLAY_COUNT):
        assert seed.clay_plate_valid(dest / seed.clay_copy_name(index))
    assert all((dest / plate.name).is_file() for plate in seed.PLACEHOLDER_PLATES)
    assert (dest / seed.EXAMPLE_NAME).is_file()
    assert not (dest / seed.AUDIO_BED_NAME).exists()
    captured = capsys.readouterr()
    assert "audio bed not seeded" in captured.err
    assert "10 plates ready" in captured.out
    assert f"wrote {seed.AUDIO_BED_NAME}" not in captured.out


def test_main_says_nothing_about_plates_when_every_stage_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A run where nothing landed prints no counts it did not earn."""
    dest = tmp_path / "in"

    def _plate_boom(_path: str | Path) -> list[Path]:
        raise PermissionError(13, "Permission denied", "cover.png")

    def _file_boom(_path: str | Path) -> Path | None:
        raise PermissionError(13, "Permission denied", "ez_example.png")

    monkeypatch.setattr(seed, "seed_clay_inputs", _plate_boom)
    monkeypatch.setattr(seed, "seed_example_input", _file_boom)
    monkeypatch.setattr(seed, "seed_audio_bed_input", _file_boom)

    assert seed.main([str(dest)]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.count("[seed-clay]") == 3


def test_a_bed_that_cannot_be_opened_fails_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The WAV writer reports its own OSError, not a garbage-collection traceback.

    ``wave.open`` handed a *path* builds a ``Wave_write`` whose ``_file`` is not
    set yet when the open is refused, so its ``__del__`` raises on the way out
    and Python prints "Exception ignored" beside the operator's own error line.
    Opening the file first keeps the refusal a plain OSError out of this module.
    """
    dest = tmp_path / "in"
    dest.mkdir()
    bed = dest / seed.AUDIO_BED_NAME
    bed.mkdir()  # something that can never be opened for writing
    seen: list[str] = []
    monkeypatch.setattr(
        sys, "unraisablehook", lambda report: seen.append(str(report.exc_value))
    )

    with pytest.raises(IsADirectoryError):
        seed.write_pcm_wav(bed, b"\0\0", 8000)

    assert seen == []


def test_main_still_refuses_a_models_dir_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    models = tmp_path / "models"
    models.mkdir()
    monkeypatch.setenv("MODELS_DIR", str(models))
    assert seed.main([str(models / "input")]) == 1
    assert "failed" in capsys.readouterr().err
