"""
ask_panel.py — Ask Questions panel matching the UI design.

Layout (matches images 3.png / 4.png):
  Left sub-panel  : NEW QUESTIONS button / SAVED QUESTIONS button (stacked, toggles)
  Right content   : changes based on which toggle is active

  NEW QUESTIONS view:
    Title: ASK QUESTIONS
    Sub:   SELECT FILES TO GENERATE QUESTIONS FROM
    • Select All checkbox
    • File checkboxes (from Data/extracted/)
    → clicking Ask sends API call, saves questionN.json

  SAVED QUESTIONS view:
    Title: SAVED QUESTIONS
    Sub:   SELECT PRE EXISTING QUESTIONS TO ANSWER
    • QUESTION01 / QUESTION02 ... buttons
    → clicking one opens the quiz
"""

from __future__ import annotations
import json
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QFileSystemWatcher
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QFrame, QHBoxLayout,
    QLabel, QPushButton, QRadioButton,
    QScrollArea, QSizePolicy, QStackedWidget,
    QVBoxLayout, QWidget,
)

from pt_theme import Colors, Fonts, Spacing, Radius
from app_config import Config


# ── Helpers ────────────────────────────────────────────────────────────────────

def _divider() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"color: {Colors.BORDER_DEFAULT};")
    return f


def _section_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(Fonts.heading())
    lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
    return lbl


