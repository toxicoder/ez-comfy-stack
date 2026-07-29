"""Lab sitecustomize: optional disable of PyTorch 2.13 Triton native ops.

Activated when the entrypoint prepends ``/opt/ez-comfy/pythonpath`` to
``PYTHONPATH`` and ``LAB_DISABLE_TORCH_NATIVE_TRITON=1``.

When set, turns off ``torch.backends.python_native.triton`` so ops such as
``bmm_outer_product`` (used during CLIP / Gemma RoPE) fall back to eager/cuBLAS
instead of JIT-compiling Triton's ``cuda_utils`` helper. Used as an escape hatch
when gcc/Python.h/libcuda link env is incomplete.

No-op when the env flag is unset or not ``1``, or when torch is unavailable.
"""

from __future__ import annotations

import os


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


apply_lab_torch_native_policy()
