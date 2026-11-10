"""The curses adapter is a translation layer, so a stub proves everything about it.

``tui.screen`` is the only module in the package allowed to import curses. These
tests never need a TTY: a stub curses module and a fake window that records calls
drive every method, which is what keeps the coverage gate reachable on a file
whose real behavior needs a terminal.
"""

from __future__ import annotations

import curses
import importlib
import sys
from collections.abc import Iterator
from typing import cast

import pytest

from tui import contract as c
from tui import screen


class _StubCurses:
    """The curses surface ``tui.screen`` touches, with every call recorded."""

    # Attributes, color numbers, and key codes at their ncurses values.
    A_NORMAL = 0
    A_BOLD = 1
    A_DIM = 2
    A_REVERSE = 4
    A_UNDERLINE = 8
    COLOR_BLACK = 0
    COLOR_RED = 1
    COLOR_GREEN = 2
    COLOR_YELLOW = 3
    COLOR_CYAN = 6
    KEY_DOWN = 258
    KEY_UP = 259
    KEY_LEFT = 260
    KEY_RIGHT = 261
    KEY_HOME = 262
    KEY_BACKSPACE = 263
    KEY_IC = 331
    KEY_NPAGE = 338
    KEY_PPAGE = 339
    KEY_ENTER = 343
    KEY_BTAB = 353
    KEY_END = 360
    KEY_RESIZE = 410

    def __init__(self, *, colors: bool = True) -> None:
        """Start an empty call log.

        Args:
            colors: Whether this fake terminal claims color support.
        """
        self.calls: list[tuple[object, ...]] = []
        self.colors = colors

    def has_colors(self) -> bool:
        """Whether this fake terminal has color.

        Returns:
            The value the test asked for.
        """
        return self.colors

    def start_color(self) -> None:
        """Record that color was started."""
        self.calls.append(("start_color",))

    def init_pair(self, pair_id: int, foreground: int, background: int) -> None:
        """Record a color pair registration.

        Args:
            pair_id: Pair slot.
            foreground: Foreground color.
            background: Background color.
        """
        self.calls.append(("init_pair", pair_id, foreground, background))

    def color_pair(self, pair_id: int) -> int:
        """Turn a pair id into an attribute mask.

        Args:
            pair_id: Pair slot.

        Returns:
            An attribute value distinguishable per pair.
        """
        return 256 + pair_id

    def doupdate(self) -> None:
        """Record the flush."""
        self.calls.append(("doupdate",))

    def beep(self) -> None:
        """Record the refusal sound."""
        self.calls.append(("beep",))

    def curs_set(self, visibility: int) -> None:
        """Record the cursor visibility request.

        Args:
            visibility: The visibility the console asked for.
        """
        self.calls.append(("curs_set", visibility))

    def set_escdelay(self, milliseconds: int) -> None:
        """Record how long curses waits to tell Escape from a sequence.

        Args:
            milliseconds: The escape delay the console asked for.
        """
        self.calls.append(("set_escdelay", milliseconds))

    def wrapper(self, starter: Callable[[curses.window], int]) -> int:
        """Run the starter against a fake stdscr, the way curses would.

        Args:
            starter: The function ``curses.wrapper`` would be handed.

        Returns:
            Whatever the starter returned.
        """
        self.calls.append(("wrapper",))
        return starter(cast("curses.window", _FakeWindow()))


class _FakeWindow:
    """Records what the adapter asks a curses window to do."""

    def __init__(
        self, rows: int = 24, cols: int = 80, keys: list[int] | None = None
    ) -> None:
        """Set the geometry and the keys ``getch`` will hand back.

        Args:
            rows: Screen height the window reports.
            cols: Screen width the window reports.
            keys: Codes returned by successive ``getch`` calls.
        """
        self.rows = rows
        self.cols = cols
        self.keys = list(keys or [])
        self.added: list[tuple[int, int, str, int]] = []
        self.erasures = 0
        self.refreshes = 0
        self.timeouts: list[int] = []
        self.keypads: list[bool] = []

    def keypad(self, flag: bool) -> None:
        """Record the special-key mode the console asked for.

        Args:
            flag: Whether special keys should be translated.
        """
        self.keypads.append(flag)

    def getmaxyx(self) -> tuple[int, int]:
        """Report the geometry.

        Returns:
            ``(rows, cols)``.
        """
        return (self.rows, self.cols)

    def erase(self) -> None:
        """Count an erase."""
        self.erasures += 1

    def addstr(self, row: int, col: int, text: str, attr: int) -> None:
        """Record one row write.

        Args:
            row: Row index.
            col: Column index.
            text: What was written.
            attr: Attribute mask used.
        """
        self.added.append((row, col, text, attr))

    def noutrefresh(self) -> None:
        """Count a flush request."""
        self.refreshes += 1

    def timeout(self, milliseconds: int) -> None:
        """Record the blocking timeout the adapter set.

        Args:
            milliseconds: Read deadline in milliseconds.
        """
        self.timeouts.append(milliseconds)

    def getch(self) -> int:
        """Return the next queued key.

        Returns:
            The next code, or ``-1`` when the queue is empty.
        """
        if not self.keys:
            return -1
        return self.keys.pop(0)


