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

        # 4. Pokušaj da importuješ i dodaš ekrane. Greške se VIŠE NE
        # gutaju tiho -- svaka se skuplja u load_errors i prikazuje na
        # ekranu (popup) čim se aplikacija pokrene, tako da se odmah
        # vidi ako neki ekran nije uspeo da se učita, umesto da dugme
        # naizgled "ne radi ništa" bez objašnjenja.
        self.load_errors = []

        screen_imports = [
            ("home", "screens.home", "HomeScreen"),
            ("recorder", "screens.recorder", "RecorderScreen"),
            ("audio_import", "screens.audio_import", "AudioImportScreen"),
            ("recordings", "screens.recordings", "RecordingsScreen"),
            ("sheet_music", "screens.sheet_music", "SheetMusicScreen"),
            ("settings", "screens.settings", "SettingsScreen"),
            ("midi", "screens.midi", "MidiScreen"),
        ]
        for screen_name, module_name, class_name in screen_imports:
            try:
                module = __import__(module_name, fromlist=[class_name])
                screen_cls = getattr(module, class_name)
                self.screen_manager.add_widget(screen_cls(name=screen_name))
            except Exception as e:
                import traceback
                err_text = traceback.format_exc()
                print(f"Upozorenje: {class_name} nije dodat. Greška: {e}")
                self.load_errors.append((screen_name, str(e), err_text))

        # 5. Ako nijedan ekran nije dodat, prikaži poruku
        if len(self.screen_manager.screens) == 0:
            self.screen_manager.add_widget(Label(text="Nema ekrana!"))

        # 6. Ako je nesto od ucitavanja ekrana puklo, pokazi to VIDLJIVO
        # na ekranu (ne samo u nevidljivoj konzoli).
        if self.load_errors:
            from kivy.clock import Clock
            Clock.schedule_once(self._show_load_errors, 0.5)

        # 7. Vrati ScreenManager
        return self.screen_manager

    def _show_load_errors(self, dt):
        from kivy.uix.popup import Popup
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.boxlayout import BoxLayout

        lines = []
        for screen_name, short_err, full_trace in self.load_errors:
            lines.append("=== {} ===\n{}\n".format(screen_name, full_trace))
        text = "\n".join(lines)

        label = Label(
            text=text,
            size_hint_y=None,
            halign="left",
            valign="top",
            font_size=12,
            color=(1, 0.5, 0.5, 1),
        )
        label.bind(
            texture_size=lambda inst, val: setattr(label, "height", val[1]),
            width=lambda inst, val: setattr(label, "text_size", (val, None)),
        )
        scroll = ScrollView()
        scroll.add_widget(label)
        root = BoxLayout(orientation="vertical")
        root.add_widget(scroll)

        popup = Popup(
            title="Neki ekrani nisu ucitani ({})".format(len(self.load_errors)),
            content=root,
            size_hint=(0.95, 0.9),
        )
        popup.open()

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
