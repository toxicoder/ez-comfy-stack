"""The keystroke loop: the only place a key press becomes a dispatch.

This module owns the console's control flow and nothing else. A key arrives from
:meth:`tui.contract.Screen.read_key`, is routed by the pane on top of the
navigation stack, and either moves the operator around, opens another pane, or
walks one catalog action down the gate ladder: row lookup, runnability,
read-only mode, the guard verdict, the parameter form, the typed token, and only
then the injected dispatch callback. No other module in the package makes that
sequence decision and no other module turns a keystroke into a child process:
the views are pure, the guard only judges, the runner only runs, and this loop
is the single place the three are wired together by hand.

Two rules keep the loop testable and honest. First, it draws only through
:mod:`tui.views` and the six-method :class:`tui.contract.Screen` protocol, so
the suite drives it with a fake that records rows: this file never imports
curses and never needs a terminal. Second, everything that can touch the machine
arrives as a constructor argument -- the probe, the guard, the dispatcher, the
lane and graph sources -- so this module never imports :mod:`tui.catalog`,
:mod:`tui.guard`, or :mod:`tui.readmodel`, and cannot reach docker, compose, or
the occupancy file on its own. The thin ``run_console`` adapter that binds the
real modules to those arguments lives beside the CLI, not here.

A refusal never passes silently: anything the console will not do rings
:meth:`tui.contract.Screen.bell` and leaves a one-line reason in the notice slot,
which the next frame draws directly under the title so it cannot be scrolled
away.

On a pane that collects text -- the palette query, a TEXT or INT parameter, the
token gate -- the cursor keys, Enter, and Esc stay keys and every other character
is text. j and k therefore never land inside an answer, except on a CHOICE field,
where they are the menu and the arrows change the focused parameter instead.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TypeAlias

from tui import views
from tui.contract import (
    EXIT_OK,
    UNMEASURED,
    ActionSpec,
    CommandResult,
    Group,
    GuardVerdict,
    Health,
    Key,
    Line,
    ParamKind,
    ParamSpec,
    RiskTier,
    RunConfig,
    RunnerKind,
    Screen,
    ScreenId,
    SessionState,
    Style,
    ViewModel,
    build_argv,
    empty_health,
)
from tui.lanes import Graph, Lane

EvaluateFn: TypeAlias = Callable[[ActionSpec, Health], GuardVerdict]
"""Ask the guard layer whether one action may run against one snapshot."""

ProbeFn: TypeAlias = Callable[[], Health]
"""Take a fresh machine snapshot."""

DispatchFn: TypeAlias = Callable[[ActionSpec, Mapping[str, str], str], CommandResult]
"""Run one action with the operator's answers and the token they typed."""

LaneSourceFn: TypeAlias = Callable[[Path], Sequence[Lane]]
"""Read the lab lanes under a checkout."""

GraphSourceFn: TypeAlias = Callable[[Path, str], Sequence[Graph]]
"""Read the promoted graphs in one lane."""

POLL_INTERVAL_S = 1.0
"""Seconds :meth:`Console.run` waits for one key before redrawing."""

PAGE_STEP = 8
"""Rows PgUp and PgDn jump at a time."""

_UNSET_FOCUS = -1
"""Pane focus that means "let the view choose", used before the operator moves."""

QUICK_LIMIT = 8
"""How many dashboard-section actions the landing screen offers up front."""

_NOTICE_ON_OPEN = "press ? for the key list, q to quit"
"""Notice shown while the console has nothing to tell the operator."""

_ROOT_ESC_NOTICE = "this is the top screen; press q to quit"
"""Reason Escape rings the bell instead of going back."""

_READ_ONLY_NOTICE = "the console is read-only; only observe-only actions may run"
"""Reason a state-changing action is refused under ``--read-only``."""

_NOT_RUNNABLE_NOTE = "policy blocks this action"
"""Fallback note for a refused catalog entry that states no reason."""

_NO_ROWS_NOTICE = "this screen has no rows to move through"
"""Reason the cursor keys ring the bell on a row-less pane."""

_NO_KEY_NOTICE = "no key binding here; press ? for the key list"
"""Reason an unbound key rings the bell."""

_NO_ROW_NOTICE = "nothing to run here"
"""Reason Enter rings the bell on an empty list."""

_READING_NOTICE = "that row is a reading, not an action"
"""Reason Enter rings the bell on a dashboard health row."""

_NO_SELECTION_NOTICE = "this row is not selectable"
"""Reason Enter rings the bell on a pane that offers no actions."""

_EMPTY_AUDIT_NOTICE = "nothing dispatched yet this session"
"""Reason Enter rings the bell on an empty operator log."""

_EMPTY_LANES_NOTICE = "no lanes found under workflows/_lab"
"""Reason Enter rings the bell when the lane source returned nothing."""

