#!/usr/bin/env python3
"""Tiny jobstore board. Stdlib only. No GPU. Empty films dir is a page, not a crash."""

from __future__ import annotations

import html
import io
import json
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, BinaryIO, TypedDict
from urllib.parse import parse_qs, urlparse

# Film ids and output prefixes used as a single path segment under guides/.
_GUIDE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*\Z")

# Jobstore films directory (``/films/films`` when present, else ``/films``).
FILMS = Path("/films/films")
if not FILMS.is_dir():
    FILMS = Path("/films")
# Guide packs live beside films, or under ``/films/guides``.
GUIDES = FILMS.parent / "guides"
if not GUIDES.is_dir():
    alt = Path("/films/guides")
    if alt.is_dir():
        GUIDES = alt

class FilmRow(TypedDict):
    """One film's board row from jobstore ``state.json``.

    Attributes:
        slug: Jobstore directory name / film id.
        film: Display title from state.
        ok: Count of shots with status ``ok`` (decimal string).
        total: Shot count (decimal string).
        audio_policy: Mix policy, default ``world-only``.
        shots: Per-shot light dicts (id, clay, look, overlay, print, audio, thumb).
    """

    slug: str
    film: str
    ok: str
    total: str
    audio_policy: str
    shots: list[dict[str, str]]


# Allowlisted 90s masters under the Comfy output root (slug -> filename).
PUBLISH_FILES = {
    "gosee": "ez_gosee_90s.mp4",
    "stillhere": "ez_stillhere_90s.mp4",
    "switchyard": "ez_switchyard_90s.mp4",
    "tidetable": "ez_tidetable_450s.mp4",
    "nightoven": "ez_nightoven_450s.mp4",
    "glasshouse": "ez_glasshouse_450s.mp4",
    "lastlane": "ez_lastlane_450s.mp4",
    "breakwater": "ez_breakwater_450s.mp4",
}


def output_root() -> Path:
    """Comfy output dir: parent of jobstore ``films/`` when that layout exists.

    Returns:
        Directory that contains allowlisted ``ez_*_90s.mp4`` masters.
    """
    if FILMS.name == "films":
        parent = FILMS.parent
        if parent.is_dir():
            return parent
    return FILMS


def publish_mp4(slug: str) -> Path | None:
    """Allowlisted 90s master under the output root, or None.

    Args:
        slug: Film slug (must be a key in ``PUBLISH_FILES``).

    Returns:
        Path to the MP4 when it exists under the output root, else ``None``.
    """
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


def _guide_id(value: str) -> str | None:
    """Return a single safe guides directory name, or None.

    Accepts a film id (``go-see``) or an output prefix (``gosee``).
    Rejects empty strings, slashes, and ``..``.

    Args:
        value: Candidate directory name.

    Returns:
        The name when it is one safe segment, else ``None``.
    """
    text = str(value or "")
    if _GUIDE_ID.fullmatch(text):
        return text
    return None


def guide_shot_id(film: str, slug: str, shot: str) -> str:
    """Choose the guides directory name for one shot.

    ``guides/<film-id>/<shot>`` wins when that directory exists. Otherwise
    ``guides/<prefix>/<shot>`` is used when it exists. When neither exists,
    the film id is returned so a later dump matches ``blender-guide``.

    Args:
        film: Film id from ``state.json`` (``go-see``).
        slug: Output prefix (``gosee``).
        shot: Shot directory name.

    Returns:
        A safe directory name, or ``""`` when neither name is safe.
    """
    film_id = _guide_id(film)
    slug_id = _guide_id(slug)
    if film_id is not None and shot.isdigit() and (GUIDES / film_id / shot).is_dir():
        return film_id
    if (
        slug_id is not None
        and slug_id != film_id
        and shot.isdigit()
        and (GUIDES / slug_id / shot).is_dir()
    ):
        return slug_id
    if film_id is not None:
        return film_id
    return slug_id or ""


def _light(on: bool) -> str:
    """CSS class for a board light.

    Args:
        on: Whether the artifact exists / shot is ok.

    Returns:
        ``on`` or ``off``.
    """
    return "on" if on else "off"


