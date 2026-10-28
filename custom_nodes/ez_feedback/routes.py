"""Fail-soft PromptServer routes for bug reports and feature requests.

Hermetic: ``aiohttp``, ``server.PromptServer``, ``EZ_GITHUB_TOKEN`` and
``torch`` are all optional. Tests call :func:`config_payload` and
:func:`handle_submit` with plain dicts and an injected opener, so nothing
touches the network.

Two routes only: ``GET /ez_feedback/config`` (does this build have a token,
what env facts should a report carry) and ``POST /ez_feedback/submit`` (file
through GitHub). Without a token submit answers 409 and the client falls back
to the prefilled ``/issues/new`` handoff. The token never crosses the wire and
never reaches a log line.
"""

from __future__ import annotations

import inspect
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from typing import Any

from . import context

TOKEN_ENV = "EZ_GITHUB_TOKEN"
"""Name of the optional GitHub token; its value is never read out."""

API_BASE_ENV = "EZ_GITHUB_API_BASE"
"""Override for the issues API base, still pinned to :data:`ALLOWED_HOST`."""

DEFAULT_API_BASE = "https://api.github.com/repos"
"""Issues API base used when :data:`API_BASE_ENV` is unset."""

ALLOWED_HOST = "api.github.com"
"""Only host an outbound report call may target."""

SUBMIT_TIMEOUT_S = 15.0
"""Socket timeout for the GitHub POST."""

USER_AGENT = "ez-comfy-stack-feedback"
"""User agent on the GitHub POST."""

NO_TOKEN_ERROR = "no token; use the GitHub link"
"""409 body: the client keeps the GitHub handoff button in that case."""


def token(environ: Mapping[str, str] | None = None) -> str:
    """Optional GitHub token, or ``""``.

    Args:
        environ: Environment mapping; defaults to ``os.environ``.

    Returns:
        Trimmed token value. Never logged, never returned by a route.
    """
    source = os.environ if environ is None else environ
    return str(source.get(TOKEN_ENV) or "").strip()


def _labels(raw: object, kind: str) -> list[str]:
    """Filter caller labels to the ones that exist in the repo.

    Args:
        raw: ``labels`` from the request body.
        kind: Report kind used for the default.

    Returns:
        Sorted unique allowed labels, or the kind default.
    """
    allowed = set(context.ALLOWED_LABELS)
    if isinstance(raw, list):
        picked = {str(item).strip() for item in raw if str(item).strip() in allowed}
        if picked:
            return sorted(picked)
    return context.labels_for(kind)


def api_url(repo: str, environ: Mapping[str, str] | None = None) -> str:
    """Issues API URL for a repo.

    Args:
        repo: ``owner/name``.
        environ: Environment mapping; may carry :data:`API_BASE_ENV`.

    Returns:
        ``https://api.github.com/repos/<repo>/issues`` by default.
    """
    source: Mapping[str, str] = os.environ if environ is None else environ
    base = str(source.get(API_BASE_ENV) or DEFAULT_API_BASE).rstrip("/")
    return f"{base}/{repo}/issues"


def gpu_probe(module: Any | None = None) -> dict[str, str]:
    """Torch / CUDA / GPU facts for :func:`context.env_snapshot`.

    torch is imported here, never at module import, so the pack still loads
    where it is absent and tests inject a stand-in module instead.

    Args:
        module: torch stand-in for tests; imported when ``None``.

    Returns:
        Only the facts that resolved (``torch``, ``cuda``, ``gpu``).
    """
    torch = module if module is not None else _import_torch()
    if torch is None:
        return {}
    facts: dict[str, str] = {}
    try:
        facts["torch"] = str(getattr(torch, "__version__", "") or "")
        version = getattr(torch, "version", None)
        facts["cuda"] = str(getattr(version, "cuda", "") or "") if version else ""
        cuda = getattr(torch, "cuda", None)
        if cuda is not None and bool(cuda.is_available()):
            facts["gpu"] = str(cuda.get_device_name(0))
    except Exception:  # noqa: BLE001 - GPU facts are best effort
        return {key: value for key, value in facts.items() if value}
    return {key: value for key, value in facts.items() if value}


def _import_torch() -> Any | None:
    """Import torch lazily.

    Returns:
        The torch module, or ``None`` when it is not installed.
    """
    try:
        import torch  # noqa: PLC0415 - optional heavy import, never at module load

        return torch
    except Exception:  # noqa: BLE001 - absent or broken CUDA stack
        return None


def config_payload(
    environ: Mapping[str, str] | None = None,
    probe: Callable[[], Mapping[str, str]] | None = None,
) -> tuple[int, dict[str, Any]]:
    """Body for ``GET /ez_feedback/config``.

    Args:
        environ: Environment mapping; defaults to ``os.environ``.
        probe: Optional torch/GPU probe for the env block.

    Returns:
        ``(200, {repoUrl, tokenPresent, labels, env})``. ``tokenPresent`` is a
        bool only - the token value never leaves the process.
    """
    return 200, {
        "repoUrl": f"{context.GITHUB_URL}/{context.REPO}",
        "tokenPresent": bool(token(environ)),
        "labels": list(context.ALLOWED_LABELS),
        "env": context.env_snapshot(
            os.environ if environ is None else environ, probe
        ),
    }


