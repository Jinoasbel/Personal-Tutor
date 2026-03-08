"""
paths.py — Runtime path resolver for frozen (PyInstaller) and source environments.
"""
from __future__ import annotations
import sys
from pathlib import Path


def _exe_root() -> Path:
    """Directory containing the exe (frozen) or main.py (source)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    # Source: go up from core/ to project root
    return Path(__file__).resolve().parent.parent


def _bundle_root() -> Path:
    """Where read-only bundled files live (icons, theme, etc.)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def get_asset(*parts: str) -> Path:
    """Resolve a read-only asset path (bundled inside _MEIPASS when frozen)."""
    return _bundle_root() / "assets" / Path(*parts)


def get_voice_samples_dir() -> Path:
    """
    Voice samples are written by the app so they must live next to the exe
    (writable), NOT inside _MEIPASS (read-only).
    """
    p = _exe_root() / "assets" / "voice_samples"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_data(*parts: str) -> Path:
    """Resolve a user-data path (always writable, next to exe)."""
    return _exe_root() / "Data" / Path(*parts)
