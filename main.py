# -*- coding: utf-8 -*-
"""
main.py

Glavna ulazna tačka aplikacije Music to Note.
Bezbedno učitava KV fajlove i ekrane, definiše cfg i navigaciju.
"""

import os
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.label import Label
from kivymd.app import MDApp

# Import konfiguracije i storage-a
import config
from storage import SheetStorage


def load_kv_files():
    """
    Bezbedno učitava sve KV fajlove iz foldera 'kv'.
    Prvo učitava theme.kv (gde su definisani ActionCard i IconButton),
    zatim ostale fajlove.
    """
    kv_dir = "kv"
    if os.path.exists(kv_dir):
        # Prvo učitaj theme.kv ako postoji (važno za custom widgete)
        theme_path = os.path.join(kv_dir, "theme.kv")
        if os.path.exists(theme_path):
            try:
                Builder.load_file(theme_path)
            except Exception as e:
                print(f"Upozorenje: Nisam mogao da učitam theme.kv. Greška: {e}")

        # Zatim učitaj sve ostale KV fajlove
        for filename in os.listdir(kv_dir):
            if filename.endswith(".kv") and filename != "theme.kv":
                try:
                    Builder.load_file(os.path.join(kv_dir, filename))
                except Exception as e:
                    print(f"Upozorenje: Nisam mogao da učitam {filename}. Greška: {e}")


class MusicToNoteApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sheet_storage = None
        self.screen_manager = None
        # Povezujemo konfiguraciju sa aplikacijom (da app.cfg radi u KV fajlovima)
        self.cfg = config

    def build(self):
        # Podešavanje teme
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.theme_style = "Dark"

        # 1. Prvo učitaj sve KV fajlove (da ekrani imaju izgled!)
        load_kv_files()

        # 2. Pronađi folder za čuvanje podataka (Android ili Desktop)
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            context = PythonActivity.mActivity
            app_dir = context.getFilesDir().getAbsolutePath()
        except Exception:
            # Za desktop testiranje
            app_dir = os.path.dirname(os.path.abspath(__file__))

        self.sheet_storage = SheetStorage(app_dir)

        # 3. Kreiraj ScreenManager
        self.screen_manager = ScreenManager()

        # 4. Pokušaj da importuješ i dodaš ekrane (preskači one koji ne postoje)
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
            from screens.audio_import import AudioImportScreen
            self.screen_manager.add_widget(AudioImportScreen(name="audio_import"))
        except Exception as e:
            print(f"Upozorenje: AudioImportScreen nije dodat. Greška: {e}")

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

        # Ako imaš i midi ekran, dodaj ga (ako postoji fajl)
        try:
            from screens.midi import MidiScreen
            self.screen_manager.add_widget(MidiScreen(name="midi"))
        except Exception as e:
            print(f"Upozorenje: MidiScreen nije dodat. Greška: {e}")

        # 5. Ako nijedan ekran nije dodat, prikaži poruku
        if len(self.screen_manager.screens) == 0:
            self.screen_manager.add_widget(Label(text="Nema ekrana!"))

        # 6. Vrati ScreenManager
        return self.screen_manager

    def go_to(self, screen_name):
        """Funkcija za navigaciju na drugi ekran."""
        if self.screen_manager.has_screen(screen_name):
            self.screen_manager.current = screen_name
        else:
            print(f"Greška: Ekran '{screen_name}' ne postoji!")

    def go_back(self):
        if self.screen_manager.current != "home":
            self.screen_manager.current = "home"
            return True
        return False


if __name__ == "__main__":
    MusicToNoteApp().run()
