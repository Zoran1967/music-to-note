# -*- coding: utf-8 -*-
"""
screens/audio_import.py

FAZA 2: Real audio file import (MP3 / WAV / M4A / AAC / OGG / FLAC).

STRATEGY NOTE: we do NOT use plyer.filechooser here. It has a known,
long-standing, unresolved bug on Android where picking a file through
certain paths (e.g. the "Gallery" shortcut, some cloud providers) makes
it return an empty selection even though the user did pick a file
(see kivy/plyer issues #512 and #683). Instead we launch Android's
native ACTION_OPEN_DOCUMENT picker directly via pyjnius -- the same
"go straight to the Android API" approach we used for microphone
recording -- and read the picked file ourselves through
ContentResolver, which works reliably regardless of which app/provider
supplied the file.
"""

import os

from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.utils import platform
from kivymd.uix.screen import MDScreen

from config import icon

REQUEST_CODE_PICK_AUDIO = 9001


class AudioImportScreen(MDScreen):
    status_text = StringProperty("Izaberi audio fajl (MP3, WAV, M4A...)")
    file_icon = StringProperty(icon("audio.png"))

    def choose_file(self):
        if platform != "android":
            self.status_text = "Uvoz fajla radi samo na Android uredjaju"
            return
        try:
            from jnius import autoclass
            from android import activity, mActivity

            Intent = autoclass("android.content.Intent")

            intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType("*/*")

            activity.bind(on_activity_result=self._on_activity_result)
            mActivity.startActivityForResult(intent, REQUEST_CODE_PICK_AUDIO)
            self.status_text = "Otvaram birac fajlova..."
        except Exception as e:
            self.status_text = "Greska pri otvaranju biraca fajlova: {}".format(e)

    def _on_activity_result(self, request_code, result_code, intent):
        Clock.schedule_once(
            lambda dt: self._handle_activity_result(request_code, result_code, intent)
        )

    def _handle_activity_result(self, request_code, result_code, intent):
        if request_code != REQUEST_CODE_PICK_AUDIO:
            return
        try:
            from android import activity

            activity.unbind(on_activity_result=self._on_activity_result)
        except Exception:
            pass

        RESULT_OK = -1
        if result_code != RESULT_OK or intent is None:
            self.status_text = "Nije izabran fajl"
            return

        try:
            uri = intent.getData()
            if uri is None:
                self.status_text = "Nije izabran fajl"
                return
            self._import_uri(uri)
        except Exception as e:
            self.status_text = "Greska pri obradi izabranog fajla: {}".format(e)

    def _import_uri(self, uri):
        try:
            from jnius import autoclass

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            context = PythonActivity.mActivity
            resolver = context.getContentResolver()

            # Ask the content provider for the real display name (works
            # for content:// URIs from any source -- Downloads, Gallery,
            # cloud drives, etc.)
            display_name = "imported_audio"
            try:
                OpenableColumns = autoclass("android.provider.OpenableColumns")
                cursor = resolver.query(uri, None, None, None, None)
                if cursor is not None:
                    cursor.moveToFirst()
                    idx = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                    if idx >= 0:
                        display_name = cursor.getString(idx)
                    cursor.close()
            except Exception:
                pass

            ext = os.path.splitext(display_name)[1].lower()
            if ext not in (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".mp4"):
                self.status_text = "Izaberi audio fajl (izabrano: {})".format(
                    display_name
                )
                return

            dest_dir = os.path.join(
                context.getFilesDir().getAbsolutePath(), "imported"
            )
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, display_name)

            input_stream = resolver.openInputStream(uri)
            buf = bytearray(8192)
            with open(dest_path, "wb") as f_out:
                n = input_stream.read(buf)
                while n and n > 0:
                    f_out.write(bytes(buf[:n]))
                    n = input_stream.read(buf)
            input_stream.close()

            size_kb = os.path.getsize(dest_path) // 1024
            self.status_text = "Ucitano: {} ({} KB)".format(display_name, size_kb)
        except Exception as e:
            self.status_text = "Greska pri kopiranju fajla: {}".format(e)
