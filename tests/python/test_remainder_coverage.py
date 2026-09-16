"""Hermetic remainder coverage for prompt enhance, podcast, research, music, docs."""

from __future__ import annotations

import importlib.util
import ipaddress
import json
import os
import runpy
import subprocess
import sys
import types
from concurrent.futures import TimeoutError as FuturesTimeout
from pathlib import Path
from collections.abc import Iterator
from typing import Any
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_prompt_enhance import client  # noqa: E402
from ez_prompt_enhance import samples as samp  # noqa: E402
from ez_prompt_enhance.nodes import (  # noqa: E402
    EZAceStepPromptEnhance,
    EZNegativePromptEnhance,
    EZSamplePrompt,
    EZWanPromptEnhance,
    _as_bool,
    _compose_user,
    _family_id,
    _style_id,
    sanitize_instrumental_lyrics,
)
from ez_podcast import nodes as podcast  # noqa: E402
from ez_podcast.nodes import EZKokoroTTS, EZPodcastScript  # noqa: E402
from ez_research import nodes as research_nodes  # noqa: E402
from ez_research import pipeline  # noqa: E402
from ez_research import search  # noqa: E402
from ez_research.nodes import EZCreativeResearch  # noqa: E402
from ez_research.search import SearchHit  # noqa: E402
from ez_music import metadata as music_meta  # noqa: E402
from ez_music import nodes as music_nodes  # noqa: E402
from ez_music.diss_examples import finalize_nill_album, nill_slug_from_stem  # noqa: E402
from ez_music.edm_examples import (  # noqa: E402
    _uniquify_score,
    drive_slug_from_stem,
    finalize_drive_album,
)
from ez_music.naming import title_case_song  # noqa: E402
from ez_music.nodes import EZAlbumPack, EZAudioMetadata, EZRapLyrics  # noqa: E402
from ez_music.pack import pack_album, write_m3u  # noqa: E402

_REAL_PIP_INSTALL = client._pip_install
_REAL_URLOPEN_SIDECAR = client._urlopen_sidecar


