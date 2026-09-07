"""LTX latent length: frames must be ``1 + 8n`` and odd.

Hermetic (stdlib). Default lab printers stay 5.00 s. Duration-head
8 / 10 / 12 s is opt-in behind this preflight — never a 30/60/90 s denoise.
"""

from __future__ import annotations

FPS_DEFAULT = 24
DURATION_DEFAULT_S = 5.00
DURATION_HEAD_S = (5.00, 8.00, 10.00, 12.00)
FRAME_MODULUS = 8


def ltx_frames_for_duration(duration_s: float, fps: int = FPS_DEFAULT) -> int:
    """Nearest legal LTX frame count for ``duration_s`` at ``fps``.

    LTX frame math is ``1 + 8n``. The nearest legal count to ``round(s*fps)``
    is always odd, so even-length latents (which crash) cannot come out of here.
    """
    if duration_s <= 0 or fps <= 0:
        raise ValueError(f"duration_s and fps must be positive, got {duration_s!r} {fps!r}")
    target = int(round(float(duration_s) * int(fps)))
    n = max(0, int(round((target - 1) / FRAME_MODULUS)))
    return 1 + FRAME_MODULUS * n


def validate_ltx_frames(frames: int) -> int:
    """Refuse even lengths and counts that are not ``1 + 8n``."""
    n = int(frames)
    if n < 1:
        raise ValueError(f"LTX frames must be >= 1, got {n}")
    if n % 2 == 0:
        raise ValueError(f"even LTX latents crash; got {n} (use 1+8n, e.g. 121)")
    if (n - 1) % FRAME_MODULUS != 0:
        raise ValueError(f"LTX frames must be 1+8n, got {n}")
    return n


def preflight_duration_s(duration_s: float) -> float:
    """Allow only the default 5.00 s printer or documented duration-head."""
    value = float(duration_s)
    for allowed in DURATION_HEAD_S:
        if abs(value - allowed) < 1e-9:
            return allowed
    raise ValueError(
        f"duration {value} s is not in {DURATION_HEAD_S}; "
        "do not queue a 30/60/90 s latent on GB10"
    )
