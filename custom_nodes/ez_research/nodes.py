"""ComfyUI node: creative research chat (occupancy llm)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from ez_prompt_enhance.samples import CUSTOM, resolve_prompt, sample_combo_labels

from .pipeline import ResearchResult, run_chat, run_research, write_brief

if TYPE_CHECKING:
    from ez_common import ComfyInputTypes

# Default web-search widget and seed research question.
_WEB_SEARCH_BOOL = (
    "BOOLEAN",
    {
        "default": True,
        "label_on": "On",
        "label_off": "Off",
        "tooltip": "On lets the node pull public web pages for its sources; "
        "off keeps the whole answer on-box.",
    },
)

_DEFAULT_MESSAGE = (
    "What lighting and camera language fits a night rooftop still of a techno "
    "wizard in a tropical city?"
)


def _as_bool(value: object) -> bool:
    """Coerce a Comfy widget value to bool.

    Args:
        value: BOOLEAN widget or loose truthy token.

    Returns:
        Parsed boolean.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


class ResearchUiBlocks(TypedDict):
    """Preview blocks the research node renders in the canvas widget."""

    text: tuple[str, ...]
    """Reply body shown in the text preview."""

    sources: tuple[str, ...]
    """Numbered source lines under the reply."""

    passthrough: tuple[str, ...]
    """Status token carried through the graph."""


class ResearchUiResult(TypedDict):
    """``OUTPUT_NODE`` payload for :class:`EZCreativeResearch`."""

    ui: ResearchUiBlocks
    """Frontend display blocks."""

    result: tuple[str, ...]
    """Reply STRING that continues the graph."""


def _pack(result: ResearchResult) -> ResearchUiResult:
    """Build the Comfy output-node payload for a research result.

    Args:
        result: Chat or research reply.

    Returns:
        UI text/sources/status plus STRING result.
    """
    return {
        "ui": {
            "text": (result.text,),
            "sources": (result.sources,),
            "passthrough": (result.status,),
        },
        "result": (result.text,),
    }


class EZCreativeResearch:
    """CPU chat / research desk for the creative process (no UNET)."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for this node.

        Returns:
            Required widget map (sample, prompt, mode, search, subagents).
        """
        return {
            "required": {
                "sample": (
                    sample_combo_labels("research_chat"),
                    {
                        "default": CUSTOM,
                        "tooltip": "Pick a lab research question to start "
                        "from, or Custom to write your own.",
                    },
                ),
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": _DEFAULT_MESSAGE,
                        "dynamicPrompts": False,
                        "tooltip": "Type your question here; this text is "
                        "used when Sample is Custom.",
                    },
                ),
                "mode": (
                    ["chat", "research"],
                    {
                        "default": "research",
                        "tooltip": "research plans several questions and "
                        "writes a brief from the answers; chat is one quick "
                        "reply.",
                    },
                ),
                "web_search": _WEB_SEARCH_BOOL,
                "subagents": (
                    "INT",
                    {
                        "default": 2,
                        "min": 1,
                        "max": 3,
                        "tooltip": "How many search questions the planner may "
                        "run, 1 to 3; more questions widen the brief.",
                    },
                ),
                "history": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "dynamicPrompts": False,
                        "tooltip": "Paste the earlier turns here so the reply "
                        "keeps the thread.",
                    },
                ),
                "catalog": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                        "tooltip": "Normally leave what the graph shipped: it "
                        "names the sample file the Sample list reads, and "
                        "blank falls back to this node's own catalog.",
                    },
                ),
            }
        }

    # Comfy node contract.
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("reply",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/research"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Creative-process chat with optional web search and sequential research "
        "subagents. Occupancy llm: GPU 35B sidecar when llm-desk is up, else "
        "on-box 4B. Handoff Prompt Forge or Spark Still. Fail-soft without a GGUF."
    )

    def run(
        self,
        prompt: str,
        mode: str = "research",
        web_search: bool = True,
        subagents: int = 2,
        history: str = "",
        sample: str = CUSTOM,
        catalog: str = "",
    ) -> ResearchUiResult:
        """Run chat or planner->search->synth and write a research brief.

        Args:
            prompt: Operator question or sample override.
            mode: ``chat`` or ``research``.
            web_search: When true, fetch SSRF-safe sources.
            subagents: Planner query count (clamped 1-3).
            history: Prior turns.
            sample: Prompt catalog sample id.
            catalog: Optional sample catalog override.

        Returns:
            Comfy output-node payload with the reply STRING.
        """
        message = resolve_prompt(
            catalog,
            sample,
            prompt,
            node_type="EZCreativeResearch",
            mode=str(mode or ""),
        )
        hist = history if isinstance(history, str) else str(history or "")
        kind = str(mode or "research").strip().lower()
        do_search = _as_bool(web_search)
        if kind == "chat":
            result = run_chat(message, history=hist, web_search=do_search)
        else:
            result = run_research(
                message,
                history=hist,
                web_search=do_search,
                subagents=subagents,
            )
        write_brief(result, message)
        return _pack(result)


# Comfy custom-node registries.
NODE_CLASS_MAPPINGS = {
    "EZCreativeResearch": EZCreativeResearch,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EZCreativeResearch": "Creative Research",
}
