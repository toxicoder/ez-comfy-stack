"""ffmpeg stitch for 18 x 5.00s LTX MP4s with a 90s publish cap.

Clip-chain stitch (1-24 duration-head stems) lives beside the film path
and does not pad the master to the cap.

Illegal LTX ``length=120`` stems (113 frames / 4.708s) are padded to 5.00s
before the duration gate (film only).

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
from typing import TYPE_CHECKING

from .jobstore import DURATION_S, DURATION_TOL
from .ltx_timing import DURATION_HEAD_S, ltx_decoded_frames
from .probe import (  # noqa: F401 - coverage/monkeypatch façade
    FfprobeMediaProbe,
    _ffprobe_csv,
    probe_audio_hz,
    probe_audio_seconds,
    probe_fps,
    probe_has_audio,
    probe_seconds,
    probe_wh,
)
from .protocols import FfmpegRunner
from .shots import (
    DEFAULT_CAP_SECONDS,
    SHOT_COUNT,
    film_slug,
    master_filename,
)

if TYPE_CHECKING:
    from ez_common.protocols import ProgressReporter

# ffmpeg/x264 stitch: loudnorm, AAC, H.264, FPS, pad, and path suffixes.
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
# Clip-chain stitch: 1-24 stems; cap is a ceiling, not pad-to-runtime.
CLIP_COUNT_MAX = 24
CLIP_CAP_DEFAULT_S = 600.0
CLIP_CAP_MAX_S = 1800.0
CLIP_PREFIX_DEFAULT = "ez_clip_chain"
CLIP_DURATION_HEAD_LABEL = "(5.00, 8.00, 10.00, 12.00) +/- 0.05"


def log(message: str) -> None:
    """Write a pack line to stderr.

    Args:
        message: Text after the ``[ez_film]`` prefix.
    Returns:
        None
    """
    print(f"[ez_film] {message}", file=sys.stderr)


def output_directory() -> Path:
    """Comfy output dir, then ``/outputs``, then ``COMFY_OUTPUT_DIR``, then ``output``.

    Returns:
        Directory path (may not exist yet).
    """
    try:
        from ez_common import output_root

        return output_root(default="output")
    except Exception:  # noqa: BLE001 - Comfy is optional in unit tests
        try:
            import folder_paths  # type: ignore[import-not-found]

            return Path(folder_paths.get_output_directory())
        except Exception:  # noqa: BLE001 - Comfy is optional in unit tests
            if Path("/outputs").is_dir():
                return Path("/outputs")
            env = (os.environ.get("COMFY_OUTPUT_DIR") or "").strip()
            if env:
                return Path(env)
            return Path("output")


class PathFfmpegTools:
    """PATH locator via this module's ``shutil.which`` (patchable in tests)."""

    def ffmpeg(self) -> str | None:
        """Return ffmpeg on PATH, or None.

        Returns:
            Executable path, or None.
        """
        return shutil.which("ffmpeg")

    def ffprobe(self) -> str | None:
        """Return ffprobe on PATH, or None.

        Returns:
            Executable path, or None.
        """
        return shutil.which("ffprobe")


def find_ffmpeg() -> str:
    """Resolve ffmpeg: PATH, then imageio-ffmpeg (VHS dependency).

    Returns:
        Executable path.
    Raises:
        RuntimeError: no ffmpeg available.
    """
    found = PathFfmpegTools().ffmpeg()
    if found:
        return found
    try:
        import imageio_ffmpeg  # type: ignore[import-not-found]

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe:
            return str(exe)
    except Exception as exc:  # noqa: BLE001 - optional dep
        log(f"imageio_ffmpeg unavailable: {exc}")
    raise RuntimeError("ffmpeg not on PATH")


def find_ffprobe() -> str | None:
    """Resolve ffprobe on PATH, or None.

    Returns:
        Executable path or None.
    """
    return PathFfmpegTools().ffprobe()


def _is_video_path(path: str) -> bool:
    """True when ``path`` has a video suffix.

    Args:
        path: Candidate file path.

    Returns:
        Whether the suffix is a video container.
    """
    return Path(path).suffix.lower() in VIDEO_SUFFIXES


def _is_image_path(path: str) -> bool:
    """True when ``path`` has an image suffix (VHS metadata PNG).

    Args:
        path: Candidate file path.

    Returns:
        Whether the suffix is an image.
    """
    return Path(path).suffix.lower() in IMAGE_SUFFIXES


def _is_muxed_audio_path(path: str) -> bool:
    """True when ``path`` is a VHS muxed ``*-audio.<videoext>`` file.

    Args:
        path: Candidate file path.

    Returns:
        Whether the stem ends with ``-audio`` and the suffix is video.
    """
    return _is_video_path(path) and Path(path).stem.endswith("-audio")


def _sibling_video(path: str) -> str | None:
    """Muxed ``{stem}-audio.mp4`` then silent ``{stem}.mp4`` next to an image.

    Args:
        path: Image path from a VHS payload.

    Returns:
        Sibling MP4 path, or None.
    """
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

    Args:
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

    Args:
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
    """True when ffmpeg failed because libx264 is not in the build.

    Args:
        stderr: ffmpeg stderr text.

    Returns:
        Whether the failure is a missing libx264 encoder.
    """
    text = (stderr or "").lower()
    if "unknown encoder" in text:
        return True
    if "encoder not found" in text:
        return True
    return "libx264" in text and "not found" in text


