"""EZImageDescribe skips the VLM when the toggle is off."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_prompt_enhance import describe as desc  # noqa: E402
from ez_prompt_enhance.nodes import EZImageDescribe, EZKleinPromptEnhance  # noqa: E402
from ez_prompt_enhance import client  # noqa: E402


class _FakeArr:
    """Minimal array stand-in for hermetic encode tests (no numpy)."""

    def __init__(self, ndim: int, shape: tuple[int, ...]) -> None:
        self.ndim = ndim
        self.shape = shape

    def astype(self, _kind: str) -> "_FakeArr":
        return self

    def __mul__(self, _other: object) -> "_FakeArr":
        return self

    def __getitem__(self, index: int) -> "_FakeArr":
        if index == 0 and self.ndim == 4:
            return _FakeArr(self.ndim - 1, self.shape[1:])
        raise IndexError(index)


def _fake_numpy_module() -> types.ModuleType:
    """Return a numpy stub with asarray/clip."""

    mod = types.ModuleType("numpy")

    def asarray(value: object) -> _FakeArr:
        if isinstance(value, _FakeArr):
            return value
        if hasattr(value, "shape") and hasattr(value, "ndim"):
            shape = tuple(getattr(value, "shape"))
            return _FakeArr(int(getattr(value, "ndim")), shape)
        return _FakeArr(3, (8, 8, 3))

    def clip(array: _FakeArr, _lo: float, _hi: float) -> _FakeArr:
        return array

    mod.asarray = asarray  # type: ignore[attr-defined]
    mod.clip = clip  # type: ignore[attr-defined]
    return mod


def _fake_pil_module() -> tuple[types.ModuleType, types.ModuleType]:
    """Return (PIL, PIL.Image) stubs that write a tiny PNG payload."""

    pil = types.ModuleType("PIL")
    image_mod = types.ModuleType("PIL.Image")

    class _Image:
        def resize(self, size: tuple[int, int]) -> "_Image":
            del size
            return self

        def save(self, buf: Any, format: str = "PNG") -> None:
            del format
            buf.write(b"png-bytes")

    def fromarray(_pixels: object) -> _Image:
        return _Image()

    image_mod.fromarray = fromarray  # type: ignore[attr-defined]
    pil.Image = image_mod  # type: ignore[attr-defined]
    return pil, image_mod


def test_describe_enable_off_does_not_call_vision() -> None:
    desc.reset_describe_for_tests()
    with patch.object(desc, "_vision_complete", return_value=("caption", None)) as mock:
        text = desc.describe_image(enable=False, image=object())
    assert text == ""
    assert desc.last_status() == desc.REASON_DISABLED
    mock.assert_not_called()
    node = EZImageDescribe()
    packed = node.run(False, object())
    assert packed["result"] == ("",)
    assert packed["ui"]["passthrough"][0] == desc.REASON_DISABLED
    assert node.check_lazy_status(False, None) == []
    assert node.check_lazy_status(True, None) == ["image"]
    spec = node.INPUT_TYPES()
    assert spec["required"]["enable"][1]["default"] is False


def test_describe_enable_on_uses_backend() -> None:
    desc.reset_describe_for_tests()
    with patch.object(desc, "_image_to_png_b64", return_value="abc"):
        with patch.object(
            desc, "_vision_complete", return_value=("a red mug on a teak desk", None)
        ) as mock:
            text = desc.describe_image(enable=True, image=object())
    assert text == "a red mug on a teak desk"
    mock.assert_called_once()
    assert desc.last_status() == ""
    with patch.object(desc, "_image_to_png_b64", return_value="abc"):
        with patch.object(desc, "_vision_complete", return_value=("", None)):
            assert desc.describe_image(enable=True, image=object()) == ""
            assert desc.last_status() == desc.REASON_EMPTY


def test_describe_paths_fail_soft(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    desc.reset_describe_for_tests()
    assert desc.describe_image(enable=True, image=None) == ""
    assert desc.last_status() == desc.REASON_NO_IMAGE
    with patch.object(desc, "_image_to_png_b64", return_value=""):
        assert desc.describe_image(enable=True, image=object()) == ""
    assert desc.describe_gguf_path().endswith(desc.DESCRIBE_GGUF)
    monkeypatch.setenv("EZ_DESCRIBE_GGUF", str(tmp_path / "a.gguf"))
    monkeypatch.setenv("EZ_DESCRIBE_MMPROJ", str(tmp_path / "b.gguf"))
    assert desc.describe_gguf_path().endswith("a.gguf")
    assert desc.describe_mmproj_path().endswith("b.gguf")
    assert desc._gguf_ready() is False
    (tmp_path / "a.gguf").write_bytes(b"gguf")
    (tmp_path / "b.gguf").write_bytes(b"proj")
    assert desc._gguf_ready() is True
    with patch.dict("sys.modules", {"llama_cpp": None}):
        llm, reason = desc._get_vision()
    assert llm is None
    assert reason == desc.REASON_LLAMA_UNAVAILABLE
    with patch.object(desc, "_get_vision", return_value=(None, desc.REASON_GGUF_MISSING)):
        text, reason = desc._vision_complete("abc")
    assert text == ""
    assert reason == desc.REASON_GGUF_MISSING

    class _FakeLlama:
        def create_chat_completion(self, **kwargs: object) -> dict[str, object]:
            del kwargs
            return {"choices": [{"message": {"content": "  a caption  "}}]}

    with patch.object(desc, "_get_vision", return_value=(_FakeLlama(), None)):
        text, reason = desc._vision_complete("abc")
    assert text == "a caption"
    assert reason is None

    class _Boom:
        def create_chat_completion(self, **kwargs: object) -> dict[str, object]:
            del kwargs
            raise RuntimeError("nope")

    with patch.object(desc, "_get_vision", return_value=(_Boom(), None)):
        text, reason = desc._vision_complete("abc")
    assert text == ""
    assert reason == desc.REASON_EMPTY
    assert desc.describe_image(enable="yes", image=None) == ""
    png = desc._image_to_png_b64(object())
    assert png == ""
    assert desc.describe_image(enable=1, image=None) == ""
    assert desc.describe_image(enable=object(), image=None) == ""
    desc._log("coverage")
    with patch.object(desc.os.path, "getsize", side_effect=OSError("stat")):
        assert desc._gguf_ready() is False

    class _Arr:
        def __init__(self, ndim: int) -> None:
            self.ndim = ndim
            self.shape = (4, 4, 3) if ndim == 3 else (1, 4, 4, 3)

        def astype(self, _kind: str) -> "_Arr":
            return self

    class _NP:
        @staticmethod
        def asarray(value: object) -> _Arr:
            del value
            return _Arr(2)

        @staticmethod
        def clip(array: _Arr, _a: float, _b: float) -> _Arr:
            return array

    with patch.dict("sys.modules", {"numpy": _NP}):
        assert desc._image_to_png_b64(object()) == ""

    class _BoomLlama:
        def __init__(self, **kwargs: object) -> None:
            raise RuntimeError("load")

    fake_boom = types.SimpleNamespace(Llama=_BoomLlama)
    desc.reset_describe_for_tests()
    with patch.dict("sys.modules", {"llama_cpp": fake_boom}):
        with patch.object(desc, "_gguf_ready", return_value=True):
            llm, reason = desc._get_vision()
    assert llm is None
    assert reason == desc.REASON_LLAMA_UNAVAILABLE

    class _EmptyContent:
        def create_chat_completion(self, **kwargs: object) -> dict[str, object]:
            del kwargs
            return {"choices": [{"message": {"content": "   "}}]}

    with patch.object(desc, "_get_vision", return_value=(_EmptyContent(), None)):
        text, reason = desc._vision_complete("abc")
    assert text == ""
    assert reason == desc.REASON_EMPTY

    with patch.object(desc, "_get_vision", return_value=(None, None)):
        text, reason = desc._vision_complete("abc")
    assert reason == desc.REASON_LLAMA_UNAVAILABLE

    class _OkLlama:
        def __init__(self, **kwargs: object) -> None:
            del kwargs

        def create_chat_completion(self, **kwargs: object) -> dict[str, object]:
            del kwargs
            return {"choices": [{"message": {"content": "ok"}}]}

    fake_mod = types.SimpleNamespace(Llama=_OkLlama)
    desc.reset_describe_for_tests()
    with patch.dict("sys.modules", {"llama_cpp": fake_mod}):
        with patch.object(desc, "_gguf_ready", return_value=True):
            llm, reason = desc._get_vision()
    assert llm is not None
    assert reason is None

    class _TypeLlama:
        def __init__(self, **kwargs: object) -> None:
            if "clip_model_path" in kwargs:
                raise TypeError("no clip")

    fake_mod2 = types.SimpleNamespace(Llama=_TypeLlama)
    desc.reset_describe_for_tests()
    with patch.dict("sys.modules", {"llama_cpp": fake_mod2}):
        with patch.object(desc, "_gguf_ready", return_value=True):
            llm, reason = desc._get_vision()
    assert llm is not None
    assert reason is None

    class _TypeThenBoom:
        def __init__(self, **kwargs: object) -> None:
            if "clip_model_path" in kwargs:
                raise TypeError("no clip")
            raise RuntimeError("still no")

    desc.reset_describe_for_tests()
    fake_boom_clip = types.SimpleNamespace(Llama=_TypeThenBoom)
    with patch.dict("sys.modules", {"llama_cpp": fake_boom_clip}):
        with patch.object(desc, "_gguf_ready", return_value=True):
            llm, reason = desc._get_vision()
    assert llm is None
    assert reason == desc.REASON_LLAMA_UNAVAILABLE

    cached = object()
    desc._VISION = cached
    desc._VISION_PATH = desc.describe_gguf_path()
    with patch.object(desc, "_gguf_ready", return_value=True):
        llm, reason = desc._get_vision()
    assert llm is cached
    assert reason is None

    class _BadBody:
        def create_chat_completion(self, **kwargs: object) -> dict[str, object]:
            del kwargs
            return {}

    with patch.object(desc, "_get_vision", return_value=(_BadBody(), None)):
        text, reason = desc._vision_complete("abc")
    assert text == ""
    assert reason == desc.REASON_EMPTY


def test_describe_image_encode_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    desc.reset_describe_for_tests()
    monkeypatch.delenv("EZ_DESCRIBE_GGUF", raising=False)
    monkeypatch.delenv("EZ_DESCRIBE_MMPROJ", raising=False)
    llm, reason = desc._get_vision()
    assert llm is None
    assert reason == desc.REASON_GGUF_MISSING
    import builtins

    real_import = builtins.__import__

    def _no_numpy(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "numpy":
            raise ImportError("no numpy")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _no_numpy)
    assert desc._image_to_png_b64(object()) == ""
    monkeypatch.setattr(builtins, "__import__", real_import)

    np_mod = _fake_numpy_module()
    monkeypatch.setitem(sys.modules, "numpy", np_mod)

    def _no_pil(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "PIL" or name.startswith("PIL."):
            raise ImportError("no pil")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _no_pil)
    assert desc._image_to_png_b64(_FakeArr(3, (8, 8, 3))) == ""
    assert desc._image_to_png_b64(_FakeArr(3, (1024, 1024, 3))) == ""
    monkeypatch.setattr(builtins, "__import__", real_import)

    pil, pil_image = _fake_pil_module()
    monkeypatch.setitem(sys.modules, "PIL", pil)
    monkeypatch.setitem(sys.modules, "PIL.Image", pil_image)

    class _Tensor:
        def detach(self) -> "_Tensor":
            return self

        def cpu(self) -> "_Tensor":
            return self

        def numpy(self) -> _FakeArr:
            return _FakeArr(3, (8, 8, 3))

    png = desc._image_to_png_b64(_Tensor())
    assert png
    batch = _FakeArr(4, (1, 32, 32, 3))
    assert desc._image_to_png_b64(batch)
    big = _FakeArr(3, (1024, 1024, 3))
    assert desc._image_to_png_b64(big)

    def _boom_asarray(value: object) -> _FakeArr:
        del value
        raise RuntimeError("bad tensor")

    monkeypatch.setattr(np_mod, "asarray", _boom_asarray, raising=False)
    assert desc._image_to_png_b64(object()) == ""


def test_enhance_splices_image_desc_into_context() -> None:
    klein = EZKleinPromptEnhance()
    with patch.object(client, "complete", return_value=("rewritten", None)) as mock:
        klein.run(
            "keep the mug",
            True,
            "edit",
            "",
            "none",
            "",
            "custom",
            "",
            "unmarked ceramic mug, teal rim light",
        )
    user = mock.call_args[0][1]
    assert "Image caption (unverified):" in user
    assert "unmarked ceramic mug" in user
    optional = EZKleinPromptEnhance.INPUT_TYPES()["optional"]
    assert "image_desc" in optional


# The real 3B GGUF output that motivated the gate: a whole invented subject on
# a still that holds no person, plus an atmosphere clause nobody can see.
HALLUCINATED_PEOPLE = (
    "A young woman in a vibrant red dress sits gracefully on a bench, her "
    "hands gently resting on her lap. The background features a serene garden "
    "with lush greenery and blooming flowers, creating a peaceful and "
    "contemplative atmosphere."
)
GARDEN_INVENTORY_ONLY = (
    "The background features a serene garden with lush greenery and blooming "
    "flowers."
)


def _stub_person_mask(monkeypatch: pytest.MonkeyPatch, mask: Any) -> None:
    """Point the person segmenter at a fixed mask.

    Args:
        monkeypatch: Pytest attr helper.
        mask: Value ``segment_people`` should answer for any still.
    """
    monkeypatch.setattr("ez_image.person_mask.segment_people", lambda _image: mask)


def test_gate_drops_invented_people_from_an_ungrounded_still(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A caption nobody can ground loses its subject and its mood prose.

    Args:
        monkeypatch: Pytest attr helper.
    """
    _stub_person_mask(monkeypatch, [[0.0, 0.0]])
    caption, reason = desc.gate_caption(HALLUCINATED_PEOPLE, object())
    assert caption == GARDEN_INVENTORY_ONLY
    assert desc.REASON_PEOPLE_DROPPED in reason
    assert desc.REASON_MOOD_DROPPED in reason
    assert desc.REASON_TRIMMED not in reason
    assert reason == f"{desc.REASON_PEOPLE_DROPPED} + {desc.REASON_MOOD_DROPPED}"
    assert "woman" not in caption.casefold()
    assert "red dress" not in caption.casefold()
    assert "atmosphere" not in caption.casefold()
    # No pixels at all is an unanswerable mask, which gates the same way.
    assert desc.gate_caption(HALLUCINATED_PEOPLE) == (caption, reason)


