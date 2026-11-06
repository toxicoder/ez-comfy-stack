"""ez-comfy editing lane: agent-driven in-browser video editor + MCP.

Import is hermetic: stdlib only at pack load. Routes attach fail-soft when
PromptServer exists (pytest-safe, mirrors ``ez_outputs``). Heavy work (ffmpeg
server renders, agent completions) is lazy and occupancy-gated.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ez_common import NodeRegistry

NODE_CLASS_MAPPINGS: NodeRegistry = {}
"""No canvas nodes yet - the lane runs on routes, the panel, and MCP."""

NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {}
"""Display names for :data:`NODE_CLASS_MAPPINGS`."""

WEB_DIRECTORY = "./js"
"""Comfy frontend extension directory (chat + timeline panel)."""

try:  # fail-soft: no PromptServer under plain pytest
    from .routes import register_routes

    register_routes()
except Exception:  # noqa: BLE001 - Comfy optional at pack import
    pass

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]
