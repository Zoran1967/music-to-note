# -*- coding: utf-8 -*-
"""
main.py

Glavna ulazna tačka aplikacije Music to Note.
Sigurna verzija - preskače ekrane koji ne postoje i ne učitava KV fajlove.
"""

import os
from kivy.uix.screenmanager import ScreenManager
from kivymd.app import MDApp

# Import storage-a
from storage import SheetStorage


class MusicToNoteApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sheet_storage = None
        self.screen_manager = None

    def build(self):
        # Podešavanje teme
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.theme_style = "Dark"

        # Pronađi folder za čuvanje podataka (Android ili Desktop)
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            context = PythonActivity.mActivity
            app_dir = context.getFilesDir().getAbsolutePath()
        except Exception:
            # Za desktop testiranje
            app_dir = os.path.dirname(os.path.abspath(__file__))

        self.sheet_storage = SheetStorage(app_dir)

        # Kreiraj ScreenManager
        self.screen_manager = ScreenManager()

        # Pokušaj da importuješ i dodaš ekrane (preskači one koji ne postoje)
        try:
            from screens.home import HomeScreen
            self.screen_manager.add_widget(HomeScreen(name="home"))
        except Exception as e:
            print(f"Upozorenje: HomeScreen nije dodat. Greška: {e}")

        try:
            from screens.recorder import RecorderScreen
            self.screen_manager.add_widget(RecorderScreen(name="recorder"))
        except Exception as e:
            print(f"Upozorenje: RecorderScreen nije dodat. Greška: {e}")

        try:
            from screens.recordings import RecordingsScreen
            self.screen_manager.add_widget(RecordingsScreen(name="recordings"))
        except Exception as e:
            print(f"Upozorenje: RecordingsScreen nije dodat. Greška: {e}")

        try:
            from screens.sheet_music import SheetMusicScreen
            self.screen_manager.add_widget(SheetMusicScreen(name="sheet_music"))
        except Exception as e:
            print(f"Upozorenje: SheetMusicScreen nije dodat. Greška: {e}")

        try:
            from screens.settings import SettingsScreen
            self.screen_manager.add_widget(SettingsScreen(name="settings"))
        except Exception as e:
            print(f"Upozorenje: SettingsScreen nije dodat. Greška: {e}")

        # Ako nijedan ekran nije dodat, dodaj prazan
        if len(self.screen_manager.screens) == 0:
            from kivy.uix.label import Label
            self.screen_manager.add_widget(Label(text="Nema ekrana!"))

        return self.screen_manager

    def go_back(self):
        if self.screen_manager.current != "home":
            self.screen_manager.current = "home"
            return True
        return False


if __name__ == "__main__":
    MusicToNoteApp().run()
