"""
settings_panel.py — AI Provider & API Key settings panel.

Lets the user:
  - Choose active provider (Anthropic / OpenAI / Gemini)
  - Enter and save their API key (masked input)
  - Choose the model for each provider
  - See a green/red status indicator per provider
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QVBoxLayout, QWidget, QFrame,
)

from pt_theme import Colors, Fonts, Spacing, Radius
from core.key_store import (
    PROVIDERS, PROVIDER_LABELS, PROVIDER_MODELS,
    save_key, load_key, load_model, load_active_provider,
    save_active_provider, has_key,
)


def _card() -> QFrame:
    f = QFrame()
    f.setStyleSheet(
        f"QFrame {{"
        f"  background: {Colors.SURFACE_MID};"
        f"  border: 1px solid {Colors.BORDER_DEFAULT};"
        f"  border-radius: {Radius.MD}px;"
        f"}}"
    )
    return f


class ProviderCard(QWidget):
    """One card per AI provider with key input, model selector, save button."""

    saved = Signal(str)   # provider name

    def __init__(self, provider: str, parent=None) -> None:
        super().__init__(parent)
        self._provider = provider
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        card = _card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.SM)

        # Header row: label + status dot
        hdr = QHBoxLayout()
        label = QLabel(PROVIDER_LABELS[self._provider])
        label.setFont(Fonts.label())
        label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; border: none;")

        self._status_dot = QLabel("●")
        self._status_dot.setFont(Fonts.label())
        self._status_dot.setStyleSheet(f"color: {Colors.TEXT_PLACEHOLDER}; border: none;")
        self._status_dot.setToolTip("No key saved")

        hdr.addWidget(label)
        hdr.addStretch()
        hdr.addWidget(self._status_dot)
        layout.addLayout(hdr)

        # API key input
        self._key_input = QLineEdit()
        self._key_input.setObjectName("LinkInput")
        self._key_input.setFont(Fonts.body())
        self._key_input.setPlaceholderText("Paste API key here…")
        self._key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._key_input.setFixedHeight(36)

        # Show/hide toggle
        key_row = QHBoxLayout()
        key_row.setSpacing(Spacing.XS)
        self._toggle_btn = QPushButton("Show")
        self._toggle_btn.setObjectName("FilesBtn")
        self._toggle_btn.setFont(Fonts.body())
        self._toggle_btn.setFixedSize(56, 36)
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.clicked.connect(self._toggle_visibility)
        key_row.addWidget(self._key_input)
        key_row.addWidget(self._toggle_btn)
        layout.addLayout(key_row)

        # Model selector
        model_row = QHBoxLayout()
        model_lbl = QLabel("Model:")
        model_lbl.setFont(Fonts.body())
        model_lbl.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; border: none;")
        model_lbl.setFixedWidth(50)

        self._model_combo = QComboBox()
        self._model_combo.setFont(Fonts.body())
        self._model_combo.setStyleSheet(f"""
            QComboBox {{
                background: {Colors.LINK_INPUT_BG};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: {Radius.SM}px;
                padding: 4px 8px;
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{
                background: {Colors.SURFACE_MID};
                color: {Colors.TEXT_PRIMARY};
                selection-background-color: {Colors.SIDEBAR_ACTIVE};
            }}
        """)
        for m in PROVIDER_MODELS[self._provider]:
            self._model_combo.addItem(m)

        model_row.addWidget(model_lbl)
        model_row.addWidget(self._model_combo)
        layout.addLayout(model_row)

        # Save button
        save_btn = QPushButton("Save Key")
        save_btn.setObjectName("SubmitBtn")
        save_btn.setFont(Fonts.label())
        save_btn.setFixedHeight(34)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._on_save)

        self._feedback = QLabel("")
        self._feedback.setFont(Fonts.body())
        self._feedback.setStyleSheet(f"color: {Colors.SUCCESS}; border: none;")

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)
        layout.addWidget(self._feedback)

        root.addWidget(card)

    def _load(self) -> None:
        """Populate fields from stored values."""
        key = load_key(self._provider)
        if key:
            self._key_input.setText(key)
            self._set_status(True)
        model = load_model(self._provider)
        idx = self._model_combo.findText(model)
        if idx >= 0:
            self._model_combo.setCurrentIndex(idx)

    def _toggle_visibility(self) -> None:
        if self._key_input.echoMode() == QLineEdit.EchoMode.Password:
            self._key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self._toggle_btn.setText("Hide")
        else:
            self._key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self._toggle_btn.setText("Show")

    def _on_save(self) -> None:
        key   = self._key_input.text().strip()
        model = self._model_combo.currentText()
        if not key:
            self._feedback.setStyleSheet(f"color: {Colors.ERROR}; border: none;")
            self._feedback.setText("Key cannot be empty.")
            return
        save_key(self._provider, key, model)
        self._set_status(True)
        self._feedback.setStyleSheet(f"color: {Colors.SUCCESS}; border: none;")
        self._feedback.setText("Saved ✓")
        self.saved.emit(self._provider)

    def _set_status(self, active: bool) -> None:
        if active:
            self._status_dot.setStyleSheet(f"color: {Colors.SUCCESS}; border: none;")
            self._status_dot.setToolTip("Key saved")
        else:
            self._status_dot.setStyleSheet(f"color: {Colors.TEXT_PLACEHOLDER}; border: none;")
            self._status_dot.setToolTip("No key saved")

    def get_provider(self) -> str:
        return self._provider


class SettingsPanel(QWidget):
    """
    Full settings panel shown when user clicks the ⚙ Settings nav item.
    Contains:
      - Active provider selector
      - One ProviderCard per supported provider
    """

    provider_changed = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        root.setSpacing(Spacing.LG)

        # Title
        title = QLabel("⚙  AI Settings")
        title.setFont(Fonts.heading())
        root.addWidget(title)

        # Active provider selector
        active_card = _card()
        active_layout = QHBoxLayout(active_card)
        active_layout.setContentsMargins(Spacing.LG, Spacing.MD, Spacing.LG, Spacing.MD)

        active_lbl = QLabel("Active Provider:")
        active_lbl.setFont(Fonts.label())
        active_lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; border: none;")

        self._provider_combo = QComboBox()
        self._provider_combo.setFont(Fonts.label())
        self._provider_combo.setFixedHeight(36)
        self._provider_combo.setStyleSheet(f"""
            QComboBox {{
                background: {Colors.LINK_INPUT_BG};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: {Radius.SM}px;
                padding: 4px 12px;
                min-width: 200px;
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox QAbstractItemView {{
                background: {Colors.SURFACE_MID};
                color: {Colors.TEXT_PRIMARY};
                selection-background-color: {Colors.SIDEBAR_ACTIVE};
            }}
        """)
        for p in PROVIDERS:
            self._provider_combo.addItem(PROVIDER_LABELS[p], p)

        # Set current
        active = load_active_provider()
        for i in range(self._provider_combo.count()):
            if self._provider_combo.itemData(i) == active:
                self._provider_combo.setCurrentIndex(i)

        self._provider_combo.currentIndexChanged.connect(self._on_provider_changed)

        active_layout.addWidget(active_lbl)
        active_layout.addWidget(self._provider_combo)
        active_layout.addStretch()
        root.addWidget(active_card)

        # One card per provider
        for p in PROVIDERS:
            pc = ProviderCard(p)
            pc.saved.connect(self._on_key_saved)
            root.addWidget(pc)

        root.addStretch()

        note = QLabel(
            "Keys are stored locally in Data/keys.json (base64 encoded).\n"
            "Add Data/ to your .gitignore to keep them private."
        )
        note.setFont(Fonts.body())
        note.setStyleSheet(f"color: {Colors.TEXT_PLACEHOLDER}; border: none;")
        note.setWordWrap(True)
        root.addWidget(note)

    def _on_provider_changed(self, index: int) -> None:
        provider = self._provider_combo.itemData(index)
        save_active_provider(provider)
        self.provider_changed.emit(provider)

    def _on_key_saved(self, provider: str) -> None:
        # If no active provider was set yet, auto-select the one just saved
        if not has_key(load_active_provider()):
            save_active_provider(provider)
            for i in range(self._provider_combo.count()):
                if self._provider_combo.itemData(i) == provider:
                    self._provider_combo.setCurrentIndex(i)
                    break
