#!/usr/bin/env python3
"""Tiny jobstore board. Stdlib only. No GPU. Empty films dir is a page, not a crash."""

from __future__ import annotations

import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, TypedDict
from urllib.parse import parse_qs, urlparse

FILMS = Path("/films/films")
if not FILMS.is_dir():
    FILMS = Path("/films")
GUIDES = FILMS.parent / "guides"
if not GUIDES.is_dir():
    alt = Path("/films/guides")
    if alt.is_dir():
        GUIDES = alt

class FilmRow(TypedDict):
    slug: str
    film: str
    ok: str
    total: str
    audio_policy: str
    shots: list[dict[str, str]]


PUBLISH_FILES = {
    "gosee": "ez_gosee_90s.mp4",
    "stillhere": "ez_stillhere_90s.mp4",
    "switchyard": "ez_switchyard_90s.mp4",
}


def output_root() -> Path:
    """Comfy output dir: parent of jobstore ``films/`` when that layout exists."""
    if FILMS.name == "films":
        parent = FILMS.parent
        if parent.is_dir():
            return parent
    return FILMS


def publish_mp4(slug: str) -> Path | None:
    """Allowlisted 90s master under the output root, or None."""
    name = PUBLISH_FILES.get(slug)
    if not name:
        return None
    root = output_root()
    path = root / name
    try:
        path.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    if path.is_file():
        return path
    return None


def _light(on: bool) -> str:
    return "on" if on else "off"


def _shot_lights(dest: Path, slug: str, sid: str, row: dict) -> dict[str, str]:
    pack = GUIDES / slug / sid
    stems = dest / "stems" / sid
    clay = (pack / "first.png").is_file() or (pack / "clay.mp4").is_file()
    look = (pack / "overlay.png").is_file()
    overlay = (pack / "score.json").is_file()
    printed = str(row.get("status") or "") == "ok"
    mixed = any((stems / name).is_file() for name in ("mix.mp4", "mix.m4a", "mix.wav"))
    thumb = ""
    if (pack / "first.png").is_file():
        thumb = f"/thumb?slug={html.escape(slug)}&shot={html.escape(sid)}&kind=clay"
    elif (pack / "overlay.png").is_file():
        thumb = f"/thumb?slug={html.escape(slug)}&shot={html.escape(sid)}&kind=overlay"
    return {
        "id": sid,
        "clay": _light(clay),
        "look": _light(look),
        "overlay": _light(overlay),
        "print": _light(printed),
        "audio": _light(mixed),
        "thumb": thumb,
    }


