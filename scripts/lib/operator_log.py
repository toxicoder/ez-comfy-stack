"""Operator progress helpers for host Python (stderr only).

Matches scripts/lib/progress.sh: [ez-comfy] prefix, TTY rewrite, NO_COLOR.
Stdout stays JSON / JSONL.
"""

from __future__ import annotations

import os
import sys
import time
from typing import TextIO

# Stderr banner and TTY rewrite latch (shared with disk_catalog).
PREFIX = "[ez-comfy]"
_REWRITE = False


def progress_enabled() -> bool:
    """True unless EZ_COMFY_PROGRESS=0.

    Returns:
        Whether operator progress bars and heartbeats may emit.
    """
    return os.environ.get("EZ_COMFY_PROGRESS", "1") != "0"


def use_color(*, stream: TextIO | None = None) -> bool:
    """True when the stream is a TTY and NO_COLOR is unset.

    Args:
        stream: Stream to test. Defaults to stderr.

    Returns:
        Whether ANSI color is allowed.
    """
    target = stream if stream is not None else sys.stderr
    if os.environ.get("NO_COLOR"):
        return False
    return bool(target.isatty())


def progress_interval_s() -> float:
    """Heartbeat seconds from EZ_COMFY_PROGRESS_INTERVAL (0 disables).

    Returns:
        Interval in seconds. Invalid values fall back to 2.0.
    """
    raw = os.environ.get("EZ_COMFY_PROGRESS_INTERVAL", "2")
    try:
        return float(raw)
    except ValueError:
        return 2.0


def format_elapsed(secs: float) -> str:
    """Format seconds as m:ss or h:mm:ss.

    Args:
        secs: Elapsed seconds (negative values clamp to 0).

    Returns:
        Human elapsed string.
    """
    total = int(secs)
    if total < 0:
        total = 0
    hours, rem = divmod(total, 3600)
    minutes, seconds = divmod(rem, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def bar_fill(filled: int, width: int = 20) -> str:
    """Unicode bar: filled cells then empty cells.

    Args:
        filled: Number of filled cells.
        width: Total cells. Non-positive values become 20.

    Returns:
        String of ``▓`` / ``░`` cells.
    """
    if width <= 0:
        width = 20
    if filled < 0:
        filled = 0
    if filled > width:
        filled = width
    return ("▓" * filled) + ("░" * (width - filled))


def emit(msg: str, *, rewrite: bool = False, stream: TextIO | None = None) -> None:
    """Write a prefixed line to stderr.

    TTY heartbeats rewrite the current line; non-TTY always emits a newline.

    Args:
        msg: Body without the ``[ez-comfy]`` prefix.
        rewrite: When True and the stream is a TTY, rewrite the current line.
        stream: Destination. Defaults to stderr.
    """
    global _REWRITE
    target = stream if stream is not None else sys.stderr
    if rewrite and target.isatty() and progress_enabled():
        target.write(f"\r\033[K{PREFIX} {msg}")
        target.flush()
        _REWRITE = True
        return
    if _REWRITE:
        target.write("\n")
        _REWRITE = False
    target.write(f"{PREFIX} {msg}\n")
    target.flush()


def log(msg: str) -> None:
    """Informational line (never rewrites).

    Args:
        msg: Message body.
    """
    emit(msg, rewrite=False)


def warn(msg: str) -> None:
    """Warning line.

    Args:
        msg: Warning body (prefixed with ``[WARN]``).
    """
    emit(f"[WARN] {msg}", rewrite=False)


def error(msg: str) -> None:
    """Error line (does not exit).

    Args:
        msg: Error body (prefixed with ``[ERROR]``).
    """
    emit(f"[ERROR] {msg}", rewrite=False)


def log_ok(msg: str) -> None:
    """Success line.

    Args:
        msg: Success body (prefixed with a check mark).
    """
    emit(f"✓ {msg}", rewrite=False)


def log_step(n: int, total: int, msg: str) -> None:
    """Numbered phase banner.

    Args:
        n: Current 1-based step.
        total: Total steps.
        msg: Phase title.
    """
    emit(f"══ {n}/{total} ══ {msg}", rewrite=False)


def log_debug(msg: str) -> None:
    """Debug line when LAB_DEBUG=1 or EZ_COMFY_LOG_LEVEL=debug.

    Args:
        msg: Debug body.
    """
    if os.environ.get("LAB_DEBUG") == "1" or os.environ.get(
        "EZ_COMFY_LOG_LEVEL", "info"
    ) == "debug":
        emit(f"[debug] {msg}", rewrite=False)


def progress_bar(cur: int, total: int, label: str = "", extra: str = "") -> None:
    """Percent bar on stderr (rewrites on TTY).

    Args:
        cur: Completed units.
        total: Total units (0 yields 0%).
        label: Optional job name.
        extra: Optional trailing note (size, path).
    """
    width = 20
    pct = 0
    filled = 0
    if total > 0:
        pct = int(cur * 100 / total)
        filled = int(cur * width / total)
    body = f"{bar_fill(filled, width)} {pct}%  {cur}/{total}"
    if label:
        body = f"{body}  {label}"
    if extra:
        body = f"{body}  {extra}"
    emit(body, rewrite=True)


def heartbeat(label: str, start: float) -> None:
    """Newline heartbeat (safe when the child also writes stderr).

    Args:
        label: Job name shown after the ellipsis.
        start: ``time.monotonic()`` start timestamp.
    """
    elapsed = format_elapsed(time.monotonic() - start)
    emit(f"… {label}  elapsed {elapsed}  (still running)", rewrite=False)
