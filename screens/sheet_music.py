# -*- coding: utf-8 -*-
"""
screens/sheet_music.py

FAZA 4: Upravljanje sačuvanim notnim zapisima.
Vraćeno na stabilnu MDBoxLayout verziju. Dodat pregled nota i preimenovanje.
"""

import os
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField

from config import COLORS, hex_to_rgba


class SheetMusicScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        self.build_ui()

    def build_ui(self):
        root = MDBoxLayout(orientation="vertical")

        top_bar = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(50),
            padding=[dp(8), dp(4)],
        )

        back_btn = MDLabel(
            text="← Nazad",
            font_size=16,
            theme_text_color="Custom",
            text_color=hex_to_rgba(COLORS["white"], 0.9),
            size_hint_x=None,
            width=dp(80),
            halign="left",
        )
        back_btn.bind(on_touch_down=self._on_back_touch)
        top_bar.add_widget(back_btn)

        title = MDLabel(
            text="Moji notni zapisi",
            font_style="H6",
            bold=True,
            theme_text_color="Custom",
            text_color=hex_to_rgba(COLORS["white"], 1),
            halign="center",
            size_hint_x=1,
        )
        top_bar.add_widget(title)

        spacer = MDLabel(size_hint_x=None, width=dp(80))
        top_bar.add_widget(spacer)

        root.add_widget(top_bar)

        scroll = ScrollView()
        self.list_container = MDBoxLayout(
            orientation="vertical",
            padding=[dp(12), dp(8)],
            spacing=dp(8),
            adaptive_height=True,
        )
        scroll.add_widget(self.list_container)
        root.add_widget(scroll)

        self.add_widget(root)

    def on_pre_enter(self, *args):
        self.refresh_list()

    def refresh_list(self):
        self.list_container.clear_widgets()

        app = self._get_app()
        if not hasattr(app, "sheet_storage"):
            self.list_container.add_widget(
                MDLabel(
                    text="Skladište nije dostupno",
                    font_style="Body2",
                    theme_text_color="Custom",
                    text_color=hex_to_rgba(COLORS["text_dim"], 0.8),
                    size_hint_y=None,
                    height=dp(40),
                )
            )
            return

        entries = app.sheet_storage.get_all_entries()
        if not entries:
            self.list_container.add_widget(
                MDLabel(
                    text="Nema sačuvanih notnih zapisa.\nAnalizirajte audio fajl da biste dodali novi.",
                    font_style="Body2",
                    halign="center",
                    theme_text_color="Custom",
                    text_color=hex_to_rgba(COLORS["text_dim"], 0.8),
                    size_hint_y=None,
                    height=dp(80),
                )
            )
            return

        for entry in entries:
            self._add_entry_row(entry)

    def _add_entry_row(self, entry):
        """Pravi red za jedan zapis (kao u originalu, radi 100%)."""
        row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(6),
            size_hint_y=None,
            height=dp(52),
        )

        # Naziv zapisa (klik otvara pregled nota)
        name_btn = MDFlatButton(
            text=entry["name"],
            font_size=14,
            theme_text_color="Custom",
            text_color=hex_to_rgba(COLORS["white"], 1),
            size_hint_x=0.5,
            halign="left",
        )
        name_btn.bind(on_release=lambda inst, eid=entry["id"]: self._show_notes_dialog(eid))
        row.add_widget(name_btn)

        # Dugme za pregled nota (Oko)
        view_btn = MDIconButton(
            icon="eye-outline",
            theme_text_color="Custom",
            text_color=hex_to_rgba(COLORS["white"], 0.8),
            size_hint_x=None,
            width=dp(36),
        )
        view_btn.bind(on_release=lambda inst, eid=entry["id"]: self._show_notes_dialog(eid))
        row.add_widget(view_btn)

        # Dugme za preimenovanje (Olovka)
        rename_btn = MDIconButton(
            icon="pencil-outline",
            theme_text_color="Custom",
            text_color=hex_to_rgba(COLORS["white"], 0.8),
            size_hint_x=None,
            width=dp(36),
        )
        rename_btn.bind(on_release=lambda inst, eid=entry["id"]: self._on_name_click(inst, eid))
        row.add_widget(rename_btn)

        # Dugme za brisanje (Kanta)
        delete_btn = MDIconButton(
            icon="trash-can-outline",
            theme_text_color="Custom",
            text_color=hex_to_rgba(COLORS["danger"], 1),
            size_hint_x=None,
            width=dp(36),
        )
        delete_btn.bind(on_release=lambda inst, eid=entry["id"]: self._delete_entry(eid))
        row.add_widget(delete_btn)

        # Dugme za PDF
        export_pdf_btn = MDIconButton(
            icon="file-pdf-box",
            theme_text_color="Custom",
            text_color=hex_to_rgba(COLORS["cyan"], 1),
            size_hint_x=None,
            width=dp(36),
        )
        export_pdf_btn.bind(on_release=lambda inst, eid=entry["id"]: self._export_entry_pdf(eid))
        row.add_widget(export_pdf_btn)

        # Dugme za MIDI
        export_midi_btn = MDIconButton(
            icon="music-note",
            theme_text_color="Custom",
            text_color=hex_to_rgba(COLORS["gold"], 1),
            size_hint_x=None,
            width=dp(36),
        )
        export_midi_btn.bind(on_release=lambda inst, eid=entry["id"]: self._export_entry_midi(eid))
        row.add_widget(export_midi_btn)

        self.list_container.add_widget(row)

    def _show_notes_dialog(self, entry_id):
        """Prikazuje dijalog sa svim notama iz zapisa."""
        entry = self._get_app().sheet_storage.get_entry(entry_id)
        if not entry:
            return

        content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(4),
            padding=[dp(8), dp(8)],
            adaptive_height=True,
        )

        scroll = ScrollView()
        notes_box = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
            spacing=dp(2),
        )

        if not entry["notes"]:
            notes_box.add_widget(MDLabel(text="Nema nota u ovom zapisu."))
        else:
            for note in entry["notes"]:
                note_text = "{}  {:.2f}s - {:.2f}s".format(
                    note.get("note", "?"),
                    note.get("start", 0.0),
                    note.get("end", 0.0)
                )
                notes_box.add_widget(
                    MDLabel(
                        text=note_text,
                        font_style="Body2",
                        theme_text_color="Custom",
                        text_color=hex_to_rgba(COLORS["white"], 0.9),
                        size_hint_y=None,
                        height=dp(24),
                    )
                )

        scroll.add_widget(notes_box)
        content.add_widget(scroll)

        dialog = MDDialog(
            title=entry["name"],
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="Zatvori",
                    on_release=lambda inst: dialog.dismiss()
                )
            ],
        )
        dialog.open()
        self.dialog = dialog

    def _get_app(self):
        from kivy.app import App
        return App.get_running_app()

    def _on_back_touch(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self._get_app().go_back()
            return True
        return False

    def _on_name_click(self, instance, entry_id):
        entry = self._get_app().sheet_storage.get_entry(entry_id)
        if not entry:
            return
        self._show_rename_dialog(entry_id, entry["name"])

    def _show_rename_dialog(self, entry_id, current_name):
        text_field = MDTextField(
            text=current_name,
            hint_text="Naziv zapisa",
            size_hint_y=None,
            height=dp(48),
        )
        dialog = MDDialog(
            title="Preimenuj zapis",
            type="custom",
            content_cls=MDBoxLayout(
                orientation="vertical",
                spacing=dp(8),
                padding=[dp(16), dp(0), dp(16), dp(8)],
                adaptive_height=True,
            ),
            buttons=[
                MDFlatButton(
                    text="Otkaži",
                    on_release=lambda inst: dialog.dismiss()
                ),
                MDRaisedButton(
                    text="Sačuvaj",
                    on_release=lambda inst: self._rename_entry(entry_id, text_field.text, dialog)
                ),
            ],
        )
        dialog.content_cls.add_widget(text_field)
        dialog.open()
        self.dialog = dialog

    def _rename_entry(self, entry_id, new_name, dialog):
        new_name = new_name.strip()
        if new_name:
            self._get_app().sheet_storage.rename_entry(entry_id, new_name)
            dialog.dismiss()
            self.refresh_list()

    def _delete_entry(self, entry_id):
        self._get_app().sheet_storage.delete_entry(entry_id)
        self.refresh_list()

    def _export_entry_pdf(self, entry_id):
        entry = self._get_app().sheet_storage.get_entry(entry_id)
        if not entry:
            return
        try:
            from transcription.notation_pdf import export_notes_to_pdf
            from android_storage import save_to_downloads

            base = entry["name"].replace(" ", "_")
            display_name = "{}.pdf".format(base)

            tmp_dir = self._get_app_dir("tmp_exports")
            os.makedirs(tmp_dir, exist_ok=True)
            tmp_path = os.path.join(tmp_dir, display_name)

            export_notes_to_pdf(entry["notes"], tmp_path, title=entry["name"], clef=None)

            def _on_done(success, message):
                print("PDF export:", message)

            save_to_downloads(tmp_path, display_name, "application/pdf", _on_done)
        except Exception as e:
            print("Greška pri PDF exportu:", e)

    def _export_entry_midi(self, entry_id):
        entry = self._get_app().sheet_storage.get_entry(entry_id)
        if not entry:
            return
        try:
            from transcription.midi_export import export_notes_to_midi
            from android_storage import save_to_downloads

            base = entry["name"].replace(" ", "_")
            display_name = "{}.mid".format(base)

            tmp_dir = self._get_app_dir("tmp_exports")
            os.makedirs(tmp_dir, exist_ok=True)
            tmp_path = os.path.join(tmp_dir, display_name)

            export_notes_to_midi(entry["notes"], tmp_path)

            # Sacuvaj trajnu kopiju u MIDI biblioteku (glavni ekran -> MIDI)
            try:
                app = self._get_app()
                if hasattr(app, "midi_storage") and app.midi_storage is not None:
                    app.midi_storage.add_entry(entry["name"], tmp_path)
            except Exception as e:
                print("Greška pri čuvanju u MIDI biblioteku:", e)

            def _on_done(success, message):
                print("MIDI export:", message)

            save_to_downloads(tmp_path, display_name, "audio/midi", _on_done)
        except Exception as e:
            print("Greška pri MIDI exportu:", e)

    def _get_app_dir(self, subfolder):
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        context = PythonActivity.mActivity
        return os.path.join(context.getFilesDir().getAbsolutePath(), subfolder)
