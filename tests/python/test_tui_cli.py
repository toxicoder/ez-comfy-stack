"""The CLI is the only door into the console, so every threshold is tested here.

These tests pin the parts an operator cannot see from the screen: the flags the
wrapper forwards, the ``--check`` audit that CI leans on, the two directories
read from the environment, the single-console lock and the missing-terminal
refusal, and the fact that a real dispatch is always written to the audit log.
``curses`` is never imported: the loop is reached through stubs, which is what
lets a headless box run this file.
"""

from __future__ import annotations

import importlib
import json
import runpy
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from tui import catalog, cli, contract as c

ROOT = Path(__file__).resolve().parents[2]
"""Repository root; ``--check`` audits against the real dispatcher here."""


def _run_config(tmp_path: Path, **overrides: object) -> c.RunConfig:
    """Build a run config pointed at a throwaway directory.

    Args:
        tmp_path: Directory to point the two host paths at.
        **overrides: Fields to replace on the default config.

    Returns:
        A config safe to hand to ``make_probe`` or ``make_dispatch``.
    """
    base: dict[str, object] = {
        "repo_root": tmp_path,
        "models_dir": tmp_path / "models",
        "comfy_output_dir": tmp_path / "output",
    }
    base.update(overrides)
    return c.RunConfig(**base)  # type: ignore[arg-type]


def _make_repo(tmp_path: Path, verbs: tuple[str, ...] = ()) -> Path:
    """Lay down a directory that looks like a checkout to ``audit_catalog``.

    Args:
        tmp_path: Directory to build in.
        verbs: Extra verb lines to append to the fake dispatcher.

    Returns:
        The fake checkout root.
    """
    scripts = tmp_path / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    (scripts / "utilities").mkdir(parents=True, exist_ok=True)
    body = "\n".join(f'  {verb}) log "x" ;;' for verb in verbs)
    (scripts / "manage.sh").write_text(
        f'#!/usr/bin/env bash\ncase "${{cmd}}" in\n{body}\nesac\n', encoding="utf-8"
    )
    return tmp_path


class _Completed:
    """A :class:`subprocess.CompletedProcess` stand-in with only what is read."""

    def __init__(self, stdout: str) -> None:
        """Set the captured stdout.

        Args:
            stdout: Text the fake command "printed".
        """
        self.stdout = stdout


# -- flags -------------------------------------------------------------------


def test_parser_accepts_every_documented_flag() -> None:
    """The wrapper forwards these exact flags, so a rename is a breaking change."""
    args = cli.build_parser().parse_args(
        [
            "--check",
            "--json",
            "--dry-run",
            "--read-only",
            "--no-color",
            "--group",
            "models",
            "--timeout",
            "30",
        ]
    )
    assert args.check is True
    assert args.json is True
    assert args.dry_run is True
    assert args.read_only is True
    assert args.no_color is True
    assert args.group == "models"
    assert args.timeout == 30.0


def test_parser_defaults_to_the_interactive_dashboard() -> None:
    """No flags means the operator gets the console, in color, with the cap."""
    args = cli.build_parser().parse_args([])
    assert args.check is False
    assert args.group == ""
    assert args.timeout == 900.0


# -- resolve_group -----------------------------------------------------------


def test_an_empty_group_name_opens_the_dashboard() -> None:
    """The default is the dashboard, not an error."""
    assert cli.resolve_group("") is c.Group.DASHBOARD


def test_a_group_name_is_forgiving_of_case_and_spaces() -> None:
    """An operator typing `` Sidecars `` lands in the right section."""
    assert cli.resolve_group("  SideCars ") is c.Group.SIDECARS


def test_an_unknown_group_name_raises() -> None:
    """A typo is a usage error the operator hears about, not a silent fallback."""
    with pytest.raises(ValueError, match="unknown group"):
        cli.resolve_group("nope")


# -- resolve_dirs ------------------------------------------------------------


def test_resolve_dirs_honours_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """The console reads the same two variables paths.sh does."""
    monkeypatch.setenv("MODELS_DIR", "/srv/models")
    monkeypatch.setenv("COMFY_OUTPUT_DIR", "/srv/out")
    assert cli.resolve_dirs() == (Path("/srv/models"), Path("/srv/out"))


