# -*- coding: utf-8 -*-
"""
screens/sheet_music.py

Displays the resulting sheet-music transcription of a previous analysis.
PHASE 1: visual placeholder only. Real note-rendering engine is added in
FAZA 4 of the project brief, after audio analysis (FAZA 3) exists.
"""

from config import icon
from screens.base import PlaceholderScreen


class SheetMusicScreen(PlaceholderScreen):
    def __init__(self, **kwargs):
        super().__init__(
            title="Notni zapis",
            subtitle=(
                "Automatski notni zapis tvoje muzike pojavi\u0107e se "
                "ovde nakon \u0161to analiza zvuka bude implementirana."
            ),
            icon_source=icon("sheet_music.png"),
            phase_note="FAZA 4 \u2022 USKORO",
            **kwargs
        )
