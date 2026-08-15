# -*- coding: utf-8 -*-
"""
screens/audio_import.py

Audio file import screen (MP3 / WAV / other supported formats).
PHASE 1: visual placeholder only. File picking and decoding are added
in FAZA 2 of the project brief.
"""

from config import icon
from screens.base import PlaceholderScreen


class AudioImportScreen(PlaceholderScreen):
    def __init__(self, **kwargs):
        super().__init__(
            title="U\u010ditaj audio",
            subtitle=(
                "Izbor MP3, WAV i drugih podr\u017eanih audio fajlova "
                "bi\u0107e omogu\u0107en u slede\u0107oj fazi razvoja."
            ),
            icon_source=icon("audio.png"),
            phase_note="FAZA 2 \u2022 USKORO",
            **kwargs
        )
