"""ez_common ProgressBar helper is fail-soft and has no nodes."""

from __future__ import annotations

import sys
import types
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
    tiny = ec.node_progress(-1)
    assert isinstance(tiny, ec.NullProgress)
    zero = ec.node_progress(0)
    assert isinstance(zero, ec.NullProgress)


def test_node_log_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    ec.node_log("ez_dub", "ASR 3/12")
    captured = capsys.readouterr()
    assert captured.err == "[ez_dub] ASR 3/12\n"
    assert captured.out == ""


def test_output_root_prefers_folder_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = types.SimpleNamespace(get_output_directory=lambda: "/comfy/output")
    monkeypatch.setitem(sys.modules, "folder_paths", fake)
    assert ec.output_root() == Path("/comfy/output")


def test_output_root_prefers_container_outputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", "/mnt/comfy-output")
    monkeypatch.delenv("COMFY_OUTPUT", raising=False)
    sys.modules.pop("folder_paths", None)
    original = Path.is_dir

    def fake_is_dir(self: Path) -> bool:
        if str(self) == "/outputs":
            return True
        return original(self)

    monkeypatch.setattr(Path, "is_dir", fake_is_dir)
    assert ec.output_root() == Path("/outputs")


def test_output_root_uses_existing_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    monkeypatch.delenv("COMFY_OUTPUT", raising=False)
    sys.modules.pop("folder_paths", None)
    original = Path.is_dir

    def fake_is_dir(self: Path) -> bool:
        if str(self) == "/outputs":
            return False
        return original(self)

    monkeypatch.setattr(Path, "is_dir", fake_is_dir)
    assert ec.output_root() == tmp_path


def test_output_root_default_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COMFY_OUTPUT_DIR", raising=False)
    monkeypatch.delenv("COMFY_OUTPUT", raising=False)
    sys.modules.pop("folder_paths", None)
    original = Path.is_dir

    def fake_is_dir(self: Path) -> bool:
        if str(self) == "/outputs":
            return False
        return original(self)

    monkeypatch.setattr(Path, "is_dir", fake_is_dir)
    assert ec.output_root() == Path("/mnt/comfy-output")
    assert ec.output_root(default="/outputs") == Path("/outputs")
    assert ec.output_root(default=None) == Path("/mnt/comfy-output")


def test_node_progress_zero_total_clamps_to_one() -> None:
    bar = ec.node_progress(0)
    assert isinstance(bar, ec.NullProgress)
    bar.update(1)


def test_node_progress_uses_comfy_progress_bar(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, int] = {}

    class _ProgressBar:
        def __init__(self, total: int) -> None:
            seen["total"] = total

        def update(self, n: int = 1) -> None:
            seen["n"] = n

    comfy = types.ModuleType("comfy")
    utils = types.ModuleType("comfy.utils")
    utils.ProgressBar = _ProgressBar  # type: ignore[attr-defined]
    comfy.utils = utils  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "comfy", comfy)
    monkeypatch.setitem(sys.modules, "comfy.utils", utils)
    bar = ec.node_progress(4)
    assert isinstance(bar, _ProgressBar)
    assert seen["total"] == 4
    bar.update(2)
    assert seen["n"] == 2
