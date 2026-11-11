"""Hermetic tests for the ez_edit EDL builder (no subprocess, no filesystem).

Covers :mod:`ez_edit.edl`: golden ffmpeg argv vectors (single clip, xfade
fade/wipe, gain, multi-track overlay, mp4 tail), the EDL handoff payload, and
every ``EdlError`` refusal branch. Numbers are fixed; nothing is injected.
"""

from __future__ import annotations

from typing import Any

import pytest

from ez_edit.edl import (
    AUDIO_LAYOUT,
    OUTPUT_ARGS,
    SAMPLE_RATE,
    EdlError,
    cmx_edl,
    edl_payload,
    ffmpeg_command,
)

OUT = "/renders/out.mp4"
"""Fixed destination used in every golden argv."""


def _raw(value: object) -> Any:
    """Loosen one value's static type so tests can feed malformed records.

    Args:
        value: Value to hand to the builder as ``Any``.

    Returns:
        The same value.
    """
    return value


def _clip(clip_id: str = "a", **overrides: Any) -> dict[str, Any]:
    """Build a valid clip record with optional overrides.

    Args:
        clip_id: Clip id and source stem.
        **overrides: Fields to add or replace.

    Returns:
        Clip record.
    """
    clip: dict[str, Any] = {
        "id": clip_id,
        "source": f"clips/{clip_id}.mp4",
        "label": clip_id,
        "in_s": 0.0,
        "out_s": 2.0,
        "track": 0,
        "gain": 1.0,
        "transition": None,
    }
    clip.update(overrides)
    return clip


def _project(**overrides: Any) -> dict[str, Any]:
    """Build a valid project record with optional overrides.

    Args:
        **overrides: Fields to add or replace.

    Returns:
        Edit project record.
    """
    project: dict[str, Any] = {
        "id": "prj-1",
        "title": "Demo",
        "fps": 24.0,
        "width": 1280,
        "height": 704,
        "clips": [_clip("a")],
        "overlays": [],
        "captions": [],
    }
    project.update(overrides)
    return project


def _filter_of(argv: list[str]) -> str:
    """Return the ``filter_complex`` graph text from an argv.

    Args:
        argv: Command vector from :func:`ffmpeg_command`.

    Returns:
        Filter graph string.
    """
    return argv[argv.index("-filter_complex") + 1]


def _vchain(index: int, pts: str = "PTS-STARTPTS") -> str:
    """Expected normalized video chain text.

    Args:
        index: ffmpeg input index.
        pts: Expected ``setpts`` expression.

    Returns:
        Chain string.
    """
    return (
        f"[{index}:v]fps=24,scale=1280:704,setsar=1,format=yuv420p,"
        f"setpts={pts}[v{index}]"
    )


def _achain(index: int, gain: str = "1", delay: str = "") -> str:
    """Expected normalized audio chain text.

    Args:
        index: ffmpeg input index.
        gain: Expected ``volume`` argument.
        delay: Expected ``adelay`` argument, or ``""`` for none.

    Returns:
        Chain string.
    """
    chain = (
        f"[{index}:a]aresample={SAMPLE_RATE},"
        f"aformat=sample_fmts=fltp:channel_layouts={AUDIO_LAYOUT},"
        f"asetpts=PTS-STARTPTS,volume={gain}"
    )
    if delay:
        chain += f",adelay=delays={delay}:all=1"
    return chain + f"[a{index}]"


def _input_args(pairs: list[tuple[str, str, str]]) -> list[str]:
    """Expected ``-ss/-to/-i`` input block.

    Args:
        pairs: ``(in_s, out_s, source)`` triples per input.

    Returns:
        argv fragment.
    """
    argv: list[str] = []
    for in_s, out_s, source in pairs:
        argv += ["-ss", in_s, "-to", out_s, "-i", source]
    return argv


