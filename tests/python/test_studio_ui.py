"""Hermetic tests for studio-ui watch/download (no network listen)."""

from __future__ import annotations
import pytest

import ast
import importlib.util
import io
import json
import re
from html import unescape
from pathlib import Path
from types import ModuleType
from typing import Any
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[2]


def _load_server() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "studio_ui_server", ROOT / "studio-ui" / "server.py"
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_watch_and_download_allowlist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    films = tmp_path / "films" / "gosee"
    films.mkdir(parents=True)
    (films / "state.json").write_text(
        json.dumps({"slug": "gosee", "film": "go-see", "shots": []}),
        encoding="utf-8",
    )
    mp4 = tmp_path / "ez_gosee_90s.mp4"
    mp4.write_bytes(b"fake-mp4")
    server = _load_server()
    monkeypatch.setattr(server, "FILMS", tmp_path / "films")
    assert server.publish_mp4("gosee") == mp4
    assert server.publish_mp4("nope") is None
    assert server.publish_mp4("../etc") is None
    page = server.watch_page("gosee")
    assert page is not None
    text = page.decode("utf-8")
    assert "<video" in text
    assert "/media/gosee" in text
    assert "Download MP4" in text
    assert server.watch_page("nope") is None


def test_studio_packages_export_empty_node_maps() -> None:
    import ez_outputs
    import ez_studio_app
    import ez_studio_blocks

    assert ez_studio_app.NODE_CLASS_MAPPINGS == {}
    assert ez_studio_app.WEB_DIRECTORY == "./js"
    assert ez_outputs.NODE_CLASS_MAPPINGS == {}
    assert ez_outputs.WEB_DIRECTORY == "./js"
    assert ez_studio_blocks.NODE_CLASS_MAPPINGS == {}
    assert "NODE_DISPLAY_NAME_MAPPINGS" in ez_studio_blocks.__all__


def _bind_handler(server: ModuleType, path: str) -> tuple[Any, dict[str, object]]:
    from io import BytesIO

    handler = server.Handler.__new__(server.Handler)
    handler.path = path
    handler.wfile = BytesIO()
    captured: dict[str, object] = {"status": None, "headers": []}

    def send_response(code: int, _message: str | None = None) -> None:
        captured["status"] = code

    def send_header(key: str, value: str) -> None:
        headers = captured["headers"]
        assert isinstance(headers, list)
        headers.append((key, value))

    handler.send_response = send_response  # type: ignore[method-assign]
    handler.send_header = send_header  # type: ignore[method-assign]
    handler.end_headers = lambda: None  # type: ignore[method-assign]
    handler.headers = {}  # type: ignore[method-assign]
    return handler, captured


