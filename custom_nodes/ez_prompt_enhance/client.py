"""On-box prompt rewrite for ez-comfy enhance nodes.

Hermetic: stdlib only at import. llama-cpp-python is optional; missing GGUF
or import fails soft and the original prompt is passed through.
"""

from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
STYLES_PATH = Path(__file__).resolve().parent / "styles.json"
DEFAULT_GGUF = "/models/comfy/llm/Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
DEFAULT_TIMEOUT_S = 60
DEFAULT_N_THREADS = 4
DEFAULT_N_CTX = 4096
DEFAULT_MAX_TOKENS = 800
STYLE_NONE = "none"
LOCK_VIEW = "view"
LOCK_STATE = "state"
LOCK_IDS = (LOCK_VIEW, LOCK_STATE)
LOCK_VIEW_LINE = (
    "Keep this exact place and inventory. New photograph from a different camera "
    "and framing."
)
LOCK_STATE_LINE = (
    "Keep this exact place, inventory, and camera framing. The shot names the only "
    "change."
)
FLAVOR_KLEIN = "klein"
FLAVOR_KLEIN_EDIT = "klein_edit"
FLAVOR_WAN = "wan"
FLAVOR_LTX = "ltx"

REASON_ENHANCE_OFF = "enhance off"
REASON_GGUF_MISSING = "GGUF missing"
REASON_LLAMA_UNAVAILABLE = "llama.cpp unavailable"
REASON_EMPTY = "timeout or empty model output"
REASON_STYLE_IGNORED_I2V = "style ignored in i2v (start image owns look)"

_LLM: Any = None
_LLM_PATH = ""
_STYLES: dict[str, dict[str, Any]] | None = None

_STYLE_LOOK_FIELDS = ("medium", "light", "color", "texture", "camera")
_WEAVE_BY_FLAVOR = {
    FLAVOR_KLEIN: (
        "Front-load the subject, then state this medium in the first two sentences. "
        "Lighting next. Photographic styles may keep lens and depth of field; "
        "graphic styles replace lens-and-sensor language with surface and tool marks. "
        "Stay under 150 words including style."
    ),
    FLAVOR_KLEIN_EDIT: (
        "Restyle medium, light, and grade only. Keep identity, inventory, "
        "architecture, and counts locked."
    ),
    FLAVOR_WAN: (
        "Put light and lens in Aesthetic control and the medium phrases in "
        "Stylization at the end of the paragraph. Compact, not a second scene."
    ),
    FLAVOR_LTX: (
        "Weave lighting, color palette, and surface texture into the flowing "
        "present-tense paragraph. One coherent light logic. No style trailer."
    ),
}


def _log(message: str) -> None:
    print(f"[ez_prompt_enhance] {message}", file=sys.stderr)


@dataclass(frozen=True)
class EnhanceResult:
    """CLIP text plus an optional passthrough reason for the node preview."""

    text: str
    reason: str | None = None

    @property
    def preview(self) -> str:
        if self.reason:
            return f"[passthrough: {self.reason}]\n{self.text}"
        return self.text


def join_prompt(
    identity: str,
    shot: str,
    inventory: str = "",
    lock: str = LOCK_VIEW,
) -> str:
    """Join a world bible, locked inventory, persist lock, and shot line.

    Arguments:
      identity: camera-free place/subject bible
      shot: camera, light, or action line for this still
      inventory: object list that must repeat across views
      lock: view (new camera) or state (same camera)
    Returns:
      One CLIP string, or empty when every field is blank.
    """
    bible = identity.strip() if isinstance(identity, str) else str(identity or "").strip()
    card = shot.strip() if isinstance(shot, str) else str(shot or "").strip()
    inv = inventory.strip() if isinstance(inventory, str) else str(inventory or "").strip()
    mode = lock.strip().lower() if isinstance(lock, str) else LOCK_VIEW
    if mode not in LOCK_IDS:
        mode = LOCK_VIEW
    if not bible and not card and not inv:
        return ""
    parts: list[str] = []
    if bible:
        parts.append(bible)
    if inv:
        parts.append(f"Locked inventory (do not change): {inv}.")
    parts.append(LOCK_STATE_LINE if mode == LOCK_STATE else LOCK_VIEW_LINE)
    if card:
        parts.append(card)
    return " ".join(parts)


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


