"""Behaviour tests for the ez_feedback pack: context builder and routes.

Hermetic: stdlib only. ``urllib.request.urlopen`` is monkeypatched everywhere
and ``handle_submit`` also takes an injected opener, so no test touches the
network. Coverage for ``custom_nodes/ez_feedback`` lives entirely here.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import threading
import types
import urllib.error
import urllib.request
from email.message import Message
from collections.abc import Callable, Iterator, Mapping
from urllib.parse import urlencode
from typing import Any, cast

import pytest

import ez_feedback
from ez_feedback import context, routes

TOKEN = "ghp_" + "SECRETVALUE123"
"""Stand-in secret; must never appear in a response payload."""

HEAVY = "%" * 300
"""Value that triple-expands under urlencoding, to bust MAX_HREF on purpose."""


class _Adder:
    """PromptServer ``routes`` stand-in that records registered handlers."""

    def __init__(self) -> None:
        self.recorded: list[tuple[str, str]] = []
        self.handlers: dict[str, Callable[[Any], Any]] = {}

    def get(self, path: str) -> Callable[[Any], Any]:
        """Register a GET handler.

        Args:
            path: Route path.

        Returns:
            The decorator.
        """
        def deco(fn: Any) -> Any:
            self.recorded.append(("get", path))
            self.handlers[path] = fn
            return fn

        return deco

    def post(self, path: str) -> Callable[[Any], Any]:
        """Register a POST handler.

        Args:
            path: Route path.

        Returns:
            The decorator.
        """
        def deco(fn: Any) -> Any:
            self.recorded.append(("post", path))
            self.handlers[path] = fn
            return fn

        return deco


class _NoAdders:
    """Routes object without ``get`` / ``post``."""


class _Response:
    """File-like GitHub response."""

    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.closed = False

    def read(self) -> bytes:
        """Body bytes.

        Returns:
            The payload handed to the constructor.
        """
        return self.payload

    def close(self) -> None:
        """Mark the response closed."""
        self.closed = True


class _BoomEnv(Mapping[str, str]):
    """Mapping whose lookup raises, like a hostile environment wrapper."""

    def __getitem__(self, key: str) -> str:
        """Fail on every lookup.

        Args:
            key: Variable name.

        Returns:
            Never returns.
        """
        raise RuntimeError("environ is not talking")

    def __len__(self) -> int:
        """Length.

        Returns:
            One.
        """
        return 1

    def __iter__(self) -> Iterator[str]:
        """Key iterator.

        Returns:
            One key.
        """
        return iter(("COMFYUI_REF",))


class _Req:
    """aiohttp request stand-in."""

    def __init__(self, body: Any = None, *, boom: bool = False) -> None:
        self._body = body
        self._boom = boom

    async def json(self) -> Any:
        """Body as JSON.

        Returns:
            The canned body.

        Raises:
            ValueError: When constructed with ``boom``.
        """
        if self._boom:
            raise ValueError("bad json")
        return self._body


def _report_args(**overrides: Any) -> dict[str, Any]:
    """A well-formed submit body.

    Args:
        **overrides: Field overrides.

    Returns:
        Request body dict.
    """
    args: dict[str, Any] = {
        "kind": "bug",
        "title": "[app:stills/still-draft] KSampler blew up",
        "body": "## What happened\n\nit did\n",
        "labels": ["bug"],
    }
    args.update(overrides)
    return args


def _opener(payload: bytes, sink: list[urllib.request.Request]) -> Callable[[Any, float], _Response]:
    """Build an opener that records requests and replays a body.

    Args:
        payload: Response bytes.
        sink: Requests land here.

    Returns:
        An ``(request, timeout) -> response`` callable.
    """
    def opener(request: Any, timeout: float) -> _Response:
        assert timeout == routes.SUBMIT_TIMEOUT_S
        sink.append(request)
        return _Response(payload)

    return opener


def _sent(request: urllib.request.Request) -> dict[str, Any]:
    """Decode the JSON payload a captured request posted.

    Args:
        request: The captured request.

    Returns:
        Parsed JSON body.
    """
    data = request.data
    assert isinstance(data, (bytes, bytearray))
    return json.loads(data.decode("utf-8"))


def _respond(payload: dict[str, Any], *, status: int = 200) -> tuple[int, dict[str, Any]]:
    """aiohttp ``json_response`` stand-in.

    Args:
        payload: Response body.
        status: HTTP status.

    Returns:
        ``(status, payload)``.
    """
    return status, payload


# --- pack shape -------------------------------------------------------------


def test_pack_exports_empty_mappings_and_js() -> None:
    assert ez_feedback.NODE_CLASS_MAPPINGS == {}
    assert ez_feedback.NODE_DISPLAY_NAME_MAPPINGS == {}
    assert ez_feedback.WEB_DIRECTORY == "./js"
    assert ez_feedback.REPO == "toxicoder/ez-comfy-stack"
    assert callable(ez_feedback.register_routes)


def test_constants_match_the_contract() -> None:
    assert context.REPO == "toxicoder/ez-comfy-stack"
    assert context.LABELS == {"bug": "bug", "enhancement": "enhancement"}
    assert context.MAX_HREF == 5500
    assert context.MAX_BODY == 60000
    assert context.HEADINGS == (
        "## What happened",
        "## Steps",
        "## Expected",
        "## Actual",
        "## Context",
        "## Environment",
        "## Recent errors",
        "## Browser",
    )
    assert context.DEGRADE_ORDER == ("## Browser", "## Recent errors", "## Environment")
    assert context.MAX_ERROR_TEXT == 2000
    assert context.MAX_FIELD == 300
    assert context.ENHANCE_HEADINGS == (
        "## Problem",
        "## Proposed solution",
        "## Alternatives",
        "## What it unlocks",
    )
    assert context.BUG_NARRATIVE_KEYS == ("what_happened", "steps", "expected", "actual")
    assert context.ENHANCE_NARRATIVE_KEYS == ("problem", "solution", "alternatives", "unlocks")


def test_surfaces_include_the_load_error_surface() -> None:
    assert "load-error" in context.SURFACES
    assert context.SURFACES[-1] == "load-error"
    assert context.title_for("bug", "load-error", "", "") == (
        "[load-error] Bug report from load-error"
    )
    assert context.title_for("enhancement", "load-error", "", "boom") == (
        "[load-error] boom"
    )


# --- clip / labels / title --------------------------------------------------


def test_clip_collapses_whitespace_and_marks_trims() -> None:
    assert context.clip("  a\n\tb  ", 10) == "a b"
    assert context.clip("abcdefg", 5) == "ab..."
    assert context.clip("abcdefg", 1) == ""
    assert context.clip(cast(str, None), 10) == ""


def test_kind_and_label_mapping() -> None:
    assert context.kind_key("Enhancement ") == "enhancement"
    assert context.kind_key("nonsense") == "bug"
    assert context.kind_key(cast(str, None)) == "bug"
    assert context.labels_for("bug") == ["bug"]
    assert context.labels_for("enhancement") == ["enhancement"]
    assert context.labels_for("docs") == ["bug"]


def test_area_for_surfaces() -> None:
    assert context.area_for("app", "stills/still-draft") == "app:stills/still-draft"
    assert context.area_for("app", "") == "app"
    assert context.area_for("film-board", "ignored") == "film-board"
    assert context.area_for("", "") == "global"


def test_title_prefixes_and_defaults() -> None:
    assert (
        context.title_for("bug", "app", "stills/still-draft", "boom")
        == "[app:stills/still-draft] boom"
    )
    assert context.title_for("bug", "media-explorer", "", "boom") == "[media-explorer] boom"
    assert context.title_for("bug", "global", "", "boom") == "boom"
    assert context.title_for("bug", "global", "", "") == "Bug report from global"
    assert (
        context.title_for("enhancement", "watch", "", "") == "[watch] Feature request from watch"
    )
    long_title = context.title_for("bug", "app", "x" * 300, "")
    assert len(long_title) == 140
    assert long_title.endswith("...")
    assert long_title.startswith("[app:xxx")


# --- redaction --------------------------------------------------------------


def test_redact_scrubs_tokens_and_home(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    text = (
        f"token ghp_ABCDEF123456 gho_ABCDEF123456 github_pat_11AAA hf_abcdefgh {tmp_path}/media"
    )
    out = context.redact(text)
    assert "ghp_" not in out
    assert "gho_" not in out
    assert "github_pat_" not in out
    assert "hf_" not in out
    assert out.count("[redacted]") == 4
    assert out.endswith("~/media")
    assert str(tmp_path) not in out


def test_redact_passes_clean_text_and_tolerates_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", "/home/spark")
    assert context.redact("nothing to scrub") == "nothing to scrub"
    assert context.redact(cast(str, None)) == "None"


def test_redact_survives_a_broken_home_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(_path: str) -> str:
        raise OSError("no home")

    monkeypatch.setattr(os.path, "expanduser", boom)
    assert context.redact("/home/spark/media") == "/home/spark/media"


def test_redact_leaves_root_home_alone(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", "/")
    assert context.redact("/var/lib/comfyui") == "/var/lib/comfyui"


# --- body sections ----------------------------------------------------------


def test_context_lines_renders_skips_and_survives_junk() -> None:
    rows: Any = [

        ("App", "stills/still-draft"),
        ("Note", "  spaced   out "),
        ("Empty", ""),
        ("Nada", None),
        ("Zero", 0),
        ("Offline", False),
        ("", "unnamed"),
        "not a pair",
        ("only one",),
    ]
    lines = context.context_lines(rows)
    assert lines[0] == "- App: stills/still-draft"
    assert lines[1] == "- Note: spaced out"
    assert "- Zero: 0" in lines
    assert "- Offline: no" in lines
    assert "- value: unnamed" in lines
    assert all("Empty" not in line for line in lines)
    assert all("Nada" not in line for line in lines)


def test_context_lines_clips_long_values() -> None:
    lines = context.context_lines([("Note", "x" * 900)])
    assert len(lines[0]) < 400
    assert lines[0].endswith("...")


def test_error_lines_shape_and_fallbacks() -> None:
    entries: Any = [
        {
            "ts": "2026-10-28T09:00:00Z",
            "surface": "app",
            "message": "boom",
            "detail": "node 7",
        },
        {"message": "no ts here"},
        {"message": ""},
        {"no message": True},
        "not a mapping",
    ]
    lines = context.error_lines(entries, "film-board")
    assert lines == [
        "- 2026-10-28T09:00:00Z [app] boom (node 7)",
        "- unknown [film-board] no ts here",
    ]


def test_error_lines_redacts_and_defaults_to_global() -> None:
    lines = context.error_lines([{"message": "ghp_ABCDEF123456", "surface": "  "}], "")
    assert lines == ["- unknown [global] [redacted]"]


def test_error_lines_keep_a_long_traceback_first_line() -> None:
    """The ring buffer renders the whole message, not the 300-char field cap."""
    message = "RuntimeError: CUDA out of memory " + ("need more memory " * 90)
    assert 1000 < len(message) < context.MAX_ERROR_TEXT
    lines = context.error_lines([{"message": message, "detail": "node 7 " * 250}], "app")
    assert len(lines) == 1
    assert message in lines[0]
    assert "..." not in lines[0]


def test_error_lines_clip_at_the_error_cap() -> None:
    lines = context.error_lines([{"message": "m" * 2500, "detail": "d" * 2500}], "app")
    assert lines[0].startswith("- unknown [app] ")
    body = lines[0].split("] ", 1)[1]
    rendered, _, detail = body.partition(" (")
    assert rendered == "m" * (context.MAX_ERROR_TEXT - 3) + "..."
    assert detail.rstrip(")") == "d" * (context.MAX_ERROR_TEXT - 3) + "..."
    assert context.MAX_ERROR_TEXT > context.MAX_FIELD


def test_browser_lines_only_present_fields() -> None:
    lines = context.browser_lines(
        {
            "viewport": "1600x900",
            "dpr": 2,
            "lang": "en-US",
            "online": True,
            "ua": "Mozilla/5.0",
            "pageUrl": "http://127.0.0.1:8188/",
            "extra": "ignored",
        }
    )
    assert lines == [
        "- Viewport: 1600x900",
        "- DPR: 2",
        "- Language: en-US",
        "- Online: yes",
        "- User agent: Mozilla/5.0",
        "- Page URL: http://127.0.0.1:8188/",
    ]
    assert context.browser_lines(None) == []
    assert context.browser_lines(cast(Any, ["nope"])) == []


def _body_args(**overrides: Any) -> dict[str, Any]:
    """Full ``build_body`` kwargs.

    Args:
        **overrides: Field overrides.

    Returns:
        Keyword arguments for :func:`context.build_body`.
    """
    kwargs: dict[str, Any] = {
        "kind": "bug",
        "surface": "app",
        "context": [("App", "stills/still-draft")],
        "environment": [("comfyui_ref", "v0.43.0")],
        "errors": [{"ts": "2026-10-28T09:00:00Z", "message": "boom"}],
        "browser": {"viewport": "1600x900", "ua": "Mozilla/5.0"},
        "traceback": "",
    }
    kwargs.update(overrides)
    return kwargs


def test_build_body_section_order_and_fill_ins() -> None:
    body = context.build_body(**_body_args())
    order = [line for line in body.split("\n") if line.startswith("## ")]
    assert order == list(context.HEADINGS)
    assert body.count(context.FILL_IN) == 4
    for heading in context.HEADINGS:
        assert f"{heading}\n\n" in body


def test_build_body_enhancement_drops_everything_empty() -> None:
    body = context.build_body(
        kind="enhancement",
        surface="global",
        context=None,
        environment=None,
        errors=None,
        browser=None,
        traceback="",
    )
    assert body == ""


def test_build_body_keeps_only_headings_with_content() -> None:
    body = context.build_body(
        **_body_args(kind="enhancement", errors=None, browser=None, context=None)
    )
    assert "## What happened" not in body
    assert "## Context" not in body
    assert "## Recent errors" not in body
    assert "## Browser" not in body
    assert "## Environment" in body


def test_build_body_traceback_block() -> None:
    body = context.build_body(**_body_args(traceback="ValueError: bad\n  line 2"))
    assert body.rstrip().endswith("```")
    assert "Traceback:" in body
    assert "ValueError: bad" in body
    assert body.index("## Browser") < body.index("Traceback:")


def test_build_body_traceback_alone_and_blanks_off() -> None:
    alone = context.build_body(
        kind="enhancement",
        surface="global",
        context=None,
        environment=None,
        errors=None,
        browser=None,
        traceback="only this",
    )
    assert alone == "Traceback:\n\n```\nonly this\n```"
    assert "## What happened" in context.build_body(**_body_args(kind="bug"))


def test_build_body_redacts_the_traceback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", "/home/spark")
    body = context.build_body(**_body_args(traceback="KeyError ghp_ABCDEF123456"))
    assert "ghp_" not in body
    assert "[redacted]" in body


# --- narrative sections -----------------------------------------------------


def test_build_body_bug_narrative_fills_every_section() -> None:
    narrative = {
        "what_happened": "KSampler failed on the stills lane.\nSecond paragraph.",
        "steps": "1. Open still-draft\n2. Queue prompt",
        "expected": "An image lands in the output dir.",
        "actual": "ValueError: shape mismatch",
    }
    body = context.build_body(**_body_args(narrative=narrative))
    order = [line for line in body.split("\n") if line.startswith("## ")]
    assert order == list(context.HEADINGS)
    assert body.count(context.FILL_IN) == 0
    assert "## What happened\n\nKSampler failed on the stills lane.\nSecond paragraph.\n\n" in body
    assert "## Steps\n\n1. Open still-draft\n2. Queue prompt\n\n" in body
    assert "## Expected\n\nAn image lands in the output dir.\n\n" in body
    assert "## Actual\n\nValueError: shape mismatch\n\n## Context" in body


def test_build_body_bug_narrative_falls_back_on_empties() -> None:
    body = context.build_body(
        **_body_args(
            narrative={"what_happened": "  typed it  ", "steps": "   ", "actual": None}
        )
    )
    assert body.count(context.FILL_IN) == 3
    assert "## What happened\n\ntyped it\n\n" in body
    assert f"## Steps\n\n{context.FILL_IN}\n\n" in body
    assert f"## Expected\n\n{context.FILL_IN}\n\n" in body
    assert f"## Actual\n\n{context.FILL_IN}" in body


def test_build_body_bug_without_narrative_is_the_old_body() -> None:
    kwargs = _body_args()
    assert context.build_body(**kwargs) == context.build_body(**kwargs, narrative=None)


def test_build_body_narrative_keeps_its_line_breaks_and_is_never_clipped() -> None:
    text = "\n\n  first line\n  indented line\n\n" + ("x" * 5000) + "\ntail  "
    body = context.build_body(**_body_args(narrative={"what_happened": text}))
    assert "x" * 5000 in body
    assert body.count("...") == 0
    assert "## What happened\n\nfirst line\n  indented line\n\n" + "x" * 5000 + "\ntail\n\n" in body


def test_build_body_narrative_is_redacted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", "/home/spark")
    body = context.build_body(
        **_body_args(narrative={"steps": "run /home/spark/x.sh with ghp_ABCDEF123456"})
    )
    assert "ghp_" not in body
    assert "/home/spark" not in body
    assert "## Steps\n\nrun ~/x.sh with [redacted]\n\n" in body


def test_build_body_enhancement_narrative_precedes_context() -> None:
    body = context.build_body(
        **_body_args(
            kind="enhancement",
            narrative={
                "problem": "wrap is slow\non long clips",
                "solution": "stream the ffmpeg pass",
                "alternatives": "  ",
                "unlocks": None,
            },
        )
    )
    order = [line for line in body.split("\n") if line.startswith("## ")]
    assert order == [
        "## Problem",
        "## Proposed solution",
        "## Context",
        "## Environment",
        "## Recent errors",
        "## Browser",
    ]
    assert "## Problem\n\nwrap is slow\non long clips\n\n" in body
    assert "## Proposed solution\n\nstream the ffmpeg pass\n\n" in body
    assert "## Alternatives" not in body
    assert "## What it unlocks" not in body
    assert context.FILL_IN not in body


def test_build_body_enhancement_drops_empty_narrative_headings() -> None:
    empty = context.build_body(**_body_args(kind="enhancement", narrative={"problem": "  "}))
    assert "## Problem" not in empty
    assert empty == context.build_body(**_body_args(kind="enhancement"))


def test_build_body_narrative_ignores_the_other_kinds_keys() -> None:
    bug = context.build_body(**_body_args(narrative={"problem": "p", "solution": "s"}))
    assert bug.count(context.FILL_IN) == 4
    assert "## Problem" not in bug
    enhancement = context.build_body(
        **_body_args(kind="enhancement", narrative={"what_happened": "w", "steps": "s"})
    )
    assert "## What happened" not in enhancement
    assert "## Steps" not in enhancement
    assert "## Problem" not in enhancement


def test_build_body_tolerates_a_non_mapping_narrative() -> None:
    kwargs = _body_args(narrative=cast(Any, ["nope"]))
    assert context.build_body(**kwargs) == context.build_body(**_body_args())
    enhancement = context.build_body(
        **_body_args(kind="enhancement", narrative=cast(Any, "problem text"))
    )
    assert "## Problem" not in enhancement


# --- href degradation -------------------------------------------------------


def test_issue_href_short_body_keeps_everything() -> None:
    href = context.issue_href(
        "[app:x] boom", context.build_body(**_body_args()), ["bug"]
    )
    assert href.startswith("https://github.com/toxicoder/ez-comfy-stack/issues/new?")
    for needle in ("Browser", "Recent", "Environment", "title=", "labels=bug"):
        assert needle in href


def test_issue_href_drops_browser_first() -> None:
    kwargs = _body_args(
        context=[("Note", "y" * 300), ("Album", "z" * 300), ("Lane", "w" * 300)],
        browser={
            "viewport": HEAVY,
            "dpr": HEAVY,
            "lang": HEAVY,
            "online": True,
            "ua": HEAVY,
            "pageUrl": HEAVY,
        },
    )
    href = context.issue_href("t", context.build_body(**kwargs), ["bug"])
    assert len(urlencode({"title": "t", "body": context.build_body(**kwargs), "labels": "bug"})) > (
        context.MAX_HREF
    )
    assert len(href) <= context.MAX_HREF
    assert "Browser" not in href
    assert "Environment" in href


def test_issue_href_returns_once_the_sections_are_gone() -> None:
    kwargs = _body_args(
        environment=[(f"k{index}", HEAVY) for index in range(8)],
        traceback="z" * 3000,
    )
    href = context.issue_href("t", context.build_body(**kwargs), ["bug"])
    assert len(href) <= context.MAX_HREF
    for gone in ("Browser", "Recent", "Environment"):
        assert gone not in href
    assert "Traceback" in href


def test_issue_href_drops_down_to_the_traceback() -> None:
    kwargs = _body_args(traceback="z" * 9000)
    href = context.issue_href("t", context.build_body(**kwargs), ["bug", "documentation"])
    assert len(href) <= context.MAX_HREF
    for gone in ("Traceback", "Browser", "Recent", "Environment"):
        assert gone not in href
    assert "labels=bug%2Cdocumentation" in href


def test_issue_href_defaults_to_the_shared_repo() -> None:
    href = context.issue_href("t", "b", [])
    assert href.startswith(f"{context.GITHUB_URL}/{context.REPO}/issues/new?")


# --- env_snapshot -----------------------------------------------------------


def test_env_snapshot_without_probe() -> None:
    facts = context.env_snapshot(
        {
            "COMFYUI_REF": "v0.43.0",
            "EZ_COMFY_IMAGE": "ghcr.io/toxicoder/ez-comfy:us-safe-studio-development",
            "COMFY_OUTPUT_DIR": "/media/comfy-output",
            "COMFY_PORT": "8199",
        }
    )
    assert facts["comfyui_ref"] == "v0.43.0"
    assert facts["image"].startswith("ghcr.io/")
    assert facts["output_dir"] == "/media/comfy-output"
    assert facts["comfy_port"] == "8199"
    assert facts["python"].startswith("3.")
    assert " " in facts["platform"]
    assert set(facts) >= {
        "comfyui_ref",
        "image",
        "python",
        "platform",
        "output_dir",
        "comfy_port",
    }


def test_env_snapshot_defaults_and_missing_keys() -> None:
    facts = context.env_snapshot({})
    assert facts["comfyui_ref"] == ""
    assert facts["comfy_port"] == "8188"


def test_env_snapshot_merges_the_injected_probe() -> None:
    facts = context.env_snapshot(
        {"COMFYUI_REF": "v0.43.0"},
        probe=lambda: cast(Any, {"torch": "2.7.0", "gpu": "NVIDIA GB10", "skip": "", "none": None}),
    )
    assert facts["torch"] == "2.7.0"
    assert facts["gpu"] == "NVIDIA GB10"
    assert "skip" not in facts
    assert "none" not in facts


def test_env_snapshot_never_raises() -> None:
    facts = context.env_snapshot(_BoomEnv(), probe=lambda: cast(Any, "not a mapping"))
    assert facts["comfyui_ref"] == ""
    assert facts["python"].startswith("3.")

    def boom() -> dict[str, str]:
        raise RuntimeError("no cuda here")

    broken = context.env_snapshot({}, probe=boom)
    assert "torch" not in broken


def test_env_snapshot_falls_back_when_platform_is_broken(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom() -> str:
        raise OSError("no platform")

    monkeypatch.setattr(context.platform, "python_version", boom)
    monkeypatch.setattr(context.platform, "system", boom)
    facts = context.env_snapshot({})
    assert facts["python"] == "unknown"
    assert facts["platform"] == "unknown"


def test_env_snapshot_redacts_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", "/home/spark")
    facts = context.env_snapshot(
        {"COMFY_OUTPUT_DIR": "/home/spark/media", "EZ_COMFY_IMAGE": "hf_TOKENVALUE1"},
        probe=lambda: {"note": "ghp_ABCDEF123456"},
    )
    assert facts["output_dir"] == "~/media"
    assert facts["image"] == "[redacted]"
    assert facts["note"] == "[redacted]"


# --- routes: config ---------------------------------------------------------


def test_config_payload_exposes_token_as_bool_only() -> None:
    status, payload = routes.config_payload(
        environ={routes.TOKEN_ENV: TOKEN, "COMFYUI_REF": "v0.43.0"},
        probe=lambda: {"torch": "2.7.0"},
    )
    assert status == 200
    assert payload["tokenPresent"] is True
    assert payload["repoUrl"] == "https://github.com/toxicoder/ez-comfy-stack"
    assert payload["labels"] == ["bug", "documentation", "enhancement"]
    assert payload["env"]["torch"] == "2.7.0"
    assert TOKEN not in json.dumps(payload)
    assert "ghp_" not in json.dumps(payload)


def test_config_payload_without_token_or_probe() -> None:
    status, payload = routes.config_payload(environ={})
    assert status == 200
    assert payload["tokenPresent"] is False
    assert "comfyui_ref" in payload["env"]


def test_config_payload_defaults_to_os_environ(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(routes.TOKEN_ENV, TOKEN)
    _status, payload = routes.config_payload()
    assert payload["tokenPresent"] is True


# --- routes: submit ---------------------------------------------------------


def test_handle_submit_posts_to_github() -> None:
    captured: list[urllib.request.Request] = []
    opener = _opener(json.dumps({"html_url": "https://x/1", "number": 7}).encode(), captured)
    status, payload = routes.handle_submit(
        _report_args(), environ={routes.TOKEN_ENV: TOKEN}, opener=opener
    )
    assert status == 200
    assert payload == {"ok": True, "url": "https://x/1", "number": 7}
    request = captured[0]
    assert request.full_url == "https://api.github.com/repos/toxicoder/ez-comfy-stack/issues"
    assert request.get_method() == "POST"
    assert request.get_header("Authorization") == f"Bearer {TOKEN}"
    assert request.get_header("User-agent") == routes.USER_AGENT
    sent = _sent(request)
    assert sent["labels"] == ["bug"]
    assert sent["title"].startswith("[app:")
    assert "## What happened" in sent["body"]


def test_handle_submit_defaults_title_and_labels() -> None:
    captured: list[urllib.request.Request] = []
    opener = _opener(b"{}", captured)
    status, payload = routes.handle_submit(
        {"kind": "enhancement"}, environ={routes.TOKEN_ENV: TOKEN}, opener=opener
    )
    assert status == 200
    assert payload == {"ok": True, "url": "", "number": None}
    sent = _sent(captured[0])
    assert sent["title"] == "Feature request from global"
    assert sent["labels"] == ["enhancement"]


def test_handle_submit_filters_unknown_labels() -> None:
    captured: list[urllib.request.Request] = []
    opener = _opener(b'{"number": 3}', captured)
    status, payload = routes.handle_submit(
        _report_args(kind="enhancement", labels=["documentation", "secrets", "", " bug "]),
        environ={routes.TOKEN_ENV: TOKEN},
        opener=opener,
    )
    sent = _sent(captured[0])
    assert status == 200
    assert payload["number"] == 3
    assert sent["labels"] == ["bug", "documentation"]


def test_handle_submit_labels_default_when_nothing_is_allowed() -> None:
    captured: list[urllib.request.Request] = []
    opener = _opener(b"{}", captured)
    routes.handle_submit(
        _report_args(labels=["nope"]), environ={routes.TOKEN_ENV: TOKEN}, opener=opener
    )
    sent = _sent(captured[0])
    assert sent["labels"] == ["bug"]


def test_handle_submit_clips_body_and_title() -> None:
    captured: list[urllib.request.Request] = []
    opener = _opener(b"{}", captured)
    routes.handle_submit(
        _report_args(title="t" * 400, body="b" * 90000),
        environ={routes.TOKEN_ENV: TOKEN},
        opener=opener,
    )
    sent = _sent(captured[0])
    assert len(sent["title"]) == 140
    assert len(sent["body"]) == context.MAX_BODY


def test_handle_submit_redacts_the_body() -> None:
    captured: list[urllib.request.Request] = []
    opener = _opener(b"{}", captured)
    routes.handle_submit(
        _report_args(body="leaked ghp_ABCDEF123456 here"),
        environ={routes.TOKEN_ENV: TOKEN},
        opener=opener,
    )
    sent = _sent(captured[0])
    assert "ghp_" not in sent["body"]


def test_handle_submit_rejects_non_github_host() -> None:
    captured: list[urllib.request.Request] = []

    def opener(request: Any, timeout: float) -> _Response:
        captured.append(request)
        raise AssertionError("must not post off-host")

    status, payload = routes.handle_submit(
        _report_args(),
        environ={routes.TOKEN_ENV: TOKEN, routes.API_BASE_ENV: "https://evil.example.com/repos"},
        opener=opener,
    )
    assert status == 400
    assert payload == {"ok": False, "error": "host must be api.github.com"}
    assert captured == []


def test_api_url_honours_the_base_override_within_the_pinned_host() -> None:
    assert routes.api_url("o/r") == "https://api.github.com/repos/o/r/issues"
    assert (
        routes.api_url("o/r", {routes.API_BASE_ENV: "https://api.github.com/api/v3/repos/"})
        == "https://api.github.com/api/v3/repos/o/r/issues"
    )


def test_handle_submit_without_token_is_409() -> None:
    def opener(request: Any, timeout: float) -> _Response:
        raise AssertionError("must not post without a token")

    status, payload = routes.handle_submit(_report_args(), environ={}, opener=opener)
    assert status == 409
    assert payload == {"ok": False, "error": "no token; use the GitHub link"}


def test_handle_submit_blank_token_is_409() -> None:
    status, payload = routes.handle_submit(
        _report_args(), environ={routes.TOKEN_ENV: "   "}, opener=None
    )
    assert status == 409
    assert payload["error"] == routes.NO_TOKEN_ERROR


def test_handle_submit_tolerates_a_non_mapping_body() -> None:
    captured: list[urllib.request.Request] = []
    opener = _opener(b"[]", captured)
    status, payload = routes.handle_submit(
        [], environ={routes.TOKEN_ENV: TOKEN}, opener=opener  # type: ignore[arg-type]
    )
    assert status == 200
    assert payload["url"] == ""


def test_handle_submit_github_http_error_is_502() -> None:
    def opener(request: Any, timeout: float) -> _Response:
        raise urllib.error.HTTPError(request.full_url, 403, "Forbidden", Message(), None)

    status, payload = routes.handle_submit(
        _report_args(), environ={routes.TOKEN_ENV: TOKEN}, opener=opener
    )
    assert status == 502
    assert payload == {"ok": False, "error": "github error 403"}


def test_handle_submit_url_error_is_502() -> None:
    def opener(request: Any, timeout: float) -> _Response:
        raise urllib.error.URLError("no route to host")

    status, payload = routes.handle_submit(
        _report_args(), environ={routes.TOKEN_ENV: TOKEN}, opener=opener
    )
    assert status == 502
    assert payload["error"].startswith("github unreachable")


def test_handle_submit_unexpected_error_never_leaks_the_token() -> None:
    def opener(request: Any, timeout: float) -> _Response:
        raise RuntimeError(f"header said Bearer {TOKEN}")

    status, payload = routes.handle_submit(
        _report_args(), environ={routes.TOKEN_ENV: TOKEN}, opener=opener
    )
    assert status == 500
    assert TOKEN not in json.dumps(payload)
    assert "ghp_" not in json.dumps(payload)


def test_handle_submit_bad_json_response_degrades() -> None:
    captured: list[urllib.request.Request] = []
    opener = _opener(b"not json at all", captured)
    status, payload = routes.handle_submit(
        _report_args(), environ={routes.TOKEN_ENV: TOKEN}, opener=opener
    )
    assert status == 200
    assert payload == {"ok": True, "url": "", "number": None}


def test_issue_fields_shapes() -> None:
    assert routes._issue_fields(b'{"html_url": "https://x/2", "number": 2}') == {
        "url": "https://x/2",
        "number": 2,
    }
    assert routes._issue_fields('{"number": "9"}') == {"url": "", "number": None}
    assert routes._issue_fields(object()) == {"url": "", "number": None}


def test_urlopen_delegates_to_urllib(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[Any] = []

    def fake(request: Any, timeout: float) -> str:
        seen.append((request, timeout))
        return "opened"

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    request = urllib.request.Request("https://api.github.com/x")
    assert routes.urlopen(request, 1.5) == "opened"
    assert seen == [(request, 1.5)]


def test_handle_submit_uses_the_module_urlopen_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[Any] = []

    def fake(request: Any, timeout: float) -> _Response:
        calls.append(request)
        return _Response(b'{"html_url": "https://x/5", "number": 5}')

    monkeypatch.setattr(routes, "urlopen", fake)
    status, payload = routes.handle_submit(_report_args(), environ={routes.TOKEN_ENV: TOKEN})
    assert status == 200
    assert payload["number"] == 5
    assert len(calls) == 1


# --- routes: gpu probe ------------------------------------------------------


def test_gpu_probe_without_torch() -> None:
    assert routes.gpu_probe() == {}
    assert routes._import_torch() is None


def test_gpu_probe_imports_torch_lazily(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = types.SimpleNamespace(__version__="2.7.0")
    monkeypatch.setitem(sys.modules, "torch", fake)
    assert routes._import_torch() is fake
    assert routes.gpu_probe() == {"torch": "2.7.0"}


def test_gpu_probe_reads_a_torch_stand_in() -> None:
    class _Cuda:
        @staticmethod
        def is_available() -> bool:
            return True

        @staticmethod
        def get_device_name(index: int) -> str:
            return "NVIDIA GB10"

    class _Version:
        cuda = "12.8"

    class _Torch:
        __version__ = "2.7.0"
        version = _Version()
        cuda = _Cuda()

    assert routes.gpu_probe(_Torch()) == {
        "torch": "2.7.0",
        "cuda": "12.8",
        "gpu": "NVIDIA GB10",
    }


def test_gpu_probe_tolerates_a_broken_cuda() -> None:
    class _BrokenCuda:
        def is_available(self) -> bool:
            raise RuntimeError("no driver")

    class _Torch:
        __version__ = "2.7.0"
        version = None
        cuda = _BrokenCuda()

    assert routes.gpu_probe(_Torch()) == {"torch": "2.7.0"}


def test_gpu_probe_drops_empty_facts() -> None:
    class _Torch:
        __version__ = ""
        version = None
        cuda = None

    assert routes.gpu_probe(_Torch()) == {}


# --- routes: enhance --------------------------------------------------------


def _enhance_args(**overrides: Any) -> dict[str, Any]:
    """A well-formed enhance body.

    Args:
        **overrides: Field overrides.

    Returns:
        Request body dict.
    """
    args: dict[str, Any] = {"kind": "bug", "text": "KSampler blew up on the stills lane"}
    args.update(overrides)
    return args


def _no_llm(_system: str, _user: str) -> tuple[str, str]:
    """Model stand-in that must never be reached.

    Args:
        _system: Unused system prompt.
        _user: Unused user text.

    Returns:
        Never returns.

    Raises:
        AssertionError: Always, so a refused request cannot call the model.
    """
    raise AssertionError("must not call the model")


def test_enhance_prompts_are_the_committed_files() -> None:
    assert routes.ENHANCE_PROMPTS == {
        "bug": routes.ENHANCE_BUG_PROMPT,
        "enhancement": routes.ENHANCE_ENHANCEMENT_PROMPT,
    }
    assert (routes.PROMPT_DIR / "enhance_bug.txt").is_file()
    assert (routes.PROMPT_DIR / "enhance_enhancement.txt").is_file()
    for kind, headings in (
        ("bug", context.FILL_HEADINGS),
        ("enhancement", context.ENHANCE_HEADINGS),
    ):
        text = routes.ENHANCE_PROMPTS[kind]
        assert text.strip()
        assert text.isascii()
        assert "ez-comfy-stack" in text
        assert "Never invent" in text or "never invent" in text.lower()
        positions = [text.index(heading) for heading in headings]
        assert positions == sorted(positions)


def test_handle_enhance_rewrites_with_the_injected_model() -> None:
    seen: list[tuple[str, str]] = []

    def llm(system: str, user: str) -> tuple[str, str]:
        seen.append((system, user))
        return "  ## What happened\n\nboom  ", "ignored"

    status, payload = routes.handle_enhance(_enhance_args(), llm=llm)
    assert status == 200
    assert payload == {"ok": True, "text": "## What happened\n\nboom"}
    assert seen == [(routes.ENHANCE_BUG_PROMPT, "KSampler blew up on the stills lane")]


def test_handle_enhance_picks_the_prompt_by_normalized_kind() -> None:
    seen: list[str] = []

    def llm(system: str, _user: str) -> tuple[str, str | None]:
        seen.append(system)
        return "text", None

    for kind in ("Enhancement ", "ENHANCEMENT", "nonsense", "", None):
        status, _payload = routes.handle_enhance(_enhance_args(kind=kind), llm=llm)
        assert status == 200
    assert seen == [
        routes.ENHANCE_ENHANCEMENT_PROMPT,
        routes.ENHANCE_ENHANCEMENT_PROMPT,
        routes.ENHANCE_BUG_PROMPT,
        routes.ENHANCE_BUG_PROMPT,
        routes.ENHANCE_BUG_PROMPT,
    ]


def test_handle_enhance_redacts_the_notes_before_the_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", "/home/spark")
    seen: list[str] = []

    def llm(_system: str, user: str) -> tuple[str, str | None]:
        seen.append(user)
        return "fine", None

    status, _payload = routes.handle_enhance(
        _enhance_args(text="  run /home/spark/x.sh with ghp_ABCDEF123456  "), llm=llm
    )
    assert status == 200
    assert seen == ["run ~/x.sh with [redacted]"]


def test_handle_enhance_without_notes_is_400() -> None:
    for body in ({}, {"text": "   "}, {"text": None}, {"text": 0}, ["not a mapping"], None):
        status, payload = routes.handle_enhance(cast(Any, body), llm=_no_llm)
        assert status == 400
        assert payload == {"ok": False, "error": "nothing to enhance"}


def test_handle_enhance_over_the_input_cap_is_400() -> None:
    status, payload = routes.handle_enhance(
        _enhance_args(text="x" * (routes.ENHANCE_INPUT_MAX + 1)), llm=_no_llm
    )
    assert status == 400
    assert payload == {"ok": False, "error": "text too long"}

    at_cap = routes.handle_enhance(
        _enhance_args(text="x" * routes.ENHANCE_INPUT_MAX), llm=lambda s, u: ("ok", None)
    )
    assert at_cap[0] == 200


def test_handle_enhance_without_an_answer_is_503() -> None:
    status, payload = routes.handle_enhance(_enhance_args(), llm=lambda s, u: ("", "no gguf"))
    assert status == 503
    assert payload == {"ok": False, "error": "no gguf"}

    blank = routes.handle_enhance(_enhance_args(), llm=lambda s, u: ("   ", None))
    assert blank[0] == 503
    assert blank[1] == {"ok": False, "error": routes.LLM_UNAVAILABLE_ERROR}

    none = routes.handle_enhance(_enhance_args(), llm=lambda s, u: (cast(Any, None), ""))
    assert none[0] == 503
    assert none[1] == {"ok": False, "error": routes.LLM_UNAVAILABLE_ERROR}


def test_handle_enhance_model_raise_is_502_with_the_type_name_only() -> None:
    def llm(_system: str, _user: str) -> tuple[str, str]:
        raise RuntimeError(f"sidecar said {TOKEN} about the stills lane")

    status, payload = routes.handle_enhance(_enhance_args(), llm=llm)
    assert status == 502
    assert payload == {"ok": False, "error": "RuntimeError"}
    assert TOKEN not in json.dumps(payload)


def test_handle_enhance_caps_and_redacts_the_rewrite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", "/home/spark")
    status, payload = routes.handle_enhance(
        _enhance_args(),
        llm=lambda s, u: ("y" * 20000 + " ghp_ABCDEF123456 /home/spark/x", None),
    )
    assert status == 200
    text = str(payload["text"])
    assert len(text) == routes.ENHANCE_OUTPUT_MAX
    assert set(text) == {"y"}


def test_handle_enhance_defaults_to_the_enhance_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[tuple[str, str]] = []

    def complete(system: str, user: str) -> tuple[str | None, str | None]:
        seen.append((system, user))
        return "## Problem\n\nplease", None

    package = types.ModuleType("ez_prompt_enhance")
    client = types.ModuleType("ez_prompt_enhance.client")
    client.complete = complete  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "ez_prompt_enhance", package)
    monkeypatch.setitem(sys.modules, "ez_prompt_enhance.client", client)

    status, payload = routes.handle_enhance(_enhance_args(kind="enhancement"))
    assert status == 200
    assert payload["text"] == "## Problem\n\nplease"
    assert seen == [(routes.ENHANCE_ENHANCEMENT_PROMPT, "KSampler blew up on the stills lane")]


def test_handle_enhance_without_the_enhance_pack_is_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "ez_prompt_enhance", types.ModuleType("ez_prompt_enhance"))
    monkeypatch.setitem(sys.modules, "ez_prompt_enhance.client", None)
    status, payload = routes.handle_enhance(_enhance_args())
    assert status == 503
    assert payload == {"ok": False, "error": routes.LLM_UNAVAILABLE_ERROR}


def test_default_llm_passes_through_a_reason(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = types.ModuleType("ez_prompt_enhance.client")

    def complete(_system: str, _user: str) -> tuple[str | None, str | None]:
        return None, "gguf missing"

    client.complete = complete  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "ez_prompt_enhance", types.ModuleType("ez_prompt_enhance"))
    monkeypatch.setitem(sys.modules, "ez_prompt_enhance.client", client)
    assert routes._default_llm("system", "user") == ("", "gguf missing")

    def raiser(_system: str, _user: str) -> tuple[str, str]:
        raise RuntimeError("no gguf")

    client.complete = raiser  # type: ignore[attr-defined]
    assert routes._default_llm("system", "user") == ("", routes.LLM_UNAVAILABLE_ERROR)


# --- routes: registration ---------------------------------------------------


def test_register_routes_attaches_both_paths() -> None:
    adder = _Adder()
    registered = routes.register_routes(
        server=types.SimpleNamespace(routes=adder), json_response=_respond
    )
    assert registered is True
    assert ("get", "/ez_feedback/config") in adder.recorded
    assert ("post", "/ez_feedback/submit") in adder.recorded


def test_register_routes_attaches_the_enhance_path() -> None:
    adder = _Adder()
    registered = routes.register_routes(
        server=types.SimpleNamespace(routes=adder), json_response=_respond
    )
    assert registered is True
    assert ("post", "/ez_feedback/enhance") in adder.recorded
    assert adder.recorded == [
        ("get", "/ez_feedback/config"),
        ("post", "/ez_feedback/submit"),
        ("post", "/ez_feedback/enhance"),
    ]
    assert routes.ENHANCE_PATH == "/ez_feedback/enhance"
    assert callable(adder.handlers[routes.ENHANCE_PATH])


def test_register_routes_without_aiohttp(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "aiohttp", None)
    assert routes.register_routes() is False


def test_register_routes_without_routes_attr() -> None:
    assert routes.register_routes(server=object(), json_response=_respond) is False


def test_register_routes_without_adders() -> None:
    registered = routes.register_routes(
        server=types.SimpleNamespace(routes=_NoAdders()), json_response=_respond
    )
    assert registered is False


def test_register_routes_with_aiohttp_and_server_module(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adder = _Adder()
    aiohttp = types.ModuleType("aiohttp")
    aiohttp.web = types.SimpleNamespace(json_response=_respond)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "aiohttp", aiohttp)
    monkeypatch.setitem(
        sys.modules,
        "server",
        types.SimpleNamespace(
            PromptServer=types.SimpleNamespace(instance=types.SimpleNamespace(routes=adder))
        ),
    )
    assert routes.register_routes() is True
    assert ("get", "/ez_feedback/config") in adder.recorded


def test_register_routes_when_the_server_import_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    aiohttp = types.ModuleType("aiohttp")
    aiohttp.web = types.SimpleNamespace(json_response=_respond)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "aiohttp", aiohttp)
    monkeypatch.setitem(sys.modules, "server", None)
    assert routes.register_routes() is False


def test_register_routes_when_server_module_has_no_instance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    aiohttp = types.ModuleType("aiohttp")
    aiohttp.web = types.SimpleNamespace(json_response=_respond)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "aiohttp", aiohttp)
    monkeypatch.setitem(
        sys.modules,
        "server",
        types.SimpleNamespace(PromptServer=types.SimpleNamespace(instance=None)),
    )
    assert routes.register_routes() is False


def test_handlers_serve_config_and_submit(monkeypatch: pytest.MonkeyPatch) -> None:
    adder = _Adder()
    routes.register_routes(
        server=types.SimpleNamespace(routes=adder), json_response=_respond
    )
    monkeypatch.setattr(routes, "urlopen", lambda request, timeout: _Response(b'{"number": 11}'))
    monkeypatch.setenv(routes.TOKEN_ENV, TOKEN)
    monkeypatch.delenv(routes.API_BASE_ENV, raising=False)

    async def _run() -> None:
        config = await adder.handlers["/ez_feedback/config"](None)
        assert config[0] == 200
        assert config[1]["tokenPresent"] is True
        assert config[1]["env"]["comfy_port"]

        submitted = await adder.handlers["/ez_feedback/submit"](
            _Req(body={"kind": "enhancement", "body": "please"})
        )
        assert submitted[0] == 200
        assert submitted[1]["ok"] is True
        assert submitted[1]["number"] == 11

        broken = await adder.handlers["/ez_feedback/submit"](_Req(boom=True))
        assert broken[0] == 200

        not_dict = await adder.handlers["/ez_feedback/submit"](_Req(body=["x"]))
        assert not_dict[0] == 200

        monkeypatch.delenv(routes.TOKEN_ENV, raising=False)
        no_token = await adder.handlers["/ez_feedback/submit"](_Req(body={"body": "x"}))
        assert no_token[0] == 409

    asyncio.run(_run())


def test_enhance_handler_answers_from_a_worker_thread(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adder = _Adder()
    routes.register_routes(
        server=types.SimpleNamespace(routes=adder), json_response=_respond
    )
    seen: list[tuple[str, str]] = []

    def llm(system: str, user: str) -> tuple[str, str | None]:
        seen.append((system, user))
        assert threading.current_thread() is not threading.main_thread()
        return "## What happened\n\nfixed", None

    monkeypatch.setattr(routes, "_default_llm", llm)

    async def _run() -> None:
        ok = await adder.handlers[routes.ENHANCE_PATH](_Req(body={"kind": "bug", "text": "boom"}))
        assert ok[0] == 200
        assert ok[1] == {"ok": True, "text": "## What happened\n\nfixed"}

        blank = await adder.handlers[routes.ENHANCE_PATH](_Req(body={"text": "   "}))
        assert blank[0] == 400
        assert blank[1]["error"] == "nothing to enhance"

        broken = await adder.handlers[routes.ENHANCE_PATH](_Req(boom=True))
        assert broken[0] == 400

        not_dict = await adder.handlers[routes.ENHANCE_PATH](_Req(body=["x"]))
        assert not_dict[0] == 400

    asyncio.run(_run())
    assert seen == [(routes.ENHANCE_BUG_PROMPT, "boom")]


def test_request_json_shapes() -> None:
    class _Async:
        async def json(self) -> dict[str, str]:
            return {"a": "b"}

    class _Sync:
        def json(self) -> dict[str, str]:
            return {"c": "d"}

    class _Raises:
        def json(self) -> dict[str, str]:
            raise ValueError("nope")

    async def _run() -> None:
        assert await routes.request_json(_Async()) == {"a": "b"}
        assert await routes.request_json(_Sync()) == {"c": "d"}
        assert await routes.request_json(_Raises()) == {}
        assert await routes.request_json(object()) == {}
        assert await routes.request_json(None) == {}

    asyncio.run(_run())


def test_token_reads_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(routes.TOKEN_ENV, f"  {TOKEN} ")
    assert routes.token() == TOKEN
    monkeypatch.delenv(routes.TOKEN_ENV, raising=False)
    assert routes.token() == ""
    assert routes.token({}) == ""