def _rows() -> list[FilmRow]:
    rows: list[FilmRow] = []
    if not FILMS.is_dir():
        return rows
    for state in sorted(FILMS.glob("*/state.json")):
        try:
            data = json.loads(state.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        dest = state.parent
        slug = str(data.get("slug") or dest.name)
        shots = data.get("shots") or []
        ok = sum(1 for s in shots if s.get("status") == "ok")
        lights = [
            _shot_lights(dest, slug, str(s.get("id") or f"{i:02d}"), s)
            for i, s in enumerate(shots, start=1)
        ]
        rows.append(
            {
                "slug": slug,
                "film": str(data.get("film") or ""),
                "ok": str(ok),
                "total": str(len(shots)),
                "audio_policy": str(data.get("audio_policy") or "world-only"),
                "shots": lights,
            }
        )
    return rows


def _page() -> bytes:
    rows = _rows()
    body = [
        "<h1>ez-comfy film board</h1>",
        "<p>Jobstore lights only. No GPU. Clay / look / overlay / print / audio.</p>",
        "<style>body{font:14px/1.4 ui-sans-serif,system-ui,sans-serif}"
        "table{border-collapse:collapse}td,th{padding:6px 8px;vertical-align:top}"
        ".on{color:#0a0}.off{color:#999}.strip img{width:64px;height:auto;"
        "background:#111} .shot{display:inline-block;margin:0 8px 8px 0;"
        "text-align:center;font-size:11px}</style>",
    ]
    if not rows:
        body.append(
            "<p>No films yet. Run <code>./scripts/utilities/compile-film.sh go-see</code> "
            "then <code>print-shot</code>.</p>"
        )
    else:
        for row in rows:
            body.append("<h2>{} / {}</h2>".format(
                html.escape(str(row["film"])), html.escape(str(row["slug"]))
            ))
            watch = ""
            slug = str(row["slug"])
            if publish_mp4(slug) is not None:
                watch = (
                    ' · <a href="/watch/{0}">Watch 90s film</a>'
                    ' · <a href="/media/{0}?dl=1">Download MP4</a>'
                ).format(html.escape(slug))
            body.append(
                "<p>prints {}/{} · audio_policy {}{}</p>".format(
                    html.escape(str(row["ok"])),
                    html.escape(str(row["total"])),
                    html.escape(str(row["audio_policy"])),
                    watch,
                )
            )
            body.append('<div class="strip">')
            for shot in row["shots"]:
                if not isinstance(shot, dict):
                    continue
                img = ""
                thumb = str(shot.get("thumb") or "")
                if thumb:
                    img = f'<img src="{thumb}" alt="" width="64">'
                body.append(
                    '<div class="shot">{}{}<br>'
                    '<span class="{}">clay</span> '
                    '<span class="{}">look</span> '
                    '<span class="{}">ov</span> '
                    '<span class="{}">print</span> '
                    '<span class="{}">audio</span></div>'.format(
                        img,
                        html.escape(str(shot.get("id") or "")),
                        shot.get("clay") or "off",
                        shot.get("look") or "off",
                        shot.get("overlay") or "off",
                        shot.get("print") or "off",
                        shot.get("audio") or "off",
                    )
                )
            body.append("</div>")
    doc = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>ez-comfy studio-ui</title></head><body>"
        + "".join(body)
        + "</body></html>"
    )
    return doc.encode("utf-8")


def watch_page(slug: str) -> bytes | None:
    """HTML5 player for an allowlisted 90s master."""
    path = publish_mp4(slug)
    if path is None:
        return None
    name = html.escape(path.name)
    safe = html.escape(slug)
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{name}</title>"
        "<style>body{margin:0;background:#111;color:#eee;"
        "font:16px/1.4 ui-sans-serif,system-ui,sans-serif}"
        "main{max-width:1280px;margin:0 auto;padding:16px}"
        "video{width:100%;height:auto;background:#000}"
        "a{color:#8cf}</style></head><body><main>"
        f"<h1>{name}</h1>"
        f'<video controls playsinline src="/media/{safe}"></video>'
        f'<p><a href="/media/{safe}?dl=1">Download MP4</a>'
        ' · <a href="/">Board</a></p>'
        "</main></body></html>"
    ).encode("utf-8")


def _safe_thumb(slug: str, shot: str, kind: str) -> Path | None:
    if not slug.isalnum() or not shot.isdigit() or kind not in {"clay", "overlay"}:
        return None
    pack = GUIDES / slug / shot
    if kind == "clay":
        path = pack / "first.png"
    else:
        path = pack / "overlay.png"
    try:
        path.resolve().relative_to(GUIDES.resolve())
    except (OSError, ValueError):
        return None
    if path.is_file():
        return path
    return None


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) == 2 and parts[0] in {"watch", "media"}:
            slug = parts[1]
            path = publish_mp4(slug)
            if path is None:
                self.send_response(404)
                self.end_headers()
                return
            if parts[0] == "watch":
                payload = watch_page(slug) or b""
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            payload = path.read_bytes()
            query = parse_qs(parsed.query)
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(len(payload)))
            if (query.get("dl") or [""])[0] == "1":
                self.send_header(
                    "Content-Disposition",
                    f'attachment; filename="{path.name}"',
                )
            self.end_headers()
            self.wfile.write(payload)
            return
        if parsed.path == "/thumb":
            query = parse_qs(parsed.query)
            slug = (query.get("slug") or [""])[0]
            shot = (query.get("shot") or [""])[0]
            kind = (query.get("kind") or ["clay"])[0]
            path = _safe_thumb(slug, shot, kind)
            if path is None:
                self.send_response(404)
                self.end_headers()
                return
            payload = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        payload = _page()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: Any) -> None:
        return


def main() -> None:
    httpd = ThreadingHTTPServer(("0.0.0.0", 8190), Handler)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
