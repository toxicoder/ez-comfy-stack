"""Optional still caption for Prompt Enhance (hermetic at import).

Enable-off returns empty without loading a VLM. Missing GGUF fails soft.
"""

from __future__ import annotations

import base64
import io
import os
import re
import threading
from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    import llama_cpp

    from ez_common import ImageTensor

VisionModel: TypeAlias = "llama_cpp.Llama"
"""Cached llama.cpp vision handle held in :data:`_VISION`."""

# Opt-in Qwen2.5-VL 3B (Apache). Not part of download-models.
DESCRIBE_GGUF = "Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf"
DESCRIBE_MMPROJ = "mmproj-Qwen2.5-VL-3B-Instruct-Q8_0.gguf"
DEFAULT_DESCRIBE_DIR = "/models/comfy/llm"
REASON_DISABLED = "describe off"
REASON_NO_IMAGE = "no image"
REASON_GGUF_MISSING = "describe GGUF missing"
REASON_LLAMA_UNAVAILABLE = "llama.cpp vision unavailable"
REASON_EMPTY = "empty vision output"
REASON_PEOPLE_DROPPED = "caption people dropped (no person in still)"
REASON_MOOD_DROPPED = "caption guesswork dropped"
REASON_TRIMMED = "caption trimmed to the visible inventory"
REASON_GATE_EMPTY = "caption dropped (nothing grounded left)"
MAX_LONG_EDGE = 768
DEFAULT_MAX_TOKENS = 220
MAX_CAPTION_WORDS = 60
"""Word cap on caption text allowed to reach a prompt or a text encoder."""
PERSON_MASK_THRESHOLD = 0.5
"""Mask cell that counts as a person, matching the cubic erase convention."""

DESCRIBE_SYSTEM = (
    "Return only a caption of this still. No preface, no markdown, no wrapping "
    "quotes. Name visible inventory, lettering (spell it), colors, materials, "
    "and layout. SFW. No real-person names. Stay under 60 words. This caption "
    "is supporting context for a prompt rewriter, and the still itself stays "
    "the authority. Name people only when at least one person is clearly "
    "visible; when none is, do not mention people and do not invent a subject, "
    "a wardrobe, or a pose. Describe only what a viewer can see: no mood, "
    "atmosphere, story, or reasoning about why something is there. Omit an "
    "object you are unsure of instead of guessing."
)

_VISION: VisionModel | None = None
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


_PERSON_TERMS = (
    "man",
    "men",
    "woman",
    "women",
    "person",
    "persons",
    "people",
    "human",
    "humans",
    "humanoid",
    "individual",
    "individuals",
    "someone",
    "somebody",
    "anyone",
    "everyone",
    "guy",
    "guys",
    "boy",
    "boys",
    "girl",
    "girls",
    "child",
    "children",
    "kid",
    "kids",
    "baby",
    "babies",
    "toddler",
    "toddlers",
    "gentleman",
    "gentlemen",
    "gentlewoman",
    "lady",
    "ladies",
    "figure",
    "figures",
    "silhouette",
    "silhouettes",
    "crowd",
    "crowds",
    "audience",
    "pedestrian",
    "pedestrians",
    "passerby",
    "passersby",
    "passer-by",
    "passers-by",
    "subject",
    "subjects",
    "he",
    "him",
    "his",
    "she",
    "her",
    "hers",
    "they",
    "them",
    "their",
    "theirs",
)
"""Lexicon that marks a caption sentence as a claim about a person."""

_PERSON_TERM_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(term) for term in _PERSON_TERMS) + r")\b",
    re.IGNORECASE,
)
"""Compiled :data:`_PERSON_TERMS` word match."""

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
"""Split a caption into sentences without eating the terminator."""

_GUESS_RE = re.compile(
    r"\b(?:seems|seem|seemingly|appears|appear|looks like|looked like|likely|"
    r"possibly|probably|presumably|suggests|suggesting|perhaps|maybe|as if|"
    r"as though|imagine|imagined)\b",
    re.IGNORECASE,
)
"""Hedges: a hedged sentence is a guess, and a guess is not inventory."""

_MOOD_CLAUSE_RE = re.compile(
    r"[,;]?\s*\b(?:creating|creates|giving|gives|evoking|evokes|conveying|"
    r"conveys|adding|adds)\b[^.;]*?"
    r"\b(?:atmosphere|ambience|ambiance|mood|vibe|vibes|calm|serenity|"
    r"coziness|tension|nostalgia|feeling|feel)\b[^.;]*",
    re.IGNORECASE,
)
"""Atmosphere clause: prose about what a scene feels like is not visible."""


def has_person_claim(caption: object) -> bool:
    """True when ``caption`` asserts a person is in the still.

    Args:
        caption: Raw or gated caption text.

    Returns:
        Whether any :data:`_PERSON_TERMS` word appears.
    """
    text = str(caption or "").strip()
    if not text:
        return False
    return bool(_PERSON_TERM_RE.search(text))


