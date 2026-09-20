"""LTX latent length: frames must be ``1 + 8n`` and odd.

Hermetic (stdlib). Film / concat printers stay 5.00 s. Standalone LTX
Apps default to 10.00 s (adjustable 5/8/10/12). Never a 30/60/90 s
denoise.
"""

from __future__ import annotations

# LTX printer timing: 24 fps, 5.00 s film default, 10.00 s App default.
FPS_DEFAULT = 24
DURATION_DEFAULT_S = 5.00
DURATION_APP_S = 10.00
DURATION_HEAD_S = (5.00, 8.00, 10.00, 12.00)
FRAME_MODULUS = 8
# 5.00 s @ 24 fps → 121; 10.00 s @ 24 fps → 241 (both 1+8n).
FRAMES_DEFAULT = 121
FRAMES_APP = 241


def snap_ltx_frames(frames: int) -> int:
    """Nearest legal LTX pixel length (``1 + 8n``).

    ``120`` (even, not ``1+8n``) snaps to ``121``, not the VAE floor of ``113``.

    Args:
        frames: Requested pixel-frame count.

    Returns:
        Odd length ``1 + 8n`` nearest to ``frames``.
    """
    n = int(frames)
    if n < 1:
        raise ValueError(f"LTX frames must be >= 1, got {n}")
    k = max(0, int(round((n - 1) / FRAME_MODULUS)))
    return 1 + FRAME_MODULUS * k


def ltx_decoded_frames(length: int) -> int:
    """Pixel frames the LTX video VAE actually emits for widget ``length``.

    Comfy allocates ``((length-1)//8)+1`` latent frames, which decode as
    ``1+8n``. Illegal ``120`` therefore becomes **113** (4.708 s @ 24 fps).

    Args:
        length: Comfy ``length`` widget value.

    Returns:
        Decoded pixel-frame count (``1 + 8n``).
    """
    n = int(length)
    if n < 1:
        raise ValueError(f"LTX length must be >= 1, got {n}")
    latent = ((n - 1) // FRAME_MODULUS) + 1
    return (latent - 1) * FRAME_MODULUS + 1


def ltx_frames_for_duration(duration_s: float, fps: int = FPS_DEFAULT) -> int:
    """Nearest legal LTX frame count for ``duration_s`` at ``fps``.

    LTX frame math is ``1 + 8n``. The nearest legal count to ``round(s*fps)``
    is always odd, so even-length latents (which crash) cannot come out of here.

    Args:
        duration_s: Requested duration in seconds.
        fps: Frames per second (lab default 24).

    Returns:
        Legal LTX frame count.
    """
    if duration_s <= 0 or fps <= 0:
        raise ValueError(f"duration_s and fps must be positive, got {duration_s!r} {fps!r}")
    target = int(round(float(duration_s) * int(fps)))
    return snap_ltx_frames(target)


def validate_ltx_frames(frames: int) -> int:
    """Refuse even lengths and counts that are not ``1 + 8n``.

    Args:
        frames: Candidate pixel-frame count.

    Returns:
        ``frames`` when legal.
    """
    n = int(frames)
    if n < 1:
        raise ValueError(f"LTX frames must be >= 1, got {n}")
    if n % 2 == 0:
        raise ValueError(f"even LTX latents crash; got {n} (use 1+8n, e.g. 121)")
    if (n - 1) % FRAME_MODULUS != 0:
        raise ValueError(f"LTX frames must be 1+8n, got {n}")
    return n


def preflight_duration_s(duration_s: float) -> float:
    """Allow the 5.00 s film printer, 10.00 s App default, or duration-head.

    Args:
        duration_s: Requested printer duration.

    Returns:
        Canonical allowed duration.
    """
    value = float(duration_s)
    for allowed in DURATION_HEAD_S:
        if abs(value - allowed) < 1e-9:
            return allowed
    raise ValueError(
        f"duration {value} s is not in {DURATION_HEAD_S}; "
        "do not queue a 30/60/90 s latent on GB10"
    )
