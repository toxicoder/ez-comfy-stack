"""Hermetic tests for :mod:`ez_edit.dispatch` (tool dispatcher + client registry).

No ffmpeg, no ffprobe, no socket, no meaningful sleep: the subprocess runner,
the PATH lookup, the ComfyUI transport, the sleeper, the occupancy reader, and
the clock are all injected fakes.
"""

from __future__ import annotations

import json
import subprocess
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Literal

import pytest
from ez_edit import dispatch, render_server, timeline
from ez_edit.protocol import EditProject, LocalCall
from ez_edit.dispatch import (
    ClientRegistry,
    DispatchError,
    build_dispatch,
    export_edl,
    import_clip,
    output_root,
    probe_duration,
    read_occupancy,
    safe_output_path,
)

FAKE_FFMPEG = "/usr/bin/ffmpeg"
FAKE_FFPROBE = "/usr/bin/ffprobe"
PROMPT = "a lathe turning a brass bowl in a sunlit workshop"


def edit_dir_of(tmp_path: Path) -> Path:
    """Create ``<tmp>/edit`` and return it.

    Args:
        tmp_path: pytest tmp directory.

    Returns:
        The edit dir (exists).
    """
    folder = tmp_path / "edit"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def media_file(tmp_path: Path, name: str = "clip.mp4") -> Path:
    """Write a dummy media file under the output root.

    Args:
        tmp_path: pytest tmp directory.
        name: File name.

    Returns:
        Written path.
    """
    folder = tmp_path / "media"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / name
    target.write_bytes(b"\x00\x00\x00\x18ftypmp42fake")
    return target


class FakeRunner:
    """``subprocess.run`` stand-in that records argv and fakes the outcome."""

    def __init__(
        self,
        *,
        returncode: int = 0,
        stdout: str = "12.5",
        stderr: str = "",
        create_output: bool = False,
    ) -> None:
        """Seed the fake outcome.

        Args:
            returncode: Exit code to report.
            stdout: Captured stdout.
            stderr: Captured stderr.
            create_output: Write the last argv element (ffmpeg success).
        """
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.create_output = create_output
        self.calls: list[list[str]] = []

    def __call__(
        self, argv: list[str], *, check: bool, capture_output: bool, text: bool
    ) -> Any:
        """Pretend to run ``argv``.

        Args:
            argv: Command vector.
            check: Unused (never raises).
            capture_output: Unused.
            text: Unused.

        Returns:
            Completed-process stand-in.
        """
        del check, capture_output, text
        self.calls.append(list(argv))
        if self.create_output:
            Path(argv[-1]).write_bytes(b"mp4")
        return SimpleNamespace(
            returncode=self.returncode, stdout=self.stdout, stderr=self.stderr
        )


def kit(**overrides: Any) -> dict[str, Any]:
    """Seam bundle with the PATH lookup pinned.

    Args:
        **overrides: Extra or replaced seams.

    Returns:
        Mutable kit dict for ``build_dispatch``.
    """
    base: dict[str, Any] = {"which": lambda name: FAKE_FFMPEG if name == "ffmpeg" else FAKE_FFPROBE}
    base.update(overrides)
    return base


def create_project(edit_dir: Path, title: str = "Reel") -> EditProject:
    """Create one project through the reducer.

    Args:
        edit_dir: Edit dir.
        title: Project title.

    Returns:
        The new project.
    """
    return timeline.apply_ops(
        None, [{"op": "project_create", "args": {"title": title}}]
    )


def seed_project(edit_dir: Path, title: str = "Reel") -> EditProject:
    """Create a project on disk.

    Args:
        edit_dir: Edit dir.
        title: Project title.

    Returns:
        The stored project.
    """
    project = create_project(edit_dir, title)
    timeline.save_project(edit_dir, project)
    return project


