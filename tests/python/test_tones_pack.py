"""Hermetic tests for the tone pack exporter (ffmpeg is always faked)."""

from __future__ import annotations

import json
import runpy
import struct
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_tones import pack  # noqa: E402
from ez_tones.catalog import KIND_FOLDERS, TONE_CATALOG, ToneSpec, by_slug  # noqa: E402
from ez_tones.synth import PEAK_CEILING  # noqa: E402
from ez_tones.pack import (  # noqa: E402
    AAC_BITRATE,
    CHANGELOG_NAME,
    DOCS_COUNT,
    ENCODERS,
    GENERATED_BY,
    LISTING_NAME,
    LOUDNESS_LUFS,
    MANIFEST_NAME,
    PROGRESS_BAR_WIDTH,
    README_NAME,
    VORBIS_QUALITY,
    WAV_EXT,
    FfmpegError,
    PackResult,
    _bar,
    build_pack,
    changelog_text,
    encode_variant,
    ffmpeg_encode_argv,
    ffmpeg_wav_argv,
    loudnorm_filter,
    main,
    manifest_for,
    readme_text,
    render_wav,
    select_tones,
    store_listing_text,
    tone_bytes,
    tone_entry,
)

TWO_TONES = ("soft-triple-tap", "sine-chime")


class FakeFfmpeg:
    """Stand in for ffmpeg: record argv, fabricate the output file.

    Attributes:
        calls: One ``(argv, stdin_payload)`` pair per invocation.
        fail: Return a non-zero exit instead of writing.
        missing: Raise the way ``subprocess.run`` does with no ffmpeg.
    """

    def __init__(self, *, fail: bool = False, missing: bool = False) -> None:
        """Start with no recorded calls.

        Args:
            fail: Exit 1 with a stderr tail.
            missing: Raise FileNotFoundError instead of running.
        """
        self.calls: list[tuple[list[str], bytes | None]] = []
        self.fail = fail
        self.missing = missing

    def __call__(self, argv: list[str], payload: bytes | None) -> subprocess.CompletedProcess[bytes]:
        """Pretend to run one ffmpeg step.

        Args:
            argv: Command vector.
            payload: Bytes that would have gone to stdin.

        Returns:
            A completed process for the recorded call.

        Raises:
            FileNotFoundError: when constructed with ``missing``.
        """
        if self.missing:
            raise FileNotFoundError("ffmpeg")
        self.calls.append((argv, payload))
        if self.fail:
            return subprocess.CompletedProcess(argv, 1, b"", b"Invalid filter name 'loudnorm'")
        dest = Path(argv[-1])
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"stub-audio")
        return subprocess.CompletedProcess(argv, 0, b"", b"")


def _samples(slugs: tuple[str, ...]) -> tuple[ToneSpec, ...]:
    """Pick shipped rows by slug for a fast build.

    Args:
        slugs: Tones to keep.

    Returns:
        The rows, in catalog order.
    """
    rows = tuple(spec for spec in TONE_CATALOG if spec.slug in slugs)
    assert rows
    return rows


def test_loudnorm_filter_levels_each_kind_differently() -> None:
    """Alarms are the loudest, notifications the quietest, by LUFS target."""
    alarm = loudnorm_filter("alarm")
    ring = loudnorm_filter("ringtone")
    notice = loudnorm_filter("notification")
    assert LOUDNESS_LUFS["alarm"] > LOUDNESS_LUFS["ringtone"] > LOUDNESS_LUFS["notification"]
    assert "loudnorm=I=-14.0" in alarm
    assert "loudnorm=I=-19.0" in ring
    assert "loudnorm=I=-23.0" in notice
    for text in (alarm, ring, notice):
        assert "linear=true" in text
        assert "alimiter=limit=0.89" in text