def load_styles() -> dict[str, dict[str, Any]]:
    """Load the style catalog (id -> structured look fields)."""
    global _STYLES
    if _STYLES is None:
        raw = json.loads(STYLES_PATH.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("styles.json must be an object")
        styles: dict[str, dict[str, Any]] = {}
        for key, value in raw.items():
            if not isinstance(value, dict):
                raise ValueError(f"style {key} must be an object")
            styles[str(key)] = dict(value)
        _STYLES = styles
    return _STYLES


def style_ids() -> list[str]:
    """Combo choices: none first, then catalog ids in file order."""
    return [STYLE_NONE, *load_styles().keys()]


def _style_entry(style_id: str) -> dict[str, Any]:
    if style_id == STYLE_NONE:
        return {}
    return load_styles().get(style_id) or {}


def _string_list(entry: dict[str, Any], field: str) -> list[str]:
    raw = entry.get(field) or []
    if isinstance(raw, str):
        return [raw.strip()] if raw.strip() else []
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        text = str(item).strip()
        if text:
            out.append(text)
    return out


def style_must_include(style_id: str) -> list[str]:
    return _string_list(_style_entry(style_id), "must_include")


def style_conflicts(style_id: str) -> list[str]:
    return _string_list(_style_entry(style_id), "conflicts")


def style_llm_block(style_id: str) -> str:
    """Dense look paragraph (medium through camera) for one catalog id."""
    entry = _style_entry(style_id)
    parts = []
    for key in _STYLE_LOOK_FIELDS:
        text = str(entry.get(key) or "").strip()
        if text:
            parts.append(text)
    return " ".join(parts)


def style_suffix(style_id: str) -> str:
    if style_id == STYLE_NONE:
        return ""
    entry = _style_entry(style_id)
    return str(entry.get("suffix") or "").strip()


def flavor_for_system(name: str) -> str:
    """Map a system-prompt stem to a style-instruction flavor."""
    if name == "klein_edit":
        return FLAVOR_KLEIN_EDIT
    if name.startswith("wan"):
        return FLAVOR_WAN
    if name.startswith("ltx"):
        return FLAVOR_LTX
    return FLAVOR_KLEIN


def format_style_instruction(style_id: str, flavor: str) -> str:
    """Compose the user-message style block for the local rewriter.

    Arguments:
      style_id: catalog id or none
      flavor: klein, klein_edit, wan, or ltx
    Returns:
      Empty string when style is none or unknown; otherwise a mandatory
      instruction the 4B model should weave into the rewrite.
    """
    block = style_llm_block(style_id)
    if not block:
        return ""
    entry = _style_entry(style_id)
    conflicts = style_conflicts(style_id)
    must = style_must_include(style_id)
    weave = _WEAVE_BY_FLAVOR.get(flavor, _WEAVE_BY_FLAVOR[FLAVOR_KLEIN])
    wan_term = str(entry.get("wan_stylization") or "").strip()
    lines = [
        "Visual style (mandatory; dropdown wins):",
        block,
        (
            "The selected visual style is mandatory and wins over any medium, lighting, "
            "camera-sensor, grade, film-stock, or art-style language already in the source. "
            "Rewrite those clauses so they match this style. Do not stack two styles. "
            "Do not only append a style tag. Weave medium, light, color, and texture into "
            "the rewrite. Keep subject, action, place, inventory, duration, audio notes, "
            "and the requested camera move unless this style requires a different projection. "
            "Do not name the style id. Do not emit brand names."
        ),
        f"Weave: {weave}",
    ]
    if conflicts:
        lines.append("Replace clauses that describe: " + ", ".join(conflicts) + ".")
    if must:
        lines.append("Phrases that must appear in the output: " + "; ".join(must) + ".")
    if flavor == FLAVOR_WAN and wan_term:
        lines.append(f"Wan stylization slot: {wan_term}.")
    return "\n".join(lines)


def ensure_style_details(text: str, style_id: str) -> str:
    """Append the style suffix when the rewrite omitted every must_include phrase.

    Arguments:
      text: CLIP prompt from the rewriter
      style_id: catalog id or none
    Returns:
      text unchanged when any must_include phrase is present; otherwise
      text plus suffix.
    """
    if style_id == STYLE_NONE:
        return text
    must = style_must_include(style_id)
    if not must:
        return text
    lowered = text.lower()
    if any(phrase.lower() in lowered for phrase in must):
        return text
    suffix = style_suffix(style_id)
    if not suffix:
        return text
    base = text.rstrip()
    if not base:
        return suffix
    return f"{base} {suffix}"


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
    raw = os.environ.get("EZ_LLM_TIMEOUT_S", str(DEFAULT_TIMEOUT_S)).strip()
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_TIMEOUT_S
    if value < 1:
        return DEFAULT_TIMEOUT_S
    return value


def _n_threads() -> int:
    raw = os.environ.get("EZ_LLM_N_THREADS", str(DEFAULT_N_THREADS)).strip()
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_N_THREADS
    if value < 1:
        return DEFAULT_N_THREADS
    return value


def _n_ctx() -> int:
    raw = os.environ.get("EZ_LLM_N_CTX", str(DEFAULT_N_CTX)).strip()
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_N_CTX
    if value < 512:
        return DEFAULT_N_CTX
    return value


def _n_gpu_layers() -> int:
    raw = os.environ.get("EZ_LLM_N_GPU_LAYERS", "0").strip()
    try:
        value = int(raw)
    except ValueError:
        return 0
    if value <= 0:
        return 0
    allow = os.environ.get("EZ_LLM_ALLOW_GPU", "").strip().lower()
    if allow not in {"1", "true", "yes", "on"}:
        _log("refusing GPU offload (set EZ_LLM_ALLOW_GPU=1 to override); n_gpu_layers=0")
        return 0
    return value


def _gguf_path() -> str:
    return os.environ.get("EZ_LLM_GGUF", DEFAULT_GGUF).strip() or DEFAULT_GGUF


def _unload_after() -> bool:
    return os.environ.get("EZ_LLM_UNLOAD", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _close_llm() -> None:
    global _LLM, _LLM_PATH
    handle = _LLM
    _LLM = None
    _LLM_PATH = ""
    if handle is None:
        return
    closer = getattr(handle, "close", None)
    if callable(closer):
        try:
            closer()
        except Exception as exc:  # noqa: BLE001 — fail-soft unload
            _log(f"llama close failed: {exc}")


def _get_llama() -> tuple[Any | None, str | None]:
    """Load llama.cpp once. Returns (handle, fail_reason)."""
    global _LLM, _LLM_PATH
    path = _gguf_path()
    if not path or not os.path.isfile(path):
        _log(f"GGUF missing at {path or '(empty EZ_LLM_GGUF)'} — passing prompt through")
        return None, REASON_GGUF_MISSING
    if _LLM is not None and _LLM_PATH == path:
        return _LLM, None
    _close_llm()
    try:
        from llama_cpp import Llama
    except ImportError:
        _log("llama-cpp-python not installed — passing prompt through")
        return None, REASON_LLAMA_UNAVAILABLE
    try:
        _LLM = Llama(
            model_path=path,
            n_ctx=_n_ctx(),
            n_threads=_n_threads(),
            n_gpu_layers=_n_gpu_layers(),
            chat_format="chatml",
            verbose=False,
        )
    except Exception as exc:  # noqa: BLE001 — fail-soft
        _log(f"failed to load GGUF {path}: {exc}")
        _LLM = None
        _LLM_PATH = ""
        return None, REASON_LLAMA_UNAVAILABLE
    _LLM_PATH = path
    _log(f"loaded local LLM {path} (cpu, n_threads={_n_threads()})")
    return _LLM, None


def _generate(llm: Any, system: str, user: str) -> str:
    body = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0,
        max_tokens=DEFAULT_MAX_TOKENS,
    )
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return ""
    if not isinstance(content, str):
        return ""
    return strip_model_wrapping(content)


def complete(system: str, user: str) -> tuple[str, str | None]:
    """Run one local chat completion. Empty text plus a reason on any failure."""
    llm, reason = _get_llama()
    if llm is None:
        return "", reason or REASON_LLAMA_UNAVAILABLE
    timeout = _timeout_s()
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_generate, llm, system, user)
            text = future.result(timeout=timeout)
    except FuturesTimeout:
        _log(f"local LLM timed out after {timeout}s")
        return "", REASON_EMPTY
    except Exception as exc:  # noqa: BLE001 — fail-soft
        _log(f"local LLM failed: {exc}")
        return "", REASON_EMPTY
    finally:
        if _unload_after():
            _close_llm()
    if not (text or "").strip():
        _log("local LLM returned no message content")
        return "", REASON_EMPTY
    return text, None


def enhance_prompt(
    system: str,
    user: str,
    *,
    enhance: bool,
    fallback: str,
) -> EnhanceResult:
    """Rewrite fallback via local LLM when enhance is true."""
    original = fallback if isinstance(fallback, str) else str(fallback)
    if not enhance:
        return EnhanceResult(original, REASON_ENHANCE_OFF)
    if not original.strip():
        return EnhanceResult(original, None)
    rewritten, reason = complete(system, user)
    if not rewritten.strip():
        return EnhanceResult(original, reason or REASON_EMPTY)
    return EnhanceResult(rewritten, None)
