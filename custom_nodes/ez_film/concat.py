"""ffmpeg stitch for 18 × 5.00s LTX MP4s with a 90s publish cap.

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


def probe_seconds(path: str, ffprobe: str | None = None) -> float | None:
    """Duration in seconds, or None if ffprobe is missing/fails.

    Arguments:
        path: MP4 path.
        ffprobe: Optional ffprobe executable.
    Returns:
        Float seconds or None.
    """
    exe = ffprobe if ffprobe is not None else find_ffprobe()
    if not exe:
        return None
    try:
        proc = subprocess.run(
            [
                exe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "csv=p=0",
                path,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        log(f"ffprobe failed: {exc}")
        return None
    text = (proc.stdout or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


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
    """Concat 18 shot MP4s, cap duration, fail if probe exceeds cap.

    Default (``xfade_cs=0``) is concat-demuxer + libx264 CRF 18 + AAC +
    ``+faststart`` so browsers can play and download the master. ``xfade_cs``
    is centiseconds of **audio** acrossfade (10 = 0.10 s); video is still a
    hard cut, re-encoded the same way. Wan-silent shots have no audio —
    xfade refuses. If ffmpeg lacks libx264, fall back to ``-c:v copy`` with
    faststart still set.

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
        RuntimeError: ffmpeg missing/fails, missing audio, or duration over cap.
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
    log(f"stitching {len(shot_paths)} shots → {out_mp4}")
    try:
        root = str(Path(__file__).resolve().parent.parent)
        if root not in sys.path:
            sys.path.insert(0, root)
        from ez_common import node_log, node_progress

        node_log("ez_film", f"stitching {len(shot_paths)} shots")
        bar = node_progress(2)
    except Exception:  # noqa: BLE001 — pytest / missing pack
        bar = None
    exe = ffmpeg or find_ffmpeg()
    runner = run or subprocess.run
    list_file = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", suffix=".txt", delete=False
    )
    video_tmp = ""
    audio_tmp = ""
    try:
        for path in shot_paths:
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
            for path in shot_paths:
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
                ffmpeg_audio_acrossfade_argv(shot_paths, audio_tmp, exe, duration_s),
                runner,
            )
            _run_ffmpeg(
                ffmpeg_mux_copy_argv(video_tmp, audio_tmp, out_mp4, cap_seconds, exe),
                runner,
            )
            if bar is not None:
                bar.update(2)
            hz = probe_audio_hz(out_mp4, ffprobe=ffprobe, run=run)
            if hz is not None and hz != int(AAC_RATE):
                raise RuntimeError(f"concat audio is {hz} Hz, expected {AAC_RATE}")
    finally:
        Path(list_file.name).unlink(missing_ok=True)
        if video_tmp:
            Path(video_tmp).unlink(missing_ok=True)
        if audio_tmp:
            Path(audio_tmp).unlink(missing_ok=True)

    dur = probe_seconds(out_mp4, ffprobe=ffprobe)
    if dur is not None and dur > float(cap_seconds) + 0.05:
        raise RuntimeError(
            f"concat duration {dur}s exceeds cap {cap_seconds}s"
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