def test_resolve_dirs_falls_back_when_they_are_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unset variable falls back rather than becoming the empty path."""
    monkeypatch.delenv("MODELS_DIR", raising=False)
    monkeypatch.delenv("COMFY_OUTPUT_DIR", raising=False)
    assert cli.resolve_dirs() == (
        Path(cli.DEFAULT_MODELS_DIR),
        Path(cli.DEFAULT_COMFY_OUTPUT_DIR),
    )


def test_resolve_dirs_treats_an_empty_value_as_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``COMFY_OUTPUT_DIR=`` is docker-compose's way of saying "not set"."""
    monkeypatch.setenv("MODELS_DIR", "")
    monkeypatch.setenv("COMFY_OUTPUT_DIR", "")
    models, output = cli.resolve_dirs()
    assert models == Path(cli.DEFAULT_MODELS_DIR)
    assert output == Path(cli.DEFAULT_COMFY_OUTPUT_DIR)


# -- repo_root_from ----------------------------------------------------------


def test_repo_root_walks_up_to_the_dispatcher() -> None:
    """The package finds the checkout that owns ``scripts/manage.sh``."""
    assert cli.repo_root_from(Path(__file__).resolve().parent) == ROOT


def test_repo_root_falls_back_to_the_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """With no dispatcher anywhere above, the cwd is the honest answer."""
    deep = tmp_path / "a" / "b"
    deep.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    assert cli.repo_root_from(deep) == tmp_path


# -- audit_catalog -----------------------------------------------------------


def test_the_real_catalog_passes_its_own_audit() -> None:
    """Against this checkout the catalog is sound; that is the CI assertion."""
    counts, defects = cli.audit_catalog(ROOT)
    assert defects == ()
    assert counts["actions"] == len(catalog.all_actions())
    assert counts["read"] + counts["write"] + counts["heavy"] == counts["actions"] - (
        counts["destructive"] + counts["refused"]
    )
    assert counts["lanes"] > 0
    assert counts["graphs"] > 0


def test_a_duplicate_action_id_is_a_defect(tmp_path: Path) -> None:
    """Two entries with one id would make the palette ambiguous."""
    _make_repo(tmp_path)
    action = c.ActionSpec(
        action_id="dup",
        title="A",
        group=c.Group.STACK,
        summary="s",
        runner=c.RunnerKind.MANAGE,
        target="status",
    )
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(cli.catalog, "all_actions", lambda: (action, action))
        _, defects = cli.audit_catalog(tmp_path)
    assert any("duplicate action ids" in d and "dup" in d for d in defects)


def test_a_missing_dispatcher_is_a_defect(tmp_path: Path) -> None:
    """Without manage.sh the completeness check cannot run, and says so."""
    _, defects = cli.audit_catalog(tmp_path)
    assert any("cannot find" in d for d in defects)


def test_an_uncovered_verb_is_a_defect(tmp_path: Path) -> None:
    """A verb the console cannot reach is exactly the gap the audit hunts."""
    _make_repo(tmp_path, verbs=("definitely-not-a-real-verb",))
    _, defects = cli.audit_catalog(tmp_path)
    assert any("definitely-not-a-real-verb" in d for d in defects)


def test_a_heavy_action_without_a_token_is_a_defect(tmp_path: Path) -> None:
    """A heavy verb the operator can run without typing is a safety defect."""
    _make_repo(tmp_path)
    action = c.ActionSpec(
        action_id="bad.heavy",
        title="A",
        group=c.Group.STACK,
        summary="s",
        runner=c.RunnerKind.MANAGE,
        target="start",
        tier=c.RiskTier.HEAVY,
    )
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(cli.catalog, "all_actions", lambda: (action,))
        _, defects = cli.audit_catalog(tmp_path)
    assert any("needs a token" in d for d in defects)


def test_a_refusal_without_a_reason_is_a_defect(tmp_path: Path) -> None:
    """The operator always deserves to know why something is greyed out."""
    _make_repo(tmp_path)
    action = c.ActionSpec(
        action_id="bad.refused",
        title="A",
        group=c.Group.STACK,
        summary="s",
        runner=c.RunnerKind.INTERNAL,
        target="nope",
        tier=c.RiskTier.REFUSED,
    )
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(cli.catalog, "all_actions", lambda: (action,))
        _, defects = cli.audit_catalog(tmp_path)
    assert any("refused without a reason" in d for d in defects)


