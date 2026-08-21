# -*- coding: utf-8 -*-
"""
screens/settings.py

FAZA 4: Prava podešavanja koja utiču na detekciju i prikaz.
Trenutno podržano:
  - Osetljivost detekcije (klizač)
  - Transpozicija nota (polustepeni)
  - Izbor ključa notnog zapisa (violinski / bas / oba)
Sve izmene se odmah čuvaju u globalnom `settings` objektu iz config.py.
"""

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.slider import MDSlider
from kivymd.uix.button import MDRaisedButton, MDFlatButton

from config import settings, COLORS, hex_to_rgba


class SettingsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        # Glavni vertikalni layout
        root = MDBoxLayout(orientation="vertical")

        # Top bar
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
            text="Podešavanja",
            font_style="H6",
            bold=True,
            theme_text_color="Custom",
            text_color=hex_to_rgba(COLORS["white"], 1),
            halign="center",
        )
        top_bar.add_widget(title)

        spacer = MDLabel(size_hint_x=None, width=dp(80))
        top_bar.add_widget(spacer)

        root.add_widget(top_bar)

        # Skrolabilni deo
        scroll = ScrollView()
        content = MDBoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(8)],
            spacing=dp(20),
            adaptive_height=True,
        )

        # --- 1. Osetljivost detekcije ---
        sens_box = self._build_section("Osetljivost detekcije")
        self.sens_value_label = MDLabel(
            text="{}".format(settings.sensitivity),
            font_style="Subtitle1",
            theme_text_color="Custom",
            text_color=hex_to_rgba(COLORS["violet"], 1),
            size_hint_y=None,
            height=dp(30),
            halign="center",
        )
        sens_box.add_widget(self.sens_value_label)

        self.sens_slider = MDSlider(
            min=0.2,
            max=0.8,
            value=settings.sensitivity,
            step=0.01,
            size_hint_y=None,
            height=dp(40),
        )
        self.sens_slider.bind(on_value=self._on_sensitivity_change)
        sens_box.add_widget(self.sens_slider)

        sens_desc = self._make_description_label(
            "Veća vrednost = strožija detekcija (manje lažnih nota, ali može propustiti tihe tonove)"
        )
        sens_box.add_widget(sens_desc)
        content.add_widget(sens_box)

        # --- 2. Transpozicija ---
        trans_box = self._build_section("Transpozicija (polustepeni)")
        trans_controls = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(40),
        )

        minus_btn = MDRaisedButton(text="-", size_hint_x=None, width=dp(50))
        minus_btn.bind(on_release=lambda inst: self._change_transpose(-1))
        trans_controls.add_widget(minus_btn)

        self.trans_value_label = MDLabel(
            text="{}".format(settings.transpose),
            font_style="H5",
            bold=True,
            theme_text_color="Custom",
            text_color=hex_to_rgba(COLORS["violet"], 1),
            halign="center",
            size_hint_x=1,
        )
        trans_controls.add_widget(self.trans_value_label)

        plus_btn = MDRaisedButton(text="+", size_hint_x=None, width=dp(50))
        plus_btn.bind(on_release=lambda inst: self._change_transpose(1))
        trans_controls.add_widget(plus_btn)

        trans_box.add_widget(trans_controls)

        trans_desc = self._make_description_label(
            "Pomera sve prepoznate note za odabrani broj polustepena"
        )
        trans_box.add_widget(trans_desc)
        content.add_widget(trans_box)

        # --- 3. Ključ notnog zapisa ---
        clef_box = self._build_section("Ključ notnog zapisa")
        clef_buttons = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(40),
        )

        self.treble_btn = MDFlatButton(text="Violinski", size_hint_x=1)
        self.treble_btn.bind(on_release=lambda inst: self._set_clef("treble"))
        clef_buttons.add_widget(self.treble_btn)

        self.bass_btn = MDFlatButton(text="Bas", size_hint_x=1)
        self.bass_btn.bind(on_release=lambda inst: self._set_clef("bass"))
        clef_buttons.add_widget(self.bass_btn)

        self.both_btn = MDFlatButton(text="Oba", size_hint_x=1)
        self.both_btn.bind(on_release=lambda inst: self._set_clef("both"))
        clef_buttons.add_widget(self.both_btn)

        clef_box.add_widget(clef_buttons)

        clef_desc = self._make_description_label(
            "Utiče na izgled notnog zapisa (PDF i ekran)"
        )
        clef_box.add_widget(clef_desc)
        content.add_widget(clef_box)

        # --- 4. Reset dugme ---
        reset_btn = MDRaisedButton(
            text="Resetuj podrazumevano",
            size_hint_y=None,
            height=dp(44),
        )
        reset_btn.bind(on_release=self._reset_settings)
        content.add_widget(reset_btn)

        scroll.add_widget(content)
        root.add_widget(scroll)

        self.add_widget(root)

        # Ažuriraj izgled dugmadi za trenutni ključ
        self._update_clef_buttons()

    def _build_section(self, title):
        """Pravi BoxLayout sa naslovom i sadržajem."""
        box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8),
            adaptive_height=True,  # visina se prilagođava sadržaju
        )
        title_label = MDLabel(
            text=title,
            font_style="Subtitle1",  # smanjeno sa H6
            bold=True,
            theme_text_color="Custom",
            text_color=hex_to_rgba(COLORS["white"], 1),
            size_hint_y=None,
            halign="left",
        )
        # Dinamička visina naslova (prelamanje na uži ekran)
        title_label.bind(
            texture_size=lambda inst, val: setattr(inst, "height", val[1] + dp(4))
        )
        box.add_widget(title_label)
        return box

    def _make_description_label(self, text):
        """Pravi opisni tekst sa Caption stilom i dinamičkom visinom."""
        label = MDLabel(
            text=text,
            font_style="Caption",  # smanjeno sa Body2
            theme_text_color="Custom",
            text_color=hex_to_rgba(COLORS["text_dim"], 0.8),
            size_hint_y=None,
            halign="left",
        )
        label.bind(
            texture_size=lambda inst, val: setattr(inst, "height", val[1] + dp(4))
        )
        return label

    def _on_back_touch(self, instance, touch):
        if instance.collide_point(*touch.pos):
            from kivy.app import App
            App.get_running_app().go_back()
            return True
        return False

    # --- Rukovaoci izmenama ---
    def _on_sensitivity_change(self, instance, value):
        settings.sensitivity = round(float(value), 2)
        self.sens_value_label.text = "{}".format(settings.sensitivity)

    def _change_transpose(self, delta):
        settings.transpose = max(-12, min(12, settings.transpose + delta))
        self.trans_value_label.text = "{}".format(settings.transpose)

    def _set_clef(self, clef):
        settings.clef = clef
        self._update_clef_buttons()

    def _update_clef_buttons(self):
        """Vizuelno označi selektovani ključ."""
        clef = settings.clef
        self.treble_btn.md_bg_color = hex_to_rgba(COLORS["violet"], 0.3) if clef == "treble" else (0, 0, 0, 0)
        self.bass_btn.md_bg_color = hex_to_rgba(COLORS["violet"], 0.3) if clef == "bass" else (0, 0, 0, 0)
        self.both_btn.md_bg_color = hex_to_rgba(COLORS["violet"], 0.3) if clef == "both" else (0, 0, 0, 0)

    def _reset_settings(self, instance):
        settings.reset_to_defaults()
        self.sens_slider.value = settings.sensitivity
        self.sens_value_label.text = "{}".format(settings.sensitivity)
        self.trans_value_label.text = "{}".format(settings.transpose)
        self._update_clef_buttons()
