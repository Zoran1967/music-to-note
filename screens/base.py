# -*- coding: utf-8 -*-
"""
screens/base.py

PlaceholderScreen is the shared base class for every secondary screen in
PHASE 1 (Recorder, Audio Import, Sheet Music, MIDI, Recordings, Settings).

Each concrete screen only sets its icon / title / subtitle -- the actual
KV layout lives once in kv/placeholder.kv and is reused automatically by
every subclass, so the whole app looks and feels consistent from the
very first phase. Real behaviour (audio capture, transcription, MIDI
export, etc.) is intentionally NOT implemented yet; it is added in later
phases without needing to touch this shared visual layer.
"""

from kivymd.uix.screen import MDScreen
from kivy.properties import StringProperty


class PlaceholderScreen(MDScreen):
    """Generic 'coming in a later phase' screen with a consistent look."""

    title_text = StringProperty("")
    subtitle_text = StringProperty("")
    icon_source = StringProperty("")
    phase_note = StringProperty("USKORO")

    def __init__(self, title, subtitle, icon_source, phase_note="USKORO", **kwargs):
        self.title_text = title
        self.subtitle_text = subtitle
        self.icon_source = icon_source
        self.phase_note = phase_note
        super().__init__(**kwargs)