def tool_result(handler: Callable[[str, dict[str, Any]], dict[str, Any]], name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Call one tool and parse its JSON text.

    Args:
        handler: Dispatcher handler.
        name: Tool name.
        args: Tool arguments.

    Returns:
        ``{"ok", "text", "data"}`` with ``data`` parsed when the text is JSON.
    """
    result = handler(name, args)
    text = result.get("text", "")
    try:
        data = json.loads(text)
    except (TypeError, ValueError):
        data = None
    return {"ok": result["ok"], "text": text, "data": data}


def test_output_root_and_safe_path_vet_caller_input(tmp_path: Path) -> None:
    """Only paths that stay under the output root are accepted."""
    edit_dir = edit_dir_of(tmp_path)
    media_file(tmp_path)
    assert output_root(edit_dir) == tmp_path.resolve()
    assert safe_output_path(edit_dir, "media/clip.mp4").name == "clip.mp4"
    absolute = tmp_path / "media" / "clip.mp4"
    assert safe_output_path(edit_dir, str(absolute)) == absolute
    with pytest.raises(DispatchError, match="outside"):
        safe_output_path(edit_dir, "../../etc/passwd")
    with pytest.raises(DispatchError, match="required"):
        safe_output_path(edit_dir, "   ")


def test_probe_duration_reads_ffprobe_output(tmp_path: Path) -> None:
    """A clean ffprobe run reports the duration and the argv used."""
    runner = FakeRunner(stdout=" 7.25\n")
    assert probe_duration(tmp_path / "clip.mp4", runner=runner, which=lambda _n: FAKE_FFPROBE) == 7.25
    assert runner.calls[0][0] == FAKE_FFPROBE
    assert runner.calls[0][-1] == str(tmp_path / "clip.mp4")


@pytest.mark.parametrize(
    ("which", "runner", "needle"),
    [
        (lambda _n: None, FakeRunner(), "ffprobe not found"),
        (lambda _n: FAKE_FFPROBE, FakeRunner(returncode=1, stderr="bad file"), "bad file"),
        (lambda _n: FAKE_FFPROBE, FakeRunner(returncode=1, stderr=""), "no output"),
        (lambda _n: FAKE_FFPROBE, FakeRunner(stdout="N/A"), "no duration"),
        (lambda _n: FAKE_FFPROBE, FakeRunner(stdout="0"), "zero duration"),
    ],
    ids=["missing", "failed", "silent", "unparsable", "zero"],
)
def test_probe_duration_refuses(
    tmp_path: Path, which: Any, runner: FakeRunner, needle: str
) -> None:
    """Every probe failure names the reason the agent can relay."""
    with pytest.raises(DispatchError, match=needle):
        probe_duration(tmp_path / "clip.mp4", runner=runner, which=which)


def test_probe_duration_uses_the_module_runner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With no injected runner the module calls subprocess itself."""
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda argv, **_kw: SimpleNamespace(returncode=0, stdout="3.5", stderr=""),
    )
    assert probe_duration(tmp_path / "clip.mp4", which=lambda _n: FAKE_FFPROBE) == 3.5


def test_import_clip_adds_a_probed_clip_to_the_newest_project(tmp_path: Path) -> None:
    """Import probes the file and lands the clip on the current project."""
    edit_dir = edit_dir_of(tmp_path)
    project = seed_project(edit_dir)
    media_file(tmp_path)
    clip = import_clip(
        edit_dir,
        path="media/clip.mp4",
        runner=FakeRunner(stdout="4.0"),
        which=lambda _n: FAKE_FFPROBE,
    )
    assert clip["source"] == "media/clip.mp4"
    assert clip["out_s"] == 4.0
    assert clip["label"] == "clip.mp4"
    assert clip["track"] == 0
    stored = timeline.load_project(edit_dir, project["id"])
    assert [row["id"] for row in stored["clips"]] == [clip["id"]]


def test_import_clip_uses_the_label_and_track(tmp_path: Path) -> None:
    """An explicit label and track survive into the clip."""
    edit_dir = edit_dir_of(tmp_path)
    seed_project(edit_dir)
    media_file(tmp_path)
    clip = import_clip(
        edit_dir,
        path=str(tmp_path / "media" / "clip.mp4"),
        label="  Opening  ",
        track=2,
        runner=FakeRunner(stdout="2"),
        which=lambda _n: FAKE_FFPROBE,
    )
    assert (clip["label"], clip["track"]) == ("Opening", 2)


def test_import_clip_refuses_a_missing_file(tmp_path: Path) -> None:
    """Nothing is probed or stored when the file is not there."""
    edit_dir = edit_dir_of(tmp_path)
    seed_project(edit_dir)
    with pytest.raises(DispatchError, match="no such file"):
        import_clip(edit_dir, path="media/gone.mp4", runner=FakeRunner(), which=lambda _n: FAKE_FFPROBE)


def test_dispatch_import_reports_the_probe_failure(tmp_path: Path) -> None:
    """The agent gets a readable refusal instead of an exception."""
    edit_dir = edit_dir_of(tmp_path)
    seed_project(edit_dir)
    media_file(tmp_path)
    handler = build_dispatch(edit_dir, runners=kit(which=lambda _n: None))
    result = tool_result(handler, "edit_import", {"path": "media/clip.mp4"})
    assert result["ok"] is False
    assert "ffprobe not found" in result["text"]