def write_preview_html(out_mp4: str) -> Path:
    """Write a one-file HTML player next to the published MP4.

    Args:
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

    Args:
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

    Args:
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

    Args:
        path: Absolute or relative MP4 path.
    Returns:
        ``file '...'`` line without newline.
    """
    escaped = path.replace("'", "'\\''")
    return f"file '{escaped}'"


def _concat_input_prefix(ffmpeg: str, list_path: str, cap_seconds: float) -> list[str]:
    """Shared concat-demuxer input + duration cap.

    Args:
        ffmpeg: ffmpeg executable.
        list_path: Concat demuxer list file.
        cap_seconds: ffmpeg ``-t`` cap.

    Returns:
        Argument prefix including inputs.
    """
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

    Args:
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
        f"{AUDIO_FILTER},apad",
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
    """Fallback stitch: video copy, AAC + loudnorm + faststart.

    Args:
        list_path: Concat demuxer list file.
        out_mp4: Destination MP4.
        cap_seconds: ffmpeg ``-t`` cap.
        ffmpeg: ffmpeg executable.

    Returns:
        Argument vector.
    """
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
        f"{AUDIO_FILTER},apad",
        "-movflags",
        MOVFLAGS,
        out_mp4,
    ]


def _clip_concat_input_prefix(ffmpeg: str, list_path: str) -> list[str]:
    """Concat-demuxer input prefix without a duration cap.

    Args:
        ffmpeg: ffmpeg executable.
        list_path: Concat demuxer list file.

    Returns:
        Argument prefix including inputs (no ``-t``).
    """
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
        "-avoid_negative_ts",
        "make_zero",
    ]


