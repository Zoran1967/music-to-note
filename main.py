# -*- coding: utf-8 -*-
"""
main.py

Glavna ulazna tačka aplikacije Music to Note.
Inicijalizuje sve module, storage i pokreće KivyMD aplikaciju.
"""

import os

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from kivymd.app import MDApp

# Import postojećih modula
from config import COLORS, hex_to_rgba
from storage import SheetStorage

# Učitavanje KV fajlova (ako postoje u folderu kv)
def load_kv_files():
    kv_dir = "kv"
    if os.path.exists(kv_dir):
        for filename in os.listdir(kv_dir):
            if filename.endswith(".kv"):
                Builder.load_file(os.path.join(kv_dir, filename))

class MusicToNoteApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sheet_storage = None
        self.screen_manager = None

    def build(self):
        # Podešavanje teme (boje, font)
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.theme_style = "Dark"

        # Učitaj sve KV fajlove (osim onih koje smo definisali u Pythonu)
        try:
            load_kv_files()
        except Exception as e:
            print(f"Greška pri učitavanju KV fajlova: {e}")

        # Inicijalizuj SheetStorage u privatnom Android folderu
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            context = PythonActivity.mActivity
            app_dir = context.getFilesDir().getAbsolutePath()
        except Exception:
            # Za desktop testiranje (ako nema Androida)
            app_dir = os.path.dirname(os.path.abspath(__file__))

        self.sheet_storage = SheetStorage(app_dir)

        # Kreiraj ScreenManager i dodaj sve postojeće ekrane
        self.screen_manager = ScreenManager()

        # Import ekrana (screens folder)
        from screens.home import HomeScreen
        from screens.recorder import RecorderScreen
        from screens.recordings import RecordingsScreen
        from screens.sheet_music import SheetMusicScreen
        from screens.settings import SettingsScreen

        self.screen_manager.add_widget(HomeScreen(name="home"))
        self.screen_manager.add_widget(RecorderScreen(name="recorder"))
        self.screen_manager.add_widget(RecordingsScreen(name="recordings"))
        self.screen_manager.add_widget(SheetMusicScreen(name="sheet_music"))
        self.screen_manager.add_widget(SettingsScreen(name="settings"))

        return self.screen_manager

    def go_back(self):
        """Vraća na prethodni ekran."""
        if self.screen_manager.current != "home":
            self.screen_manager.current = "home"
            return True
        return False

if __name__ == "__main__":
    # Podesi veličinu prozora za desktop testiranje (opciono)
    Window.size = (360, 640)
    MusicToNoteApp().run()
