[app]
title = Music to Note
package.name = musictonote
package.domain = org.musictonote

source.dir = .
source.include_exts = py,png,jpg,kv,ttf,atlas

version = 0.3.0

# FAZA 2: pyjnius (direct Android API access) + plyer.
# FAZA 3: pitch detection now implemented in PURE PYTHON (see
# transcription/pitch_detection.py) instead of aubio/numpy. Those
# proved too fragile to build for Android (numpy 2.x ABI break in
# aubio's old C code, then numpy recipe git-tag mismatches). No new
# native dependencies needed for this phase.
requirements = python3==3.11.9,hostpython3==3.11.9,kivy,kivymd==1.2.0,pyjnius,plyer

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
