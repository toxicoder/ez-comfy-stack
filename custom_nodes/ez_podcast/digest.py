"""Map-reduce a study digest and a duration-sized Speaker A/B script.

Uses the on-box GGUF via ez_prompt_enhance.client. Fail-soft without a
model: concatenated sources plus a naive Speaker A wrap. Unloads the
writer after the last script section so TTS can run in the same Queue.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from .ingest import SourceRecord, format_sources_block, format_status

# Writer prompts, format/duration catalogs, and spoken-word budget (~150 wpm).
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
WORDS_PER_MINUTE = 150
FORMAT_QUICK = "Quick recap"
FORMAT_DEEP = "Deep dive"
FORMAT_EXPLAINER = "Explainer"
FORMAT_QUIZ = "Quiz drill"
FORMAT_LECTURE = "Solo lecture"
FORMAT_DEBATE = "Debate"
FORMATS = (
    FORMAT_QUICK,
    FORMAT_DEEP,
    FORMAT_EXPLAINER,
    FORMAT_QUIZ,
    FORMAT_LECTURE,
    FORMAT_DEBATE,
)
DEFAULT_FORMAT = FORMAT_EXPLAINER
DURATION_COMMUTE = "3 min commute"
DURATION_BRIEFING = "8 min briefing"
DURATION_LESSON = "15 min lesson"
DURATION_SEMINAR = "25 min seminar"
DURATIONS = (
    DURATION_COMMUTE,
    DURATION_BRIEFING,
    DURATION_LESSON,
    DURATION_SEMINAR,
)
DEFAULT_DURATION = DURATION_BRIEFING
DURATION_MINUTES = {
    DURATION_COMMUTE: 3,
    DURATION_BRIEFING: 8,
    DURATION_LESSON: 15,
    DURATION_SEMINAR: 25,
}
DURATION_SECTIONS = {
    DURATION_COMMUTE: 1,
    DURATION_BRIEFING: 3,
    DURATION_LESSON: 5,
    DURATION_SEMINAR: 8,
}
FORMAT_HINTS = {
    FORMAT_QUICK: (
        "Two-host quick recap. Alternate Speaker A and Speaker B. Tight. "
        "What to remember, then stop."
    ),
    FORMAT_DEEP: (
        "Two-host deep dive. Alternate Speaker A and Speaker B. Examples, "
        "caveats, and how the pieces connect."
    ),
    FORMAT_EXPLAINER: (
        "Explainer. Speaker A is the teacher. Speaker B is a curious student "
        "who asks the next honest question. Alternate turns."
    ),
    FORMAT_QUIZ: (
        "Quiz drill. Speaker A asks a short question from the digest. "
        "Speaker B answers. Speaker A confirms or corrects. Alternate."
    ),
    FORMAT_LECTURE: (
        "Solo lecture. Speaker A only. No Speaker B lines. Teach in order."
    ),
    FORMAT_DEBATE: (
        "Debate. Speaker A and Speaker B argue real tensions in the sources, "
        "then synthesize. Alternate turns. Do not invent a fight."
    ),
}


def _log(message: str) -> None:
    """Write a pack status line to stderr.

    Args:
        message: Text after the ``[ez_podcast]`` prefix.
    """
    print(f"[ez_podcast] {message}", file=sys.stderr)


def _ensure_lab_custom_nodes_path() -> None:
    """Make sibling ez_* packs importable under ComfyUI 0.34+ load_custom_node."""
    root = str(Path(__file__).resolve().parent.parent)
    if root not in sys.path:
        sys.path.insert(0, root)


def _as_bool(value: object) -> bool:
    """Coerce a Comfy widget value to bool.

    Args:
        value: BOOLEAN widget or loose truthy token.

    Returns:
        Parsed boolean.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def resolve_format(value: object) -> str:
    """Map a combo value to a known format label.

    Args:
        value: Format widget.

    Returns:
        One of ``FORMATS``, default explainer.
    """
    raw = value if isinstance(value, str) else str(value or "")
    text = " ".join(raw.strip().split())
    if text in FORMATS:
        return text
    lowered = text.lower().replace("_", " ").replace("-", " ")
    aliases = {
        "quick recap": FORMAT_QUICK,
        "quick_recap": FORMAT_QUICK,
        "deep dive": FORMAT_DEEP,
        "deep_dive": FORMAT_DEEP,
        "explainer": FORMAT_EXPLAINER,
        "quiz": FORMAT_QUIZ,
        "quiz drill": FORMAT_QUIZ,
        "lecture": FORMAT_LECTURE,
        "solo lecture": FORMAT_LECTURE,
        "debate": FORMAT_DEBATE,
    }
    return aliases.get(lowered, DEFAULT_FORMAT)


