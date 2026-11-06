"""Fail-soft PromptServer routes for the Outputs sidebar.

Hermetic import: aiohttp / ``server.PromptServer`` are optional. Tests call
:func:`handle_list`, :func:`handle_delete`, and :func:`handle_to_input`
with plain dicts. Delete and copy accept a single ``rel`` or a ``rels`` list.
"""

from __future__ import annotations

import inspect
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, TypedDict, TypeVar, cast

from .catalog import (
    BatchError,
    CatalogError,
    CopyRow,
    OutputRow,
    copy_many_to_input,
    copy_to_input,
    delete_many,
    delete_output,
    input_root,
    list_outputs,
    output_directory,
)

if TYPE_CHECKING:
    from ez_common import Json


class ListPayload(TypedDict):
    """Body for ``GET /ez_outputs/list``."""

    items: list[OutputRow]
    """Newest-first media rows within the cap."""

    truncated: bool
    """True when more rows existed than the cap allowed."""

    count: int
    """Rows returned."""


class DeletePayload(TypedDict, total=False):
    """Body for ``POST /ez_outputs/delete`` (single or bulk)."""

    ok: bool
    """True on any accepted request."""

    rel: str
    """Single-file path the request removed."""

    error: str
    """Operator-facing refuse reason."""

    deleted: list[str]
    """Relative paths removed in a bulk request."""

    errors: list[BatchError]
    """Refused rows in a bulk request."""


class CopyPayload(TypedDict, total=False):
    """Body for ``POST /ez_outputs/to-input`` (single or bulk)."""

    ok: bool
    """True on any accepted request."""

    name: str
    """LoadImage combo value for the copied file."""

    rel: str
    """Source path relative to the output root."""

    error: str
    """Operator-facing refuse reason."""

    copied: list[CopyRow]
    """Rows copied into the input directory in a bulk request."""

    errors: list[BatchError]
    """Refused rows in a bulk request."""


class JsonResponder(Protocol):
    """aiohttp ``web.json_response`` or a test stand-in for it."""

    def __call__(self, payload: object, *, status: int = ...) -> object:
        """Build one route response.

        Args:
            payload: JSON-serialisable body.
            status: HTTP status code.

        Returns:
            Whatever the server framework expects.
        """
        ...


_PayloadT = TypeVar("_PayloadT", bound=Mapping[str, object])


def _json_ok(
    payload: _PayloadT, *, status: int = 200
) -> tuple[int, _PayloadT]:
    """Return an HTTP status and JSON object.

    Args:
        payload: Response body.
        status: HTTP status.

    Returns:
        ``(status, payload)``.
    """
    return status, payload


def rels_from_args(args: Mapping[str, Json]) -> list[str]:
    """Collect ``rel`` or ``rels`` from a request body.

    Prefers a non-empty ``rels`` list. Falls back to a single ``rel`` string
    so ``ez_media_pick.js`` keeps working.

    Args:
        args: Body/query mapping.

    Returns:
        Relative paths (may be empty).
    """
    raw = args.get("rels")
    if isinstance(raw, list):
        found = [str(item).strip() for item in raw if str(item).strip()]
        if found:
            return found
    if isinstance(raw, str) and raw.strip():
        return [raw.strip()]
    rel = str(args.get("rel") or "").strip()
    return [rel] if rel else []


def handle_list(
    args: Mapping[str, Json], *, root: Path | None = None
) -> tuple[int, ListPayload]:
    """List media files.

    Args:
        args: Query dict with optional ``kind``, ``q``, ``limit``.
        root: Output root override for tests.

    Returns:
        ``(200, {items, truncated, count})``.
    """
    base = output_directory() if root is None else root
    kind = str(args.get("kind") or "all")
    query = str(args.get("q") or args.get("query") or "")
    raw_limit = args.get("limit")
    try:
        limit = int(raw_limit) if isinstance(raw_limit, (str, int, float)) else 0
    except (TypeError, ValueError):
        limit = 0
    cap = limit if limit > 0 else 500
    items = list_outputs(base, kind=kind, query=query, limit=cap + 1)
    truncated = len(items) > cap
    clipped = items[:cap]
    body: ListPayload = {
        "items": clipped,
        "truncated": truncated,
        "count": len(clipped),
    }
    return _json_ok(body)


