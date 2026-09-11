"""ez_common ProgressBar helper is fail-soft and has no nodes."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "custom_nodes"))

import ez_common as ec  # noqa: E402


def test_pack_has_no_nodes() -> None:
    assert ec.NODE_CLASS_MAPPINGS == {}
    assert ec.NODE_DISPLAY_NAME_MAPPINGS == {}


def test_null_progress_is_noop() -> None:
    bar = ec.NullProgress()
    bar.update(1)
    bar.update_absolute(3)


def test_node_progress_without_comfy_is_null() -> None:
    bar = ec.node_progress(4)
    assert isinstance(bar, ec.NullProgress)
    bar.update(1)


def test_node_log_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    ec.node_log("ez_dub", "ASR 3/12")
    captured = capsys.readouterr()
    assert captured.err == "[ez_dub] ASR 3/12\n"
    assert captured.out == ""
