"""Retire the old Quality combo's copy out of shipped graph text.

The three-rung Detail ladder replaced the Quality combo, and the builders were
rewritten with it. Shipped graphs are stamped, not rebuilt, so a Note an author
wrote in 2024 still tells an operator to "set Quality **High**" or claims that
``ultra`` swaps in Klein 9B. A control the operator cannot select is worse than
no control, and a rung list that names weights the ladder refuses to write is a
false promise about the pixels they are about to pay for.

This pass swaps that copy in place, the way :data:`_wire_format.RETIRED_BLURBS`
swaps a retired Format sentence. It is a table, not a rewriter: every pair is an
exact sentence an older stamp left behind and the sentence the ladder ships now,
so a re-stamp converges instead of stacking, and nothing here invents wording a
builder does not already use.

Run after the stamp and before ``//:docs:generate``::

    PYTHONPATH=custom_nodes:tests/python python3 tests/python/_retire_combo_copy.py

The catalog gate (:mod:`test_app_catalog_audit`) scores the same surfaces with
the same :data:`RETIRED_CONTROL_PHRASES` and :data:`CONTENT_WIDGET_TYPES`, so
the pass and the gate cannot drift into agreeing on different copy.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from _lab_paths import lab_graph_paths

CONTENT_WIDGET_TYPES: frozenset[str] = frozenset(
    {
        "EZRapLyrics",
        "EZAceStepPromptEnhance",
        "TextEncodeAceStepAudio1.5",
    }
)
"""Node types whose string widgets hold authored content, not UI copy.

A lyric that rhymes the word "quality" is a lyric, not an instruction to an
operator, so these types keep their wording.
"""

EXTRA_KEYS: tuple[str, ...] = ("lab_description", "lab_note", "lab_graph_note")
"""``extra`` keys the operator console prints as the App's own description."""

TITLE_KEYS: tuple[str, ...] = ("title", "title_mode")
"""Node fields LiteGraph shows as the node's caption on the canvas."""

