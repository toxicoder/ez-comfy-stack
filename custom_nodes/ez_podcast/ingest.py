"""Parse a lazy study paste into source records (pages, captions, files).

Hermetic: stdlib. Tests inject ``page_fetch_hook`` and ``caption_fetch_hook``.
HTTPS page fetch reuses ez_research SSRF gates. Video URLs pull captions
only (no media download, no dub ASR).
"""

from __future__ import annotations

import html as html_module
import re
import sys
import tempfile
from pathlib import Path
from typing import Callable, Protocol, TypedDict
from urllib.parse import urlparse

# Paste caps, URL/file matchers, HTML strip, video hosts, and caption langs.
MAX_URLS = 8
MAX_PASTE_CHARS = 48000
MAX_SOURCE_CHARS = 8000
MAX_TOTAL_SOURCE_CHARS = 32000
URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")
_VTT_TS_RE = re.compile(
    r"^\d{1,2}:\d{2}(?::\d{2})?[.,]\d{3}\s+-->\s+\d{1,2}:\d{2}"
)
TEXT_SUFFIXES = (".txt", ".md", ".srt", ".vtt")
VIDEO_SUFFIXES = (".mp4", ".mkv", ".webm", ".mov")
VIDEO_HOSTS = frozenset(
    {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtu.be",
        "vimeo.com",
        "www.vimeo.com",
        "player.vimeo.com",
    }
)
USER_AGENT = "ez-comfy-podcast-learn/1.0"

page_fetch_hook: Callable[[str], str] | None = None
caption_fetch_hook: Callable[[str], str] | None = None


class CaptionFetcher(Protocol):
    """Test/production caption fetch (yt-dlp subs, no media)."""

    def __call__(self, url: str, /) -> str:
        """Return caption text for ``url``.

        Args:
            url: Video HTTPS URL.

        Returns:
            Plain caption text, or empty when captions are missing.
        """
        ...


class PageFetcher(Protocol):
    """Test/production HTTPS page fetch (SSRF-gated in production)."""

    def __call__(self, url: str, /) -> str:
        """Return page text for ``url``.

        Args:
            url: Absolute HTTPS URL.

        Returns:
            Plain text, or empty on block/error.
        """
        ...


class SourceRecord(TypedDict):
    """One ingested source after parse/fetch."""

    kind: str
    title: str
    url: str
    text: str
    status: str


def _log(message: str) -> None:
    """Write a pack status line to stderr.

    Args:
        message: Text after the ``[ez_podcast]`` prefix.
    """
    print(f"[ez_podcast] {message}", file=sys.stderr)


def _ensure_lab_custom_nodes_path() -> None:
    """Make sibling ez_* packs importable under ComfyUI 0.34+ load_custom_node."""
    root = str(Path(__file__).resolve().parent.parent)
    if root not in sys.path:
        sys.path.insert(0, root)


