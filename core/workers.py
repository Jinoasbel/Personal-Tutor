"""
workers.py — QThread workers for background processing.
Keeps the UI responsive during heavy operations (OCR, summarization, etc.)

Extracted text is saved to disk automatically:
  Data/extracted/fromfile/<filename>.txt   — for uploaded files
  Data/extracted/fromlink/<linkname>.txt   — for pasted links (future)
"""

from __future__ import annotations
import re
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from .ocr_engine import OCREngine
from .summarizer import Summarizer
from .audio_generator import AudioGenerator


def _sanitise(name: str) -> str:
    """Strip characters that are illegal in Windows/Linux filenames."""
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    name = name.strip(". ")
    return name or "unnamed"


def _save_extracted(text: str, folder: Path, stem: str) -> Path:
    """
    Save extracted text to  folder/<stem>.txt
    Creates the folder if it doesn't exist.
    Returns the saved file path.
    """
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / f"{_sanitise(stem)}.txt"
    out.write_text(text, encoding="utf-8")
    return out


class OCRWorker(QThread):
    """
    Runs OCR on a list of files in a background thread.
    Each file's extracted text is saved to Data/extracted/fromfile/<filename>.txt
    """

    progress = Signal(str)   # status message
    result   = Signal(str)   # combined extracted text for all files
    error    = Signal(str)   # error message

    def __init__(self, file_paths: list[Path], extracted_dir: Path, parent=None) -> None:
        super().__init__(parent)
        self._files         = file_paths
        self._extracted_dir = extracted_dir   # Data/extracted/fromfile
        self._engine        = OCREngine()

    def run(self) -> None:
        try:
            combined_parts: list[str] = []

            for fp in self._files:
                fp = Path(fp)
                self.progress.emit(f"Extracting: {fp.name}…")

                text = self._engine.extract_from_file(fp)

                # Save individual file result
                saved = _save_extracted(text, self._extracted_dir, fp.stem)
                self.progress.emit(f"Saved → {saved}")

                combined_parts.append(f"--- {fp.name} ---\n{text}")

            self.result.emit("\n\n".join(combined_parts))

        except Exception as exc:
            self.error.emit(str(exc))


class LinkOCRWorker(QThread):
    """
    Placeholder worker for extracting text from links.
    Saves result to Data/extracted/fromlink/<sanitised_url>.txt
    Wire in web scraping / YouTube transcript logic inside run().
    """

    progress = Signal(str)
    result   = Signal(str)
    error    = Signal(str)

    def __init__(self, links: list[str], extracted_dir: Path, parent=None) -> None:
        super().__init__(parent)
        self._links         = links
        self._extracted_dir = extracted_dir   # Data/extracted/fromlink

    def run(self) -> None:
        try:
            combined_parts: list[str] = []

            for link in self._links:
                self.progress.emit(f"Fetching: {link}…")

                # ── TODO: replace with real scraping / transcript logic ────────
                text = f"[Link extraction not yet implemented]\nURL: {link}"
                # ─────────────────────────────────────────────────────────────

                # Use the domain + path as the filename stem
                stem = _sanitise(link.replace("https://", "").replace("http://", ""))
                stem = stem[:120]   # cap length for filesystem safety

                saved = _save_extracted(text, self._extracted_dir, stem)
                self.progress.emit(f"Saved → {saved}")

                combined_parts.append(f"--- {link} ---\n{text}")

            self.result.emit("\n\n".join(combined_parts))

        except Exception as exc:
            self.error.emit(str(exc))


class SummaryWorker(QThread):
    """Runs text summarization in a background thread."""

    progress = Signal(str)
    result   = Signal(str)
    error    = Signal(str)

    def __init__(self, text: str, parent=None) -> None:
        super().__init__(parent)
        self._text = text
        self._summarizer = Summarizer()

    def run(self) -> None:
        try:
            self.progress.emit("Summarizing…")
            summary = self._summarizer.summarize(self._text)
            self.result.emit(summary)
        except Exception as exc:
            self.error.emit(str(exc))


class AudioWorker(QThread):
    """Generates audio from text in a background thread."""

    progress = Signal(str)
    result   = Signal(str)
    error    = Signal(str)

    def __init__(self, text: str, output_path: Path, parent=None) -> None:
        super().__init__(parent)
        self._text   = text
        self._output = output_path
        self._generator = AudioGenerator()

    def run(self) -> None:
        try:
            self.progress.emit("Generating audio…")
            out = self._generator.generate(self._text, self._output)
            self.result.emit(str(out))
        except Exception as exc:
            self.error.emit(str(exc))


class QuestionWorker(QThread):
    """Calls AI to generate questions from selected extracted texts."""

    progress = Signal(str)
    result   = Signal(str)   # path to saved question JSON file
    error    = Signal(str)

    def __init__(self, texts: list[str], parent=None) -> None:
        super().__init__(parent)
        self._texts = texts

    def run(self) -> None:
        try:
            from .question_generator import generate_questions, save_questions
            self.progress.emit("Generating questions…")
            combined = "\n\n".join(self._texts)
            questions = generate_questions(combined)
            path = save_questions(questions)
            self.result.emit(str(path))
        except Exception as exc:
            self.error.emit(str(exc))


class QuestionGenWorker(QThread):
    """Calls AI API to generate questions in a background thread."""

    progress = Signal(str)
    result   = Signal(str)   # path to saved question JSON
    error    = Signal(str)

    def __init__(self, source_texts: dict, parent=None) -> None:
        super().__init__(parent)
        self._source_texts = source_texts

    def run(self) -> None:
        try:
            from .qa_engine import QAEngine
            self.progress.emit("Generating questions…")
            engine = QAEngine()
            path = engine.generate_questions(self._source_texts)
            self.result.emit(str(path))
        except Exception as exc:
            self.error.emit(str(exc))