def test_single_clip_golden_argv() -> None:
    argv = ffmpeg_command(_project(), OUT)
    assert argv == [
        "ffmpeg",
        "-y",
        *_input_args([("0", "2", "clips/a.mp4")]),
        "-filter_complex",
        ";".join([_vchain(0), _achain(0)]),
        "-map",
        "[v0]",
        "-map",
        "[a0]",
        *OUTPUT_ARGS,
        "-t",
        "2",
        OUT,
    ]


def test_ffmpeg_bin_override_and_trim_formatting() -> None:
    project = _project(clips=[_clip("a", in_s=0.125, out_s=2.5, gain=1.25)])
    argv = ffmpeg_command(project, OUT, ffmpeg_bin="/usr/bin/ffmpeg")
    assert argv[0] == "/usr/bin/ffmpeg"
    assert argv[2:8] == ["-ss", "0.125", "-to", "2.5", "-i", "clips/a.mp4"]
    assert "volume=1.25" in _filter_of(argv)
    assert argv[-3:] == ["-t", "2.375", OUT]


def test_two_clips_fade_xfade_golden_argv() -> None:
    project = _project(
        clips=[
            _clip("a"),
            _clip("b", transition={"kind": "fade", "duration_s": 0.5}),
        ]
    )
    argv = ffmpeg_command(project, OUT)
    graph = ";".join(
        [
            _vchain(0),
            _achain(0),
            _vchain(1),
            _achain(1),
            "[v0][v1]xfade=transition=fade:duration=0.5:offset=1.5[x1]",
            "[a0][a1]acrossfade=d=0.5:c1=tri:c2=tri[ax1]",
        ]
    )
    assert argv == [
        "ffmpeg",
        "-y",
        *_input_args([("0", "2", "clips/a.mp4"), ("0", "2", "clips/b.mp4")]),
        "-filter_complex",
        graph,
        "-map",
        "[x1]",
        "-map",
        "[ax1]",
        *OUTPUT_ARGS,
        "-t",
        "3.5",
        OUT,
    ]


def test_two_clips_wipe_uses_wipeleft_transition() -> None:
    project = _project(
        clips=[
            _clip("a"),
            _clip("b", transition={"kind": "wipe", "duration_s": 0.25}),
        ]
    )
    graph = _filter_of(ffmpeg_command(project, OUT))
    assert "[v0][v1]xfade=transition=wipeleft:duration=0.25:offset=1.75[x1]" in graph
    assert "[a0][a1]acrossfade=d=0.25:c1=tri:c2=tri[ax1]" in graph


def test_two_clips_cut_uses_concat_chains() -> None:
    project = _project(clips=[_clip("a"), _clip("b")])
    graph = _filter_of(ffmpeg_command(project, OUT))
    assert "[v0][v1]concat=n=2:v=1:a=0[c1]" in graph
    assert "[a0][a1]concat=n=2:v=0:a=1[ac1]" in graph
    argv = ffmpeg_command(project, OUT)
    assert argv[argv.index("-map") + 1] == "[c1]"
    assert argv[-2] == "4"


def test_gain_volume_applied_per_clip() -> None:
    project = _project(clips=[_clip("a", gain=0.5), _clip("b", gain=0.0)])
    graph = _filter_of(ffmpeg_command(project, OUT))
    assert _achain(0, gain="0.5") in graph
    assert _achain(1, gain="0") in graph


def test_multi_track_overlay_golden_argv() -> None:
    project = _project(
        clips=[
            _clip("a", out_s=4.0),
            _clip("b"),
            _clip("c", in_s=1.0, out_s=2.0, track=1, x=0.5, y=0.25),
        ]
    )
    argv = ffmpeg_command(project, OUT)
    graph = ";".join(
        [
            _vchain(0),
            _achain(0),
            _vchain(1),
            _achain(1),
            _vchain(2, pts="PTS-STARTPTS+4/TB"),
            _achain(2, delay="4000"),
            "[v0][v1]concat=n=2:v=1:a=0[c1]",
            "[a0][a1]concat=n=2:v=0:a=1[ac1]",
            "[c1][v2]overlay=x=640:y=176:eof_action=pass[o1]",
            "[ac1][a2]amix=inputs=2:duration=longest:normalize=0[aout]",
        ]
    )
    assert argv == [
        "ffmpeg",
        "-y",
        *_input_args(
            [
                ("0", "4", "clips/a.mp4"),
                ("0", "2", "clips/b.mp4"),
                ("1", "2", "clips/c.mp4"),
            ]
        ),
        "-filter_complex",
        graph,
        "-map",
        "[o1]",
        "-map",
        "[aout]",
        *OUTPUT_ARGS,
        "-t",
        "6",
        OUT,
    ]


