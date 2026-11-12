"""Audio-to-notes transcription with nothing but the standard library.

The hermetic test lane pins only pytest and mutagen, so this module carries
its own DSP: a radix-2 FFT, spectral-flux onset detection with an adaptive
threshold, a harmonic-sieve pitch estimator, and an autocorrelation tempo
tracker. ffmpeg does the job it is better at - decoding any container,
down-mixing, and resampling - and hands back raw float PCM on stdout.

The pipeline is per lane. Each :class:`LaneSpec` owns a frequency band, so the
bass line, the chord bed, the topline, and the kit are segmented against their
own band energy instead of fighting for one global threshold. That is what
makes the output useful in a DAW: a human mutes a lane and replaces it.

Determinism is a feature, not an accident. Same bytes in, same notes out, so
the drift test can pin a transcription the same way it pins a lab graph.
"""

from __future__ import annotations

import array
import math
import subprocess
from dataclasses import dataclass, field

from ez_music.timeline import (
    DEFAULT_BPM,
    PITCH_MAX,
    PITCH_MIN,
    PROGRAM_ACOUSTIC_GRAND_PIANO,
    PROGRAM_ELECTRIC_BASS,
    PROGRAM_LEAD_SYNTH,
    KeySignature,
    Note,
    SourceInfo,
    TempoMap,
    Timeline,
    Track,
)

# Analysis sample rate. 16 kHz puts the Nyquist limit above the top of the
# melodic range we care about and halves the FFT work against 32 kHz.
ANALYSIS_SAMPLE_RATE = 16000

# FFT frame and hop. 64 ms frames at a 16 ms hop track a fast melody legibly;
# that is roughly 60 analysis frames a second, close enough to the 100 fps
# published onset-detector practice to catch chord attacks without smearing
# the kit.
FRAME_SIZE = 1024
HOP_SIZE = 256

# MIDI numbers of the lane boundaries. 28 is E1, 52 is E3, 84 is C6.
BASS_PITCH_MAX = 52
HARMONY_PITCH_MAX = 84
MELODY_PITCH_MAX = 108

# General MIDI percussive pitches this transcriber assigns.
KICK_PITCH = 36
SNARE_PITCH = 38
CLOSED_HAT_PITCH = 42
OPEN_HAT_PITCH = 46
TOM_PITCH = 45
CRASH_PITCH = 49

# Lowest and highest fundamental the pitch estimator is asked to consider,
# kept as a documented bound on the estimator rather than a lane default.
PITCH_FLOOR_HZ = 40.0
PITCH_CEILING_HZ = 3200.0

# Centre of the tempo prior. A comb filter alone cannot tell a beat from its
# double, so the score carries a mild preference for the tempo popular music
# actually sits at, expressed in octaves around this figure.
TEMPO_PRIOR_BPM = 120.0
TEMPO_PRIOR_OCTAVES = 1.0

# A competing tempo has to beat the incumbent by this much to take over, which
# stops a marginal autocorrelation win from flipping the reported beat.
TEMPO_SWITCH_MARGIN = 1.01

# How much of a candidate's score the octave above must carry before the
# candidate is read as a sub-octave ghost of that upper note.
OCTAVE_PROMOTION_RATIO = 0.6


@dataclass(frozen=True)
class LaneSpec:
    """One transcription lane and the band it listens to.

    The band and the pitch range are separate on purpose. Onsets and note
    length are measured inside the band, which is what keeps the bass line out
    of the topline, but pitch is searched across the whole spectrum between
    ``low_pitch`` and ``high_pitch``: a melody note's fundamental often sits
    below its own band, and a search limited to the band then locks onto the
    second harmonic and reports the octave above.

    Args:
        name: Lane name, used as the track name and stem filename.
        low_hz: Bottom of the band in hertz.
        high_hz: Top of the band in hertz.
        channel: MIDI channel to write the lane to.
        program: General MIDI program, or None for the percussion lane.
        is_drums: True for the kit lane, which maps energy to GM pitches.
        max_voices: Pitches to keep per onset; 1 for a monophonic lane.
        percussive: True when onsets come from the band's transient energy
            rather than from a pitched attack.
        low_pitch: Lowest MIDI note the lane may report.
        high_pitch: Highest MIDI note the lane may report.
    """

    name: str
    low_hz: float
    high_hz: float
    channel: int
    program: int | None = None
    is_drums: bool = False
    max_voices: int = 1
    percussive: bool = False
    low_pitch: int = 24
    high_pitch: int = 108


