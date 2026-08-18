# -*- coding: utf-8 -*-
"""
screens/audio_import.py

FAZA 2: Real audio file import (MP3 / WAV).

Uses plyer.filechooser (native file picker), then copies the picked
file into the app's own private storage so later phases (analysis,
transcription) always know exactly where to find it.

NOTE: we deliberately do NOT pass a `filters` argument to
filechooser.open_file() -- plyer's filter format is inconsistent
across platforms and was causing the picker to return None instead of
a real path. Instead we accept any file and check the extension
ourselves after the user picks one, which is more robust.
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

            filechooser.open_file(on_selection=self._on_file_selected)
        except Exception as e:
            self.status_text = "Greska pri otvaranju biraca fajlova: {}".format(e)

    def _on_file_selected(self, selection):
        # This callback may run off the main thread -- hop back onto it
        # before touching any Kivy properties.
        Clock.schedule_once(lambda dt: self._handle_selection(selection))

    def _handle_selection(self, selection):
        if not selection or not selection[0]:
            self.status_text = "Nije izabran fajl"
            return

        src_path = selection[0]
        if not isinstance(src_path, str):
            self.status_text = "Neocekivan format izabranog fajla"
            return

        ext = os.path.splitext(src_path)[1].lower()
        if ext not in (".mp3", ".wav"):
            self.status_text = "Izaberi MP3 ili WAV fajl (izabrano: {})".format(
                ext or "nepoznat format"
            )
            return

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
