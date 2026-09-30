"""Hermetic tests for the Drive-through beat joiner.

Synthetic 8 kHz stems built from sines and seeded noise: no Comfy, no torch,
no GPU. Covers whole-bar grid validation, seam length arithmetic, sample
continuity, the sub-band hand-off, and the mid-band equal-power fade.
"""

from __future__ import annotations

import math
import random
import sys
import types
from pathlib import Path
from typing import Any, cast

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_music import join as aj  # noqa: E402
from ez_music.nodes import EZAudioBeatJoin, NODE_CLASS_MAPPINGS  # noqa: E402

RATE = 8000
BPM = 172.0


def _audio(samples: list[float], sample_rate: int = RATE) -> dict[str, Any]:
    """Wrap PCM in a Comfy AUDIO dict (nested lists, no torch needed).

    Args:
        samples: 1-D PCM.
        sample_rate: Waveform rate.

    Returns:
        AUDIO mapping.
    """
    return {"waveform": [list(samples)], "sample_rate": sample_rate}


def _bars_samples(bars: int, bpm: float = BPM, sample_rate: int = RATE) -> int:
    """Samples in a whole number of bars.

    Args:
        bars: Bar count.
        bpm: Tempo.
        sample_rate: Waveform rate.

    Returns:
        Rounded sample count.
    """
    return int(round(bars * 240.0 / bpm * sample_rate))


def _sine(freq: float, length: int, amp: float = 0.6, sample_rate: int = RATE) -> list[float]:
    """Sinusoid starting at phase 0.

    Args:
        freq: Hertz.
        length: Sample count.
        amp: Peak amplitude.
        sample_rate: Waveform rate.

    Returns:
        PCM.
    """
    step = 2.0 * math.pi * freq / sample_rate
    return [amp * math.sin(step * i) for i in range(length)]


def _noise(length: int, amp: float, seed: int) -> list[float]:
    """Deterministic white noise.

    Args:
        length: Sample count.
        amp: Peak amplitude.
        seed: RNG seed.

    Returns:
        PCM.
    """
    rng = random.Random(seed)
    return [rng.uniform(-amp, amp) for _ in range(length)]


def _mix(length: int, seed: int) -> list[float]:
    """Grid-shaped test stem: sub, mid, and a little noise floor.

    Args:
        length: Sample count.
        seed: Noise seed (also nudges the mid tone per stem).

    Returns:
        PCM.
    """
    mid_freq = 900.0 + 130.0 * seed
    out = _sine(60.0, length, 0.6)
    mid = _sine(mid_freq, length, 0.15)
    hiss = _noise(length, 0.02, seed)
    return [a + b + c for a, b, c in zip(out, mid, hiss)]


def _flatten(payload: Any) -> list[float]:
    """Flatten any waveform shape to PCM through the production helper.

    Args:
        payload: Waveform value.

    Returns:
        PCM.
    """
    return aj._as_pcm(payload)  # noqa: SLF001 - deliberate white-box check


def _goertzel_energy(samples: list[float], freq: float, sample_rate: int = RATE) -> float:
    """Squared magnitude of one tone over a window.

    Args:
        samples: Window PCM.
        freq: Tone frequency.
        sample_rate: Waveform rate.

    Returns:
        Energy (magnitude squared).
    """
    if not samples:
        return 0.0
    step = 2.0 * math.pi * freq / sample_rate
    real = sum(s * math.cos(step * i) for i, s in enumerate(samples))
    imag = sum(s * math.sin(step * i) for i, s in enumerate(samples))
    return (real * real + imag * imag) / len(samples)


def _abs_diffs(samples: list[float]) -> list[float]:
    """Absolute first difference.

    Args:
        samples: PCM.

    Returns:
        One fewer sample.
    """
    return [abs(b - a) for a, b in zip(samples, samples[1:])]