def resolve_duration(value: object) -> str:
    """Map a combo value to a known duration label.

    Args:
        value: Duration widget.

    Returns:
        One of ``DURATIONS``, default briefing.
    """
    raw = value if isinstance(value, str) else str(value or "")
    text = " ".join(raw.strip().split())
    if text in DURATIONS:
        return text
    lowered = text.lower().replace("_", " ")
    aliases = {
        "commute": DURATION_COMMUTE,
        "3 min commute": DURATION_COMMUTE,
        "briefing": DURATION_BRIEFING,
        "8 min briefing": DURATION_BRIEFING,
        "lesson": DURATION_LESSON,
        "15 min lesson": DURATION_LESSON,
        "seminar": DURATION_SEMINAR,
        "25 min seminar": DURATION_SEMINAR,
    }
    return aliases.get(lowered, DEFAULT_DURATION)


def word_budget(duration: str) -> int:
    """Spoken word target for ``duration``.

    Args:
        duration: Resolved duration label.

    Returns:
        Approximate word count at ``WORDS_PER_MINUTE``.
    """
    minutes = DURATION_MINUTES.get(duration, DURATION_MINUTES[DEFAULT_DURATION])
    return int(minutes) * WORDS_PER_MINUTE


def section_count(duration: str) -> int:
    """How many GGUF script passes to run.

    Args:
        duration: Resolved duration label.

    Returns:
        Section count (at least 1).
    """
    count = DURATION_SECTIONS.get(duration, DURATION_SECTIONS[DEFAULT_DURATION])
    return max(1, int(count))


def load_prompt(name: str) -> str:
    """Load a writer system prompt from this pack.

    Args:
        name: Stem without ``.txt``.

    Returns:
        File contents stripped of trailing whitespace.
    """
    path = PROMPTS_DIR / f"{name}.txt"
    return path.read_text(encoding="utf-8").strip()


def _complete(system: str, user: str) -> tuple[str, str]:
    """One GGUF completion. Empty text when llama.cpp is missing.

    Args:
        system: System prompt.
        user: User message.

    Returns:
        ``(text, reason)``.
    """
    try:
        _ensure_lab_custom_nodes_path()
        from ez_prompt_enhance.client import complete as llama_complete
    except Exception as exc:  # noqa: BLE001 - fail-soft
        _log(f"prompt enhance client unavailable: {exc}")
        return "", "llama.cpp unavailable"
    text, reason = llama_complete(system, user, max_tokens=800, temperature=0.2)
    return (text or "").strip(), (reason or "")


def _close_writer() -> None:
    """Unload the GGUF so Kokoro can run in the same Queue."""
    try:
        _ensure_lab_custom_nodes_path()
        from ez_prompt_enhance.client import _close_llm
    except Exception as exc:  # noqa: BLE001 - unload is best-effort
        _log(f"writer unload import failed: {exc}")
        return
    try:
        _close_llm()
    except Exception as exc:  # noqa: BLE001 - unload is best-effort
        _log(f"writer unload failed: {exc}")


def fallback_digest(records: list[SourceRecord]) -> str:
    """Concatenate usable sources when the GGUF is missing.

    Args:
        records: Ingest records.

    Returns:
        Plain digest text.
    """
    block = format_sources_block(records)
    if block:
        return block
    return "No usable sources. Paste notes or HTTPS links and Queue again."


def naive_script(digest: str, *, fmt: str, duration: str) -> str:
    """Wrap digest sentences into Speaker lines without an LLM.

    Args:
        digest: Study digest.
        fmt: Resolved format label.
        duration: Resolved duration label.

    Returns:
        Labeled script clipped to the word budget.
    """
    body = (digest or "").strip()
    if not body:
        return "Speaker A: Paste sources, then Queue with Rewrite on."
    budget = word_budget(duration)
    lecture = fmt == FORMAT_LECTURE
    sentences: list[str] = []
    for chunk in body.replace("?", ".").replace("!", ".").split("."):
        piece = " ".join(chunk.split()).strip()
        if piece:
            sentences.append(piece)
    if not sentences:
        sentences = [body]
    lines: list[str] = []
    words = 0
    speaker = "Speaker A"
    for sentence in sentences:
        token_count = len(sentence.split())
        if words and words + token_count > budget:
            break
        lines.append(f"{speaker}: {sentence}.")
        words += token_count
        if not lecture:
            speaker = "Speaker B" if speaker == "Speaker A" else "Speaker A"
        if words >= budget:
            break
    return "\n".join(lines) if lines else f"Speaker A: {body}"