# The four lanes every export ships. Bands overlap by design at the crossovers
# so a note whose energy straddles a boundary still lands somewhere. The pitch
# ranges are the instruments an operator expects to find on each lane.
DEFAULT_LANES = (
    LaneSpec("Drums", 20.0, 2500.0, 9, None, True, 1, True, 35, 81),
    LaneSpec("Bass", 45.0, 190.0, 1, PROGRAM_ELECTRIC_BASS, False, 1, False, 28, 55),
    LaneSpec(
        "Harmony",
        160.0,
        900.0,
        2,
        PROGRAM_ACOUSTIC_GRAND_PIANO,
        False,
        3,
        False,
        40,
        84,
    ),
    LaneSpec("Melody", 700.0, 3200.0, 3, PROGRAM_LEAD_SYNTH, False, 1, False, 60, 100),
)


@dataclass(frozen=True)
class AnalysisSettings:
    """Knobs for one transcription run.

    Args:
        sample_rate: Rate ffmpeg resamples to before analysis.
        frame_size: FFT size; a power of two.
        hop_size: Samples between frames; must divide into frame_size.
        min_note_s: Shortest note the segmenter keeps, in seconds.
        max_note_s: Longest note it will hold open, in seconds.
        onset_offset: How far above the local median a flux peak must sit to
            count as an attack.
        onset_gap_s: Minimum spacing between two accepted attacks.
        min_strength: Weakest harmonic-sieve score a pitch may carry.
        tempo_min: Slowest tempo the tracker may report.
        tempo_max: Fastest tempo the tracker may report.
        lanes: Lanes to transcribe.
        quantize: Snap note attacks to the beat grid.
        quantize_strength: How hard to snap, 0 to 1.
    """

    sample_rate: int = ANALYSIS_SAMPLE_RATE
    frame_size: int = FRAME_SIZE
    hop_size: int = HOP_SIZE
    min_note_s: float = 0.08
    max_note_s: float = 4.0
    onset_offset: float = 0.02
    onset_gap_s: float = 0.06
    min_strength: float = 0.06
    tempo_min: float = 60.0
    tempo_max: float = 180.0
    lanes: tuple[LaneSpec, ...] = DEFAULT_LANES
    quantize: bool = True
    quantize_strength: float = 0.6

    def __post_init__(self) -> None:
        """Reject a knob setting the FFT cannot honour.

        Raises:
            ValueError: the frame is not a power of two, the hop does not fit
                inside it, or the tempo window is inverted.
        """
        if self.frame_size & (self.frame_size - 1):
            raise ValueError(f"frame_size {self.frame_size} is not a power of two")
        if not 0 < self.hop_size <= self.frame_size:
            raise ValueError(f"hop_size {self.hop_size} outside 1..{self.frame_size}")
        if self.tempo_min >= self.tempo_max:
            raise ValueError(
                f"tempo_min {self.tempo_min} must be below tempo_max {self.tempo_max}"
            )


@dataclass
class FrameSet:
    """Magnitude frames of one decoded take.

    Args:
        frames: One magnitude list per frame, in time order.
        sample_rate: Rate the audio was analysed at.
        hop_size: Samples between frame starts.
    """

    frames: list[list[float]] = field(default_factory=list)
    sample_rate: int = ANALYSIS_SAMPLE_RATE
    hop_size: int = HOP_SIZE

    @property
    def duration_s(self) -> float:
        """Return the analysed length.

        Returns:
            Seconds covered by the frames.
        """
        return len(self.frames) * self.hop_size / self.sample_rate

    def time_of(self, index: int) -> float:
        """Return the centre time of a frame.

        Args:
            index: Frame index.
        Returns:
            Seconds from the top of the take.
        """
        return index * self.hop_size / self.sample_rate


def decode_audio(path: str, sample_rate: int = ANALYSIS_SAMPLE_RATE) -> list[float]:
    """Decode an audio file to mono float samples with ffmpeg.

    Args:
        path: Source file; any container ffmpeg reads.
        sample_rate: Rate to resample to.
    Returns:
        Samples in -1.0 to 1.0.
    Raises:
        RuntimeError: ffmpeg is missing or refused the file.
    """
    command = [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        path,
        "-f",
        "f32le",
        "-acodec",
        "pcm_f32le",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-",
    ]
    try:
        completed = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
        )
    except FileNotFoundError as exc:
        raise RuntimeError("ffmpeg is not installed") from exc
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError(f"ffmpeg could not decode {path}: {detail}")
    samples = array.array("f")
    samples.frombytes(completed.stdout)
    return list(samples)


