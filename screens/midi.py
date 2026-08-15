# -*- coding: utf-8 -*-
"""
screens/midi.py

MIDI export / playback screen.
PHASE 1: visual placeholder only. MIDI generation and export (MusicXML /
PDF too) are added in FAZA 5 of the project brief.
"""

from config import icon
from screens.base import PlaceholderScreen


class MidiScreen(PlaceholderScreen):
    def __init__(self, **kwargs):
        super().__init__(
            title="MIDI",
            subtitle=(
                "Generisanje i izvoz MIDI zapisa iz prepoznate muzike "
                "bi\u0107e dostupno u kasnijoj fazi razvoja."
            ),
            icon_source=icon("midi.png"),
            phase_note="FAZA 5 \u2022 USKORO",
            **kwargs
        )
