"""Unit tests for docker/pythonpath/sitecustomize.py lab Triton policy."""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pytest

PYTHONPATH_DIR = Path(__file__).resolve().parents[2] / "docker" / "pythonpath"


def _load_sitecustomize(monkeypatch: pytest.MonkeyPatch, env_value: str | None):
    """Load sitecustomize freshly with the given env flag."""
    if env_value is None:
        monkeypatch.delenv("LAB_DISABLE_TORCH_NATIVE_TRITON", raising=False)
    else:
        monkeypatch.setenv("LAB_DISABLE_TORCH_NATIVE_TRITON", env_value)

    # Ensure package path is first so we import our sitecustomize
    monkeypatch.syspath_prepend(str(PYTHONPATH_DIR))
    sys.modules.pop("sitecustomize", None)
    return importlib.import_module("sitecustomize")


def test_apply_noop_when_flag_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_sitecustomize(monkeypatch, None)
    # Should not raise; flag off means no torch import required for success path
    mod.apply_lab_torch_native_policy()


def test_apply_disables_triton_when_flag_set(monkeypatch: pytest.MonkeyPatch) -> None:
    class _TritonCtl:
        enabled = True

    pn = types.ModuleType("torch.backends.python_native")
    pn.triton = _TritonCtl()

    backends = types.ModuleType("torch.backends")
    backends.python_native = pn
    torch_mod = types.ModuleType("torch")
    torch_mod.backends = backends

    monkeypatch.setitem(sys.modules, "torch", torch_mod)
    monkeypatch.setitem(sys.modules, "torch.backends", backends)
    monkeypatch.setitem(sys.modules, "torch.backends.python_native", pn)

    mod = _load_sitecustomize(monkeypatch, "1")
    mod.apply_lab_torch_native_policy()
    assert pn.triton.enabled is False


def test_apply_ignores_missing_torch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "torch", None)  # force import failure path
    # Remove any real torch
    for name in list(sys.modules):
        if name == "torch" or name.startswith("torch."):
            sys.modules.pop(name, None)

    # Block import of torch
    import builtins

    real_import = builtins.__import__

    def _block_torch(name, *args, **kwargs):
        if name == "torch" or name.startswith("torch."):
            raise ImportError("blocked")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _block_torch)
    mod = _load_sitecustomize(monkeypatch, "1")
    mod.apply_lab_torch_native_policy()  # must not raise


def test_apply_noop_when_flag_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    class _TritonCtl:
        enabled = True

    pn = types.ModuleType("torch.backends.python_native")
    pn.triton = _TritonCtl()
    backends = types.ModuleType("torch.backends")
    backends.python_native = pn
    torch_mod = types.ModuleType("torch")
    torch_mod.backends = backends
    monkeypatch.setitem(sys.modules, "torch", torch_mod)
    monkeypatch.setitem(sys.modules, "torch.backends", backends)
    monkeypatch.setitem(sys.modules, "torch.backends.python_native", pn)

    mod = _load_sitecustomize(monkeypatch, "0")
    mod.apply_lab_torch_native_policy()
    assert pn.triton.enabled is True
