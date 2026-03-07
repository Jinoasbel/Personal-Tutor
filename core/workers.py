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
    Extracts real content from URLs using LinkExtractor.

    YouTube: fetches real title via oEmbed + real transcript via
             youtube-transcript-api, then sends to AI for a polished article.
    Other:   fetches page HTML, strips tags, sends to AI for a structured summary.

    File is saved as: Data/extracted/fromlink/<real_video_or_page_title>.txt
    """

    progress = Signal(str)
    result   = Signal(str)
    error    = Signal(str)

    def __init__(self, links: list[str], extracted_dir: Path, parent=None) -> None:
        super().__init__(parent)
        self._links         = links
        self._extracted_dir = extracted_dir

    def run(self) -> None:
        try:
            from .link_extractor import LinkExtractor
            extractor      = LinkExtractor()
            combined_parts: list[str] = []

            for link in self._links:
                self.progress.emit(f"Fetching: {link}…")
                try:
                    filename_stem, text = extractor.extract(link)
                except Exception as exc:
                    filename_stem = _sanitise(
                        link.replace("https://", "").replace("http://", "")
                    )[:80]
                    text = f"[Extraction failed]\nURL: {link}\nError: {exc}"

                saved = _save_extracted(text, self._extracted_dir, filename_stem)
                stem_display = saved.stem  # just the video/page title, no path or extension
                self.progress.emit(f"Fetched: {stem_display}")
                combined_parts.append(f"--- {link} ---\n{text}")

            self.result.emit("\n\n".join(combined_parts))
        except Exception as exc:
            self.error.emit(str(exc))



class SummaryWorker(QThread):
    """Runs AI summarization for selected files in a background thread."""

    progress = Signal(str)
    result   = Signal(str)   # path to saved summary .txt
    error    = Signal(str)

    def __init__(self, source_texts: dict, parent=None) -> None:
        super().__init__(parent)
        self._source_texts = source_texts

    def run(self) -> None:
        try:
            self.progress.emit("Summarizing…")
            path = Summarizer().summarize(self._source_texts)
            self.result.emit(str(path))
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


class LessonWorker(QThread):
    """
    Two-stage background worker:
      Stage 1 — AI transforms extracted text into a teaching script
      Stage 2 — Kokoro TTS converts the script to MP3

    Signals:
        progress(str)  — status message for the UI
        script_ready(str) — path to saved lesson script .txt
        result(str)    — path to saved .mp3 audio file
        error(str)     — error message
    """

    progress     = Signal(str)
    script_ready = Signal(str)   # lesson .txt path
    result       = Signal(str)   # audio .mp3 path
    error        = Signal(str)

    def __init__(self, source_texts: dict, voice: str = "af_heart", parent=None) -> None:
        super().__init__(parent)
        self._source_texts = source_texts
        self._voice        = voice

    def run(self) -> None:
        try:
            from app_config import Config
            from .lesson_writer import LessonWriter
            from .audio_generator import AudioGenerator
            import re

            # ── Stage 1: AI script transformation ─────────────────────────────
            self.progress.emit("Writing lesson script…")
            writer      = LessonWriter()
            script_path = writer.write_lesson(self._source_texts)
            self.script_ready.emit(str(script_path))
            self.progress.emit("Lesson script ready — starting audio generation…")

            # ── Stage 2: Kokoro TTS ────────────────────────────────────────────
            script_text = script_path.read_text(encoding="utf-8")

            # Build audio filename from source stems
            stems    = list(self._source_texts.keys())
            base     = "_".join(stems)
            base     = re.sub(r'[\\/*?:"<>|\s]', "_", base).strip("_")[:100]

            Config.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
            mp3_path = Config.AUDIO_DIR / f"{base}_lesson.wav"

            # Avoid overwriting
            counter = 2
            while mp3_path.exists():
                mp3_path = Config.AUDIO_DIR / f"{base}_lesson_{counter}.wav"
                counter += 1

            generator = AudioGenerator(voice=self._voice)
            final_path = generator.generate(
                script_text,
                mp3_path,
                progress_cb=lambda msg: self.progress.emit(msg),
            )

            self.result.emit(str(final_path))

        except Exception as exc:
            import traceback
            traceback.print_exc()
            self.error.emit(str(exc))


class VoiceSampleWorker(QThread):
    """
    Generates missing voice sample MP3s at app startup.

    - Runs only once per missing voice file
    - Silently skips if Kokoro is not installed
    - Emits sample_ready(voice_key) as each file finishes
      so the UI can enable play buttons one by one
    - Emits all_done when all voices are processed
    """

    sample_ready = Signal(str)   # voice_key
    all_done     = Signal()

    SAMPLE_TEXT = (
        "Hello! I'm your personal tutor, here to help you learn. "
        "Let's get started on something great today."
    )

    def __init__(self, voices: dict, samples_dir: Path, parent=None) -> None:
        super().__init__(parent)
        self._voices      = voices       # {key: display_name}
        self._samples_dir = samples_dir

    def run(self) -> None:
        try:
            from kokoro import KPipeline
        except ImportError:
            # Kokoro not installed — skip silently
            self.all_done.emit()
            return

        try:
            import numpy as np
            import soundfile as sf
        except ImportError:
            self.all_done.emit()
            return

        self._samples_dir.mkdir(parents=True, exist_ok=True)

        # Load pipeline once for all voices
        try:
            pipeline = KPipeline(lang_code="a")
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"VoiceSampleWorker: pipeline load failed: {e}")
            self.all_done.emit()
            return

        for voice_key in self._voices:
            # Check both .wav and .mp3 (legacy)
            wav_path = self._samples_dir / f"{voice_key}.wav"
            mp3_path = self._samples_dir / f"{voice_key}.mp3"
            if wav_path.exists() or mp3_path.exists():
                self.sample_ready.emit(voice_key)
                continue

            try:
                audio_parts = []
                for _, _, audio in pipeline(self.SAMPLE_TEXT, voice=voice_key):
                    if audio is not None:
                        audio_parts.append(audio)

                if not audio_parts:
                    continue

                combined = np.concatenate(audio_parts)

                # Save directly as WAV — reliable, no conversion needed
                wav_path = self._samples_dir / f"{voice_key}.wav"
                sf.write(str(wav_path), combined, 24000)
                self.sample_ready.emit(voice_key)

            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(
                    f"VoiceSampleWorker: failed for {voice_key}: {e}"
                )

        self.all_done.emit()
