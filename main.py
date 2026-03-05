"""
main.py
-------
Entry point — starts the Qt application and shows TutorApp.
No logic lives here.
"""

import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import TutorApp


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = TutorApp()
    window.show()
    sys.exit(app.exec())
