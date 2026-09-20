"""Optional still caption for Prompt Enhance (hermetic at import).

Enable-off returns empty without loading a VLM. Missing GGUF fails soft.
"""

from __future__ import annotations

import base64
import io
import os
import threading
from typing import Any

# Opt-in Qwen2.5-VL 3B (Apache). Not part of download-models.
DESCRIBE_GGUF = "Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf"
DESCRIBE_MMPROJ = "mmproj-Qwen2.5-VL-3B-Instruct-Q8_0.gguf"
DEFAULT_DESCRIBE_DIR = "/models/comfy/llm"
REASON_DISABLED = "describe off"
REASON_NO_IMAGE = "no image"
REASON_GGUF_MISSING = "describe GGUF missing"
REASON_LLAMA_UNAVAILABLE = "llama.cpp vision unavailable"
REASON_EMPTY = "empty vision output"
MAX_LONG_EDGE = 768
DEFAULT_MAX_TOKENS = 220

DESCRIBE_SYSTEM = (
    "Return only a caption of this still. No preface, no markdown, no wrapping "
    "quotes. Name inventory, lettering (spell it), colors, layout, and where "
    "the subject sits. SFW. No real-person names. Stay under 80 words. This "
    "caption will be supporting context for a prompt rewriter — do not write "
    "a new scene."
)

_VISION: Any = None
_VISION_PATH = ""
_VISION_LOCK = threading.Lock()
_LAST_STATUS = REASON_DISABLED


