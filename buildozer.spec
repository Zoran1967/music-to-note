[app]
title = Music to Note
package.name = musictonote
package.domain = org.musictonote

source.dir = .
source.include_exts = py,png,jpg,kv,ttf,atlas

version = 0.2.0

# FAZA 2: pyjnius (Android MediaRecorder) + plyer (retired, replaced by
# direct Intent-based file picker, but package harmless to keep).
# FAZA 3: aubio for pitch/onset detection. aubio 0.4.9's optional numpy
# ufunc wrapper (ufuncs.c) is written against the OLD numpy C API and
# fails to compile against numpy 2.x (breaking API change in 2024).
# Pinning numpy==1.26.4 (last stable 1.x release, fully Python 3.11
# compatible) fixes this without needing a numpy upgrade anywhere else
# in the app.
requirements = python3==3.11.9,hostpython3==3.11.9,kivy,kivymd==1.2.0,pyjnius,plyer,numpy==1.26.4,aubio==0.4.9

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/assets/icons/music_notes.png

android.permissions = RECORD_AUDIO,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 34
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