def test_dispatch_import_lands_the_clip_it_probed(tmp_path: Path) -> None:
    """The agent's import tool relays the clip it stored on the project."""
    edit_dir = edit_dir_of(tmp_path)
    project = seed_project(edit_dir)
    media_file(tmp_path)
    handler = build_dispatch(
        edit_dir,
        runners=kit(subprocess=FakeRunner(stdout="3.0"), which=lambda _n: FAKE_FFPROBE),
    )
    result = tool_result(handler, "edit_import", {"path": "media/clip.mp4", "label": "Bowl"})
    assert result["ok"] is True
    assert result["data"]["clip"]["source"] == "media/clip.mp4"
    assert result["data"]["clip"]["label"] == "Bowl"
    assert result["data"]["duration_s"] == 3.0
    stored = timeline.load_project(edit_dir, project["id"])
    assert [row["label"] for row in stored["clips"]] == ["Bowl"]


def test_apply_ops_stamps_updated_at_from_the_injected_clock(tmp_path: Path) -> None:
    """The lane's ISO stamp seam reaches the reducer as a datetime clock."""
    edit_dir = edit_dir_of(tmp_path)
    handler = build_dispatch(
        edit_dir, runners=kit(clock=lambda: "2026-01-01T00:00:00+00:00")
    )
    result = tool_result(
        handler, "edit_apply_ops", {"ops": [{"op": "project_create", "args": {"title": "T"}}]}
    )
    assert result["ok"] is True
    assert result["data"]["project"]["updated_at"] == "2026-01-01T00:00:00+00:00"


def test_apply_ops_to_refuses_a_clock_that_is_not_iso_8601(tmp_path: Path) -> None:
    """An unreadable stamp is a reducer refusal, not a crash mid-write."""
    edit_dir = edit_dir_of(tmp_path)
    with pytest.raises(timeline.TimelineError, match="clock:"):
        dispatch.apply_ops_to(
            edit_dir,
            ops=[{"op": "project_create", "args": {"title": "T"}}],
            clock=lambda: "yesterday",
        )
    assert list((edit_dir / "projects").glob("*.json")) == []


def test_dispatch_unknown_tool_is_a_refusal(tmp_path: Path) -> None:
    """An invented tool name never reaches the lane."""
    handler = build_dispatch(edit_dir_of(tmp_path), runners=kit())
    result = handler("edit_launch_missiles", {})
    assert result == {"ok": False, "text": "unknown tool: edit_launch_missiles"}


def test_dispatch_tolerates_non_mapping_args(tmp_path: Path) -> None:
    """A model that sends a list as args still gets the state payload."""
    edit_dir = edit_dir_of(tmp_path)
    handler = build_dispatch(edit_dir, runners=kit())
    result = handler("edit_get_state", ["not", "a", "mapping"])  # type: ignore[arg-type]
    assert result["ok"] is True
    assert json.loads(result["text"]) == {"project": None, "jobs": []}


def test_dispatch_get_state_lists_rows_for_the_project(tmp_path: Path) -> None:
    """State carries the newest project and its rows."""
    edit_dir = edit_dir_of(tmp_path)
    project = seed_project(edit_dir)
    render_server.start_render(edit_dir, project, mode="client", client_id="tab1")
    handler = build_dispatch(edit_dir, runners=kit())
    data = tool_result(handler, "edit_get_state", {})["data"]
    assert data["project"]["id"] == project["id"]
    assert [row["kind"] for row in data["jobs"]] == ["exec_client"]


def test_dispatch_apply_ops_creates_and_edits(tmp_path: Path) -> None:
    """Ops run through the reducer and persist."""
    edit_dir = edit_dir_of(tmp_path)
    handler = build_dispatch(edit_dir, runners=kit())
    created = tool_result(
        handler,
        "edit_apply_ops",
        {"ops": [{"op": "project_create", "args": {"title": "Cut"}}]},
    )
    assert created["ok"] is True
    assert created["data"]["project"]["title"] == "Cut"
    assert created["data"]["clips"] == 0
    bad = tool_result(handler, "edit_apply_ops", {"ops": [{"op": "nope", "args": {}}]})
    assert bad["ok"] is False and "nope" in bad["text"]


def test_dispatch_apply_ops_refuses_a_junk_op(tmp_path: Path) -> None:
    """A non-object op row is refused by the reducer, not dropped."""
    edit_dir = edit_dir_of(tmp_path)
    handler = build_dispatch(edit_dir, runners=kit())
    result = tool_result(
        handler,
        "edit_apply_ops",
        {"ops": ["junk", {"op": "project_create", "args": {}}]},
    )
    assert result["ok"] is False


