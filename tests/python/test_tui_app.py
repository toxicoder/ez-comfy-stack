"""The keystroke loop routes keys, gates dispatches, and never needs a terminal.

``scripts/lib/tui/app.py`` is the one place a key press becomes a dispatch, so
these tests drive it with a fake :class:`tui.contract.Screen` that replays
scripted keys and records the rows it was asked to draw, plus probe, guard,
dispatch, lane, and graph callbacks that record what they were handed. Nothing
here imports curses, allocates a terminal, or starts a process: the assertions
are on the rows the console drew, on the keys it rang the bell for, and on the
answers and token the injected dispatcher received.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from tui import app
from tui import contract as c
from tui import lanes as lane_lib

REPO = Path("/repo")
"""Stand-in checkout the console dispatches from; nothing reads it."""

_HEALTH = c.Health(
    stack_state="running",
    attention="kitchen",
    host_free_gib=64,
    disk_free_gib=200,
    occupancy_mode="idle",
    occupancy_orphaned=False,
    parked=False,
    queue="idle",
    llm_live=False,
    shaping=True,
    shaping_mbps=400,
    downloads_running=False,
    packs=(("klein", True),),
    errors=(),
)
"""A fully measured snapshot, so no guard fails for want of a reading."""

_ALLOWED = c.GuardVerdict(allowed=True)
"""The verdict every action gets unless a test says otherwise."""


class _FakeScreen:
    """Screen double that replays scripted keys and records drawn rows.

    Attributes:
        frames: One entry per present, each the rows drawn into that frame.
        keys_read: Keys handed back to the console, in order.
        timeouts: Per-read timeouts the console asked for.
        bells: How many times the console rang.
        clears: How many times the console erased the buffer.
        presents: How many times the console flushed a frame.
    """

    def __init__(self, keys: Sequence[str], *, rows: int = 24, cols: int = 80) -> None:
        """Load the script and the geometry.

        Args:
            keys: Keys to hand back, one per read; when the script runs out the
                double hands back one quit key, and a console that ignores it
                fails loudly rather than spinning.
            rows: Rows the terminal reports.
            cols: Columns the terminal reports.
        """
        self._keys = list(keys)
        self._rows = rows
        self._cols = cols
        self._buffer: list[tuple[int, str, c.Style]] = []
        self._quit_given = False
        self.frames: list[list[tuple[int, str, c.Style]]] = []
        self.keys_read: list[str] = []
        self.timeouts: list[float] = []
        self.bells = 0
        self.clears = 0
        self.presents = 0

    def size(self) -> tuple[int, int]:
        """The geometry the test asked for.

        Returns:
            ``(rows, cols)`` exactly as configured, including zero.
        """
        return (self._rows, self._cols)

    def clear(self) -> None:
        """Erase the recorded back buffer."""
        self._buffer = []
        self.clears += 1

    def draw(self, row: int, text: str, *, style: c.Style = c.Style.NORMAL) -> None:
        """Record one drawn row.

        Args:
            row: Zero-based row index.
            text: Row content.
            style: Drawing intent.
        """
        self._buffer.append((row, text, style))

    def present(self) -> None:
        """Flush the recorded rows as one frame."""
        self.frames.append(list(self._buffer))
        self.presents += 1

    def read_key(self, timeout_s: float) -> str:
        """Hand back the next scripted key.

        Args:
            timeout_s: The deadline the console is willing to wait.

        Returns:
            The next scripted key, or one quit key once the script runs out.

        Raises:
            AssertionError: The console asked for another key after being told
                to quit, which means it is stuck on a pane.
        """
        self.timeouts.append(timeout_s)
        if self._keys:
            key = self._keys.pop(0)
        elif not self._quit_given:
            self._quit_given = True
            key = c.Key.QUIT
        else:
            raise AssertionError("the console did not leave the loop")
        self.keys_read.append(key)
        return key

    def bell(self) -> None:
        """Count a refusal."""
        self.bells += 1


class _Backend:
    """The injected collaborators, with every call recorded.

    Attributes:
        dispatched: ``(action_id, answers, token)`` per dispatch, oldest first.
        evaluated: Action ids the guard was asked about.
        probe_calls: How often the console re-read the machine.
        lane_calls: Lane ids the graph source was asked for.
    """

    def __init__(
        self,
        *,
        health: c.Health = _HEALTH,
        verdicts: Mapping[str, c.GuardVerdict] | None = None,
        results: Mapping[str, c.CommandResult] | None = None,
        lanes: Sequence[lane_lib.Lane] = (),
        graphs: Sequence[lane_lib.Graph] = (),
    ) -> None:
        """Load the readings, verdicts, outcomes, and browse data.

        Args:
            health: The snapshot the probe returns.
            verdicts: Guard verdict per action id; allowed when absent.
            results: Outcome per action id; a clean run when absent.
            lanes: Lanes the lane source returns.
            graphs: Graphs the graph source returns.
        """
        self._health = health
        self._verdicts = dict(verdicts or {})
        self._results = dict(results or {})
        self._lanes = list(lanes)
        self._graphs = list(graphs)
        self.dispatched: list[tuple[str, dict[str, str], str]] = []
        self.evaluated: list[str] = []
        self.probe_calls = 0
        self.lane_calls: list[str] = []

    def probe(self) -> c.Health:
        """Take a snapshot.

        Returns:
            The configured health record.
        """
        self.probe_calls += 1
        return self._health

    def evaluate(self, action: c.ActionSpec, health: c.Health) -> c.GuardVerdict:
        """Judge one action against the snapshot the console holds.

        Args:
            action: The catalog entry being offered.
            health: The snapshot it is judged against.

        Returns:
            The configured verdict, or an allowed one.
        """
        self.evaluated.append(action.action_id)
        assert health == self._health
        return self._verdicts.get(action.action_id, _ALLOWED)

    def dispatch(
        self, action: c.ActionSpec, answers: Mapping[str, str], token: str
    ) -> c.CommandResult:
        """Pretend to run one action.

        Args:
            action: The catalog entry that cleared every gate.
            answers: The operator's parameter answers.
            token: The token typed at the confirm gate.

        Returns:
            The configured outcome, or a clean one.
        """
        self.dispatched.append((action.action_id, dict(answers), token))
        return self._results.get(action.action_id, _outcome(action.action_id))

    def lane_source(self, repo_root: Path) -> list[lane_lib.Lane]:
        """List the lanes.

        Args:
            repo_root: The checkout to read.

        Returns:
            The configured lanes.
        """
        assert repo_root == REPO
        return self._lanes

    def graph_source(self, repo_root: Path, lane_id: str) -> list[lane_lib.Graph]:
        """List one lane's graphs.

        Args:
            repo_root: The checkout to read.
            lane_id: The lane being opened.

        Returns:
            The configured graphs.
        """
        assert repo_root == REPO
        self.lane_calls.append(lane_id)
        return self._graphs


def _config(*, read_only: bool = False, start_group: str = "") -> c.RunConfig:
    """Build a launch config pointing at the stand-in checkout.

    Args:
        read_only: Refuse to dispatch anything but an observe-only action.
        start_group: Section to open on instead of the dashboard.

    Returns:
        A run config for the console.
    """
    return c.RunConfig(
        repo_root=REPO,
        models_dir=REPO / "models",
        comfy_output_dir=REPO / "out",
        start_group=c.Group(start_group) if start_group else c.Group.DASHBOARD,
        read_only=read_only,
    )


def _action(
    action_id: str,
    title: str,
    group: c.Group,
    *,
    tier: c.RiskTier = c.RiskTier.READ,
    confirm: c.ConfirmKind = c.ConfirmKind.NONE,
    runner: c.RunnerKind = c.RunnerKind.MANAGE,
    target: str = "",
    fixed: tuple[str, ...] = (),
    params: tuple[c.ParamSpec, ...] = (),
    refuse_reason: str = "",
    summary: str = "Prints something harmless.",
) -> c.ActionSpec:
    """Build one catalog entry.

    Args:
        action_id: Dotted id.
        title: List label.
        group: Left-rail section.
        tier: Risk tier.
        confirm: Literal the child script demands.
        runner: Which entry point owns the target.
        target: Verb or utility name; the id's last segment when empty.
        fixed: Always-present arguments.
        params: Operator-supplied arguments.
        refuse_reason: Why a refused action can never run.
        summary: One-line effect.

    Returns:
        A catalog entry for the console to offer.
    """
    return c.ActionSpec(
        action_id=action_id,
        title=title,
        group=group,
        summary=summary,
        runner=runner,
        target=target or action_id.split(".")[-1],
        fixed_args=fixed,
        params=params,
        tier=tier,
        confirm=confirm,
        refuse_reason=refuse_reason,
    )


_STATUS = _action("stack.status", "Show status", c.Group.STACK, fixed=("status",))
_STOP = _action(
    "stack.stop", "Stop the stack", c.Group.STACK, tier=c.RiskTier.WRITE, fixed=("stop",)
)
_START = _action(
    "stack.start",
    "Start the stack",
    c.Group.STACK,
    tier=c.RiskTier.HEAVY,
    confirm=c.ConfirmKind.YES,
    fixed=("start",),
)
_WIPE = _action(
    "disk.wipe",
    "Wipe the cache",
    c.Group.DISK,
    tier=c.RiskTier.REFUSED,
    refuse_reason="the wipe verb was retired",
)
_PURGE = _action(
    "disk.purge",
    "Purge the cache",
    c.Group.DISK,
    tier=c.RiskTier.DESTRUCTIVE,
    confirm=c.ConfirmKind.DELETE,
    fixed=("purge",),
)
_STACK_ACTIONS = (_STATUS, _STOP, _START)
"""The three stack verbs most sessions walk down."""

_STACK_KEY = c.Group.STACK.hotkey
"""Digit that opens the stack section."""

_LANES_KEY = c.Group.LANES.hotkey
"""Digit that opens the lane browser."""

_MODELS_KEY = c.Group.MODELS.hotkey
"""Digit that opens the models section."""

_FILM_KEY = c.Group.FILM.hotkey
"""Digit that opens the film section."""

_DISK_KEY = c.Group.DISK.hotkey
"""Digit that opens the disk section."""


def _outcome(action_id: str, *, ran: bool = True, note: str = "") -> c.CommandResult:
    """Build one dispatch outcome.

    Args:
        action_id: The action that ran.
        ran: False for a dry run or a blocked run.
        note: Trailing operator note.

    Returns:
        A command result.
    """
    return c.CommandResult(
        action_id=action_id,
        argv=("scripts/manage.sh", action_id.split(".")[-1]),
        returncode=0 if ran else c.UNMEASURED,
        output="line one\nline two",
        duration_s=1.5,
        ran=ran,
        note=note,
    )


def _choice(name: str, values: tuple[str, ...], *, default: str = "") -> c.ParamSpec:
    """Build a CHOICE parameter.

    Args:
        name: Answer key.
        values: Offered values.
        default: Pre-filled answer.

    Returns:
        A parameter spec.
    """
    return c.ParamSpec(
        name=name,
        label=name.capitalize(),
        kind=c.ParamKind.CHOICE,
        flag=f"--{name}",
        choices=tuple(c.Choice(value=value, label=value) for value in values),
        default=default,
    )


def _text(name: str, *, default: str = "") -> c.ParamSpec:
    """Build a TEXT parameter.

    Args:
        name: Answer key.
        default: Pre-filled answer.

    Returns:
        A parameter spec.
    """
    return c.ParamSpec(
        name=name, label=name.capitalize(), kind=c.ParamKind.TEXT, default=default
    )


def _int(name: str, *, low: int = 0, high: int = 1_000, default: str = "") -> c.ParamSpec:
    """Build an INT parameter.

    Args:
        name: Answer key.
        low: Inclusive lower bound.
        high: Inclusive upper bound.
        default: Pre-filled answer.

    Returns:
        A parameter spec.
    """
    return c.ParamSpec(
        name=name,
        label=name.capitalize(),
        kind=c.ParamKind.INT,
        flag=f"--{name}",
        low=low,
        high=high,
        default=default,
    )


def _download(**params: c.ParamSpec) -> c.ActionSpec:
    """Build a models action whose parameters are named per test.

    Args:
        **params: Parameters, in argv order; keyword order is the declaration
            order the form walks.

    Returns:
        A catalog entry in the models section.
    """
    return _action(
        "models.download",
        "Download a pack",
        c.Group.MODELS,
        tier=c.RiskTier.WRITE,
        fixed=("download-models",),
        params=tuple(params.values()),
    )


def _run(
    keys: Sequence[str],
    actions: Sequence[c.ActionSpec] = _STACK_ACTIONS,
    *,
    backend: _Backend | None = None,
    rows: int = 24,
    cols: int = 80,
    config: c.RunConfig | None = None,
) -> tuple[_FakeScreen, _Backend]:
    """Run a whole console session.

    Args:
        keys: The operator's keystrokes.
        actions: The catalog the console offers.
        backend: Injected collaborators; a fresh one when omitted.
        rows: Terminal rows to report.
        cols: Terminal columns to report.
        config: Launch settings; the defaults when omitted.

    Returns:
        The recording screen and the recording backend.

    Raises:
        AssertionError: The console kept asking for keys after being told to quit.
    """
    screen = _FakeScreen(keys, rows=rows, cols=cols)
    active = backend or _Backend()
    console = app.Console(
        config or _config(),
        screen=screen,
        actions=actions,
        evaluate=active.evaluate,
        probe=active.probe,
        dispatch=active.dispatch,
        lane_source=active.lane_source,
        graph_source=active.graph_source,
    )
    assert console.run() == c.EXIT_OK
    return screen, active


def _painted(screen: _FakeScreen) -> dict[int, str]:
    """Rows of the most recent frame.

    Args:
        screen: The recording screen.

    Returns:
        Row index to drawn text.
    """
    return {row: text for row, text, _style in screen.frames[-1]}


def _body(screen: _FakeScreen) -> str:
    """Everything the most recent frame drew.

    Args:
        screen: The recording screen.

    Returns:
        The frame's rows, joined.
    """
    return "\n".join(_painted(screen).values())


def _all_body(screen: _FakeScreen) -> str:
    """Everything every frame drew.

    Args:
        screen: The recording screen.

    Returns:
        Each frame's rows, joined, so an assertion can name a pane the operator
        passed through on the way to the last screen.
    """
    return "\n".join(
        "\n".join(text for _row, text, _style in frame) for frame in screen.frames
    )


def _title(screen: _FakeScreen) -> str:
    """Title of the most recent frame.

    Args:
        screen: The recording screen.

    Returns:
        The text on the row under the status bar.
    """
    return _painted(screen).get(1, "")


def _titles(screen: _FakeScreen) -> list[str]:
    """Titles of every frame the console drew.

    Args:
        screen: The recording screen.

    Returns:
        One title per frame.
    """
    return [
        next((text for row, text, _style in frame if row == 1), "") for frame in screen.frames
    ]


def _notices(screen: _FakeScreen) -> list[str]:
    """Notice lines of every frame the console drew.

    Args:
        screen: The recording screen.

    Returns:
        The alert-styled row of each frame that had one.
    """
    return [
        text for frame in screen.frames for _row, text, style in frame if style is c.Style.ALERT
    ]


def _notice(screen: _FakeScreen) -> str:
    """Notice line the console drew last, if any.

    Args:
        screen: The recording screen.

    Returns:
        The alert-styled row of the last frame, or empty when it had none.
    """
    for _row, text, style in screen.frames[-1]:
        if style is c.Style.ALERT:
            return text
    return ""


def _focused(screen: _FakeScreen) -> str:
    """Row the console drew reversed.

    Args:
        screen: The recording screen.

    Returns:
        The focused row's text, or empty when nothing is focused.
    """
    for _row, text, style in screen.frames[-1]:
        if style is c.Style.REVERSE:
            return text
    return ""


def test_opening_frame_shows_the_status_bar_and_the_footer() -> None:
    """The status bar owns the top row and the key strip the last."""
    screen, backend = _run([], _STACK_ACTIONS)
    painted = _painted(screen)
    assert screen.presents == 1
    assert painted[0].startswith("stack running")
    assert painted[23].endswith("q quit")
    assert len(screen.frames[-1]) == 24
    assert backend.probe_calls == 1


def test_a_one_row_terminal_gets_only_the_status_bar() -> None:
    """A screen with one row loses the body rather than crashing."""
    screen, _backend = _run([], _STACK_ACTIONS, rows=1)
    assert len(screen.frames[-1]) == 1
    assert _painted(screen)[0].startswith("stack running")


def test_a_zero_size_terminal_is_never_painted() -> None:
    """A screen with no rows draws nothing and still flushes."""
    screen, _backend = _run([], _STACK_ACTIONS, rows=0, cols=0)
    assert screen.frames[-1] == []
    assert screen.clears == 1


def test_a_tiny_terminal_never_draws_more_rows_than_it_has() -> None:
    """Three rows carry the bar, the title, and the footer and nothing more."""
    screen, _backend = _run([], _STACK_ACTIONS, rows=3, cols=20)
    frame = screen.frames[-1]
    assert [row for row, _text, _style in frame] == [0, 1, 2]
    assert len(frame) == 3


def test_q_leaves_the_loop() -> None:
    """The quit key ends the session without another frame."""
    screen, _backend = _run(["q"], _STACK_ACTIONS)
    assert screen.keys_read == ["q"]
    assert screen.presents == 1


def test_a_closed_terminal_leaves_the_loop() -> None:
    """The terminal-closed key ends the session too."""
    screen, _backend = _run([c.Key.QUIT], _STACK_ACTIONS)
    assert screen.keys_read == [c.Key.QUIT]


def test_a_timeout_redraws_without_polling_the_machine() -> None:
    """A timeout tick refreshes the screen and leaves the readings alone."""
    screen, backend = _run([c.Key.TIMEOUT], _STACK_ACTIONS)
    assert backend.probe_calls == 1
    assert screen.presents == 2
    assert screen.timeouts[0] == app.POLL_INTERVAL_S


def test_a_resize_key_redraws_without_polling_the_machine() -> None:
    """A resize tick repaints without taking a fresh reading."""
    screen, backend = _run([c.Key.RESIZE], _STACK_ACTIONS)
    assert backend.probe_calls == 1
    assert screen.presents == 2


def test_g_re_reads_the_machine() -> None:
    """The re-read key takes a fresh snapshot on demand."""
    _screen, backend = _run(["g"], _STACK_ACTIONS)
    assert backend.probe_calls == 2


def test_esc_at_the_top_screen_bells_and_says_why() -> None:
    """Escape on the landing screen rings and names the quit key."""
    screen, _backend = _run([c.Key.ESC], _STACK_ACTIONS)
    assert screen.bells == 1
    assert "press q to quit" in _notice(screen)


def test_x_folds_the_detail_pane_away_and_back() -> None:
    """The detail toggle hides the read-only pane and shows it again."""
    hidden, _backend = _run([_STACK_KEY, "x"], _STACK_ACTIONS)
    assert "runnable" not in _body(hidden)
    shown, _backend = _run([_STACK_KEY, "x", "x"], _STACK_ACTIONS)
    assert "runnable" in _body(shown)


def test_d_is_refused_because_dry_run_is_a_launch_flag() -> None:
    """The dry-run switch is fixed at launch, and the console says so."""
    screen, _backend = _run(["d"], _STACK_ACTIONS)
    assert screen.bells == 1
    assert "--dry-run" in _notice(screen)


def test_an_unbound_key_bells_without_touching_anything() -> None:
    """An unknown key rings, explains, and changes no state."""
    screen, backend = _run(["z"], _STACK_ACTIONS)
    assert screen.bells == 1
    assert "no key binding" in _notice(screen)
    assert backend.dispatched == []


@pytest.mark.parametrize("group", list(c.Group))
def test_every_section_hotkey_opens_and_closes(group: c.Group) -> None:
    """All ten sections open from their digit, and Esc returns to the landing screen."""
    expected = {
        c.Group.DASHBOARD: "Studio dashboard",
        c.Group.LANES: "Lanes",
        c.Group.AUDIT: "Operator log",
        c.Group.HELP: "Help",
    }.get(group, f"{group.value.capitalize()} actions")
    screen, _backend = _run([group.hotkey, c.Key.ESC], _STACK_ACTIONS)
    assert _titles(screen)[1] == expected
    assert _title(screen) == "Studio dashboard"


def test_the_console_opens_on_the_configured_section() -> None:
    """The launch section starts the operator somewhere other than the dashboard."""
    screen, _backend = _run([], _STACK_ACTIONS, config=_config(start_group="disk"))
    assert _title(screen) == "Disk actions"


def test_cursor_and_pager_keys_move_the_focus() -> None:
    """j, k, the arrows, and the pager keys all move the focused row."""
    screen, _backend = _run([_STACK_KEY, "j", "j", "j", "k"], _STACK_ACTIONS)
    assert _focused(screen).startswith("Stop the stack")
    screen, _backend = _run([_STACK_KEY, c.Key.DOWN, c.Key.DOWN, c.Key.UP], _STACK_ACTIONS)
    assert _focused(screen).startswith("Stop the stack")
    screen, _backend = _run([_STACK_KEY, c.Key.PGDN], _STACK_ACTIONS)
    assert _focused(screen).startswith("Start the stack")
    screen, _backend = _run([_STACK_KEY, c.Key.PGDN, c.Key.PGUP], _STACK_ACTIONS)
    assert _focused(screen).startswith("Show status")
    screen, _backend = _run([_STACK_KEY, c.Key.END], _STACK_ACTIONS)
    assert _focused(screen).startswith("Start the stack")
    screen, _backend = _run([_STACK_KEY, c.Key.END, c.Key.HOME], _STACK_ACTIONS)
    assert _focused(screen).startswith("Show status")


def test_cursor_keys_bell_on_a_pane_without_rows() -> None:
    """Moving on the empty operator log rings instead of moving nothing."""
    screen, _backend = _run(["a", "j"], ())
    assert screen.bells == 1
    assert "no rows" in _notice(screen)
    screen, _backend = _run(["a", c.Key.END], ())
    assert "no rows" in _notice(screen)


def test_the_landing_screen_focuses_the_first_runnable_quick_action() -> None:
    """Before the operator moves, the view picks the focus; after, the loop does."""
    quick = _action("dashboard.doctor", "Run doctor", c.Group.DASHBOARD, fixed=("doctor",))
    screen, _backend = _run([], (_STATUS, quick))
    assert _focused(screen).startswith("Run doctor")
    screen, _backend = _run(["k"], (_STATUS, quick))
    assert "Run doctor" not in _focused(screen)


def test_enter_on_a_health_reading_bells() -> None:
    """A dashboard reading is not an action and says so."""
    screen, backend = _run([c.Key.HOME, c.Key.ENTER], _STACK_ACTIONS)
    assert screen.bells == 1
    assert "not an action" in _notice(screen)
    assert backend.dispatched == []


def test_enter_on_an_empty_list_bells() -> None:
    """A palette query that matches nothing has nothing to run."""
    screen, backend = _run(["/", "z", "z", "z", c.Key.ENTER], _STACK_ACTIONS)
    assert screen.bells == 1
    assert "nothing to run" in _notice(screen)
    assert backend.dispatched == []


def test_enter_on_a_pane_without_selectable_rows_bells() -> None:
    """The help rows are documentation, not actions."""
    screen, _backend = _run(["?", c.Key.ENTER], _STACK_ACTIONS)
    assert screen.bells == 1
    assert "not selectable" in _notice(screen)


def test_a_read_action_dispatches_and_shows_the_result() -> None:
    """A T0 action goes straight out and comes back as a result screen."""
    screen, backend = _run([_STACK_KEY, c.Key.ENTER], _STACK_ACTIONS)
    assert backend.dispatched == [("stack.status", {}, "")]
    assert "Running: Show status" in _titles(screen)
    assert _title(screen) == "Result: stack.status"
    assert "exit 0" in _notice(screen)


def test_a_dry_run_result_is_reported_as_not_running() -> None:
    """A dispatch that did not run is announced as such."""
    blocked = _outcome("stack.status", ran=False, note="dry run")
    backend = _Backend(results={"stack.status": blocked})
    screen, _active = _run([_STACK_KEY, c.Key.ENTER], _STACK_ACTIONS, backend=backend)
    assert "did not run: dry run" in _notice(screen)
    assert "argv scripts/manage.sh status" in _body(screen)


def test_result_enter_returns_to_the_list_and_the_log_replays_the_outcome() -> None:
    """The outcome screen gives back to the list, and the log shows it again."""
    screen, _backend = _run([_STACK_KEY, c.Key.ENTER, c.Key.ENTER], _STACK_ACTIONS)
    assert _title(screen) == "Stack actions"
    screen, _backend = _run([_STACK_KEY, c.Key.ENTER, "a", c.Key.ENTER], _STACK_ACTIONS)
    assert _title(screen) == "Result: stack.status"
    assert "exit 0" in _body(screen)


def test_the_log_row_names_the_dispatch() -> None:
    """The operator log lists what ran and how it ended."""
    screen, _backend = _run([_STACK_KEY, c.Key.ENTER, "a"], _STACK_ACTIONS)
    assert "stack.status" in _body(screen)
    assert "ok" in _body(screen)


def test_the_audit_pane_bells_before_there_is_history() -> None:
    """An empty operator log has nothing to show."""
    screen, _backend = _run(["a", c.Key.ENTER], _STACK_ACTIONS)
    assert screen.bells == 1
    assert "nothing dispatched yet" in _notice(screen)


def test_a_blocked_action_bells_with_the_guard_reason() -> None:
    """A red guard stops the action and hands the reason back."""
    blocked = c.GuardVerdict(allowed=False, reasons=("the queue is busy",))
    backend = _Backend(verdicts={"stack.status": blocked})
    screen, active = _run([_STACK_KEY, c.Key.ENTER], _STACK_ACTIONS, backend=backend)
    assert active.dispatched == []
    assert screen.bells == 1
    assert "blocked: the queue is busy" in _notice(screen)


def test_a_refused_action_bells_with_its_policy_reason() -> None:
    """A refused catalog entry never reaches the dispatcher."""
    screen, backend = _run([_DISK_KEY, c.Key.ENTER], (_WIPE,))
    assert backend.dispatched == []
    assert screen.bells == 1
    assert "retired" in _notice(screen)


def test_a_refused_action_without_a_reason_still_says_why() -> None:
    """A refused entry with no stated reason gets the generic one."""
    silent = _action("disk.no", "No", c.Group.DISK, tier=c.RiskTier.REFUSED)
    screen, _backend = _run([_DISK_KEY, c.Key.ENTER], (silent,))
    assert "policy blocks this action" in _notice(screen)


def test_read_only_mode_refuses_a_state_changing_action() -> None:
    """Under read-only mode a write action stops at the read-only gate."""
    keys = [_STACK_KEY, "j", c.Key.ENTER]
    screen, backend = _run(keys, _STACK_ACTIONS, config=_config(read_only=True))
    assert backend.dispatched == []
    assert screen.bells == 1
    assert "read-only" in _notice(screen)


def test_read_only_mode_still_runs_an_observe_only_action() -> None:
    """The read-only gate lets a T0 action through."""
    keys = [_STACK_KEY, c.Key.ENTER]
    _screen, backend = _run(keys, _STACK_ACTIONS, config=_config(read_only=True))
    assert backend.dispatched == [("stack.status", {}, "")]


def test_a_heavy_action_asks_for_the_token_then_runs() -> None:
    """A T2 action stops at the gate and dispatches only with the token typed."""
    keys = [_STACK_KEY, "j", "j", c.Key.ENTER, "y", "e", "s", c.Key.ENTER]
    screen, backend = _run(keys, _STACK_ACTIONS)
    assert "Confirm: Start the stack" in _titles(screen)
    assert "type exactly: yes" in _all_body(screen)
    assert backend.dispatched == [("stack.start", {}, "yes")]
    assert _title(screen) == "Result: stack.start"


def test_a_destructive_action_needs_the_exact_delete_token() -> None:
    """A T3 action names the literal and refuses a near miss."""
    wrong = [_DISK_KEY, "j", c.Key.ENTER, "y", "e", "s", c.Key.ENTER]
    screen, backend = _run(wrong, (_WIPE, _PURGE))
    assert backend.dispatched == []
    assert screen.bells == 1
    assert "type DELETE exactly" in _notice(screen)
    right = [_DISK_KEY, "j", c.Key.ENTER, "D", "E", "L", "E", "T", "E", c.Key.ENTER]
    _screen, backend = _run(right, (_WIPE, _PURGE))
    assert backend.dispatched == [("disk.purge", {}, "DELETE")]


def test_backspace_edits_the_typed_token() -> None:
    """A mistyped token can be corrected without abandoning the gate."""
    keys = [_STACK_KEY, "j", "j", c.Key.ENTER, "y", "e", "s", "x", c.Key.BACKSPACE, c.Key.ENTER]
    _screen, backend = _run(keys, _STACK_ACTIONS)
    assert backend.dispatched == [("stack.start", {}, "yes")]


def test_a_modifier_key_at_the_token_gate_bells() -> None:
    """A pager key at the gate is not a character and rings."""
    screen, backend = _run([_STACK_KEY, "j", "j", c.Key.ENTER, c.Key.PGUP], _STACK_ACTIONS)
    assert backend.dispatched == []
    assert screen.bells == 1
    assert "press enter to run" in _notice(screen)


def test_esc_at_the_token_gate_records_a_declined_result() -> None:
    """Walking away records a declined run instead of stopping quietly."""
    keys = [_STACK_KEY, "j", "j", c.Key.ENTER, "y", c.Key.ESC]
    screen, backend = _run(keys, _STACK_ACTIONS)
    assert backend.dispatched == []
    assert _title(screen) == "Result: stack.start"
    assert "declined at the confirm prompt" in _body(screen)
    screen, _backend = _run([*keys, "a"], _STACK_ACTIONS)
    assert "stack.start" in _body(screen)
    assert "skipped" in _body(screen)


def test_missing_parameters_open_the_form_before_anything_runs() -> None:
    """An unanswered required parameter sends the operator to the form."""
    download = _download(tier=_choice("tier", ("turbo", "full")))
    screen, backend = _run([_MODELS_KEY, c.Key.ENTER], (download,))
    assert backend.dispatched == []
    assert _title(screen) == "Parameters: Download a pack"
    assert "turbo, full" in _body(screen)


def test_a_choice_field_cycles_with_j_and_k_and_commits_with_enter() -> None:
    """j walks the menu, k walks it back, and Enter runs with the answer."""
    download = _download(tier=_choice("tier", ("turbo", "full")))
    keys = [_MODELS_KEY, c.Key.ENTER, "j", "j", "k", c.Key.ENTER]
    screen, backend = _run(keys, (download,))
    assert backend.dispatched == [("models.download", {"tier": "turbo"}, "")]
    assert "argv download-models --tier turbo" in _all_body(screen)


def test_a_choice_field_refuses_typed_characters_and_backspace() -> None:
    """A menu answer is cycled, not typed or erased."""
    download = _download(tier=_choice("tier", ("turbo", "full")))
    screen, _backend = _run([_MODELS_KEY, c.Key.ENTER, "z"], (download,))
    assert screen.bells == 1
    assert "press j or k" in _notice(screen)
    screen, backend = _run([_MODELS_KEY, c.Key.ENTER, c.Key.BACKSPACE], (download,))
    assert screen.bells == 1
    assert "use j and k" in _notice(screen)
    assert backend.dispatched == []


def test_a_choice_field_without_choices_bells() -> None:
    """A menu parameter with nothing to choose is said out loud."""
    broken = _download(tier=_choice("tier", ()))
    screen, backend = _run([_MODELS_KEY, c.Key.ENTER, "j"], (broken,))
    assert screen.bells == 1
    assert "offers no choices" in _notice(screen)
    assert backend.dispatched == []


def test_text_and_int_fields_take_characters_and_validate_on_enter() -> None:
    """TEXT and INT take typed characters and are validated by the argv builder."""
    add = _download(slug=_text("slug"), count=_int("count", high=10))
    keys = [_MODELS_KEY, c.Key.ENTER, "w", "a", "n", c.Key.DOWN, "3", c.Key.ENTER]
    screen, backend = _run(keys, (add,))
    assert backend.dispatched == [("models.download", {"slug": "wan", "count": "3"}, "")]
    assert "argv download-models wan --count 3" in _all_body(screen)


def test_a_bad_integer_answer_is_shown_and_the_form_stays_open() -> None:
    """A rejected answer rings, names the problem, and keeps the operator on the form."""
    add = _download(slug=_text("slug", default="wan"), count=_int("count", high=10))
    keys = [_MODELS_KEY, c.Key.ENTER, c.Key.DOWN, "9", "9", c.Key.ENTER]
    screen, backend = _run(keys, (add,))
    assert backend.dispatched == []
    assert screen.bells == 1
    assert "outside 0..10" in _notice(screen)
    assert _title(screen) == "Parameters: Download a pack"
    fixed = [_MODELS_KEY, c.Key.ENTER, c.Key.DOWN, "9", "9", c.Key.BACKSPACE, c.Key.ENTER]
    _screen, backend = _run(fixed, (add,))
    assert backend.dispatched == [("models.download", {"slug": "wan", "count": "9"}, "")]


def test_backspace_empties_a_typed_answer_and_the_preview_says_so() -> None:
    """Deleting the last character leaves the field required again."""
    add = _download(slug=_text("slug"), count=_int("count", high=10, default="2"))
    keys = [_MODELS_KEY, c.Key.ENTER, "w", "a", "n"]
    keys += [c.Key.BACKSPACE, c.Key.BACKSPACE, c.Key.BACKSPACE, c.Key.ENTER]
    screen, backend = _run(keys, (add,))
    assert backend.dispatched == []
    assert "slug: Slug is required" in _notice(screen)


def test_the_form_moves_between_fields_with_the_arrow_and_pager_keys() -> None:
    """Up, down, Home, End, and the pager keys change the focused field."""
    wide = _action(
        "film.render",
        "Render a shot",
        c.Group.FILM,
        fixed=("render",),
        params=(_text("shot"), _choice("look", ("flat", "film")), _int("count")),
    )
    screen, _backend = _run([_FILM_KEY, c.Key.ENTER, c.Key.END], (wide,))
    assert _focused(screen).startswith("Count")
    screen, _backend = _run([_FILM_KEY, c.Key.ENTER, c.Key.END, c.Key.HOME], (wide,))
    assert _focused(screen).startswith("Shot")
    screen, _backend = _run([_FILM_KEY, c.Key.ENTER, c.Key.PGDN], (wide,))
    assert _focused(screen).startswith("Count")
    screen, _backend = _run([_FILM_KEY, c.Key.ENTER, c.Key.PGDN, c.Key.PGUP], (wide,))
    assert _focused(screen).startswith("Shot")


def test_an_unbound_key_on_the_form_bells() -> None:
    """A stray key on the form rings instead of editing an answer."""
    wide = _action(
        "film.render", "Render a shot", c.Group.FILM, fixed=("render",), params=(_text("shot"),)
    )
    screen, backend = _run([_FILM_KEY, c.Key.ENTER, c.Key.LEFT], (wide,))
    assert screen.bells == 1
    assert "no key binding" in _notice(screen)
    assert backend.dispatched == []


def test_esc_on_the_form_abandons_the_action() -> None:
    """Escape leaves the collector without dispatching."""
    add = _download(slug=_text("slug"))
    screen, backend = _run([_MODELS_KEY, c.Key.ENTER, c.Key.ESC], (add,))
    assert backend.dispatched == []
    assert _title(screen) == "Models actions"
    assert "cancelled" in _notice(screen)


def test_an_action_whose_default_the_argv_builder_rejects_is_reported() -> None:
    """A default the builder will not accept rings instead of dispatching."""
    odd = _download(tier=_choice("tier", ("turbo",), default="nope"))
    screen, backend = _run([_MODELS_KEY, c.Key.ENTER], (odd,))
    assert backend.dispatched == []
    assert screen.bells == 1
    assert "is not one of" in _notice(screen)


def test_the_palette_filters_as_the_operator_types() -> None:
    """The query narrows the list, and Enter runs the match down its gates."""
    keys = ["/", "s", "t", "a", "r", "t", c.Key.ENTER]
    screen, backend = _run(keys, _STACK_ACTIONS)
    assert "matches 1/3" in _all_body(screen)
    assert "Confirm: Start the stack" in _titles(screen)
    assert backend.dispatched == []


def test_the_palette_edits_navigates_and_rings_for_junk() -> None:
    """Editing the query, moving the focus, and junk keys all behave."""
    screen, _backend = _run(["/", "s", "t", "a", "t", "u", "s", c.Key.BACKSPACE], _STACK_ACTIONS)
    assert "query 'statu'" in _body(screen)
    screen, _backend = _run(["/", c.Key.BACKSPACE], _STACK_ACTIONS)
    assert screen.bells == 1
    assert "already empty" in _notice(screen)
    screen, _backend = _run(["/", c.Key.DOWN, c.Key.PGDN, c.Key.PGUP, c.Key.UP], _STACK_ACTIONS)
    assert _focused(screen).startswith("Show status")
    screen, _backend = _run(["/", c.Key.HOME, c.Key.END], _STACK_ACTIONS)
    assert _focused(screen).startswith("Start the stack")
    screen, _backend = _run(["/", c.Key.LEFT], _STACK_ACTIONS)
    assert screen.bells == 1
    assert "no key binding" in _notice(screen)


def test_esc_closes_the_palette() -> None:
    """Escape drops the palette and shows what was underneath."""
    screen, _backend = _run(["/", "s", c.Key.ESC], _STACK_ACTIONS)
    assert _title(screen) == "Studio dashboard"


def test_safe_stop_arms_and_dispatches_the_stack_stop_action() -> None:
    """S then y runs the stack's own stop verb."""
    screen, backend = _run(["S", "y"], _STACK_ACTIONS)
    assert any("safe stop armed" in line for line in _notices(screen))
    assert backend.dispatched == [("stack.stop", {}, "")]
    assert _title(screen) == "Result: stack.stop"


