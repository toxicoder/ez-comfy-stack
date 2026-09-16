"""Turn JSON schema for analyze / translate / render."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any, NotRequired, TypedDict, cast

# Analyze / render stage widget values.
STAGES = ("all", "analyze", "render")
DEFAULT_STAGE = "all"


class Turn(TypedDict):
    """One diarized speech window.

    Attributes:
        id: 1-based turn id.
        speaker: Cluster label such as ``spk00``.
        t0: Start seconds.
        t1: End seconds.
        text: Source-language ASR.
        text_target: Translated line (may be empty).
        overlap: True when a louder overlapping turn won.
        rms: Window energy.
    """

    id: int
    speaker: str
    t0: float
    t1: float
    text: str
    text_target: str
    overlap: bool
    rms: float


class ScriptPayload(TypedDict):
    """Widget JSON for analyze / translate / render.

    Attributes:
        target_language: ISO target.
        source_language: ISO source or ``auto``.
        stage: ``all``, ``analyze``, or ``render``.
        status: Operator-facing reason.
        turns: Normalized turn list.
        slug: Optional job id from ingest.
    """

    target_language: str
    source_language: str
    stage: str
    status: str
    turns: list[Turn]
    slug: NotRequired[str]


def empty_payload(
    *,
    target_language: str = "es",
    source_language: str = "auto",
    stage: str = DEFAULT_STAGE,
    status: str = "",
) -> ScriptPayload:
    """Envelope stored in the App translation widget.

    Args:
        target_language: ISO target.
        source_language: ISO source or ``auto``.
        stage: Widget stage; unknown values become ``all``.
        status: Operator-facing reason.

    Returns:
        Payload with an empty turn list.
    """
    name = stage if stage in STAGES else DEFAULT_STAGE
    return {
        "target_language": target_language or "es",
        "source_language": source_language or "auto",
        "stage": name,
        "status": status or "",
        "turns": [],
    }


def normalize_turn(raw: object, index: int) -> Turn:
    """Coerce one turn mapping.

    Args:
        raw: Mapping or ignored junk.
        index: 1-based fallback id.

    Returns:
        Turn dict with id, speaker, t0, t1, text, text_target, overlap, rms.
    """
    if not isinstance(raw, dict):
        return {
            "id": index,
            "speaker": "spk00",
            "t0": 0.0,
            "t1": 0.0,
            "text": "",
            "text_target": "",
            "overlap": False,
            "rms": 0.0,
        }
    t0 = float(raw.get("t0") or 0.0)
    t1 = float(raw.get("t1") or t0)
    if t1 < t0:
        t0, t1 = t1, t0
    speaker = str(raw.get("speaker") or "spk00").strip() or "spk00"
    tid = raw.get("id")
    if tid is None:
        ident = index
    else:
        try:
            ident = int(tid)
        except (TypeError, ValueError):
            ident = index
    return {
        "id": ident,
        "speaker": speaker,
        "t0": t0,
        "t1": t1,
        "text": str(raw.get("text") or ""),
        "text_target": str(raw.get("text_target") or ""),
        "overlap": bool(raw.get("overlap")),
        "rms": float(raw.get("rms") or 0.0),
    }


def parse_payload(raw: object) -> ScriptPayload:
    """Parse widget text or a mapping into a payload.

    Args:
        raw: JSON string, mapping, or empty.

    Returns:
        Normalized payload. Invalid JSON becomes an empty payload with status.
    """
    if isinstance(raw, dict):
        data = raw
    else:
        text = raw if isinstance(raw, str) else str(raw or "")
        stripped = text.strip()
        if not stripped:
            return empty_payload(status="empty script")
        try:
            loaded = json.loads(stripped)
        except json.JSONDecodeError:
            return empty_payload(status="invalid json")
        if isinstance(loaded, list):
            data = {"turns": loaded}
        elif isinstance(loaded, dict):
            data = loaded
        else:
            return empty_payload(status="invalid json")
    raw_turns = data.get("turns")
    turns_raw: list[Any] = raw_turns if isinstance(raw_turns, list) else []
    turns: list[Turn] = [
        normalize_turn(item, i + 1) for i, item in enumerate(turns_raw)
    ]
    stage = str(data.get("stage") or DEFAULT_STAGE).strip().lower()
    if stage not in STAGES:
        stage = DEFAULT_STAGE
    return {
        "target_language": str(data.get("target_language") or "es"),
        "source_language": str(data.get("source_language") or "auto"),
        "stage": stage,
        "status": str(data.get("status") or ""),
        "turns": turns,
    }


def dumps_payload(payload: Mapping[str, Any]) -> str:
    """Pretty-print a payload for the App widget.

    Args:
        payload: Normalized script mapping (JSON keys).

    Returns:
        Indented JSON string.
    """
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _copy_turn(turn: Mapping[str, Any]) -> Turn:
    """Shallow-copy a JSON turn mapping.

    Args:
        turn: Turn-shaped mapping.

    Returns:
        New Turn dict.
    """
    return cast(Turn, dict(turn))


def assign_overlap(turns: Sequence[Mapping[str, Any]]) -> list[Turn]:
    """When two turns overlap, keep the louder one and mark overlap.

    Args:
        turns: Normalized turns (not necessarily sorted).

    Returns:
        New list sorted by t0. Overlapping quieter turns are dropped.
    """
    ordered = sorted(
        (_copy_turn(t) for t in turns), key=lambda t: (t["t0"], t["t1"])
    )
    kept: list[Turn] = []
    for turn in ordered:
        if not kept:
            kept.append(turn)
            continue
        prev = kept[-1]
        if turn["t0"] < prev["t1"]:
            prev["overlap"] = True
            turn["overlap"] = True
            if float(turn.get("rms") or 0.0) > float(prev.get("rms") or 0.0):
                kept[-1] = turn
            continue
        kept.append(turn)
    return kept


# Adjacent-turn merge: gap ceiling and speakable window cap.
MERGE_GAP_S = 0.35
MERGE_MAX_S = 12.0


def _join_turn_text(left: str, right: str) -> str:
    """Join two ASR/target strings with a single space.

    Args:
        left: Earlier text.
        right: Later text.

    Returns:
        Combined line, or whichever side is non-empty.
    """
    a = (left or "").strip()
    b = (right or "").strip()
    if a and b:
        return f"{a} {b}"
    return a or b


def merge_adjacent_turns(
    turns: Sequence[Mapping[str, Any]],
    *,
    gap_s: float = MERGE_GAP_S,
) -> list[Turn]:
    """Merge consecutive same-speaker turns when gap < gap_s.

    Concatenate text with a single space. Union [t0, t1].
    rms = max of the two. overlap stays True if either was.
    Call AFTER assign_overlap, BEFORE translate. A merged window longer
    than ``MERGE_MAX_S`` starts a new turn so ``fit_turn`` stays speakable.

    Args:
        turns: Normalized turns (not necessarily sorted).
        gap_s: Maximum gap in seconds to merge.

    Returns:
        Merged list sorted by ``t0``.
    """
    ordered = sorted(
        (_copy_turn(t) for t in turns), key=lambda t: (t["t0"], t["t1"])
    )
    if not ordered:
        return []
    out: list[Turn] = [_copy_turn(ordered[0])]
    limit = float(gap_s)
    for turn in ordered[1:]:
        prev = out[-1]
        same = str(turn.get("speaker") or "") == str(prev.get("speaker") or "")
        gap = float(turn["t0"]) - float(prev["t1"])
        a = str(prev.get("text") or "").strip()
        b = str(turn.get("text") or "").strip()
        union_s = max(float(prev["t1"]), float(turn["t1"])) - min(
            float(prev["t0"]), float(turn["t0"])
        )
        if not same or gap >= limit or union_s > MERGE_MAX_S:
            out.append(_copy_turn(turn))
            continue
        prev["t0"] = min(float(prev["t0"]), float(turn["t0"]))
        prev["t1"] = max(float(prev["t1"]), float(turn["t1"]))
        prev["text"] = _join_turn_text(a, b)
        prev["text_target"] = _join_turn_text(
            str(prev.get("text_target") or ""),
            str(turn.get("text_target") or ""),
        )
        prev["rms"] = max(
            float(prev.get("rms") or 0.0), float(turn.get("rms") or 0.0)
        )
        prev["overlap"] = bool(prev.get("overlap")) or bool(turn.get("overlap"))
    return out