def measure_duration_s(samples: list[float], sample_rate: int) -> float:
    """Return the length of a decoded take.

    Args:
        samples: Decoded samples.
        sample_rate: Rate they were decoded at.
    Returns:
        Seconds.
    """
    return len(samples) / sample_rate


def hann_window(size: int) -> list[float]:
    """Build a periodic Hann window.

    Args:
        size: Window length.
    Returns:
        Multipliers for one frame.
    """
    return [0.5 - 0.5 * math.cos(2.0 * math.pi * n / size) for n in range(size)]


def fft_magnitudes(samples: list[float], window: list[float]) -> list[float]:
    """Return the magnitude spectrum of one windowed frame.

    Args:
        samples: Frame samples, at least ``len(window)`` long.
        window: Window multipliers, a power of two long.
    Returns:
        ``len(window) // 2 + 1`` magnitudes, DC first.
    """
    size = len(window)
    data = [complex(samples[index] * window[index], 0.0) for index in range(size)]
    _fft(data)
    half = size // 2
    return [abs(data[index]) for index in range(half + 1)]


def _fft(data: list[complex]) -> None:
    """Run an in-place iterative radix-2 FFT.

    Args:
        data: Complex buffer whose length is a power of two; reordered and
            transformed in place.
    """
    size = len(data)
    index = 1
    partner = 0
    while index < size:
        bit = size >> 1
        while partner & bit:
            partner ^= bit
            bit >>= 1
        partner |= bit
        if index < partner:
            data[index], data[partner] = data[partner], data[index]
        index += 1
    length = 2
    while length <= size:
        angle = -2.0 * math.pi / length
        step_real = math.cos(angle)
        step_imag = math.sin(angle)
        half = length >> 1
        for start in range(0, size, length):
            w_real, w_imag = 1.0, 0.0
            for offset in range(half):
                low = start + offset
                high = low + half
                low_value = data[low]
                timed = data[high]
                v_real = timed.real * w_real - timed.imag * w_imag
                v_imag = timed.real * w_imag + timed.imag * w_real
                data[low] = complex(low_value.real + v_real, low_value.imag + v_imag)
                data[high] = complex(low_value.real - v_real, low_value.imag - v_imag)
                w_real, w_imag = (
                    w_real * step_real - w_imag * step_imag,
                    w_real * step_imag + w_imag * step_real,
                )
        length <<= 1


def bin_hz(bin_index: int, size: int, sample_rate: int) -> float:
    """Return the frequency of a spectrum bin.

    Args:
        bin_index: Bin number.
        size: FFT size.
        sample_rate: Sample rate the frame came from.
    Returns:
        Hertz.
    """
    return bin_index * sample_rate / size


def hz_to_midi(hz: float) -> float:
    """Convert a frequency to a fractional MIDI note number.

    Args:
        hz: Frequency above zero.
    Returns:
        MIDI note number, A4 = 69 at 440 Hz.
    """
    return 69.0 + 12.0 * math.log2(hz / 440.0)


def midi_to_hz(pitch: int) -> float:
    """Convert a MIDI note number to a frequency.

    Args:
        pitch: MIDI note number.
    Returns:
        Hertz, equal temperament.
    """
    return 440.0 * math.pow(2.0, (pitch - 69) / 12.0)


def band_edges(low_hz: float, high_hz: float, size: int, sample_rate: int) -> tuple[int, int]:
    """Return the bin range that covers a frequency band.

    Args:
        low_hz: Bottom of the band.
        high_hz: Top of the band.
        size: FFT size.
        sample_rate: Sample rate of the frames.
    Returns:
        First and one-past-last bin index, clamped to the spectrum.
    """
    last = size // 2
    low = max(1, min(last, int(math.floor(low_hz * size / sample_rate))))
    high = max(low + 1, min(last + 1, int(math.ceil(high_hz * size / sample_rate))))
    return low, high


def stft(samples: list[float], settings: AnalysisSettings) -> FrameSet:
    """Short-time Fourier transform a take into magnitude frames.

    Args:
        samples: Decoded mono samples.
        settings: Frame, hop, and sample rate to use.
    Returns:
        Frames with the metadata needed to map a frame back to a time.
    """
    size = settings.frame_size
    hop = settings.hop_size
    window = hann_window(size)
    frames: list[list[float]] = []
    limit = len(samples) - size
    start = 0
    while start <= limit:
        frames.append(fft_magnitudes(samples[start : start + size], window))
        start += hop
    return FrameSet(frames, settings.sample_rate, hop)


