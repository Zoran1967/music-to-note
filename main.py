# -*- coding: utf-8 -*-
"""
main.py

Music -> Note
--------------
A modern Android app that listens to music (microphone or audio file)
and turns it into sheet music / MIDI.

FAZA 1: visual environment, theme, navigation -- DONE.
FAZA 2: real microphone recording + real audio file import -- ACTIVE.
FAZA 3+: audio analysis, sheet music, MIDI export -- still placeholders.

DIAGNOSTIC MODE:
If anything fails while building the real UI, this file catches the
error and shows the full Python traceback directly on the phone screen
instead of silently crashing to a black screen. This stays in the code
for the entire life of the project, per project strategy.

Run with (desktop, for design preview):
    python3 main.py
"""

import os
import traceback

from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.utils import platform

if platform not in ("android", "ios"):
    if os.environ.get("MTN_DESKTOP_PREVIEW", "1") == "1":
        Window.size = (390, 780)


def _build_real_app(app):
    """Everything that could realistically break lives in here, wrapped
    by build() below so a failure shows on-screen instead of crashing."""
    import config as cfg
    from kivymd.uix.screenmanager import MDScreenManager
    from kivy.uix.screenmanager import SlideTransition

    from screens.home import HomeScreen
    from screens.recorder import RecorderScreen
    from screens.audio_import import AudioImportScreen
    from screens.sheet_music import SheetMusicScreen
    from screens.midi import MidiScreen
    from screens.recordings import RecordingsScreen
    from screens.settings import SettingsScreen

    app.cfg = cfg
    app.title = cfg.APP_NAME

    LabelBase.register(
        name="Poppins",
        fn_regular=cfg.FONT_REGULAR,
        fn_bold=cfg.FONT_BOLD,
    )
    try:
        for style_name in ("H4", "H5", "H6", "Subtitle1", "Body2", "Caption"):
            app.theme_cls.font_styles[style_name][0] = "Poppins"
    except (KeyError, TypeError, IndexError):
        pass

    app.theme_cls.theme_style = "Dark"
    app.theme_cls.primary_palette = "DeepPurple"
    app.theme_cls.accent_palette = "Cyan"

    Builder.load_file(os.path.join(cfg.KV_DIR, "theme.kv"))
    Builder.load_file(os.path.join(cfg.KV_DIR, "placeholder.kv"))
    Builder.load_file(os.path.join(cfg.KV_DIR, "home.kv"))
    Builder.load_file(os.path.join(cfg.KV_DIR, "recorder.kv"))
    Builder.load_file(os.path.join(cfg.KV_DIR, "audio_import.kv"))

    sm = MDScreenManager()
    sm.transition = SlideTransition(duration=0.22)

    sm.add_widget(HomeScreen(name=cfg.Routes.HOME))
    sm.add_widget(RecorderScreen(name=cfg.Routes.RECORDER))
    sm.add_widget(AudioImportScreen(name=cfg.Routes.AUDIO_IMPORT))
    sm.add_widget(SheetMusicScreen(name=cfg.Routes.SHEET_MUSIC))
    sm.add_widget(MidiScreen(name=cfg.Routes.MIDI))
    sm.add_widget(RecordingsScreen(name=cfg.Routes.RECORDINGS))
    sm.add_widget(SettingsScreen(name=cfg.Routes.SETTINGS))

    sm.current = cfg.Routes.HOME
    app.sm = sm
    return sm


def _build_error_screen(error_text):
    """Plain-Kivy (no KivyMD dependency) scrollable error screen so it
    works even if KivyMD itself is what failed to load."""
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.label import Label
    from kivy.uix.boxlayout import BoxLayout
    from kivy.core.window import Window as _Win

    _Win.clearcolor = (0.05, 0.05, 0.08, 1)

    root = BoxLayout(orientation="vertical", padding=20, spacing=10)
    title = Label(
        text="[b]Music -> Note -- GRESKA PRI POKRETANJU[/b]\n"
             "(uslikaj ovaj ekran i posalji)",
        markup=True,
        size_hint_y=None,
        height=90,
        color=(1, 0.4, 0.4, 1),
        halign="center",
    )
    root.add_widget(title)

    scroll = ScrollView()
    label = Label(
        text=error_text,
        size_hint_y=None,
        text_size=(_Win.width - 40, None),
        color=(0.9, 0.9, 0.95, 1),
        halign="left",
        valign="top",
        font_size=13,
    )
    label.bind(texture_size=lambda inst, val: setattr(label, "height", val[1]))
    scroll.add_widget(label)
    root.add_widget(scroll)
    return root


from kivymd.app import MDApp


class MusicToNoteApp(MDApp):
    """Root application class for Music -> Note."""

    def build(self):
        try:
            return _build_real_app(self)
        except Exception:
            err = traceback.format_exc()
            print("=" * 60)
            print("MUSIC TO NOTE STARTUP ERROR:")
            print(err)
            print("=" * 60)
            return _build_error_screen(err)

    def go_to(self, route_name: str):
        if not hasattr(self, "sm") or self.sm.current == route_name:
            return
        self.sm.transition.direction = "left"
        self.sm.current = route_name

    def go_back(self):
        if not hasattr(self, "sm"):
            return
        self.sm.transition.direction = "right"
        self.sm.current = self.cfg.Routes.HOME


if __name__ == "__main__":
    MusicToNoteApp().run()
