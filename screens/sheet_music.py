# -*- coding: utf-8 -*-
"""
screens/sheet_music.py

FAZA 4: Prikaz notnog zapisa direktno u aplikaciji.

Radi sa listom nota koju generiše transcription/pitch_detection.py
(NoteDetector.notes). Crtanje se obavlja na Kivy Canvas-u -- nema
eksternih biblioteka, ista strategija kao i ostatak projekta.

Note se crtaju na 5 linija (violinski ključ). Trajanje nota je
proporcionalno njihovom trajanju u sekundama -- duža nota = više
horizontalnog prostora.
"""

from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Ellipse, Rectangle
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivy.properties import ListProperty

from config import COLORS, hex_to_rgba


NOTE_LETTERS = ["C", "D", "E", "F", "G", "A", "B"]
STAFF_LINE_GAP = dp(9)
STAFF_TOP_MARGIN = dp(30)
STAFF_BOTTOM_MARGIN = dp(30)
STAFF_LINES = 5
NOTE_SPACING_BASE = dp(20)  # minimalni horizontalni razmak između nota


class StaffCanvas(Widget):
    """Widget koji crta notni zapis na Canvas-u."""

    notes = ListProperty([])  # lista {"note": "A4", "start": 0.0, "end": 1.0}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(notes=self._redraw, size=self._redraw)

    def _redraw(self, *args):
        self.canvas.clear()
        self.clear_widgets()
        if not self.notes:
            return

        with self.canvas:
            self._draw_staff_lines()
            self._draw_notes()

    def _draw_staff_lines(self):
        Color(*hex_to_rgba(COLORS["text_dim"], 0.5))
        y_base = self.height - STAFF_TOP_MARGIN
        line_spacing = STAFF_LINE_GAP
        for i in range(STAFF_LINES):
            y = y_base - i * line_spacing
            Line(points=[0, y, self.width, y], width=1)

    def _note_to_step(self, note_name):
        """'A4' -> step broj (0 = E4, donja linija)."""
        letter = note_name[0]
        rest = note_name[1:]
        accidental = ""
        if rest and rest[0] in "#b":
            accidental = rest[0]
            rest = rest[1:]
        try:
            octave = int(rest)
        except (ValueError, IndexError):
            octave = 4

        letter_index = NOTE_LETTERS.index(letter)
        ref_index = NOTE_LETTERS.index("E")
        step = (octave - 4) * 7 + (letter_index - ref_index)
        return step, accidental

    def _draw_notes(self):
        if not self.notes:
            return

        # Normalizuj trajanja za prikaz
        durations = [max(0.1, n["end"] - n["start"]) for n in self.notes]
        max_dur = max(durations) if durations else 1.0

        x = dp(40)  # početna pozicija (posle ključa)
        y_base = self.height - STAFF_TOP_MARGIN
        step_height = STAFF_LINE_GAP / 2.0

        for n in self.notes:
            duration = max(0.1, n["end"] - n["start"])
            # Duža nota = više horizontalnog prostora
            note_width = NOTE_SPACING_BASE + (duration / max_dur) * dp(30)

            step, accidental = self._note_to_step(n["note"])
            y = y_base - step * step_height

            # Crtanje pomoćnih linija za note van sistema
            if step < 0:
                Color(*hex_to_rgba(COLORS["text_dim"], 0.4))
                s = -2
                while s >= step:
                    if s % 2 == 0:
                        ly = y_base - s * step_height
                        Line(points=[x - dp(5), ly, x + dp(5), ly], width=1)
                    s -= 1
            elif step > 8:
                Color(*hex_to_rgba(COLORS["text_dim"], 0.4))
                s = 10
                while s <= step:
                    if s % 2 == 0:
                        ly = y_base - s * step_height
                        Line(points=[x - dp(5), ly, x + dp(5), ly], width=1)
                    s += 1

            # Crna boja za note
            Color(0, 0, 0, 1)

            # Nota (elipsa)
            rx, ry = dp(4), dp(3)
            Ellipse(pos=(x - rx, y - ry), size=(rx * 2, ry * 2))

            # Vrat note (linija gore ili dole)
            if step >= 4:
                Line(points=[x - rx, y, x - rx, y - dp(22)], width=1.5)
            else:
                Line(points=[x + rx, y, x + rx, y + dp(22)], width=1.5)

            # Akcidental
            if accidental:
                Color(*hex_to_rgba(COLORS["gold"], 0.9))
                Rectangle(pos=(x - dp(12), y - dp(1)), size=(dp(4), dp(4)))

            # Ispis imena note (kao Label widget)
            label = MDLabel(
                text=n["note"],
                font_size=10,
                theme_text_color="Custom",
                text_color=hex_to_rgba(COLORS["text_dim"], 0.8),
                size_hint=(None, None),
                size=(dp(40), dp(15)),
                pos=(x - dp(20), y - dp(28)),
                halign="center",
            )
            self.add_widget(label)

            x += note_width


class SheetMusicScreen(MDScreen):
    """Ekran za prikaz notnog zapisa."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._notes = []

        # Glavni layout
        layout = MDBoxLayout(orientation="vertical")

        # Top bar
        top_bar = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(50),
            padding=[dp(8), dp(4)],
        )

        # Dugme Nazad
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

        # Naslov
        title = MDLabel(
            text="Notni zapis",
            font_style="H6",
            bold=True,
            theme_text_color="Custom",
            text_color=hex_to_rgba(COLORS["white"], 1),
            halign="center",
        )
        top_bar.add_widget(title)

        # Prazan prostor sa desne strane (da naslov bude centriran)
        spacer = MDLabel(size_hint_x=None, width=dp(80))
        top_bar.add_widget(spacer)

        layout.add_widget(top_bar)

        # ScrollView sa Canvas-om
        scroll = ScrollView()
        self.staff_canvas = StaffCanvas(
            size_hint=(None, 1),
            width=dp(500),
        )
        scroll.add_widget(self.staff_canvas)
        layout.add_widget(scroll)

        # Status label
        self.status_label = MDLabel(
            text="Nema prepoznatih nota",
            halign="center",
            theme_text_color="Custom",
            text_color=hex_to_rgba(COLORS["text_dim"], 0.8),
            size_hint_y=None,
            height=dp(30),
        )
        layout.add_widget(self.status_label)

        self.add_widget(layout)

    def _on_back_touch(self, instance, touch):
        if instance.collide_point(*touch.pos):
            from kivy.app import App
            App.get_running_app().go_back()
            return True
        return False

    def set_notes(self, notes):
        """Postavi note za prikaz."""
        self._notes = notes if notes else []
        self.staff_canvas.notes = self._notes

        if not self._notes:
            self.status_label.text = "Nema prepoznatih nota"
        else:
            self.status_label.text = "{} nota".format(len(self._notes))
            # Prilagodi širinu Canvas-a broju nota
            total_width = dp(80) + len(self._notes) * dp(50)
            self.staff_canvas.width = max(dp(500), total_width)

    def clear_notes(self):
        """Obriši prikaz."""
        self.set_notes([])
