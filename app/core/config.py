"""
Application settings module.

This module re-exports the settings from app.config.settings to maintain
backward compatibility with existing imports.
"""
from app.config.settings import Settings, get_settings, settings

__all__ = ["Settings", "get_settings", "settings"]