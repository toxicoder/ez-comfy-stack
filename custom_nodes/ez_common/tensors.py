"""Tensor aliases for the torch / numpy boundary.

``torch`` and ``numpy`` are not installed for the hermetic typecheck lane
(the gate must run without CUDA), so the honest annotation for a Comfy image
is not ``Any`` - it is the real class, spelled through ``TYPE_CHECKING``.
Each checker resolves it to its own stubs when the package is present and
to an opaque imported value when it is not, which keeps call sites
``image[-1:]`` / ``image.shape`` legal without pretending to know the API.

Annotation-only module: import it under ``TYPE_CHECKING`` like the other
type modules. Never import it for runtime behaviour, and never add a
function here - a tensor that needs helpers belongs in the pack that owns
the operation.

The two ``np.ndarray`` parameters are the one place explicit ``Any`` is
allowed outside Comfy's registry: ``ndarray`` is generic in shape and dtype,
and naming them would pin a dtype this repo does not guarantee. That is why
this module is listed in ``mypy.ini`` as a declared boundary.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeAlias

if TYPE_CHECKING:
    import numpy as np
    import torch

Tensor: TypeAlias = "torch.Tensor"
"""A torch tensor of unstated dtype and shape."""

ImageTensor: TypeAlias = "torch.Tensor"
"""Comfy image tensor: BHWC float in ``0..1``."""

MaskTensor: TypeAlias = "torch.Tensor"
"""Comfy mask tensor: single channel, float in ``0..1``."""

LatentTensor: TypeAlias = "torch.Tensor"
"""VAE latent tensor (BCHW in latent space)."""

PcmTensor: TypeAlias = "torch.Tensor"
"""Audio waveform tensor (channels x samples)."""

NdArray: TypeAlias = "np.ndarray[Any, np.dtype[Any]]"
"""A numpy array of unstated dtype, at the optional-import boundary."""

__all__ = [
    "ImageTensor",
    "LatentTensor",
    "MaskTensor",
    "NdArray",
    "PcmTensor",
    "Tensor",
]
