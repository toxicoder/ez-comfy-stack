"""Cubic block world: block study, reference route, and people paste."""

from __future__ import annotations

import sys
import types
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_image.cubic import (  # noqa: E402
    EZCubicCondition,
    attach_reference,
    block_study,
    cell_size,
    erase_people,
    read_bhwc,
    write_bhwc,
    _quantize_channel,
)
from ez_image import person_mask as pm  # noqa: E402
from ez_prompt_enhance import client  # noqa: E402
from ez_prompt_enhance.background import REASON_PHOTO_ANCHOR  # noqa: E402
from ez_prompt_enhance.nodes import EZKleinPromptEnhance  # noqa: E402
from ez_prompt_enhance.samples import load_catalog  # noqa: E402
from ez_image.person_mask import (  # noqa: E402
    EZReinsertPeople,
    _fit_hwc,
    _resize_mask,
    MISS_COOLDOWN_S,
    PERSON_CLASS,
    REASON_MISSING,
    REASON_NOT_CUBIC,
    REASON_NO_PEOPLE,
    REASON_OFF,
    REASON_PASTED,
    WEIGHT_NAME,
    WEIGHT_URL,
    _deeplab_tools,
    _download,
    _torch_load,
    _weight_in,
    dilate_mask,
    download_weight,
    feather_mask,
    load_segmenter,
    person_mask_disabled,
    person_mask_roots,
    imagenet_normalize,
    person_mask_from_logits,
    person_mask_path,
    ready_weight_path,
    reinsert_people,
    reset_person_segmenter,
    run_deeplab,
    segment_people,
    segmenter_available,
)

CUBIC = "Rebuild this photographed place as cubic voxels."
"""Short cube prompt that :func:`is_reconstruction` always recognizes."""


@pytest.fixture(autouse=True)
def _isolated_segmenter_state(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[None]:
    """Keep the cached segmenter, cooldown, and model-root env per test.

    Args:
        monkeypatch: Pytest env/attr helper.

    Yields:
        Nothing; the fixture only installs the guards.
    """
    reset_person_segmenter()
    monkeypatch.delenv("EZ_PERSON_MASK", raising=False)
    monkeypatch.delenv("EZ_PERSON_MASK_PATH", raising=False)
    monkeypatch.delenv("MODELS_ROOT", raising=False)
    monkeypatch.delenv("MODELS_DIR", raising=False)
    yield
    reset_person_segmenter()


def _frame(height: int, width: int, paint: Any) -> list[Any]:
    """Build one HWC frame. ``paint(y, x)`` returns a 3-channel pixel."""
    return [[list(paint(y, x)) for x in range(width)] for y in range(height)]


def _flat(color: tuple[float, float, float], height: int, width: int) -> list[Any]:
    return _frame(height, width, lambda _y, _x: color)


class _Shot:
    """Tensor stand-in with detach/cpu/tolist plus device and dtype."""

    def __init__(self, data: list[Any]) -> None:
        self.data = data
        self.device = "cpu"
        self.dtype = "float32"

    def detach(self) -> _Shot:
        return self

    def cpu(self) -> _Shot:
        return self

    def tolist(self) -> list[Any]:
        return self.data


def test_cell_size_clamps() -> None:
    assert cell_size(36, 36) == 12
    assert cell_size(36 * 30, 36 * 30) == 30
    assert cell_size(36 * 50, 1800) == 40
    assert cell_size(0, 5) == 12


def test_block_study_is_a_cube_grid_not_the_photo() -> None:
    source = _frame(
        36,
        36,
        lambda y, x: (0.2 + (x % 12) * 0.03, 0.15, 0.1) if x < 18 else (0.05, 0.2, 0.7),
    )
    out = block_study([source])
    assert isinstance(out, list)
    mid = [tuple(out[0][8][x]) for x in range(12)]
    assert len(set(mid)) == 1
    assert len({tuple(source[8][x]) for x in range(12)}) > 1
    assert tuple(out[0][8][0]) != tuple(out[0][8][24])
    assert tuple(out[0][0][6]) != tuple(out[0][8][6])
    assert block_study([]) == []
    assert block_study([[]]) == [[]]
    assert block_study([[[]]]) == [[]]
    assert read_bhwc(_frame(2, 2, lambda _y, _x: (1.0, 0.0, 0.0)))[0][0][0] == [
        1.0,
        0.0,
        0.0,
    ]


def test_block_study_reads_tensors_and_writes_them_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    data = [_flat((0.4, 0.4, 0.4), 12, 12)]
    shot = _Shot(data)
    seen: dict[str, Any] = {}

    def tensor(payload: list[Any], dtype: str, device: str) -> str:
        seen["dtype"] = dtype
        seen["device"] = device
        seen["batch"] = len(payload)
        return "tensor"

    fake = types.SimpleNamespace(tensor=tensor)
    monkeypatch.setitem(sys.modules, "torch", fake)
    assert write_bhwc(data, shot) == "tensor"
    assert seen == {"dtype": "float32", "device": "cpu", "batch": 1}
    assert block_study(shot) == "tensor"
    monkeypatch.setitem(sys.modules, "torch", None)
    assert write_bhwc(data, shot) is data


def test_read_bhwc_rejects_junk() -> None:
    with pytest.raises(TypeError):
        read_bhwc(object())
    with pytest.raises(TypeError):
        read_bhwc(types.SimpleNamespace(tolist=lambda: "nope"))


def test_attach_reference_fallback_does_not_alias() -> None:
    cond: list[Any] = [["tok", {"reference_latents": ["old"]}]]
    out = attach_reference(cond, "photo")
    assert cond[0][1]["reference_latents"] == ["old"]
    assert out[0][1]["reference_latents"] == ["old", "photo"]
    bare = attach_reference([["tok", "meta"], "lonely"], "photo")
    assert bare[0] == ["tok", "meta"]
    assert bare[1] == "lonely"
    assert attach_reference({"samples": 1}, "lat")["reference"] == "lat"
    assert attach_reference("nope", "lat") == "nope"


def test_attach_reference_uses_comfy_when_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[Any] = []

    class _Ref:
        def append(self, conditioning: list[Any], latent: str) -> tuple[list[Any]]:
            calls.append(latent)
            refs = conditioning[0][1].setdefault("reference_latents", [])
            refs.append(latent)
            return (conditioning,)

    pkg = types.ModuleType("comfy_extras")
    pkg.__path__ = []  # type: ignore[attr-defined]
    sub = types.ModuleType("comfy_extras.nodes_flux")
    sub.ReferenceLatent = _Ref  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "comfy_extras", pkg)
    monkeypatch.setitem(sys.modules, "comfy_extras.nodes_flux", sub)
    out = attach_reference([["tok", {}]], "study")
    assert calls == ["study"], calls
    assert out[0][1]["reference_latents"] == ["study"]

    class _Bare:
        def append(self, conditioning: list[Any], latent: str) -> str:
            del conditioning, latent
            return "bare"

    sub.ReferenceLatent = _Bare  # type: ignore[attr-defined]
    assert attach_reference([["tok", {}]], "study") == "bare"

    class _Boom:
        def append(self, conditioning: list[Any], latent: str) -> tuple[list[Any]]:
            del conditioning, latent
            raise RuntimeError("no reference")

    sub.ReferenceLatent = _Boom  # type: ignore[attr-defined]
    fallen = attach_reference([["tok", {}]], "study")
    assert fallen[0][1]["reference_latents"] == ["study"]