def handle_delete(
    args: Mapping[str, Json], *, root: Path | None = None
) -> tuple[int, DeletePayload]:
    """Delete one media file, or many when ``rels`` is a list.

    Args:
        args: Body/query with ``rel`` or ``rels``.
        root: Output root override for tests.

    Returns:
        Single: ``(200, {ok, rel})`` or ``(400, {error})``.
        Bulk: ``(200, {ok, deleted, errors})`` when any succeeded, else 400.
    """
    base = output_directory() if root is None else root
    rels = rels_from_args(args)
    if len(rels) <= 1:
        rel = rels[0] if rels else str(args.get("rel") or "")
        try:
            delete_output(base, rel)
        except CatalogError as exc:
            return _json_ok(DeletePayload(error=str(exc)), status=400)
        return _json_ok(DeletePayload(ok=True, rel=rel))
    try:
        deleted, errors = delete_many(base, rels)
    except CatalogError as exc:
        return _json_ok(DeletePayload(error=str(exc)), status=400)
    payload = DeletePayload(ok=True, deleted=deleted, errors=errors)
    if not deleted:
        first = errors[0]["error"] if errors else "invalid output path"
        return _json_ok(
            DeletePayload(error=first, deleted=deleted, errors=errors), status=400
        )
    return _json_ok(payload)


def handle_to_input(
    args: Mapping[str, Json],
    *,
    root: Path | None = None,
    input_dir: Path | None = None,
) -> tuple[int, CopyPayload]:
    """Copy one media file (or many) into the LoadImage input directory.

    Args:
        args: Body/query with ``rel`` or ``rels``.
        root: Output root override for tests.
        input_dir: Input directory override for tests.

    Returns:
        Single: ``(200, {ok, name})`` or ``(400, {error})``.
        Bulk: ``(200, {ok, copied, errors})`` when any succeeded, else 400.
    """
    base = output_directory() if root is None else root
    dest_root = input_root() if input_dir is None else input_dir
    rels = rels_from_args(args)
    if len(rels) <= 1:
        rel = rels[0] if rels else str(args.get("rel") or "")
        try:
            dest = copy_to_input(base, rel, input_dir=dest_root)
        except CatalogError as exc:
            return _json_ok(CopyPayload(error=str(exc)), status=400)
        return _json_ok(CopyPayload(ok=True, name=dest.name, rel=dest.name))
    try:
        copied, errors = copy_many_to_input(base, rels, input_dir=dest_root)
    except CatalogError as exc:
        return _json_ok(CopyPayload(error=str(exc)), status=400)
    if not copied:
        first = errors[0]["error"] if errors else "invalid output path"
        return _json_ok(
            CopyPayload(error=first, copied=copied, errors=errors), status=400
        )
    return _json_ok(CopyPayload(ok=True, copied=copied, errors=errors))


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
            return await raw
        return raw
    except Exception:  # noqa: BLE001 - empty/invalid body
        return {}


def register_routes(
    *,
    server: object | None = None,
    json_response: object | None = None,
) -> bool:
    """Attach ``/ez_outputs/*`` when PromptServer (or a stand-in) exists.

    Args:
        server: Optional PromptServer stand-in with ``routes.get`` / ``post``.
        json_response: Optional ``(payload, status=)`` factory. Defaults to
            aiohttp ``web.json_response`` when that import works.

    Returns:
        True when routes were registered.
    """
    responder = cast(JsonResponder, json_response)
    if json_response is None:
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
        body = await request_json(request)
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
        body = await request_json(request)
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
