# -*- coding: utf-8 -*-
"""
screens/settings.py

FAZA 4: Prava podešavanja koja utiču na detekciju i prikaz.
Trenutno podržano:
  - Osetljivost detekcije (klizač)
  - Transpozicija nota (polustepeni)
  - Izbor ključa notnog zapisa (violinski / bas / oba)
Sve izmene se odmah čuvaju u globalnom `settings` objektu iz config.py.

FAZA 6: Redizajniran izgled (kartice sa zaobljenim ivicama i tankim
"glow" okvirom u violet boji), usklađen sa bojama koje već koristi
ostatak aplikacije (config.COLORS). Funkcionalnost je nepromenjena.
"""

from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle, Line
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.slider import MDSlider

from config import settings, COLORS, hex_to_rgba


class _CardBox(MDBoxLayout):
    """Kartica sa zaobljenim ivicama i tankim violet okvirom (bez klika)."""

    def __init__(self, radius=18, bg_alpha=0.55, border_alpha=0.45, **kwargs):
        super().__init__(**kwargs)
        self._radius = dp(radius)
        with self.canvas.before:
            self._bg_color = Color(*hex_to_rgba(COLORS["card_glass"], bg_alpha))
            self._bg_rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[self._radius]
            )
            self._border_color = Color(*hex_to_rgba(COLORS["violet"], border_alpha))
            self._border_line = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, self._radius),
                width=1.3,
            )
        self.bind(pos=self._update_canvas, size=self._update_canvas)

    def _update_canvas(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
        self._border_line.rounded_rectangle = (
            self.x, self.y, self.width, self.height, self._radius
        )


class _GlowButton(ButtonBehavior, MDBoxLayout):
    """Klikabilna kartica sa zaobljenim ivicama i violet okvirom (dugme)."""

    def __init__(self, radius=14, bg_alpha=0.55, border_alpha=0.55, **kwargs):
        super().__init__(**kwargs)
        self._radius = dp(radius)
        self._bg_alpha = bg_alpha
        self._border_alpha = border_alpha
        with self.canvas.before:
            self._bg_color = Color(*hex_to_rgba(COLORS["card_glass"], bg_alpha))
            self._bg_rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[self._radius]
            )
            self._border_color = Color(*hex_to_rgba(COLORS["violet"], border_alpha))
            self._border_line = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, self._radius),
                width=1.4,
            )
        self.bind(pos=self._update_canvas, size=self._update_canvas)

    def _update_canvas(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
        self._border_line.rounded_rectangle = (
            self.x, self.y, self.width, self.height, self._radius
        )

    def set_selected(self, selected):
        bg_hex = COLORS["violet_mid"] if selected else COLORS["card_glass"]
        bg_alpha = 0.9 if selected else self._bg_alpha
        border_alpha = 1.0 if selected else self._border_alpha
        self._bg_color.rgba = hex_to_rgba(bg_hex, bg_alpha)
        self._border_color.rgba = hex_to_rgba(COLORS["violet"], border_alpha)


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
            height=dp(56),
            padding=[dp(16), dp(8)],
        )

        back_btn = MDLabel(
            text="Nazad",
            font_size="15sp",
            theme_text_color="Custom",
            text_color=hex_to_rgba(COLORS["text_dim"], 0.9),
            size_hint_x=None,
            width=dp(70),
            halign="left",
            valign="middle",
        )
        back_btn.bind(on_touch_down=self._on_back_touch)
        top_bar.add_widget(back_btn)

        title = MDLabel(
            text="Podešavanja",
            font_size="26sp",
            bold=True,
            theme_text_color="Custom",
            text_color=hex_to_rgba(COLORS["white"], 1),
            halign="center",
            valign="middle",
        )
        top_bar.add_widget(title)

        spacer = MDLabel(size_hint_x=None, width=dp(70))
        top_bar.add_widget(spacer)

        root.add_widget(top_bar)

        # Skrolabilni deo
        scroll = ScrollView()
        content = MDBoxLayout(
            orientation="vertical",
            padding=[dp(16), dp(4), dp(16), dp(16)],
            spacing=dp(22),
            adaptive_height=True,
        )

        # --- 1. Osetljivost detekcije ---
        content.add_widget(self._make_section_title("Osetljivost detekcije"))

        sens_card = _CardBox(
            orientation="vertical",
            spacing=dp(10),
            padding=[dp(18), dp(18)],
            adaptive_height=True,
            radius=18,
        )

        self.sens_value_label = MDLabel(
            text="{}".format(settings.sensitivity),
            font_size="30sp",
            bold=True,
            theme_text_color="Custom",
            text_color=hex_to_rgba(COLORS["violet"], 1),
            size_hint_y=None,
            height=dp(42),
            halign="center",
        )
        sens_card.add_widget(self.sens_value_label)

        self.sens_slider = MDSlider(
            min=0.2,
            max=0.8,
            value=settings.sensitivity,
            step=0.01,
            size_hint_y=None,
            height=dp(36),
        )
        self.sens_slider.bind(on_value=self._on_sensitivity_change)
        sens_card.add_widget(self.sens_slider)

        sens_card.add_widget(
            self._make_description_label(
                "Veća vrednost = strožija detekcija (manje lažnih nota, "
                "ali može propustiti tihe tonove)"
            )
        )
        content.add_widget(sens_card)

        # --- 2. Transpozicija ---
        content.add_widget(self._make_section_title("Transpozicija (polustepeni)"))

        trans_card = _CardBox(
            orientation="vertical",
            spacing=dp(10),
            padding=[dp(18), dp(18)],
            adaptive_height=True,
            radius=18,
        )

        trans_controls = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(14),
            size_hint_y=None,
            height=dp(52),
        )

        minus_btn = _GlowButton(
            radius=14,
            size_hint_x=None,
            width=dp(52),
            padding=[0, 0],
        )
        minus_label = MDLabel(
            text="\u2212",
            font_size="22sp",
            bold=True,
            theme_text_color="Custom",
            text_color=hex_to_rgba(COLORS["white"], 1),
            halign="center",
            valign="middle",
        )
        minus_btn.add_widget(minus_label)
        minus_btn.bind(on_release=lambda inst: self._change_transpose(-1))
        trans_controls.add_widget(minus_btn)

        self.trans_value_label = MDLabel(
            text="{}".format(settings.transpose),
            font_size="30sp",
            bold=True,
            theme_text_color="Custom",
            text_color=hex_to_rgba(COLORS["violet"], 1),
            halign="center",
            valign="middle",
            size_hint_x=1,
        )
        trans_controls.add_widget(self.trans_value_label)

        plus_btn = _GlowButton(
            radius=14,
            size_hint_x=None,
            width=dp(52),
            padding=[0, 0],
        )
        plus_label = MDLabel(
            text="+",
            font_size="22sp",
            bold=True,
            theme_text_color="Custom",
            text_color=hex_to_rgba(COLORS["white"], 1),
            halign="center",
            valign="middle",
        )
        plus_btn.add_widget(plus_label)
        plus_btn.bind(on_release=lambda inst: self._change_transpose(1))
        trans_controls.add_widget(plus_btn)

        trans_card.add_widget(trans_controls)

        trans_card.add_widget(
            self._make_description_label(
                "Pomera sve prepoznate note za odabrani broj polustepena"
            )
        )
        content.add_widget(trans_card)

        # --- 3. Ključ notnog zapisa ---
        content.add_widget(self._make_section_title("Ključ notnog zapisa"))

        clef_card = _CardBox(
            orientation="vertical",
            spacing=dp(10),
            padding=[dp(10), dp(10)],
            adaptive_height=True,
            radius=18,
        )

        clef_buttons = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(52),
        )

        self.treble_btn = self._make_clef_button("Violinski", "treble")
        clef_buttons.add_widget(self.treble_btn)

        self.bass_btn = self._make_clef_button("Bas", "bass")
        clef_buttons.add_widget(self.bass_btn)

        self.both_btn = self._make_clef_button("Oba", "both")
        clef_buttons.add_widget(self.both_btn)

        clef_card.add_widget(clef_buttons)

        clef_card.add_widget(
            self._make_description_label("Utiče na izgled notnog zapisa (PDF i ekran)")
        )
        content.add_widget(clef_card)

        # --- 4. Reset dugme ---
        reset_btn = _GlowButton(
            radius=24,
            bg_alpha=0.65,
            border_alpha=0.7,
            size_hint_y=None,
            height=dp(52),
        )
        reset_label = MDLabel(
            text="Resetuj podrazumevano",
            font_size="16sp",
            bold=True,
            theme_text_color="Custom",
            text_color=hex_to_rgba(COLORS["white"], 1),
            halign="center",
            valign="middle",
        )
        reset_btn.add_widget(reset_label)
        reset_btn.bind(on_release=self._reset_settings)
        content.add_widget(reset_btn)

        scroll.add_widget(content)
        root.add_widget(scroll)

        self.add_widget(root)

        # Ažuriraj izgled dugmadi za trenutni ključ
        self._update_clef_buttons()

    def _make_clef_button(self, text, clef_id):
        btn = _GlowButton(
            radius=14,
            size_hint_x=1,
            padding=[dp(6), dp(6)],
        )
        label = MDLabel(
            text=text,
            font_size="14sp",
            bold=True,
            theme_text_color="Custom",
            text_color=hex_to_rgba(COLORS["white"], 1),
            halign="center",
            valign="middle",
        )
        btn.add_widget(label)
        btn.bind(on_release=lambda inst: self._set_clef(clef_id))
        return btn

    def _make_section_title(self, title):
        label = MDLabel(
            text=title,
            font_size="18sp",
            bold=True,
            theme_text_color="Custom",
            text_color=hex_to_rgba(COLORS["white"], 1),
            size_hint_y=None,
            halign="left",
        )
        label.bind(
            texture_size=lambda inst, val: setattr(inst, "height", val[1] + dp(4))
        )
        return label

    def _make_description_label(self, text):
        """Pravi opisni tekst sa Caption stilom i dinamičkom visinom."""
        label = MDLabel(
            text=text,
            font_style="Caption",
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
        self.treble_btn.set_selected(clef == "treble")
        self.bass_btn.set_selected(clef == "bass")
        self.both_btn.set_selected(clef == "both")

    def _reset_settings(self, instance):
        settings.reset_to_defaults()
        self.sens_slider.value = settings.sensitivity
        self.sens_value_label.text = "{}".format(settings.sensitivity)
        self.trans_value_label.text = "{}".format(settings.transpose)
        self._update_clef_buttons()
