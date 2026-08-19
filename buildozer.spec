[app]
title = Music to Note
package.name = musictonote
package.domain = org.musictonote

source.dir = .
source.include_exts = py,png,jpg,kv,ttf,atlas

version = 0.2.0

# FAZA 2: pyjnius (Android MediaRecorder) + plyer.
# FAZA 3: aubio for pitch/onset detection. aubio 0.4.9's optional numpy
# ufunc wrapper needs an OLD numpy C API and breaks against numpy 2.x.
# p4a's numpy recipe clones from git and does `git checkout <version>`,
# and numpy's actual GitHub release tags use a "v" prefix (v1.26.4),
# which our previous attempt (bare "1.26.4") didn't match.
requirements = python3==3.11.9,hostpython3==3.11.9,kivy,kivymd==1.2.0,pyjnius,plyer,numpy==v1.26.4,aubio==0.4.9

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
