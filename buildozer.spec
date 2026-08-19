[app]
title = Music to Note
package.name = musictonote
package.domain = org.musictonote

source.dir = .
source.include_exts = py,png,jpg,kv,ttf,atlas

version = 0.2.0

# FAZA 2: added pyjnius (direct Android MediaRecorder access for mic
# recording) and plyer (native file picker for audio import).
# FAZA 3: added aubio (lightweight C library for pitch/onset detection --
# chosen over librosa/numpy/scipy to avoid their long history of
# python-for-android build failures). This line is being tested in
# ISOLATION first: aubio is added to requirements and we only try
# `import aubio` at startup to confirm it builds and loads correctly,
# before writing any real pitch-detection logic around it.
requirements = python3==3.11.9,hostpython3==3.11.9,kivy,kivymd==1.2.0,pyjnius,plyer,aubio

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
