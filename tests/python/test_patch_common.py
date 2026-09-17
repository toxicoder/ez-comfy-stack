"""Shared Spark patch helpers (compile, newline splice, CLI)."""

from __future__ import annotations

import sys
from pathlib import Path

import patch_common as pc
import pytest


def test_compiles_module_and_snippet() -> None:
    assert pc.compiles("x = 1\n") is True
    assert pc.compiles("def broken(:\n") is False
    assert pc.compiles("    x = 1\n") is False
    assert pc.compiles("    x = 1\n", allow_indented_snippet=True) is True
    assert pc.compiles("def broken(:\n", allow_indented_snippet=True) is False


def test_consumed_and_newline() -> None:
    needle = "abc"
    assert pc.consumed_and_newline("abc\r\nX", needle, 0) == (needle + "\r\n", "\r\n")
    assert pc.consumed_and_newline("abc\nX", needle, 0) == (needle + "\n", "\n")
    assert pc.consumed_and_newline("abc", needle, 0) == (needle, "\n")


def test_cli_main_default_and_arg(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[Path] = []

    def _apply(root: Path) -> int:
        seen.append(root)
        return 0

    monkeypatch.setattr(sys, "argv", ["patch_common.py"])
    assert pc.cli_main(_apply, None) == 0
    assert seen[0] == Path(pc.DEFAULT_COMFY_ROOT)
    assert pc.cli_main(_apply, [str(tmp_path)]) == 0
    assert seen[1] == tmp_path
