"""Off-box prompt rewrite client for ez-comfy enhance nodes.

Hermetic: stdlib only. No torch, no comfy, no pip extras. Calls the xAI
OpenAI-compatible Chat Completions API when a key is present; otherwise
returns the original prompt (fail-soft).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_BASE_URL = "https://api.x.ai/v1"
DEFAULT_MODEL = "grok-4.6"
DEFAULT_TIMEOUT_S = 20
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def _log(message: str) -> None:
    print(f"[ez_prompt_enhance] {message}", file=sys.stderr)


def load_system_prompt(name: str) -> str:
    """Load a named system prompt from the prompts/ directory.

    Arguments:
      name: stem without .txt (e.g. klein_t2i)
    Returns:
      File contents stripped of trailing whitespace.
    Raises:
      FileNotFoundError if the prompt file is missing.
    """
    path = PROMPTS_DIR / f"{name}.txt"
    return path.read_text(encoding="utf-8").strip()


def strip_model_wrapping(text: str) -> str:
    """Remove markdown fences or wrapping quotes from a model reply."""
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {"'", '"'}:
        cleaned = cleaned[1:-1].strip()
    return cleaned


def _timeout_s() -> int:
    raw = os.environ.get("XAI_TIMEOUT_S", str(DEFAULT_TIMEOUT_S)).strip()
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_TIMEOUT_S
    if value < 1:
        return DEFAULT_TIMEOUT_S
    return value


def _api_key() -> str:
    return os.environ.get("XAI_API_KEY", "").strip()


def _base_url() -> str:
    return os.environ.get("XAI_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")


def _model() -> str:
    return os.environ.get("XAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def chat_complete(system: str, user: str) -> str:
    """Call chat completions. Empty string on any failure (caller passthrough)."""
    key = _api_key()
    if not key:
        _log("XAI_API_KEY unset — passing prompt through")
        return ""
    url = f"{_base_url()}/chat/completions"
    payload = {
        "model": _model(),
        "temperature": 0,
        "max_tokens": 800,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=_timeout_s()) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        _log(f"HTTP {exc.code} from prompt rewrite API: {detail}")
        return ""
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        _log(f"prompt rewrite API failed: {exc}")
        return ""
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        _log("prompt rewrite API returned no message content")
        return ""
    if not isinstance(content, str):
        return ""
    return strip_model_wrapping(content)


def enhance_prompt(system: str, prompt: str, *, enhance: bool) -> str:
    """Rewrite prompt when enhance is true; otherwise return it unchanged."""
    original = prompt if isinstance(prompt, str) else str(prompt)
    if not enhance:
        return original
    if not original.strip():
        return original
    rewritten = chat_complete(system, original)
    if not rewritten.strip():
        return original
    return rewritten
