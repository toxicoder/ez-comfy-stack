"""Command-line entry point for the guarded operator console.

Two modes share one flag set. The interactive mode draws the curses console and
is the operator path. ``--check`` is the headless twin: it audits the catalog
against ``scripts/manage.sh``, proves every heavy action carries a confirmation,
and prints a report without ever touching a terminal. That is what CI and
``//:validate`` can run, and what an operator on a headless Spark checks before
trusting the screen.

Exit codes are stable because the launcher and the docs quote them: ``0`` clean,
``1`` bad flags or a catalog defect, ``2`` asked to draw without a TTY, ``3``
another console holds the single-console lock.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from tui import catalog, contract, lanes, readmodel, runner
from tui.contract import EXIT_LOCKED, EXIT_OK, EXIT_NO_TTY, EXIT_USAGE, Group

DEFAULT_MODELS_DIR = "/mnt/models"
"""Fallback for ``MODELS_DIR``, matching ``lab_models_dir`` in paths.sh."""

DEFAULT_COMFY_OUTPUT_DIR = "/mnt/comfy-output"
"""Fallback for ``COMFY_OUTPUT_DIR``, matching paths.sh."""

MANAGE_SH_RELPATH = "scripts/manage.sh"
"""The dispatcher the catalog is checked against."""

PROBE_TIMEOUT_S = 15
"""Wall-clock ceiling for one status probe, in seconds.

A probe is three short read-only commands (``manage.sh status --json``, the
occupancy read, the limit read). Anything slower than this means docker or the
GPU telemetry is wedged, and the loop should draw the stale reading and say so
rather than freeze the screen waiting on it.
"""


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for both modes.

    Returns:
        A parser whose flags match ``scripts/utilities/studio-tui.sh``.
    """
    parser = argparse.ArgumentParser(
        prog="studio-tui",
        description=(
            "Guarded operator console for ez-comfy-stack. One screen over every "
            "manage.sh verb, the model tiers, the occupancy desk, the sidecars, "
            "the cut tools, and the lab lanes."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="audit the catalog and guard wiring, print a report, exit",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="with --check, emit the report as JSON",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="dispatch prints the argv and does not run it",
    )
    parser.add_argument(
        "--read-only",
        action="store_true",
        help="only observe-only actions may dispatch",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="render monochrome",
    )
    parser.add_argument(
        "--group",
        default="",
        help="open on one section instead of the dashboard",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=900.0,
        help="per-command wall-clock cap in seconds (default 900)",
    )
    return parser


def resolve_group(name: str) -> Group:
    """Map a ``--group`` value onto a section.

    Args:
        name: Section name as typed; empty means the dashboard.

    Returns:
        The section to open on.

    Raises:
        ValueError: The name is not a section, and is not empty.
    """
    if not name:
        return Group.DASHBOARD
    for member in Group:
        if member.value == name.strip().lower():
            return member
    raise ValueError(f"unknown group {name!r}")


def resolve_dirs() -> tuple[Path, Path]:
    """Read the two host directories the console needs.

    Returns:
        ``(models_dir, comfy_output_dir)``, honouring the same environment
        variables as ``scripts/lib/paths.sh``.
    """
    models = Path(os.environ.get("MODELS_DIR") or DEFAULT_MODELS_DIR)
    output = Path(os.environ.get("COMFY_OUTPUT_DIR") or DEFAULT_COMFY_OUTPUT_DIR)
    return models, output


def repo_root_from(start: Path) -> Path:
    """Find the checkout that owns this package.

    Args:
        start: A directory to walk up from, normally the package location.

    Returns:
        The nearest ancestor that carries ``scripts/manage.sh``; falls back to
        the current working directory when none does.
    """
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / MANAGE_SH_RELPATH).is_file():
            return candidate
    return Path.cwd()


