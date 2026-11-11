"""Hermetic tests for the EZCutout BiRefNet pre-pass.

Stdlib only. No Comfy, torch, transformers, Docker, or GPU: every inference
import is faked, and every fail-soft path is asserted to hand the operator the
input image back with a status that says why.
"""

from __future__ import annotations

import sys
import types
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_image import cutout  # noqa: E402


def _image(height: int = 3, width: int = 4, channels: int = 3) -> list[list[list[float]]]:
    """Build a small HWC float image.

    Args:
        height: Rows.
        width: Columns.
        channels: Channels per pixel.

    Returns:
        HWC nested lists in 0..1.
    """
    return [
        [[(x + c) / 10.0 for c in range(channels)] for x in range(width)]
        for _ in range(height)
    ]


@pytest.fixture(autouse=True)
def _clean_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear the cached model, the cooldown, and every cutout env var."""
    cutout.reset_cutout_model()
    for name in (
        "EZ_CUTOUT",
        "EZ_CUTOUT_MODEL_DIR",
        "MODELS_ROOT",
        "MODELS_DIR",
    ):
        monkeypatch.delenv(name, raising=False)


# ---------------------------------------------------------------------------
# Node contract
# ---------------------------------------------------------------------------


def test_node_contract_matches_the_pack_convention() -> None:
    """Sockets, returns, and registries are what Comfy and the gates expect."""
    node = cutout.EZCutout
    assert node.RETURN_TYPES == ("IMAGE", "IMAGE", "MASK")
    assert node.RETURN_NAMES == ("image", "matte", "mask")
    assert node.FUNCTION == "run"
    assert node.CATEGORY == "ez-comfy/image"
    assert node.OUTPUT_NODE is False
    assert node.DESCRIPTION
    required = node.INPUT_TYPES()["required"]
    assert list(required) == ["image", "backdrop", "dilate", "feather"]
    assert required["backdrop"][0] == list(cutout.BACKDROPS)
    assert cutout.NODE_CLASS_MAPPINGS == {"EZCutout": cutout.EZCutout}
    assert cutout.NODE_DISPLAY_NAME_MAPPINGS == {
        "EZCutout": "Cut out subject (BiRefNet)"
    }


def test_ez_image_pack_exports_the_cutout_class() -> None:
    """The barrel merges the new module, which the node-type gate requires."""
    import ez_image

    assert "EZCutout" in ez_image.NODE_CLASS_MAPPINGS
    assert "EZCutout" in ez_image.NODE_DISPLAY_NAME_MAPPINGS


def test_run_reports_status_and_three_results() -> None:
    """``run`` returns ui.text plus the (image, matte, mask) triple."""
    image = _image()
    out = cutout.EZCutout().run(image)
    assert out["ui"]["text"] == (cutout.REASON_NO_MODEL,)
    assert len(out["result"]) == 3
    assert out["result"][0] is image


# ---------------------------------------------------------------------------
# Kill switch and model roots
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [("0", True), ("off", True), ("FALSE", True), (" No ", True), ("1", False), ("", False)],
)
def test_cutout_disabled_reads_the_kill_switch(
    monkeypatch: pytest.MonkeyPatch, value: str, expected: bool
) -> None:
    """``EZ_CUTOUT`` off-values disable the pre-pass."""
    monkeypatch.setenv("EZ_CUTOUT", value)
    assert cutout.cutout_disabled() is expected


def test_cutout_roots_prefers_env_then_falls_back(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Both env names are consulted, then the container and host fallbacks."""
    monkeypatch.setenv("MODELS_ROOT", str(tmp_path / "a"))
    monkeypatch.setenv("MODELS_DIR", str(tmp_path / "b"))
    roots = cutout.cutout_roots()
    assert roots[:2] == [str(tmp_path / "a"), str(tmp_path / "b")]
    assert roots.count("/models") == 1
    assert "/mnt/models" in roots