def test_gate_keeps_the_person_when_the_mask_grounds_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A lit person mask vouches for the sentence that names them.

    Args:
        monkeypatch: Pytest attr helper.
    """
    _stub_person_mask(monkeypatch, [[0.9, 0.1]])
    caption, reason = desc.gate_caption(HALLUCINATED_PEOPLE, object())
    assert "A young woman in a vibrant red dress sits gracefully on a bench" in caption
    assert "her hands gently resting on her lap" in caption
    assert caption.endswith(GARDEN_INVENTORY_ONLY)
    assert reason == desc.REASON_MOOD_DROPPED
    assert desc.REASON_PEOPLE_DROPPED not in reason


def test_has_person_claim_matches_the_person_lexicon() -> None:
    """The lexicon fires on people words and stays quiet on inventory."""
    assert desc.has_person_claim("A young woman sits on a bench.") is True
    assert desc.has_person_claim("someone, a crowd, a silhouette") is True
    assert desc.has_person_claim("a red mug on a teak desk") is False
    assert desc.has_person_claim("the featured tile figure") is True
    assert desc.has_person_claim(["a woman on a bench"]) is True
    assert desc.has_person_claim(42) is False
    assert desc.has_person_claim(None) is False
    assert desc.has_person_claim("   ") is False
    assert desc.has_person_claim(object()) is False


def test_caption_without_people_keeps_environment_sentences() -> None:
    """Only the sentences that name a person are cut.

    Returns:
        None.
    """
    kept = desc.caption_without_people(
        "A young woman sits on a bench. The plaza holds a stone fountain. "
        "She wears a red dress."
    )
    assert kept == "The plaza holds a stone fountain."
    assert desc.caption_without_people("A young woman sits on a bench.") == ""
    assert desc.caption_without_people("") == ""
    assert desc.caption_without_people(None) == ""
    assert desc.caption_without_people("   ") == ""


def test_still_has_people_answers_true_flat_and_unanswerable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The mask answers True, False, or nothing at all.

    Args:
        monkeypatch: Pytest attr helper.
    """
    assert desc.still_has_people(None) is None
    _stub_person_mask(monkeypatch, [[0.9, 0.1]])
    assert desc.still_has_people(object()) is True
    _stub_person_mask(monkeypatch, [[desc.PERSON_MASK_THRESHOLD]])
    assert desc.still_has_people(object()) is True
    _stub_person_mask(monkeypatch, [[desc.PERSON_MASK_THRESHOLD - 0.01, 0.0]])
    assert desc.still_has_people(object()) is False
    _stub_person_mask(monkeypatch, [[0.0] * 8 for _ in range(8)])
    assert desc.still_has_people(object()) is False
    _stub_person_mask(monkeypatch, None)
    assert desc.still_has_people(object()) is None
    _stub_person_mask(monkeypatch, [["bright"]])
    assert desc.still_has_people(object()) is None
    _stub_person_mask(monkeypatch, [[None]])
    assert desc.still_has_people(object()) is None
    _stub_person_mask(monkeypatch, [0.9])
    assert desc.still_has_people(object()) is None

    def _boom(_image: Any) -> None:
        raise RuntimeError("segmenter exploded")

    monkeypatch.setattr("ez_image.person_mask.segment_people", _boom)
    assert desc.still_has_people(object()) is None
    with patch.dict("sys.modules", {"ez_image.person_mask": None}):
        assert desc.still_has_people(object()) is None


