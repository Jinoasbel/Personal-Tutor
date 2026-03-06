"""
link_row.py — A single link-input row in the Upload dialog.
Contains a chain-link icon and a text input field.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QWidget

from pt_theme import Colors, Fonts, Strings, Spacing, Layout


class LinkRow(QWidget):
    """One row with a link icon + input field."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("LinkRow")
        self.setFixedHeight(Layout.LINK_ROW_H)
        self._build_ui()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(Spacing.SM, Spacing.XS, Spacing.SM, Spacing.XS)
        layout.setSpacing(Spacing.SM)

        # Chain-link icon (unicode character as label)
        icon = QLabel("🔗")
        icon.setObjectName("LinkIcon")
        icon.setFixedSize(Layout.LINK_ICON_W, Layout.LINK_ROW_H - Spacing.XS * 2)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(f"font-size: 18px; color: {Colors.ICON_DEFAULT};")

        # Input field
        self._input = QLineEdit()
        self._input.setObjectName("LinkInput")
        self._input.setPlaceholderText(Strings.LINK_PLACEHOLDER)
        self._input.setFont(Fonts.body())
        self._input.setFixedHeight(Layout.LINK_ROW_H - Spacing.XS * 2)

        layout.addWidget(icon)
        layout.addWidget(self._input)

    # ── Public API ─────────────────────────────────────────────────────────────

    def get_text(self) -> str:
        return self._input.text().strip()

    def clear(self) -> None:
        self._input.clear()