def test_dispatch_render_server_runs_ffmpeg_once(tmp_path: Path) -> None:
    """A server render runs one ffmpeg argv through the injected runner."""
    edit_dir = edit_dir_of(tmp_path)
    project = seed_project(edit_dir)
    media_file(tmp_path)
    import_clip(edit_dir, path="media/clip.mp4", runner=FakeRunner(stdout="4"), which=lambda _n: FAKE_FFPROBE)
    runner = FakeRunner(create_output=True)
    handler = build_dispatch(edit_dir, runners=kit(subprocess=runner))
    result = tool_result(handler, "edit_render", {"mode": "server"})
    assert result["ok"] is True
    assert result["data"]["state"] == "ok"
    assert len(runner.calls) == 1
    assert runner.calls[0][0] == FAKE_FFMPEG


def test_dispatch_render_failure_is_an_ok_false_result(tmp_path: Path) -> None:
    """An ffmpeg that exits non-zero comes back as a refusal, not a raise."""
    edit_dir = edit_dir_of(tmp_path)
    project = seed_project(edit_dir)
    media_file(tmp_path)
    import_clip(edit_dir, path="media/clip.mp4", runner=FakeRunner(stdout="4"), which=lambda _n: FAKE_FFPROBE)
    handler = build_dispatch(
        edit_dir, runners=kit(subprocess=FakeRunner(returncode=1, stderr="boom"))
    )
    result = tool_result(handler, "edit_render", {"mode": "server", "project_id": project["id"]})
    assert result["ok"] is False
    assert result["data"]["state"] == "failed"


def test_dispatch_render_client_leaves_a_row_for_the_panel(tmp_path: Path) -> None:
    """A client render is queued, never executed on the Spark."""
    edit_dir = edit_dir_of(tmp_path)
    seed_project(edit_dir)
    media_file(tmp_path)
    import_clip(edit_dir, path="media/clip.mp4", runner=FakeRunner(stdout="4"), which=lambda _n: FAKE_FFPROBE)
    runner = FakeRunner()
    handler = build_dispatch(edit_dir, runners=kit(subprocess=runner))
    result = tool_result(handler, "edit_render", {"mode": "client", "client_id": "tab1"})
    assert result["ok"] is True
    assert result["data"]["state"] == "pending"
    assert runner.calls == []


def test_dispatch_render_rejects_a_bad_mode(tmp_path: Path) -> None:
    """A mode outside the vocabulary is refused before any row is written."""
    edit_dir = edit_dir_of(tmp_path)
    seed_project(edit_dir)
    handler = build_dispatch(edit_dir, runners=kit())
    result = tool_result(handler, "edit_render", {"mode": "cloud"})
    assert result["ok"] is False and "bad render mode" in result["text"]


def test_dispatch_render_without_a_project_says_so(tmp_path: Path) -> None:
    """The agent is told to create a project first."""
    handler = build_dispatch(edit_dir_of(tmp_path), runners=kit())
    result = tool_result(handler, "edit_render", {"mode": "server"})
    assert result["ok"] is False and "project_create" in result["text"]


def test_dispatch_job_status_reads_and_reports_missing_rows(tmp_path: Path) -> None:
    """A known row round-trips; an unknown one is a readable refusal."""
    edit_dir = edit_dir_of(tmp_path)
    project = seed_project(edit_dir)
    row = render_server.start_render(edit_dir, project, mode="client", client_id="tab1")
    handler = build_dispatch(edit_dir, runners=kit())
    found = tool_result(handler, "edit_job_status", {"job_id": row["id"]})
    assert found["ok"] is True and found["data"]["id"] == row["id"]
    missing = tool_result(handler, "edit_job_status", {"job_id": "zzz"})
    assert missing["ok"] is False and "missing edit job" in missing["text"]


def test_dispatch_export_edl_writes_the_handoff(tmp_path: Path) -> None:
    """Export writes one handoff file and names it relative to the root."""
    edit_dir = edit_dir_of(tmp_path)
    seed_project(edit_dir)
    media_file(tmp_path)
    import_clip(edit_dir, path="media/clip.mp4", runner=FakeRunner(stdout="4"), which=lambda _n: FAKE_FFPROBE)
    handler = build_dispatch(edit_dir, runners=kit())
    result = tool_result(handler, "edit_export_edl", {})
    assert result["ok"] is True
    assert result["data"]["clips"] == 1
    written = edit_dir / "projects" / f"{result['data']['project_id']}.edl.json"
    assert written.is_file()
    assert json.loads(written.read_text(encoding="utf-8"))["clips"][0]["source"] == "media/clip.mp4"


def test_export_edl_refuses_an_unsafe_project_id(tmp_path: Path) -> None:
    """A traversing id never reaches the file system."""
    edit_dir = edit_dir_of(tmp_path)
    seed_project(edit_dir)
    with pytest.raises(DispatchError, match="unsafe project_id"):
        export_edl(edit_dir, "../escape")


