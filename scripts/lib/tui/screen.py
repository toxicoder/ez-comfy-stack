"""The one curses adapter in the package, kept as small as a translation layer.

Every other module draws through :class:`tui.contract.Screen` and never names a
terminal. This file is where that protocol meets curses: it converts a
:class:`~tui.contract.Style` into an attribute mask, a curses key code into a
:class:`~tui.contract.Key` name, and a flush into one ``noutrefresh``. There is
no layout, no truncation policy beyond the row width, and no key handling here,
because each of those decisions belongs to a view the suite can drive without a
TTY.

Keeping it this thin is what makes the console testable: the tests hand the
adapter a stub ``curses`` module and a fake window that records calls, so
100% coverage is reachable with no terminal attached.
"""

from __future__ import annotations

import curses
from collections.abc import Callable

from tui.contract import Key, Screen, Style

_MONO_ATTRS: dict[Style, int] = {
    Style.NORMAL: curses.A_NORMAL,
    Style.BOLD: curses.A_BOLD,
    Style.DIM: curses.A_DIM,
    Style.REVERSE: curses.A_REVERSE,
    Style.TITLE: curses.A_BOLD | curses.A_UNDERLINE,
}
"""Attribute masks for the styles that need no color pair."""

_OK_PAIR = 1
"""Color pair id for :attr:`~tui.contract.Style.OK`."""

_WARN_PAIR = 2
"""Color pair id for :attr:`~tui.contract.Style.WARN`."""

_BAD_PAIR = 3
"""Color pair id for the two red styles."""

_ACCENT_PAIR = 4
"""Color pair id for :attr:`~tui.contract.Style.ACCENT`."""

_STYLE_PAIR_IDS: dict[Style, int] = {
    Style.OK: _OK_PAIR,
    Style.WARN: _WARN_PAIR,
    Style.BAD: _BAD_PAIR,
    Style.ACCENT: _ACCENT_PAIR,
    Style.ALERT: _BAD_PAIR,
}
"""Color pair id per style; every key here is absent from ``_MONO_ATTRS``."""

_COLOR_INIT: tuple[tuple[int, int, int], ...] = (
    (_OK_PAIR, curses.COLOR_GREEN, curses.COLOR_BLACK),
    (_WARN_PAIR, curses.COLOR_YELLOW, curses.COLOR_BLACK),
    (_BAD_PAIR, curses.COLOR_RED, curses.COLOR_BLACK),
    (_ACCENT_PAIR, curses.COLOR_CYAN, curses.COLOR_BLACK),
)
"""``(pair id, foreground, background)`` registered by :func:`init_colors`."""

_KEY_NAMES: dict[int, str] = {
    curses.KEY_UP: Key.UP,
    curses.KEY_DOWN: Key.DOWN,
    curses.KEY_LEFT: Key.LEFT,
    curses.KEY_RIGHT: Key.RIGHT,
    curses.KEY_ENTER: Key.ENTER,
    10: Key.ENTER,  # line feed: Enter as getch reports it outside keypad mode
    13: Key.ENTER,  # carriage return: the same key on some terminals
    curses.KEY_BACKSPACE: Key.BACKSPACE,
    127: Key.BACKSPACE,  # delete: what a terminal sends for Backspace
    27: Key.ESC,  # escape: KEY_ESC is absent from some curses builds
    curses.KEY_PPAGE: Key.PGUP,
    curses.KEY_NPAGE: Key.PGDN,
    curses.KEY_HOME: Key.HOME,
    curses.KEY_END: Key.END,
    9: Key.TAB,  # horizontal tab: KEY_TAB is absent from some curses builds
    curses.KEY_BTAB: Key.BACKTAB,
    curses.KEY_RESIZE: Key.RESIZE,
}
"""Curses key code to :class:`~tui.contract.Key` name, before printable codes."""

_PRINTABLE_LOW = 32
"""First key code :func:`normalize_key` returns as itself: a space."""

_PRINTABLE_HIGH = 126
"""Last key code :func:`normalize_key` returns as itself: a tilde."""