def test_ffmpeg_wav_argv_reads_raw_float_from_stdin() -> None:
    """The master step takes interleaved f32 on stdin, writes 16-bit WAV."""
    argv = ffmpeg_wav_argv(Path("/tmp/a.wav"), 48000, 2, "alarm")
    assert argv[0] == "ffmpeg"
    assert argv[-1] == "/tmp/a.wav"
    assert argv[argv.index("-f") + 1] == pack.F32_FORMAT
    assert pack.F32_FORMAT in ("f32le", "f32be")
    assert argv[argv.index("-i") + 1] == "-"
    assert argv.count("-ar") == 2
    assert argv[argv.index("-ar") + 1] == "48000"
    assert argv.count("-ac") == 2
    ac_slots = [i for i, token in enumerate(argv) if token == "-ac"]
    assert argv[ac_slots[0] + 1] == "2"
    assert argv[ac_slots[1] + 1] == "2"
    assert argv[argv.index("-c:a") + 1] == "pcm_s16le"
    assert "+bitexact" in argv and "-1" in argv


def test_ffmpeg_encode_argv_picks_the_codec_flags() -> None:
    """AAC gets a bitrate, Vorbis gets a VBR quality."""
    aac = ffmpeg_encode_argv(Path("/tmp/a.wav"), Path("/tmp/a.m4a"), "aac", 44100)
    ogg = ffmpeg_encode_argv(Path("/tmp/a.wav"), Path("/tmp/a.ogg"), "vorbis", 44100)
    assert aac[aac.index("-c:a") + 1] == "aac"
    assert aac[aac.index("-b:a") + 1] == AAC_BITRATE
    assert aac[-1] == "/tmp/a.m4a"
    assert ogg[ogg.index("-c:a") + 1] == "libvorbis"
    assert ogg[ogg.index("-q:a") + 1] == VORBIS_QUALITY
    assert ogg[-1] == "/tmp/a.ogg"


def test_tone_bytes_is_float32_and_channel_wide() -> None:
    """Raw frames are four bytes a sample, doubled for stereo."""
    stereo = by_slug("marimba-grove")
    assert stereo is not None
    mono = replace(stereo, channels=1)
    raw = tone_bytes(mono, 44100)
    wide = tone_bytes(stereo, 44100)
    assert len(raw) % 4 == 0
    assert len(wide) == 2 * len(raw)
    assert tone_bytes(mono, 44100) == raw


def test_run_accepts_a_clean_step(tmp_path: Path) -> None:
    """A zero exit is the only thing a build needs."""
    runner = FakeFfmpeg()
    dest = tmp_path / "step.wav"
    pack._run(["ffmpeg", str(dest)], b"pcm", runner)
    assert runner.calls == [(["ffmpeg", str(dest)], b"pcm")]


def test_run_reports_a_missing_ffmpeg() -> None:
    """No ffmpeg on PATH is a stated problem, not a traceback."""
    with pytest.raises(FfmpegError, match="ffmpeg is not installed"):
        pack._run(["ffmpeg"], None, FakeFfmpeg(missing=True))


def test_run_reports_a_failed_encode() -> None:
    """ffmpeg's own words come back in the error."""
    with pytest.raises(FfmpegError, match="Invalid filter name"):
        pack._run(["ffmpeg"], None, FakeFfmpeg(fail=True))


def test_frames_are_fed_quiet_enough_for_the_loudness_pass() -> None:
    """ffmpeg gets headroom, so loudnorm can hit the LUFS target."""
    spec = by_slug("marimba-grove")
    assert spec is not None
    raw = tone_bytes(spec, 44100)
    peak = max(abs(struct.unpack_from("<f", raw, offset)[0]) for offset in range(0, len(raw), 4))
    assert peak == pytest.approx(pack.FEED_CEILING, rel=1e-6)
    assert pack.FEED_CEILING < PEAK_CEILING


def test_spawn_runs_a_real_command() -> None:
    """The production adapter is a plain captured subprocess call."""
    proc = pack._spawn([sys.executable, "-c", "pass"], b"")
    assert proc.returncode == 0
    assert proc.stdout == b""