def test_strip_mood_prose_cuts_atmosphere_and_hedges() -> None:
    """Atmosphere clauses and hedged sentences are not inventory."""
    kept, dropped = desc._strip_mood_prose(
        "A red mug sits on the table, giving the scene a cozy mood."
    )
    assert kept == "A red mug sits on the table."
    assert dropped is True

    kept, dropped = desc._strip_mood_prose(
        "There appears to be a bench. A red mug sits on the table."
    )
    assert kept == "A red mug sits on the table."
    assert dropped is True

    kept, dropped = desc._strip_mood_prose(
        "Creating a peaceful atmosphere. A red mug sits on the table."
    )
    assert kept == "A red mug sits on the table."
    assert dropped is True

    kept, dropped = desc._strip_mood_prose("a red mug on a teak desk")
    assert kept == "a red mug on a teak desk"
    assert dropped is False

    kept, dropped = desc._strip_mood_prose("   ")
    assert kept == ""
    assert dropped is False


def test_trim_caption_caps_the_word_count() -> None:
    """A long caption is cut at the cap and closed with a period."""
    short = "a red mug on a teak desk"
    assert desc._trim_caption(short) == (short, False)

    at_cap = " ".join(f"tile{i}" for i in range(desc.MAX_CAPTION_WORDS))
    assert desc._trim_caption(at_cap) == (at_cap, False)

    over = " ".join(f"tile{i}" for i in range(desc.MAX_CAPTION_WORDS + 12))
    trimmed, was_trimmed = desc._trim_caption(over)
    assert was_trimmed is True
    assert len(trimmed.split()) == desc.MAX_CAPTION_WORDS
    assert trimmed.startswith("tile0 ")
    assert trimmed.endswith("tile59.")


