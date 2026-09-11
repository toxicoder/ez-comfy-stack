"""ffmpeg stitch for 18 × 5.00s LTX MP4s with a 90s publish cap.

Illegal LTX ``length=120`` stems (113 frames / 4.708s) are padded to 5.00s
before the duration gate.

Hermetic at import: stdlib only. ffmpeg is resolved at call time.
"""

from __future__ import annotations

import html
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .jobstore import DURATION_S, DURATION_TOL
from .ltx_timing import ltx_decoded_frames
from .shots import DEFAULT_CAP_SECONDS, SHOT_COUNT, film_slug

LOUDNORM_FILTER = "loudnorm=I=-14:LRA=11:TP=-1.5"
AAC_BITRATE = "192k"
AAC_RATE = "48000"
AUDIO_FILTER = f"aresample={AAC_RATE},{LOUDNORM_FILTER}"
X264_PRESET = "veryfast"
X264_CRF = "18"
PIX_FMT = "yuv420p"
MOVFLAGS = "+faststart"
FPS = "24"
FPS_INT = 24
# Illegal widget 120 floors to 113 pixel frames (4.708333s @ 24fps).
LTX_120_DECODED_FRAMES = ltx_decoded_frames(120)
PAD_HOLD_FRAMES = int(round(DURATION_S * FPS_INT)) - LTX_120_DECODED_FRAMES
SHOT_WIDTH = 1280
SHOT_HEIGHT = 704
MASTER_TOL_S = 0.10
AUDIO_SYNC_TOL_S = 0.050
VIDEO_SUFFIXES = (".mp4", ".webm", ".mkv", ".mov", ".m4v")
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp", ".gif")


def log(message: str) -> None:
    """Write a pack line to stderr.

    Arguments:
        message: Text after the ``[ez_film]`` prefix.
    Returns:
        None
    """
    print(f"[ez_film] {message}", file=sys.stderr)


def output_directory() -> Path:
    """Comfy output dir, then ``COMFY_OUTPUT_DIR``, then ``output``.

    Returns:
        Directory path (may not exist yet).
    """
    try:
        import folder_paths  # type: ignore[import-not-found]

        return Path(folder_paths.get_output_directory())
    except Exception:  # noqa: BLE001 — Comfy is optional in unit tests
        env = os.environ.get("COMFY_OUTPUT_DIR")
        if env:
            return Path(env)
        return Path("output")


def find_ffmpeg() -> str:
    """Resolve ffmpeg: PATH, then imageio-ffmpeg (VHS dependency).

    Returns:
        Executable path.
    Raises:
        RuntimeError: no ffmpeg available.
    """
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg  # type: ignore[import-not-found]

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe:
            return str(exe)
    except Exception as exc:  # noqa: BLE001 — optional dep
        log(f"imageio_ffmpeg unavailable: {exc}")
    raise RuntimeError("ffmpeg not on PATH")


def find_ffprobe() -> str | None:
    """Resolve ffprobe on PATH, or None.

    Returns:
        Executable path or None.
    """
    return shutil.which("ffprobe")


def _is_video_path(path: str) -> bool:
    """True when ``path`` has a video suffix."""
    return Path(path).suffix.lower() in VIDEO_SUFFIXES


def _is_image_path(path: str) -> bool:
    """True when ``path`` has an image suffix (VHS metadata PNG)."""
    return Path(path).suffix.lower() in IMAGE_SUFFIXES


def _is_muxed_audio_path(path: str) -> bool:
    """True when ``path`` is a VHS muxed ``*-audio.<videoext>`` file."""
    return _is_video_path(path) and Path(path).stem.endswith("-audio")


def _sibling_video(path: str) -> str | None:
    """Muxed ``{stem}-audio.mp4`` then silent ``{stem}.mp4`` next to an image."""
    if not _is_image_path(path):
        return None
    image = Path(path)
    muxed = image.with_name(f"{image.stem}-audio.mp4")
    if muxed.is_file():
        return str(muxed)
    silent = image.with_suffix(".mp4")
    if silent.is_file():
        return str(silent)
    return None