def _shot_lights(
    dest: Path, slug: str, sid: str, row: dict[str, Any]
) -> dict[str, str]:
    """Build one shot's clay/look/overlay/print/audio lights and thumb URL.

    Args:
        dest: Film jobstore directory (contains ``stems/``).
        slug: Resolved guide directory name (film id or output prefix).
        sid: Shot id (directory name under the guide pack).
        row: Shot object from ``state.json``.

    Returns:
        Light dict consumed by :func:`_page`.
    """
    guide = _guide_id(slug)
    pack = GUIDES / guide / sid if guide is not None and sid.isdigit() else None
    stems = dest / "stems" / sid if sid.isdigit() else None
    clay = False
    look = False
    overlay = False
    thumb = ""
    if pack is not None:
        clay = (pack / "first.png").is_file() or (pack / "clay.mp4").is_file()
        look = (pack / "overlay.png").is_file()
        overlay = (pack / "score.json").is_file()
        if (pack / "first.png").is_file():
            thumb = f"/thumb?slug={html.escape(guide or '')}&shot={html.escape(sid)}&kind=clay"
        elif (pack / "overlay.png").is_file():
            thumb = f"/thumb?slug={html.escape(guide or '')}&shot={html.escape(sid)}&kind=overlay"
    printed = str(row.get("status") or "") == "ok"
    mixed = False
    if stems is not None:
        mixed = any(
            (stems / name).is_file() for name in ("mix.mp4", "mix.m4a", "mix.wav")
        )
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
    """Load board rows from each ``*/state.json`` under ``FILMS``.

    Returns:
        Sorted film rows (empty when the films dir is missing).
    """
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
        film = str(data.get("film") or "")
        shots = data.get("shots") or []
        ok = sum(1 for s in shots if isinstance(s, dict) and s.get("status") == "ok")
        lights = []
        for index, shot in enumerate(shots, start=1):
            if not isinstance(shot, dict):
                continue
            sid = str(shot.get("id") or f"{index:02d}")
            guide = guide_shot_id(film, slug, sid)
            lights.append(_shot_lights(dest, guide, sid, shot))
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
    """Render the jobstore board HTML.

    Returns:
        UTF-8 HTML document bytes.
    """
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
                    ' - <a href="/watch/{0}">Watch 90s film</a>'
                    ' - <a href="/media/{0}?dl=1">Download MP4</a>'
                ).format(html.escape(slug))
            body.append(
                "<p>prints {}/{} - audio_policy {}{}</p>".format(
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
    """HTML5 player for an allowlisted 90s master.

    Args:
        slug: Film slug (must resolve via :func:`publish_mp4`).

    Returns:
        Player HTML bytes, or ``None`` when the master is missing.
    """
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
        ' - <a href="/">Board</a></p>'
        "</main></body></html>"
    ).encode("utf-8")


def _safe_thumb(slug: str, shot: str, kind: str) -> Path | None:
    """Resolve a clay/overlay PNG under ``GUIDES``, or ``None``.

    Args:
        slug: Film id (``go-see``) or output prefix (``gosee``).
        shot: Digit-only shot id.
        kind: ``clay`` (``first.png``) or ``overlay``.

    Returns:
        File path when it exists under ``GUIDES``, else ``None``.
    """
    if _guide_id(slug) is None or not shot.isdigit() or kind not in {"clay", "overlay"}:
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


def parse_byte_range(header: str, size: int) -> tuple[int, int] | None:
    """Parse one ``bytes=`` range into an inclusive span.

    Accepts ``START-END``, open ``START-``, and a suffix ``-N``. A comma
    means more than one range, which this board does not serve.

    Args:
        header: Raw ``Range`` header value.
        size: File size in bytes.

    Returns:
        ``(start, end)`` inclusive, or ``None`` when the range cannot be
        satisfied.
    """
    text = header.strip()
    if not text.lower().startswith("bytes="):
        return None
    spec = text[6:].strip()
    if not spec or "," in spec or size < 1:
        return None
    if spec.startswith("-"):
        try:
            tail = int(spec[1:])
        except ValueError:
            return None
        if tail < 1:
            return None
        start = size - tail
        if start < 0:
            start = 0
        return start, size - 1
    if "-" not in spec:
        return None
    start_text, end_text = spec.split("-", 1)
    try:
        start = int(start_text)
    except ValueError:
        return None
    if start >= size:
        return None
    if end_text == "":
        return start, size - 1
    try:
        end = int(end_text)
    except ValueError:
        return None
    if end < start:
        return None
    if end >= size:
        end = size - 1
    return start, end


def write_file_span(
    src: BinaryIO,
    dest: io.BufferedIOBase,
    start: int,
    length: int,
    *,
    chunk: int = 65536,
) -> None:
    """Copy ``length`` bytes from ``src`` at ``start`` into ``dest``.

    Args:
        src: Opened binary file.
        dest: Socket or buffer (``BaseHTTPRequestHandler.wfile``).
        start: First byte offset.
        length: Number of bytes to copy.
        chunk: Read size. Kept small so a 512m studio-ui process does not
            hold the master.
    """
    src.seek(start)
    remaining = length
    while remaining > 0:
        data = src.read(min(chunk, remaining))
        if not data:
            break
        dest.write(data)
        remaining -= len(data)


class Handler(BaseHTTPRequestHandler):
    """Stdlib HTTP handler for the board, thumbs, and allowlisted MP4s."""

    def _send(
        self,
        payload: bytes,
        content_type: str,
        extra_headers: list[tuple[str, str]] | None = None,
    ) -> None:
        """Write a 200 response.

        Args:
            payload: Body bytes.
            content_type: ``Content-Type`` value.
            extra_headers: Optional extra header pairs.
        """
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        for name, value in extra_headers or []:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(payload)

    def _send_404(self) -> None:
        """Write an empty 404."""
        self.send_response(404)
        self.end_headers()

    def _serve_watch(self, slug: str) -> None:
        """Serve the watch HTML for a published master.

        Args:
            slug: Film slug.
        """
        if publish_mp4(slug) is None:
            self._send_404()
            return
        self._send(watch_page(slug) or b"", "text/html; charset=utf-8")

    def _header(self, name: str) -> str:
        """Read one request header.

        Args:
            name: Header name.

        Returns:
            The value, or ``""`` when the test double has no headers.
        """
        headers = getattr(self, "headers", None)
        if headers is None:
            return ""
        return str(headers.get(name) or "")

    def _stream_file(
        self,
        path: Path,
        content_type: str,
        *,
        download_name: str | None,
        honor_range: bool,
    ) -> None:
        """Stream a file in chunks, honoring one byte range.

        Args:
            path: File that exists.
            content_type: ``Content-Type`` value.
            download_name: Attachment filename. When set, ``Range`` is ignored
                so the download is the whole file.
            honor_range: When True, a ``Range`` header selects a slice.
        """
        size = path.stat().st_size
        start = 0
        end = size - 1 if size else 0
        status = 200
        if honor_range:
            requested = self._header("Range")
            if requested:
                span = parse_byte_range(requested, size)
                if span is None:
                    self.send_response(416)
                    self.send_header("Content-Range", f"bytes */{size}")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                start, end = span
                status = 206
        length = 0 if status == 200 and size == 0 else end - start + 1
        self.send_response(status)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        if status == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        if download_name:
            self.send_header(
                "Content-Disposition", f'attachment; filename="{download_name}"'
            )
        self.end_headers()
        if length == 0:
            return
        with path.open("rb") as src:
            write_file_span(src, self.wfile, start, length)

    def _serve_media(self, slug: str, query: dict[str, list[str]]) -> None:
        """Serve the published MP4, optionally as a download.

        Args:
            slug: Film slug.
            query: Parsed query string.
        """
        path = publish_mp4(slug)
        if path is None:
            self._send_404()
            return
        download = (query.get("dl") or [""])[0] == "1"
        name = path.name if download else None
        self._stream_file(
            path,
            "video/mp4",
            download_name=name,
            honor_range=not download,
        )

    def _serve_thumb(self, query: dict[str, list[str]]) -> None:
        """Serve an allowlisted clay/look PNG.

        Args:
            query: Parsed query string (``slug`` / ``shot`` / ``kind``).
        """
        slug = (query.get("slug") or [""])[0]
        shot = (query.get("shot") or [""])[0]
        kind = (query.get("kind") or ["clay"])[0]
        path = _safe_thumb(slug, shot, kind)
        if path is None:
            self._send_404()
            return
        self._stream_file(path, "image/png", download_name=None, honor_range=True)

    def _serve_board(self) -> None:
        """Serve the film board HTML."""
        self._send(_page(), "text/html; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        """Serve board HTML, ``/watch``, ``/media``, or ``/thumb``.

        Returns:
            None
        """
        parsed = urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) == 2 and parts[0] in {"watch", "media"}:
            slug = parts[1]
            if parts[0] == "watch":
                self._serve_watch(slug)
                return
            self._serve_media(slug, parse_qs(parsed.query))
            return
        if parsed.path == "/thumb":
            self._serve_thumb(parse_qs(parsed.query))
            return
        self._serve_board()

    def log_message(self, format: str, *args: Any) -> None:
        """Swallow request logs (board is a sidecar, not an access log).

        Args:
            format: Unused printf-style log format from ``BaseHTTPRequestHandler``.
            *args: Unused format arguments.
        """
        return


def main() -> None:
    """Listen on ``0.0.0.0:8190`` until killed."""
    print("[ez-comfy] studio-ui http://0.0.0.0:8190", file=sys.stderr, flush=True)
    httpd = ThreadingHTTPServer(("0.0.0.0", 8190), Handler)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