def test_cutout_roots_drops_an_env_that_matches_a_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An env var set to a fallback path does not duplicate it."""
    monkeypatch.setenv("MODELS_ROOT", "/models")
    assert cutout.cutout_roots() == ["/models", "/mnt/models"]


def test_model_dir_honours_the_operator_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """``EZ_CUTOUT_MODEL_DIR`` wins over the pack layout."""
    monkeypatch.setenv("EZ_CUTOUT_MODEL_DIR", str(tmp_path / "mine"))
    assert cutout.model_dir() == str(tmp_path / "mine")


def test_model_dir_defaults_to_the_first_root(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without an override the first root's tier_dir is preferred."""
    monkeypatch.setenv("MODELS_ROOT", "/models")
    assert cutout.model_dir() == f"/models/{cutout.MODEL_SUBDIR}"


def test_dir_in_uses_the_manifest_tier_dir() -> None:
    """The probe path matches the manifest ``tier_dir`` byte for byte."""
    assert cutout.MODEL_SUBDIR == "ZhengPeng7__BiRefNet_birefnet"
    assert cutout._dir_in("/models") == "/models/ZhengPeng7__BiRefNet_birefnet"


# ---------------------------------------------------------------------------
# Readiness probes
# ---------------------------------------------------------------------------


def test_file_ready(tmp_path: Path) -> None:
    """Only a non-empty real file counts as ready."""
    missing = tmp_path / "nope"
    empty = tmp_path / "empty"
    full = tmp_path / "full"
    empty.write_bytes(b"")
    full.write_bytes(b"x")
    assert cutout._file_ready(str(missing)) is False
    assert cutout._file_ready(str(empty)) is False
    assert cutout._file_ready(str(full)) is True


def test_file_ready_survives_an_os_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A stat failure reports not-ready rather than raising."""
    target = tmp_path / "full"
    target.write_bytes(b"x")

    def boom(_path: str) -> int:
        raise OSError("stat failed")

    monkeypatch.setattr("os.path.getsize", boom)
    assert cutout._file_ready(str(target)) is False


def _seed_pack(folder: Path, skip: str | None = None) -> None:
    """Write every pack file except ``skip``.

    Args:
        folder: Directory to fill.
        skip: Name to leave out.
    """
    folder.mkdir(parents=True, exist_ok=True)
    for name in cutout.MODEL_FILES:
        if name != skip:
            (folder / name).write_bytes(b"data")


def test_dir_ready_needs_every_file(tmp_path: Path) -> None:
    """A partial pack is not loadable: the loader needs the remote-code files."""
    good = tmp_path / "good"
    _seed_pack(good)
    assert cutout._dir_ready(str(good)) is True
    partial = tmp_path / "partial"
    _seed_pack(partial, skip="birefnet.py")
    assert cutout._dir_ready(str(partial)) is False


def test_ready_model_dir_probes_roots(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The first root holding a complete pack is returned."""
    other = tmp_path / "other"
    root = tmp_path / "good"
    _seed_pack(root / cutout.MODEL_SUBDIR)
    monkeypatch.setenv("MODELS_ROOT", str(other))
    monkeypatch.setenv("MODELS_DIR", str(root))
    assert cutout.ready_model_dir() == cutout._dir_in(str(root))


def test_ready_model_dir_uses_the_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An override directory is probed on its own."""
    _seed_pack(tmp_path)
    monkeypatch.setenv("EZ_CUTOUT_MODEL_DIR", str(tmp_path))
    assert cutout.ready_model_dir() == str(tmp_path)


def test_ready_model_dir_returns_none_when_nothing_is_installed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """No pack anywhere means no load attempt."""
    monkeypatch.setenv("MODELS_ROOT", str(tmp_path / "missing"))
    assert cutout.ready_model_dir() is None


# ---------------------------------------------------------------------------
# Self-serve download
# ---------------------------------------------------------------------------


def test_download_writes_a_non_empty_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A successful fetch leaves a ready file."""
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(b"payload"))
    dest = tmp_path / "sub" / "model.safetensors"
    assert cutout._download("https://example/model.safetensors", str(dest)) is True
    assert dest.read_bytes() == b"payload"


