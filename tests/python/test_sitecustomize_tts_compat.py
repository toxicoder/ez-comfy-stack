"""Unit tests for sitecustomize TTS deprecation shims (no GPU, no Chatterbox)."""

from __future__ import annotations

import contextlib
import importlib
import sys
import types
import warnings
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

PYTHONPATH_DIR = Path(__file__).resolve().parents[2] / "docker" / "pythonpath"


def _drop_lab_finders() -> None:
    """Remove lab TTS compat finders left by a prior sitecustomize import."""
    sys.meta_path[:] = [
        finder
        for finder in sys.meta_path
        if not getattr(finder, "_lab_tts_compat", False)
    ]


def _load_sitecustomize(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    """Load sitecustomize freshly with Triton policy off."""
    monkeypatch.delenv("LAB_DISABLE_TORCH_NATIVE_TRITON", raising=False)
    monkeypatch.syspath_prepend(str(PYTHONPATH_DIR))
    _drop_lab_finders()
    sys.modules.pop("sitecustomize", None)
    return importlib.import_module("sitecustomize")


class _SDPBackend:
    FLASH_ATTENTION = "flash"
    EFFICIENT_ATTENTION = "efficient"
    MATH = "math"
    CUDNN_ATTENTION = "cudnn"


def _install_fake_attention(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[types.ModuleType, list[object]]:
    """Install fake torch.nn.attention that records sdpa_kernel backends."""
    seen: list[object] = []

    @contextlib.contextmanager
    def sdpa_kernel(backends: Any, set_priority: bool = False) -> Iterator[str]:
        del set_priority
        seen.append(list(backends))
        yield "ok"

    attn = types.ModuleType("torch.nn.attention")
    attn.SDPBackend = _SDPBackend  # type: ignore[attr-defined]
    attn.sdpa_kernel = sdpa_kernel  # type: ignore[attr-defined]
    nn_mod = types.ModuleType("torch.nn")
    nn_mod.attention = attn  # type: ignore[attr-defined]
    nn_mod.Linear = type("Linear", (), {})  # type: ignore[attr-defined]
    torch_mod = types.ModuleType("torch")
    torch_mod.nn = nn_mod  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "torch", torch_mod)
    monkeypatch.setitem(sys.modules, "torch.nn", nn_mod)
    monkeypatch.setitem(sys.modules, "torch.nn.attention", attn)
    return attn, seen


def test_load_does_not_import_torch(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(sys.modules):
        if name == "torch" or name.startswith("torch."):
            sys.modules.pop(name, None)
    mod = _load_sitecustomize(monkeypatch)
    assert "torch" not in sys.modules
    assert callable(mod.apply_lab_sdp_kernel_shim)
    assert callable(mod.apply_lab_lora_linear_shim)


def test_sdp_shim_maps_flags_and_skips_deprecated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _attn, seen = _install_fake_attention(monkeypatch)
    cuda = types.ModuleType("torch.backends.cuda")

    def _deprecated_sdp_kernel(**_kwargs: object) -> None:
        warnings.warn(
            "`torch.backends.cuda.sdp_kernel()` is deprecated.",
            FutureWarning,
            stacklevel=1,
        )

    cuda.sdp_kernel = _deprecated_sdp_kernel  # type: ignore[attr-defined]
    mod = _load_sitecustomize(monkeypatch)
    mod.apply_lab_sdp_kernel_shim(cuda)
    shim = getattr(cuda, "sdp_kernel")
    assert getattr(shim, "_lab_sdpa_shim", False)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with shim(
            enable_flash=True,
            enable_math=False,
            enable_mem_efficient=True,
            enable_cudnn=False,
        ) as ctx:
            assert ctx == "ok"
    assert seen == [[_SDPBackend.FLASH_ATTENTION, _SDPBackend.EFFICIENT_ATTENTION]]
    assert not any(item.category is FutureWarning for item in caught)


def test_sdp_shim_skips_missing_backend_member(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _PartialBackend:
        FLASH_ATTENTION = "flash"
        EFFICIENT_ATTENTION = "efficient"
        MATH = "math"

    seen: list[object] = []

    @contextlib.contextmanager
    def sdpa_kernel(backends: Any, set_priority: bool = False) -> Iterator[None]:
        del set_priority
        seen.append(backends)
        yield None

    attn = types.ModuleType("torch.nn.attention")
    attn.SDPBackend = _PartialBackend  # type: ignore[attr-defined]
    attn.sdpa_kernel = sdpa_kernel  # type: ignore[attr-defined]
    nn_mod = types.ModuleType("torch.nn")
    nn_mod.attention = attn  # type: ignore[attr-defined]
    torch_mod = types.ModuleType("torch")
    torch_mod.nn = nn_mod  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "torch", torch_mod)
    monkeypatch.setitem(sys.modules, "torch.nn", nn_mod)
    monkeypatch.setitem(sys.modules, "torch.nn.attention", attn)
    cuda = types.ModuleType("torch.backends.cuda")
    cuda.sdp_kernel = lambda **_k: None  # type: ignore[attr-defined]
    mod = _load_sitecustomize(monkeypatch)
    mod.apply_lab_sdp_kernel_shim(cuda)
    with getattr(cuda, "sdp_kernel")():
        pass
    assert seen == [
        [
            _PartialBackend.FLASH_ATTENTION,
            _PartialBackend.EFFICIENT_ATTENTION,
            _PartialBackend.MATH,
        ]
    ]


def test_sdp_shim_noop_when_sdpa_kernel_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attn = types.ModuleType("torch.nn.attention")
    attn.SDPBackend = _SDPBackend  # type: ignore[attr-defined]
    nn_mod = types.ModuleType("torch.nn")
    nn_mod.attention = attn  # type: ignore[attr-defined]
    torch_mod = types.ModuleType("torch")
    torch_mod.nn = nn_mod  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "torch", torch_mod)
    monkeypatch.setitem(sys.modules, "torch.nn", nn_mod)
    monkeypatch.setitem(sys.modules, "torch.nn.attention", attn)
    cuda = types.ModuleType("torch.backends.cuda")

    def _stock() -> None:
        return None

    cuda.sdp_kernel = _stock  # type: ignore[attr-defined]
    mod = _load_sitecustomize(monkeypatch)
    mod.apply_lab_sdp_kernel_shim(cuda)
    assert cuda.sdp_kernel is _stock


def test_sdp_shim_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_attention(monkeypatch)
    cuda = types.ModuleType("torch.backends.cuda")
    cuda.sdp_kernel = lambda **_k: None  # type: ignore[attr-defined]
    mod = _load_sitecustomize(monkeypatch)
    mod.apply_lab_sdp_kernel_shim(cuda)
    first = cuda.sdp_kernel
    mod.apply_lab_sdp_kernel_shim(cuda)
    assert cuda.sdp_kernel is first


def test_sdp_shim_reads_sys_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_attention(monkeypatch)
    cuda = types.ModuleType("torch.backends.cuda")
    cuda.sdp_kernel = lambda **_k: None  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "torch.backends.cuda", cuda)
    mod = _load_sitecustomize(monkeypatch)
    mod.apply_lab_sdp_kernel_shim()
    assert getattr(cuda.sdp_kernel, "_lab_sdpa_shim", False)