def band_energy(frame: list[float], low: int, high: int) -> float:
    """Sum energy in a bin range.

    Args:
        frame: Magnitude spectrum.
        low: First bin.
        high: One past the last bin.
    Returns:
        Sum of magnitudes, 0.0 for an empty range.
    """
    return sum(frame[index] for index in range(min(low, len(frame)), min(high, len(frame))))


def spectral_flux(frames: list[list[float]], low: int, high: int) -> list[float]:
    """Return the half-rectified band flux between consecutive frames.

    Args:
        frames: Magnitude frames in time order.
        low: First band bin.
        high: One past the last band bin.
    Returns:
        One value per frame; the first frame is 0.0.
    """
    out: list[float] = []
    previous: list[float] | None = None
    for frame in frames:
        if previous is None:
            out.append(0.0)
        else:
            rise = 0.0
            for index in range(low, high):
                delta = frame[index] - previous[index]
                if delta > 0.0:
                    rise += delta
            out.append(rise)
        previous = frame
    return out


def _median(values: list[float]) -> float:
    """Return the median of a list.

    Args:
        values: Values to summarise; may be empty.
    Returns:
        Middle value, or the mean of the two middle values, or 0.0 when empty.
    """
    if not values:
        return 0.0
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def peak_pick(
    envelope: list[float],
    offset: float,
    gap_frames: int,
    window: int = 10,
) -> list[int]:
    """Pick adaptive-threshold peaks in an onset envelope.

    A frame wins when it is a local maximum and sits above the median of its
    neighbourhood by ``offset`` times that neighbourhood's spread. Silence
    yields no peaks because the envelope has no spread to exceed.

    Args:
        envelope: Onset strength per frame.
        offset: Threshold multiplier over the local median.
        gap_frames: Frames to skip after a accepted peak.
        window: Half-width of the neighbourhood used for the local median.
    Returns:
        Frame indices of the accepted attacks, in time order.
    """
    if not envelope:
        return []
    scale = max(envelope)
    if scale <= 0.0:
        return []
    normalised = [value / scale for value in envelope]
    peaks: list[int] = []
    last_taken = -gap_frames - 1
    for index in range(1, len(normalised) - 1):
        low = max(0, index - window)
        high = min(len(normalised), index + window + 1)
        neighbourhood = normalised[low:high]
        threshold = _median(neighbourhood) + offset
        value = normalised[index]
        if value < threshold:
            continue
        if value < normalised[index - 1] or value < normalised[index + 1]:
            continue
        if index - last_taken < gap_frames:
            continue
        peaks.append(index)
        last_taken = index
    return peaks


def pitch_candidates(
    frame: list[float],
    size: int,
    sample_rate: int,
    low_pitch: int,
    high_pitch: int,
    harmonics: int = 4,
) -> list[tuple[int, float]]:
    """Score every MIDI pitch in a range by its harmonic stack.

    Energy at a fundamental and its first ``harmonics`` - 1 overtones is
    summed, then discounted when the fundamental itself is quiet. That second
    step is what separates a real 110 Hz note from the sub-octave ghost below
    it: a ghost is built entirely of other notes' overtones and carries no
    energy of its own at its fundamental.

    Args:
        frame: Magnitude spectrum.
        size: FFT size.
        sample_rate: Sample rate of the frame.
        low_pitch: Lowest MIDI note to score.
        high_pitch: Highest MIDI note to score.
        harmonics: How many partials to add in.
    Returns:
        ``(pitch, score)`` pairs, strongest first.
    """
    last_bin = len(frame) - 1
    nyquist = sample_rate / 2.0
    scored: list[tuple[int, float]] = []
    for pitch in range(low_pitch, high_pitch + 1):
        base = midi_to_hz(pitch)
        if base * 2.0 > nyquist:
            continue
        total = 0.0
        weight = 1.0
        strongest = 0.0
        for order in range(1, harmonics + 1):
            bin_index = int(round(base * order * size / sample_rate))
            if bin_index > last_bin:
                break
            value = frame[bin_index] * weight
            total += value
            strongest = max(strongest, value)
            weight *= 0.75
        if total <= 0.0 or strongest <= 0.0:
            continue
        fundamental_bin = int(round(base * size / sample_rate))
        fundamental = frame[fundamental_bin] if fundamental_bin <= last_bin else 0.0
        presence = min(1.0, (fundamental / strongest) * 2.0)
        scored.append((pitch, total * (0.25 + 0.75 * presence)))
    scored.sort(key=lambda pair: -pair[1])
    return scored


