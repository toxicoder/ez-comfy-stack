"""Structural interfaces for ez_* packs (PEP 544).

Behavioral seams use ``typing.Protocol``. JSON/YAML records stay TypedDict
in the owning pack. Classes do not need to inherit these; matching methods
are enough for mypy and Pyright.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, TypeAlias

ComfyInputTypes: TypeAlias = dict[str, Any]
"""ComfyUI ``INPUT_TYPES`` payload. Widget values stay ``Any``."""


class ProgressReporter(Protocol):
    """Comfy ProgressBar or :class:`ez_common.NullProgress`."""

    def update(self, n: int = 1) -> None:
        """Report a relative progress step.

        Args:
            n: Step count (Comfy ProgressBar API).
        """
        ...

    def update_absolute(self, value: int) -> None:
        """Report an absolute progress value.

        Args:
            value: Absolute step (Comfy ProgressBar API).
        """
        ...


class StatusSink(Protocol):
    """One-line operator status (stderr)."""

    def log(self, message: str) -> None:
        """Write a human status line without a trailing newline.

        Args:
            message: Status text after the pack prefix.
        """
        ...


class OccupancySource(Protocol):
    """Read the current occupancy mode string."""

    def read_mode(self) -> str:
        """Return the occupancy mode.

        Returns:
            Mode id, or ``unknown`` when the file is missing.
        """
        ...


class OccupancyPolicy(Protocol):
    """Allow or refuse a Queue given required vs current occupancy."""

    def allow(self, required: str, current: str) -> None:
        """Refuse a mismatch (raise) or no-op.

        Args:
            required: Heavy mode the graph needs.
            current: Mode from :meth:`OccupancySource.read_mode`.
        """
        ...


class CompletedProc(Protocol):
    """``subprocess.CompletedProcess``-shaped result (text mode)."""

    # Text-mode subprocess.run fields tests and ffmpeg callers read.
    returncode: int
    stdout: str
    stderr: str


class SubprocessRunner(Protocol):
    """``subprocess.run`` or a hermetic test double."""

    def __call__(
        self,
        argv: list[str],
        *,
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> CompletedProc:
        """Run ``argv`` and return a completed process.

        Args:
            argv: Command vector.
            check: Raise on non-zero (production ffmpeg paths use True).
            capture_output: Capture stdout/stderr.
            text: Decode as text.

        Returns:
            Completed process with ``returncode`` / ``stdout`` / ``stderr``.
        """
        ...


class ComfyNode(Protocol):
    """Structural Comfy custom-node contract (``NODE_CLASS_MAPPINGS`` values).

    Node classes stay plain; they satisfy this Protocol structurally. Do not
    inherit from it (Comfy registration uses class attributes, not ABCs).
    """

    # Comfy registry fields on every mapped node class.
    RETURN_TYPES: tuple[str, ...]
    FUNCTION: str
    CATEGORY: str

    @classmethod
    def INPUT_TYPES(cls) -> ComfyInputTypes:
        """Return widget specs.

        Returns:
            Comfy ``INPUT_TYPES`` mapping.
        """
        ...

    def run(self, *args: object, **kwargs: object) -> object:
        """Execute the node.

        Args:
            *args: Positional widget and socket values.
            **kwargs: Named widget values.

        Returns:
            Comfy return tuple or OUTPUT_NODE payload.
        """
        ...


class FileSystem(Protocol):
    """Narrow filesystem seam for jobstore / occupancy tests."""

    def is_file(self, path: Path) -> bool:
        """Return whether ``path`` is a file.

        Args:
            path: Candidate path.

        Returns:
            True when the path is a file.
        """
        ...

    def is_dir(self, path: Path) -> bool:
        """Return whether ``path`` is a directory.

        Args:
            path: Candidate path.

        Returns:
            True when the path is a directory.
        """
        ...

    def read_text(self, path: Path) -> str:
        """Read UTF-8 text.

        Args:
            path: File path.

        Returns:
            File contents.
        """
        ...

    def write_text(self, path: Path, text: str) -> None:
        """Write UTF-8 text.

        Args:
            path: File path.
            text: Contents.
        """
        ...
