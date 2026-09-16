"""Hermetic tests for studio-ui watch/download (no network listen)."""

from __future__ import annotations
import pytest

import importlib.util
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
    import ez_studio_app
    import ez_studio_blocks

    assert ez_studio_app.NODE_CLASS_MAPPINGS == {}
    assert ez_studio_app.WEB_DIRECTORY == "./js"
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
