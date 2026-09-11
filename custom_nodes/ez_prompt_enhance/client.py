"""On-box prompt rewrite for ez-comfy enhance nodes.

Hermetic: stdlib only at import. llama-cpp-python is optional; missing GGUF
or import fails soft and the original prompt is passed through.

GPU-first: occupancy llm-desk/llm/idle uses the host sidecar when it answers.
CPU 4B is the OOM-safe path next to Wan / LTX / TRELLIS.
"""

from __future__ import annotations

import importlib
import json
import os
import platform
import re
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
STYLES_PATH = Path(__file__).resolve().parent / "styles.json"
VIEWS_PATH = Path(__file__).resolve().parent / "views.json"
GGUF_FILENAME = "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
SNAPSHOT_DIR = "unsloth__Qwen3-4B-Instruct-2507-GGUF_llm"
DEFAULT_GGUF = f"/models/comfy/llm/{GGUF_FILENAME}"
DEFAULT_TIMEOUT_S = 180
DEFAULT_N_THREADS = 8
DEFAULT_N_CTX = 4096
DEFAULT_MAX_TOKENS = 800
STYLE_NONE = "none"
LOCK_VIEW = "view"
LOCK_STATE = "state"
LOCK_IDS = (LOCK_VIEW, LOCK_STATE)
LOCK_VIEW_CLOSER = "This still is only the room and backdrop the shot names."
LOCK_VIEW_LINE = (
    "Same building, rooms, furniture placement, and materials. "
    "New photograph from a different camera in a walkthrough of this place. "
    f"{LOCK_VIEW_CLOSER}"
)
LOCK_STATE_LINE = (
    "Keep this exact place, inventory, and camera framing. The shot names the only "
    "change."
)
FLAVOR_KLEIN = "klein"
FLAVOR_KLEIN_EDIT = "klein_edit"
FLAVOR_KLEIN_IDENTITY = "klein_identity"
FLAVOR_WAN = "wan"
FLAVOR_LTX = "ltx"

REASON_ENHANCE_OFF = "enhance off"
REASON_GGUF_MISSING = "GGUF missing"
REASON_LLAMA_UNAVAILABLE = "llama.cpp unavailable"
REASON_LLM_LOAD_FAILED = "GGUF failed to load"
REASON_EMPTY = "timeout or empty model output"
REASON_SIDECAR_EMPTY = "empty sidecar output"

CPU_FORCE_OCCUPANCY = frozenset({"wan", "ltx", "trellis"})
GPU_SAFE_OCCUPANCY = frozenset(
    {
        "klein",
        "llm",
        "llm-desk",
        "idle",
        "unknown",
        "audio",
        "blender-desk",
        "none",
    }
)
SIDECAR_OK_OCCUPANCY = frozenset(
    {"llm-desk", "llm", "idle", "unknown", "blender-desk"}
)
DEFAULT_SIDECAR_PORT = "30000"
DEFAULT_SIDECAR_NGL = 99

LLAMA_CPP_CPU_VERSION = "0.3.35"
LLAMA_CPP_CPU_PKG = f"llama-cpp-python=={LLAMA_CPP_CPU_VERSION}"
LLAMA_CPP_CPU_INDEX = "https://abetlen.github.io/llama-cpp-python/whl/cpu"
PYPI_SIMPLE_INDEX = "https://pypi.org/simple"
LLAMA_CPP_OPERATOR_PYTHON = (
    "/comfy-state/ComfyUI/.venv/bin/python"
)
HEAL_PIP_TIMEOUT_S = 120

_LLM: Any = None
_LLM_PATH = ""
_HEAL_LOCK = threading.Lock()
_HEAL_TRIED = False
_HEAL_ERROR = ""
_HEAL_PIP_FAILED = False
_LAST_IMPORT_ERROR = ""
_LLAMA_IMPORT_ERRORS = (ImportError, OSError, RuntimeError, FileNotFoundError)
REASON_STYLE_IGNORED_I2V = "style ignored in i2v (start image owns look)"
REASON_STYLE_IGNORED_FLF = "style ignored in flf (start and end frames own look)"
REASON_STYLE_IGNORED_VACE = "style ignored in vace (both clips own look)"
STYLE_IGNORED_MODES = {
    "i2v": REASON_STYLE_IGNORED_I2V,
    "flf": REASON_STYLE_IGNORED_FLF,
    "vace": REASON_STYLE_IGNORED_VACE,
}

