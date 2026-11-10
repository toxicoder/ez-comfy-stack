"""The runner dispatches exactly one catalog action, and cannot be talked into more.

These tests pin the properties that make the console safe to hand an operator:
the argv is a tuple prefixed with the script that owns the verb, nothing ever
goes through a shell, the confirm token is the only thing written to the child's
stdin, the two non-interactive overrides never reach the child, one console holds
the directory lock, and every refusal comes back as a result instead of an
exception.
"""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Mapping
from pathlib import Path

import pytest

from tui import catalog
from tui import contract as c
from tui import runner as r

ROOT = Path(__file__).resolve().parents[2]
"""Repository root, used to read the runner source in the no-shell test."""

RUNNER_SOURCE = ROOT / "scripts" / "lib" / "tui" / "runner.py"
"""The module under test, read as text for the shell-escape grep."""

_CHILD_SCRIPT = """#!/usr/bin/env python3
import os
import sys

print("out:" + " ".join(sys.argv[1:]))
print("err:" + os.environ.get("REPO_ROOT", "unset"))
print("confirm:" + os.environ.get("LAB_CONFIRM_TOKEN", "unset"))
print("noninteractive:" + os.environ.get("LAB_NON_INTERACTIVE", "unset"))
print("piped:" + (sys.stdin.readline().strip() or "none"))
sys.exit(3)
"""
"""Child the default spawn runs: it echoes its argument, its env, and its stdin."""


def _action(**overrides: object) -> c.ActionSpec:
    """Build an action, overriding only what a test cares about.

    Args:
        **overrides: Fields to replace on the default action.

    Returns:
        A catalog entry for runner tests.
    """
    base: dict[str, object] = {
        "action_id": "stack.start",
        "title": "Start the stack",
        "group": c.Group.STACK,
        "summary": "Bring ComfyUI up.",
        "runner": c.RunnerKind.MANAGE,
        "target": "start",
        "tier": c.RiskTier.HEAVY,
        "confirm": c.ConfirmKind.YES,
    }
    base.update(overrides)
    return c.ActionSpec(**base)  # type: ignore[arg-type]


def _answers_for(action: c.ActionSpec) -> dict[str, str]:
    """Give every parameter of ``action`` an answer that passes validation.

    Args:
        action: The catalog entry to answer.

    Returns:
        A mapping suitable for :func:`tui.contract.build_argv`.
    """
    answers: dict[str, str] = {}
    for param in action.params:
        if param.kind is c.ParamKind.CHOICE:
            answers[param.name] = param.default if param.default else param.choices[0].value
        elif param.kind is c.ParamKind.INT:
            answers[param.name] = str(param.default or param.low)
        elif param.kind is c.ParamKind.FLAG:
            continue
        else:
            answers[param.name] = param.default or "value"
    return answers


def _recorder(returncode: int = 0, output: str = "ok") -> _SpawnRecorder:
    """Build a spawn fake that records what it was handed.

    Args:
        returncode: Exit status the fake reports.
        output: Merged output the fake reports.

    Returns:
        A callable usable as the ``spawn`` argument of ``run_action``.
    """
    return _SpawnRecorder(returncode=returncode, output=output)


class _SpawnRecorder:
    """A :data:`tui.runner.Spawn` that records calls instead of starting work."""

    def __init__(self, returncode: int = 0, output: str = "ok") -> None:
        """Set what the fake reports back.

        Args:
            returncode: Exit status the fake reports.
            output: Merged output the fake reports.
        """
        self.returncode = returncode
        self.output = output
        self.calls: list[tuple[tuple[str, ...], dict[str, str], str | None, float]] = []
        self.raises: Exception | None = None

    def __call__(
        self,
        argv: tuple[str, ...],
        env: Mapping[str, str],
        stdin_text: str | None,
        timeout_s: float,
    ) -> tuple[int, str]:
        """Record one dispatch.

        Args:
            argv: Full argv the runner built.
            env: Environment the child would get.
            stdin_text: Text that would be piped to the child.
            timeout_s: Timeout the child would get.

        Returns:
            ``(returncode, output)`` as configured.
        """
        if self.raises is not None:
            raise self.raises
        self.calls.append((argv, dict(env), stdin_text, timeout_s))
        return (self.returncode, self.output)


def _manage_repo(tmp_path: Path) -> Path:
    """Create a fake repo root holding a runnable ``scripts/manage.sh``.

    Args:
        tmp_path: Directory to build the tree in.

    Returns:
        The fake repo root.
    """
    scripts = tmp_path / "scripts"
    scripts.mkdir(parents=True)
    script = scripts / "manage.sh"
    script.write_text(_CHILD_SCRIPT, encoding="utf-8")
    script.chmod(0o755)
    return tmp_path


