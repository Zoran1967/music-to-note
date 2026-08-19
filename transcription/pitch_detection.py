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
    if confidence
