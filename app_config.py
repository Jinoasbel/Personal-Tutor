"""
app_config.py — Application-level configuration constants.

Paths are resolved relative to the exe when frozen (PyInstaller)
or relative to the project root when running from source.
"""

import sys
from pathlib import Path


def _root() -> Path:
    """Directory next to the exe or next to main.py."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


class Config:
    # ── Paths ─────────────────────────────────────────────────────────────────
    DATA_DIR          = _root() / "Data"
    TEMP_DIR          = DATA_DIR / "temp"

    EXTRACTED_DIR     = DATA_DIR / "extracted"
    EXTRACTED_FILE    = EXTRACTED_DIR / "fromfile"
    EXTRACTED_LINK    = EXTRACTED_DIR / "fromlink"

    QUESTIONS_DIR     = DATA_DIR / "questions"
    RESULTS_DIR       = DATA_DIR / "results"
    SUMMARIES_DIR     = DATA_DIR / "summaries"
    LESSONS_DIR       = DATA_DIR / "lessons"
    AUDIO_DIR         = DATA_DIR / "audio"
    AUDIO_OUTPUT      = AUDIO_DIR / "output_audio.wav"

    # ── AI Service ────────────────────────────────────────────────────────────
    AI_PROVIDER       = "anthropic"
    AI_API_KEY        = ""
    AI_MODEL_CLAUDE   = "claude-sonnet-4-20250514"
    AI_MODEL_OPENAI   = "gpt-4o"
    AI_QUESTION_COUNT = 10

    # ── OCR ───────────────────────────────────────────────────────────────────
    OCR_LANG          = "en"

    # ── Features ──────────────────────────────────────────────────────────────
    FEATURE_AUDIO     = True
    FEATURE_QA        = True
    FEATURE_LINKS     = True
    HIGH_DPI          = True