def _path_strings(value: object) -> list[str]:
    """Flatten a VHS_FILENAMES payload into path strings.

    Arguments:
        value: str path, ``(saved, [paths])`` tuple, list, dict, or Path.
    Returns:
        Path strings in payload order (empty when unusable).
    """
    if value is None:
        return []
    if isinstance(value, Path):
        return [str(value)]
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, dict):
        for key in ("filename", "path", "file"):
            raw = value.get(key)
            if raw:
                return _path_strings(raw)
        return []
    if isinstance(value, (list, tuple)):
        if not value:
            return []
        if len(value) == 2 and isinstance(value[0], bool):
            return _path_strings(value[1])
        out: list[str] = []
        for item in value:
            out.extend(_path_strings(item))
        return out
    return []


def resolve_shot_path(value: object) -> str:
    """Most-complete video path from a VHS_FILENAMES payload or a plain path.

    VideoHelperSuite writes files in creation order: metadata PNG, silent
    MP4, then muxed ``*-audio.mp4``. VHS documents ``output[1][-1]`` as the
    most complete file. Prefer that muxed AV, then the last video suffix,
    then a sibling MP4 next to a PNG.

    Arguments:
        value: str path, ``(saved, [paths])`` tuple, list, or dict.
    Returns:
        Path string.
    Raises:
        ValueError: empty / unusable payload or no video in the list.
    """
    if value is None:
        raise ValueError("missing shot file")
    if not isinstance(value, (Path, str, dict, list, tuple)):
        raise ValueError(f"unusable shot payload: {type(value).__name__}")
    if isinstance(value, dict):
        paths = _path_strings(value)
        if not paths:
            raise ValueError("shot dict has no filename")
    else:
        paths = _path_strings(value)
        if not paths:
            raise ValueError("empty shot path")
    muxed = [path for path in paths if _is_muxed_audio_path(path)]
    if muxed:
        return muxed[-1]
    videos = [path for path in paths if _is_video_path(path)]
    if videos:
        return videos[-1]
    sibling = _sibling_video(paths[-1])
    if sibling:
        return sibling
    raise ValueError(f"no MP4 in shot payload (got {paths[-1]})")


def encoder_missing(stderr: str) -> bool:
    """True when ffmpeg failed because libx264 is not in the build."""
    text = (stderr or "").lower()
    if "unknown encoder" in text:
        return True
    if "encoder not found" in text:
        return True
    return "libx264" in text and "not found" in text


def write_preview_html(out_mp4: str) -> Path:
    """Write a one-file HTML player next to the published MP4.

    Arguments:
        out_mp4: Published MP4 path.
    Returns:
        HTML sidecar path.
    """
    path = Path(out_mp4)
    name = path.name
    title = html.escape(path.stem)
    src = html.escape(name)
    sidecar = path.with_suffix(".html")
    sidecar.write_text(
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"  <title>{title}</title>\n"
        "  <style>\n"
        "    body{margin:0;background:#111;color:#eee;"
        "font:16px/1.4 system-ui,sans-serif}\n"
        "    main{max-width:1280px;margin:0 auto;padding:16px}\n"
        "    video{width:100%;height:auto;background:#000}\n"
        "    a{color:#8cf}\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        "  <main>\n"
        f"    <h1>{title}</h1>\n"
        f'    <video controls playsinline src="{src}"></video>\n'
        f'    <p><a href="{src}" download>Download MP4</a></p>\n'
        "  </main>\n"
        "</body>\n"
        "</html>\n",
        encoding="utf-8",
    )
    return sidecar


def copy_publish_master(
    out_mp4: str, film: str, output_dir: Path | None = None
) -> Path | None:
    """Copy the master into ``films/<slug>/publish/`` when that dir exists.

    Arguments:
        out_mp4: Published MP4 path.
        film: Film id.
        output_dir: Override output directory.
    Returns:
        Destination path, or None when skipped.
    """
    dest = output_dir if output_dir is not None else output_directory()
    publish = dest / "films" / film_slug(film) / "publish"
    if not publish.is_dir():
        return None
    master = publish / "master.mp4"
    try:
        shutil.copy2(out_mp4, master)
    except OSError as exc:
        log(f"publish master copy skipped: {exc}")
        return None
    return master


