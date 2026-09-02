"""Hermetic tests for ez_prompt_enhance (no Comfy, no network)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_prompt_enhance import client  # noqa: E402
from ez_prompt_enhance.nodes import (  # noqa: E402
    EZKleinPromptEnhance,
    EZLTXPromptEnhance,
    EZWanPromptEnhance,
    NODE_CLASS_MAPPINGS,
)


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: object) -> bool:
        return False


def _completion(text: str) -> dict:
    return {"choices": [{"message": {"content": text}}]}


def test_system_prompts_encode_model_rules() -> None:
    klein = client.load_system_prompt("klein_t2i")
    assert "Qwen3-4B" in klein
    assert "<|im_start|>" in klein
    assert "sentences" in klein.lower()
    edit = client.load_system_prompt("klein_edit")
    assert "identity" in edit.lower()
    wan_t2v = client.load_system_prompt("wan_t2v")
    assert "80" in wan_t2v and "120" in wan_t2v
    assert "audio" in wan_t2v.lower()
    wan_i2v = client.load_system_prompt("wan_i2v")
    assert "Motion + Camera" in wan_i2v
    assert "audio" in wan_i2v.lower()
    ltx_t2v = client.load_system_prompt("ltx_t2v")
    assert "present" in ltx_t2v.lower()
    assert "quotation" in ltx_t2v.lower()
    assert "interleaved" in ltx_t2v.lower()
    ltx_i2v = client.load_system_prompt("ltx_i2v")
    assert "first frame" in ltx_i2v.lower()
    assert "camera motion" in ltx_i2v.lower()


def test_strip_fences_and_quotes() -> None:
    fenced = "```text\nA red bicycle leans on brick.\n```"
    assert client.strip_model_wrapping(fenced) == "A red bicycle leans on brick."
    assert client.strip_model_wrapping('"A red bicycle."') == "A red bicycle."


def test_enhance_false_skips_api(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XAI_API_KEY", "xai-test")
    with patch.object(client.urllib.request, "urlopen") as opener:
        out = client.enhance_prompt("sys", "lazy bike", enhance=False)
    assert out == "lazy bike"
    opener.assert_not_called()


def test_missing_key_passthrough(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    with patch.object(client.urllib.request, "urlopen") as opener:
        out = client.enhance_prompt("sys", "lazy bike", enhance=True)
    assert out == "lazy bike"
    opener.assert_not_called()


def test_http_error_passthrough(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XAI_API_KEY", "xai-test")

    def boom(*_args: object, **_kwargs: object) -> object:
        raise HTTPError("https://api.x.ai/v1/chat/completions", 401, "nope", hdrs=None, fp=MagicMock(read=lambda: b"denied"))

    with patch.object(client.urllib.request, "urlopen", side_effect=boom):
        out = client.enhance_prompt("sys", "lazy bike", enhance=True)
    assert out == "lazy bike"


def test_timeout_passthrough(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XAI_API_KEY", "xai-test")
    with patch.object(client.urllib.request, "urlopen", side_effect=URLError("timed out")):
        out = client.enhance_prompt("sys", "lazy bike", enhance=True)
    assert out == "lazy bike"


def test_success_strips_fences(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XAI_API_KEY", "xai-test")
    monkeypatch.setenv("XAI_MODEL", "grok-4.6")
    fake = _FakeResponse(_completion("```\nA photoreal still of a red bicycle.\n```"))
    with patch.object(client.urllib.request, "urlopen", return_value=fake) as opener:
        out = client.enhance_prompt("sys", "red bike", enhance=True)
    assert out == "A photoreal still of a red bicycle."
    opener.assert_called_once()
    request = opener.call_args[0][0]
    assert request.full_url.endswith("/chat/completions")
    body = json.loads(request.data.decode("utf-8"))
    assert body["model"] == "grok-4.6"
    assert body["temperature"] == 0


def test_lab_graphs_use_model_native_prompts_and_enhance_nodes() -> None:
    wf = ROOT / "workflows"
    draft = json.loads((wf / "still-draft-lab-example.json").read_text(encoding="utf-8"))
    hero = json.loads((wf / "still-hero-lab-example.json").read_text(encoding="utf-8"))
    klein_d = next(n for n in draft["nodes"] if n.get("type") == "EZKleinPromptEnhance")
    klein_h = next(n for n in hero["nodes"] if n.get("type") == "EZKleinPromptEnhance")
    assert klein_d["widgets_values"][0] == klein_h["widgets_values"][0]
    assert klein_d["widgets_values"][1] is False
    wan_t = json.loads((wf / "wan-t2v-draft-lab-example.json").read_text(encoding="utf-8"))
    wan_i = json.loads((wf / "wan-i2v-draft-lab-example.json").read_text(encoding="utf-8"))
    ltx_t = json.loads((wf / "ltx-t2v-hero-lab-example.json").read_text(encoding="utf-8"))
    ltx_i = json.loads((wf / "ltx-i2v-hero-lab-example.json").read_text(encoding="utf-8"))
    wan_tp = next(n for n in wan_t["nodes"] if n.get("type") == "EZWanPromptEnhance")["widgets_values"][0]
    wan_ip = next(n for n in wan_i["nodes"] if n.get("type") == "EZWanPromptEnhance")["widgets_values"][0]
    ltx_tp = next(n for n in ltx_t["nodes"] if n.get("type") == "EZLTXPromptEnhance")["widgets_values"][0]
    ltx_ip = next(n for n in ltx_i["nodes"] if n.get("type") == "EZLTXPromptEnhance")["widgets_values"][0]
    assert "dollies" in wan_tp.lower() or "dolly" in wan_tp.lower()
    assert "score" not in wan_tp.lower()
    assert "start-image" in wan_ip.lower() or "start image" in wan_ip.lower()
    assert "score" not in wan_ip.lower()
    assert "YouTube 16:9 still:" not in wan_tp
    assert "footsteps" in ltx_tp.lower() or "bell" in ltx_tp.lower()
    assert "no score" in ltx_ip.lower() or "no music" in ltx_ip.lower()
    assert not any(
        n.get("type") == "CLIPTextEncode" and n.get("title") == "Positive"
        for n in wan_i["nodes"]
    )


def test_node_mappings_and_modes() -> None:
    assert set(NODE_CLASS_MAPPINGS) == {
        "EZKleinPromptEnhance",
        "EZWanPromptEnhance",
        "EZLTXPromptEnhance",
    }
    klein = EZKleinPromptEnhance()
    wan = EZWanPromptEnhance()
    ltx = EZLTXPromptEnhance()
    off = klein.run("A red bicycle.", False, "t2i", "YouTube 16:9 still")
    assert off["result"] == ("A red bicycle.",)
    with patch.object(client, "chat_complete", return_value="rewritten-klein") as mock:
        on = klein.run("bike", True, "edit", "")
    assert on["result"] == ("rewritten-klein",)
    system = mock.call_args[0][0]
    assert "identity" in system.lower()
    with patch.object(client, "chat_complete", return_value="rewritten-wan") as mock:
        wan.run("push in", True, "i2v", "5 seconds, 24 fps")
    assert "Motion + Camera" in mock.call_args[0][0]
    with patch.object(client, "chat_complete", return_value="rewritten-ltx") as mock:
        ltx.run("bike moves", True, "t2v", "5 seconds, 24 fps", audio_notes="wind, no score")
    user = mock.call_args[0][1]
    assert "Audio notes: wind, no score" in user
    assert "Duration / framing: 5 seconds, 24 fps" in user