def test_output_tail_is_libx264_yuv420p_aac_faststart() -> None:
    argv = ffmpeg_command(_project(), OUT)
    tail = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-movflags", "+faststart"]
    assert list(OUTPUT_ARGS) == tail
    start = argv.index("-c:v")
    assert argv[start:-3] == tail
    assert argv[-3:] == ["-t", "2", OUT]


def test_upper_track_before_any_base_clip_offsets_at_zero() -> None:
    project = _project(clips=[_clip("u", track=1)])
    with pytest.raises(EdlError, match="no track-0 clips"):
        ffmpeg_command(project, OUT)
    payload = edl_payload(project)
    assert payload["duration_s"] == 0.0
    assert payload["clips"][0]["timeline_start_s"] == 0.0


def test_edl_payload_shape_and_client_only_planes() -> None:
    overlay = {"id": "o1", "kind": "text", "text": "hi"}
    caption = {"id": "c1", "text": "yo"}
    project = _project(
        clips=[
            _clip("a"),
            _clip("b", transition={"kind": "wipe", "duration_s": 0.5}),
        ],
        overlays=[overlay],
        captions=[caption],
    )
    payload = edl_payload(project)
    assert payload["version"] == 1
    assert payload["id"] == "prj-1"
    assert payload["title"] == "Demo"
    assert payload["fps"] == 24.0
    assert payload["width"] == 1280
    assert payload["height"] == 704
    assert payload["duration_s"] == 3.5
    assert payload["overlays"] == [overlay]
    assert payload["captions"] == [caption]
    assert payload["client_only"] == ["overlays", "captions"]
    assert payload["clips"] == [
        {
            "id": "a",
            "label": "a",
            "source": "clips/a.mp4",
            "in_s": 0.0,
            "out_s": 2.0,
            "duration_s": 2.0,
            "track": 0,
            "gain": 1.0,
            "timeline_start_s": 0.0,
            "transition": None,
        },
        {
            "id": "b",
            "label": "b",
            "source": "clips/b.mp4",
            "in_s": 0.0,
            "out_s": 2.0,
            "duration_s": 2.0,
            "track": 0,
            "gain": 1.0,
            "timeline_start_s": 1.5,
            "transition": {"kind": "wipe", "duration_s": 0.5},
        },
    ]


def test_edl_payload_defaults_missing_fields() -> None:
    project = _project(clips=[{"source": "s.mp4", "out_s": 1.0}])
    clip = edl_payload(project)["clips"][0]
    assert clip["id"] == "clip-0"
    assert clip["label"] == ""
    assert clip["in_s"] == 0.0
    assert clip["track"] == 0
    assert clip["gain"] == 1.0
    assert clip["duration_s"] == 1.0


def test_edl_payload_tolerates_transition_record_without_kind() -> None:
    project = _project(clips=[_clip("a"), _clip("b", transition={"junk": 1})])
    assert edl_payload(project)["clips"][1]["transition"] is None


def test_edl_payload_missing_planes_default_empty() -> None:
    project = _project()
    project.pop("overlays")
    project.pop("captions")
    payload = edl_payload(project)
    assert payload["overlays"] == []
    assert payload["captions"] == []


