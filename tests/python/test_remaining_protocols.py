"""Encyclopedia façade, podcast OptionalBackendHook, forge helpers."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
CUSTOM = ROOT / "custom_nodes"
if str(DOCS) not in sys.path:
    sys.path.insert(0, str(DOCS))
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_podcast import nodes as podcast  # noqa: E402
from ez_studio_forge import pipeline as forge  # noqa: E402
from workflow_nodes import ACE_LANGUAGE_CHOICES, encyclopedia  # noqa: E402
from workflow_nodes_core import core_nodes  # noqa: E402
from workflow_nodes_enhance import enhance_nodes  # noqa: E402
from workflow_nodes_ltx import ltx_nodes  # noqa: E402
from workflow_nodes_packs import pack_nodes  # noqa: E402
from workflow_nodes_trellis import trellis_nodes  # noqa: E402
from workflow_nodes_vhs_ace import vhs_ace_nodes  # noqa: E402


def test_encyclopedia_concatenates_families() -> None:
    enc = encyclopedia()
    families = [
        core_nodes(),
        vhs_ace_nodes(),
        ltx_nodes(),
        trellis_nodes(),
        enhance_nodes(),
        pack_nodes(),
    ]
    merged: dict[str, Any] = {}
    for part in families:
        merged.update(part)
    assert set(enc) == set(merged)
    assert "KSampler" in enc
    assert "VHS_VideoCombine" in enc
    assert "EZKleinPromptEnhance" in enc
    assert "EZAppForge" in enc
    assert ACE_LANGUAGE_CHOICES[0]["id"] == "en"


def test_optional_backend_hook_protocol() -> None:
    dummy = object()
    cast(Any, podcast.OptionalBackendHook.__dict__["__call__"])(
        dummy, "hi", "chatterbox", "ref.wav"
    )
    assert podcast.optional_backend_hook is None


def test_forge_planner_skips_when_template_pinned() -> None:
    plan, status, reason = forge._planner_result(  # noqa: SLF001
        "still of a mug", "klein/still-draft", use_llm=True
    )
    assert plan is None
    assert status == "heuristic"
    assert reason == "keyword heuristic"
