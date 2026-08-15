# -*- coding: utf-8 -*-
"""
screens/recordings.py

List of previously made transcriptions / recordings.
PHASE 1: visual placeholder only. Local database & history list are
added once FAZA 3/4 provide real transcription results to store.
"""

from config import icon
from screens.base import PlaceholderScreen


class RecordingsScreen(PlaceholderScreen):
    def __init__(self, **kwargs):
        super().__init__(
            title="Moji zapisi",
            subtitle=(
                "Ovde \u0107e se prikazivati istorija svih tvojih "
                "prethodnih snimaka i transkripcija."
            ),
            icon_source=icon("recordings.png"),
            phase_note="USKORO",
            **kwargs
        )