def test_sdp_shim_noop_when_cuda_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    sys.modules.pop("torch.backends.cuda", None)
    mod = _load_sitecustomize(monkeypatch)
    mod.apply_lab_sdp_kernel_shim()


def test_lora_shim_replaces_compatible_linear(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Linear:
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.args = args
            self.kwargs = kwargs

    class LoRACompatibleLinear:
        def __init__(self, *args: object, **kwargs: object) -> None:
            warnings.warn("LoRACompatibleLinear is deprecated", FutureWarning)

    class LoRACompatibleConv:
        pass

    nn_mod = types.ModuleType("torch.nn")
    nn_mod.Linear = Linear  # type: ignore[attr-defined]
    torch_mod = types.ModuleType("torch")
    torch_mod.nn = nn_mod  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "torch", torch_mod)
    monkeypatch.setitem(sys.modules, "torch.nn", nn_mod)
    lora = types.ModuleType("diffusers.models.lora")
    lora.LoRACompatibleLinear = LoRACompatibleLinear  # type: ignore[attr-defined]
    lora.LoRACompatibleConv = LoRACompatibleConv  # type: ignore[attr-defined]
    mod = _load_sitecustomize(monkeypatch)
    mod.apply_lab_lora_linear_shim(lora)
    assert lora.LoRACompatibleLinear is Linear
    assert lora.LoRACompatibleConv is LoRACompatibleConv
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        lora.LoRACompatibleLinear(4, 4)
    assert not any(item.category is FutureWarning for item in caught)


def test_lora_shim_reads_sys_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    class Linear:
        pass

    nn_mod = types.ModuleType("torch.nn")
    nn_mod.Linear = Linear  # type: ignore[attr-defined]
    torch_mod = types.ModuleType("torch")
    torch_mod.nn = nn_mod  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "torch", torch_mod)
    monkeypatch.setitem(sys.modules, "torch.nn", nn_mod)
    lora = types.ModuleType("diffusers.models.lora")
    lora.LoRACompatibleLinear = object  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "diffusers.models.lora", lora)
    mod = _load_sitecustomize(monkeypatch)
    mod.apply_lab_lora_linear_shim()
    assert lora.LoRACompatibleLinear is Linear


def test_lora_shim_noop_without_torch(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(sys.modules):
        if name == "torch" or name.startswith("torch."):
            sys.modules.pop(name, None)

    import builtins

    real_import = builtins.__import__

    def _block_torch(name, *args, **kwargs):
        if name == "torch" or name.startswith("torch."):
            raise ImportError("blocked")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _block_torch)
    lora = types.ModuleType("diffusers.models.lora")
    sentinel = object()
    lora.LoRACompatibleLinear = sentinel  # type: ignore[attr-defined]
    mod = _load_sitecustomize(monkeypatch)
    mod.apply_lab_lora_linear_shim(lora)
    assert lora.LoRACompatibleLinear is sentinel


def test_register_applies_already_imported_modules(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_attention(monkeypatch)
    cuda = types.ModuleType("torch.backends.cuda")
    cuda.sdp_kernel = lambda **_k: None  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "torch.backends.cuda", cuda)

    class Linear:
        pass

    nn_mod = sys.modules["torch.nn"]
    nn_mod.Linear = Linear  # type: ignore[attr-defined]
    lora = types.ModuleType("diffusers.models.lora")
    lora.LoRACompatibleLinear = object  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "diffusers.models.lora", lora)
    mod = _load_sitecustomize(monkeypatch)
    # Import already registered hooks; calling again must still shim preloaded mods.
    mod.register_lab_tts_compat_hooks()
    assert getattr(cuda.sdp_kernel, "_lab_sdpa_shim", False)
    assert lora.LoRACompatibleLinear is Linear
