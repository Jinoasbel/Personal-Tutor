"""
text_store.py
-------------
Handles all persistence of extracted OCR text to a local .txt file.

Rules:
    - First extraction → creates the file and writes the content.
    - Every subsequent extraction → APPENDS to the same file with a
      separator so entries are clearly distinguished.
    - The store file location is defined in app_config (EXTRACTED_TEXT_FILE).
    - This module has zero GUI imports — purely I/O logic.

Usage:
    from text_store import TextStore
    store = TextStore()
    store.append(source_name="invoice.pdf", text="--- PAGE 1 ---\n...")
    all_text = store.read_all()
    store.clear()
"""

import os
from datetime import datetime
import app_config as cfg


class TextStore:
    """
    Append-only store for OCR-extracted text backed by a local .txt file.
    """

    def __init__(self):
        self._path = cfg.EXTRACTED_TEXT_FILE
        # Ensure the parent directory exists
        parent = os.path.dirname(self._path)
        if parent:
            os.makedirs(parent, exist_ok=True)

    # ── Public API ────────────────────────────────────────────────────────────

    def append(self, source_name: str, text: str) -> None:
        """
        Append one extraction result to the store file.
        Creates the file if it does not exist yet.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        separator = cfg.TEXT_STORE_SEPARATOR
        block = (
            f"{separator}\n"
            f"SOURCE : {source_name}\n"
            f"TIME   : {timestamp}\n"
            f"{separator}\n"
            f"{text.strip()}\n\n"
        )
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(block)

    def read_all(self) -> str:
        """Return the full contents of the store file, or empty string."""
        if not os.path.exists(self._path):
            return ""
        with open(self._path, "r", encoding="utf-8") as f:
            return f.read()

    def clear(self) -> None:
        """Wipe the store file (creates a blank file)."""
        with open(self._path, "w", encoding="utf-8") as f:
            f.write("")

    def file_path(self) -> str:
        return self._path

    def exists(self) -> bool:
        return os.path.exists(self._path)