def caption_without_people(caption: object) -> str:
    """Drop every sentence in ``caption`` that claims a person.

    Environment sentences survive. The check is a lexicon, so a sentence
    about a statue ("a bronze figure") or an art subject is dropped too: the
    gate errs toward keeping invented people out of the prompt.

    Args:
        caption: Raw caption text.

    Returns:
        Caption with person sentences removed, possibly empty.
    """
    text = str(caption or "").strip()
    if not text:
        return ""
    kept = [
        sentence.strip()
        for sentence in _SENTENCE_SPLIT_RE.split(text)
        if sentence.strip() and not _PERSON_TERM_RE.search(sentence)
    ]
    return " ".join(kept)


def still_has_people(image: ImageTensor | None) -> bool | None:
    """Ask the person mask whether ``image`` actually contains a person.

    Args:
        image: Comfy IMAGE tensor, or None.

    Returns:
        True when the mask lights up, False when it stays flat, and None when
        the segmenter cannot answer (off, no weights, no torch, bad tensor).
    """
    if image is None:
        return None
    try:
        from ez_image.person_mask import segment_people

        mask = segment_people(image)
    except Exception:  # noqa: BLE001 - hermetic tests, no torch, no ez_image
        return None
    if mask is None:
        return None
    try:
        return any(
            float(cell) >= PERSON_MASK_THRESHOLD for row in mask for cell in row
        )
    except (TypeError, ValueError):
        return None


def _strip_mood_prose(text: str) -> tuple[str, bool]:
    """Cut atmosphere clauses and hedged sentences out of a caption.

    Args:
        text: Caption without person sentences.

    Returns:
        ``(kept text, whether anything was cut)``.
    """
    kept: list[str] = []
    dropped = False
    for sentence in _SENTENCE_SPLIT_RE.split(text):
        item = sentence.strip()
        if not item:
            continue
        slimmed = re.sub(r"\s+([.!?])", r"\1", _MOOD_CLAUSE_RE.sub("", item)).strip()
        if slimmed != item:
            dropped = True
        if _GUESS_RE.search(slimmed):
            dropped = True
            continue
        if not slimmed.strip(" .!?"):
            continue
        kept.append(slimmed)
    return " ".join(kept), dropped


def _trim_caption(text: str) -> tuple[str, bool]:
    """Cap a caption so it cannot out-shout the operator instruction.

    Args:
        text: Gated caption.

    Returns:
        ``(caption, whether it was cut)``.
    """
    words = text.split()
    if len(words) <= MAX_CAPTION_WORDS:
        return text, False
    return " ".join(words[:MAX_CAPTION_WORDS]).rstrip(" ,;:.") + ".", True


def gate_caption(caption: object, image: ImageTensor | None = None) -> tuple[str, str]:
    """Filter a raw VLM caption down to what the still can actually support.

    The on-box 3B vision GGUF invents whole subjects at temperature 0, so the
    caption is an unverified claim rather than inventory. A sentence that
    names a person survives only when the person mask finds someone in the
    same still; a hedged sentence is a guess; atmosphere prose is not
    visible. What survives is word-capped before it can reach a prompt.

    Args:
        caption: Raw VLM caption.
        image: The still the caption came from, used for person grounding.

    Returns:
        ``(usable caption, reason)``; reason is empty when nothing was cut.
    """
    text = str(caption or "").strip()
    if not text:
        return "", ""
    reasons: list[str] = []
    if has_person_claim(text) and still_has_people(image) is not True:
        text = caption_without_people(text)
        reasons.append(REASON_PEOPLE_DROPPED)
    text, mood_cut = _strip_mood_prose(text)
    if mood_cut:
        reasons.append(REASON_MOOD_DROPPED)
    text, trimmed = _trim_caption(text)
    if trimmed:
        reasons.append(REASON_TRIMMED)
    if not text:
        return "", REASON_GATE_EMPTY
    return text, " + ".join(reasons)


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


def _image_to_png_b64(image: ImageTensor) -> str:
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
    except Exception:  # noqa: BLE001 - hermetic tests
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
    except Exception:  # noqa: BLE001 - fail-soft
        return ""


def _get_vision() -> tuple[VisionModel | None, str | None]:
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
        kwargs: dict[str, str | int | bool] = {
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
    user: list[dict[str, object]] = [
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


def describe_image(*, enable: object, image: ImageTensor | None = None) -> str:
    """Return a gated still caption, or empty when disabled / fail-soft.

    The raw VLM text passes through :func:`gate_caption` here, at the one
    place that still has the pixels, so every consumer of the caption
    (the CLIP trailer, the rewriter Image block, the negative lane) sees the
    same grounded string.

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
    safe, gate_reason = gate_caption(text, image)
    _LAST_STATUS = gate_reason
    return safe


def reset_describe_for_tests() -> None:
    """Drop the cached VLM handle (tests only)."""
    global _VISION, _VISION_PATH, _LAST_STATUS
    _VISION = None
    _VISION_PATH = ""
    _LAST_STATUS = REASON_DISABLED
