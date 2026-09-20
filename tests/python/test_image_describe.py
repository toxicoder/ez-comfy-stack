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
    assert llm is not None or reason == desc.REASON_LLAMA_UNAVAILABLE

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
    np = pytest.importorskip("numpy")

    class _Tensor:
        def detach(self) -> "_Tensor":
            return self

        def cpu(self) -> "_Tensor":
            return self

        def numpy(self) -> object:
            return np.zeros((8, 8, 3), dtype="float32")

    png = desc._image_to_png_b64(_Tensor())
    assert png
    import builtins

    real_import = builtins.__import__

    def _no_numpy(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "numpy":
            raise ImportError("no numpy")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _no_numpy)
    assert desc._image_to_png_b64(object()) == ""
    monkeypatch.setattr(builtins, "__import__", real_import)

    def _no_pil(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "PIL" or name.startswith("PIL."):
            raise ImportError("no pil")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _no_pil)
    small = np.zeros((1, 8, 8, 3), dtype="float32")
    assert desc._image_to_png_b64(small) == ""
    big = np.zeros((1, 1024, 1024, 3), dtype="float32")
    assert desc._image_to_png_b64(big) == ""
    monkeypatch.setattr(builtins, "__import__", real_import)
    with patch.object(np, "asarray", side_effect=RuntimeError("bad tensor")):
        assert desc._image_to_png_b64(object()) == ""


def test_describe_image_png_roundtrip_and_empty_vision() -> None:
    desc.reset_describe_for_tests()
    np = pytest.importorskip("numpy")
    batch = np.zeros((1, 32, 32, 3), dtype="float32")
    batch[0, 0, 0] = 1.0
    png = desc._image_to_png_b64(batch)
    assert isinstance(png, str)
    assert len(png) > 20
    big = np.zeros((1, 1024, 1024, 3), dtype="float32")
    png_big = desc._image_to_png_b64(big)
    assert isinstance(png_big, str)
    with patch.object(desc, "_image_to_png_b64", return_value="abc"):
        with patch.object(desc, "_vision_complete", return_value=("", desc.REASON_EMPTY)):
            assert desc.describe_image(enable=True, image=object()) == ""
            assert desc.last_status() == desc.REASON_EMPTY
    cached = object()
    desc._VISION = cached
    desc._VISION_PATH = desc.describe_gguf_path()
    with patch.object(desc, "_gguf_ready", return_value=True):
        llm, reason = desc._get_vision()
    assert llm is cached
    assert reason is None

    class _TypeThenBoom:
        def __init__(self, **kwargs: object) -> None:
            if "clip_model_path" in kwargs:
                raise TypeError("no clip")
            raise RuntimeError("still no")

    desc.reset_describe_for_tests()
    fake = types.SimpleNamespace(Llama=_TypeThenBoom)
    with patch.dict("sys.modules", {"llama_cpp": fake}):
        with patch.object(desc, "_gguf_ready", return_value=True):
            llm, reason = desc._get_vision()
    assert llm is None
    assert reason == desc.REASON_LLAMA_UNAVAILABLE


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
    assert "Image:" in user
    assert "unmarked ceramic mug" in user
    optional = EZKleinPromptEnhance.INPUT_TYPES()["optional"]
    assert "image_desc" in optional
