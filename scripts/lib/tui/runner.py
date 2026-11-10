"""Execute exactly one catalog action, and nothing else.

The console's whole blast radius lives in this module: one
:class:`~tui.contract.ActionSpec` goes in, one child process comes out. The
argument list is built by :func:`tui.contract.build_argv` and prefixed with the
entry point that owns the target -- ``scripts/manage.sh <verb>`` for a CLI verb,
``scripts/utilities/<name>.sh`` for a bare utility -- and is then handed to
``subprocess.run`` as a plain list in its default exec mode. There is no shell
mode anywhere in this file, so there is no string to quote and no second command
an operator can smuggle in behind a parameter answer.

The child gets a purpose-built environment rather than a copy of the console's.
The two variables that would answer a confirm prompt on the operator's behalf,
``LAB_NON_INTERACTIVE`` and ``LAB_CONFIRM_TOKEN``, are stripped even when the
console itself was launched with them set, so ``require_heavy_confirm`` and
``require_delete_confirm`` in ``scripts/lib/safety.sh`` stay live and read what
the operator actually typed. The typed token is the only thing this module ever
writes to the child's stdin.

Every dispatch is appended to a JSONL audit line under the Comfy output dir,
and only one console at a time may hold the flock that guards that directory.
"""

from __future__ import annotations

import fcntl
import json
import os
import subprocess
import time
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO, TypeAlias

from tui.contract import (
    UNMEASURED,
    ActionSpec,
    CommandResult,
    ConfirmKind,
    RunnerKind,
    build_argv,
)

Spawn: TypeAlias = Callable[
    [tuple[str, ...], Mapping[str, str], str | None, float],
    tuple[int, str],
]
"""Run ``argv`` in ``env``, feed it ``stdin_text``, return ``(returncode, output)``.

The fourth positional argument is the timeout in seconds. Production uses
:func:`default_spawn`; a test injects its own fake so no real process starts.
"""

LOCK_FILENAME = ".studio-tui.lock"
"""Name of the single-console flock file inside the Comfy output dir."""

AUDIT_FILENAME = ".studio-tui-audit.jsonl"
"""Name of the append-only dispatch log inside the Comfy output dir."""

_PASSTHROUGH_ENV: tuple[str, ...] = ("NO_COLOR", "LANG", "TERM")
"""Host variables copied into the child because they only change presentation."""

_FORBIDDEN_ENV: frozenset[str] = frozenset({"LAB_NON_INTERACTIVE", "LAB_CONFIRM_TOKEN"})
"""Variables that would answer a confirm prompt for the child; never forwarded."""

_DEFAULT_PATH = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
"""``PATH`` used when the console was started without one."""


def child_env(repo_root: Path, extra: Mapping[str, str]) -> dict[str, str]:
    """Build the environment every action child runs with.

    The environment is assembled from scratch instead of copied from
    ``os.environ``: a script that changes behavior because a variable happens
    to be set in the console's session is a worse failure than a script that
    sees a clean one. The confirm overrides are dropped last, so they cannot
    arrive through ``extra`` either.

    Args:
        repo_root: Repository root the scripts live under.
        extra: Variables this action needs on top of the baseline.

    Returns:
        The child environment, guaranteed free of the confirm overrides.
    """
    env: dict[str, str] = {
        "PATH": os.environ.get("PATH") or _DEFAULT_PATH,
        "HOME": os.environ.get("HOME") or str(Path.home()),
        "REPO_ROOT": str(repo_root),
        "PYTHONPATH": os.pathsep.join(
            (str(repo_root / "custom_nodes"), str(repo_root / "scripts" / "lib"))
        ),
    }
    for key in _PASSTHROUGH_ENV:
        value = os.environ.get(key)
        if value is not None:
            env[key] = value
    env.update(extra)
    return {name: value for name, value in env.items() if name not in _FORBIDDEN_ENV}


def command_argv(
    repo_root: Path,
    action: ActionSpec,
    answers: Mapping[str, str],
) -> tuple[str, ...]:
    """Prefix the action's arguments with the script that owns its target.

    Args:
        repo_root: Repository root the scripts live under.
        action: The catalog entry being dispatched.
        answers: Operator answers keyed by :attr:`~tui.contract.ParamSpec.name`.

    Returns:
        The full argv, executable first, as a plain tuple of strings.

    Raises:
        ValueError: The action is handled inside the console, or an answer is
            invalid for its parameter.
    """
    argv = build_argv(action, answers)
    if action.runner is RunnerKind.MANAGE:
        return (str(repo_root / "scripts" / "manage.sh"), action.target, *argv)
    if action.runner is RunnerKind.UTILITY:
        return (str(repo_root / "scripts" / "utilities" / f"{action.target}.sh"), *argv)
    raise ValueError(f"{action.action_id}: internal actions are dispatched in the console")


def default_spawn(
    argv: tuple[str, ...],
    env: Mapping[str, str],
    stdin_text: str | None,
    timeout_s: float,
) -> tuple[int, str]:
    """Run the argv as a real child process.

    ``subprocess.run`` gets a list and no ``shell``, so the argv the operator
    reviewed is exactly what ``execve`` sees. stdout and stderr are merged,
    because the operator reads them as one transcript.

    Args:
        argv: Full argv, executable first.
        env: Environment for the child.
        stdin_text: Text piped to the child, or None when it asks nothing.
        timeout_s: Seconds before the child is killed.

    Returns:
        ``(returncode, merged output)``.
    """
    completed = subprocess.run(
        list(argv),
        env=dict(env),
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=timeout_s,
    )
    streams = [part for part in (completed.stdout, completed.stderr) if part]
    return (completed.returncode, "\n".join(streams))


