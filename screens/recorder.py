# -*- coding: utf-8 -*-
"""
screens/recorder.py

Microphone recording screen.
PHASE 1: visual placeholder only. Real microphone capture, live waveform
rendering, and note detection are added in later phases (see FAZA 2 and
FAZA 3 in the project brief).
"""

from config import icon
from screens.base import PlaceholderScreen


class RecorderScreen(PlaceholderScreen):
    def __init__(self, **kwargs):
        super().__init__(
            title="Snimi muziku",
            subtitle=(
                "Snimanje preko mikrofona i analiza zvuka u\u017eivo "
                "bi\u0107e dostupni u slede\u0107oj fazi razvoja."
            ),
            icon_source=icon("microphone.png"),
            phase_note="FAZA 2 \u2022 USKORO",
            **kwargs
        )
