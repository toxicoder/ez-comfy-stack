#!/usr/bin/env python3
"""Tiny jobstore board. Stdlib only. No GPU. Empty films dir is a page, not a crash."""

from __future__ import annotations

import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

FILMS = Path("/films/films")
if not FILMS.is_dir():
    FILMS = Path("/films")


def _rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if not FILMS.is_dir():
        return rows
    for state in sorted(FILMS.glob("*/state.json")):
        try:
            data = json.loads(state.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        shots = data.get("shots") or []
        ok = sum(1 for s in shots if s.get("status") == "ok")
        rows.append(
            {
                "slug": str(data.get("slug") or state.parent.name),
                "film": str(data.get("film") or ""),
                "ok": str(ok),
                "total": str(len(shots)),
            }
        )
    return rows


def _page() -> bytes:
    rows = _rows()
    body = ["<h1>ez-comfy film board</h1>", "<p>Jobstore lights only. No GPU.</p>"]
    if not rows:
        body.append(
            "<p>No films yet. Run <code>./scripts/utilities/compile-film.sh go-see</code> "
            "then <code>print-shot</code>.</p>"
        )
    else:
        body.append("<table><tr><th>film</th><th>slug</th><th>ok</th></tr>")
        for row in rows:
            body.append(
                "<tr><td>{}</td><td>{}</td><td>{}/{}</td></tr>".format(
                    html.escape(row["film"]),
                    html.escape(row["slug"]),
                    html.escape(row["ok"]),
                    html.escape(row["total"]),
                )
            )
        body.append("</table>")
    doc = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>ez-comfy studio-ui</title></head><body>"
        + "".join(body)
        + "</body></html>"
    )
    return doc.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        payload = _page()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt: str, *args: object) -> None:
        return


def main() -> None:
    httpd = ThreadingHTTPServer(("0.0.0.0", 8190), Handler)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
