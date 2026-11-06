"""EDL handoff payload and ffmpeg argv builder for the editing lane.

Pure text building: no subprocess, no filesystem, no ``timeline`` import (the
reducer owns project mutation). ``render_server`` resolves and vets clip
sources against the Comfy output root, then calls :func:`ffmpeg_command`.

Text planes are client-mode only: overlay and caption records (see
:class:`~ez_edit.protocol.Overlay` / :class:`~ez_edit.protocol.Caption`) are
drawn by the browser panel on its canvas before the WebCodecs encode. A
server render therefore composites video tracks, transitions, and per-clip
audio gain only, and a project that carries overlays or captions still
renders its picture and audio correctly.

Track semantics: track 0 is the base plane, listed in timeline order, joined
by ``xfade`` (``fade`` / ``wipeleft``) or hard ``concat``. A clip on a higher
track is composited above the plane below it with ``overlay`` at ``x``/``y``
fractions of the frame, starting at the base time where the last track-0 clip
listed before it begins (the reducer appends B-roll after the clip it covers).
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import NamedTuple, TypedDict, get_args

from .protocol import TransitionKind

SAMPLE_RATE = 48000
"""Audio sample rate every clip is resampled to before mixing."""

AUDIO_LAYOUT = "stereo"
"""Channel layout every clip is normalized to before mixing."""

XFADE_TRANSITIONS: dict[str, str] = {"fade": "fade", "wipe": "wipeleft"}
"""Timeline transition kind -> ffmpeg ``xfade`` transition name."""

TRANSITION_KINDS: tuple[TransitionKind, ...] = get_args(TransitionKind)
"""Runtime vocabulary taken from :data:`~ez_edit.protocol.TransitionKind`."""

OUTPUT_ARGS: tuple[str, ...] = (
    "-c:v",
    "libx264",
    "-pix_fmt",
    "yuv420p",
    "-c:a",
    "aac",
    "-movflags",
    "+faststart",
)
"""Fixed MP4 encode tail: libx264, yuv420p, AAC, faststart."""


class EdlError(ValueError):
    """Refusal for a project that cannot render (bad shapes, bad trims)."""


class EdlTransition(TypedDict):
    """Transition block written into one EDL clip row."""

    kind: str
    """``fade`` or ``wipe`` (``cut`` clips carry no transition block)."""

    duration_s: float
    """Overlap seconds the editor should apply."""


class EdlClip(TypedDict):
    """One clip row of the EDL handoff document, in project order."""

    id: str
    """Clip id."""

    label: str
    """Human label."""

    source: str
    """Source path under the Comfy output dir."""

    in_s: float
    """Source in-point seconds."""

    out_s: float
    """Source out-point seconds."""

    duration_s: float
    """Timeline length this clip occupies."""

    track: int
    """Video track index (0 = base plane)."""

    gain: float
    """Audio gain multiplier."""

    timeline_start_s: float
    """Where the clip lands on the rendered timeline."""

    transition: EdlTransition | None
    """Transition entering this clip, or ``None`` for a hard cut."""


class EdlDocument(TypedDict):
    """The EDL handoff document a Kdenlive/Shotcut or client render reads."""

    version: int
    """Document version (always 1 today)."""

    id: str
    """Project id."""

    title: str
    """Project title."""

    fps: float
    """Project frame rate."""

    width: int
    """Project frame width."""

    height: int
    """Project frame height."""

    duration_s: float
    """Base-plane length in seconds."""

    clips: list[EdlClip]
    """Clip rows in project order."""

    overlays: list[dict[str, object]]
    """Text/image overlay records the browser draws (client mode only)."""

    captions: list[dict[str, object]]
    """Caption records the browser draws (client mode only)."""

    client_only: list[str]
    """Fields a server render ignores, so an editor can flag them."""


class _Clip(NamedTuple):
    """One validated clip plus its derived timeline facts."""

    order: int
    """Index in the project ``clips`` list (also the ffmpeg input index)."""
    cid: str
    """Clip id."""
    label: str
    """Human label."""
    source: str
    """Media path (caller-resolved)."""
    in_s: float
    """Source in-point."""
    out_s: float
    """Source out-point."""
    track: int
    """Video track index (0 = base plane)."""
    gain: float
    """Audio gain multiplier."""
    x: float
    """Overlay left position, 0..1 of frame width."""
    y: float
    """Overlay top position, 0..1 of frame height."""
    kind: str
    """Transition entering this clip (``cut`` / ``fade`` / ``wipe``)."""
    trans_s: float
    """Transition overlap seconds (0.0 for ``cut``)."""

    @property
    def duration(self) -> float:
        """Timeline length this clip occupies.

        Returns:
            ``out_s - in_s`` seconds.
        """
        return self.out_s - self.in_s


class _Model(NamedTuple):
    """Validated project, shared by both public builders."""

    clips: list[_Clip]
    """Every clip, in project order."""
    overlays: list[dict[str, object]]
    """Text/image overlay records (client-mode planes; handoff only)."""
    captions: list[dict[str, object]]
    """Caption records (client-mode planes; handoff only)."""
    fps: float
    """Project frame rate."""
    width: int
    """Project frame width."""
    height: int
    """Project frame height."""


def _fmt(value: float) -> str:
    """Render a number for argv with at most 3 decimals, no trailing zeros.

    Args:
        value: Seconds, rate, or gain.

    Returns:
        Plain decimal text (``2``, ``1.5``, ``0.375``).
    """
    number = float(value)
    if number == 0.0:
        return "0"
    text = f"{number:.3f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _as_float(raw: object, field: str) -> float:
    """Coerce a JSON number, refusing bool, non-numbers, and NaN/inf.

    Args:
        raw: Value from the project record.
        field: Label used in the refusal message.

    Returns:
        Finite float.

    Raises:
        EdlError: Not a finite number.
    """
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise EdlError(f"{field} must be a number")
    value = float(raw)
    if not math.isfinite(value):
        raise EdlError(f"{field} must be finite")
    return value


def _as_int(raw: object, field: str) -> int:
    """Coerce a JSON integer, refusing bool and float.

    Args:
        raw: Value from the project record.
        field: Label used in the refusal message.

    Returns:
        Integer value.

    Raises:
        EdlError: Not an integer.
    """
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise EdlError(f"{field} must be an integer")
    return int(raw)


def _place(value: float, field: str) -> float:
    """Validate a 0..1 placement fraction.

    Args:
        value: Fraction of the frame.
        field: Label used in the refusal message.

    Returns:
        The fraction unchanged.

    Raises:
        EdlError: Outside 0..1.
    """
    if value < 0.0 or value > 1.0:
        raise EdlError(f"{field} must be within 0..1")
    return value


def _validated_transition(order: int, raw: object) -> tuple[str, float]:
    """Normalize the transition entering one clip.

    Args:
        order: Clip index (for messages).
        raw: Transition record or ``None``.

    Returns:
        ``(kind, duration_s)`` with ``("cut", 0.0)`` for no transition.

    Raises:
        EdlError: Bad shape, unknown kind, or a fade/wipe without duration.
    """
    if raw is None:
        return ("cut", 0.0)
    if not isinstance(raw, Mapping):
        raise EdlError(f"clip {order} transition must be a mapping")
    kind = str(raw.get("kind") or "cut")
    if kind not in TRANSITION_KINDS:
        raise EdlError(f"clip {order} transition kind {kind!r} is unknown")
    if kind == "cut":
        return ("cut", 0.0)
    duration = _as_float(
        raw.get("duration_s", 0.0), f"clip {order} transition duration_s"
    )
    if duration <= 0.0:
        raise EdlError(f"clip {order} transition {kind} needs duration_s > 0")
    return (kind, duration)


def _validated_clip(order: int, raw: object) -> _Clip:
    """Validate one clip record.

    Args:
        order: Index in the project list (also the ffmpeg input index).
        raw: Clip record.

    Returns:
        Validated clip.

    Raises:
        EdlError: Bad shape, missing source, or bad trim/track/gain/placement.
    """
    if not isinstance(raw, Mapping):
        raise EdlError(f"clip {order} must be a mapping")
    source = str(raw.get("source") or "").strip()
    if not source:
        raise EdlError(f"clip {order} has no source")
    in_s = _as_float(raw.get("in_s", 0.0), f"clip {order} in_s")
    out_s = _as_float(raw.get("out_s"), f"clip {order} out_s")
    if in_s < 0.0:
        raise EdlError(f"clip {order} in_s must be >= 0")
    if out_s <= in_s:
        raise EdlError(f"clip {order} out_s must exceed in_s")
    track = _as_int(raw.get("track", 0), f"clip {order} track")
    if track < 0:
        raise EdlError(f"clip {order} track must be >= 0")
    gain = _as_float(raw.get("gain", 1.0), f"clip {order} gain")
    if gain < 0.0:
        raise EdlError(f"clip {order} gain must be >= 0")
    x = _place(_as_float(raw.get("x", 0.0), f"clip {order} x"), f"clip {order} x")
    y = _place(_as_float(raw.get("y", 0.0), f"clip {order} y"), f"clip {order} y")
    kind, trans_s = _validated_transition(order, raw.get("transition"))
    return _Clip(
        order=order,
        cid=str(raw.get("id") or f"clip-{order}"),
        label=str(raw.get("label") or ""),
        source=source,
        in_s=in_s,
        out_s=out_s,
        track=track,
        gain=gain,
        x=x,
        y=y,
        kind=kind,
        trans_s=trans_s,
    )


def _record_list(raw: object, field: str) -> list[dict[str, object]]:
    """Copy a text-plane list (``overlays`` / ``captions``).

    Args:
        raw: Value from the project record.
        field: Label used in the refusal message.

    Returns:
        Copied records (empty when the field is missing).

    Raises:
        EdlError: Not a list, or an entry is not a mapping.
    """
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise EdlError(f"project {field} must be a list")
    for item in raw:
        if not isinstance(item, Mapping):
            raise EdlError(f"project {field} entries must be mappings")
    return [dict(item) for item in raw]


def _prepare(project: object) -> _Model:
    """Validate the whole project once, for both builders.

    Args:
        project: Edit project record; anything that is not a mapping is
            refused.

    Returns:
        Validated model.

    Raises:
        EdlError: Shape, range, or transition-fit refusal.
    """
    if not isinstance(project, Mapping):
        raise EdlError("project must be a mapping")
    fps = _as_float(project.get("fps"), "project fps")
    if fps <= 0.0:
        raise EdlError("project fps must be > 0")
    width = _as_int(project.get("width"), "project width")
    height = _as_int(project.get("height"), "project height")
    if width <= 0 or height <= 0:
        raise EdlError("project width/height must be > 0")
    raw_clips = project.get("clips")
    if not isinstance(raw_clips, (list, tuple)):
        raise EdlError("project clips must be a list")
    if not raw_clips:
        raise EdlError("project has no clips")
    clips = [_validated_clip(order, raw) for order, raw in enumerate(raw_clips)]
    return _Model(
        clips=clips,
        overlays=_record_list(project.get("overlays"), "overlays"),
        captions=_record_list(project.get("captions"), "captions"),
        fps=fps,
        width=width,
        height=height,
    )


def _base_plan(base: Sequence[_Clip]) -> tuple[list[tuple[_Clip, float]], float]:
    """Lay the track-0 clips end to end, overlapping transitions.

    Args:
        base: Track-0 clips in timeline order.

    Returns:
        ``[(clip, start_s), ...]`` and the total base duration.

    Raises:
        EdlError: A transition is longer than a neighbouring clip.
    """
    placed: list[tuple[_Clip, float]] = []
    cursor = 0.0
    for pos, clip in enumerate(base):
        start = cursor
        if pos > 0 and clip.kind != "cut":
            previous = base[pos - 1]
            if clip.trans_s >= min(previous.duration, clip.duration):
                raise EdlError(
                    f"clip {clip.order} transition {clip.trans_s}s does not fit "
                    f"{previous.duration}s / {clip.duration}s clips"
                )
            start = cursor - clip.trans_s
        placed.append((clip, start))
        cursor = start + clip.duration
    return placed, cursor


def _starts_by_order(placed: Sequence[tuple[_Clip, float]]) -> dict[int, float]:
    """Map base clip input index to its timeline start.

    Args:
        placed: Output of :func:`_base_plan`.

    Returns:
        Input index -> base timeline start seconds.
    """
    return {clip.order: start for clip, start in placed}


def _overlay_offset(clip: _Clip, starts: Mapping[int, float]) -> float:
    """Base timeline offset a higher-track clip sits at.

    Args:
        clip: Higher-track clip.
        starts: Base starts from :func:`_starts_by_order`.

    Returns:
        Start seconds (0.0 when no base clip precedes it).
    """
    offset = 0.0
    for order, start in starts.items():
        if order < clip.order and start >= offset:
            offset = start
    return offset


def _video_filter(
    clip: _Clip, *, fps: float, width: int, height: int, offset: float = 0.0
) -> str:
    """One normalized video chain for a clip input.

    Args:
        clip: Validated clip.
        fps: Project frame rate.
        width: Project frame width.
        height: Project frame height.
        offset: Timeline shift for higher-track clips.

    Returns:
        ``[N:v]...[vN]`` filter chain.
    """
    pts = "PTS-STARTPTS" if offset <= 0.0 else f"PTS-STARTPTS+{_fmt(offset)}/TB"
    return (
        f"[{clip.order}:v]fps={_fmt(fps)},scale={width}:{height},setsar=1,"
        f"format=yuv420p,setpts={pts}[v{clip.order}]"
    )


def _audio_filter(clip: _Clip, *, offset: float = 0.0) -> str:
    """One normalized audio chain for a clip input, with the clip gain.

    Args:
        clip: Validated clip.
        offset: Timeline delay for higher-track clips.

    Returns:
        ``[N:a]...[aN]`` filter chain.
    """
    chain = (
        f"[{clip.order}:a]aresample={SAMPLE_RATE},"
        f"aformat=sample_fmts=fltp:channel_layouts={AUDIO_LAYOUT},"
        f"asetpts=PTS-STARTPTS,volume={_fmt(clip.gain)}"
    )
    if offset > 0.0:
        chain += f",adelay=delays={int(round(offset * 1000))}:all=1"
    return chain + f"[a{clip.order}]"


def _base_filters(placed: Sequence[tuple[_Clip, float]]) -> tuple[list[str], str, str]:
    """Join the base clips with concat / xfade chains.

    Args:
        placed: Output of :func:`_base_plan` (at least one clip).

    Returns:
        ``(filter chains, video label, audio label)`` for the base plane.
    """
    first = placed[0][0]
    if len(placed) == 1:
        return ([], f"v{first.order}", f"a{first.order}")
    chains: list[str] = []
    video = f"v{first.order}"
    audio = f"a{first.order}"
    cursor = placed[0][1] + first.duration
    for pos in range(1, len(placed)):
        clip, start = placed[pos]
        index = clip.order
        overlap = cursor - start
        if overlap > 0.0:
            vout, aout = f"x{pos}", f"ax{pos}"
            chains.append(
                f"[{video}][v{index}]xfade=transition={XFADE_TRANSITIONS[clip.kind]}"
                f":duration={_fmt(overlap)}:offset={_fmt(start)}[{vout}]"
            )
            chains.append(
                f"[{audio}][a{index}]acrossfade=d={_fmt(overlap)}:c1=tri:c2=tri[{aout}]"
            )
        else:
            vout, aout = f"c{pos}", f"ac{pos}"
            chains.append(f"[{video}][v{index}]concat=n=2:v=1:a=0[{vout}]")
            chains.append(f"[{audio}][a{index}]concat=n=2:v=0:a=1[{aout}]")
        video, audio = vout, aout
        cursor = start + clip.duration
    return (chains, video, audio)


def ffmpeg_command(
    project: Mapping[str, object],
    out_path: str | Path,
    *,
    ffmpeg_bin: str = "ffmpeg",
) -> list[str]:
    """Build the one ffmpeg argv that renders a project to mp4.

    Per-clip trim uses input-level ``-ss``/``-to``; tracks stack through a
    single ``filter_complex`` (base plane via concat/xfade, higher tracks via
    ``overlay`` at ``x``/``y`` of the frame); per-clip gain uses ``volume``.
    The tail writes libx264 / yuv420p / AAC with ``+faststart`` and cuts the
    mux to the base duration with ``-t``.

    Overlays and captions are not drawn here: text planes are client-mode
    only, so a project that has them still renders picture and audio.

    Args:
        project: Edit project record (validated here).
        out_path: Destination mp4 path.
        ffmpeg_bin: Executable to put at ``argv[0]``.

    Returns:
        Command vector.

    Raises:
        EdlError: The project cannot render (see :func:`_prepare`).
    """
    model = _prepare(project)
    base = [clip for clip in model.clips if clip.track == 0]
    if not base:
        raise EdlError("project has no track-0 clips to render")
    placed, total = _base_plan(base)
    starts = _starts_by_order(placed)
    upper = sorted(
        (clip for clip in model.clips if clip.track > 0),
        key=lambda clip: (clip.track, clip.order),
    )

    argv: list[str] = [ffmpeg_bin, "-y"]
    chains: list[str] = []
    for clip in model.clips:
        argv += ["-ss", _fmt(clip.in_s), "-to", _fmt(clip.out_s), "-i", clip.source]
        offset = _overlay_offset(clip, starts) if clip.track > 0 else 0.0
        chains.append(
            _video_filter(
                clip,
                fps=model.fps,
                width=model.width,
                height=model.height,
                offset=offset,
            )
        )
        chains.append(_audio_filter(clip, offset=offset))

    base_chains, video, audio = _base_filters(placed)
    chains += base_chains
    audio_labels = [audio]
    for pos, clip in enumerate(upper, start=1):
        offset = _overlay_offset(clip, starts)
        mixed = f"o{pos}"
        chains.append(
            f"[{video}][v{clip.order}]overlay="
            f"x={int(round(clip.x * model.width))}:"
            f"y={int(round(clip.y * model.height))}:eof_action=pass[{mixed}]"
        )
        video = mixed
        audio_labels.append(f"a{clip.order}")
    if len(audio_labels) > 1:
        joined = "".join(f"[{label}]" for label in audio_labels)
        chains.append(
            f"{joined}amix=inputs={len(audio_labels)}:duration=longest:normalize=0"
            "[aout]"
        )
        audio = "aout"

    argv += [
        "-filter_complex",
        ";".join(chains),
        "-map",
        f"[{video}]",
        "-map",
        f"[{audio}]",
        *OUTPUT_ARGS,
        "-t",
        _fmt(total),
        str(out_path),
    ]
    return argv


def edl_payload(project: Mapping[str, object]) -> EdlDocument:
    """Build the EDL handoff dict (Kdenlive/Shotcut and client-render path).

    Args:
        project: Edit project record (validated here).

    Returns:
        Ordered clips with source/in/out/transition/gain plus the text planes
        (``overlays`` / ``captions``) the browser draws.

    Raises:
        EdlError: The project cannot render (see :func:`_prepare`).
    """
    model = _prepare(project)
    base = [clip for clip in model.clips if clip.track == 0]
    placed, total = _base_plan(base) if base else ([], 0.0)
    starts = _starts_by_order(placed)
    clips: list[EdlClip] = []
    for clip in model.clips:
        start = (
            starts[clip.order]
            if clip.track == 0
            else _overlay_offset(clip, starts)
        )
        clips.append(
            {
                "id": clip.cid,
                "label": clip.label,
                "source": clip.source,
                "in_s": clip.in_s,
                "out_s": clip.out_s,
                "duration_s": round(clip.duration, 3),
                "track": clip.track,
                "gain": clip.gain,
                "timeline_start_s": round(start, 3),
                "transition": (
                    None if clip.kind == "cut" else {"kind": clip.kind,
                                                     "duration_s": clip.trans_s}
                ),
            }
        )
    return {
        "version": 1,
        "id": str(project.get("id") or ""),
        "title": str(project.get("title") or ""),
        "fps": model.fps,
        "width": model.width,
        "height": model.height,
        "duration_s": round(total, 3),
        "clips": clips,
        "overlays": model.overlays,
        "captions": model.captions,
        "client_only": ["overlays", "captions"],
    }