def test_download_rejects_an_empty_body(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A zero-length body is not a usable weight."""
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen(b""))
    dest = tmp_path / "model.safetensors"
    assert cutout._download("https://example/model.safetensors", str(dest)) is False


def test_download_swallows_a_network_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A raised network error becomes False, not a traceback."""

    def boom(*_args: object, **_kwargs: object) -> object:
        raise OSError("network down")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    dest = tmp_path / "model.safetensors"
    assert cutout._download("https://example/model.safetensors", str(dest)) is False


class _FakeResponse:
    """Context-managed stand-in for a urllib response."""

    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *_exc: object) -> None:
        return None

    def read(self) -> bytes:
        """Return the body."""
        return self._payload


def _fake_urlopen(payload: bytes):
    """Build a urlopen stub returning ``payload``.

    Args:
        payload: Bytes the fake response yields.

    Returns:
        A callable matching urlopen's call sites.
    """

    def _open(*_args: object, **_kwargs: object) -> _FakeResponse:
        return _FakeResponse(payload)

    return _open


def test_download_model_fetches_every_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A writable root gets the whole pack in one pass."""
    monkeypatch.setenv("MODELS_ROOT", str(tmp_path))
    seen: list[str] = []

    def spy(url: str, dest: str) -> bool:
        seen.append(url)
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        Path(dest).write_bytes(b"x")
        return True

    monkeypatch.setattr(cutout, "_download", spy)
    assert cutout.download_model() is True
    assert len(seen) == len(cutout.MODEL_FILES)
    assert all(url.startswith(cutout.MODEL_URL_BASE) for url in seen)


def test_download_model_skips_files_it_already_has(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An installed file is not refetched."""
    folder = tmp_path / cutout.MODEL_SUBDIR
    _seed_pack(folder, skip="config.json")
    monkeypatch.setenv("MODELS_ROOT", str(tmp_path))
    seen: list[str] = []

    def spy(url: str, dest: str) -> bool:
        seen.append(url)
        Path(dest).write_bytes(b"x")
        return True

    monkeypatch.setattr(cutout, "_download", spy)
    assert cutout.download_model() is True
    assert seen == [f"{cutout.MODEL_URL_BASE}/config.json"]


def test_download_model_gives_up_on_a_failed_fetch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """One failed file aborts the pack rather than leaving it half-built."""
    monkeypatch.setenv("MODELS_ROOT", str(tmp_path))
    monkeypatch.setattr(cutout, "_download", lambda url, dest: False)
    assert cutout.download_model() is False


def test_download_model_skips_an_unwritable_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A root that cannot be written is passed over, then nothing lands."""
    monkeypatch.setenv("MODELS_ROOT", str(tmp_path / "nope"))
    monkeypatch.setattr(cutout.os, "access", lambda *_args, **_kw: False)
    assert cutout.download_model() is False


def test_download_model_survives_an_unmakeable_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A root whose directory cannot be created is skipped, not fatal."""
    monkeypatch.setenv("MODELS_ROOT", str(tmp_path / "nope"))

    def boom(*_args: object, **_kwargs: object) -> None:
        raise OSError("read-only")

    monkeypatch.setattr(cutout.os, "makedirs", boom)
    assert cutout.download_model() is False


# ---------------------------------------------------------------------------
# Lazy dependency import
# ---------------------------------------------------------------------------


