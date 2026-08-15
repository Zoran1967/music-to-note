# -*- coding: utf-8 -*-
"""
config.py
Centralized configuration: paths, color palette, typography, and
shared UI constants for the Music -> Note application.

PHASE 1 NOTE:
This phase only defines visual/theme constants and asset paths.
No audio, transcription, or database logic is configured here yet.
"""

import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ASSETS_DIR = os.path.join(BASE_DIR, "assets")
ICONS_DIR = os.path.join(ASSETS_DIR, "icons")
BACKGROUNDS_DIR = os.path.join(ASSETS_DIR, "backgrounds")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
KV_DIR = os.path.join(BASE_DIR, "kv")


def icon(name: str) -> str:
    """Return absolute path to an icon asset by filename."""
    return os.path.join(ICONS_DIR, name)


def background(name: str) -> str:
    """Return absolute path to a background asset by filename."""
    return os.path.join(BACKGROUNDS_DIR, name)


MAIN_BACKGROUND = background("main_background.png")
HERO_VISUAL = background("hero_visual.png")

# ---------------------------------------------------------------------------
# Color palette (Hex + normalized RGBA for KivyMD)
# ---------------------------------------------------------------------------
COLORS = {
    "navy_deep":    "#0A0C18",
    "navy_mid":     "#131029",
    "violet_deep":  "#1C1038",
    "violet_mid":   "#281A4A",
    "violet":       "#7C4DFF",
    "cyan":         "#00E5FF",
    "gold":         "#FFC857",
    "white":        "#F5F7FF",
    "text_dim":     "#B7B9D6",
    "card_glass":   "#1A1730",
    "danger":       "#FF5C7A",
}


def hex_to_rgba(hex_color: str, alpha: float = 1.0):
    """Convert '#RRGGBB' to a normalized (r, g, b, a) tuple for KivyMD."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return (r, g, b, alpha)


# Pre-computed RGBA tuples used throughout the KV templates
RGBA = {name: hex_to_rgba(value) for name, value in COLORS.items()}

# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------
FONT_REGULAR = os.path.join(FONTS_DIR, "Poppins-Regular.ttf")
FONT_MEDIUM = os.path.join(FONTS_DIR, "Poppins-Medium.ttf")
FONT_BOLD = os.path.join(FONTS_DIR, "Poppins-Bold.ttf")
FONT_LIGHT = os.path.join(FONTS_DIR, "Poppins-Light.ttf")

# ---------------------------------------------------------------------------
# Shared UI constants
# ---------------------------------------------------------------------------
CARD_RADIUS = 26
BUTTON_RADIUS = 20
GLOW_OPACITY = 0.35

APP_NAME = "Music \u2192 Note"
APP_TAGLINE = "Sluša muziku. Ispisuje note."

# Screen route names (used by ScreenManager)
class Routes:
    HOME = "home"
    RECORDER = "recorder"
    AUDIO_IMPORT = "audio_import"
    SHEET_MUSIC = "sheet_music"
    MIDI = "midi"
    RECORDINGS = "recordings"
    SETTINGS = "settings"