def test_a_manage_action_is_prefixed_with_the_cli(tmp_path: Path) -> None:
    """A CLI verb runs ``scripts/manage.sh <verb> <args...>``, the verb once.

    The entry carries its own verb in ``fixed_args``, which is what the form and
    the confirm gate preview, so the runner adds only the executable.
    """
    action = _action(fixed_args=("start", "--now"))
    argv = r.command_argv(tmp_path, action, {})
    assert argv == (str(tmp_path / "scripts" / "manage.sh"), "start", "--now")


def test_a_utility_action_is_prefixed_with_its_script(tmp_path: Path) -> None:
    """An unmanaged utility runs ``scripts/utilities/<name>.sh`` with no verb."""
    action = _action(runner=c.RunnerKind.UTILITY, target="tail-log")
    argv = r.command_argv(tmp_path, action, {})
    assert argv == (str(tmp_path / "scripts" / "utilities" / "tail-log.sh"),)


@pytest.mark.parametrize("action", catalog.all_actions(), ids=lambda a: a.action_id)
def test_a_dispatched_verb_is_never_repeated(action: c.ActionSpec, tmp_path: Path) -> None:
    """No real entry reaches the dispatcher with its entry point named twice.

    The catalog and the runner each used to think they owned the verb, which made
    every managed action run ``manage.sh start start``. One real entry per case
    keeps that seam honest on both sides at once.

    Args:
        action: One real catalog entry.
        tmp_path: Repository root to prefix with.
    """
    if action.runner is c.RunnerKind.INTERNAL or not action.is_runnable():
        pytest.skip("nothing is executed")
    argv = r.command_argv(tmp_path, action, _answers_for(action))
    if action.runner is c.RunnerKind.MANAGE:
        assert argv[0] == str(tmp_path / "scripts" / "manage.sh")
        assert argv[1] == action.target
        assert argv[2:3] != (action.target,), f"{action.action_id}: verb doubled"
    else:
        assert argv[0] == str(tmp_path / "scripts" / "utilities" / f"{action.target}.sh")
        assert argv[1:2] != (action.target,), f"{action.action_id}: name doubled"


def test_an_internal_action_has_no_executable() -> None:
    """Navigation is handled in the console; it must never reach ``execve``."""
    action = _action(runner=c.RunnerKind.INTERNAL, target="")
    with pytest.raises(ValueError, match="internal actions"):
        r.command_argv(ROOT, action, {})


def test_a_dry_run_reports_the_argv_and_starts_nothing(tmp_path: Path) -> None:
    """The operator sees exactly what would have run, and no process exists."""
    spawn = _recorder()
    result = r.run_action(
        _action(fixed_args=("start",)),
        {},
        repo_root=tmp_path,
        dry_run=True,
        typed_token="yes",
        spawn=spawn,
    )
    assert result.ran is False
    assert result.note == "dry run"
    assert result.returncode == c.UNMEASURED
    assert result.argv == (str(tmp_path / "scripts" / "manage.sh"), "start")
    assert spawn.calls == []


def test_a_wrong_token_declines_without_starting_anything(tmp_path: Path) -> None:
    """Retyping the wrong literal stops the dispatch before the child exists."""
    spawn = _recorder()
    result = r.run_action(
        _action(),
        {},
        repo_root=tmp_path,
        typed_token="no",
        spawn=spawn,
    )
    assert result.ran is False
    assert result.note == "confirmation declined"
    assert result.returncode == c.UNMEASURED
    assert result.duration_s == 0.0
    assert spawn.calls == []


def test_an_empty_token_is_a_decline_not_an_assent(tmp_path: Path) -> None:
    """Selecting a heavy action without typing anything runs nothing."""
    spawn = _recorder()
    result = r.run_action(_action(), {}, repo_root=tmp_path, spawn=spawn)
    assert result.ran is False
    assert result.note == "confirmation declined"
    assert spawn.calls == []


def test_the_typed_token_is_the_only_thing_piped_to_the_child(tmp_path: Path) -> None:
    """The confirm answer goes to the child's stdin, which stays live for it."""
    spawn = _recorder(returncode=0, output="started")
    result = r.run_action(
        _action(), {}, repo_root=tmp_path, typed_token="yes", spawn=spawn
    )
    argv, env, stdin_text, timeout_s = spawn.calls[0]
    assert argv[0].endswith("manage.sh")
    assert stdin_text == "yes\n"
    assert timeout_s == 900.0
    assert env["REPO_ROOT"] == str(tmp_path)
    assert result.ran is True
    assert result.returncode == 0
    assert result.output == "started"