def ffmpeg_clip_stitch_argv(
    list_path: str, out_mp4: str, ffmpeg: str
) -> list[str]:
    """Playable clip stitch (H.264 + AAC + faststart) without ``-t`` / ``apad``.

    Same vector as :func:`ffmpeg_stitch_argv` except this does not call
    :func:`_concat_input_prefix`, omits the duration cap, and uses
    ``-af AUDIO_FILTER`` without ``,apad``. Cap is enforced by probing
    stems before encode.

    Args:
        list_path: Concat demuxer list file.
        out_mp4: Destination MP4.
        ffmpeg: ffmpeg executable.
    Returns:
        Argument vector.
    """
    return [
        *_clip_concat_input_prefix(ffmpeg, list_path),
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


def ffmpeg_clip_stitch_copy_argv(
    list_path: str, out_mp4: str, ffmpeg: str
) -> list[str]:
    """Clip stitch fallback: video copy, AAC + loudnorm + faststart, no ``-t``.

    Args:
        list_path: Concat demuxer list file.
        out_mp4: Destination MP4.
        ffmpeg: ffmpeg executable.

    Returns:
        Argument vector.
    """
    return [
        *_clip_concat_input_prefix(ffmpeg, list_path),
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


def audio_acrossfade_filter(
    n_inputs: int,
    duration_s: float,
    cap_seconds: float = DEFAULT_CAP_SECONDS,
    shot_seconds: float = DURATION_S,
) -> str:
    """Build an ffmpeg ``-filter_complex`` graph for chained audio acrossfade.

    Each input is padded/trimmed to ``shot_seconds`` (the 5.00 s picture
    contract). Joins use ``acrossfade`` with ``o=0`` so duration stays the
    sum of inputs (picture-aligned hard cuts). Overlap-on acrossfade would
    shorten audio by ``(n-1)*d`` and miss the 50 ms A/V gate. The chain is
    then loudnormed and padded/trimmed to ``cap_seconds``.

    Args:
        n_inputs: Number of audio inputs (``[0:a]`` ...).
        duration_s: Acrossfade duration in seconds (e.g. 0.10).
        cap_seconds: Publish cap for the final atrim (default 90).
        shot_seconds: Per-shot atrim (default 5.00).
    Returns:
        filter_complex string ending in ``[a]`` after loudnorm + cap pad.
    Raises:
        ValueError: fewer than two inputs.
    """
    if n_inputs < 2:
        raise ValueError("acrossfade needs at least 2 inputs")
    d = f"{duration_s:.2f}"
    shot = f"{float(shot_seconds):.2f}"
    cap = f"{float(cap_seconds):.2f}"
    prep = [
        f"[{index}:a]apad,atrim=duration={shot},asetpts=PTS-STARTPTS[s{index}]"
        for index in range(n_inputs)
    ]
    xfade = f"acrossfade=d={d}:o=0:c1=tri:c2=tri"
    if n_inputs == 2:
        chain = f"[s0][s1]{xfade}[ax]"
    else:
        parts = [f"[s0][s1]{xfade}[a1]"]
        for index in range(2, n_inputs):
            prev = index - 1
            label = "ax" if index == n_inputs - 1 else f"a{index}"
            parts.append(f"[a{prev}][s{index}]{xfade}[{label}]")
        chain = ";".join(parts)
    tail = f"[ax]{AUDIO_FILTER},apad,atrim=duration={cap},asetpts=PTS-STARTPTS[a]"
    return ";".join([*prep, chain, tail])


def ffmpeg_video_copy_argv(
    list_path: str, out_mp4: str, cap_seconds: float, ffmpeg: str
) -> list[str]:
    """Concat demuxer, H.264 video, drop audio (step 1 of xfade remux).

    Args:
        list_path: Concat demuxer list file.
        out_mp4: Destination video-only MP4.
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
        "-an",
        out_mp4,
    ]


def ffmpeg_video_streamcopy_argv(
    list_path: str, out_mp4: str, cap_seconds: float, ffmpeg: str
) -> list[str]:
    """Concat demuxer, video copy, drop audio (libx264 fallback).

    Args:
        list_path: Concat demuxer list file.
        out_mp4: Destination video-only MP4.
        cap_seconds: ffmpeg ``-t`` cap.
        ffmpeg: ffmpeg executable.

    Returns:
        Argument vector.
    """
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
    cap_seconds: float = DEFAULT_CAP_SECONDS,
) -> list[str]:
    """N-input picture-aligned audio acrossfade + loudnorm to AAC 48 kHz stereo 192k.

    Args:
        shot_paths: Shot MP4 paths in beat/shot order.
        out_m4a: Destination AAC file.
        ffmpeg: ffmpeg executable.
        duration_s: Acrossfade duration in seconds.
        cap_seconds: Publish cap for the final atrim.

    Returns:
        Argument vector.
    """
    argv: list[str] = [ffmpeg, "-y"]
    for path in shot_paths:
        argv.extend(["-i", path])
    argv.extend(
        [
            "-filter_complex",
            audio_acrossfade_filter(
                len(shot_paths), duration_s, cap_seconds=cap_seconds
            ),
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
    """Mux copied video with acrossfaded AAC (step 3 of xfade remux).

    Args:
        video_mp4: Video-only concat.
        audio_m4a: Acrossfaded AAC.
        out_mp4: Destination master.
        cap_seconds: ffmpeg ``-t`` cap.
        ffmpeg: ffmpeg executable.

    Returns:
        Argument vector.
    """
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


def is_ltx_120_floor_duration(dur: float) -> bool:
    """True when ``dur`` is the 113-frame VAE floor of an illegal 120 widget.

    Args:
        dur: Probed duration in seconds.

    Returns:
        Whether ``dur`` matches the 113-frame floor.
    """
    expected = LTX_120_DECODED_FRAMES / float(FPS_INT)
    return abs(float(dur) - expected) <= (1.0 / float(FPS_INT))


def ffmpeg_pad_stem_argv(
    src: str,
    dest: str,
    ffmpeg: str,
    extra_frames: int = PAD_HOLD_FRAMES,
) -> list[str]:
    """Clone last video frame + pad audio to the 5.00s picture contract.

    Args:
        src: Short LTX stem.
        dest: Padded destination MP4.
        ffmpeg: ffmpeg executable.
        extra_frames: Cloned hold frames (default 7 for 113->120).

    Returns:
        Argument vector.
    """
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
    run: FfmpegRunner | None = None,
    temps: list[str] | None = None,
) -> str:
    """Pad a 113-frame LTX neighbor to 5.00s; otherwise return ``path``.

    Args:
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
        f"padded {dur:.6f}s -> {DURATION_S:.2f}s "
        f"(LTX 8n+1 neighbor {LTX_120_DECODED_FRAMES} frames) ({path})"
    )
    _run_ffmpeg(ffmpeg_pad_stem_argv(path, dest, ffmpeg), run or subprocess.run)
    return dest


def normalize_stitch_stems(
    shot_paths: list[str],
    *,
    ffmpeg: str,
    ffprobe: str | None = None,
    run: FfmpegRunner | None = None,
) -> tuple[list[str], list[str]]:
    """Pad 113-frame LTX neighbors; return ``(paths, temps_to_unlink)``.

    Args:
        shot_paths: Candidate MP4 paths in beat/shot order.
        ffmpeg: ffmpeg executable.
        ffprobe: Optional ffprobe executable.
        run: Override ``subprocess.run``.

    Returns:
        ``(normalized paths, temp paths to unlink)``.
    """
    temps: list[str] = []
    out = [
        normalize_stitch_stem(
            path, ffmpeg=ffmpeg, ffprobe=ffprobe, run=run, temps=temps
        )
        for path in shot_paths
    ]
    return out, temps


def validate_stitch_stems(
    shot_paths: list[str],
    *,
    ffprobe: str | None = None,
    run: FfmpegRunner | None = None,
    expected_count: int | None = None,
) -> None:
    """Refuse missing, unreadable, short, or silent stems before ffmpeg.

    Args:
        shot_paths: Candidate MP4 paths in beat/shot order.
        ffprobe: Optional ffprobe executable.
        run: Override ``subprocess.run``.
        expected_count: Required stem count (default 18 for 90s one-click).
    Raises:
        ValueError: wrong shot count.
        RuntimeError: a stem is missing, unreadable, or off-contract.
    """
    count = SHOT_COUNT if expected_count is None else int(expected_count)
    if len(shot_paths) != count:
        raise ValueError(f"expected {count} shots, found {len(shot_paths)}")
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
                f"shot duration {dur!r} (need {DURATION_S} +/- {DURATION_TOL}) ({path})"
            )
        wh = probe_wh(path, ffprobe=exe, run=run)
        if wh != (SHOT_WIDTH, SHOT_HEIGHT):
            raise RuntimeError(
                f"shot size {wh!r} (need {SHOT_WIDTH}x{SHOT_HEIGHT}) ({path})"
            )
        if not probe_has_audio(path, ffprobe=exe, run=run):
            raise RuntimeError(f"shot missing audio ({path})")
        valid.append(path)
    if len(valid) != count:
        raise RuntimeError(
            f"expected {count} valid shots, found {len(valid)}; "
            "refusing to write a short master"
        )


