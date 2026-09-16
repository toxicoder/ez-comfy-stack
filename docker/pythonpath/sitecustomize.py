"""Lab sitecustomize: Triton policy plus Chatterbox TTS deprecation shims.

Activated when the entrypoint prepends ``/opt/ez-comfy/pythonpath`` to
``PYTHONPATH``.

Triton
------
When ``LAB_DISABLE_TORCH_NATIVE_TRITON=1``, turns off
``torch.backends.python_native.triton`` so ops such as ``bmm_outer_product``
(used during CLIP / Gemma RoPE) fall back to eager/cuBLAS instead of
JIT-compiling Triton's ``cuda_utils`` helper. Escape hatch when
gcc/Python.h/libcuda link env is incomplete.

TTS (ez_dub Chatterbox clone)
-----------------------------
Lazy import hooks (no eager torch import):

* ``torch.backends.cuda.sdp_kernel`` → ``torch.nn.attention.sdpa_kernel``
  with the same enable_* mapping torch 2.14 uses internally, minus the
  ``FutureWarning``.
* ``diffusers.models.lora.LoRACompatibleLinear`` → ``torch.nn.Linear`` so
  Chatterbox Matcha ``FeedForward`` / ``SnakeBeta`` do not construct the
  class deprecated in diffusers 1.0. Does **not** install PEFT (that would
  flip ``USE_PEFT_BACKEND`` for Comfy LoRAs).

No-op when torch / diffusers / ``sdpa_kernel`` is unavailable.
"""

from __future__ import annotations

import contextlib
import os
import sys
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager
from typing import Any, cast

# (sdp_kernel kwarg, SDPBackend enum name) pairs for the torch 2.14 mapping.
_SDP_BACKEND_FLAGS: tuple[tuple[str, str], ...] = (
    ("enable_flash", "FLASH_ATTENTION"),
    ("enable_mem_efficient", "EFFICIENT_ATTENTION"),
    ("enable_math", "MATH"),
    ("enable_cudnn", "CUDNN_ATTENTION"),
)


def apply_lab_torch_native_policy() -> None:
    """Disable torch python_native Triton DSL when the lab env flag is set.

    Returns:
        None
    """
    if os.environ.get("LAB_DISABLE_TORCH_NATIVE_TRITON", "0") != "1":
        return
    try:
        import torch.backends.python_native as pn
    except Exception:
        return
    triton_ctl = getattr(pn, "triton", None)
    if triton_ctl is None:
        return
    try:
        triton_ctl.enabled = False
    except Exception:
        # Older torch without python_native.triton controller — ignore.
        return


def apply_lab_sdp_kernel_shim(cuda_mod: Any | None = None) -> None:
    """Replace deprecated ``sdp_kernel`` with ``sdpa_kernel`` mapping.

    Args:
        cuda_mod: ``torch.backends.cuda`` module. ``None`` reads ``sys.modules``.

    Returns:
        None
    """
    if cuda_mod is None:
        cuda_mod = sys.modules.get("torch.backends.cuda")
    if cuda_mod is None:
        return
    current = getattr(cuda_mod, "sdp_kernel", None)
    if current is None or getattr(current, "_lab_sdpa_shim", False):
        return
    try:
        from torch.nn.attention import SDPBackend
        from torch.nn.attention import sdpa_kernel as sdpa_kernel_cm
    except Exception:
        return
    if not callable(sdpa_kernel_cm):
        return
    enter_sdpa = cast(
        Callable[[list[Any]], AbstractContextManager[Any]],
        sdpa_kernel_cm,
    )

    def _backend_list(
        enable_flash: bool,
        enable_math: bool,
        enable_mem_efficient: bool,
        enable_cudnn: bool,
    ) -> list[Any]:
        """Map enable_* flags to ``SDPBackend`` members that exist.

        Args:
            enable_flash: Include ``FLASH_ATTENTION`` when present.
            enable_math: Include ``MATH`` when present.
            enable_mem_efficient: Include ``EFFICIENT_ATTENTION`` when present.
            enable_cudnn: Include ``CUDNN_ATTENTION`` when present.

        Returns:
            Backend enum values to pass to ``sdpa_kernel``.
        """
        flags = {
            "enable_flash": enable_flash,
            "enable_math": enable_math,
            "enable_mem_efficient": enable_mem_efficient,
            "enable_cudnn": enable_cudnn,
        }
        backends: list[Any] = []
        for flag, attr in _SDP_BACKEND_FLAGS:
            if not flags[flag]:
                continue
            backend = getattr(SDPBackend, attr, None)
            if backend is not None:
                backends.append(backend)
        return backends

    @contextlib.contextmanager
    def sdp_kernel(
        enable_flash: bool = True,
        enable_math: bool = True,
        enable_mem_efficient: bool = True,
        enable_cudnn: bool = True,
    ) -> Iterator[Any]:
        """Context manager with the old ``sdp_kernel`` enable_* API.

        Args:
            enable_flash: Enable flash attention.
            enable_math: Enable the math (eager) kernel.
            enable_mem_efficient: Enable memory-efficient attention.
            enable_cudnn: Enable cuDNN attention.

        Returns:
            An iterator that yields the inner ``sdpa_kernel`` context.
        """
        backends = _backend_list(
            enable_flash,
            enable_math,
            enable_mem_efficient,
            enable_cudnn,
        )
        with enter_sdpa(backends) as context:
            yield context

    sdp_kernel._lab_sdpa_shim = True  # type: ignore[attr-defined]
    setattr(cuda_mod, "sdp_kernel", sdp_kernel)


