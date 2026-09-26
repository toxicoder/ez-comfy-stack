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

from ._styles import (
    CONTEXT_SYSTEM_ADDENDUM,
    STYLE_SYSTEM_ADDENDUM,
    apply_style_to_prompt,
    compose_context_user,
    ensure_style_details,
    flavor_for_system,
    format_style_instruction,
    join_context_fields,
    load_styles,
    style_conflicts,
    style_ids,
    style_llm_block,
    style_must_include,
    style_suffix,
    with_audio_system,
    with_cinema_system,
    with_context_system,
    with_style_system,
)
from ._styles import (  # noqa: F401 - coverage/monkeypatch façade
    _collapse_spaces,
    _drop_phrase,
    _own_look_blob,
    _string_list,
    _strip_phrases,
    _style_entry,
)

# Paths, GGUF defaults, occupancy, heal, style, and rewrite constants.
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
NEGATIVE_MAX_TOKENS = 200
NEGATIVE_FAMILIES = (
    "klein",
    "wan",
    "ltx",
    "zimage",
    "longcat",
    "dreamx",
    "s2v",
)
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
REASON_STYLE_IGNORED_S2V = "style ignored in s2v (start image and wav own look)"
REASON_STYLE_IGNORED_VC = "style ignored in vc (previous frames own look)"
REASON_STYLE_IGNORED_TEXT_SWAP = (
    "style ignored in text_swap (source still owns look)"
)
REASON_STYLE_IGNORED_BG_SWAP = (
    "style ignored in background_swap (source still owns subject look)"
)
STYLE_IGNORED_MODES = {
    "i2v": REASON_STYLE_IGNORED_I2V,
    "flf": REASON_STYLE_IGNORED_FLF,
    "vace": REASON_STYLE_IGNORED_VACE,
    "s2v": REASON_STYLE_IGNORED_S2V,
    "vc": REASON_STYLE_IGNORED_VC,
    "text_swap": REASON_STYLE_IGNORED_TEXT_SWAP,
    "background_swap": REASON_STYLE_IGNORED_BG_SWAP,
}

_STYLES: dict[str, dict[str, Any]] | None = None
_VIEWS: dict[str, list[dict[str, str]]] | None = None

_THINK_BLOCKS = (
    re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE),
    re.compile(r"<\|think\|>.*?<\|/think\|>", re.DOTALL | re.IGNORECASE),
)


def _log(message: str) -> None:
    """Write an operator status line to stderr.

    Args:
        message: Human status without a trailing newline.
    """
    print(f"[ez_prompt_enhance] {message}", file=sys.stderr)


def llama_cpp_direct_wheel_url() -> str:
    """GitHub release manylinux wheel for this CPU arch, or empty.

    Returns:
        Wheel URL for aarch64/x86_64, else empty.
    """
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
    """pip install operands: CPU extra-index as --index-url, pin, binaries only.

    Returns:
        Argument list after ``python -m pip install``.
    """
    return [
        "--only-binary=:all:",
        "--index-url",
        LLAMA_CPP_CPU_INDEX,
        "--extra-index-url",
        PYPI_SIMPLE_INDEX,
        LLAMA_CPP_CPU_PKG,
    ]


def llama_cpp_direct_wheel_pip_args() -> list[str]:
    """pip install operands: replace a same-version wheel from GitHub.

    Returns:
        Force-reinstall args, or empty when the arch has no wheel URL.
    """
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
    """Exact docker exec pip line for a blocking Dub / Enhance status.

    Returns:
        One-line ``docker exec ... pip install`` the operator can paste.
    """
    args = llama_cpp_direct_wheel_pip_args() or llama_cpp_cpu_pip_index_args()
    return (
        f"docker exec ez-comfy-studio {LLAMA_CPP_OPERATOR_PYTHON} "
        f"-m pip install {' '.join(args)}"
    )


def llama_cpp_unavailable_status() -> str:
    """Operator-facing next step when Llama cannot import after heal.

    Returns:
        Status line including the pip command.
    """
    cmd = llama_cpp_operator_pip_command()
    pip_detail = _HEAL_ERROR.strip()
    import_detail = _LAST_IMPORT_ERROR.strip()
    if _HEAL_PIP_FAILED and pip_detail:
        return f"llama.cpp unavailable - CPU wheel pip failed ({pip_detail}). {cmd}"
    if import_detail:
        return f"llama.cpp unavailable - Llama import failed ({import_detail}). {cmd}"
    if pip_detail:
        return f"llama.cpp unavailable - Llama import failed ({pip_detail}). {cmd}"
    return f"llama.cpp unavailable - Llama did not import. {cmd}"