def test_gate_joins_reasons_in_people_mood_trim_order() -> None:
    """Every cut is reported once, in people, mood, trim order."""
    clean = "a red mug on a teak desk beside an open notebook"
    assert desc.gate_caption(clean) == (clean, "")

    filler = " ".join(f"brick{i}" for i in range(desc.MAX_CAPTION_WORDS + 10))
    combo = (
        "A young woman in a red dress sits on a bench. The stone plaza "
        f"stretches wide with {filler}, creating a solemn and quiet mood."
    )
    caption, reason = desc.gate_caption(combo)
    assert reason == " + ".join(
        (desc.REASON_PEOPLE_DROPPED, desc.REASON_MOOD_DROPPED, desc.REASON_TRIMMED)
    )
    assert len(caption.split()) == desc.MAX_CAPTION_WORDS
    assert caption.endswith(".")
    assert "woman" not in caption.casefold()
    assert "mood" not in caption.casefold()

    over = " ".join(f"tile{i}" for i in range(desc.MAX_CAPTION_WORDS + 3))
    assert desc.gate_caption(over) == (
        " ".join(f"tile{i}" for i in range(desc.MAX_CAPTION_WORDS)) + ".",
        desc.REASON_TRIMMED,
    )


def test_gate_drops_a_caption_with_nothing_grounded_left() -> None:
    """A caption that gates down to nothing never reaches a prompt."""
    assert desc.gate_caption("A young woman in a red dress sits on a bench.") == (
        "",
        desc.REASON_GATE_EMPTY,
    )
    assert desc.gate_caption("It looks like it might be raining, perhaps.") == (
        "",
        desc.REASON_GATE_EMPTY,
    )
    assert desc.gate_caption("Creating a peaceful atmosphere.") == (
        "",
        desc.REASON_GATE_EMPTY,
    )
    assert desc.gate_caption("") == ("", "")
    assert desc.gate_caption(None) == ("", "")


