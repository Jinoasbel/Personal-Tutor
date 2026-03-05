"""
ui/pages/questions_page.py
--------------------------
Questions page — ask questions, view answers in a threaded log.

Questions and answers are stored in app_state["questions"] as a list
of {"question": str, "answer": str} dicts.

For now, answers are placeholder responses. This is the integration
point for an LLM or retrieval system in the future.
"""

from PySide6.QtWidgets import (
    QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QScrollArea, QWidget, QFrame
)
from PySide6.QtCore import Qt

import app_config as cfg
from ui.pages.base_page import BasePage


class _QACard(QFrame):
    """
    A single question + answer bubble:
        ┌─────────────────────────────────────┐
        │  Q: What is photosynthesis?         │
        │  A: Photosynthesis is the process…  │
        └─────────────────────────────────────┘
    """

    def __init__(self, entry: dict, parent=None):
        super().__init__(parent)
        self.setStyleSheet(cfg.card_style(cfg.COLOR_CARD_BG, cfg.CARD_RADIUS))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        q_label = QLabel(f"Q:  {entry.get('question', '')}")
        q_label.setFont(cfg.FONT_SUBHEADING)
        q_label.setStyleSheet(cfg.label_style(cfg.COLOR_TEXT_MAIN))
        q_label.setWordWrap(True)
        layout.addWidget(q_label)

        answer = entry.get("answer", cfg.QUESTIONS_THINKING)
        a_label = QLabel(f"{cfg.QUESTIONS_ANSWER_PREFIX}{answer}")
        a_label.setFont(cfg.FONT_BODY_SMALL)
        a_label.setStyleSheet(cfg.label_style(cfg.COLOR_TEXT_SUBTLE))
        a_label.setWordWrap(True)
        layout.addWidget(a_label)


class QuestionsPage(BasePage):
    """
    Layout:
        ┌─────────────────────────────────────┐
        │  Questions                          │
        │  ┌─────────────────────────────┐    │
        │  │  Q: ...                     │    │
        │  │  A: ...                     │    │
        │  └─────────────────────────────┘    │
        │  [question input]        [Ask]      │
        └─────────────────────────────────────┘
    """

    def __init__(self, app_state: dict, parent=None):
        super().__init__(cfg.PAGE_QUESTIONS, app_state, parent)
        self.app_state.setdefault("questions", [])
        self._build_ui()

    def _build_ui(self):
        # ── Scrollable Q&A log ────────────────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(cfg.scroll_area_style(cfg.COLOR_PRIMARY_BG))
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._log_widget = QWidget()
        self._log_widget.setStyleSheet(f"background: {cfg.COLOR_PRIMARY_BG};")
        self._log_layout = QVBoxLayout(self._log_widget)
        self._log_layout.setContentsMargins(0, 0, 0, 0)
        self._log_layout.setSpacing(8)
        self._log_layout.addStretch()

        self._empty_label = QLabel(cfg.QUESTIONS_EMPTY)
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setFont(cfg.FONT_BODY)
        self._empty_label.setStyleSheet(cfg.label_style(cfg.COLOR_TEXT_SUBTLE))
        self._empty_label.setWordWrap(True)
        self._log_layout.insertWidget(0, self._empty_label)

        self._scroll.setWidget(self._log_widget)
        self.content_layout.addWidget(self._scroll, stretch=1)

        # ── Input row ─────────────────────────────────────────────────────────
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self._input = QLineEdit()
        self._input.setFixedHeight(cfg.INPUT_HEIGHT)
        self._input.setPlaceholderText(cfg.QUESTIONS_INPUT_PLACEHOLDER)
        self._input.setFont(cfg.FONT_BODY)
        self._input.setStyleSheet(
            cfg.input_style(cfg.COLOR_INPUT_BG, cfg.COLOR_TEXT_MAIN, cfg.COLOR_INPUT_BORDER)
        )
        self._input.returnPressed.connect(self._submit_question)

        ask_btn = QPushButton(cfg.QUESTIONS_SUBMIT_BTN)
        ask_btn.setFixedHeight(cfg.ADD_BTN_HEIGHT)
        ask_btn.setFixedWidth(70)
        ask_btn.setFont(cfg.FONT_BUTTON)
        ask_btn.setStyleSheet(
            cfg.action_button_style(cfg.COLOR_STATUS_OK, "#3a9a40", cfg.COLOR_TEXT_MAIN)
        )
        ask_btn.setCursor(Qt.PointingHandCursor)
        ask_btn.clicked.connect(self._submit_question)

        input_row.addWidget(self._input, stretch=1)
        input_row.addWidget(ask_btn)
        self.content_layout.addLayout(input_row)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_enter(self):
        self._refresh_log()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _submit_question(self):
        question = self._input.text().strip()
        if not question:
            return

        # Build a simple context-aware answer from available app state
        answer = self._generate_answer(question)

        self.app_state["questions"].append({
            "question": question,
            "answer":   answer
        })
        self._input.clear()
        self._refresh_log()

        # Scroll to bottom so latest Q&A is visible
        self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        )

    def _generate_answer(self, question: str) -> str:
        """
        Placeholder answer logic.
        Replace this method body with an LLM call or retrieval system.
        Currently checks if any lesson content contains keywords from the question.
        """
        q_lower = question.lower()
        lessons = self.app_state.get("lessons", [])

        for lesson in lessons:
            content = lesson.get("content", "")
            # Simple keyword match — find any sentence containing question words
            for sentence in content.split("."):
                words = [w.strip("?,!") for w in q_lower.split()]
                if any(w in sentence.lower() for w in words if len(w) > 3):
                    snippet = sentence.strip()
                    if snippet:
                        return f"{snippet}. (from lesson: {lesson['title']})"

        doc_text = self.app_state.get("last_extracted_text", "")
        if doc_text:
            for sentence in doc_text.split("."):
                words = [w.strip("?,!") for w in q_lower.split()]
                if any(w in sentence.lower() for w in words if len(w) > 3):
                    snippet = sentence.strip()
                    if snippet:
                        return f"{snippet}. (from uploaded document)"

        return "No relevant content found yet. Upload a document or add lessons to get started."

    # ── Rendering ─────────────────────────────────────────────────────────────

    def _refresh_log(self):
        while self._log_layout.count() > 1:
            item = self._log_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        questions = self.app_state.get("questions", [])
        self._empty_label.setVisible(len(questions) == 0)

        for entry in questions:
            card = _QACard(entry)
            self._log_layout.insertWidget(self._log_layout.count() - 1, card)
