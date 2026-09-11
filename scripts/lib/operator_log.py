"""Operator progress helpers for host Python (stderr only).

Matches scripts/lib/progress.sh: [ez-comfy] prefix, TTY rewrite, NO_COLOR.
Stdout stays JSON / JSONL.
"""

from __future__ import annotations

import os
import sys
import time
from typing import TextIO

PREFIX = "[ez-comfy]"
_REWRITE = False


def progress_enabled() -> bool:
    """True unless EZ_COMFY_PROGRESS=0."""
    return os.environ.get("EZ_COMFY_PROGRESS", "1") != "0"


def use_color(*, stream: TextIO | None = None) -> bool:
    """True when the stream is a TTY and NO_COLOR is unset."""
    target = stream if stream is not None else sys.stderr
    if os.environ.get("NO_COLOR"):
        return False
    return bool(target.isatty())


def progress_interval_s() -> float:
    """Heartbeat seconds from EZ_COMFY_PROGRESS_INTERVAL (0 disables)."""
    raw = os.environ.get("EZ_COMFY_PROGRESS_INTERVAL", "2")
    try:
        return float(raw)
    except ValueError:
        return 2.0


def format_elapsed(secs: float) -> str:
    """Format seconds as m:ss or h:mm:ss."""
    total = int(secs)
    if total < 0:
        total = 0
    hours, rem = divmod(total, 3600)
    minutes, seconds = divmod(rem, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def bar_fill(filled: int, width: int = 20) -> str:
    """Unicode bar: filled cells then empty cells."""
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
    """Informational line (never rewrites)."""
    emit(msg, rewrite=False)


def warn(msg: str) -> None:
    """Warning line."""
    emit(f"[WARN] {msg}", rewrite=False)


def error(msg: str) -> None:
    """Error line (does not exit)."""
    emit(f"[ERROR] {msg}", rewrite=False)


def log_ok(msg: str) -> None:
    """Success line."""
    emit(f"✓ {msg}", rewrite=False)


def log_step(n: int, total: int, msg: str) -> None:
    """Numbered phase banner."""
    emit(f"══ {n}/{total} ══ {msg}", rewrite=False)


def log_debug(msg: str) -> None:
    """Debug line when LAB_DEBUG=1 or EZ_COMFY_LOG_LEVEL=debug."""
    if os.environ.get("LAB_DEBUG") == "1" or os.environ.get(
        "EZ_COMFY_LOG_LEVEL", "info"
    ) == "debug":
        emit(f"[debug] {msg}", rewrite=False)


def progress_bar(cur: int, total: int, label: str = "", extra: str = "") -> None:
    """Percent bar on stderr (rewrites on TTY)."""
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
    """Newline heartbeat (safe when the child also writes stderr)."""
    elapsed = format_elapsed(time.monotonic() - start)
    emit(f"… {label}  elapsed {elapsed}  (still running)", rewrite=False)
