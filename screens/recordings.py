# -*- coding: utf-8 -*-
"""
screens/recordings.py

FAZA 2: Real recordings list + in-app playback + delete.

Recordings are saved to the app's own private storage (getFilesDir()),
invisible to normal file manager apps by design (avoids Android
scoped-storage/permission headaches). The user sees a simple list here
and can tap play to listen, or tap X to delete a recording.

Every risky step is wrapped in try/except and reported directly in the
list (as a message row) rather than crashing, per project strategy.
"""

import os

from kivy.factory import Factory
from kivy.utils import platform
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen


def _recordings_dir():
    from jnius import autoclass

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    context = PythonActivity.mActivity
    return os.path.join(context.getFilesDir().getAbsolutePath(), "recordings")


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
                    "Rad sa snimcima dostupan je samo na Android uredjaju"
                )
            )
            return

        try:
            rec_dir = _recordings_dir()
            if not os.path.isdir(rec_dir):
                container.add_widget(self._make_message("Jos uvek nemas nijedan snimak"))
                return

            files = [f for f in os.listdir(rec_dir) if f.lower().endswith(".m4a")]
            files.sort(
                key=lambda f: os.path.getmtime(os.path.join(rec_dir, f)),
                reverse=True,
            )

            if not files:
                container.add_widget(self._make_message("Jos uvek nemas nijedan snimak"))
                return

            for fname in files:
                full_path = os.path.join(rec_dir, fname)
                self._add_row(container, fname, full_path)
        except Exception as e:
            container.add_widget(
                self._make_message("Greska pri ucitavanju liste: {}".format(e))
            )

    def _add_row(self, container, fname, full_path):
        size_kb = os.path.getsize(full_path) // 1024
        row = Factory.RecordingRow()
        row.filename = fname
        row.subtitle = "{} KB".format(size_kb)
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
                        self._make_message("Jos uvek nemas nijedan snimak")
                    )
        except Exception as e:
            container = self.ids.get("list_container")
            if container is not None:
                container.add_widget(
                    self._make_message("Greska pri brisanju: {}".format(e))
                )
