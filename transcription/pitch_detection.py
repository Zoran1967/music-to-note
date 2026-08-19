# -*- coding: utf-8 -*-
"""
transcription/pitch_detection.py

FAZA 3: Pure-Python pitch/note detection.

STRATEGY NOTE: earlier attempts to use `aubio` (a C library) for this
repeatedly failed to build on python-for-android (numpy ABI breakage,
git tag mismatches in the numpy recipe -- see project history). To
avoid depending on ANY C extension for this core feature, detection is
implemented here in plain Python using the classic autocorrelation
method.

INCREMENTAL DESIGN: running the whole analysis in one continuous loop
(even on a background thread) pegs the CPU long enough that some
Android OEM skins (MIUI in particular) treat the app as "frozen" and
force-kill it without any dialog. NoteDetector processes just a few
frames per .step() call instead, meant to be driven from
Clock.schedule_interval on the main thread -- each tick does a tiny
amount of work and returns control immediately, so the UI (and
Android's "is this app alive" check) never sees a long unbroken burst
of CPU usage.

Only WAV files are supported directly (read via the stdlib `wave`
module, zero dependencies). MP3/M4A/etc. analysis would require
routing through Android's MediaCodec API -- left for a later phase.
"""

import math
import wave

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Frame/hop sizes tuned for SAMPLE_RATE=16000 audio (see recorder.py).
FRAME_SIZE = 1024
HOP_SIZE = 512
FMIN = 70.0    # ~D2, comfortably below a low male voice / bass instrument
FMAX = 1050.0  # ~C6, comfortably above a soprano voice / high melody line
MIN_NOTE_DURATION = 0.08  # seconds -- discard shorter, likely spurious blips
SILENCE_ENERGY_RATIO = 0.0025  # relative energy threshold to call a frame "silent"
MAX_ANALYSIS_SECONDS = 20  # keep pure-Python analysis's total work bounded
MIN_CONFIDENCE = 0.35  # normalized autocorrelation threshold to accept a pitch


def freq_to_note(freq):
    """Convert a frequency in Hz to a note name like 'A4'. A4 = 440 Hz."""
    if not freq or freq <= 0:
        return None
    midi_num = 69 + 12 * math.log2(freq / 440.0)
    midi_round = round(midi_num)
    note_name = NOTE_NAMES[midi_round % 12]
    octave = midi_round // 12 - 1
    return "{}{}".format(note_name, octave)