def write_disclosure_sidecar(out_mp4: str, text: str) -> Path | None:
    """Write LTX disclosure next to the published MP4. No-op when text is empty.

    Arguments:
        out_mp4: Published MP4 path.
        text: Disclosure body (already run through EZFilmDisclosure).
    Returns:
        Sidecar path, or None when skipped.
    """
    body = str(text or "").strip()
    if not body:
        return None
    sidecar = Path(out_mp4).with_suffix(".disclosure.txt")
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_text(body + "\n", encoding="utf-8")
    return sidecar


def concat_list_line(path: str) -> str:
    """One concat-demuxer line with escaped single quotes.

    Arguments:
        path: Absolute or relative MP4 path.
    Returns:
        ``file '…'`` line without newline.
    """
    escaped = path.replace("'", "'\\''")
    return f"file '{escaped}'"


def _concat_input_prefix(ffmpeg: str, list_path: str, cap_seconds: float) -> list[str]:
    """Shared concat-demuxer input + duration cap."""
    return [
        ffmpeg,
        "-y",
        "-fflags",
        "+genpts",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        list_path,
        "-t",
        str(cap_seconds),
        "-avoid_negative_ts",
        "make_zero",
    ]


def ffmpeg_stitch_argv(
    list_path: str,
    out_mp4: str,
    cap_seconds: float,
    ffmpeg: str,
) -> list[str]:
    """Build the default playable stitch (H.264 + AAC + faststart).

    Audio acrossfade is a separate three-step remux (see :func:`stitch_film`
    ``xfade_cs``). If libx264 is missing, :func:`stitch_film` falls back to
    :func:`ffmpeg_stitch_copy_argv`.

    Arguments:
        list_path: Concat demuxer list file.
        out_mp4: Destination MP4.
        cap_seconds: ffmpeg ``-t`` cap.
        ffmpeg: ffmpeg executable.
    Returns:
        Argument vector.
    """
    return [
        *_concat_input_prefix(ffmpeg, list_path, cap_seconds),
        "-r",
        FPS,
        "-c:v",
        "libx264",
        "-preset",
        X264_PRESET,
        "-crf",
        X264_CRF,
        "-pix_fmt",
        PIX_FMT,
        "-c:a",
        "aac",
        "-ar",
        AAC_RATE,
        "-ac",
        "2",
        "-b:a",
        AAC_BITRATE,
        "-af",
        AUDIO_FILTER,
        "-movflags",
        MOVFLAGS,
        out_mp4,
    ]


def ffmpeg_stitch_copy_argv(
    list_path: str,
    out_mp4: str,
    cap_seconds: float,
    ffmpeg: str,
) -> list[str]:
    """Fallback stitch: video copy, AAC + loudnorm + faststart."""
    return [
        *_concat_input_prefix(ffmpeg, list_path, cap_seconds),
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-ar",
        AAC_RATE,
        "-ac",
        "2",
        "-b:a",
        AAC_BITRATE,
        "-af",
        AUDIO_FILTER,
        "-movflags",
        MOVFLAGS,
        out_mp4,
    ]


def audio_acrossfade_filter(n_inputs: int, duration_s: float) -> str:
    """Build an ffmpeg ``-filter_complex`` graph for chained audio acrossfade.

    Arguments:
        n_inputs: Number of audio inputs (``[0:a]`` …).
        duration_s: Acrossfade duration in seconds (e.g. 0.10).
    Returns:
        filter_complex string ending in ``[a]`` after loudnorm.
    Raises:
        ValueError: fewer than two inputs.
    """
    if n_inputs < 2:
        raise ValueError("acrossfade needs at least 2 inputs")
    d = f"{duration_s:.2f}"
    if n_inputs == 2:
        chain = f"[0:a][1:a]acrossfade=d={d}:c1=tri:c2=tri[ax]"
    else:
        parts = [f"[0:a][1:a]acrossfade=d={d}:c1=tri:c2=tri[a1]"]
        for index in range(2, n_inputs):
            prev = index - 1
            label = "ax" if index == n_inputs - 1 else f"a{index}"
            parts.append(
                f"[a{prev}][{index}:a]acrossfade=d={d}:c1=tri:c2=tri[{label}]"
            )
        chain = ";".join(parts)
    return f"{chain};[ax]{AUDIO_FILTER}[a]"