def _section_sub(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(Fonts.body())
    lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
    return lbl


def _question_btn(label: str) -> QPushButton:
    btn = QPushButton(label)
    btn.setFont(Fonts.nav_button())
    btn.setFixedHeight(52)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {Colors.SIDEBAR_BTN_BG};
            color: {Colors.TEXT_PRIMARY};
            border: none;
            border-radius: {Radius.MD}px;
            letter-spacing: 1px;
        }}
        QPushButton:hover {{
            background: {Colors.SIDEBAR_BTN_HOVER};
        }}
    """)
    return btn


# ── Left toggle sub-panel ──────────────────────────────────────────────────────

class TogglePanel(QWidget):
    """NEW QUESTIONS / SAVED QUESTIONS toggle buttons on the left."""

    switched = Signal(int)   # 0 = new, 1 = saved

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedWidth(180)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.SM, Spacing.LG, Spacing.SM, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        self._new_btn = self._make_toggle("NEW QUESTIONS", 0)
        self._saved_btn = self._make_toggle("SAVED QUESTIONS", 1)

        layout.addWidget(self._new_btn)
        layout.addWidget(self._saved_btn)
        layout.addStretch()

        # Default: NEW QUESTIONS active
        self._set_active(0)

    def _make_toggle(self, label: str, idx: int) -> QPushButton:
        btn = QPushButton(label)
        btn.setFont(Fonts.label())
        btn.setFixedHeight(52)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setProperty("idx", idx)
        btn.clicked.connect(lambda: self._set_active(idx))
        return btn

    def _set_active(self, idx: int) -> None:
        active_style = f"""
            QPushButton {{
                background: {Colors.SIDEBAR_ACTIVE};
                color: {Colors.TEXT_PRIMARY};
                border: none;
                border-radius: {Radius.MD}px;
                font-weight: bold;
            }}
        """
        inactive_style = f"""
            QPushButton {{
                background: {Colors.BTN_PRIMARY_BG};
                color: {Colors.TEXT_SECONDARY};
                border: none;
                border-radius: {Radius.MD}px;
            }}
            QPushButton:hover {{
                background: {Colors.BTN_PRIMARY_HOVER};
                color: {Colors.TEXT_PRIMARY};
            }}
        """
        self._new_btn.setStyleSheet(active_style if idx == 0 else inactive_style)
        self._saved_btn.setStyleSheet(active_style if idx == 1 else inactive_style)
        self.switched.emit(idx)


# ── NEW QUESTIONS view ─────────────────────────────────────────────────────────

class NewQuestionsView(QWidget):
    """File checkbox list + Ask button."""

    ask_requested = Signal(dict)   # {stem: text}

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._file_checks: dict[str, QCheckBox] = {}
        self._build_ui()
        self._setup_watcher()
        self._refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        root.setSpacing(Spacing.MD)

        root.addWidget(_section_title("ASK QUESTIONS"))
        root.addWidget(_section_sub("SELECT FILES TO GENERATE QUESTIONS FROM"))
        root.addWidget(_divider())

        # Status
        self._status = QLabel("")
        self._status.setFont(Fonts.body())
        self._status.setStyleSheet(f"color: {Colors.TEXT_ACCENT};")
        self._status.setVisible(False)
        root.addWidget(self._status)

        # Select All
        self._select_all = QCheckBox("select all")
        self._select_all.setFont(Fonts.label())
        self._select_all.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        self._select_all.stateChanged.connect(self._on_select_all)
        root.addWidget(self._select_all)

        # Scrollable file list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._list_widget = QWidget()
        self._list_widget.setStyleSheet("background: transparent;")
        self._list_vbox = QVBoxLayout(self._list_widget)
        self._list_vbox.setContentsMargins(Spacing.SM, 0, 0, 0)
        self._list_vbox.setSpacing(Spacing.SM)
        self._list_vbox.addStretch()
        scroll.setWidget(self._list_widget)
        root.addWidget(scroll, stretch=1)

        # Ask button — pinned to bottom
        self._ask_btn = QPushButton("  Generate Questions")
        self._ask_btn.setObjectName("UploadFab")
        self._ask_btn.setFont(Fonts.upload_button())
        self._ask_btn.setFixedHeight(44)
        self._ask_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._ask_btn.clicked.connect(self.ask)
        root.addWidget(self._ask_btn)

    def _setup_watcher(self) -> None:
        self._watcher = QFileSystemWatcher(self)
        for f in (Config.EXTRACTED_FILE, Config.EXTRACTED_LINK):
            f.mkdir(parents=True, exist_ok=True)
            self._watcher.addPath(str(f))
        self._watcher.directoryChanged.connect(self._refresh)

    def _refresh(self) -> None:
        # Clear
        for i in reversed(range(self._list_vbox.count() - 1)):
            item = self._list_vbox.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
                self._list_vbox.removeItem(item)
        self._file_checks.clear()

        all_files: list[Path] = []
        for folder in (Config.EXTRACTED_FILE, Config.EXTRACTED_LINK):
            if folder.exists():
                all_files.extend(
                    sorted(folder.glob("*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
                )

        for fp in all_files:
            cb = QCheckBox(f"  {fp.stem}")
            cb.setFont(Fonts.body())
            cb.setStyleSheet(f"""
                QCheckBox {{
                    color: {Colors.TEXT_PRIMARY};
                    padding: {Spacing.XS}px;
                }}
                QCheckBox::indicator {{
                    width: 16px; height: 16px;
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
            self._list_vbox.insertWidget(self._list_vbox.count() - 1, cb)

    def _on_select_all(self, state: int) -> None:
        checked = state == Qt.CheckState.Checked.value
        for cb in self._file_checks.values():
            cb.setChecked(checked)

    def ask(self) -> None:
        selected = {p: cb for p, cb in self._file_checks.items() if cb.isChecked()}
        if not selected:
            self.set_status("Please select at least one file.")
            return
        source_texts: dict[str, str] = {}
        for path_str in selected:
            fp = Path(path_str)
            try:
                source_texts[fp.stem] = fp.read_text(encoding="utf-8")
            except Exception:
                pass
        self._ask_btn.setEnabled(False)
        self.set_status(f"Generating questions for {len(source_texts)} file(s)…")
        self.ask_requested.emit(source_texts)

    def set_status(self, text: str) -> None:
        self._status.setText(text)
        self._status.setVisible(bool(text))
        # Re-enable button when generation is complete or errored
        if text and not text.startswith("Generating"):
            self._ask_btn.setEnabled(True)


# ── SAVED QUESTIONS view ───────────────────────────────────────────────────────

class SavedQuestionsView(QWidget):
    """List of QUESTION01, QUESTION02 ... buttons."""

    open_quiz = Signal(str)   # path to JSON

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()
        self._setup_watcher()
        self._refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        root.setSpacing(Spacing.MD)

        root.addWidget(_section_title("SAVED QUESTIONS"))
        root.addWidget(_section_sub("SELECT PRE EXISTING QUESTIONS TO ANSWER"))
        root.addWidget(_divider())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._list_widget = QWidget()
        self._list_widget.setStyleSheet("background: transparent;")
        self._list_vbox = QVBoxLayout(self._list_widget)
        self._list_vbox.setContentsMargins(0, 0, 0, 0)
        self._list_vbox.setSpacing(Spacing.SM)
        self._list_vbox.addStretch()
        scroll.setWidget(self._list_widget)
        root.addWidget(scroll, stretch=1)

    def _setup_watcher(self) -> None:
        self._watcher = QFileSystemWatcher(self)
        Config.QUESTIONS_DIR.mkdir(parents=True, exist_ok=True)
        self._watcher.addPath(str(Config.QUESTIONS_DIR))
        self._watcher.directoryChanged.connect(self._refresh)

    def refresh(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        # Clear
        for i in reversed(range(self._list_vbox.count() - 1)):
            item = self._list_vbox.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
                self._list_vbox.removeItem(item)

        if not Config.QUESTIONS_DIR.exists():
            return

        files = sorted(
            Config.QUESTIONS_DIR.glob("question*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        for f in files:
            # Label as QUESTION01, QUESTION02 etc. (zero-padded)
            num = ''.join(filter(str.isdigit, f.stem))
            label = f"QUESTION{num.zfill(2)}"
            btn = _question_btn(label)
            btn.setProperty("q_path", str(f))
            btn.clicked.connect(lambda _, p=str(f): self.open_quiz.emit(p))
            self._list_vbox.insertWidget(self._list_vbox.count() - 1, btn)


# ── QUIZ view ──────────────────────────────────────────────────────────────────

class QuizView(QWidget):
    """Radio-button quiz with Submit + result overlay."""

    go_back = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._questions: list[dict] = []
        self._question_file: Path | None = None
        self._option_groups: dict[int, QButtonGroup] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._stack = QStackedWidget()

        # ── Quiz page ──────────────────────────────────────────────────────────
        quiz_page = QWidget()
        ql = QVBoxLayout(quiz_page)
        ql.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        ql.setSpacing(Spacing.MD)

        hdr = QHBoxLayout()
        self._quiz_title = QLabel("Quiz")
        self._quiz_title.setFont(Fonts.heading())

        back_btn = QPushButton("← Back")
        back_btn.setObjectName("FilesBtn")
        back_btn.setFont(Fonts.label())
        back_btn.setFixedHeight(32)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.go_back)

        hdr.addWidget(self._quiz_title)
        hdr.addStretch()
        hdr.addWidget(back_btn)
        ql.addLayout(hdr)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._q_container = QWidget()
        self._q_container.setStyleSheet("background: transparent;")
        self._q_vbox = QVBoxLayout(self._q_container)
        self._q_vbox.setContentsMargins(0, 0, 0, 0)
        self._q_vbox.setSpacing(Spacing.MD)
        self._q_vbox.addStretch()
        scroll.setWidget(self._q_container)
        ql.addWidget(scroll)

        submit_row = QHBoxLayout()
        submit_btn = QPushButton("Submit Answers")
        submit_btn.setObjectName("SubmitBtn")
        submit_btn.setFont(Fonts.upload_button())
        submit_btn.setFixedHeight(44)
        submit_btn.setMinimumWidth(160)
        submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        submit_btn.clicked.connect(self._on_submit)
        submit_row.addStretch()
        submit_row.addWidget(submit_btn)
        ql.addLayout(submit_row)

        # ── Result page ────────────────────────────────────────────────────────
        self._result_page = ResultView()
        self._result_page.back_to_quiz.connect(lambda: self._stack.setCurrentIndex(0))
        self._result_page.go_to_list.connect(self.go_back)

        self._stack.addWidget(quiz_page)
        self._stack.addWidget(self._result_page)
        root.addWidget(self._stack)

    def load(self, question_file: str) -> None:
        self._question_file = Path(question_file)
        data = json.loads(self._question_file.read_text(encoding="utf-8"))
        self._questions = data.get("questions", [])
        num = ''.join(filter(str.isdigit, self._question_file.stem))
        self._quiz_title.setText(f"QUESTION{num.zfill(2)}")
        self._render_questions()
        self._stack.setCurrentIndex(0)

    def _render_questions(self) -> None:
        while self._q_vbox.count() > 1:
            item = self._q_vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._option_groups.clear()
        for q in self._questions:
            self._q_vbox.insertWidget(self._q_vbox.count() - 1, self._make_card(q))

    def _make_card(self, q: dict) -> QWidget:
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: {Colors.SURFACE_MID};"
            f"border: 1px solid {Colors.BORDER_DEFAULT};"
            f"border-radius: {Radius.MD}px; }}"
        )
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(Spacing.LG, Spacing.MD, Spacing.LG, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        q_lbl = QLabel(f"Q{q['id']}.  {q['question']}")
        q_lbl.setFont(Fonts.label())
        q_lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; border: none;")
        q_lbl.setWordWrap(True)
        layout.addWidget(q_lbl)
        layout.addWidget(_divider())

        group = QButtonGroup(card)
        group.setExclusive(True)
        for opt in q.get("options", []):
            rb = QRadioButton(opt)
            rb.setFont(Fonts.body())
            rb.setStyleSheet(f"""
                QRadioButton {{
                    color: {Colors.TEXT_PRIMARY};
                    padding: {Spacing.XS}px {Spacing.SM}px;
                    border: none;
                    border-radius: {Radius.XS}px;
                }}
                QRadioButton:hover {{ background: {Colors.SURFACE_LIGHT}; }}
                QRadioButton::indicator {{
                    width: 14px; height: 14px;
                    border: 2px solid {Colors.BORDER_DEFAULT};
                    border-radius: 7px; background: transparent;
                }}
                QRadioButton::indicator:checked {{
                    background: {Colors.ICON_ACTIVE};
                    border-color: {Colors.ICON_ACTIVE};
                }}
            """)
            group.addButton(rb)
            layout.addWidget(rb)

        self._option_groups[q["id"]] = group
        return card

    def _on_submit(self) -> None:
        user_answers: dict[int, str] = {}
        for qid, group in self._option_groups.items():
            checked = group.checkedButton()
            if checked:
                user_answers[qid] = checked.text().strip()[0].upper()
        try:
            from core.qa_engine import QAEngine
            result_path = QAEngine().score_attempt(self._question_file, user_answers)
            result_data = json.loads(result_path.read_text(encoding="utf-8"))
            self._result_page.show_result(result_data, result_path)
            self._stack.setCurrentIndex(1)
        except Exception as exc:
            self._quiz_title.setText(f"Error: {exc}")


# ── Result view ────────────────────────────────────────────────────────────────

class ResultView(QWidget):
    back_to_quiz = Signal()
    go_to_list   = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        root.setSpacing(Spacing.MD)

        self._score_label = QLabel("")
        self._score_label.setFont(Fonts.heading())
        self._score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._score_label.setStyleSheet(
            f"color: {Colors.TEXT_PRIMARY};"
            f"background: {Colors.SIDEBAR_BTN_BG};"
            f"border-radius: {Radius.MD}px;"
            f"padding: {Spacing.LG}px;"
        )

        self._save_label = QLabel("")
        self._save_label.setFont(Fonts.body())
        self._save_label.setStyleSheet(f"color: {Colors.TEXT_ACCENT};")
        self._save_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._save_label.setWordWrap(True)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self._breakdown = QWidget()
        self._breakdown.setStyleSheet("background: transparent;")
        self._bvbox = QVBoxLayout(self._breakdown)
        self._bvbox.setSpacing(Spacing.SM)
        self._bvbox.addStretch()
        scroll.setWidget(self._breakdown)

        btn_row = QHBoxLayout()
        retry = QPushButton("← Retry")
        retry.setObjectName("FilesBtn")
        retry.setFont(Fonts.label())
        retry.setFixedHeight(36)
        retry.setCursor(Qt.CursorShape.PointingHandCursor)
        retry.clicked.connect(self.back_to_quiz)

        back = QPushButton("Question Sets")
        back.setObjectName("SubmitBtn")
        back.setFont(Fonts.label())
        back.setFixedHeight(36)
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.clicked.connect(self.go_to_list)

        btn_row.addWidget(retry)
        btn_row.addStretch()
        btn_row.addWidget(back)

        root.addWidget(self._score_label)
        root.addWidget(self._save_label)
        root.addWidget(scroll)
        root.addLayout(btn_row)

    def show_result(self, data: dict, result_path: Path) -> None:
        score = data["score"]
        total = data["total"]
        pct   = int(score / total * 100) if total else 0
        self._score_label.setText(f"🎯  {score} / {total}  correct   ({pct}%)")
        self._save_label.setText(f"Result saved → {result_path}")

        while self._bvbox.count() > 1:
            item = self._bvbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for ans in data.get("answers", []):
            card = QFrame()
            card.setStyleSheet(
                f"QFrame {{ background: {Colors.SURFACE_MID};"
                f"border: 1px solid {Colors.BORDER_DEFAULT};"
                f"border-radius: {Radius.MD}px; }}"
            )
            cl = QVBoxLayout(card)
            cl.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
            cl.setSpacing(Spacing.XS)

            color = Colors.SUCCESS if ans["is_correct"] else Colors.ERROR
            icon  = "✅" if ans["is_correct"] else "❌"

            q_lbl = QLabel(f"{icon}  Q{ans['id']}.  {ans['question']}")
            q_lbl.setFont(Fonts.label())
            q_lbl.setStyleSheet(f"color: {color}; border: none;")
            q_lbl.setWordWrap(True)

            a_lbl = QLabel(
                f"Your answer: <b>{ans['selected'] or '—'}</b>   "
                f"Correct: <b>{ans['correct']}</b>"
            )
            a_lbl.setFont(Fonts.body())
            a_lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; border: none;")

            cl.addWidget(q_lbl)
            cl.addWidget(a_lbl)
            self._bvbox.insertWidget(self._bvbox.count() - 1, card)


# ── Main AskPanel ──────────────────────────────────────────────────────────────

class AskPanel(QWidget):
    """
    Three-column layout:
      [sidebar nav] | [NEW QUESTIONS / SAVED QUESTIONS toggle] | [content]
    """

    question_asked = Signal(str)   # kept for compat

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Left toggle panel
        self._toggle = TogglePanel()
        self._toggle.switched.connect(self._on_toggle)
        root.addWidget(self._toggle)

        # Right content stack
        self._stack = QStackedWidget()

        self._new_view   = NewQuestionsView()
        self._saved_view = SavedQuestionsView()
        self._quiz_view  = QuizView()

        self._stack.addWidget(self._new_view)    # 0
        self._stack.addWidget(self._saved_view)  # 1
        self._stack.addWidget(self._quiz_view)   # 2

        root.addWidget(self._stack, stretch=1)

        # Wiring
        self._new_view.ask_requested.connect(self._on_ask_requested)
        self._saved_view.open_quiz.connect(self._open_quiz)
        self._quiz_view.go_back.connect(self._on_quiz_back)

    def _on_toggle(self, idx: int) -> None:
        # 0 = new, 1 = saved — don't override if quiz is open
        if self._stack.currentIndex() != 2:
            self._stack.setCurrentIndex(idx)
        if idx == 1:
            self._saved_view.refresh()

    def _on_ask_requested(self, source_texts: dict) -> None:
        from core.workers import QuestionGenWorker
        self._gen_worker = QuestionGenWorker(source_texts, parent=self)
        self._gen_worker.progress.connect(self._new_view.set_status)
        self._gen_worker.result.connect(self._on_questions_generated)
        self._gen_worker.error.connect(
            lambda e: self._new_view.set_status(f"Error: {e}")
        )
        self._gen_worker.start()

    def _on_questions_generated(self, path: str) -> None:
        self._new_view.set_status(f"Saved → {path}")
        self._saved_view.refresh()

    def _open_quiz(self, path: str) -> None:
        self._quiz_view.load(path)
        self._stack.setCurrentIndex(2)

    def _on_quiz_back(self) -> None:
        self._stack.setCurrentIndex(1)
        self._toggle._set_active(1)

    # compat stubs
    def append_answer(self, question: str, answer: str) -> None:
        pass

    def clear(self) -> None:
        pass
