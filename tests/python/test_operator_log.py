"""Host operator_log: prefix, bars, debug gate, no stdout leak."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "lib"))

import operator_log as ol  # noqa: E402


def test_progress_enabled_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EZ_COMFY_PROGRESS", raising=False)
    assert ol.progress_enabled() is True
    monkeypatch.setenv("EZ_COMFY_PROGRESS", "0")
    assert ol.progress_enabled() is False


def test_progress_interval_parses(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EZ_COMFY_PROGRESS_INTERVAL", raising=False)
    assert ol.progress_interval_s() == 2.0
    monkeypatch.setenv("EZ_COMFY_PROGRESS_INTERVAL", "0")
    assert ol.progress_interval_s() == 0.0
    monkeypatch.setenv("EZ_COMFY_PROGRESS_INTERVAL", "nope")
    assert ol.progress_interval_s() == 2.0


def test_format_elapsed_and_bar_fill() -> None:
    assert ol.format_elapsed(0) == "0:00"
    assert ol.format_elapsed(90) == "1:30"
    assert ol.format_elapsed(3723) == "1:02:03"
    assert ol.bar_fill(0, 4) == "░░░░"
    assert ol.bar_fill(4, 4) == "▓▓▓▓"
    assert ol.bar_fill(2, 4) == "▓▓░░"


def test_emit_and_log_ok_go_to_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    ol.log("hello operator")
    ol.log_ok("done")
    ol.log_step(1, 4, "Klein 4B")
    ol.warn("careful")
    ol.error("boom")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("[ez-comfy] hello operator\n")
    assert "✓ done" in captured.err
    assert "══ 1/4 ══ Klein 4B" in captured.err
    assert "[WARN] careful" in captured.err
    assert "[ERROR] boom" in captured.err


def test_log_debug_silent_by_default(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("LAB_DEBUG", raising=False)
    monkeypatch.delenv("EZ_COMFY_LOG_LEVEL", raising=False)
    ol.log_debug("secret")
    assert capsys.readouterr().err == ""
    monkeypatch.setenv("EZ_COMFY_LOG_LEVEL", "debug")
    ol.log_debug("secret")
    assert "secret" in capsys.readouterr().err


def test_progress_bar_newline_when_not_tty(capsys: pytest.CaptureFixture[str]) -> None:
    ol.progress_bar(3, 7, "Klein 4B", "12 GiB")
    err = capsys.readouterr().err
    assert err.startswith("[ez-comfy]")
    assert "3/7" in err
    assert "Klein 4B" in err
    assert err.endswith("\n")


def test_heartbeat_newline(capsys: pytest.CaptureFixture[str]) -> None:
    ol.heartbeat("Blender dump", 0.0)
    err = capsys.readouterr().err
    assert "still running" in err
    assert "Blender dump" in err


def test_use_color_respects_no_color(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    assert ol.use_color() is False
