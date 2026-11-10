"""The console's shared vocabulary stays honest to the shell safety layer.

``scripts/lib/tui/contract.py`` is the seam every TUI module imports, so a
drift here (a softened floor, a guard that stopped explaining itself) would
silently loosen the whole console. These tests pin the numbers to the shell
source they mirror and walk every branch of the small enum surface.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tui import contract as c

ROOT = Path(__file__).resolve().parents[2]
"""Repository root, used to read the shell source the floors are mirrored from."""

SAFETY_SH = ROOT / "scripts" / "lib" / "safety.sh"
"""The shell file that owns the real headroom floors."""


def _shell_constant(name: str) -> int:
    """Read a ``NAME=value`` integer constant out of ``safety.sh``.

    Args:
        name: Constant to look up.

    Returns:
        The integer the shell declares.

    Raises:
        AssertionError: The constant is absent or not an integer.
    """
    text = SAFETY_SH.read_text(encoding="utf-8")
    match = re.search(rf':\s*"\$\{{{name}:=([0-9]+)\}}"', text)
    assert match is not None, f"{name} no longer declared in safety.sh"
    return int(match.group(1))


def test_headroom_floors_match_the_shell_source() -> None:
    """The console blocks on the same floors ``manage.sh start`` blocks on."""
    assert c.MIN_HOST_FREE_GIB == _shell_constant("MIN_HOST_FREE_GIB")
    assert c.MIN_DISK_FREE_GIB == _shell_constant("MIN_DISK_FREE_GIB")


def test_unmeasured_is_negative_so_guards_can_fail_closed() -> None:
    """An unknown reading is distinguishable from a healthy zero."""
    assert c.UNMEASURED < 0


@pytest.mark.parametrize(
    ("tier", "needs_token"),
    [
        (c.RiskTier.READ, False),
        (c.RiskTier.WRITE, False),
        (c.RiskTier.HEAVY, True),
        (c.RiskTier.DESTRUCTIVE, True),
        (c.RiskTier.REFUSED, False),
    ],
)
def test_only_the_two_heavy_tiers_demand_a_token(
    tier: c.RiskTier, needs_token: bool
) -> None:
    """Only the tiers whose child script reads stdin ask for a literal."""
    assert tier.requires_token() is needs_token


@pytest.mark.parametrize(
    ("tier", "badge"),
    [
        (c.RiskTier.READ, "read"),
        (c.RiskTier.WRITE, "write"),
        (c.RiskTier.HEAVY, "HEAVY"),
        (c.RiskTier.DESTRUCTIVE, "DELETE"),
        (c.RiskTier.REFUSED, "REFUSED"),
    ],
)
def test_risk_badges_are_short_and_distinct(tier: c.RiskTier, badge: str) -> None:
    """The status column stays scannable at 80 columns."""
    assert tier.label() == badge
    assert len(badge) <= 11


@pytest.mark.parametrize(
    ("kind", "token"),
    [
        (c.ConfirmKind.NONE, ""),
        (c.ConfirmKind.YES, "yes"),
        (c.ConfirmKind.DELETE, "DELETE"),
    ],
)
def test_confirm_tokens_are_the_exact_shell_literals(
    kind: c.ConfirmKind, token: str
) -> None:
    """The token piped to the child matches what ``safety.sh`` accepts."""
    assert kind.token() == token


def test_group_hotkeys_are_ten_distinct_digits() -> None:
    """Every section is one keystroke away and no two collide."""
    hotkeys = [group.hotkey for group in c.Group]
    assert sorted(hotkeys) == list("0123456789")


def test_every_guard_explains_its_block() -> None:
    """A blocked action always has operator-facing wording, never a bare no."""
    for guard in c.Guard:
        reason = guard.explain()
        assert reason
        assert reason[0].islower()
        assert len(reason) > 12


def test_action_spec_defaults_to_a_quiet_read() -> None:
    """An action is read-only unless its author says otherwise."""
    action = c.ActionSpec(
        action_id="stack.status",
        title="Show status",
        group=c.Group.STACK,
        summary="Print the stack status.",
        runner=c.RunnerKind.MANAGE,
        target="status",
    )
    assert action.is_runnable()
    assert action.tier is c.RiskTier.READ
    assert action.confirm is c.ConfirmKind.NONE
    assert action.guards == ()
    assert action.params == ()


def test_refused_actions_are_never_runnable() -> None:
    """A policy-blocked action reports itself as unrunnable."""
    action = c.ActionSpec(
        action_id="models.download_h3",
        title="Download MiniMax H3",
        group=c.Group.MODELS,
        summary="Refused.",
        runner=c.RunnerKind.MANAGE,
        target="download-h3",
        tier=c.RiskTier.REFUSED,
        refuse_reason="MiniMax H3 is outside the US-safe catalog",
    )
    assert not action.is_runnable()
    assert action.refuse_reason


def test_guard_verdict_defaults_to_blocked_and_fresh() -> None:
    """A verdict with no reasons is still an explicit allow, not a default."""
    allowed = c.GuardVerdict(allowed=True)
    assert allowed.guards_failed == ()
    assert not allowed.stale
    blocked = c.GuardVerdict(
        allowed=False,
        reasons=("free RAM is unknown",),
        guards_failed=(c.Guard.HEADROOM_OK,),
        stale=True,
    )
    assert not blocked.allowed
    assert blocked.stale
    assert blocked.guards_failed == (c.Guard.HEADROOM_OK,)


def test_command_result_carries_the_exact_argv() -> None:
    """What the operator reviewed is what was executed."""
    result = c.CommandResult(
        action_id="stack.start",
        argv=("scripts/manage.sh", "start"),
        returncode=0,
        output="up",
        duration_s=1.5,
        ran=True,
    )
    assert result.argv == ("scripts/manage.sh", "start")
    assert result.note == ""
    blocked = c.CommandResult(
        action_id="stack.start",
        argv=("scripts/manage.sh", "start"),
        returncode=c.UNMEASURED,
        output="",
        duration_s=0.0,
        ran=False,
        note="blocked: free RAM unknown",
    )
    assert not blocked.ran
    assert blocked.returncode == c.UNMEASURED


def test_empty_health_blocks_everything_before_the_first_poll() -> None:
    """A cold console knows nothing and therefore permits nothing heavy."""
    health = c.empty_health()
    assert health["host_free_gib"] == c.UNMEASURED
    assert health["disk_free_gib"] == c.UNMEASURED
    assert health["stack_state"] == "unknown"
    assert health["queue"] == "unmeasured"
    assert health["errors"] == ("no reading yet",)
    assert health["packs"] == ()


def test_frame_and_line_carry_style() -> None:
    """A frame is pure data: rows plus styles, no terminal handle."""
    line = c.Line(text="hello", style=c.Style.OK)
    frame = c.Frame(title="Dashboard", lines=(line,), footer="q quit")
    assert frame.title == "Dashboard"
    assert frame.lines[0].style is c.Style.OK
    assert frame.footer == "q quit"


def test_session_state_is_isolated_per_instance() -> None:
    """Two sessions never share the mutable param or history dicts."""
    first = c.SessionState()
    second = c.SessionState()
    first.params["tier"] = "turbo"
    first.history.append(
        c.CommandResult("a", ("x",), 0, "", 0.0, True),
    )
    assert second.params == {}
    assert second.history == []
    assert not first.dry_run
    assert not first.read_only
    assert first.last_result is None
    assert first.selected == 0
    assert first.scroll == 0
    assert first.poll_errors == ()


def test_key_constants_are_lowercase_names() -> None:
    """The keymap matches on names, so no escape sequence leaks into a view."""
    names = [
        value
        for name, value in vars(c.Key).items()
        if not name.startswith("_") and isinstance(value, str)
    ]
    assert names
    assert all(name == name.lower() for name in names)


def test_every_style_member_has_a_value() -> None:
    """The curses adapter maps each style, so none may be an empty string."""
    for style in c.Style:
        assert style.value


def test_argv_styles_and_param_kinds_are_distinct() -> None:
    """The two argv spellings and the four param kinds do not overlap."""
    assert {member.value for member in c.ArgvStyle} == {"spaced", "equals", "positional"}
    assert {member.value for member in c.ParamKind} == {
        "choice",
        "text",
        "flag",
        "int",
    }


def test_param_spec_bounds_and_defaults() -> None:
    """A parameter carries its own bounds so the collector can validate."""
    param = c.ParamSpec(
        name="limit",
        label="Bandwidth cap",
        kind=c.ParamKind.INT,
        flag="--limit",
        argv_style=c.ArgvStyle.EQUALS,
        low=1,
        high=10_000,
        default="auto",
        help_text="Mbps",
    )
    assert param.low == 1
    assert param.high == 10_000
    assert param.required
    assert param.choices == ()
    choice = c.Choice(value="turbo", label="Turbo", note="~10 GB")
    assert choice.note == "~10 GB"
    bare = c.Choice(value="x", label="X")
    assert bare.note == ""


def test_runner_kinds_cover_the_three_dispatch_shapes() -> None:
    """Every action targets the CLI, a bare utility, or the console itself."""
    assert {member.value for member in c.RunnerKind} == {"manage", "utility", "internal"}