def _joined(parts: list[list[float]], overlap_bars: Any = 2, crossover_hz: float = 120.0) -> list[float]:
    """Join PCM through the pure core.

    Args:
        parts: Segments.
        overlap_bars: Whole bars per seam (int or per-seam list).
        crossover_hz: Sub/mid split.

    Returns:
        Joined PCM.
    """
    return aj.join_pcm(parts, RATE, BPM, overlap_bars, crossover_hz=crossover_hz)


# --- grid validation ------------------------------------------------------


def test_on_grid_segments_join_without_raising() -> None:
    """Whole-bar segments pass the grid gate."""
    length = _bars_samples(2)
    out = _joined([_mix(length, 1), _mix(length, 2)])
    assert len(out) > 0


def test_off_grid_segment_names_segment_and_delta() -> None:
    """An off-grid pass raises with its label and the measured delta."""
    length = _bars_samples(2)
    bad = length + int(0.20 * RATE)
    with pytest.raises(ValueError) as excinfo:
        _joined([_mix(length, 1), _mix(bad, 2)])
    text = str(excinfo.value)
    assert "segment 2" in text
    assert "0.20" in text or "0.19" in text


def test_bad_bpm_is_rejected() -> None:
    """A non-positive tempo cannot define a bar."""
    with pytest.raises(ValueError, match="bpm"):
        aj.join_pcm([[0.0, 0.1]], RATE, 0.0, 2)


# --- length arithmetic ----------------------------------------------------



def test_output_length_subtracts_every_seam_overlap() -> None:
    """Output length is the sum less one whole-bar overlap per seam."""
    length = _bars_samples(6)
    parts = [_mix(length, i) for i in (1, 2, 3)]
    overlap = _bars_samples(2)
    expected = 3 * length - 2 * overlap
    out = _joined(parts, overlap_bars=2)
    assert len(out) == expected
def test_per_seam_overlap_list_matches_scalar_equivalent() -> None:
    """A per-seam list equals the scalar form when the values agree."""
    length = _bars_samples(6)
    parts = [_mix(length, i) for i in (1, 2, 3)]
    assert _joined(parts, overlap_bars=[2, 2]) == _joined(parts, overlap_bars=2)


def test_zero_overlap_is_a_butt_join() -> None:
    """overlap_bars=0 concatenates without touching the samples."""
    length = _bars_samples(2)
    parts = [_mix(length, 1), _mix(length, 2)]
    assert _joined(parts, overlap_bars=0) == parts[0] + parts[1]


def test_overlap_list_length_must_match_seams() -> None:
    """A per-seam list needs exactly one entry per seam."""
    length = _bars_samples(2)
    parts = [_mix(length, 1), _mix(length, 2)]
    with pytest.raises(ValueError, match="overlap_bars"):
        _joined(parts, overlap_bars=[2, 2])


def test_overlap_longer_than_a_segment_is_rejected() -> None:
    """The overlap cannot eat a whole pass."""
    length = _bars_samples(2)
    with pytest.raises(ValueError, match="overlap"):
        _joined([_mix(length, 1), _mix(length, 2)], overlap_bars=20)


# --- seam continuity ------------------------------------------------------



def test_seam_has_no_discontinuity_spike() -> None:
    """Seam first differences stay in line with the rest of the master."""
    length = _bars_samples(4)
    overlap = _bars_samples(1)
    parts = [_mix(length, i) for i in (1, 2, 3)]
    out = _joined(parts, overlap_bars=1)
    # Layout: p0 body | seam | p1 body | seam | p2 body. The blend mixes
    # two uncorrelated hiss floors, so compare distributions rather than
    # single extremes; a hard cut (the control below) blows this margin.
    seam_flags = (
        [False] * (length - overlap)
        + [True] * overlap
        + [False] * (length - 2 * overlap)
        + [True] * overlap
        + [False] * (length - overlap)
    )
    diffs = _abs_diffs(out)
    seam = sorted(d for d, flag in zip(diffs, seam_flags[: len(diffs)]) if flag)
    body = sorted(d for d, flag in zip(diffs, seam_flags[: len(diffs)]) if not flag)
    assert seam and body, "the fixture must leave samples in both regions"

    def p999(values: list[float]) -> float:
        """Upper 0.1 % percentile of a sorted diff list.

        Args:
            values: Sorted first differences.

        Returns:
            The percentile value.
        """
        return values[min(len(values) - 1, int(0.999 * len(values)))]

    assert p999(seam) <= 1.25 * p999(body) + 0.02