def test_a_delete_action_pipes_the_delete_literal(tmp_path: Path) -> None:
    """The destructive tier answers ``require_delete_confirm``, not ``yes``."""
    spawn = _recorder()
    r.run_action(
        _action(tier=c.RiskTier.DESTRUCTIVE, confirm=c.ConfirmKind.DELETE),
        {},
        repo_root=tmp_path,
        typed_token="DELETE",
        spawn=spawn,
    )
    assert spawn.calls[0][2] == "DELETE\n"


def test_an_action_that_asks_nothing_gets_no_stdin(tmp_path: Path) -> None:
    """A read-only verb is handed a closed stdin, not an empty line."""
    spawn = _recorder()
    r.run_action(
        _action(tier=c.RiskTier.READ, confirm=c.ConfirmKind.NONE),
        {},
        repo_root=tmp_path,
        spawn=spawn,
    )
    assert spawn.calls[0][2] is None


def test_a_refused_action_never_reaches_the_runner(tmp_path: Path) -> None:
    """A policy-blocked catalog entry reports its reason and stops."""
    spawn = _recorder()
    result = r.run_action(
        _action(tier=c.RiskTier.REFUSED, refuse_reason="MiniMax H3 is off-catalog"),
        {},
        repo_root=tmp_path,
        typed_token="yes",
        spawn=spawn,
    )
    assert result.ran is False
    assert result.note == "MiniMax H3 is off-catalog"
    assert result.argv == ()
    assert result.returncode == c.UNMEASURED
    assert spawn.calls == []


def test_a_refusal_without_a_reason_still_says_no(tmp_path: Path) -> None:
    """A misconfigured refused entry cannot dispatch silently."""
    result = r.run_action(
        _action(tier=c.RiskTier.REFUSED), {}, repo_root=tmp_path, spawn=_recorder()
    )
    assert result.ran is False
    assert result.note == "refused by policy"


def test_a_timeout_becomes_a_result_not_an_exception(tmp_path: Path) -> None:
    """A wedged child is reported; the console keeps running."""
    spawn = _recorder()
    spawn.raises = subprocess.TimeoutExpired(cmd=["manage.sh", "start"], timeout=1.0)
    result = r.run_action(
        _action(),
        {},
        repo_root=tmp_path,
        typed_token="yes",
        timeout_s=1.0,
        spawn=spawn,
    )
    assert result.ran is True
    assert result.returncode == c.UNMEASURED
    assert result.note == "timed out after 1 s"
    assert result.duration_s >= 0.0


def test_the_argv_reaches_the_child_as_a_tuple_never_a_string(tmp_path: Path) -> None:
    """The spawn seam takes an argv list, so there is nothing left to parse."""
    spawn = _recorder()
    r.run_action(
        _action(fixed_args=("--tier", "turbo")),
        {},
        repo_root=tmp_path,
        typed_token="yes",
        spawn=spawn,
    )
    argv = spawn.calls[0][0]
    assert isinstance(argv, tuple)
    assert all(isinstance(part, str) for part in argv)
    assert argv[-2:] == ("--tier", "turbo")


def test_the_module_never_asks_for_a_shell() -> None:
    """No path from a keystroke to a shell; the argv is the only interface."""
    source = RUNNER_SOURCE.read_text(encoding="utf-8")
    assert "shell=True" not in source
    assert "shell = True" not in source


