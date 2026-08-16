[app]
title = Music to Note
package.name = musictonote
package.domain = org.musictonote

source.dir = .
source.include_exts = py,png,jpg,kv,ttf,atlas

version = 0.1.0

# PHASE 1: only UI/navigation deps. Audio + AI libraries are added from
# FAZA 2/3 onward (e.g. numpy, librosa, music21, pretty_midi).
requirements = python3==3.11.9,hostpython3==3.11.9,kivy,kivymd

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