def reset_llama_runtime_for_tests() -> None:
    """Clear cached LLM handle and CPU-wheel heal state (unit tests only)."""
    global _HEAL_TRIED, _HEAL_ERROR, _HEAL_PIP_FAILED, _LAST_IMPORT_ERROR
    _close_llm()
    _HEAL_TRIED = False
    _HEAL_ERROR = ""
    _HEAL_PIP_FAILED = False
    _LAST_IMPORT_ERROR = ""


def _pip_install(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run ``python -m pip install`` on this interpreter. Tests patch this.

    Args:
        args: Operand list after ``pip install``.

    Returns:
        Completed process (timeout becomes a non-zero synthetic result).
    """
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
    """Last non-empty pip line, truncated.

    Args:
        proc: Failed or timed-out pip result.

    Returns:
        One-line error for Enhance status.
    """
    text = (proc.stderr or proc.stdout or "").strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return f"pip exit {proc.returncode}"
    return lines[-1][:200]


def _forget_llama_module() -> None:
    """Drop cached ``llama_cpp`` modules so the next import reloads the wheel."""
    for name in list(sys.modules):
        if name == "llama_cpp" or name.startswith("llama_cpp."):
            sys.modules.pop(name, None)
    importlib.invalidate_caches()


def _load_llama_class() -> Any | None:
    """Return llama_cpp.Llama, or None when the CPU wheel is missing.

    Returns:
        ``Llama`` class, or None after recording the import error.
    """
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
    """Install the CPU wheel once per process. Empty string on success.

    Returns:
        Empty on importable Llama, else a short pip/import error.
    """
    global _HEAL_TRIED, _HEAL_ERROR, _HEAL_PIP_FAILED
    with _HEAL_LOCK:
        if _HEAL_TRIED:
            return _HEAL_ERROR
        _HEAL_TRIED = True
        _HEAL_PIP_FAILED = False
        _log("llama-cpp-python missing - installing CPU wheel")

        def _import_ok() -> bool:
            """Reload llama_cpp and report whether Llama imports.

            Returns:
                True when ``Llama`` is importable after dropping cached modules.
            """
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

    Args:
        reason: Internal passthrough token, or None when the rewriter ran.

    Returns:
        Empty string on success; a one-line next step otherwise.
    """
    if not reason:
        return ""
    if reason == REASON_GGUF_MISSING:
        return "GGUF missing - run ./scripts/manage.sh download-models"
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
        """CLIP string only (the prefix used to confuse the CLIP prompt box).

        Returns:
            The rewritten or original prompt text.
        """
        return self.text

    @property
    def status(self) -> str:
        """Operator-facing passthrough reason, or empty on success.

        Returns:
            Status line from ``status_for_reason``.
        """
        return status_for_reason(self.reason)


def join_prompt(
    identity: str,
    shot: str,
    inventory: str = "",
    lock: str = LOCK_VIEW,
) -> str:
    """Join a world bible, locked inventory, persist lock, and shot line.

    Args:
        identity: Camera-free place/subject bible.
        shot: Camera, light, or action line for this still.
        inventory: Object list that must repeat across views.
        lock: ``view`` (new camera) or ``state`` (same camera).
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

    Args:
        name: Stem without ``.txt`` (e.g. ``klein_t2i``).
    Returns:
      File contents stripped of trailing whitespace.
    Raises:
      FileNotFoundError if the prompt file is missing.
    """
    path = PROMPTS_DIR / f"{name}.txt"
    return path.read_text(encoding="utf-8").strip()


def load_view_pack(name: str) -> list[dict[str, str]]:
    """Load one camera-role pack from views.json (label + shot, no identity nouns).

    Args:
        name: Pack key in ``views.json``.

    Returns:
        Cards with ``label`` and ``shot`` strings.

    Raises:
        KeyError: Unknown pack name.
        ValueError: Malformed catalog.
    """
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




# Negative-prompt artifact tokens and word matcher.
_ARTIFACT_KEEP = (
    "watermark",
    "watermarks",
    "melted geometry",
    "duplicate limbs",
    "morphing",
    "identity drift",
    "warping objects",
    "face melting",
    "flicker",
    "jitter",
    "frame stutter",
    "rubbery motion",
    "melting edges",
    "texture crawl",
    "sudden cuts",
    "burned-in text",
    "oversharpen halos",
    "muddy blacks",
    "muddy textures",
    "plastic skin",
    "extra fingers",
    "fused fingers",
    "missing fingers",
    "poorly drawn hands",
    "poorly drawn faces",
    "poorly drawn face",
    "extra limbs",
    "disfigured hands",
    "wrong hand count",
    "malformed hands",
    "three legs",
    "walking backwards",
    "many people",
    "deformed facial features",
    "missing facial features",
)
# Positive phrases that mean the operator asked for that defect.
_DEFECT_REQUESTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("extra finger", ("six-finger", "six finger", "6 finger", "extra finger")),
    ("fused finger", ("fused finger",)),
    ("missing finger", ("missing finger",)),
    ("three leg", ("three leg", "three-leg")),
    (
        "walking backwards",
        (
            "walking backwards",
            "walk backward",
            "walking backward",
            "walks backward",
        ),
    ),
    ("many people", ("many people", "crowd")),
    ("still picture", ("no motion", "motionless", "completely still", "hold still")),
    ("static", ("no motion", "motionless", "completely still", "hold still")),
)
_WORD_RE = re.compile(r"[a-z0-9][a-z0-9'-]{4,}")


