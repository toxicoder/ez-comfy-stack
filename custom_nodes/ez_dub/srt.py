"""SRT captions from dub turns."""

from __future__ import annotations

from typing import Any


def format_ts(seconds: float) -> str:
    """SRT timestamp ``HH:MM:SS,mmm``."""
    total_ms = max(0, int(round(float(seconds) * 1000)))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def turns_to_srt(turns: list[dict[str, Any]], *, field: str = "text") -> str:
    """Build an SRT body.

    Arguments:
        turns: Normalized turns with t0/t1.
        field: ``text`` (source) or ``text_target``.
    Returns:
        SRT string (empty when no spoken lines).
    """
    blocks: list[str] = []
    index = 1
    for turn in turns:
        line = str(turn.get(field) or "").strip()
        if not line:
            continue
        t0 = float(turn.get("t0") or 0.0)
        t1 = float(turn.get("t1") or t0)
        if t1 <= t0:
            t1 = t0 + 0.2
        blocks.append(f"{index}\n{format_ts(t0)} --> {format_ts(t1)}\n{line}\n")
        index += 1
    return "\n".join(blocks).rstrip() + ("\n" if blocks else "")