def test_safe_stop_still_demands_the_token_of_a_heavy_stop() -> None:
    """The two-key confirm does not bypass the token gate."""
    heavy = _action(
        "stack.stop",
        "Stop the stack",
        c.Group.STACK,
        tier=c.RiskTier.HEAVY,
        confirm=c.ConfirmKind.YES,
        fixed=("stop",),
    )
    keys = ["S", "y", "y", "e", "s", c.Key.ENTER]
    screen, backend = _run(keys, (heavy,))
    assert backend.dispatched == [("stack.stop", {}, "yes")]
    assert _title(screen) == "Result: stack.stop"


def test_safe_stop_cancels_and_stays_armed_as_expected() -> None:
    """n or esc cancels an armed stop; any other key rings and keeps it armed."""
    screen, backend = _run(["S", "n", "q"], _STACK_ACTIONS)
    assert backend.dispatched == []
    assert "cancelled" in _notice(screen)
    screen, backend = _run(["S", c.Key.ESC], _STACK_ACTIONS)
    assert backend.dispatched == []
    assert "cancelled" in _notice(screen)
    screen, backend = _run(["S", "z", "y"], _STACK_ACTIONS)
    assert screen.bells == 1
    assert backend.dispatched == [("stack.stop", {}, "")]


def test_safe_stop_without_a_stop_action_bells_and_explains() -> None:
    """With no stop verb in the catalog the console says there is nothing to stop."""
    screen, backend = _run(["S"], (_STATUS,))
    assert backend.dispatched == []
    assert screen.bells == 1
    assert "nothing to safe-stop" in _notice(screen)