def test_render_wav_feeds_the_synthesised_frames() -> None:
    """One tone becomes one master, fed to ffmpeg on stdin."""
    runner = FakeFfmpeg()
    spec = by_slug("glass-two-note")
    assert spec is not None
    dest = Path("/tmp/whatever/glass-two-note.wav")
    written = render_wav(spec, dest, 44100, runner)
    assert written == dest
    argv, payload = runner.calls[0]
    assert argv[-1] == str(dest)
    assert payload is not None and len(payload) % 4 == 0


def test_encode_variant_transcodes_the_master() -> None:
    """The sibling step reads the master and never needs stdin."""
    runner = FakeFfmpeg()
    dest = encode_variant(Path("/tmp/a.wav"), Path("/tmp/a.ogg"), "vorbis", 44100, runner)
    assert dest == Path("/tmp/a.ogg")
    assert runner.calls[0][1] is None


def test_select_tones_filters_by_kind_and_slug() -> None:
    """Kind and slug filters compose, and an unknown slug is named."""
    assert select_tones(TONE_CATALOG) == TONE_CATALOG
    alarms = select_tones(TONE_CATALOG, kinds=("alarm",))
    assert alarms and all(spec.kind == "alarm" for spec in alarms)
    picked = select_tones(TONE_CATALOG, kinds=("notification",), only_slugs=TWO_TONES)
    assert tuple(spec.slug for spec in picked) == TWO_TONES
    with pytest.raises(ValueError, match="unknown tone slug"):
        select_tones(TONE_CATALOG, only_slugs=("not-a-tone",))


def test_bar_fills_clamps_and_matches_its_width() -> None:
    """The progress bar is always the same length."""
    assert _bar(0.0) == "." * PROGRESS_BAR_WIDTH
    assert _bar(1.0) == "#" * PROGRESS_BAR_WIDTH
    assert _bar(2.0) == _bar(1.0)
    assert _bar(-1.0) == _bar(0.0)
    assert len(_bar(0.5)) == PROGRESS_BAR_WIDTH


def test_tone_entry_describes_the_tone() -> None:
    """A manifest row carries everything a store needs per file."""
    spec = by_slug("woody-knock")
    assert spec is not None
    row = tone_entry(spec, 48000, {"wav": "notifications/woody-knock.wav"})
    assert row["slug"] == "woody-knock"
    assert row["kind"] == "notification"
    assert row["channels"] == 1
    assert row["sample_rate"] == 48000
    assert row["loopable"] is True
    assert row["loudness_lufs"] == LOUDNESS_LUFS["notification"]
    assert row["tags"] == list(spec.tags)
    assert row["files"] == {"wav": "notifications/woody-knock.wav"}
    assert row["steps"] == len(spec.motif)


def test_manifest_for_counts_the_whole_pack() -> None:
    """The manifest totals match what a build writes."""
    body = manifest_for("Pack", "2.1.0", 44100, [])
    assert body["pack_name"] == "Pack"
    assert body["version"] == "2.1.0"
    assert body["generated_by"] == GENERATED_BY
    assert body["tone_count"] == 0
    assert body["file_count"] == DOCS_COUNT
    assert body["tones"] == []
    assert GENERATED_BY.isascii() and "20" not in GENERATED_BY


def test_store_listing_carries_the_play_sections() -> None:
    """Title, descriptions, category, keywords, and data safety are there."""
    rows = _samples(TWO_TONES)
    text = store_listing_text("Spark Tones", "1.0.0", rows)
    for heading in ("## Title", "## Short description", "## Full description", "## Category", "## Keywords", "## Data safety"):
        assert heading in text
    assert "collects nothing" in text
    assert "no network access" in text
    assert text.isascii()
    assert "soft-triple-tap" not in text


