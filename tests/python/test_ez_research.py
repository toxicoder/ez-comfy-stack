"""Hermetic tests for ez_research (no Comfy, no network, no GGUF)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

import ez_research  # noqa: E402
from ez_research import pipeline  # noqa: E402
from ez_research import search  # noqa: E402
from ez_research.nodes import EZCreativeResearch, NODE_CLASS_MAPPINGS  # noqa: E402
from ez_research.search import SearchHit  # noqa: E402


def _public_addrinfo(host: str, port: int, *_args: object, **_kwargs: object) -> list[tuple[Any, ...]]:
    return [(2, 1, 6, "", ("8.8.8.8", port))]


@pytest.fixture(autouse=True)
def _no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("network forbidden in hermetic tests")

    monkeypatch.setattr(search, "_urlopen", _blocked)
    monkeypatch.setattr(search, "_getaddrinfo", _public_addrinfo)


def test_pack_exports_node() -> None:
    assert "EZCreativeResearch" in NODE_CLASS_MAPPINGS
    assert NODE_CLASS_MAPPINGS["EZCreativeResearch"] is EZCreativeResearch
    assert ez_research.WEB_DIRECTORY == "./js"


def test_ssrf_rejects_non_https_and_private() -> None:
    assert search.is_blocked_url("http://example.com") == "https only"
    assert search.is_blocked_url("file:///etc/passwd") == "https only"
    assert search.is_blocked_url("https://127.0.0.1/") == "blocked ip"
    assert search.is_blocked_url("https://192.168.1.9/") == "blocked ip"
    assert search.is_blocked_url("https://10.0.0.5/") == "blocked ip"
    assert search.is_blocked_url("https://169.254.169.254/") == "blocked ip"
    assert search.is_blocked_url("https://localhost/") == "blocked host"
    assert search.is_blocked_url("https://user:pw@example.com/") == "userinfo blocked"
    assert search.is_blocked_url("") == "empty url"


def test_ssrf_rejects_dns_to_private(monkeypatch: pytest.MonkeyPatch) -> None:
    def _private(_host: str, port: int) -> list[tuple[Any, ...]]:
        return [(2, 1, 6, "", ("10.1.2.3", port))]

    monkeypatch.setattr(search, "_getaddrinfo", _private)
    assert search.is_blocked_url("https://evil.example/") == "blocked ip"


def test_ssrf_allows_public_https(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(search, "_getaddrinfo", _public_addrinfo)
    assert search.is_blocked_url("https://en.wikipedia.org/wiki/Light") is None


def test_parse_wikipedia_opensearch() -> None:
    payload = [
        "neon",
        ["Neon lighting"],
        ["Gas-discharge lamps."],
        ["https://en.wikipedia.org/wiki/Neon_lighting"],
    ]
    hits = search.parse_wikipedia_opensearch(payload)
    assert len(hits) == 1
    assert hits[0].title == "Neon lighting"
    assert hits[0].url.endswith("Neon_lighting")


def test_parse_wikipedia_rejects_private_url() -> None:
    payload = ["q", ["x"], ["y"], ["https://127.0.0.1/secret"]]
    assert search.parse_wikipedia_opensearch(payload) == []


def test_decode_ddg_href_unwraps_uddg() -> None:
    href = (
        "//duckduckgo.com/l/?uddg=https%3A%2F%2Fen.wikipedia.org%2Fwiki%2FKey"
        "&rut=abc"
    )
    assert search.decode_ddg_href(href) == "https://en.wikipedia.org/wiki/Key"


def test_parse_duckduckgo_html() -> None:
    markup = """
    <a class="result__a" href="https://en.wikipedia.org/wiki/Key_light">Key light</a>
    <a class="result__snippet">The primary light on a subject.</a>
    """
    hits = search.parse_duckduckgo_html(markup)
    assert len(hits) == 1
    assert hits[0].title == "Key light"
    assert "primary light" in hits[0].snippet


def test_http_get_blocks_before_urlopen() -> None:
    assert search.http_get("http://example.com") == ""
    assert search.http_get("https://127.0.0.1/") == ""


def test_http_get_reads_public_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(search, "_getaddrinfo", _public_addrinfo)

    class _Resp:
        def geturl(self) -> str:
            return "https://example.com/ok"

        def read(self, _n: int) -> bytes:
            return b'{"ok": true}'

        def __enter__(self) -> _Resp:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

    monkeypatch.setattr(search, "_urlopen", lambda *_a, **_k: _Resp())
    assert json.loads(search.http_get("https://example.com/ok"))["ok"] is True


def test_http_get_drops_redirect_to_private(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(search, "_getaddrinfo", _public_addrinfo)

    class _Resp:
        def geturl(self) -> str:
            return "https://127.0.0.1/meta"

        def read(self, _n: int) -> bytes:
            return b"secret"

        def __enter__(self) -> _Resp:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

    monkeypatch.setattr(search, "_urlopen", lambda *_a, **_k: _Resp())
    assert search.http_get("https://example.com/ok") == ""


def test_search_web_wikipedia_then_ddg(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(search, "_getaddrinfo", _public_addrinfo)

    def _fake_get(url: str, data: bytes | None = None, timeout: float = 8.0) -> str:
        if "api.php" in url:
            return json.dumps(
                [
                    "q",
                    ["Key light"],
                    ["Main light."],
                    ["https://en.wikipedia.org/wiki/Key_light"],
                ]
            )
        if "rest_v1" in url:
            return json.dumps({"extract": "A key light is the primary light."})
        if "duckduckgo" in url:
            return (
                '<a class="result__a" href="https://en.wikipedia.org/wiki/Fill_light">'
                "Fill light</a>"
                '<a class="result__snippet">Secondary light.</a>'
            )
        return ""

    monkeypatch.setattr(search, "http_get", _fake_get)
    hits = search.search_web("key light", limit=5, fetch_bodies=True)
    titles = [h.title for h in hits]
    assert "Key light" in titles
    assert any(h.body.startswith("A key light") for h in hits)


def test_format_sources_and_bad_wiki_payload() -> None:
    assert search.parse_wikipedia_opensearch({"no": "list"}) == []
    assert search.parse_wikipedia_opensearch(["q", "bad", "x", "y"]) == []
    hits = [
        SearchHit("A", "https://en.wikipedia.org/wiki/A", "snip"),
        SearchHit("B", "https://en.wikipedia.org/wiki/B", "", body="body"),
    ]
    blob = search.format_sources(hits)
    assert "1. A" in blob
    assert "snip" in blob
    assert search.decode_ddg_href("https://en.wikipedia.org/wiki/X") == (
        "https://en.wikipedia.org/wiki/X"
    )


def test_http_get_oserror(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(search, "_getaddrinfo", _public_addrinfo)

    def _boom(*_a: object, **_k: object) -> object:
        raise OSError("nope")

    monkeypatch.setattr(search, "_urlopen", _boom)
    assert search.http_get("https://example.com/x") == ""


def test_wikipedia_search_bad_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(search, "http_get", lambda *_a, **_k: "not-json")
    assert search.wikipedia_search("q", fetch_bodies=False) == []


def test_duckduckgo_search_parses_html(monkeypatch: pytest.MonkeyPatch) -> None:
    markup = (
        '<a class="result__a" href="https://en.wikipedia.org/wiki/Fill_light">'
        "Fill light</a>"
        '<a class="result__snippet">Secondary light.</a>'
    )
    monkeypatch.setattr(search, "http_get", lambda *_a, **_k: markup)
    hits = search.duckduckgo_search("fill", limit=2, fetch_bodies=False)
    assert hits[0].title == "Fill light"


def test_empty_query_is_no_hits() -> None:
    assert search.search_web("  ") == []
    assert search.wikipedia_search("") == []
    assert search.duckduckgo_search("") == []


def test_clamp_and_planner_json() -> None:
    assert pipeline.clamp_subagents("9") == 3
    assert pipeline.clamp_subagents(0) == 1
    assert pipeline.clamp_subagents("nope") == 2
    queries = pipeline.parse_planner_queries(
        'noise {"queries":["neon night","rooftop camera"]} trailing',
        "fallback",
        2,
    )
    assert queries == ["neon night", "rooftop camera"]
    assert pipeline.parse_planner_queries("not json", "the question", 2) == [
        "the question"
    ]
    assert pipeline.parse_planner_queries("", "", 2) == []


def test_run_chat_with_search(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        pipeline,
        "search_web",
        lambda *_a, **_k: [
            SearchHit("Key", "https://en.wikipedia.org/wiki/Key", "snip")
        ],
    )
    monkeypatch.setattr(pipeline, "_complete", lambda *_a, **_k: ("use a key light", ""))
    result = pipeline.run_chat("lighting", web_search=True)
    assert result.text == "use a key light"
    assert "Key" in result.sources
    assert result.queries == ["lighting"]


def test_write_brief_from_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path / "out"))
    monkeypatch.delenv("MODELS_DIR", raising=False)
    result = pipeline.ResearchResult("hello", "src", "ok", [])
    path = pipeline.write_brief(result, "hello")
    assert path is not None
    text = path.read_text(encoding="utf-8")
    assert "hello" in text
    assert "src" in text


def test_run_chat_fail_soft_without_llama(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pipeline, "_complete", lambda *_a, **_k: ("", "GGUF missing"))
    monkeypatch.setattr(pipeline, "search_web", lambda *_a, **_k: [])
    result = pipeline.run_chat("hello", web_search=False)
    assert result.status == "GGUF missing"
    assert "Next App" in result.text
    empty = pipeline.run_chat("  ")
    assert empty.status == "empty message"


def test_run_research_calls_search_per_query(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def _complete(system: str, user: str) -> tuple[str, str]:
        if "JSON" in system or "queries" in system.lower() or "plan" in system.lower():
            return '{"queries":["neon","rooftop"]}', ""
        return "## Brief\nCited [1].\n## Next App\nprompt-forge-lab-example", ""

    def _search(query: str, **_kwargs: object) -> list[SearchHit]:
        calls.append(query)
        return [
            SearchHit(
                title=query,
                url=f"https://en.wikipedia.org/wiki/{query}",
                snippet="snippet",
            )
        ]

    monkeypatch.setattr(pipeline, "_complete", _complete)
    monkeypatch.setattr(pipeline, "search_web", _search)
    result = pipeline.run_research("night rooftop", subagents=2)
    assert calls == ["neon", "rooftop"]
    assert result.queries == ["neon", "rooftop"]
    assert "Cited" in result.text
    assert "wikipedia.org" in result.sources


def test_run_research_empty_and_search_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        pipeline,
        "_complete",
        lambda *_a, **_k: ('{"queries":["only"]}', ""),
    )
    monkeypatch.setattr(
        pipeline,
        "search_web",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("search off")),
    )
    empty = pipeline.run_research("")
    assert empty.status == "empty message"
    result = pipeline.run_research("q", web_search=False, subagents=1)
    assert result.queries == ["only"]
    assert result.sources == ""


def test_write_brief_refuses_models_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    models = tmp_path / "models"
    models.mkdir()
    monkeypatch.setenv("MODELS_DIR", str(models))
    monkeypatch.delenv("COMFY_OUTPUT_DIR", raising=False)
    result = pipeline.ResearchResult("body", "src", "ok", [])
    assert pipeline.write_brief(result, "hi", output_dir=models) is None
    out = tmp_path / "output"
    path = pipeline.write_brief(result, "Night Rooftop!!", output_dir=out)
    assert path is not None
    assert path.parent.name == "research"
    assert path.name.startswith("ez_research_")
    assert "body" in path.read_text(encoding="utf-8")
    assert pipeline.slug_for_prompt("") == "brief"


def test_node_run_chat_and_research(monkeypatch: pytest.MonkeyPatch) -> None:
    from ez_research import nodes as research_nodes

    monkeypatch.setattr(
        research_nodes,
        "run_chat",
        lambda message, history="", web_search=False: pipeline.ResearchResult(
            "chat-reply", "s", "ok", []
        ),
    )
    monkeypatch.setattr(
        research_nodes,
        "run_research",
        lambda message, history="", web_search=True, subagents=2: pipeline.ResearchResult(
            "research-reply", "src", "ok", ["q"]
        ),
    )
    monkeypatch.setattr(research_nodes, "write_brief", lambda *_a, **_k: None)
    node = EZCreativeResearch()
    chat = node.run("hi", mode="chat", web_search=False)
    assert chat["result"] == ("chat-reply",)
    research = node.run("hi", mode="research", web_search=True, subagents=2)
    assert research["result"] == ("research-reply",)
    types = node.INPUT_TYPES()
    assert types["required"]["mode"][0] == ["chat", "research"]
    assert pipeline.load_prompt("planner").startswith("You plan")


def _is_custom_nodes_entry(entry: str) -> bool:
    try:
        return Path(entry).resolve() == CUSTOM.resolve()
    except OSError:
        return False


def _hide_modules(*prefixes: str) -> dict[str, ModuleType]:
    saved: dict[str, ModuleType] = {}
    for name in list(sys.modules):
        if name in prefixes or any(name.startswith(p + ".") for p in prefixes):
            saved[name] = sys.modules.pop(name)
    return saved


def test_comfy_style_load_without_prompt_enhance_on_path() -> None:
    """ComfyUI 0.34 load_custom_node: path-based name, custom_nodes not on path."""
    pack = CUSTOM / "ez_research"
    sys_module_name = str(pack).replace(".", "_x_")
    saved_path = list(sys.path)
    saved = _hide_modules("ez_research", "ez_prompt_enhance")
    try:
        sys.path[:] = [p for p in sys.path if not _is_custom_nodes_entry(p)]
        spec = importlib.util.spec_from_file_location(
            sys_module_name, pack / "__init__.py"
        )
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[sys_module_name] = module
        spec.loader.exec_module(module)
        assert "EZCreativeResearch" in module.NODE_CLASS_MAPPINGS
        assert module.WEB_DIRECTORY == "./js"
    finally:
        sys.path[:] = saved_path
        for name in list(sys.modules):
            if name == sys_module_name or name.startswith(sys_module_name + "."):
                sys.modules.pop(name, None)
        sys.modules.update(saved)


def test_ensure_lab_custom_nodes_path_inserts_parent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys, "path", [p for p in sys.path if not _is_custom_nodes_entry(p)]
    )
    assert not any(_is_custom_nodes_entry(p) for p in sys.path)
    pipeline._ensure_lab_custom_nodes_path()
    assert Path(sys.path[0]).resolve() == CUSTOM.resolve()


def test_complete_fail_soft_when_client_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _boom() -> None:
        raise ModuleNotFoundError("ez_prompt_enhance")

    monkeypatch.setattr(pipeline, "_ensure_lab_custom_nodes_path", _boom)
    text, reason = pipeline._complete("system", "user")
    assert text == ""
    assert "unavailable" in reason


def test_complete_imports_sibling_after_path_ensure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        sys, "path", [p for p in sys.path if not _is_custom_nodes_entry(p)]
    )
    for name in list(sys.modules):
        if name == "ez_prompt_enhance" or name.startswith("ez_prompt_enhance."):
            monkeypatch.delitem(sys.modules, name, raising=False)

    def _fake_complete(
        system: str,
        user: str,
        max_tokens: int = 700,
        temperature: float = 0.2,
    ) -> tuple[str, str]:
        del max_tokens, temperature
        assert system == "sys"
        assert user == "user"
        return "ok", ""

    pipeline._ensure_lab_custom_nodes_path()
    from ez_prompt_enhance import client as enhance_client

    monkeypatch.setattr(enhance_client, "complete", _fake_complete)
    text, reason = pipeline._complete("sys", "user")
    assert text == "ok"
    assert reason == ""