@pytest.fixture(autouse=True)
def _reset_llama(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    client.reset_llama_runtime_for_tests()
    monkeypatch.setattr(
        client,
        "_pip_install",
        lambda args: subprocess.CompletedProcess(
            args=["pip", "install", *args],
            returncode=1,
            stdout="",
            stderr="test: pip disabled",
        ),
    )
    monkeypatch.setattr(
        client,
        "_urlopen_sidecar",
        lambda *_a, **_k: (_ for _ in ()).throw(TimeoutError("sidecar down")),
    )
    yield
    client.reset_llama_runtime_for_tests()
    client._STYLES = None
    client._VIEWS = None
    if hasattr(samp.load_index, "cache_clear"):
        samp.load_index.cache_clear()
    if hasattr(samp.load_catalog, "cache_clear"):
        samp.load_catalog.cache_clear()
    if hasattr(samp._sample_combo_labels_cached, "cache_clear"):
        samp._sample_combo_labels_cached.cache_clear()


def _load_docs(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# --- ez_prompt_enhance.client -------------------------------------------------


def test_client_wheel_url_unknown_and_amd64(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client.platform, "machine", lambda: "riscv64")
    assert client.llama_cpp_direct_wheel_url() == ""
    assert client.llama_cpp_direct_wheel_pip_args() == []
    monkeypatch.setattr(client.platform, "machine", lambda: "amd64")
    url = client.llama_cpp_direct_wheel_url()
    assert "x86_64" in url
    monkeypatch.setattr(client.platform, "machine", lambda: "x86_64")
    assert "x86_64" in client.llama_cpp_direct_wheel_url()
    monkeypatch.setattr(client.platform, "machine", lambda: "arm64")
    assert "aarch64" in client.llama_cpp_direct_wheel_url()
    monkeypatch.setattr(client.platform, "machine", lambda: "aarch64")
    assert "aarch64" in client.llama_cpp_direct_wheel_url()


def test_client_pip_timeout_and_short_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _timeout(*_a: object, **_k: object) -> object:
        raise subprocess.TimeoutExpired(cmd="pip", timeout=1)

    monkeypatch.setattr(client, "_pip_install", _REAL_PIP_INSTALL)
    monkeypatch.setattr(client.subprocess, "run", _timeout)
    proc = client._pip_install(["pkg"])
    assert proc.returncode == 1
    assert "timed out" in proc.stderr
    empty = subprocess.CompletedProcess(args=["pip"], returncode=9, stdout="", stderr="")
    assert client._short_pip_error(empty) == "pip exit 9"


def test_client_forget_llama_and_heal_success(monkeypatch: pytest.MonkeyPatch) -> None:
    sys.modules["llama_cpp"] = types.ModuleType("llama_cpp")
    sys.modules["llama_cpp.inner"] = types.ModuleType("llama_cpp.inner")
    client._forget_llama_module()
    assert "llama_cpp" not in sys.modules
    calls = {"n": 0}

    def _pip(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls["n"] += 1
        return subprocess.CompletedProcess(
            args=["pip", *args], returncode=0, stdout="ok", stderr=""
        )

    monkeypatch.setattr(client, "_pip_install", _pip)
    monkeypatch.setattr(client, "_load_llama_class", lambda: object())
    assert client._heal_llama_cpp_cpu() == ""
    assert calls["n"] == 1
    assert client._heal_llama_cpp_cpu() == ""


def test_client_heal_direct_wheel_success(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[list[str]] = []

    def _pip(args: list[str]) -> subprocess.CompletedProcess[str]:
        seen.append(list(args))
        if "--force-reinstall" in args:
            return subprocess.CompletedProcess(args=["pip"], returncode=0, stdout="", stderr="")
        return subprocess.CompletedProcess(args=["pip"], returncode=1, stdout="", stderr="miss")

    monkeypatch.setattr(client, "_pip_install", _pip)
    monkeypatch.setattr(client, "_load_llama_class", lambda: object())
    err = client._heal_llama_cpp_cpu()
    assert err == ""
    assert any("--force-reinstall" in row for row in seen)


def test_client_unavailable_status_pip_detail() -> None:
    client._HEAL_PIP_FAILED = False
    client._HEAL_ERROR = "wheel missing"
    client._LAST_IMPORT_ERROR = ""
    text = client.llama_cpp_unavailable_status()
    assert "Llama import failed" in text
    assert "wheel missing" in text


def test_client_load_views_and_styles_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    views = tmp_path / "views.json"
    views.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(client, "VIEWS_PATH", views)
    client._VIEWS = None
    with pytest.raises(ValueError, match="object"):
        client.load_view_pack("x")
    views.write_text('{"pack": "nope"}', encoding="utf-8")
    client._VIEWS = None
    with pytest.raises(ValueError, match="list"):
        client.load_view_pack("pack")
    views.write_text('{"pack": [1]}', encoding="utf-8")
    client._VIEWS = None
    with pytest.raises(ValueError, match="objects"):
        client.load_view_pack("pack")
    views.write_text('{"pack": [{"label": "", "shot": "x"}]}', encoding="utf-8")
    client._VIEWS = None
    with pytest.raises(ValueError, match="label"):
        client.load_view_pack("pack")
    views.write_text('{"pack": [{"label": "a", "shot": "b"}]}', encoding="utf-8")
    client._VIEWS = None
    assert client.load_view_pack("pack")[0]["shot"] == "b"
    with pytest.raises(KeyError):
        client.load_view_pack("missing")
    styles = tmp_path / "styles.json"
    styles.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(client, "STYLES_PATH", styles)
    client._STYLES = None
    with pytest.raises(ValueError, match="object"):
        client.load_styles()
    styles.write_text('{"a": 1}', encoding="utf-8")
    client._STYLES = None
    with pytest.raises(ValueError, match="must be an object"):
        client.load_styles()


def test_client_string_list_and_style_helpers() -> None:
    assert client._string_list({"must_include": "  one  "}, "must_include") == ["one"]
    assert client._string_list({"must_include": "  "}, "must_include") == []
    assert client._string_list({"must_include": 3}, "must_include") == []
    assert client.style_llm_block("none") == ""
    assert client.style_suffix("none") == ""
    assert client.apply_style_to_prompt("hello", "not-a-style") == "hello"
    assert client._token_hits_blob("", "abc") is False
    assert client._token_hits_blob("watermark", "") is False
    assert client._token_hits_blob("melted geometry extra", "geometry") is True
    assert client._inferred_style_ids("") == []
    assert client.join_prompt("", "", "", "nope") == ""
    joined = client.join_prompt(None, None, None, 1)  # type: ignore[arg-type]
    assert joined == ""
    assert client.compose_context_user("", "ctx") == "Context:\nctx"


def test_client_occupancy_and_sidecar_edges(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    (tmp_path / ".occupancy.json").write_text("{not-json", encoding="utf-8")
    assert client.occupancy_mode() == "unknown"
    (tmp_path / ".occupancy.json").write_text("[]", encoding="utf-8")
    assert client.occupancy_mode() == "unknown"
    (tmp_path / ".occupancy.json").write_text('{"mode": ""}', encoding="utf-8")
    assert client.occupancy_mode() == "unknown"
    monkeypatch.setenv("COMFY_OUTPUT_DIR", "/outputs")
    assert client.occupancy_mode() in {"unknown", "idle", "llm", "ltx", "klein", "wan"}
    assert client.sidecar_occupancy_ok("") is True
    monkeypatch.setenv("EZ_LLM_SIDECAR_PORT", "nope")
    monkeypatch.setenv("EZ_LLM_SIDECAR_URL", "http://desk:9/")
    assert client.sidecar_base_url() == "http://desk:9"
    monkeypatch.setenv("EZ_LLM_TIMEOUT_S", "nope")
    assert client._sidecar_timeout_s() == float(client.DEFAULT_TIMEOUT_S)
    monkeypatch.setenv("EZ_LLM_TIMEOUT_S", "0")
    assert client._sidecar_timeout_s() == float(client.DEFAULT_TIMEOUT_S)
    monkeypatch.setenv("EZ_LLM_TIMEOUT_S", "0")
    assert client._timeout_s() == client.DEFAULT_TIMEOUT_S
    monkeypatch.setenv("EZ_LLM_N_CTX", "nope")
    assert client._n_ctx() == client.DEFAULT_N_CTX
    monkeypatch.setenv("EZ_LLM_N_CTX", "8")
    assert client._n_ctx() == client.DEFAULT_N_CTX


def test_client_sidecar_chat_branches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    (tmp_path / ".occupancy.json").write_text(json.dumps({"mode": "llm"}), encoding="utf-8")

    class _Resp:
        def __init__(self, payload: bytes) -> None:
            self._payload = payload

        def read(self) -> bytes:
            return self._payload

        def __enter__(self) -> _Resp:
            return self

        def __exit__(self, *_a: object) -> None:
            return None

    monkeypatch.setattr(client, "_urlopen_sidecar", lambda *_a, **_k: _Resp(b""))
    assert client._complete_via_sidecar("s", "u") is None

    calls = {"n": 0}

    def _open(request: object, timeout: float) -> _Resp:
        del timeout
        url = str(getattr(request, "full_url", "") or request)
        calls["n"] += 1
        if "/v1/models" in url:
            return _Resp(b'{"ok":true}')
        raise TimeoutError("chat down")

    monkeypatch.setattr(client, "_urlopen_sidecar", _open)
    assert client._complete_via_sidecar("s", "u", max_tokens=0, temperature=-1) is None

    def _bad_json(request: object, timeout: float) -> _Resp:
        del timeout
        url = str(getattr(request, "full_url", "") or request)
        if "/v1/models" in url:
            return _Resp(b'{"ok":true}')
        return _Resp(b"not-json")

    monkeypatch.setattr(client, "_urlopen_sidecar", _bad_json)
    pair = client._complete_via_sidecar("s", "u")
    assert pair is not None
    text, reason = pair
    assert text == ""
    assert reason == client.REASON_SIDECAR_EMPTY

    def _no_choices(request: object, timeout: float) -> _Resp:
        del timeout
        url = str(getattr(request, "full_url", "") or request)
        if "/v1/models" in url:
            return _Resp(b'{"ok":true}')
        return _Resp(b'{"choices":[]}')

    monkeypatch.setattr(client, "_urlopen_sidecar", _no_choices)
    pair = client._complete_via_sidecar("s", "u")
    assert pair is not None
    _text, reason = pair
    assert reason == client.REASON_SIDECAR_EMPTY

    def _empty_msg(request: object, timeout: float) -> _Resp:
        del timeout
        url = str(getattr(request, "full_url", "") or request)
        if "/v1/models" in url:
            return _Resp(b'{"ok":true}')
        return _Resp(b'{"choices":[{"message":{"content":""}}]}')

    monkeypatch.setattr(client, "_urlopen_sidecar", _empty_msg)
    pair = client._complete_via_sidecar("s", "u")
    assert pair is not None
    _text, reason = pair
    assert reason == client.REASON_SIDECAR_EMPTY


def test_client_gpu_layers_and_close_generate_complete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    (tmp_path / ".occupancy.json").write_text(json.dumps({"mode": "idle"}), encoding="utf-8")
    monkeypatch.delenv("EZ_LLM_ALLOW_GPU", raising=False)
    monkeypatch.setenv("EZ_LLM_N_GPU_LAYERS", "nope")
    assert client._n_gpu_layers() == client.DEFAULT_SIDECAR_NGL
    monkeypatch.setenv("EZ_LLM_N_GPU_LAYERS", "7")
    assert client._n_gpu_layers() == 7
    monkeypatch.delenv("EZ_LLM_N_GPU_LAYERS", raising=False)
    (tmp_path / ".occupancy.json").write_text(json.dumps({"mode": "other"}), encoding="utf-8")
    assert client._n_gpu_layers() == 0

    class _Handle:
        def close(self) -> None:
            raise RuntimeError("close fail")

    client._LLM = _Handle()
    client._LLM_PATH = "x"
    client._close_llm()
    gguf = tmp_path / "model.gguf"
    gguf.write_bytes(b"gguf")
    monkeypatch.setenv("EZ_LLM_GGUF", str(gguf))
    client._LLM = object()
    client._LLM_PATH = str(gguf)
    handle, reason = client._get_llama()
    assert handle is client._LLM
    assert reason is None

    class _BoomRetry:
        def __init__(self, **kwargs: object) -> None:
            if "chat_format" in kwargs:
                raise TypeError("no chat_format")
            raise RuntimeError("still no")

    fake = types.ModuleType("llama_cpp")
    fake.Llama = _BoomRetry  # type: ignore[attr-defined]
    client._close_llm()
    with patch.dict(sys.modules, {"llama_cpp": fake}):
        handle, reason = client._get_llama()
    assert handle is None
    assert reason == client.REASON_LLM_LOAD_FAILED

    class _NoneHeal:
        pass

    client.reset_llama_runtime_for_tests()
    monkeypatch.setattr(client, "_load_llama_class", lambda: None)
    monkeypatch.setattr(client, "_heal_llama_cpp_cpu", lambda: "heal fail")
    handle, reason = client._get_llama()
    assert reason == client.REASON_LLAMA_UNAVAILABLE
    monkeypatch.setattr(client, "_heal_llama_cpp_cpu", lambda: "")
    handle, reason = client._get_llama()
    assert reason == client.REASON_LLAMA_UNAVAILABLE

    class _BadBody:
        def create_chat_completion(self, **_k: object) -> dict[str, object]:
            return {}

    assert client._generate(_BadBody(), "s", "u", max_tokens=0, temperature=-1) == ""

    class _NonStr:
        def create_chat_completion(self, **_k: object) -> dict[str, object]:
            return {"choices": [{"message": {"content": 3}}]}

    assert client._generate(_NonStr(), "s", "u") == ""

    class _Pool:
        def __init__(self, **_k: object) -> None:
            return None

        def __enter__(self) -> _Pool:
            return self

        def __exit__(self, *_a: object) -> None:
            return None

        def submit(self, *_a: object, **_k: object) -> Any:
            class _F:
                def result(self, timeout: object = None) -> str:
                    del timeout
                    raise FuturesTimeout()

            return _F()

    monkeypatch.setattr(client, "ThreadPoolExecutor", _Pool)
    monkeypatch.setattr(client, "_get_llama", lambda: (object(), None))
    monkeypatch.setattr(client, "_complete_via_sidecar", lambda *_a, **_k: None)
    text, reason = client.complete(
        "s", "u", max_tokens=0, temperature=-1, timeout_s="bad"  # type: ignore[arg-type]
    )
    assert reason == client.REASON_EMPTY

    class _PoolExc(_Pool):
        def submit(self, *_a: object, **_k: object) -> Any:
            class _F:
                def result(self, timeout: object = None) -> str:
                    del timeout
                    raise RuntimeError("gen fail")

            return _F()

    monkeypatch.setattr(client, "ThreadPoolExecutor", _PoolExc)
    text, reason = client.complete("s", "u", timeout_s=0)
    assert reason == client.REASON_EMPTY

    class _PoolEmpty(_Pool):
        def submit(self, *_a: object, **_k: object) -> Any:
            class _F:
                def result(self, timeout: object = None) -> str:
                    del timeout
                    return "  "

            return _F()

    monkeypatch.setattr(client, "ThreadPoolExecutor", _PoolEmpty)
    monkeypatch.setenv("EZ_LLM_UNLOAD", "1")
    text, reason = client.complete("s", "u")
    assert reason == client.REASON_EMPTY
    monkeypatch.setattr(
        client, "_complete_via_sidecar", lambda *_a, **_k: ("side", None)
    )
    text, reason = client.complete("s", "u")
    assert text == "side"
    out = client.enhance_prompt("s", "u", enhance=True, fallback="   ")
    assert out.reason is None
    monkeypatch.setattr(client, "complete", lambda *_a, **_k: ("", "empty"))
    out = client.enhance_prompt("s", "u", enhance=True, fallback=12)  # type: ignore[arg-type]
    assert out.text == "12"


# --- nodes / samples ----------------------------------------------------------


def test_prompt_nodes_helpers_and_wan_vace() -> None:
    assert _as_bool(1) is True
    assert _as_bool("yes") is True
    assert _as_bool("no") is False
    assert _as_bool(object()) is False
    assert _family_id("WAN") == "wan"
    assert _family_id(None) == "klein"
    assert _style_id("missing") == "none"
    assert _compose_user("", "", "") == ""
    with patch.object(client, "complete", return_value=("vace-out", None)) as mock:
        EZWanPromptEnhance().run("join", True, "vace", "5 seconds", "anime")
    assert "join" in mock.call_args[0][0].lower() or "vace" in mock.call_args[0][0].lower()
    folded = sanitize_instrumental_lyrics("orphan cue\n\n[inst]\n\ncue two")
    assert "[inst" in folded
    types = EZSamplePrompt.INPUT_TYPES()
    assert "sample" in types["required"]
    with patch(
        "ez_prompt_enhance.nodes.load_system_prompt",
        side_effect=FileNotFoundError("missing"),
    ):
        miss = EZNegativePromptEnhance().run("watermarks", True, "klein", "")
    assert miss["ui"]["passthrough"][0] == "passthrough"
    with patch(
        "ez_prompt_enhance.nodes.complete",
        return_value=("", "empty"),
    ):
        with patch("ez_prompt_enhance.nodes.load_system_prompt", return_value="sys"):
            empty = EZNegativePromptEnhance().run("watermarks", True, "ltx", "")
    assert empty["ui"]["passthrough"][0]


def test_ace_prompt_missing_and_passthrough(monkeypatch: pytest.MonkeyPatch) -> None:
    ace = EZAceStepPromptEnhance()
    with patch(
        "ez_prompt_enhance.nodes.load_system_prompt",
        side_effect=FileNotFoundError("ace"),
    ):
        out = ace.run("tags", "[verse]\nhi", True, "vocal")
    assert out["ui"]["passthrough"][0] == "passthrough"
    with patch(
        "ez_prompt_enhance.nodes.complete",
        side_effect=[("tags-out", None), ("", "lyric fail")],
    ):
        with patch(
            "ez_prompt_enhance.nodes._close_llm",
            side_effect=RuntimeError("unload"),
        ):
            vocal = ace.run("lazy", "[verse]\nhi", True, "vocal")
    assert vocal["result"][0] == "tags-out"
    with patch(
        "ez_prompt_enhance.nodes.complete",
        return_value=("lo-fi keys", None),
    ):
        with patch("ez_prompt_enhance.nodes._close_llm"):
            inst = ace.run("lo-fi keys", "", True, "instrumental")
    assert "instrumental" in inst["result"][0].lower()
    with patch(
        "ez_prompt_enhance.nodes.complete",
        return_value=("", "empty"),
    ):
        with patch("ez_prompt_enhance.nodes._close_llm"):
            back = ace.run("orig-tags", "[verse]\nx", True, "vocal")
    assert back["result"][0] == "orig-tags"
    assert back["ui"]["passthrough"][0]


def test_samples_edge_catalogs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(samp, "SAMPLES_DIR", tmp_path)
    samp.load_index.cache_clear()
    samp.load_catalog.cache_clear()
    samp._sample_combo_labels_cached.cache_clear()
    assert samp._as_str(None) == ""
    assert samp.load_index() == {}
    (tmp_path / "index.json").write_text("[]", encoding="utf-8")
    samp.load_index.cache_clear()
    assert samp.load_index() == {}
    assert samp.catalog_exists("") is False
    assert samp.catalog_exists("custom") is False
    assert samp.catalog_for_rel("") == ""
    assert samp.family_catalog("NopeNode", "x") == ""
    (tmp_path / "klein_t2i.json").write_text("not-json", encoding="utf-8")
    samp.load_catalog.cache_clear()
    assert samp.load_catalog("klein_t2i") == ()
    (tmp_path / "klein_t2i.json").write_text("{}", encoding="utf-8")
    samp.load_catalog.cache_clear()
    assert samp.load_catalog("klein_t2i") == ()
    payload = [
        "skip",
        {"id": "a", "label": "custom", "prompt": "x"},
        {"id": "b", "label": "One", "prompt": ""},
        {"id": "b", "label": "Dup", "prompt": "y"},
        {"id": "c", "label": "one", "prompt": "z"},
        {"id": "d", "label": "Two", "prompt": "", "lyrics": "bars", "tags": "boom"},
    ]
    (tmp_path / "klein_t2i.json").write_text(json.dumps(payload), encoding="utf-8")
    samp.load_catalog.cache_clear()
    rows = samp.load_catalog("klein_t2i")
    assert [item.id for item in rows] == ["b", "d"]
    labels = samp.sample_labels("klein_t2i")
    assert labels[-1] == samp.CUSTOM
    (tmp_path / "with_custom.json").write_text(
        json.dumps([{"id": "c", "label": "custom", "prompt": "x"}]),
        encoding="utf-8",
    )
    samp.load_catalog.cache_clear()
    # catalog load skips custom label so combo still appends custom
    assert samp.sample_labels("with_custom")[-1] == samp.CUSTOM
    (tmp_path / "with_custom.json").write_text(
        json.dumps([{"id": "c", "label": "Custom", "prompt": "x"}]),
        encoding="utf-8",
    )
    samp.load_catalog.cache_clear()
    # exact CUSTOM string skipped; mixed-case Custom also skipped via lower
    assert samp.CUSTOM in samp.sample_labels("with_custom")
    assert samp._lookup("klein_t2i", "two") is not None
    assert samp._lookup("klein_t2i", "nope") is None
    assert samp.resolve_prompt("klein_t2i", "One", "fallback") == "fallback"
    assert samp.resolve_prompt("klein_t2i", "Two", "fallback") == "bars"
    assert samp.resolve_ace_sample("klein_t2i", "missing", "t", "l") == ("t", "l")
    dump = samp.catalog_payload("klein_t2i")
    assert dump[-1]["lyrics"] == "bars"
    samp._sample_combo_labels_cached.cache_clear()
    combo = samp.sample_combo_labels("klein_t2i")
    assert combo[-1] == samp.CUSTOM
    assert "Two" in combo
    assert samp.sample_combo_labels("")[-1] == samp.CUSTOM
    monkeypatch.setattr(samp, "SAMPLES_DIR", tmp_path / "missing-dir")
    samp.load_catalog.cache_clear()
    samp._sample_combo_labels_cached.cache_clear()
    assert samp.list_catalog_ids() == ()
    assert samp.sample_combo_labels("klein_t2i") == [samp.CUSTOM]
    samp.load_index.cache_clear()
    assert samp.resolve_catalog("", lab_rel="klein_t2i") == ""
    monkeypatch.setattr(samp, "SAMPLES_DIR", tmp_path)
    (tmp_path / "index.json").write_text(
        json.dumps({"audio/albums/x/y/cover": "klein_t2i"}), encoding="utf-8"
    )
    samp.load_index.cache_clear()
    assert samp.catalog_for_rel("audio/albums/x/y/cover") == "klein_t2i"


# --- podcast ------------------------------------------------------------------


def test_podcast_as_bool_and_unlabeled_turn() -> None:
    assert podcast._as_bool(1) is True
    assert podcast._as_bool("on") is True
    assert podcast._as_bool("no") is False
    turns = podcast.parse_speaker_turns("orphan line\nSpeaker A: hi")
    assert turns[0] == ("speaker_a", "orphan line")


def test_podcast_audio_helpers_torch_and_numpy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Tensor:
        def __init__(self, ndim: int = 1) -> None:
            self.ndim = ndim

        def unsqueeze(self, _dim: int) -> _Tensor:
            return _Tensor(self.ndim + 1)

    torch_mod = types.ModuleType("torch")
    torch_mod.float32 = "f32"  # type: ignore[attr-defined]
    torch_mod.zeros = lambda *_a, **_k: "zeros"  # type: ignore[attr-defined]
    torch_mod.as_tensor = lambda samples, dtype=None: _Tensor(1 if not hasattr(samples, "ndim") else 1)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "torch", torch_mod)
    empty = podcast._empty_audio()
    assert empty["waveform"] == "zeros"
    one = podcast._audio_from_pcm([0.1, 0.2], 24000)
    assert one["sample_rate"] == 24000
    torch_mod.as_tensor = lambda samples, dtype=None: _Tensor(2)  # type: ignore[attr-defined]
    two = podcast._audio_from_pcm([[0.1], [0.2]], 24000)
    assert two["sample_rate"] == 24000
    monkeypatch.setitem(sys.modules, "torch", None)
    import builtins

    real_import = builtins.__import__

    def _no_torch(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "torch":
            raise ImportError("no torch")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _no_torch)
    sys.modules.pop("torch", None)
    assert podcast._empty_audio()["waveform"] == [[[0.0]]]
    assert podcast._audio_from_pcm([1.0], 8)["waveform"] == [1.0]
    monkeypatch.setattr(builtins, "__import__", real_import)
    assert podcast._concat_pcm([]) == [0.0]
    np_mod = types.ModuleType("numpy")
    np_mod.concatenate = lambda xs: [0.0, 1.0]  # type: ignore[attr-defined]
    np_mod.asarray = lambda c, dtype=None: types.SimpleNamespace(reshape=lambda _n: c)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "numpy", np_mod)
    assert podcast._concat_pcm([[0.0], [1.0]]) == [0.0, 1.0]

    def _no_np(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "numpy":
            raise ImportError("no numpy")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _no_np)
    sys.modules.pop("numpy", None)

    class _Arr:
        def tolist(self) -> list[float]:
            return [0.2]

    out = podcast._concat_pcm([_Arr(), [0.3]])
    assert out[0] == 0.2
    monkeypatch.setattr(builtins, "__import__", real_import)


def test_podcast_script_import_fail_and_unload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    types_in = EZPodcastScript.INPUT_TYPES()
    assert "flavor" in types_in["required"]
    tts_types = EZKokoroTTS.INPUT_TYPES()
    assert "backend" in tts_types["required"]

    n = {"i": 0}

    def _boom_second() -> None:
        n["i"] += 1
        if n["i"] > 1:
            raise ModuleNotFoundError("ez_prompt_enhance")

    monkeypatch.setattr(podcast, "_ensure_lab_custom_nodes_path", _boom_second)
    out = EZPodcastScript().run("hi", True)
    assert "unavailable" in out["ui"]["passthrough"][0]
    monkeypatch.setattr(podcast, "_ensure_lab_custom_nodes_path", lambda: None)

    def _import_close(*_a: object, **_k: object) -> Any:
        raise RuntimeError("close")

    with (
        patch("ez_prompt_enhance.client.complete", return_value=("Speaker A: hi", None)),
        patch("ez_prompt_enhance.client._close_llm", side_effect=RuntimeError("unload")),
    ):
        ok = EZPodcastScript().run("lazy", True, "radio_drama")
    assert "Speaker A" in ok["result"][0]


def test_podcast_tts_optional_and_kokoro(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tts = EZKokoroTTS()
    audio = tts.run(
        "Announcer: Open.\nSpeaker A: Hi.",
        include_announcer=True,
        backend=podcast.BACKEND_CHATTERBOX,
        speaker_a_ref=str(tmp_path / "a.wav"),
        speaker_b_ref=str(tmp_path / "b.wav"),
    )[0]
    assert "sample_rate" in audio
    (tmp_path / "owned.wav").write_bytes(b"RIFF")
    assert tts._try_optional_backend("hi", podcast.BACKEND_CHATTERBOX, str(tmp_path / "owned.wav")) is None
    onnx = tmp_path / "kokoro-v1.0.onnx"
    voices = tmp_path / "voices-v1.0.bin"
    onnx.write_bytes(b"onnx")
    voices.write_bytes(b"voices")
    monkeypatch.setenv("MODELS_DIR", str(tmp_path))
    monkeypatch.setenv("MODELS_ROOT", str(tmp_path))
    monkeypatch.setattr(
        podcast,
        "resolve_kokoro_paths",
        lambda: (str(onnx), str(voices)),
    )
    audio = tts.run("Speaker A: Hi.")[0]
    assert "sample_rate" in audio
    kokoro = types.ModuleType("kokoro_onnx")

    class _K:
        def __init__(self, *_a: object) -> None:
            return None

        def create(self, text: str, voice: str, speed: float) -> tuple[list[float], int]:
            del text, voice, speed
            return [0.1, 0.2], 24000

    kokoro.Kokoro = _K  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "kokoro_onnx", kokoro)
    pcm, rate = tts._synthesize_kokoro("hi", "af_heart", 1.0)
    assert pcm == [0.1, 0.2]
    assert rate == 24000

    class _Boom:
        def __init__(self, *_a: object) -> None:
            raise RuntimeError("synth")

    kokoro.Kokoro = _Boom  # type: ignore[attr-defined]
    pcm, rate = tts._synthesize_kokoro("hi", "af_heart", 1.0)
    assert pcm is None
    podcast.optional_backend_hook = lambda *_a, **_k: [0.0]
    try:
        pcm, rate = tts._synthesize_turn(
            "hi", "af_heart", podcast.BACKEND_QWEN3TTS, 1.0, str(tmp_path / "owned.wav")
        )
        assert pcm == [0.0]
    finally:
        podcast.optional_backend_hook = None
    pb = types.ModuleType("ez_common")

    class _Bar:
        def update(self, n: int = 1) -> None:
            del n

    pb.node_progress = lambda n: _Bar()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "ez_common", pb)
    monkeypatch.setitem(sys.modules, "kokoro_onnx", kokoro)

    class _Ok:
        def __init__(self, *_a: object) -> None:
            return None

        def create(self, text: str, voice: str, speed: float) -> tuple[list[float], int]:
            del text, voice, speed
            return [0.1], 24000

    kokoro.Kokoro = _Ok  # type: ignore[attr-defined]
    audio = tts.run("Speaker A: Hi.\nSpeaker B: Yo.")[0]
    assert audio["sample_rate"] == 24000


# --- research -----------------------------------------------------------------


def test_research_nodes_as_bool_and_pipeline_edges(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert research_nodes._as_bool(1) is True
    assert research_nodes._as_bool("yes") is True
    assert research_nodes._as_bool("no") is False
    assert pipeline.clamp_subagents(True) == 1
    assert pipeline.clamp_subagents(2.9) == 2
    assert pipeline.parse_planner_queries("{not json", "fb", 2) == ["fb"]
    queries = pipeline.parse_planner_queries(
        '{"queries":["A","a","B"]}', "fb", 3
    )
    assert queries == ["A", "B"]
    assert pipeline._as_bool("ON") is True
    user = pipeline._compose_user("q", "old", "extra")
    assert "Prior turns" in user
    hits = [SearchHit("T", "https://example.com", "snip")]
    brief = pipeline._fallback_brief("q", hits)
    assert "example.com" in brief
    monkeypatch.setattr(pipeline, "search_web", lambda *_a, **_k: hits)
    monkeypatch.setattr(pipeline, "_complete", lambda *_a, **_k: ("", ""))
    chat = pipeline.run_chat("hello", history="h", web_search=True)
    assert chat.status == "llm passthrough"
    def _complete_plan(system: str, user: str) -> tuple[str, str]:
        del system
        if "json only" in user.lower() or "subagent count" in user.lower():
            return '{"queries":["q"]}', ""
        return "", ""

    monkeypatch.setattr(pipeline, "_complete", _complete_plan)
    research = pipeline.run_research("hello", web_search=True, subagents=1)
    assert research.status == "llm passthrough"
    assert pipeline.slug_for_prompt("!!!") == "brief"
    monkeypatch.setattr(
        pipeline,
        "_ensure_lab_custom_nodes_path",
        lambda: None,
    )
    import builtins

    real_import = builtins.__import__

    def _no_common(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "ez_common":
            raise ImportError("no")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _no_common)
    assert pipeline._progress(3) is None
    monkeypatch.setattr(builtins, "__import__", real_import)
    monkeypatch.delenv("COMFY_OUTPUT_DIR", raising=False)
    monkeypatch.delenv("MODELS_DIR", raising=False)
    original = Path.is_dir

    def fake_is_dir(self: Path) -> bool:
        if str(self) == "/outputs":
            return False
        return original(self)

    monkeypatch.setattr(Path, "is_dir", fake_is_dir)

    def _boom_root(**_k: object) -> Path:
        raise RuntimeError("no root")

    monkeypatch.setattr("ez_common.output_root", _boom_root)
    result = pipeline.ResearchResult("body", "", "ok", [])
    assert pipeline.write_brief(result, "hi") is None
    original_write = Path.write_text

    def _boom_write(self: Path, data: str, encoding: str | None = None, errors: str | None = None, newline: str | None = None) -> int:
        if self.suffix == ".md" and "ez_research_" in self.name:
            raise OSError("ro")
        return original_write(self, data, encoding=encoding, errors=errors, newline=newline)

    monkeypatch.setattr(Path, "write_text", _boom_write)
    assert pipeline.write_brief(result, "hi", output_dir=tmp_path / "out") is None


def test_research_search_ssrf_and_bodies(monkeypatch: pytest.MonkeyPatch) -> None:
    mapped = ipaddress.IPv6Address("::ffff:10.0.0.1")
    assert search._ip_blocked(mapped) is True
    assert search.is_blocked_url("https:///nohost") == "missing host"

    def _dns_fail(_host: str, _port: int) -> list[tuple[Any, ...]]:
        raise OSError("dns")

    monkeypatch.setattr(search, "_getaddrinfo", _dns_fail)
    assert search.is_blocked_url("https://example.com/") == "dns failed"

    def _weird(_host: str, port: int) -> list[tuple[Any, ...]]:
        return [
            (2, 1, 6, "", ()),
            (2, 1, 6, "", (None, port)),
            (2, 1, 6, "", ("not-an-ip", port)),
            (2, 1, 6, "", ("8.8.8.8", port)),
        ]

    monkeypatch.setattr(search, "_getaddrinfo", _weird)
    assert search.is_blocked_url("https://example.com/") is None

    def _link_local(_host: str, port: int) -> list[tuple[Any, ...]]:
        return [(10, 1, 6, "", ("fe80::1%eth0", port))]

    monkeypatch.setattr(search, "_getaddrinfo", _link_local)
    assert search.is_blocked_url("https://example.com/") == "blocked ip"
    payload = ["q", ["x"], ["y"], ["https://127.0.0.1/x"]]
    assert search.parse_wikipedia_opensearch(payload) == []
    markup = '<a class="result__a" href=""></a>'
    assert search.parse_duckduckgo_html(markup) == []
    markup = '<a class="result__a" href="https://127.0.0.1/x">t</a>'
    assert search.parse_duckduckgo_html(markup) == []

    monkeypatch.setattr(search, "_getaddrinfo", lambda *_a, **_k: [(2, 1, 6, "", ("8.8.8.8", 443))])

    class _Resp:
        def geturl(self) -> str:
            return "https://example.com/ok"

        def read(self, _n: int) -> Any:
            class _Sliced:
                def decode(self, *_a: object, **_k: object) -> str:
                    raise UnicodeError("nope")

            class _Boom:
                def __len__(self) -> int:
                    return search.MAX_BODY + 8

                def __getitem__(self, _s: object) -> _Sliced:
                    return _Sliced()

                def decode(self, *_a: object, **_k: object) -> str:
                    raise UnicodeError("nope")

            return _Boom()

        def __enter__(self) -> _Resp:
            return self

        def __exit__(self, *_a: object) -> None:
            return None

    monkeypatch.setattr(search, "_urlopen", lambda *_a, **_k: _Resp())
    assert search.http_get("https://example.com/ok") == ""
    monkeypatch.setattr(search, "http_get", lambda *_a, **_k: "")
    assert search._wiki_summary_body("Title") == ""
    monkeypatch.setattr(search, "http_get", lambda *_a, **_k: "not-json")
    assert search._wiki_summary_body("Title") == ""
    monkeypatch.setattr(search, "http_get", lambda *_a, **_k: "[]")
    assert search._wiki_summary_body("Title") == ""
    monkeypatch.setattr(search, "http_get", lambda *_a, **_k: '{"extract": 1}')
    assert search._wiki_summary_body("Title") == ""
    monkeypatch.setattr(search, "http_get", lambda *_a, **_k: "")
    assert search.wikipedia_search("q") == []
    assert search.duckduckgo_search("q") == []

    def _get(url: str, data: bytes | None = None, timeout: float = 8.0) -> str:
        del data, timeout
        if "duckduckgo" in url:
            return (
                '<a class="result__a" href="https://en.wikipedia.org/wiki/A">A</a>'
                '<a class="result__snippet">snip</a>'
            )
        if "en.wikipedia.org/wiki" in url:
            return "<p>body</p>"
        return ""

    monkeypatch.setattr(search, "http_get", _get)
    hits = search.duckduckgo_search("q", limit=1, fetch_bodies=True)
    assert hits and hits[0].body
    wiki = [
        SearchHit("A", "https://en.wikipedia.org/wiki/A", "s"),
        SearchHit("B", "https://en.wikipedia.org/wiki/B", "s"),
    ]
    monkeypatch.setattr(search, "wikipedia_search", lambda *_a, **_k: wiki)
    extra = [
        SearchHit("A", "https://en.wikipedia.org/wiki/A", "dup"),
        SearchHit("C", "https://en.wikipedia.org/wiki/C", "c"),
    ]
    monkeypatch.setattr(search, "duckduckgo_search", lambda *_a, **_k: extra)
    filled = search.search_web("q", limit=2, fetch_bodies=False)
    assert [h.title for h in filled] == ["A", "B"]
    filled3 = search.search_web("q", limit=3, fetch_bodies=False)
    assert [h.title for h in filled3] == ["A", "B", "C"]


# --- music --------------------------------------------------------------------


def test_music_helpers_pack_and_nodes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert music_nodes._as_bool(1) is True
    assert music_nodes._as_bool("yes") is True
    assert title_case_song("foo--bar") == "Foo--Bar"
    assert nill_slug_from_stem("01-lab-coat") == "lab-coat"
    assert finalize_nill_album([]) == ()
    assert _uniquify_score(1, "\n\n[intro]\nhi") == "[intro, grid 1 1]"
    assert "grid 2 0" in _uniquify_score(2, "plain text")
    assert drive_slug_from_stem("1-hour-drop") == "hour-drop"
    assert finalize_drive_album(()) == ()
    missing = tmp_path / "no-dir"
    with pytest.raises(FileNotFoundError):
        write_m3u(missing, album="X")
    dest = tmp_path / "albums" / "A" / "B"
    dest.mkdir(parents=True)
    (dest / "01.flac").write_bytes(b"f")
    (dest / "01.flac.meta.json").write_text("{}", encoding="utf-8")
    zipped = pack_album(dest, album="B")
    assert zipped.is_file()
    music_meta._log("hi")
    assert music_meta._picture_mime(Path("x.webp")) == "image/webp"
    assert music_meta._picture_mime(Path("x.bin")) == "image/jpeg"
    flac = tmp_path / "t.flac"
    flac.write_bytes(b"f")
    sidecar = music_meta.stamp_audio_file(flac, music_meta.AudioMeta(
        artist="A", album="B", title="T", track=1, tracktotal=1, year=2026
    ))
    assert sidecar.is_file()
    ogg = tmp_path / "t.ogg"
    ogg.write_bytes(b"o")
    music_meta.stamp_audio_file(
        ogg,
        music_meta.AudioMeta(
            artist="A", album="B", title="T", track=1, tracktotal=0, year=2026
        ),
    )

    class _Flac(dict):
        def clear_pictures(self) -> None:
            return None

        def add_picture(self, picture: object) -> None:
            self["pic"] = picture

        def save(self) -> None:
            return None

    class _Picture:
        def __init__(self) -> None:
            self.type = 0
            self.mime = ""
            self.desc = ""
            self.data = b""

    flac_mod = types.ModuleType("mutagen.flac")
    flac_mod.FLAC = lambda _p: _Flac()  # type: ignore[attr-defined]
    flac_mod.Picture = _Picture  # type: ignore[attr-defined]
    mutagen = types.ModuleType("mutagen")
    monkeypatch.setitem(sys.modules, "mutagen", mutagen)
    monkeypatch.setitem(sys.modules, "mutagen.flac", flac_mod)
    cover = tmp_path / "c.png"
    cover.write_bytes(b"png")
    music_meta._stamp_flac(
        flac,
        music_meta.AudioMeta(
            artist="A", album="B", title="T", track=1, tracktotal=1, year=2026
        ),
        cover,
    )

    def _import_err(*_a: object, **_k: object) -> None:
        raise ImportError("mutagen")

    monkeypatch.setattr(music_meta, "_stamp_id3", _import_err)
    wav = tmp_path / "t.wav"
    wav.write_bytes(b"w")
    music_meta.stamp_audio_file(
        wav,
        music_meta.AudioMeta(
            artist="A", album="B", title="T", track=1, tracktotal=1, year=2026
        ),
    )

    def _boom(*_a: object, **_k: object) -> None:
        raise RuntimeError("tag")

    monkeypatch.setattr(music_meta, "_stamp_id3", _boom)
    music_meta.stamp_audio_file(
        wav,
        music_meta.AudioMeta(
            artist="A", album="B", title="T", track=1, tracktotal=1, year=2026
        ),
    )

    def _boom_root(**_k: object) -> Path:
        raise RuntimeError("no root")

    monkeypatch.setattr("ez_common.output_root", _boom_root)
    monkeypatch.delenv("COMFY_OUTPUT_DIR", raising=False)
    folder = types.SimpleNamespace(get_output_directory=lambda: str(tmp_path))
    monkeypatch.setitem(sys.modules, "folder_paths", folder)
    dest = music_meta.album_dir_from_env("A", "B")
    assert dest.is_dir()
    monkeypatch.delitem(sys.modules, "folder_paths", raising=False)
    dest = music_meta.album_dir_from_env("A", "B")
    assert dest.name == "B"
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path / "env-out"))
    dest = music_meta.album_dir_from_env("A", "B")
    assert "env-out" in str(dest)

    n = {"i": 0}

    def _boom_second() -> None:
        n["i"] += 1
        if n["i"] > 1:
            raise ModuleNotFoundError("ez_prompt_enhance")

    monkeypatch.setattr(music_nodes, "_ensure_lab_custom_nodes_path", _boom_second)
    out = EZRapLyrics().run("lyrics", True)
    assert "unavailable" in out["ui"]["passthrough"][0]
    monkeypatch.setattr(music_nodes, "_ensure_lab_custom_nodes_path", lambda: None)
    with patch("ez_music.nodes.load_writer_prompt", side_effect=FileNotFoundError("x")):
        miss = EZRapLyrics().run("lyrics", True)
    assert miss["ui"]["passthrough"][0] == "passthrough"
    with (
        patch("ez_prompt_enhance.client.complete", return_value=("", None)),
        patch("ez_prompt_enhance.client._close_llm", side_effect=RuntimeError("x")),
    ):
        empty = EZRapLyrics().run("lyrics", True)
    assert empty["ui"]["passthrough"][0] == "passthrough"

    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    audio = {"waveform": None, "sample_rate": 8000}

    class _Img:
        def cpu(self) -> Any:
            raise RuntimeError("tensor")

    out = EZAudioMetadata().run(audio, cover=_Img(), art_mode="upload")
    assert out["result"][0] is audio
    np_mod = types.ModuleType("numpy")

    class _Arr:
        ndim = 4

        def __getitem__(self, _i: object) -> _Arr:
            return self

        def max(self) -> float:
            return 0.5

        def __mul__(self, _o: object) -> _Arr:
            return self

        def clip(self, *_a: object) -> _Arr:
            return self

        def astype(self, _t: object) -> list[list[int]]:
            return [[1]]

    np_mod.asarray = lambda _a: _Arr()  # type: ignore[attr-defined]
    pil = types.ModuleType("PIL")
    image_mod = types.ModuleType("PIL.Image")

    class _Im:
        def save(self, dest: Path) -> None:
            Path(dest).write_bytes(b"png")

    image_mod.fromarray = lambda _a: _Im()  # type: ignore[attr-defined]
    pil.Image = image_mod  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "numpy", np_mod)
    monkeypatch.setitem(sys.modules, "PIL", pil)
    monkeypatch.setitem(sys.modules, "PIL.Image", image_mod)
    saved = music_nodes._save_cover_tensor([[0.1]], tmp_path / "cover.png")
    assert saved.is_file()

    class _CpuImg:
        def cpu(self) -> Any:
            return types.SimpleNamespace(numpy=lambda: [[0.2]])

    music_nodes._save_cover_tensor(_CpuImg(), tmp_path / "cover2.png")
    other = tmp_path / "other" / "cover.jpg"
    other.parent.mkdir()
    other.write_bytes(b"jpg")
    monkeypatch.setattr(
        music_nodes,
        "_save_cover_tensor",
        lambda _img, dest: dest.write_bytes(b"x") or dest,
    )
    monkeypatch.setattr(
        "ez_music.metadata.resolve_cover",
        lambda **_k: other,
    )
    monkeypatch.setattr(music_nodes, "_stamp_output_masters", lambda *_a, **_k: [])
    out = EZAudioMetadata().run(
        audio,
        artist="A",
        album="B",
        title="Song",
        art_mode="upload",
        cover=object(),
    )
    assert "tagged" in out["ui"]["text"][0] or "no SaveAudio" in out["ui"]["text"][0]
    assert music_nodes._stamp_output_masters("", tmp_path, object(), None) == []
    monkeypatch.setattr(
        "ez_common.output_root",
        lambda **_k: (_ for _ in ()).throw(RuntimeError("x")),
    )
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    assert music_nodes._output_root(tmp_path) == tmp_path
    monkeypatch.delenv("COMFY_OUTPUT_DIR", raising=False)
    monkeypatch.setitem(
        sys.modules,
        "folder_paths",
        types.SimpleNamespace(get_output_directory=lambda: str(tmp_path)),
    )
    assert music_nodes._output_root(tmp_path) == tmp_path
    monkeypatch.delitem(sys.modules, "folder_paths", raising=False)
    assert music_nodes._output_root(tmp_path) == tmp_path