def sieve_pitches(
    frame: list[float],
    size: int,
    sample_rate: int,
    low_pitch: int,
    high_pitch: int,
    max_voices: int,
    min_strength: float,
) -> list[tuple[int, float]]:
    """Pick up to ``max_voices`` pitches with a greedy harmonic sieve.

    Each winner removes its own partials from the working spectrum, so the
    second pick is genuine remaining energy rather than the octave above the
    first. Pitch is scored across the full spectrum, bounded by the lane's own
    note range.

    Args:
        frame: Magnitude spectrum.
        size: FFT size.
        sample_rate: Sample rate of the frame.
        low_pitch: Lowest MIDI note the lane may report.
        high_pitch: Highest MIDI note the lane may report.
        max_voices: Pitches to return at most.
        min_strength: Weakest score to keep, as a fraction of the best score.
    Returns:
        ``(pitch, normalised_strength)`` pairs, strongest first.
    """
    floor = max(PITCH_MIN, low_pitch)
    ceiling = min(PITCH_MAX, high_pitch)
    if ceiling < floor:
        return []
    base_scores = dict(pitch_candidates(frame, size, sample_rate, floor, ceiling))
    working = list(frame)
    chosen: list[tuple[int, float]] = []
    reference: float | None = None
    while len(chosen) < max_voices:
        scored = pitch_candidates(working, size, sample_rate, floor, ceiling)
        if not scored:
            break
        raw_pitch, raw_score = scored[0]
        pitch, score = _resolve_octave((raw_pitch, raw_score), base_scores, floor, ceiling)
        # Retire the pitch we just read, whether or not it was promoted. A
        # sub-octave ghost that keeps its own energy would otherwise return as
        # the strongest reading on every pass and the sieve would never move
        # on. Zeroing its partials makes its own score fall to zero, so each
        # pass retires at least one candidate and the loop terminates.
        _remove_partials(working, raw_pitch, size, sample_rate)
        if pitch != raw_pitch:
            _remove_partials(working, pitch, size, sample_rate)
        if any(pitch == taken for taken, _ in chosen):
            continue
        if reference is None:
            reference = score
        if score < reference * min_strength:
            break
        chosen.append((pitch, score / reference))
    return chosen


def _resolve_octave(
    candidate: tuple[int, float],
    base_scores: dict[int, float],
    floor: int,
    ceiling: int,
) -> tuple[int, float]:
    """Correct a sub-octave reading onto the pitch that really sounds.

    A kick drum puts real energy where the fundamental of a ghost note an
    octave below the bass would sit, so the fundamental-presence check alone
    cannot reject it. The tell is that the octave above also scores well: a
    genuine low note has nothing an octave up, a ghost has the whole note.

    Args:
        candidate: ``(pitch, score)`` the sieve wants to take.
        base_scores: Scores of every candidate in the unedited frame.
        floor: Lowest pitch the lane may report.
        ceiling: Highest pitch the lane may report.
    Returns:
        The candidate, promoted one octave when the upper score carries a
        substantial share of the lower one.
    """
    pitch, score = candidate
    upper = pitch + 12
    if upper > ceiling:
        return candidate
    upper_score = base_scores.get(upper, 0.0)
    if score <= 0.0 or upper_score < score * OCTAVE_PROMOTION_RATIO:
        return candidate
    return (upper, upper_score)


def _remove_partials(
    working: list[float], pitch: int, size: int, sample_rate: int
) -> None:
    """Zero out a pitch's fundamental and its first few overtones.

    Args:
        working: Spectrum to edit in place.
        pitch: MIDI note whose partials to erase.
        size: FFT size.
        sample_rate: Sample rate of the frame.
    """
    base = midi_to_hz(pitch)
    last_bin = len(working) - 1
    for order in range(1, 6):
        bin_index = int(round(base * order * size / sample_rate))
        if bin_index > last_bin:
            break
        working[bin_index] = 0.0
        if bin_index + 1 <= last_bin:
            working[bin_index + 1] = 0.0


