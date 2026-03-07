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

        # Status bar (shown during OCR / link fetch) — single line, fixed height
        self._status_label = QLabel("")
        self._status_label.setFont(Fonts.body())
        self._status_label.setStyleSheet(f"color: {Colors.TEXT_ACCENT};")
        self._status_label.setFixedHeight(20)
        self._status_label.setWordWrap(False)
        self._status_label.setTextFormat(Qt.TextFormat.PlainText)
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
        """Show a single-line status message. Truncates at first newline."""
        single = text.split("\n")[0].strip()
        self._status_label.setText(single)
        self._status_label.setVisible(bool(single))

    def clear(self) -> None:
        self._text_area.clear()
        self._file_title.setVisible(False)
        self._status_label.setVisible(False)



# ── Summarize Panel ────────────────────────────────────────────────────────────

class SummarizePanel(QWidget):
    """
    Left pane  : file checkboxes (fromfile + fromlink), Select All, Summarize btn
    Right pane : summary text viewer + saved summaries list
    """

    summarize_requested = Signal(dict)   # {stem: text}

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._file_checks: dict[str, object] = {}   # path -> QCheckBox
        self._build_ui()
        self._setup_watcher()
        self._refresh_files()
        self._refresh_summaries()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Left pane: file selection ──────────────────────────────────────────
        left = QWidget()
        left.setMinimumWidth(220)
        left.setMaximumWidth(300)
        left.setStyleSheet(
            f"background: {Colors.SURFACE_MID};"            f"border-right: 1px solid {Colors.BORDER_DEFAULT};"
        )
        lv = QVBoxLayout(left)
        lv.setContentsMargins(Spacing.MD, Spacing.XL, Spacing.MD, Spacing.XL)
        lv.setSpacing(Spacing.SM)

        title_lbl = QLabel("SUMMARIZE")
        title_lbl.setFont(Fonts.heading())
        title_lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        lv.addWidget(title_lbl)

        sub_lbl = QLabel("SELECT FILES TO SUMMARIZE")
        sub_lbl.setFont(Fonts.body())
        sub_lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        lv.addWidget(sub_lbl)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color: {Colors.BORDER_DEFAULT};")
        lv.addWidget(line)

        # Status
        self._status_lbl = QLabel("")
        self._status_lbl.setFont(Fonts.body())
        self._status_lbl.setStyleSheet(f"color: {Colors.TEXT_ACCENT};")
        self._status_lbl.setWordWrap(True)
        self._status_lbl.setVisible(False)
        lv.addWidget(self._status_lbl)

        # Select All
        from PySide6.QtWidgets import QCheckBox, QScrollArea
        self._select_all = QCheckBox("  Select All")
        self._select_all.setFont(Fonts.label())
        self._select_all.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        self._select_all.stateChanged.connect(self._on_select_all)
        lv.addWidget(self._select_all)

        # Scrollable checkbox list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._cb_container = QWidget()
        self._cb_container.setStyleSheet("background: transparent;")
        self._cb_vbox = QVBoxLayout(self._cb_container)
        self._cb_vbox.setContentsMargins(Spacing.XS, 0, 0, 0)
        self._cb_vbox.setSpacing(Spacing.XS)
        self._cb_vbox.addStretch()
        scroll.setWidget(self._cb_container)
        lv.addWidget(scroll)

        # Summarize button
        self._summarize_btn = QPushButton("  Summarize")
        self._summarize_btn.setObjectName("UploadFab")
        self._summarize_btn.setFont(Fonts.upload_button())
        self._summarize_btn.setFixedHeight(44)
        self._summarize_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._summarize_btn.clicked.connect(self._on_summarize)
        lv.addWidget(self._summarize_btn)

        # ── Right pane: two sections ───────────────────────────────────────────
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        rv.setSpacing(Spacing.MD)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(4)
        splitter.setStyleSheet(
            f"QSplitter::handle {{ background: {Colors.BORDER_DEFAULT}; }}"
        )

        # Top: current summary viewer
        top_widget = QWidget()
        top_widget.setStyleSheet("background: transparent;")
        tv = QVBoxLayout(top_widget)
        tv.setContentsMargins(0, 0, 0, 0)
        tv.setSpacing(Spacing.XS)

        viewer_hdr = QHBoxLayout()
        viewer_title = QLabel("Summary")
        viewer_title.setFont(Fonts.label())
        viewer_title.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        self._summary_source = QLabel("")
        self._summary_source.setFont(Fonts.body())
        self._summary_source.setStyleSheet(f"color: {Colors.TEXT_PLACEHOLDER}; font-size: 10px;")
        viewer_hdr.addWidget(viewer_title)
        viewer_hdr.addStretch()
        viewer_hdr.addWidget(self._summary_source)
        tv.addLayout(viewer_hdr)

        self._text_area = QTextEdit()
        self._text_area.setReadOnly(True)
        self._text_area.setFont(Fonts.body())
        self._text_area.setPlaceholderText("Select files and click Summarize to generate a summary…")
        self._text_area.setStyleSheet(f"""
            QTextEdit {{
                background: {Colors.SURFACE_MID};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: {Radius.MD}px;
                padding: {Spacing.MD}px;
            }}
        """)
        tv.addWidget(self._text_area)
        splitter.addWidget(top_widget)

        # Bottom: saved summaries list
        bottom_widget = QWidget()
        bottom_widget.setStyleSheet("background: transparent;")
        bv = QVBoxLayout(bottom_widget)
        bv.setContentsMargins(0, 0, 0, 0)
        bv.setSpacing(Spacing.XS)

        saved_hdr = QHBoxLayout()
        saved_title = QLabel("Saved Summaries")
        saved_title.setFont(Fonts.label())
        saved_title.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        refresh_btn = QPushButton("↻")
        refresh_btn.setObjectName("FilesBtn")
        refresh_btn.setFont(Fonts.label())
        refresh_btn.setFixedSize(28, 28)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self._refresh_summaries)
        saved_hdr.addWidget(saved_title)
        saved_hdr.addStretch()
        saved_hdr.addWidget(refresh_btn)
        bv.addLayout(saved_hdr)

        self._summary_list = QListWidget()
        self._summary_list.setFont(Fonts.body())
        self._summary_list.setMaximumHeight(160)
        self._summary_list.setStyleSheet(f"""
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
            QListWidget::item:hover {{ background: {Colors.SURFACE_LIGHT}; }}
            QListWidget::item:selected {{
                background: {Colors.SIDEBAR_ACTIVE};
                border-left: 3px solid {Colors.ICON_ACTIVE};
            }}
        """)
        self._summary_list.currentItemChanged.connect(self._on_summary_selected)
        bv.addWidget(self._summary_list)
        splitter.addWidget(bottom_widget)

        splitter.setSizes([400, 160])
        rv.addWidget(splitter)

        root.addWidget(left)
        root.addWidget(right, stretch=1)

    def _setup_watcher(self) -> None:
        from PySide6.QtCore import QFileSystemWatcher
        self._watcher = QFileSystemWatcher(self)
        for f in (Config.EXTRACTED_FILE, Config.EXTRACTED_LINK):
            f.mkdir(parents=True, exist_ok=True)
            self._watcher.addPath(str(f.resolve()))
        Config.SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
        self._summaries_watch_path = str(Config.SUMMARIES_DIR.resolve())
        self._watcher.addPath(self._summaries_watch_path)
        self._watcher.directoryChanged.connect(self._on_dir_changed)

    def _on_dir_changed(self, path: str) -> None:
        if path == self._summaries_watch_path:
            self._refresh_summaries()
        else:
            self._refresh_files()

    def _refresh_files(self) -> None:
        from PySide6.QtWidgets import QCheckBox
        # Clear
        for i in reversed(range(self._cb_vbox.count() - 1)):
            item = self._cb_vbox.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
                self._cb_vbox.removeItem(item)
        self._file_checks.clear()

        all_files = []
        for folder in (Config.EXTRACTED_FILE, Config.EXTRACTED_LINK):
            if folder.exists():
                all_files.extend(
                    sorted(folder.glob("*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
                )

        for fp in all_files:
            tag = "📄" if fp.parent.name == "fromfile" else "🔗"
            cb = QCheckBox(f"  {tag}  {fp.stem}")
            cb.setFont(Fonts.body())
            cb.setStyleSheet(f"""
                QCheckBox {{
                    color: {Colors.TEXT_PRIMARY};
                    padding: {Spacing.XS}px;
                }}
                QCheckBox::indicator {{
                    width: 15px; height: 15px;
                    border: 2px solid {Colors.BORDER_DEFAULT};
                    border-radius: {Radius.XS}px;
                    background: {Colors.SURFACE_MID};
                }}
                QCheckBox::indicator:checked {{
                    background: {Colors.ICON_ACTIVE};
                    border-color: {Colors.ICON_ACTIVE};
                }}
            """)
            self._file_checks[str(fp)] = cb
            self._cb_vbox.insertWidget(self._cb_vbox.count() - 1, cb)

    def _refresh_summaries(self) -> None:
        self._summary_list.clear()
        if not Config.SUMMARIES_DIR.exists():
            return
        files = sorted(
            Config.SUMMARIES_DIR.glob("*_summarized*.txt"),
            key=lambda p: p.stat().st_mtime, reverse=True
        )
        for f in files:
            item = QListWidgetItem(f"📝  {f.stem}")
            item.setData(Qt.ItemDataRole.UserRole, str(f))
            self._summary_list.addItem(item)

    def _on_select_all(self, state: int) -> None:
        checked = state == Qt.CheckState.Checked.value
        for cb in self._file_checks.values():
            cb.setChecked(checked)

    def _on_summarize(self) -> None:
        selected = {p: cb for p, cb in self._file_checks.items() if cb.isChecked()}
        if not selected:
            self._set_status("Please select at least one file.")
            return
        source_texts = {}
        for path_str in selected:
            fp = Path(path_str)
            try:
                source_texts[fp.stem] = fp.read_text(encoding="utf-8")
            except Exception:
                pass
        self._set_status(f"Summarizing {len(source_texts)} file(s)…")
        self.summarize_requested.emit(source_texts)

    def _on_summary_selected(self, current, _prev) -> None:
        if not current:
            return
        fp = Path(current.data(Qt.ItemDataRole.UserRole))
        try:
            content = fp.read_text(encoding="utf-8")
        except Exception as e:
            content = f"[Could not read file: {e}]"
        self._text_area.setPlainText(content)
        self._summary_source.setText(fp.name)

    def _set_status(self, text: str) -> None:
        self._status_lbl.setText(text)
        self._status_lbl.setVisible(bool(text))

    # ── Public API ─────────────────────────────────────────────────────────────

    def set_text(self, text: str) -> None:
        """Called by main_window to show status or result."""
        self._set_status(text)

    def show_summary(self, path: str) -> None:
        """Load and display a freshly saved summary, refresh the list."""
        self._refresh_summaries()
        fp = Path(path)
        try:
            content = fp.read_text(encoding="utf-8")
        except Exception as e:
            content = f"[Error reading summary: {e}]"
        self._text_area.setPlainText(content)
        self._summary_source.setText(fp.name)
        self._set_status(f"Saved → {fp.name}")

        # Auto-select the new entry in the list so the user can see it
        for i in range(self._summary_list.count()):
            item = self._summary_list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == str(fp):
                self._summary_list.setCurrentItem(item)
                break

    def clear(self) -> None:
        self._text_area.clear()
        self._summary_source.setText("")
        self._set_status("")
