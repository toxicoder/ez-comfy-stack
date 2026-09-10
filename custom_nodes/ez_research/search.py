"""SSRF-safe HTTPS search for ez_research.

Hermetic: stdlib only. Tests inject ``_urlopen`` and ``_getaddrinfo``.
No API keys. Fail-soft: empty hits on any network or parse error.
"""

from __future__ import annotations

import html as html_module
import ipaddress
import json
import re
import socket
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Sequence

USER_AGENT = "ez-comfy-research/1.0"
MAX_BODY = 256 * 1024
DEFAULT_TIMEOUT_S = 8.0
MAX_REDIRECTS = 3
MAX_SNIPPET = 400
MAX_BODY_CHARS = 2000

WIKI_OPENSEARCH = "https://en.wikipedia.org/w/api.php"
WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/"
DDG_HTML = "https://html.duckduckgo.com/html/"

_PRIVATE_NETS = (
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
)

_BLOCKED_HOSTS = frozenset(
    {
        "localhost",
        "localhost.localdomain",
        "metadata.google.internal",
        "metadata.internal",
    }
)

_RESULT_A_RE = re.compile(
    r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
_SNIPPET_RE = re.compile(
    r'class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</(?:a|td|div|span)>',
    re.IGNORECASE | re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")

_urlopen: Callable[..., Any] = urllib.request.urlopen
_getaddrinfo: Callable[..., list[tuple[Any, ...]]] = socket.getaddrinfo


@dataclass
class SearchHit:
    """One search result (title, URL, snippet, optional fetched body)."""

    title: str
    url: str
    snippet: str
    body: str = ""


def _log(message: str) -> None:
    print(f"[ez_research] {message}", file=sys.stderr)


def _ip_blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast:
        return True
    if ip.is_reserved or ip.is_unspecified:
        return True
    mapped = getattr(ip, "ipv4_mapped", None)
    if mapped is not None:
        return _ip_blocked(mapped)
    return any(ip in net for net in _PRIVATE_NETS)


def is_blocked_url(
    url: str,
    *,
    resolver: Callable[..., list[tuple[Any, ...]]] | None = None,
) -> str | None:
    """Return a reason string when ``url`` must not be fetched.

    Arguments:
        url: Absolute URL.
        resolver: Optional ``getaddrinfo`` substitute.
    Returns:
        Block reason, or None when the URL may be fetched.
    """
    raw = (url or "").strip()
    if not raw:
        return "empty url"
    parsed = urllib.parse.urlparse(raw)
    scheme = (parsed.scheme or "").lower()
    if scheme != "https":
        return "https only"
    host = (parsed.hostname or "").strip().lower()
    if not host:
        return "missing host"
    if parsed.username or parsed.password:
        return "userinfo blocked"
    if host in _BLOCKED_HOSTS:
        return "blocked host"
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None and _ip_blocked(literal):
        return "blocked ip"
    lookup = resolver or _getaddrinfo
    try:
        infos = lookup(host, parsed.port or 443)
    except OSError:
        return "dns failed"
    for info in infos:
        sockaddr = info[4] if len(info) > 4 else ()
        addr = sockaddr[0] if sockaddr else ""
        if not isinstance(addr, str) or not addr:
            continue
        if "%" in addr:
            addr = addr.split("%", 1)[0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            continue
        if _ip_blocked(ip):
            return "blocked ip"
    return None


def decode_ddg_href(href: str) -> str:
    """Unwrap DuckDuckGo ``/l/?uddg=`` redirect links to the target HTTPS URL."""
    raw = html_module.unescape((href or "").strip())
    if raw.startswith("//"):
        raw = "https:" + raw
    parsed = urllib.parse.urlparse(raw)
    host = (parsed.netloc or "").lower()
    if "duckduckgo.com" in host and parsed.path.startswith("/l/"):
        qs = urllib.parse.parse_qs(parsed.query)
        wrapped = qs.get("uddg") or qs.get("u")
        if wrapped:
            return urllib.parse.unquote(wrapped[0])
    return raw


def _strip_html(blob: str) -> str:
    text = _TAG_RE.sub(" ", blob or "")
    text = html_module.unescape(text)
    return _SPACE_RE.sub(" ", text).strip()


def parse_wikipedia_opensearch(payload: object) -> list[SearchHit]:
    """Parse MediaWiki opensearch JSON into hits."""
    if not isinstance(payload, list) or len(payload) < 4:
        return []
    titles = payload[1]
    snippets = payload[2]
    urls = payload[3]
    if not (
        isinstance(titles, list)
        and isinstance(snippets, list)
        and isinstance(urls, list)
    ):
        return []
    hits: list[SearchHit] = []
    for i, title_raw in enumerate(titles):
        title = str(title_raw or "").strip()
        url = str(urls[i] if i < len(urls) else "").strip()
        snippet = str(snippets[i] if i < len(snippets) else "").strip()
        if not title or not url:
            continue
        if is_blocked_url(url) is not None:
            continue
        hits.append(
            SearchHit(
                title=title,
                url=url,
                snippet=snippet[:MAX_SNIPPET],
            )
        )
    return hits


def parse_duckduckgo_html(markup: str) -> list[SearchHit]:
    """Parse DuckDuckGo HTML result titles, URLs, and snippets."""
    hits: list[SearchHit] = []
    for match in _RESULT_A_RE.finditer(markup or ""):
        href = decode_ddg_href(match.group(1))
        title = _strip_html(match.group(2))
        if not href or not title:
            continue
        if is_blocked_url(href) is not None:
            continue
        hits.append(SearchHit(title=title, url=href, snippet=""))
    snippets = [_strip_html(raw) for raw in _SNIPPET_RE.findall(markup or "")]
    for i, snippet in enumerate(snippets):
        if i < len(hits) and snippet:
            hits[i].snippet = snippet[:MAX_SNIPPET]
    return hits


def http_get(
    url: str,
    *,
    data: bytes | None = None,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> str:
    """GET or POST ``url``. Empty string on block, timeout, or error."""
    reason = is_blocked_url(url)
    if reason:
        _log(f"blocked fetch: {reason}")
        return ""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
    }
    method = "POST" if data is not None else "GET"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with _urlopen(  # noqa: S310 — scheme/host checked in is_blocked_url
            request,
            timeout=timeout,
            context=ssl.create_default_context(),
        ) as resp:
            final = str(getattr(resp, "geturl", lambda: url)())
            blocked = is_blocked_url(final)
            if blocked:
                _log(f"blocked redirect: {blocked}")
                return ""
            raw = resp.read(MAX_BODY + 1)
    except (OSError, urllib.error.URLError, TimeoutError, ValueError, ssl.SSLError) as exc:
        _log(f"fetch failed: {exc}")
        return ""
    if len(raw) > MAX_BODY:
        raw = raw[:MAX_BODY]
    try:
        return raw.decode("utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001 — fail-soft
        _log(f"decode failed: {exc}")
        return ""


def _wiki_summary_body(title: str) -> str:
    slug = urllib.parse.quote(title.replace(" ", "_"), safe="")
    blob = http_get(WIKI_SUMMARY + slug)
    if not blob:
        return ""
    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        return ""
    if not isinstance(data, dict):
        return ""
    extract = data.get("extract")
    if not isinstance(extract, str):
        return ""
    return extract.strip()[:MAX_BODY_CHARS]


def wikipedia_search(query: str, *, limit: int = 3, fetch_bodies: bool = True) -> list[SearchHit]:
    """OpenSearch Wikipedia, optionally filling REST summary bodies."""
    q = (query or "").strip()
    if not q:
        return []
    cap = max(1, min(int(limit), 5))
    params = urllib.parse.urlencode(
        {
            "action": "opensearch",
            "format": "json",
            "limit": str(cap),
            "search": q,
        }
    )
    blob = http_get(f"{WIKI_OPENSEARCH}?{params}")
    if not blob:
        return []
    try:
        payload: Any = json.loads(blob)
    except json.JSONDecodeError:
        return []
    hits = parse_wikipedia_opensearch(payload)[:cap]
    if fetch_bodies:
        for hit in hits:
            hit.body = _wiki_summary_body(hit.title)
    return hits


def duckduckgo_search(query: str, *, limit: int = 3, fetch_bodies: bool = False) -> list[SearchHit]:
    """DuckDuckGo HTML fallback. Bodies stay off unless asked (SSRF surface)."""
    q = (query or "").strip()
    if not q:
        return []
    cap = max(1, min(int(limit), 5))
    data = urllib.parse.urlencode({"q": q, "b": ""}).encode("utf-8")
    blob = http_get(DDG_HTML, data=data)
    if not blob:
        return []
    hits = parse_duckduckgo_html(blob)[:cap]
    if fetch_bodies:
        for hit in hits:
            if is_blocked_url(hit.url) is not None:
                continue
            page = http_get(hit.url)
            if page:
                hit.body = _strip_html(page)[:MAX_BODY_CHARS]
    return hits


def search_web(
    query: str,
    *,
    limit: int = 5,
    fetch_bodies: bool = True,
) -> list[SearchHit]:
    """Wikipedia first, DuckDuckGo HTML to fill remaining slots."""
    q = (query or "").strip()
    if not q:
        return []
    cap = max(1, min(int(limit), 8))
    hits = wikipedia_search(q, limit=min(3, cap), fetch_bodies=fetch_bodies)
    seen = {hit.url for hit in hits}
    if len(hits) < cap:
        extra = duckduckgo_search(
            q,
            limit=cap - len(hits),
            fetch_bodies=False,
        )
        for hit in extra:
            if hit.url in seen:
                continue
            hits.append(hit)
            seen.add(hit.url)
            if len(hits) >= cap:
                break
    return hits[:cap]


def format_sources(hits: Sequence[SearchHit]) -> str:
    """Markdown source list for the App preview and MCP payload."""
    lines: list[str] = []
    for i, hit in enumerate(hits, start=1):
        snippet = hit.snippet or hit.body[:MAX_SNIPPET]
        lines.append(f"{i}. {hit.title} — {hit.url}")
        if snippet:
            lines.append(f"   {snippet}")
    return "\n".join(lines)