def test_cutout_tools_returns_none_without_torch(monkeypatch: pytest.MonkeyPatch) -> None:
    """A host with no torch cannot run inference, and says so by returning None."""
    import builtins

    real_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name in {"torch", "numpy"}:
            raise ImportError(name)
        return real_import(name, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert cutout._cutout_tools() is None


def test_cutout_tools_returns_modules_when_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fake torch/numpy are handed back for the inference path."""
    monkeypatch.setitem(sys.modules, "torch", types.ModuleType("torch"))
    monkeypatch.setitem(sys.modules, "numpy", types.ModuleType("numpy"))
    tools = cutout._cutout_tools()
    assert tools is not None
    assert tools[0].__name__ == "torch"


# ---------------------------------------------------------------------------
# Model load, fail-soft on every path
# ---------------------------------------------------------------------------


def test_load_model_uses_the_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """A loaded model is reused without probing anything."""
    sentinel = object()
    monkeypatch.setattr(cutout, "_MODEL", sentinel)
    assert cutout.load_model() is sentinel


def test_load_model_respects_the_kill_switch(monkeypatch: pytest.MonkeyPatch) -> None:
    """With the switch off nothing is loaded, even with a pack on disk."""
    monkeypatch.setenv("EZ_CUTOUT", "0")
    assert cutout.load_model() is None


def test_load_model_honours_the_miss_cooldown(monkeypatch: pytest.MonkeyPatch) -> None:
    """A recent failure is not retried on every Queue."""
    monkeypatch.setattr(cutout, "_LAST_MISS_S", cutout.time.monotonic())
    monkeypatch.setattr(cutout, "_cutout_tools", lambda: (object(), object()))
    assert cutout.load_model() is None


def test_load_model_without_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    """No torch means no model and a stamped cooldown."""
    monkeypatch.setattr(cutout, "_cutout_tools", lambda: None)
    assert cutout.load_model() is None
    assert cutout._LAST_MISS_S is not None


def test_load_model_without_weights_and_a_failed_download(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No pack and no network means fail-soft."""
    monkeypatch.setattr(cutout, "_cutout_tools", lambda: (object(), object()))
    monkeypatch.setattr(cutout, "ready_model_dir", lambda: None)
    monkeypatch.setattr(cutout, "download_model", lambda: False)
    assert cutout.load_model() is None


def test_load_model_when_a_download_lies_about_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A download that claims success but leaves no pack still fails soft."""
    monkeypatch.setattr(cutout, "_cutout_tools", lambda: (object(), object()))
    monkeypatch.setattr(cutout, "ready_model_dir", lambda: None)
    monkeypatch.setattr(cutout, "download_model", lambda: True)
    assert cutout.load_model() is None
    assert cutout._LAST_MISS_S is not None


def test_load_model_builds_the_remote_code_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The documented ``trust_remote_code`` path is the one used."""
    built: dict[str, object] = {}

    class _Model:
        def eval(self) -> None:
            """Mark eval mode."""
            built["evalled"] = True

    class _Auto:
        @staticmethod
        def from_pretrained(path: str, **kwargs: object) -> _Model:
            built["path"] = path
            built["kwargs"] = kwargs
            return _Model()

    module = types.ModuleType("transformers")
    module.AutoModelForImageSegmentation = _Auto  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "transformers", module)
    monkeypatch.setattr(cutout, "_cutout_tools", lambda: (object(), object()))
    monkeypatch.setattr(cutout, "ready_model_dir", lambda: "/models/pack")
    model = cutout.load_model()
    assert isinstance(model, _Model)
    assert built == {"path": "/models/pack", "kwargs": {"trust_remote_code": True}, "evalled": True}
    assert cutout._MODEL is model
    cutout.reset_cutout_model()


def test_load_model_swallows_a_broken_checkpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A checkpoint that cannot build returns None, never an exception."""

    class _Auto:
        @staticmethod
        def from_pretrained(*_args: object, **_kwargs: object) -> object:
            raise RuntimeError("corrupt safetensors")

    module = types.ModuleType("transformers")
    module.AutoModelForImageSegmentation = _Auto  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "transformers", module)
    monkeypatch.setattr(cutout, "_cutout_tools", lambda: (object(), object()))
    monkeypatch.setattr(cutout, "ready_model_dir", lambda: "/models/pack")
    assert cutout.load_model() is None
    assert cutout._LAST_MISS_S is not None


# ---------------------------------------------------------------------------
# Preprocess, output decoding, geometry
# ---------------------------------------------------------------------------


def test_preprocess_normalises_to_the_model_canvas() -> None:
    """The card's 1024 canvas and ImageNet stats are applied per channel."""
    chw = cutout._preprocess(_image(height=2, width=2), 4)
    assert len(chw) == 3
    assert len(chw[0]) == 4 and len(chw[0][0]) == 4
    first = _image(height=2, width=2)[0][0][0]
    assert chw[0][0][0] == pytest.approx((first - cutout.IMAGENET_MEAN[0]) / cutout.IMAGENET_STD[0])


def test_preprocess_tolerates_an_empty_image() -> None:
    """Zero-size input yields a canvas of mean-subtracted zeros, not a crash."""
    chw = cutout._preprocess([], 2)
    assert len(chw) == 3 and len(chw[0]) == 2


