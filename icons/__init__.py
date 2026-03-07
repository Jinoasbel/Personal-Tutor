"""
icons/__init__.py — Central icon registry.

HOW TO SWAP AN ICON:
  1. Download your new icon file (SVG or PNG) into this folder
  2. Change the filename string on the relevant line below
  3. That's it — the whole app picks it up automatically

All paths are relative to this file's location (the icons/ folder).
"""

from pathlib import Path

# Root of this package
_DIR = Path(__file__).resolve().parent


def _p(filename: str) -> str:
    """Return the absolute path string for an icon file."""
    return str(_DIR / filename)


# ── Sidebar / Navigation ───────────────────────────────────────────────────────
# Change the filename string to swap the icon.

MENU        = _p("menu.svg")        # hamburger / sidebar toggle
EXTRACTED   = _p("extracted.svg")   # Extracted panel
SUMMARIZE   = _p("summarize.svg")   # Summarize panel
AUDIO       = _p("audio.svg")       # Audio panel
ASK         = _p("ask.svg")         # Ask Questions panel
SETTINGS    = _p("settings.svg")    # Settings (pinned bottom)

# ── Actions ────────────────────────────────────────────────────────────────────
UPLOAD      = _p("upload.svg")      # Upload FAB button
REFRESH     = _p("refresh.svg")     # Refresh file list
CLOSE       = _p("close.svg")       # Close / dismiss dialogs

# ── Status ─────────────────────────────────────────────────────────────────────
CHECK       = _p("check.svg")       # Success / correct answer
ERROR       = _p("error.svg")       # Failure / wrong answer