def compose_negative_user(prompt: str, positive: str) -> str:
    """Build the rewriter user message: positive context plus negative seed.

    Args:
        prompt: Canned or lazy negative seed.
        positive: CLIP-bound positive string (may be empty).
    Returns:
      User message with POSITIVE / NEGATIVE SEED sections.
    """
    seed = (prompt or "").strip()
    pos = (positive or "").strip()
    parts: list[str] = []
    if pos:
        parts.append(f"POSITIVE:\n{pos}")
    parts.append(f"NEGATIVE SEED:\n{seed or '(empty)'}")
    return "\n\n".join(parts)


def _negative_tokens(negative: str) -> list[str]:
    """Split a comma-separated negative seed.

    Args:
        negative: Negative CLIP string.

    Returns:
        Stripped tokens, empties dropped.
    """
    return [token.strip() for token in (negative or "").split(",") if token.strip()]


def _is_artifact_token(token: str) -> bool:
    """True when a negative token is a keep-forever artifact.

    Args:
        token: One comma-separated negative clause.

    Returns:
        Whether the token mentions a protected artifact phrase.
    """
    low = token.lower()
    for keep in _ARTIFACT_KEEP:
        if keep in low or low in keep:
            return True
    return False


def _token_hits_blob(token: str, blob: str) -> bool:
    """True when a negative token overlaps a positive look blob.

    Args:
        token: Lowercased negative clause.
        blob: Lowercased positive look text.

    Returns:
        Whether the whole token or a 5+ char word appears in ``blob``.
    """
    if not token or not blob:
        return False
    if token in blob:
        return True
    for word in _WORD_RE.findall(token):
        if word in blob:
            return True
    return False


def _inferred_style_ids(positive: str) -> list[str]:
    """Guess selected style ids from positive CLIP text.

    Args:
        positive: CLIP-bound positive string.

    Returns:
        Catalog ids whose medium/label/suffix/must-include appear in the positive.
    """
    blob = (positive or "").lower()
    if not blob:
        return []
    hits: list[str] = []
    for sid, entry in load_styles().items():
        needles: list[str] = []
        for field in ("medium", "label", "suffix"):
            text = str(entry.get(field) or "").strip().rstrip(".")
            if len(text) >= 8:
                needles.append(text.lower())
        for phrase in style_must_include(sid):
            if len(phrase) >= 8:
                needles.append(phrase.lower())
        if any(needle in blob for needle in needles):
            hits.append(sid)
    return hits


def _style_own_look(style_id: str) -> str:
    """Lowercased look blob plus label and Wan stylization.

    Args:
        style_id: Catalog id.

    Returns:
        Text used to decide which negative tokens fight this style.
    """
    entry = _style_entry(style_id)
    parts = [
        _own_look_blob(style_id),
        str(entry.get("label") or ""),
        str(entry.get("wan_stylization") or ""),
    ]
    return " ".join(parts).lower()


