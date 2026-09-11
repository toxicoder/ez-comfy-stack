"""Strip GGUF fences and instruction-like leak tails from translations."""

from __future__ import annotations

import re

LEAK_PATTERNS: tuple[str, ...] = (
    "voice model",
    "modelo de voz",
    "help you develop",
    "te ayude a desarrollar",
    "read this sentence",
    "sample of my voice",
    "this is a test of my voice",
    "i-translated",
)
EN_FUNCTION = {"the", "and", "of", "to", "in", "that", "this", "with", "for", "you"}
TARGET_MARKERS: dict[str, set[str]] = {
    "es": {
        "el",
        "la",
        "los",
        "las",
        "un",
        "una",
        "que",
        "de",
        "y",
        "en",
        "es",
        "por",
        "con",
        "me",
        "te",
        "se",
        "está",
        "están",
        "del",
        "al",
    },
    "pt": {"o", "a", "os", "as", "um", "uma", "que", "de", "e", "não", "é", "do", "da"},
    "fr": {"le", "la", "les", "un", "une", "des", "que", "et", "est", "à", "pas", "du"},
    "de": {"der", "die", "das", "und", "ist", "ein", "eine", "nicht", "ich", "den", "dem"},
    "it": {"il", "lo", "la", "gli", "le", "un", "una", "che", "di", "e", "non", "è", "del"},
    "en": set(),
}

_THINK_RE = re.compile(r"<think>.*?</think>", re.IGNORECASE | re.DOTALL)
_PREFIX_RE = re.compile(
    r"^\s*(?:translation|traducci[oó]n)\s*:\s*",
    re.IGNORECASE,
)
_TOKEN_RE = re.compile(r"[A-Za-zÀ-ÿ']+")
_TAIL_CONNECTOR_RE = re.compile(
    r"(?:,|;|:|-|\s+|de una manera que|de forma que|in a way that)+$",
    re.IGNORECASE,
)


def strip_model_fences(text: str) -> str:
    """Remove <think>…</think>, wrapping quotes, 'Translation:' / 'Traducción:' prefixes."""
    out = _THINK_RE.sub("", text or "")
    out = out.strip()
    if len(out) >= 2 and out[0] == out[-1] and out[0] in {'"', "'"}:
        out = out[1:-1].strip()
    if (out.startswith('"') and out.endswith('"')) or (
        out.startswith("'") and out.endswith("'")
    ):
        out = out[1:-1].strip()
    out = _PREFIX_RE.sub("", out).strip()
    if len(out) >= 2 and out[0] == out[-1] and out[0] in {'"', "'"}:
        out = out[1:-1].strip()
    return out


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def strip_leak_tails(text: str) -> str:
    """Drop a final sentence that matches LEAK_PATTERNS. Keep the rest."""
    raw = (text or "").strip()
    if not raw:
        return ""
    lower = raw.lower()
    cut = -1
    for pat in LEAK_PATTERNS:
        idx = lower.find(pat)
        if idx >= 0 and (cut < 0 or idx < cut):
            cut = idx
    if cut >= 0:
        prefix = _TAIL_CONNECTOR_RE.sub("", raw[:cut]).rstrip(" ,;:-")
        if prefix:
            return prefix
        sentences = _split_sentences(raw)
        if len(sentences) > 1:
            return " ".join(sentences[:-1]).strip()
        return ""
    sentences = _split_sentences(raw)
    if len(sentences) > 1:
        last = sentences[-1].lower()
        if any(pat in last for pat in LEAK_PATTERNS):
            return " ".join(sentences[:-1]).strip()
    return raw


def looks_like_target(text: str, language: str) -> bool:
    """Heuristic. False if empty, or leftover English on a non-English job."""
    raw = (text or "").strip()
    if not raw:
        return False
    lang = (language or "").strip().lower()
    if len(lang) > 2:
        lang = lang[:2]
    if lang in {"", "en"}:
        return True
    tokens = [tok.lower() for tok in _TOKEN_RE.findall(raw)]
    en_hits = sum(1 for tok in tokens if tok in EN_FUNCTION)
    markers = TARGET_MARKERS.get(lang, set())
    mark_hits = sum(1 for tok in tokens if tok in markers)
    if any(ord(ch) > 127 for ch in raw):
        mark_hits += 2
    if en_hits >= 3 and mark_hits < 2:
        return False
    return True


def sanitize_target(text: str, *, source_text: str, language: str) -> str:
    """strip fences → strip leak tails → strip()."""
    del source_text, language
    out = strip_model_fences(text)
    out = strip_leak_tails(out)
    return out.strip()