def test_cubic_condition_picks_photo_or_study(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ordinary prompts and a usable segmenter route photo vs. block study.

    Args:
        monkeypatch: Pytest attr helper.
    """
    monkeypatch.setattr(
        "ez_image.person_mask.segment_people", lambda _image: None
    )
    monkeypatch.setattr("ez_image.person_mask.segmenter_available", lambda: True)
    node = EZCubicCondition()
    assert node.INPUT_TYPES()["required"]["prompt"][1]["forceInput"] is True
    cond = [["tok", {}]]
    photo = {"samples": "photo"}
    harbor = node.run(cond, photo, [], types.SimpleNamespace(), "fog harbor pier")
    assert harbor[0][0][1]["reference_latents"] == [photo]
    assert cond[0][1] == {}

    class _Vae:
        def encode(self, image: Any) -> dict[str, str]:
            assert image
            return {"samples": "study"}

    cubic = node.run(cond, photo, [_flat((0.2, 0.3, 0.4), 12, 12)], _Vae(), CUBIC)
    assert cubic[0][0][1]["reference_latents"] == [{"samples": "study"}]

    class _BadVae:
        def encode(self, image: Any) -> dict[str, str]:
            del image
            raise RuntimeError("encode")

    failed = node.run(cond, photo, [_flat((0.2, 0.2, 0.2), 12, 12)], _BadVae(), CUBIC)
    assert failed[0][0][1]["reference_latents"] == [photo]
    missing = node.run(cond, photo, object(), types.SimpleNamespace(), CUBIC)
    assert missing[0][0][1]["reference_latents"] == [photo]
    no_encode = node.run(cond, photo, [], types.SimpleNamespace(), CUBIC)
    assert no_encode[0][0][1]["reference_latents"] == [photo]


def test_cubic_condition_fails_closed_to_the_photo_without_a_segmenter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without the person paste the study is never built, so people survive.

    Args:
        monkeypatch: Pytest attr helper.
    """
    monkeypatch.setattr("ez_image.person_mask.segmenter_available", lambda: False)
    built: list[Any] = []

    def spy_study(image: Any) -> Any:
        """Record any attempt to build a block study.

        Args:
            image: Source still handed to the study builder.

        Returns:
            The image, unchanged.
        """
        built.append(image)
        return image

    monkeypatch.setattr("ez_image.cubic.block_study", spy_study)

    class _Vae:
        def encode(self, image: Any) -> dict[str, str]:
            assert image
            return {"samples": "study"}

    node = EZCubicCondition()
    cond = [["tok", {}]]
    photo = {"samples": "photo"}
    guarded = node.run(cond, photo, [_flat((0.2, 0.3, 0.4), 12, 12)], _Vae(), CUBIC)
    assert guarded[0][0][1]["reference_latents"] == [photo]
    assert built == []


def test_erase_people_fills_persons_with_blurred_background(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    background = (0.75, 0.5, 0.25)
    person = (0.0, 1.0, 0.0)
    image = _frame(
        36,
        36,
        lambda y, x: person if 12 <= y < 24 and 12 <= x < 24 else background,
    )
    study = block_study([image])
    bare = block_study([image])[0]
    assert bare[18][18] == [0.0, 1.0, 0.0]  # cubed person before erase

    def mask_of(_image: Any) -> list[list[float]]:
        return [
            [1.0 if 12 <= x < 24 and 12 <= y < 24 else 0.0 for x in range(36)]
            for y in range(36)
        ]

    monkeypatch.setattr("ez_image.person_mask.segment_people", mask_of)
    erased = erase_people(study, image)[0]
    radius = cell_size(36, 36)
    for channel in range(3):
        plane = [[bare[y][x][channel] for x in range(36)] for y in range(36)]
        expected = feather_mask(plane, radius)
        for y in range(36):
            for x in range(36):
                if 12 <= y < 24 and 12 <= x < 24:
                    assert erased[y][x][channel] == _quantize_channel(expected[y][x])
                else:
                    assert erased[y][x] == bare[y][x]
    # filled cell reads as background, not the cubed person
    assert erased[18][18] != list(bare[18][18])

    def small_mask(_image: Any) -> list[list[float]]:
        return [
            [1.0 if 6 <= x < 12 and 6 <= y < 12 else 0.0 for x in range(18)]
            for y in range(18)
        ]

    monkeypatch.setattr("ez_image.person_mask.segment_people", small_mask)
    # half-resolution mask resizes onto the study before erasing
    assert erase_people(study, image)[0] == erased


def test_erase_people_fail_soft(monkeypatch: pytest.MonkeyPatch) -> None:
    image = _frame(
        36,
        36,
        lambda y, x: (0.1, 0.9, 0.1) if 12 <= y < 24 and 12 <= x < 24 else (0.75, 0.5, 0.25),
    )
    study = block_study([image])
    # segmenter unavailable (missing weights): study passes through
    monkeypatch.setattr("ez_image.person_mask.segment_people", lambda _image: None)
    assert erase_people(study, image) is study
    # no person pixels: study passes through
    monkeypatch.setattr(
        "ez_image.person_mask.segment_people",
        lambda _image: [[0.0] * 36 for _ in range(36)],
    )
    assert erase_people(study, image) is study
    empty: list[Any] = []
    assert erase_people(empty, image) is empty


def test_reinsert_passthrough_and_paste() -> None:
    plate = [_flat((0.0, 0.0, 1.0), 20, 20)]
    source = [_flat((1.0, 0.0, 0.0), 20, 20)]
    same, status = reinsert_people(plate, source, "fog harbor pier")
    assert same is plate
    assert status == REASON_NOT_CUBIC

    def mask(_image: Any) -> list[list[float]]:
        grid = [[0.0] * 20 for _y in range(20)]
        for y in range(4, 16):
            for x in range(4, 16):
                grid[y][x] = 1.0
        return grid

    pasted, pasted_status = reinsert_people(plate, source, CUBIC, segment=mask)
    assert pasted_status == REASON_PASTED
    assert pasted[0][10][10] == [1.0, 0.0, 0.0]
    # dilate: the paste owns a ring just outside the raw segmentation boundary
    ring = dilate_mask(mask(None), 2)
    assert ring[10][16] == 1.0 and ring[10][2] == 1.0
    assert ring[10][18] == 0.0 and ring[10][1] == 0.0
    # feather: alpha ramps down over ~6px, no 1px hard step
    red = [pasted[0][10][x][0] for x in range(12, 20)]
    assert red == pytest.approx([12 / 13, 11 / 13, 10 / 12, 9 / 11, 8 / 10, 7 / 9, 6 / 8, 5 / 7])
    assert pasted[0][0][0] == pytest.approx([25 / 49, 0.0, 24 / 49])
    assert pasted is not plate

    empty, empty_status = reinsert_people(
        plate,
        source,
        CUBIC,
        segment=lambda _image: [[0.0] * 20 for _y in range(20)],
    )
    assert empty_status == REASON_NO_PEOPLE
    assert empty[0][10][10] == [0.0, 0.0, 1.0]

    missing, missing_status = reinsert_people(
        plate, source, CUBIC, segment=lambda _image: None
    )
    assert missing is plate
    assert missing_status == REASON_MISSING
    def explode(_image: Any) -> list[list[float]]:
        raise RuntimeError("seg")

    boom, boom_status = reinsert_people(plate, source, CUBIC, segment=explode)
    assert boom is plate
    assert boom_status == REASON_MISSING
    junk, junk_status = reinsert_people(object(), source, CUBIC, segment=mask)
    assert junk_status == REASON_MISSING
    assert junk is not source


def test_reinsert_resizes_and_respects_the_off_switch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EZ_PERSON_MASK", "off")
    plate = [_flat((0.0, 1.0, 0.0), 8, 8)]
    assert person_mask_disabled() is True
    same, status = reinsert_people(plate, plate, CUBIC, segment=lambda _image: [[1.0]])
    assert same is plate
    assert status == REASON_OFF
    monkeypatch.delenv("EZ_PERSON_MASK", raising=False)
    small = [_flat((1.0, 1.0, 0.0), 4, 4)]
    wide = [_flat((0.0, 0.0, 0.0), 8, 8)]

    def tiny(_image: Any) -> list[list[float]]:
        return [[1.0, 1.0], [1.0, 1.0]]

    pasted, status = reinsert_people(wide, small, CUBIC, segment=tiny)
    assert status == REASON_PASTED
    assert len(pasted[0]) == 8
    assert len(pasted[0][0]) == 8
    big_plate = [_flat((0.0, 0.0, 1.0), 8, 8)]
    big_source = _frame(
        16,
        16,
        lambda y, x: (1.0, 0.0, 0.0) if 4 <= y < 12 and 4 <= x < 12 else (0.0, 1.0, 0.0),
    )

    def big_mask(_image: Any) -> list[list[float]]:
        return [
            [1.0 if 4 <= x < 12 and 4 <= y < 12 else 0.0 for x in range(16)]
            for y in range(16)
        ]

    pasted_big, status_big = reinsert_people(big_plate, [big_source], CUBIC, segment=big_mask)
    assert status_big == REASON_PASTED
    assert len(pasted_big[0]) == 8
    assert len(pasted_big[0][0]) == 8
    # resize math is resolution-agnostic: plate pixel (y, x) samples source (2y, 2x)
    assert pasted_big[0][4][4] == [1.0, 0.0, 0.0]
    assert pasted_big[0][0][0] == [0.0, 1.0, 0.0]
    node = EZReinsertPeople()
    assert node.INPUT_TYPES()["required"]["prompt"][1]["forceInput"] is True
    packed = node.run(wide, small, "fog harbor")
    assert packed["ui"]["text"] == (REASON_NOT_CUBIC,)
    assert packed["result"][0] is wide


def test_imagenet_normalize_matches_deeplab_stats() -> None:
    out = imagenet_normalize([[[(1.0, 1.0, 1.0), (0.0,)]]])
    pixel = out[0][0][0]
    assert abs(pixel[0] - ((1.0 - 0.485) / 0.229)) < 1e-6
    assert abs(pixel[1] - ((1.0 - 0.456) / 0.224)) < 1e-6
    assert len(out[0][0][1]) == 3
    assert out[0][0][1][0] < 0.0


def test_mask_morphology_and_logits() -> None:
    assert _resize_mask([], 4, 4) == []
    assert _fit_hwc([], 4, 4) == []
    assert dilate_mask([], 1) == []
    assert feather_mask([], 1) == []
    assert dilate_mask([[1.0, 1.0]], 0) == [[1.0, 1.0]]
    assert feather_mask([[1.0, 0.0]], 0) == [[1.0, 0.0]]
    assert dilate_mask([[0.0, 0.0]], 1) == [[0.0, 0.0]]
    dot = [[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.0]]
    dilated = dilate_mask(dot, 1)
    assert dilated == [[1.0, 1.0, 1.0], [1.0, 1.0, 1.0], [1.0, 1.0, 1.0]]
    soft = feather_mask([[0.0, 1.0, 0.0]], 1)
    assert 0.0 < soft[0][0] < 1.0
    ramp = feather_mask([[0.0] * 13 + [1.0] + [0.0] * 13], 6)
    assert ramp[0][6] == 0.0
    assert ramp[0][7] == pytest.approx(1 / 13)
    assert ramp[0][19] == pytest.approx(1 / 13)
    assert ramp[0][20] == 0.0
    chw: list[Any] = []
    for cls in range(16):
        score = 5.0 if cls == PERSON_CLASS else 0.1
        chw.append([[score, 0.0]])
    mask = person_mask_from_logits(chw)
    assert mask == [[1.0, 0.0]]
    with pytest.raises(ValueError):
        person_mask_from_logits([])


def test_person_mask_roots_prefer_the_container_mount(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Roots come from MODELS_ROOT then MODELS_DIR, then the fixed fallbacks.

    Args:
        monkeypatch: Pytest env helper.
        tmp_path: Isolated directory used as a host model root.
    """
    host = str(tmp_path)
    monkeypatch.setenv("MODELS_ROOT", "/models")
    monkeypatch.setenv("MODELS_DIR", host)
    assert person_mask_roots() == ["/models", host, "/mnt/models"]
    monkeypatch.setenv("MODELS_DIR", "   ")
    assert person_mask_roots() == ["/models", "/mnt/models"]
    monkeypatch.delenv("MODELS_ROOT", raising=False)
    monkeypatch.setenv("MODELS_DIR", "/models")
    assert person_mask_roots() == ["/models", "/mnt/models"]
    monkeypatch.delenv("MODELS_DIR", raising=False)
    assert person_mask_roots() == ["/models", "/mnt/models"]
    monkeypatch.setenv("MODELS_ROOT", "/mnt/models")
    assert person_mask_roots() == ["/mnt/models", "/models"]
    assert _weight_in("/models") == f"/models/comfy/ez-person/{WEIGHT_NAME}"
    assert person_mask_path() == _weight_in("/mnt/models")
    monkeypatch.delenv("MODELS_ROOT", raising=False)
    assert person_mask_path() == _weight_in("/models")


def test_ready_weight_path_finds_the_container_root_checkpoint(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The Compose container only sets MODELS_ROOT, so that root must resolve.

    Args:
        monkeypatch: Pytest env helper.
        tmp_path: Host model root that holds no checkpoint.
    """
    container = tmp_path / "container-models"
    checkpoint = container / "comfy" / "ez-person" / WEIGHT_NAME
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_bytes(b"weights")
    monkeypatch.setenv("MODELS_ROOT", str(container))
    monkeypatch.setenv("MODELS_DIR", str(tmp_path / "host-models"))
    assert person_mask_path() == str(checkpoint)
    assert ready_weight_path() == str(checkpoint)
    checkpoint.write_bytes(b"")
    assert ready_weight_path() is None


def test_segmenter_available_cooldown_cache_and_off_switch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One failed load is remembered; a success caches; reset clears both.

    Args:
        monkeypatch: Pytest attr/env helper.
    """
    clock = {"now": 1000.0}
    monkeypatch.setattr(pm, "time", types.SimpleNamespace(monotonic=lambda: clock["now"]))
    calls = {"load": 0}

    def failing_load() -> Any:
        calls["load"] += 1
        return None

    monkeypatch.setattr("ez_image.person_mask.load_segmenter", failing_load)
    assert segmenter_available() is False
    assert calls["load"] == 1
    assert segmenter_available() is False
    assert calls["load"] == 1
    clock["now"] += MISS_COOLDOWN_S + 1.0
    assert segmenter_available() is False
    assert calls["load"] == 2
    reset_person_segmenter()
    assert segmenter_available() is False
    assert calls["load"] == 3

    reset_person_segmenter()
    loads = {"n": 0}

    def working_load() -> Any:
        loads["n"] += 1
        return object()

    monkeypatch.setattr("ez_image.person_mask.load_segmenter", working_load)
    assert segmenter_available() is True
    assert segmenter_available() is True
    assert loads["n"] == 1
    monkeypatch.setenv("EZ_PERSON_MASK", "off")
    assert segmenter_available() is False


def test_container_state_without_weights_keeps_the_people(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Compose-like env (MODELS_ROOT only, no checkpoint) fails closed.

    This is the shipped bug: the person segmenter could never load in the
    container, so every cubic step failed soft on its own and Klein deleted
    the people. The gate must be one call that the whole route shares.

    Args:
        monkeypatch: Pytest env/attr helper.
        tmp_path: Empty container model root standing in for ``/models``.
    """
    container = tmp_path / "models"
    container.mkdir()
    monkeypatch.setenv("MODELS_ROOT", str(container))
    monkeypatch.delenv("MODELS_DIR", raising=False)
    monkeypatch.setattr("ez_image.person_mask.load_segmenter", lambda: None)
    assert person_mask_roots()[0] == str(container)
    assert ready_weight_path() is None
    assert segmenter_available() is False

    cubic = next(
        item
        for item in load_catalog("klein_background_swap")
        if item.id == "voxel-block-world"
    )
    klein = EZKleinPromptEnhance()
    with patch.object(client, "complete", return_value=("rewritten", None)) as mock:
        packed = klein.run(
            cubic.prompt,
            True,
            "background_swap",
            "match the source still",
            "none",
            image_desc="wet dock, red coat, unmarked hull",
        )
    mock.assert_not_called()
    text = packed["result"][0]
    assert "Keep the people as photographed" in text
    assert "empty of people" not in text.lower()
    assert "with its people removed" not in text
    assert "Source still: wet dock, red coat, unmarked hull" in text
    assert packed["ui"]["passthrough"][0] == REASON_PHOTO_ANCHOR

    node = EZCubicCondition()
    cond = [["tok", {}]]
    photo = {"samples": "photo"}

    class _Vae:
        def encode(self, image: Any) -> dict[str, str]:
            assert image
            return {"samples": "study"}

    routed = node.run(cond, photo, [_flat((0.2, 0.3, 0.4), 12, 12)], _Vae(), CUBIC)
    assert routed[0][0][1]["reference_latents"] == [photo]

    plate = [_flat((0.0, 0.0, 1.0), 8, 8)]
    source = [_flat((1.0, 0.0, 0.0), 8, 8)]
    same, status = reinsert_people(plate, source, CUBIC)
    assert same is plate
    assert status == REASON_MISSING


def test_segmenter_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    reset_person_segmenter()
    monkeypatch.setenv("EZ_PERSON_MASK", "off")
    assert load_segmenter() is None
    assert segment_people([_flat((0.0, 0.0, 0.0), 2, 2)]) is None
    monkeypatch.delenv("EZ_PERSON_MASK", raising=False)
    monkeypatch.setattr(
        "ez_image.person_mask._deeplab_tools",
        lambda: None,
    )
    assert load_segmenter() is None
    assert _deeplab_tools() is None

    weight = tmp_path / "deeplab.pth"
    monkeypatch.setenv("EZ_PERSON_MASK_PATH", str(weight))
    assert person_mask_path() == str(weight)
    assert ready_weight_path() is None
    weight.write_bytes(b"")
    assert ready_weight_path() is None
    weight.write_bytes(b"weights")
    assert ready_weight_path() == str(weight)

    loaded: dict[str, Any] = {}

    class _Model:
        def load_state_dict(self, state: dict[str, int]) -> None:
            loaded["state"] = state

        def eval(self) -> _Model:
            loaded["eval"] = True
            return self

    class _Weights:
        COCO_WITH_VOC_LABELS_V1 = "coco"

    def factory(weights: Any) -> _Model:
        loaded["weights"] = weights
        return _Model()

    def torch_load(path: str, map_location: str = "cpu", weights_only: bool | None = None) -> dict[str, int]:
        if weights_only is not None:
            raise TypeError("old torch")
        loaded["path"] = path
        loaded["map"] = map_location
        return {"ok": 1}

    monkeypatch.setattr(
        "ez_image.person_mask._deeplab_tools",
        lambda: (types.SimpleNamespace(load=torch_load), factory, _Weights),
    )
    monkeypatch.setattr("ez_image.person_mask.download_weight", lambda: None)
    model = load_segmenter()
    assert loaded["weights"] is None
    assert loaded["state"] == {"ok": 1}
    assert loaded["eval"] is True
    assert model is not None

    weight.unlink()
    monkeypatch.setattr("ez_image.person_mask.ready_weight_path", lambda: None)
    monkeypatch.setattr("ez_image.person_mask.download_weight", lambda: None)
    enum_model = load_segmenter()
    assert loaded["weights"] == "coco"
    assert enum_model is not None

    def boom(weights: Any) -> _Model:
        del weights
        raise RuntimeError("bad weights")

    monkeypatch.setattr(
        "ez_image.person_mask._deeplab_tools",
        lambda: (types.SimpleNamespace(load=torch_load), boom, _Weights),
    )
    assert load_segmenter() is None


def test_download_weight(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    dest = tmp_path / "ez-person" / "mask.pth"
    monkeypatch.setenv("EZ_PERSON_MASK_PATH", str(dest))

    class _Body:
        def read(self) -> bytes:
            return b"ckpt"

        def __enter__(self) -> _Body:
            return self

        def __exit__(self, *_exc: object) -> None:
            return None

    def opener(url: str, timeout: int) -> _Body:
        assert url == WEIGHT_URL
        assert timeout > 0
        return _Body()

    monkeypatch.setattr("ez_image.person_mask.urlopen", opener)
    assert download_weight() == str(dest)
    assert dest.read_bytes() == b"ckpt"
    assert _download(WEIGHT_URL, str(dest)) is True

    def empty(url: str, timeout: int) -> _Body:
        del url, timeout
        body = _Body()
        body.read = lambda: b""  # type: ignore[method-assign]
        return body

    monkeypatch.setattr("ez_image.person_mask.urlopen", empty)
    assert _download(WEIGHT_URL, str(tmp_path / "empty.pth")) is False

    def broke(url: str, timeout: int) -> _Body:
        del url, timeout
        raise OSError("offline")

    monkeypatch.setattr("ez_image.person_mask.urlopen", broke)
    assert _download(WEIGHT_URL, str(dest)) is False

    def _ro(*_args: object, **_kwargs: object) -> None:
        raise OSError("ro")

    monkeypatch.setattr("ez_image.person_mask.os.makedirs", _ro)
    assert download_weight() is None
    monkeypatch.setattr("ez_image.person_mask.os.makedirs", lambda *_a, **_k: None)
    monkeypatch.setattr("ez_image.person_mask.os.access", lambda *_a, **_k: False)
    assert download_weight() is None
    monkeypatch.setattr("ez_image.person_mask.os.makedirs", lambda *_a, **_k: None)
    monkeypatch.setattr("ez_image.person_mask.os.access", lambda *_a, **_k: True)
    monkeypatch.setattr(
        "ez_image.person_mask._download",
        lambda *_a, **_k: False,
    )
    assert download_weight() is None


def test_download_weight_walks_the_writable_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Unwritable candidates are skipped, not fatal, and the next root wins.

    Args:
        monkeypatch: Pytest env/attr helper.
        tmp_path: Writable scratch root.
    """
    blocker = tmp_path / "blocked"
    blocker.write_text("x", encoding="utf-8")
    monkeypatch.setenv("EZ_PERSON_MASK_PATH", str(blocker / WEIGHT_NAME))
    monkeypatch.setattr("ez_image.person_mask._download", lambda *_a, **_k: False)
    assert download_weight() is None

    first = tmp_path / "first"
    second = tmp_path / "second"
    monkeypatch.delenv("EZ_PERSON_MASK_PATH", raising=False)
    monkeypatch.setenv("MODELS_ROOT", str(first))
    monkeypatch.setenv("MODELS_DIR", str(second))
    seen: list[str] = []

    def fake_makedirs(path: str, *_args: Any, **_kwargs: Any) -> None:
        seen.append(str(path))

    def fake_access(path: str, _mode: int) -> bool:
        return str(path) == str(second / "comfy" / "ez-person")

    def fake_download(url: str, dest: str) -> bool:
        assert url == WEIGHT_URL
        return True

    monkeypatch.setattr("ez_image.person_mask.os.makedirs", fake_makedirs)
    monkeypatch.setattr("ez_image.person_mask.os.access", fake_access)
    monkeypatch.setattr("ez_image.person_mask._download", fake_download)
    assert download_weight() == str(second / "comfy" / "ez-person" / WEIGHT_NAME)
    assert seen == [
        str(first / "comfy" / "ez-person"),
        str(second / "comfy" / "ez-person"),
    ]

    monkeypatch.setattr("ez_image.person_mask.os.access", lambda *_a, **_k: False)
    assert download_weight() is None


def test_run_deeplab_and_segment_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_person_segmenter()
    monkeypatch.delenv("EZ_PERSON_MASK", raising=False)
    assert run_deeplab(object(), []) is None

    class _NoGrad:
        def __enter__(self) -> None:
            return None

        def __exit__(self, *_exc: object) -> None:
            return None

    class _Tensor:
        def __init__(self, data: list[Any]) -> None:
            self.data = data

        def movedim(self, src: int, dst: int) -> _Tensor:
            assert src == -1 and dst == 1
            return self

    chw: list[Any] = []
    for cls in range(16):
        score = 4.0 if cls == PERSON_CLASS else 0.0
        chw.append([[score]])
    batched = [chw]

    class _Logits:
        def tolist(self) -> list[Any]:
            return batched

        def detach(self) -> _Logits:
            return self

        def cpu(self) -> _Logits:
            return self

    class _Model:
        def __init__(self) -> None:
            self.calls = 0

        def eval(self) -> None:
            self.calls += 1

        def __call__(self, tensor: _Tensor) -> dict[str, _Logits]:
            assert isinstance(tensor, _Tensor)
            return {"out": _Logits()}

    fake_torch = types.SimpleNamespace(tensor=_Tensor, no_grad=_NoGrad)
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    mask = run_deeplab(_Model(), [_flat((0.2, 0.2, 0.2), 2, 2)])
    assert mask == [[1.0]]
    assert run_deeplab(lambda _t: (_ for _ in ()).throw(RuntimeError("fwd")), [_flat((0, 0, 0), 1, 1)]) is None
    assert run_deeplab(lambda _t: {"out": None}, [_flat((0, 0, 0), 1, 1)]) is None
    assert run_deeplab(lambda _t: object(), [_flat((0, 0, 0), 1, 1)]) is None
    assert run_deeplab(lambda _t: [], [_flat((0, 0, 0), 1, 1)]) is None
    assert run_deeplab(lambda _t: [[]], [_flat((0, 0, 0), 1, 1)]) == []
    assert run_deeplab(lambda _t: [[["nope"]]], [_flat((0, 0, 0), 1, 1)]) is None

    plain = types.SimpleNamespace(tensor=lambda data: data)
    monkeypatch.setitem(sys.modules, "torch", plain)
    direct = run_deeplab(lambda _t: chw, [_flat((0.1, 0.1, 0.1), 1, 1)])
    assert direct == [[1.0]]

    calls = {"load": 0}

    def fake_load() -> _Model:
        calls["load"] += 1
        return _Model()

    monkeypatch.setattr("ez_image.person_mask.load_segmenter", fake_load)
    monkeypatch.setattr("ez_image.person_mask.run_deeplab", lambda _model, _image: [[1.0]])
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    reset_person_segmenter()
    assert segment_people([_flat((0, 0, 0), 2, 2)]) == [[1.0]]
    assert segment_people([_flat((0, 0, 0), 2, 2)]) == [[1.0]]
    assert calls["load"] == 1
    reset_person_segmenter()
    monkeypatch.setattr("ez_image.person_mask.load_segmenter", lambda: None)
    assert segment_people([_flat((0, 0, 0), 2, 2)]) is None


def test_deeplab_import_and_weight_edges(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for name in (
        "torch",
        "torchvision",
        "torchvision.models",
        "torchvision.models.segmentation",
    ):
        monkeypatch.setitem(sys.modules, name, None)
    assert _deeplab_tools() is None

    torch_mod = types.ModuleType("torch")
    tv = types.ModuleType("torchvision")
    models = types.ModuleType("torchvision.models")
    seg = types.ModuleType("torchvision.models.segmentation")
    seg.deeplabv3_resnet50 = lambda **_kwargs: "net"  # type: ignore[attr-defined]

    class _Weights:
        COCO_WITH_VOC_LABELS_V1 = "coco"

    seg.DeepLabV3_ResNet50_Weights = _Weights  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "torch", torch_mod)
    monkeypatch.setitem(sys.modules, "torchvision", tv)
    monkeypatch.setitem(sys.modules, "torchvision.models", models)
    monkeypatch.setitem(sys.modules, "torchvision.models.segmentation", seg)
    tools = _deeplab_tools()
    assert tools is not None
    assert tools[2] is _Weights

    monkeypatch.delenv("EZ_PERSON_MASK_PATH", raising=False)
    monkeypatch.setenv("MODELS_DIR", str(tmp_path))
    assert person_mask_path().endswith("deeplabv3_resnet50_coco-cd0a2569.pth")
    monkeypatch.setenv("MODELS_DIR", "  ")
    assert person_mask_path().startswith("/models")

    def _boom(*_args: object, **_kwargs: object) -> bool:
        raise OSError("stat")

    monkeypatch.setattr("ez_image.person_mask.os.path.isfile", _boom)
    assert ready_weight_path() is None

    class _Body:
        def read(self) -> bytes:
            return b"ckpt"

        def __enter__(self) -> _Body:
            return self

        def __exit__(self, *_exc: object) -> None:
            return None

    monkeypatch.setattr("ez_image.person_mask.urlopen", lambda *_a, **_k: _Body())
    blocker = tmp_path / "not-dir"
    blocker.write_text("x", encoding="utf-8")
    assert _download(WEIGHT_URL, str(blocker / "child.pth")) is False

    plate: list[Any] = [[[]]]
    missing, status = reinsert_people(
        plate,
        [],
        CUBIC,
        segment=lambda _image: [[1.0]],
    )
    assert missing is plate
    assert status == REASON_MISSING
    skipped, skipped_status = reinsert_people(
        [_flat((0.0, 0.0, 1.0), 4, 4)],
        [[]],
        CUBIC,
        segment=lambda _image: [[1.0, 1.0], [1.0, 1.0]],
    )
    assert skipped_status == REASON_NO_PEOPLE
    assert skipped[0][0][0] == [0.0, 0.0, 1.0]
    blank, blank_status = reinsert_people(
        [[]],
        [_flat((1.0, 0.0, 0.0), 2, 2)],
        CUBIC,
        segment=lambda _image: [[1.0, 1.0], [1.0, 1.0]],
    )
    assert blank_status == REASON_NO_PEOPLE
    assert blank == [[]]
    hot = block_study([_frame(12, 12, lambda _y, _x: (2.0, -1.0, 0.5))])
    assert hot[0][6][6][0] <= 1.0
    assert hot[0][6][6][1] >= 0.0


def test_torch_load_falls_back_without_weights_only() -> None:
    calls: list[bool] = []

    def load(path: str, map_location: str = "cpu", weights_only: bool | None = None) -> str:
        del path, map_location
        calls.append(weights_only is not None)
        if weights_only is not None:
            raise TypeError("old")
        return "state"

    torch_mod = types.SimpleNamespace(load=load)
    assert _torch_load(torch_mod, "file.pth") == "state"
    assert calls == [True, False]