def _as_bool(value: object) -> bool:
    """Coerce a Comfy widget value to bool.

    Args:
        value: BOOLEAN widget or loose truthy token.

    Returns:
        Parsed boolean.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def strip_html(blob: str) -> str:
    """Remove tags and collapse whitespace.

    Args:
        blob: HTML or plain text.

    Returns:
        Plain text.
    """
    text = _TAG_RE.sub(" ", blob or "")
    text = html_module.unescape(text)
    return _SPACE_RE.sub(" ", text).strip()


def truncate_text(text: str, limit: int = MAX_SOURCE_CHARS) -> str:
    """Trim ``text`` to ``limit`` characters.

    Args:
        text: Source body.
        limit: Max characters.

    Returns:
        Original or truncated string.
    """
    body = text if isinstance(text, str) else str(text or "")
    cap = int(limit) if int(limit) > 0 else MAX_SOURCE_CHARS
    if len(body) <= cap:
        return body
    return body[:cap].rstrip()


def is_video_url(url: str) -> bool:
    """True when ``url`` is a known video host or a media-file path.

    Args:
        url: Absolute URL.

    Returns:
        Whether caption fetch should run instead of HTML fetch.
    """
    parsed = urlparse((url or "").strip())
    host = (parsed.hostname or "").strip().lower()
    if host in VIDEO_HOSTS:
        return True
    path = (parsed.path or "").lower()
    return path.endswith(VIDEO_SUFFIXES)


def parse_captions(blob: str) -> str:
    """Parse WebVTT or SRT into spoken lines.

    Args:
        blob: Caption file contents.

    Returns:
        Deduped spoken text.
    """
    lines: list[str] = []
    seen: set[str] = set()
    for raw in (blob or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.upper().startswith("WEBVTT"):
            continue
        if line.startswith("NOTE ") or line == "NOTE":
            continue
        if line.startswith("STYLE") or line.startswith("REGION"):
            continue
        if line.isdigit():
            continue
        if _VTT_TS_RE.match(line):
            continue
        if "-->" in line:
            continue
        if line.startswith("Kind:") or line.startswith("Language:"):
            continue
        cleaned = strip_html(line)
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        lines.append(cleaned)
    return " ".join(lines).strip()


def _read_local_file(path: Path) -> SourceRecord:
    """Read a local text/caption file.

    Args:
        path: Existing file.

    Returns:
        Source record (file or skipped).
    """
    suffix = path.suffix.lower()
    if suffix not in TEXT_SUFFIXES:
        return {
            "kind": "skipped",
            "title": path.name,
            "url": str(path),
            "text": "",
            "status": "no captions",
        }
    try:
        blob = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        _log(f"local read failed: {exc}")
        return {
            "kind": "skipped",
            "title": path.name,
            "url": str(path),
            "text": "",
            "status": f"read failed: {exc}",
        }
    body = parse_captions(blob) if suffix in {".srt", ".vtt"} else blob.strip()
    body = truncate_text(body)
    kind = "captions" if suffix in {".srt", ".vtt"} else "file"
    status = "ok" if body else "empty file"
    return {
        "kind": kind if body else "skipped",
        "title": path.name,
        "url": str(path),
        "text": body,
        "status": status,
    }


def _looks_like_path(token: str) -> bool:
    """True when ``token`` is a plausible local file path.

    Args:
        token: Non-URL paste token.

    Returns:
        Whether to try a filesystem read.
    """
    text = (token or "").strip().strip("\"'")
    if not text or "://" in text:
        return False
    lowered = text.lower()
    if not lowered.endswith(TEXT_SUFFIXES + VIDEO_SUFFIXES):
        return False
    return text.startswith(("/", "./", "../")) or "/" in text or text[0] == "."


def collect_urls(paste: str) -> tuple[list[str], list[str], str]:
    """Split paste into unique URLs, dropped extras, and leftover prose.

    Args:
        paste: Operator blob.

    Returns:
        ``(kept_urls, dropped_urls, prose)``.
    """
    raw = paste if isinstance(paste, str) else str(paste or "")
    if len(raw) > MAX_PASTE_CHARS:
        raw = raw[:MAX_PASTE_CHARS]
        _log(f"paste truncated to {MAX_PASTE_CHARS} chars")
    found = URL_RE.findall(raw)
    kept: list[str] = []
    dropped: list[str] = []
    seen: set[str] = set()
    for url in found:
        cleaned = url.rstrip(").,;]")
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        if len(kept) < MAX_URLS:
            kept.append(cleaned)
        else:
            dropped.append(cleaned)
    prose = raw
    for url in found:
        prose = prose.replace(url, " ")
    prose = _SPACE_RE.sub(" ", prose).strip()
    return kept, dropped, prose


def _fetch_page(url: str) -> str:
    """Fetch and strip an HTTPS page (hook or ez_research SSRF fetch).

    Args:
        url: Absolute URL.

    Returns:
        Plain text, possibly empty.
    """
    if page_fetch_hook is not None:
        return truncate_text(page_fetch_hook(url))
    _ensure_lab_custom_nodes_path()
    try:
        from ez_research.search import http_get, is_blocked_url
    except Exception as exc:  # noqa: BLE001 — fail-soft
        _log(f"page fetch unavailable: {exc}")
        return ""
    reason = is_blocked_url(url)
    if reason:
        _log(f"blocked fetch: {reason}")
        return ""
    blob = http_get(url)
    return truncate_text(strip_html(blob))


def _yt_dlp_captions(url: str) -> str:
    """Download subtitles only with yt-dlp.

    Args:
        url: Video URL.

    Returns:
        Parsed caption text, or empty.
    """
    import subprocess

    with tempfile.TemporaryDirectory(prefix="ez-learn-caps-") as tmp:
        dest = Path(tmp) / "captions"
        cmd = [
            "yt-dlp",
            "--skip-download",
            "--write-sub",
            "--write-auto-sub",
            "--sub-lang",
            "en.*",
            "--sub-format",
            "vtt/srt/best",
            "--no-playlist",
            "-o",
            str(dest),
            url,
        ]
        try:
            proc = subprocess.run(  # noqa: S603 — fixed argv, no shell
                cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            _log(f"caption fetch failed: {exc}")
            return ""
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "").strip()
            _log(f"yt-dlp captions miss: {err or proc.returncode}")
        blobs: list[str] = []
        root = Path(tmp)
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".vtt", ".srt"}:
                continue
            try:
                blobs.append(path.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
        if not blobs:
            return ""
        return truncate_text(parse_captions("\n".join(blobs)))


def _fetch_captions(url: str) -> str:
    """Return captions for a video URL.

    Args:
        url: Video HTTPS URL.

    Returns:
        Caption text, or empty.
    """
    if caption_fetch_hook is not None:
        return truncate_text(caption_fetch_hook(url))
    return _yt_dlp_captions(url)


def _ingest_url(url: str, *, fetch_links: bool) -> SourceRecord:
    """Fetch one URL as a page or caption track.

    Args:
        url: Absolute URL.
        fetch_links: When false, skip network.

    Returns:
        Source record.
    """
    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()
    title = (parsed.hostname or url).strip()
    if scheme != "https":
        return {
            "kind": "skipped",
            "title": title,
            "url": url,
            "text": "",
            "status": "https only",
        }
    if not fetch_links:
        return {
            "kind": "skipped",
            "title": title,
            "url": url,
            "text": "",
            "status": "fetch off",
        }
    if is_video_url(url):
        text = _fetch_captions(url)
        if not text:
            return {
                "kind": "skipped",
                "title": title,
                "url": url,
                "text": "",
                "status": "no captions",
            }
        return {
            "kind": "captions",
            "title": title,
            "url": url,
            "text": text,
            "status": "ok",
        }
    if page_fetch_hook is None:
        _ensure_lab_custom_nodes_path()
        check_blocked: Callable[..., str | None] | None
        try:
            from ez_research.search import is_blocked_url as check_blocked
        except Exception:  # noqa: BLE001 — treat as fetch miss
            check_blocked = None
        if check_blocked is not None:
            blocked_reason = check_blocked(url)
            if blocked_reason:
                return {
                    "kind": "skipped",
                    "title": title,
                    "url": url,
                    "text": "",
                    "status": f"blocked: {blocked_reason}",
                }
    text = _fetch_page(url)
    if not text:
        return {
            "kind": "skipped",
            "title": title,
            "url": url,
            "text": "",
            "status": "empty page",
        }
    return {
        "kind": "page",
        "title": title,
        "url": url,
        "text": text,
        "status": "ok",
    }


def ingest_paste(paste: object, *, fetch_links: object = True) -> list[SourceRecord]:
    """Turn a lazy paste into ordered, capped source records.

    Args:
        paste: Operator blob (prose, URLs, local paths).
        fetch_links: When true, fetch HTTPS pages and video captions.

    Returns:
        Source records including skipped rows (status explains why).
    """
    raw = paste if isinstance(paste, str) else str(paste or "")
    do_fetch = _as_bool(fetch_links)
    urls, dropped, prose = collect_urls(raw)
    records: list[SourceRecord] = []
    if dropped:
        _log(f"dropped {len(dropped)} extra URLs (cap {MAX_URLS})")
        records.append(
            {
                "kind": "skipped",
                "title": "extra URLs",
                "url": "",
                "text": "",
                "status": f"dropped {len(dropped)} extra URLs",
            }
        )
    for url in urls:
        records.append(_ingest_url(url, fetch_links=do_fetch))
    leftovers = prose
    for token in leftovers.split():
        if not _looks_like_path(token):
            continue
        path = Path(token.strip("\"'")).expanduser()
        if not path.is_file():
            continue
        records.append(_read_local_file(path))
        leftovers = leftovers.replace(token, " ")
    leftovers = _SPACE_RE.sub(" ", leftovers).strip()
    if leftovers:
        records.append(
            {
                "kind": "paste",
                "title": "pasted notes",
                "url": "",
                "text": truncate_text(leftovers),
                "status": "ok",
            }
        )
    return records


def format_sources_block(records: list[SourceRecord]) -> str:
    """Join usable source bodies for the digest LLM.

    Args:
        records: Ingest records.

    Returns:
        Numbered source block, capped to ``MAX_TOTAL_SOURCE_CHARS``.
    """
    chunks: list[str] = []
    total = 0
    index = 0
    for rec in records:
        body = (rec.get("text") or "").strip()
        if not body or rec.get("kind") == "skipped":
            continue
        index += 1
        title = rec.get("title") or f"source {index}"
        url = rec.get("url") or ""
        header = f"[{index}] {title}"
        if url:
            header = f"{header}\nURL: {url}"
        piece = f"{header}\n{body}"
        if total + len(piece) > MAX_TOTAL_SOURCE_CHARS:
            remain = MAX_TOTAL_SOURCE_CHARS - total
            if remain < 80:
                _log("source block hit total cap")
                break
            piece = piece[:remain].rstrip()
            chunks.append(piece)
            total = MAX_TOTAL_SOURCE_CHARS
            _log("source block truncated at total cap")
            break
        chunks.append(piece)
        total += len(piece) + 2
    return "\n\n".join(chunks).strip()


def format_status(records: list[SourceRecord]) -> str:
    """One-line-per-source ingest status.

    Args:
        records: Ingest records.

    Returns:
        Newline-joined status, or empty.
    """
    lines: list[str] = []
    for rec in records:
        title = rec.get("title") or rec.get("url") or rec.get("kind") or "source"
        status = rec.get("status") or ""
        kind = rec.get("kind") or ""
        lines.append(f"{kind}: {title} — {status}")
    return "\n".join(lines)
