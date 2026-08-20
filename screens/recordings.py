# -*- coding: utf-8 -*-
"""
screens/recordings.py

FAZA 2/3: Recordings + imported audio list, in-app playback, delete,
and (FAZA 3, WAV recordings only) pure-Python pitch/note analysis.

Recordings are saved to the app's own private storage (getFilesDir()),
invisible to normal file manager apps by design (avoids Android
scoped-storage/permission headaches).

Every risky step is wrapped in try/except and reported directly in the
list (as a message row) rather than crashing, per project strategy.
"""

import os

from kivy.clock import Clock
from kivy.factory import Factory
from kivy.utils import platform
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen


def _app_dir(subfolder):
    from jnius import autoclass

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    context = PythonActivity.mActivity
    return os.path.join(context.getFilesDir().getAbsolutePath(), subfolder)


def _export_dir():
    """Public-ish app-scoped storage (no extra permissions needed on
    modern Android): /storage/emulated/0/Android/data/<package>/files/exports
    Visible via any file manager that can browse Android/data."""
    from jnius import autoclass

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    context = PythonActivity.mActivity
    ext_dir = context.getExternalFilesDir(None)
    base = ext_dir.getAbsolutePath() if ext_dir is not None else _app_dir("exports")
    return os.path.join(base, "exports")


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
            entries += self._collect(_app_dir("recordings"), (".wav",), "Snimljeno")
            entries += self._collect(
                _app_dir("imported"),
                (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"),
                "Ucitano",
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
        is_wav = fname.lower().endswith(".wav")

        row = Factory.RecordingRow()
        row.filename = fname
        row.subtitle = "{} \u2014 {} KB".format(label, size_kb)
        row.can_analyze = is_wav

        row.ids.play_btn.bind(
            on_release=lambda inst, p=full_path: self.play_recording(p)
        )
        row.ids.delete_btn.bind(
            on_release=lambda inst, p=full_path, r=row: self.delete_recording(p, r)
        )
        if is_wav:
            row.ids.analyze_btn.bind(
                on_release=lambda inst, p=full_path, r=row: self.analyze_recording(p, r)
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

    # -- FAZA 3: Analysis --------------------------------------------------
    def analyze_recording(self, path, row_widget):
        row_widget.subtitle = "Analiziram... 0%"

        try:
            from transcription.pitch_detection import NoteDetector
            detector = NoteDetector(path)
        except Exception as e:
            row_widget.subtitle = "Greska pri analizi: {}".format(e)
            return

        def _tick(dt):
            try:
                # Small chunk per tick -- keeps every frame of the app
                # responsive so Android never thinks it's frozen.
                still_working = detector.step(frames_per_step=4)
                row_widget.subtitle = "Analiziram... {}%".format(
                    int(detector.progress * 100)
                )
                if not still_working:
                    row_widget.subtitle = "Analiza zavrsena \u2014 {} nota".format(
                        len(detector.notes)
                    )
                    self._show_results_popup(detector.notes, path)
                    return False  # stop the Clock schedule
            except Exception as e:
                row_widget.subtitle = "Greska pri analizi: {}".format(e)
                return False

        Clock.schedule_interval(_tick, 0.03)

    def _show_results_popup(self, notes, source_path):
        from kivy.uix.popup import Popup
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.label import Label
        from kivy.uix.boxlayout import BoxLayout
        from kivymd.uix.button import MDRaisedButton

        if not notes:
            text = (
                "Nije prepoznata nijedna jasna nota.\n\n"
                "Probaj snimak sa jasnijim, glasnijim pevanjem/sviranjem "
                "jedne melodije (bez pozadinske buke)."
            )
        else:
            lines = [
                "{:<5} {:>6.2f}s - {:<6.2f}s".format(n["note"], n["start"], n["end"])
                for n in notes
            ]
            text = "\n".join(lines)

        label = Label(
            text=text,
            size_hint_y=None,
            halign="left",
            valign="top",
            font_size=14,
        )
        label.bind(
            texture_size=lambda inst, val: setattr(label, "height", val[1]),
            width=lambda inst, val: setattr(label, "text_size", (val, None)),
        )

        scroll = ScrollView()
        scroll.add_widget(label)

        root = BoxLayout(orientation="vertical", spacing="8dp")
        root.add_widget(scroll)

        status_label = Label(text="", size_hint_y=None, height="30dp", font_size=13)
        root.add_widget(status_label)

        popup = Popup(
            title="Prepoznate note ({})".format(len(notes)),
            content=root,
            size_hint=(0.9, 0.85),
        )

        if notes:
            export_btn = MDRaisedButton(
                text="Izvezi kao PDF",
                size_hint_y=None,
                height="44dp",
                pos_hint={"center_x": 0.5},
            )
            export_btn.bind(
                on_release=lambda inst: self._export_pdf(
                    notes, source_path, status_label
                )
            )
            root.add_widget(export_btn)

        popup.open()

    def _export_pdf(self, notes, source_path, status_label):
        try:
            from transcription.notation_pdf import export_notes_to_pdf

            out_dir = _export_dir()
            os.makedirs(out_dir, exist_ok=True)

            base = os.path.splitext(os.path.basename(source_path))[0]
            out_path = os.path.join(out_dir, "{}_note.pdf".format(base))

            export_notes_to_pdf(notes, out_path, title="Note - {}".format(base))
            status_label.text = "Sacuvano: {}".format(out_path)
        except Exception as e:
            status_label.text = "Greska pri izvozu: {}".format(e)
