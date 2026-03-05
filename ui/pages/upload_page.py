"""
ui/pages/upload_page.py
-----------------------
The document upload and OCR extraction page.

Responsibilities:
    - Shows a drop-zone prompt when no document is loaded.
    - Triggers OCR via the shared OCREngine (passed through app_state).
    - Displays extracted text in a read-only textbox.
    - Reports status (ready / extracting / success / error).
"""

from PySide6.QtWidgets import (
    QLabel, QPlainTextEdit, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QFrame
)
from PySide6.QtCore import Qt

import app_config as cfg
from ui.pages.base_page import BasePage


class UploadPage(BasePage):
    """
    Layout:
        ┌─────────────────────────────────┐
        │  Document Upload                │  ← inherited title
        │  ─────────────────────────────  │
        │  Status label                   │
        │  ┌───────────────────────────┐  │
        │  │  Drop zone / text output  │  │
        │  └───────────────────────────┘  │
        │  [ Browse File ]                │
        └─────────────────────────────────┘
    """

    def __init__(self, app_state: dict, parent=None):
        super().__init__(cfg.PAGE_UPLOAD, app_state, parent)
        self._build_ui()

    def _build_ui(self):
        # ── Status label ─────────────────────────────────────────────────────
        self._status = QLabel(cfg.STATUS_INIT)
        self._status.setFont(cfg.FONT_STATUS)
        self._status.setStyleSheet(cfg.label_style(cfg.COLOR_STATUS_WAIT))
        self.content_layout.addWidget(self._status)

        # ── Drop zone (shown when no text extracted yet) ──────────────────────
        self._drop_zone = QFrame()
        self._drop_zone.setStyleSheet(
            f"QFrame {{ background-color: {cfg.COLOR_TEXTBOX_BG};"
            f"  border: 2px dashed {cfg.COLOR_DIVIDER}; border-radius: 10px; }}"
        )
        drop_layout = QVBoxLayout(self._drop_zone)
        drop_layout.setAlignment(Qt.AlignCenter)

        drop_icon = QLabel("📄")
        drop_icon.setAlignment(Qt.AlignCenter)
        drop_icon.setFont(cfg.FONT_HEADING)
        drop_icon.setStyleSheet(cfg.label_style(cfg.COLOR_TEXT_SUBTLE))

        drop_msg = QLabel(cfg.UPLOAD_PROMPT_TEXT)
        drop_msg.setAlignment(Qt.AlignCenter)
        drop_msg.setFont(cfg.FONT_BODY)
        drop_msg.setStyleSheet(cfg.label_style(cfg.COLOR_TEXT_SUBTLE))

        drop_hint = QLabel(cfg.UPLOAD_HINT_TEXT)
        drop_hint.setAlignment(Qt.AlignCenter)
        drop_hint.setFont(cfg.FONT_HINT)
        drop_hint.setStyleSheet(cfg.label_style(cfg.COLOR_DIVIDER))

        drop_layout.addWidget(drop_icon)
        drop_layout.addWidget(drop_msg)
        drop_layout.addWidget(drop_hint)

        # ── Text output (shown after extraction) ──────────────────────────────
        self._output = QPlainTextEdit()
        self._output.setReadOnly(True)
        self._output.setFont(cfg.FONT_BODY)
        self._output.setStyleSheet(cfg.textbox_style(cfg.COLOR_TEXTBOX_BG, cfg.COLOR_TEXT_MAIN))
        self._output.setVisible(False)

        self.content_layout.addWidget(self._drop_zone, stretch=1)
        self.content_layout.addWidget(self._output,    stretch=1)

        # ── Browse button ─────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._browse_btn = QPushButton(cfg.LABEL_UPLOAD)
        self._browse_btn.setFixedHeight(cfg.ADD_BTN_HEIGHT)
        self._browse_btn.setFont(cfg.FONT_BUTTON)
        self._browse_btn.setStyleSheet(
            cfg.action_button_style(cfg.COLOR_ACCENT_MAIN, cfg.COLOR_ACCENT_HOVER, cfg.COLOR_TEXT_MAIN)
        )
        self._browse_btn.setCursor(Qt.PointingHandCursor)
        self._browse_btn.clicked.connect(self._open_dialog)
        btn_row.addWidget(self._browse_btn)
        self.content_layout.addLayout(btn_row)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_enter(self):
        self._status.setText(cfg.STATUS_READY)
        self._status.setStyleSheet(cfg.label_style(cfg.COLOR_TEXT_MAIN))

    # ── Internal ──────────────────────────────────────────────────────────────

    def _open_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, cfg.DIALOG_TITLE, "", cfg.DIALOG_FILTER
        )
        if path:
            self._start_ocr(path)

    def _start_ocr(self, file_path: str):
        self._status.setText(cfg.STATUS_EXTRACTING)
        self._status.setStyleSheet(cfg.label_style(cfg.COLOR_STATUS_WAIT))
        self._browse_btn.setEnabled(False)

        ocr = self.app_state.get("ocr_engine")
        if ocr is None:
            self._on_error("OCR engine not initialised in app_state.")
            return

        ocr.extract(file_path, on_success=self._on_success, on_error=self._on_error)

    def _on_success(self, text: str):
        # Store extracted text in shared state so other pages can use it
        self.app_state["last_extracted_text"] = text

        self._drop_zone.setVisible(False)
        self._output.setVisible(True)
        self._output.setPlainText(text)
        self._status.setText(cfg.STATUS_SUCCESS)
        self._status.setStyleSheet(cfg.label_style(cfg.COLOR_STATUS_OK))
        self._browse_btn.setEnabled(True)

    def _on_error(self, message: str):
        self._status.setText(f"{cfg.STATUS_ERROR_PREFIX}{message}")
        self._status.setStyleSheet(cfg.label_style(cfg.COLOR_STATUS_ERROR))
        self._browse_btn.setEnabled(True)

    # ── Public ────────────────────────────────────────────────────────────────

    def set_upload_enabled(self, enabled: bool):
        self._browse_btn.setEnabled(enabled)