def _unlink_master(out_mp4: str) -> None:
    """Best-effort delete a failed master so 17-shot files never publish.

    Args:
        out_mp4: Master path to delete.
    """
    Path(out_mp4).unlink(missing_ok=True)


def assert_master_duration(
    out_mp4: str,
    cap_seconds: float,
    *,
    ffprobe: str | None = None,
    run: FfmpegRunner | None = None,
) -> None:
    """Fail closed if the stitched master is not ``cap +/- 0.10`` with synced audio.

    Args:
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
            f"(need {cap:.2f} +/- {MASTER_TOL_S})"
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


def assert_clip_master_duration(
    out_mp4: str,
    probed_sum: float,
    cap_seconds: float,
    n_stems: int,
    *,
    ffprobe: str | None = None,
    run: FfmpegRunner | None = None,
) -> None:
    """Fail closed if the clip master is not ``sum(stems)`` with synced audio.

    Cap is a ceiling. Never requires the master to reach ``cap - 0.10``.

    Args:
        out_mp4: Stitched MP4 path.
        probed_sum: Sum of stem durations.
        cap_seconds: Publish ceiling.
        n_stems: Stem count (widens the sum band).
        ffprobe: Optional ffprobe executable.
        run: Override ``subprocess.run``.
    Raises:
        RuntimeError: missing probe, duration off sum or over cap, or A/V skew.
    """
    exe = ffprobe if ffprobe is not None else find_ffprobe()
    if not exe:
        if run is None:
            _unlink_master(out_mp4)
            raise RuntimeError("ffprobe required to validate the stitched master")
        exe = "ffprobe"
    dur = probe_seconds(out_mp4, ffprobe=exe, run=run)
    if dur is None:
        _unlink_master(out_mp4)
        raise RuntimeError(f"concat duration unreadable ({out_mp4})")
    clip_tol = max(MASTER_TOL_S, 0.05 * int(n_stems))
    cap = float(cap_seconds)
    if dur < probed_sum - clip_tol or dur > probed_sum + clip_tol:
        _unlink_master(out_mp4)
        raise RuntimeError(
            f"clip concat duration {dur}s off sum {probed_sum}s "
            f"(need +/-{clip_tol})"
        )
    if dur > cap + MASTER_TOL_S:
        _unlink_master(out_mp4)
        raise RuntimeError(f"clip concat duration {dur}s exceeds cap {cap}s")
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


def _run_ffmpeg(argv: list[str], runner: FfmpegRunner) -> None:
    """Run one ffmpeg argv; raise RuntimeError on non-zero.

    Args:
        argv: ffmpeg argument vector.
        runner: ``subprocess.run`` or a test double.
    """
    log(" ".join(argv))
    proc = runner(argv, check=False, capture_output=True, text=True)
    if getattr(proc, "returncode", 1) != 0:
        err = getattr(proc, "stderr", "") or getattr(proc, "stdout", "") or ""
        raise RuntimeError(f"ffmpeg stitch failed: {err.strip() or 'exit 1'}")


def _run_with_x264_fallback(
    playable: list[str], fallback: list[str], runner: FfmpegRunner
) -> None:
    """Run playable argv; retry fallback when libx264 is missing.

    Args:
        playable: Preferred libx264 argv.
        fallback: Stream-copy argv used when libx264 is missing.
        runner: ``subprocess.run`` or a test double.
    """
    try:
        _run_ffmpeg(playable, runner)
    except RuntimeError as exc:
        if not encoder_missing(str(exc)):
            raise
        log("libx264 missing; falling back to stream-copy + faststart")
        _run_ffmpeg(fallback, runner)


class ConcatPipeline:
    """Stitch N shot MP4s behind the :func:`stitch_film` façade."""

    def __init__(
        self,
        shot_paths: list[str],
        out_mp4: str,
        cap_seconds: float,
        *,
        ffmpeg: str | None = None,
        ffprobe: str | None = None,
        run: FfmpegRunner | None = None,
        xfade_cs: int = 0,
        expected_count: int | None = None,
    ) -> None:
        """Store stitch arguments.

        Args:
            shot_paths: MP4 paths in beat/shot order.
            out_mp4: Destination path.
            cap_seconds: Publish cap (default 90).
            ffmpeg: Override ffmpeg path.
            ffprobe: Override ffprobe path.
            run: Override ``subprocess.run`` (tests).
            xfade_cs: Audio acrossfade in centiseconds; 0 disables.
            expected_count: Required stem count (default 18).
        """
        self._shots = shot_paths
        self._out = out_mp4
        self._cap = cap_seconds
        self._ffmpeg_override = ffmpeg
        self._ffprobe = ffprobe
        self._run = run
        self._xfade_cs = xfade_cs
        self._expected = expected_count

    def run(self) -> str:
        """Normalize, validate, encode, and gate the master.

        Returns:
            ``out_mp4``.
        Raises:
            ValueError: wrong shot count or invalid xfade_cs.
            RuntimeError: ffmpeg missing/fails, missing/short stems, or duration off cap.
        """
        count = self._shot_count()
        self._require_count(count)
        self._reject_images()
        self._require_xfade_range()
        exe = self._ffmpeg()
        work_paths, pad_tmps = self._normalize(exe)
        try:
            self._validate(work_paths, count)
            self._encode(work_paths, exe)
        finally:
            self._unlink_temps(pad_tmps)
        self._assert_master()
        return self._out

    def _shot_count(self) -> int:
        """Required stem count (18 unless overridden).

        Returns:
            Expected number of shots.
        """
        if self._expected is None:
            return SHOT_COUNT
        return int(self._expected)

    def _require_count(self, count: int) -> None:
        """Refuse a short or long stem list.

        Args:
            count: Required stem count.
        Raises:
            ValueError: ``len(shot_paths)`` is not ``count``.
        """
        if len(self._shots) != count:
            raise ValueError(f"expected {count} shots, found {len(self._shots)}")

    def _reject_images(self) -> None:
        """Refuse VHS metadata PNGs in the stem list.

        Raises:
            RuntimeError: a path has an image suffix.
        """
        for path in self._shots:
            if _is_image_path(path):
                raise RuntimeError(
                    f"shot is an image, not an MP4 ({path}); "
                    "VHS_FILENAMES first file is a metadata PNG - use the muxed *-audio.mp4"
                )

    def _require_xfade_range(self) -> None:
        """Refuse xfade outside 0-50 centiseconds.

        Raises:
            ValueError: ``xfade_cs`` is out of range.
        """
        if self._xfade_cs < 0 or self._xfade_cs > 50:
            raise ValueError(f"xfade_cs must be 0-50, got {self._xfade_cs}")

    def _ffmpeg(self) -> str:
        """Resolve ffmpeg (override, else PATH / imageio).

        Returns:
            Executable path.
        """
        return self._ffmpeg_override or find_ffmpeg()

    def _runner(self) -> FfmpegRunner:
        """Injected runner, else ``subprocess.run``.

        Returns:
            Callable matching :class:`~ez_film.protocols.FfmpegRun`.
        """
        if self._run is not None:
            return self._run
        return subprocess.run

    def _normalize(self, ffmpeg: str) -> tuple[list[str], list[str]]:
        """Pad 113-frame LTX neighbors.

        Args:
            ffmpeg: ffmpeg executable.

        Returns:
            ``(paths, temps_to_unlink)``.
        """
        return normalize_stitch_stems(
            self._shots, ffmpeg=ffmpeg, ffprobe=self._ffprobe, run=self._run
        )

    def _validate(self, work_paths: list[str], count: int) -> None:
        """Refuse missing, unreadable, short, or silent stems.

        Args:
            work_paths: Normalized MP4 paths.
            count: Required stem count.
        """
        validate_stitch_stems(
            work_paths, ffprobe=self._ffprobe, run=self._run, expected_count=count
        )

    def _progress(self, n_shots: int) -> ProgressReporter | None:
        """Log the stitch and return a two-step bar when ez_common loads.

        Args:
            n_shots: Stem count being stitched.

        Returns:
            Progress bar, or None in hermetic tests.
        """
        log(f"stitching {n_shots} shots -> {self._out}")
        try:
            root = str(Path(__file__).resolve().parent.parent)
            if root not in sys.path:
                sys.path.insert(0, root)
            from ez_common import node_log, node_progress

            node_log("ez_film", f"stitching {n_shots} shots")
            return node_progress(2)
        except Exception:  # noqa: BLE001 - pytest / missing pack
            return None

    def _write_concat_list(self, work_paths: list[str]) -> str:
        """Write a concat-demuxer list file.

        Args:
            work_paths: Normalized MP4 paths.

        Returns:
            List-file path (caller unlinks).
        """
        list_file = tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".txt", delete=False
        )
        for path in work_paths:
            list_file.write(concat_list_line(path) + "\n")
        list_file.close()
        return list_file.name

    def _encode(self, work_paths: list[str], ffmpeg: str) -> None:
        """Hard-cut or xfade-remux into ``out_mp4``.

        Args:
            work_paths: Normalized MP4 paths.
            ffmpeg: ffmpeg executable.
        """
        bar = self._progress(len(work_paths))
        runner = self._runner()
        list_path = self._write_concat_list(work_paths)
        video_tmp = ""
        audio_tmp = ""
        try:
            if self._xfade_cs == 0:
                self._encode_hardcut(list_path, ffmpeg, runner, bar)
            else:
                video_tmp, audio_tmp = self._encode_xfade(
                    work_paths, list_path, ffmpeg, runner, bar
                )
        finally:
            Path(list_path).unlink(missing_ok=True)
            if video_tmp:
                Path(video_tmp).unlink(missing_ok=True)
            if audio_tmp:
                Path(audio_tmp).unlink(missing_ok=True)

    def _encode_hardcut(
        self,
        list_path: str,
        ffmpeg: str,
        runner: FfmpegRunner,
        bar: ProgressReporter | None,
    ) -> None:
        """Concat-demuxer H.264+AAC, with stream-copy fallback.

        Args:
            list_path: Concat demuxer list file.
            ffmpeg: ffmpeg executable.
            runner: ``subprocess.run`` or a test double.
            bar: Optional two-step progress bar.
        """
        _run_with_x264_fallback(
            ffmpeg_stitch_argv(list_path, self._out, self._cap, ffmpeg),
            ffmpeg_stitch_copy_argv(list_path, self._out, self._cap, ffmpeg),
            runner,
        )
        if bar is not None:
            bar.update(2)

    def _require_xfade_audio(self, work_paths: list[str]) -> None:
        """Refuse xfade when any stem is silent.

        Args:
            work_paths: Normalized MP4 paths.
        Raises:
            RuntimeError: a stem has no audio stream.
        """
        for path in work_paths:
            if not probe_has_audio(path, ffprobe=self._ffprobe, run=self._run):
                raise RuntimeError(
                    f"xfade requires audio on every shot (missing on {path}); "
                    "Wan-silent concat cannot use --xfade"
                )

    def _encode_xfade(
        self,
        work_paths: list[str],
        list_path: str,
        ffmpeg: str,
        runner: FfmpegRunner,
        bar: ProgressReporter | None,
    ) -> tuple[str, str]:
        """Picture-aligned audio acrossfade remux (video / audio / mux).

        Args:
            work_paths: Normalized MP4 paths.
            list_path: Concat demuxer list file.
            ffmpeg: ffmpeg executable.
            runner: ``subprocess.run`` or a test double.
            bar: Optional two-step progress bar.

        Returns:
            ``(video_tmp, audio_tmp)`` paths for the caller to unlink.
        """
        self._require_xfade_audio(work_paths)
        duration_s = self._xfade_cs / 100.0
        video_tmp = list_path + ".v.mp4"
        audio_tmp = list_path + ".a.m4a"
        _run_with_x264_fallback(
            ffmpeg_video_copy_argv(list_path, video_tmp, self._cap, ffmpeg),
            ffmpeg_video_streamcopy_argv(list_path, video_tmp, self._cap, ffmpeg),
            runner,
        )
        _run_ffmpeg(
            ffmpeg_audio_acrossfade_argv(
                work_paths,
                audio_tmp,
                ffmpeg,
                duration_s,
                cap_seconds=self._cap,
            ),
            runner,
        )
        _run_ffmpeg(
            ffmpeg_mux_copy_argv(video_tmp, audio_tmp, self._out, self._cap, ffmpeg),
            runner,
        )
        if bar is not None:
            bar.update(2)
        hz = probe_audio_hz(self._out, ffprobe=self._ffprobe, run=self._run)
        if hz is not None and hz != int(AAC_RATE):
            raise RuntimeError(f"concat audio is {hz} Hz, expected {AAC_RATE}")
        return video_tmp, audio_tmp

    def _unlink_temps(self, paths: list[str]) -> None:
        """Best-effort delete pad temps.

        Args:
            paths: Temp MP4 paths.
        """
        for tmp in paths:
            Path(tmp).unlink(missing_ok=True)

    def _assert_master(self) -> None:
        """Fail closed if the stitched master is off cap or out of A/V sync."""
        assert_master_duration(
            self._out, self._cap, ffprobe=self._ffprobe, run=self._run
        )


def stitch_film(
    shot_paths: list[str],
    out_mp4: str,
    cap_seconds: float = DEFAULT_CAP_SECONDS,
    *,
    ffmpeg: str | None = None,
    ffprobe: str | None = None,
    run: FfmpegRunner | None = None,
    xfade_cs: int = 0,
    expected_count: int | None = None,
) -> str:
    """Concat N shot MP4s, cap duration, fail closed on short or long masters.

    Default (``xfade_cs=0``) is concat-demuxer + libx264 CRF 18 + AAC +
    ``+faststart`` so browsers can play and download the master. ``xfade_cs``
    is centiseconds of **audio** acrossfade (10 = 0.10 s) with overlap off
    (``o=0``) so duration stays on the hard-cut picture. Wan-silent shots
    have no audio - xfade refuses. If ffmpeg lacks libx264, fall back to
    ``-c:v copy`` with faststart still set.

    Every stem must exist, last 5.00 +/- 0.05s, be 1280x704, and carry audio.
    Illegal LTX ``length=120`` files (113 frames / 4.708s) are padded to
    5.00s (cloned last frame) before the duration gate. After stitch the
    master must be ``cap +/- 0.10`` s with audio within 50 ms of picture. A
    failed master is deleted so a short stem list cannot publish.

    Args:
        shot_paths: MP4 paths in beat/shot order (not VHS metadata PNGs).
        out_mp4: Destination path.
        cap_seconds: Publish cap (default 90).
        ffmpeg: Override ffmpeg path.
        ffprobe: Override ffprobe path.
        run: Override ``subprocess.run`` (tests).
        xfade_cs: Audio acrossfade in centiseconds (overlap off); 0 disables.
        expected_count: Required stem count (default 18 for 90s one-click).
    Returns:
        ``out_mp4``.
    Raises:
        ValueError: wrong shot count or invalid xfade_cs.
        RuntimeError: ffmpeg missing/fails, missing/short stems, or duration off cap.
    """
    return ConcatPipeline(
        shot_paths,
        out_mp4,
        cap_seconds,
        ffmpeg=ffmpeg,
        ffprobe=ffprobe,
        run=run,
        xfade_cs=xfade_cs,
        expected_count=expected_count,
    ).run()


class ClipConcatPipeline:
    """Stitch N clip MP4s behind the :func:`stitch_clips` façade."""

    def __init__(
        self,
        clip_paths: list[str],
        out_mp4: str,
        cap_seconds: float,
        *,
        ffmpeg: str | None = None,
        ffprobe: str | None = None,
        run: FfmpegRunner | None = None,
        xfade_cs: int = 0,
    ) -> None:
        """Store clip-stitch arguments.

        Args:
            clip_paths: MP4 paths in beat order.
            out_mp4: Destination path.
            cap_seconds: Publish ceiling (default 600).
            ffmpeg: Override ffmpeg path.
            ffprobe: Override ffprobe path.
            run: Override ``subprocess.run`` (tests).
            xfade_cs: Must be 0 in v1 (hard cut).
        """
        self._clips = clip_paths
        self._out = out_mp4
        self._cap = cap_seconds
        self._ffmpeg_override = ffmpeg
        self._ffprobe = ffprobe
        self._run = run
        self._xfade_cs = xfade_cs

    def run(self) -> str:
        """Validate stems, encode without ``-t`` / ``apad``, and gate the master.

        Returns:
            ``out_mp4``.
        Raises:
            ValueError: stem count outside 1-24.
            RuntimeError: xfade, missing stems, duration-head miss, or ffmpeg.
        """
        self._require_count()
        self._require_hardcut()
        self._reject_images()
        exe = self._ffmpeg()
        probed_sum = self._validate()
        self._encode(exe)
        assert_clip_master_duration(
            self._out,
            probed_sum,
            self._cap,
            len(self._clips),
            ffprobe=self._ffprobe,
            run=self._run,
        )
        return self._out

    def _require_count(self) -> None:
        """Refuse an empty or over-long stem list.

        Raises:
            ValueError: ``len(clip_paths)`` is not in 1-24.
        """
        count = len(self._clips)
        if count < 1 or count > CLIP_COUNT_MAX:
            raise ValueError(f"expected 1-{CLIP_COUNT_MAX} clips, found {count}")

    def _require_hardcut(self) -> None:
        """Refuse clip audio acrossfade in v1.

        Raises:
            RuntimeError: ``xfade_cs`` is not 0.
        """
        if int(self._xfade_cs) != 0:
            raise RuntimeError(
                "clip xfade not in v1; use xfade_cs=0 (hard cut)"
            )

    def _reject_images(self) -> None:
        """Refuse VHS metadata PNGs in the stem list.

        Raises:
            RuntimeError: a path has an image suffix.
        """
        for path in self._clips:
            if _is_image_path(path):
                raise RuntimeError(
                    f"clip is an image, not an MP4 ({path}); "
                    "VHS_FILENAMES first file is a metadata PNG - use the muxed *-audio.mp4"
                )

    def _ffmpeg(self) -> str:
        """Resolve ffmpeg (override, else PATH / imageio).

        Returns:
            Executable path.
        """
        return self._ffmpeg_override or find_ffmpeg()

    def _runner(self) -> FfmpegRunner:
        """Injected runner, else ``subprocess.run``.

        Returns:
            Callable matching :class:`~ez_film.protocols.FfmpegRun`.
        """
        if self._run is not None:
            return self._run
        return subprocess.run

    def _ffprobe_exe(self) -> str:
        """Resolve ffprobe for stem probes.

        Returns:
            Executable path or a dummy when tests inject ``run``.
        Raises:
            RuntimeError: no ffprobe and no injected runner.
        """
        exe = self._ffprobe if self._ffprobe is not None else find_ffprobe()
        if exe:
            return exe
        if self._run is None:
            raise RuntimeError("ffprobe required to validate clips")
        return "ffprobe"

    def _validate(self) -> float:
        """Probe duration, size, and audio; refuse over-cap before ffmpeg.

        Returns:
            Sum of probed stem durations.
        Raises:
            RuntimeError: missing, unreadable, off-contract, or over-cap stems.
        """
        exe = self._ffprobe_exe()
        durations: list[float] = []
        first_wh: tuple[int, int] | None = None
        for path in self._clips:
            if not path or not str(path).strip():
                raise RuntimeError("missing clip file")
            file_path = Path(path)
            if not file_path.is_file():
                raise RuntimeError(f"unreadable clip ({path})")
            if file_path.stat().st_size < 1:
                raise RuntimeError(f"empty clip ({path})")
            dur = probe_seconds(path, ffprobe=exe, run=self._run)
            if dur is None or not any(
                abs(float(dur) - allowed) <= DURATION_TOL
                for allowed in DURATION_HEAD_S
            ):
                raise RuntimeError(
                    f"clip duration {dur}s is not in {CLIP_DURATION_HEAD_LABEL} ({path})"
                )
            durations.append(float(dur))
            wh = probe_wh(path, ffprobe=exe, run=self._run)
            if first_wh is None:
                first_wh = wh
            if first_wh is None or wh != first_wh:
                raise RuntimeError(
                    f"clip size mismatch {wh} vs first stem {first_wh} ({path})"
                )
            if not probe_has_audio(path, ffprobe=exe, run=self._run):
                raise RuntimeError(f"clip missing audio ({path})")
        probed_sum = sum(durations)
        if probed_sum > float(self._cap) + MASTER_TOL_S:
            raise RuntimeError(
                f"clip concat duration {probed_sum}s exceeds cap {float(self._cap)}s"
            )
        return probed_sum

    def _progress(self, n_clips: int) -> ProgressReporter | None:
        """Log the stitch and return a two-step bar when ez_common loads.

        Args:
            n_clips: Stem count being stitched.

        Returns:
            Progress bar, or None in hermetic tests.
        """
        log(f"stitching {n_clips} clips -> {self._out}")
        try:
            root = str(Path(__file__).resolve().parent.parent)
            if root not in sys.path:
                sys.path.insert(0, root)
            from ez_common import node_log, node_progress

            node_log("ez_film", f"stitching {n_clips} clips")
            return node_progress(2)
        except Exception:  # noqa: BLE001 - pytest / missing pack
            return None

    def _write_concat_list(self, work_paths: list[str]) -> str:
        """Write a concat-demuxer list file.

        Args:
            work_paths: Clip MP4 paths.

        Returns:
            List-file path (caller unlinks).
        """
        list_file = tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix=".txt", delete=False
        )
        for path in work_paths:
            list_file.write(concat_list_line(path) + "\n")
        list_file.close()
        return list_file.name

    def _encode(self, ffmpeg: str) -> None:
        """Concat-demuxer H.264+AAC, with stream-copy fallback.

        Args:
            ffmpeg: ffmpeg executable.
        """
        bar = self._progress(len(self._clips))
        runner = self._runner()
        list_path = self._write_concat_list(self._clips)
        try:
            _run_with_x264_fallback(
                ffmpeg_clip_stitch_argv(list_path, self._out, ffmpeg),
                ffmpeg_clip_stitch_copy_argv(list_path, self._out, ffmpeg),
                runner,
            )
            if bar is not None:
                bar.update(2)
        finally:
            Path(list_path).unlink(missing_ok=True)


def stitch_clips(
    clip_paths: list[str],
    out_mp4: str,
    cap_seconds: float = CLIP_CAP_DEFAULT_S,
    *,
    ffmpeg: str | None = None,
    ffprobe: str | None = None,
    run: FfmpegRunner | None = None,
    xfade_cs: int = 0,
) -> str:
    """Concat N clip MP4s. Cap is a ceiling. Master ~ sum(stems).

    Raises if ``xfade_cs != 0`` (v1 hard-cut). Does not call film stitch
    helpers that pad or cut to cap.

    Args:
        clip_paths: MP4 paths in beat order (not VHS metadata PNGs).
        out_mp4: Destination path.
        cap_seconds: Publish ceiling (default 600).
        ffmpeg: Override ffmpeg path.
        ffprobe: Override ffprobe path.
        run: Override ``subprocess.run`` (tests).
        xfade_cs: Must be 0 in v1.
    Returns:
        ``out_mp4``.
    Raises:
        ValueError: stem count outside 1-24.
        RuntimeError: ffmpeg missing/fails, missing stems, or duration off sum.
    """
    return ClipConcatPipeline(
        clip_paths,
        out_mp4,
        cap_seconds,
        ffmpeg=ffmpeg,
        ffprobe=ffprobe,
        run=run,
        xfade_cs=xfade_cs,
    ).run()


def publish_path(
    film: str,
    output_dir: Path | None = None,
    *,
    act: int = 0,
) -> Path:
    """Published master path under the output directory.

    90s films write ``ez_{slug}_90s.mp4``. Five-act films write
    ``ez_{slug}_450s.mp4`` for the whole film, or
    ``ez_{slug}_actN_90s.mp4`` when ``act`` is 1-5.

    Args:
        film: Film id.
        output_dir: Override output directory.
        act: 1-based act index; 0 means the film master.
    Returns:
        Destination path.
    """
    dest = output_dir if output_dir is not None else output_directory()
    return dest / master_filename(film, act=act)