def test_describe_image_surfaces_the_gate_reason_in_last_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The gated caption and its reason are what callers see.

    Args:
        monkeypatch: Pytest attr helper.
    """
    _stub_person_mask(monkeypatch, [[0.0, 0.0]])
    desc.reset_describe_for_tests()
    with patch.object(desc, "_image_to_png_b64", return_value="abc"):
        with patch.object(
            desc, "_vision_complete", return_value=(HALLUCINATED_PEOPLE, None)
        ):
            text = desc.describe_image(enable=True, image=object())
    assert text == GARDEN_INVENTORY_ONLY
    assert desc.last_status() == (
        f"{desc.REASON_PEOPLE_DROPPED} + {desc.REASON_MOOD_DROPPED}"
    )

    desc.reset_describe_for_tests()
    with patch.object(desc, "_image_to_png_b64", return_value="abc"):
        with patch.object(
            desc, "_vision_complete", return_value=("a red mug on a teak desk", None)
        ):
            text = desc.describe_image(enable=True, image=object())
    assert text == "a red mug on a teak desk"
    assert desc.last_status() == ""

    desc.reset_describe_for_tests()
    with patch.object(desc, "_image_to_png_b64", return_value="abc"):
        with patch.object(
            desc,
            "_vision_complete",
            return_value=("A young woman in a red dress sits on a bench.", None),
        ):
            text = desc.describe_image(enable=True, image=object())
    assert text == ""
    assert desc.last_status() == desc.REASON_GATE_EMPTY
