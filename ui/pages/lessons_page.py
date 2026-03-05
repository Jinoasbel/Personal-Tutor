"""
ui/pages/lessons_page.py
------------------------
Lessons page — create and manage lessons.

Lessons are stored in app_state["lessons"] as a list of dicts.
If extracted text exists (app_state["last_extracted_text"]), a
"Generate from document" button appears to pre-populate a lesson.
"""

from PySide6.QtWidgets import (
    QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QScrollArea, QWidget, QFrame, QTextEdit
)
from PySide6.QtCore import Qt

import app_config as cfg
from ui.pages.base_page import BasePage


class _LessonCard(QFrame):
    """
    Single lesson card:
        ┌───────────────────────────────────────┐
        │  Lesson Title                   [X]   │
        │  Preview of content...                │
        └───────────────────────────────────────┘
    """

    def __init__(self, lesson: dict, on_delete, parent=None):
        super().__init__(parent)
        self.setStyleSheet(cfg.card_style(cfg.COLOR_CARD_BG, cfg.CARD_RADIUS))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 10, 10)
        layout.setSpacing(4)

        header = QHBoxLayout()
        title = QLabel(lesson.get("title", "Untitled"))
        title.setFont(cfg.FONT_SUBHEADING)
        title.setStyleSheet(cfg.label_style(cfg.COLOR_TEXT_MAIN))
        header.addWidget(title, stretch=1)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(28, 28)
        del_btn.setFont(cfg.FONT_BODY_SMALL)
        del_btn.setStyleSheet(
            cfg.action_button_style("transparent", cfg.COLOR_STATUS_ERROR, cfg.COLOR_STATUS_ERROR)
        )
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.clicked.connect(lambda: on_delete(lesson))
        header.addWidget(del_btn)

        layout.addLayout(header)

        preview_text = lesson.get("content", "")[:120]
        if len(lesson.get("content", "")) > 120:
            preview_text += "..."
        preview = QLabel(preview_text)
        preview.setFont(cfg.FONT_HINT)
        preview.setStyleSheet(cfg.label_style(cfg.COLOR_TEXT_SUBTLE))
        preview.setWordWrap(True)
        layout.addWidget(preview)


class LessonsPage(BasePage):
    """
    Layout:
        ┌─────────────────────────────────────┐
        │  Lessons                            │
        │  [Generate from document]  (if doc) │
        │  ┌─────────────────────────────┐    │
        │  │ lesson card                 │    │
        │  └─────────────────────────────┘    │
        │  [title input]  [+ New Lesson]      │
        └─────────────────────────────────────┘
    """

    def __init__(self, app_state: dict, parent=None):
        super().__init__(cfg.PAGE_LESSONS, app_state, parent)
        self.app_state.setdefault("lessons", [])
        self._build_ui()

    def _build_ui(self):
        # ── "Generate from document" banner ───────────────────────────────────
        self._gen_banner = QFrame()
        self._gen_banner.setStyleSheet(
            f"QFrame {{ background-color: {cfg.COLOR_ACCENT_MAIN};"
            f"  border-radius: {cfg.CARD_RADIUS}px; }}"
        )
        banner_layout = QHBoxLayout(self._gen_banner)
        banner_layout.setContentsMargins(14, 8, 10, 8)

        banner_label = QLabel("Document text available — generate a lesson from it?")
        banner_label.setFont(cfg.FONT_BODY_SMALL)
        banner_label.setStyleSheet(cfg.label_style(cfg.COLOR_TEXT_MAIN))
        banner_layout.addWidget(banner_label, stretch=1)

        gen_btn = QPushButton("Generate")
        gen_btn.setFixedHeight(30)
        gen_btn.setFont(cfg.FONT_BUTTON)
        gen_btn.setStyleSheet(
            cfg.action_button_style(cfg.COLOR_STATUS_OK, "#3a9a40", cfg.COLOR_TEXT_MAIN)
        )
        gen_btn.setCursor(Qt.PointingHandCursor)
        gen_btn.clicked.connect(self._generate_from_doc)
        banner_layout.addWidget(gen_btn)

        self._gen_banner.setVisible(False)
        self.content_layout.addWidget(self._gen_banner)

        # ── Scrollable list ────────────────────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(cfg.scroll_area_style(cfg.COLOR_PRIMARY_BG))
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._list_widget = QWidget()
        self._list_widget.setStyleSheet(f"background: {cfg.COLOR_PRIMARY_BG};")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(8)
        self._list_layout.addStretch()

        self._empty_label = QLabel(cfg.LESSONS_EMPTY)
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setFont(cfg.FONT_BODY)
        self._empty_label.setStyleSheet(cfg.label_style(cfg.COLOR_TEXT_SUBTLE))
        self._empty_label.setWordWrap(True)
        self._list_layout.insertWidget(0, self._empty_label)

        self._scroll.setWidget(self._list_widget)
        self.content_layout.addWidget(self._scroll, stretch=1)

        # ── Input row ─────────────────────────────────────────────────────────
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self._input = QLineEdit()
        self._input.setFixedHeight(cfg.INPUT_HEIGHT)
        self._input.setPlaceholderText(cfg.LESSON_INPUT_PLACEHOLDER)
        self._input.setFont(cfg.FONT_BODY)
        self._input.setStyleSheet(
            cfg.input_style(cfg.COLOR_INPUT_BG, cfg.COLOR_TEXT_MAIN, cfg.COLOR_INPUT_BORDER)
        )
        self._input.returnPressed.connect(self._add_lesson)

        add_btn = QPushButton(cfg.LESSONS_ADD_BTN)
        add_btn.setFixedHeight(cfg.ADD_BTN_HEIGHT)
        add_btn.setFont(cfg.FONT_BUTTON)
        add_btn.setStyleSheet(
            cfg.action_button_style(cfg.COLOR_ACCENT_MAIN, cfg.COLOR_ACCENT_HOVER, cfg.COLOR_TEXT_MAIN)
        )
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._add_lesson)

        input_row.addWidget(self._input, stretch=1)
        input_row.addWidget(add_btn)
        self.content_layout.addLayout(input_row)

        self._refresh_list()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_enter(self):
        has_doc = bool(self.app_state.get("last_extracted_text", "").strip())
        self._gen_banner.setVisible(has_doc)
        self._refresh_list()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _add_lesson(self, title: str = "", content: str = ""):
        raw_title = title or self._input.text().strip()
        if not raw_title:
            return
        self.app_state["lessons"].append({
            "title":   raw_title,
            "content": content or f"Lesson: {raw_title}"
        })
        self._input.clear()
        self._refresh_list()

    def _generate_from_doc(self):
        text = self.app_state.get("last_extracted_text", "").strip()
        if not text:
            return
        # Use first 60 chars of extracted text as an auto-title
        auto_title = text[:60].replace("\n", " ").strip()
        self.app_state["lessons"].append({
            "title":   auto_title,
            "content": text
        })
        self._gen_banner.setVisible(False)
        self._refresh_list()

    def _delete_lesson(self, lesson: dict):
        self.app_state["lessons"] = [
            l for l in self.app_state["lessons"] if l is not lesson
        ]
        self._refresh_list()

    # ── Rendering ─────────────────────────────────────────────────────────────

    def _refresh_list(self):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        lessons = self.app_state.get("lessons", [])
        self._empty_label.setVisible(len(lessons) == 0)

        for lesson in lessons:
            card = _LessonCard(lesson, on_delete=self._delete_lesson)
            self._list_layout.insertWidget(self._list_layout.count() - 1, card)