# --- docs ---------------------------------------------------------------------


def test_docs_commands_validation_and_quote(tmp_path: Path) -> None:
    cmd = _load_docs("ez_docs_commands_rem", ROOT / "docs" / "commands.py")
    cmd._BUILDER_CACHE.clear()
    data = cmd.load_builder()
    again = cmd.load_builder()
    assert again is data
    not_obj = tmp_path / "builder.json"
    not_obj.write_text("[]", encoding="utf-8")
    cmd._BUILDER_CACHE.pop(str(not_obj), None)
    with pytest.raises(ValueError, match="object"):
        cmd.load_builder(not_obj)
    raw: dict[str, Any] = {"variables": "x", "commands": []}
    with pytest.raises(ValueError, match="variables"):
        cmd.validate_builder(raw)
    with pytest.raises(ValueError, match="commands"):
        cmd.validate_builder({"variables": [{"id": "SPARK_HOST", "label": "h", "default": ""}], "commands": []})
    with pytest.raises(ValueError, match="variables"):
        cmd.validate_builder({"variables": [], "commands": [{"id": "a", "argv": ["x"]}]})
    with pytest.raises(ValueError, match="object"):
        cmd.validate_builder({"variables": [1], "commands": [{"id": "a", "argv": ["x"]}]})
    with pytest.raises(ValueError, match="env-style"):
        cmd.validate_builder(
            {"variables": [{"id": "bad"}], "commands": [{"id": "a", "argv": ["x"]}]}
        )
    base_vars = [
        {"id": name, "label": name, "default": ""}
        for name in cmd.SESSION_VAR_IDS
    ]
    dup = list(base_vars)
    dup[0] = dict(base_vars[0])
    with pytest.raises(ValueError, match="duplicate variable"):
        cmd.validate_builder(
            {
                "variables": base_vars + [base_vars[0]],
                "commands": [{"id": "a", "argv": ["x"]}],
            }
        )
    missing_label = [dict(v) for v in base_vars]
    missing_label[0]["label"] = ""
    with pytest.raises(ValueError, match="label"):
        cmd.validate_builder({"variables": missing_label, "commands": [{"id": "a", "argv": ["x"]}]})
    bad_default = [dict(v) for v in base_vars]
    bad_default[0]["default"] = 1
    with pytest.raises(ValueError, match="default"):
        cmd.validate_builder({"variables": bad_default, "commands": [{"id": "a", "argv": ["x"]}]})
    extra = [dict(v) for v in base_vars]
    extra.append({"id": "EXTRA", "label": "x", "default": ""})
    with pytest.raises(ValueError, match="unknown session"):
        cmd.validate_builder({"variables": extra, "commands": [{"id": "a", "argv": ["x"]}]})
    with pytest.raises(ValueError, match="object"):
        cmd.validate_builder({"variables": base_vars, "commands": [1]})
    with pytest.raises(ValueError, match="id"):
        cmd.validate_builder({"variables": base_vars, "commands": [{"id": "BAD", "argv": ["x"]}]})
    with pytest.raises(ValueError, match="argv"):
        cmd.validate_builder({"variables": base_vars, "commands": [{"id": "ok", "argv": []}]})
    with pytest.raises(ValueError, match="flags"):
        cmd.validate_builder(
            {"variables": base_vars, "commands": [{"id": "ok", "argv": ["x"], "flags": "no"}]}
        )
    with pytest.raises(ValueError, match="object"):
        cmd._validate_flag("c", 0, 1, [])
    with pytest.raises(ValueError, match="name"):
        cmd._validate_flag("c", 0, {"name": "BAD"}, [])
    seen: list[str] = ["dup"]
    with pytest.raises(ValueError, match="duplicate flag"):
        cmd._validate_flag("c", 0, {"name": "dup", "kind": "bool"}, seen)
    with pytest.raises(ValueError, match="kind"):
        cmd._validate_flag("c", 0, {"name": "f", "kind": "nope"}, [])
    with pytest.raises(ValueError, match="bool"):
        cmd._validate_flag("c", 0, {"name": "f", "kind": "bool", "default": "x"}, [])
    with pytest.raises(ValueError, match="choices"):
        cmd._validate_flag("c", 0, {"name": "f", "kind": "choice"}, [])
    with pytest.raises(ValueError, match="object"):
        cmd._validate_flag(
            "c", 0, {"name": "f", "kind": "choice", "choices": [1], "default": "a"}, []
        )
    with pytest.raises(ValueError, match="value"):
        cmd._validate_flag(
            "c",
            0,
            {"name": "f", "kind": "choice", "choices": [{"value": "", "label": "x"}], "default": "a"},
            [],
        )
    with pytest.raises(ValueError, match="duplicate choice"):
        cmd._validate_flag(
            "c",
            0,
            {
                "name": "f",
                "kind": "choice",
                "choices": [
                    {"value": "a", "label": "A"},
                    {"value": "a", "label": "B"},
                ],
                "default": "a",
            },
            [],
        )
    with pytest.raises(ValueError, match="label"):
        cmd._validate_flag(
            "c",
            0,
            {
                "name": "f",
                "kind": "choice",
                "choices": [{"value": "a", "label": ""}],
                "default": "a",
            },
            [],
        )
    with pytest.raises(ValueError, match="default"):
        cmd._validate_flag(
            "c",
            0,
            {
                "name": "f",
                "kind": "choice",
                "choices": [{"value": "a", "label": "A"}],
                "default": "z",
            },
            [],
        )
    with pytest.raises(ValueError, match="bind_var"):
        cmd._validate_flag(
            "c",
            0,
            {
                "name": "f",
                "kind": "choice",
                "choices": [{"value": "a", "label": "A"}],
                "default": "a",
                "bind_var": "NOPE",
            },
            [],
        )
    assert cmd._shell_quote("") == "''"
    assert "'" in cmd._shell_quote("a b")
    recipe = {
        "argv": ["./x"],
        "flags": [
            {"name": "need", "kind": "choice", "required": True, "default": "d", "choices": [{"value": "d", "label": "D"}]},
            {"name": "skip", "kind": "choice", "required": False, "default": "", "choices": [{"value": "d", "label": "D"}]},
            {"name": "empty", "kind": "choice", "required": True, "default": "", "choices": [{"value": "d", "label": "D"}]},
        ],
    }
    line = cmd.render_command(recipe, {"need": "", "skip": "", "empty": ""}, {})
    assert "--need" in line
    assert "--skip" not in line