def _assert_refused(project: object, match: str) -> None:
    """Both builders must refuse a project with the same message.

    Args:
        project: Malformed project record (fed as ``Any``).
        match: Substring the ``EdlError`` message must contain.
    """
    with pytest.raises(EdlError, match=match):
        ffmpeg_command(_raw(project), OUT)
    with pytest.raises(EdlError, match=match):
        edl_payload(_raw(project))


def test_refuses_non_mapping_project_and_bad_geometry() -> None:
    _assert_refused(42, "project must be a mapping")
    _assert_refused(_project(fps=None), "project fps must be a number")
    _assert_refused(_project(fps="24"), "project fps must be a number")
    _assert_refused(_project(fps=True), "project fps must be a number")
    _assert_refused(_project(fps=float("nan")), "project fps must be finite")
    _assert_refused(_project(fps=0), "project fps must be > 0")
    _assert_refused(_project(width=None), "project width must be an integer")
    _assert_refused(_project(width=100.0), "project width must be an integer")
    _assert_refused(_project(width=True), "project width must be an integer")
    _assert_refused(_project(height="704"), "project height must be an integer")
    _assert_refused(_project(width=0), "width/height must be > 0")
    _assert_refused(_project(height=-2), "width/height must be > 0")


def test_refuses_bad_clip_container() -> None:
    _assert_refused(_project(clips="nope"), "project clips must be a list")
    _assert_refused(_project(clips=[]), "project has no clips")
    _assert_refused(_project(clips=[3]), "clip 0 must be a mapping")


def test_refuses_bad_source_and_trims() -> None:
    _assert_refused(_project(clips=[_clip("a", source="  ")]), "has no source")
    _assert_refused(_project(clips=[_clip("a", source=None)]), "has no source")
    _assert_refused(_project(clips=[_clip("a", in_s=-1.0)]), "in_s must be >= 0")
    _assert_refused(_project(clips=[_clip("a", in_s="x")]), "clip 0 in_s must be a number")
    _assert_refused(_project(clips=[_clip("a", in_s=True)]), "clip 0 in_s must be a number")
    _assert_refused(_project(clips=[_clip("a", out_s=0.0)]), "out_s must exceed in_s")
    _assert_refused(_project(clips=[{"id": "a", "source": "s"}]), "clip 0 out_s must be a number")


def test_refuses_bad_track_gain_and_placement() -> None:
    _assert_refused(_project(clips=[_clip("a", track=-1)]), "track must be >= 0")
    _assert_refused(_project(clips=[_clip("a", track=1.5)]), "track must be an integer")
    _assert_refused(_project(clips=[_clip("a", track=True)]), "track must be an integer")
    _assert_refused(_project(clips=[_clip("a", gain=-0.5)]), "gain must be >= 0")
    _assert_refused(_project(clips=[_clip("a", gain="loud")]), "clip 0 gain must be a number")
    _assert_refused(_project(clips=[_clip("a", x=1.5)]), "clip 0 x must be within 0..1")
    _assert_refused(_project(clips=[_clip("a", y=-0.1)]), "clip 0 y must be within 0..1")
    _assert_refused(_project(clips=[_clip("a", x="left")]), "clip 0 x must be a number")


def test_refuses_bad_transition_records() -> None:
    _assert_refused(_project(clips=[_clip("a"), _clip("b", transition="fade")]),
                    "clip 1 transition must be a mapping")
    _assert_refused(
        _project(clips=[_clip("a"), _clip("b", transition={"kind": "dissolve"})]),
        "transition kind 'dissolve' is unknown",
    )
    _assert_refused(
        _project(clips=[_clip("a"), _clip("b", transition={"kind": "fade"})]),
        "fade needs duration_s > 0",
    )
    _assert_refused(
        _project(
            clips=[_clip("a"), _clip("b", transition={"kind": "wipe", "duration_s": 0.0})]
        ),
        "wipe needs duration_s > 0",
    )
    _assert_refused(
        _project(
            clips=[
                _clip("a"),
                _clip("b", transition={"kind": "fade", "duration_s": "x"}),
            ]
        ),
        "clip 1 transition duration_s must be a number",
    )


