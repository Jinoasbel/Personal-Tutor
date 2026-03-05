"""
ui/pages/study_plans_page.py
----------------------------
Study Plans page — create, view, and delete study plans.

Each plan is stored as a dict in app_state["study_plans"] (a list).
Plans persist for the lifetime of the app session.
"""

from PySide6.QtWidgets import (
    QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QScrollArea, QWidget, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt

import app_config as cfg
from ui.pages.base_page import BasePage


class _PlanCard(QFrame):
    """
    A single study plan row:
        ┌──────────────────────────────────────────┐
        │  Plan Title                  [Open] [X]  │
        └──────────────────────────────────────────┘
    """

    def __init__(self, plan: dict, on_delete, on_open, parent=None):
        super().__init__(parent)
        self.plan = plan
        self.setFixedHeight(cfg.CARD_HEIGHT)
        self.setStyleSheet(cfg.card_style(cfg.COLOR_CARD_BG, cfg.CARD_RADIUS))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 10, 0)
        layout.setSpacing(8)

        name = QLabel(plan.get("title", "Untitled"))
        name.setFont(cfg.FONT_BODY)
        name.setStyleSheet(cfg.label_style(cfg.COLOR_TEXT_MAIN))
        layout.addWidget(name, stretch=1)

        open_btn = QPushButton(cfg.STUDY_PLAN_OPEN_BTN)
        open_btn.setFixedSize(64, 30)
        open_btn.setFont(cfg.FONT_BODY_SMALL)
        open_btn.setStyleSheet(
            cfg.action_button_style(cfg.COLOR_ACCENT_MAIN, cfg.COLOR_ACCENT_HOVER, cfg.COLOR_TEXT_MAIN)
        )
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.clicked.connect(lambda: on_open(plan))
        layout.addWidget(open_btn)

        del_btn = QPushButton(cfg.STUDY_PLAN_DELETE_BTN)
        del_btn.setFixedSize(64, 30)
        del_btn.setFont(cfg.FONT_BODY_SMALL)
        del_btn.setStyleSheet(
            cfg.action_button_style(cfg.COLOR_STATUS_ERROR, "#cc3333", cfg.COLOR_TEXT_MAIN)
        )
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.clicked.connect(lambda: on_delete(plan))
        layout.addWidget(del_btn)


class StudyPlansPage(BasePage):
    """
    Layout:
        ┌─────────────────────────────────┐
        │  Study Plans                    │
        │  ┌─────────────────────────┐    │
        │  │ plan card               │    │
        │  │ plan card               │    │
        │  └─────────────────────────┘    │
        │  [input field]  [+ New Plan]    │
        └─────────────────────────────────┘
    """

    def __init__(self, app_state: dict, parent=None):
        super().__init__(cfg.PAGE_STUDY_PLANS, app_state, parent)
        self.app_state.setdefault("study_plans", [])
        self._build_ui()

    def _build_ui(self):
        # ── Scrollable card list ──────────────────────────────────────────────
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

        self._scroll.setWidget(self._list_widget)
        self.content_layout.addWidget(self._scroll, stretch=1)

        # ── Empty state label ─────────────────────────────────────────────────
        self._empty_label = QLabel(cfg.STUDY_PLANS_EMPTY)
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setFont(cfg.FONT_BODY)
        self._empty_label.setStyleSheet(cfg.label_style(cfg.COLOR_TEXT_SUBTLE))
        self._empty_label.setWordWrap(True)
        self._list_layout.insertWidget(0, self._empty_label)

        # ── Input row ─────────────────────────────────────────────────────────
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self._input = QLineEdit()
        self._input.setFixedHeight(cfg.INPUT_HEIGHT)
        self._input.setPlaceholderText(cfg.STUDY_PLAN_INPUT_PLACEHOLDER)
        self._input.setFont(cfg.FONT_BODY)
        self._input.setStyleSheet(
            cfg.input_style(cfg.COLOR_INPUT_BG, cfg.COLOR_TEXT_MAIN, cfg.COLOR_INPUT_BORDER)
        )
        self._input.returnPressed.connect(self._add_plan)

        add_btn = QPushButton(cfg.STUDY_PLANS_ADD_BTN)
        add_btn.setFixedHeight(cfg.ADD_BTN_HEIGHT)
        add_btn.setFont(cfg.FONT_BUTTON)
        add_btn.setStyleSheet(
            cfg.action_button_style(cfg.COLOR_ACCENT_MAIN, cfg.COLOR_ACCENT_HOVER, cfg.COLOR_TEXT_MAIN)
        )
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._add_plan)

        input_row.addWidget(self._input, stretch=1)
        input_row.addWidget(add_btn)
        self.content_layout.addLayout(input_row)

        self._refresh_list()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _add_plan(self):
        title = self._input.text().strip()
        if not title:
            return
        self.app_state["study_plans"].append({"title": title, "lessons": []})
        self._input.clear()
        self._refresh_list()

    def _delete_plan(self, plan: dict):
        self.app_state["study_plans"] = [
            p for p in self.app_state["study_plans"] if p is not plan
        ]
        self._refresh_list()

    def _open_plan(self, plan: dict):
        # Store selected plan in shared state for other pages to reference
        self.app_state["active_study_plan"] = plan

    # ── List rendering ────────────────────────────────────────────────────────

    def _refresh_list(self):
        """Rebuild the card list from app_state."""
        # Remove all cards (keep the stretch at the end)
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        plans = self.app_state.get("study_plans", [])
        self._empty_label.setVisible(len(plans) == 0)

        for plan in plans:
            card = _PlanCard(plan, on_delete=self._delete_plan, on_open=self._open_plan)
            self._list_layout.insertWidget(self._list_layout.count() - 1, card)

    def on_enter(self):
        self._refresh_list()