def audit_catalog(repo_root: Path) -> tuple[dict[str, int], tuple[str, ...]]:
    """Check the catalog against the dispatcher and against its own invariants.

    Args:
        repo_root: The git checkout to read ``scripts/manage.sh`` from.

    Returns:
        A ``(counts, defects)`` pair. ``counts`` summarises the catalog;
        ``defects`` is empty when the console is safe to offer.
    """
    defects: list[str] = []
    actions = catalog.all_actions()

    ids = [action.action_id for action in actions]
    if len(ids) != len(set(ids)):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        defects.append(f"duplicate action ids: {', '.join(dupes)}")

    manage_path = repo_root / MANAGE_SH_RELPATH
    if manage_path.is_file():
        missing = catalog.missing_verbs(manage_path.read_text(encoding="utf-8"))
        if missing:
            defects.append(f"verbs with no catalog entry: {', '.join(missing)}")
    else:
        defects.append(f"cannot find {manage_path} to audit verbs against")

    for action in actions:
        if action.tier.requires_token() and not action.confirm.token():
            defects.append(f"{action.action_id}: {action.tier.label()} needs a token")
        if not action.is_runnable() and not action.refuse_reason:
            defects.append(f"{action.action_id}: refused without a reason")
        if action.runner is contract.RunnerKind.UTILITY:
            utility = repo_root / "scripts" / "utilities" / f"{action.target}.sh"
            if not utility.is_file():
                defects.append(f"{action.action_id}: no {utility.relative_to(repo_root)}")
        for arg in action.fixed_args:
            if arg == "--yes" or arg.startswith("LAB_"):
                defects.append(f"{action.action_id}: fixed_args must not force {arg}")

    tiers: dict[str, int] = {}
    for action in actions:
        tiers[action.tier.value] = tiers.get(action.tier.value, 0) + 1
    counts: dict[str, int] = {
        "actions": len(actions),
        "read": tiers.get(contract.RiskTier.READ.value, 0),
        "write": tiers.get(contract.RiskTier.WRITE.value, 0),
        "heavy": tiers.get(contract.RiskTier.HEAVY.value, 0),
        "destructive": tiers.get(contract.RiskTier.DESTRUCTIVE.value, 0),
        "refused": tiers.get(contract.RiskTier.REFUSED.value, 0),
        "lanes": len(lanes.lanes(repo_root)),
        "graphs": sum(lane.graph_count for lane in lanes.lanes(repo_root)),
    }
    return counts, tuple(defects)


def run_check(repo_root: Path, *, as_json: bool) -> int:
    """Print the catalog audit.

    Args:
        repo_root: The git checkout to audit.
        as_json: Emit a JSON document instead of the human report.

    Returns:
        ``EXIT_OK`` when the catalog is sound, ``EXIT_USAGE`` otherwise.
    """
    counts, defects = audit_catalog(repo_root)
    if as_json:
        print(json.dumps({"counts": counts, "defects": list(defects)}, indent=2))
    else:
        print(f"studio-tui check: {counts['actions']} actions")
        for key in ("read", "write", "heavy", "destructive", "refused"):
            print(f"  {key:<12} {counts[key]}")
        print(f"  lanes        {counts['lanes']} ({counts['graphs']} graphs)")
        if defects:
            print(f"  DEFECTS ({len(defects)}):")
            for defect in defects:
                print(f"    - {defect}")
        else:
            print("  catalog sound")
    return EXIT_USAGE if defects else EXIT_OK


def make_probe(config: contract.RunConfig) -> Callable[[], contract.Health]:
    """Build the poll closure the loop calls on ``g`` and on entry.

    Args:
        config: Resolved run configuration.

    Returns:
        A zero-argument callable returning a fresh :class:`~tui.contract.Health`.
    """

    def run(argv: tuple[str, ...]) -> str:
        """Execute one read-only probe and return its captured stdout.

        Args:
            argv: The probe's argument list.

        Returns:
            Whatever the probe printed; the parser upstream decides what it means.
        """
        completed = subprocess.run(
            list(argv),
            cwd=str(config.repo_root),
            env=runner.child_env(config.repo_root, {}),
            capture_output=True,
            text=True,
            timeout=PROBE_TIMEOUT_S,
            check=False,
        )
        return completed.stdout

    return lambda: readmodel.probe_health(
        run,
        repo_root=config.repo_root,
        models_dir=config.models_dir,
        comfy_output_dir=config.comfy_output_dir,
    )


