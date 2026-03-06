"""
main_window.py — Application main window.
"""

from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout, QMainWindow, QPushButton,
    QStackedWidget, QVBoxLayout, QWidget,
)

from pt_theme import Colors, Fonts, Strings, Layout, Spacing
from ui.sidebar import Sidebar
from ui.upload_dialog import UploadDialog
from ui.panels import ExtractedPanel, SummarizePanel, AudioPanel
from ui.ask_panel import AskPanel
from ui.settings_panel import SettingsPanel
from core.app_state import AppState
from core.workers import OCRWorker, LinkOCRWorker, SummaryWorker, AudioWorker
from app_config import Config


class MainWindow(QMainWindow):

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(Strings.APP_TITLE)
        self.setMinimumSize(Layout.WINDOW_MIN_W, Layout.WINDOW_MIN_H)
        self.resize(Layout.WINDOW_DEF_W, Layout.WINDOW_DEF_H)

        self._state        = AppState()
        self._ocr_worker:  OCRWorker     | None = None
        self._link_worker: LinkOCRWorker | None = None
        self._sum_worker:  SummaryWorker | None = None
        self._aud_worker:  AudioWorker   | None = None

        for d in (
            Config.EXTRACTED_FILE, Config.EXTRACTED_LINK,
            Config.QUESTIONS_DIR,  Config.RESULTS_DIR,
        ):
            d.mkdir(parents=True, exist_ok=True)

        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        h = QHBoxLayout(central)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        self._sidebar = Sidebar()
        self._sidebar.panel_changed.connect(self._switch_panel)

        content_wrapper = QWidget()
        content_wrapper.setObjectName("ContentArea")
        content_wrapper.setStyleSheet(
            f"QWidget#ContentArea {{ background-color: {Colors.BG_TERTIARY}; }}"
        )

        cv = QVBoxLayout(content_wrapper)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(0)

        # Panels
        self._stack            = QStackedWidget()
        self._panel_extracted  = ExtractedPanel()
        self._panel_summarize  = SummarizePanel()
        self._panel_audio      = AudioPanel()
        self._panel_ask        = AskPanel()
        self._panel_settings   = SettingsPanel()

        self._stack.addWidget(self._panel_extracted)   # 0
        self._stack.addWidget(self._panel_summarize)   # 1
        self._stack.addWidget(self._panel_audio)       # 2
        self._stack.addWidget(self._panel_ask)         # 3
        self._stack.addWidget(self._panel_settings)    # 4

        self._panel_map = {
            "extracted": 0,
            "summarize": 1,
            "audio":     2,
            "ask":       3,
            "settings":  4,
        }

        # Upload FAB
        fab_row = QHBoxLayout()
        fab_row.setContentsMargins(0, 0, Spacing.XL, Spacing.XL)
        self._upload_fab = QPushButton(Strings.UPLOAD_BTN)
        self._upload_fab.setObjectName("UploadFab")
        self._upload_fab.setFont(Fonts.upload_button())
        self._upload_fab.setFixedHeight(Layout.FAB_H)
        self._upload_fab.setMinimumWidth(Layout.FAB_MIN_W)
        self._upload_fab.setCursor(Qt.CursorShape.PointingHandCursor)
        self._upload_fab.clicked.connect(self._open_upload_dialog)
        fab_row.addStretch()
        fab_row.addWidget(self._upload_fab)

        cv.addWidget(self._stack)
        cv.addLayout(fab_row)

        h.addWidget(self._sidebar)
        h.addWidget(content_wrapper, stretch=1)

        self._upload_dialog = UploadDialog(self)
        self._upload_dialog.submitted.connect(self._on_upload_submitted)

        self._panel_summarize.summarize_requested.connect(self._run_summarize)
        self._panel_audio.audio_requested.connect(self._run_audio)

    def _switch_panel(self, panel_id: str) -> None:
        self._stack.setCurrentIndex(self._panel_map.get(panel_id, 0))
        self._state.active_panel = panel_id

    def _open_upload_dialog(self) -> None:
        self._upload_dialog.reset()
        self._upload_dialog.exec()

    def _on_upload_submitted(self, links: list[str], files: list[Path]) -> None:
        self._state.pasted_links   = links
        self._state.uploaded_files = files
        if files:
            self._run_ocr(files)
        if links:
            self._run_link_extraction(links)

    def _run_ocr(self, files: list[Path]) -> None:
        if self._ocr_worker and self._ocr_worker.isRunning():
            return
        self._panel_extracted.set_text(Strings.MSG_OCR_RUNNING)
        self._sidebar.select_panel("extracted")
        self._switch_panel("extracted")
        self._ocr_worker = OCRWorker(files, Config.EXTRACTED_FILE, parent=self)
        self._ocr_worker.progress.connect(self._panel_extracted.set_text)
        self._ocr_worker.result.connect(self._on_ocr_done)
        self._ocr_worker.error.connect(
            lambda e: self._panel_extracted.set_text(f"{Strings.MSG_OCR_FAIL}\n\n{e}")
        )
        self._ocr_worker.start()

    def _on_ocr_done(self, text: str) -> None:
        self._state.extracted_text = text
        self._panel_extracted.set_text(text)

    def _run_link_extraction(self, links: list[str]) -> None:
        if self._link_worker and self._link_worker.isRunning():
            return
        self._link_worker = LinkOCRWorker(links, Config.EXTRACTED_LINK, parent=self)
        self._link_worker.progress.connect(self._panel_extracted.set_text)
        self._link_worker.result.connect(self._on_ocr_done)
        self._link_worker.error.connect(
            lambda e: self._panel_extracted.set_text(f"Link extraction failed:\n\n{e}")
        )
        self._link_worker.start()

    def _run_summarize(self) -> None:
        if not self._state.has_content():
            self._panel_summarize.set_text(Strings.EXTRACTED_EMPTY)
            return
        if self._sum_worker and self._sum_worker.isRunning():
            return
        self._panel_summarize.set_text(Strings.MSG_SUMMARIZING)
        self._sum_worker = SummaryWorker(self._state.extracted_text, parent=self)
        self._sum_worker.result.connect(self._on_summary_done)
        self._sum_worker.error.connect(
            lambda e: self._panel_summarize.set_text(f"Error: {e}")
        )
        self._sum_worker.start()

    def _on_summary_done(self, text: str) -> None:
        self._state.summary_text = text
        self._panel_summarize.set_text(text)

    def _run_audio(self) -> None:
        if not self._state.has_content():
            self._panel_audio.set_status(Strings.EXTRACTED_EMPTY)
            return
        if self._aud_worker and self._aud_worker.isRunning():
            return
        self._panel_audio.set_status(Strings.MSG_AUDIO_GEN)
        self._aud_worker = AudioWorker(
            self._state.extracted_text, Config.AUDIO_OUTPUT, parent=self
        )
        self._aud_worker.result.connect(
            lambda p: self._panel_audio.set_status(f"Audio saved: {p}")
        )
        self._aud_worker.error.connect(
            lambda e: self._panel_audio.set_status(f"Error: {e}")
        )
        self._aud_worker.start()