def init_colors() -> None:
    """Register the color pairs :func:`attr_for` asks for.

    Calling it twice is harmless: curses replaces a pair's colors in place, so
    re-initializing after a terminal reset is safe. A terminal without color
    support is left alone, and the mono attributes still read.
    """
    if not curses.has_colors():
        return
    curses.start_color()
    for pair_id, foreground, background in _COLOR_INIT:
        curses.init_pair(pair_id, foreground, background)


def attr_for(style: Style) -> int:
    """Translate a drawing intent into curses attributes.

    Args:
        style: The intent the view asked for.

    Returns:
        The attribute mask to hand to ``addstr``.
    """
    if style in _MONO_ATTRS:
        return _MONO_ATTRS[style]
    return curses.color_pair(_STYLE_PAIR_IDS[style])


def normalize_key(code: int) -> str:
    """Translate one ``getch`` code into a :class:`~tui.contract.Key` name.

    Args:
        code: The raw code curses returned.

    Returns:
        A :class:`~tui.contract.Key` name, the character itself for a printable
        code, or :attr:`~tui.contract.Key.TIMEOUT` for anything else.
    """
    if code in _KEY_NAMES:
        return _KEY_NAMES[code]
    if _PRINTABLE_LOW <= code <= _PRINTABLE_HIGH:
        return chr(code)
    return Key.TIMEOUT


class CursesScreen:
    """Draws :class:`tui.contract.Screen` calls on a real curses window.

    Each method is one or two curses calls. Nothing here decides what to show,
    where a row goes, or what a key means beyond the table above.
    """

    def __init__(self, stdscr: curses.window) -> None:
        """Bind the adapter to the window curses started with.

        Args:
            stdscr: The window to draw on.
        """
        self._win = stdscr

    def size(self) -> tuple[int, int]:
        """Current geometry of the window.

        Returns:
            ``(rows, cols)``, each clamped to at least 1.
        """
        rows, cols = self._win.getmaxyx()
        return (max(rows, 1), max(cols, 1))

    def clear(self) -> None:
        """Erase the back buffer before the next frame is drawn."""
        self._win.erase()

    def draw(self, row: int, text: str, *, style: Style = Style.NORMAL) -> None:
        """Write one row, leaving the last cell free.

        The row is cut one column short of the width: writing the bottom-right
        cell is the one thing curses treats as an error, and a row that reaches
        the edge never needs that cell.

        Args:
            row: Zero-based row index; a row off the screen is ignored.
            text: Content to write.
            style: Drawing intent.
        """
        rows, cols = self.size()
        if 0 <= row < rows:
            self._win.addstr(row, 0, text[: max(cols - 1, 1)], attr_for(style))

    def present(self) -> None:
        """Flush the drawn rows to the terminal in one update."""
        self._win.noutrefresh()
        curses.doupdate()

    def read_key(self, timeout_s: float) -> str:
        """Wait for one keypress.

        Args:
            timeout_s: Seconds to wait before giving up.

        Returns:
            A :class:`~tui.contract.Key` name or a single printable character.
        """
        self._win.timeout(int(timeout_s * 1000))
        return normalize_key(self._win.getch())

    def bell(self) -> None:
        """Signal a refusal without moving anything on screen."""
        curses.beep()


def run_with_screen(on_screen: Callable[[Screen], int]) -> int:
    """Open curses, hand one :class:`~tui.contract.Screen` to the loop, restore the terminal.

    This is the only place curses is started and the only place it is torn down,
    so a crash inside the loop still leaves the operator a working shell rather
    than a garbled TTY. ``curses.wrapper`` is what guarantees that restore.

    Args:
        on_screen: Called once with the live screen; returns the process exit code.

    Returns:
        Whatever ``on_screen`` returned.
    """

    def _main(stdscr: curses.window) -> int:
        """Prepare the terminal and hand one adapter to the loop.

        Args:
            stdscr: The window ``curses.wrapper`` opened.

        Returns:
            Whatever the loop returned, which becomes the exit code.
        """
        curses.curs_set(0)
        stdscr.keypad(True)
        init_colors()
        return on_screen(CursesScreen(stdscr))

    return int(curses.wrapper(_main))
