"""
main.py — Entry point for Personal Tutor.
Run with:  python main.py
"""

import sys
from pathlib import Path

# ── Ensure the project root is always first on sys.path ───────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
# ─────────────────────────────────────────────────────────────────────────────

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app_config import Config
from pt_theme import get_stylesheet
from main_window import MainWindow


def main() -> None:
    if Config.HIGH_DPI:
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName(Config.__module__)
    app.setStyleSheet(get_stylesheet())

    Path(Config.DATA_DIR).mkdir(parents=True, exist_ok=True)
    Path(Config.TEMP_DIR).mkdir(parents=True, exist_ok=True)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