def test_refuses_transition_longer_than_clips() -> None:
    project = _project(
        clips=[
            _clip("a"),
            _clip("b", transition={"kind": "fade", "duration_s": 2.0}),
        ]
    )
    _assert_refused(project, "transition 2.0s does not fit 2.0s / 2.0s clips")


def test_refuses_bad_text_plane_containers() -> None:
    _assert_refused(_project(overlays="oops"), "project overlays must be a list")
    _assert_refused(_project(captions=[3]), "project captions entries must be mappings")


# --- CMX 3600 handoff --------------------------------------------------------


def _cmx_project(**overrides: Any) -> dict[str, Any]:
    """Build a two-clip base-plane project with one roll title.

    Args:
        **overrides: Fields to add or replace on the project.

    Returns:
        Edit project record.
    """
    project = _project(
        clips=[
            _clip("a", label="A Roll", source="clips/a b.mp4"),
            _clip(
                "b",
                label="",
                in_s=1.0,
                out_s=4.0,
                transition={"kind": "fade", "duration_s": 0.5},
            ),
        ]
    )
    project.update(overrides)
    return project


def test_cmx_edl_golden_header_and_two_events() -> None:
    assert cmx_edl(_cmx_project()) == (
        "TITLE: Demo\n"
        "FCM: NON-DROP FRAME\n"
        "\n"
        "001  A_ROLL    V     C        "
        "00:00:00:00 00:00:02:00 00:00:00:00 00:00:02:00\n"
        "* FROM CLIP NAME: A_ROLL\n"
        "\n"
        "002  B.MP4     V     D        "
        "00:00:01:00 00:00:04:00 00:00:01:12 00:00:04:12\n"
        "* FROM CLIP NAME: B.MP4\n"
    )


def test_cmx_edl_wipe_uses_the_wipe_event_code() -> None:
    project = _cmx_project(
        clips=[
            _clip("a"),
            _clip("b", transition={"kind": "wipe", "duration_s": 0.5}),
        ]
    )
    events = [line for line in cmx_edl(project).splitlines() if " V     " in line]
    assert " V     C " in events[0]
    assert " V     W " in events[1]


def test_cmx_edl_carries_frames_into_minutes_and_hours() -> None:
    project = _cmx_project(clips=[_clip("a", in_s=3661.5, out_s=3662.0)])
    text = cmx_edl(project)
    assert "01:01:01:12 01:01:02:00" in text


def test_cmx_edl_rounds_half_a_frame_up() -> None:
    project = _cmx_project(clips=[_clip("a", in_s=24.5 / 24, out_s=25.5 / 24)])
    assert "00:00:01:01 00:00:01:02" in cmx_edl(project)


def test_cmx_edl_skips_clips_above_the_base_plane() -> None:
    project = _cmx_project(clips=[_clip("a"), _clip("b", track=1)])
    text = cmx_edl(project)
    assert text.count(" V     C        ") == 1
    assert "B.MP4" not in text


def test_cmx_edl_folds_unsafe_reel_characters() -> None:
    project = _cmx_project(clips=[_clip("a", label="", source="clips\\take one.mp4")])
    assert "* FROM CLIP NAME: TAKE_ONE.MP4" in cmx_edl(project)


def test_cmx_edl_collapses_the_title_and_defaults_when_blank() -> None:
    assert "TITLE: Spring Cut" in cmx_edl(_cmx_project(title=" Spring\n Cut "))
    assert "TITLE: EZ Edit" in cmx_edl(_cmx_project(title=""))


def test_cmx_edl_refuses_a_frame_rate_below_one() -> None:
    with pytest.raises(EdlError, match="fps must be >= 1 to export CMX"):
        cmx_edl(_raw(_cmx_project(fps=0.4)))


def test_cmx_edl_refuses_a_project_without_a_base_plane() -> None:
    with pytest.raises(EdlError, match="no base-plane \\(track 0\\) clip"):
        cmx_edl(_raw(_cmx_project(clips=[_clip("a", track=2)])))
