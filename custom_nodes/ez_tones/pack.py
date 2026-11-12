"""Render the catalog and package it as a sellable Android tone pack.

One build writes, per tone: a 16-bit WAV master, an AAC ``.m4a``, and a
Vorbis ``.ogg``, grouped into Android's ``ringtones/``,
``notifications/``, and ``alarms/`` folders, plus ``manifest.json`` and
the Play Store listing artefacts (``store-listing.md``,
``CHANGELOG.md``, ``README.md``).

Audio leaves Python as raw native float32 on ffmpeg's stdin; ffmpeg does
the loudness and peak shaping with ``loudnorm`` plus ``alimiter`` against
the constants below, so every tone in a pack arrives at the same level
without ever clipping. The build is deterministic: no clock, no RNG, no
metadata that changes between runs, so two builds of one catalog are
byte-identical.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from array import array
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeAlias

from ez_common.json_value import Json, JsonObject

from .catalog import (
    KIND_FOLDERS,
    KINDS,
    TONE_CATALOG,
    ToneKind,
    ToneSpec,
    by_slug,
    load_catalog,
    write_catalog_template,
)
from .synth import DEFAULT_SAMPLE_RATE, interleave, normalise, render_motif

Codec: TypeAlias = Literal["aac", "vorbis"]
"""Sibling codecs Android ships tones in."""

F32_FORMAT = "f32le" if sys.byteorder == "little" else "f32be"
"""ffmpeg raw-float input name matching this host's native ``array("f")`` bytes."""

RunnerFn: TypeAlias = Callable[[list[str], bytes | None], subprocess.CompletedProcess[bytes]]
"""``subprocess.run`` adapter for one ffmpeg step (tests inject a double)."""

DEFAULT_PACK_NAME = "Spark Tones"
"""Pack name stamped on the manifest and the listing."""

DEFAULT_VERSION = "1.0.0"
"""Version an operator bumps when they add tones."""

DEFAULT_OUT_DIR = Path("out/tone-pack")
"""Default export directory under the working tree."""

MANIFEST_NAME = "manifest.json"
"""Machine-readable pack description Play tooling reads."""

LISTING_NAME = "store-listing.md"
"""Play Store listing draft."""

README_NAME = "README.md"
"""Operator note that ships inside the exported pack."""

CHANGELOG_NAME = "CHANGELOG.md"
"""Release note that ships inside the exported pack."""

WAV_EXT = ".wav"
"""Master container."""

ENCODERS: tuple[tuple[Codec, str], ...] = (("aac", ".m4a"), ("vorbis", ".ogg"))
"""Sibling encoding steps run for every tone, with their extensions."""

LOUDNESS_LUFS: dict[ToneKind, float] = {
    "notification": -23.0,
    "ringtone": -19.0,
    "alarm": -14.0,
}
"""Integrated-loudness target per kind, LUFS.

Notifications sit lowest because they loop behind a screen and must not
startle; alarms sit loudest because the point of an alarm is to wake
someone up.
"""

LOUDNORM_LRA = 11
"""Loudness-range value handed to ffmpeg ``loudnorm``."""

TRUE_PEAK_DBTP = -1.5
"""True-peak ceiling ``loudnorm`` aims for, dBTP (Play guidance)."""

LIMITER_CEILING = 0.89
"""``alimiter`` peak ceiling, linear, applied after loudnorm as a hard stop."""

FEED_CEILING = 0.2
"""Peak the synthesised frame is scaled to before ffmpeg sees it, linear.

loudnorm is run in linear mode, so it can only raise gain as far as the
true-peak target allows. Handing it a frame already peaking at full scale
means a percussive tone can never reach its LUFS target, so the frame is
fed in about 14 dB quiet and loudnorm owns the final level.
"""

AAC_BITRATE = "160k"
"""AAC bitrate for ``.m4a`` ringtones."""

VORBIS_QUALITY = "5"
"""libvorbis VBR quality for ``.ogg`` notification sounds."""

PROGRESS_BAR_WIDTH = 24
"""Cells in the progress bar the build prints per tone."""

