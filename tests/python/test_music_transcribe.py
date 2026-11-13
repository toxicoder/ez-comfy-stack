"""Hermetic tests for the stdlib transcriber: FFT, flux, sieve, tempo, lanes.

No ffmpeg and no third-party DSP are needed: every decode goes through a
monkeypatched :func:`subprocess.run`, so the tests feed the module the raw
float PCM ffmpeg would have written and assert what the analysis makes of it.
The deterministic end-to-end case synthesises a known song out of ``math``
alone and checks that the recovered pitches and tempo are the ones that went
in.
"""

from __future__ import annotations

import array
import math
from dataclasses import dataclass

import pytest
from ez_music import transcribe
from ez_music.timeline import (
    DEFAULT_BPM,
    Note,
    TempoMap,
    Timeline,
    Track,
)

RATE = 16000
FRAME = 1024
HOP = 256
SPECTRUM_WIDTH = FRAME // 2 + 1
LEAD_HARMONICS = (1.0, 0.45, 0.22, 0.12, 0.06)
SONG_SECONDS = 8.0
SONG_BPM = 120.0
BASS_RIFF = (41, 41, 48, 45)
MELODY_LINE = (72, 74, 76, 79, 77, 76, 74, 72)


@dataclass(frozen=True)
class _FakeProcess:
    """What ffmpeg would have handed back on the other side of a pipe.

    Args:
        returncode: Exit status of the decode.
        stdout: Raw PCM bytes written to the pipe.
        stderr: Decoder diagnostics.
    """

    returncode: int
    stdout: bytes
    stderr: bytes


def _pcm_bytes(samples: list[float]) -> bytes:
    """Encode samples the way ffmpeg writes ``f32le``.

    Args:
        samples: Mono samples in -1.0 to 1.0.
    Returns:
        Little-endian float32 bytes.
    """
    buffer = array.array("f", samples)
    return buffer.tobytes()


def _install_ffmpeg(
    monkeypatch: pytest.MonkeyPatch,
    samples: list[float],
    returncode: int = 0,
    stderr: bytes = b"",
) -> list[list[str]]:
    """Replace the subprocess call decode_audio makes.

    Args:
        monkeypatch: pytest monkeypatch fixture.
        samples: Mono samples the fake ffmpeg "decodes" to.
        returncode: Exit status the fake reports.
        stderr: Diagnostics the fake writes to stderr.
    Returns:
        List that collects the argv of every call made.
    """
    calls: list[list[str]] = []
    payload = _pcm_bytes(samples)

    def _run(command: list[str], **kwargs: object) -> _FakeProcess:
        calls.append(list(command))
        return _FakeProcess(returncode, payload, stderr)

    monkeypatch.setattr(transcribe.subprocess, "run", _run)
    return calls


def _sine_take(
    seconds: float = 1.0,
    pitch: int = 69,
    gain: float = 0.5,
    harmonics: tuple[float, ...] = LEAD_HARMONICS,
) -> list[float]:
    """Synthesise a single decaying tone.

    Args:
        seconds: Length of the take.
        pitch: MIDI note number of the fundamental.
        gain: Amplitude multiplier.
        harmonics: Amplitude of each partial, fundamental first.
    Returns:
        Mono samples at the analysis rate.
    """
    total = int(seconds * RATE)
    base = transcribe.midi_to_hz(pitch)
    samples: list[float] = []
    for index in range(total):
        at = index / RATE
        envelope = min(1.0, index / (0.01 * RATE)) * math.exp(-1.8 * at)
        value = 0.0
        for order, weight in enumerate(harmonics, start=1):
            if base * order > RATE / 2.0:
                break
            value += weight * math.sin(2.0 * math.pi * base * order * at)
        samples.append(gain * envelope * value)
    return samples


