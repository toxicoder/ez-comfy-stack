"""Hermetic tests for studio-ui watch/download (no network listen)."""

from __future__ import annotations
import pytest

import importlib.util
import io
import json
from pathlib import Path
from types import ModuleType
from typing import Any

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