GENERATED_BY = "ez-comfy-stack ez_tones"
"""Producer string stamped on the manifest; date-free on purpose, so two
builds of one catalog are byte-identical."""

DOCS_COUNT = 4
"""Non-audio files a build writes: manifest, listing, README, changelog."""

TAG_LIST_MAX = 24
"""Keywords the store listing is allowed to carry."""


class FfmpegError(RuntimeError):
    """ffmpeg was missing or refused to encode."""


def loudnorm_filter(kind: ToneKind) -> str:
    """ffmpeg audio filter chain that levels one kind.

    Args:
        kind: Tone role whose loudness target applies.

    Returns:
        A ``-af`` filter string: loudnorm to the kind's LUFS target, then a
        peak limiter at :data:`LIMITER_CEILING`.
    """
    target = LOUDNESS_LUFS[kind]
    return (
        f"loudnorm=I={target}:LRA={LOUDNORM_LRA}:TP={TRUE_PEAK_DBTP}:linear=true,"
        f"alimiter=limit={LIMITER_CEILING}:level=false"
    )


def ffmpeg_wav_argv(
    dest: Path,
    sample_rate: int,
    channels: int,
    kind: ToneKind,
) -> list[str]:
    """ffmpeg command that turns raw float32 stdin into a WAV master.

    The frame on stdin is already interleaved at ``channels``, so the input
    and output channel counts match and nothing is upmixed here.

    Args:
        dest: WAV path to write.
        sample_rate: Rate the raw samples are stamped at.
        channels: 1 or 2.
        kind: Tone role whose loudness chain applies.

    Returns:
        Argument vector; feed PCM to its stdin.
    """
    return [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        F32_FORMAT,
        "-ar",
        str(sample_rate),
        "-ac",
        str(channels),
        "-i",
        "-",
        "-ar",
        str(sample_rate),
        "-ac",
        str(channels),
        "-af",
        loudnorm_filter(kind),
        "-c:a",
        "pcm_s16le",
        "-map_metadata",
        "-1",
        "-fflags",
        "+bitexact",
        str(dest),
    ]


def ffmpeg_encode_argv(
    src: Path,
    dest: Path,
    codec: Codec,
    sample_rate: int,
) -> list[str]:
    """ffmpeg command that transcodes a WAV master to a sibling format.

    Args:
        src: WAV master to read.
        dest: ``.m4a`` or ``.ogg`` path to write.
        codec: Target codec.
        sample_rate: Rate to keep.

    Returns:
        Argument vector.
    """
    argv = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(src),
        "-ar",
        str(sample_rate),
        "-map_metadata",
        "-1",
        "-fflags",
        "+bitexact",
    ]
    if codec == "aac":
        argv += ["-c:a", "aac", "-b:a", AAC_BITRATE]
    else:
        argv += ["-c:a", "libvorbis", "-q:a", VORBIS_QUALITY]
    argv.append(str(dest))
    return argv


def _spawn(argv: list[str], payload: bytes | None) -> subprocess.CompletedProcess[bytes]:
    """Run one ffmpeg step, feeding ``payload`` on stdin.

    Args:
        argv: Command vector.
        payload: Raw bytes for stdin, or ``None``.

    Returns:
        Completed process with captured bytes.
    """
    return subprocess.run(argv, input=payload, capture_output=True, check=False)


def _run(argv: list[str], payload: bytes | None, runner: RunnerFn) -> None:
    """Run one ffmpeg step and fail loudly when it does not.

    Args:
        argv: Command vector.
        payload: Raw bytes for stdin, or ``None``.
        runner: Process runner seam.

    Raises:
        FfmpegError: ffmpeg is missing, or exited non-zero.
    """
    try:
        proc = runner(argv, payload)
    except FileNotFoundError as exc:
        raise FfmpegError("ffmpeg is not installed; install it and run the build again") from exc
    if proc.returncode != 0:
        detail = proc.stderr.decode("utf-8", "replace").strip()
        raise FfmpegError(f"ffmpeg exited {proc.returncode}: {detail[-300:]}")


