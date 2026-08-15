# Music → Note

Android aplikacija koja slu\u0161a muziku (mikrofon ili audio fajl) i pretvara je u notni zapis / MIDI.

## Status: FAZA 1 — izgled i okruženje ✅

Ova verzija sadrži **isključivo**:
- kompletnu vizuelnu temu (boje, tipografija, pozadina)
- kompletan set od 12 tematskih PNG ikonica u jedinstvenom dizajn-sistemu
- glavni ekran sa navigacijom ka svih 6 funkcija
- placeholder ekrane za svaku funkciju (Snimi muziku, Učitaj audio, Notni zapis, MIDI, Moji zapisi, Podešavanja)
- pripremljenu modularnu arhitekturu za sledeće faze

**Nema još:** snimanja zvuka, analize, prepoznavanja tonova, baze podataka. To dolazi u narednim fazama (FAZA 2–6), redom, tek kada se potvrdi izgled.

## Struktura projekta

```
MusicToNotes/
├── main.py                 # Ulazna tačka aplikacije, ScreenManager, tema
├── config.py                # Boje, putanje, tipografija, konstante
├── requirements.txt
├── buildozer.spec           # Android build konfiguracija
│
├── screens/
│   ├── base.py               # PlaceholderScreen (deljen izgled za faze 2-6)
│   ├── home.py                # Glavni ekran
│   ├── recorder.py            # 🎤 Snimi muziku (placeholder)
│   ├── audio_import.py        # 🎵 Učitaj audio (placeholder)
│   ├── sheet_music.py         # 🎼 Notni zapis (placeholder)
│   ├── midi.py                 # 🎹 MIDI (placeholder)
│   ├── recordings.py          # 📂 Moji zapisi (placeholder)
│   └── settings.py             # ⚙️ Podešavanja (placeholder)
│
├── kv/
│   ├── theme.kv               # Deljeni dizajn-sistem: GlassCard, ActionCard, IconButton, TopBar
│   ├── home.kv                 # Layout glavnog ekrana
│   └── placeholder.kv          # Deljeni layout za sve sekundarne ekrane
│
├── assets/
│   ├── icons/                  # 12 PNG ikonica (microphone, audio, music_notes, sheet_music,
│   │                            #  midi, recordings, settings, back, play, pause, stop, save)
│   ├── backgrounds/             # main_background.png + hero_visual.png
│   └── fonts/                   # Poppins (Regular/Medium/Bold/Light)
│
├── audio/          # REZERVISANO za FAZU 2 (mikrofon, učitavanje fajlova)
├── transcription/  # REZERVISANO za FAZU 3-4 (analiza zvuka, notni zapis)
└── database/        # REZERVISANO za FAZU 4+ (istorija zapisa, podešavanja)
```

## Pokretanje na desktopu (za pregled dizajna)

```bash
pip install -r requirements.txt
python3 main.py
```

Otvara se prozor veličine telefona (390×780) radi lakšeg pregleda dizajna. Ovo je samo desktop-preview mod za developere; na pravom Android uređaju aplikacija koristi ceo ekran.

## Build za Android

```bash
pip install buildozer
buildozer android debug
```

(Zahteva Linux/WSL okruženje sa Android SDK/NDK zavisnostima koje buildozer sam preuzima pri prvom pokretanju.)

## Sledeći koraci (ne raditi dok se FAZA 1 ne potvrdi)

- **FAZA 2** — mikrofon (snimanje uživo) i učitavanje audio fajlova (MP3/WAV)
- **FAZA 3** — analiza zvuka i prepoznavanje tonova
- **FAZA 4** — automatsko formiranje notnog zapisa
- **FAZA 5** — MIDI / MusicXML / PDF export
- **FAZA 6** — poboljšanje AI transkripcije, razdvajanje instrumenata, optimizacija za Android
