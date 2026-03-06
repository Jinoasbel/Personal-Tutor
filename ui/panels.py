"""
panels.py — Content panel widgets for each nav section.
"""

from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QFileSystemWatcher
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QSplitter, QTextEdit, QVBoxLayout, QWidget,
)

from pt_theme import Colors, Fonts, Strings, Spacing, Radius
from app_config import Config


def _placeholder_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("PlaceholderLabel")
    lbl.setFont(Fonts.body())
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setWordWrap(True)
    return lbl


# ── Extracted Text Panel ───────────────────────────────────────────────────────

class ExtractedPanel(QWidget):
    """
    Two-pane panel:
      Left  — file list browsed from Data/extracted/ (fromfile + fromlink)
      Right — content of the selected file
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_status: str = ""   # live OCR status text
        self._build_ui()
        self._setup_watcher()
        self._refresh_file_list()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        root.setSpacing(Spacing.MD)

        # Header row
        header = QHBoxLayout()
        title = QLabel(Strings.NAV_EXTRACTED)
        title.setFont(Fonts.heading())

        refresh_btn = QPushButton("↻  Refresh")
        refresh_btn.setObjectName("FilesBtn")
        refresh_btn.setFont(Fonts.label())
        refresh_btn.setFixedHeight(32)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self._refresh_file_list)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(refresh_btn)
        root.addLayout(header)

        # Status bar (shown during OCR)
        self._status_label = QLabel("")
        self._status_label.setFont(Fonts.body())
        self._status_label.setStyleSheet(f"color: {Colors.TEXT_ACCENT};")
        self._status_label.setVisible(False)
        root.addWidget(self._status_label)

        # Splitter — file list | content viewer
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet(
            f"QSplitter::handle {{ background: {Colors.BORDER_DEFAULT}; }}"
        )

        # ── Left pane: file list ───────────────────────────────────────────────
        left = QWidget()
        left.setMinimumWidth(180)
        left.setMaximumWidth(300)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, Spacing.SM, 0)
        left_layout.setSpacing(Spacing.XS)

        # Section headers + lists
        self._list_file = self._make_list()
        self._list_link = self._make_list()

        lbl_file = self._make_section_label("📄  From File")
        lbl_link = self._make_section_label("🔗  From Link")

        left_layout.addWidget(lbl_file)
        left_layout.addWidget(self._list_file)
        left_layout.addWidget(lbl_link)
        left_layout.addWidget(self._list_link)

        # ── Right pane: content viewer ─────────────────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(Spacing.SM, 0, 0, 0)
        right_layout.setSpacing(Spacing.XS)

        self._file_title = QLabel("")
        self._file_title.setFont(Fonts.label())
        self._file_title.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        self._file_title.setVisible(False)

        self._text_area = QTextEdit()
        self._text_area.setReadOnly(True)
        self._text_area.setFont(Fonts.mono())
        self._text_area.setPlaceholderText(Strings.EXTRACTED_EMPTY)

        right_layout.addWidget(self._file_title)
        right_layout.addWidget(self._text_area)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        root.addWidget(splitter)

        # Connect list selection
        self._list_file.currentItemChanged.connect(self._on_item_selected)
        self._list_link.currentItemChanged.connect(self._on_item_selected)

    def _make_list(self) -> QListWidget:
        lst = QListWidget()
        lst.setFont(Fonts.body())
        lst.setStyleSheet(f"""
            QListWidget {{
                background: {Colors.SURFACE_MID};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: {Radius.SM}px;
                padding: {Spacing.XS}px;
            }}
            QListWidget::item {{
                padding: {Spacing.SM}px {Spacing.MD}px;
                border-radius: {Radius.XS}px;
                color: {Colors.TEXT_PRIMARY};
            }}
            QListWidget::item:hover {{
                background: {Colors.SURFACE_LIGHT};
            }}
            QListWidget::item:selected {{
                background: {Colors.SIDEBAR_ACTIVE};
                color: {Colors.TEXT_PRIMARY};
                border-left: 3px solid {Colors.ICON_ACTIVE};
            }}
        """)
        lst.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        return lst

    def _make_section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(Fonts.label())
        lbl.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY};"
            f"padding: {Spacing.XS}px 0px;"
        )
        return lbl

    # ── File Watcher ───────────────────────────────────────────────────────────

    def _setup_watcher(self) -> None:
        """Watch the extracted folders and auto-refresh when files change."""
        self._watcher = QFileSystemWatcher(self)
        for folder in (Config.EXTRACTED_FILE, Config.EXTRACTED_LINK):
            folder.mkdir(parents=True, exist_ok=True)
            self._watcher.addPath(str(folder))
        self._watcher.directoryChanged.connect(self._refresh_file_list)

    # ── File List ──────────────────────────────────────────────────────────────

    def _refresh_file_list(self) -> None:
        """Reload both lists from disk."""
        self._populate_list(self._list_file, Config.EXTRACTED_FILE)
        self._populate_list(self._list_link, Config.EXTRACTED_LINK)

    def _populate_list(self, lst: QListWidget, folder: Path) -> None:
        lst.clear()
        if not folder.exists():
            return
        txt_files = sorted(folder.glob("*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
        for f in txt_files:
            item = QListWidgetItem(f.stem)
            item.setData(Qt.ItemDataRole.UserRole, str(f))
            item.setToolTip(str(f))
            lst.addItem(item)

    # ── Selection ──────────────────────────────────────────────────────────────

    def _on_item_selected(self, current: QListWidgetItem | None, _prev) -> None:
        if current is None:
            return
        # Deselect the other list
        sender = self.sender()
        if sender is self._list_file:
            self._list_link.clearSelection()
        else:
            self._list_file.clearSelection()

        file_path = Path(current.data(Qt.ItemDataRole.UserRole))
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as exc:
            content = f"[Could not read file: {exc}]"

        self._file_title.setText(f"  {file_path.name}")
        self._file_title.setVisible(True)
        self._text_area.setPlainText(content)

    # ── Public API ─────────────────────────────────────────────────────────────

    def set_text(self, text: str) -> None:
        """Called during OCR to show live status in the status bar."""
        self._status_label.setText(text)
        self._status_label.setVisible(bool(text))

    def clear(self) -> None:
        self._text_area.clear()
        self._file_title.setVisible(False)
        self._status_label.setVisible(False)


# ── Summarize Panel ────────────────────────────────────────────────────────────

class SummarizePanel(QWidget):
    summarize_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.MD)

        header = QHBoxLayout()
        title = QLabel(Strings.NAV_SUMMARIZE)
        title.setFont(Fonts.heading())

        run_btn = QPushButton("Run Summarize")
        run_btn.setObjectName("FilesBtn")
        run_btn.setFont(Fonts.label())
        run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        run_btn.setFixedHeight(34)
        run_btn.clicked.connect(self.summarize_requested)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(run_btn)

        self._text_area = QTextEdit()
        self._text_area.setReadOnly(True)
        self._text_area.setFont(Fonts.body())
        self._text_area.setPlaceholderText(Strings.SUMMARIZE_EMPTY)

        layout.addLayout(header)
        layout.addWidget(self._text_area)

    def set_text(self, text: str) -> None:
        self._text_area.setPlainText(text)

    def clear(self) -> None:
        self._text_area.clear()


# ── Audio Panel ────────────────────────────────────────────────────────────────

class AudioPanel(QWidget):
    audio_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.MD)

        header = QHBoxLayout()
        title = QLabel(Strings.NAV_AUDIO)
        title.setFont(Fonts.heading())

        gen_btn = QPushButton("Generate Audio")
        gen_btn.setObjectName("FilesBtn")
        gen_btn.setFont(Fonts.label())
        gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        gen_btn.setFixedHeight(34)
        gen_btn.clicked.connect(self.audio_requested)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(gen_btn)

        self._status = _placeholder_label(Strings.AUDIO_EMPTY)

        layout.addLayout(header)
        layout.addStretch()
        layout.addWidget(self._status)
        layout.addStretch()

    def set_status(self, text: str) -> None:
        self._status.setText(text)