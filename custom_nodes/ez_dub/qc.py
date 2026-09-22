"""Job-dir QC sidecar. Not a Comfy node."""

from __future__ import annotations

from typing import Any

from .sanitize import LEAK_PATTERNS, looks_like_target

# Mix QC thresholds (interior gap and quiet peak).
GAP_LIMIT_S = 0.80
QUIET_PEAK = 0.25


def _cross_lang(target_language: str) -> bool:
    """True when the target is not English/auto (clone must translate).

    Args:
        target_language: ISO target widget.

    Returns:
        Whether empty/passthrough targets are a defect.
    """
    lang = (target_language or "").strip().lower()
    if len(lang) > 2:
        lang = lang[:2]
    return lang not in {"", "en", "auto"}


def _spoken(turn: dict[str, Any]) -> bool:
    """True when a JSON turn has source text.

    Args:
        turn: JSON turn mapping.

    Returns:
        Whether ``text`` is non-empty.
    """
    return bool(str(turn.get("text") or "").strip())


def evaluate_qc(
    mix: list[float],
    rate: int,
    turns: list[dict[str, Any]],
    *,
    target_language: str,
    peak: float,
    extra_flags: list[str] | None = None,
    reference: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a JSON-able dict. Never raises.

    Args:
        mix: Mix PCM.
        rate: Sample rate.
        turns: JSON turns.
        target_language: ISO target.
        peak: Unused (call-site compatibility).
        extra_flags: Optional extra check ids.
        reference: Per-speaker reference-window sidecars.

    Returns:
        ``{ok, flags, checks, rate}`` mapping (JSON boundary).
    """
    del peak
    checks: list[dict[str, str]] = []
    try:
        samples = [float(x) for x in (mix or [])]
        mag = max((abs(x) for x in samples), default=0.0)
        if mag < QUIET_PEAK:
            checks.append(
                {"id": "quiet_mix", "level": "warn", "rule": "max abs < 0.25"}
            )
        from .speech import is_speech_like

        if not is_speech_like(samples, int(rate) or 0):
            checks.append(
                {
                    "id": "mix_not_speech",
                    "level": "fail",
                    "rule": "mix is not speech-like (drone, hush, or tone)",
                }
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
        fail_extra = {"mix_not_speech"}
        for ident in extra_flags or []:
            name = str(ident or "").strip()
            if name:
                level = "fail" if name in fail_extra else "warn"
                checks.append({"id": name, "level": level, "rule": name})
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
        "reference": dict(reference or {}),
    }
