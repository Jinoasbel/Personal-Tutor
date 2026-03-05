"""
app_config.py
-------------
Central configuration for ALL UI constants, labels, colors, fonts,
dimensions, and stylesheet templates.

Nothing in the rest of the app hardcodes any of these values.
"""

from PySide6.QtGui import QFont


# ── Window ────────────────────────────────────────────────────────────────────

WINDOW_TITLE  = "Personal Tutor"
WINDOW_WIDTH  = 1000
WINDOW_HEIGHT = 650


# ── Navigation labels + page keys ────────────────────────────────────────────
# PAGE_KEY is used internally to identify which page to show.
# The sidebar builds its buttons from NAV_ITEMS.

PAGE_UPLOAD       = "upload"
PAGE_STUDY_PLANS  = "study_plans"
PAGE_LESSONS      = "lessons"
PAGE_QUESTIONS    = "questions"

NAV_ITEMS = [
    ("〉   STUDY PLANS", PAGE_STUDY_PLANS),
    ("〉   LESSONS",     PAGE_LESSONS),
    ("〉   QUESTIONS",   PAGE_QUESTIONS),
]

LABEL_UPLOAD     = "＋   UPLOAD"
LABEL_HAMBURGER  = "≡"


# ── Page display titles ────────────────────────────────────────────────────────

PAGE_TITLES = {
    PAGE_UPLOAD:      "Document Upload",
    PAGE_STUDY_PLANS: "Study Plans",
    PAGE_LESSONS:     "Lessons",
    PAGE_QUESTIONS:   "Questions",
}


# ── Status messages (upload/OCR page) ─────────────────────────────────────────

STATUS_READY        = "Ready. Upload a document to extract text."
STATUS_EXTRACTING   = "Extracting text..."
STATUS_SUCCESS      = "Extraction complete."
STATUS_INIT         = "Initializing..."
STATUS_ERROR_PREFIX = "Error: "
UPLOAD_PROMPT_TEXT  = "Drop a file here or click  + UPLOAD"
UPLOAD_HINT_TEXT    = "Supported formats: PNG, JPG, JPEG, PDF"


# ── Study Plans page ──────────────────────────────────────────────────────────

STUDY_PLANS_EMPTY            = "No study plans yet.\nCreate one to get started."
STUDY_PLANS_ADD_BTN          = "+  New Study Plan"
STUDY_PLAN_INPUT_PLACEHOLDER = "Enter study plan title..."
STUDY_PLAN_DELETE_BTN        = "Delete"
STUDY_PLAN_OPEN_BTN          = "Open"


# ── Lessons page ──────────────────────────────────────────────────────────────

LESSONS_EMPTY   = "No lessons yet.\nUpload a document first to generate a lesson."
LESSONS_ADD_BTN = "+  New Lesson"
LESSON_INPUT_PLACEHOLDER = "Enter lesson title..."


# ── Questions page ────────────────────────────────────────────────────────────

QUESTIONS_EMPTY              = "No questions yet.\nAdd a question or generate from a lesson."
QUESTIONS_ADD_BTN            = "+  New Question"
QUESTIONS_INPUT_PLACEHOLDER  = "Type your question here..."
QUESTIONS_SUBMIT_BTN         = "Ask"
QUESTIONS_ANSWER_PREFIX      = "Answer: "
QUESTIONS_THINKING           = "Thinking..."


# ── File dialog ───────────────────────────────────────────────────────────────

DIALOG_TITLE  = "Select a Document"
DIALOG_FILTER = "Documents (*.png *.jpg *.jpeg *.pdf)"


# ── Colors ────────────────────────────────────────────────────────────────────

COLOR_PRIMARY_BG      = "#3a4645"
COLOR_SECONDARY_BG    = "#8e8e8e"
COLOR_ACCENT_MAIN     = "#4a5351"
COLOR_ACCENT_HOVER    = "#5c6664"
COLOR_ACCENT_ACTIVE   = "#6a7f7c"
COLOR_TEXT_MAIN       = "#ffffff"
COLOR_TEXT_MUTED      = "#333333"
COLOR_TEXT_SUBTLE     = "#aaaaaa"
COLOR_STATUS_WAIT     = "#f0c040"
COLOR_STATUS_OK       = "#4caf50"
COLOR_STATUS_ERROR    = "#ff4c4c"
COLOR_TEXTBOX_BG      = "#2b3332"
COLOR_CARD_BG         = "#344140"
COLOR_CARD_HOVER      = "#3e4e4c"
COLOR_DIVIDER         = "#4a5a58"
COLOR_HAMBURGER_HOVER = "#9e9e9e"
COLOR_INPUT_BG        = "#2b3332"
COLOR_INPUT_BORDER    = "#4a5a58"


# ── Fonts ─────────────────────────────────────────────────────────────────────

_FONT_FAMILY = "Segoe UI"

