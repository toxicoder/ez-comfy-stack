"""JSON / YAML value vocabulary for every parse boundary.

Anything that enters this repo from disk or the wire - ``json.loads``, the
restricted-YAML readers, an MCP request, a Comfy graph file - is one of
these until a parser narrows it to a record ``TypedDict`` in the owning
pack. Aliases cost nothing at runtime and they are what keeps ``Any`` out
of a parser signature: ``json.loads`` returns :data:`Json`, never ``Any``.

The aliases are recursive on purpose. A document is a tree, and a reader
that walks it should narrow one level at a time with ``isinstance`` rather
than give up and call the node ``Any``.

Two read-only spellings take the place of ``Mapping[str, object]`` and
``Sequence[object]`` in a reader signature: :data:`JsonMap` and
:data:`JsonList`. They say "a parsed object whose leaves are still unknown"
instead of "anything at all", and because ``Mapping`` and ``Sequence`` are
covariant a caller holding ``dict[str, str]`` still satisfies them.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypeAlias

JsonScalar: TypeAlias = str | int | float | bool | None
"""A single JSON / YAML scalar."""

Json: TypeAlias = "JsonScalar | list[Json] | dict[str, Json]"
"""Any value reachable from a parsed JSON or restricted-YAML document."""

JsonObject: TypeAlias = dict[str, Json]
"""A parsed document whose top level is an object (the mutable form a builder writes)."""

JsonMap: TypeAlias = Mapping[str, Json]
"""A parsed object read through the read-only view.

This is the type a reader or a validator takes: the caller may hold a
``dict[str, str]`` or a ``dict[str, Json]`` and both satisfy it, which a
``dict[str, object]`` parameter does not. Reach for this before ``object``
whenever the value came from a parser and only its leaves are unknown.
"""

JsonArray: TypeAlias = list[Json]
"""A parsed document whose top level is an array."""

JsonList: TypeAlias = Sequence[Json]
"""A parsed array read through the read-only view."""

__all__ = [
    "Json",
    "JsonArray",
    "JsonList",
    "JsonMap",
    "JsonObject",
    "JsonScalar",
]
