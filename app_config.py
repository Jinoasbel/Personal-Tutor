"""
app_config.py — Application-level configuration constants.
Non-UI settings such as paths, OCR options, feature flags.
"""

from pathlib import Path


class Config:
    # ── Paths ─────────────────────────────────────────────────────────────────
    DATA_DIR          = Path("Data")
    AUDIO_OUTPUT      = DATA_DIR / "output_audio.mp3"
    TEMP_DIR          = DATA_DIR / "temp"

    # Extracted text is saved here, organised by source:
    #   Data/extracted/fromfile/<original_filename>.txt
    #   Data/extracted/fromlink/<sanitised_link_name>.txt
    EXTRACTED_DIR     = DATA_DIR / "extracted"
    EXTRACTED_FILE    = EXTRACTED_DIR / "fromfile"
    EXTRACTED_LINK    = EXTRACTED_DIR / "fromlink"

    # ── OCR ───────────────────────────────────────────────────────────────────
    OCR_LANG          = "en"

    # ── Features (toggle on/off) ──────────────────────────────────────────────
    FEATURE_AUDIO     = True
    FEATURE_QA        = True
    FEATURE_LINKS     = True

    # ── Appearance ────────────────────────────────────────────────────────────
    HIGH_DPI          = True
