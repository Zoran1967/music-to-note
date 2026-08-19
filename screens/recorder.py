# -*- coding: utf-8 -*-
"""
screens/recorder.py

FAZA 2/3: Real microphone recording -- now via raw PCM capture.

STRATEGY CHANGE (FAZA 3): switched from MediaRecorder (compressed
AAC/.m4a output) to Android's AudioRecord API, which gives us raw PCM
audio samples directly. We write those samples to a plain WAV file
using Python's built-in `wave` module (zero dependencies). This means
our own recordings can be pitch-analyzed later using a pure-Python
algorithm (no numpy/aubio needed -- those proved too fragile to build
for Android, see project history), AND it sidesteps any
MediaRecorder/MediaPlayer codec quirks entirely.

Every risky operation is wrapped in try/except that reports the
problem in status_text on screen, per project strategy.
"""

import os
import time
import threading
import wave

from kivy.clock import Clock
from kivy.properties import StringProperty, BooleanProperty
from kivy.utils import platform
from kivymd.uix.screen import MDScreen

from config import icon

SAMPLE_RATE = 16000  # plenty for musical pitch detection, keeps files small


class RecorderScreen(MDScreen):
    status_text = StringProperty("Spremno za snimanje")
    timer_text = StringProperty("00:00")
    mic_icon = StringProperty(icon("microphone.png"))
    is_recording = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._audio_record = None
        self._record_thread = None
        self._stop_flag = False
        self._pcm_chunks = []
        self._start_time = None
        self._clock_event = None
        self._output_path = None
        self._permission_granted = False

    # -- Lifecycle --------------------------------------------------
    def on_pre_enter(self, *args):
        if platform == "android":
            self._ensure_permission()
        else:
            self.status_text = "Snimanje radi samo na Android uredjaju"

    # -- Permissions --------------------------------------------------
    def _ensure_permission(self):
        try:
            from android.permissions import (
                request_permissions,
                Permission,
                check_permission,
            )

            if check_permission(Permission.RECORD_AUDIO):
                self._permission_granted = True
                self.status_text = "Spremno za snimanje"
                return

            def _callback(permissions, results):
                def _apply(dt):
                    self._permission_granted = bool(results) and all(results)
                    if self._permission_granted:
                        self.status_text = "Spremno za snimanje"
                    else:
                        self.status_text = "Dozvola za mikrofon nije odobrena"

                Clock.schedule_once(_apply)

            request_permissions([Permission.RECORD_AUDIO], _callback)
        except Exception as e:
            self.status_text = "Greska pri trazenju dozvole: {}".format(e)

    # -- Recording control --------------------------------------------------
    def toggle_record(self):
        if platform != "android":
            self.status_text = "Snimanje radi samo na Android uredjaju"
            return
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        if not self._permission_granted:
            self.status_text = "Cekam dozvolu za mikrofon..."
            self._ensure_permission()
            return
        try:
            from jnius import autoclass

            AudioRecord = autoclass("android.media.AudioRecord")
            AudioFormat = autoclass("android.media.AudioFormat")
            AudioSource = autoclass("android.media.MediaRecorder$AudioSource")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")

            context = PythonActivity.mActivity
            rec_dir = os.path.join(
                context.getFilesDir().getAbsolutePath(), "recordings"
            )
            os.makedirs(rec_dir, exist_ok=True)
            filename = "recording_{}.wav".format(int(time.time()))
            self._output_path = os.path.join(rec_dir, filename)

            channel_config = AudioFormat.CHANNEL_IN_MONO
            audio_format = AudioFormat.ENCODING_PCM_16BIT

            min_buf = AudioRecord.getMinBufferSize(
                SAMPLE_RATE, channel_config, audio_format
            )
            if min_buf <= 0:
                raise RuntimeError("Nepodrzana konfiguracija mikrofona na ovom uredjaju")
            buf_size = max(min_buf, SAMPLE_RATE * 2)

            audio_record = AudioRecord(
                AudioSource.MIC, SAMPLE_RATE, channel_config, audio_format, buf_size
            )
            audio_record.startRecording()

            self._audio_record = audio_record
            self._pcm_chunks = []
            self._stop_flag = False

            def _record_loop(rec=audio_record, size=buf_size, chunks=self._pcm_chunks):
                java_buf = bytearray(size)
                while not self._stop_flag:
                    n = rec.read(java_buf, 0, len(java_buf))
                    if n and n > 0:
                        chunks.append(bytes(java_buf[:n]))

            self._record_thread = threading.Thread(target=_record_loop, daemon=True)
            self._record_thread.start()

            self._start_time = time.time()
            self.is_recording = True
            self.mic_icon = icon("stop.png")
            self.status_text = "Snima se..."
            self._clock_event = Clock.schedule_interval(self._update_timer, 0.5)
        except Exception as e:
            self.status_text = "Greska pri pokretanju snimanja: {}".format(e)
            self.is_recording = False

    def _update_timer(self, dt):
        elapsed = int(time.time() - self._start_time)
        m, s = divmod(elapsed, 60)
        self.timer_text = "{:02d}:{:02d}".format(m, s)

    def stop_recording(self):
        recorded_seconds = 0
        if self._start_time is not None:
            recorded_seconds = time.time() - self._start_time

        self._stop_flag = True
        if self._record_thread is not None:
            self._record_thread.join(timeout=2.0)
            self._record_thread = None

        try:
            if self._audio_record is not None:
                self._audio_record.stop()
                self._audio_record.release()
                self._audio_record = None
        except Exception as e:
            self.status_text = "Greska pri zaustavljanju: {}".format(e)

        if self._clock_event is not None:
            self._clock_event.cancel()
            self._clock_event = None
        self.is_recording = False
        self.mic_icon = icon("microphone.png")

        if recorded_seconds < 0.6:
            self.status_text = "Snimak prekratak, pokusaj ponovo (drzi due)"
            self.timer_text = "00:00"
            return

        try:
            pcm_data = b"".join(self._pcm_chunks)
            self._pcm_chunks = []
            if not pcm_data:
                self.status_text = "Snimak nije sacuvan (nema podataka)"
                self.timer_text = "00:00"
                return

            with wave.open(self._output_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit PCM
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(pcm_data)

            size_kb = os.path.getsize(self._output_path) // 1024
            self.status_text = "Sacuvano: {} ({} KB)".format(
                os.path.basename(self._output_path), size_kb
            )
        except Exception as e:
            self.status_text = "Greska pri cuvanju WAV fajla: {}".format(e)
        finally:
            self.timer_text = "00:00"