def ffmpeg_video_copy_argv(
    list_path: str, out_mp4: str, cap_seconds: float, ffmpeg: str
) -> list[str]:
    """Concat demuxer, H.264 video, drop audio (step 1 of xfade remux)."""
    return [
        *_concat_input_prefix(ffmpeg, list_path, cap_seconds),
        "-r",
        FPS,
        "-c:v",
        "libx264",
        "-preset",
        X264_PRESET,
        "-crf",
        X264_CRF,
        "-pix_fmt",
        PIX_FMT,
        "-an",
        out_mp4,
    ]


def ffmpeg_video_streamcopy_argv(
    list_path: str, out_mp4: str, cap_seconds: float, ffmpeg: str
) -> list[str]:
    """Concat demuxer, video copy, drop audio (libx264 fallback)."""
    return [
        *_concat_input_prefix(ffmpeg, list_path, cap_seconds),
        "-c:v",
        "copy",
        "-an",
        out_mp4,
    ]


def ffmpeg_audio_acrossfade_argv(
    shot_paths: list[str],
    out_m4a: str,
    ffmpeg: str,
    duration_s: float,
) -> list[str]:
    """N-input audio acrossfade + loudnorm to AAC 48 kHz stereo 192k."""
    argv: list[str] = [ffmpeg, "-y"]
    for path in shot_paths:
        argv.extend(["-i", path])
    argv.extend(
        [
            "-filter_complex",
            audio_acrossfade_filter(len(shot_paths), duration_s),
            "-map",
            "[a]",
            "-c:a",
            "aac",
            "-ar",
            AAC_RATE,
            "-ac",
            "2",
            "-b:a",
            AAC_BITRATE,
            out_m4a,
        ]
    )
    return argv


def ffmpeg_mux_copy_argv(
    video_mp4: str, audio_m4a: str, out_mp4: str, cap_seconds: float, ffmpeg: str
) -> list[str]:
    """Mux copied video with acrossfaded AAC (step 3 of xfade remux)."""
    return [
        ffmpeg,
        "-y",
        "-i",
        video_mp4,
        "-i",
        audio_m4a,
        "-t",
        str(cap_seconds),
        "-c:v",
        "copy",
        "-c:a",
        "copy",
        "-movflags",
        MOVFLAGS,
        out_mp4,
    ]