def test_docs_shell_and_workflow_remainder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    gen = _load_docs("ez_shell_docs_rem", ROOT / "docs" / "generate_shell_docs.py")
    body = gen._format_body(
        [
            "Important: keep restart no.",
            "Warning: type yes.",
            "Note: unload first.",
            "Note",
            "./foo --bar",
            "cmd -- flag",
            "Usage:",
            "./scripts/manage.sh start",
            "",
            "  continued",
            "```",
        ]
    )
    assert "!!! important" in body
    assert "!!! warning" in body
    assert "!!! note" in body
    assert "```bash" in body
    assert "```text" in body
    path = tmp_path / "s.sh"
    path.write_text(
        "# ## Empty Sec\n# ### Empty Sub\n# @function empty_fn\n# @command empty_cmd\n",
        encoding="utf-8",
    )
    docs = gen.extract_from_file(path)
    assert any(item.startswith("## Empty Sec") for item in docs)
    monkeypatch.setattr(gen, "SCRIPTS_DIR", tmp_path)
    (tmp_path / "manage.sh").write_text("# ## X\n", encoding="utf-8")
    files = gen._iter_script_files()
    assert files[0].name == "manage.sh"
    monkeypatch.setattr(gen, "OUTPUT_DIR", tmp_path)
    blocked = tmp_path / "blocked.md"
    monkeypatch.setattr(gen, "OUTPUT_FILE", blocked)
    blocked.write_text("old", encoding="utf-8")
    monkeypatch.setattr(gen, "render_reference", lambda: "new\n")
    original_read = Path.read_text

    def _read(self: Path, encoding: str = "utf-8", errors: str | None = None) -> str:
        if self.resolve() == blocked.resolve():
            raise OSError("no")
        if errors is None:
            return original_read(self, encoding=encoding)
        return original_read(self, encoding=encoding, errors=errors)

    monkeypatch.setattr(Path, "read_text", _read)
    assert gen.main(["--force"]) == 0
    monkeypatch.setattr(Path, "read_text", original_read)
    monkeypatch.setattr(sys, "argv", ["generate_shell_docs.py"])
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(str(ROOT / "docs" / "generate_shell_docs.py"), run_name="__main__")
    assert exc.value.code == 0

    gwd = _load_docs("ez_gwd_rem", ROOT / "docs" / "generate_workflow_docs.py")
    monkeypatch.setattr(
        sys,
        "path",
        [p for p in sys.path if p != str(ROOT / "docs")],
    )
    spec = importlib.util.spec_from_file_location(
        "ez_gwd_path", ROOT / "docs" / "generate_workflow_docs.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert gwd._cell(None) == "—"
    assert gwd._fence("") == ""
    assert gwd._fence("``` hi")
    assert gwd._mermaid_id("G", "") == "Gx"
    rel = gwd.lab_rel_of(tmp_path / "klein" / "still.json", {}, tmp_path)
    assert rel.endswith("klein/still")
    assert gwd.extract_note([{"type": "KSampler"}]) == ""
    groups = gwd.assign_groups(
        [{"id": 1, "pos": [0, 0]}],
        [{"title": "G", "bounding": [1, 2]}],
    )
    assert groups[1] == "Ungrouped"
    assert gwd.mermaid_for_graph({"nodes": [], "groups": []}) == ""
    many = {"nodes": [{"id": i, "type": "N", "title": "t"} for i in range(30)], "groups": []}
    assert gwd.mermaid_for_graph(many) == ""
    missing = tmp_path / "no-styles.json"
    assert gwd.load_styles(missing) == {}
    bad = tmp_path / "styles.json"
    bad.write_text("[]", encoding="utf-8")
    assert gwd.load_styles(bad) == {}
    choices = gwd.expand_choices({"choices": ["a", {"id": "b"}]}, styles={}, ace_language=[], ace_keyscale=[])
    assert {row["id"] for row in choices} == {"a", "b"}
    spec_n = {
        "widgets": [
            {"storage": "dict", "key": "a"},
            {"storage": "dict", "key": "b"},
            {"storage": "dict", "key": "c"},
        ],
        "variants": [{"widgets": [{"storage": "dict", "key": "a"}]}],
    }
    assert gwd.match_layout(spec_n, None) is not None
    assert gwd.match_layout(spec_n, {"a": 1, "b": 2}) is not None
    assert gwd.match_layout(spec_n, {"z": 1}) is None
    assert gwd.match_layout(spec_n, 3) is None
    widget = {"storage": "dict", "key": 1}
    assert gwd.read_widget_value({"1": "x"}, widget) is None
    page = gwd.render_graph_page(
        "klein/x",
        {"nodes": [], "extra": {"lab_description": "desc"}},
        {},
        styles={},
        ace_language=[],
        ace_keyscale=[],
    )
    assert "desc" in page
    dump = gwd._track_widgets(
        {
            "nodes": [
                {"type": "Note", "widgets_values": ["n"]},
                {"type": "X", "title": "T", "widgets_values": {"k": "v"}},
            ]
        }
    )
    assert "Key" in dump
    lab = tmp_path / "lab"
    lab.mkdir()
    (lab / "gone.json").symlink_to(lab / "missing.json")
    (lab / "list.json").write_text("[]", encoding="utf-8")
    (lab / "ok.json").write_text("{}", encoding="utf-8")
    rows = gwd.iter_lab_graphs(lab)
    assert any(item[0].endswith("ok") for item in rows)
    dest = tmp_path / "out"
    dest.mkdir()
    (dest / "old.md").write_text("old", encoding="utf-8")
    gwd.generate(
        repo_root=ROOT,
        lab_root=lab,
        out_dir=dest,
        encyclopedia_page=tmp_path / "enc.md",
        encyclopedia={},
        styles_path=missing,
        write=True,
    )
    assert not (dest / "old.md").is_file()
    nav = gwd.inject_nav(
        [{"Home": "index.md"}, "plain", {"Create": [{"Workflow details": "x.md"}]}],
        [
            {"id": "index", "path": "generated/workflows/index.md", "lane": "index", "kind": "index"},
            {"id": "z/extra", "path": "generated/workflows/z/extra.md", "lane": "custom", "kind": "graph"},
        ],
    )
    assert "plain" in nav
    monkeypatch.setattr(sys, "argv", ["generate_workflow_docs.py"])
    monkeypatch.setattr(Path, "unlink", lambda self, *a, **k: None)
    monkeypatch.setattr(Path, "write_text", lambda self, *a, **k: None)
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(str(ROOT / "docs" / "generate_workflow_docs.py"), run_name="__main__")
    assert exc.value.code == 0


def test_docs_glossary_hooks_page_brief(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    gloss = _load_docs("ez_gloss_rem", ROOT / "docs" / "glossary.py")
    assert gloss.relative_glossary_href("learn/comfyui/index.html", "klein").endswith("#klein")
    with pytest.raises(ValueError, match="object"):
        gloss._term_from_mapping(1, 0)
    with pytest.raises(ValueError, match="id"):
        gloss._term_from_mapping({"id": "BAD"}, 0)
    with pytest.raises(ValueError, match="title"):
        gloss._term_from_mapping({"id": "ok", "title": ""}, 0)
    with pytest.raises(ValueError, match="aliases"):
        gloss._term_from_mapping({"id": "ok", "title": "T", "aliases": []}, 0)
    with pytest.raises(ValueError, match="category"):
        gloss._term_from_mapping(
            {"id": "ok", "title": "T", "aliases": ["t"], "category": ""}, 0
        )
    with pytest.raises(ValueError, match="short"):
        gloss._term_from_mapping(
            {
                "id": "ok",
                "title": "T",
                "aliases": ["t"],
                "category": "C",
                "short": "a\nb",
            },
            0,
        )
    with pytest.raises(ValueError, match="long"):
        gloss._term_from_mapping(
            {
                "id": "ok",
                "title": "T",
                "aliases": ["t"],
                "category": "C",
                "short": "s",
                "long": "",
            },
            0,
        )
    with pytest.raises(ValueError, match="see_also"):
        gloss._term_from_mapping(
            {
                "id": "ok",
                "title": "T",
                "aliases": ["t"],
                "category": "C",
                "short": "s",
                "long": "L",
                "see_also": [1],
            },
            0,
        )
    term = gloss.Term("a", "A", ("a",), "Zed", "s", "l", ())
    term2 = gloss.Term("a", "B", ("b",), "Zed", "s", "l", ())
    with pytest.raises(ValueError, match="duplicate id"):
        gloss.validate_glossary((term, term2))
    path = tmp_path / "g.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="list"):
        gloss.load_glossary(path)
    gloss._GLOSSARY_CACHE[str(path)] = (term,)
    assert gloss.load_glossary(path) == (term,)
    assert gloss._category_sort_key("Nope")[0] == len(gloss.CATEGORY_ORDER)
    assert gloss._tag_name("<>") is None
    html = gloss._wrap_fragment(
        "<!--c-->text",
        gloss._alias_index((term,))[0],
        gloss._alias_index((term,))[1],
        set(),
        "",
    )
    assert "<!--c-->" in html
    assert gloss.wrap_html("<p>x</p>", ()) == "<p>x</p>"
    injected = gloss.inject_glossary_assets('<p id="ez-glossary-data"></p>', (term,))
    assert injected.endswith("></p>") or "ez-glossary-data" in injected
    once = gloss.inject_glossary_assets('id="ez-glossary-data"', (term,))
    assert once == 'id="ez-glossary-data"'
    no_body = gloss.inject_glossary_assets("<html></html>", (term,))
    assert "ez-glossary-dialog" in no_body
    assert gloss._page_url(None) == ""

    hooks = _load_docs("ez_hooks_rem", ROOT / "docs" / "hooks.py")
    original_spec = hooks.importlib.util.spec_from_file_location
    monkeypatch.setattr(
        hooks.importlib.util,
        "spec_from_file_location",
        lambda *_a, **_k: None,
    )
    hooks._COMMANDS_MOD = None
    with pytest.raises(ImportError):
        hooks._commands_mod()
    hooks._GLOSSARY_MOD = None
    with pytest.raises(ImportError):
        hooks._glossary_mod()
    hooks._PAGE_BRIEF_MOD = None
    with pytest.raises(ImportError):
        hooks._page_brief_mod()
    monkeypatch.setattr(hooks.importlib.util, "spec_from_file_location", original_spec)
    hooks._COMMANDS_MOD = None
    hooks._GLOSSARY_MOD = None
    hooks._PAGE_BRIEF_MOD = None
    assert hooks._parse_datetime("") is None
    assert hooks._parse_datetime("999999999999999999999") is None
    naive = hooks._parse_datetime("2020-01-01T00:00:00")
    assert naive is not None and naive.tzinfo is not None
    assert hooks._parse_datetime("not-a-date") is None
    monkeypatch.setattr(
        hooks.subprocess,
        "run",
        lambda *_a, **_k: (_ for _ in ()).throw(OSError("git")),
    )
    assert hooks._git_head_committer_date() is None
    monkeypatch.setattr(
        hooks.subprocess,
        "run",
        lambda *_a, **_k: (_ for _ in ()).throw(subprocess.TimeoutExpired(cmd="git", timeout=1)),
    )
    assert hooks._git_head_committer_date() is None
    monkeypatch.setattr(
        hooks.subprocess,
        "run",
        lambda *_a, **_k: types.SimpleNamespace(returncode=1, stdout=""),
    )
    assert hooks._git_head_committer_date() is None
    hooks._published_cache = hooks._UNSET
    monkeypatch.setenv("EZ_DOCS_PUBLISHED_AT", "2020-01-01T00:00:00Z")
    first = hooks.published_at()
    second = hooks.published_at()
    assert first == second
    monkeypatch.setattr(
        hooks.importlib.util,
        "spec_from_file_location",
        lambda *_a, **_k: None,
    )
    with pytest.raises(ImportError):
        hooks._workflow_docs_mod()
    monkeypatch.setattr(hooks.importlib.util, "spec_from_file_location", original_spec)
    monkeypatch.setattr(hooks, "docs_version", lambda: "development")
    html = '<span class="ez-published-chip">x</span><h1>Hi</h1>'
    out = hooks.on_post_page(html)
    assert "ez-docs-dev-banner" in out
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{", encoding="utf-8")
    monkeypatch.setattr(hooks.Path, "is_file", lambda self: True)
    monkeypatch.setattr(hooks.Path, "read_text", lambda self, encoding="utf-8": "{")
    assert hooks.inject_workflow_nav({"nav": []})["nav"] == []
    monkeypatch.setattr(hooks.Path, "read_text", lambda self, encoding="utf-8": '{"pages": 1}')
    assert hooks.inject_workflow_nav({"nav": []})["nav"] == []

    brief = _load_docs("ez_brief_rem", ROOT / "docs" / "page_brief.py")
    assert brief._skip_ws("   ", 0) == 3
    assert brief._read_ul("nope", 0) is None
    assert brief._read_ul("<ul/>", 0) is None
    src = "<h1>T</h1><p><strong>What's on this page</strong></p><p>no list</p>"
    assert "ez-page-brief" not in brief.wrap_page_brief(src)
    src2 = (
        "<h1>T</h1><p><strong>What's on this page</strong></p><ul><li>a</li></ul>"
        "<p><strong>What this enables</strong></p><p>no</p>"
    )
    assert "ez-page-brief" not in brief.wrap_page_brief(src2)


def test_remaining_one_liners(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import ez_common as ec
    from ez_podcast.nodes import EZPodcastDisclosure

    assert isinstance(ec.node_progress(-3), ec.NullProgress)
    assert music_meta._picture_mime(Path("a.jpg")) == "image/jpeg"
    assert music_meta._picture_mime(Path("a.jpeg")) == "image/jpeg"
    assert music_nodes._as_bool(object()) is False
    assert music_nodes._stamp_output_masters(
        "prefix",
        tmp_path,
        object(),
        None,
    ) == []
    assert podcast._as_bool(object()) is False
    assert "script" in EZPodcastDisclosure.INPUT_TYPES()["required"]
    saved_common = sys.modules.get("ez_common")
    sys.modules["ez_common"] = None  # type: ignore[assignment]
    try:
        audio = EZKokoroTTS().run("Speaker A: Hi.")[0]
        assert "sample_rate" in audio
    finally:
        if saved_common is not None:
            sys.modules["ez_common"] = saved_common
        else:
            sys.modules.pop("ez_common", None)
    assert client.with_style_system("sys", "none") == "sys"
    monkeypatch.setenv("EZ_LLM_N_THREADS", "nope")
    assert client._n_threads() == client.DEFAULT_N_THREADS
    monkeypatch.setenv("EZ_LLM_N_THREADS", "0")
    assert client._n_threads() == client.DEFAULT_N_THREADS

    class _Resp:
        def read(self) -> bytes:
            return b"x"

        def __enter__(self) -> _Resp:
            return self

        def __exit__(self, *_a: object) -> None:
            return None

    monkeypatch.setattr(client, "_urlopen_sidecar", _REAL_URLOPEN_SIDECAR)
    monkeypatch.setattr(client.urllib.request, "urlopen", lambda *_a, **_k: _Resp())
    req = client.urllib.request.Request("https://example.invalid/")
    assert client._urlopen_sidecar(req, 0.1).read() == b"x"
    assert _family_id("nope") == "klein"
    assert samp._as_str(3) == "3"
    assert samp._as_str(None) == ""
    assert samp.load_catalog("custom") == ()
    assert samp.load_catalog("missing-catalog-xyz") == ()
    assert samp._lookup("klein_t2i", samp.CUSTOM) is None
    assert samp.resolve_catalog("", lab_rel="klein/still-draft") in {"", "klein_t2i"}
    monkeypatch.setattr(
        samp,
        "load_catalog",
        lambda _cid: (samp.Sample(id="x", label="Custom", prompt="p"),),
    )
    labels = samp.sample_labels("any")
    assert samp.CUSTOM in labels
    samp._sample_combo_labels_cached.cache_clear()
    assert samp.CUSTOM in samp.sample_combo_labels("any")
    assert research_nodes._as_bool(object()) is False
    assert pipeline.parse_planner_queries("{not json}", "fb", 2) == ["fb"]
    assert pipeline._as_bool(1.5) is True
    assert pipeline._as_bool("no") is False
    assert pipeline._as_bool(object()) is False
    monkeypatch.delenv("COMFY_OUTPUT_DIR", raising=False)
    original = Path.is_dir

    def fake_is_dir(self: Path) -> bool:
        if str(self) == "/outputs":
            return False
        return original(self)

    monkeypatch.setattr(Path, "is_dir", fake_is_dir)
    monkeypatch.setitem(
        sys.modules,
        "folder_paths",
        types.SimpleNamespace(get_output_directory=lambda: str(tmp_path / "fp-out")),
    )
    result = pipeline.ResearchResult("body", "", "ok", [])
    path = pipeline.write_brief(result, "hi")
    assert path is not None
    monkeypatch.setattr(
        "ez_common.output_root",
        lambda **_k: (_ for _ in ()).throw(RuntimeError("x")),
    )
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path / "env-brief"))
    path = pipeline.write_brief(result, "hi")
    assert path is not None
    assert search._ip_blocked(ipaddress.IPv4Address("240.0.0.1")) is True
    assert search._ip_blocked(ipaddress.IPv4Address("8.8.8.8")) is False
    payload = ["q", [""], ["y"], ["https://en.wikipedia.org/wiki/X"]]
    assert search.parse_wikipedia_opensearch(payload) == []
    markup = '<a class="result__a" href="https://en.wikipedia.org/wiki/X"></a>'
    assert search.parse_duckduckgo_html(markup) == []
    monkeypatch.setattr(
        search,
        "is_blocked_url",
        lambda url, **_k: "blocked" if "blocked" in url else None,
    )
    monkeypatch.setattr(search, "http_get", lambda *_a, **_k: "page")
    hits = [
        SearchHit("B", "https://example.com/blocked", "s"),
        SearchHit("C", "https://example.com/ok", "s"),
    ]
    monkeypatch.setattr(search, "parse_duckduckgo_html", lambda _m: hits)
    monkeypatch.setattr(search, "is_blocked_url", lambda url, **_k: "blocked" if "blocked" in url else None)
    out = search.duckduckgo_search("q", fetch_bodies=True)
    assert out
    assert samp.family_catalog("EZRapLyrics", "unknown-mode") == "rap_draft"
    assert pipeline._as_bool(True) is True
    assert pipeline._as_bool(False) is False
    assert pipeline._as_bool(2) is True
    monkeypatch.delenv("COMFY_OUTPUT_DIR", raising=False)
    monkeypatch.delitem(sys.modules, "folder_paths", raising=False)
    saved_ec = sys.modules.get("ez_common")
    sys.modules["ez_common"] = None  # type: ignore[assignment]
    try:
        assert pipeline.write_brief(result, "hi") is None
    finally:
        if saved_ec is not None:
            sys.modules["ez_common"] = saved_ec
        else:
            sys.modules.pop("ez_common", None)
    assert search._ip_blocked(ipaddress.IPv6Address("64:ff9b::1")) is True
    assert search._ip_blocked(ipaddress.IPv6Address("::ffff:8.8.8.8")) is False
    public_mapped = types.SimpleNamespace(
        is_private=False,
        is_loopback=False,
        is_link_local=False,
        is_multicast=False,
        is_reserved=False,
        is_unspecified=False,
        ipv4_mapped=ipaddress.IPv4Address("1.1.1.1"),
    )
    assert search._ip_blocked(public_mapped) is False  # type: ignore[arg-type]
    private_mapped = types.SimpleNamespace(
        is_private=False,
        is_loopback=False,
        is_link_local=False,
        is_multicast=False,
        is_reserved=False,
        is_unspecified=False,
        ipv4_mapped=ipaddress.IPv4Address("10.0.0.1"),
    )
    assert search._ip_blocked(private_mapped) is True  # type: ignore[arg-type]
    gen = _load_docs("ez_shell_docs_gap", ROOT / "docs" / "generate_shell_docs.py")
    body = gen._format_body(["Usage:", "./scripts/manage.sh start", "", "  --help"])
    assert "```bash" in body
    trailing = gen._format_body(["Usage:", "./scripts/manage.sh start", "", "", "Note: done"])
    assert "```bash" in trailing
    path = tmp_path / "orphan.sh"
    path.write_text("# ### Orphan sub\n", encoding="utf-8")
    docs = gen.extract_from_file(path)
    assert any(item.startswith("### Orphan") for item in docs)
    gloss = _load_docs("ez_gloss_gap", ROOT / "docs" / "glossary.py")
    assert gloss._page_url(types.SimpleNamespace(url="learn/")) == "learn/"
    hooks = _load_docs("ez_hooks_gap", ROOT / "docs" / "hooks.py")
    monkeypatch.setattr(
        hooks.subprocess,
        "run",
        lambda *_a, **_k: types.SimpleNamespace(returncode=2, stdout=""),
    )
    assert hooks._git_head_committer_date() is None
    monkeypatch.setattr(hooks, "docs_version", lambda: "development")
    html = '<article class="md-content__inner"><h1>Hi</h1></article>'
    out_html = hooks.on_post_page(html)
    assert "ez-docs-dev-banner" in out_html
    import importlib
    import sitecustomize as sc

    lora = types.ModuleType("diffusers.models.lora")
    sys.modules["torch.nn"] = None  # type: ignore[assignment]
    try:
        sc.apply_lab_lora_linear_shim(lora)
    finally:
        sys.modules.pop("torch.nn", None)
