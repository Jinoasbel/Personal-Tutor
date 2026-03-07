"""
app_config.py — Application-level configuration constants.
"""

from pathlib import Path


class Config:
    # ── Paths ─────────────────────────────────────────────────────────────────
    DATA_DIR          = Path("Data")
    TEMP_DIR          = DATA_DIR / "temp"

    EXTRACTED_DIR     = DATA_DIR / "extracted"
    EXTRACTED_FILE    = EXTRACTED_DIR / "fromfile"
    EXTRACTED_LINK    = EXTRACTED_DIR / "fromlink"

    # Generated question sets saved as question1.json, question2.json …
    QUESTIONS_DIR     = DATA_DIR / "questions"

    # Quiz attempt results saved as result1.json, result2.json …
    RESULTS_DIR       = DATA_DIR / "results"

    # Summaries saved as <name>_summarized.txt
    SUMMARIES_DIR     = DATA_DIR / "summaries"

    # Lesson teaching scripts saved as <name>_lesson.txt
    LESSONS_DIR       = DATA_DIR / "lessons"

    # Generated audio lessons saved as <name>_lesson.mp3
    AUDIO_DIR         = DATA_DIR / "audio"

    # Legacy single audio output (kept for compatibility)
    AUDIO_OUTPUT      = AUDIO_DIR / "output_audio.mp3"

    # ── AI Service ────────────────────────────────────────────────────────────
    AI_PROVIDER       = "claude"
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
