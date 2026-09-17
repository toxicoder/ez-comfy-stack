"""Prompt-enhance Protocols and style-module façade."""

from __future__ import annotations

from typing import Any, cast

from ez_prompt_enhance import _styles, client, protocols
from ez_prompt_enhance.nodes import (
    EZKleinPromptEnhance,
    EZLTXPromptEnhance,
    EZZimagePromptEnhance,
)


def test_style_helpers_reexport_from_client() -> None:
    assert client.style_ids is _styles.style_ids
    assert client.apply_style_to_prompt is _styles.apply_style_to_prompt
    assert client.flavor_for_system is _styles.flavor_for_system
    assert "none" in client.style_ids()


def test_visual_input_types_key_order() -> None:
    klein = EZKleinPromptEnhance.INPUT_TYPES()["required"]
    assert list(klein.keys()) == [
        "sample",
        "prompt",
        "enhance",
        "mode",
        "duration_hint",
        "style",
        "catalog",
    ]
    zimage = EZZimagePromptEnhance.INPUT_TYPES()["required"]
    assert list(zimage.keys()) == [
        "sample",
        "prompt",
        "enhance",
        "duration_hint",
        "style",
        "catalog",
    ]
    ltx = EZLTXPromptEnhance.INPUT_TYPES()["required"]
    assert list(ltx.keys()) == [
        "sample",
        "prompt",
        "enhance",
        "mode",
        "duration_hint",
        "audio_notes",
        "style",
        "catalog",
    ]


def test_protocol_stubs_execute() -> None:
    dummy = object()
    cast(Any, protocols.ChatCompleter.complete)(
        dummy, "sys", "user", max_tokens=8, unload=False
    )
    cast(Any, protocols.SidecarTransport.urlopen)(dummy, object(), 1.0)
    cast(Any, protocols.StyleCatalog.ids)(dummy)
    cast(Any, protocols.StyleCatalog.apply)(dummy, "text", "none")
    cast(Any, protocols.SystemPrompts.load)(dummy, "klein_t2i")
    cast(Any, protocols.LlamaLoader.get)(dummy)
