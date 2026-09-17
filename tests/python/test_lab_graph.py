"""Shared lab Graph, EnhanceSchema, and Protocol fakes."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
TESTS = Path(__file__).resolve().parent
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

from _enhance_schema import ENHANCE_WIDGET_ORDER, enhance_mode  # noqa: E402
from _fakes import (  # noqa: E402
    FakeChatCompleter,
    FakeFfmpegRun,
    FakeFolderPaths,
    FakeProgress,
    FakeSidecarTransport,
    FakeWhisperModel,
)
from _lab_graph import Graph  # noqa: E402
from ez_common import ProgressReporter  # noqa: E402
from ez_film.protocols import FfmpegRun  # noqa: E402
from ez_prompt_enhance.nodes import (  # noqa: E402
    EZAceStepPromptEnhance,
    EZDreamXPromptEnhance,
    EZKleinPromptEnhance,
    EZLongCatPromptEnhance,
    EZLTXPromptEnhance,
    EZWanPromptEnhance,
    EZZimagePromptEnhance,
)
from ez_prompt_enhance.protocols import ChatCompleter, SidecarTransport  # noqa: E402


def _tiny(g: Graph) -> None:
    g.add(
        1,
        "SaveAudio",
        [800.0, 400.0],
        [200.0, 80.0],
        "Save",
        ["ez"],
        inputs=[g.inp("audio", "AUDIO")],
        outputs=[],
    )


def test_graph_dump_flags_keep_identity() -> None:
    g = Graph("audio/podcast/two-host-episode", pop_lab_rel=False, enable_lab=True)
    _tiny(g)
    dumped = g.dump({"groups": [], "lab_note": "n"})
    assert dumped["id"] == "two-host-episode"
    assert dumped["extra"]["lab_rel"] == "audio/podcast/two-host-episode"

    dub = Graph("audio/dub/clone-translate")
    _tiny(dub)
    dumped_dub = dub.dump(
        {"groups": [], "lab_rel": "audio/dub/clone-translate", "lab_note": "n"}
    )
    assert dumped_dub["id"] == "clone-translate"
    assert dumped_dub["extra"]["lab_rel"] == "audio/dub/clone-translate"


def test_enhance_schema_matches_input_types() -> None:
    classes: dict[str, Any] = {
        "EZKleinPromptEnhance": EZKleinPromptEnhance,
        "EZWanPromptEnhance": EZWanPromptEnhance,
        "EZLTXPromptEnhance": EZLTXPromptEnhance,
        "EZZimagePromptEnhance": EZZimagePromptEnhance,
        "EZLongCatPromptEnhance": EZLongCatPromptEnhance,
        "EZDreamXPromptEnhance": EZDreamXPromptEnhance,
        "EZAceStepPromptEnhance": EZAceStepPromptEnhance,
    }
    for ntype, cls in classes.items():
        required = list(cls.INPUT_TYPES()["required"].keys())
        assert tuple(required) == ENHANCE_WIDGET_ORDER[ntype]


def test_enhance_mode_uses_named_index() -> None:
    klein = {
        "type": "EZKleinPromptEnhance",
        "widgets_values": ["custom", "p", True, "edit", "16:9", "none", ""],
    }
    assert enhance_mode(klein) == "edit"
    zimage = {"type": "EZZimagePromptEnhance", "widgets_values": []}
    assert enhance_mode(zimage) == "t2i"
    ace = {
        "type": "EZAceStepPromptEnhance",
        "widgets_values": ["custom", "tags", "lyrics", True, "instrumental", ""],
    }
    assert enhance_mode(ace) == "instrumental"
    assert enhance_mode({"type": "EZKleinPromptEnhance", "widgets_values": []}) == ""


def test_protocol_fakes_match_seams() -> None:
    bar: ProgressReporter = FakeProgress()
    bar.update(1)
    bar.update_absolute(0)
    runner: FfmpegRun = FakeFfmpegRun()
    proc = FakeFfmpegRun()(["ffmpeg"], check=False, capture_output=True, text=True)
    assert runner is not None
    assert proc.returncode == 0
    chat: ChatCompleter = FakeChatCompleter()
    text, reason = chat.complete("sys", "user")
    assert text == "user"
    assert reason is None
    transport: SidecarTransport = FakeSidecarTransport()
    assert transport is not None
    with FakeSidecarTransport().urlopen(object(), 1.0) as resp:
        assert resp.read() == b"{}"
    folders = FakeFolderPaths(Path("/tmp"))
    assert folders.get_output_directory() == "/tmp"
    assert FakeWhisperModel().transcribe("a.wav") == []
