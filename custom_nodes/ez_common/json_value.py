"""JSON / YAML value vocabulary for every parse boundary.

Anything that enters this repo from disk or the wire - ``json.loads``, the
restricted-YAML readers, an MCP request, a Comfy graph file - is one of
these until a parser narrows it to a record ``TypedDict`` in the owning
pack. Aliases cost nothing at runtime and they are what keeps ``Any`` out
of a parser signature: ``json.loads`` returns :data:`Json`, never ``Any``.

The aliases are recursive on purpose. A document is a tree, and a reader
that walks it should narrow one level at a time with ``isinstance`` rather
than give up and call the node ``Any``.
"""

from __future__ import annotations

from typing import TypeAlias

JsonScalar: TypeAlias = str | int | float | bool | None
"""A single JSON / YAML scalar."""

Json: TypeAlias = "JsonScalar | list[Json] | dict[str, Json]"
"""Any value reachable from a parsed JSON or restricted-YAML document."""

JsonObject: TypeAlias = dict[str, Json]
"""A parsed document whose top level is an object."""

JsonArray: TypeAlias = list[Json]
"""A parsed document whose top level is an array."""

__all__ = [
    "Json",
    "JsonArray",
    "JsonObject",
    "JsonScalar",
]
