# -*- coding: utf-8 -*-
"""
screens/recorder.py

FAZA 2: Real microphone recording.

Strategy (agreed and locked in project memory):
- Uses pyjnius to call Android's built-in MediaRecorder directly.
  We deliberately do NOT use plyer.audio (known "setAudioSource failed"
  bug) nor the audiostream package (unmaintained, breaks on modern
  python-for-android).
- Every risky operation (permission request, recorder start/stop) is
  wrapped in try/except that reports the problem in status_text on
  screen, instead of silently failing or crashing the app.
- Saves to the app's own private storage (getFilesDir()) so we don't
  need broad external-storage permissions or deal with scoped-storage
  headaches in this phase.
"""

import os
import time

from kivy.clock import Clock
from kivy.properties import StringProperty, BooleanProperty
from kivy.utils import platform
from kivymd.uix.screen import MDScreen

from config import icon


class RecorderScreen(MDScreen):
    status_text = StringProperty("Spremno za snimanje")
    timer_text = StringProperty("00:00")
    mic_icon = StringProperty(icon("microphone.png"))
    is_recording = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._recorder = None
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

            MediaRecorder = autoclass("android.media.MediaRecorder")
            AudioSource = autoclass("android.media.MediaRecorder$AudioSource")
            OutputFormat = autoclass("android.media.MediaRecorder$OutputFormat")
            AudioEncoder = autoclass("android.media.MediaRecorder$AudioEncoder")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")

            context = PythonActivity.mActivity
            rec_dir = os.path.join(
                context.getFilesDir().getAbsolutePath(), "recordings"
            )
            os.makedirs(rec_dir, exist_ok=True)
            filename = "recording_{}.3gp".format(int(time.time()))
            self._output_path = os.path.join(rec_dir, filename)

            recorder = MediaRecorder()
            recorder.setAudioSource(AudioSource.MIC)
            recorder.setOutputFormat(OutputFormat.THREE_GPP)
            recorder.setAudioEncoder(AudioEncoder.AMR_NB)
            recorder.setOutputFile(self._output_path)
            recorder.prepare()
            recorder.start()

            self._recorder = recorder
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
        try:
            if self._recorder is not None:
                self._recorder.stop()
                self._recorder.release()
                self._recorder = None
        except Exception as e:
            self.status_text = "Greska pri zaustavljanju: {}".format(e)
        finally:
            if self._clock_event is not None:
                self._clock_event.cancel()
                self._clock_event = None
            self.is_recording = False
            self.mic_icon = icon("microphone.png")
            if self._output_path and os.path.exists(self._output_path):
                size_kb = os.path.getsize(self._output_path) // 1024
                self.status_text = "Sacuvano: {} ({} KB)".format(
                    os.path.basename(self._output_path), size_kb
                )
            else:
                self.status_text = "Snimak nije sacuvan"
            self.timer_text = "00:00"
