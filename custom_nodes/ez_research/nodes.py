"""ComfyUI node: creative research chat (occupancy llm)."""

from __future__ import annotations

from .pipeline import ResearchResult, run_chat, run_research, write_brief

_WEB_SEARCH_BOOL = (
    "BOOLEAN",
    {"default": True, "label_on": "On", "label_off": "Off"},
)

_DEFAULT_MESSAGE = (
    "What lighting and camera language fits a night rooftop still of a techno "
    "wizard in a tropical city?"
)


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def _pack(result: ResearchResult) -> dict:
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
    def INPUT_TYPES(cls) -> dict:
        return {
            "required": {
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": _DEFAULT_MESSAGE,
                        "dynamicPrompts": False,
                    },
                ),
                "mode": (["chat", "research"], {"default": "research"}),
                "web_search": _WEB_SEARCH_BOOL,
                "subagents": ("INT", {"default": 2, "min": 1, "max": 3}),
                "history": (
                    "STRING",
                    {"multiline": True, "default": "", "dynamicPrompts": False},
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("reply",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/research"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Creative-process chat with optional web search and sequential research "
        "subagents. Occupancy llm: on-box Qwen3-4B-Instruct GGUF, CPU only. "
        "Handoff Prompt Forge or Spark Still. Fail-soft without a GGUF."
    )

    def run(
        self,
        prompt: object,
        mode: object = "research",
        web_search: object = True,
        subagents: object = 2,
        history: object = "",
    ) -> dict:
        message = prompt if isinstance(prompt, str) else str(prompt or "")
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


NODE_CLASS_MAPPINGS = {
    "EZCreativeResearch": EZCreativeResearch,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EZCreativeResearch": "Creative Research",
}
