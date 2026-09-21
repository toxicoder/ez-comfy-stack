"""Hand-authored encyclopedia of every Comfy node type used in workflows/_lab.

Widget order matches lab JSON ``widgets_values`` (list index or VHS dict key).
Combo lists are ComfyUI v0.37.0 INPUT_TYPES, lab ez_* INPUT_TYPES, or the ACE
encoder contract in tests/python/_ace_widgets_contract.py.

Do not invent sampler/CLIP/VHS values. Lab-specific generation effects live
in ``lab_notes`` and each widget's ``generation`` field.

Family tables live in ``workflow_nodes_*.py``; this module concatenates them.
"""

from __future__ import annotations

from typing import Any

from workflow_nodes_core import core_nodes
from workflow_nodes_enhance import enhance_nodes
from workflow_nodes_lib import ACE_KEYSCALE_CHOICES, ACE_LANGUAGE_CHOICES
from workflow_nodes_ltx import ltx_nodes
from workflow_nodes_packs import pack_nodes
from workflow_nodes_trellis import trellis_nodes
from workflow_nodes_vhs_ace import vhs_ace_nodes

__all__ = [
    "ACE_KEYSCALE_CHOICES",
    "ACE_LANGUAGE_CHOICES",
    "encyclopedia",
]


def encyclopedia() -> dict[str, Any]:
    """Return the node encyclopedia keyed by Comfy type.

    Returns:
        Mapping of node type → spec.
    """
    nodes: dict[str, Any] = {}
    nodes.update(core_nodes())
    nodes.update(vhs_ace_nodes())
    nodes.update(ltx_nodes())
    nodes.update(trellis_nodes())
    nodes.update(enhance_nodes())
    nodes.update(pack_nodes())
    return nodes
