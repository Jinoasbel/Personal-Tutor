"""
ui/sidebar.py
-------------
Collapsible sidebar with navigation buttons and an upload shortcut.

The hamburger button is NOT here — it lives as a floating overlay on
TutorApp (main_window.py) so it remains visible when sidebar collapses.

Emits:
    navigateTo(page_key: str)  — when a nav button is clicked
    uploadRequested()          — when the Upload button is clicked
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

import app_config as cfg


class SidebarWidget(QWidget):

    navigateTo      = Signal(str)   # page_key
    uploadRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.expanded = True
        self._nav_buttons: dict[str, QPushButton] = {}   # page_key → button
        self._active_key: str = cfg.PAGE_UPLOAD

        self.setStyleSheet(cfg.sidebar_style(cfg.COLOR_SECONDARY_BG))
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Space reserved for the floating hamburger button
        root.addSpacing(cfg.HAMBURGER_BTN_SIZE + 16)

        # ── Nav items ────────────────────────────────────────────────────────
        self._nav_container = QWidget()
        self._nav_container.setStyleSheet("background: transparent;")
        nav_layout = QVBoxLayout(self._nav_container)
        nav_layout.setContentsMargins(10, 0, 10, 0)
        nav_layout.setSpacing(5)

        for label, page_key in cfg.NAV_ITEMS:
            btn = self._make_nav_button(label, page_key)
            nav_layout.addWidget(btn)
            self._nav_buttons[page_key] = btn

        nav_layout.addStretch()
        root.addWidget(self._nav_container, stretch=1)

        # ── Upload button ────────────────────────────────────────────────────
        self._upload_btn = QPushButton(cfg.LABEL_UPLOAD)
        self._upload_btn.setFixedHeight(cfg.UPLOAD_BUTTON_HEIGHT)
        self._upload_btn.setFont(cfg.FONT_BUTTON)
        self._upload_btn.setStyleSheet(
            cfg.upload_button_style(cfg.COLOR_ACCENT_MAIN, cfg.COLOR_ACCENT_HOVER, cfg.COLOR_TEXT_MAIN)
        )
        self._upload_btn.setCursor(Qt.PointingHandCursor)
        self._upload_btn.clicked.connect(self.uploadRequested)

        upload_row = QHBoxLayout()
        upload_row.setContentsMargins(10, 0, 10, 16)
        upload_row.addWidget(self._upload_btn)
        root.addLayout(upload_row)

    # ── Factory ───────────────────────────────────────────────────────────────

    def _make_nav_button(self, label: str, page_key: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setFixedHeight(cfg.NAV_BUTTON_HEIGHT)
        btn.setFont(cfg.FONT_BUTTON)
        btn.setStyleSheet(
            cfg.nav_button_style(cfg.COLOR_ACCENT_MAIN, cfg.COLOR_ACCENT_HOVER, cfg.COLOR_TEXT_MAIN)
        )
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda checked=False, k=page_key: self._on_nav_clicked(k))
        return btn

    # ── Public API ────────────────────────────────────────────────────────────

    def set_active(self, page_key: str):
        """Highlight the active nav button; reset the previous one."""
        prev = self._nav_buttons.get(self._active_key)
        if prev:
            prev.setStyleSheet(
                cfg.nav_button_style(cfg.COLOR_ACCENT_MAIN, cfg.COLOR_ACCENT_HOVER, cfg.COLOR_TEXT_MAIN)
            )
        self._active_key = page_key
        curr = self._nav_buttons.get(page_key)
        if curr:
            curr.setStyleSheet(
                cfg.nav_button_active_style(cfg.COLOR_ACCENT_ACTIVE, cfg.COLOR_TEXT_MAIN)
            )

    def collapse(self):
        self._nav_container.setVisible(False)
        self._upload_btn.setVisible(False)
        self.setFixedWidth(cfg.SIDEBAR_CLOSED_W)
        self.expanded = False

    def expand(self, parent_width: int):
        self.setFixedWidth(int(parent_width * cfg.SIDEBAR_FRACTION))
        self._nav_container.setVisible(True)
        self._upload_btn.setVisible(True)
        self.expanded = True

    def set_upload_enabled(self, enabled: bool):
        self._upload_btn.setEnabled(enabled)

    def apply_font_scale(self, scale: float):
        def s(base: int) -> int:
            return max(cfg.BASE_FONT_MIN, int(base * scale))

        f = QFont(cfg.FONT_BUTTON.family(), s(cfg.BASE_FONT_BUTTON), QFont.Bold)
        for btn in self._nav_buttons.values():
            btn.setFont(f)
        self._upload_btn.setFont(f)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _on_nav_clicked(self, page_key: str):
        self.set_active(page_key)
        self.navigateTo.emit(page_key)
