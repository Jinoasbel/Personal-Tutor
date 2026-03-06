"""
sidebar.py — Collapsible sidebar with hamburger toggle and navigation buttons.
Matches the Main_UI.pdf design: hamburger top-left, nav buttons stacked below.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget,
)

from pt_theme import Colors, Fonts, Strings, Spacing, Layout, Radius


_NAV_ITEMS = [
    ("extracted", Strings.NAV_EXTRACTED, "›", Strings.TIP_EXTRACTED),
    ("summarize", Strings.NAV_SUMMARIZE, "›", Strings.TIP_SUMMARIZE),
    ("audio",     Strings.NAV_AUDIO,     "›", Strings.TIP_AUDIO),
    ("ask",       Strings.NAV_ASK,       "›", Strings.TIP_ASK),
]


class Sidebar(QWidget):
    """
    Left navigation sidebar.

    Signals:
        panel_changed(str panel_id)
    """

    panel_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(Layout.SIDEBAR_W_EXPANDED)
        self._build_ui()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.SM, Spacing.MD, Spacing.SM, Spacing.MD)
        layout.setSpacing(Spacing.XS)

        # Hamburger menu button
        self._hamburger = QPushButton("☰")
        self._hamburger.setFixedSize(Layout.NAV_BTN_ICON_W + 4, Layout.NAV_BTN_ICON_W + 4)
        self._hamburger.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hamburger.setStyleSheet(
            f"QPushButton {{"
            f"  background: transparent;"
            f"  color: {Colors.TEXT_PRIMARY};"
            f"  font-size: 20px;"
            f"  border: none;"
            f"  border-radius: {Radius.SM}px;"
            f"}}"
            f"QPushButton:hover {{ background: {Colors.SIDEBAR_BTN_HOVER}; }}"
        )
        self._hamburger.clicked.connect(self._on_hamburger)

        layout.addWidget(self._hamburger, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addSpacing(Spacing.MD)

        # Navigation buttons
        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)

        for panel_id, label, arrow, tip in _NAV_ITEMS:
            btn = self._make_nav_btn(label, arrow, tip)
            btn.setProperty("panel_id", panel_id)
            self._btn_group.addButton(btn)
            layout.addWidget(btn)

        layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # Select first button by default
        buttons = self._btn_group.buttons()
        if buttons:
            buttons[0].setChecked(True)

        self._btn_group.buttonClicked.connect(self._on_nav_clicked)

    def _make_nav_btn(self, label: str, arrow: str, tip: str) -> QPushButton:
        btn = QPushButton(f"  {arrow}   {label}")
        btn.setObjectName("NavButton")
        btn.setFont(Fonts.nav_button())
        btn.setFixedHeight(Layout.NAV_BTN_H)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(tip)
        return btn

    # ── Slots ──────────────────────────────────────────────────────────────────

    def _on_nav_clicked(self, btn: QPushButton) -> None:
        panel_id = btn.property("panel_id")
        if panel_id:
            self.panel_changed.emit(panel_id)

    def _on_hamburger(self) -> None:
        """Toggle sidebar width (collapse/expand)."""
        if self.width() == Layout.SIDEBAR_W_EXPANDED:
            self.setFixedWidth(Layout.SIDEBAR_W_COLLAPSED)
            for btn in self._btn_group.buttons():
                btn.setText("›")
        else:
            self.setFixedWidth(Layout.SIDEBAR_W_EXPANDED)
            for btn, (_, label, arrow, _tip) in zip(
                self._btn_group.buttons(), _NAV_ITEMS
            ):
                btn.setText(f"  {arrow}   {label}")

    # ── Public API ─────────────────────────────────────────────────────────────

    def select_panel(self, panel_id: str) -> None:
        """Programmatically select a nav item."""
        for btn in self._btn_group.buttons():
            if btn.property("panel_id") == panel_id:
                btn.setChecked(True)
                break