_STYLES: dict[str, dict[str, Any]] | None = None
_VIEWS: dict[str, list[dict[str, str]]] | None = None

_STYLE_LOOK_FIELDS = ("medium", "light", "color", "texture", "camera")
_LAB_LOOK_PHRASES = (
    "HD 3D game-engine pre-rendered cutscene still",
    "HD 3D game-engine pre-rendered cutscene",
    "3D game-engine pre-rendered cutscene still",
    "3D game-engine pre-rendered cutscene",
    "game-engine pre-rendered cutscene",
    "game-engine pre-rendered",
    "game-engine",
    "photoreal cinematic still",
    "photoreal still",
    "photoreal shot",
)
STYLE_SYSTEM_ADDENDUM = (
    "The user message contains a Visual style block. That style is the only look. "
    "Rewrite the whole prompt as that medium. Drop any other medium, 3D-render, "
    "photoreal, or lens language that fights it. Output only the CLIP prompt."
)
_THINK_BLOCKS = (
    re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE),
    re.compile(r"<\|think\|>.*?<\|/think\|>", re.DOTALL | re.IGNORECASE),
)
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
    FLAVOR_KLEIN_IDENTITY: (
        "Keep the bible camera-free. Do not add lens, shot scale, or a camera move."
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


def llama_cpp_direct_wheel_url() -> str:
    """GitHub release manylinux wheel for this CPU arch, or empty."""
    machine = platform.machine().lower()
    if machine in {"aarch64", "arm64"}:
        tag = "manylinux2014_aarch64.manylinux_2_17_aarch64"
    elif machine in {"x86_64", "amd64"}:
        tag = "manylinux2014_x86_64.manylinux_2_17_x86_64"
    else:
        return ""
    return (
        "https://github.com/abetlen/llama-cpp-python/releases/download/"
        f"v{LLAMA_CPP_CPU_VERSION}/llama_cpp_python-{LLAMA_CPP_CPU_VERSION}"
        f"-py3-none-{tag}.whl"
    )


def llama_cpp_cpu_pip_index_args() -> list[str]:
    """pip install operands: CPU extra-index as --index-url, pin, binaries only."""
    return [
        "--only-binary=:all:",
        "--index-url",
        LLAMA_CPP_CPU_INDEX,
        "--extra-index-url",
        PYPI_SIMPLE_INDEX,
        LLAMA_CPP_CPU_PKG,
    ]


def llama_cpp_direct_wheel_pip_args() -> list[str]:
    """pip install operands: replace a same-version wheel from GitHub."""
    wheel = llama_cpp_direct_wheel_url()
    if not wheel:
        return []
    return [
        "--force-reinstall",
        "--no-deps",
        "--only-binary=:all:",
        wheel,
    ]


def llama_cpp_operator_pip_command() -> str:
    """Exact docker exec pip line for a blocking Dub / Enhance status."""
    args = llama_cpp_direct_wheel_pip_args() or llama_cpp_cpu_pip_index_args()
    return (
        f"docker exec ez-comfy-studio {LLAMA_CPP_OPERATOR_PYTHON} "
        f"-m pip install {' '.join(args)}"
    )


def llama_cpp_unavailable_status() -> str:
    """Operator-facing next step when Llama cannot import after heal."""
    cmd = llama_cpp_operator_pip_command()
    pip_detail = _HEAL_ERROR.strip()
    import_detail = _LAST_IMPORT_ERROR.strip()
    if _HEAL_PIP_FAILED and pip_detail:
        return f"llama.cpp unavailable — CPU wheel pip failed ({pip_detail}). {cmd}"
    if import_detail:
        return f"llama.cpp unavailable — Llama import failed ({import_detail}). {cmd}"
    if pip_detail:
        return f"llama.cpp unavailable — Llama import failed ({pip_detail}). {cmd}"
    return f"llama.cpp unavailable — Llama did not import. {cmd}"


def reset_llama_runtime_for_tests() -> None:
    """Clear cached LLM handle and CPU-wheel heal state (unit tests only)."""
    global _HEAL_TRIED, _HEAL_ERROR, _HEAL_PIP_FAILED, _LAST_IMPORT_ERROR
    _close_llm()
    _HEAL_TRIED = False
    _HEAL_ERROR = ""
    _HEAL_PIP_FAILED = False
    _LAST_IMPORT_ERROR = ""


def _pip_install(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run ``python -m pip install`` on this interpreter. Tests patch this."""
    try:
        return subprocess.run(
            [sys.executable, "-m", "pip", "install", *args],
            capture_output=True,
            text=True,
            timeout=HEAL_PIP_TIMEOUT_S,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            args=[sys.executable, "-m", "pip", "install", *args],
            returncode=1,
            stdout="",
            stderr=f"pip timed out after {HEAL_PIP_TIMEOUT_S}s",
        )


def _short_pip_error(proc: subprocess.CompletedProcess[str]) -> str:
    text = (proc.stderr or proc.stdout or "").strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return f"pip exit {proc.returncode}"
    return lines[-1][:200]


def _forget_llama_module() -> None:
    for name in list(sys.modules):
        if name == "llama_cpp" or name.startswith("llama_cpp."):
            sys.modules.pop(name, None)
    importlib.invalidate_caches()


def _load_llama_class() -> Any | None:
    """Return llama_cpp.Llama, or None when the CPU wheel is missing."""
    global _LAST_IMPORT_ERROR
    try:
        from llama_cpp import Llama
    except _LLAMA_IMPORT_ERRORS as exc:
        _LAST_IMPORT_ERROR = str(exc).strip() or type(exc).__name__
        _log(f"llama_cpp import failed: {_LAST_IMPORT_ERROR}")
        return None
    _LAST_IMPORT_ERROR = ""
    return Llama


def _heal_llama_cpp_cpu() -> str:
    """Install the CPU wheel once per process. Empty string on success."""
    global _HEAL_TRIED, _HEAL_ERROR, _HEAL_PIP_FAILED
    with _HEAL_LOCK:
        if _HEAL_TRIED:
            return _HEAL_ERROR
        _HEAL_TRIED = True
        _HEAL_PIP_FAILED = False
        _log("llama-cpp-python missing — installing CPU wheel")

        def _import_ok() -> bool:
            _forget_llama_module()
            return _load_llama_class() is not None

        proc = _pip_install(llama_cpp_cpu_pip_index_args())
        if proc.returncode == 0 and _import_ok():
            _HEAL_ERROR = ""
            _log("llama-cpp-python CPU wheel installed")
            return ""
        wheel_args = llama_cpp_direct_wheel_pip_args()
        if wheel_args:
            _log("CPU extra-index pip missed or Llama still missing; trying direct wheel")
            proc = _pip_install(wheel_args)
            if proc.returncode == 0 and _import_ok():
                _HEAL_ERROR = ""
                _log("llama-cpp-python CPU wheel installed from GitHub release")
                return ""
        if proc.returncode != 0:
            _HEAL_PIP_FAILED = True
            _HEAL_ERROR = _short_pip_error(proc)
            _log(f"llama-cpp-python CPU wheel pip failed: {_HEAL_ERROR}")
            return _HEAL_ERROR
        _HEAL_ERROR = _LAST_IMPORT_ERROR or "import failed after pip"
        _log(f"llama-cpp-python installed but import failed: {_HEAL_ERROR}")
        return _HEAL_ERROR


def status_for_reason(reason: str | None) -> str:
    """Operator-facing Enhance status (never mixed into CLIP text).

    Arguments:
        reason: Internal passthrough token, or None when the rewriter ran.

    Returns:
        Empty string on success; a one-line next step otherwise.
    """
    if not reason:
        return ""
    if reason == REASON_GGUF_MISSING:
        return "GGUF missing — run ./scripts/manage.sh download-models"
    if reason == REASON_LLAMA_UNAVAILABLE:
        return llama_cpp_unavailable_status()
    if reason == REASON_LLM_LOAD_FAILED:
        return "GGUF failed to load"
    if reason == REASON_EMPTY:
        return "timeout or empty model output"
    return reason


@dataclass(frozen=True)
class EnhanceResult:
    """CLIP text plus an optional passthrough reason for the status widget."""

    text: str
    reason: str | None = None

    @property
    def preview(self) -> str:
        """CLIP string only (the prefix used to confuse the CLIP prompt box)."""
        return self.text

    @property
    def status(self) -> str:
        return status_for_reason(self.reason)


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
      lock=view with a shot card front-loads the camera so Klein treats
      the still as a new walkthrough frame, then repeats that this still
      is only the room and backdrop the shot names. lock=state and
      identity-only joins keep the bible first.
    """
    bible = identity.strip() if isinstance(identity, str) else str(identity or "").strip()
    card = shot.strip() if isinstance(shot, str) else str(shot or "").strip()
    inv = inventory.strip() if isinstance(inventory, str) else str(inventory or "").strip()
    mode = lock.strip().lower() if isinstance(lock, str) else LOCK_VIEW
    if mode not in LOCK_IDS:
        mode = LOCK_VIEW
    if not bible and not card and not inv:
        return ""
    inv_line = f"Locked inventory (do not change): {inv}." if inv else ""
    lock_line = LOCK_STATE_LINE if mode == LOCK_STATE else LOCK_VIEW_LINE
    parts: list[str] = []
    camera_first = mode == LOCK_VIEW and bool(card)
    if camera_first:
        parts.append(card)
        parts.append(lock_line)
        if bible:
            parts.append(bible)
        if inv_line:
            parts.append(inv_line)
        parts.append(LOCK_VIEW_CLOSER)
        return " ".join(parts)
    if bible:
        parts.append(bible)
    if inv_line:
        parts.append(inv_line)
    parts.append(lock_line)
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


def load_view_pack(name: str) -> list[dict[str, str]]:
    """Load one camera-role pack from views.json (label + shot, no identity nouns)."""
    global _VIEWS
    if _VIEWS is None:
        raw = json.loads(VIEWS_PATH.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("views.json must be an object")
        views: dict[str, list[dict[str, str]]] = {}
        for key, value in raw.items():
            if not isinstance(value, list):
                raise ValueError(f"view pack {key} must be a list")
            cards: list[dict[str, str]] = []
            for item in value:
                if not isinstance(item, dict):
                    raise ValueError(f"view pack {key} entries must be objects")
                label = str(item.get("label") or "").strip()
                shot = str(item.get("shot") or "").strip()
                if not label or not shot:
                    raise ValueError(f"view pack {key} needs label and shot")
                cards.append({"label": label, "shot": shot})
            views[str(key)] = cards
        _VIEWS = views
    pack = _VIEWS.get(name)
    if pack is None:
        raise KeyError(f"unknown view pack {name!r}")
    return pack


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


def with_style_system(system: str, style_id: str) -> str:
    """Append the dropdown-wins addendum when a style is selected."""
    if style_id == STYLE_NONE:
        return system
    return f"{system.rstrip()}\n\n{STYLE_SYSTEM_ADDENDUM}"


def _collapse_spaces(text: str) -> str:
    cleaned = re.sub(r"[ \t]+", " ", text)
    cleaned = re.sub(r" +([,.;:])", r"\1", cleaned)
    cleaned = re.sub(r"\s+\n", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _drop_phrase(text: str, phrase: str) -> str:
    token = (phrase or "").strip()
    if len(token) < 5:
        return text
    pattern = re.compile(re.escape(token), re.IGNORECASE)
    return pattern.sub("", text)


def _own_look_blob(style_id: str) -> str:
    entry = _style_entry(style_id)
    parts = [str(entry.get(field) or "") for field in _STYLE_LOOK_FIELDS]
    parts.extend(style_must_include(style_id))
    parts.append(style_suffix(style_id))
    return " ".join(parts).lower()


def _strip_phrases(style_id: str) -> list[str]:
    own = _own_look_blob(style_id)
    phrases = list(style_conflicts(style_id))
    for extra in _LAB_LOOK_PHRASES:
        if extra.lower() not in own:
            phrases.append(extra)
    for sid, other in load_styles().items():
        if sid == style_id:
            continue
        head = str(other.get("medium") or "").split(".")[0].strip()
        if len(head) >= 8 and head.lower() not in own:
            phrases.append(head)
        for item in _string_list(other, "must_include"):
            if len(item) >= 8 and item.lower() not in own:
                phrases.append(item)
    phrases.sort(key=len, reverse=True)
    return phrases


def apply_style_to_prompt(text: str, style_id: str) -> str:
    """Force the dropdown style into CLIP text: strip fights, front-load medium.

    Arguments:
      text: rewriter or source prompt
      style_id: catalog id or none
    Returns:
      text unchanged when style is none; otherwise a restyled CLIP prompt.
    """
    if style_id == STYLE_NONE:
        return text
    entry = _style_entry(style_id)
    if not entry:
        return text
    body = (text or "").strip()
    for phrase in _strip_phrases(style_id):
        body = _drop_phrase(body, phrase)
    body = _collapse_spaces(body)
    medium = str(entry.get("medium") or "").strip().rstrip(".")
    light = str(entry.get("light") or "").strip().rstrip(".")
    heads: list[str] = []
    if medium and medium.lower() not in body.lower():
        heads.append(medium)
    if light and light.lower() not in body.lower():
        heads.append(light)
    if heads:
        lead = ". ".join(heads) + "."
        body = f"{lead} {body}".strip() if body else lead
    for phrase in style_must_include(style_id):
        if phrase.lower() not in body.lower():
            body = f"{body} {phrase}." if body else f"{phrase}."
    suffix = style_suffix(style_id)
    if suffix and suffix.rstrip(".").lower() not in body.lower():
        body = f"{body} {suffix}".strip() if body else suffix
    return _collapse_spaces(body)


def ensure_style_details(text: str, style_id: str) -> str:
    """Apply the selected style to CLIP text (alias of apply_style_to_prompt)."""
    return apply_style_to_prompt(text, style_id)


def flavor_for_system(name: str) -> str:
    """Map a system-prompt stem to a style-instruction flavor."""
    if name == "klein_edit":
        return FLAVOR_KLEIN_EDIT
    if name == "klein_identity":
        return FLAVOR_KLEIN_IDENTITY
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


def strip_model_wrapping(text: str) -> str:
    """Remove think tags, markdown fences, or wrapping quotes from a model reply."""
    cleaned = (text or "").strip()
    for pattern in _THINK_BLOCKS:
        cleaned = pattern.sub("", cleaned)
    cleaned = cleaned.strip()
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


def occupancy_mode() -> str:
    """Read occupancy mode from outputs ``.occupancy.json`` (unknown if missing)."""
    seen: set[str] = set()
    candidates: list[Path] = []
    for raw in (
        os.environ.get("COMFY_OUTPUT_DIR", "").strip(),
        "/outputs",
    ):
        if not raw or raw in seen:
            continue
        seen.add(raw)
        candidates.append(Path(raw) / ".occupancy.json")
    for path in candidates:
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        mode = str(data.get("mode") or "").strip()
        return mode or "unknown"
    return "unknown"


def sidecar_occupancy_ok(mode: str | None = None) -> bool:
    """True when occupancy allows the host 35B sidecar (not a visual/ACE GPU job)."""
    current = occupancy_mode() if mode is None else str(mode or "").strip()
    if not current:
        current = "unknown"
    return current in SIDECAR_OK_OCCUPANCY


def sidecar_base_url() -> str:
    """OpenAI-compatible origin. Container uses host.docker.internal."""
    port = os.environ.get("EZ_LLM_SIDECAR_PORT", DEFAULT_SIDECAR_PORT).strip()
    if not port.isdigit():
        port = DEFAULT_SIDECAR_PORT
    explicit = os.environ.get("EZ_LLM_SIDECAR_URL", "").strip().rstrip("/")
    if explicit:
        return explicit
    in_container = Path("/.dockerenv").is_file() or (
        os.environ.get("MODELS_ROOT", "").strip() == "/models"
    )
    host = "host.docker.internal" if in_container else "127.0.0.1"
    return f"http://{host}:{port}"


def _sidecar_timeout_s() -> float:
    try:
        value = float(os.environ.get("EZ_LLM_TIMEOUT_S", str(DEFAULT_TIMEOUT_S)).strip())
    except ValueError:
        return float(DEFAULT_TIMEOUT_S)
    if value <= 0:
        return float(DEFAULT_TIMEOUT_S)
    return value


def _urlopen_sidecar(request: urllib.request.Request, timeout: float) -> Any:
    """Indirection so pytest can mock sidecar HTTP without touching search."""
    return urllib.request.urlopen(request, timeout=timeout)


def _complete_via_sidecar(
    system: str,
    user: str,
    *,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = 0.0,
) -> tuple[str, str | None] | None:
    """Use llama-server /v1 when occupancy allows and it answers. None if down."""
    if not sidecar_occupancy_ok():
        return None
    base = sidecar_base_url()
    timeout = _sidecar_timeout_s()
    models_req = urllib.request.Request(
        f"{base}/v1/models",
        method="GET",
        headers={"Accept": "application/json"},
    )
    try:
        with _urlopen_sidecar(models_req, min(timeout, 0.4)) as resp:
            body = resp.read()
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return None
    if not body:
        return None
    tokens = int(max_tokens) if int(max_tokens) > 0 else DEFAULT_MAX_TOKENS
    temp = float(temperature)
    if temp < 0.0:
        temp = 0.0
    payload = {
        "model": "qwen36-35b-a3b",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temp,
        "max_tokens": tokens,
    }
    chat_req = urllib.request.Request(
        f"{base}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with _urlopen_sidecar(chat_req, timeout) as resp:
            raw = resp.read()
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        _log(f"llm-desk sidecar chat failed: {exc}")
        return None
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        return "", REASON_SIDECAR_EMPTY
    choices = data.get("choices") if isinstance(data, dict) else None
    if not isinstance(choices, list) or not choices:
        return "", REASON_SIDECAR_EMPTY
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    text = ""
    if isinstance(message, dict):
        text = strip_model_wrapping(str(message.get("content") or ""))
    if not text:
        return "", REASON_SIDECAR_EMPTY
    _log(f"llm engine=sidecar url={base}")
    return text, None


def _n_gpu_layers() -> int:
    """GPU 4B when occupancy is not a video/mesh hog. CPU next to Wan/LTX/TRELLIS.

    ``EZ_LLM_ALLOW_GPU=0`` forces CPU. Occupancy ``wan``/``ltx``/``trellis``
    forces CPU even if ngl is set. GPU-safe occupancy (klein/llm/idle/…)
    defaults to 99 so CPU is not the writing-desk default.
    """
    allow = os.environ.get("EZ_LLM_ALLOW_GPU", "").strip().lower()
    if allow in {"0", "false", "no", "off"}:
        return 0
    mode = occupancy_mode()
    if mode in CPU_FORCE_OCCUPANCY:
        _log(f"occupancy {mode}: CPU 4B (OOM-safe); n_gpu_layers=0")
        return 0
    raw = os.environ.get("EZ_LLM_N_GPU_LAYERS", "").strip()
    requested = 0
    if raw:
        try:
            requested = int(raw)
        except ValueError:
            requested = 0
    if requested > 0:
        return requested
    if mode in GPU_SAFE_OCCUPANCY:
        return DEFAULT_SIDECAR_NGL
    return 0


def resolve_gguf_path() -> str:
    """First existing GGUF among env, comfy/llm, and the HF snapshot dir.

    Operators should not set EZ_LLM_GGUF. Fallbacks cover a missing relative
    ``comfy/llm/`` link after ``download-llm`` left the snapshot in place.

    Returns:
        Path to an existing file, or the env/default path for missing logs.
    """
    env_path = os.environ.get("EZ_LLM_GGUF", "").strip()
    models_root = (os.environ.get("MODELS_ROOT") or "").strip()
    models_dir = (os.environ.get("MODELS_DIR") or "").strip()
    comfy_home = (os.environ.get("COMFY_HOME") or "").strip()
    roots: list[str] = []
    for root in (models_root, models_dir, "/models"):
        if root and root not in roots:
            roots.append(root)
    candidates: list[str] = []
    if env_path:
        candidates.append(env_path)
    candidates.append(DEFAULT_GGUF)
    for root in roots:
        candidates.append(f"{root}/comfy/llm/{GGUF_FILENAME}")
        candidates.append(f"{root}/{SNAPSHOT_DIR}/{GGUF_FILENAME}")
    if comfy_home:
        candidates.append(f"{comfy_home}/models/llm/{GGUF_FILENAME}")
    seen: set[str] = set()
    for path in candidates:
        if not path or path in seen:
            continue
        seen.add(path)
        if os.path.isfile(path):
            return path
    return env_path or DEFAULT_GGUF


def _gguf_path() -> str:
    return resolve_gguf_path()


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
    llama_cls = _load_llama_class()
    if llama_cls is None:
        heal_err = _heal_llama_cpp_cpu()
        if heal_err:
            _log(f"llama-cpp-python not installed — {heal_err}")
            return None, REASON_LLAMA_UNAVAILABLE
        llama_cls = _load_llama_class()
        if llama_cls is None:
            _log("llama-cpp-python not installed — passing prompt through")
            return None, REASON_LLAMA_UNAVAILABLE
    kwargs: dict[str, Any] = {
        "model_path": path,
        "n_ctx": _n_ctx(),
        "n_threads": _n_threads(),
        "n_gpu_layers": _n_gpu_layers(),
        "verbose": False,
    }
    try:
        _LLM = llama_cls(chat_format="chatml", **kwargs)
    except TypeError as exc:
        _log(f"Llama chat_format unsupported ({exc}); retrying without it")
        try:
            _LLM = llama_cls(**kwargs)
        except Exception as retry_exc:  # noqa: BLE001 — fail-soft
            _log(f"failed to load GGUF {path}: {retry_exc}")
            _LLM = None
            _LLM_PATH = ""
            return None, REASON_LLM_LOAD_FAILED
    except Exception as exc:  # noqa: BLE001 — fail-soft
        _log(f"failed to load GGUF {path}: {exc}")
        _LLM = None
        _LLM_PATH = ""
        return None, REASON_LLM_LOAD_FAILED
    _LLM_PATH = path
    ngl = _n_gpu_layers()
    engine = "gpu-4b" if ngl > 0 else "cpu-4b"
    _log(f"loaded local LLM {path} (engine={engine}, n_gpu_layers={ngl}, n_threads={_n_threads()})")
    return _LLM, None


def _generate(
    llm: Any,
    system: str,
    user: str,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = 0.0,
) -> str:
    tokens = int(max_tokens) if int(max_tokens) > 0 else DEFAULT_MAX_TOKENS
    temp = float(temperature)
    if temp < 0.0:
        temp = 0.0
    body = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temp,
        max_tokens=tokens,
    )
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return ""
    if not isinstance(content, str):
        return ""
    return strip_model_wrapping(content)


def complete(
    system: str,
    user: str,
    *,
    max_tokens: int | None = None,
    temperature: float | None = None,
    timeout_s: int | None = None,
) -> tuple[str, str | None]:
    """GPU sidecar when occupancy allows, else local 4B. Empty text plus a reason."""
    tokens = DEFAULT_MAX_TOKENS if max_tokens is None else int(max_tokens)
    if tokens < 1:
        tokens = DEFAULT_MAX_TOKENS
    temp = 0.0 if temperature is None else float(temperature)
    if temp < 0.0:
        temp = 0.0
    sidecar = _complete_via_sidecar(system, user, max_tokens=tokens, temperature=temp)
    if sidecar is not None:
        return sidecar
    llm, reason = _get_llama()
    if llm is None:
        return "", reason or REASON_LLAMA_UNAVAILABLE
    if timeout_s is None:
        timeout = _timeout_s()
    else:
        try:
            timeout = int(timeout_s)
        except (TypeError, ValueError):
            timeout = _timeout_s()
        if timeout < 1:
            timeout = _timeout_s()
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_generate, llm, system, user, tokens, temp)
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
