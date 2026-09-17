"""Hermetic still/motion prompts for Cinema Rack illustration clips.

Maps each catalog row to a locked illustration stage and a 5s video prompt.
No network. Catalog JSON is read from disk when listing an axis.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, TypedDict

# Repo root and Cinema Rack JSON catalogs.
ROOT = Path(__file__).resolve().parents[1]
CINEMA = ROOT / "custom_nodes" / "ez_prompt_enhance" / "cinema"

DURATION_S = 5
ASPECT_RATIO = "16:9"

# ffmpeg zoompan recipes used when video models are unavailable (ZDR).
MOTION_KINDS = (
    "hold",
    "zoom_in",
    "zoom_out",
    "pan_left",
    "pan_right",
    "tilt_up",
    "tilt_down",
    "rise",
    "drop",
    "orbit",
    "jitter",
    "whip_left",
    "whip_right",
)

STAGES = (
    "face_close",
    "portrait_mcu",
    "medium_person",
    "full_body",
    "street_wide",
    "interior_room",
    "night_neon",
    "tabletop_hands",
)

# Invented adult lock; no living people, brands, or readable signs.
_SUBJECT = (
    "An invented adult woman in her thirties with olive-brown skin, dark wavy "
    "hair half-tied back, wearing a charcoal wool coat over a cream knit"
)

_STAGE_LOCK: dict[str, str] = {
    "face_close": (
        f"{_SUBJECT}, extreme close-up of her left eye, brow, and cheek filling "
        "a 16:9 frame, a catchlight in the iris, late-afternoon harbor light, "
        "photoreal cinema still, no text overlay, no logos."
    ),
    "portrait_mcu": (
        f"{_SUBJECT}, head-and-shoulders medium close-up at eye level on an "
        "unmarked quay, stone buildings soft behind her, photoreal cinema still, "
        "16:9, no text overlay, no logos."
    ),
    "medium_person": (
        f"{_SUBJECT}, waist-up on an unmarked harbor street, cobbles and a quiet "
        "quay behind her, photoreal cinema still, 16:9, no text overlay, no logos."
    ),
    "full_body": (
        f"{_SUBJECT}, full figure on cobbles of an unmarked harbor street, "
        "buildings receding, photoreal cinema still, 16:9, no text overlay, no logos."
    ),
    "street_wide": (
        f"{_SUBJECT}, small in an unmarked European harbor street, stone facades, "
        "a quiet quay, late-afternoon light, photoreal cinema still, 16:9, no "
        "text overlay, no logos, no famous landmarks."
    ),
    "interior_room": (
        f"{_SUBJECT} in an unmarked plaster room with a tall window and a wooden "
        "table, available daylight, photoreal cinema still, 16:9, no text overlay, "
        "no logos."
    ),
    "night_neon": (
        f"{_SUBJECT} on wet cobbles of the same unmarked harbor street at night, "
        "unnamed colored practicals in shop windows, photoreal cinema still, 16:9, "
        "no text overlay, no logos."
    ),
    "tabletop_hands": (
        f"{_SUBJECT}'s hands on an unmarked wooden table with a plain ceramic cup, "
        "soft window light, photoreal cinema still, 16:9, no text overlay, no logos."
    ),
}


class ClipSpec(TypedDict):
    """One illustration clip recipe."""

    axis_id: str
    technique_id: str
    label: str
    stage: str
    still_prompt: str
    motion_prompt: str
    duration_s: int
    aspect_ratio: str
    edit_kind: str
    second_stage: str
    motion_kind: str


def _tid(row: dict[str, Any]) -> str:
    """Return the technique id string.

    Args:
        row: Catalog row.

    Returns:
        Id or empty string.
    """
    return str(row.get("id") or "")


def _tags(row: dict[str, Any]) -> set[str]:
    """Return lowercase tags.

    Args:
        row: Catalog row.

    Returns:
        Tag set.
    """
    return {str(item).lower() for item in (row.get("tags") or []) if item}


def _clause(row: dict[str, Any]) -> str:
    """Return the motion clause, falling back to the still freeze.

    Args:
        row: Catalog row.

    Returns:
        Clause text.
    """
    clause = str(row.get("clause") or "").strip()
    if clause:
        return clause
    return str(row.get("still") or "").strip()


def stage_for(axis_id: str, row: dict[str, Any]) -> str:
    """Pick an illustration stage for ``row``.

    Args:
        axis_id: Cinema Rack axis key.
        row: Technique object.

    Returns:
        A member of ``STAGES``.
    """
    tid = _tid(row)
    tags = _tags(row)
    if axis_id == "framing_shot_size":
        if "ecu" in tags or tid.startswith("size_ecu") or "choker" in tid:
            if any(part in tid for part in ("hand", "palm", "finger", "handshake")):
                return "tabletop_hands"
            if "feet" in tid:
                return "full_body"
            return "face_close"
        if "insert" in tags:
            return "tabletop_hands"
        if "wide" in tags or any(part in tid for part in ("ews", "ws", "establishing")):
            return "street_wide"
        if "body" in tags or "fs" in tid or "full" in tid:
            return "full_body"
        if any(part in tid for part in ("_cu", "mcu")) or "close" in tags:
            return "portrait_mcu"
        if "group" in tags:
            return "street_wide"
        return "medium_person"
    if axis_id == "camera_angles":
        if "tabletop" in tid:
            return "tabletop_hands"
        if "drone" in tags or any(
            part in tid for part in ("bird", "aerial", "god", "topdown", "boom")
        ):
            return "street_wide"
        if any(part in tid for part in ("worm", "ground", "ankle")):
            return "full_body"
        if any(part in tid for part in ("eye", "ots", "seated", "chest")):
            return "portrait_mcu"
        return "medium_person"
    if axis_id == "lenses_optics":
        if "macro" in tags or "macro" in tid:
            return "tabletop_hands"
        if "wide" in tags or any(
            part in tid for part in ("fisheye", "rect_14", "18_", "24_", "28_")
        ):
            return "street_wide"
        if "portrait" in tags or any(part in tid for part in ("85_", "100_", "135_")):
            return "portrait_mcu"
        if "long" in tags:
            return "street_wide"
        return "portrait_mcu"
    if axis_id == "composition":
        if "landscape" in tags or "leading_road" in tid:
            return "street_wide"
        if "portrait" in tags:
            return "portrait_mcu"
        return "interior_room"
    if axis_id == "lighting":
        if any(part in tid for part in ("night", "neon", "moon", "sodium")):
            return "night_neon"
        if any(part in tid for part in ("window", "interior", "room")):
            return "interior_room"
        return "portrait_mcu"
    if axis_id == "color_film_look":
        if any(part in tid for part in ("night", "neon", "bleach")):
            return "night_neon"
        return "street_wide"
    if axis_id == "atmosphere_weather":
        if any(part in tid for part in ("night", "neon")):
            return "night_neon"
        if any(part in tid for part in ("interior", "room", "window")):
            return "interior_room"
        return "street_wide"
    if axis_id == "genre_looks":
        if any(part in tid for part in ("noir", "night", "horror")):
            return "night_neon"
        return "street_wide"
    if axis_id == "viral_looks":
        return "medium_person"
    if axis_id == "time_motion":
        return "street_wide"
    if axis_id == "in_camera_optical":
        return "medium_person"
    if axis_id == "editing_transitions":
        return "medium_person"
    if axis_id == "camera_movement":
        if "drone" in tags or "god_view" in tid:
            return "street_wide"
        if "vehicle" in tags:
            return "street_wide"
        if "underwater" in tags:
            return "street_wide"
        if any(
            part in tid
            for part in (
                "macro",
                "probe",
                "food",
                "product",
                "table",
                "candle",
                "mini_jib",
            )
        ):
            return "tabletop_hands"
        if any(part in tid for part in ("face", "eyes", "crib")):
            return "face_close"
        if "night" in tid:
            return "night_neon"
        if "handheld" in tags or "pov" in tags:
            return "medium_person"
        if "locked" in tags:
            return "interior_room"
        return "street_wide"
    return "medium_person"


def edit_join(axis_id: str, row: dict[str, Any]) -> tuple[str, str]:
    """Return an editing join kind and second stage.

    Args:
        axis_id: Axis key.
        row: Technique object.

    Returns:
        ``(kind, second_stage)``. Kind is empty when the row is not an edit.
    """
    if axis_id != "editing_transitions":
        return "", ""
    tid = _tid(row)
    tags = _tags(row)
    if "dissolve" in tags or "fade" in tags or "morph" in tags or "dream" in tags:
        kind = "dissolve"
    elif "wipe" in tags or "iris" in tags or "wipe" in tid:
        kind = "wipe"
    elif "match" in tags:
        kind = "match"
    else:
        kind = "cut"
    first = stage_for(axis_id, row)
    second = "street_wide" if first != "street_wide" else "interior_room"
    return kind, second


def motion_kind(axis_id: str, row: dict[str, Any]) -> str:
    """Map a catalog row to an ffmpeg camera-move recipe.

    Args:
        axis_id: Axis key.
        row: Technique object.

    Returns:
        A member of ``MOTION_KINDS``.
    """
    tid = _tid(row)
    token = str(row.get("wan_token") or "").lower()
    tags = _tags(row)
    blob = f"{tid} {token} {' '.join(sorted(tags))}"
    if "whip" in blob and "left" in blob:
        return "whip_left"
    if "whip" in blob and "right" in blob:
        return "whip_right"
    if "handheld" in blob or "jitter" in blob:
        return "jitter"
    if "orbit" in blob or "circle" in blob or "carousel" in blob or "roll" in blob:
        return "orbit"
    if any(part in blob for part in ("crane up", "boom up", "rise", "pedestal up")):
        return "rise"
    if any(part in blob for part in ("crane down", "boom down", "drop", "descend", "pedestal down")):
        return "drop"
    if "tilt up" in blob:
        return "tilt_up"
    if "tilt down" in blob:
        return "tilt_down"
    if any(
        part in blob
        for part in ("dolly out", "zoom out", "pull", "crash out")
    ):
        return "zoom_out"
    if any(
        part in blob
        for part in ("dolly in", "zoom in", "crash zoom", "push", "dolly zoom")
    ):
        return "zoom_in"
    if "pan left" in blob or (token == "pan" and "left" in tid):
        return "pan_left"
    if "pan right" in blob or (token == "pan" and "right" in tid):
        return "pan_right"
    if "tracking" in blob or "truck" in blob or "slider" in blob:
        if "left" in blob:
            return "pan_left"
        return "pan_right"
    if axis_id == "camera_movement" and "left" in tid:
        return "pan_left"
    if axis_id == "camera_movement" and "right" in tid:
        return "pan_right"
    if "locked" in tags or "fixed camera" in token:
        return "hold"
    if axis_id == "camera_movement":
        return "zoom_in"
    return "hold"


def still_prompt(axis_id: str, row: dict[str, Any], stage: str) -> str:
    """Build a first-frame still prompt.

    Args:
        axis_id: Axis key.
        row: Technique object.
        stage: Illustration stage.

    Returns:
        Prompt text.
    """
    lock = _STAGE_LOCK.get(stage) or _STAGE_LOCK["medium_person"]
    freeze = str(row.get("still") or "").strip() or _clause(row)
    label = str(row.get("label") or axis_id)
    return f"{lock} Illustrate {label}: {freeze}"


def motion_prompt(axis_id: str, row: dict[str, Any]) -> str:
    """Build a 5s video prompt.

    Args:
        axis_id: Axis key.
        row: Technique object.

    Returns:
        Present-tense motion prompt.
    """
    clause = _clause(row)
    token = str(row.get("wan_token") or "").strip()
    if axis_id == "editing_transitions":
        return (
            f"{clause} Keep the camera simple; the join is assembled in edit. "
            "Photoreal live action, 16:9, no text overlay, no logos."
        )
    if token:
        return (
            f"The camera performs {token} in one continuous five-second take. "
            f"{clause} Photoreal live action, 16:9, no text overlay, no logos."
        )
    return (
        f"Locked camera, the subject breathes. {clause} Photoreal live action, "
        "16:9, no text overlay, no logos."
    )


def clip_spec(axis_id: str, row: dict[str, Any]) -> ClipSpec:
    """Return the illustration recipe for one catalog row.

    Args:
        axis_id: Axis key.
        row: Technique object.

    Returns:
        Clip spec mapping.
    """
    stage = stage_for(axis_id, row)
    kind, second = edit_join(axis_id, row)
    return {
        "axis_id": axis_id,
        "technique_id": _tid(row),
        "label": str(row.get("label") or _tid(row)),
        "stage": stage,
        "still_prompt": still_prompt(axis_id, row, stage),
        "motion_prompt": motion_prompt(axis_id, row),
        "duration_s": DURATION_S,
        "aspect_ratio": ASPECT_RATIO,
        "edit_kind": kind,
        "second_stage": second,
        "motion_kind": motion_kind(axis_id, row),
    }


def load_axis_rows(axis_id: str) -> list[dict[str, Any]]:
    """Load technique rows for ``axis_id`` from the shipped catalogs.

    Args:
        axis_id: Axis key.

    Returns:
        Technique objects.

    Raises:
        SystemExit: Unknown axis or malformed JSON.
    """
    axes_path = CINEMA / "axes.json"
    axes = json.loads(axes_path.read_text(encoding="utf-8"))
    if not isinstance(axes, dict) or axis_id not in axes:
        raise SystemExit(f"unknown axis {axis_id}")
    meta = axes[axis_id]
    if not isinstance(meta, dict):
        raise SystemExit(f"unknown axis {axis_id}")
    filename = str(meta.get("file") or f"{axis_id}.json")
    rows = json.loads((CINEMA / filename).read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise SystemExit(f"{filename} must be a list")
    return [row for row in rows if isinstance(row, dict)]


def specs_for_axis(axis_id: str) -> list[ClipSpec]:
    """Return clip specs for every row on ``axis_id``.

    Args:
        axis_id: Axis key.

    Returns:
        Clip specs in catalog order.
    """
    return [clip_spec(axis_id, row) for row in load_axis_rows(axis_id)]


def main(argv: list[str] | None = None) -> int:
    """Print JSON clip specs for one axis.

    Args:
        argv: CLI words; defaults to ``sys.argv[1:]``.

    Returns:
        Process exit status.
    """
    args = sys.argv[1:] if argv is None else argv
    axis = ""
    index = 0
    while index < len(args):
        word = args[index]
        if word == "--axis":
            index += 1
            if index >= len(args):
                raise SystemExit("usage: cinema_clip_prompts.py --axis ID")
            axis = args[index]
        else:
            raise SystemExit(f"unknown arg {word}")
        index += 1
    if not axis:
        raise SystemExit("usage: cinema_clip_prompts.py --axis ID")
    print(json.dumps(specs_for_axis(axis), indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