def test_dispatch_export_edl_writes_cmx_text(tmp_path: Path) -> None:
    """``format=cmx`` hands the same cut over as CMX 3600 text."""
    edit_dir = edit_dir_of(tmp_path)
    seed_project(edit_dir)
    media_file(tmp_path)
    import_clip(edit_dir, path="media/clip.mp4", runner=FakeRunner(stdout="4"), which=lambda _n: FAKE_FFPROBE)
    handler = build_dispatch(edit_dir, runners=kit())
    result = tool_result(handler, "edit_export_edl", {"format": "cmx"})
    assert result["ok"] is True and result["data"]["format"] == "cmx"
    written = edit_dir / "projects" / f"{result['data']['project_id']}.edl"
    assert written.read_text(encoding="utf-8").startswith("TITLE:")


def test_dispatch_export_edl_refuses_an_unknown_format(tmp_path: Path) -> None:
    """A format nobody implements fails the call with the name it did not know."""
    handler = build_dispatch(edit_dir_of(tmp_path), runners=kit())
    result = tool_result(handler, "edit_export_edl", {"format": "xmeml"})
    assert result["ok"] is False and "unknown edl format" in result["text"]


def test_dispatch_list_projects_returns_summary_rows(tmp_path: Path) -> None:
    """An agent holding no project id can still discover what exists."""
    edit_dir = edit_dir_of(tmp_path)
    seed_project(edit_dir)
    handler = build_dispatch(edit_dir, runners=kit())
    result = tool_result(handler, "edit_list_projects", {})
    assert result["ok"] is True
    rows = result["data"]["projects"]
    assert len(rows) == 1 and rows[0]["clips"] == 0
    assert set(rows[0]) == {
        "id", "title", "fps", "width", "height", "clips", "updated_at",
    }


def test_dispatch_export_edl_without_a_project(tmp_path: Path) -> None:
    """Nothing to hand off is reported as such."""
    handler = build_dispatch(edit_dir_of(tmp_path), runners=kit())
    result = tool_result(handler, "edit_export_edl", {})
    assert result["ok"] is False and "no edit project" in result["text"]


def test_dispatch_occupancy_uses_the_injected_reader(tmp_path: Path) -> None:
    """The occupancy tool relays whatever mode the seam reports."""
    handler = build_dispatch(edit_dir_of(tmp_path), runners=kit(occupancy=lambda: "klein"))
    assert tool_result(handler, "occupancy_status", {})["data"] == {"mode": "klein"}


def test_read_occupancy_falls_back_to_the_state_file(tmp_path: Path) -> None:
    """No seam means the occupancy file (or unknown) answers."""
    (tmp_path / ".occupancy.json").write_text('{"mode": "wan"}', encoding="utf-8")
    assert read_occupancy({}, {"COMFY_OUTPUT_DIR": str(tmp_path)}) == "wan"
    assert read_occupancy({"environ": {"COMFY_OUTPUT_DIR": str(tmp_path / "none")}}) == "unknown"
    assert read_occupancy({"occupancy": lambda: "  "}) == "unknown"


def test_dispatch_generate_clip_uses_the_injected_queue(tmp_path: Path) -> None:
    """The generate tool hands the model's args to the queue seam."""
    edit_dir = edit_dir_of(tmp_path)
    seen: dict[str, Any] = {}

    def fake_generate(target: Path | str, **kwargs: Any) -> Any:
        """Record the args and return a running row.

        Args:
            target: Edit dir.
            **kwargs: Generation arguments.

        Returns:
            A jobstore row.
        """
        seen["target"] = Path(target)
        seen.update(kwargs)
        return render_server.JobRecord(
            id="g1",
            kind="generate_clip",
            project_id="p",
            state="ok",
            mode="server",
            message="done",
            out_path="renders/x.mp4",
            created_at="",
            updated_at="",
            client_id="tab1",
        )

    handler = build_dispatch(edit_dir, runners=kit(generate=fake_generate))
    result = tool_result(
        handler, "edit_generate_clip", {"prompt": PROMPT, "duration_s": "bad", "fps": 30}
    )
    assert result["ok"] is True
    assert seen["prompt"] == PROMPT
    assert seen["duration_s"] == 5.0
    assert seen["fps"] == 30.0


