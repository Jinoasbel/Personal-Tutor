"""
audio_panel.py — Audio lesson panel.

Fixes & additions:
  - QAudioOutput uses QMediaDevices.defaultAudioOutput() → works with headphones
  - Voice selector dropdown in left pane
  - On launch: if Data/audio/ has lessons, show ReadyView immediately
  - Single audio file output (WAV temp cleaned up in audio_generator)
"""

from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QTimer, QUrl, QFileSystemWatcher
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaDevices
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton,
    QScrollArea, QSlider, QStackedWidget,
    QTextEdit, QVBoxLayout, QWidget,
)

from pt_theme import Colors, Fonts, Spacing, Radius
from app_config import Config
from core.audio_generator import VOICES, DEFAULT_VOICE


# ── Spinner ────────────────────────────────────────────────────────────────────

class SpinnerRing(QWidget):
    def __init__(self, size: int = 80, parent=None) -> None:
        super().__init__(parent)
        self._angle = 0
        self._size  = size
        self.setFixedSize(size, size)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def start(self) -> None:  self._timer.start(30)
    def stop(self)  -> None:  self._timer.stop()

    def _tick(self) -> None:
        self._angle = (self._angle + 8) % 360
        self.update()

    def paintEvent(self, _) -> None:
        p  = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx = cy = self._size // 2
        r  = self._size // 2 - 8
        pen = QPen(QColor(Colors.BORDER_DEFAULT), 6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawEllipse(cx - r, cy - r, r * 2, r * 2)
        pen.setColor(QColor(Colors.ICON_ACTIVE))
        p.setPen(pen)
        p.drawArc(cx - r, cy - r, r * 2, r * 2,
                  (90 - self._angle) * 16, -120 * 16)
        p.end()


# ── Sub-views ──────────────────────────────────────────────────────────────────

class IdleView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lv = QVBoxLayout(self)
        lv.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel("Select files and click\nGenerate Lesson to begin")
        lbl.setFont(Fonts.body())
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color: {Colors.TEXT_PLACEHOLDER};")
        lbl.setWordWrap(True)
        lv.addWidget(lbl)


class BusyView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lv = QVBoxLayout(self)
        lv.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lv.setSpacing(Spacing.LG)

        self._spinner = SpinnerRing(80, self)
        self._status  = QLabel("Starting…")
        self._status.setFont(Fonts.body())
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setWordWrap(True)
        self._status.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")

        hint = QLabel("This may take several minutes")
        hint.setFont(Fonts.body())
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet(f"color: {Colors.TEXT_PLACEHOLDER}; font-size: 11px;")

        spin_row = QHBoxLayout()
        spin_row.addStretch()
        spin_row.addWidget(self._spinner)
        spin_row.addStretch()

        lv.addLayout(spin_row)
        lv.addWidget(self._status)
        lv.addWidget(hint)

    def set_status(self, text: str) -> None:
        self._status.setText(text.split("\n")[0])

    def start(self) -> None: self._spinner.start()
    def stop(self)  -> None: self._spinner.stop()


class ReadyView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_path = ""
        self._build_ui()
        self._setup_player()
        self._setup_watcher()
        # Load existing lessons on startup
        self.refresh_lessons()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(Spacing.MD)

        # Script viewer
        sh = QHBoxLayout()
        sh.addWidget(self._make_label("Lesson Script", Fonts.label(), Colors.TEXT_SECONDARY))
        sh.addStretch()
        self._script_src = QLabel("")
        self._script_src.setFont(Fonts.body())
        self._script_src.setStyleSheet(f"color:{Colors.TEXT_PLACEHOLDER};font-size:10px;")
        sh.addWidget(self._script_src)
        root.addLayout(sh)

        self._script_area = QTextEdit()
        self._script_area.setReadOnly(True)
        self._script_area.setFont(Fonts.body())
        self._script_area.setPlaceholderText("Lesson script will appear here…")
        self._script_area.setStyleSheet(f"""
            QTextEdit {{
                background:{Colors.SURFACE_MID}; color:{Colors.TEXT_PRIMARY};
                border:1px solid {Colors.BORDER_DEFAULT};
                border-radius:{Radius.MD}px; padding:{Spacing.MD}px;
            }}""")
        root.addWidget(self._script_area, stretch=2)

        # Saved lessons list
        lh = QHBoxLayout()
        lh.addWidget(self._make_label("Saved Lessons", Fonts.label(), Colors.TEXT_SECONDARY))
        lh.addStretch()
        ref = QPushButton("↻")
        ref.setObjectName("FilesBtn")
        ref.setFixedSize(28, 28)
        ref.setCursor(Qt.CursorShape.PointingHandCursor)
        ref.clicked.connect(self.refresh_lessons)
        lh.addWidget(ref)
        root.addLayout(lh)

        self._lesson_list = QListWidget()
        self._lesson_list.setFont(Fonts.body())
        self._lesson_list.setMaximumHeight(120)
        self._lesson_list.setStyleSheet(f"""
            QListWidget {{
                background:{Colors.SURFACE_MID};
                border:1px solid {Colors.BORDER_DEFAULT};
                border-radius:{Radius.SM}px; padding:{Spacing.XS}px;
            }}
            QListWidget::item {{
                padding:{Spacing.SM}px {Spacing.MD}px;
                border-radius:{Radius.XS}px; color:{Colors.TEXT_PRIMARY};
            }}
            QListWidget::item:hover  {{ background:{Colors.SURFACE_LIGHT}; }}
            QListWidget::item:selected {{
                background:{Colors.SIDEBAR_ACTIVE};
                border-left:3px solid {Colors.ICON_ACTIVE};
            }}""")
        self._lesson_list.currentItemChanged.connect(self._on_lesson_selected)
        root.addWidget(self._lesson_list)

        # ── Player card ────────────────────────────────────────────────────────
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                background:{Colors.SURFACE_MID};
                border:1px solid {Colors.BORDER_DEFAULT};
                border-radius:{Radius.MD}px;
            }}""")
        pv = QVBoxLayout(card)
        pv.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        pv.setSpacing(Spacing.XS)

        self._track_lbl = QLabel("No lesson loaded")
        self._track_lbl.setFont(Fonts.label())
        self._track_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._track_lbl.setStyleSheet(
            f"color:{Colors.TEXT_SECONDARY}; background:transparent; border:none;"
        )
        pv.addWidget(self._track_lbl)

        slider_ss = f"""
            QSlider::groove:horizontal {{
                background:{Colors.BORDER_DEFAULT}; height:4px; border-radius:2px;
            }}
            QSlider::handle:horizontal {{
                background:{Colors.ICON_ACTIVE};
                width:12px; height:12px; border-radius:6px; margin:-4px 0;
            }}
            QSlider::sub-page:horizontal {{
                background:{Colors.ICON_ACTIVE}; border-radius:2px;
            }}"""

        self._seek = QSlider(Qt.Orientation.Horizontal)
        self._seek.setRange(0, 1000)
        self._seek.setStyleSheet(slider_ss)
        self._seek.sliderMoved.connect(self._on_seek)
        pv.addWidget(self._seek)

        ctrl = QHBoxLayout()
        ctrl.setSpacing(Spacing.SM)

        self._time_lbl = QLabel("0:00 / 0:00")
        self._time_lbl.setFont(Fonts.body())
        self._time_lbl.setStyleSheet(
            f"color:{Colors.TEXT_PLACEHOLDER}; font-size:10px;"
            f" background:transparent; border:none;"
        )

        self._play_btn = QPushButton("▶")
        self._play_btn.setFixedSize(40, 40)
        self._play_btn.setStyleSheet(f"""
            QPushButton {{
                background:{Colors.ICON_ACTIVE}; color:white;
                border-radius:20px; font-size:14px; border:none;
            }}
            QPushButton:hover {{ background:{Colors.BTN_UPLOAD_HOVER}; }}""")
        self._play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._play_btn.clicked.connect(self._toggle_play)

        vol_lbl = QLabel("🔊")
        vol_lbl.setStyleSheet("background:transparent; border:none; font-size:14px;")
        self._vol = QSlider(Qt.Orientation.Horizontal)
        self._vol.setRange(0, 100)
        self._vol.setValue(80)
        self._vol.setFixedWidth(80)
        self._vol.setStyleSheet(slider_ss)
        self._vol.valueChanged.connect(self._on_volume)

        ctrl.addWidget(self._time_lbl)
        ctrl.addStretch()
        ctrl.addWidget(self._play_btn)
        ctrl.addStretch()
        ctrl.addWidget(vol_lbl)
        ctrl.addWidget(self._vol)
        pv.addLayout(ctrl)

        root.addWidget(card)

    def _make_label(self, text, font, color) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(font)
        lbl.setStyleSheet(f"color:{color};")
        return lbl

    # ── Player setup ───────────────────────────────────────────────────────────

    def _setup_player(self) -> None:
        self._player = QMediaPlayer(self)

        # Use system default audio output — works for headphones too
        default_device = QMediaDevices.defaultAudioOutput()
        self._audio_out = QAudioOutput(default_device, self)
        self._audio_out.setVolume(0.8)
        self._player.setAudioOutput(self._audio_out)

        self._player.playbackStateChanged.connect(self._on_state_changed)
        self._player.positionChanged.connect(self._on_pos_changed)
        self._player.durationChanged.connect(self._on_dur_changed)

        self._seek_timer = QTimer(self)
        self._seek_timer.setInterval(400)
        self._seek_timer.timeout.connect(self._sync_seek)
        self._seek_timer.start()

    def _setup_watcher(self) -> None:
        self._watcher = QFileSystemWatcher(self)
        Config.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        self._watcher.addPath(str(Config.AUDIO_DIR.resolve()))
        self._watcher.directoryChanged.connect(lambda _: self.refresh_lessons())

    # ── Lessons list ───────────────────────────────────────────────────────────

    def refresh_lessons(self) -> None:
        current_path = self._current_path
        self._lesson_list.clear()
        if not Config.AUDIO_DIR.exists():
            return
        files = sorted(
            list(Config.AUDIO_DIR.glob("*_lesson*.wav")) +
            list(Config.AUDIO_DIR.glob("*_lesson*.mp3")),
            key=lambda p: p.stat().st_mtime, reverse=True,
        )
        for f in files:
            item = QListWidgetItem(f"🎵  {f.stem}")
            item.setData(Qt.ItemDataRole.UserRole, str(f))
            self._lesson_list.addItem(item)

        # Re-select previously selected item if still present
        if current_path:
            for i in range(self._lesson_list.count()):
                if self._lesson_list.item(i).data(Qt.ItemDataRole.UserRole) == current_path:
                    self._lesson_list.setCurrentRow(i)
                    return

    def _on_lesson_selected(self, current, _prev) -> None:
        if not current:
            return
        self.load_audio(current.data(Qt.ItemDataRole.UserRole))

    # ── Public loaders ─────────────────────────────────────────────────────────

    def load_audio(self, path: str) -> None:
        self._current_path = path
        self._player.setSource(QUrl.fromLocalFile(path))
        self._track_lbl.setText(Path(path).stem)
        self._play_btn.setText("▶")

    def load_script(self, path: str) -> None:
        fp = Path(path)
        try:
            self._script_area.setPlainText(fp.read_text(encoding="utf-8"))
            self._script_src.setText(fp.name)
        except Exception as e:
            self._script_area.setPlainText(f"[Could not read script: {e}]")

    def select_newest(self) -> None:
        self.refresh_lessons()
        if self._lesson_list.count() > 0:
            self._lesson_list.setCurrentRow(0)

    def has_lessons(self) -> bool:
        if not Config.AUDIO_DIR.exists():
            return False
        return bool(
            list(Config.AUDIO_DIR.glob("*_lesson*.wav")) +
            list(Config.AUDIO_DIR.glob("*_lesson*.mp3"))
        )

    # ── Player controls ────────────────────────────────────────────────────────

    def _toggle_play(self) -> None:
        if not self._current_path:
            return
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def _on_state_changed(self, state) -> None:
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        self._play_btn.setText("⏸" if playing else "▶")

    def _on_seek(self, value: int) -> None:
        dur = self._player.duration()
        if dur > 0:
            self._player.setPosition(int(value / 1000 * dur))

    def _on_pos_changed(self, pos: int) -> None:
        self._update_time(pos, self._player.duration())

    def _on_dur_changed(self, dur: int) -> None:
        self._update_time(self._player.position(), dur)

    def _sync_seek(self) -> None:
        dur = self._player.duration()
        if dur > 0:
            self._seek.blockSignals(True)
            self._seek.setValue(int(self._player.position() / dur * 1000))
            self._seek.blockSignals(False)

    def _update_time(self, pos: int, dur: int) -> None:
        def fmt(ms):
            s = max(ms, 0) // 1000
            return f"{s // 60}:{s % 60:02d}"
        self._time_lbl.setText(f"{fmt(pos)} / {fmt(dur)}")

    def _on_volume(self, value: int) -> None:
        self._audio_out.setVolume(value / 100.0)



# ── Voice Selector Widget ──────────────────────────────────────────────────────

SAMPLES_DIR = (
    __import__('pathlib').Path(__file__).parent.parent / "assets" / "voice_samples"
)


class VoicePopup(QWidget):
    """
    Floating popup window containing voice rows with play buttons.
    Opens below the VoiceSelector button, closes on outside click.
    """

    voice_chosen = Signal(str)   # voice_key

    def __init__(self, parent=None) -> None:
        super().__init__(parent, Qt.WindowType.Popup)
        self.setStyleSheet(f"""
            QWidget {{
                background: {Colors.SURFACE_MID};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: {Radius.MD}px;
            }}
        """)
        self._rows: dict[str, "_VoiceRow"] = {}
        self._current_player: QMediaPlayer | None = None
        self._current_audio:  QAudioOutput | None = None
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        root.setSpacing(2)
        self.setMinimumWidth(260)

        for key, display in VOICES.items():
            row = _VoiceRow(key, display, self)
            row.selected.connect(self._on_selected)
            row.play_clicked.connect(self._on_play)
            self._rows[key] = row
            root.addWidget(row)

    def _on_selected(self, voice_key: str) -> None:
        for k, r in self._rows.items():
            r.set_checked(k == voice_key)
        self._stop_current()
        self.voice_chosen.emit(voice_key)
        self.hide()

    def _on_play(self, voice_key: str) -> None:
        """Play or stop the sample for voice_key."""
        # If same voice is playing, stop it
        row = self._rows.get(voice_key)
        if not row:
            return

        if (self._current_player and
                self._current_player.playbackState() ==
                QMediaPlayer.PlaybackState.PlayingState):
            # Stop whatever is playing
            prev_key = getattr(self, "_playing_key", None)
            self._stop_current()
            if prev_key == voice_key:
                return   # toggled off

        # Find sample file — WAV preferred (MP3 may be corrupt)
        sample = SAMPLES_DIR / f"{voice_key}.wav"
        if not sample.exists():
            sample = SAMPLES_DIR / f"{voice_key}.mp3"
        if not sample.exists():
            return

        # Create fresh player — store on self to prevent GC
        self._current_player = QMediaPlayer(self)
        self._current_audio  = QAudioOutput(
            QMediaDevices.defaultAudioOutput(), self
        )
        self._current_audio.setVolume(0.9)
        self._current_player.setAudioOutput(self._current_audio)
        self._playing_key = voice_key

        def on_state(state, vk=voice_key):
            playing = state == QMediaPlayer.PlaybackState.PlayingState
            if vk in self._rows:
                self._rows[vk].set_play_icon("⏹" if playing else "▶")
            if not playing:
                self._playing_key = None

        self._current_player.playbackStateChanged.connect(on_state)
        self._current_player.setSource(QUrl.fromLocalFile(str(sample)))
        self._current_player.play()
        row.set_play_icon("⏹")

    def _stop_current(self) -> None:
        if self._current_player:
            self._current_player.stop()
        key = getattr(self, "_playing_key", None)
        if key and key in self._rows:
            self._rows[key].set_play_icon("▶")
        self._playing_key = None

    def set_checked(self, voice_key: str) -> None:
        for k, r in self._rows.items():
            r.set_checked(k == voice_key)

    def enable_preview(self, voice_key: str) -> None:
        if voice_key in self._rows:
            self._rows[voice_key].enable_play()

    def stop_all(self) -> None:
        self._stop_current()


class _VoiceRow(QWidget):
    """Row inside VoicePopup: radio dot + name + ▶ play button."""

    selected    = Signal(str)
    play_clicked = Signal(str)

    def __init__(self, voice_key: str, display: str, parent=None) -> None:
        super().__init__(parent)
        self._key = voice_key
        self.setStyleSheet("background: transparent; border: none;")
        self.setFixedHeight(34)

        row = QHBoxLayout(self)
        row.setContentsMargins(Spacing.XS, 0, Spacing.XS, 0)
        row.setSpacing(Spacing.SM)

        self._dot = QPushButton()
        self._dot.setCheckable(True)
        self._dot.setFixedSize(14, 14)
        self._dot.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 2px solid {Colors.BORDER_DEFAULT};
                border-radius: 7px;
            }}
            QPushButton:checked {{
                background: {Colors.ICON_ACTIVE};
                border-color: {Colors.ICON_ACTIVE};
            }}
        """)
        self._dot.clicked.connect(lambda: self.selected.emit(self._key))

        self._lbl = QLabel(display)
        self._lbl.setFont(Fonts.body())
        self._lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; border: none;")
        from PySide6.QtWidgets import QSizePolicy as SP
        self._lbl.setSizePolicy(SP.Policy.Expanding, SP.Policy.Preferred)

        self._play_btn = QPushButton("▶")
        self._play_btn.setFixedSize(24, 24)
        self._play_btn.setEnabled(False)
        self._play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._play_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Colors.TEXT_PLACEHOLDER};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: 12px;
                font-size: 9px;
            }}
            QPushButton:enabled {{
                color: {Colors.ICON_ACTIVE};
                border-color: {Colors.ICON_ACTIVE};
            }}
            QPushButton:enabled:hover {{
                background: {Colors.SIDEBAR_ACTIVE};
            }}
        """)
        self._play_btn.clicked.connect(lambda: self.play_clicked.emit(self._key))

        row.addWidget(self._dot)
        row.addWidget(self._lbl)
        row.addStretch()
        row.addWidget(self._play_btn)

    def set_checked(self, v: bool) -> None:
        self._dot.setChecked(v)

    def enable_play(self) -> None:
        self._play_btn.setEnabled(True)

    def set_play_icon(self, icon: str) -> None:
        self._play_btn.setText(icon)


class VoiceSelector(QWidget):
    """
    Dropdown-style voice picker.
    Shows selected voice name + chevron button.
    Clicking opens VoicePopup below it.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._current = DEFAULT_VOICE
        self._popup   = VoicePopup()
        self._popup.voice_chosen.connect(self._on_chosen)
        self._build()
        self._popup.set_checked(DEFAULT_VOICE)

    def _build(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._btn = QPushButton(VOICES.get(DEFAULT_VOICE, DEFAULT_VOICE) + "  ▾")
        self._btn.setFont(Fonts.body())
        self._btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.SURFACE_MID};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: {Radius.SM}px;
                padding: {Spacing.XS}px {Spacing.SM}px;
                text-align: left;
            }}
            QPushButton:hover {{
                border-color: {Colors.ICON_ACTIVE};
            }}
        """)
        self._btn.clicked.connect(self._open_popup)
        root.addWidget(self._btn)

    def _open_popup(self) -> None:
        self._popup.stop_all()
        # Position popup below the button
        btn_global = self._btn.mapToGlobal(self._btn.rect().bottomLeft())
        self._popup.setFixedWidth(max(self._btn.width(), 260))
        self._popup.move(btn_global)
        self._popup.show()

    def _on_chosen(self, voice_key: str) -> None:
        self._current = voice_key
        self._btn.setText(VOICES.get(voice_key, voice_key) + "  ▾")

    def selected_voice(self) -> str:
        return self._current

    def on_sample_ready(self, voice_key: str) -> None:
        self._popup.enable_preview(voice_key)



# ── Main Audio Panel ───────────────────────────────────────────────────────────

class AudioPanel(QWidget):

    lesson_requested = Signal(dict)   # {stem: text}
    audio_requested  = Signal()       # legacy compatibility

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._file_checks: dict[str, QCheckBox] = {}
        self._build_ui()
        self._setup_file_watcher()
        self._refresh_files()
        # If lessons already exist from previous runs, show ReadyView immediately
        if self._ready.has_lessons():
            self._ready.select_newest()
            self._stack.setCurrentIndex(2)

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Left pane ──────────────────────────────────────────────────────────
        left = QWidget()
        left.setMinimumWidth(220)
        left.setMaximumWidth(300)
        left.setStyleSheet(
            f"background:{Colors.SURFACE_MID};"
            f"border-right:1px solid {Colors.BORDER_DEFAULT};"
        )
        lv = QVBoxLayout(left)
        lv.setContentsMargins(Spacing.MD, Spacing.XL, Spacing.MD, Spacing.XL)
        lv.setSpacing(Spacing.SM)

        title = QLabel("AUDIO LESSON")
        title.setFont(Fonts.heading())
        title.setStyleSheet(f"color:{Colors.TEXT_PRIMARY};")
        lv.addWidget(title)

        sub = QLabel("SELECT FILES FOR LESSON")
        sub.setFont(Fonts.body())
        sub.setStyleSheet(f"color:{Colors.TEXT_SECONDARY};")
        lv.addWidget(sub)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color:{Colors.BORDER_DEFAULT};")
        lv.addWidget(line)

        # Status
        self._status_lbl = QLabel("")
        self._status_lbl.setFont(Fonts.body())
        self._status_lbl.setStyleSheet(f"color:{Colors.TEXT_ACCENT};")
        self._status_lbl.setFixedHeight(20)
        self._status_lbl.setWordWrap(False)
        self._status_lbl.setVisible(False)
        lv.addWidget(self._status_lbl)

        # Voice selector
        voice_lbl = QLabel("Voice")
        voice_lbl.setFont(Fonts.label())
        voice_lbl.setStyleSheet(f"color:{Colors.TEXT_SECONDARY};")
        lv.addWidget(voice_lbl)

        self._voice_selector = VoiceSelector(self)
        lv.addWidget(self._voice_selector)

        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setStyleSheet(f"color:{Colors.BORDER_DEFAULT};")
        lv.addWidget(line2)

        # Select All
        self._select_all = QCheckBox("  Select All")
        self._select_all.setFont(Fonts.label())
        self._select_all.setStyleSheet(f"color:{Colors.TEXT_PRIMARY};")
        self._select_all.stateChanged.connect(self._on_select_all)
        lv.addWidget(self._select_all)

        # Scrollable file checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border:none; background:transparent; }")
        self._cb_container = QWidget()
        self._cb_container.setStyleSheet("background:transparent;")
        self._cb_vbox = QVBoxLayout(self._cb_container)
        self._cb_vbox.setContentsMargins(Spacing.XS, 0, 0, 0)
        self._cb_vbox.setSpacing(Spacing.XS)
        self._cb_vbox.addStretch()
        scroll.setWidget(self._cb_container)
        lv.addWidget(scroll)

        # Generate button
        self._gen_btn = QPushButton("  Generate Lesson")
        self._gen_btn.setObjectName("UploadFab")
        self._gen_btn.setFont(Fonts.upload_button())
        self._gen_btn.setFixedHeight(44)
        self._gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._gen_btn.clicked.connect(self._on_generate)
        lv.addWidget(self._gen_btn)

        # ── Right pane ─────────────────────────────────────────────────────────
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        rv.setSpacing(0)

        self._stack = QStackedWidget()
        self._idle  = IdleView()
        self._busy  = BusyView()
        self._ready = ReadyView()
        self._stack.addWidget(self._idle)   # 0
        self._stack.addWidget(self._busy)   # 1
        self._stack.addWidget(self._ready)  # 2
        rv.addWidget(self._stack)

        root.addWidget(left)
        root.addWidget(right, stretch=1)

    # ── File watcher ───────────────────────────────────────────────────────────

    def _setup_file_watcher(self) -> None:
        self._fw = QFileSystemWatcher(self)
        for f in (Config.EXTRACTED_FILE, Config.EXTRACTED_LINK):
            f.mkdir(parents=True, exist_ok=True)
            self._fw.addPath(str(f.resolve()))
        self._fw.directoryChanged.connect(lambda _: self._refresh_files())

    def _refresh_files(self) -> None:
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
                    sorted(folder.glob("*.txt"),
                           key=lambda p: p.stat().st_mtime, reverse=True)
                )
        for fp in all_files:
            tag = "📄" if fp.parent.name == "fromfile" else "🔗"
            cb  = QCheckBox(f"  {tag}  {fp.stem}")
            cb.setFont(Fonts.body())
            cb.setStyleSheet(f"""
                QCheckBox {{
                    color:{Colors.TEXT_PRIMARY}; padding:{Spacing.XS}px;
                }}
                QCheckBox::indicator {{
                    width:15px; height:15px;
                    border:2px solid {Colors.BORDER_DEFAULT};
                    border-radius:{Radius.XS}px;
                    background:{Colors.SURFACE_MID};
                }}
                QCheckBox::indicator:checked {{
                    background:{Colors.ICON_ACTIVE};
                    border-color:{Colors.ICON_ACTIVE};
                }}""")
            self._file_checks[str(fp)] = cb
            self._cb_vbox.insertWidget(self._cb_vbox.count() - 1, cb)

    # ── Actions ────────────────────────────────────────────────────────────────

    def _on_select_all(self, state: int) -> None:
        checked = state == Qt.CheckState.Checked.value
        for cb in self._file_checks.values():
            cb.setChecked(checked)

    def _on_generate(self) -> None:
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
        if not source_texts:
            return
        self._show_busy("Writing lesson script…")
        self.lesson_requested.emit(source_texts)

    def selected_voice(self) -> str:
        return self._voice_selector.selected_voice()

    def _set_status(self, text: str) -> None:
        self._status_lbl.setText(text.split("\n")[0])
        self._status_lbl.setVisible(bool(text))

    # ── Public API ─────────────────────────────────────────────────────────────

    def show_idle(self) -> None:
        self._stack.setCurrentIndex(0)
        self._gen_btn.setEnabled(True)

    def show_busy(self, message: str = "Starting…") -> None:
        self._show_busy(message)

    def _show_busy(self, message: str) -> None:
        self._busy.set_status(message)
        self._busy.start()
        self._stack.setCurrentIndex(1)
        self._gen_btn.setEnabled(False)

    def update_progress(self, message: str) -> None:
        self._busy.set_status(message)

    def show_ready(self, script_path: str, audio_path: str) -> None:
        self._busy.stop()
        self._ready.refresh_lessons()
        self._ready.load_script(script_path)
        self._ready.load_audio(audio_path)
        self._ready.select_newest()
        self._stack.setCurrentIndex(2)
        self._gen_btn.setEnabled(True)
        self._set_status("Lesson ready!")

    def show_error(self, message: str) -> None:
        self._busy.stop()
        self._stack.setCurrentIndex(0)
        self._gen_btn.setEnabled(True)
        self._set_status(f"Error: {message}")

    def set_status(self, text: str) -> None:
        self._set_status(text)
