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
            btn_row = BoxLayout(
                orientation="horizontal",
                spacing="8dp",
                size_hint_y=None,
                height="44dp",
            )

            export_pdf_btn = MDRaisedButton(
                text="Izvezi kao PDF",
                size_hint_x=0.5,
            )
            export_pdf_btn.bind(
                on_release=lambda inst: self._export_pdf(
                    notes, source_path, status_label
                )
            )
            btn_row.add_widget(export_pdf_btn)

            export_midi_btn = MDRaisedButton(
                text="Izvezi kao MIDI",
                size_hint_x=0.5,
            )
            export_midi_btn.bind(
                on_release=lambda inst: self._export_midi(
                    notes, source_path, status_label
                )
            )
            btn_row.add_widget(export_midi_btn)

            root.add_widget(btn_row)

        popup.open()

    def _export_pdf(self, notes, source_path, status_label):
        try:
            from transcription.notation_pdf import export_notes_to_pdf
            from android_storage import save_to_downloads

            base = os.path.splitext(os.path.basename(source_path))[0]
            display_name = "{}_note.pdf".format(base)

            tmp_dir = _app_dir("tmp_exports")
            os.makedirs(tmp_dir, exist_ok=True)
            tmp_path = os.path.join(tmp_dir, display_name)

            export_notes_to_pdf(notes, tmp_path, title="Note - {}".format(base))
            status_label.text = "Cuvam u Download..."

            def _on_done(success, message):
                if success:
                    status_label.text = "Sacuvano: {}".format(message)
                else:
                    status_label.text = "Greska pri izvozu: {}".format(message)

            save_to_downloads(tmp_path, display_name, "application/pdf", _on_done)
        except Exception as e:
            status_label.text = "Greska pri izvozu: {}".format(e)

    def _export_midi(self, notes, source_path, status_label):
        try:
            from transcription.midi_export import export_notes_to_midi
            from android_storage import save_to_downloads

            base = os.path.splitext(os.path.basename(source_path))[0]
            display_name = "{}_note.mid".format(base)

            tmp_dir = _app_dir("tmp_exports")
            os.makedirs(tmp_dir, exist_ok=True)
            tmp_path = os.path.join(tmp_dir, display_name)

            export_notes_to_midi(notes, tmp_path)
            status_label.text = "Cuvam u Download..."

            def _on_done(success, message):
                if success:
                    status_label.text = "Sacuvano: {}".format(message)
                else:
                    status_label.text = "Greska pri izvozu: {}".format(message)

            save_to_downloads(tmp_path, display_name, "audio/midi", _on_done)
        except Exception as e:
            status_label.text = "Greska pri izvozu: {}".format(e)
