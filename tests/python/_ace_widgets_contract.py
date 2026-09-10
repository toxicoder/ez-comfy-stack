"""TextEncodeAceStepAudio1.5 widgets_values layout (ComfyUI v0.34.6).

Not collected by pytest (leading underscore). Native ACE-Step 1.5 seed
has control_after_generate, so widgets_values is 15 slots — seed is
followed by fixed/increment/decrement/randomize. Combo widgets are
strict; a missing control slot shifts timesignature/language/keyscale.
"""

from __future__ import annotations

import re
from typing import Any

ACE_ENCODER_TYPE = "TextEncodeAceStepAudio1.5"
ACE_WIDGET_COUNT = 15
ACE_SEED_CONTROL = frozenset({"fixed", "increment", "decrement", "randomize"})
ACE_TIMESIGNATURE = frozenset({"2", "3", "4", "6"})
# comfy_extras/nodes_ace.py TextEncodeAceStepAudio1.5 language combo (v0.34.6).
ACE_LANGUAGE = frozenset(
    {
        "ar",
        "az",
        "bg",
        "bn",
        "ca",
        "cs",
        "da",
        "de",
        "el",
        "en",
        "es",
        "fa",
        "fi",
        "fr",
        "he",
        "hi",
        "hr",
        "ht",
        "hu",
        "id",
        "is",
        "it",
        "ja",
        "ko",
        "la",
        "lt",
        "ms",
        "ne",
        "nl",
        "no",
        "pa",
        "pl",
        "pt",
        "ro",
        "ru",
        "sa",
        "sk",
        "sr",
        "sv",
        "sw",
        "ta",
        "te",
        "th",
        "tl",
        "tr",
        "uk",
        "ur",
        "vi",
        "yue",
        "zh",
        "unknown",
    }
)
ACE_KEYSCALE_RE = re.compile(r"^[A-G][#b]? (major|minor)$")


def assert_ace_encoder_widgets(node: dict[str, Any], *, where: str = "") -> list:
    """Assert native ACE 1.5 encoder widget order and combo membership.

    Arguments:
        node: graph node dict with type TextEncodeAceStepAudio1.5
        where: label included in assertion messages (graph id / title)
    Returns:
        widgets_values list after the checks pass
    """
    label = where or str(node.get("title") or node.get("id") or ACE_ENCODER_TYPE)
    widgets = node.get("widgets_values") or []
    assert isinstance(widgets, list), f"{label}: widgets_values must be a list"
    assert len(widgets) == ACE_WIDGET_COUNT, (
        f"{label}: expected {ACE_WIDGET_COUNT} ACE widgets "
        f"(seed + control_after_generate), got {len(widgets)}: {widgets!r}"
    )
    assert widgets[3] in ACE_SEED_CONTROL, (
        f"{label}: widgets[3] must be seed control_after_generate "
        f"{sorted(ACE_SEED_CONTROL)}, got {widgets[3]!r}"
    )
    assert widgets[6] in ACE_TIMESIGNATURE, (
        f"{label}: timesignature widgets[6] must be one of "
        f"{sorted(ACE_TIMESIGNATURE)}, got {widgets[6]!r}"
    )
    assert widgets[7] in ACE_LANGUAGE, (
        f"{label}: language widgets[7] must be an ACE language combo "
        f"value, got {widgets[7]!r}"
    )
    assert isinstance(widgets[8], str) and ACE_KEYSCALE_RE.match(widgets[8]), (
        f"{label}: keyscale widgets[8] must look like 'C minor', got {widgets[8]!r}"
    )
    assert isinstance(widgets[9], bool), (
        f"{label}: generate_audio_codes widgets[9] must be bool, got {widgets[9]!r}"
    )
    return widgets


def iter_ace_encoders(graph: dict[str, Any]):
    """Yield TextEncodeAceStepAudio1.5 nodes from a lab graph."""
    for node in graph.get("nodes") or []:
        if node.get("type") == ACE_ENCODER_TYPE:
            yield node
