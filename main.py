# -*- coding: utf-8 -*-
"""
main.py

Music -> Note
--------------
A modern Android app that listens to music (microphone or audio file)
and turns it into sheet music / MIDI.

PHASE 1 OF DEVELOPMENT
=======================
This build contains ONLY the visual environment and navigation of the
app: theme, background, icon set, home screen, and placeholder screens
for every planned feature. There is intentionally NO audio capture, NO
signal analysis, and NO database logic yet -- those arrive in later,
clearly separated phases (see the module docstrings inside audio/,
transcription/, and database/ for what is planned there).

Run with (desktop, for design preview):
    python3 main.py

Package for Android later with Buildozer once functionality is added.
"""

import os

from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.lang import Builder

from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivy.uix.screenmanager import SlideTransition

import config as cfg
from screens.home import HomeScreen
from screens.recorder import RecorderScreen
from screens.audio_import import AudioImportScreen
from screens.sheet_music import SheetMusicScreen
from screens.midi import MidiScreen
from screens.recordings import RecordingsScreen
from screens.settings import SettingsScreen


# A comfortable portrait preview size when running on desktop during
# design/review. This has no effect on the real Android build, where
# the OS controls the window size.
if os.environ.get("MTN_DESKTOP_PREVIEW", "1") == "1":
    Window.size = (390, 780)


class MusicToNoteApp(MDApp):
    """Root application class for Music -> Note."""

    # Exposed to every KV file as `app.cfg` so screens can reach paths,
    # colors and copy without hard-coding strings all over the UI.
    cfg = cfg

    def build(self):
        self.title = cfg.APP_NAME

        # Register the custom Poppins family for a premium, consistent
        # typographic feel across the whole app.
        LabelBase.register(
            name="Poppins",
            fn_regular=cfg.FONT_REGULAR,
            fn_bold=cfg.FONT_BOLD,
        )
        self.theme_cls.font_styles["H5"][0] = "Poppins"
        self.theme_cls.font_styles["H6"][0] = "Poppins"
        self.theme_cls.font_styles["Subtitle1"][0] = "Poppins"
        self.theme_cls.font_styles["Body2"][0] = "Poppins"
        self.theme_cls.font_styles["Caption"][0] = "Poppins"

        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.accent_palette = "Cyan"

        # Load the shared design-system KV files before any screen KV,
        # so <GlassCard>, <ActionCard>, <IconButton>, <TopBar> exist
        # by the time home.kv / placeholder.kv reference them.
        Builder.load_file(os.path.join(cfg.KV_DIR, "theme.kv"))
        Builder.load_file(os.path.join(cfg.KV_DIR, "placeholder.kv"))
        Builder.load_file(os.path.join(cfg.KV_DIR, "home.kv"))

        self.sm = MDScreenManager()
        self.sm.transition = SlideTransition(duration=0.22)

        self.sm.add_widget(HomeScreen(name=cfg.Routes.HOME))
        self.sm.add_widget(RecorderScreen(name=cfg.Routes.RECORDER))
        self.sm.add_widget(AudioImportScreen(name=cfg.Routes.AUDIO_IMPORT))
        self.sm.add_widget(SheetMusicScreen(name=cfg.Routes.SHEET_MUSIC))
        self.sm.add_widget(MidiScreen(name=cfg.Routes.MIDI))
        self.sm.add_widget(RecordingsScreen(name=cfg.Routes.RECORDINGS))
        self.sm.add_widget(SettingsScreen(name=cfg.Routes.SETTINGS))

        self.sm.current = cfg.Routes.HOME
        return self.sm

    # -- Simple, shared navigation helpers used from every KV file ------
    def go_to(self, route_name: str):
        if self.sm.current == route_name:
            return
        self.sm.transition.direction = "left"
        self.sm.current = route_name

    def go_back(self):
        self.sm.transition.direction = "right"
        self.sm.current = cfg.Routes.HOME


if __name__ == "__main__":
    MusicToNoteApp().run()
