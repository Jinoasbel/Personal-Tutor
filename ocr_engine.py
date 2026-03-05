"""
ocr_engine.py
-------------
Runs PaddleOCR in a fully isolated subprocess so Qt's event loop
is NEVER touched by PaddleOCR's native libraries.

Architecture:
    OCREngine           — public API, lives in the Qt process
    _SubprocessWatcher  — QThread that only watches the subprocess stdout
                          (no heavy work here, just I/O waiting)
    ocr_worker_process  — completely separate Python process that runs
                          PaddleOCR and writes JSON to stdout

Why subprocess and not QThread alone?
    PaddleOCR links against OpenCV, ONNXRuntime and MKL. These native
    libraries register OS-level callbacks that re-enter the event system.
    Inside a QThread (same process as Qt) those callbacks can stall
    PySide6's event loop regardless of CPU core count. A subprocess has
    its own address space — zero shared state with Qt, guaranteed.
"""

import os
import sys
import json
import subprocess

from PySide6.QtCore import QThread, QObject, Signal


# ── Subprocess watcher (QThread only does lightweight I/O waiting) ────────────

class _SubprocessWatcher(QObject):
    """
    Launched in a QThread. Starts the OCR subprocess, waits for it to
    finish, reads one JSON line from stdout, then emits the result signal.

    This thread never touches PaddleOCR — it only calls subprocess.run()
    which is safe to do from any thread.
    """

    finished = Signal(str)
    failed   = Signal(str)

    def __init__(self, file_path: str):
        super().__init__()
        self._file_path = file_path

        # Path to the standalone worker script, next to this file
        self._worker_script = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "ocr_worker_process.py"
        )

    def run(self) -> None:
        """Blocks this thread (not the UI thread) until the subprocess exits."""
        try:
            proc = subprocess.run(
                [sys.executable, self._worker_script, self._file_path],
                capture_output=True,
                text=True
            )

            raw_output = proc.stdout.strip()
            if not raw_output:
                stderr_hint = proc.stderr.strip()[-300:] if proc.stderr else "no output"
                self.failed.emit(f"Worker produced no output. stderr: {stderr_hint}")
                return

            data = json.loads(raw_output)

            if data.get("success"):
                self.finished.emit(data["text"])
            else:
                self.failed.emit(data.get("error", "Unknown error in OCR worker."))

        except json.JSONDecodeError as exc:
            self.failed.emit(f"Could not parse worker output: {exc}")
        except Exception as exc:
            self.failed.emit(str(exc))


# ── Public API ────────────────────────────────────────────────────────────────

class OCREngine:
    """
    Manages the subprocess + watcher thread lifecycle.

    Usage:
        engine = OCREngine()
        engine.extract(file_path, on_success=slot, on_error=slot)

    Both slots are called on the main Qt thread via Signal/Slot delivery.
    """

    def __init__(self):
        self._thread: QThread | None = None
        self._watcher: _SubprocessWatcher | None = None

    def extract(self, file_path: str, on_success, on_error) -> None:
        """
        Spawns the OCR subprocess via a lightweight watcher QThread.
        Any previous run is stopped cleanly first.
        """
        self._teardown()

        self._thread  = QThread()
        self._watcher = _SubprocessWatcher(file_path)
        self._watcher.moveToThread(self._thread)

        # Lifecycle
        self._thread.started.connect(self._watcher.run)
        self._watcher.finished.connect(on_success)
        self._watcher.failed.connect(on_error)

        # Auto-cleanup
        self._watcher.finished.connect(self._thread.quit)
        self._watcher.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def _teardown(self) -> None:
        """Gracefully stops the watcher thread if one is still running."""
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(msecs=3000)