def test_safe_stop_falls_back_to_an_action_id_that_ends_in_stop() -> None:
    """A utility verb whose id ends in stop is found when no manage stop exists."""
    utility = _action(
        "film.stop",
        "Stop the render",
        c.Group.FILM,
        tier=c.RiskTier.WRITE,
        runner=c.RunnerKind.UTILITY,
        target="film-cut",
    )
    _screen, backend = _run(["S", "y"], (_STATUS, utility))
    assert backend.dispatched == [("film.stop", {}, "")]


def test_the_lane_browser_walks_down_and_back() -> None:
    """Lanes, graphs, and the detail pane each open and give way in turn."""
    lanes = [
        lane_lib.Lane(
            lane_id="photos", order=10, title="Photos", description="Stills.", graph_count=1
        )
    ]
    graphs = [
        lane_lib.Graph(
            lane_id="photos",
            rel_id="photos/background-swap",
            title="background-swap",
            description="Swap a background.",
            occupancy="photos",
        )
    ]
    backend = _Backend(lanes=lanes, graphs=graphs)
    keys = [_LANES_KEY, c.Key.ENTER, c.Key.ENTER, c.Key.ESC, c.Key.ESC, c.Key.ESC]
    screen, active = _run(keys, _STACK_ACTIONS, backend=backend)
    assert _titles(screen)[:4] == [
        "Studio dashboard",
        "Lanes",
        "Lane: Photos",
        "Graph: background-swap",
    ]
    assert active.lane_calls == ["photos"]
    assert _title(screen) == "Studio dashboard"


