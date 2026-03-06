"""
app_state.py — Central application state shared across UI panels.
Single source of truth for uploaded content, extracted text, etc.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AppState:
    """
    Holds the current session's data.
    All UI panels read/write through this object.
    """
    # Input
    uploaded_files: list[Path]  = field(default_factory=list)
    pasted_links:   list[str]   = field(default_factory=list)

    # Processed outputs
    extracted_text: str  = ""
    summary_text:   str  = ""
    audio_path:     Path | None = None

    # Active view
    active_panel: str = "extracted"   # "extracted" | "summarize" | "audio" | "ask"

    def reset(self) -> None:
        """Clear all session data."""
        self.uploaded_files.clear()
        self.pasted_links.clear()
        self.extracted_text = ""
        self.summary_text = ""
        self.audio_path = None
        self.active_panel = "extracted"

    def has_content(self) -> bool:
        return bool(self.extracted_text.strip())