def _surface(window: _FakeWindow) -> screen.CursesScreen:
    """Bind the adapter to a fake window.

    Args:
        window: The window the adapter should draw on.

    Returns:
        The adapter, ready for one test's assertions.
    """
    return screen.CursesScreen(cast("curses.window", window))


@pytest.fixture(autouse=True)
def curses_stub(monkeypatch: pytest.MonkeyPatch) -> Iterator[_StubCurses]:
    """Bind ``tui.screen`` to the stubbed curses for every test in this module.

    Args:
        monkeypatch: Fixture that restores ``sys.modules`` afterwards.

    Yields:
        The stub the module was reloaded against.
    """
    stub = _StubCurses()
    monkeypatch.setitem(sys.modules, "curses", stub)
    importlib.reload(screen)
    try:
        yield stub
    finally:
        importlib.reload(screen)


MAPPED_KEYS: tuple[tuple[int, str], ...] = (
    (_StubCurses.KEY_UP, c.Key.UP),
    (_StubCurses.KEY_DOWN, c.Key.DOWN),
    (_StubCurses.KEY_LEFT, c.Key.LEFT),
    (_StubCurses.KEY_RIGHT, c.Key.RIGHT),
    (_StubCurses.KEY_ENTER, c.Key.ENTER),
    (10, c.Key.ENTER),
    (13, c.Key.ENTER),
    (_StubCurses.KEY_BACKSPACE, c.Key.BACKSPACE),
    (127, c.Key.BACKSPACE),
    (27, c.Key.ESC),
    (_StubCurses.KEY_PPAGE, c.Key.PGUP),
    (_StubCurses.KEY_NPAGE, c.Key.PGDN),
    (_StubCurses.KEY_HOME, c.Key.HOME),
    (_StubCurses.KEY_END, c.Key.END),
    (9, c.Key.TAB),
    (_StubCurses.KEY_BTAB, c.Key.BACKTAB),
    (_StubCurses.KEY_RESIZE, c.Key.RESIZE),
)
"""Every ``(getch code, contract key name)`` pair the adapter must translate."""


def test_a_monochrome_style_becomes_its_attribute(curses_stub: _StubCurses) -> None:
    """The intents that need no color map straight onto curses attributes."""
    assert screen.attr_for(c.Style.NORMAL) == curses_stub.A_NORMAL
    assert screen.attr_for(c.Style.BOLD) == curses_stub.A_BOLD
    assert screen.attr_for(c.Style.DIM) == curses_stub.A_DIM
    assert screen.attr_for(c.Style.REVERSE) == curses_stub.A_REVERSE
    assert screen.attr_for(c.Style.TITLE) == curses_stub.A_BOLD | curses_stub.A_UNDERLINE


@pytest.mark.parametrize(
    ("style", "pair_id"),
    [
        (c.Style.OK, 1),
        (c.Style.WARN, 2),
        (c.Style.BAD, 3),
        (c.Style.ACCENT, 4),
        (c.Style.ALERT, 3),
    ],
)
def test_a_colored_style_becomes_its_pair(
    curses_stub: _StubCurses, style: c.Style, pair_id: int
) -> None:
    """Every colored intent resolves to a registered color pair."""
    assert screen.attr_for(style) == curses_stub.color_pair(pair_id)


def test_the_style_tables_partition_the_enum() -> None:
    """A style with no attributes would raise at draw time, so none may be missed."""
    mono = set(screen._MONO_ATTRS)
    colored = set(screen._STYLE_PAIR_IDS)
    assert mono.isdisjoint(colored)
    assert mono | colored == set(c.Style)


def test_init_colors_registers_every_pair(curses_stub: _StubCurses) -> None:
    """The pairs attr_for asks for exist before the first frame is drawn."""
    screen.init_colors()
    screen.init_colors()
    pairs = [call for call in curses_stub.calls if call[0] == "init_pair"]
    assert curses_stub.calls[0] == ("start_color",)
    assert {call[1] for call in pairs} == {1, 2, 3, 4}
    assert len(pairs) == 8


def test_init_colors_leaves_a_dumb_terminal_alone(
    curses_stub: _StubCurses,
) -> None:
    """A terminal without color keeps the mono attributes and sees no calls."""
    curses_stub.colors = False
    screen.init_colors()
    assert curses_stub.calls == []


@pytest.mark.parametrize(("code", "name"), MAPPED_KEYS)
def test_every_mapped_key_code_has_a_contract_name(code: int, name: str) -> None:
    """Each escape sequence arrives as one of the names the keymap matches."""
    assert screen.normalize_key(code) == name


def test_the_key_table_maps_exactly_the_documented_names() -> None:
    """The adapter translates every key the contract names, and nothing else."""
    assert set(screen._KEY_NAMES.values()) == {name for _, name in MAPPED_KEYS}
    assert len(screen._KEY_NAMES) == len(MAPPED_KEYS)


