"""Fail-soft PromptServer route for Check models.

Hermetic import: aiohttp / ``server.PromptServer`` are optional. Tests call
:func:`handle_check` with plain dicts.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Sequence

from .check import run_check


def _json_ok(payload: dict[str, Any], *, status: int = 200) -> tuple[int, dict[str, Any]]:
    """Return an HTTP status and JSON object.

    Args:
        payload: Response body.
        status: HTTP status.

    Returns:
        ``(status, payload)``.
    """
    return status, payload


def handle_check(
    args: dict[str, Any],
    *,
    roots: Sequence[Path] | None = None,
) -> tuple[int, dict[str, Any]]:
    """Scan required models for the posted graph hints.

    Args:
        args: JSON body (occupancy, quality, loader names, ...).
        roots: Models-root override for tests.

    Returns:
        ``(200, check payload)``.
    """
    body = args if isinstance(args, dict) else {}
    payload = run_check(body, roots=roots)
    return _json_ok(payload)


async def request_json(request: object) -> object:
    """Read a JSON body from an aiohttp-like request.

    Args:
        request: Object with optional ``json`` callable (async or sync).

    Returns:
        Parsed body, or ``{}`` when missing/invalid.
    """
    json_fn = getattr(request, "json", None)
    if not callable(json_fn):
        return {}
    try:
        raw = json_fn()
        if inspect.isawaitable(raw):
            return await raw  # type: ignore[misc]
        return raw
    except Exception:  # noqa: BLE001 - empty/invalid body
        return {}


def register_routes(
    *,
    server: object | None = None,
    json_response: Any | None = None,
) -> bool:
    """Attach ``POST /ez_quality/check`` when PromptServer exists.

    Args:
        server: Optional PromptServer stand-in with ``routes.post``.
        json_response: Optional ``(payload, status=)`` factory. Defaults to
            aiohttp ``web.json_response`` when that import works.

    Returns:
        True when the route was registered.
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

    async def check_handler(request: object) -> object:
        """Serve POST /ez_quality/check.

        Args:
            request: aiohttp request with a JSON body.

        Returns:
            JSON response from :func:`handle_check`.
        """
        body = await request_json(request)
        if not isinstance(body, dict):
            body = {}
        status, payload = handle_check(body)
        return responder(payload, status=status)

    adder_post = getattr(routes, "post", None)
    if adder_post is None:
        return False
    adder_post("/ez_quality/check")(check_handler)
    return True
