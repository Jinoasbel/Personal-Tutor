"""
app_config.py — Application-level configuration constants.
"""

from pathlib import Path


class Config:
    # ── Paths ─────────────────────────────────────────────────────────────────
    DATA_DIR          = Path("Data")
    AUDIO_OUTPUT      = DATA_DIR / "output_audio.mp3"
    TEMP_DIR          = DATA_DIR / "temp"

    EXTRACTED_DIR     = DATA_DIR / "extracted"
    EXTRACTED_FILE    = EXTRACTED_DIR / "fromfile"
    EXTRACTED_LINK    = EXTRACTED_DIR / "fromlink"

    # Generated question sets saved as question1.json, question2.json …
    QUESTIONS_DIR     = DATA_DIR / "questions"

    # Quiz attempt results saved as result1.json, result2.json …
    RESULTS_DIR       = DATA_DIR / "results"

    # ── AI Service ────────────────────────────────────────────────────────────
    AI_PROVIDER       = "claude"           # "claude" | "openai"
    AI_API_KEY        = ""                 # or set via env var ANTHROPIC_API_KEY / OPENAI_API_KEY
    AI_MODEL_CLAUDE   = "claude-sonnet-4-20250514"
    AI_MODEL_OPENAI   = "gpt-4o"
    AI_QUESTION_COUNT = 10                 # questions per generation

    # ── OCR ───────────────────────────────────────────────────────────────────
    OCR_LANG          = "en"

    # ── Features ──────────────────────────────────────────────────────────────
    FEATURE_AUDIO     = True
    FEATURE_QA        = True
    FEATURE_LINKS     = True
    HIGH_DPI          = True