def test_readme_shows_an_operator_how_to_add_a_tone() -> None:
    """The pack explains the JSON route, not a code change."""
    text = readme_text("Spark Tones", "1.0.0")
    assert "Add a tone" in text
    assert "--catalog" in text
    assert "--template" in text
    assert text.isascii()


def test_chelog_lists_the_release() -> None:
    """The changelog names the version and the tones in it."""
    text = changelog_text("Spark Tones", "1.2.3", _samples(TWO_TONES))
    assert "## 1.2.3" in text
    assert "soft-triple-tap" in text
    assert text.isascii()


def test_build_pack_dry_run_writes_nothing(tmp_path: Path) -> None:
    """A dry run plans the full file list and touches no disk."""
    out = tmp_path / "pack"
    lines: list[str] = []
    result = build_pack(
        _samples(TWO_TONES),
        out,
        only_slugs=TWO_TONES,
        runner=FakeFfmpeg(),
        dry_run=True,
        report=lines.append,
    )
    assert not out.exists()
    assert result.dry_run is True
    assert result.tone_count == 2
    assert result.file_count == 2 * (len(ENCODERS) + 1) + DOCS_COUNT
    assert result.manifest_path == out / MANIFEST_NAME
    assert any("dry-run" in line for line in lines)
    assert any("notification" in line for line in lines)


def test_build_pack_writes_the_whole_pack(tmp_path: Path) -> None:
    """Every tone lands as WAV, M4A, and OGG next to the docs."""
    out = tmp_path / "pack"
    lines: list[str] = []
    result = build_pack(
        _samples(TWO_TONES),
        out,
        pack_name="Test Tones",
        runner=FakeFfmpeg(),
        report=lines.append,
    )
    assert isinstance(result, PackResult)
    assert result.dry_run is False
    assert all(path.is_file() for path in result.files)
    assert len(result.files) == result.file_count
    folder = out / KIND_FOLDERS["notification"]
    assert (folder / f"soft-triple-tap{WAV_EXT}").is_file()
    assert (folder / "soft-triple-tap.m4a").is_file()
    assert (folder / "soft-triple-tap.ogg").is_file()
    assert (out / LISTING_NAME).is_file() and (out / README_NAME).is_file()
    assert (out / CHANGELOG_NAME).is_file()
    body = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert body["pack_name"] == "Test Tones"
    assert body["tone_count"] == 2
    assert body["file_count"] == result.file_count
    slugs = [row["slug"] for row in body["tones"]]
    assert slugs == list(TWO_TONES)
    assert body["tones"][0]["files"]["wav"] == "notifications/soft-triple-tap.wav"
    assert any(line.startswith("wrote ") for line in lines)


def test_build_pack_is_byte_reproducible(tmp_path: Path) -> None:
    """Two builds of one catalog are identical, so diffs mean changes."""
    first = tmp_path / "a"
    second = tmp_path / "b"
    build_pack(_samples(("glass-two-note",)), first, runner=FakeFfmpeg(), report=lambda _t: None)
    build_pack(_samples(("glass-two-note",)), second, runner=FakeFfmpeg(), report=lambda _t: None)
    left = sorted(path.relative_to(first).as_posix() for path in first.rglob("*") if path.is_file())
    right = sorted(path.relative_to(second).as_posix() for path in second.rglob("*") if path.is_file())
    assert left == right
    for name in left:
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_build_pack_falls_back_to_the_real_runner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """With no runner injected the build uses the production adapter."""
    fake = FakeFfmpeg()
    monkeypatch.setattr(pack, "_spawn", fake)
    result = build_pack(_samples(("sine-chime",)), tmp_path / "p", report=lambda _t: None)
    assert fake.calls
    assert result.tone_count == 1


def test_build_pack_surfaces_an_ffmpeg_failure(tmp_path: Path) -> None:
    """A refused encode stops the build instead of shipping a silent pack."""
    with pytest.raises(FfmpegError, match="ffmpeg exited 1"):
        build_pack(
            _samples(TWO_TONES),
            tmp_path / "p",
            runner=FakeFfmpeg(fail=True),
            report=lambda _t: None,
        )