def apply_lab_lora_linear_shim(lora_mod: Any | None = None) -> None:
    """Point ``LoRACompatibleLinear`` at ``nn.Linear`` (Chatterbox Matcha).

    Args:
        lora_mod: ``diffusers.models.lora`` module. ``None`` reads ``sys.modules``.

    Returns:
        None
    """
    if lora_mod is None:
        lora_mod = sys.modules.get("diffusers.models.lora")
    if lora_mod is None:
        return
    try:
        import torch.nn as nn
    except Exception:
        return
    linear = getattr(nn, "Linear", None)
    if linear is None:
        return
    if getattr(lora_mod, "LoRACompatibleLinear", None) is linear:
        return
    setattr(lora_mod, "LoRACompatibleLinear", linear)


def _apply_named_shim(fullname: str, module: Any) -> None:
    """Dispatch a post-import shim by module name.

    Args:
        fullname: Fully-qualified module name.
        module: Newly executed module.

    Returns:
        None
    """
    if fullname == "torch.backends.cuda":
        apply_lab_sdp_kernel_shim(module)
    elif fullname == "diffusers.models.lora":
        apply_lab_lora_linear_shim(module)


def _apply_if_already_imported() -> None:
    """Shim targets that landed in ``sys.modules`` before the finder ran."""
    cuda_mod = sys.modules.get("torch.backends.cuda")
    if cuda_mod is not None:
        apply_lab_sdp_kernel_shim(cuda_mod)
    lora_mod = sys.modules.get("diffusers.models.lora")
    if lora_mod is not None:
        apply_lab_lora_linear_shim(lora_mod)


class _LabCompatFinder:
    """Wrap loaders for torch CUDA backends and diffusers LoRA modules."""

    # Fully-qualified modules that receive a post-import shim.
    _TARGETS = frozenset({"torch.backends.cuda", "diffusers.models.lora"})

    def __init__(self) -> None:
        self._lab_tts_compat = True
        self._armed = set(self._TARGETS)
        self._finding = False

    def find_spec(
        self,
        fullname: str,
        path: object | None = None,
        target: object | None = None,
    ) -> Any:
        """Return a wrapped spec for TTS shim targets.

        Args:
            fullname: Fully-qualified module name.
            path: Parent package ``__path__`` or None.
            target: Reload target module or None.

        Returns:
            A ``ModuleSpec`` with a post-exec callback, or None.
        """
        if fullname not in self._armed or self._finding:
            return None
        self._finding = True
        try:
            spec = None
            for finder in sys.meta_path:
                if finder is self:
                    continue
                find = getattr(finder, "find_spec", None)
                if find is None:
                    continue
                spec = find(fullname, path, target)
                if spec is not None:
                    break
            if spec is None or spec.loader is None:
                return None
            orig_loader = spec.loader
            finder_self = self

            class _Loader:
                """Delegating loader that runs a named shim after ``exec_module``."""

                def create_module(self, load_spec: Any) -> Any:
                    """Create the module via the original loader when it implements it.

                    Args:
                        load_spec: Importlib module spec.

                    Returns:
                        The created module, or ``None`` for default creation.
                    """
                    create = getattr(orig_loader, "create_module", None)
                    if create is not None:
                        return create(load_spec)
                    return None

                def exec_module(self, module: Any) -> None:
                    """Execute the original loader, then apply the TTS shim.

                    Args:
                        module: Module object to populate.
                    """
                    orig_loader.exec_module(module)
                    finder_self._armed.discard(fullname)
                    _apply_named_shim(fullname, module)

            spec.loader = _Loader()
            return spec
        finally:
            self._finding = False


# Singleton import finder installed on ``sys.meta_path`` (idempotent register).
_LAB_COMPAT_FINDER: _LabCompatFinder | None = None


def register_lab_tts_compat_hooks() -> None:
    """Install the import finder. Idempotent. Applies to already-imported mods.

    Returns:
        None
    """
    global _LAB_COMPAT_FINDER
    if _LAB_COMPAT_FINDER is None or _LAB_COMPAT_FINDER not in sys.meta_path:
        _LAB_COMPAT_FINDER = _LabCompatFinder()
        sys.meta_path.insert(0, _LAB_COMPAT_FINDER)
    _apply_if_already_imported()


apply_lab_torch_native_policy()
register_lab_tts_compat_hooks()