def test_as_grid_unwraps_a_nested_batch() -> None:
    """A [1,1,H,W] list collapses to H,W."""
    assert cutout._as_grid([[[[1.0, 2.0], [3.0, 4.0]]]]) == [[1.0, 2.0], [3.0, 4.0]]


def test_as_grid_accepts_a_tensor_like() -> None:
    """detach/cpu/tolist are followed before the shape test."""

    class _T:
        def detach(self) -> "_T":
            return self

        def cpu(self) -> "_T":
            return self

        def tolist(self) -> list[list[float]]:
            return [[0.5, 0.25]]

    assert cutout._as_grid(_T()) == [[0.5, 0.25]]


def test_as_grid_rejects_a_flat_list() -> None:
    """A 1D sequence is not a map."""
    assert cutout._as_grid([1.0, 2.0]) == []


def test_as_grid_rejects_the_empty_thing() -> None:
    """Nothing in, nothing out."""
    assert cutout._as_grid(None) == []


def test_as_grid_rejects_a_ragged_map() -> None:
    """Only the first row is shape-checked, so a later non-row must not crash."""
    assert cutout._as_grid([[0.5, 0.25], "not a row"]) == []


def test_as_grid_rejects_a_non_numeric_cell() -> None:
    """A stray string or a bool is not alpha, and the whole map is dropped."""
    assert cutout._as_grid([[0.5, "hot"]]) == []
    assert cutout._as_grid([[True, 0.25]]) == []


def test_to_mask_sigmoids_the_last_logit_map() -> None:
    """BiRefNet hands back logits; the card's sigmoid is applied here."""
    import math

    mask = cutout._to_mask([[[0.0, 2.0]]], 1, 2)
    assert mask[0][0] == pytest.approx(0.5)
    assert mask[0][1] == pytest.approx(1.0 / (1.0 + math.exp(-2.0)))


def test_to_mask_takes_the_last_entry_of_a_pyramid() -> None:
    """The final entry is the full-resolution prediction."""
    mask = cutout._to_mask([[[9.0]], [[1.0, -1.0]]], 1, 2)
    assert mask[0][0] > 0.5
    assert mask[0][1] < 0.5


def test_to_mask_on_an_unreadable_output() -> None:
    """A garbage model output yields a blank matte of the right shape."""
    mask = cutout._to_mask(None, 2, 3)
    assert len(mask) == 2 and len(mask[0]) == 3
    assert all(value == 0.0 for row in mask for value in row)


def test_subject_ratio() -> None:
    """The mean alpha is the subject share, and empty is zero."""
    assert cutout._subject_ratio([]) == 0.0
    assert cutout._subject_ratio([[0.0, 1.0], [1.0, 1.0]]) == pytest.approx(0.75)


# ---------------------------------------------------------------------------
# Segmentation entry point
# ---------------------------------------------------------------------------


class _FakeTorch:
    """Minimal torch surface the inference path touches."""

    float32 = "float32"

    def __init__(self) -> None:
        self.no_grad_calls = 0

    def tensor(self, data: object, dtype: object = None) -> "_FakeTensor":
        """Wrap a list as a fake tensor."""
        return _FakeTensor(data, dtype)

    class _NoGrad:
        def __enter__(self) -> None:
            return None

        def __exit__(self, *_exc: object) -> None:
            return None

    def no_grad(self) -> "_FakeTorch._NoGrad":
        """Return a context manager."""
        self.no_grad_calls += 1
        return self._NoGrad()


class _FakeTensor:
    """Fake tensor with a ``to``."""

    def __init__(self, data: object, dtype: object) -> None:
        self.data = data
        self.dtype = dtype
        self.on_device = False

    def to(self, _device: object) -> "_FakeTensor":
        """Mark it as moved."""
        self.on_device = True
        return self


class _FakeModel:
    """Callable model returning a two-level logit pyramid."""

    def __init__(self, device: object | None = None) -> None:
        self.device = device
        self.calls = 0

    def __call__(self, _tensor: object) -> list[list[list[float]]]:
        """Return a coarse and a fine map."""
        self.calls += 1
        return [[[0.0]], [[5.0, -5.0], [-5.0, 5.0]]]


def test_segment_subject_without_a_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """No model means no matte."""
    monkeypatch.setattr(cutout, "load_model", lambda: None)
    assert cutout.segment_subject(_image()) is None


