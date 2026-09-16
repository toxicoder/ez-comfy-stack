"""ComfyUI node: clone a lab graph into live _user/ (occupancy llm)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from ez_prompt_enhance.samples import CUSTOM, resolve_prompt, sample_combo_labels

from .pipeline import AUTO, ForgeResult, generate_app, template_combo_labels

if TYPE_CHECKING:
    from ez_common import ComfyInputTypes

# Default as_app BOOLEAN widget and seed brief.
_BOOL = (
    "BOOLEAN",
    {"default": True, "label_on": "On", "label_off": "Off"},
)

_DEFAULT_BRIEF = (
    "1:1 IG still of a chipped cobalt mug on pale stone, unmarked surfaces."
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


def _pack(result: ForgeResult) -> dict[str, Any]:
    """Build the Comfy output-node payload for a forge result.

    Args:
        result: Clone outcome.

    Returns:
        UI summary plus STRING path (or error).
    """
    summary = result.path if result.ok else (result.error or "failed")
    widgets = ", ".join(result.widgets) if result.widgets else "(none)"
    return {
        "ui": {
            "text": (summary,),
            "template": (result.template,),
            "occupancy": (result.occupancy,),
            "widgets": (widgets,),
            "passthrough": (result.status or result.error or ""),
        },
        "result": (summary,),
    }


class EZAppForge:
    """CPU desk that clones a shipped lab graph into live `_user/`."""

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return Comfy widget specs for this node.

        Returns:
            Required widget map (sample, prompt, template, slug, flags).
        """
        templates = template_combo_labels()
        if AUTO not in templates:
            templates = [AUTO, *templates]
        return {
            "required": {
                "sample": (sample_combo_labels("app_forge"), {"default": CUSTOM}),
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": _DEFAULT_BRIEF,
                        "dynamicPrompts": False,
                    },
                ),
                "template": (templates, {"default": AUTO}),
                "slug": ("STRING", {"default": "mug-ig", "multiline": False}),
                "as_app": _BOOL,
                "overwrite": (
                    "BOOLEAN",
                    {"default": False, "label_on": "On", "label_off": "Off"},
                ),
                "catalog": ("STRING", {"default": "", "multiline": False}),
            }
        }

    # Comfy node contract.
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("path",)
    FUNCTION = "run"
    CATEGORY = "ez-comfy/studio"
    OUTPUT_NODE = True
    DESCRIPTION = (
        "Clone a shipped lab graph into live _user/ as a new App. Occupancy llm: "
        "GPU 35B sidecar when llm-desk is up, else on-box 4B or keyword heuristic. "
        "Does not Queue. Does not write _lab. Handoff Prompt Forge or Spark Still. "
        "Fail-soft without a GGUF."
    )

    def run(
        self,
        prompt: object,
        template: object = AUTO,
        slug: object = "mug-ig",
        as_app: object = True,
        overwrite: object = False,
        sample: object = CUSTOM,
        catalog: object = "",
    ) -> dict[str, Any]:
        """Clone a lab graph into live `_user/` from a brief.

        Args:
            prompt: Operator brief or sample override.
            template: Lab rel or ``auto``.
            slug: Destination stem under `_user/`.
            as_app: Write ``.app.json`` when true.
            overwrite: Replace an existing `_user` graph.
            sample: Prompt catalog sample id.
            catalog: Optional sample catalog override.

        Returns:
            Comfy output-node payload with the saved path or error.
        """
        brief = resolve_prompt(
            catalog,
            sample,
            prompt,
            node_type="EZAppForge",
            mode="",
        )
        result = generate_app(
            brief,
            template=str(template or AUTO),
            slug=str(slug or ""),
            as_app=_as_bool(as_app),
            overwrite=_as_bool(overwrite),
        )
        return _pack(result)


# Comfy custom-node registries.
NODE_CLASS_MAPPINGS = {
    "EZAppForge": EZAppForge,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EZAppForge": "App Forge",
}