def _spike_spectrum(
    partial_amps: dict[int, float],
    size: int = FRAME,
    sample_rate: int = RATE,
) -> list[float]:
    """Build a magnitude frame with energy at a pitch and its overtones.

    Args:
        partial_amps: Amplitude per MIDI pitch; overtones decay by 0.6 each.
        size: FFT size the frame came from.
        sample_rate: Sample rate the frame came from.
    Returns:
        One magnitude spectrum, DC first.
    """
    frame = [0.0] * (size // 2 + 1)
    for pitch, amplitude in partial_amps.items():
        base = transcribe.midi_to_hz(pitch)
        for order in range(1, 9):
            bin_index = round(base * order * size / sample_rate)
            if bin_index > size // 2:
                break
            frame[bin_index] = max(frame[bin_index], amplitude * 0.6 ** (order - 1))
    return frame


def _tone_spectrum(
    pitch: int,
    harmonics: tuple[float, ...] = LEAD_HARMONICS,
) -> list[float]:
    """Build a magnitude frame for one harmonic tone.

    Args:
        pitch: MIDI note number of the fundamental.
        harmonics: Amplitude of each partial, fundamental first.
    Returns:
        One magnitude spectrum, DC first.
    """
    frame = [0.0] * SPECTRUM_WIDTH
    base = transcribe.midi_to_hz(pitch)
    for order, weight in enumerate(harmonics, start=1):
        bin_index = round(base * order * FRAME / RATE)
        if bin_index > FRAME // 2:
            break
        frame[bin_index] = weight
    return frame


def _attack_frames(
    spectrum: list[float],
    frames: int = 20,
    onset: int = 4,
) -> transcribe.FrameSet:
    """Wrap a spectrum in a FrameSet that goes loud at one attack.

    Args:
        spectrum: Magnitude frame the attack sounds with.
        frames: Number of frames to build.
        onset: Frame index where the energy arrives.
    Returns:
        FrameSet the lane segmenter can work on.
    """
    quiet = [0.0] * SPECTRUM_WIDTH
    return transcribe.FrameSet(
        [list(spectrum) if index >= onset else list(quiet) for index in range(frames)],
        RATE,
        HOP,
    )


def _band_frame(sub_level: float, mid_level: float, high_level: float) -> list[float]:
    """Build a frame whose three analysis bands carry set per-bin levels.

    The bands share the bin at 120 Hz, so the sub band is written last and
    owns that bin: ``classify_percussion`` counts it in both the sub and the
    mid sum, exactly as it does on real audio.

    Args:
        sub_level: Magnitude in every bin below 120 Hz.
        mid_level: Magnitude in every bin between 120 Hz and 4 kHz.
        high_level: Magnitude in every bin above 4 kHz.
    Returns:
        One magnitude spectrum for :func:`transcribe.classify_percussion`.
    """
    frame = [0.0] * SPECTRUM_WIDTH
    for low_hz, high_hz, level in (
        (4000.0, 16000.0, high_level),
        (120.0, 4000.0, mid_level),
        (20.0, 120.0, sub_level),
    ):
        low, high = transcribe.band_edges(low_hz, high_hz, FRAME, RATE)
        for index in range(low, high):
            frame[index] = level
    return frame


def _impulse_train(bpm: float, seconds: float, amplitude: float = 1.0) -> list[float]:
    """Build an onset envelope with an attack on every beat.

    Args:
        bpm: Tempo the envelope repeats at.
        seconds: Length of the envelope.
        amplitude: Height of each attack.
    Returns:
        One value per analysis frame.
    """
    seconds_per_frame = HOP / RATE
    count = int(seconds / seconds_per_frame)
    envelope = [0.0] * count
    period = (60.0 / bpm) / seconds_per_frame
    for beat in range(int(count / period) + 1):
        index = round(beat * period)
        if 0 <= index < count:
            envelope[index] = amplitude
    return envelope


def _add_tone(
    buffer: list[float],
    start_s: float,
    pitch: int,
    length_s: float,
    gain: float,
    harmonics: tuple[float, ...],
) -> None:
    """Mix one decaying harmonic tone into a sample buffer.

    Args:
        buffer: Samples to add into, modified in place.
        start_s: Attack time in seconds.
        pitch: MIDI note number of the fundamental.
        length_s: Sounding length in seconds.
        gain: Amplitude multiplier.
        harmonics: Amplitude of each partial, fundamental first.
    """
    base = transcribe.midi_to_hz(pitch)
    first = int(start_s * RATE)
    for index in range(int(length_s * RATE)):
        position = first + index
        if position >= len(buffer):
            break
        at = index / RATE
        envelope = min(1.0, index / (0.01 * RATE)) * math.exp(-1.8 * at)
        value = 0.0
        for order, weight in enumerate(harmonics, start=1):
            if base * order > RATE / 2.0:
                break
            value += weight * math.sin(2.0 * math.pi * base * order * at)
        buffer[position] += gain * envelope * value


def _add_kick(buffer: list[float], start_s: float) -> None:
    """Mix one kick drum into a sample buffer.

    Args:
        buffer: Samples to add into, modified in place.
        start_s: Attack time in seconds.
    """
    first = int(start_s * RATE)
    for index in range(int(0.16 * RATE)):
        position = first + index
        if position >= len(buffer):
            break
        at = index / RATE
        frequency = 70.0 * math.exp(-18.0 * at) + 40.0
        buffer[position] += 0.9 * math.exp(-22.0 * at) * math.sin(2.0 * math.pi * frequency * at)


def _add_hat(buffer: list[float], start_s: float, seed: int = 12345) -> int:
    """Mix one deterministic noise-burst hat into a sample buffer.

    Args:
        buffer: Samples to add into, modified in place.
        start_s: Attack time in seconds.
        seed: State of the linear congruential noise generator.
    Returns:
        The noise generator state after the burst, for the next call.
    """
    first = int(start_s * RATE)
    state = seed
    for index in range(int(0.05 * RATE)):
        position = first + index
        if position >= len(buffer):
            break
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        noise = (state / 0x7FFFFFFF) - 0.5
        buffer[position] += 0.25 * math.exp(-60.0 * (index / RATE)) * noise
    return state


def _normalise(buffer: list[float], peak: float = 0.85) -> list[float]:
    """Scale a buffer to a safe peak level.

    Args:
        buffer: Mixed samples.
        peak: Target peak amplitude.
    Returns:
        Normalised samples.
    """
    loudest = max(abs(value) for value in buffer) or 1.0
    return [value / loudest * peak for value in buffer]


def _song_samples(seconds: float = SONG_SECONDS) -> list[float]:
    """Synthesise the take the end-to-end tests transcribe.

    Args:
        seconds: Length of the take; the full song needs eight.
    Returns:
        Mono samples at the analysis rate: kick on every beat, a hat on the off
        beat, a bass riff one note per bar, and a melody one note per beat.
    """
    beat_s = 60.0 / SONG_BPM
    buffer = [0.0] * int(seconds * RATE)
    state = 12345
    for beat in range(int(seconds / beat_s)):
        start = beat * beat_s
        _add_kick(buffer, start)
        if beat % 2 == 1:
            state = _add_hat(buffer, start + beat_s / 2.0, state)
        _add_tone(
            buffer,
            start,
            BASS_RIFF[(beat // 4) % len(BASS_RIFF)],
            beat_s * 0.95,
            0.5,
            (1.0, 0.3, 0.1),
        )
        _add_tone(
            buffer,
            start,
            MELODY_LINE[beat % len(MELODY_LINE)],
            beat_s * 0.9,
            0.28,
            LEAD_HARMONICS,
        )
    return _normalise(buffer)


def _lane_track(lane: transcribe.LaneSpec, samples: list[float]) -> Track:
    """Transcribe one lane of a synthesised take.

    Args:
        lane: Lane to segment.
        samples: Mono samples at the analysis rate.
    Returns:
        Lane with whatever notes the analysis found.
    """
    settings = transcribe.AnalysisSettings()
    frames = transcribe.stft(samples, settings)
    return transcribe.transcribe_lane(lane, frames, settings, ())


def _timeline_of(tracks: tuple[Track, ...], duration_s: float = 8.0) -> Timeline:
    """Wrap lanes in a timeline for the key estimator.

    Args:
        tracks: Lanes the song carries.
        duration_s: Length of the take.
    Returns:
        Timeline at 120 BPM.
    """
    return Timeline(
        title="Keyed",
        duration_s=duration_s,
        tempo_map=TempoMap.at_tempo(120.0),
        tracks=tracks,
    )


def test_analysis_settings_rejects_a_frame_that_is_not_a_power_of_two() -> None:
    """The radix-2 FFT needs a power-of-two frame."""
    with pytest.raises(ValueError, match="not a power of two"):
        transcribe.AnalysisSettings(frame_size=1000)


def test_analysis_settings_rejects_a_hop_outside_the_frame() -> None:
    """A hop wider than the frame would read samples that were never framed."""
    with pytest.raises(ValueError, match="hop_size"):
        transcribe.AnalysisSettings(hop_size=FRAME + 1)
    with pytest.raises(ValueError, match="hop_size"):
        transcribe.AnalysisSettings(hop_size=0)


def test_analysis_settings_rejects_an_inverted_tempo_window() -> None:
    """The comb filter cannot search a range that runs backwards."""
    with pytest.raises(ValueError, match="tempo_min"):
        transcribe.AnalysisSettings(tempo_min=180.0, tempo_max=60.0)


def test_frameset_reports_the_time_of_every_frame() -> None:
    """A frame index maps back to seconds through the hop."""
    frames = transcribe.FrameSet([[0.0] * 3] * 5, RATE, HOP)
    assert frames.duration_s == pytest.approx(5 * HOP / RATE)
    assert frames.time_of(3) == pytest.approx(3 * HOP / RATE)
    assert transcribe.FrameSet().duration_s == 0.0


def test_decode_audio_returns_mono_floats_and_the_command_it_ran(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ffmpeg is asked for mono float PCM at the analysis rate."""
    samples = [0.0, 0.25, -0.5, 1.0]
    calls = _install_ffmpeg(monkeypatch, samples)
    assert transcribe.decode_audio("take.wav") == pytest.approx(samples)
    assert len(calls) == 1
    argv = calls[0]
    assert argv[0] == "ffmpeg"
    assert "-i" in argv and "take.wav" in argv
    assert argv[argv.index("-ar") + 1] == str(RATE)
    assert argv[argv.index("-ac") + 1] == "1"
    assert argv[-1] == "-"


def test_decode_audio_accepts_a_custom_rate(monkeypatch: pytest.MonkeyPatch) -> None:
    """The operator can ask for a different analysis rate."""
    calls = _install_ffmpeg(monkeypatch, [0.0])
    transcribe.decode_audio("take.wav", 44100)
    assert calls[0][calls[0].index("-ar") + 1] == "44100"


def test_decode_audio_reports_a_missing_ffmpeg(monkeypatch: pytest.MonkeyPatch) -> None:
    """A host without ffmpeg fails with the repair, not a traceback."""

    def _run(command: list[str], **kwargs: object) -> _FakeProcess:
        raise FileNotFoundError("ffmpeg")

    monkeypatch.setattr(transcribe.subprocess, "run", _run)
    with pytest.raises(RuntimeError, match="ffmpeg is not installed"):
        transcribe.decode_audio("take.wav")


def test_decode_audio_reports_a_refused_file(monkeypatch: pytest.MonkeyPatch) -> None:
    """A non-zero exit carries the decoder's own words into the error."""
    calls: list[list[str]] = []

    def _run(command: list[str], **kwargs: object) -> _FakeProcess:
        calls.append(list(command))
        return _FakeProcess(1, b"", b"Invalid data found when processing input")

    monkeypatch.setattr(transcribe.subprocess, "run", _run)
    with pytest.raises(RuntimeError, match="Invalid data found"):
        transcribe.decode_audio("broken.wav")
    assert len(calls) == 1


def test_measure_duration_s_counts_the_frames() -> None:
    """Length is samples over rate, nothing else."""
    assert transcribe.measure_duration_s([0.0] * RATE, RATE) == 1.0
    assert transcribe.measure_duration_s([], RATE) == 0.0


def test_hann_window_is_periodic_and_ends_where_it_started() -> None:
    """A periodic window starts at zero and never exceeds one."""
    window = transcribe.hann_window(8)
    assert len(window) == 8
    assert window[0] == pytest.approx(0.0)
    assert window[4] == pytest.approx(1.0)
    assert window[1] == pytest.approx(window[7])
    assert max(window) <= 1.0


def test_fft_matches_a_naive_transform() -> None:
    """The in-place radix-2 butterfly is a correct discrete Fourier transform."""
    values = [0.2, -0.4, 0.9, 0.1, -0.7, 0.3, 0.0, 0.6]
    data = [complex(value, 0.0) for value in values]
    transcribe._fft(data)
    size = len(values)
    for bin_index in range(size):
        expected = sum(
            values[n] * complex(math.cos(-2.0 * math.pi * bin_index * n / size),
                                math.sin(-2.0 * math.pi * bin_index * n / size))
            for n in range(size)
        )
        assert data[bin_index].real == pytest.approx(expected.real, abs=1e-9)
        assert data[bin_index].imag == pytest.approx(expected.imag, abs=1e-9)


def test_fft_magnitudes_peaks_at_the_tone_bin() -> None:
    """A pure tone lands in the bin its frequency names."""
    samples = [
        0.8 * math.sin(2.0 * math.pi * 440.0 * index / RATE) for index in range(FRAME)
    ]
    magnitudes = transcribe.fft_magnitudes(samples, transcribe.hann_window(FRAME))
    assert len(magnitudes) == SPECTRUM_WIDTH
    peak = max(range(len(magnitudes)), key=lambda index: magnitudes[index])
    assert peak == 28
    assert transcribe.bin_hz(peak, FRAME, RATE) == pytest.approx(437.5)


def test_pitch_and_bin_conversions_round_trip() -> None:
    """A4 is 440 Hz and every MIDI note maps back onto itself."""
    assert transcribe.midi_to_hz(69) == pytest.approx(440.0)
    assert transcribe.hz_to_midi(440.0) == pytest.approx(69.0)
    assert transcribe.hz_to_midi(110.0) == pytest.approx(45.0)
    for pitch in (24, 45, 60, 69, 108):
        assert transcribe.hz_to_midi(transcribe.midi_to_hz(pitch)) == pytest.approx(pitch)
    assert transcribe.bin_hz(0, FRAME, RATE) == 0.0
    assert transcribe.bin_hz(FRAME // 2, FRAME, RATE) == pytest.approx(RATE / 2.0)


def test_band_edges_clamp_to_the_spectrum() -> None:
    """An out-of-range band still names bins the frame actually has."""
    low, high = transcribe.band_edges(0.0, 99999.0, FRAME, RATE)
    assert low == 1
    assert high == SPECTRUM_WIDTH
    assert transcribe.band_edges(20.0, 21.0, FRAME, RATE) == (1, 2)
    assert transcribe.band_edges(20.0, 2500.0, FRAME, RATE) == (1, 160)


def test_stft_frames_a_take_at_the_hop() -> None:
    """Frames advance by the hop and carry half a spectrum each."""
    settings = transcribe.AnalysisSettings()
    frames = transcribe.stft([0.0] * (FRAME + 3 * HOP), settings)
    assert len(frames.frames) == 4
    assert len(frames.frames[0]) == SPECTRUM_WIDTH
    assert frames.sample_rate == RATE
    assert frames.hop_size == HOP


def test_stft_returns_no_frames_for_a_take_shorter_than_the_window() -> None:
    """A take that cannot fill one window produces no frames at all."""
    assert transcribe.stft([0.0] * 100, transcribe.AnalysisSettings()).frames == []


def test_band_energy_sums_only_its_band() -> None:
    """Energy outside the band is not counted, and an empty band is zero."""
    frame = [0.0] * SPECTRUM_WIDTH
    frame[10] = 2.0
    frame[11] = 3.0
    frame[300] = 9.0
    assert transcribe.band_energy(frame, 10, 12) == 5.0
    assert transcribe.band_energy(frame, 20, 20) == 0.0
    assert transcribe.band_energy(frame, 500, 600) == 0.0


def test_spectral_flux_is_half_rectified() -> None:
    """Only rising energy counts, and the first frame has nothing to rise from."""
    frames = [
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 3.0, 0.0, 0.0],
        [0.0, 0.5, 0.0, 0.0],
    ]
    assert transcribe.spectral_flux(frames, 1, 3) == [0.0, 2.0, 0.0]
    assert transcribe.spectral_flux([], 0, 1) == []


def test_median_handles_empty_odd_and_even_lists() -> None:
    """The adaptive threshold needs a median for every neighbourhood shape."""
    assert transcribe._median([]) == 0.0
    assert transcribe._median([3.0, 1.0, 2.0]) == 2.0
    assert transcribe._median([1.0, 2.0, 3.0, 4.0]) == 2.5


def test_peak_pick_ignores_silence() -> None:
    """With no spread to exceed, an envelope has no attacks."""
    assert transcribe.peak_pick([], 0.02, 4) == []
    assert transcribe.peak_pick([0.0] * 30, 0.02, 4) == []


def test_peak_pick_accepts_isolated_attacks_only() -> None:
    """A peak must clear its local median and keep its distance from its neighbour."""
    envelope = [0.0] * 30
    for index in (5, 12, 20):
        envelope[index] = 1.0
    assert transcribe.peak_pick(envelope, 0.02, 4) == [5, 12, 20]
    assert transcribe.peak_pick(envelope, 5.0, 4) == [], "no peak clears that offset"
    plateau = [0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 1.0, 0.0] * 4
    assert transcribe.peak_pick(plateau, 0.02, 4) == [3, 14, 22, 26, 30]


def test_pitch_candidates_scores_a_harmonic_stack() -> None:
    """The fundamental and its overtones add up to the strongest reading."""
    frame = _spike_spectrum({57: 1.0})
    scored = transcribe.pitch_candidates(frame, FRAME, RATE, 50, 65)
    assert scored[0][0] == 57
    assert scored[0][1] > scored[1][1]


def test_pitch_candidates_penalises_a_missing_fundamental() -> None:
    """A ghost made only of other notes' overtones is discounted, not trusted."""
    with_fundamental = _spike_spectrum({57: 1.0})
    without = list(with_fundamental)
    without[round(transcribe.midi_to_hz(57) * FRAME / RATE)] = 0.0
    loud = dict(transcribe.pitch_candidates(with_fundamental, FRAME, RATE, 57, 57))[57]
    ghost = dict(transcribe.pitch_candidates(without, FRAME, RATE, 57, 57))[57]
    assert loud > 0.0
    assert ghost < loud * 0.25, "a ghost with no fundamental must score far lower"


def test_pitch_candidates_skips_a_pitch_its_octave_cannot_reach() -> None:
    """A pitch whose second partial is past Nyquist is not scored at all."""
    frame = _spike_spectrum({107: 1.0, 108: 1.0})
    scored = transcribe.pitch_candidates(frame, FRAME, RATE, 105, 110)
    pitches = [pitch for pitch, _ in scored]
    assert 107 in pitches, "the top scoreable pitch still competes"
    assert 108 not in pitches, "2 * 4186 Hz is over the Nyquist limit"
    assert max(pitches) < 108


def test_pitch_candidates_returns_nothing_for_silence() -> None:
    """A frame with no energy scores no pitch."""
    assert transcribe.pitch_candidates([0.0] * SPECTRUM_WIDTH, FRAME, RATE, 40, 60) == []


def test_sieve_pitches_returns_nothing_for_an_inverted_range() -> None:
    """A lane whose ceiling sits under its floor cannot report a pitch."""
    frame = _spike_spectrum({60: 1.0})
    assert transcribe.sieve_pitches(frame, FRAME, RATE, 70, 60, 3, 0.06) == []


def test_sieve_pitches_returns_nothing_for_a_silent_frame() -> None:
    """With no energy at all the sieve stops on the first pass."""
    assert transcribe.sieve_pitches([0.0] * SPECTRUM_WIDTH, FRAME, RATE, 36, 84, 3, 0.06) == []


def test_sieve_pitches_promotes_a_sub_octave_ghost_onto_the_real_note() -> None:
    """A kick-sized ghost an octave under the bass is read as the bass."""
    frame = _spike_spectrum({45: 0.9, 57: 1.0})
    chosen = transcribe.sieve_pitches(frame, FRAME, RATE, 36, 84, 3, 0.06)
    assert [pitch for pitch, _ in chosen] == [57], "the octave above is the note that sounds"
    assert chosen[0][1] == pytest.approx(1.0)


def test_sieve_pitches_keeps_three_independent_voices() -> None:
    """A triad is read as three pitches, each normalised against the loudest."""
    frame = _spike_spectrum({60: 1.0, 64: 0.9, 67: 0.8})
    chosen = transcribe.sieve_pitches(frame, FRAME, RATE, 55, 75, 3, 0.06)
    assert [pitch for pitch, _ in chosen] == [60, 64, 67]
    assert chosen[0][1] == pytest.approx(1.0)
    assert 0.0 < chosen[2][1] < 1.0


def test_sieve_pitches_retires_a_promoted_pitch_and_moves_on(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every pass retires the pitch it read, so the sieve cannot loop forever.

    The duplicate reading is scripted rather than synthesised: the sieve
    zeroes a taken pitch's partials, so a colliding candidate cannot survive
    to a later pass on real audio, and that retirement branch is exactly what
    is under test here.
    """
    rounds: list[list[tuple[int, float]]] = [
        [(60, 1.0), (48, 0.9)],
        [(60, 1.0)],
        [(48, 0.9)],
        [],
    ]

    def _scored(
        frame: list[float],
        size: int,
        sample_rate: int,
        low_pitch: int,
        high_pitch: int,
        harmonics: int = 4,
    ) -> list[tuple[int, float]]:
        return list(rounds.pop(0)) if rounds else []

    removed: list[int] = []

    def _retire(
        working: list[float], pitch: int, size: int, sample_rate: int
    ) -> None:
        removed.append(pitch)

    monkeypatch.setattr(transcribe, "pitch_candidates", _scored)
    monkeypatch.setattr(transcribe, "_remove_partials", _retire)
    chosen = transcribe.sieve_pitches([0.0] * SPECTRUM_WIDTH, FRAME, RATE, 36, 84, 3, 0.06)
    assert chosen == [(60, 1.0)], "the promoted ghost is dropped as a duplicate"
    assert removed == [60, 48, 60], "the ghost and its octave are both retired"
    assert rounds == []


@pytest.mark.parametrize(
    ("upper_score", "expected"),
    [
        (0.0, 45),
        (0.4, 45),
        (0.59, 45),
        (0.6, 57),
        (0.9, 57),
    ],
)
def test_resolve_octave_promotes_only_a_full_octave_above(
    upper_score: float, expected: int
) -> None:
    """The octave above has to carry a real share of the candidate's score."""
    base = {45: 1.0, 57: upper_score}
    promoted, score = transcribe._resolve_octave((45, 1.0), base, 36, 84)
    assert promoted == expected
    assert score == pytest.approx(1.0 if expected == 45 else upper_score)


def test_resolve_octave_leaves_a_scoreless_candidate_alone() -> None:
    """A candidate with no score of its own is not promoted onto anything."""
    assert transcribe._resolve_octave((45, 0.0), {45: 0.0, 57: 1.0}, 36, 84) == (45, 0.0)


def test_resolve_octave_leaves_a_pitch_at_the_ceiling_alone() -> None:
    """There is nothing above the lane ceiling to promote onto."""
    candidate = (84, 1.0)
    assert transcribe._resolve_octave(candidate, {84: 1.0, 96: 2.0}, 36, 84) == candidate


def test_remove_partials_clears_the_fundamental_and_its_overtones() -> None:
    """A retired pitch leaves no energy for the next pass to re-read."""
    working = _spike_spectrum({57: 1.0})
    assert max(working) > 0.0
    transcribe._remove_partials(working, 57, FRAME, RATE)
    base = transcribe.midi_to_hz(57)
    for order in range(1, 6):
        bin_index = round(base * order * FRAME / RATE)
        assert working[bin_index] == 0.0
        assert working[bin_index + 1] == 0.0


def test_remove_partials_stops_when_the_spectrum_runs_out() -> None:
    """A high pitch has no fifth partial to erase; the loop must not run off."""
    working = [1.0] * SPECTRUM_WIDTH
    transcribe._remove_partials(working, 96, FRAME, RATE)
    base = transcribe.midi_to_hz(96)
    cleared = [
        round(base * order * FRAME / RATE)
        for order in range(1, 6)
        if round(base * order * FRAME / RATE) <= FRAME // 2
    ]
    assert cleared, "some partials were in range"
    assert all(working[bin_index] == 0.0 for bin_index in cleared)
    assert working[-1] == 1.0, "bins past the stack are left alone"


@pytest.mark.parametrize(
    ("sub_level", "mid_level", "high_level", "expected"),
    [
        (0.0, 0.0, 0.0, transcribe.CLOSED_HAT_PITCH),
        (0.2, 0.004, 0.002, transcribe.KICK_PITCH),
        (0.2, 0.0021, 0.0049, transcribe.CRASH_PITCH),
        (0.01, 1.0, 0.001, transcribe.SNARE_PITCH),
        (0.55, 0.0145, 0.0001, transcribe.TOM_PITCH),
        (0.05, 0.005, 0.01, transcribe.CLOSED_HAT_PITCH),
        (0.002, 0.001, 0.02, transcribe.OPEN_HAT_PITCH),
    ],
)
def test_classify_percussion_maps_a_frame_onto_the_kit(
    sub_level: float, mid_level: float, high_level: float, expected: int
) -> None:
    """Kick owns the sub band, snare the mid burst, hats everything above 4 kHz."""
    pitch, share = transcribe.classify_percussion(
        _band_frame(sub_level, mid_level, high_level), FRAME, RATE
    )
    assert pitch == expected
    assert 0.0 <= share <= 1.0


def test_classify_percussion_reports_no_confidence_for_silence() -> None:
    """A frame with no energy is not a drum hit."""
    assert transcribe.classify_percussion([0.0] * SPECTRUM_WIDTH, FRAME, RATE) == (
        transcribe.CLOSED_HAT_PITCH,
        0.0,
    )


def test_estimate_tempo_falls_back_for_an_envelope_it_cannot_read() -> None:
    """Too few frames to comb means no measured beat, so the default stands."""
    assert transcribe.estimate_tempo([0.5] * 7, RATE, HOP, 60.0, 180.0) == (DEFAULT_BPM, 0.0)


def test_estimate_tempo_falls_back_when_the_range_is_unmeasurable() -> None:
    """A tempo window narrower than the envelope cannot be swept."""
    envelope = [0.0] * 20
    envelope[3] = 1.0
    assert transcribe.estimate_tempo(envelope, 1000, 10, 60.0, 180.0) == (DEFAULT_BPM, 0.0)


def test_estimate_tempo_skips_a_lag_it_cannot_score() -> None:
    """A lag whose double covers the whole envelope contributes nothing.

    The envelope is one hundred frames at ten milliseconds a frame, so the
    sweep runs from lag 33 to lag 50 and every lag from 50 up has no room for
    even its first tap. The winner is therefore the first scorable lag, 33,
    which measures 181.8 BPM and folds into the window as 90.9.
    """
    envelope = [0.0] * 100
    envelope[10] = 1.0
    bpm, offset = transcribe.estimate_tempo(envelope, 1000, 10, 120.0, 180.0)
    assert bpm == pytest.approx(60.0 / (33 * 0.01) / 2.0)
    assert offset == pytest.approx(0.1)


def test_estimate_tempo_reports_120_and_not_its_half() -> None:
    """A genuine 120 BPM signal is never read as 60.

    The comb alone cannot tell a beat from its double, so the log-Gaussian
    prior at 120 BPM and the half/double agreement are what keep the answer
    on the beat instead of an octave below it.
    """
    envelope = _impulse_train(120.0, 8.0)
    bpm, offset = transcribe.estimate_tempo(envelope, RATE, HOP, 60.0, 180.0)
    assert bpm == pytest.approx(120.0, abs=2.0)
    assert bpm > 90.0, "an octave error would report 60 BPM"
    assert 0.0 <= offset < 60.0 / bpm


def test_tempo_switch_margin_holds_the_incumbent(monkeypatch: pytest.MonkeyPatch) -> None:
    """A rival has to win by the margin, not just by a hair."""
    envelope = _impulse_train(120.0, 8.0)
    guarded = transcribe.estimate_tempo(envelope, RATE, HOP, 60.0, 180.0)
    monkeypatch.setattr(transcribe, "TEMPO_SWITCH_MARGIN", 0.0)
    unguarded = transcribe.estimate_tempo(envelope, RATE, HOP, 60.0, 180.0)
    assert guarded[0] == pytest.approx(120.0, abs=2.0)
    assert unguarded[0] != pytest.approx(guarded[0]), (
        "with no margin the last positive lag wins, so the answer drifts off the beat"
    )


def test_fold_to_range_doubles_and_halves_into_the_window() -> None:
    """Folding keeps the measured beat and leaves a tempo that already fits."""
    assert transcribe._fold_to_range(30.0, 60.0, 180.0) == 60.0
    assert transcribe._fold_to_range(360.0, 60.0, 180.0) == 180.0
    assert transcribe._fold_to_range(120.0, 60.0, 180.0) == 120.0


def test_beat_offset_needs_a_usable_lag() -> None:
    """No lag and no envelope both put the downbeat at the top."""
    assert transcribe._beat_offset([0.1] * 10, 0, 0.01) == 0.0
    assert transcribe._beat_offset([], 4, 0.01) == 0.0
    assert transcribe._beat_offset([0.0, 0.0, 1.0, 0.0] * 4, 4, 0.01) == pytest.approx(0.02)


def test_beat_grid_needs_a_tempo_and_a_length() -> None:
    """A take with no length or no tempo gets no grid."""
    assert transcribe.beat_grid(0.0, 120.0, 0.0) == ()
    assert transcribe.beat_grid(2.0, 0.0, 0.0) == ()


def test_beat_grid_aligns_downbeats_and_drops_the_lead_in() -> None:
    """The grid is pulled back to a bar boundary, then clipped at zero."""
    grid = transcribe.beat_grid(2.0, 120.0, 0.1)
    assert grid == pytest.approx((0.1, 0.6, 1.1, 1.6))
    early = transcribe.beat_grid(2.0, 120.0, 1.55)
    assert early[0] == pytest.approx(0.05)
    assert all(beat >= 0.0 for beat in early)


def test_note_span_needs_frames_and_energy() -> None:
    """A missing frame or a silent attack lasts one frame."""
    assert transcribe.note_span([], 0, 5, 20, 0.35, 50) == 1
    frames = [[0.0] * SPECTRUM_WIDTH for _ in range(6)]
    assert transcribe.note_span(frames, 99, 5, 20, 0.35, 50) == 1
    assert transcribe.note_span(frames, 0, 5, 20, 0.35, 50) == 1


def test_note_span_ends_after_the_band_goes_quiet() -> None:
    """Two frames under the floor close the note; one does not."""
    frames: list[list[float]] = []
    for index in range(20):
        frame = [0.0] * SPECTRUM_WIDTH
        if index < 6:
            frame[10] = 1.0
        frames.append(frame)
    assert transcribe.note_span(frames, 0, 5, 20, 0.35, 50) == 6
    assert transcribe.note_span(frames, 0, 5, 20, 0.35, 4) == 4


def test_velocity_scales_onto_the_midi_range() -> None:
    """The loudest frame in the lane plays at 127 and silence at 40."""
    assert transcribe._velocity(0.0, 0.0) == 40
    assert transcribe._velocity(1.0, 1.0) == 127
    assert transcribe._velocity(5.0, 1.0) == 127
    assert transcribe._velocity(0.5, 1.0) == 84


def test_snap_pulls_an_attack_toward_the_nearest_beat() -> None:
    """Zero strength leaves the measured attack alone, one lands it on the beat."""
    assert transcribe._snap(1.0, (), 0.5) == 1.0
    assert transcribe._snap(1.0, (0.0, 2.0), 0.0) == 1.0
    assert transcribe._snap(1.1, (1.0,), 0.5) == pytest.approx(1.05)
    assert transcribe._snap(1.1, (1.0,), 1.0) == pytest.approx(1.0)


def test_pad_frame_matches_the_spectrum_the_fft_produced() -> None:
    """A frame is passed through, trimmed, or padded to exactly the width asked for."""
    assert transcribe._pad_frame([1.0, 2.0], 2) == [1.0, 2.0]
    assert transcribe._pad_frame([1.0, 2.0, 3.0], 2) == [1.0, 2.0]
    assert transcribe._pad_frame([1.0], 3) == [1.0, 0.0, 0.0]


def test_estimate_key_needs_pitched_material() -> None:
    """A drum-only take carries no pitch classes, so no key is claimed."""
    drums = Track("Drums", 9, None, (Note(36, 0.0, 0.5),), True)
    assert transcribe.estimate_key(_timeline_of((drums,))) is None
    assert transcribe.estimate_key(_timeline_of(())) is None


def test_estimate_key_reads_a_c_major_triad() -> None:
    """C E G C score as C major rather than some other rotation."""
    notes = tuple(Note(pitch, 0.0, 1.0) for pitch in (60, 64, 67, 72, 79))
    key = transcribe.estimate_key(_timeline_of((Track("Lead", 3, 80, notes),)))
    assert key is not None
    assert (key.key_number, key.major) == (0, True)
    assert key.name == "C major"


def test_transcribe_lane_finds_a_note_inside_its_band() -> None:
    """A bass line whose fundamental is in the band is written as that pitch."""
    lane = transcribe.LaneSpec("Bass", 45.0, 190.0, 1, 33, False, 1, False, 28, 55)
    track = _lane_track(lane, _sine_take(1.0, 45, 0.6, (1.0, 0.3, 0.1)))
    assert track.name == "Bass"
    assert track.channel == 1
    assert track.program == 33
    assert track.notes, "the attack is segmented"
    assert {note.pitch for note in track.notes} == {45}
    assert track.notes[0].start_s == pytest.approx(HOP / RATE, abs=0.01), "attack at the top"
    assert all(40 <= note.velocity <= 127 for note in track.notes)


def test_transcribe_lane_finds_a_fundamental_below_its_band() -> None:
    """Pitch is searched by range, not by band, so the octave is not guessed.

    The lane hears its attack in the 700 to 3200 Hz band, but the note is a
    C4 whose fundamental sits at 261 Hz. Only the ``low_pitch`` bound lets the
    estimator read it; a lane that also narrowed the pitch range reports the
    octave above instead.
    """
    samples = _sine_take(1.0, 60, 0.6, LEAD_HARMONICS)
    wide = transcribe.LaneSpec("Melody", 700.0, 3200.0, 3, 80, False, 1, False, 60, 100)
    narrow = transcribe.LaneSpec("Melody", 700.0, 3200.0, 3, 80, False, 1, False, 72, 100)
    wide_notes = _lane_track(wide, samples).notes
    narrow_notes = _lane_track(narrow, samples).notes
    assert wide_notes, "the attack in the band is segmented"
    assert {note.pitch for note in wide_notes} == {60}
    assert {note.pitch for note in narrow_notes} == {72}


def test_transcribe_lane_snaps_a_drum_hit_to_the_grid() -> None:
    """A kick is classified and written as a GM pitch on the beat."""
    frames = _attack_frames(_band_frame(0.2, 0.004, 0.002))
    lane = transcribe.LaneSpec("Drums", 20.0, 2500.0, 9, None, True, 1, True, 35, 81)
    track = transcribe.transcribe_lane(lane, frames, transcribe.AnalysisSettings(), (0.1, 0.6))
    assert track.is_drums is True
    assert track.program is None
    assert [note.pitch for note in track.notes] == [transcribe.KICK_PITCH]
    assert track.notes[0].start_s == pytest.approx(0.0856, abs=1e-6), "snapped 60 percent"
    assert track.notes[0].velocity == 127


def test_transcribe_lane_drops_a_burst_shorter_than_the_floor() -> None:
    """A note that cannot reach the shortest legal length is not a note."""
    lane = transcribe.LaneSpec("Melody", 700.0, 3200.0, 3, 80, False, 1, False, 60, 100)
    frames = _attack_frames(_tone_spectrum(72))
    settings = transcribe.AnalysisSettings(min_note_s=5.0)
    track = transcribe.transcribe_lane(lane, frames, settings, ())
    assert track.notes == ()
    assert track.name == "Melody"


def test_transcribe_lane_reports_an_empty_lane() -> None:
    """A silent band yields the lane with no notes, not a missing lane."""
    lane = transcribe.LaneSpec("Bass", 45.0, 190.0, 1, 33, False, 1, False, 28, 55)
    frames = transcribe.FrameSet([[0.0] * SPECTRUM_WIDTH] * 20, RATE, HOP)
    track = transcribe.transcribe_lane(lane, frames, transcribe.AnalysisSettings(), ())
    assert track.notes == ()
    assert track.note_count == 0


def test_transcribe_returns_a_default_timeline_for_an_unusable_take(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A take shorter than one window is transcribed as an empty score."""
    _install_ffmpeg(monkeypatch, [0.0] * 100)
    timeline = transcribe.transcribe("take.wav", "Too Short")
    assert timeline.title == "Too Short"
    assert timeline.duration_s == pytest.approx(100 / RATE)
    assert timeline.bpm == DEFAULT_BPM
    assert timeline.tracks == ()
    assert timeline.beats == ()
    assert timeline.key is None
    assert timeline.confidence is None
    assert timeline.source is not None
    assert timeline.source.path == "take.wav"
    assert timeline.source.sample_rate == RATE
    assert timeline.source.bpm_hint is None


def test_transcribe_default_timeline_keeps_a_bpm_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    """Even with nothing to analyse, a tempo the operator gave is honoured."""
    _install_ffmpeg(monkeypatch, [0.0] * 10)
    timeline = transcribe.transcribe("take.wav", "Too Short", bpm_hint=96.0)
    assert timeline.bpm == 96.0
    assert timeline.source is not None
    assert timeline.source.bpm_hint == 96.0


def test_transcribe_reports_silence_honestly(monkeypatch: pytest.MonkeyPatch) -> None:
    """A take with nothing in it claims no notes, no key, and no confidence."""
    _install_ffmpeg(monkeypatch, [0.0] * (RATE * 2))
    timeline = transcribe.transcribe("silence.wav", "Silence")
    assert timeline.duration_s == pytest.approx(2.0)
    assert timeline.note_count == 0
    assert [track.notes for track in timeline.tracks] == [(), (), (), ()]
    assert timeline.key is None
    assert timeline.confidence is None
    assert 60.0 <= timeline.bpm <= 180.0


def test_transcribe_trusts_the_bpm_hint_over_what_it_measured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A tag or an operator tempo wins over the measured one.

    The hint is recorded twice on purpose: in the tempo map, and on the
    provenance record a DAW hand-off reads, so a human reopening the timeline
    can see the tempo came from a tag rather than from the analysis.
    """
    _install_ffmpeg(monkeypatch, _song_samples(2.0))
    timeline = transcribe.transcribe("take.wav", "Hinted", bpm_hint=100.0)
    assert timeline.bpm == 100.0
    assert timeline.tempo_map.points[0].bpm == 100.0
    assert timeline.source is not None
    assert timeline.source.path == "take.wav"
    assert timeline.source.bpm_hint == 100.0
    assert timeline.beats, "the grid is laid at the hinted tempo"
    assert timeline.beats[0] >= 0.0
    assert timeline.beats[-1] <= 2.0
    assert timeline.beats[1] - timeline.beats[0] == pytest.approx(0.6)


def test_transcribe_recovers_the_song_it_was_given(monkeypatch: pytest.MonkeyPatch) -> None:
    """A known song comes back as the pitches and tempo that went in."""
    _install_ffmpeg(monkeypatch, _song_samples())
    timeline = transcribe.transcribe("song.wav", "Known Song", transcribe.AnalysisSettings())
    by_name = {track.name: track for track in timeline.tracks}
    assert timeline.duration_s == pytest.approx(SONG_SECONDS, abs=0.05)
    assert timeline.bpm == pytest.approx(SONG_BPM, abs=3.0)
    assert timeline.bpm > 90.0, "a half-time error would report 60 BPM"
    assert timeline.beats, "the grid covers the take"
    assert timeline.beats[-1] < SONG_SECONDS
    assert timeline.confidence is not None
    assert 0.0 < timeline.confidence <= 1.0
    assert timeline.key is not None
    melody = {note.pitch for note in by_name["Melody"].notes}
    assert set(MELODY_LINE).issubset(melody), f"melody recall lost {set(MELODY_LINE) - melody}"
    assert all(60 <= pitch <= 100 for pitch in melody)
    bass = {note.pitch for note in by_name["Bass"].notes}
    assert set(BASS_RIFF).issubset(bass), f"bass recall lost {set(BASS_RIFF) - bass}"
    assert all(28 <= pitch <= 55 for pitch in bass)
    drums = {note.pitch for note in by_name["Drums"].notes}
    assert transcribe.KICK_PITCH in drums
    assert len(by_name["Drums"].notes) >= 8, "one kick per beat"


def test_default_lanes_cover_the_four_export_roles() -> None:
    """The kit, bass, harmony, and topline lanes are the export contract."""
    assert [lane.name for lane in transcribe.DEFAULT_LANES] == [
        "Drums",
        "Bass",
        "Harmony",
        "Melody",
    ]
    assert [lane.channel for lane in transcribe.DEFAULT_LANES] == [9, 1, 2, 3]
    assert transcribe.DEFAULT_LANES[0].is_drums is True
    assert transcribe.DEFAULT_LANES[0].program is None
    assert transcribe.DEFAULT_LANES[0].percussive is True
    assert transcribe.DEFAULT_LANES[2].max_voices == 3
    for lane in transcribe.DEFAULT_LANES:
        assert lane.low_hz < lane.high_hz
        assert lane.low_pitch < lane.high_pitch
        assert lane.low_pitch <= lane.high_pitch


def test_lane_band_and_pitch_range_are_separate_knobs() -> None:
    """The band is where onsets are heard; the pitch range is where notes are read."""
    lane = transcribe.LaneSpec(
        "Topline",
        low_hz=700.0,
        high_hz=3200.0,
        channel=3,
        program=80,
        is_drums=False,
        max_voices=1,
        percussive=False,
        low_pitch=40,
        high_pitch=96,
    )
    assert lane.low_hz == 700.0
    assert lane.high_hz == 3200.0
    assert lane.low_pitch == 40
    assert lane.high_pitch == 96
    band_floor_pitch = round(transcribe.hz_to_midi(lane.low_hz))
    band_top_pitch = round(transcribe.hz_to_midi(lane.high_hz))
    assert transcribe.midi_to_hz(lane.low_pitch) < lane.low_hz, "search starts under the band"
    assert lane.low_pitch != band_floor_pitch, "the pitch floor is not the band floor"
    assert lane.high_pitch != band_top_pitch, "the pitch ceiling is not the band top"
    assert transcribe.LaneSpec("Pad", 200.0, 900.0, 4).max_voices == 1
    assert transcribe.LaneSpec("Pad", 200.0, 900.0, 4).percussive is False


def test_constants_pin_the_analysis_grid() -> None:
    """The FFT shape and the kit map are what the tests reason in."""
    assert (transcribe.ANALYSIS_SAMPLE_RATE, transcribe.FRAME_SIZE) == (RATE, FRAME)
    assert transcribe.HOP_SIZE == HOP
    assert FRAME & (FRAME - 1) == 0
    assert FRAME % HOP == 0
    assert transcribe.PITCH_FLOOR_HZ < transcribe.midi_to_hz(28)
    assert transcribe.PITCH_CEILING_HZ > transcribe.midi_to_hz(100)
    assert transcribe.TEMPO_PRIOR_BPM == 120.0
    assert transcribe.TEMPO_SWITCH_MARGIN > 1.0
    assert 0.0 < transcribe.OCTAVE_PROMOTION_RATIO < 1.0
    assert transcribe.KICK_PITCH == 36


def test_transcribe_builds_one_track_per_configured_lane(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two lanes in means two tracks out, in the order they were asked for."""
    _install_ffmpeg(monkeypatch, _sine_take(1.0, 45, 0.6, (1.0, 0.3, 0.1)))
    lanes = (
        transcribe.LaneSpec("Bass", 45.0, 190.0, 1, 33, False, 1, False, 28, 55),
        transcribe.LaneSpec("Top", 700.0, 3200.0, 3, 80, False, 1, False, 60, 100),
    )
    timeline = transcribe.transcribe("take.wav", "Two Lanes", transcribe.AnalysisSettings(lanes=lanes))
    assert [track.name for track in timeline.tracks] == ["Bass", "Top"]
    assert [track.channel for track in timeline.tracks] == [1, 3]
    assert timeline.title == "Two Lanes"
