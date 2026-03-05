"""
ui/pages/base_page.py
---------------------
Abstract base class every page must inherit.

Contract:
    - Receives page_key (str) and an optional shared app_state dict.
    - Must implement on_enter() called when the page becomes visible.
    - May implement on_leave() called when navigating away.
    - Has a standard page_title label at the top.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

import app_config as cfg


class BasePage(QWidget):
    """
    Standard page shell:
        ┌──────────────────────────────┐
        │  Page Title                  │  ← FONT_HEADING, always present
        ├──────────────────────────────┤
        │  (subclass fills this area)  │
        └──────────────────────────────┘

    Subclasses call super().__init__() then add their widgets to
    self.content_layout.
    """

    def __init__(self, page_key: str, app_state: dict, parent=None):
        super().__init__(parent)
        self.page_key  = page_key
        self.app_state = app_state          # Shared mutable state across pages

        self.setStyleSheet(cfg.page_style(cfg.COLOR_PRIMARY_BG))

        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(
            cfg.PAGE_PADDING, cfg.PAGE_PADDING,
            cfg.PAGE_PADDING, cfg.PAGE_PADDING
        )
        self._outer.setSpacing(12)

        # ── Page title ───────────────────────────────────────────────────────
        title_text = cfg.PAGE_TITLES.get(page_key, page_key.replace("_", " ").title())
        self._title_label = QLabel(title_text)
        self._title_label.setFont(cfg.FONT_HEADING)
        self._title_label.setStyleSheet(cfg.label_style(cfg.COLOR_TEXT_MAIN))
        self._title_label.setAlignment(Qt.AlignLeft)
        self._outer.addWidget(self._title_label)

        # ── Content area subclasses populate ─────────────────────────────────
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(10)
        self._outer.addLayout(self.content_layout, stretch=1)

    # ── Lifecycle hooks ───────────────────────────────────────────────────────

    def on_enter(self) -> None:
        """Called every time this page is navigated to. Override as needed."""

    def on_leave(self) -> None:
        """Called every time the user navigates away. Override as needed."""
