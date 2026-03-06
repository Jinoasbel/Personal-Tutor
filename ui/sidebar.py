"""
sidebar.py — Sidebar with per-item icons, Settings pinned at bottom.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget,
)

from pt_theme import Colors, Fonts, Spacing, Layout, Radius


# (panel_id, label, unicode_icon)
_NAV_ITEMS = [
    ("extracted", "EXTRACTED",     "🗂"),
    ("summarize", "SUMARIZE",      "📖"),
    ("audio",     "AUDIO",         "🎧"),
    ("ask",       "ASK QUESTIONS", "❓"),
]

_SETTINGS_ITEM = ("settings", "SETTINGS", "⚙")


class Sidebar(QWidget):
    panel_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(Layout.SIDEBAR_W_EXPANDED)
        self._expanded = True
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.SM, Spacing.MD, Spacing.SM, Spacing.MD)
        layout.setSpacing(Spacing.XS)

        # ── Hamburger ──────────────────────────────────────────────────────────
        self._hamburger = QPushButton("☰")
        self._hamburger.setFixedSize(Layout.NAV_BTN_ICON_W + 4, Layout.NAV_BTN_ICON_W + 4)
        self._hamburger.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hamburger.setStyleSheet(
            f"QPushButton {{"
            f"  background: transparent; color: {Colors.TEXT_PRIMARY};"
            f"  font-size: 20px; border: none;"
            f"  border-radius: {Radius.SM}px;"
            f"}}"
            f"QPushButton:hover {{ background: {Colors.SIDEBAR_BTN_HOVER}; }}"
        )
        self._hamburger.clicked.connect(self._on_hamburger)
        layout.addWidget(self._hamburger, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addSpacing(Spacing.MD)

        # ── Main nav ───────────────────────────────────────────────────────────
        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)
        self._nav_buttons: list[QPushButton] = []

        for panel_id, label, icon in _NAV_ITEMS:
            btn = self._make_nav_btn(label, icon)
            btn.setProperty("panel_id", panel_id)
            self._btn_group.addButton(btn)
            self._nav_buttons.append(btn)
            layout.addWidget(btn)

        # ── Spacer ─────────────────────────────────────────────────────────────
        layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # ── Settings pinned at bottom ──────────────────────────────────────────
        panel_id, label, icon = _SETTINGS_ITEM
        self._settings_btn = self._make_nav_btn(label, icon)
        self._settings_btn.setProperty("panel_id", panel_id)
        self._btn_group.addButton(self._settings_btn)
        layout.addWidget(self._settings_btn)

        # Default select first
        if self._nav_buttons:
            self._nav_buttons[0].setChecked(True)

        self._btn_group.buttonClicked.connect(self._on_nav_clicked)

    def _make_nav_btn(self, label: str, icon: str) -> QPushButton:
        """Build a nav button with icon on left and label text."""
        btn = QPushButton()
        btn.setObjectName("NavButton")
        btn.setFont(Fonts.nav_button())
        btn.setFixedHeight(Layout.NAV_BTN_H)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setProperty("icon_char", icon)
        btn.setProperty("label_text", label)
        self._apply_btn_content(btn, icon, label, expanded=True)
        return btn

    def _apply_btn_content(self, btn: QPushButton, icon: str, label: str, expanded: bool) -> None:
        if expanded:
            btn.setText(f"  {icon}    {label}")
        else:
            btn.setText(f"  {icon}")

    # ── Slots ──────────────────────────────────────────────────────────────────

    def _on_nav_clicked(self, btn: QPushButton) -> None:
        panel_id = btn.property("panel_id")
        if panel_id:
            self.panel_changed.emit(panel_id)

    def _on_hamburger(self) -> None:
        self._expanded = not self._expanded
        all_buttons = self._nav_buttons + [self._settings_btn]
        for btn in all_buttons:
            icon  = btn.property("icon_char")
            label = btn.property("label_text")
            self._apply_btn_content(btn, icon, label, self._expanded)
        w = Layout.SIDEBAR_W_EXPANDED if self._expanded else Layout.SIDEBAR_W_COLLAPSED
        self.setFixedWidth(w)

    # ── Public API ─────────────────────────────────────────────────────────────

    def select_panel(self, panel_id: str) -> None:
        for btn in self._btn_group.buttons():
            if btn.property("panel_id") == panel_id:
                btn.setChecked(True)
                break
