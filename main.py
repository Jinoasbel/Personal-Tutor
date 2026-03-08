"""
main.py — Entry point for Ur Personal Tutor.
"""

import sys
import multiprocessing

# ── MUST be the very first thing called in a frozen Windows exe ───────────────
# Without this, PyInstaller re-executes main() for every new thread/process,
# causing multiple windows to open and workers crashing the app.
if __name__ == "__main__" or getattr(sys, "frozen", False):
    multiprocessing.freeze_support()
import logging
import traceback
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════════════
# CRITICAL — fix for frozen windowed exe (console=False in PyInstaller):
#
# When console=False, sys.stdout and sys.stderr are None.
# Kokoro uses loguru which calls loguru.add(sys.stderr) at import time.
# If sys.stderr is None this raises:
#   TypeError: Cannot log to objects of type 'NoneType'
#
# Fix: replace None streams with a no-op writer BEFORE any import that
# pulls in kokoro or loguru.
# ══════════════════════════════════════════════════════════════════════════════
class _NullWriter:
    def write(self, *a, **kw): pass
    def flush(self, *a, **kw): pass
    def isatty(self): return False

if sys.stdout is None:
    sys.stdout = _NullWriter()
if sys.stderr is None:
    sys.stderr = _NullWriter()

# Also fix standard logging lastResort / root handler
logging.root.addHandler(logging.NullHandler())
if logging.lastResort is None:
    logging.lastResort = logging.StreamHandler(sys.stderr)

# Silence noisy third-party loggers right away
for _noisy in ("kokoro", "phonemizer", "transformers",
               "huggingface_hub", "filelock", "urllib3",
               "PIL", "paddle", "ppocr", "loguru"):
    _lg = logging.getLogger(_noisy)
    _lg.setLevel(logging.ERROR)
    _lg.propagate = False
    _lg.addHandler(logging.NullHandler())

# ── Resolve project root ───────────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    _PROJECT_ROOT = Path(sys.executable).parent
    _MEIPASS = Path(sys._MEIPASS)
    if str(_MEIPASS) not in sys.path:
        sys.path.insert(0, str(_MEIPASS))
else:
    _PROJECT_ROOT = Path(__file__).resolve().parent

if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
# ─────────────────────────────────────────────────────────────────────────────

_LOG_FILE = _PROJECT_ROOT / "ur_personal_tutor.log"


def _setup_logging() -> None:
    """Log to a file always; also stdout when running from source."""
    file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8", mode="w")
    file_handler.setFormatter(
        logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    )
    # Replace any existing handlers on root logger
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(file_handler)
    root.setLevel(logging.DEBUG)

    if not getattr(sys, "frozen", False):
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
        root.addHandler(sh)

    # Keep noisy libraries silent even after full logging is set up
    for _noisy in ("kokoro", "phonemizer", "transformers",
                   "huggingface_hub", "filelock", "urllib3",
                   "PIL", "paddle", "ppocr"):
        lg = logging.getLogger(_noisy)
        lg.setLevel(logging.ERROR)
        lg.propagate = False


def _load_icon():
    from PySide6.QtGui import QIcon
    if getattr(sys, "frozen", False):
        icons_dir = Path(sys._MEIPASS) / "assets" / "icons"
    else:
        icons_dir = _PROJECT_ROOT / "assets" / "icons"

    ico = icons_dir / "app.ico"
    if ico.exists():
        return QIcon(str(ico))

    icon = QIcon()
    for size in [16, 32, 48, 64, 128, 256]:
        png = icons_dir / f"icon_{size}.png"
        if png.exists():
            icon.addFile(str(png))
    return icon


def main() -> None:
    _setup_logging()
    log = logging.getLogger(__name__)
    log.info(f"Starting Ur Personal Tutor  root={_PROJECT_ROOT}")
    log.info(f"Frozen={getattr(sys, 'frozen', False)}")

    try:
        from PySide6.QtWidgets import QApplication
        from app_config import Config
        from pt_theme import get_stylesheet
        from main_window import MainWindow

        app = QApplication(sys.argv)
        app.setApplicationName("Ur Personal Tutor")
        app.setApplicationDisplayName("Ur Personal Tutor")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("Jinoasbel")

        app_icon = _load_icon()
        app.setWindowIcon(app_icon)
        app.setStyleSheet(get_stylesheet())

        for d in (Config.DATA_DIR, Config.TEMP_DIR):
            Path(d).mkdir(parents=True, exist_ok=True)
        log.info(f"Data dir: {Config.DATA_DIR}")

        window = MainWindow()
        window.setWindowIcon(app_icon)
        window.show()

        sys.exit(app.exec())

    except Exception:
        log.critical("FATAL ERROR:\n" + traceback.format_exc())
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            if not QApplication.instance():
                _app = QApplication(sys.argv)
            msg = QMessageBox()
            msg.setWindowTitle("Ur Personal Tutor — Error")
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("The application failed to start.")
            msg.setInformativeText(
                f"Please send this log file to the developer:\n\n{_LOG_FILE}"
            )
            msg.exec()
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
