"""
sidebar.py — Sidebar using QIcon images from the icons/ registry.

To swap any icon: open icons/__init__.py, change the filename string,
drop the new file in icons/. Done.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import (
    QButtonGroup, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget,
)

import icons
from icons.icon_loader import load_icon
from pt_theme import Colors, Fonts, Spacing, Layout, Radius


# ── Nav item definitions ───────────────────────────────────────────────────────
# (panel_id, display_label, icon_path_from_registry)
_NAV_ITEMS = [
    ("extracted", "EXTRACTED",     icons.EXTRACTED),
    ("summarize", "SUMARIZE",      icons.SUMMARIZE),
    ("audio",     "AUDIO",         icons.AUDIO),
    ("ask",       "ASK QUESTIONS", icons.ASK),
]

_SETTINGS_ITEM = ("settings", "SETTINGS", icons.SETTINGS)

# Icon render size (px)
_ICON_SIZE = 20


class Sidebar(QWidget):
    panel_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(Layout.SIDEBAR_W_EXPANDED)
        self._expanded = True
        self._build_ui()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.SM, Spacing.MD, Spacing.SM, Spacing.MD)
        layout.setSpacing(Spacing.XS)

        # ── Hamburger ──────────────────────────────────────────────────────────
        self._hamburger = QPushButton()
        self._hamburger.setIcon(load_icon(icons.MENU, _ICON_SIZE))
        self._hamburger.setIconSize(QSize(_ICON_SIZE, _ICON_SIZE))
        self._hamburger.setFixedSize(Layout.NAV_BTN_ICON_W + 4, Layout.NAV_BTN_ICON_W + 4)
        self._hamburger.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hamburger.setToolTip("Toggle sidebar")
        self._hamburger.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: {Radius.SM}px;
            }}
            QPushButton:hover {{ background: {Colors.SIDEBAR_BTN_HOVER}; }}
        """)
        self._hamburger.clicked.connect(self._on_hamburger)
        layout.addWidget(self._hamburger, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addSpacing(Spacing.MD)

        # ── Main nav buttons ───────────────────────────────────────────────────
        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)
        self._nav_buttons: list[QPushButton] = []

        for panel_id, label, icon_path in _NAV_ITEMS:
            btn = self._make_nav_btn(label, icon_path)
            btn.setProperty("panel_id", panel_id)
            btn.setProperty("label_text", label)
            btn.setProperty("icon_path", icon_path)
            self._btn_group.addButton(btn)
            self._nav_buttons.append(btn)
            layout.addWidget(btn)

        # ── Spacer ─────────────────────────────────────────────────────────────
        layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # ── Settings pinned at bottom ──────────────────────────────────────────
        s_id, s_label, s_icon = _SETTINGS_ITEM
        self._settings_btn = self._make_nav_btn(s_label, s_icon)
        self._settings_btn.setProperty("panel_id",   s_id)
        self._settings_btn.setProperty("label_text", s_label)
        self._settings_btn.setProperty("icon_path",  s_icon)
        self._btn_group.addButton(self._settings_btn)
        layout.addWidget(self._settings_btn)

        # Default: select first nav button
        if self._nav_buttons:
            self._nav_buttons[0].setChecked(True)

        self._btn_group.buttonClicked.connect(self._on_nav_clicked)

    def _make_nav_btn(self, label: str, icon_path: str) -> QPushButton:
        btn = QPushButton(f"  {label}")
        btn.setObjectName("NavButton")
        btn.setFont(Fonts.nav_button())
        btn.setFixedHeight(Layout.NAV_BTN_H)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setCheckable(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setIcon(load_icon(icon_path, _ICON_SIZE))
        btn.setIconSize(QSize(_ICON_SIZE, _ICON_SIZE))
        return btn

    # ── Slots ──────────────────────────────────────────────────────────────────

    def _on_nav_clicked(self, btn: QPushButton) -> None:
        panel_id = btn.property("panel_id")
        if panel_id:
            self.panel_changed.emit(panel_id)

    def _on_hamburger(self) -> None:
        self._expanded = not self._expanded
        all_btns = self._nav_buttons + [self._settings_btn]

        if self._expanded:
            self.setFixedWidth(Layout.SIDEBAR_W_EXPANDED)
            for btn in all_btns:
                label = btn.property("label_text")
                btn.setText(f"  {label}")
        else:
            self.setFixedWidth(Layout.SIDEBAR_W_COLLAPSED)
            for btn in all_btns:
                btn.setText("")   # icon-only; QIcon still shows

    # ── Public API ─────────────────────────────────────────────────────────────

    def select_panel(self, panel_id: str) -> None:
        for btn in self._btn_group.buttons():
            if btn.property("panel_id") == panel_id:
                btn.setChecked(True)
                break
