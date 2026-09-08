"""Hermetic tests for studio-ui watch/download (no network listen)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load_server():
    spec = importlib.util.spec_from_file_location(
        "studio_ui_server", ROOT / "studio-ui" / "server.py"
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_watch_and_download_allowlist(tmp_path: Path, monkeypatch) -> None:
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


def test_film_board_links_watch_when_mp4_exists(
    tmp_path: Path, monkeypatch
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