RETIRED_COPY: tuple[tuple[str, str], ...] = (
    (
        "Profile: Quality `flux3-fast` writes UNET "
        "`flux3-image-klein-int8-convrot.safetensors`, 16 steps, CFG 1.0.",
        "Profile: Detail **draft** writes UNET "
        "`flux3-image-klein-int8-convrot.safetensors`, 16 steps, CFG 1.0.",
    ),
    (
        "Profile: Quality `flux3-quality` writes UNET "
        "`flux3-image-klein-base-int8-convrot.safetensors`, 50 steps, CFG 3.5.",
        "Profile: Detail **final** writes UNET "
        "`flux3-image-klein-base-int8-convrot.safetensors`, 50 steps, CFG 3.5.",
    ),
    (
        "This graph ships those same values, so Queue matches with Quality left "
        "on lab.",
        "This graph ships those same values, so Queue matches with Detail left "
        "on **standard**.",
    ),
    (
        "Quality never changes pixels - Format / platform does (Custom uses "
        "Width x Height).",
        "Detail never changes pixels - Format / platform does (Custom uses "
        "Width x Height).",
    ),
    (
        "Gated FLUX 3 Klein distilled still; 16 steps, CFG 1.0 (Quality "
        "flux3-fast).",
        "Gated FLUX 3 Klein distilled still; 16 steps, CFG 1.0 (Detail draft).",
    ),
    (
        "Gated FLUX 3 Klein base still; 50 steps, CFG 3.5 (Quality "
        "flux3-quality).",
        "Gated FLUX 3 Klein base still; 50 steps, CFG 3.5 (Detail final).",
    ),
    (
        "Quality: the combo offers only the four Qwen tiers this graph can "
        "honor - qwen_image_2.1_int8_convrot.safetensors plus the turbo, NVFP4, "
        "and turbo-NVFP4 twins.",
        "Detail: three rungs, all inside Qwen-Image - draft is the turbo build "
        "at 16 steps, CFG 1.0; standard writes nothing; final is the base INT8 "
        "build (qwen_image_2.1_int8_convrot.safetensors) at 50 steps, CFG 3.5.",
    ),
    (
        "Quality never swaps to Klein, FLUX 3, or any other family: those live "
        "in their own apps.",
        "Detail never swaps to Klein, FLUX 3, or any other family: those live "
        "in their own apps.",
    ),
    (
        "Opt-in Qwen-Image 2.1 square still; the only graph the Qwen Quality "
        "tiers can honor.",
        "Opt-in Qwen-Image 2.1 square still; the only graph the Qwen Detail "
        "rungs can honor.",
    ),
    (
        "For tiny or dense type, set Quality **High** (Klein base if "
        "`download-image --tier base` is on disk).",
        "For tiny or dense type, pick Detail **Final** (it needs "
        "`flux-2-klein-base-4b-fp8.safetensors` on disk - "
        "`download-image --tier base`).",
    ),
    (
        "If the plate is only the flat study, set Quality **High** (Klein base "
        "if `download-image --tier base` is on disk).",
        "If the plate is only the flat study, pick Detail **Final** (it needs "
        "`flux-2-klein-base-4b-fp8.safetensors` on disk - "
        "`download-image --tier base`).",
    ),
    (
        "Quality is the only weight swap this App offers, and it stays inside "
        "the Klein stack: standard = Klein 4B fp8 (8 steps, CFG 1.0), draft = "
        "Klein 4B nvfp4 (4 steps, CFG 1.0), high and Free Commercial Use "
        "(<$10M) = Klein 4B base (24 steps, CFG 3.5), ultra = Klein 9B "
        "distilled, max = Klein 9B base.",
        "Detail is the only weight swap this App offers, and it stays inside "
        "the Klein stack: draft = Klein 4B nvfp4 (4 steps, CFG 1.0), standard = "
        "what this App ships tuned for (writes nothing, so it always applies), "
        "final = Klein 4B base fp8 (24 steps, CFG 3.5).",
    ),
    (
        "Quality ultra/max may select opt-in Non-Commercial weights when those "
        "files are on disk (gated, not YouTube-ok).",
        "No rung reaches the opt-in Non-Commercial weights (gated, not "
        "YouTube-ok).",
    ),
    (
        "They load Wan and LTX UNETs, which this audio graph's Quality cannot "
        "drive, so they are not parked on this canvas.",
        "They load Wan and LTX UNETs, which this audio graph's Detail ladder "
        "cannot drive, so they are not parked on this canvas.",
    ),
    (
        "No rung reaches the opt-in Non-Commercial weights (Klein 9B / "
        "FLUX.2-dev, gated, not YouTube-ok).",
        "No rung reaches the opt-in Non-Commercial weights (gated, not "
        "YouTube-ok).",
    ),
    (
        "Quality does not change size.",
        "Detail does not change size.",
    ),
    (
        "Image model - Quality swaps within the Klein stack",
        "Image model - Detail swaps within the Klein stack",
    ),
    (
        "Daily Klein 4B still; Quality swaps within the Klein stack",
        "Daily Klein 4B still; Detail swaps within the Klein stack",
    ),
)
"""``(retired sentence, ladder sentence)`` pairs, longest first.

Each left-hand side is copy this repo shipped before the ladder. The right-hand
side is the wording the promoted builders use today, so the shipped catalog and
a fresh build agree. Order matters: the tier-table sentence has to be swapped
before the short sentences inside it.
"""


def _retire(text: str) -> str:
    """Swap every retired sentence this text carries for the ladder's wording.

    Globals:
        None.
    Arguments:
        text: Operator-facing copy as stored in the graph.
    Outputs:
        Nothing; returns the rewritten string.
    Returns:
        ``text`` with each :data:`RETIRED_COPY` left-hand side replaced, or the
        same string when it carries none of them.
    """
    for retired, replacement in RETIRED_COPY:
        if retired in text:
            text = text.replace(retired, replacement)
    return text


def retired_phrases(text: str) -> tuple[str, ...]:
    """Return the retired sentences ``text`` still carries.

    Globals:
        None.
    Arguments:
        text: Operator-facing copy to check.
    Outputs:
        Nothing; returns a tuple.
    Returns:
        Each left-hand side of :data:`RETIRED_COPY` found in ``text``, in table
        order. Empty once the catalog has converged.
    """
    return tuple(retired for retired, _ in RETIRED_COPY if retired in text)


