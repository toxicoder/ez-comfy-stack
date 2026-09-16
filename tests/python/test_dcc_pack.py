"""Hermetic decode_png and path helpers for ez_dcc.pack."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_dcc import pack as dcc_pack  # noqa: E402


class _Arr:
    def __init__(self, shape: tuple[int, ...]) -> None:
        self.shape = shape

    def __getitem__(self, _idx: object) -> _Arr:
        if self.shape[-1:] == (4,):
            return _Arr(self.shape[:-1] + ((3,) if True else ()))
        return _Arr(self.shape[:2] if len(self.shape) > 2 else self.shape)

    def __truediv__(self, _other: object) -> _Arr:
        return self


class _Image:
    def __init__(self, mode: str, *, transparent: bool = False) -> None:
        self.mode = mode
        self.info = {"transparency": 1} if transparent else {}

    def convert(self, mode: str) -> _Image:
        return _Image(mode)


class _Torch:
    @staticmethod
    def from_numpy(_arr: object) -> _TorchTensor:
        return _TorchTensor()


class _TorchTensor:
    def __getitem__(self, _idx: object) -> _TorchTensor:
        return self


def _install_fakes(monkeypatch: pytest.MonkeyPatch, mode: str, *, transparent: bool = False) -> None:
    fake_np = types.ModuleType("numpy")
    fake_np.float32 = "f4"  # type: ignore[attr-defined]

    def asarray(_img: object, dtype: object = None) -> _Arr:
        channels = 4 if mode in {"RGBA", "LA"} or transparent else 3
        return _Arr((4, 4, channels))

    def ones(shape: tuple[int, ...], dtype: object = None) -> _Arr:
        return _Arr(shape)

    fake_np.asarray = asarray  # type: ignore[attr-defined]
    fake_np.ones = ones  # type: ignore[attr-defined]
    fake_pil = types.ModuleType("PIL")
    fake_image_mod = types.ModuleType("PIL.Image")

    def open(_path: object) -> _Image:
        return _Image(mode, transparent=transparent)

    fake_image_mod.open = open  # type: ignore[attr-defined]
    fake_pil.Image = fake_image_mod  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "numpy", fake_np)
    monkeypatch.setitem(sys.modules, "PIL", fake_pil)
    monkeypatch.setitem(sys.modules, "PIL.Image", fake_image_mod)
    monkeypatch.setitem(sys.modules, "torch", _Torch)


def test_path_helpers_and_unknown_layers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", str(tmp_path))
    shot = dcc_pack.shot_dir("go-see", "12")
    assert shot == tmp_path / "guides" / "go-see" / "12"
    still = dcc_pack.still_dir("go-see", "mug")
    assert "stills" in still.as_posix()
    assert dcc_pack.camera_json_path("go-see", "12").name == "camera.json"
    pack = tmp_path / "pack"
    (pack / "depth").mkdir(parents=True)
    (pack / "depth" / "0001.png").write_bytes(b"x")
    (pack / "canny").mkdir()
    (pack / "canny" / "0001.png").write_bytes(b"y")
    assert dcc_pack.shot_still_path(pack, "first").name == "first.png"
    assert dcc_pack.shot_still_path(pack, "clay").name == "first.png"
    assert dcc_pack.shot_still_path(pack, "last").name == "last.png"
    assert dcc_pack.shot_still_path(pack, "depth").name == "0001.png"
    assert dcc_pack.shot_still_path(pack, "canny").name == "0001.png"
    with pytest.raises(ValueError, match="unknown shot still"):
        dcc_pack.shot_still_path(pack, "normal")
    assert dcc_pack.shot_video_path(pack, "clay").name == "clay.mp4"
    with pytest.raises(ValueError, match="unknown shot video"):
        dcc_pack.shot_video_path(pack, "rgb")
    assert dcc_pack.still_pack_path(pack, "rgb").name == "first.png"
    assert dcc_pack.still_pack_path(pack, "depth").name == "depth.png"
    with pytest.raises(ValueError, match="unknown still pack"):
        dcc_pack.still_pack_path(pack, "clay")


def test_decode_png_rgb_and_rgba(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    png = tmp_path / "x.png"
    png.write_bytes(b"fake")
    _install_fakes(monkeypatch, "RGB")
    image, mask = dcc_pack.decode_png(png)
    assert image is not None and mask is not None
    _install_fakes(monkeypatch, "RGBA")
    image, mask = dcc_pack.decode_png(png)
    assert image is not None and mask is not None
    _install_fakes(monkeypatch, "P", transparent=True)
    image, mask = dcc_pack.decode_png(png)
    assert image is not None and mask is not None


def test_output_directory_folder_paths_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("COMFY_OUTPUT_DIR", raising=False)
    fake_common = types.ModuleType("ez_common")

    def boom(_default: str = "") -> Path:
        raise RuntimeError("no comfy")

    fake_common.output_root = boom  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "ez_common", fake_common)
    fake_fp = types.ModuleType("folder_paths")
    fake_fp.get_output_directory = lambda: "/from-folder-paths"  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "folder_paths", fake_fp)
    assert dcc_pack.output_directory() == Path("/from-folder-paths")
    monkeypatch.delitem(sys.modules, "folder_paths", raising=False)
    assert dcc_pack.output_directory() == Path("/outputs")


def test_output_directory_env_when_ez_common_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("COMFY_OUTPUT_DIR", "/from-env")
    fake_common = types.ModuleType("ez_common")

    def boom(_default: str = "") -> Path:
        raise RuntimeError("no comfy")

    fake_common.output_root = boom  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "ez_common", fake_common)
    assert dcc_pack.output_directory() == Path("/from-env")


def test_shot_still_png_fallbacks(tmp_path: Path) -> None:
    pack = tmp_path / "pack"
    pack.mkdir()
    assert dcc_pack.shot_still_path(pack, "depth").name == "depth.png"
    assert dcc_pack.shot_still_path(pack, "canny").name == "canny.png"
