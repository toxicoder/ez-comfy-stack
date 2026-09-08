"""Turn JSON schema for analyze / translate / render."""

from __future__ import annotations

import json
from typing import Any

STAGES = ("all", "analyze", "render")
DEFAULT_STAGE = "all"


def empty_payload(
    *,
    target_language: str = "es",
    source_language: str = "auto",
    stage: str = DEFAULT_STAGE,
    status: str = "",
) -> dict[str, Any]:
    """Envelope stored in the App translation widget."""
    name = stage if stage in STAGES else DEFAULT_STAGE
    return {
        "target_language": target_language or "es",
        "source_language": source_language or "auto",
        "stage": name,
        "status": status or "",
        "turns": [],
    }


def normalize_turn(raw: object, index: int) -> dict[str, Any]:
    """Coerce one turn mapping.

    Arguments:
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


def parse_payload(raw: object) -> dict[str, Any]:
    """Parse widget text or a mapping into a payload.

    Arguments:
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
    turns = [normalize_turn(item, i + 1) for i, item in enumerate(turns_raw)]
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


def dumps_payload(payload: dict[str, Any]) -> str:
    """Pretty-print a payload for the App widget."""
    return json.dumps(payload, indent=2, ensure_ascii=False)


def assign_overlap(turns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """When two turns overlap, keep the louder one and mark overlap.

    Arguments:
        turns: Normalized turns (not necessarily sorted).
    Returns:
        New list sorted by t0. Overlapping quieter turns are dropped.
    """
    ordered = sorted((dict(t) for t in turns), key=lambda t: (t["t0"], t["t1"]))
    kept: list[dict[str, Any]] = []
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