def test_an_empty_lane_list_bells() -> None:
    """A checkout with no lanes says so instead of opening an empty list."""
    screen, _backend = _run([_LANES_KEY, c.Key.ENTER], _STACK_ACTIONS)
    assert screen.bells == 1
    assert "no lanes found" in _notice(screen)


def test_an_empty_graph_list_bells() -> None:
    """A lane with no promoted graphs says so."""
    lane = lane_lib.Lane(lane_id="photos", order=10, title="Photos", description="Stills.")
    screen, _backend = _run(
        [_LANES_KEY, c.Key.ENTER, c.Key.ENTER], _STACK_ACTIONS, backend=_Backend(lanes=[lane])
    )
    assert screen.bells == 1
    assert "no promoted graphs" in _notice(screen)


def test_an_unbound_key_on_the_outcome_pane_bells() -> None:
    """The result screen takes Enter, the globals, and nothing else."""
    screen, _backend = _run([_STACK_KEY, c.Key.ENTER, "z"], _STACK_ACTIONS)
    assert _title(screen) == "Result: stack.status"
    assert screen.bells == 1
    assert "no key binding" in _notice(screen)


def test_the_form_moves_back_a_field_with_k() -> None:
    """k walks a TEXT or INT field back to the previous parameter."""
    wide = _action(
        "film.render",
        "Render a shot",
        c.Group.FILM,
        fixed=("render",),
        params=(_text("shot"), _text("take")),
    )
    screen, _backend = _run([_FILM_KEY, c.Key.ENTER, c.Key.END, c.Key.UP], (wide,))
    assert _focused(screen).startswith("Shot")