def test_dispatch_generate_clip_reports_a_failed_row(tmp_path: Path) -> None:
    """A refusal row from the queue is an ok-false tool result."""
    edit_dir = edit_dir_of(tmp_path)

    def fake_generate(_target: Path | str, **_kwargs: Any) -> Any:
        """Return a failed row.

        Args:
            _target: Edit dir.
            **_kwargs: Generation arguments.

        Returns:
            A failed jobstore row.
        """
        return render_server.JobRecord(
            id="g2",
            kind="generate_clip",
            project_id="",
            state="failed",
            mode="server",
            message="occupancy is wan",
            out_path="",
            created_at="",
            updated_at="",
            client_id="",
        )

    handler = build_dispatch(edit_dir, runners=kit(generate=fake_generate))
    result = tool_result(handler, "edit_generate_clip", {"prompt": PROMPT})
    assert result["ok"] is False and "occupancy is wan" in result["text"]


def test_dispatch_generate_clip_uses_the_real_queue(tmp_path: Path) -> None:
    """Without a queue seam the real generate module is used."""
    edit_dir = edit_dir_of(tmp_path)

    class Transport:
        """Answer the queue POST and one history poll."""

        def __init__(self) -> None:
            """Seed the reply queue."""
            self.replies = [{"prompt_id": "pid"}, {"pid": {"outputs": {}}}]
            self.calls: list[str] = []

        def __call__(self, request: urllib.request.Request, timeout: float) -> Any:
            """Pop the next reply.

            Args:
                request: Prepared request.
                timeout: Socket timeout.

            Returns:
                Response stand-in.
            """
            del timeout
            self.calls.append(request.full_url)
            payload = json.dumps(self.replies.pop(0) if self.replies else {})

            class _Response:
                def __enter__(self) -> "_Response":
                    """Enter.

                    Returns:
                        Self.
                    """
                    return self

                def __exit__(self, *_args: object) -> Literal[False]:
                    """Exit.

                    Args:
                        *_args: Ignored.

                    Returns:
                        False.
                    """
                    return False

                def read(self) -> bytes:
                    """Read the body.

                    Returns:
                        Encoded payload.
                    """
                    return payload.encode("utf-8")

            return _Response()

    transport = Transport()
    handler = build_dispatch(
        edit_dir,
        runners=kit(
            urlopen=transport,
            sleeper=lambda _s: None,
            occupancy=lambda: "idle",
            environ={"EZ_EDIT_COMFY_URL": "http://127.0.0.1:8188"},
        ),
    )
    result = tool_result(handler, "edit_generate_clip", {"prompt": PROMPT})
    assert result["ok"] is True
    assert result["data"]["kind"] == "generate_clip"
    assert transport.calls[0] == "http://127.0.0.1:8188/prompt"


def test_registry_sync_stores_only_usable_tools(tmp_path: Path) -> None:
    """Sync keeps named tools and drops junk rows."""
    registry = ClientRegistry(edit_dir_of(tmp_path), clock=lambda: "2026-01-01T00:00:00+00:00")
    count = registry.sync(
        "tab1",
        [
            {"server_id": "srv", "server_url": "http://127.0.0.1:7000/mcp", "name": "read_file", "description": "Read", "input_schema": {"type": "object"}},
            {"name": "   "},
            "junk",
            None,
        ],
    )
    assert count == 1
    entries = registry.all_tools()
    assert entries[0].client_id == "tab1"
    assert entries[0].tool["name"] == "read_file"
    document = json.loads((registry.client_dir("tab1") / "tools.json").read_text(encoding="utf-8"))
    assert document["updated_at"] == "2026-01-01T00:00:00+00:00"


def test_registry_sync_refuses_junk_payloads(tmp_path: Path) -> None:
    """A non-list tool payload and an unsafe id are refused."""
    registry = ClientRegistry(edit_dir_of(tmp_path))
    junk_tools: Any = {"name": "read_file"}
    with pytest.raises(DispatchError, match="tools must be a list"):
        registry.sync("tab1", junk_tools)
    for bad in ("", "../out", "a/b", "~x"):
        with pytest.raises(DispatchError):
            registry.sync(bad, [])


def test_registry_all_tools_tolerates_junk_files(tmp_path: Path) -> None:
    """A corrupt or shape-wrong tools file is skipped, not fatal."""
    registry = ClientRegistry(edit_dir_of(tmp_path))
    good = registry.client_dir("tab1")
    good.mkdir(parents=True)
    (good / "tools.json").write_text('{"tools": "nope"}', encoding="utf-8")
    other = registry.client_dir("tab2")
    other.mkdir(parents=True)
    (other / "tools.json").write_text("[]", encoding="utf-8")
    assert registry.all_tools() == []
    assert registry.all_tools("tab1") == []


def test_registry_all_tools_without_a_clients_dir(tmp_path: Path) -> None:
    """A lane that never saw a browser reports no tools."""
    registry = ClientRegistry(tmp_path / "edit")
    assert registry.all_tools() == []


