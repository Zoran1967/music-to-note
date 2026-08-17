# -*- coding: utf-8 -*-
"""
screens/audio_import.py

FAZA 2: Real audio file import (MP3 / WAV).

Uses plyer.filechooser (standard, well-supported package for native
file pickers) to let the user pick a file, then copies it into the
app's own private storage so later phases (analysis, transcription)
always know exactly where to find it.

Every risky step is wrapped in try/except and reported in status_text
on screen, per project strategy -- never fail silently or crash.
"""

import os
import shutil

from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.utils import platform
from kivymd.uix.screen import MDScreen

from config import icon


class AudioImportScreen(MDScreen):
    status_text = StringProperty("Izaberi MP3 ili WAV fajl")
    file_icon = StringProperty(icon("audio.png"))

    def choose_file(self):
        if platform != "android":
            self.status_text = "Uvoz fajla radi samo na Android uredjaju"
            return
        try:
            from plyer import filechooser

            filechooser.open_file(
                on_selection=self._on_file_selected,
                filters=[("Audio fajlovi", "*.mp3", "*.wav")],
            )
        except Exception as e:
            self.status_text = "Greska pri otvaranju biraca fajlova: {}".format(e)

    def _on_file_selected(self, selection):
        # This callback may run off the main thread -- hop back onto it
        # before touching any Kivy properties.
        Clock.schedule_once(lambda dt: self._handle_selection(selection))

    def _handle_selection(self, selection):
        if not selection:
            self.status_text = "Nije izabran fajl"
            return
        src_path = selection[0]
        try:
            from jnius import autoclass

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            context = PythonActivity.mActivity
            dest_dir = os.path.join(
                context.getFilesDir().getAbsolutePath(), "imported"
            )
            os.makedirs(dest_dir, exist_ok=True)
            filename = os.path.basename(src_path)
            dest_path = os.path.join(dest_dir, filename)
            shutil.copy(src_path, dest_path)
            size_kb = os.path.getsize(dest_path) // 1024
            self.status_text = "Ucitano: {} ({} KB)".format(filename, size_kb)
        except Exception as e:
            self.status_text = "Greska pri kopiranju fajla: {}".format(e)