def test_handler_routes_watch_media_thumb_and_board(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    films = tmp_path / "films" / "gosee"
    films.mkdir(parents=True)
    (films / "state.json").write_text(
        json.dumps(
            {
                "slug": "gosee",
                "film": "go-see",
                "audio_policy": "world-only",
                "shots": [{"id": "01", "status": "ok"}],
            }
        ),
        encoding="utf-8",
    )
    (films / "stems" / "01").mkdir(parents=True)
    (films / "stems" / "01" / "mix.wav").write_bytes(b"mix")
    guides = tmp_path / "guides" / "gosee" / "01"
    guides.mkdir(parents=True)
    (guides / "first.png").write_bytes(b"png-clay")
    (guides / "overlay.png").write_bytes(b"png-ov")
    (guides / "score.json").write_text("{}", encoding="utf-8")
    (tmp_path / "ez_gosee_90s.mp4").write_bytes(b"mp4-bytes")
    server = _load_server()
    monkeypatch.setattr(server, "FILMS", tmp_path / "films")
    monkeypatch.setattr(server, "GUIDES", tmp_path / "guides")

    handler, captured = _bind_handler(server, "/")
    server.Handler.do_GET(handler)
    assert captured["status"] == 200
    board = handler.wfile.getvalue().decode("utf-8")
    assert "ez-comfy film board" in board
    assert "/watch/gosee" in board
    assert "clay" in board

    handler, captured = _bind_handler(server, "/watch/gosee")
    server.Handler.do_GET(handler)
    assert captured["status"] == 200
    assert b"<video" in handler.wfile.getvalue()

    handler, captured = _bind_handler(server, "/media/gosee")
    server.Handler.do_GET(handler)
    assert captured["status"] == 200
    assert handler.wfile.getvalue() == b"mp4-bytes"

    handler, captured = _bind_handler(server, "/media/gosee?dl=1")
    server.Handler.do_GET(handler)
    assert captured["status"] == 200
    assert handler.wfile.getvalue() == b"mp4-bytes"
    headers = captured["headers"]
    assert isinstance(headers, list)
    assert any(k == "Content-Disposition" for k, _v in headers)

    handler, captured = _bind_handler(server, "/watch/nope")
    server.Handler.do_GET(handler)
    assert captured["status"] == 404

    handler, captured = _bind_handler(server, "/media/nope")
    server.Handler.do_GET(handler)
    assert captured["status"] == 404

    handler, captured = _bind_handler(server, "/thumb?slug=gosee&shot=01&kind=clay")
    server.Handler.do_GET(handler)
    assert captured["status"] == 200
    assert handler.wfile.getvalue() == b"png-clay"

    handler, captured = _bind_handler(server, "/thumb?slug=../x&shot=01&kind=clay")
    server.Handler.do_GET(handler)
    assert captured["status"] == 404

    handler, captured = _bind_handler(server, "/thumb?slug=gosee&shot=01&kind=overlay")
    server.Handler.do_GET(handler)
    assert captured["status"] == 200
    assert handler.wfile.getvalue() == b"png-ov"

    empty = tmp_path / "empty-films"
    empty.mkdir()
    monkeypatch.setattr(server, "FILMS", empty)
    handler, captured = _bind_handler(server, "/")
    server.Handler.do_GET(handler)
    assert b"No films yet" in handler.wfile.getvalue()

    server.Handler.log_message(handler, "ignored %s", "x")


def test_main_uses_mocked_server(monkeypatch: pytest.MonkeyPatch) -> None:
    server = _load_server()
    seen: dict[str, object] = {}

    class FakeServer:
        def __init__(self, addr: tuple[str, int], handler: object) -> None:
            seen["addr"] = addr
            seen["handler"] = handler

        def serve_forever(self) -> None:
            seen["served"] = True

    monkeypatch.setattr(server, "ThreadingHTTPServer", FakeServer)
    server.main()
    assert seen["addr"] == ("0.0.0.0", 8190)
    assert seen["served"] is True


def test_rows_when_films_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    server = _load_server()
    monkeypatch.setattr(server, "FILMS", tmp_path / "no-such-films")
    assert server._rows() == []


def test_rows_skip_invalid_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dest = tmp_path / "films" / "bad"
    dest.mkdir(parents=True)
    (dest / "state.json").write_text("{not-json", encoding="utf-8")
    server = _load_server()
    monkeypatch.setattr(server, "FILMS", tmp_path / "films")
    assert server._rows() == []


def test_publish_mp4_when_films_is_not_named_films(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    server = _load_server()
    monkeypatch.setattr(server, "FILMS", tmp_path)
    (tmp_path / "ez_gosee_90s.mp4").write_bytes(b"x")
    assert server.publish_mp4("gosee") == tmp_path / "ez_gosee_90s.mp4"
    assert server.output_root() == tmp_path


def test_guides_alt_when_parent_guides_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    alt = tmp_path / "films" / "guides"
    alt.mkdir(parents=True)
    original = Path.is_dir

    def fake_is_dir(self: Path) -> bool:
        text = str(self)
        if text == "/films/films":
            return False
        if text == "/films":
            return True
        if text == "/guides":
            return False
        if text == "/films/guides":
            return True
        return original(self)

    monkeypatch.setattr(Path, "is_dir", fake_is_dir)
    server = _load_server()
    assert server.GUIDES == Path("/films/guides")
    assert server.FILMS == Path("/films")


def test_publish_mp4_resolve_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    server = _load_server()
    monkeypatch.setattr(server, "FILMS", tmp_path)
    (tmp_path / "ez_gosee_90s.mp4").write_bytes(b"x")

    def boom(self: Path) -> Path:
        del self
        raise OSError("resolve failed")

    monkeypatch.setattr(Path, "resolve", boom)
    assert server.publish_mp4("gosee") is None


def test_overlay_thumb_when_clay_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dest = tmp_path / "films" / "gosee"
    dest.mkdir(parents=True)
    pack = tmp_path / "guides" / "gosee" / "01"
    pack.mkdir(parents=True)
    (pack / "overlay.png").write_bytes(b"ov")
    server = _load_server()
    monkeypatch.setattr(server, "FILMS", tmp_path / "films")
    monkeypatch.setattr(server, "GUIDES", tmp_path / "guides")
    lights = server._shot_lights(dest, "gosee", "01", {"status": ""})
    assert "kind=overlay" in lights["thumb"]
    assert lights["look"] == "on"


def test_page_skips_non_dict_shot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    server = _load_server()
    monkeypatch.setattr(
        server,
        "_rows",
        lambda: [
            {
                "slug": "gosee",
                "film": "go-see",
                "ok": "0",
                "total": "1",
                "audio_policy": "world-only",
                "shots": ["not-a-dict", {"id": "01", "thumb": ""}],
            }
        ],
    )
    html = server._page().decode("utf-8")
    assert "01" in html
    assert "not-a-dict" not in html


def test_safe_thumb_resolve_fail_and_missing_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    server = _load_server()
    monkeypatch.setattr(server, "GUIDES", tmp_path / "guides")
    (tmp_path / "guides" / "gosee" / "01").mkdir(parents=True)
    assert server._safe_thumb("gosee", "01", "overlay") is None

    def boom(self: Path) -> Path:
        del self
        raise ValueError("escape")

    monkeypatch.setattr(Path, "resolve", boom)
    assert server._safe_thumb("gosee", "01", "clay") is None


def test_server_dunder_main(monkeypatch: pytest.MonkeyPatch) -> None:
    import runpy

    seen: dict[str, object] = {}

    class FakeServer:
        def __init__(self, addr: tuple[str, int], handler: object) -> None:
            seen["addr"] = addr
            seen["handler"] = handler

        def serve_forever(self) -> None:
            seen["served"] = True

    monkeypatch.setattr("http.server.ThreadingHTTPServer", FakeServer)
    runpy.run_path(str(ROOT / "studio-ui" / "server.py"), run_name="__main__")
    assert seen["addr"] == ("0.0.0.0", 8190)
    assert seen["served"] is True


def test_film_board_links_watch_when_mp4_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dest = tmp_path / "films" / "gosee"
    dest.mkdir(parents=True)
    (dest / "state.json").write_text(
        json.dumps(
            {
                "slug": "gosee",
                "film": "go-see",
                "audio_policy": "world-only",
                "shots": [{"id": "01", "status": "ok"}],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "ez_gosee_90s.mp4").write_bytes(b"x")
    server = _load_server()
    monkeypatch.setattr(server, "FILMS", tmp_path / "films")
    monkeypatch.setattr(server, "GUIDES", tmp_path / "guides")
    html = server._page().decode("utf-8")
    assert "/watch/gosee" in html
    assert "/media/gosee?dl=1" in html


def _write_board(
    tmp_path: Path,
    *,
    film: str = "go-see",
    slug: str = "gosee",
    shots: list[object] | None = None,
) -> None:
    dest = tmp_path / "films" / slug
    dest.mkdir(parents=True)
    (dest / "state.json").write_text(
        json.dumps(
            {
                "slug": slug,
                "film": film,
                "audio_policy": "world-only",
                "shots": shots if shots is not None else [{"id": "01", "status": "ok"}],
            }
        ),
        encoding="utf-8",
    )


def test_rows_prefer_film_id_guide_pack(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_board(tmp_path)
    film_pack = tmp_path / "guides" / "go-see" / "01"
    legacy = tmp_path / "guides" / "gosee" / "01"
    film_pack.mkdir(parents=True)
    legacy.mkdir(parents=True)
    (film_pack / "first.png").write_bytes(b"clay-film")
    (legacy / "overlay.png").write_bytes(b"legacy-only")
    server = _load_server()
    monkeypatch.setattr(server, "FILMS", tmp_path / "films")
    monkeypatch.setattr(server, "GUIDES", tmp_path / "guides")
    assert server.guide_shot_id("go-see", "gosee", "01") == "go-see"
    row = server._rows()[0]
    assert row["slug"] == "gosee"
    shot = row["shots"][0]
    assert shot["clay"] == "on"
    assert shot["look"] == "off"
    assert "slug=go-see" in shot["thumb"]

    handler, captured = _bind_handler(server, "/thumb?slug=go-see&shot=01&kind=clay")
    server.Handler.do_GET(handler)
    assert captured["status"] == 200
    assert handler.wfile.getvalue() == b"clay-film"


def test_rows_fall_back_to_output_prefix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_board(tmp_path)
    legacy = tmp_path / "guides" / "gosee" / "01"
    legacy.mkdir(parents=True)
    (legacy / "first.png").write_bytes(b"legacy-clay")
    server = _load_server()
    monkeypatch.setattr(server, "FILMS", tmp_path / "films")
    monkeypatch.setattr(server, "GUIDES", tmp_path / "guides")
    assert server.guide_shot_id("go-see", "gosee", "01") == "gosee"
    assert server.guide_shot_id("go-see", "gosee", "02") == "go-see"
    assert server.guide_shot_id("switchyard", "switchyard", "01") == "switchyard"
    assert server.guide_shot_id("../x", "gosee", "01") == "gosee"
    assert server.guide_shot_id("../x", "../y", "01") == ""
    assert server.guide_shot_id("go-see", "gosee", "../01") == "go-see"
    shot = server._rows()[0]["shots"][0]
    assert shot["clay"] == "on"
    assert "slug=gosee" in shot["thumb"]


def test_rows_skip_non_dict_shot_and_refuse_bad_guide_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_board(tmp_path, shots=["nope", {"id": "01", "status": "ok"}])
    server = _load_server()
    monkeypatch.setattr(server, "FILMS", tmp_path / "films")
    monkeypatch.setattr(server, "GUIDES", tmp_path / "guides")
    row = server._rows()[0]
    assert row["total"] == "2"
    assert row["ok"] == "1"
    assert len(row["shots"]) == 1
    lights = server._shot_lights(tmp_path / "films" / "gosee", "../x", "01", {})
    assert lights["clay"] == "off"
    assert lights["thumb"] == ""
    lights = server._shot_lights(tmp_path / "films" / "gosee", "gosee", "ab", {"status": "ok"})
    assert lights["print"] == "on"
    assert lights["audio"] == "off"
    assert server._safe_thumb("go-see", "01", "clay") is None
    assert server._safe_thumb("go/see", "01", "clay") is None
    assert server._safe_thumb("go-see", "1a", "clay") is None


def _header_value(captured: dict[str, object], name: str) -> str:
    headers = captured["headers"]
    assert isinstance(headers, list)
    for key, value in headers:
        if key == name:
            assert isinstance(value, str)
            return value
    raise AssertionError(name)


def test_parse_byte_range_and_short_read() -> None:
    server = _load_server()
    assert server.parse_byte_range("bytes=2-5", 10) == (2, 5)
    assert server.parse_byte_range("bytes=8-", 10) == (8, 9)
    assert server.parse_byte_range("bytes=0-99", 10) == (0, 9)
    assert server.parse_byte_range("bytes=-3", 10) == (7, 9)
    assert server.parse_byte_range("bytes=-30", 10) == (0, 9)
    assert server.parse_byte_range("bytes=0-1,2-3", 10) is None
    assert server.parse_byte_range("nope", 10) is None
    assert server.parse_byte_range("bytes=", 10) is None
    assert server.parse_byte_range("bytes=abc", 10) is None
    assert server.parse_byte_range("bytes=1-x", 10) is None
    assert server.parse_byte_range("bytes=1a-2", 10) is None
    assert server.parse_byte_range("bytes=5-2", 10) is None
    assert server.parse_byte_range("bytes=10-10", 10) is None
    assert server.parse_byte_range("bytes=-0", 10) is None
    assert server.parse_byte_range("bytes=-x", 10) is None
    assert server.parse_byte_range("bytes=0-1", 0) is None
    src = io.BytesIO(b"0123456789")
    dest = io.BytesIO()
    server.write_file_span(src, dest, 2, 5, chunk=2)
    assert dest.getvalue() == b"23456"
    short = io.BytesIO(b"ab")
    out = io.BytesIO()
    server.write_file_span(short, out, 0, 10, chunk=4)
    assert out.getvalue() == b"ab"


def test_media_range_is_partial_and_download_ignores_range(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    films = tmp_path / "films" / "gosee"
    films.mkdir(parents=True)
    (films / "state.json").write_text("{}", encoding="utf-8")
    mp4 = tmp_path / "ez_gosee_90s.mp4"
    mp4.write_bytes(b"0123456789")
    server = _load_server()
    monkeypatch.setattr(server, "FILMS", tmp_path / "films")
    bare = server.Handler.__new__(server.Handler)
    assert bare._header("Range") == ""

    handler, captured = _bind_handler(server, "/media/gosee")
    handler.headers = {"Range": "bytes=2-5"}
    server.Handler.do_GET(handler)
    assert captured["status"] == 206
    assert handler.wfile.getvalue() == b"2345"
    assert _header_value(captured, "Content-Range") == "bytes 2-5/10"
    assert _header_value(captured, "Content-Length") == "4"
    assert _header_value(captured, "Accept-Ranges") == "bytes"

    handler, captured = _bind_handler(server, "/media/gosee")
    handler.headers = {"Range": "bytes=50-60"}
    server.Handler.do_GET(handler)
    assert captured["status"] == 416
    assert handler.wfile.getvalue() == b""
    assert _header_value(captured, "Content-Range") == "bytes */10"

    handler, captured = _bind_handler(server, "/media/gosee?dl=1")
    handler.headers = {"Range": "bytes=2-5"}
    server.Handler.do_GET(handler)
    assert captured["status"] == 200
    assert handler.wfile.getvalue() == b"0123456789"
    assert _header_value(captured, "Content-Disposition").startswith("attachment;")

    mp4.write_bytes(b"")
    handler, captured = _bind_handler(server, "/media/gosee")
    server.Handler.do_GET(handler)
    assert captured["status"] == 200
    assert handler.wfile.getvalue() == b""
    assert _header_value(captured, "Content-Length") == "0"

    handler, captured = _bind_handler(server, "/")
    server.Handler._send(handler, b"hi", "text/plain", [("X-Test", "1")])
    assert handler.wfile.getvalue() == b"hi"
    assert _header_value(captured, "X-Test") == "1"


# Canonical values from the ez-feedback contract (/tmp/ezfb-contract.md). Both
# studio-ui/server.py and custom_nodes/ez_feedback/context.py are pinned here
# so the two builders cannot drift apart.
_CANON_REPO = "toxicoder/ez-comfy-stack"
_CANON_LABELS = {"bug": "bug", "enhancement": "enhancement"}
_CANON_MAX_HREF = 5500
_CANON_HEADINGS = (
    "## What happened",
    "## Steps",
    "## Expected",
    "## Actual",
    "## Context",
    "## Environment",
    "## Recent errors",
    "## Browser",
)
_CANON_SURFACES = ("film-board", "watch")
_CANON_LEADS = ("Bug report from", "Feature request from")

_ISSUE_HREF = re.compile(r'<a href="(https://github\.com/[^"]+)"')


def _issue_hrefs(markup: str) -> list[str]:
    """Report hrefs in one page, in document order, still HTML-escaped.

    Args:
        markup: Rendered HTML.

    Returns:
        ``href`` attribute values of the GitHub report links.
    """
    return _ISSUE_HREF.findall(markup)


def _params(href: str) -> dict[str, list[str]]:
    """Query params of one report href.

    Args:
        href: ``href`` attribute value, HTML-unescaped.

    Returns:
        ``parse_qs`` mapping that keeps blank values.
    """
    return parse_qs(urlparse(href).query, keep_blank_values=True)


def _body(href: str) -> str:
    """Issue body of one report href.

    Args:
        href: ``href`` attribute value, HTML-unescaped.

    Returns:
        Markdown body.
    """
    return _params(href)["body"][0]


def _board(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[ModuleType, str]:
    """Render a board over one film with two shots and a guides pack.

    Args:
        tmp_path: pytest temp root.
        monkeypatch: pytest monkeypatch for the module path globals.

    Returns:
        ``(server module, board HTML)``.
    """
    _write_board(
        tmp_path,
        shots=[{"id": "01", "status": "ok"}, {"id": "02", "status": "pending"}],
    )
    pack = tmp_path / "guides" / "gosee" / "01"
    pack.mkdir(parents=True)
    (pack / "first.png").write_bytes(b"clay")
    pack2 = tmp_path / "guides" / "gosee" / "02"
    pack2.mkdir(parents=True)
    (pack2 / "overlay.png").write_bytes(b"ov")
    server = _load_server()
    monkeypatch.setattr(server, "FILMS", tmp_path / "films")
    monkeypatch.setattr(server, "GUIDES", tmp_path / "guides")
    return server, server._page().decode("utf-8")


def test_board_header_carries_report_links(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    server, page = _board(tmp_path, monkeypatch)
    header = page.split("<style>", 1)[0]
    assert 'href="https://github.com/toxicoder/ez-comfy-stack/issues/new?' in header
    assert 'target="_blank"' in header
    assert 'rel="noopener"' in header
    assert "Report a bug</a>" in header
    assert "Request a feature</a>" in header
    assert header.count("<svg") == 2 == header.count("</svg>")

    hrefs = [unescape(href) for href in _issue_hrefs(page)]
    assert _params(hrefs[0])["title"] == ["[film-board] Bug report from film-board"]
    assert _params(hrefs[1])["title"] == [
        "[film-board] Feature request from film-board"
    ]
    assert _params(hrefs[0])["labels"] == ["bug"]
    assert _params(hrefs[1])["labels"] == ["enhancement"]
    assert set(_params(hrefs[0])) == {"title", "body", "labels"}

    board_body = _body(hrefs[0])
    assert "- films: 1" in board_body
    assert "- prints: 1/2" in board_body
    assert "- audio_policy: world-only" in board_body
    assert "- route: /" in board_body
    assert server.SURFACE_BOARD == "film-board"


def test_board_film_and_shot_links_carry_their_own_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    server, page = _board(tmp_path, monkeypatch)
    hrefs = [unescape(href) for href in _issue_hrefs(page)]
    assert len(hrefs) == 6

    film_body = _body(hrefs[2])
    assert "- slug: gosee" in film_body
    assert "- film: go-see" in film_body
    assert "- prints: 1/2" in film_body
    assert _params(hrefs[2])["title"] == ["[film-board] Bug report from film-board"]
    assert _params(hrefs[3])["title"] == [
        "[film-board] Feature request from film-board"
    ]

    shot_bodies = [_body(href) for href in hrefs[4:]]
    assert "- shot: 01" in shot_bodies[0]
    assert "- thumb: clay" in shot_bodies[0]
    assert "- shot: 02" in shot_bodies[1]
    assert "- thumb: overlay" in shot_bodies[1]
    assert all("- slug: gosee" in body for body in shot_bodies)
    assert page.count('target="_blank"') == len(hrefs)
    assert page.count('rel="noopener"') == len(hrefs)


def test_watch_page_nav_carries_report_links(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_board(tmp_path)
    (tmp_path / "ez_gosee_90s.mp4").write_bytes(b"mp4")
    server = _load_server()
    monkeypatch.setattr(server, "FILMS", tmp_path)
    page = (server.watch_page("gosee") or b"").decode("utf-8")
    nav = page.split("<p>", 1)[1]
    assert '<a href="/">Board</a>' in nav
    assert "Report a bug</a>" in nav
    assert "Request a feature</a>" in nav
    assert nav.count("<svg") == 2 == nav.count("</svg>")
    assert 'target="_blank"' in nav
    assert 'rel="noopener"' in nav

    hrefs = [unescape(href) for href in _issue_hrefs(page)]
    assert len(hrefs) == 2
    assert _params(hrefs[0])["title"] == ["[watch] Bug report from watch"]
    assert _params(hrefs[1])["title"] == ["[watch] Feature request from watch"]
    assert _params(hrefs[0])["labels"] == ["bug"]
    assert _params(hrefs[1])["labels"] == ["enhancement"]
    body = _body(hrefs[0])
    assert "- slug: gosee" in body
    assert "- film: ez_gosee_90s.mp4" in body
    assert "- route: /watch/gosee" in body
    assert server.SURFACE_WATCH == "watch"
    assert "shot" not in body


def test_report_links_escape_every_interpolated_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    hostile = 'g"<>&se'
    _write_board(tmp_path, film='F<>&ilm', slug=hostile)
    server = _load_server()
    monkeypatch.setattr(server, "FILMS", tmp_path / "films")
    monkeypatch.setattr(server, "GUIDES", tmp_path / "guides")
    page = server._page().decode("utf-8")

    raw_hrefs = _issue_hrefs(page)
    assert len(raw_hrefs) == 5
    joined = " ".join(raw_hrefs)
    for attr in raw_hrefs:
        assert "<" not in attr
        assert '"' not in attr
        assert "&" not in attr.replace("&amp;", "")
    assert "%3C" in joined and "%3E" in joined and "%22" in joined and "%26" in joined
    assert "<script" not in page
    assert hostile not in page

    decoded = [_body(unescape(href)) for href in raw_hrefs]
    assert '- slug: g"<>&se' in decoded[2]
    assert "- film: F<>&ilm" in decoded[2]
    assert '- slug: g"<>&se' in decoded[4]

    master = tmp_path / 'ez_<bad>&"name.mp4'
    master.write_bytes(b"x")
    monkeypatch.setattr(server, "FILMS", tmp_path)
    monkeypatch.setattr(server, "PUBLISH_FILES", {hostile: master.name})
    watch_html = (server.watch_page(hostile) or b"").decode("utf-8")
    watch_hrefs = _issue_hrefs(watch_html)
    assert len(watch_hrefs) == 2
    for attr in watch_hrefs:
        assert "<" not in attr and '"' not in attr
        assert "&" not in attr.replace("&amp;", "")
        assert "%22" in attr and "%3C" in attr
    watch_body = _body(unescape(watch_hrefs[0]))
    assert '- slug: g"<>&se' in watch_body
    assert '- film: ez_<bad>&"name.mp4' in watch_body
    assert "- route: /watch/g" in watch_body


def test_report_href_uses_only_the_pinned_query_params() -> None:
    server = _load_server()
    href = server.issue_href("bug", "film-board", [("slug", "gosee")])
    assert href.startswith("https://github.com/toxicoder/ez-comfy-stack/issues/new?")
    assert list(_params(href)) == ["title", "body", "labels"]
    assert _params(href)["labels"] == ["bug"]
    assert server.labels_for("bug") == ["bug"]
    assert server.labels_for("enhancement") == ["enhancement"]
    assert server.labels_for("nope") == ["bug"]


def test_report_body_keeps_the_canonical_section_order() -> None:
    server = _load_server()
    bug = server.build_body(
        "bug", [("slug", "gosee")], [("python", "3.12.0")]
    )
    headings = [line for line in bug.splitlines() if line.startswith("## ")]
    assert headings == list(_CANON_HEADINGS[:6])
    assert bug.count("<!-- Replace this line. -->") == 4
    assert "- slug: gosee" in bug
    assert "- python: 3.12.0" in bug

    feature = server.build_body("enhancement", [("slug", "gosee")], [])
    assert [line for line in feature.splitlines() if line.startswith("## ")] == [
        "## Context"
    ]
    assert "## Environment" not in feature
    assert "<!-- Replace this line. -->" not in feature

    assert server.build_body("enhancement", [], []) == (
        "Feature request. Edit the blanks, then submit."
    )
    assert server.context_lines([("slug", ""), ("", "value")]) == []


def test_report_href_degrades_instead_of_exceeding_max_href(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = _load_server()
    context = [("slug", "gosee"), ("film", "go-see")]
    many = [(f"k{i}", "x" * 120) for i in range(80)]
    monkeypatch.setattr(server, "env_pairs", lambda: many)
    href = server.issue_href("bug", "film-board", context)
    assert len(href) <= server.MAX_HREF
    assert "## Environment" not in _body(href)
    assert "- slug: gosee" in _body(href)

    monkeypatch.setattr(server, "env_pairs", lambda: [])
    long_context = [(f"k{i}", "y" * 120) for i in range(60)]
    untrimmed = server.build_body("bug", long_context, [])
    assert len(untrimmed) > 4000
    monkeypatch.setattr(server, "MAX_HREF", 4000)
    clipped = server.issue_href("bug", "film-board", long_context)
    assert len(clipped) <= server.MAX_HREF
    first = next(
        row for row in _body(clipped).splitlines() if row.startswith("- k0: ")
    )
    assert len(first) == len("- k0: ") + 40
    assert "- k59: " in _body(clipped)

    monkeypatch.setattr(server, "MAX_HREF", 1)
    bare = server.issue_href("enhancement", "watch", [("film", "go-see")])
    assert bare.startswith(server.ISSUES_NEW + "?")
    assert _params(bare)["title"] == ["[watch] Feature request from watch"]
    assert _params(bare)["labels"] == ["enhancement"]
    assert _params(bare)["body"] == ["Feature request. Edit the blanks, then submit."]


def test_report_helpers_clip_redact_and_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    server = _load_server()
    assert server.clip("  a\n b\tc ", 20) == "a b c"
    assert server.clip("", 20) == ""
    assert server.clip("abcdef", 10) == "abcdef"
    assert server.clip("abcdefghij", 8) == "abcde..."
    assert server.clip("abcdef", 3) == "abc"
    assert server.clip("abcdef", 0) == ""
    assert server.title_for("bug", "watch").startswith("[watch] Bug report from")
    assert len(server.title_for("bug", "x" * 400)) <= 140

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    text = f"log {tmp_path}/films and ghp_abcdefghijklmnopqrstuvwxyz plus hf_123456"
    redacted = server.redact(text)
    assert "~" in redacted and str(tmp_path) not in redacted
    assert "[redacted]" in redacted and "ghp_" not in redacted
    assert "github_pat_" not in server.redact("github_pat_abcdefghijklmnopqrstuvwxyz")
    assert "gho_" not in server.redact("gho_abcdefghij")
    assert server.redact("") == ""

    assert server._count("7") == 7
    assert server._count("x") == 0
    assert server._count(None) == 0
    rows: list[Any] = [
        {"slug": "a", "film": "A", "ok": "x", "total": "2", "audio_policy": "silent"},
        {"slug": "b", "film": "B", "ok": "1", "total": "3", "audio_policy": "silent"},
    ]
    assert server._board_context(rows) == [
        ("films", "2"),
        ("prints", "1/5"),
        ("audio_policy", "silent"),
        ("route", "/"),
    ]
    assert server._shot_context("gosee", "01", "") == [
        ("slug", "gosee"),
        ("shot", "01"),
        ("thumb", "clay"),
    ]
    assert server._watch_context("gosee", Path("/out/ez_gosee_90s.mp4")) == [
        ("slug", "gosee"),
        ("film", "ez_gosee_90s.mp4"),
        ("route", "/watch/gosee"),
    ]
    env = dict(server.env_pairs())
    assert {"python", "platform", "output_dir"} <= set(env)


def test_report_link_markup_and_defaults() -> None:
    server = _load_server()
    markup = server.report_link("bug", "film-board", [("slug", "gosee")])
    assert markup.startswith('<a href="https://github.com/')
    assert '" target="_blank" rel="noopener">' in markup
    assert markup.endswith("Report a bug</a>")
    assert server.GITHUB_ICON in markup
    assert server.report_link("nope", "watch", []).startswith('<a href="https://')
    assert server.report_link("nope", "watch", []).endswith("Report a bug</a>")
    assert server.report_link("enhancement", "watch", []).endswith(
        "Request a feature</a>"
    )


def test_report_links_render_the_github_mark_as_static_markup() -> None:
    """Each anchor opens with the octicon mark, then the escaped label."""
    server = _load_server()
    icon = server.GITHUB_ICON
    assert icon.startswith('<svg viewBox="0 0 16 16" width="14" height="14"')
    assert 'aria-hidden="true"' in icon
    assert 'fill="currentColor"' in icon
    assert icon.startswith("<svg") and icon.endswith("</svg>")
    mark = re.search(r'<path d="([^"]+)"', icon)
    assert mark is not None
    assert mark.group(1).startswith("M6.766 11.328c-2.063")
    assert mark.group(1).endswith("5.47-.5.657-.656")

    markup = server.report_link("enhancement", "watch", [])
    anchor, _, label = markup.partition('" target="_blank" rel="noopener">')
    assert anchor.startswith('<a href="https://github.com/')
    assert label == icon + "Request a feature</a>"
    assert "<svg" in markup and "&lt;svg" not in markup


def test_report_builder_matches_the_pinned_contract() -> None:
    server = _load_server()
    assert server.REPO == _CANON_REPO
    assert server.ISSUES_NEW == f"https://github.com/{_CANON_REPO}/issues/new"
    assert server.MAX_HREF == _CANON_MAX_HREF
    assert server.LABELS == dict(_CANON_LABELS)
    assert server.LINK_TEXT == {
        "bug": "Report a bug",
        "enhancement": "Request a feature",
    }
    assert server.BODY_HEADINGS == _CANON_HEADINGS
    assert server.FILL_HEADINGS == _CANON_HEADINGS[:4]
    assert server.SURFACE_BOARD == _CANON_SURFACES[0]
    assert server.SURFACE_WATCH == _CANON_SURFACES[1]
    assert server.BLANK == "<!-- Replace this line. -->"
    for surface in _CANON_SURFACES:
        for kind, lead in zip(("bug", "enhancement"), _CANON_LEADS):
            assert server.title_for(kind, surface) == f"[{surface}] {lead} {surface}"
            assert server.labels_for(kind) == [_CANON_LABELS[kind]]


def _literal(tree: ast.Module, name: str) -> object:
    """Module-level literal bound to one name.

    Args:
        tree: Parsed module.
        name: Constant name.

    Returns:
        The literal value, or ``None`` when the name is not a literal.
    """
    for node in tree.body:
        value: ast.expr | None = None
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id == name:
                value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name and node.value is not None:
                value = node.value
        if value is not None:
            try:
                return ast.literal_eval(value)
            except ValueError:
                return None
    return None


def _headings_in(text: str) -> list[str]:
    """Body headings in first-appearance order.

    Args:
        text: Source text of one report builder.

    Returns:
        Every ``## `` heading literal found in the file.
    """
    found: list[str] = []
    for match in re.findall(r'"(## [^"]+)"', text):
        if match not in found:
            found.append(match)
    return found


def test_report_builder_matches_context_py_constants() -> None:
    source = ROOT / "custom_nodes" / "ez_feedback" / "context.py"
    if not source.is_file():
        pytest.skip("custom_nodes/ez_feedback/context.py is not in this worktree yet")
    text = source.read_text(encoding="utf-8")
    tree = ast.parse(text)
    server = _load_server()

    assert _literal(tree, "REPO") == _CANON_REPO == server.REPO
    assert _literal(tree, "LABELS") == _CANON_LABELS == server.LABELS
    assert _literal(tree, "MAX_HREF") == _CANON_MAX_HREF == server.MAX_HREF
    enhance_headings = _literal(tree, "ENHANCE_HEADINGS")
    assert isinstance(enhance_headings, tuple), "context.py lost ENHANCE_HEADINGS"
    assert list(enhance_headings) == [
        "## Problem",
        "## Proposed solution",
        "## Alternatives",
        "## What it unlocks",
    ]
    # The enhancement headings extend feature-request bodies only; the bug body
    # order pinned against the studio-ui builder must stay the canonical eight.
    body_headings = [h for h in _headings_in(text) if h not in set(enhance_headings)]
    assert body_headings == list(_CANON_HEADINGS) == list(server.BODY_HEADINGS)
    for lead in _CANON_LEADS:
        assert f'"{lead}' in text or f"'{lead}" in text or f"{lead} " in text
    for surface in _CANON_SURFACES:
        assert surface in text