def classify_percussion(
    frame: list[float], size: int, sample_rate: int
) -> tuple[int, float]:
    """Map one broadband frame onto a General MIDI kit piece.

    Kick owns the sub band, snare the mid burst with noise on top, and the
    hats everything that lives only above 6 kHz.

    Args:
        frame: Magnitude spectrum of an attack.
        size: FFT size.
        sample_rate: Sample rate of the frame.
    Returns:
        MIDI pitch of the kit piece and the confidence of the guess, 0 to 1.
    """
    sub = band_energy(frame, *band_edges(20.0, 120.0, size, sample_rate))
    mid = band_energy(frame, *band_edges(120.0, 4000.0, size, sample_rate))
    high = band_energy(frame, *band_edges(4000.0, 16000.0, size, sample_rate))
    total = sub + mid + high
    if total <= 0.0:
        return CLOSED_HAT_PITCH, 0.0
    shares = ((sub / total, KICK_PITCH), (mid / total, SNARE_PITCH), (high / total, CLOSED_HAT_PITCH))
    share, pitch = max(shares, key=lambda pair: pair[0])
    if pitch == CLOSED_HAT_PITCH and share > 0.75:
        pitch = OPEN_HAT_PITCH
    if pitch == SNARE_PITCH and sub / total > 0.45:
        pitch = TOM_PITCH
    if pitch == KICK_PITCH and high / total > 0.35:
        pitch = CRASH_PITCH
    return pitch, share


def estimate_tempo(
    envelope: list[float],
    sample_rate: int,
    hop_size: int,
    tempo_min: float,
    tempo_max: float,
) -> tuple[float, float]:
    """Track the beat from an onset envelope.

    The envelope is scored against a comb of impulse trains, which is what
    keeps a track from locking onto double or half the true beat: a lag wins
    only when the half and double lags agree with it.

    Args:
        envelope: Onset strength per frame.
        sample_rate: Rate the frames came from.
        hop_size: Samples between frames.
        tempo_min: Slowest tempo to consider.
        tempo_max: Fastest tempo to consider.
    Returns:
        ``(bpm, first_beat_offset_s)``; ``DEFAULT_BPM`` and 0.0 when the
        envelope has no usable rhythm.
    """
    if len(envelope) < 8:
        return DEFAULT_BPM, 0.0
    seconds_per_frame = hop_size / sample_rate
    min_lag = max(2, int(math.floor(60.0 / tempo_max / seconds_per_frame)))
    max_lag = min(len(envelope) - 1, int(math.ceil(60.0 / tempo_min / seconds_per_frame)))
    if max_lag <= min_lag:
        return DEFAULT_BPM, 0.0
    best_lag = min_lag
    best_score = -1.0
    for lag in range(min_lag, max_lag + 1):
        score = 0.0
        taps = 0
        for tap, weight in ((1, 1.0), (2, 0.6), (3, 0.3)):
            span = lag * tap
            if span * 2 >= len(envelope):
                continue
            taps += 1
            for index in range(len(envelope) - span):
                score += weight * envelope[index] * envelope[index + span]
        if taps == 0:
            continue
        score /= taps
        candidate_bpm = 60.0 / (lag * seconds_per_frame)
        prior = math.exp(
            -0.5
            * (math.log2(candidate_bpm / TEMPO_PRIOR_BPM) / TEMPO_PRIOR_OCTAVES) ** 2
        )
        score *= prior
        if score > best_score * TEMPO_SWITCH_MARGIN:
            best_score = score
            best_lag = lag
    bpm = 60.0 / (best_lag * seconds_per_frame)
    return _fold_to_range(bpm, tempo_min, tempo_max), _beat_offset(
        envelope, best_lag, seconds_per_frame
    )


def _fold_to_range(bpm: float, tempo_min: float, tempo_max: float) -> float:
    """Fold a tempo into the search range by doubling or halving.

    Args:
        bpm: Measured tempo.
        tempo_min: Bottom of the range.
        tempo_max: Top of the range.
    Returns:
        A tempo inside the range that shares the measured beat.
    """
    value = bpm
    while value < tempo_min:
        value *= 2.0
    while value > tempo_max:
        value /= 2.0
    return value


def _beat_offset(envelope: list[float], lag: int, seconds_per_frame: float) -> float:
    """Find where in the beat the first downbeat sits.

    Args:
        envelope: Onset strength per frame.
        lag: Beat length in frames.
        seconds_per_frame: Frame stride in seconds.
    Returns:
        Seconds to the first beat, always inside one beat.
    """
    if lag <= 0 or not envelope:
        return 0.0
    best_phase = 0
    best_score = -1.0
    for phase in range(lag):
        score = sum(envelope[index] for index in range(phase, len(envelope), lag))
        if score > best_score:
            best_score = score
            best_phase = phase
    return best_phase * seconds_per_frame