def test_a_utility_entry_point_that_does_not_exist_is_a_defect(tmp_path: Path) -> None:
    """A utility action must name a script that is actually in the tree."""
    _make_repo(tmp_path)
    action = c.ActionSpec(
        action_id="bad.utility",
        title="A",
        group=c.Group.DISK,
        summary="s",
        runner=c.RunnerKind.UTILITY,
        target="ghost",
    )
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(cli.catalog, "all_actions", lambda: (action,))
        _, defects = cli.audit_catalog(tmp_path)
    assert any("ghost.sh" in d for d in defects)


def test_a_real_utility_entry_point_is_accepted(tmp_path: Path) -> None:
    """The same rule passes when the script is there, so it is not a false alarm."""
    _make_repo(tmp_path)
    (tmp_path / "scripts" / "utilities" / "real.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    action = c.ActionSpec(
        action_id="ok.utility",
        title="A",
        group=c.Group.DISK,
        summary="s",
        runner=c.RunnerKind.UTILITY,
        target="real",
    )
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(cli.catalog, "all_actions", lambda: (action,))
        _, defects = cli.audit_catalog(tmp_path)
    assert defects == ()


@pytest.mark.parametrize("forced", ["--yes", "LAB_CONFIRM_TOKEN=1"])
def test_a_forced_confirmation_in_fixed_args_is_a_defect(
    tmp_path: Path, forced: str
) -> None:
    """The console may never answer a confirm prompt on the operator's behalf."""
    _make_repo(tmp_path)
    action = c.ActionSpec(
        action_id="bad.forced",
        title="A",
        group=c.Group.STACK,
        summary="s",
        runner=c.RunnerKind.MANAGE,
        target="start",
        fixed_args=(forced,),
    )
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(cli.catalog, "all_actions", lambda: (action,))
        _, defects = cli.audit_catalog(tmp_path)
    assert any("must not force" in d for d in defects)


# -- run_check ---------------------------------------------------------------


def test_run_check_prints_the_human_report(capsys: pytest.CaptureFixture[str]) -> None:
    """The default report is what an operator reads before trusting the screen."""
    assert cli.run_check(ROOT, as_json=False) == c.EXIT_OK
    out = capsys.readouterr().out
    assert "catalog sound" in out
    assert "actions" in out


def test_run_check_prints_json(capsys: pytest.CaptureFixture[str]) -> None:
    """``--json`` is machine-readable for a CI step."""
    assert cli.run_check(ROOT, as_json=True) == c.EXIT_OK
    doc: dict[str, Any] = json.loads(capsys.readouterr().out)
    assert doc["defects"] == []
    assert doc["counts"]["actions"] > 0