def test_registry_owner_and_clients_for_tool(tmp_path: Path) -> None:
    """Owner lookup drives which panel a local call is queued on."""
    registry = ClientRegistry(edit_dir_of(tmp_path))
    registry.sync(
        "tab1",
        [{"server_id": "srv", "server_url": "http://127.0.0.1:7000/mcp", "name": "read_file"}],
    )
    registry.sync(
        "tab2",
        [{"server_id": "other", "server_url": "http://127.0.0.1:7001/mcp", "name": "list_dir"}],
    )
    entry = registry.owner("srv", "read_file")
    assert entry is not None and entry.client_id == "tab1"
    assert registry.owner("srv", "list_dir") is None
    assert registry.clients_for_tool("list_dir") == ["tab2"]


def test_registry_enqueue_pending_and_answer(tmp_path: Path) -> None:
    """A queued call is pending until the panel answers it."""
    registry = ClientRegistry(edit_dir_of(tmp_path), clock=lambda: "2026-01-01T00:00:00+00:00")
    call = registry.enqueue(
        "tab1", server_url="http://127.0.0.1:7000/mcp", name="read_file", args={"p": 1}
    )
    assert call["args"] == {"p": 1}
    assert registry.pending("tab1") == [call]
    assert registry.answer(call["call_id"]) is None
    assert registry.submit_result(call["call_id"], ok=True, text=" hello ") is True
    answer = registry.answer(call["call_id"])
    assert answer is not None and answer.ok and answer.text == " hello "
    assert registry.pending("tab1") == []


def test_registry_pending_sorts_and_skips_junk(tmp_path: Path) -> None:
    """Rows sort by stamp then id, and unreadable rows are skipped."""
    registry = ClientRegistry(edit_dir_of(tmp_path))
    first = registry.enqueue("tab1", server_url="u", name="a", args={})
    second = registry.enqueue("tab1", server_url="u", name="b", args={})
    folder = registry._calls_dir("tab1")
    (folder / "broken.json").write_text("nope", encoding="utf-8")
    (folder / f"{first['call_id']}.json").write_text(
        json.dumps({"call_id": first["call_id"], "state": "pending", "created_at": "2026-01-02"}),
        encoding="utf-8",
    )
    (folder / f"{second['call_id']}.json").write_text(
        json.dumps({"call_id": second["call_id"], "state": "pending", "created_at": "2026-01-01"}),
        encoding="utf-8",
    )
    assert [row["call_id"] for row in registry.pending("tab1")] == [
        second["call_id"],
        first["call_id"],
    ]
    assert registry.pending("nobody") == []


def test_registry_submit_result_refuses_unknown_calls(tmp_path: Path) -> None:
    """An unknown, unsafe, or unreadable call id cannot be answered."""
    registry = ClientRegistry(edit_dir_of(tmp_path))
    assert registry.submit_result("nope", ok=True, text="x") is False
    assert registry.submit_result("../nope", ok=True, text="x") is False
    assert registry.answer("nope") is None
    call = registry.enqueue("tab1", server_url="u", name="a", args={})
    (registry._calls_dir("tab1") / f"{call['call_id']}.json").write_text("nope", encoding="utf-8")
    assert registry.submit_result(call["call_id"], ok=False, text="x") is False
    assert registry.answer(call["call_id"]) is None


def test_registry_submit_result_ignores_rows_that_are_not_files(tmp_path: Path) -> None:
    """With a calls dir present, an absent or shadowed id still answers nothing."""
    registry = ClientRegistry(edit_dir_of(tmp_path))
    registry.enqueue("tab1", server_url="u", name="a", args={})
    (registry._calls_dir("tab1") / "shadow.json").mkdir()
    assert registry.submit_result("missing", ok=True, text="x") is False
    assert registry.submit_result("shadow", ok=True, text="x") is False
    assert registry.answer("missing") is None
    assert registry.answer("shadow") is None


def test_registry_without_a_clients_dir_finds_nothing(tmp_path: Path) -> None:
    """A lane with no clients dir answers every lookup with nothing."""
    registry = ClientRegistry(tmp_path / "edit")
    assert registry.submit_result("abc", ok=True, text="x") is False
    assert registry.answer("abc") is None


def test_registry_wait_returns_the_answer_written_by_the_sleeper(tmp_path: Path) -> None:
    """The dispatcher unblocks as soon as the panel posts its result."""
    registry = ClientRegistry(edit_dir_of(tmp_path))
    call = registry.enqueue("tab1", server_url="u", name="a", args={})

    def answer_after_one_poll(_seconds: float) -> None:
        """Land the panel's answer on the first poll.

        Args:
            _seconds: Poll interval (ignored).
        """
        registry.submit_result(call["call_id"], ok=True, text="tool output")

    answer = registry.wait(call["call_id"], sleeper=answer_after_one_poll, timeout_s=1.0, poll_s=0.001)
    assert answer is not None
    assert (answer.ok, answer.text) == (True, "tool output")


