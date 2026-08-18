# -*- coding: utf-8 -*-
"""
screens/recordings.py# -*- coding: utf-8 -*-
"""
screens/recordings.py

FAZA 2: Real recordings list + in-app playback.

Recordings are saved to the app's own private storage (getFilesDir()),
which is invisible to normal file manager apps by design (avoids
Android scoped-storage/permission headaches). Instead of hunting for
the file on the phone, the user sees a simple list here and taps a row
to play it back immediately, using Android's MediaPlayer via pyjnius.

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

            files = [f for f in os.listdir(rec_dir) if f.lower().endswith(".3gp")]
            files.sort(
                key=lambda f: os.path.getmtime(os.path.join(rec_dir, f)),
                reverse=True,
            )

            if not files:
                container.add_widget(self._make_message("Jos uvek nemas nijedan snimak"))
                return

            for fname in files:
                full_path = os.path.join(rec_dir, fname)
                size_kb = os.path.getsize(full_path) // 1024
                row = Factory.RecordingRow()
                row.filename = fname
                row.subtitle = "{} KB \u2014 dodirni za reprodukciju".format(size_kb)
                row.bind(on_release=lambda inst, p=full_path: self.play_recording(p))
                container.add_widget(row)
        except Exception as e:
            container.add_widget(
                self._make_message("Greska pri ucitavanju liste: {}".format(e))
            )

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

List of previously made transcriptions / recordings.
PHASE 1: visual placeholder only. Local database & history list are
added once FAZA 3/4 provide real transcription results to store.
"""

from config import icon
from screens.base import PlaceholderScreen


class RecordingsScreen(PlaceholderScreen):
    def __init__(self, **kwargs):
        super().__init__(
            title="Moji zapisi",
            subtitle=(
                "Ovde \u0107e se prikazivati istorija svih tvojih "
                "prethodnih snimaka i transkripcija."
            ),
            icon_source=icon("recordings.png"),
            phase_note="USKORO",
            **kwargs
        )
