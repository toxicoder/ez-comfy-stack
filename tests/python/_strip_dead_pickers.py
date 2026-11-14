"""Delete image pickers that nothing on the graph can ever read.

A ``LoadImage`` whose output feeds nothing is a widget that lies. The operator
picks a file, Queue runs, and every pixel comes out as if the widget were
empty. Two kinds of unwired picker are honest and stay:

* a picker that already carries a link; and
* a declared opt-in that says so out loud - listed in ``extra.lab_optional_unwired``,
  muted (LiteGraph mode 4) so the canvas shows it switched off, and sitting
  beside a named optional input it could be wired into. The album ``Cover
  image`` loader beside ``EZAudioMetadata.cover`` is that pattern.

What is left is a picker a live graph pretends to use: unmuted, so the App and
the canvas both treat it as part of the render, while nothing reads it. Those
go, and the App stops offering a choice that changes nothing.

Run it over the catalog with ``PYTHONPATH=custom_nodes:tests/python``::

    python3 tests/python/_strip_dead_pickers.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

from _stamp_app_mode import NODE_MODE_BYPASS
from _wire_prompt_enhance import remove_node

PICKER_TYPES = frozenset(
    {
        "EZOptionalImage",
        "EZSnapImage",
        "LoadImage",
        "LoadImageMask",
        "VHS_LoadVideo",
    }
)
"""Node types whose whole job is to hand the graph an image the operator chose.

The same set the catalog gate scores, so the pass and the gate cannot drift into
agreeing on different shapes of picker.
"""

IMAGE_SLOT_NAMES = frozenset(
    {
        "image",
        "images",
        "cover",
        "end_image",
        "reference_image",
        "start_image",
        "vae_image",
    }
)
"""Input slot names that take an image, used when a slot carries no type."""

NOTE_FIXES: dict[str, tuple[tuple[str, str], ...]] = {
    "video/silent/first-last-5s": (
        (
            "Load a start frame and an end frame.",
            "Load a start frame. End-frame control needs the Fun InP FLF "
            "sampler the Comfy pin does not expose yet.",
        ),
    ),
    "video/silent/vace-join": (
        (
            "Load Shot A last frame and Shot B first frame. Native "
            "WanVaceToVideo is the intended join when the Comfy pin exposes it;",
            "Load Shot A last frame. The Shot B half needs WanVaceToVideo, "
            "which this Comfy pin does not expose yet;",
        ),
    ),
}
"""Operator copy that promised a control the pinned ComfyUI cannot honour.

Keyed by lab id, then ``(found, replaced)`` pairs applied to every Note on the
graph. A dead picker leaves behind a sentence that tells the operator to use it,
so the sentence goes with the node.
"""


def _output_linked(node: Mapping[str, Any]) -> bool:
    """True when any output of ``node`` carries at least one link id."""
    for out in node.get("outputs") or []:
        if isinstance(out, dict) and (out.get("links") or []):
            return True
    return False


def _open_image_slot(graph: Mapping[str, Any], picker_id: int) -> bool:
    """True when another node still has an unwired image slot to receive it."""
    for node in graph.get("nodes") or []:
        if int(node.get("id") or -1) == picker_id:
            continue
        for slot in node.get("inputs") or []:
            if not isinstance(slot, dict) or slot.get("link") is not None:
                continue
            name = str(slot.get("name") or "").strip().lower()
            slot_type = str(slot.get("type") or slot.get("link_type") or "").upper()
            if slot_type == "IMAGE" or name in IMAGE_SLOT_NAMES:
                return True
    return False


def dead_pickers(graph: Mapping[str, Any]) -> list[int]:
    """Ids of picker nodes on this graph that nothing can consume.

    Args:
        graph: Serialized Comfy graph.

    Returns:
        Node ids to delete, in graph order.
    """
    declared = {
        str(name)
        for name in ((graph.get("extra") or {}).get("lab_optional_unwired") or [])
    }
    dead: list[int] = []
    for node in graph.get("nodes") or []:
        ntype = str(node.get("type") or "")
        if ntype not in PICKER_TYPES or _output_linked(node):
            continue
        node_id = int(node.get("id") or -1)
        opted_in = (
            ntype in declared
            and int(node.get("mode") or 0) == NODE_MODE_BYPASS
            and _open_image_slot(graph, node_id)
        )
        if opted_in:
            continue
        dead.append(node_id)
    return dead


def fix_dead_picker_notes(graph: dict[str, Any], lab_rel: str) -> int:
    """Rewrite Note copy that names a control this graph no longer carries.

    Args:
        graph: Serialized Comfy graph, mutated in place.
        lab_rel: Lab id, such as ``video/silent/vace-join``.

    Returns:
        Number of Note widgets whose text changed.
    """
    edits = NOTE_FIXES.get(lab_rel) or ()
    changed = 0
    for node in graph.get("nodes") or []:
        if node.get("type") not in ("Note", "MarkdownNote"):
            continue
        values = list(node.get("widgets_values") or [])
        if not values or not isinstance(values[0], str):
            continue
        text = values[0]
        for needle, replacement in edits:
            if needle in text:
                text = text.replace(needle, replacement)
        if text != values[0]:
            values[0] = text
            node["widgets_values"] = values
            changed += 1
    return changed


def strip_dead_pickers(graph: dict[str, Any], lab_rel: str = "") -> int:
    """Delete this graph's dead pickers and stale copy.

    Args:
        graph: Serialized Comfy graph, mutated in place.
        lab_rel: Lab id used to look up :data:`NOTE_FIXES`; empty skips copy.

    Returns:
        Number of nodes deleted plus Note widgets rewritten. The copy repair
        runs whether or not this pass deleted anything, so a graph whose node
        went away in an earlier run still gets its stale sentence fixed.
    """
    removed = 0
    for node_id in dead_pickers(graph):
        remove_node(graph, node_id)
        removed += 1
    return removed + fix_dead_picker_notes(graph, lab_rel)


def strip_all(root: Path | None = None) -> int:
    """Strip every lab graph; return the number of graphs that changed.

    Args:
        root: Workflows root. Defaults to this checkout's ``workflows``.

    Returns:
        Count of files rewritten.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _lab_paths import lab_graph_paths

    base = root if root is not None else Path(__file__).resolve().parents[2] / "workflows"
    touched = 0
    for path in lab_graph_paths(base):
        graph = json.loads(path.read_text(encoding="utf-8"))
        lab_rel = str(path).split("_lab/")[-1].removesuffix(".json")
        if strip_dead_pickers(graph, lab_rel):
            path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
            touched += 1
            print(f"stripped {path}")
    return touched


if __name__ == "__main__":
    strip_all()