def beat_grid(
    duration_s: float, bpm: float, offset_s: float, beats_per_bar: int = 4
) -> tuple[float, ...]:
    """Lay a beat grid across a take.

    Args:
        duration_s: Length to cover.
        bpm: Tempo of the grid.
        offset_s: Time of the first beat.
        beats_per_bar: Beats per bar, used to keep downbeats aligned.
    Returns:
        Beat times in seconds, starting at the first beat at or after 0.0.
    """
    if bpm <= 0.0 or duration_s <= 0.0:
        return ()
    beat_s = 60.0 / bpm
    first = offset_s
    while first > 0.0:
        first -= beat_s * beats_per_bar
    grid: list[float] = []
    while first < duration_s:
        if first >= 0.0:
            grid.append(first)
        first += beat_s
    return tuple(grid)


def note_span(
    frames: list[list[float]],
    onset_index: int,
    low: int,
    high: int,
    floor_ratio: float,
    max_frames: int,
) -> int:
    """Measure how long a band stays loud after an attack.

    Args:
        frames: Magnitude frames of the lane's band.
        onset_index: Frame the attack landed on.
        low: First band bin.
        high: One past the last band bin.
        floor_ratio: Fraction of the attack energy under which the note ends.
        max_frames: Longest note to hold open.
    Returns:
        Number of frames the note sounds, at least 1.
    """
    if not frames or onset_index >= len(frames):
        return 1
    attack = band_energy(frames[onset_index], low, high)
    if attack <= 0.0:
        return 1
    floor = attack * floor_ratio
    limit = min(len(frames) - 1, onset_index + max_frames)
    run_below = 0
    for index in range(onset_index + 1, limit + 1):
        if band_energy(frames[index], low, high) < floor:
            run_below += 1
            if run_below >= 2:
                return max(1, index - run_below + 1 - onset_index)
        else:
            run_below = 0
    return max(1, limit - onset_index)


def _velocity(peak: float, loudest: float) -> int:
    """Scale a band peak onto a MIDI velocity.

    Args:
        peak: Energy of the note's loudest frame.
        loudest: Loudest energy anywhere in the lane's band.
    Returns:
        Velocity between 40 and 127; a lane with no energy plays at 40.
    """
    if loudest <= 0.0:
        return 40
    ratio = max(0.0, min(1.0, peak / loudest))
    return max(40, min(127, round(40.0 + ratio * 87.0)))


def _snap(start_s: float, beats: tuple[float, ...], strength: float) -> float:
    """Pull an attack toward the nearest beat.

    Args:
        start_s: Measured attack time.
        beats: Beat grid times.
        strength: 0.0 leaves the attack alone, 1.0 lands it on the beat.
    Returns:
        Attack time to write.
    """
    if not beats or strength <= 0.0:
        return start_s
    nearest = min(beats, key=lambda beat: abs(beat - start_s))
    return start_s + (nearest - start_s) * strength


def transcribe_lane(
    lane: LaneSpec, frames: FrameSet, settings: AnalysisSettings, beats: tuple[float, ...]
) -> Track:
    """Segment one lane of the take into notes.

    Args:
        lane: Lane to transcribe.
        frames: Magnitude frames of the whole take.
        settings: Analysis knobs.
        beats: Beat grid to snap attacks to.
    Returns:
        Lane with its notes in attack order.
    """
    size = settings.frame_size
    sample_rate = settings.sample_rate
    spectrum_width = size // 2 + 1
    padded = [_pad_frame(frame, spectrum_width) for frame in frames.frames]
    low, high = band_edges(lane.low_hz, lane.high_hz, size, sample_rate)
    flux = spectral_flux(padded, low, high)
    gap_frames = max(1, int(round(settings.onset_gap_s * sample_rate / settings.hop_size)))
    attacks = peak_pick(flux, settings.onset_offset, gap_frames)
    loudest = max((band_energy(frame, low, high) for frame in padded), default=0.0)
    max_frames = max(2, int(round(settings.max_note_s * sample_rate / settings.hop_size)))
    notes: list[Note] = []
    for onset in attacks:
        span = note_span(padded, onset, low, high, 0.35, max_frames)
        if span * settings.hop_size / sample_rate < settings.min_note_s:
            continue
        peak = max(
            band_energy(padded[index], low, high)
            for index in range(onset, min(len(padded), onset + span))
        )
        start = frames.time_of(onset)
        if lane.is_drums:
            pitch, _ = classify_percussion(padded[onset], size, sample_rate)
            notes.append(
                Note(pitch, _snap(start, beats, settings.quantize_strength),
                     max(settings.min_note_s, span * settings.hop_size / sample_rate),
                     _velocity(peak, loudest))
            )
            continue
        centre = onset + min(span - 1, 2) // 2
        voices = sieve_pitches(
            padded[centre], size, sample_rate, lane.low_pitch, lane.high_pitch,
            lane.max_voices, settings.min_strength,
        )
        for pitch, strength in voices:
            notes.append(
                Note(pitch, _snap(start, beats, settings.quantize_strength),
                     max(settings.min_note_s, span * settings.hop_size / sample_rate),
                     _velocity(peak * strength, loudest))
            )
    notes.sort(key=lambda note: (note.start_s, note.pitch))
    return Track(
        name=lane.name,
        channel=lane.channel,
        program=lane.program,
        notes=tuple(notes),
        is_drums=lane.is_drums,
    )


