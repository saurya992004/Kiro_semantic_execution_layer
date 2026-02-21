"""
Phase 12 — Personalisation Module
System personalization tools for Jarvis
"""

from .personalisation_tools import (
    toggle_dark_mode,
    get_current_theme,
    set_wallpaper,
    set_display_brightness,
    set_display_resolution,
    set_accent_color,
    set_default_app,
    manage_startup_apps,
    apply_theme_preset,
    save_personalization_profile,
    load_personalization_profile
)

__all__ = [
    "toggle_dark_mode",
    "get_current_theme",
    "set_wallpaper",
    "set_display_brightness",
    "set_display_resolution",
    "set_accent_color",
    "set_default_app",
    "manage_startup_apps",
    "apply_theme_preset",
    "save_personalization_profile",
    "load_personalization_profile"
]
