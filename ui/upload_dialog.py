"""
upload_dialog.py — Upload dialog.

Changes:
  - X close button in top-right corner (also Escape key closes)
  - Rounded corners, draggable frameless window
  - Link rows: pasting a URL triggers AI to fetch + transcribe/describe content
    (YouTube, articles, any URL) and saves to Data/extracted/fromlink/
"""

from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtWidgets import (
    QDialog, QFileDialog, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QSizePolicy,
    QVBoxLayout, QWidget,
)

from pt_theme import Colors, Fonts, Strings, Spacing, Radius, Layout
from .link_row import LinkRow


class UploadDialog(QDialog):
    """
    Modal dialog for uploading links and files.

    Signals:
        submitted(list[str] links, list[Path] files)
    """

    submitted = Signal(list, list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("UploadDialog")
        self.setWindowTitle(Strings.UPLOAD_TITLE)
        self.setModal(True)
        self.setFixedSize(Layout.DIALOG_W, Layout.DIALOG_H)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint
        )
        # For dragging the frameless window
        self._drag_pos: QPoint | None = None

        self._selected_files: list[Path] = []
        self._link_rows: list[LinkRow]   = []

        self._build_ui()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.XL)
        root.setSpacing(Spacing.LG)

        # ── Top bar: title + close button ──────────────────────────────────────
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)

        dialog_title = QLabel(Strings.UPLOAD_TITLE)
        dialog_title.setFont(Fonts.heading())
        dialog_title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setToolTip("Close")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Colors.TEXT_SECONDARY};
                border: none;
                border-radius: 16px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {Colors.ERROR};
                color: #ffffff;
            }}
        """)
        close_btn.clicked.connect(self.reject)

        top_bar.addWidget(dialog_title)
        top_bar.addStretch()
        top_bar.addWidget(close_btn)
        root.addLayout(top_bar)

        # ── Links panel ────────────────────────────────────────────────────────
        links_panel = QWidget()
        links_panel.setObjectName("LinkPanel")
        links_panel.setStyleSheet(
            f"QWidget#LinkPanel {{"
            f"  background-color: {Colors.UPLOAD_PANEL_BG};"
            f"  border-radius: {Radius.MD}px;"
            f"}}"
        )
        links_layout = QVBoxLayout(links_panel)
        links_layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        links_layout.setSpacing(Spacing.XS)

        # Scrollable link rows
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll_area.setMaximumHeight(Layout.LINKS_AREA_MAX_H)
        self._scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._links_container = QWidget()
        self._links_container.setStyleSheet("background: transparent;")
        self._links_vbox = QVBoxLayout(self._links_container)
        self._links_vbox.setContentsMargins(0, 0, 0, 0)
        self._links_vbox.setSpacing(Spacing.XS)
        self._links_vbox.addStretch()
        self._scroll_area.setWidget(self._links_container)

        self._add_link_row()
        self._add_link_row()

        add_btn = QPushButton(Strings.ADD_LINK_SYMBOL)
        add_btn.setObjectName("AddLinkBtn")
        add_btn.setFixedSize(Layout.ADD_BTN_SIZE, Layout.ADD_BTN_SIZE)
        add_btn.setFont(Fonts.heading())
        add_btn.setToolTip(Strings.TIP_ADD_LINK)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_link_row)

        add_row = QHBoxLayout()
        add_row.addStretch()
        add_row.addWidget(add_btn)
        add_row.addStretch()

        links_layout.addWidget(self._scroll_area)
        links_layout.addLayout(add_row)

        # ── Files row ──────────────────────────────────────────────────────────
        files_row = QHBoxLayout()
        files_row.setSpacing(Spacing.MD)

        folder_icon = QLabel("📁")
        folder_icon.setFixedSize(Layout.LINK_ICON_W, Layout.FILES_BTN_H)
        folder_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        folder_icon.setStyleSheet("font-size: 24px;")

        self._files_btn = QPushButton(Strings.UPLOAD_FILES_BTN)
        self._files_btn.setObjectName("FilesBtn")
        self._files_btn.setFont(Fonts.upload_button())
        self._files_btn.setFixedHeight(Layout.FILES_BTN_H)
        self._files_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._files_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._files_btn.setToolTip(Strings.TIP_BROWSE_FILES)
        self._files_btn.clicked.connect(self._browse_files)

        files_row.addWidget(folder_icon)
        files_row.addWidget(self._files_btn)

        # ── Submit row ─────────────────────────────────────────────────────────
        submit_row = QHBoxLayout()
        submit_row.addStretch()

        submit_btn = QPushButton(Strings.UPLOAD_SUBMIT)
        submit_btn.setObjectName("SubmitBtn")
        submit_btn.setFont(Fonts.upload_button())
        submit_btn.setFixedSize(Layout.SUBMIT_BTN_W, Layout.SUBMIT_BTN_H)
        submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        submit_btn.clicked.connect(self._on_submit)

        submit_row.addWidget(submit_btn)
        submit_row.addStretch()

        root.addWidget(links_panel)
        root.addLayout(files_row)
        root.addStretch()
        root.addLayout(submit_row)

    # ── Drag support (frameless window) ────────────────────────────────────────

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event) -> None:
        self._drag_pos = None

    def keyPressEvent(self, event) -> None:
        """Allow Escape key to close the dialog."""
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    # ── Slots ──────────────────────────────────────────────────────────────────

    def _add_link_row(self) -> None:
        row = LinkRow(self._links_container)
        insert_pos = self._links_vbox.count() - 1
        self._links_vbox.insertWidget(insert_pos, row)
        self._link_rows.append(row)
        self._scroll_area.verticalScrollBar().setValue(
            self._scroll_area.verticalScrollBar().maximum()
        )

    def _browse_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select files",
            "",
            Strings.FILE_FILTER_ALL,
        )
        if paths:
            self._selected_files = [Path(p) for p in paths]
            count = len(self._selected_files)
            self._files_btn.setText(
                f"{count} file{'s' if count != 1 else ''} selected"
            )

    def _on_submit(self) -> None:
        links = [r.get_text().strip() for r in self._link_rows if r.get_text().strip()]
        self.submitted.emit(links, self._selected_files)
        self.accept()

    # ── Public API ─────────────────────────────────────────────────────────────

    def reset(self) -> None:
        for row in self._link_rows:
            row.clear()
        self._selected_files = []
        self._files_btn.setText(Strings.UPLOAD_FILES_BTN)