def test_segment_subject_without_torch(monkeypatch: pytest.MonkeyPatch) -> None:
    """A model but no torch still yields no matte."""
    monkeypatch.setattr(cutout, "load_model", lambda: object())
    monkeypatch.setattr(cutout, "_cutout_tools", lambda: None)
    assert cutout.segment_subject(_image()) is None


def test_segment_subject_on_an_empty_image(monkeypatch: pytest.MonkeyPatch) -> None:
    """Zero geometry returns None instead of dividing by a missing size."""
    monkeypatch.setattr(cutout, "load_model", lambda: object())
    monkeypatch.setattr(cutout, "_cutout_tools", lambda: (_FakeTorch(), None))
    assert cutout.segment_subject([]) is None


def test_segment_subject_moves_the_tensor_and_decodes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The happy path builds a tensor, runs it, and returns an HW alpha."""
    torch = _FakeTorch()
    model = _FakeModel(device="cuda")
    monkeypatch.setattr(cutout, "load_model", lambda: model)
    monkeypatch.setattr(cutout, "_cutout_tools", lambda: (torch, None))
    mask = cutout.segment_subject(_image(height=2, width=2))
    assert mask is not None
    assert len(mask) == 2 and len(mask[0]) == 2
    assert mask[0][0] > 0.9 and mask[1][1] > 0.9
    assert model.calls == 1 and torch.no_grad_calls == 1


def test_segment_subject_without_a_device_field(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A model that reports no device skips the tensor move."""
    model = _FakeModel(device=None)
    monkeypatch.setattr(cutout, "load_model", lambda: model)
    monkeypatch.setattr(cutout, "_cutout_tools", lambda: (_FakeTorch(), None))
    assert cutout.segment_subject(_image(height=2, width=2)) is not None


def test_segment_subject_swallows_an_inference_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A model that raises is a missing matte, not a failed Queue."""

    class _Boom(_FakeModel):
        def __call__(self, _tensor: object) -> list[list[list[float]]]:
            raise RuntimeError("CUDA out of memory")

    monkeypatch.setattr(cutout, "load_model", lambda: _Boom())
    monkeypatch.setattr(cutout, "_cutout_tools", lambda: (_FakeTorch(), None))
    assert cutout.segment_subject(_image(height=2, width=2)) is None


# ---------------------------------------------------------------------------
# Compositing and the node body
# ---------------------------------------------------------------------------


def test_blend_over_white_black_and_original() -> None:
    """Each backdrop replaces the background the documented way."""
    pixels = [[[0.2, 0.4, 0.6]]]
    mask = [[0.5]]
    white = cutout._blend(pixels, mask, cutout.BACKDROP_WHITE)[0][0]
    assert white == pytest.approx([0.6, 0.7, 0.8])
    black = cutout._blend(pixels, mask, cutout.BACKDROP_BLACK)[0][0]
    assert black == pytest.approx([0.1, 0.2, 0.3])
    kept = cutout._blend(pixels, mask, cutout.BACKDROP_KEEP)[0][0]
    assert kept == pytest.approx([0.2, 0.4, 0.6])


def test_blend_tolerates_a_short_mask_and_short_pixel() -> None:
    """A mask smaller than the image reads as background, not IndexError."""
    wide = [[[0.2, 0.4, 0.6]]]
    assert cutout._blend(wide, [[]], cutout.BACKDROP_BLACK)[0][0] == pytest.approx(
        [0.0, 0.0, 0.0]
    )
    assert cutout._blend(wide, [[]], cutout.BACKDROP_WHITE)[0][0] == pytest.approx(
        [1.0, 1.0, 1.0]
    )
    thin = [[[0.2]]]
    assert len(cutout._blend(thin, [[1.0]], cutout.BACKDROP_WHITE)[0][0]) == 3


def test_matte_image_greys_the_alpha() -> None:
    """The matte is a 3-channel copy so stock SaveImage can write it."""
    assert cutout._matte_image([[0.25, 0.75]]) == [[[0.25, 0.25, 0.25], [0.75, 0.75, 0.75]]]


def test_remove_background_passes_through_when_off(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Kill switch off: the image is returned untouched with a white matte."""
    monkeypatch.setenv("EZ_CUTOUT", "off")
    image = _image()
    cut, matte, mask, status = cutout.remove_background(image)
    assert cut is image
    assert status == cutout.REASON_DISABLED
    assert all(value == 1.0 for row in mask for value in row)
    assert matte[0][0][0] == [1.0, 1.0, 1.0]