@pytest.mark.parametrize(("code", "char"), [(97, "a"), (32, " "), (126, "~"), (42, "*")])
def test_a_printable_code_comes_back_as_itself(code: int, char: str) -> None:
    """A character the operator typed is the key; nothing wraps it."""
    assert screen.normalize_key(code) == char


@pytest.mark.parametrize("code", [-1, 0, 8, 31, 200, 513])
def test_an_unusable_code_reads_as_a_timeout(code: int) -> None:
    """A control code, ``ERR``, or an unmapped sequence is not a keypress."""
    assert screen.normalize_key(code) == c.Key.TIMEOUT


def test_the_adapter_satisfies_the_screen_protocol() -> None:
    """The app draws through the protocol, so the adapter must implement all of it."""
    for name in ("size", "clear", "draw", "present", "read_key", "bell"):
        assert callable(getattr(screen.CursesScreen, name, None)), name


def test_size_reports_the_window_and_never_zero() -> None:
    """A window that reports a collapsed size still lets a view lay out one row."""
    assert _surface(_FakeWindow(24, 80)).size() == (24, 80)
    assert _surface(_FakeWindow(0, 0)).size() == (1, 1)


def test_clear_erases_the_back_buffer() -> None:
    """One frame starts from a clean slate."""
    window = _FakeWindow()
    _surface(window).clear()
    assert window.erasures == 1


def test_draw_writes_one_styled_row_at_the_left_margin(curses_stub: _StubCurses) -> None:
    """A row lands at column 0 with the attributes the style resolves to."""
    window = _FakeWindow()
    _surface(window).draw(3, "free 41 GiB", style=c.Style.OK)
    assert window.added == [(3, 0, "free 41 GiB", screen.attr_for(c.Style.OK))]


def test_draw_truncates_to_the_terminal_width() -> None:
    """A long line is cut, never wrapped, so the frame cannot scroll sideways."""
    window = _FakeWindow(cols=10)
    _surface(window).draw(0, "x" * 40)
    assert window.added[0][2] == "x" * 9


def test_draw_ignores_a_row_outside_the_screen() -> None:
    """An off-screen row from a stale view is dropped instead of raising."""
    window = _FakeWindow(rows=5)
    surface = _surface(window)
    surface.draw(-1, "above")
    surface.draw(5, "below")
    surface.draw(99, "far below")
    assert window.added == []


def test_present_flushes_in_one_update(curses_stub: _StubCurses) -> None:
    """The frame appears at once, so a running command's tail does not flicker."""
    window = _FakeWindow()
    _surface(window).present()
    assert window.refreshes == 1
    assert curses_stub.calls == [("doupdate",)]


def test_read_key_sets_the_deadline_and_names_the_key() -> None:
    """The blocking read is bounded, and the code comes back as a key name."""
    window = _FakeWindow(keys=[_StubCurses.KEY_DOWN, ord("j"), -1])
    surface = _surface(window)
    assert surface.read_key(0.25) == c.Key.DOWN
    assert surface.read_key(0.0) == "j"
    assert surface.read_key(1.0) == c.Key.TIMEOUT
    assert window.timeouts == [250, 0, 1000]


def test_bell_uses_the_terminal_not_the_layout(curses_stub: _StubCurses) -> None:
    """A refusal is heard; nothing on screen moves."""
    window = _FakeWindow()
    _surface(window).bell()
    assert curses_stub.calls == [("beep",)]
    assert window.added == []


# -- run_with_screen ---------------------------------------------------------


def test_the_launcher_sets_the_terminal_up_then_hands_over_one_screen(
    curses_stub: _StubCurses,
) -> None:
    """The loop gets exactly one adapter, after the cursor and colors are set."""
    handed: list[object] = []

    def on_screen(live: c.Screen) -> int:
        """Remember what the launcher passed and return an exit code.

        Args:
            live: The screen the launcher built.

        Returns:
            The code the launcher is expected to propagate.
        """
        handed.append(live)
        return 7

    assert screen.run_with_screen(on_screen) == 7
    assert len(handed) == 1
    assert isinstance(handed[0], screen.CursesScreen)
    assert ("curs_set", 0) in curses_stub.calls
    assert ("wrapper",) in curses_stub.calls
    window = cast("_FakeWindow", cast("screen.CursesScreen", handed[0])._win)
    assert window.keypads == [True]
    assert ("start_color",) in curses_stub.calls
    escdelays = [
        call[1] for call in curses_stub.calls if call and call[0] == "set_escdelay"
    ]
    assert escdelays, "curses must be told to stop waiting a second on Escape"
    assert escdelays[0] <= 50, (
        "the 1000 ms default makes Escape feel dead on a remote session and "
        "mangles an Escape pressed just before another key"
    )


def test_the_launcher_reports_what_the_loop_returned(
    curses_stub: _StubCurses,
) -> None:
    """The loop's code is the process exit code, unchanged."""
    assert screen.run_with_screen(lambda _live: 0) == 0
    assert screen.run_with_screen(lambda _live: 2) == 2