def _read_wav_samples(path):
    """Read a mono or stereo 16-bit WAV file into a plain array of ints."""
    with wave.open(path, "rb") as wf:
        n_channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        sample_rate = wf.getframerate()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)

    if sample_width != 2:
        raise ValueError(
            "Podrzan je samo 16-bit WAV (dobijen {}-bit)".format(sample_width * 8)
        )

    import array
    samples = array.array("h")
    samples.frombytes(raw)

    if n_channels == 2:
        mono = array.array("h", [0]) * (len(samples) // 2)
        for i in range(len(mono)):
            l = samples[2 * i]
            r = samples[2 * i + 1]
            mono[i] = (l + r) // 2
        samples = mono
    elif n_channels != 1:
        raise ValueError("Podrzan je samo mono ili stereo WAV")

    return samples, sample_rate


def _autocorrelation_pitch(frame, sample_rate):
    """Estimate the fundamental frequency of one frame via autocorrelation.
    Returns None if the frame looks silent/unvoiced."""
    n = len(frame)
    mean = sum(frame) / n
    centered = [s - mean for s in frame]

    energy = sum(s * s for s in centered)
    if energy < 1e-6:
        return None

    lag_min = max(1, int(sample_rate / FMAX))
    lag_max = min(n - 1, int(sample_rate / FMIN))
    if lag_max <= lag_min:
        return None

    best_lag = -1
    best_corr = 0.0
    for lag in range(lag_min, lag_max):
        corr = 0.0
        for i in range(n - lag):
            corr += centered[i] * centered[i + lag]
        if corr > best_corr:
            best_corr = corr
            best_lag = lag

    if best_lag <= 0:
        return None

    confidence = best_corr / (energy + 1e-9)
    if confidence < MIN_CONFIDENCE:
        return None

    return sample_rate / best_lag


class NoteDetector:
    """Incremental, pure-Python pitch/note detector.

    Reads the whole WAV file up-front (cheap: just decoding samples),
    then processes a handful of frames per .step() call so the caller
    can drive it from Clock.schedule_interval on the main thread
    without ever blocking long enough for Android to think the app is
    frozen.

    After construction:
        detector.progress -> float 0.0-1.0
        detector.notes    -> list of {"note": str, "start": float, "end": float}
                              (populated as segments complete, and finalized
                              on the last successful .step() call)

    .step(frames_per_step=N) processes up to N frames and returns True if
    there is more work to do, or False once analysis is finished (or has
    failed and given up).
    """

    def __init__(self, path):
        samples, sample_rate = _read_wav_samples(path)

        max_samples = int(MAX_ANALYSIS_SECONDS * sample_rate)
        if len(samples) > max_samples:
            samples = samples[:max_samples]

        self._samples = samples
        self._sample_rate = sample_rate
        self._pos = 0  # index (in samples) of the next frame to analyze

        # Reference energy for silence detection, based on a quick peek
        # at the loudest frame -- avoids treating a quiet recording as
        # "all silence" just because it's quiet overall.
        self._max_energy = self._estimate_max_energy()

        self.progress = 0.0
        self.notes = []

        # State for the note segment currently being built.
        self._current_note = None
        self._current_start = None
        self._current_end = None

    def _estimate_max_energy(self):
        n = len(self._samples)
        if n == 0:
            return 1.0
        step = max(1, n // (FRAME_SIZE * 20))
        peak = 1.0
        for start in range(0, max(1, n - FRAME_SIZE), HOP_SIZE * step):
            frame = self._samples[start:start + FRAME_SIZE]
            if len(frame) < FRAME_SIZE:
                continue
            mean = sum(frame) / len(frame)
            energy = sum((s - mean) ** 2 for s in frame)
            if energy > peak:
                peak = energy
        return peak

    def _close_current_segment(self, end_time):
        if self._current_note is None:
            return
        if end_time - self._current_start >= MIN_NOTE_DURATION:
            self.notes.append({
                "note": self._current_note,
                "start": self._current_start,
                "end": end_time,
            })
        self._current_note = None
        self._current_start = None
        self._current_end = None

    def _process_frame(self, start_sample):
        frame = self._samples[start_sample:start_sample + FRAME_SIZE]
        if len(frame) < FRAME_SIZE:
            return

        frame_time = start_sample / self._sample_rate
        hop_time = HOP_SIZE / self._sample_rate

        mean = sum(frame) / len(frame)
        energy = sum((s - mean) ** 2 for s in frame)

        note = None
        if self._max_energy <= 0 or energy / self._max_energy >= SILENCE_ENERGY_RATIO:
            freq = _autocorrelation_pitch(frame, self._sample_rate)
            note = freq_to_note(freq) if freq else None

        if note == self._current_note:
            if note is not None:
                self._current_end = frame_time + hop_time
        else:
            self._close_current_segment(frame_time)
            if note is not None:
                self._current_note = note
                self._current_start = frame_time
                self._current_end = frame_time + hop_time

    def step(self, frames_per_step=4):
        n = len(self._samples)
        if n <= FRAME_SIZE:
            self.progress = 1.0
            self._close_current_segment(0.0)
            return False

        last_start = n - FRAME_SIZE

        for _ in range(frames_per_step):
            if self._pos > last_start:
                break
            self._process_frame(self._pos)
            self._pos += HOP_SIZE

        self.progress = min(1.0, self._pos / last_start) if last_start > 0 else 1.0

        if self._pos > last_start:
            end_time = n / self._sample_rate
            self._close_current_segment(end_time)
            self.progress = 1.0
            return False

        return True
