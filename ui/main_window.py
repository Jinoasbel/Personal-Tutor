"""
ui/main_window.py
-----------------
Root application window.

Responsibilities:
    - Hosts the sidebar + a QStackedWidget of pages.
    - Owns the floating hamburger overlay.
    - Owns the shared app_state dict passed to all pages.
    - Owns the OCREngine instance (stored in app_state).
    - Routes navigation signals from the sidebar to page switches.
    - Handles responsive resize (sidebar width + font scaling).

It does NOT contain any page-specific logic — that lives in each page.
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout,
    QPushButton, QStackedWidget, QFileDialog
)
from PySide6.QtCore import Qt, QSize, QRect
from PySide6.QtGui import QFont, QResizeEvent

import app_config as cfg
from ocr_engine import OCREngine
from ui.sidebar import SidebarWidget
from ui.pages.upload_page      import UploadPage
from ui.pages.study_plans_page import StudyPlansPage
from ui.pages.lessons_page     import LessonsPage
from ui.pages.questions_page   import QuestionsPage


class TutorApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle(cfg.WINDOW_TITLE)
        self.resize(cfg.WINDOW_WIDTH, cfg.WINDOW_HEIGHT)

        # ── Shared state passed to every page ─────────────────────────────────
        self._app_state: dict = {
            "ocr_engine":           OCREngine(),
            "last_extracted_text":  "",
            "study_plans":          [],
            "lessons":              [],
            "questions":            [],
            "active_study_plan":    None,
        }

        # ── Central widget ────────────────────────────────────────────────────
        self._central = QWidget()
        self._central.setStyleSheet(cfg.main_frame_style(cfg.COLOR_PRIMARY_BG))
        self.setCentralWidget(self._central)

        root = QHBoxLayout(self._central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ───────────────────────────────────────────────────────────
        self._sidebar = SidebarWidget(parent=self._central)
        self._sidebar.setFixedWidth(int(cfg.WINDOW_WIDTH * cfg.SIDEBAR_FRACTION))
        self._sidebar.navigateTo.connect(self._navigate_to)
        self._sidebar.uploadRequested.connect(self._on_upload_requested)
        root.addWidget(self._sidebar)

        # ── Page stack ────────────────────────────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(cfg.page_style(cfg.COLOR_PRIMARY_BG))
        root.addWidget(self._stack, stretch=1)

        # Build all pages and register them
        self._pages: dict[str, object] = {}
        self._register_page(cfg.PAGE_UPLOAD,      UploadPage(self._app_state))
        self._register_page(cfg.PAGE_STUDY_PLANS, StudyPlansPage(self._app_state))
        self._register_page(cfg.PAGE_LESSONS,     LessonsPage(self._app_state))
        self._register_page(cfg.PAGE_QUESTIONS,   QuestionsPage(self._app_state))

        # ── Floating hamburger ────────────────────────────────────────────────
        self._hamburger = QPushButton(cfg.LABEL_HAMBURGER, self._central)
        self._hamburger.setFixedSize(QSize(cfg.HAMBURGER_BTN_SIZE, cfg.HAMBURGER_BTN_SIZE))
        self._hamburger.setFont(cfg.FONT_HAMBURGER)
        self._hamburger.setStyleSheet(cfg.hamburger_style(cfg.COLOR_HAMBURGER_HOVER))
        self._hamburger.setCursor(Qt.PointingHandCursor)
        self._hamburger.clicked.connect(self._toggle_sidebar)
        self._place_hamburger()

        # Start on upload page
        self._navigate_to(cfg.PAGE_UPLOAD)

    # ── Page registration ─────────────────────────────────────────────────────

    def _register_page(self, key: str, page: QWidget):
        self._pages[key] = page
        self._stack.addWidget(page)

    # ── Navigation ────────────────────────────────────────────────────────────

    def _navigate_to(self, page_key: str):
        page = self._pages.get(page_key)
        if page is None:
            return
        self._stack.setCurrentWidget(page)
        page.on_enter()
        self._sidebar.set_active(page_key)

    # ── Upload shortcut ───────────────────────────────────────────────────────

    def _on_upload_requested(self):
        """Sidebar upload button — open dialog and navigate to upload page."""
        path, _ = QFileDialog.getOpenFileName(
            self, cfg.DIALOG_TITLE, "", cfg.DIALOG_FILTER
        )
        if path:
            self._navigate_to(cfg.PAGE_UPLOAD)
            upload_page: UploadPage = self._pages[cfg.PAGE_UPLOAD]
            upload_page._start_ocr(path)

    # ── Hamburger ─────────────────────────────────────────────────────────────

    def _place_hamburger(self):
        self._hamburger.setGeometry(QRect(
            cfg.HAMBURGER_OFFSET_X,
            cfg.HAMBURGER_OFFSET_Y,
            cfg.HAMBURGER_BTN_SIZE,
            cfg.HAMBURGER_BTN_SIZE
        ))
        self._hamburger.raise_()

    def _toggle_sidebar(self):
        if self._sidebar.expanded:
            self._sidebar.collapse()
        else:
            self._sidebar.expand(self.width())
        self._place_hamburger()

    # ── Resize ────────────────────────────────────────────────────────────────

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        win_w, win_h = self.width(), self.height()

        if self._sidebar.expanded:
            self._sidebar.setFixedWidth(int(win_w * cfg.SIDEBAR_FRACTION))

        scale = max(0.6, min(min(win_w / cfg.BASE_WIN_W, win_h / cfg.BASE_WIN_H), 2.0))
        self._sidebar.apply_font_scale(scale)

        ham_size = max(cfg.BASE_FONT_MIN, int(cfg.BASE_FONT_HEADING * scale))
        self._hamburger.setFont(QFont(cfg.FONT_HAMBURGER.family(), ham_size, QFont.Bold))
        self._place_hamburger()