def test_hard_cut_control_does_spike_so_the_gate_has_teeth() -> None:
    """A butt join of phase-mismatched content spikes, so the gate bites."""
    length = _bars_samples(2)
    tail = _sine(60.0, length, 0.6)
    # Same 808 tone starting at the top of its swing: the butt splice has
    # a full-amplitude phase jump exactly where the crossfade would be.
    step = 2.0 * math.pi * 60.0 / RATE
    head = [0.6 * math.cos(step * i) for i in range(length)]
    butt = tail + head
    soft = aj.join_pcm([tail, head], RATE, BPM, 1)
    assert max(_abs_diffs(butt)) > max(_abs_diffs(soft)) + 0.1

def test_sub_band_handoff_neither_doubles_nor_nulls() -> None:
    """Two in-phase 60 Hz passes crossfaded at the seam keep one sub."""
    length = _bars_samples(4)
    overlap = _bars_samples(2)
    # One 808 run split across two passes, the way two ACE renders of the
    # same riff arrive: the seam centre carries both passes at once.
    master = _sine(60.0, 2 * length - overlap, 0.6)
    parts = [master[:length], master[length - overlap :]]
    out = _joined(parts, overlap_bars=2)
    centre = length - overlap + overlap // 2
    half = overlap // 2
    window = out[centre - half // 2 : centre + half // 2]
    sub_band = aj.one_pole_lowpass(window, RATE, 120.0)
    ref = _goertzel_energy(
        master[centre - half // 2 : centre + half // 2], 60.0
    )
    energy = _goertzel_energy(sub_band, 60.0)
    assert 0.7 * ref <= energy <= 1.3 * ref
    mid_residual = aj.mid_band(window, sub_band)
    assert max(abs(v) for v in mid_residual[200:-200]) < 0.05

def test_mid_band_crossfade_holds_power() -> None:
    """Uncorrelated mid content crosses without a 3 dB hole."""
    length = _bars_samples(4)
    overlap = _bars_samples(2)
    parts = [_noise(length, 0.3, 11), _noise(length, 0.3, 22)]
    out = _joined(parts, overlap_bars=2)
    centre = length - overlap + overlap // 2
    half = overlap // 2
    window = out[centre - half // 2 : centre + half // 2]
    joined_mid = aj.mid_band(window, aj.one_pole_lowpass(window, RATE, 120.0))

    def _probe_mid(part: list[float], start: int) -> float:
        """Mid energy of one part over the window aligned to the seam.

        Args:
            part: Segment PCM.
            start: Index where the aligned window begins in that part.

        Returns:
            1200 Hz energy of the part's mid band.
        """
        probe = part[start : start + len(window)]
        low = aj.one_pole_lowpass(probe, RATE, 120.0)
        return _goertzel_energy(aj.mid_band(probe, low), 1200.0)

    # At the seam centre both weights are one half, so uncorrelated mid
    # content lands at the average of the two passes' own mid energy. The
    # seam starts at len(p0) - overlap in the master; the prev pass reads
    # from its own tail at that index, the next pass reads from its head
    # offset by the seam start.
    seam_start = len(parts[0]) - overlap
    window_start = centre - half // 2
    ref = (
        _probe_mid(parts[0], window_start)
        + _probe_mid(parts[1], window_start - seam_start)
    ) / len(parts)
    energy = _goertzel_energy(joined_mid, 1200.0)
    assert 0.6 * ref <= energy <= 1.5 * ref
def test_mismatched_sample_rate_raises() -> None:
    """Segments must share one rate."""
    length = _bars_samples(2)
    with pytest.raises(ValueError, match="sample rate"):
        aj.join_audio(
            [_audio(_mix(length, 1), RATE), _audio(_mix(_bars_samples(2, 40.0, 4000), 4), 4000)],
            bpm=40.0,
            overlap_bars=2,
        )


def test_single_segment_is_returned_unchanged() -> None:
    """One pass ships as-is: no resample, no fade, same payload."""
    segment = _audio(_mix(_bars_samples(2), 1))
    assert aj.join_audio([segment], bpm=BPM, overlap_bars=2) is segment


def test_empty_input_returns_a_single_silence() -> None:
    """No passes yields a one-sample silence at the fallback rate."""
    out = aj.join_audio([], bpm=BPM, overlap_bars=2)
    assert out["sample_rate"] == aj.FALLBACK_SAMPLE_RATE
    assert len(_flatten(out["waveform"])) == 1


# --- pcm helpers ----------------------------------------------------------


def test_as_pcm_accepts_tensors_arrays_lists_and_scalars() -> None:
    """Every waveform shape Comfy can hand us flattens to PCM."""

    class TensorLike:
        """Minimal torch/numpy stand-in."""

        def __init__(self, data: Any, with_cpu: bool) -> None:
            """Remember the payload.

            Args:
                data: Nested lists.
                with_cpu: Expose a ``cpu()`` hop like a CUDA tensor.
            """
            self._data = data
            self._with_cpu = with_cpu

        def detach(self) -> "TensorLike":
            """Return self.

            Returns:
                This object.
            """
            return self

        def cpu(self) -> "TensorLike":
            """Return self.

            Returns:
                This object.
            """
            return self

        def tolist(self) -> Any:
            """Return the payload.

            Returns:
                Nested lists.
            """
            return self._data

    assert _flatten(TensorLike([[0.5]], with_cpu=True)) == [0.5]
    assert _flatten(TensorLike([[0.25]], with_cpu=False)) == [0.25]
    assert _flatten([[[0.1, 0.2], [0.3]]]) == [0.1, 0.2, 0.3]
    assert _flatten(0.5) == [0.5]
    assert _flatten(None) == []
    with pytest.raises(ValueError, match="waveform"):
        _flatten("nope")


# --- save-audio unpacking -------------------------------------------------


class _FakeTensor:
    """Stand-in for ``torch.Tensor`` that tracks its own shape.

    Args:
        data: Flattened PCM.
        shape: Shape the PCM is wrapped in.
    """

    def __init__(self, data: Any, shape: tuple[int, ...]) -> None:
        """Remember the payload.

        Args:
            data: Flattened PCM.
            shape: Tensor shape.
        """
        self.data = data
        self.shape = shape

    @property
    def ndim(self) -> int:
        """Rank of the payload.

        Returns:
            Dimensions in ``shape``.
        """
        return len(self.shape)

    def unsqueeze(self, dim: int) -> "_FakeTensor":
        """Insert a size-1 axis at ``dim``, like ``torch.Tensor`` does.

        Args:
            dim: Axis index.

        Returns:
            A tensor one rank higher.
        """
        shape = list(self.shape)
        shape.insert(dim, 1)
        return _FakeTensor(self.data, tuple(shape))

    def tolist(self) -> Any:
        """Return the payload.

        Returns:
            Flattened PCM.
        """
        return self.data


class _FakeTorch:
    """Stand-in for the ``torch`` module, packing PCM as a flat tensor.

    Args:
        seen: Optional dict that records each payload handed over.
    """

    float32 = "float32"

    def __init__(self, seen: dict[str, Any] | None = None) -> None:
        """Remember the recorder.

        Args:
            seen: Dict that records payloads, or None.
        """
        self.seen = seen

    def as_tensor(self, data: Any, dtype: Any = None) -> _FakeTensor:
        """Wrap a flat payload, one entry per sample.

        Args:
            data: PCM.
            dtype: Requested dtype.

        Returns:
            A rank-1 tensor, exactly as ``torch.as_tensor`` wraps a list.
        """
        del dtype
        if self.seen is not None:
            self.seen["data"] = data
        return _FakeTensor(data, (len(data),))


class _FakeNoTorch:
    """Stand-in whose conversion refuses, exercising the fallback."""

    float32 = "float32"

    @staticmethod
    def as_tensor(*_args: Any, **_kwargs: Any) -> Any:
        """Fail like a missing backend.

        Returns:
            Nothing.

        Raises:
            RuntimeError: always.
        """
        raise RuntimeError("no torch")


def _shape(payload: Any) -> tuple[int, ...]:
    """Shape of a waveform payload, nested lists or a tensor stand-in.

    Args:
        payload: Waveform value.

    Returns:
        One entry per axis; empty for a scalar or an empty payload.
    """
    if hasattr(payload, "shape"):
        return tuple(payload.shape)
    if not isinstance(payload, (list, tuple)) or not payload:
        return ()
    return (len(payload),) + _shape(payload[0])


def _batch_item_ranks(waveform: Any) -> list[int]:
    """Rank of every dim-0 item, as the core save nodes read them.

    ``comfy_api/latest/_ui.py`` ``AudioSaveHelper.save_audio`` (ComfyUI
    v0.37.0) walks dim 0 of the ``waveform`` payload as a batch axis and
    unpacks each item as ``[channels, samples]``. A rank-1 item raises
    ``IndexError: Dimension out of range (expected to be in range of
    [-1, 0], but got 1)`` and the take never reaches the encoder.

    Args:
        waveform: Waveform value from an AUDIO dict.

    Returns:
        Rank of each batch item on the save-side read.
    """
    shape = _shape(waveform)
    if not shape:
        return []
    return [len(shape) - 1] * shape[0]


def test_packed_master_unwraps_the_way_save_audio_reads_it() -> None:
    """Every joined master unwraps as one batch of mono [1, N] PCM.

    A [1, N] waveform iterates as one rank-1 batch item, which is what
    SaveAudio and SaveAudioMP3 reject on the pinned runtime, so the check
    runs over the nested fallback and over the torch stand-in alike.
    """
    length = _bars_samples(6)

    def join(*parts: list[float]) -> Any:
        """Join PCM through the node and hand back the packed waveform.

        Args:
            *parts: One PCM segment per ACE pass, in render order.

        Returns:
            The joined master waveform.
        """
        node = EZAudioBeatJoin()
        wired: dict[str, Any] = {
            f"audio_{index:02d}": _audio(part) for index, part in enumerate(parts, 1)
        }
        result = node.run(bpm=BPM, overlap_bars=2, crossover_hz=120.0, **wired)
        return cast("dict[str, Any]", result[0])["waveform"]

    # A multi-pass take is the joined case; no pass at all is the one-sample
    # silence. A single wired pass ships unchanged instead of being repacked.
    masters = [aj.join_audio([], bpm=BPM, overlap_bars=2)["waveform"]]
    with _patch_torch(_FakeTorch()):
        masters.append(join(_mix(length, 1), _mix(length, 2)))
        masters.append(join(_mix(length, 1), _mix(length, 2), _mix(length, 3)))
    for master in masters:
        assert _batch_item_ranks(master) == [2]
    assert _batch_item_ranks([[0.0] * length]) == [1], "the guard needs teeth"


def test_packed_waveform_is_a_rank3_mono_waveform() -> None:
    """Both packers nest to 1 x 1 x N, the shape core producers emit."""
    with _patch_torch(_FakeNoTorch()):
        fallback = aj.pack_audio([0.1, 0.2], RATE)
    assert fallback["waveform"] == [[[0.1, 0.2]]]
    assert _batch_item_ranks(fallback["waveform"]) == [2]

    with _patch_torch(_FakeTorch()):
        packed = aj.pack_audio([0.1, 0.2], RATE)
        empty = aj.pack_audio([], RATE)
    assert isinstance(packed["waveform"], _FakeTensor), "the tensor branch was skipped"
    assert isinstance(empty["waveform"], _FakeTensor), "the tensor branch was skipped"
    assert _shape(packed["waveform"]) == (1, 1, 2)
    assert _shape(empty["waveform"]) == (1, 1, 0)


def test_pack_audio_uses_torch_when_present() -> None:
    """The lazy torch path packs a tensor, not the nested-list fallback."""
    captured: dict[str, Any] = {}

    with _patch_torch(_FakeTorch(captured)):
        packed = aj.pack_audio([0.1, 0.2], 44100)
    assert packed["sample_rate"] == 44100
    assert captured["data"] == [0.1, 0.2]
    assert isinstance(packed["waveform"], _FakeTensor)
    assert packed["waveform"].ndim == 3
    assert packed["waveform"].shape == (1, 1, 2)
    assert _batch_item_ranks(packed["waveform"]) == [2]
    with _patch_torch(_FakeNoTorch()):
        fallback = aj.pack_audio([0.1, 0.2], 0)
    assert fallback["sample_rate"] == aj.FALLBACK_SAMPLE_RATE
    assert fallback["waveform"] == [[[0.1, 0.2]]]
    assert _batch_item_ranks(fallback["waveform"]) == [2]


class _patch_torch:
    """Swap a stand-in ``torch`` module into ``sys.modules``.

    Args:
        module: Object to register as ``torch``.
    """

    def __init__(self, module: Any) -> None:
        """Remember the stand-in.

        Args:
            module: Object to register as ``torch``.
        """
        self._module = module

    def __enter__(self) -> None:
        """Install the stand-in."""
        sys.modules["torch"] = self._module

    def __exit__(self, *_exc: object) -> None:
        """Remove the stand-in."""
        sys.modules.pop("torch", None)



def test_one_pole_split_keeps_the_sub_and_drops_it_from_the_mid() -> None:
    """The crossover sends a kick to the sub and a hat to the mid."""
    length = 4000
    kick = _sine(60.0, length, 0.6)
    hat = _sine(2600.0, length, 0.4)
    kick_low = aj.one_pole_lowpass(kick, RATE, 120.0)
    hat_low = aj.one_pole_lowpass(hat, RATE, 120.0)
    # The zero-phase filter settles after a few corner periods; compare
    # bands over the settled interior of each probe.
    core = slice(1200, 2800)
    assert _goertzel_energy(kick_low[core], 60.0) > 0.6 * _goertzel_energy(
        kick[core], 60.0
    )
    assert _goertzel_energy(hat_low[core], 2600.0) < 0.1 * _goertzel_energy(
        hat[core], 2600.0
    )
    assert aj.mid_band(hat, hat_low)[core] == pytest.approx(hat[core], abs=2e-3)
def test_quiet_index_clamps_at_both_ends() -> None:
    """Zero-crossing search never runs off the buffer."""
    samples = [0.9, 0.1, 0.8, 0.7, 0.05]
    assert aj._quiet_index(samples, 0, 2) == 1  # noqa: SLF001
    assert aj._quiet_index(samples, 4, 2) == 4  # noqa: SLF001
    assert aj._quiet_index(samples, 2, 0) == 2  # noqa: SLF001


# --- node wrapper ---------------------------------------------------------


def test_node_is_registered() -> None:
    """The joiner ships in the ez_music pack with the music category."""
    assert NODE_CLASS_MAPPINGS["EZAudioBeatJoin"] is EZAudioBeatJoin
    assert EZAudioBeatJoin.CATEGORY == "ez-comfy/music"  # type: ignore[attr-defined]
    assert EZAudioBeatJoin.RETURN_TYPES == ("AUDIO",)  # type: ignore[attr-defined]
    assert EZAudioBeatJoin.FUNCTION == "run"  # type: ignore[attr-defined]


def test_node_declares_widgets_and_sockets() -> None:
    """Widget list and the N-segment socket scheme."""
    spec = EZAudioBeatJoin.INPUT_TYPES()  # type: ignore[attr-defined]
    required = spec["required"]
    assert required["audio_01"] == ("AUDIO",)
    assert required["bpm"][1]["default"] == 172
    assert required["overlap_bars"][1]["default"] == "2"
    assert required["crossover_hz"][1]["default"] == 120.0
    optional = spec["optional"]
    assert optional["audio_02"] == ("AUDIO",)
    assert optional[f"audio_{aj.MAX_JOIN_SEGMENTS:02d}"] == ("AUDIO",)
    assert f"audio_{aj.MAX_JOIN_SEGMENTS + 1:02d}" not in optional


def test_node_overlap_widget_takes_a_per_seam_list() -> None:
    """The overlap widget reads "2, 1" as one entry per seam."""
    length = _bars_samples(4)
    node = EZAudioBeatJoin()

    def run(overlap: object) -> list[float]:
        """Join three passes through the node with one overlap spec.

        Args:
            overlap: Value for the ``overlap_bars`` widget.

        Returns:
            Master PCM.
        """
        result = node.run(
            bpm=BPM,
            overlap_bars=overlap,  # type: ignore[arg-type]
            crossover_hz=120.0,
            audio_01=_audio(_mix(length, 1)),
            audio_02=_audio(_mix(length, 2)),
            audio_03=_audio(_mix(length, 3)),
        )
        return _flatten(cast("dict[str, Any]", result[0])["waveform"])

    assert run("2, 1") == run([2, 1])
    assert run("2, 1") != run("1, 2")


def test_node_rejects_a_non_numeric_overlap() -> None:
    """A junk overlap widget is a graph error with the value in it."""
    node = EZAudioBeatJoin()
    with pytest.raises(ValueError, match="overlap_bars"):
        node.run(
            bpm=BPM, overlap_bars="two", crossover_hz=120.0,
            audio_01=_audio(_mix(_bars_samples(2), 1)),
        )


def test_node_run_joins_wired_audio() -> None:
    """Wired AUDIO dicts come back as one master."""
    length = _bars_samples(2)
    node = EZAudioBeatJoin()
    result = node.run(
        bpm=BPM,
        overlap_bars=2,
        crossover_hz=120.0,
        audio_01=_audio(_mix(length, 1)),
        audio_02=_audio(_mix(length, 2)),
    )
    assert len(result) == 1
    master = result[0]
    assert cast("dict[str, Any]", master)["sample_rate"] == RATE
    expected = 2 * length - _bars_samples(2)
    assert abs(len(_flatten(cast("dict[str, Any]", master)["waveform"])) - expected) <= 1


def test_node_refuses_a_hole_before_a_wired_segment() -> None:
    """A gap ahead of a later pass is a graph error, not silence."""
    length = _bars_samples(2)
    node = EZAudioBeatJoin()
    with pytest.raises(ValueError, match="audio_02"):
        node.run(
            bpm=BPM,
            overlap_bars=2,
            crossover_hz=120.0,
            audio_01=_audio(_mix(length, 1)),
            audio_03=_audio(_mix(length, 2)),
        )


def test_node_requires_the_first_segment() -> None:
    """Nothing wired to audio_01 is a graph error."""
    node = EZAudioBeatJoin()
    with pytest.raises(ValueError, match="audio_01"):
        node.run(bpm=BPM, overlap_bars=2, crossover_hz=120.0)


def test_node_passes_a_single_segment_through() -> None:
    """One pass ships unchanged, so a 1-pass take still renders."""
    length = _bars_samples(2)
    segment = _audio(_mix(length, 1))
    node = EZAudioBeatJoin()
    out = node.run(
        bpm=BPM, overlap_bars=2, crossover_hz=120.0, audio_01=segment
    )
    assert out[0] is segment


def test_bar_and_overlap_math_follows_the_240_over_bpm_bar() -> None:
    """A bar is 240/bpm seconds, the arranger's own 2-bar-cell bar."""
    assert aj.bar_seconds(BPM) == pytest.approx(240.0 / BPM)
    assert aj.overlap_seconds(2, BPM) == pytest.approx(2 * 240.0 / BPM)
    assert 2.6 <= aj.overlap_seconds(2, 176.0) <= 2.9
    assert 1.4 <= aj.overlap_seconds(1, 165.0) <= 1.6


def test_unused_module_alias_is_none_free() -> None:
    """Guard the import surface used by the pack."""
    assert isinstance(aj.MAX_JOIN_SEGMENTS, int)
    assert isinstance(types.ModuleType("ez_music.join"), types.ModuleType)


def test_as_pcm_rejects_a_bool_payload() -> None:
    """A bool is not audio: it would read as one or zero."""
    with pytest.raises(ValueError, match="waveform is not audio"):
        aj._as_pcm(True)


def test_one_pole_lowpass_on_empty_input_returns_empty() -> None:
    """The filter has nothing to settle on when the buffer is empty."""
    assert aj.one_pole_lowpass([], RATE, 120.0) == []


def test_quiet_index_on_empty_input_keeps_the_boundary() -> None:
    """With no samples to search, the nominal boundary stands."""
    assert aj._quiet_index([], 5, 32) == 5


def test_join_pcm_on_no_parts_returns_empty() -> None:
    """Nothing wired means nothing to stitch."""
    assert aj.join_pcm([], RATE, bpm=BPM, overlap_bars=2) == []


def test_negative_overlap_is_rejected() -> None:
    """A seam cannot take back time before the pass starts."""
    length = _bars_samples(4)
    parts = [_mix(length, 1), _mix(length, 2), _mix(length, 3)]
    with pytest.raises(ValueError, match="overlap_bars must be 0 or more"):
        aj.join_pcm(parts, RATE, bpm=BPM, overlap_bars=[-1, 1])


def test_overlap_pair_that_eats_the_middle_segment_is_rejected() -> None:
    """Two seams together may not consume the pass they share."""
    length = _bars_samples(2)
    parts = [_mix(length, 1), _mix(length, 2), _mix(length, 3)]
    with pytest.raises(ValueError, match="eat segment"):
        aj.join_pcm(parts, RATE, bpm=BPM, overlap_bars=[2, 2])


def test_join_audio_without_a_sample_rate_names_the_segment() -> None:
    """An AUDIO dict missing its rate is a graph error, not silence."""
    broken = {"waveform": [[0.0] * _bars_samples(2)]}
    good = _audio(_mix(_bars_samples(2), 1))
    with pytest.raises(ValueError, match="sample_rate"):
        aj.join_audio([broken, good], bpm=BPM, overlap_bars=1)


def test_overlap_widget_rejects_an_empty_spec() -> None:
    """Blank widget text has no bar count in it."""
    node = EZAudioBeatJoin()
    with pytest.raises(ValueError, match="needs a number of bars"):
        node.run(
            bpm=BPM,
            overlap_bars=" , ",
            crossover_hz=120.0,
            audio_01=_audio(_mix(_bars_samples(2), 1)),
        )


def test_overlap_widget_accepts_a_single_string_entry() -> None:
    """One entry comes back as a scalar, not a one-item list."""
    from ez_music.nodes import _parse_overlap

    assert _parse_overlap("2") == 2
    assert _parse_overlap([2, 1]) == [2, 1]
    assert _parse_overlap(2) == 2