def tone_bytes(spec: ToneSpec, sample_rate: int) -> bytes:
    """Render one tone to interleaved native float32 bytes.

    Args:
        spec: Tone to synthesise.
        sample_rate: Rate to render at.

    Returns:
        Raw PCM ready for ffmpeg's stdin, about 14 dB under full scale so
        :func:`loudnorm_filter` has room to raise the gain.
    """
    mono = normalise(render_motif(spec.motif, spec.timbre, sample_rate), FEED_CEILING)
    return array("f", interleave(mono, spec.channels, sample_rate)).tobytes()


def render_wav(
    spec: ToneSpec,
    dest: Path,
    sample_rate: int,
    runner: RunnerFn,
) -> Path:
    """Render one tone into a levelled WAV master.

    Args:
        spec: Tone to synthesise.
        dest: WAV path to write (parents are created).
        sample_rate: Rate to render at.
        runner: Process runner seam.

    Returns:
        The WAV path written.

    Raises:
        FfmpegError: ffmpeg refused the encode.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    _run(ffmpeg_wav_argv(dest, sample_rate, spec.channels, spec.kind), tone_bytes(spec, sample_rate), runner)
    return dest


def encode_variant(
    src: Path,
    dest: Path,
    codec: Codec,
    sample_rate: int,
    runner: RunnerFn,
) -> Path:
    """Transcode a WAV master into one sibling format.

    Args:
        src: WAV master.
        dest: Destination path.
        codec: Target codec.
        sample_rate: Rate to keep.
        runner: Process runner seam.

    Returns:
        The path written.

    Raises:
        FfmpegError: ffmpeg refused the encode.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    _run(ffmpeg_encode_argv(src, dest, codec, sample_rate), None, runner)
    return dest


def select_tones(
    catalog: Sequence[ToneSpec] = TONE_CATALOG,
    kinds: Sequence[ToneKind] = (),
    only_slugs: Sequence[str] = (),
) -> tuple[ToneSpec, ...]:
    """Pick the rows a build should render.

    Args:
        catalog: Rows to choose from.
        kinds: Kinds to keep; empty keeps every kind.
        only_slugs: Slugs to keep; empty keeps every picked row.

    Returns:
        Selected rows in catalog order.

    Raises:
        ValueError: a named slug is not in ``catalog``.
    """
    wanted = tuple(kinds) or KINDS
    rows = tuple(spec for spec in catalog if spec.kind in wanted)
    if not only_slugs:
        return rows
    missing = [slug for slug in only_slugs if by_slug(slug, catalog) is None]
    if missing:
        raise ValueError(f"unknown tone slug(s): {', '.join(missing)}")
    keep = set(only_slugs)
    return tuple(spec for spec in rows if spec.slug in keep)


def _bar(fraction: float) -> str:
    """Render a fixed-width text progress bar.

    Args:
        fraction: Completion between 0 and 1.

    Returns:
        ``PROGRESS_BAR_WIDTH`` cells of ``#`` and ``.``.
    """
    filled = round(min(max(fraction, 0.0), 1.0) * PROGRESS_BAR_WIDTH)
    return "#" * filled + "." * (PROGRESS_BAR_WIDTH - filled)


def manifest_for(
    pack_name: str,
    version: str,
    sample_rate: int,
    entries: list[Json],
) -> JsonObject:
    """Build the ``manifest.json`` body.

    Args:
        pack_name: Pack name.
        version: Pack version.
        sample_rate: Rate every file was rendered at.
        entries: Per-tone rows from :func:`tone_entry`.

    Returns:
        JSON object ready for ``json.dumps``.
    """
    body: JsonObject = {
        "pack_name": pack_name,
        "version": version,
        "generated_by": GENERATED_BY,
        "sample_rate": sample_rate,
        "tone_count": len(entries),
        "file_count": len(entries) * (len(ENCODERS) + 1) + DOCS_COUNT,
        "tones": entries,
    }
    return body