_DRY_RUN_NOTICE = "dry run is fixed by --dry-run at launch; press g to re-read"
"""Reason the dry-run key is refused mid-session."""

_STOP_ARMED_NOTICE = "safe stop armed: press y to stop the stack, esc to cancel"
"""Prompt shown between ``S`` and its second key."""

_STOP_MISSING_NOTICE = "no stop action is offered; nothing to safe-stop"
"""Reason ``S`` rings the bell when the catalog offers no stop verb."""

_STOP_CANCELLED_NOTICE = "safe stop cancelled"
"""Notice when the operator answers an armed ``S`` with esc or n."""

_PROBE_NOTICE = "machine re-read"
"""Notice after an explicit re-poll."""

_DECLINE_NOTE = "declined at the confirm prompt"
"""Note recorded when the operator leaves the token gate without typing."""

_TYPE_TOKEN_NOTICE = "press enter to run, or esc to abandon"
"""Nudge for a modifier key pressed while typing a token."""

_STOP_ID_SUFFIX = ".stop"
"""Action-id suffix the safe-stop key accepts."""

_STOP_TARGET = "stop"
"""Manage verb the safe-stop key prefers."""

_QUIT_KEY = "q"
"""Key that leaves the console from any non-text pane."""

_HELP_KEY = "?"
"""Key that opens the key list and the safety contract."""

_PALETTE_KEY = "/"
"""Key that opens the action palette."""

_PROBE_KEY = "g"
"""Key that re-reads the machine."""

_DETAIL_KEY = "x"
"""Key that folds the detail pane away or back."""

_AUDIT_KEY = "a"
"""Key that opens the operator log."""

_DRY_RUN_KEY = "d"
"""Key the help screen names; refused here because the flag is a launch flag."""

_STOP_KEY = "S"
"""Key that arms the safe stop."""

_YES_KEY = "y"
"""Second key of the safe-stop confirmation."""

_NO_KEY = "n"
"""Key that cancels an armed safe stop."""

_DOWN_KEYS: frozenset[str] = frozenset({"j", Key.DOWN})
"""Keys that move the focus one row down."""

_UP_KEYS: frozenset[str] = frozenset({"k", Key.UP})
"""Keys that move the focus one row up."""

_CYCLE_KEYS: frozenset[str] = frozenset({"j", "k"})
"""Keys that cycle a focused CHOICE parameter; arrows still change fields."""

_GROUP_BY_HOTKEY: dict[str, Group] = {group.hotkey: group for group in Group}
"""Section each digit jumps to."""

_SPECIAL_GROUP_SCREEN: dict[Group, ScreenId] = {
    Group.DASHBOARD: ScreenId.DASHBOARD,
    Group.LANES: ScreenId.LANES,
    Group.AUDIT: ScreenId.AUDIT,
    Group.HELP: ScreenId.HELP,
}
"""Sections whose hotkey opens a pane of its own instead of an action list."""

_LIST_SCREENS: frozenset[ScreenId] = frozenset(
    {
        ScreenId.DASHBOARD,
        ScreenId.GROUP,
        ScreenId.PALETTE,
        ScreenId.AUDIT,
        ScreenId.LANES,
        ScreenId.LANE_GRAPHS,
        ScreenId.GRAPH_DETAIL,
        ScreenId.HELP,
    }
)
"""Panes whose cursor keys and Enter act on rows."""

_ACTION_SCREENS: frozenset[ScreenId] = frozenset(
    {ScreenId.DASHBOARD, ScreenId.GROUP, ScreenId.PALETTE}
)
"""Panes whose rows are catalog entries that may be dispatched."""

_DENIED = GuardVerdict(allowed=False, reasons=("no guard verdict yet; press g",))
"""Fail-closed verdict used when the guard has not spoken about an action."""

_NOTHING_DISPATCHED = CommandResult(
    action_id="none",
    argv=(),
    returncode=UNMEASURED,
    output="",
    duration_s=0.0,
    ran=False,
    note="nothing dispatched this session",
)
"""Outcome the result pane shows before the operator has run anything."""

_NO_ACTION = ActionSpec(
    action_id="",
    title="",
    group=Group.DASHBOARD,
    summary="",
    runner=RunnerKind.INTERNAL,
    target="",
)
"""Placeholder for a modal pane that is not open; never rendered."""

_NO_LANE = Lane(lane_id="", order=0, title="", description="")
"""Lane placeholder for a browser that is not open."""

_NO_GRAPH = Graph(lane_id="", rel_id="", title="", description="", occupancy="")
"""Graph placeholder for a detail pane that is not open."""


def _clamp(index: int, count: int) -> int:
    """Keep a focus index inside a list.

    Args:
        index: Index the operator wants focused.
        count: Number of rows.

    Returns:
        An index between 0 and ``count - 1``, or 0 for an empty list.
    """
    return min(max(index, 0), max(count - 1, 0))