def test_run_check_reports_defects_and_exits_usage(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A broken catalog fails the check loudly, in both output modes."""
    _, defects = cli.audit_catalog(tmp_path)
    assert defects
    assert cli.run_check(tmp_path, as_json=False) == c.EXIT_USAGE
    assert "DEFECTS" in capsys.readouterr().out
    assert cli.run_check(tmp_path, as_json=True) == c.EXIT_USAGE
    doc: dict[str, Any] = json.loads(capsys.readouterr().out)
    assert doc["defects"]


# -- make_probe --------------------------------------------------------------


def test_make_probe_shells_out_once_per_reading_and_parses_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The poll closure runs read-only argvs in the checkout and parses them."""
    seen: list[list[str]] = []

    def fake_run(argv: list[str], **kwargs: object) -> _Completed:
        """Record the argv and answer with empty JSON."""
        seen.append(argv)
        assert kwargs["cwd"] == str(tmp_path)
        assert kwargs["timeout"] == cli.PROBE_TIMEOUT_S
        assert kwargs["check"] is False
        return _Completed("{}")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    health = cli.make_probe(_run_config(tmp_path))()
    assert seen, "no probe ran"
    assert all("/scripts/" in argv[0] for argv in seen)
    assert seen[0] == [str(tmp_path / "scripts" / "manage.sh"), "status", "--json"]
    assert health["stack_state"] == "unknown"


def test_make_probe_survives_a_failing_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A wedged docker still leaves the console drawble, with an error line."""

    def boom(argv: list[str], **kwargs: object) -> _Completed:
        """Pretend every probe timed out.

        Args:
            argv: The argv that would have run.
            **kwargs: Ignored.

        Returns:
            A completed process with no output.
        """
        raise subprocess.TimeoutExpired(argv, 1)

    monkeypatch.setattr(cli.subprocess, "run", boom)
    health = cli.make_probe(_run_config(tmp_path))()
    assert health["errors"]


# -- make_dispatch -----------------------------------------------------------


def test_make_dispatch_runs_and_audits(tmp_path: Path) -> None:
    """Every dispatch lands in the audit log, which is the operator's receipt."""
    from tui import runner

    recorded: list[tuple[c.CommandResult, Path]] = []
    result = c.CommandResult(
        action_id="stack.start",
        argv=("scripts/manage.sh", "start"),
        returncode=0,
        output="",
        duration_s=0.1,
        ran=True,
    )
    action = c.ActionSpec(
        action_id="stack.start",
        title="A",
        group=c.Group.STACK,
        summary="s",
        runner=c.RunnerKind.MANAGE,
        target="start",
    )
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(runner, "run_action", lambda *a, **k: result)
        patch.setattr(runner, "record", lambda res, audit: recorded.append((res, audit)))
        got = cli.make_dispatch(_run_config(tmp_path))(action, {"tier": "fast"}, "yes")
    assert got is result
    assert recorded == [(result, runner.audit_path(tmp_path / "output"))]


def test_make_dispatch_passes_the_operator_answers_through(tmp_path: Path) -> None:
    """The typed token and the answers reach the runner unchanged."""
    from tui import runner

    seen: dict[str, object] = {}

    def spy(action: c.ActionSpec, answers: Mapping[str, str], **kwargs: object) -> c.CommandResult:
        """Capture the call.

        Args:
            action: The action selected.
            answers: The form answers.
            **kwargs: The keyword arguments under test.

        Returns:
            A blocked result; nothing is executed.
        """
        seen["action"] = action
        seen["answers"] = answers
        seen.update(kwargs)
        return c.CommandResult(
            action_id=action.action_id,
            argv=(),
            returncode=c.UNMEASURED,
            output="",
            duration_s=0.0,
            ran=False,
            note="blocked",
        )

    action = c.ActionSpec(
        action_id="stack.start",
        title="A",
        group=c.Group.STACK,
        summary="s",
        runner=c.RunnerKind.MANAGE,
        target="start",
    )
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(runner, "run_action", spy)
        patch.setattr(runner, "record", lambda res, audit: None)
        cli.make_dispatch(_run_config(tmp_path, dry_run=True))(action, {"a": "b"}, "DELETE")
    assert seen["action"] is action
    assert seen["answers"] == {"a": "b"}
    assert seen["typed_token"] == "DELETE"
    assert seen["dry_run"] is True
    assert seen["repo_root"] == tmp_path


# -- launch ------------------------------------------------------------------


def test_launch_wires_the_parts_and_returns_the_loop_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``launch`` is the only place the console's modules meet, so it is pinned."""
    import tui.screen

    built: dict[str, object] = {}

    class FakeConsole:
        """Console stand-in that records the wiring and reports a code."""

        def __init__(self, config: c.RunConfig, **kwargs: object) -> None:
            """Remember the config and every injected collaborator.

            Args:
                config: The resolved run configuration.
                **kwargs: Injected collaborators.
            """
            built["config"] = config
            built.update(kwargs)

        def run(self) -> int:
            """Return a canned loop exit code.

            Returns:
                The code ``launch`` is expected to hand back.
            """
            return 7

    def fake_with_screen(on_screen: Callable[[Any], int]) -> int:
        """Run the builder against a stand-in screen.

        Args:
            on_screen: The builder ``launch`` passed.

        Returns:
            Whatever the builder returned.
        """
        return on_screen(SimpleNamespace())

    fake_app = SimpleNamespace(Console=FakeConsole)
    monkeypatch.setitem(sys.modules, "tui.app", fake_app)
    # `from tui import app` prefers the package attribute, so both must be stubbed.
    monkeypatch.setattr(importlib.import_module("tui"), "app", fake_app, raising=False)
    monkeypatch.setattr(tui.screen, "run_with_screen", fake_with_screen)
    config = _run_config(tmp_path)
    assert cli.launch(config) == 7
    assert built["config"] is config
    assert set(built) == {
        "config",
        "screen",
        "actions",
        "evaluate",
        "probe",
        "dispatch",
        "lane_source",
        "graph_source",
    }
    assert callable(built["probe"])
    assert callable(built["dispatch"])
    assert built["lane_source"] is cli.lanes.lanes
    assert built["graph_source"] is cli.lanes.graphs


# -- main --------------------------------------------------------------------


def test_main_hands_argparse_a_help_exit_back_as_zero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--help`` is a success, and the wrapper must not turn it into a failure."""
    capsys.readouterr()
    assert cli.main(["--help"]) == c.EXIT_OK


def test_main_rejects_an_unknown_flag() -> None:
    """A typo is usage error 1, not a traceback."""
    assert cli.main(["--nope"]) == c.EXIT_USAGE


def test_main_runs_the_check_without_a_terminal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``--check`` never needs a tty, which is why CI can call it."""
    monkeypatch.setattr(cli, "run_check", lambda root, *, as_json: c.EXIT_OK)
    assert cli.main(["--check"]) == c.EXIT_OK


def test_main_rejects_a_non_positive_timeout() -> None:
    """A zero timeout would kill every child the moment it starts."""
    assert cli.main(["--timeout", "0"]) == c.EXIT_USAGE


def test_main_rejects_an_unknown_group() -> None:
    """A mistyped section is reported instead of silently opening the dashboard."""
    assert cli.main(["--group", "nonsense"]) == c.EXIT_USAGE


def test_main_refuses_a_second_console(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """One console at a time: a second one exits 3 and says why."""
    from tui import runner

    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setattr(
        runner.ConsoleLock, "acquire", lambda self: False, raising=True
    )
    assert cli.main([]) == c.EXIT_LOCKED
    assert "another console" in capsys.readouterr().err


def test_main_refuses_to_draw_without_a_terminal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Piping the console must fail with 2 rather than corrupt a log."""
    from tui import runner

    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setattr(runner.ConsoleLock, "acquire", lambda self: True)
    monkeypatch.setattr(runner.ConsoleLock, "release", lambda self: None)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
    assert cli.main([]) == c.EXIT_NO_TTY
    assert "--check" in capsys.readouterr().err


def test_main_launches_and_always_releases_the_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The lock is released even when the loop raises, so a crash cannot strand it."""
    from tui import runner

    released: list[bool] = []
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setattr(runner.ConsoleLock, "acquire", lambda self: True)
    monkeypatch.setattr(runner.ConsoleLock, "release", lambda self: released.append(True))
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(
        cli, "launch", lambda config: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    with pytest.raises(RuntimeError, match="boom"):
        cli.main([])
    assert released == [True]


def test_main_passes_the_resolved_flags_into_the_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """What the operator typed is what the loop is handed, unmangled."""
    from tui import runner

    seen: list[c.RunConfig] = []
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("MODELS_DIR", str(tmp_path / "m"))
    monkeypatch.setattr(runner.ConsoleLock, "acquire", lambda self: True)
    monkeypatch.setattr(runner.ConsoleLock, "release", lambda self: None)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    def fake_launch(config: c.RunConfig) -> int:
        """Record the config the operator's flags resolved to.

        Args:
            config: The config ``main`` built from argv.

        Returns:
            Zero, the way a console that exited cleanly would.
        """
        seen.append(config)
        return 0

    monkeypatch.setattr(cli, "launch", fake_launch)
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert cli.main(["--dry-run", "--read-only", "--group", "lanes", "--timeout", "5"]) == 0
    config = seen[0]
    assert config.dry_run is True
    assert config.read_only is True
    assert config.start_group is c.Group.LANES
    assert config.timeout_s == 5.0
    assert config.use_color is True
    assert config.models_dir == tmp_path / "m"
    assert config.comfy_output_dir == tmp_path


def test_main_respects_no_color_env_and_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``NO_COLOR`` is honoured without the flag, and the flag forces it anyway."""
    from tui import runner

    seen: list[c.RunConfig] = []
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setattr(runner.ConsoleLock, "acquire", lambda self: True)
    monkeypatch.setattr(runner.ConsoleLock, "release", lambda self: None)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(cli, "launch", seen.append)
    cli.main([])
    assert seen[0].use_color is False


def test_main_takes_argv_from_the_environment_when_none_is_given(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``main()`` with no argument reads ``sys.argv``, which is how ``-m`` works."""
    monkeypatch.setattr(sys, "argv", ["studio-tui", "--check"])
    monkeypatch.setattr(cli, "run_check", lambda root, *, as_json: c.EXIT_OK)
    assert cli.main() == c.EXIT_OK


def test_module_main_entrypoint_exits_with_the_check_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``python3 -m tui.cli`` and the wrapper reach this guard; it must exit clean."""
    monkeypatch.setattr(sys, "argv", ["studio-tui", "--check"])
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(
            str(ROOT / "scripts" / "lib" / "tui" / "cli.py"),
            run_name="__main__",
        )
    assert exc.value.code == 0
