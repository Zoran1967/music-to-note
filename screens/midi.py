# -*- coding: utf-8 -*-
"""
screens/midi.py

FAZA 5: Biblioteka sačuvanih MIDI zapisa.

Svaki put kad se MIDI izveze -- bilo iz Recordings ekrana (analiza
snimka) bilo iz Sheet Music ekrana (izvoz sačuvanog notnog zapisa) --
trajna kopija tog .mid fajla se automatski čuva ovde preko
storage.MidiStorage. Korisnik ovde vidi sve sačuvane MIDI zapise,
numerisane redom, jedan ispod drugog, sa dugmetom za brisanje i
dugmetom za ponovni izvoz u Downloads (bez potrebe da ponovo radi
analizu ili traži originalni notni zapis).
"""

import os

from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton

from config import COLORS, hex_to_rgba


class MidiScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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
            text="\u2190 Nazad",
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
            text="Moji MIDI zapisi",
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
            spacing=dp(12),
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
        if not hasattr(app, "midi_storage") or app.midi_storage is None:
            self.list_container.add_widget(
                MDLabel(
                    text="Skladište MIDI zapisa nije dostupno",
                    font_style="Body2",
                    theme_text_color="Custom",
                    text_color=hex_to_rgba(COLORS["text_dim"], 0.8),
                    size_hint_y=None,
                    height=dp(40),
                )
            )
            return

        entries = app.midi_storage.get_all_entries()
        if not entries:
            self.list_container.add_widget(
                MDLabel(
                    text=(
                        "Nema sačuvanih MIDI zapisa.\n"
                        "Izvezi MIDI iz snimka ili notnog zapisa "
                        "da bi se pojavio ovde."
                    ),
                    font_style="Body2",
                    halign="center",
                    theme_text_color="Custom",
                    text_color=hex_to_rgba(COLORS["text_dim"], 0.8),
                    size_hint_y=None,
                    height=dp(80),
                )
            )
            return

        for index, entry in enumerate(entries, start=1):
            self._add_entry_row(index, entry)

    def _add_entry_row(self, index, entry):
        row = MDBoxLayout(
            orientation="vertical",
            spacing=dp(6),
            padding=[dp(4), dp(4)],
            size_hint_y=None,
            height=dp(92),
        )

        title_label = MDLabel(
            text="{}. {}".format(index, entry["name"]),
            font_size="13sp",
            bold=True,
            theme_text_color="Custom",
            text_color=hex_to_rgba(COLORS["white"], 1),
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle",
            shorten=True,
            shorten_from="right",
        )
        title_label.bind(
            width=lambda inst, val: setattr(inst, "text_size", (val, dp(28)))
        )
        row.add_widget(title_label)

        btn_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(40),
        )

        delete_btn = MDRaisedButton(
            text="Obriši MIDI",
            md_bg_color=hex_to_rgba(COLORS["danger"], 1),
            size_hint_x=0.5,
        )
        delete_btn.bind(
            on_release=lambda inst, eid=entry["id"]: self._delete_entry(eid)
        )
        btn_row.add_widget(delete_btn)

        export_btn = MDRaisedButton(
            text="Izvezi",
            md_bg_color=hex_to_rgba(COLORS["gold"], 1),
            size_hint_x=0.5,
        )
        export_btn.bind(
            on_release=lambda inst, eid=entry["id"]: self._export_entry(eid)
        )
        btn_row.add_widget(export_btn)

        row.add_widget(btn_row)

        separator = MDBoxLayout(
            size_hint_y=None,
            height=dp(1),
        )
        row.add_widget(separator)

        self.list_container.add_widget(row)

    def _get_app(self):
        from kivy.app import App
        return App.get_running_app()

    def _on_back_touch(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self._get_app().go_back()
            return True
        return False

    def _delete_entry(self, entry_id):
        self._get_app().midi_storage.delete_entry(entry_id)
        self.refresh_list()

    def _export_entry(self, entry_id):
        app = self._get_app()
        entry = app.midi_storage.get_entry(entry_id)
        if not entry:
            return
        try:
            from android_storage import save_to_downloads

            stored_path = app.midi_storage.get_entry_path(entry_id)
            if stored_path is None or not os.path.exists(stored_path):
                print("MIDI fajl nije pronadjen na disku")
                return

            base = entry["name"].replace(" ", "_")
            display_name = "{}.mid".format(base)

            def _on_done(success, message):
                print("MIDI izvoz:", message)

            save_to_downloads(stored_path, display_name, "audio/midi", _on_done)
        except Exception as e:
            print("Greska pri izvozu MIDI zapisa:", e)