def tone_entry(
    spec: ToneSpec,
    sample_rate: int,
    files: dict[str, Json],
) -> JsonObject:
    """Build one manifest row for a tone.

    Args:
        spec: Tone the row describes.
        sample_rate: Rate the files carry.
        files: Codec to pack-relative path, from the build loop.

    Returns:
        JSON object for ``manifest.json``.
    """
    tags: list[Json] = [str(tag) for tag in spec.tags]
    row: JsonObject = {
        "slug": spec.slug,
        "name": spec.name,
        "kind": spec.kind,
        "category": spec.category,
        "mood": spec.mood,
        "timbre": spec.timbre,
        "bpm": spec.bpm,
        "tags": tags,
        "duration_s": spec.duration_s,
        "sample_rate": sample_rate,
        "channels": spec.channels,
        "loopable": spec.loopable,
        "loudness_lufs": LOUDNESS_LUFS[spec.kind],
        "steps": len(spec.motif),
        "files": files,
    }
    return row


def store_listing_text(pack_name: str, version: str, tones: Sequence[ToneSpec]) -> str:
    """Draft the Play Store listing the pack ships with.

    Args:
        pack_name: Pack name.
        version: Pack version.
        tones: Rows the pack contains.

    Returns:
        Markdown listing text.
    """
    counts = {kind: sum(1 for spec in tones if spec.kind == kind) for kind in KINDS}
    keywords = sorted({tag for spec in tones for tag in spec.tags})[:TAG_LIST_MAX]
    cats = ", ".join(sorted({spec.category for spec in tones}))
    lines = [
        f"# {pack_name} {version}",
        "",
        "## Title",
        "",
        f"{pack_name} - Ringtones, Notifications & Alarms",
        "",
        "## Short description",
        "",
        "Clean generated tones: ringtones, notification sounds, and alarms.",
        "",
        "## Full description",
        "",
        f"{pack_name} is a pack of {len(tones)} original tones, written and",
        "synthesised in-house - no samples, no licensed recordings, no loops",
        "lifted from elsewhere.",
        "",
        f"- {counts['ringtone']} ringtones up to 30 s, mono or stereo",
        f"- {counts['notification']} short notification chimes, cut to loop cleanly",
        f"- {counts['alarm']} alarm beds, levelled louder than the rest",
        "- Every file ships as WAV, M4A (AAC), and OGG (Vorbis)",
        "- Loudness matched per kind, peak limited so nothing clips",
        "",
        "Tones are generated from a catalog, so the pack is identical on every",
        "device and every install. Drop a new row into the catalog JSON and the",
        "next build carries it.",
        "",
        "## Category",
        "",
        f"Music & Audio (tones: {cats})",
        "",
        "## Keywords",
        "",
        ", ".join(keywords),
        "",
        "## Data safety",
        "",
        "This app collects nothing. There is no account, no analytics, no ads,",
        "no advertising identifiers, and no network access at all: the tones are",
        "bundled assets and the only thing the app does is let you set one as a",
        "ringtone, a notification sound, or an alarm. No data leaves the device,",
        "and nothing is encrypted or shared because nothing is collected.",
        "",
    ]
    return "\n".join(lines)


def readme_text(pack_name: str, version: str) -> str:
    """Write the operator README that ships inside the pack.

    Args:
        pack_name: Pack name.
        version: Pack version.

    Returns:
        Markdown text explaining how to add a tone.
    """
    lines = [
        f"# {pack_name} {version}",
        "",
        "Exported tone pack: WAV masters plus M4A (AAC) and OGG (Vorbis)",
        "siblings, grouped into ``ringtones/``, ``notifications/``, and",
        "``alarms/``, with ``manifest.json`` and ``store-listing.md``.",
        "",
        "## Add a tone",
        "",
        "1. Ask for the catalog template (the export verb takes a",
        "   ``--template`` path) and open the JSON it writes.",
        "2. Add one object to ``tones``. ``pitches`` is the easy form: a list",
        "   of MIDI notes, ``null`` for a rest, played at ``bpm``. Use",
        "   ``motif`` when you need exact step lengths.",
        "3. Re-run the tone export verb with ``--catalog`` pointing at that",
        "   file. A row whose ``slug`` matches a shipped tone replaces it.",
        "",
        "Notifications must land between 2 and 5 seconds, ringtones between 3",
        "and 30, alarms between 4 and 30; a row outside its budget fails the",
        "build with the slug in the message.",
        "",
        "## Rebuild",
        "",
        "Rebuilding the same catalog produces byte-identical files, so a diff",
        "of two builds is always a real change.",
        "",
    ]
    return "\n".join(lines)


