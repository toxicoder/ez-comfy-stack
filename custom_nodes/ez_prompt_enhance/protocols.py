"""Prompt-enhance behavioral seams (PEP 544).

Caches and monkeypatch targets stay on :mod:`ez_prompt_enhance.client`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeAlias

if TYPE_CHECKING:
    import llama_cpp

LlamaModel: TypeAlias = "llama_cpp.Llama"
"""Process-cached llama.cpp handle held by :class:`ez_prompt_enhance.client`."""


class ChatCompleter(Protocol):
    """Sidecar or local GGUF chat completion."""

    def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 800,
        unload: bool = False,
    ) -> tuple[str, str | None]:
        """Generate one rewrite.

        Args:
            system: System prompt.
            user: User message.
            max_tokens: Decode cap.
            unload: Drop the local GGUF after this call.

        Returns:
            ``(text, reason)``. ``reason`` is a passthrough token on failure.
        """
        ...


class SidecarTransport(Protocol):
    """OpenAI-compatible HTTP POST used by the 35B sidecar."""

    def urlopen(self, request: object, timeout: float) -> object:
        """POST one chat completion.

        Args:
            request: ``urllib.request.Request``.
            timeout: Seconds.

        Returns:
            Response with ``read()`` / ``__enter__``.
        """
        ...


class StyleCatalog(Protocol):
    """``styles.json`` look catalog."""

    def ids(self) -> list[str]:
        """Return combo choices (``none`` first).

        Returns:
            Style ids.
        """
        ...

    def apply(self, text: str, style_id: str) -> str:
        """Restyle CLIP text.

        Args:
            text: Source or rewriter prompt.
            style_id: Catalog id or ``none``.

        Returns:
            Restyled prompt.
        """
        ...


class SystemPrompts(Protocol):
    """Family system-prompt files under ``prompts/``."""

    def load(self, name: str) -> str:
        """Load a stem.

        Args:
            name: File stem without ``.txt``.

        Returns:
            Prompt text.
        """
        ...


class LlamaLoader(Protocol):
    """Process-cached llama.cpp GGUF loader."""

    def get(self) -> tuple[LlamaModel | None, str | None]:
        """Return the cached Llama or a fail-soft reason.

        Returns:
            ``(model, reason)``. ``model`` is None on passthrough.
        """
        ...
