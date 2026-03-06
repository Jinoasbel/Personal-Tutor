"""
main_window.py — Application main window.
Wires sidebar, content panels, upload dialog, and core logic together.
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
from ui.panels import ExtractedPanel, SummarizePanel, AudioPanel, AskPanel
from core.app_state import AppState
from core.workers import OCRWorker, LinkOCRWorker, SummaryWorker, AudioWorker
from core.qa_engine import QAEngine
from app_config import Config


class MainWindow(QMainWindow):
    """Top-level application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(Strings.APP_TITLE)
        self.setMinimumSize(Layout.WINDOW_MIN_W, Layout.WINDOW_MIN_H)
        self.resize(Layout.WINDOW_DEF_W, Layout.WINDOW_DEF_H)

        self._state       = AppState()
        self._qa_engine   = QAEngine()
        self._ocr_worker:  OCRWorker     | None = None
        self._link_worker: LinkOCRWorker | None = None
        self._sum_worker:  SummaryWorker | None = None
        self._aud_worker:  AudioWorker   | None = None

        # Ensure extraction folders exist
        Config.EXTRACTED_FILE.mkdir(parents=True, exist_ok=True)
        Config.EXTRACTED_LINK.mkdir(parents=True, exist_ok=True)

        self._build_ui()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)

        h_layout = QHBoxLayout(central)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar()
        self._sidebar.panel_changed.connect(self._switch_panel)

        # Content area
        content_wrapper = QWidget()
        content_wrapper.setObjectName("ContentArea")
        content_wrapper.setStyleSheet(
            f"QWidget#ContentArea {{ background-color: {Colors.BG_TERTIARY}; }}"
        )

        content_v = QVBoxLayout(content_wrapper)
        content_v.setContentsMargins(0, 0, 0, 0)
        content_v.setSpacing(0)

        # Stacked panels
        self._stack = QStackedWidget()
        self._panel_extracted = ExtractedPanel()
        self._panel_summarize = SummarizePanel()
        self._panel_audio     = AudioPanel()
        self._panel_ask       = AskPanel()

        self._stack.addWidget(self._panel_extracted)   # 0
        self._stack.addWidget(self._panel_summarize)   # 1
        self._stack.addWidget(self._panel_audio)       # 2
        self._stack.addWidget(self._panel_ask)         # 3

        self._panel_map = {
            "extracted": 0,
            "summarize": 1,
            "audio":     2,
            "ask":       3,
        }

        # UPLOAD FAB
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

        content_v.addWidget(self._stack)
        content_v.addLayout(fab_row)

        h_layout.addWidget(self._sidebar)
        h_layout.addWidget(content_wrapper, stretch=1)

        # Upload dialog
        self._upload_dialog = UploadDialog(self)
        self._upload_dialog.submitted.connect(self._on_upload_submitted)

        # Panel signals
        self._panel_summarize.summarize_requested.connect(self._run_summarize)
        self._panel_audio.audio_requested.connect(self._run_audio)
        self._panel_ask.question_asked.connect(self._on_question)

    # ── Panel Switching ────────────────────────────────────────────────────────

    def _switch_panel(self, panel_id: str) -> None:
        idx = self._panel_map.get(panel_id, 0)
        self._stack.setCurrentIndex(idx)
        self._state.active_panel = panel_id

    # ── Upload ─────────────────────────────────────────────────────────────────

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

    # ── OCR Worker (files) ─────────────────────────────────────────────────────

    def _run_ocr(self, files: list[Path]) -> None:
        if self._ocr_worker and self._ocr_worker.isRunning():
            return

        self._panel_extracted.set_text(Strings.MSG_OCR_RUNNING)
        self._sidebar.select_panel("extracted")
        self._switch_panel("extracted")

        self._ocr_worker = OCRWorker(
            files,
            extracted_dir=Config.EXTRACTED_FILE,
            parent=self,
        )
        self._ocr_worker.progress.connect(self._panel_extracted.set_text)
        self._ocr_worker.result.connect(self._on_ocr_done)
        self._ocr_worker.error.connect(
            lambda e: self._panel_extracted.set_text(f"{Strings.MSG_OCR_FAIL}\n\n{e}")
        )
        self._ocr_worker.start()

    def _on_ocr_done(self, text: str) -> None:
        self._state.extracted_text = text
        self._panel_extracted.set_text(text)
        self._qa_engine.set_context(text)

    # ── Link Worker ────────────────────────────────────────────────────────────

    def _run_link_extraction(self, links: list[str]) -> None:
        if self._link_worker and self._link_worker.isRunning():
            return

        self._link_worker = LinkOCRWorker(
            links,
            extracted_dir=Config.EXTRACTED_LINK,
            parent=self,
        )
        self._link_worker.progress.connect(self._panel_extracted.set_text)
        self._link_worker.result.connect(self._on_ocr_done)
        self._link_worker.error.connect(
            lambda e: self._panel_extracted.set_text(f"Link extraction failed:\n\n{e}")
        )
        self._link_worker.start()

    # ── Summarize ──────────────────────────────────────────────────────────────

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

    # ── Audio ──────────────────────────────────────────────────────────────────

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

    # ── Q&A ────────────────────────────────────────────────────────────────────

    def _on_question(self, question: str) -> None:
        answer = self._qa_engine.ask(question)
        self._panel_ask.append_answer(question, answer)