def write_digest(records: list[SourceRecord], *, enhance: bool) -> tuple[str, str]:
    """Build an ordered, deduped digest.

    Args:
        records: Ingest records.
        enhance: When false, concatenate sources.

    Returns:
        ``(digest, status)``.
    """
    fallback = fallback_digest(records)
    if not enhance:
        return fallback, "enhance off"
    block = format_sources_block(records)
    if not block:
        return fallback, "no sources"
    system = load_prompt("learn_digest")
    user = (
        "Write one pedagogically ordered, deduped study digest of these "
        "sources. Drop repeated claims. Keep conflicts as named conflicts.\n\n"
        f"{block}"
    )
    text, reason = _complete(system, user)
    if not text:
        return fallback, reason or "passthrough"
    return text, reason or "ok"


def _script_system(fmt: str, duration: str) -> str:
    """System prompt for one script section.

    Args:
        fmt: Format label.
        duration: Duration label.

    Returns:
        Combined system prompt.
    """
    base = load_prompt("learn_script")
    hint = FORMAT_HINTS.get(fmt, FORMAT_HINTS[DEFAULT_FORMAT])
    budget = word_budget(duration)
    sections = section_count(duration)
    return (
        f"{base}\n\nFormat: {fmt}. {hint}\n"
        f"Duration: {duration}. Whole-episode budget about {budget} words "
        f"across {sections} section(s). This call writes one section only."
    )


def write_script(
    digest: str,
    *,
    fmt: str,
    duration: str,
    enhance: bool,
) -> tuple[str, str]:
    """Write a Speaker-labeled script sized to ``duration``.

    Args:
        digest: Study digest.
        fmt: Format label.
        duration: Duration label.
        enhance: When false, naive-wrap the digest.

    Returns:
        ``(script, status)``.
    """
    body = (digest or "").strip()
    if not enhance:
        return naive_script(body, fmt=fmt, duration=duration), "enhance off"
    sections = section_count(duration)
    budget = word_budget(duration)
    per = max(80, budget // sections)
    parts: list[str] = []
    reasons: list[str] = []
    previous = ""
    system = _script_system(fmt, duration)
    try:
        if not body:
            return naive_script("", fmt=fmt, duration=duration), "no digest"
        for index in range(sections):
            role = "opening" if index == 0 else (
                "closing recap" if index == sections - 1 else "middle"
            )
            user = (
                f"Section {index + 1} of {sections} ({role}). "
                f"About {per} words. Continue the same hosts.\n\n"
                f"Digest:\n{body}"
            )
            if previous:
                user += f"\n\nPrevious section (do not repeat):\n{previous}"
            text, reason = _complete(system, user)
            if reason:
                reasons.append(reason)
            if not text:
                continue
            parts.append(text)
            previous = text
    finally:
        _close_writer()
    if not parts:
        return naive_script(body, fmt=fmt, duration=duration), (
            reasons[-1] if reasons else "passthrough"
        )
    script = "\n".join(parts).strip()
    status = "ok"
    if reasons and any(item and item != "ok" for item in reasons):
        status = reasons[-1]
    return script, status


def run_learn(
    records: list[SourceRecord],
    *,
    fmt: object,
    duration: object,
    enhance: object,
) -> dict[str, Any]:
    """Digest + script payload for ``EZPodcastLearn``.

    Args:
        records: Ingest records.
        fmt: Format widget.
        duration: Duration widget.
        enhance: Rewrite toggle.

    Returns:
        Mapping with digest, script, and status strings.
    """
    kind = resolve_format(fmt)
    length = resolve_duration(duration)
    on = _as_bool(enhance)
    digest, digest_status = write_digest(records, enhance=on)
    script, script_status = write_script(
        digest, fmt=kind, duration=length, enhance=on
    )
    status_parts = [format_status(records), digest_status, script_status]
    status = " | ".join(part for part in status_parts if part)
    return {
        "digest": digest,
        "script": script,
        "status": status,
        "format": kind,
        "duration": length,
    }