def make_dispatch(
    config: contract.RunConfig,
) -> Callable[[contract.ActionSpec, Mapping[str, str], str], contract.CommandResult]:
    """Build the dispatch closure the loop calls when an action is selected.

    Every run is recorded to the audit log, including the ones that were blocked,
    so the Audit pane shows what the guard refused and not only what ran.

    Args:
        config: Resolved run configuration.

    Returns:
        A callable taking ``(action, answers, typed_token)``.
    """
    audit = runner.audit_path(config.comfy_output_dir)

    def dispatch(
        action: contract.ActionSpec,
        answers: Mapping[str, str],
        typed_token: str,
    ) -> contract.CommandResult:
        """Run one action through the runner and log it.

        Args:
            action: The catalog entry the operator selected.
            answers: The parameter form's answers.
            typed_token: What the operator typed at the confirm prompt.

        Returns:
            What the child reported back.
        """
        result = runner.run_action(
            action,
            answers,
            repo_root=config.repo_root,
            dry_run=config.dry_run,
            typed_token=typed_token,
            timeout_s=config.timeout_s,
        )
        runner.record(result, audit)
        return result

    return dispatch


def launch(config: contract.RunConfig) -> int:
    """Wire the real modules into the loop and run it on a live screen.

    This is the only place the console's parts meet: the catalog supplies
    actions, the guard judges them, the read model polls, the runner dispatches,
    and the screen module alone owns curses.

    Args:
        config: Resolved run configuration.

    Returns:
        The loop's exit code.
    """
    from tui import app, guard, screen  # late: keeps --check free of curses

    def build(live_screen: contract.Screen) -> int:
        """Construct the console on the live screen and run its loop.

        Args:
            live_screen: The screen curses opened.

        Returns:
            The loop's exit code.
        """
        console = app.Console(
            config,
            screen=live_screen,
            actions=catalog.all_actions(),
            evaluate=guard.evaluate,
            probe=make_probe(config),
            dispatch=make_dispatch(config),
            lane_source=lanes.lanes,
            graph_source=lanes.graphs,
        )
        return console.run()

    return screen.run_with_screen(build)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the console or its headless check.

    Args:
        argv: Argument list; ``None`` takes ``sys.argv[1:]``.

    Returns:
        One of ``contract.EXIT_OK``, ``EXIT_USAGE``, ``EXIT_NO_TTY``,
        ``EXIT_LOCKED``.
    """
    parser = build_parser()
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
    except SystemExit as exc:  # argparse already printed the reason
        code = int(exc.code) if exc.code is not None else EXIT_USAGE
        return EXIT_OK if code == 0 else EXIT_USAGE

    root = repo_root_from(Path(__file__).resolve().parent)
    if args.check:
        return run_check(root, as_json=args.json)

    if args.timeout <= 0:
        print("[studio-tui] --timeout must be positive", file=sys.stderr)
        return EXIT_USAGE
    try:
        start_group = resolve_group(args.group)
    except ValueError as exc:
        print(f"[studio-tui] {exc}", file=sys.stderr)
        return EXIT_USAGE

    models_dir, output_dir = resolve_dirs()
    config = contract.RunConfig(
        repo_root=root,
        models_dir=models_dir,
        comfy_output_dir=output_dir,
        start_group=start_group,
        dry_run=args.dry_run,
        read_only=args.read_only,
        use_color=not (args.no_color or bool(os.environ.get("NO_COLOR"))),
        timeout_s=float(args.timeout),
    )

    lock = runner.ConsoleLock(output_dir)
    if not lock.acquire():
        print(
            "[studio-tui] another console holds the lock; close it first",
            file=sys.stderr,
        )
        return EXIT_LOCKED
    try:
        if not sys.stdout.isatty():
            print(
                "[studio-tui] stdout is not a terminal; use --check for a "
                "headless audit or run from an interactive shell",
                file=sys.stderr,
            )
            return EXIT_NO_TTY
        return launch(config)
    finally:
        lock.release()


if __name__ == "__main__":
    raise SystemExit(main())
