"""Fail-soft PromptServer routes for the Outputs sidebar.

Hermetic import: aiohttp / ``server.PromptServer`` are optional. Tests call
:func:`handle_list`, :func:`handle_delete`, and :func:`handle_to_input`
with plain dicts.
"""

from __future__ import annotations

from typing import Any

from .catalog import (
    CatalogError,
    copy_to_input,
    delete_output,
    input_root,
    list_outputs,
    output_directory,
)


def _json_ok(payload: dict[str, Any], *, status: int = 200) -> tuple[int, dict[str, Any]]:
    """Return an HTTP status and JSON object.

    Args:
        payload: Response body.
        status: HTTP status.

    Returns:
        ``(status, payload)``.
    """
    return status, payload


def handle_list(args: dict[str, Any], *, root: Any | None = None) -> tuple[int, dict[str, Any]]:
    """List media files.

    Args:
        args: Query dict with optional ``kind``, ``q``, ``limit``.
        root: Output root override for tests.

    Returns:
        ``(200, {items})``.
    """
    base = output_directory() if root is None else root
    kind = str(args.get("kind") or "all")
    query = str(args.get("q") or args.get("query") or "")
    try:
        limit = int(args.get("limit") or 0)
    except (TypeError, ValueError):
        limit = 0
    items = list_outputs(base, kind=kind, query=query, limit=limit or 500)
    return _json_ok({"items": items})


def handle_delete(args: dict[str, Any], *, root: Any | None = None) -> tuple[int, dict[str, Any]]:
    """Delete one media file.

    Args:
        args: Body/query with ``rel``.
        root: Output root override for tests.

    Returns:
        ``(200, {ok, rel})`` or ``(400, {error})``.
    """
    base = output_directory() if root is None else root
    rel = str(args.get("rel") or "")
    try:
        delete_output(base, rel)
    except CatalogError as exc:
        return _json_ok({"error": str(exc)}, status=400)
    return _json_ok({"ok": True, "rel": rel})


def handle_to_input(
    args: dict[str, Any],
    *,
    root: Any | None = None,
    input_dir: Any | None = None,
) -> tuple[int, dict[str, Any]]:
    """Copy one media file into the LoadImage input directory.

    Args:
        args: Body/query with ``rel``.
        root: Output root override for tests.
        input_dir: Input directory override for tests.

    Returns:
        ``(200, {ok, name})`` or ``(400, {error})``.
    """
    base = output_directory() if root is None else root
    dest_root = input_root() if input_dir is None else input_dir
    rel = str(args.get("rel") or "")
    try:
        dest = copy_to_input(base, rel, input_dir=dest_root)
    except CatalogError as exc:
        return _json_ok({"error": str(exc)}, status=400)
    return _json_ok({"ok": True, "name": dest.name, "rel": dest.name})


def register_routes(
    *,
    server: object | None = None,
    json_response: Any | None = None,
) -> bool:
    """Attach ``/ez_outputs/*`` when PromptServer (or a stand-in) exists.

    Args:
        server: Optional PromptServer stand-in with ``routes.get`` / ``post``.
        json_response: Optional ``(payload, status=)`` factory. Defaults to
            aiohttp ``web.json_response`` when that import works.

    Returns:
        True when routes were registered.
    """
    responder = json_response
    if responder is None:
        try:
            from aiohttp import web

            responder = web.json_response
        except Exception:  # noqa: BLE001 — optional in pytest
            return False
    inst = server
    if inst is None:
        try:
            server_mod = __import__("server")
            prompt_server = getattr(server_mod, "PromptServer", None)
            inst = getattr(prompt_server, "instance", None)
        except Exception:  # noqa: BLE001 — Comfy optional in pytest
            return False
        if inst is None:
            return False
    routes = getattr(inst, "routes", None)
    if routes is None:
        return False

    async def list_handler(request: object) -> object:
        """Serve GET /ez_outputs/list.

        Args:
            request: aiohttp request with a ``query`` mapping.

        Returns:
            JSON response from :func:`handle_list`.
        """
        query = getattr(request, "query", {}) or {}
        status, payload = handle_list(dict(query))
        return responder(payload, status=status)

    async def delete_handler(request: object) -> object:
        """Serve POST /ez_outputs/delete.

        Args:
            request: aiohttp request with a JSON body.

        Returns:
            JSON response from :func:`handle_delete`.
        """
        try:
            json_fn = getattr(request, "json", None)
            body = await json_fn() if callable(json_fn) else {}
        except Exception:  # noqa: BLE001 — empty/invalid body
            body = {}
        if not isinstance(body, dict):
            body = {}
        status, payload = handle_delete(body)
        return responder(payload, status=status)

    async def to_input_handler(request: object) -> object:
        """Serve POST /ez_outputs/to-input.

        Args:
            request: aiohttp request with a JSON body.

        Returns:
            JSON response from :func:`handle_to_input`.
        """
        try:
            json_fn = getattr(request, "json", None)
            body = await json_fn() if callable(json_fn) else {}
        except Exception:  # noqa: BLE001 — empty/invalid body
            body = {}
        if not isinstance(body, dict):
            body = {}
        status, payload = handle_to_input(body)
        return responder(payload, status=status)

    adder_get = getattr(routes, "get", None)
    adder_post = getattr(routes, "post", None)
    if adder_get is None or adder_post is None:
        return False
    adder_get("/ez_outputs/list")(list_handler)
    adder_post("/ez_outputs/delete")(delete_handler)
    adder_post("/ez_outputs/to-input")(to_input_handler)
    return True