def test_remove_background_on_an_empty_batch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No pixels at all short-circuits before the model is asked."""
    monkeypatch.setattr(cutout, "segment_subject", lambda _i: [[1.0]])
    cut, matte, mask, status = cutout.remove_background([])
    assert cut == [] and matte == [] and mask == []
    assert status == cutout.REASON_NO_MODEL


def test_remove_background_passes_through_without_a_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing matte model is reported and the photo survives."""
    monkeypatch.setattr(cutout, "segment_subject", lambda _i: None)
    image = _image()
    cut, _matte, mask, status = cutout.remove_background(image)
    assert cut is image
    assert status == cutout.REASON_NO_MODEL
    assert mask  # opaque matte keeps downstream nodes wired


def test_remove_background_rejects_a_vacuous_matte(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An all-black detection is a failed run, not a fully erased photo."""
    monkeypatch.setattr(cutout, "segment_subject", lambda _i: [[0.0] * 4 for _ in range(3)])
    image = _image()
    cut, _matte, _mask, status = cutout.remove_background(image)
    assert cut is image
    assert status == cutout.REASON_EMPTY


def test_remove_background_cuts_the_subject(monkeypatch: pytest.MonkeyPatch) -> None:
    """A full matte over white keeps the subject and drops the room."""
    monkeypatch.setattr(cutout, "segment_subject", lambda _i: [[1.0] * 4 for _ in range(3)])
    image = _image()
    cut, matte, mask, status = cutout.remove_background(image, "white", 0, 0)
    assert status == cutout.REASON_CUT
    assert cut[0][0][0] == image[0][0]
    assert matte[0][0][0] == [1.0, 1.0, 1.0]
    assert len(mask) == 3 and len(mask[0]) == 4


def test_remove_background_erases_outside_the_matte(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Where alpha is zero the backdrop wins."""
    grid = [[0.0] * 4 for _ in range(3)]
    grid[1][1] = 1.0
    monkeypatch.setattr(cutout, "segment_subject", lambda _i: grid)
    image = _image()
    cut, _matte, _mask, status = cutout.remove_background(image, "black", 0, 0)
    assert status == cutout.REASON_CUT
    assert cut[0][0][0] == pytest.approx([0.0, 0.0, 0.0])
    assert cut[0][1][1] == image[1][1]


def test_remove_background_clamps_out_of_range_edges(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ridiculous dilate/feather values are clamped, not exploded."""
    monkeypatch.setattr(cutout, "segment_subject", lambda _i: [[1.0] * 4 for _ in range(3)])
    _cut, _matte, mask, status = cutout.remove_background(_image(), "white", 999, -5)
    assert status == cutout.REASON_CUT
    assert len(mask) == 3


def test_passthrough_sizes_the_matte_to_the_subject() -> None:
    """The fallback matte matches the frame so SaveImage stays happy."""
    image = _image(height=2, width=3)
    cut, matte, mask, status = cutout._passthrough(image, image, "status")
    assert cut is image and status == "status"
    assert len(mask) == 2 and len(mask[0]) == 3
    assert matte[0][0][0] == [1.0, 1.0, 1.0]


def test_the_matte_never_claims_the_gpu_lane() -> None:
    """``photos/cutout`` rides the ``none`` lane, so BiRefNet stays on CPU.

    The occupancy rule is one heavy GPU job per Spark and the App page reads
    ``none``. A matte model that walked onto CUDA would queue beside a running
    Klein or Wan take and spend the headroom that rule protects, so the loader
    takes no device argument at all and the tensors never move.
    """
    source = Path(cutout.__file__).read_text(encoding="utf-8")
    loader = source[source.index("def load_model") : source.index("def _preprocess")]
    for needle in ("device_map", "torch_device", ".cuda(", 'to("cuda"', "half()"):
        assert needle not in loader, needle