def _is_text(key: str) -> bool:
    """Whether a key name is one printable character of operator text.

    Args:
        key: The key :meth:`tui.contract.Screen.read_key` returned.

    Returns:
        True for a single printable character, which text-entry screens take as
        input rather than as a command.
    """
    return len(key) == 1 and key.isprintable()


def _result_notice(result: CommandResult) -> str:
    """Summarise one dispatch for the notice slot.

    Args:
        result: What the injected dispatcher returned.

    Returns:
        A single line naming the exit status, or why nothing ran.
    """
    if not result.ran:
        return f"{result.action_id} did not run: {result.note or 'blocked'}"
    return f"{result.action_id} exit {result.returncode} in {result.duration_s:.1f}s"


@dataclass(frozen=True)
class _Pane:
    """One entry on the navigation stack.

    Attributes:
        screen: Which screen this pane shows.
        group: The section a group pane lists.
        selected: Row, or form field, the operator has focused; :data:`_UNSET_FOCUS`
            until a cursor key moves it, which lets a view pick the opening focus.
        query: Text typed into the palette.
    """

    screen: ScreenId
    group: Group = Group.DASHBOARD
    selected: int = _UNSET_FOCUS
    query: str = ""


@dataclass
class Console:
    """The guarded operator console loop, driven by :meth:`run`.

    Everything that can touch the machine is injected, so a test can drive a
    whole session with a fake screen and no terminal, and this module stays
    importable without curses, docker, or a repository on disk.
    """

    def __init__(
        self,
        config: RunConfig,
        *,
        screen: Screen,
        actions: Sequence[ActionSpec],
        evaluate: EvaluateFn,
        probe: ProbeFn,
        dispatch: DispatchFn,
        lane_source: LaneSourceFn,
        graph_source: GraphSourceFn,
    ) -> None:
        """Bind the loop to one screen and one set of collaborators.

        Args:
            config: Resolved launch settings, including the section to open on.
            screen: The drawing surface; a recording fake in tests.
            actions: The catalog the console offers.
            evaluate: Guard check for one action against one snapshot.
            probe: Reads a fresh machine snapshot.
            dispatch: Runs one action and returns its outcome.
            lane_source: Reads the lab lanes for the browser.
            graph_source: Reads the promoted graphs in one lane.
        """
        self._config = config
        self._screen = screen
        self._actions = tuple(actions)
        self._evaluate = evaluate
        self._probe = probe
        self._dispatch_cb = dispatch
        self._lane_source = lane_source
        self._graph_source = graph_source
        self._by_id: dict[str, ActionSpec] = {
            action.action_id: action for action in self._actions
        }
        self._session = SessionState(
            dry_run=config.dry_run,
            read_only=config.read_only,
        )
        self._health: Health = empty_health()
        self._verdicts: dict[str, GuardVerdict] = {}
        self._panes: list[_Pane] = [self._pane_for_group(config.start_group)]
        self._notice = _NOTICE_ON_OPEN
        self._detail_open = True
        self._stop_pending = False
        self._stop_action: ActionSpec = _NO_ACTION
        self._form_action: ActionSpec = _NO_ACTION
        self._confirm_action: ActionSpec = _NO_ACTION
        self._confirm_argv: tuple[str, ...] = ()
        self._typed = ""
        self._progress_action: ActionSpec = _NO_ACTION
        self._last_result: CommandResult = _NOTHING_DISPATCHED
        self._lane: Lane = _NO_LANE
        self._graph: Graph = _NO_GRAPH
        self._lanes: tuple[Lane, ...] = ()
        self._graphs: tuple[Graph, ...] = ()
        self._load(self._panes[0])

    def run(self) -> int:
        """Poll once, then draw and read keys until the operator leaves.

        Each handled key is followed by exactly one frame, so a handler only has
        to change state; the single exception is :meth:`_run_command`, which
        paints the progress pane itself before the blocking dispatch.

        Returns:
            :data:`~tui.contract.EXIT_OK`. A failed command is a result the
            operator reads on the outcome pane, not an error in the loop.
        """
        self._poll()
        self._draw()
        while True:
            key = self._screen.read_key(POLL_INTERVAL_S)
            if not self._handle_key(key):
                return EXIT_OK
            self._draw()

    def _poll(self) -> None:
        """Take one machine snapshot and ask the guard about every action."""
        self._health = self._probe()
        self._verdicts = {
            action.action_id: self._evaluate(action, self._health)
            for action in self._actions
        }
        self._session.poll_errors = self._health["errors"]

    def _handle_key(self, key: str) -> bool:
        """Route one key to the pane on top of the stack.

        Args:
            key: A :class:`~tui.contract.Key` name or one printable character.

        Returns:
            False when the operator asked to leave the console.
        """
        self._notice = ""
        if key in (Key.TIMEOUT, Key.RESIZE):
            return True
        if key == Key.QUIT:
            return False
        if self._stop_pending:
            return self._stop_key(key)
        screen = self._top().screen
        if screen is ScreenId.CONFIRM:
            return self._confirm_key(key)
        if screen is ScreenId.PARAM_FORM:
            return self._form_key(key)
        if screen is ScreenId.PALETTE:
            return self._palette_key(key)
        if screen in _LIST_SCREENS:
            return self._list_key(key)
        return self._plain_key(key)

    def _global_key(self, key: str) -> bool | None:
        """Handle the keys that work on every pane that is not collecting text.

        Args:
            key: The key the operator pressed.

        Returns:
            False to end the loop, True when this handler took the key, or None
            when the key belongs to the pane underneath.
        """
        if key == _QUIT_KEY:
            return False
        if key == Key.ESC:
            self._go_back()
            return True
        if key in _GROUP_BY_HOTKEY:
            self._open(self._pane_for_group(_GROUP_BY_HOTKEY[key]))
            return True
        if key in (_HELP_KEY, _AUDIT_KEY):
            group = Group.HELP if key == _HELP_KEY else Group.AUDIT
            self._open(self._pane_for_group(group))
            return True
        if key == _PALETTE_KEY:
            self._open(_Pane(screen=ScreenId.PALETTE))
            return True
        if key == _PROBE_KEY:
            self._poll()
            self._notice = _PROBE_NOTICE
            return True
        if key == _DETAIL_KEY:
            self._detail_open = not self._detail_open
            self._notice = "detail pane hidden" if not self._detail_open else "detail pane shown"
            return True
        if key == _DRY_RUN_KEY:
            self._screen.bell()
            self._notice = _DRY_RUN_NOTICE
            return True
        if key == _STOP_KEY:
            return self._arm_stop()
        return None

    def _list_key(self, key: str) -> bool:
        """Route a key on a pane that shows selectable rows.

        Args:
            key: The key the operator pressed.

        Returns:
            False to end the loop.
        """
        handled = self._global_key(key)
        if handled is not None:
            return handled
        if key == Key.ENTER:
            self._activate()
            return True
        if key in _DOWN_KEYS:
            self._move(1)
            return True
        if key in _UP_KEYS:
            self._move(-1)
            return True
        if key == Key.PGDN:
            self._move(PAGE_STEP)
            return True
        if key == Key.PGUP:
            self._move(-PAGE_STEP)
            return True
        if key == Key.HOME:
            self._jump(first=True)
            return True
        if key == Key.END:
            self._jump(first=False)
            return True
        self._screen.bell()
        self._notice = _NO_KEY_NOTICE
        return True

    def _plain_key(self, key: str) -> bool:
        """Route a key on a pane with no selectable rows.

        Args:
            key: The key the operator pressed.

        Returns:
            False to end the loop.
        """
        if key == Key.ENTER:
            self._go_back()
            return True
        handled = self._global_key(key)
        if handled is not None:
            return handled
        self._screen.bell()
        self._notice = _NO_KEY_NOTICE
        return True

    def _palette_key(self, key: str) -> bool:
        """Edit the palette query, or leave the palette.

        Args:
            key: The key the operator pressed.

        Returns:
            False to end the loop.
        """
        pane = self._top()
        if key == Key.ESC:
            self._panes.pop()
            return True
        if key == Key.ENTER:
            self._activate()
            return True
        if key in _DOWN_KEYS:
            self._move(1)
            return True
        if key in _UP_KEYS:
            self._move(-1)
            return True
        if key == Key.PGDN:
            self._move(PAGE_STEP)
            return True
        if key == Key.PGUP:
            self._move(-PAGE_STEP)
            return True
        if key == Key.HOME:
            self._jump(first=True)
            return True
        if key == Key.END:
            self._jump(first=False)
            return True
        if key == Key.BACKSPACE:
            if not pane.query:
                self._screen.bell()
                self._notice = "the palette query is already empty"
                return True
            self._set_top(replace(pane, query=pane.query[:-1], selected=0))
            return True
        if _is_text(key):
            self._set_top(replace(pane, query=pane.query + key, selected=0))
            return True
        self._screen.bell()
        self._notice = _NO_KEY_NOTICE
        return True

    def _form_key(self, key: str) -> bool:
        """Collect one answer on the parameter form.

        A focused CHOICE field cycles with j and k; a TEXT or INT field takes
        typed characters, deletes with Backspace, and is validated by
        :func:`tui.contract.build_argv` when Enter commits the whole form.

        Args:
            key: The key the operator pressed.

        Returns:
            False to end the loop.
        """
        if key == Key.ESC:
            self._panes.pop()
            self._notice = f"{self._form_action.title} cancelled"
            return True
        if key == Key.ENTER:
            return self._commit_form()
        action = self._form_action
        field = self._focus()
        param = action.params[_clamp(field, len(action.params))]
        if param.kind is ParamKind.CHOICE and key in _CYCLE_KEYS:
            self._cycle_choice(param, 1 if key == "j" else -1)
            return True
        if key in _DOWN_KEYS:
            self._set_field(field + 1)
            return True
        if key in _UP_KEYS:
            self._set_field(field - 1)
            return True
        if key == Key.PGDN:
            self._set_field(field + PAGE_STEP)
            return True
        if key == Key.PGUP:
            self._set_field(field - PAGE_STEP)
            return True
        if key == Key.HOME:
            self._set_field(0)
            return True
        if key == Key.END:
            self._set_field(len(action.params) - 1)
            return True
        if key == Key.BACKSPACE:
            return self._erase(param)
        if _is_text(key):
            return self._type(param, key)
        self._screen.bell()
        self._notice = _NO_KEY_NOTICE
        return True

    def _confirm_key(self, key: str) -> bool:
        """Collect the confirmation token at the last gate.

        Args:
            key: The key the operator pressed.

        Returns:
            True; the gate is left with Enter or Esc, never with ``q``.
        """
        if key == Key.ESC:
            self._decline_confirm()
            return True
        if key == Key.BACKSPACE:
            self._typed = self._typed[:-1]
            return True
        if key == Key.ENTER:
            return self._submit_token()
        if _is_text(key):
            self._typed += key
            return True
        self._screen.bell()
        self._notice = _TYPE_TOKEN_NOTICE
        return True

    def _stop_key(self, key: str) -> bool:
        """Take the second key of the safe-stop confirmation.

        Args:
            key: The key the operator pressed.

        Returns:
            True; the confirmation always keeps the loop alive.
        """
        if key == _YES_KEY:
            self._safe_stop()
            return True
        if key in (_NO_KEY, Key.ESC):
            self._stop_pending = False
            self._notice = _STOP_CANCELLED_NOTICE
            return True
        self._screen.bell()
        self._notice = _STOP_ARMED_NOTICE
        return True

    def _arm_stop(self) -> bool:
        """Arm the safe stop, or refuse it when the catalog has no stop verb.

        Returns:
            True; arming never ends the loop.
        """
        action = self._find_stop_action()
        if action is None:
            self._screen.bell()
            self._notice = _STOP_MISSING_NOTICE
            return True
        self._stop_action = action
        self._stop_pending = True
        self._notice = _STOP_ARMED_NOTICE
        return True

    def _safe_stop(self) -> None:
        """Send the stack's own stop action down the same gate ladder as a click.

        The confirmation keys never bypass a gate: the read-only refusal, the
        guard verdict, and the action's own token still apply.
        """
        action = self._stop_action
        self._stop_pending = False
        self._session.params = {}
        self._typed = ""
        self._run_action(action)

    def _find_stop_action(self) -> ActionSpec | None:
        """Locate the action that stops the stack.

        Returns:
            The manage ``stop`` verb, else an action whose id ends in ``.stop``,
            or None when the console offers no way to stop.
        """
        for action in self._actions:
            if action.runner is RunnerKind.MANAGE and action.target == _STOP_TARGET:
                return action
        for action in self._actions:
            if action.action_id.endswith(_STOP_ID_SUFFIX):
                return action
        return None

    def _activate(self) -> None:
        """Act on the focused row of the pane on top of the stack."""
        screen = self._top().screen
        if screen is ScreenId.LANES:
            self._open_lane()
            return
        if screen is ScreenId.LANE_GRAPHS:
            self._open_graph()
            return
        if screen is ScreenId.AUDIT:
            self._show_history_row()
            return
        if screen in _ACTION_SCREENS:
            self._choose_action()
            return
        self._screen.bell()
        self._notice = _NO_SELECTION_NOTICE

    def _choose_action(self) -> None:
        """Dispatch the focused catalog row, or say which gate stopped it."""
        model = self._current_model()
        if not model.rows:
            self._screen.bell()
            self._notice = _NO_ROW_NOTICE
            return
        action = self._by_id.get(model.rows[model.selected].key)
        if action is None:
            self._screen.bell()
            self._notice = _READING_NOTICE
            return
        self._run_action(action)

    def _run_action(self, action: ActionSpec) -> None:
        """Walk one action down the gate ladder.

        Args:
            action: The catalog entry the operator selected.
        """
        if not action.is_runnable():
            self._screen.bell()
            reason = action.refuse_reason or _NOT_RUNNABLE_NOTE
            self._notice = f"{action.title} is refused: {reason}"
            return
        if self._session.read_only and action.tier is not RiskTier.READ:
            self._screen.bell()
            self._notice = _READ_ONLY_NOTICE
            return
        verdict = self._verdicts.get(action.action_id) or _DENIED
        if not verdict.allowed:
            self._screen.bell()
            self._notice = f"{action.title} is blocked: {'; '.join(verdict.reasons)}"
            return
        if self._missing_params(action):
            self._open_form(action)
            return
        self._proceed(action)

    def _missing_params(self, action: ActionSpec) -> tuple[ParamSpec, ...]:
        """Which required parameters the operator has not answered yet.

        Args:
            action: The catalog entry being dispatched.

        Returns:
            The parameters that are both required and without an answer or a
            default, in argv order.
        """
        return tuple(
            param
            for param in action.params
            if param.required and not (self._session.params.get(param.name) or param.default)
        )

    def _open_form(self, action: ActionSpec) -> None:
        """Start collecting the answers one action still needs.

        Parameters that carry a default are pre-filled, so the answers handed to
        the dispatcher are the answers the preview showed.

        Args:
            action: The catalog entry being dispatched.
        """
        self._form_action = action
        for param in action.params:
            if param.default and param.name not in self._session.params:
                self._session.params[param.name] = param.default
        missing = self._missing_params(action)
        target = missing[0] if missing else None
        field = next(
            (index for index, param in enumerate(action.params) if param is target),
            0,
        )
        self._open(_Pane(screen=ScreenId.PARAM_FORM, selected=field))

    def _proceed(self, action: ActionSpec) -> None:
        """Send a fully answered action to the token gate or straight out.

        Args:
            action: The catalog entry whose answers are complete.
        """
        error = self._form_error(action)
        if error:
            self._screen.bell()
            self._notice = error
            return
        if action.tier.requires_token():
            self._open_confirm(action)
            return
        self._run_command(action)

    def _form_error(self, action: ActionSpec) -> str:
        """Ask the argv builder whether the answers on file are usable.

        Args:
            action: The catalog entry being answered.

        Returns:
            Empty when ``build_argv`` accepts the answers, else the message the
            operator has to read.
        """
        try:
            build_argv(action, self._session.params)
        except ValueError as exc:
            return str(exc)
        return ""

    def _cycle_choice(self, param: ParamSpec, step: int) -> None:
        """Move a CHOICE answer to its next or previous option.

        Args:
            param: The focused CHOICE parameter.
            step: ``1`` to advance with j, ``-1`` to go back with k.
        """
        if not param.choices:
            self._screen.bell()
            self._notice = f"{param.name} offers no choices"
            return
        values = tuple(choice.value for choice in param.choices)
        current = self._session.params.get(param.name, param.default)
        index = values.index(current) if current in values else -1
        self._session.params[param.name] = values[(index + step) % len(values)]
        self._notice = self._form_error(self._form_action)

    def _type(self, param: ParamSpec, key: str) -> bool:
        """Append one character to a text or integer answer.

        Args:
            param: The focused parameter.
            key: The character the operator typed.

        Returns:
            True; typing never ends the loop.
        """
        if param.kind is ParamKind.CHOICE:
            self._screen.bell()
            self._notice = f"{param.name} is a choice; press j or k"
            return True
        current = self._session.params.get(param.name, param.default)
        self._session.params[param.name] = current + key
        self._notice = self._form_error(self._form_action)
        return True

    def _erase(self, param: ParamSpec) -> bool:
        """Delete the last character of a text or integer answer.

        Args:
            param: The focused parameter.

        Returns:
            True; editing never ends the loop.
        """
        if param.kind in (ParamKind.CHOICE, ParamKind.FLAG):
            self._screen.bell()
            self._notice = f"{param.name} is a {param.kind.value}; use j and k"
            return True
        current = self._session.params.get(param.name, param.default)
        self._session.params[param.name] = current[:-1]
        self._notice = self._form_error(self._form_action)
        return True

    def _set_field(self, field: int) -> None:
        """Focus one parameter of the form.

        Args:
            field: Parameter index the operator moved to.
        """
        count = len(self._form_action.params)
        self._set_top(replace(self._top(), selected=_clamp(field, count)))

    def _commit_form(self) -> bool:
        """Validate the answers on file and move on to the token gate.

        Returns:
            True; a bad answer keeps the operator on the form.
        """
        action = self._form_action
        error = self._form_error(action)
        if error:
            self._screen.bell()
            self._notice = error
            return True
        self._panes.pop()
        self._proceed(action)
        return True

    def _open_confirm(self, action: ActionSpec) -> None:
        """Open the typed-token gate for one fully answered action.

        Args:
            action: The catalog entry about to run.
        """
        self._confirm_action = action
        self._typed = ""
        self._confirm_argv = build_argv(action, self._session.params)
        self._open(_Pane(screen=ScreenId.CONFIRM))

    def _submit_token(self) -> bool:
        """Check the typed token and dispatch, or ring and stay put.

        Returns:
            True; a wrong token leaves the operator on the gate.
        """
        action = self._confirm_action
        token = action.confirm.token()
        if self._typed != token:
            self._screen.bell()
            self._notice = f"that is not the token; type {token} exactly"
            return True
        self._panes.pop()
        self._run_command(action)
        return True

    def _decline_confirm(self) -> None:
        """Record that the operator walked away from the token gate."""
        result = CommandResult(
            action_id=self._confirm_action.action_id,
            argv=self._confirm_argv,
            returncode=UNMEASURED,
            output="",
            duration_s=0.0,
            ran=False,
            note=_DECLINE_NOTE,
        )
        self._session.history.append(result)
        self._last_result = result
        self._session.params = {}
        self._panes.pop()
        self._panes.append(_Pane(screen=ScreenId.RESULT))
        self._notice = f"{result.action_id}: {_DECLINE_NOTE}"

    def _run_command(self, action: ActionSpec) -> None:
        """Draw the progress pane, dispatch, and hand the outcome to the operator.

        The dispatcher is synchronous, so the progress frame is the last thing
        visible before the call and the result frame replaces it in place.

        Args:
            action: The catalog entry that cleared every gate.
        """
        answers = dict(self._session.params)
        token = self._typed
        self._typed = ""
        self._session.params = {}
        self._progress_action = action
        self._panes.append(_Pane(screen=ScreenId.PROGRESS))
        self._draw()
        result = self._dispatch_cb(action, answers, token)
        self._session.history.append(result)
        self._last_result = result
        self._panes[-1] = _Pane(screen=ScreenId.RESULT)
        self._notice = _result_notice(result)

    def _open_lane(self) -> None:
        """Enter the focused lane."""
        if not self._lanes:
            self._screen.bell()
            self._notice = _EMPTY_LANES_NOTICE
            return
        self._lane = self._lanes[self._focus()]
        self._open(_Pane(screen=ScreenId.LANE_GRAPHS))

    def _open_graph(self) -> None:
        """Open the focused graph in the detail pane."""
        if not self._graphs:
            self._screen.bell()
            self._notice = f"lane {self._lane.lane_id} has no promoted graphs"
            return
        self._graph = self._graphs[self._focus()]
        self._open(_Pane(screen=ScreenId.GRAPH_DETAIL))

    def _show_history_row(self) -> None:
        """Show the outcome of the focused operator-log entry."""
        history = self._session.history
        if not history:
            self._screen.bell()
            self._notice = _EMPTY_AUDIT_NOTICE
            return
        self._last_result = history[self._focus()]
        self._open(_Pane(screen=ScreenId.RESULT))

    def _move(self, delta: int) -> None:
        """Move the focused row of the top pane.

        Args:
            delta: Rows to move; negative moves up.
        """
        model = self._current_model()
        count = len(model.rows)
        if count == 0:
            self._screen.bell()
            self._notice = _NO_ROWS_NOTICE
            return
        pane = self._top()
        self._set_top(replace(pane, selected=_clamp(model.selected + delta, count)))

    def _jump(self, *, first: bool) -> None:
        """Move the focus to the first or the last row of the top pane.

        Args:
            first: True for the first row, False for the last.
        """
        count = len(self._current_model().rows)
        if count == 0:
            self._screen.bell()
            self._notice = _NO_ROWS_NOTICE
            return
        self._set_top(replace(self._top(), selected=0 if first else count - 1))

    def _focus(self) -> int:
        """The row the model has focused, which is the row Enter acts on.

        Returns:
            The focused index the view layer settled on; the view may move the
            focus the operator left behind (the dashboard lands on the first
            runnable quick action), so the model, not the pane, is the truth.
        """
        return self._current_model().selected

    def _go_back(self) -> None:
        """Leave the top pane, or say that there is nowhere left to go."""
        if len(self._panes) <= 1:
            self._screen.bell()
            self._notice = _ROOT_ESC_NOTICE
            return
        self._panes.pop()
        self._stop_pending = False

    def _open(self, pane: _Pane) -> None:
        """Read what a pane needs, push it, and clear the notice slot.

        Args:
            pane: The pane to show.
        """
        self._load(pane)
        self._panes.append(pane)
        self._notice = _NOTICE_ON_OPEN

    def _load(self, pane: _Pane) -> None:
        """Refresh the browse cache a pane is about to render from.

        Args:
            pane: The pane being opened; only the two browsers read the disk.
        """
        if pane.screen is ScreenId.LANES:
            self._lanes = tuple(self._lane_source(self._config.repo_root))
        if pane.screen is ScreenId.LANE_GRAPHS:
            self._graphs = tuple(self._graph_source(self._config.repo_root, self._lane.lane_id))

    def _pane_for_group(self, group: Group) -> _Pane:
        """Build the pane a section's hotkey opens.

        Args:
            group: The section the operator jumped to.

        Returns:
            The dashboard, lanes, audit, and help sections open their own pane;
            every other section opens its action list.
        """
        return _Pane(screen=_SPECIAL_GROUP_SCREEN.get(group, ScreenId.GROUP), group=group)

    def _top(self) -> _Pane:
        """The pane on top of the navigation stack.

        Returns:
            The most recently opened pane; the stack never empties, because
            :meth:`_go_back` refuses to pop the last one.
        """
        return self._panes[-1]

    def _set_top(self, pane: _Pane) -> None:
        """Replace the pane on top of the navigation stack.

        Args:
            pane: The pane that takes its place.
        """
        self._panes[-1] = pane

    def _actions_by_group(self, group: Group) -> tuple[ActionSpec, ...]:
        """The catalog entries that belong to one section.

        Args:
            group: The section being listed.

        Returns:
            Matching actions in catalog order.
        """
        return tuple(action for action in self._actions if action.group is group)

    def _quick_actions(self) -> tuple[ActionSpec, ...]:
        """The actions the landing screen offers up front.

        Returns:
            At most :data:`QUICK_LIMIT` entries from the dashboard section.
        """
        return self._actions_by_group(Group.DASHBOARD)[:QUICK_LIMIT]

    def _current_model(self) -> ViewModel:
        """Build the model for the pane on top of the stack.

        Returns:
            The model the view layer produced, with the detail pane folded away
            when the operator hid it and the notice line placed first so a
            refusal is never scrolled off.
        """
        model = self._model_for_pane()
        detail = model.detail if self._detail_open else ()
        if self._notice:
            detail = (Line(self._notice, Style.ALERT), *detail)
        if detail == model.detail:
            return model
        return replace(model, detail=detail)

    def _dashboard_model(self, pane: _Pane) -> ViewModel:
        """Build the landing screen, honouring a cursor the operator moved.

        Args:
            pane: The dashboard pane on top of the stack.

        Returns:
            The dashboard model; the view chooses the opening focus (the first
            runnable quick action) until a cursor key moves it.
        """
        model = views.dashboard(self._health, self._verdicts, self._quick_actions())
        if pane.selected == _UNSET_FOCUS:
            return model
        return replace(model, selected=_clamp(pane.selected, len(model.rows)))

    def _model_for_pane(self) -> ViewModel:
        """Ask the view layer for the model of the top pane.

        Returns:
            One :class:`~tui.contract.ViewModel` per pane kind; a pane that is
            not open renders its placeholder, which the stack never shows.
        """
        pane = self._top()
        screen = pane.screen
        if screen is ScreenId.DASHBOARD:
            return self._dashboard_model(pane)
        if screen is ScreenId.GROUP:
            return views.group_list(
                pane.group, self._actions_by_group(pane.group), self._verdicts, pane.selected
            )
        if screen is ScreenId.PALETTE:
            return views.palette(pane.query, self._actions, self._verdicts, pane.selected)
        if screen is ScreenId.PARAM_FORM:
            return views.param_form(self._form_action, self._session.params, pane.selected)
        if screen is ScreenId.CONFIRM:
            return views.confirm_view(self._confirm_action, self._confirm_argv, self._typed)
        if screen is ScreenId.PROGRESS:
            return views.progress_view(self._progress_action, ())
        if screen is ScreenId.RESULT:
            return views.result_view(self._last_result)
        if screen is ScreenId.LANES:
            return views.lane_list(self._lanes, pane.selected)
        if screen is ScreenId.LANE_GRAPHS:
            return views.graph_list(self._lane, self._graphs, pane.selected)
        if screen is ScreenId.GRAPH_DETAIL:
            return views.graph_detail(self._graph)
        if screen is ScreenId.AUDIT:
            return views.audit_view(self._session.history, pane.selected)
        return views.help_view()

    def _draw(self) -> None:
        """Render the top pane through the view layer and flush it to the screen.

        The status bar owns the top row and the frame's key strip owns the last,
        so the body gets the rows between them and never more than the terminal
        has.
        """
        rows, cols = self._screen.size()
        frame = views.render(self._current_model(), cols, max(rows - 1, 1))
        self._screen.clear()
        self._paint(0, views.status_bar(self._health, cols), rows)
        for offset, line in enumerate(frame.lines, start=1):
            self._paint(offset, line, rows)
        self._screen.present()

    def _paint(self, row: int, line: Line, rows: int) -> None:
        """Draw one line, but only where the terminal has room for it.

        Args:
            row: Zero-based row index.
            line: The line to draw.
            rows: Rows the terminal has.
        """
        if 0 <= row < rows:
            self._screen.draw(row, line.text, style=line.style)