def _as_bool(value: object) -> bool:
    """Parse a Comfy BOOLEAN widget.

    Args:
        value: Bool, number, or yes/no string.

    Returns:
        Parsed flag; unrecognized strings are False.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def last_status() -> str:
    """Return the last describe fail-soft / skip reason.

    Returns:
        Status string (empty when a caption was produced).
    """
    return _LAST_STATUS


def describe_gguf_path() -> str:
    """Return the GGUF path from env or the lab default.

    Returns:
        Absolute GGUF path.
    """
    override = os.environ.get("EZ_DESCRIBE_GGUF", "").strip()
    if override:
        return override
    return f"{DEFAULT_DESCRIBE_DIR}/{DESCRIBE_GGUF}"


def describe_mmproj_path() -> str:
    """Return the mmproj path from env or the lab default.

    Returns:
        Absolute mmproj path.
    """
    override = os.environ.get("EZ_DESCRIBE_MMPROJ", "").strip()
    if override:
        return override
    return f"{DEFAULT_DESCRIBE_DIR}/{DESCRIBE_MMPROJ}"


def _log(message: str) -> None:
    """Write a pack line to stderr.

    Args:
        message: Text after the prefix.
    """
    print(f"[ez_prompt_enhance] {message}", flush=True)


def _gguf_ready() -> bool:
    """True when both GGUF files exist and are non-empty.

    Returns:
        Whether describe weights are on disk.
    """
    gguf = describe_gguf_path()
    mmproj = describe_mmproj_path()
    try:
        return os.path.isfile(gguf) and os.path.getsize(gguf) > 0 and (
            os.path.isfile(mmproj) and os.path.getsize(mmproj) > 0
        )
    except OSError:
        return False


def _image_to_png_b64(image: Any) -> str:
    """Encode a Comfy IMAGE tensor as PNG base64.

    Args:
        image: BHWC tensor, numpy array, or object with ``shape``.

    Returns:
        Base64 PNG, or empty when encode is not possible.

    Raises:
        Exception: Propagated only after callers wrap fail-soft.
    """
    try:
        import numpy as np
    except Exception:  # noqa: BLE001 — hermetic tests
        return ""
    try:
        tensor = image
        if hasattr(tensor, "detach"):
            tensor = tensor.detach()
        if hasattr(tensor, "cpu"):
            tensor = tensor.cpu()
        if hasattr(tensor, "numpy"):
            array = tensor.numpy()
        else:
            array = np.asarray(tensor)
        if array.ndim == 4:
            array = array[0]
        if array.ndim != 3:
            return ""
        clip = np.clip(array, 0.0, 1.0)
        pixels = (clip * 255.0).astype("uint8")
        height, width = int(pixels.shape[0]), int(pixels.shape[1])
        try:
            from PIL import Image as PILImage
        except Exception:  # noqa: BLE001
            return ""
        long_edge = max(height, width)
        if long_edge > MAX_LONG_EDGE:
            scale = MAX_LONG_EDGE / float(long_edge)
            new_h = max(int(round(height * scale)), 1)
            new_w = max(int(round(width * scale)), 1)
            pil = PILImage.fromarray(pixels)
            pil = pil.resize((new_w, new_h))
            buf = io.BytesIO()
            pil.save(buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode("ascii")
        pil = PILImage.fromarray(pixels)
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:  # noqa: BLE001 — fail-soft
        return ""


def _get_vision() -> tuple[Any, str | None]:
    """Load llama.cpp with mmproj, or return a fail-soft reason.

    Returns:
        ``(llm, None)`` or ``(None, reason)``.
    """
    global _VISION, _VISION_PATH
    if not _gguf_ready():
        return None, REASON_GGUF_MISSING
    path = describe_gguf_path()
    mmproj = describe_mmproj_path()
    with _VISION_LOCK:
        if _VISION is not None and _VISION_PATH == path:
            return _VISION, None
        try:
            from llama_cpp import Llama
        except Exception as exc:  # noqa: BLE001
            _log(f"llama.cpp import failed for describe: {exc}")
            return None, REASON_LLAMA_UNAVAILABLE
        kwargs: dict[str, Any] = {
            "model_path": path,
            "n_ctx": 4096,
            "n_threads": int(os.environ.get("EZ_LLM_THREADS", "8") or 8),
            "verbose": False,
        }
        # clip_model_path is the llama-cpp-python mmproj hook (0.3+).
        kwargs["clip_model_path"] = mmproj
        try:
            _VISION = Llama(**kwargs)
        except TypeError:
            kwargs.pop("clip_model_path", None)
            try:
                _VISION = Llama(**kwargs)
            except Exception as exc:  # noqa: BLE001
                _log(f"describe GGUF failed to load: {exc}")
                _VISION = None
                return None, REASON_LLAMA_UNAVAILABLE
        except Exception as exc:  # noqa: BLE001
            _log(f"describe GGUF failed to load: {exc}")
            _VISION = None
            return None, REASON_LLAMA_UNAVAILABLE
        _VISION_PATH = path
        _log(f"loaded describe VLM {path}")
        return _VISION, None


def _vision_complete(png_b64: str) -> tuple[str, str | None]:
    """Caption one PNG via llama.cpp chat+image, fail-soft.

    Args:
        png_b64: Base64 PNG payload.

    Returns:
        ``(text, None)`` or ``("", reason)``.
    """
    llm, reason = _get_vision()
    if llm is None:
        return "", reason or REASON_LLAMA_UNAVAILABLE
    data_url = f"data:image/png;base64,{png_b64}"
    user: Any = [
        {"type": "image_url", "image_url": {"url": data_url}},
        {"type": "text", "text": "Caption this still for a prompt rewriter."},
    ]
    try:
        body = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": DESCRIBE_SYSTEM},
                {"role": "user", "content": user},
            ],
            temperature=0.0,
            max_tokens=DEFAULT_MAX_TOKENS,
        )
    except Exception as exc:  # noqa: BLE001
        _log(f"describe complete failed: {exc}")
        return "", REASON_EMPTY
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return "", REASON_EMPTY
    if not isinstance(content, str) or not content.strip():
        return "", REASON_EMPTY
    return content.strip(), None


def describe_image(*, enable: object, image: Any = None) -> str:
    """Return a still caption, or empty when disabled / fail-soft.

    Args:
        enable: Comfy BOOLEAN; off skips the VLM.
        image: Optional Comfy IMAGE tensor.

    Returns:
        Caption string (may be empty).
    """
    global _LAST_STATUS
    if not _as_bool(enable):
        _LAST_STATUS = REASON_DISABLED
        return ""
    if image is None:
        _LAST_STATUS = REASON_NO_IMAGE
        return ""
    png_b64 = _image_to_png_b64(image)
    if not png_b64:
        _LAST_STATUS = REASON_NO_IMAGE
        return ""
    text, reason = _vision_complete(png_b64)
    if not text:
        _LAST_STATUS = reason or REASON_EMPTY
        return ""
    _LAST_STATUS = ""
    return text


def reset_describe_for_tests() -> None:
    """Drop the cached VLM handle (tests only)."""
    global _VISION, _VISION_PATH, _LAST_STATUS
    _VISION = None
    _VISION_PATH = ""
    _LAST_STATUS = REASON_DISABLED
