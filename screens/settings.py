# -*- coding: utf-8 -*-
"""
screens/settings.py

Application settings screen.
PHASE 1: visual placeholder only. Real preferences (audio quality,
sensitivity, theme, storage location, etc.) are wired in a later phase.
"""

from config import icon
from screens.base import PlaceholderScreen


class SettingsScreen(PlaceholderScreen):
    def __init__(self, **kwargs):
        super().__init__(
            title="Pode\u0161avanja",
            subtitle=(
                "Pode\u0161avanja aplikacije (kvalitet zvuka, osetljivost, "
                "tema) bi\u0107e dodata u narednim fazama."
            ),
            icon_source=icon("settings.png"),
            phase_note="USKORO",
            **kwargs
        )
