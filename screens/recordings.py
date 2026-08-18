# -*- coding: utf-8 -*-
"""
screens/recordings.py

FAZA 2: Real recordings + imported audio list, in-app playback, delete.

Shows BOTH microphone recordings (getFilesDir()/recordings, .m4a) AND
imported audio files (getFilesDir()/imported, .mp3 / .wav) in one
combined, newest-first list, so there's a single place to find and
play anything the user has captured or brought into the app.

Every risky step is wrapped in try/except and reported directly in the
list (as a message row) rather than crashing, per project strategy.
"""

import os

from kivy.factory import Factory
from kivy.utils import platform
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen


def _app_dir(subfolder):
    from jnius import autoclass

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    context = PythonActivity.mActivity
    return os.path.join(context.getFilesDir().getAbsolutePath(), subfolder)


class RecordingsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._player = None

    # -- Lifecycle --------------------------------------------------
    def on_pre_enter(self, *args):
        self.refresh_list()

    def on_leave(self, *args):
        self._stop_playback()

    # -- List building --------------------------------------------------
    def refresh_list(self):
        container = self.ids.get("list_container")
        if container is None:
            return
        container.clear_widgets()

        if platform != "android":
            container.add_widget(
                self._make_message(
                    "Rad sa zapisima dostupan je samo na Android uredjaju"
                )
            )
            return

        try:
            entries = []
            entries += self._collect(
                _app_dir("recordings"), (".m4a",), "Snimljeno"
            )
            entries += self._collect(
                _app_dir("imported"), (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"), "Ucitano"
            )
            entries.sort(key=lambda e: e[2], reverse=True)  # newest first

            if not entries:
                container.add_widget(
                    self._make_message("Jos uvek nemas nijedan zapis")
                )
                return

            for full_path, fname, _mtime, label in entries:
                self._add_row(container, fname, full_path, label)
        except Exception as e:
            container.add_widget(
                self._make_message("Greska pri ucitavanju liste: {}".format(e))
            )

    def _collect(self, folder, extensions, label):
        results = []
        if os.path.isdir(folder):
            for fname in os.listdir(folder):
                if fname.lower().endswith(extensions):
                    full_path = os.path.join(folder, fname)
                    mtime = os.path.getmtime(full_path)
                    results.append((full_path, fname, mtime, label))
        return results

    def _add_row(self, container, fname, full_path, label):
        size_kb = os.path.getsize(full_path) // 1024
        row = Factory.RecordingRow()
        row.filename = fname
        row.subtitle = "{} \u2014 {} KB".format(label, size_kb)
        row.ids.play_btn.bind(
            on_release=lambda inst, p=full_path: self.play_recording(p)
        )
        row.ids.delete_btn.bind(
            on_release=lambda inst, p=full_path, r=row: self.delete_recording(p, r)
        )
        container.add_widget(row)

    def _make_message(self, text):
        return MDLabel(
            text=text,
            font_style="Body2",
            halign="center",
            theme_text_color="Custom",
            text_color=(0.70, 0.72, 0.88, 1),
            size_hint_y=None,
            height="60dp",
        )

    # -- Playback --------------------------------------------------
    def play_recording(self, path):
        try:
            from jnius import autoclass

            self._stop_playback()

            MediaPlayer = autoclass("android.media.MediaPlayer")
            player = MediaPlayer()
            player.setDataSource(path)
            player.prepare()
            player.start()
            self._player = player
        except Exception as e:
            container = self.ids.get("list_container")
            if container is not None:
                container.add_widget(
                    self._make_message("Greska pri reprodukciji: {}".format(e))
                )

    def _stop_playback(self):
        if self._player is not None:
            try:
                self._player.stop()
                self._player.release()
            except Exception:
                pass
            self._player = None

    # -- Delete --------------------------------------------------
    def delete_recording(self, path, row_widget):
        try:
            self._stop_playback()
            if os.path.exists(path):
                os.remove(path)
            container = self.ids.get("list_container")
            if container is not None and row_widget in container.children:
                container.remove_widget(row_widget)
                if not container.children:
                    container.add_widget(
                        self._make_message("Jos uvek nemas nijedan zapis")
                    )
        except Exception as e:
            container = self.ids.get("list_container")
            if container is not None:
                container.add_widget(
                    self._make_message("Greska pri brisanju: {}".format(e))
                )
