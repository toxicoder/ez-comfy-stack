"""Fail-soft PromptServer route for the image-studio run preview.

Hermetic import: aiohttp / ``server.PromptServer`` are optional. Tests call
:func:`handle_preview` with plain dicts. The handler imports the prompt
composer lazily so this pack does not import ``ez_prompt_enhance`` at startup.
"""

from __future__ import annotations

import inspect
from typing import Any


PREVIEW_UNAVAILABLE = (
    "Preview unavailable - Queue still uses the nodes. Reload the App after pull if this stays."
)
"""Shown when the preview composer cannot run. Queue is unchanged."""


def _json_ok(payload: dict[str, Any], *, status: int = 200) -> tuple[int, dict[str, Any]]:
    """Return an HTTP status and JSON object.

    Args:
        payload: Response body.
        status: HTTP status.

    Returns:
        ``(status, payload)``.
    """
    return status, payload


def handle_preview(args: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """Resolve the image-studio values Queue will send.

    Args:
        args: JSON body of App widget values.

    Returns:
        ``(200, preview payload)``. A composer failure is still 200 with
        ``ok`` false so the App can say the preview is unavailable.
    """
    body = args if isinstance(args, dict) else {}
    try:
        from ez_prompt_enhance.studio_preview import preview_payload
    except Exception:  # noqa: BLE001 - pack missing in a partial install
        return _json_ok({"ok": False, "summary": PREVIEW_UNAVAILABLE})
    try:
        payload = preview_payload(body)
    except Exception:  # noqa: BLE001 - catalog or widget parse; Queue still runs
        return _json_ok({"ok": False, "summary": PREVIEW_UNAVAILABLE})
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
    """Attach ``POST /ez_image/studio-preview`` when PromptServer exists.

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

    async def preview_handler(request: object) -> object:
        """Serve POST /ez_image/studio-preview.

        Args:
            request: aiohttp request with a JSON body.

        Returns:
            JSON response from :func:`handle_preview`.
        """
        body = await request_json(request)
        if not isinstance(body, dict):
            body = {}
        status, payload = handle_preview(body)
        return responder(payload, status=status)

    adder_post = getattr(routes, "post", None)
    if adder_post is None:
        return False
    adder_post("/ez_image/studio-preview")(preview_handler)
    return True