def _blocked(action: ActionSpec, argv: tuple[str, ...], note: str) -> CommandResult:
    """Build the result of a dispatch that never started.

    Args:
        action: The catalog entry that was stopped.
        argv: The argv that would have run.
        note: Why nothing ran.

    Returns:
        A result marked not-run with an unmeasurable return code.
    """
    return CommandResult(
        action_id=action.action_id,
        argv=argv,
        returncode=UNMEASURED,
        output="",
        duration_s=0.0,
        ran=False,
        note=note,
    )


def run_action(
    action: ActionSpec,
    answers: Mapping[str, str],
    *,
    repo_root: Path,
    dry_run: bool = False,
    typed_token: str = "",
    timeout_s: float = 900.0,
    spawn: Spawn | None = None,
) -> CommandResult:
    """Dispatch one action and report what came back.

    The checks run in a fixed order so an operator always learns the most
    important thing first: policy refuses the action outright, then a dry run
    stops before anything starts, then the typed token gate runs, and only then
    does a process exist. A refusal never raises: the app loop has to be able to
    show the reason and stay alive.

    Args:
        action: The catalog entry to run.
        answers: Operator answers keyed by parameter name.
        repo_root: Repository root the scripts live under.
        dry_run: Report the argv without starting anything.
        typed_token: What the operator retyped at the confirm dialog.
        timeout_s: Seconds before the child is killed.
        spawn: Process runner to use; the real one when None.

    Returns:
        A :class:`~tui.contract.CommandResult` for this one dispatch.
    """
    if not action.is_runnable():
        return CommandResult(
            action_id=action.action_id,
            argv=(),
            returncode=UNMEASURED,
            output="",
            duration_s=0.0,
            ran=False,
            note=action.refuse_reason or "refused by policy",
        )
    argv = command_argv(repo_root, action, answers)
    if dry_run:
        return _blocked(action, argv, "dry run")
    token = action.confirm.token()
    if token and typed_token != token:
        return _blocked(action, argv, "confirmation declined")
    runner: Spawn = default_spawn if spawn is None else spawn
    stdin_text = f"{token}\n" if action.confirm is not ConfirmKind.NONE else None
    started = time.monotonic()
    try:
        returncode, output = runner(argv, child_env(repo_root, {}), stdin_text, timeout_s)
    except subprocess.TimeoutExpired:
        return CommandResult(
            action_id=action.action_id,
            argv=argv,
            returncode=UNMEASURED,
            output="",
            duration_s=time.monotonic() - started,
            ran=True,
            note=f"timed out after {timeout_s:g} s",
        )
    return CommandResult(
        action_id=action.action_id,
        argv=argv,
        returncode=returncode,
        output=output,
        duration_s=time.monotonic() - started,
        ran=True,
    )


def audit_path(comfy_output_dir: Path) -> Path:
    """Locate the dispatch log for one Comfy output directory.

    Args:
        comfy_output_dir: Directory the console writes under.

    Returns:
        Path of the JSONL audit file, which need not exist yet.
    """
    return comfy_output_dir / AUDIT_FILENAME


def record(result: CommandResult, audit: Path) -> None:
    """Append one dispatch to the audit log.

    The audit is an operator nicety, never a reason to lose the console: a log
    that cannot be written (read-only disk, an output dir that is not a
    directory) is dropped silently and the dispatch still stands.

    Args:
        result: The dispatch to log.
        audit: Destination file, as returned by :func:`audit_path`.
    """
    row = {
        "action_id": result.action_id,
        "argv": " ".join(result.argv),
        "returncode": result.returncode,
        "duration_s": round(result.duration_s, 3),
        "ran": result.ran,
        "note": result.note,
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    try:
        audit.parent.mkdir(parents=True, exist_ok=True)
        with audit.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    except OSError:
        return


class ConsoleLock:
    """Single-console guard so two TUIs never drive the same stack at once.

    The lock is an ``flock`` on a file inside the Comfy output dir: it is held
    by the open file description, so it dies with the process and never outlives
    a crashed console. Acquiring never raises; the reason a lock could not be
    taken is kept for the UI to show.
    """

    def __init__(self, comfy_output_dir: Path) -> None:
        """Point the lock at the directory that holds it.

        Args:
            comfy_output_dir: Directory the console writes under.
        """
        self._dir = comfy_output_dir
        self._handle: TextIO | None = None
        self._reason = ""

    @property
    def path(self) -> Path:
        """The lock file itself.

        Returns:
            ``<comfy_output_dir>/.studio-tui.lock``.
        """
        return self._dir / LOCK_FILENAME

    @property
    def reason(self) -> str:
        """Why the last acquire failed.

        Returns:
            An operator-facing sentence naming what stopped the last acquire,
            empty when the lock was taken.
        """
        return self._reason

    def acquire(self) -> bool:
        """Take the lock without waiting.

        Returns:
            True when this console holds the lock; False when another console
            holds it or the directory cannot be written.
        """
        if self._handle is not None:
            return True
        try:
            handle = self.path.open("a+", encoding="utf-8")
        except OSError as exc:
            self._reason = f"cannot open {self.path}: {exc}"
            return False
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            handle.close()
            self._reason = f"another console holds {self.path} ({exc.strerror})"
            return False
        self._reason = ""
        self._handle = handle
        return True

    def release(self) -> None:
        """Drop the lock; safe to call more than once and safe to call unheld."""
        if self._handle is None:
            return
        handle = self._handle
        self._handle = None
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()