def changelog_text(pack_name: str, version: str, tones: Sequence[ToneSpec]) -> str:
    """Write the release note that ships inside the pack.

    Args:
        pack_name: Pack name.
        version: Pack version.
        tones: Rows the pack contains.

    Returns:
        Markdown text.
    """
    lines = [
        f"# {pack_name} changelog",
        "",
        f"## {version}",
        "",
        f"- {len(tones)} tones rendered at the pack sample rate.",
        "- Each tone exported as WAV, M4A (AAC), and OGG (Vorbis).",
        "- Loudness matched per kind and peak limited.",
        "- Manifest, store listing, and this note written alongside.",
        "",
        "Tones in this release: " + ", ".join(spec.slug for spec in tones),
        "",
    ]
    return "\n".join(lines)


@dataclass(frozen=True)
class PackResult:
    """What one build planned or wrote.

    Attributes:
        out_dir: Directory the pack landed in.
        pack_name: Name stamped on the manifest and listing.
        version: Version stamped on the manifest.
        sample_rate: Rate every file was rendered at.
        tones: Rows that were built.
        files: Every file written, or planned for a dry run.
        manifest_path: Path of ``manifest.json``.
        tone_count: Number of tones built.
        file_count: Number of files written or planned.
        dry_run: True when nothing touched the disk.
    """

    out_dir: Path
    pack_name: str
    version: str
    sample_rate: int
    tones: tuple[ToneSpec, ...]
    files: tuple[Path, ...]
    manifest_path: Path
    tone_count: int
    file_count: int
    dry_run: bool


def build_pack(
    catalog: Sequence[ToneSpec] = TONE_CATALOG,
    out_dir: Path | str = DEFAULT_OUT_DIR,
    *,
    kinds: Sequence[ToneKind] = (),
    only_slugs: Sequence[str] = (),
    pack_name: str = DEFAULT_PACK_NAME,
    version: str = DEFAULT_VERSION,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    runner: RunnerFn | None = None,
    dry_run: bool = False,
    report: Callable[[str], None] = print,
) -> PackResult:
    """Render every selected tone and write the whole pack.

    Args:
        catalog: Rows to build.
        out_dir: Pack directory (created when needed).
        kinds: Kinds to build; empty builds every kind.
        only_slugs: Slugs to build; empty builds every selected row.
        pack_name: Name stamped on the manifest and listing.
        version: Version stamped on the manifest.
        sample_rate: Rate to render at.
        runner: ffmpeg runner seam; ``None`` uses the real one.
        dry_run: Print the plan and write nothing.
        report: Progress line sink.

    Returns:
        A :class:`PackResult` listing what was written (or planned).

    Raises:
        ValueError: a named slug is unknown.
        FfmpegError: ffmpeg is missing or refused an encode.
    """
    rows = select_tones(catalog, kinds, only_slugs)
    active: RunnerFn = runner if runner is not None else _spawn
    root = Path(out_dir)
    files: list[Path] = []
    entries: list[Json] = []
    total = len(rows)
    for index, spec in enumerate(rows, start=1):
        folder = root / KIND_FOLDERS[spec.kind]
        wav = folder / f"{spec.slug}{WAV_EXT}"
        paths: dict[str, Json] = {"wav": _rel(wav, root)}
        files.append(wav)
        if not dry_run:
            render_wav(spec, wav, sample_rate, active)
        for codec, ext in ENCODERS:
            dest = folder / f"{spec.slug}{ext}"
            files.append(dest)
            if not dry_run:
                encode_variant(wav, dest, codec, sample_rate, active)
            paths[codec] = _rel(dest, root)
        entries.append(tone_entry(spec, sample_rate, paths))
        report(
            f"[{_bar(index / total)}] {index}/{total} {spec.kind} "
            f"{spec.slug} ({spec.duration_s}s)"
        )
    writable: list[tuple[Path, str]] = [
        (
            root / MANIFEST_NAME,
            json.dumps(
                manifest_for(pack_name, version, sample_rate, entries),
                indent=2,
                sort_keys=True,
            )
            + "\n",
        ),
        (root / LISTING_NAME, store_listing_text(pack_name, version, rows)),
        (root / README_NAME, readme_text(pack_name, version)),
        (root / CHANGELOG_NAME, changelog_text(pack_name, version, rows)),
    ]
    for path, text in writable:
        files.append(path)
    if dry_run:
        report(f"dry-run: {len(files)} files planned under {root}, nothing written")
        return _result(root, pack_name, version, sample_rate, rows, files, dry_run=True)
    root.mkdir(parents=True, exist_ok=True)
    for path, text in writable:
        path.write_text(text, encoding="utf-8")
    report(f"wrote {len(rows)} tones and {len(files)} pack files to {root}")
    return _result(root, pack_name, version, sample_rate, rows, files, dry_run=False)


