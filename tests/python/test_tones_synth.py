"""Hermetic tests for the pure-Python tone synthesiser."""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import cast

import pytest

ROOT = Path(__file__).resolve().parents[2]
CUSTOM = ROOT / "custom_nodes"
if str(CUSTOM) not in sys.path:
    sys.path.insert(0, str(CUSTOM))

from ez_tones.synth import (  # noqa: E402
    A4_HZ,
    DECAY_K,
    PEAK_CEILING,
    TIMBRES,
    WAVETABLE_LEN,
    Motif,
    Timbre,
    Voice,
    additive_wave,
    adsr_envelope,
    apply_fades,
    hz_to_midi,
    interleave,
    midi_to_hz,
    motif_duration,
    ms_to_samples,
    normalise,
    render_motif,
    render_note,
    voice_for,
)


def test_midi_to_hz_uses_equal_temperament() -> None:
    """A4 is 440 and one semitone up is 440 * 2**(1/12)."""
    assert midi_to_hz(69) == pytest.approx(A4_HZ)
    assert midi_to_hz(70) == pytest.approx(A4_HZ * 2.0 ** (1.0 / 12.0))
    assert midi_to_hz(57) == pytest.approx(220.0)


def test_hz_to_midi_round_trips() -> None:
    """Every note survives a trip through the frequency domain."""
    for pitch in range(21, 109):
        assert hz_to_midi(midi_to_hz(pitch)) == pitch
    assert hz_to_midi(440.0) == 69


def test_hz_to_midi_rejects_a_flat_frequency() -> None:
    """Zero and negative frequencies have no note."""
    with pytest.raises(ValueError, match="freq must be > 0"):
        hz_to_midi(0.0)
    with pytest.raises(ValueError, match="freq must be > 0"):
        hz_to_midi(-12.5)


def test_ms_to_samples_rounds_and_floors_at_zero() -> None:
    """Millisecond maths stays whole and never negative."""
    assert ms_to_samples(0.5, 44100) == 22
    assert ms_to_samples(1000.0, 48000) == 48000
    assert ms_to_samples(-20.0, 44100) == 0


def test_additive_wave_rejects_bad_requests() -> None:
    """Silent length, flat pitch, and super-Nyquist all fail loudly."""
    assert additive_wave(440.0, (1.0,), 0, 48000) == []
    with pytest.raises(ValueError, match="freq must be > 0"):
        additive_wave(0.0, (1.0,), 8, 48000)
    with pytest.raises(ValueError, match="at or above Nyquist"):
        additive_wave(24000.0, (1.0,), 8, 48000)


def test_additive_wave_tracks_the_fundamental() -> None:
    """A sine table crosses zero twice per period."""
    rate = 48000
    freq = 1000.0
    wave = additive_wave(freq, (1.0,), rate, rate)
    assert len(wave) == rate
    assert max(abs(value) for value in wave) <= 1.0 + 1e-9
    crossings = sum(1 for i in range(1, len(wave)) if wave[i - 1] <= 0.0 < wave[i])
    assert crossings == pytest.approx(freq, rel=0.01)


def test_additive_wave_skips_absent_partials() -> None:
    """An all-zero harmonic list renders silence, not a divide by zero."""
    assert additive_wave(440.0, (0.0, 0.0), 6, 48000) == [0.0] * 6


def test_additive_wave_wraps_the_table_and_its_phase() -> None:
    """A near-Nyquist tone walks off both ends of the wavetable."""
    wave = additive_wave(23999.0, (1.0, 0.5), 4, 48000)
    assert len(wave) == 4
    assert all(abs(value) <= 1.0 for value in wave)


def test_adsr_envelope_shapes_all_four_stages() -> None:
    """Attack rises, decay falls to the held level, release ends low."""
    rate = 48000
    env = adsr_envelope(rate, rate, 10.0, 20.0, 0.4, 10.0)
    assert len(env) == rate
    assert env[0] == pytest.approx(1.0 / (ms_to_samples(10.0, rate) + 1))
    assert max(env) <= 1.0
    held = env[-ms_to_samples(30.0, rate)]
    assert held == pytest.approx(0.4 + 0.6 * math.exp(-DECAY_K), rel=1e-6)
    assert env[-1] < held


def test_adsr_envelope_arcs_a_note_too_short_for_ramps() -> None:
    """A four-sample step gets one smooth arc instead of clipped ramps."""
    env = adsr_envelope(4, 48000, 10.0, 20.0, 0.5, 10.0)
    assert len(env) == 4
    assert all(0.0 < value < 1.0 for value in env)
    assert env[0] < env[1] and env[2] > env[3]


def test_adsr_envelope_of_nothing_is_nothing() -> None:
    """A zero-length note has no gain curve."""
    assert adsr_envelope(0, 48000, 5.0, 5.0, 0.5, 5.0) == []


def test_voice_for_knows_every_timbre() -> None:
    """Every published timbre resolves to a usable voice."""
    for timbre in TIMBRES:
        voice = voice_for(timbre)
        assert isinstance(voice, Voice)
        assert voice.harmonics[0] == 1.0
        assert 0.0 <= voice.sustain <= 1.0


