"""Job-dir QC sidecar. Not a Comfy node."""

from __future__ import annotations

from typing import Any

from .sanitize import LEAK_PATTERNS, looks_like_target

GAP_LIMIT_S = 0.80
QUIET_PEAK = 0.25


def _cross_lang(target_language: str) -> bool:
    lang = (target_language or "").strip().lower()
    if len(lang) > 2:
        lang = lang[:2]
    return lang not in {"", "en", "auto"}


def _spoken(turn: dict[str, Any]) -> bool:
    return bool(str(turn.get("text") or "").strip())


def evaluate_qc(
    mix: list[float],
    rate: int,
    turns: list[dict[str, Any]],
    *,
    target_language: str,
    peak: float,
) -> dict[str, Any]:
    """Return a JSON-able dict. Never raises."""
    del peak
    checks: list[dict[str, str]] = []
    try:
        samples = [float(x) for x in (mix or [])]
        mag = max((abs(x) for x in samples), default=0.0)
        if mag < QUIET_PEAK:
            checks.append(
                {"id": "quiet_mix", "level": "warn", "rule": "max abs < 0.25"}
            )
        ordered = []
        for raw in turns or []:
            if not isinstance(raw, dict):
                continue
            ordered.append(raw)
        ordered.sort(key=lambda t: float(t.get("t0") or 0.0))
        for i in range(len(ordered) - 1):
            gap = float(ordered[i + 1].get("t0") or 0.0) - float(
                ordered[i].get("t1") or 0.0
            )
            if gap > GAP_LIMIT_S:
                checks.append(
                    {
                        "id": "gap",
                        "level": "warn",
                        "rule": "interior silence > 0.80 s",
                    }
                )
                break
        cross = _cross_lang(target_language)
        lang = (target_language or "es").strip().lower() or "es"
        for turn in ordered:
            if not _spoken(turn):
                continue
            text = str(turn.get("text") or "")
            target = str(turn.get("text_target") or "")
            if cross and not target.strip():
                checks.append(
                    {
                        "id": "empty_target",
                        "level": "fail",
                        "rule": "empty text_target on cross-lang spoken turn",
                    }
                )
            if target.strip() and not looks_like_target(target, lang):
                checks.append(
                    {
                        "id": "english_left",
                        "level": "warn",
                        "rule": "text_target not target-like",
                    }
                )
            lower = target.lower()
            if any(pat in lower for pat in LEAK_PATTERNS):
                checks.append(
                    {
                        "id": "leak",
                        "level": "warn",
                        "rule": "text_target matches leak pattern",
                    }
                )
            if cross and target.strip() and target.strip() == text.strip():
                checks.append(
                    {
                        "id": "passthrough",
                        "level": "warn",
                        "rule": "text_target equals source on cross-lang turn",
                    }
                )
    except Exception:  # noqa: BLE001 — never raise
        return {"ok": False, "flags": [], "checks": []}
    flags: list[str] = []
    seen: set[str] = set()
    for item in checks:
        ident = str(item.get("id") or "")
        if ident and ident not in seen:
            seen.add(ident)
            flags.append(ident)
    fails = [c for c in checks if c.get("level") == "fail"]
    return {
        "ok": not fails,
        "flags": flags,
        "checks": checks,
        "rate": int(rate or 0),
    }
