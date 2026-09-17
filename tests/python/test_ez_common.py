"""ez_common ProgressBar helper is fail-soft and has no nodes."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Any, cast

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "custom_nodes"))

import ez_common as ec  # noqa: E402


def test_pack_has_no_nodes() -> None:
    assert ec.NODE_CLASS_MAPPINGS == {}
    assert ec.NODE_DISPLAY_NAME_MAPPINGS == {}
    payload: ec.ComfyInputTypes = {"required": {"x": ("STRING", {"default": ""})}}
    assert payload["required"]["x"][0] == "STRING"


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


def test_ensure_custom_nodes_path_inserts_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    custom = str(ROOT / "custom_nodes")
    monkeypatch.setattr(sys, "path", [p for p in sys.path if p != custom])
    first = ec.ensure_custom_nodes_path()
    assert first == ROOT / "custom_nodes"
    assert sys.path[0] == custom
    again = ec.ensure_custom_nodes_path(anchor=ROOT / "custom_nodes" / "ez_common")
    assert again == first
    assert sys.path.count(custom) == 1
    packed = ec.ensure_custom_nodes_path(
        anchor=ROOT / "custom_nodes" / "ez_common" / "__init__.py"
    )
    assert packed == first


def test_ensure_custom_nodes_path_falls_back_outside_tree(tmp_path: Path) -> None:
    outside = tmp_path / "not-custom" / "nested"
    outside.mkdir(parents=True)
    root = ec.ensure_custom_nodes_path(anchor=outside)
    assert root == ROOT / "custom_nodes"


def test_node_log_sink_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    sink = ec.NodeLogSink("ez_dub")
    sink.log("ASR 3/12")
    captured = capsys.readouterr()
    assert captured.err == "[ez_dub] ASR 3/12\n"


def _invoke_protocol(owner: object, name: str, *args: object, **kwargs: object) -> None:
    """Call a Protocol ellipsis body (coverage). Typed as Any to avoid ABC errors.

    Args:
        owner: Protocol class.
        name: Method name.
        *args: Bound-self plus positional args.
        **kwargs: Keyword args.
    """
    cast(Any, getattr(owner, name))(*args, **kwargs)


def test_protocol_stubs_execute() -> None:
    """Call Protocol ellipsis bodies so coverage stays at 100%."""
    bar = ec.NullProgress()
    _invoke_protocol(ec.ProgressReporter, "update", bar, 1)
    _invoke_protocol(ec.ProgressReporter, "update_absolute", bar, 0)
    sink = ec.NodeLogSink("ez_test")
    _invoke_protocol(ec.StatusSink, "log", sink, "ok")

    class _Occ:
        def read_mode(self) -> str:
            return "idle"

    _invoke_protocol(ec.OccupancySource, "read_mode", _Occ())

    class _Pol:
        def allow(self, required: str, current: str) -> None:
            return None

    _invoke_protocol(ec.OccupancyPolicy, "allow", _Pol(), "klein", "klein")

    class _Proc:
        returncode = 0
        stdout = ""
        stderr = ""

    class _Run:
        def __call__(
            self,
            argv: list[str],
            *,
            check: bool,
            capture_output: bool,
            text: bool,
        ) -> _Proc:
            del argv, check, capture_output, text
            return _Proc()

    _invoke_protocol(
        ec.SubprocessRunner,
        "__call__",
        _Run(),
        ["true"],
        check=False,
        capture_output=True,
        text=True,
    )

    class _FS:
        def is_file(self, path: Path) -> bool:
            del path
            return False

        def is_dir(self, path: Path) -> bool:
            del path
            return False

        def read_text(self, path: Path) -> str:
            del path
            return ""

        def write_text(self, path: Path, text: str) -> None:
            del path, text

    fs = _FS()
    here = Path(".")
    _invoke_protocol(ec.FileSystem, "is_file", fs, here)
    _invoke_protocol(ec.FileSystem, "is_dir", fs, here)
    _invoke_protocol(ec.FileSystem, "read_text", fs, here)
    _invoke_protocol(ec.FileSystem, "write_text", fs, here, "x")

    class _Node:
        RETURN_TYPES: tuple[str, ...] = ("STRING",)
        FUNCTION: str = "run"
        CATEGORY: str = "ez-comfy"

        @classmethod
        def INPUT_TYPES(cls) -> dict[str, object]:
            return {}

        def run(self, *args: object, **kwargs: object) -> object:
            del args, kwargs
            return ()

    _invoke_protocol(ec.ComfyNode, "INPUT_TYPES")
    _invoke_protocol(ec.ComfyNode, "run", _Node())


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