def test_the_default_spawn_runs_a_real_child_and_merges_the_streams(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With no injected spawn the operator's answers reach a real process."""
    monkeypatch.setenv("LAB_CONFIRM_TOKEN", "DELETE")
    monkeypatch.setenv("LAB_NON_INTERACTIVE", "1")
    repo_root = _manage_repo(tmp_path)
    result = r.run_action(
        _action(fixed_args=("status",)),
        {},
        repo_root=repo_root,
        typed_token="yes",
    )
    assert result.ran is True
    assert result.returncode == 3
    assert "out:status" in result.output
    assert "err:" + str(repo_root) in result.output
    assert "piped:yes" in result.output
    assert "confirm:unset" in result.output
    assert "noninteractive:unset" in result.output


def test_child_env_strips_the_confirm_overrides(tmp_path: Path) -> None:
    """The real prompts in the child script have to stay live.

    A console launched out of a scripted context still carries
    ``LAB_NON_INTERACTIVE`` and ``LAB_CONFIRM_TOKEN``; forwarding them would let
    the child skip ``require_heavy_confirm`` and ``require_delete_confirm``.
    """
    monkeypatch = pytest.MonkeyPatch()
    try:
        monkeypatch.setenv("LAB_NON_INTERACTIVE", "1")
        monkeypatch.setenv("LAB_CONFIRM_TOKEN", "DELETE")
        env = r.child_env(tmp_path, {"LAB_CONFIRM_TOKEN": "DELETE"})
    finally:
        monkeypatch.undo()
    assert "LAB_NON_INTERACTIVE" not in env
    assert "LAB_CONFIRM_TOKEN" not in env


def test_child_env_carries_the_paths_the_scripts_need(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The child finds the repo, the vendored nodes, and the operator's locale."""
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.setenv("HOME", "/home/operator")
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("LANG", "C.UTF-8")
    monkeypatch.setenv("TERM", "xterm-256color")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "do-not-leak")
    env = r.child_env(tmp_path, {"EZ_COMFY_TIER": "turbo"})
    assert env["PATH"] == "/usr/bin"
    assert env["HOME"] == "/home/operator"
    assert env["REPO_ROOT"] == str(tmp_path)
    assert env["PYTHONPATH"].split(os.pathsep) == [
        str(tmp_path / "custom_nodes"),
        str(tmp_path / "scripts" / "lib"),
    ]
    assert (env["NO_COLOR"], env["LANG"], env["TERM"]) == ("1", "C.UTF-8", "xterm-256color")
    assert env["EZ_COMFY_TIER"] == "turbo"
    assert "AWS_SECRET_ACCESS_KEY" not in env


def test_child_env_falls_back_when_the_console_has_no_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A console started from a bare environment still hands the child a PATH."""
    monkeypatch.delenv("PATH", raising=False)
    monkeypatch.delenv("HOME", raising=False)
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("LANG", raising=False)
    monkeypatch.delenv("TERM", raising=False)
    env = r.child_env(tmp_path, {})
    assert env["PATH"] == r._DEFAULT_PATH
    assert env["HOME"] == str(Path.home())
    assert "NO_COLOR" not in env
    assert "LANG" not in env
    assert "TERM" not in env


def test_one_console_holds_the_lock_and_the_second_is_told(tmp_path: Path) -> None:
    """Two TUIs must never drive the same stack, so the second one backs off."""
    first = r.ConsoleLock(tmp_path)
    second = r.ConsoleLock(tmp_path)
    assert first.acquire() is True
    assert first.path == tmp_path / r.LOCK_FILENAME
    assert first.reason == ""
    assert first.acquire() is True
    assert second.acquire() is False
    assert str(second.path) in second.reason
    assert "another console" in second.reason
    second.release()
    first.release()
    first.release()
    assert second.acquire() is True
    second.release()


def test_a_lock_on_an_unwritable_directory_reports_a_reason(tmp_path: Path) -> None:
    """A console that cannot write its state dir says why instead of crashing."""
    if os.geteuid() == 0:
        pytest.skip("root ignores the directory mode")
    locked_dir = tmp_path / "output"
    locked_dir.mkdir()
    locked_dir.chmod(0o500)
    try:
        lock = r.ConsoleLock(locked_dir)
        assert lock.acquire() is False
        assert "cannot open" in lock.reason
        assert lock.path.name == r.LOCK_FILENAME
        lock.release()
    finally:
        locked_dir.chmod(0o755)


def test_a_lock_on_a_missing_directory_reports_a_reason(tmp_path: Path) -> None:
    """An output dir that is not there yet is a refusal, not a crash."""
    lock = r.ConsoleLock(tmp_path / "not-created")
    assert lock.acquire() is False
    assert "cannot open" in lock.reason


def test_audit_path_names_the_jsonl_next_to_the_lock(tmp_path: Path) -> None:
    """The audit lives in the same guarded directory as the lock."""
    assert r.audit_path(tmp_path) == tmp_path / r.AUDIT_FILENAME


def test_record_appends_one_parseable_line_per_dispatch(tmp_path: Path) -> None:
    """The operator log is machine-readable and keeps the argv reviewable."""
    audit = tmp_path / "state" / r.AUDIT_FILENAME
    result = c.CommandResult(
        action_id="stack.start",
        argv=(str(tmp_path / "scripts" / "manage.sh"), "start"),
        returncode=0,
        output="up",
        duration_s=1.2345,
        ran=True,
        note="",
    )
    r.record(result, audit)
    r.record(result, audit)
    lines = audit.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    row = json.loads(lines[0])
    assert row["action_id"] == "stack.start"
    assert row["argv"].endswith("manage.sh start")
    assert row["returncode"] == 0
    assert row["duration_s"] == 1.234
    assert row["ran"] is True
    assert row["note"] == ""
    assert row["ts"].endswith("+00:00")


def test_record_never_breaks_the_console(tmp_path: Path) -> None:
    """An audit that cannot be written is dropped; the dispatch still stands."""
    blocker = tmp_path / "output"
    blocker.write_text("not a directory", encoding="utf-8")
    r.record(
        c.CommandResult("stack.stop", ("manage.sh", "stop"), 0, "", 0.5, True),
        blocker / r.AUDIT_FILENAME,
    )
    assert blocker.read_text(encoding="utf-8") == "not a directory"