def _result(
    root: Path,
    pack_name: str,
    version: str,
    sample_rate: int,
    rows: Sequence[ToneSpec],
    files: Sequence[Path],
    *,
    dry_run: bool,
) -> PackResult:
    """Assemble the pack result a build returns.

    Args:
        root: Pack directory.
        pack_name: Name stamped on the manifest.
        version: Version stamped on the manifest.
        sample_rate: Rate every file was rendered at.
        rows: Rows built.
        files: Files written or planned.
        dry_run: True when nothing touched the disk.

    Returns:
        The pack result.
    """
    return PackResult(
        out_dir=root,
        pack_name=pack_name,
        version=version,
        sample_rate=sample_rate,
        tones=tuple(rows),
        files=tuple(files),
        manifest_path=root / MANIFEST_NAME,
        tone_count=len(rows),
        file_count=len(files),
        dry_run=dry_run,
    )


def _rel(path: Path, root: Path) -> str:
    """Pack-relative forward-slash path for the manifest.

    Args:
        path: File inside the pack.
        root: Pack directory.

    Returns:
        Relative POSIX path.
    """
    return path.relative_to(root).as_posix()


def build_parser() -> argparse.ArgumentParser:
    """Argument parser for the tone export verb.

    Returns:
        Configured parser.
    """
    parser = argparse.ArgumentParser(
        prog="ez_tones.pack",
        description="Render catalog tones and package an Android tone pack.",
    )
    parser.add_argument("--out", default=str(DEFAULT_OUT_DIR), help="pack directory")
    parser.add_argument("--kind", action="append", choices=list(KINDS), help="build only this kind (repeatable)")
    parser.add_argument("--tone", action="append", help="build only this slug (repeatable)")
    parser.add_argument("--catalog", help="operator catalog JSON merged over the shipped pack")
    parser.add_argument("--template", help="write the operator catalog template here and exit")
    parser.add_argument("--pack-name", default=DEFAULT_PACK_NAME, help="name stamped on the pack")
    parser.add_argument("--version", default=DEFAULT_VERSION, help="version stamped on the pack")
    parser.add_argument(
        "--sample-rate",
        type=int,
        choices=[44100, 48000],
        default=DEFAULT_SAMPLE_RATE,
        help="sample rate for every file",
    )
    parser.add_argument("--dry-run", action="store_true", help="print the plan, write nothing")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Command-line entry point for the tone export verb.

    Args:
        argv: Argument vector; ``None`` reads the process arguments.

    Returns:
        Process exit code: 0 on success, 1 when the catalog or ffmpeg failed.
    """
    args = build_parser().parse_args(argv)
    try:
        if args.template:
            write_catalog_template(args.template)
            print(f"wrote catalog template to {args.template}")
            return 0
        catalog: tuple[ToneSpec, ...] = TONE_CATALOG
        if args.catalog:
            catalog = load_catalog(args.catalog)
        build_pack(
            catalog,
            args.out,
            kinds=tuple(args.kind or ()),
            only_slugs=tuple(args.tone or ()),
            pack_name=args.pack_name,
            version=args.version,
            sample_rate=args.sample_rate,
            dry_run=args.dry_run,
        )
    except (ValueError, FfmpegError) as exc:
        print(f"tones: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
