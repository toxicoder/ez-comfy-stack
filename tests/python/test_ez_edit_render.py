"""Hermetic tests for the ez_edit render jobstore (no ffmpeg, no wall clock).

Covers :mod:`ez_edit.render_server`: the server lifecycle ``pending ->
running -> ok/failed`` through a fake :class:`ez_common.protocols.
SubprocessRunner`, ffmpeg lookup failures, stderr excerpts, path-traversal
refusals, the client claim/complete protocol, and the row-file store under
``<edit_dir>/jobs``. Clocks and PATH lookups are injected; every path lives
under ``tmp_path``.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from ez_edit import render_server
from ez_edit.protocol import JobKind, JobRecord
from ez_edit.render_server import (
    CLIENT_ID_MESSAGE,
    CLIENT_KIND,
    CLIENT_WAIT_MESSAGE,
    CLAIMED_MESSAGE,
    MISSING_FFMPEG_MESSAGE,
    OUTPUT_TAIL_CHARS,
    RUNNING_MESSAGE,
    SERVER_KIND,
    claim_next_client_job,
    complete_client_job,
    job_path,
    jobs_dir,
    list_jobs,
    read_job,
    render_path,
    renders_dir,
    start_render,
    tick_job,
    write_job,
)

STAMP = "2026-01-02T03:04:05+00:00"
"""Fixed ISO-8601 UTC stamp injected wherever the store stamps time."""


def _clock() -> str:
    """Return the fixed stamp.

    Returns:
        :data:`STAMP`.
    """
    return STAMP


def _raw(value: object) -> Any:
    """Loosen one value's static type so tests can feed malformed rows.

    Args:
        value: Value to hand to the store as ``Any``.

    Returns:
        The same value.
    """
    return value


class FakeProc:
    """``subprocess.CompletedProcess``-shaped result for the seam."""

    def __init__(
        self, returncode: int = 0, stdout: str = "", stderr: str = ""
    ) -> None:
        """Store the text-mode result fields.

        Args:
            returncode: Exit code.
            stdout: Captured stdout.
            stderr: Captured stderr.
        """
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class FakeRunner:
    """Hermetic ``SubprocessRunner`` double that records every argv.

    Satisfies the seam structurally (no inheritance). Optionally raises
    instead of returning, skips writing the output file, and probes the row
    state while the command is "running".
    """

    def __init__(
        self,
        *,
        returncode: int = 0,
        stdout: str = "",
        stderr: str = "",
        write_output: bool = True,
        raises: BaseException | None = None,
        state_probe: Callable[[], str] | None = None,
    ) -> None:
        """Store the scripted behaviour.

        Args:
            returncode: Exit code to report.
            stdout: Captured stdout to report.
            stderr: Captured stderr to report.
            write_output: Write a stub file at ``argv[-1]`` on success.
            raises: Exception to raise instead of returning.
            state_probe: Called per invocation to snapshot the row state.
        """
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.write_output = write_output
        self.raises = raises
        self.state_probe = state_probe
        self.calls: list[list[str]] = []
        self.kwargs: list[dict[str, bool]] = []
        self.states_at_call: list[str] = []

    def __call__(
        self,
        argv: list[str],
        *,
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> FakeProc:
        """Record the call and return the scripted result.

        Args:
            argv: Command vector.
            check: Seam keyword.
            capture_output: Seam keyword.
            text: Seam keyword.

        Returns:
            Scripted :class:`FakeProc`.
        """
        self.calls.append(list(argv))
        self.kwargs.append(
            {"check": check, "capture_output": capture_output, "text": text}
        )
        if self.state_probe is not None:
            self.states_at_call.append(self.state_probe())
        if self.raises is not None:
            raise self.raises
        if self.returncode == 0 and self.write_output:
            out = Path(argv[-1])
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text("stub mp4", encoding="utf-8")
        return FakeProc(self.returncode, self.stdout, self.stderr)


def _edit(tmp_path: Path) -> Path:
    """Build the resolved ``<tmp>/edit`` directory path.

    Args:
        tmp_path: Pytest temp root.

    Returns:
        Edit dir path (created lazily by the store).
    """
    return (tmp_path / "edit").resolve()


def _project(*sources: str, **overrides: Any) -> dict[str, Any]:
    """Build a renderable project record.

    Args:
        *sources: Clip sources (default one relative clip).
        **overrides: Fields to add or replace.

    Returns:
        Edit project record.
    """
    clips = [
        {
            "id": f"c{index}",
            "source": source,
            "label": source,
            "in_s": 0.0,
            "out_s": 2.0,
            "track": 0,
            "gain": 1.0,
            "transition": None,
        }
        for index, source in enumerate(sources or ("clips/a.mp4",))
    ]
    project: dict[str, Any] = {
        "id": "prj 1",
        "title": "Demo",
        "fps": 24.0,
        "width": 1280,
        "height": 704,
        "clips": clips,
        "overlays": [],
        "captions": [],
    }
    project.update(overrides)
    return project


def _row(
    job_id: str,
    *,
    kind: JobKind = CLIENT_KIND,
    state: str = "pending",
    project_id: str = "",
    client_id: str = "br",
    created_at: str = STAMP,
    message: str = "",
) -> JobRecord:
    """Craft a persisted row for store-level tests.

    Args:
        job_id: Row id.
        kind: Row kind.
        state: Lifecycle state.
        project_id: Owning project id.
        client_id: Browser owner.
        created_at: Created stamp.
        message: Row message.

    Returns:
        The crafted row.
    """
    return JobRecord(
        id=job_id,
        kind=kind,
        project_id=project_id,
        state=_raw(state),
        mode=_raw("client" if kind == CLIENT_KIND else "server"),
        message=message,
        out_path="",
        created_at=created_at,
        updated_at=created_at,
        client_id=client_id,
    )


def _state_probe(edit_dir: Path) -> Callable[[], str]:
    """Probe the single row state while a fake ffmpeg is "running".

    Args:
        edit_dir: Edit dir holding the jobs folder.

    Returns:
        Callable returning the lone row's state, or ``missing``.
    """

    def probe() -> str:
        """Read the single persisted row.

        Returns:
            Row state, or ``missing`` when none exists.
        """
        files = sorted(jobs_dir(edit_dir).glob("*.json"))
        if not files:
            return "missing"
        return read_job(edit_dir, files[0].stem)["state"]

    return probe


def _start_server(
    edit_dir: Path,
    runner: FakeRunner,
    *,
    which: Callable[[str], str | None] | None = None,
    project: dict[str, Any] | None = None,
) -> JobRecord:
    """Start a server render with sane test defaults.

    Args:
        edit_dir: Edit dir.
        runner: Fake subprocess seam.
        which: PATH lookup, default resolves ffmpeg.
        project: Project record, default one relative clip.

    Returns:
        Final row.
    """
    return start_render(
        edit_dir,
        project or _project(),
        mode="server",
        runner=runner,
        which=which or (lambda _name: "/usr/bin/ffmpeg"),
        now=_clock,
    )


def test_server_success_lifecycle_and_persistence(tmp_path: Path) -> None:
    edit = _edit(tmp_path)
    runner = FakeRunner(state_probe=_state_probe(edit))
    row = _start_server(edit, runner)
    assert row["state"] == "ok"
    assert row["kind"] == SERVER_KIND
    assert row["mode"] == "server"
    assert row["message"] == "rendered 1 clips"
    assert row["out_path"] == f"renders/prj-1-{row['id']}.mp4"
    assert row["created_at"] == STAMP
    assert row["updated_at"] == STAMP
    assert runner.calls and runner.states_at_call == ["running"]
    assert runner.kwargs == [{"check": False, "capture_output": True, "text": True}]
    persisted = json.loads(
        (jobs_dir(edit) / f"{row['id']}.json").read_text(encoding="utf-8")
    )
    assert persisted["state"] == "ok"
    assert read_job(edit, row["id"]) == row
    assert (edit / row["out_path"]).is_file()


def test_server_argv_vets_source_and_writes_mp4_tail(tmp_path: Path) -> None:
    edit = _edit(tmp_path)
    runner = FakeRunner()
    row = _start_server(edit, runner)
    argv = runner.calls[0]
    assert argv[0] == "/usr/bin/ffmpeg"
    expected_source = str((tmp_path / "clips" / "a.mp4").resolve())
    assert argv[argv.index("-i") + 1] == expected_source
    assert Path(argv[-1]) == render_path(edit, "prj 1", row["id"])
    tail = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-movflags", "+faststart"]
    start = argv.index("-c:v")
    assert argv[start : start + len(tail)] == tail
    assert argv[-3:] == ["-t", "2", argv[-1]]


def test_missing_ffmpeg_fails_naming_ffmpeg(tmp_path: Path) -> None:
    edit = _edit(tmp_path)
    runner = FakeRunner()
    row = _start_server(edit, runner, which=lambda _name: None)
    assert row["state"] == "failed"
    assert row["message"] == MISSING_FFMPEG_MESSAGE
    assert "ffmpeg" in row["message"]
    assert "apt-get" in row["message"]
    assert runner.calls == []


def test_runner_nonzero_exit_keeps_collapsed_stderr(tmp_path: Path) -> None:
    edit = _edit(tmp_path)
    runner = FakeRunner(returncode=1, stderr="line one\n   line two")
    row = _start_server(edit, runner)
    assert row["state"] == "failed"
    assert row["message"] == "ffmpeg exited 1: line one line two"


def test_runner_stderr_is_tailed_to_output_tail_chars(tmp_path: Path) -> None:
    edit = _edit(tmp_path)
    noise = ("filler " * 100).strip() + " END"
    runner = FakeRunner(returncode=2, stderr=noise)
    row = _start_server(edit, runner)
    excerpt = row["message"].removeprefix("ffmpeg exited 2: ")
    assert len(excerpt) <= OUTPUT_TAIL_CHARS
    assert excerpt.endswith("END")
    assert not excerpt.startswith("filler")


def test_proc_tail_prefers_stderr_then_stdout_then_placeholder() -> None:
    assert render_server._proc_tail(FakeProc(1, "", "err text")) == "err text"
    assert render_server._proc_tail(FakeProc(1, "out text", "")) == "out text"
    assert render_server._proc_tail(FakeProc(1, "", "")) == "no output"
    assert render_server._proc_tail(object()) == "no output"
    assert render_server._proc_tail(FakeProc(1, "a\n b\t c", "")) == "a b c"


def test_runner_oserror_marks_failed(tmp_path: Path) -> None:
    edit = _edit(tmp_path)
    runner = FakeRunner(raises=OSError("exec failed"))
    row = _start_server(edit, runner)
    assert row["state"] == "failed"
    assert row["message"] == "OSError: exec failed"


def test_unrenderable_project_fails_before_runner(tmp_path: Path) -> None:
    edit = _edit(tmp_path)
    runner = FakeRunner()
    project = _project()
    project["clips"] = []
    row = _start_server(edit, runner, project=project)
    assert row["state"] == "failed"
    assert row["message"] == "EdlError: project has no clips"
    assert runner.calls == []
    junk = _project()
    junk["clips"] = _raw([3])
    junk_row = _start_server(edit, runner, project=junk)
    assert junk_row["state"] == "failed"
    assert junk_row["message"] == "ValueError: clip must be a mapping"


def test_source_escape_outside_root_fails(tmp_path: Path) -> None:
    edit = _edit(tmp_path)
    relative = _start_server(edit, FakeRunner(), project=_project("../evil.mp4"))
    assert relative["state"] == "failed"
    assert "outside" in relative["message"]
    absolute = _start_server(edit, FakeRunner(), project=_project("/etc/passwd"))
    assert absolute["state"] == "failed"
    assert "/etc/passwd" in absolute["message"]
    empty = _start_server(edit, FakeRunner(), project=_project(""))
    assert empty["state"] == "failed"
    assert empty["message"] == "ValueError: clip has no source"


def test_absolute_source_inside_root_is_ok(tmp_path: Path) -> None:
    edit = _edit(tmp_path)
    source = str((tmp_path / "clips" / "a.mp4").resolve())
    row = _start_server(edit, FakeRunner(), project=_project(source))
    assert row["state"] == "ok"


def test_zero_exit_without_output_file_fails(tmp_path: Path) -> None:
    edit = _edit(tmp_path)
    runner = FakeRunner(returncode=0, write_output=False)
    row = _start_server(edit, runner)
    assert row["state"] == "failed"
    assert "ffmpeg produced no output at" in row["message"]


def test_server_message_notes_deferred_text_planes(tmp_path: Path) -> None:
    edit = _edit(tmp_path)
    project = _project(
        overlays=[{"id": "o1", "kind": "text", "text": "hi"}],
        captions=[{"id": "c1", "text": "yo"}],
    )
    row = _start_server(edit, FakeRunner(), project=project)
    assert row["state"] == "ok"
    assert row["message"] == "rendered 1 clips; 2 text planes render in client mode"


def test_default_runner_routes_through_subprocess_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    edit = _edit(tmp_path)
    calls: list[tuple[list[str], dict[str, bool]]] = []

    def fake_run(
        argv: list[str], *, check: bool, capture_output: bool, text: bool
    ) -> FakeProc:
        """Fake the real subprocess module for the default seam.

        Args:
            argv: Command vector.
            check: Seam keyword.
            capture_output: Seam keyword.
            text: Seam keyword.

        Returns:
            A zero-exit proc.
        """
        calls.append((list(argv), {"check": check, "capture_output": capture_output,
                                   "text": text}))
        Path(argv[-1]).parent.mkdir(parents=True, exist_ok=True)
        Path(argv[-1]).write_text("stub", encoding="utf-8")
        return FakeProc(0)

    monkeypatch.setattr(render_server.subprocess, "run", fake_run)
    row = start_render(
        edit,
        _project(),
        mode="server",
        which=lambda _name: "/usr/bin/ffmpeg",
        now=_clock,
    )
    assert row["state"] == "ok"
    assert calls[0][1] == {"check": False, "capture_output": True, "text": True}


def test_start_render_rejects_unknown_mode(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="bad render mode"):
        start_render(_edit(tmp_path), _project(), mode=_raw("gpu"))


def test_client_row_stays_pending_for_the_panel(tmp_path: Path) -> None:
    edit = _edit(tmp_path)
    runner = FakeRunner()
    row = start_render(
        edit,
        _project(),
        mode="client",
        client_id="br-1",
        runner=runner,
        now=_clock,
    )
    assert row["state"] == "pending"
    assert row["kind"] == CLIENT_KIND
    assert row["mode"] == "client"
    assert row["client_id"] == "br-1"
    assert row["message"] == CLIENT_WAIT_MESSAGE
    assert runner.calls == []
    assert read_job(edit, row["id"])["state"] == "pending"


def test_client_row_without_client_id_fails(tmp_path: Path) -> None:
    row = start_render(_edit(tmp_path), _project(), mode="client", now=_clock)
    assert row["state"] == "failed"
    assert row["kind"] == CLIENT_KIND
    assert row["message"] == CLIENT_ID_MESSAGE


def test_claim_transitions_and_two_claims_never_share_one_job(
    tmp_path: Path,
) -> None:
    edit = _edit(tmp_path)
    write_job(edit, _row("z-job", created_at="2026-01-01T00:00:00+00:00"))
    write_job(edit, _row("a-job", created_at="2026-01-02T00:00:00+00:00"))
    first = claim_next_client_job(edit, "br")
    assert first is not None and first["id"] == "z-job"
    assert first["state"] == "running"
    assert first["message"] == CLAIMED_MESSAGE
    second = claim_next_client_job(edit, "br")
    assert second is not None and second["id"] == "a-job"
    assert claim_next_client_job(edit, "br") is None
    assert read_job(edit, "z-job")["state"] == "running"
    assert read_job(edit, "a-job")["state"] == "running"


def test_claim_requires_matching_client_and_empty_queue(tmp_path: Path) -> None:
    edit = _edit(tmp_path)
    assert claim_next_client_job(edit, "br") is None
    assert claim_next_client_job(edit, "") is None
    write_job(edit, _row("other", client_id="someone-else"))
    write_job(edit, _row("srv-row", kind=SERVER_KIND, state="pending"))
    assert claim_next_client_job(edit, "br") is None
    assert read_job(edit, "other")["state"] == "pending"
    claimed = claim_next_client_job(edit, "someone-else")
    assert claimed is not None and claimed["id"] == "other"
    assert claim_next_client_job(edit, "someone-else") is None


def test_complete_client_job_ok_and_default_messages(tmp_path: Path) -> None:
    edit = _edit(tmp_path)
    write_job(edit, _row("j1"))
    done = complete_client_job(
        edit, "j1", ok=True, out_path="renders/x.webm", message="done", now=_clock
    )
    assert done["state"] == "ok"
    assert done["out_path"] == "renders/x.webm"
    assert done["message"] == "done"
    write_job(edit, _row("j2"))
    default_ok = complete_client_job(edit, "j2", ok=True, out_path="./out/y.webm")
    assert default_ok["out_path"] == "out/y.webm"
    assert default_ok["message"] == "rendered in the browser"
    assert default_ok["updated_at"] != default_ok["created_at"]
    write_job(edit, _row("j3"))
    failed = complete_client_job(edit, "j3", ok=False)
    assert failed["state"] == "failed"
    assert failed["out_path"] == ""
    assert failed["message"] == "browser render failed"
    write_job(edit, _row("j4"))
    noted = complete_client_job(edit, "j4", ok=False, message="gpu hiccup")
    assert noted["message"] == "gpu hiccup"


def test_complete_client_job_requires_safe_out_path(tmp_path: Path) -> None:
    edit = _edit(tmp_path)
    write_job(edit, _row("j1"))
    with pytest.raises(ValueError, match="needs an out_path"):
        complete_client_job(edit, "j1", ok=True, out_path="", now=_clock)
    with pytest.raises(ValueError, match="needs an out_path"):
        complete_client_job(edit, "j1", ok=True, out_path="   ", now=_clock)
    with pytest.raises(ValueError, match="unsafe client output path"):
        complete_client_job(edit, "j1", ok=True, out_path="/abs/x.webm", now=_clock)
    with pytest.raises(ValueError, match="unsafe client output path"):
        complete_client_job(edit, "j1", ok=True, out_path="renders/../x.webm", now=_clock)
    assert read_job(edit, "j1")["state"] == "pending"


def test_complete_client_job_rejects_server_rows(tmp_path: Path) -> None:
    edit = _edit(tmp_path)
    write_job(edit, _row("srv", kind=SERVER_KIND))
    with pytest.raises(ValueError, match="not exec_client"):
        complete_client_job(edit, "srv", ok=True, out_path="renders/x.mp4")


def test_read_job_missing_and_corrupt_rows(tmp_path: Path) -> None:
    edit = _edit(tmp_path)
    with pytest.raises(FileNotFoundError, match="missing edit job"):
        read_job(edit, "nope")
    jobs_dir(edit).mkdir(parents=True, exist_ok=True)
    job_path(edit, "garbage").write_text("{nope", encoding="utf-8")
    with pytest.raises(ValueError):
        read_job(edit, "garbage")
    job_path(edit, "listy").write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid edit job"):
        read_job(edit, "listy")
    jobs_dir(edit).mkdir(parents=True, exist_ok=True)
    (jobs_dir(edit) / "dir.json").mkdir()
    with pytest.raises(FileNotFoundError):
        read_job(edit, "dir")


def test_read_job_fills_missing_fields_with_defaults(tmp_path: Path) -> None:
    edit = _edit(tmp_path)
    jobs_dir(edit).mkdir(parents=True, exist_ok=True)
    job_path(edit, "j1").write_text('{"id": "j1"}', encoding="utf-8")
    row = read_job(edit, "j1")
    assert row["kind"] == SERVER_KIND
    assert row["state"] == "pending"
    assert row["mode"] == "server"
    assert row["message"] == ""
    assert row["client_id"] == ""


def test_tick_job_updates_only_what_it_is_given(tmp_path: Path) -> None:
    edit = _edit(tmp_path)
    write_job(edit, _row("j1", message="before"))
    untouched = tick_job(edit, "j1")
    assert untouched["state"] == "pending"
    assert untouched["message"] == "before"
    assert untouched["out_path"] == ""
    assert untouched["updated_at"] != STAMP
    advanced = tick_job(
        edit, "j1", state="running", message="", out_path="renders/a.mp4", now=_clock
    )
    assert advanced["state"] == "running"
    assert advanced["message"] == "before"
    assert advanced["out_path"] == "renders/a.mp4"
    assert advanced["updated_at"] == STAMP
    with pytest.raises(ValueError, match="bad job state"):
        tick_job(edit, "j1", state=_raw("done"))
    with pytest.raises(FileNotFoundError):
        tick_job(edit, "ghost", state="ok")


def test_list_jobs_orders_by_created_then_id(tmp_path: Path) -> None:
    edit = _edit(tmp_path)
    write_job(edit, _row("b", project_id="p1", created_at="2026-01-02T00:00:00+00:00"))
    write_job(edit, _row("a", project_id="p2", created_at="2026-01-02T00:00:00+00:00"))
    write_job(edit, _row("c", project_id="p1", created_at="2026-01-01T00:00:00+00:00"))
    assert [row["id"] for row in list_jobs(edit)] == ["c", "a", "b"]
    assert [row["id"] for row in list_jobs(edit, "p1")] == ["c", "b"]


def test_list_jobs_skips_corrupt_rows_and_missing_dir(tmp_path: Path) -> None:
    edit = _edit(tmp_path)
    assert list_jobs(edit) == []
    write_job(edit, _row("good"))
    jobs_dir(edit).mkdir(parents=True, exist_ok=True)
    (jobs_dir(edit) / "corrupt.json").write_text("{oops", encoding="utf-8")
    (jobs_dir(edit) / "list.json").write_text("[1]", encoding="utf-8")
    (jobs_dir(edit) / "dir.json").mkdir()
    assert [row["id"] for row in list_jobs(edit)] == ["good"]


def test_write_job_slugs_the_id_and_leaves_no_tmp(tmp_path: Path) -> None:
    edit = _edit(tmp_path)
    row = _row("  spaced id ")
    write_job(edit, row)
    path = jobs_dir(edit) / "spaced-id.json"
    assert path.is_file()
    assert not (jobs_dir(edit) / "spaced-id.json.tmp").exists()
    assert json.loads(path.read_text(encoding="utf-8"))["id"] == "  spaced id "


def test_path_helpers_slug_ids_and_names(tmp_path: Path) -> None:
    edit = _edit(tmp_path)
    assert jobs_dir(edit) == edit / "jobs"
    assert renders_dir(edit) == edit / "renders"
    assert job_path(edit, "we/ird").name == "we-ird.json"
    assert job_path(edit, "***").name == "job.json"
    assert render_path(edit, "", "").name == "project-job.mp4"
    assert render_path(edit, "prj 1", "j1").name == "prj-1-j1.mp4"


def test_start_render_writes_running_message_before_runner(tmp_path: Path) -> None:
    edit = _edit(tmp_path)

    def message_probe() -> str:
        """Read the lone persisted row's message mid-render.

        Returns:
            Row message, or empty when no row exists yet.
        """
        files = sorted(jobs_dir(edit).glob("*.json"))
        if not files:
            return ""
        return read_job(edit, files[0].stem)["message"]

    runner = FakeRunner(state_probe=message_probe)
    _start_server(edit, runner)
    assert runner.states_at_call == [RUNNING_MESSAGE]