def copy_surfaces(node: dict) -> list[tuple[str, str]]:
    """Return the ``(field, text)`` pairs an operator reads on one node.

    Globals:
        None.
    Arguments:
        node: One graph node as stored.
    Outputs:
        Nothing; returns a list of ``(label, text)`` pairs.
    Returns:
        The node's caption fields and its string widgets, labelled for an error
        message. Widgets of a :data:`CONTENT_WIDGET_TYPES` node are skipped:
        they hold authored lyrics and prompts, not UI copy.
    """
    node_type = str(node.get("type") or "")
    surfaces: list[tuple[str, str]] = []
    for key in TITLE_KEYS:
        value = node.get(key)
        if isinstance(value, str):
            surfaces.append((f".{key}", value))
    if node_type in CONTENT_WIDGET_TYPES:
        return surfaces
    widgets = node.get("widgets_values") or []
    if isinstance(widgets, list):
        for index, widget in enumerate(widgets):
            if isinstance(widget, str):
                surfaces.append((f".widgets_values[{index}]", widget))
            elif isinstance(widget, dict):
                for key, value in widget.items():
                    if isinstance(value, str):
                        surfaces.append((f".widgets_values[{index}].{key}", value))
    return surfaces


def retired_copy(graph: dict) -> list[str]:
    """Return every retired sentence a graph still shows an operator.

    Globals:
        None.
    Arguments:
        graph: The parsed lab graph.
    Outputs:
        Nothing; returns a list of ``"<where>: <sentence>"`` strings.
    Returns:
        One entry per retired sentence per surface, empty once converged.
    """
    found: list[str] = []
    for node in graph.get("nodes", []) or []:
        node_type = str(node.get("type") or "")
        for label, text in copy_surfaces(node):
            for phrase in retired_phrases(text):
                found.append(f"{node_type} {node.get('id')} {label}: {phrase}")
    extra = graph.get("extra") or {}
    for key in EXTRA_KEYS:
        value = extra.get(key)
        if isinstance(value, str):
            for phrase in retired_phrases(value):
                found.append(f"extra.{key}: {phrase}")
    return found


def retire_combo_copy(graph: dict) -> int:
    """Rewrite retired combo copy in one graph, in place.

    Globals:
        None.
    Arguments:
        graph: The parsed lab graph, mutated.
    Outputs:
        Nothing.
    Returns:
        The number of surfaces rewritten, so a caller can tell a no-op from a
        fix and keep the pass idempotent.
    """
    changed = 0
    for node in graph.get("nodes", []) or []:
        for label, text in copy_surfaces(node):
            rewritten = _retire(text)
            if rewritten == text:
                continue
            if label.startswith(".widgets_values["):
                _set_widget(node, label, rewritten)
            else:
                node[label.removeprefix(".")] = rewritten
            changed += 1
    extra = graph.get("extra") or {}
    for key in EXTRA_KEYS:
        value = extra.get(key)
        if not isinstance(value, str):
            continue
        rewritten = _retire(value)
        if rewritten != value:
            extra[key] = rewritten
            changed += 1
    return changed


def _set_widget(node: dict, label: str, value: str) -> None:
    """Write one string widget by the label :func:`copy_surfaces` produced.

    Globals:
        None.
    Arguments:
        node: The node that owns the widget.
        label: A label of the form ``.widgets_values[3]`` or
            ``.widgets_values[3].field``.
        value: The replacement text.
    Outputs:
        The widget is replaced in place.
    Returns:
        None.
    """
    widgets = node.get("widgets_values")
    if not isinstance(widgets, list):
        return
    head, _, tail = label.removeprefix(".widgets_values[").partition("]")
    index = int(head)
    if tail.startswith("."):
        slot = widgets[index]
        if isinstance(slot, dict):
            slot[tail[1:]] = value
    else:
        widgets[index] = value


def retire_all(root: Path | None = None) -> int:
    """Retire combo copy across the shipped catalog.

    Globals:
        None.
    Arguments:
        root: Optional catalog directory; defaults to the shipped ``_lab`` tree.
    Outputs:
        One ``retired <path>`` line per rewritten graph on stdout.
    Returns:
        The total number of surfaces rewritten.
    """
    paths = lab_graph_paths() if root is None else sorted(root.rglob("*.json"))
    total = 0
    for path in paths:
        graph = json.loads(path.read_text(encoding="utf-8"))
        changed = retire_combo_copy(graph)
        if changed:
            path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
            print(f"retired {path}")
            total += changed
    return total


if __name__ == "__main__":
    sys.exit(0 if retire_all() >= 0 else 1)
