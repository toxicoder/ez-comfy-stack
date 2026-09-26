"""Camera and foley enums so Enhance cannot invent a second dolly.

Hermetic stdlib. Compiler / App Mode widgets must pick from these sets.
"""

from __future__ import annotations

# Closed camera / foley tokens so Enhance cannot invent a second move.
CAMERAS = (
    "dolly in",
    "dolly out",
    "pan left",
    "pan right",
    "tracking",
    "fixed camera",
)

FOLEY = (
    "wind",
    "footsteps",
    "room tone",
    "shop bell",
    "electrical hum",
    "glyph chime",
    "none",
)


def _norm(token: str) -> str:
    """Collapse whitespace and lowercase a widget token.

    Args:
        token: Raw camera or foley string.

    Returns:
        Normalized token.
    """
    return " ".join(str(token).strip().lower().split())


def validate_camera(token: str) -> str:
    """Return the canonical camera token or raise.

    Args:
        token: Camera widget value.

    Returns:
        Canonical camera string from ``CAMERAS``.
    """
    key = _norm(token)
    for item in CAMERAS:
        if key == item:
            return item
    raise ValueError(f"unknown camera {token!r}; allowed: {', '.join(CAMERAS)}")


def validate_foley(token: str) -> str:
    """Return the canonical foley token or raise.

    Args:
        token: Foley widget value.

    Returns:
        Canonical foley string from ``FOLEY``.
    """
    key = _norm(token)
    for item in FOLEY:
        if key == item:
            return item
    raise ValueError(f"unknown foley {token!r}; allowed: {', '.join(FOLEY)}")


def shot_card(
    sid: str,
    *,
    camera: str = "dolly in",
    foley: str = "room tone",
    status: str = "pending",
) -> dict[str, str]:
    """One App Mode / subgraph card payload for a shot.

    Args:
        sid: Shot id ``01``...``18``.
        camera: Camera token (default dolly in).
        foley: Foley token (default room tone).
        status: Jobstore status string.

    Returns:
        Card dict with canonical camera and foley.
    """
    return {
        "id": str(sid),
        "status": str(status),
        "camera": validate_camera(camera),
        "foley": validate_foley(foley),
    }