def test_voice_for_names_an_unknown_timbre() -> None:
    """A typo in a catalog row says which timbre it did not know."""
    with pytest.raises(ValueError, match="unknown timbre 'hollow'"):
        voice_for(cast(Timbre, "hollow"))


def test_render_note_applies_the_envelope() -> None:
    """A note has the requested length and stays inside its gain."""
    samples = render_note(69, 0.25, 0.8, "marimba", 44100)
    assert len(samples) == ms_to_samples(250.0, 44100)
    assert max(abs(value) for value in samples) <= 0.8 + 1e-9


def test_render_note_clamps_velocity() -> None:
    """Velocity outside 0..1 is pinned, not obeyed."""
    loud = render_note(69, 0.1, 3.0, "sine", 44100)
    full = render_note(69, 0.1, 1.0, "sine", 44100)
    silent = render_note(69, 0.1, -1.0, "sine", 44100)
    assert loud == pytest.approx(full)
    assert set(silent) == {0.0}


def test_render_note_of_no_length_is_silent() -> None:
    """A zero-second note renders nothing."""
    assert render_note(69, 0.0, 0.9, "pluck", 44100) == []


def test_normalise_hits_the_ceiling() -> None:
    """The loudest sample lands exactly on the stated ceiling."""
    scaled = normalise([0.5, -0.25], 0.8)
    assert max(abs(value) for value in scaled) == pytest.approx(0.8)
    assert scaled[0] == pytest.approx(0.8)


def test_normalise_handles_empty_and_silent_frames() -> None:
    """Nothing to scale stays nothing, and silence stays silence."""
    assert normalise([]) == []
    assert normalise([0.0, 0.0, 0.0]) == [0.0, 0.0, 0.0]


def test_normalise_pins_an_out_of_range_ceiling() -> None:
    """A ceiling past full scale cannot clip, and a negative one is silence."""
    assert max(abs(value) for value in normalise([2.0], 4.0)) == pytest.approx(1.0)
    assert normalise([0.5], -1.0) == [0.0]


def test_apply_fades_ramps_both_ends() -> None:
    """Head and tail ramp to silence, and the middle is untouched."""
    rate = 48000
    body = [0.5] * ms_to_samples(50.0, rate)
    faded = apply_fades(body, rate, 10.0)
    assert faded[0] == pytest.approx(0.0, abs=0.05)
    assert faded[-1] == pytest.approx(0.0, abs=0.05)
    assert faded[len(faded) // 2] == 0.5
    assert faded[0] == faded[-1]


def test_apply_fades_leaves_a_frame_too_short_to_ramp() -> None:
    """One sample has no room for a fade, so it is returned as is."""
    assert apply_fades([], 48000) == []
    assert apply_fades([0.4], 48000, 10.0) == [0.4]


def test_interleave_dups_the_mono_channel() -> None:
    """Stereo carries the same level on both sides at a sub-ms offset."""
    rate = 48000
    mono = [0.25] * ms_to_samples(10.0, rate)
    stereo = interleave(mono, 2, rate)
    assert len(stereo) == 2 * len(mono)
    assert stereo[2] == 0.25
    assert stereo[3] == 0.0
    assert stereo[-2] == 0.25


def test_interleave_mono_and_rejects_odd_channel_counts() -> None:
    """Mono passes straight through; three channels is a bug."""
    assert interleave([0.1, 0.2], 1) == [0.1, 0.2]
    with pytest.raises(ValueError, match="channels must be 1 or 2"):
        interleave([0.1], 3)


def test_render_motif_places_rests_and_peaks_at_the_ceiling() -> None:
    """A rest occupies its length and the frame never clips."""
    motif: Motif = ((69, 0.2, 0.9), (None, 0.1, 0.0), (76, 0.2, 0.9))
    samples = render_motif(motif, "bell", 44100)
    assert len(samples) == ms_to_samples(motif_duration(motif) * 1000.0, 44100)
    assert max(abs(value) for value in samples) == pytest.approx(PEAK_CEILING)
    rest_start = ms_to_samples(200.0, 44100)
    rest_mid = rest_start + ms_to_samples(50.0, 44100)
    assert samples[rest_mid] == pytest.approx(0.0, abs=0.02)


def test_render_motif_is_deterministic_and_loop_clean() -> None:
    """Two renders agree to the bit and the seam is silent."""
    motif: Motif = ((60, 0.3, 0.9), (64, 0.3, 0.8), (67, 0.4, 0.7))
    first = render_motif(motif, "glass", 44100)
    second = render_motif(motif, "glass", 44100)
    assert first == second
    assert abs(first[0]) < 1e-6
    assert abs(first[-1]) < 1e-6


def test_render_motif_of_nothing_is_silence() -> None:
    """An empty motif renders an empty frame."""
    assert render_motif((), "synth", 44100) == []


def test_motif_duration_adds_the_steps() -> None:
    """Duration is the sum of step lengths, rounded to milliseconds."""
    assert motif_duration(((69, 0.125, 0.9), (None, 0.25, 0.0))) == 0.375
    assert motif_duration(()) == 0.0


def test_wavetable_length_is_a_shared_constant() -> None:
    """The table size is the one the phase walk assumes."""
    assert WAVETABLE_LEN == 2048
    assert len(TIMBRES) == 7