def test_the_guard_is_asked_about_every_action_on_each_poll() -> None:
    """Every action carries a verdict, so no row is ever offered without one."""
    _screen, backend = _run(["g"], _STACK_ACTIONS)
    assert backend.evaluated == ["stack.status", "stack.stop", "stack.start"] * 2


def test_the_key_list_names_every_key_the_loop_honors() -> None:
    """A headless operator reads the keys offline, so a missing row is a dead end."""
    named = {token for keys, _, _ in app._HELP_BINDINGS for token in keys.split()}
    for key in (
        app._QUIT_KEY,
        app._HELP_KEY,
        app._PALETTE_KEY,
        app._PROBE_KEY,
        app._DETAIL_KEY,
        app._AUDIT_KEY,
        app._DRY_RUN_KEY,
        app._STOP_KEY,
        app._YES_KEY,
        app._NO_KEY,
        c.Key.ENTER,
        c.Key.ESC,
        "j",
        "k",
    ):
        assert key in named, f"{key} is bound in the loop but absent from the key list"
    rows = {keys: (scope, note) for keys, scope, note in app._HELP_BINDINGS}
    assert app._YES_KEY in rows and app._NO_KEY in rows, (
        "the safe stop is two keys, and the answer key needs its own row"
    )
    assert "safe stop" in rows[app._STOP_KEY][1]


def test_the_key_list_invents_no_key_the_loop_ignores() -> None:
    """A key the key list advertises and the loop drops costs an operator a minute."""
    honored = {
        app._QUIT_KEY,
        app._HELP_KEY,
        app._PALETTE_KEY,
        app._PROBE_KEY,
        app._DETAIL_KEY,
        app._AUDIT_KEY,
        app._DRY_RUN_KEY,
        app._STOP_KEY,
        app._YES_KEY,
        app._NO_KEY,
        c.Key.ENTER,
        c.Key.ESC,
        c.Key.UP,
        c.Key.DOWN,
        c.Key.PGUP,
        c.Key.PGDN,
        c.Key.HOME,
        c.Key.END,
        "j",
        "k",
        *app._GROUP_BY_HOTKEY,
    }
    spelled_out = {"1", "to", "0"}
    for keys, _scope, _meaning in app._HELP_BINDINGS:
        for token in keys.split():
            assert token in honored or token in spelled_out, (
                f"the key list advertises {token!r}, which no handler reads"
            )
