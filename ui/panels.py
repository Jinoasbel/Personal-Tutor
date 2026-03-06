"""
panels.py — Content panel widgets for each nav section.
Each panel is a QWidget shown in the right-hand content area.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QTextEdit, QVBoxLayout, QWidget,
)

from pt_theme import Colors, Fonts, Strings, Spacing, Radius


def _placeholder_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("PlaceholderLabel")
    lbl.setFont(Fonts.body())
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setWordWrap(True)
    return lbl


# ── Extracted Text Panel ───────────────────────────────────────────────────────

class ExtractedPanel(QWidget):
    """Displays OCR-extracted text."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.MD)

        title = QLabel(Strings.NAV_EXTRACTED)
        title.setFont(Fonts.heading())

        self._text_area = QTextEdit()
        self._text_area.setReadOnly(True)
        self._text_area.setFont(Fonts.mono())
        self._text_area.setPlaceholderText(Strings.EXTRACTED_EMPTY)

        layout.addWidget(title)
        layout.addWidget(self._text_area)

    def set_text(self, text: str) -> None:
        self._text_area.setPlainText(text)

    def clear(self) -> None:
        self._text_area.clear()


# ── Summarize Panel ────────────────────────────────────────────────────────────

class SummarizePanel(QWidget):
    """Displays summarized content. Trigger button runs summarization."""

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
    """Placeholder panel for audio generation."""

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


# ── Ask Questions Panel ────────────────────────────────────────────────────────

class AskPanel(QWidget):
    """Panel for Q&A interaction."""

    question_asked = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.MD)

        title = QLabel(Strings.NAV_ASK)
        title.setFont(Fonts.heading())

        self._answer_area = QTextEdit()
        self._answer_area.setReadOnly(True)
        self._answer_area.setFont(Fonts.body())
        self._answer_area.setPlaceholderText(Strings.ASK_EMPTY)

        # Input row
        input_row = QHBoxLayout()
        input_row.setSpacing(Spacing.SM)

        self._question_input = QTextEdit()
        self._question_input.setObjectName("LinkInput")
        self._question_input.setFont(Fonts.body())
        self._question_input.setPlaceholderText(Strings.ASK_PLACEHOLDER)
        self._question_input.setFixedHeight(60)
        self._question_input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        send_btn = QPushButton(Strings.ASK_SEND)
        send_btn.setObjectName("SubmitBtn")
        send_btn.setFont(Fonts.label())
        send_btn.setFixedSize(80, 60)
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.clicked.connect(self._on_send)

        input_row.addWidget(self._question_input)
        input_row.addWidget(send_btn)

        layout.addWidget(title)
        layout.addWidget(self._answer_area)
        layout.addLayout(input_row)

    def _on_send(self) -> None:
        q = self._question_input.toPlainText().strip()
        if q:
            self.question_asked.emit(q)
            self._question_input.clear()

    def append_answer(self, question: str, answer: str) -> None:
        self._answer_area.append(f"<b>Q:</b> {question}")
        self._answer_area.append(f"<b>A:</b> {answer}")
        self._answer_area.append("")

    def clear(self) -> None:
        self._answer_area.clear()