FONT_HEADING    = QFont(_FONT_FAMILY, 20, QFont.Bold)
FONT_SUBHEADING = QFont(_FONT_FAMILY, 14, QFont.Bold)
FONT_BUTTON     = QFont(_FONT_FAMILY, 11, QFont.Bold)
FONT_BODY       = QFont(_FONT_FAMILY, 13)
FONT_BODY_SMALL = QFont(_FONT_FAMILY, 11)
FONT_STATUS     = QFont(_FONT_FAMILY, 12)
FONT_HINT       = QFont(_FONT_FAMILY, 10)
FONT_HAMBURGER  = QFont(_FONT_FAMILY, 24, QFont.Bold)


# ── Base font sizes (for responsive scaling) ──────────────────────────────────

BASE_FONT_HEADING  = 20
BASE_FONT_BUTTON   = 11
BASE_FONT_BODY     = 13
BASE_FONT_STATUS   = 12
BASE_FONT_MIN      = 9
BASE_WIN_W         = 1000
BASE_WIN_H         = 650


# ── Dimensions ────────────────────────────────────────────────────────────────

SIDEBAR_FRACTION     = 0.25
SIDEBAR_CLOSED_W     = 60
NAV_BUTTON_HEIGHT    = 45
UPLOAD_BUTTON_HEIGHT = 45
HAMBURGER_BTN_SIZE   = 44
HAMBURGER_OFFSET_X   = 8
HAMBURGER_OFFSET_Y   = 8
TEXTBOX_PADDING      = 20
STATUS_TOP_PADDING   = 16
PAGE_PADDING         = 24
CARD_HEIGHT          = 56
CARD_RADIUS          = 8
INPUT_HEIGHT         = 40
ADD_BTN_HEIGHT       = 40


# ── Stylesheet templates ──────────────────────────────────────────────────────

def sidebar_style(bg: str) -> str:
    return f"background-color: {bg}; border: none;"

def nav_button_style(bg: str, hover: str, text: str) -> str:
    return (
        f"QPushButton {{ background-color: {bg}; color: {text};"
        f"  border: none; text-align: left; padding-left: 14px; }}"
        f"QPushButton:hover {{ background-color: {hover}; }}"
    )

def nav_button_active_style(bg: str, text: str) -> str:
    return (
        f"QPushButton {{ background-color: {bg}; color: {text};"
        f"  border: none; text-align: left; padding-left: 14px;"
        f"  border-left: 3px solid {COLOR_STATUS_OK}; }}"
    )

def upload_button_style(bg: str, hover: str, text: str) -> str:
    return (
        f"QPushButton {{ background-color: {bg}; color: {text};"
        f"  border: none; text-align: left; padding-left: 14px;"
        f"  border-radius: 6px; }}"
        f"QPushButton:hover {{ background-color: {hover}; }}"
        f"QPushButton:disabled {{ color: #666666; }}"
    )

def action_button_style(bg: str, hover: str, text: str) -> str:
    return (
        f"QPushButton {{ background-color: {bg}; color: {text};"
        f"  border: none; border-radius: 6px; padding: 0 16px; }}"
        f"QPushButton:hover {{ background-color: {hover}; }}"
        f"QPushButton:disabled {{ color: #666666; }}"
    )

def hamburger_style(hover: str) -> str:
    return (
        f"QPushButton {{ background-color: transparent; border: none;"
        f"  color: {COLOR_TEXT_MUTED}; }}"
        f"QPushButton:hover {{ background-color: {hover}; border-radius: 6px; }}"
    )

def main_frame_style(bg: str) -> str:
    return f"background-color: {bg}; border: none;"

def textbox_style(bg: str, text: str) -> str:
    return (
        f"QPlainTextEdit {{ background-color: {bg}; color: {text};"
        f"  border: none; border-radius: 8px; padding: 10px; }}"
    )

def card_style(bg: str, radius: int) -> str:
    return f"QFrame {{ background-color: {bg}; border-radius: {radius}px; border: none; }}"

def input_style(bg: str, text: str, border: str) -> str:
    return (
        f"QLineEdit {{ background-color: {bg}; color: {text};"
        f"  border: 1px solid {border}; border-radius: 6px; padding: 0 10px; }}"
        f"QLineEdit:focus {{ border: 1px solid {COLOR_STATUS_OK}; }}"
    )

def label_style(color: str) -> str:
    return f"color: {color}; background: transparent;"

def page_style(bg: str) -> str:
    return f"background-color: {bg}; border: none;"

def scroll_area_style(bg: str) -> str:
    return (
        f"QScrollArea {{ background-color: {bg}; border: none; }}"
        f"QWidget {{ background-color: {bg}; }}"
        f"QScrollBar:vertical {{ background: {bg}; width: 6px; border: none; }}"
        f"QScrollBar::handle:vertical {{ background: {COLOR_DIVIDER}; border-radius: 3px; }}"
        f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}"
    )

def textedit_style(bg: str, text: str) -> str:
    return (
        f"QTextEdit {{ background-color: {bg}; color: {text};"
        f"  border: none; border-radius: 8px; padding: 10px; }}"
    )