def _pad_frame(frame: list[float], width: int) -> list[float]:
    """Return a frame padded or trimmed to a fixed width.

    Args:
        frame: Magnitude spectrum.
        width: Bins to return.
    Returns:
        Frame of exactly that width.
    """
    if len(frame) == width:
        return frame
    if len(frame) > width:
        return frame[:width]
    return frame + [0.0] * (width - len(frame))


def estimate_key(timeline: Timeline) -> KeySignature | None:
    """Guess the key from the aggregate pitch content.

    A 12-bin pitch-class profile is scored against the major and natural minor
    templates; the best score wins.

    Args:
        timeline: Transcribed song.
    Returns:
        Best key, or None when the song carries no pitched material.
    """
    profile = [0.0] * 12
    counted = 0
    for track in timeline.tracks:
        if track.is_drums:
            continue
        for note in track.notes:
            profile[note.pitch % 12] += note.duration_s * note.velocity
            counted += 1
    if counted == 0:
        return None
    major_template = (6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88)
    minor_template = (6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17)
    total = sum(profile) or 1.0
    normalised = [value / total for value in profile]
    best: tuple[float, KeySignature] | None = None
    for rotation in range(12):
        for template, major in ((major_template, True), (minor_template, False)):
            shifted = [normalised[(rotation + index) % 12] for index in range(12)]
            score = sum(weight * value for weight, value in zip(template, shifted))
            current = KeySignature(rotation, major)
            if best is None or score > best[0]:
                best = (score, current)
    return None if best is None else best[1]


def transcribe(
    audio_path: str,
    title: str,
    settings: AnalysisSettings | None = None,
    bpm_hint: float | None = None,
) -> Timeline:
    """Transcribe an audio file into a timeline.

    Args:
        audio_path: Source audio; anything ffmpeg reads.
        title: Song name for the timeline header.
        settings: Analysis knobs, defaults included.
        bpm_hint: Tempo to trust over the measured one, when a tag or an
            operator supplied one.
    Returns:
        Timeline with one track per lane, a beat grid, and provenance.
    Raises:
        RuntimeError: ffmpeg could not decode the source.
    """
    knobs = settings or AnalysisSettings()
    samples = decode_audio(audio_path, knobs.sample_rate)
    duration_s = measure_duration_s(samples, knobs.sample_rate)
    frames = stft(samples, knobs)
    if not frames.frames:
        return Timeline(
            title=title,
            duration_s=duration_s,
            tempo_map=TempoMap.at_tempo(bpm_hint if bpm_hint is not None else DEFAULT_BPM),
            source=SourceInfo(audio_path, duration_s, knobs.sample_rate, bpm_hint=bpm_hint),
        )
    width = len(frames.frames[0])
    flux = spectral_flux(frames.frames, 1, max(2, width))
    measured_bpm, offset_s = estimate_tempo(
        flux,
        knobs.sample_rate,
        knobs.hop_size,
        knobs.tempo_min,
        knobs.tempo_max,
    )
    bpm = bpm_hint if bpm_hint is not None else measured_bpm
    grid = beat_grid(duration_s, bpm, offset_s)
    tempo_map = TempoMap.at_tempo(bpm)
    tracks = tuple(
        transcribe_lane(lane, frames, knobs, grid) for lane in knobs.lanes
    )
    pitched = tuple(
        Track(track.name, track.channel, track.program, track.notes, False)
        for track in tracks
        if not track.is_drums
    )
    skeleton = Timeline(title, duration_s, tempo_map, grid, pitched)
    strengths = [
        note.velocity / 127.0 for track in tracks for note in track.notes
    ]
    confidence = sum(strengths) / len(strengths) if strengths else None
    return Timeline(
        title=title,
        duration_s=duration_s,
        tempo_map=tempo_map,
        beats=grid,
        tracks=tracks,
        key=estimate_key(skeleton),
        confidence=confidence,
        source=SourceInfo(
            audio_path, duration_s, knobs.sample_rate, bpm_hint=bpm_hint
        ),
    )