def _requests_defect(token: str, positive: str) -> bool:
    """True when the positive asks for the defect this negative token blocks.

    Args:
        token: One comma-separated negative clause.
        positive: CLIP-bound positive string.

    Returns:
        Whether the token should be dropped because the positive requested it.
    """
    low = token.lower()
    pos = positive.lower()
    for needle, phrases in _DEFECT_REQUESTS:
        if needle in low and any(phrase in pos for phrase in phrases):
            return True
    return False


def complement_negative(negative: str, positive: str) -> str:
    """Drop negative tokens that fight the positive look; keep artifacts.

    Anatomy tokens stay even when the positive merely names a hand or a face.
    They drop only when the positive asks for that defect (six fingers, a crowd).

    Args:
        negative: Comma-separated negative seed or rewriter output.
        positive: CLIP-bound positive (style already applied).
    Returns:
      Comma-separated negative. Unchanged when positive is empty.
    """
    seed = (negative or "").strip()
    if not seed:
        return seed
    pos = (positive or "").strip()
    if not pos:
        return seed
    look = pos.lower()
    for sid in _inferred_style_ids(pos):
        look = f"{look} {_style_own_look(sid)}"
    kept: list[str] = []
    for token in _negative_tokens(seed):
        if _requests_defect(token, pos):
            continue
        if _is_artifact_token(token):
            kept.append(token)
            continue
        low = token.lower()
        if _token_hits_blob(low, look):
            continue
        kept.append(token)
    return ", ".join(kept)




def strip_model_wrapping(text: str) -> str:
    """Remove think tags, markdown fences, or wrapping quotes from a model reply.

    Args:
        text: Raw model content.

    Returns:
        CLIP-ready string with wrappers stripped.
    """
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
    """LLM generate timeout in seconds from ``EZ_LLM_TIMEOUT_S``.

    Returns:
        Positive timeout, else ``DEFAULT_TIMEOUT_S``.
    """
    raw = os.environ.get("EZ_LLM_TIMEOUT_S", str(DEFAULT_TIMEOUT_S)).strip()
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_TIMEOUT_S
    if value < 1:
        return DEFAULT_TIMEOUT_S
    return value


def _n_threads() -> int:
    """llama.cpp CPU thread count from ``EZ_LLM_N_THREADS``.

    Returns:
        Positive thread count, else ``DEFAULT_N_THREADS``.
    """
    raw = os.environ.get("EZ_LLM_N_THREADS", str(DEFAULT_N_THREADS)).strip()
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_N_THREADS
    if value < 1:
        return DEFAULT_N_THREADS
    return value


def _n_ctx() -> int:
    """llama.cpp context length from ``EZ_LLM_N_CTX``.

    Returns:
        Context size of at least 512, else ``DEFAULT_N_CTX``.
    """
    raw = os.environ.get("EZ_LLM_N_CTX", str(DEFAULT_N_CTX)).strip()
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_N_CTX
    if value < 512:
        return DEFAULT_N_CTX
    return value


def occupancy_mode() -> str:
    """Read occupancy mode from outputs ``.occupancy.json`` (unknown if missing).

    Returns:
        Occupancy mode string, or ``unknown`` when the file is missing.
    """
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
    """True when occupancy allows the host 35B sidecar (not a visual/ACE GPU job).

    Args:
        mode: Occupancy id to test; ``None`` reads ``.occupancy.json``.

    Returns:
        Whether the sidecar may take this rewrite.
    """
    current = occupancy_mode() if mode is None else str(mode or "").strip()
    if not current:
        current = "unknown"
    return current in SIDECAR_OK_OCCUPANCY


def sidecar_base_url() -> str:
    """OpenAI-compatible origin. Container uses host.docker.internal.

    Returns:
        ``http://host:port`` with no trailing slash.
    """
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
    """Sidecar HTTP timeout from ``EZ_LLM_TIMEOUT_S``.

    Returns:
        Positive timeout in seconds.
    """
    try:
        value = float(os.environ.get("EZ_LLM_TIMEOUT_S", str(DEFAULT_TIMEOUT_S)).strip())
    except ValueError:
        return float(DEFAULT_TIMEOUT_S)
    if value <= 0:
        return float(DEFAULT_TIMEOUT_S)
    return value


def _urlopen_sidecar(request: urllib.request.Request, timeout: float) -> Any:
    """Indirection so pytest can mock sidecar HTTP without touching search.

    Args:
        request: ``urllib`` request for ``/v1/models`` or chat.
        timeout: Socket timeout in seconds.

    Returns:
        Opened HTTP response (caller closes it).
    """
    return urllib.request.urlopen(request, timeout=timeout)