def _ffprobe_csv(
    path: str,
    args: list[str],
    ffprobe: str | None = None,
    run: Any = None,
) -> str | None:
    """Run ffprobe and return stripped stdout, or None on failure."""
    exe = ffprobe if ffprobe is not None else find_ffprobe()
    if not exe:
        return None
    runner = run or subprocess.run
    try:
        proc = runner(
            [exe, "-v", "error", *args, path],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        log(f"ffprobe failed: {exc}")
        return None
    if getattr(proc, "returncode", 1) != 0:
        return None
    text = (getattr(proc, "stdout", "") or "").strip()
    return text or None


def probe_has_audio(
    path: str, ffprobe: str | None = None, run: Any = None
) -> bool:
    """True when ffprobe reports an audio stream.

    Arguments:
        path: MP4 path.
        ffprobe: Optional ffprobe executable.
        run: Override ``subprocess.run``.
    Returns:
        False when ffprobe is missing or no audio stream.
    """
    text = _ffprobe_csv(
        path,
        [
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=codec_type",
            "-of",
            "csv=p=0",
        ],
        ffprobe=ffprobe,
        run=run,
    )
    if not text:
        return False
    return "audio" in text.lower()


def probe_audio_hz(
    path: str, ffprobe: str | None = None, run: Any = None
) -> int | None:
    """Audio sample rate in Hz, or None if unavailable."""
    text = _ffprobe_csv(
        path,
        [
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=sample_rate",
            "-of",
            "csv=p=0",
        ],
        ffprobe=ffprobe,
        run=run,
    )
    if not text:
        return None
    try:
        return int(float(text.split(",")[-1].strip()))
    except ValueError:
        return None


def probe_seconds(path: str, ffprobe: str | None = None, run: Any = None) -> float | None:
    """Duration in seconds, or None if ffprobe is missing/fails.

    Arguments:
        path: MP4 path.
        ffprobe: Optional ffprobe executable.
        run: Override ``subprocess.run``.
    Returns:
        Float seconds or None.
    """
    text = _ffprobe_csv(
        path,
        ["-show_entries", "format=duration", "-of", "csv=p=0"],
        ffprobe=ffprobe,
        run=run,
    )
    if not text:
        return None
    try:
        return float(text.split(",")[0].strip())
    except ValueError:
        return None


def is_ltx_120_floor_duration(dur: float) -> bool:
    """True when ``dur`` is the 113-frame VAE floor of an illegal 120 widget."""
    expected = LTX_120_DECODED_FRAMES / float(FPS_INT)
    return abs(float(dur) - expected) <= (1.0 / float(FPS_INT))


def ffmpeg_pad_stem_argv(
    src: str,
    dest: str,
    ffmpeg: str,
    extra_frames: int = PAD_HOLD_FRAMES,
) -> list[str]:
    """Clone last video frame + pad audio to the 5.00s picture contract."""
    pad_dur = extra_frames / float(FPS_INT)
    target = f"{DURATION_S:.2f}"
    vfilter = (
        f"[0:v]tpad=stop_mode=clone:stop={extra_frames},"
        f"fps={FPS},trim=duration={target},setpts=PTS-STARTPTS[v]"
    )
    afilter = (
        f"[0:a]apad=pad_dur={pad_dur:.6f},"
        f"atrim=duration={target},asetpts=PTS-STARTPTS[a]"
    )
    return [
        ffmpeg,
        "-y",
        "-i",
        src,
        "-filter_complex",
        f"{vfilter};{afilter}",
        "-map",
        "[v]",
        "-map",
        "[a]",
        "-t",
        target,
        "-r",
        FPS,
        "-c:v",
        "libx264",
        "-preset",
        X264_PRESET,
        "-crf",
        X264_CRF,
        "-pix_fmt",
        PIX_FMT,
        "-c:a",
        "aac",
        "-ar",
        AAC_RATE,
        "-ac",
        "2",
        "-b:a",
        AAC_BITRATE,
        dest,
    ]


def normalize_stitch_stem(
    path: str,
    *,
    ffmpeg: str,
    ffprobe: str | None = None,
    run: Any = None,
    temps: list[str] | None = None,
) -> str:
    """Pad a 113-frame LTX neighbor to 5.00s; otherwise return ``path``.

    Arguments:
        path: Candidate MP4.
        ffmpeg: ffmpeg executable (required to pad).
        ffprobe: Optional ffprobe executable.
        run: Override ``subprocess.run``.
        temps: Optional list that receives temp paths for later unlink.
    Returns:
        Original path, or a temp padded to 5.00s.
    Raises:
        RuntimeError: pad ffmpeg fails.
    """
    dur = probe_seconds(path, ffprobe=ffprobe, run=run)
    if dur is None or abs(dur - DURATION_S) <= DURATION_TOL:
        return path
    if not is_ltx_120_floor_duration(dur):
        return path
    handle = tempfile.NamedTemporaryFile(
        "wb", suffix=".pad.mp4", delete=False
    )
    dest = handle.name
    handle.close()
    if temps is not None:
        temps.append(dest)
    log(
        f"padded {dur:.6f}s → {DURATION_S:.2f}s "
        f"(LTX 8n+1 neighbor {LTX_120_DECODED_FRAMES} frames) ({path})"
    )
    _run_ffmpeg(ffmpeg_pad_stem_argv(path, dest, ffmpeg), run or subprocess.run)
    return dest


def normalize_stitch_stems(
    shot_paths: list[str],
    *,
    ffmpeg: str,
    ffprobe: str | None = None,
    run: Any = None,
) -> tuple[list[str], list[str]]:
    """Pad 113-frame LTX neighbors; return ``(paths, temps_to_unlink)``."""
    temps: list[str] = []
    out = [
        normalize_stitch_stem(
            path, ffmpeg=ffmpeg, ffprobe=ffprobe, run=run, temps=temps
        )
        for path in shot_paths
    ]
    return out, temps


def probe_wh(
    path: str, ffprobe: str | None = None, run: Any = None
) -> tuple[int, int] | None:
    """First video stream width×height, or None."""
    text = _ffprobe_csv(
        path,
        [
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=p=0",
        ],
        ffprobe=ffprobe,
        run=run,
    )
    if not text or "," not in text:
        return None
    left, right = text.split(",", 1)
    try:
        return int(left), int(right)
    except ValueError:
        return None


def probe_audio_seconds(
    path: str, ffprobe: str | None = None, run: Any = None
) -> float | None:
    """Audio stream duration in seconds, or None."""
    text = _ffprobe_csv(
        path,
        [
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=duration",
            "-of",
            "csv=p=0",
        ],
        ffprobe=ffprobe,
        run=run,
    )
    if text:
        token = text.split(",")[0].strip()
        if token and token.upper() != "N/A":
            try:
                return float(token)
            except ValueError:
                pass
    return probe_seconds(path, ffprobe=ffprobe, run=run)


def validate_stitch_stems(
    shot_paths: list[str],
    *,
    ffprobe: str | None = None,
    run: Any = None,
) -> None:
    """Refuse missing, unreadable, short, or silent stems before ffmpeg.

    Arguments:
        shot_paths: Candidate MP4 paths in beat/shot order.
        ffprobe: Optional ffprobe executable.
        run: Override ``subprocess.run``.
    Raises:
        ValueError: wrong shot count.
        RuntimeError: a stem is missing, unreadable, or off-contract.
    """
    if len(shot_paths) != SHOT_COUNT:
        raise ValueError(f"expected {SHOT_COUNT} shots, found {len(shot_paths)}")
    exe = ffprobe if ffprobe is not None else find_ffprobe()
    if not exe:
        raise RuntimeError("ffprobe required to validate shots")
    valid: list[str] = []
    for path in shot_paths:
        if not path or not str(path).strip():
            raise RuntimeError("missing shot file")
        file_path = Path(path)
        if not file_path.is_file():
            raise RuntimeError(f"unreadable shot ({path})")
        if file_path.stat().st_size < 1:
            raise RuntimeError(f"empty shot ({path})")
        dur = probe_seconds(path, ffprobe=exe, run=run)
        if dur is None or abs(dur - DURATION_S) > DURATION_TOL:
            raise RuntimeError(
                f"shot duration {dur!r} (need {DURATION_S}±{DURATION_TOL}) ({path})"
            )
        wh = probe_wh(path, ffprobe=exe, run=run)
        if wh != (SHOT_WIDTH, SHOT_HEIGHT):
            raise RuntimeError(
                f"shot size {wh!r} (need {SHOT_WIDTH}x{SHOT_HEIGHT}) ({path})"
            )
        if not probe_has_audio(path, ffprobe=exe, run=run):
            raise RuntimeError(f"shot missing audio ({path})")
        valid.append(path)
    if len(valid) != SHOT_COUNT:
        raise RuntimeError(
            f"expected {SHOT_COUNT} valid shots, found {len(valid)}; "
            "refusing to write a short master"
        )


def _unlink_master(out_mp4: str) -> None:
    """Best-effort delete a failed master so 17-shot files never publish."""
    Path(out_mp4).unlink(missing_ok=True)


def assert_master_duration(
    out_mp4: str,
    cap_seconds: float,
    *,
    ffprobe: str | None = None,
    run: Any = None,
) -> None:
    """Fail closed if the stitched master is not ``cap±0.10`` with synced audio.

    Arguments:
        out_mp4: Stitched MP4 path.
        cap_seconds: Publish cap (90.00).
        ffprobe: Optional ffprobe executable.
        run: Override ``subprocess.run``.
    Raises:
        RuntimeError: missing probe, duration outside band, or A/V skew.
    """
    exe = ffprobe if ffprobe is not None else find_ffprobe()
    if not exe:
        if run is None:
            _unlink_master(out_mp4)
            raise RuntimeError("ffprobe required to validate the stitched master")
        # Tests inject ``run``; production never passes run without a binary.
        exe = "ffprobe"
    dur = probe_seconds(out_mp4, ffprobe=exe, run=run)
    if dur is None:
        _unlink_master(out_mp4)
        raise RuntimeError(f"concat duration unreadable ({out_mp4})")
    cap = float(cap_seconds)
    if dur > cap + MASTER_TOL_S:
        _unlink_master(out_mp4)
        raise RuntimeError(f"concat duration {dur}s exceeds cap {cap}s")
    if dur < cap - MASTER_TOL_S:
        _unlink_master(out_mp4)
        raise RuntimeError(
            f"concat duration {dur}s short of cap {cap}s "
            f"(need {cap:.2f}±{MASTER_TOL_S})"
        )
    if not probe_has_audio(out_mp4, ffprobe=exe, run=run):
        _unlink_master(out_mp4)
        raise RuntimeError(f"concat master missing audio ({out_mp4})")
    audio_dur = probe_audio_seconds(out_mp4, ffprobe=exe, run=run)
    if audio_dur is None or abs(audio_dur - dur) > AUDIO_SYNC_TOL_S:
        _unlink_master(out_mp4)
        raise RuntimeError(
            f"concat audio duration {audio_dur!r}s vs video {dur}s "
            f"(need within {AUDIO_SYNC_TOL_S * 1000:.0f} ms)"
        )


def _run_ffmpeg(argv: list[str], runner: Any) -> None:
    """Run one ffmpeg argv; raise RuntimeError on non-zero."""
    log(" ".join(argv))
    proc = runner(argv, check=False, capture_output=True, text=True)
    if getattr(proc, "returncode", 1) != 0:
        err = getattr(proc, "stderr", "") or getattr(proc, "stdout", "") or ""
        raise RuntimeError(f"ffmpeg stitch failed: {err.strip() or 'exit 1'}")


def _run_with_x264_fallback(
    playable: list[str], fallback: list[str], runner: Any
) -> None:
    """Run playable argv; retry fallback when libx264 is missing."""
    try:
        _run_ffmpeg(playable, runner)
    except RuntimeError as exc:
        if not encoder_missing(str(exc)):
            raise
        log("libx264 missing; falling back to stream-copy + faststart")
        _run_ffmpeg(fallback, runner)


def stitch_film(
    shot_paths: list[str],
    out_mp4: str,
    cap_seconds: float = DEFAULT_CAP_SECONDS,
    *,
    ffmpeg: str | None = None,
    ffprobe: str | None = None,
    run: Any = None,
    xfade_cs: int = 0,
) -> str:
    """Concat 18 shot MP4s, cap duration, fail closed on short or long masters.

    Default (``xfade_cs=0``) is concat-demuxer + libx264 CRF 18 + AAC +
    ``+faststart`` so browsers can play and download the master. ``xfade_cs``
    is centiseconds of **audio** acrossfade (10 = 0.10 s); video is still a
    hard cut, re-encoded the same way. Wan-silent shots have no audio —
    xfade refuses. If ffmpeg lacks libx264, fall back to ``-c:v copy`` with
    faststart still set.

    Every stem must exist, last 5.00±0.05s, be 1280×704, and carry audio.
    Illegal LTX ``length=120`` files (113 frames / 4.708s) are padded to
    5.00s (cloned last frame) before the duration gate. After stitch the
    master must be ``cap±0.10`` s with audio within 50 ms of picture. A
    failed master is deleted so a 17-shot file cannot publish.

    Arguments:
        shot_paths: Exactly 18 MP4 paths in beat/shot order (not VHS metadata PNGs).
        out_mp4: Destination path.
        cap_seconds: Publish cap (default 90).
        ffmpeg: Override ffmpeg path.
        ffprobe: Override ffprobe path.
        run: Override ``subprocess.run`` (tests).
        xfade_cs: Audio acrossfade in centiseconds; 0 disables.
    Returns:
        ``out_mp4``.
    Raises:
        ValueError: wrong shot count or invalid xfade_cs.
        RuntimeError: ffmpeg missing/fails, missing/short stems, or duration off cap.
    """
    if len(shot_paths) != SHOT_COUNT:
        raise ValueError(f"expected {SHOT_COUNT} shots, found {len(shot_paths)}")
    for path in shot_paths:
        if _is_image_path(path):
            raise RuntimeError(
                f"shot is an image, not an MP4 ({path}); "
                "VHS_FILENAMES first file is a metadata PNG — use the muxed *-audio.mp4"
            )
    if xfade_cs < 0 or xfade_cs > 50:
        raise ValueError(f"xfade_cs must be 0–50, got {xfade_cs}")
    exe = ffmpeg or find_ffmpeg()
    work_paths, pad_tmps = normalize_stitch_stems(
        shot_paths, ffmpeg=exe, ffprobe=ffprobe, run=run
    )
    try:
        validate_stitch_stems(work_paths, ffprobe=ffprobe, run=run)
        log(f"stitching {len(work_paths)} shots → {out_mp4}")
        try:
            root = str(Path(__file__).resolve().parent.parent)
            if root not in sys.path:
                sys.path.insert(0, root)
            from ez_common import node_log, node_progress

            node_log("ez_film", f"stitching {len(work_paths)} shots")
            bar = node_progress(2)
        except Exception:  # noqa: BLE001 — pytest / missing pack
            bar = None
        runner = run or subprocess.run
        list_file = tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".txt", delete=False
        )
        video_tmp = ""
        audio_tmp = ""
        try:
            for path in work_paths:
                list_file.write(concat_list_line(path) + "\n")
            list_file.close()
            if xfade_cs == 0:
                _run_with_x264_fallback(
                    ffmpeg_stitch_argv(list_file.name, out_mp4, cap_seconds, exe),
                    ffmpeg_stitch_copy_argv(list_file.name, out_mp4, cap_seconds, exe),
                    runner,
                )
                if bar is not None:
                    bar.update(2)
            else:
                for path in work_paths:
                    if not probe_has_audio(path, ffprobe=ffprobe, run=run):
                        raise RuntimeError(
                            f"xfade requires audio on every shot (missing on {path}); "
                            "Wan-silent concat cannot use --xfade"
                        )
                duration_s = xfade_cs / 100.0
                video_tmp = list_file.name + ".v.mp4"
                audio_tmp = list_file.name + ".a.m4a"
                _run_with_x264_fallback(
                    ffmpeg_video_copy_argv(list_file.name, video_tmp, cap_seconds, exe),
                    ffmpeg_video_streamcopy_argv(
                        list_file.name, video_tmp, cap_seconds, exe
                    ),
                    runner,
                )
                _run_ffmpeg(
                    ffmpeg_audio_acrossfade_argv(
                        work_paths, audio_tmp, exe, duration_s
                    ),
                    runner,
                )
                _run_ffmpeg(
                    ffmpeg_mux_copy_argv(
                        video_tmp, audio_tmp, out_mp4, cap_seconds, exe
                    ),
                    runner,
                )
                if bar is not None:
                    bar.update(2)
                hz = probe_audio_hz(out_mp4, ffprobe=ffprobe, run=run)
                if hz is not None and hz != int(AAC_RATE):
                    raise RuntimeError(
                        f"concat audio is {hz} Hz, expected {AAC_RATE}"
                    )
        finally:
            Path(list_file.name).unlink(missing_ok=True)
            if video_tmp:
                Path(video_tmp).unlink(missing_ok=True)
            if audio_tmp:
                Path(audio_tmp).unlink(missing_ok=True)
    finally:
        for tmp in pad_tmps:
            Path(tmp).unlink(missing_ok=True)

    assert_master_duration(
        out_mp4, cap_seconds, ffprobe=ffprobe, run=run
    )
    return out_mp4


def publish_path(film: str, output_dir: Path | None = None) -> Path:
    """``ez_{slug}_90s.mp4`` under the output directory.

    Arguments:
        film: Film id.
        output_dir: Override output directory.
    Returns:
        Destination path.
    """
    dest = output_dir if output_dir is not None else output_directory()
    return dest / f"ez_{film_slug(film)}_90s.mp4"