def test_registry_wait_times_out_with_the_default_sleeper(tmp_path: Path) -> None:
    """Nobody answering comes back as no answer, quickly."""
    registry = ClientRegistry(edit_dir_of(tmp_path))
    call = registry.enqueue("tab1", server_url="u", name="a", args={})
    assert registry.wait(call["call_id"], timeout_s=0.003, poll_s=0.001) is None


def _sync_read_tool(registry: ClientRegistry) -> None:
    """Advertise one laptop tool from ``tab1``.

    Args:
        registry: Registry under test.
    """
    registry.sync(
        "tab1",
        [
            {
                "server_id": "srv",
                "server_url": "http://127.0.0.1:7000/mcp",
                "name": "read_file",
                "description": "Read a laptop file",
                "input_schema": {"type": "object"},
            }
        ],
    )


def test_dispatch_local_tool_round_trip(tmp_path: Path) -> None:
    """A ``local__`` call is queued on its panel and the answer comes back."""
    edit_dir = edit_dir_of(tmp_path)
    registry = ClientRegistry(edit_dir)
    _sync_read_tool(registry)
    calls: list[LocalCall] = []

    def answer(_seconds: float) -> None:
        """Answer the first pending call the dispatcher queued.

        Args:
            _seconds: Poll interval (ignored).
        """
        pending = registry.pending("tab1")
        if pending and len(calls) < 1:
            calls.append(pending[0])
            registry.submit_result(pending[0]["call_id"], ok=True, text="file body")

    handler = build_dispatch(
        edit_dir,
        runners={"sleeper": answer, "local_timeout_s": 1.0, "local_poll_s": 0.001},
        client_registry=registry,
    )
    result = handler("local__srv__read_file", {"path": "notes.md"})
    assert result == {"ok": True, "text": "file body"}
    assert calls[0]["args"] == {"path": "notes.md"}
    assert calls[0]["name"] == "read_file"


def test_dispatch_local_tool_timeout(tmp_path: Path) -> None:
    """A panel that never answers produces a readable refusal."""
    edit_dir = edit_dir_of(tmp_path)
    registry = ClientRegistry(edit_dir)
    _sync_read_tool(registry)
    handler = build_dispatch(
        edit_dir,
        runners={"sleeper": lambda _s: None, "local_timeout_s": 0.003, "local_poll_s": 0.001},
        client_registry=registry,
    )
    result = handler("local__srv__read_file", {})
    assert result["ok"] is False
    assert "did not answer" in result["text"]


@pytest.mark.parametrize(
    ("name", "needle"),
    [
        ("local__srv", "bad local tool name"),
        ("local____tool", "bad local tool name"),
        ("local__srv__", "bad local tool name"),
        ("local__a__b__c", "bad local tool name"),
        ("other__srv__tool", "unknown tool"),
    ],
    ids=["too-few", "blank-server", "blank-tool", "too-many", "wrong-prefix"],
)
def test_dispatch_rejects_malformed_local_names(
    tmp_path: Path, name: str, needle: str
) -> None:
    """A name outside ``local__<server_id>__<tool>`` is refused, not queued.

    A name that never carries the ``local__`` envelope is not a local tool at
    all, so it reads as an unknown static tool instead.
    """
    edit_dir = edit_dir_of(tmp_path)
    registry = ClientRegistry(edit_dir)
    _sync_read_tool(registry)
    handler = build_dispatch(edit_dir, runners={}, client_registry=registry)
    result = handler(name, {})
    assert result["ok"] is False
    assert needle in result["text"]
    assert registry.pending("tab1") == []


def test_dispatch_local_tool_nobody_advertised(tmp_path: Path) -> None:
    """An unknown laptop tool names the Discover step the panel must run."""
    edit_dir = edit_dir_of(tmp_path)
    registry = ClientRegistry(edit_dir)
    handler = build_dispatch(edit_dir, runners={}, client_registry=registry)
    result = handler("local__srv__read_file", {})
    assert result["ok"] is False
    assert "Discover" in result["text"]


def test_build_dispatch_defaults_to_no_seams(tmp_path: Path) -> None:
    """No runners and no registry still answer a static tool."""
    edit_dir = edit_dir_of(tmp_path)
    handler = build_dispatch(edit_dir)
    assert handler("occupancy_status", {})["ok"] is True