def _complete_via_sidecar(
    system: str,
    user: str,
    *,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = 0.0,
) -> tuple[str, str | None] | None:
    """Use llama-server /v1 when occupancy allows and it answers. None if down.

    Args:
        system: System prompt.
        user: User message.
        max_tokens: Chat completion cap.
        temperature: Sampling temperature (clamped at 0).

    Returns:
        ``(text, reason)`` when the sidecar answers, or None if it is down.
    """
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
    forces CPU even if ngl is set. GPU-safe occupancy (klein/llm/idle/...)
    defaults to 99 so CPU is not the writing-desk default.

    Returns:
        ``n_gpu_layers`` for llama.cpp (0 means CPU).
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
    """Resolved GGUF path for this process.

    Returns:
        Path from ``resolve_gguf_path``.
    """
    return resolve_gguf_path()


def _unload_after() -> bool:
    """True when ``EZ_LLM_UNLOAD`` asks to close the handle after each call.

    Returns:
        Whether ``complete`` should unload llama.cpp.
    """
    return os.environ.get("EZ_LLM_UNLOAD", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _close_llm() -> None:
    """Drop the cached llama.cpp handle and close it when possible."""
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
        except Exception as exc:  # noqa: BLE001 - fail-soft unload
            _log(f"llama close failed: {exc}")


def _get_llama() -> tuple[Any | None, str | None]:
    """Load llama.cpp once. Returns (handle, fail_reason).

    Returns:
        ``(Llama, None)`` on success, or ``(None, reason)`` for fail-soft.
    """
    global _LLM, _LLM_PATH
    path = _gguf_path()
    if not path or not os.path.isfile(path):
        _log(f"GGUF missing at {path or '(empty EZ_LLM_GGUF)'} - passing prompt through")
        return None, REASON_GGUF_MISSING
    if _LLM is not None and _LLM_PATH == path:
        return _LLM, None
    _close_llm()
    llama_cls = _load_llama_class()
    if llama_cls is None:
        heal_err = _heal_llama_cpp_cpu()
        if heal_err:
            _log(f"llama-cpp-python not installed - {heal_err}")
            return None, REASON_LLAMA_UNAVAILABLE
        llama_cls = _load_llama_class()
        if llama_cls is None:
            _log("llama-cpp-python not installed - passing prompt through")
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
        except Exception as retry_exc:  # noqa: BLE001 - fail-soft
            _log(f"failed to load GGUF {path}: {retry_exc}")
            _LLM = None
            _LLM_PATH = ""
            return None, REASON_LLM_LOAD_FAILED
    except Exception as exc:  # noqa: BLE001 - fail-soft
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
    """Run one chat completion on a loaded llama.cpp handle.

    Args:
        llm: llama.cpp ``Llama`` instance.
        system: System prompt.
        user: User message.
        max_tokens: Completion cap.
        temperature: Sampling temperature (clamped at 0).

    Returns:
        Stripped assistant content, or empty on a malformed response.
    """
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
    """GPU sidecar when occupancy allows, else local 4B. Empty text plus a reason.

    Args:
        system: System prompt.
        user: User message.
        max_tokens: Completion cap; ``None`` uses the default.
        temperature: Sampling temperature; ``None`` is 0.
        timeout_s: Local generate timeout; ``None`` uses env/default.

    Returns:
        ``(text, None)`` on success, or ``("", reason)`` for fail-soft.
    """
    _log("enhancing prompt (sidecar or local 4B)...")
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
    except Exception as exc:  # noqa: BLE001 - fail-soft
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
    """Rewrite fallback via local LLM when enhance is true.

    Args:
        system: System prompt.
        user: User message (operator prompt plus optional context).
        enhance: When false, return ``fallback`` with enhance-off reason.
        fallback: Original CLIP / tags string.

    Returns:
        ``EnhanceResult`` with rewritten text or the original on fail-soft.
    """
    original = fallback if isinstance(fallback, str) else str(fallback)
    if not enhance:
        return EnhanceResult(original, REASON_ENHANCE_OFF)
    if not original.strip():
        return EnhanceResult(original, None)
    rewritten, reason = complete(system, user)
    if not rewritten.strip():
        return EnhanceResult(original, reason or REASON_EMPTY)
    return EnhanceResult(rewritten, None)
