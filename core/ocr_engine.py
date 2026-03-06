"""
ocr_engine.py — OCR logic using PaddleOCR v3.x
Separates all OCR processing from the UI layer.
"""

from __future__ import annotations
from pathlib import Path


class OCREngine:
    """
    Wraps PaddleOCR for text extraction from images and PDFs.
    Lazy-initialised: the heavy model loads only on first use.
    Compatible with PaddleOCR 3.x API.
    """

    def __init__(self) -> None:
        self._ocr = None

    # ── Private ───────────────────────────────────────────────────────────────

    def _load(self) -> None:
        """Lazy-load PaddleOCR."""
        if self._ocr is None:
            from paddleocr import PaddleOCR  # type: ignore
            self._ocr = PaddleOCR(lang="en", enable_mkldnn=False)

    def _parse_results(self, results) -> list[str]:
        """
        Parse PaddleOCR v3.x results into flat list of text strings.
        v3.x returns a list of dicts with 'rec_texts' key.
        Falls back to v2.x list-of-list format if needed.
        """
        lines: list[str] = []
        if not results:
            return lines

        for item in results:
            try:
                # v3.x format: dict with 'rec_texts'
                if isinstance(item, dict):
                    texts = item.get("rec_texts", [])
                    for t in texts:
                        if t and str(t).strip():
                            lines.append(str(t).strip())
                # v2.x format: list of [bbox, [text, confidence]]
                elif isinstance(item, list):
                    for line in item:
                        try:
                            text = line[1][0]
                            if text and str(text).strip():
                                lines.append(str(text).strip())
                        except (IndexError, TypeError):
                            continue
            except Exception:
                continue

        return lines

    # ── Public API ────────────────────────────────────────────────────────────

    def extract_from_file(self, file_path: str | Path) -> str:
        """
        Extract text from a single image or PDF file.

        Args:
            file_path: Absolute path to the file.

        Returns:
            Extracted text as a single string, lines joined by newlines.

        Raises:
            FileNotFoundError: If the file does not exist.
            RuntimeError: If OCR fails.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        self._load()

        try:
            results = self._ocr.predict(str(path))
            lines = self._parse_results(results)
            return "\n".join(lines)
        except Exception as exc:
            raise RuntimeError(f"OCR extraction failed: {exc}") from exc

    def extract_from_files(self, file_paths: list[str | Path]) -> dict[str, str]:
        """
        Extract text from multiple files.

        Returns:
            Dict mapping file path strings to extracted text.
        """
        results: dict[str, str] = {}
        for fp in file_paths:
            try:
                results[str(fp)] = self.extract_from_file(fp)
            except Exception as exc:
                results[str(fp)] = f"[ERROR] {exc}"
        return results
