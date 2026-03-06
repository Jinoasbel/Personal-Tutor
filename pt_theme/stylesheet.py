"""
stylesheet.py — Generates the global QSS stylesheet from theme tokens.
Import and call `get_stylesheet()` once at app startup.
"""

from .colors import Colors
from .dimensions import Radius, Spacing


def get_stylesheet() -> str:
    """Return the full application QSS stylesheet."""
    return f"""

    /* ── Global ───────────────────────────────────────────────────────────── */
    QWidget {{
        background-color: {Colors.BG_PRIMARY};
        color: {Colors.TEXT_PRIMARY};
        border: none;
        outline: none;
    }}

    QMainWindow {{
        background-color: {Colors.BG_PRIMARY};
    }}

    /* ── Sidebar ──────────────────────────────────────────────────────────── */
    #Sidebar {{
        background-color: {Colors.SIDEBAR_BG};
        border-right: 1px solid {Colors.BORDER_DEFAULT};
    }}

    /* ── Nav Buttons ──────────────────────────────────────────────────────── */
    QPushButton#NavButton {{
        background-color: {Colors.SIDEBAR_BTN_BG};
        color: {Colors.TEXT_PRIMARY};
        border: none;
        border-radius: {Radius.SM}px;
        padding: {Spacing.SM}px {Spacing.MD}px;
        text-align: left;
    }}
    QPushButton#NavButton:hover {{
        background-color: {Colors.SIDEBAR_BTN_HOVER};
    }}
    QPushButton#NavButton:checked {{
        background-color: {Colors.SIDEBAR_ACTIVE};
        border-left: 3px solid {Colors.ICON_ACTIVE};
    }}

    /* ── Content Area ─────────────────────────────────────────────────────── */
    #ContentArea {{
        background-color: {Colors.BG_TERTIARY};
    }}

    /* ── UPLOAD FAB ───────────────────────────────────────────────────────── */
    QPushButton#UploadFab {{
        background-color: {Colors.BTN_UPLOAD_BG};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.BTN_UPLOAD_BORDER};
        border-radius: {Radius.PILL}px;
        padding: 10px 22px;
    }}
    QPushButton#UploadFab:hover {{
        background-color: {Colors.BTN_UPLOAD_HOVER};
        border-color: {Colors.ICON_ACTIVE};
    }}

    /* ── Upload Dialog ────────────────────────────────────────────────────── */
    QDialog#UploadDialog {{
        background-color: {Colors.BG_PRIMARY};
        border: 1px solid {Colors.BORDER_DEFAULT};
        border-radius: {Radius.MD}px;
    }}

    /* ── Links Panel ──────────────────────────────────────────────────────── */
    QWidget#LinkPanel {{
        background-color: {Colors.UPLOAD_PANEL_BG};
        border-radius: {Radius.MD}px;
    }}

    /* ── Link Row ─────────────────────────────────────────────────────────── */
    QWidget#LinkRow {{
        background-color: transparent;
    }}

    QLabel#LinkIcon {{
        background-color: transparent;
        color: {Colors.ICON_DEFAULT};
    }}

    QLineEdit#LinkInput {{
        background-color: {Colors.LINK_INPUT_BG};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.BORDER_DEFAULT};
        border-radius: {Radius.SM}px;
        padding: {Spacing.SM}px {Spacing.MD}px;
        selection-background-color: {Colors.BORDER_FOCUS};
    }}
    QLineEdit#LinkInput:focus {{
        border-color: {Colors.BORDER_FOCUS};
    }}
    QLineEdit#LinkInput::placeholder {{
        color: {Colors.TEXT_PLACEHOLDER};
    }}

    /* ── Add Link Button ──────────────────────────────────────────────────── */
    QPushButton#AddLinkBtn {{
        background-color: {Colors.BTN_ADD_BG};
        color: {Colors.TEXT_PRIMARY};
        border-radius: {Radius.PILL}px;
        font-size: 18px;
        font-weight: bold;
    }}
    QPushButton#AddLinkBtn:hover {{
        background-color: {Colors.BTN_ADD_HOVER};
    }}

    /* ── Files Button ─────────────────────────────────────────────────────── */
    QPushButton#FilesBtn {{
        background-color: {Colors.BTN_PRIMARY_BG};
        color: {Colors.TEXT_PRIMARY};
        border: none;
        border-radius: {Radius.SM}px;
        padding: {Spacing.SM}px {Spacing.LG}px;
        text-align: center;
    }}
    QPushButton#FilesBtn:hover {{
        background-color: {Colors.BTN_PRIMARY_HOVER};
    }}

    /* ── Submit Button ────────────────────────────────────────────────────── */
    QPushButton#SubmitBtn {{
        background-color: {Colors.BTN_PRIMARY_BG};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.BORDER_DEFAULT};
        border-radius: {Radius.LG}px;
        padding: 10px 32px;
    }}
    QPushButton#SubmitBtn:hover {{
        background-color: {Colors.BTN_PRIMARY_HOVER};
        border-color: {Colors.ICON_ACTIVE};
    }}

    /* ── Scrollbar ────────────────────────────────────────────────────────── */
    QScrollBar:vertical {{
        background: {Colors.SCROLLBAR_BG};
        width: 6px;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical {{
        background: {Colors.SCROLLBAR_HANDLE};
        border-radius: 3px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {Colors.SCROLLBAR_HOVER};
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: {Colors.SCROLLBAR_BG};
        height: 6px;
        border-radius: 3px;
    }}
    QScrollBar::handle:horizontal {{
        background: {Colors.SCROLLBAR_HANDLE};
        border-radius: 3px;
        min-width: 30px;
    }}

    /* ── Text Areas ───────────────────────────────────────────────────────── */
    QTextEdit {{
        background-color: {Colors.SURFACE_MID};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.BORDER_DEFAULT};
        border-radius: {Radius.SM}px;
        padding: {Spacing.MD}px;
        selection-background-color: {Colors.BORDER_FOCUS};
    }}
    QTextEdit:focus {{
        border-color: {Colors.BORDER_FOCUS};
    }}

    /* ── Labels ───────────────────────────────────────────────────────────── */
    QLabel {{
        background-color: transparent;
        color: {Colors.TEXT_PRIMARY};
    }}
    QLabel#PlaceholderLabel {{
        color: {Colors.TEXT_PLACEHOLDER};
    }}

    /* ── Tooltip ──────────────────────────────────────────────────────────── */
    QToolTip {{
        background-color: {Colors.SURFACE_DARK};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.BORDER_DEFAULT};
        padding: {Spacing.XS}px {Spacing.SM}px;
        border-radius: {Radius.XS}px;
    }}
    """