def test_main_dry_run_prints_the_plan(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The CLI plans without writing when told to."""
    out = tmp_path / "cli"
    code = main(["--out", str(out), "--kind", "notification", "--tone", "sine-chime", "--dry-run"])
    assert code == 0
    assert not out.exists()
    printed = capsys.readouterr().out
    assert "dry-run" in printed
    assert "sine-chime" in printed


def test_main_writes_a_pack(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The CLI verb renders a pack end to end."""
    monkeypatch.setattr(pack, "_spawn", FakeFfmpeg())
    out = tmp_path / "cli"
    code = main(
        [
            "--out",
            str(out),
            "--tone",
            "soft-triple-tap",
            "--sample-rate",
            "48000",
            "--pack-name",
            "CLI Tones",
            "--version",
            "3.0.0",
        ]
    )
    assert code == 0
    body = json.loads((out / MANIFEST_NAME).read_text(encoding="utf-8"))
    assert body["pack_name"] == "CLI Tones"
    assert body["version"] == "3.0.0"
    assert body["sample_rate"] == 48000
    assert "wrote" in capsys.readouterr().out


def test_main_merges_an_operator_catalog(tmp_path: Path) -> None:
    """An operator file reaches the build through --catalog."""
    catalog = tmp_path / "catalog.json"
    catalog.write_text(
        json.dumps({"tones": []}),
        encoding="utf-8",
    )
    assert main(["--catalog", str(catalog), "--tone", "sine-chime", "--dry-run"]) == 0


def test_main_writes_the_template(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """The --template flag hands an operator a file to edit."""
    target = tmp_path / "nested" / "tones.json"
    assert main(["--template", str(target)]) == 0
    assert target.is_file()
    assert "catalog template" in capsys.readouterr().out


def test_main_reports_a_bad_catalog(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A missing operator file is a one-line error and exit 1."""
    assert main(["--catalog", str(tmp_path / "gone.json")]) == 1
    assert "catalog file not found" in capsys.readouterr().err


def test_main_reports_an_unknown_tone(capsys: pytest.CaptureFixture[str]) -> None:
    """A typo in --tone is reported, not ignored."""
    assert main(["--tone", "nope", "--dry-run"]) == 1
    assert "unknown tone slug" in capsys.readouterr().err


def test_main_reports_an_ffmpeg_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A refused encode exits 1 with ffmpeg's reason."""
    monkeypatch.setattr(pack, "_spawn", FakeFfmpeg(fail=True))
    assert main(["--out", str(tmp_path / "p"), "--tone", "sine-chime"]) == 1
    assert "ffmpeg exited 1" in capsys.readouterr().err


def test_main_rejects_choices_it_does_not_know() -> None:
    """Argparse guards the kind and sample-rate domains."""
    with pytest.raises(SystemExit):
        main(["--kind", "siren"])
    with pytest.raises(SystemExit):
        main(["--sample-rate", "22050"])


def test_running_the_module_as_a_script_exits_cleanly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The package entry point the operator CLI calls really works."""
    monkeypatch.setattr(sys, "argv", ["ez_tones.pack", "--out", str(tmp_path / "m"), "--dry-run"])
    monkeypatch.delitem(sys.modules, "ez_tones.pack", raising=False)
    with pytest.raises(SystemExit) as caught:
        runpy.run_module("ez_tones.pack", run_name="__main__", alter_sys=True)
    assert caught.value.code == 0


def test_exported_constants_match_the_android_reality() -> None:
    """The numbers the module documents are the numbers it uses."""
    assert ENCODERS == (("aac", ".m4a"), ("vorbis", ".ogg"))
    assert WAV_EXT == ".wav"
    assert MANIFEST_NAME == "manifest.json"
    assert {spec.kind for spec in _samples(TWO_TONES)} == {"notification"}
    assert DOCS_COUNT == 4