def handle_submit(
    args: Mapping[str, object],
    *,
    environ: Mapping[str, str] | None = None,
    opener: Callable[[urllib.request.Request, float], Any] | None = None,
) -> tuple[int, dict[str, Any]]:
    """Body for ``POST /ez_feedback/submit``.

    The body is redacted and clipped to :data:`context.MAX_BODY` before it is
    posted, and the token is only ever used as an ``Authorization`` header.

    Args:
        args: Request body with ``kind``, ``title``, ``body``, ``labels``.
        environ: Environment mapping; defaults to ``os.environ``.
        opener: ``(request, timeout)`` HTTP callable; tests inject one.

    Returns:
        ``(200, {ok, url, number})`` on success, ``(409, {ok, error})`` with no
        token, ``(400, ...)`` for a non-GitHub host, ``(502|500, ...)`` when
        GitHub cannot be reached.
    """
    source: Mapping[str, str] = os.environ if environ is None else environ
    body_args: Mapping[str, object] = args if isinstance(args, Mapping) else {}
    kind = context.kind_key(str(body_args.get("kind") or "bug"))
    title = context.clip(str(body_args.get("title") or "").strip(), context.MAX_TITLE)
    if not title:
        title = context.title_for(kind, context.GLOBAL_AREA, "", "")
    body = context.redact(str(body_args.get("body") or ""))[: context.MAX_BODY]
    labels = _labels(body_args.get("labels"), kind)
    secret = token(source)
    if not secret:
        return 409, {"ok": False, "error": NO_TOKEN_ERROR}
    url = api_url(context.REPO, source)
    if urllib.parse.urlsplit(url).hostname != ALLOWED_HOST:
        return 400, {"ok": False, "error": f"host must be {ALLOWED_HOST}"}
    payload = {"title": title, "body": body, "labels": labels}
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {secret}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    post = opener if opener is not None else urlopen
    try:
        response = post(request, SUBMIT_TIMEOUT_S)
        raw = response.read()
        response.close()
    except urllib.error.HTTPError as exc:
        return 502, {"ok": False, "error": context.redact(f"github error {exc.code}")}
    except urllib.error.URLError as exc:
        return 502, {"ok": False, "error": context.redact(f"github unreachable {exc.reason}")}
    except Exception as exc:  # noqa: BLE001 - never leak a traceback to the client
        return 500, {"ok": False, "error": context.redact(type(exc).__name__)}
    return 200, {"ok": True, **_issue_fields(raw)}


def _issue_fields(raw: object) -> dict[str, Any]:
    """Pull ``url`` and ``number`` out of a GitHub create-issue response.

    Args:
        raw: Response bytes, text, or mapping.

    Returns:
        ``{url, number}`` with empty/``None`` values when GitHub said nothing.
    """
    data: object = raw
    if isinstance(data, (bytes, bytearray)):
        data = bytes(data).decode("utf-8", "replace")
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except ValueError:
            data = {}
    if not isinstance(data, Mapping):
        data = {}
    number = data.get("number")
    url = str(data.get("html_url") or "")
    return {
        "url": url,
        "number": number if isinstance(number, int) else None,
    }


def urlopen(request: urllib.request.Request, timeout: float) -> Any:
    """Indirection so pytest can mock GitHub without touching the network.

    Args:
        request: The prepared issues-API request.
        timeout: Socket timeout in seconds.

    Returns:
        Opened HTTP response (caller reads and closes it).
    """
    return urllib.request.urlopen(request, timeout=timeout)


async def request_json(request: object) -> object:
    """Read a JSON body from an aiohttp-like request.

    Args:
        request: Object with an optional ``json`` callable (async or sync).

    Returns:
        Parsed body, or ``{}`` when missing or invalid.
    """
    json_fn = getattr(request, "json", None)
    if not callable(json_fn):
        return {}
    try:
        raw = json_fn()
        if inspect.isawaitable(raw):
            return await raw  # type: ignore[misc]
        return raw
    except Exception:  # noqa: BLE001 - empty or invalid body
        return {}


def register_routes(
    *,
    server: object | None = None,
    json_response: Any | None = None,
) -> bool:
    """Attach ``/ez_feedback/*`` when PromptServer (or a stand-in) exists.

    Args:
        server: Optional PromptServer stand-in with ``routes.get`` / ``post``.
        json_response: Optional ``(payload, status=)`` factory. Defaults to
            aiohttp ``web.json_response`` when that import works.

    Returns:
        True when both routes were registered.
    """
    responder = json_response
    if responder is None:
        try:
            from aiohttp import web

            responder = web.json_response
        except Exception:  # noqa: BLE001 - optional in pytest
            return False
    inst = server
    if inst is None:
        try:
            server_mod = __import__("server")
            prompt_server = getattr(server_mod, "PromptServer", None)
            inst = getattr(prompt_server, "instance", None)
        except Exception:  # noqa: BLE001 - Comfy optional in pytest
            return False
        if inst is None:
            return False
    routes = getattr(inst, "routes", None)
    if routes is None:
        return False

    async def config_handler(request: object) -> object:
        """Serve ``GET /ez_feedback/config``.

        Args:
            request: aiohttp request (unused; no query inputs).

        Returns:
            JSON response from :func:`config_payload`.
        """
        status, payload = config_payload(probe=gpu_probe)
        return responder(payload, status=status)

    async def submit_handler(request: object) -> object:
        """Serve ``POST /ez_feedback/submit``.

        Args:
            request: aiohttp request with a JSON body.

        Returns:
            JSON response from :func:`handle_submit`.
        """
        body = await request_json(request)
        if not isinstance(body, dict):
            body = {}
        status, payload = handle_submit(body)
        return responder(payload, status=status)

    adder_get = getattr(routes, "get", None)
    adder_post = getattr(routes, "post", None)
    if adder_get is None or adder_post is None:
        return False
    adder_get("/ez_feedback/config")(config_handler)
    adder_post("/ez_feedback/submit")(submit_handler)
    return True
