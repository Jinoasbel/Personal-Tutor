"""
audio_generator.py — Kokoro TTS engine.

Fixes:
  - Only one output file produced (WAV deleted after successful MP3 conversion)
  - Temp WAV written to Data/temp/ to avoid polluting Data/audio/
  - Voice selectable at construction time

Install:
    pip install kokoro soundfile pydub
    ffmpeg must be installed system-wide for MP3 conversion
"""

from __future__ import annotations
import logging
import re
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

SAMPLE_RATE = 24000
CHUNK_SIZE  = 450   # safe chars per Kokoro call

# All available Kokoro voices with display names
VOICES: dict[str, str] = {
    "af_heart":   "Heart (Warm Female)",
    "af_bella":   "Bella (Soft Female)",
    "af_nicole":  "Nicole (Clear Female)",
    "af_sarah":   "Sarah (Bright Female)",
    "am_adam":    "Adam (Deep Male)",
    "am_michael": "Michael (Calm Male)",
    "bf_emma":    "Emma (British Female)",
    "bf_isabella":"Isabella (British Female)",
    "bm_george":  "George (British Male)",
    "bm_lewis":   "Lewis (British Male)",
}
DEFAULT_VOICE = "af_heart"


class AudioGenerator:

    def __init__(self, voice: str = DEFAULT_VOICE) -> None:
        self._voice    = voice if voice in VOICES else DEFAULT_VOICE
        self._pipeline = None   # lazy-loaded on first generate()

    def _load_pipeline(self, progress_cb: Callable[[str], None] | None = None) -> None:
        if self._pipeline is not None:
            return
        try:
            from kokoro import KPipeline
        except ImportError:
            raise RuntimeError(
                "Kokoro not installed. Run: pip install kokoro soundfile pydub"
            )

        cache        = Path.home() / ".cache" / "huggingface"
        model_exists = any(cache.rglob("kokoro*")) if cache.exists() else False
        if not model_exists and progress_cb:
            progress_cb("First run: downloading voice model (~300 MB)… please wait")

        logger.info("Loading Kokoro pipeline…")
        self._pipeline = KPipeline(lang_code="a")
        logger.info("Kokoro pipeline ready")

    def generate(
        self,
        text: str,
        output_path: str | Path,
        progress_cb: Callable[[str], None] | None = None,
    ) -> Path:
        """
        Convert lesson script to MP3 (or WAV if pydub unavailable).
        Temp WAV is always written to Data/temp/ and deleted after conversion.
        """
        import numpy as np
        try:
            import soundfile as sf
        except ImportError:
            raise RuntimeError("soundfile not installed. Run: pip install soundfile")

        from app_config import Config
        Config.TEMP_DIR.mkdir(parents=True, exist_ok=True)

        out      = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        # Temp WAV always goes to Data/temp/ — never in Data/audio/
        wav_path = Config.TEMP_DIR / (out.stem + "_tmp.wav")

        # 1. Load model
        self._load_pipeline(progress_cb)

        # 2. Split into sentence-safe chunks
        chunks = self._split_chunks(text)
        total  = len(chunks)
        logger.info(f"Generating audio for {total} chunks with voice '{self._voice}'…")

        # 3. Generate per chunk
        audio_parts: list = []
        for i, chunk in enumerate(chunks, 1):
            if progress_cb:
                progress_cb(f"Generating speech… ({i}/{total})")
            try:
                for _, _, audio in self._pipeline(chunk, voice=self._voice):
                    if audio is not None:
                        audio_parts.append(audio)
            except Exception as e:
                logger.warning(f"Chunk {i} failed: {e}")

        if not audio_parts:
            raise RuntimeError("No audio was generated — all chunks failed.")

        # 4. Concatenate + write temp WAV
        if progress_cb:
            progress_cb("Combining audio…")
        combined = np.concatenate(audio_parts)
        sf.write(str(wav_path), combined, SAMPLE_RATE)
        logger.info(f"Temp WAV written: {wav_path}")

        # 5. Convert to MP3, then delete temp WAV
        final = self._wav_to_mp3(wav_path, out, progress_cb)
        return final

    def _wav_to_mp3(
        self,
        wav_path: Path,
        mp3_path: Path,
        progress_cb: Callable[[str], None] | None = None,
    ) -> Path:
        try:
            from pydub import AudioSegment
            if progress_cb:
                progress_cb("Converting to MP3…")
            audio = AudioSegment.from_wav(str(wav_path))
            # Ensure output path has .mp3 extension
            final = mp3_path.with_suffix(".mp3")
            audio.export(str(final), format="mp3", bitrate="128k")
            wav_path.unlink(missing_ok=True)   # always remove temp WAV
            logger.info(f"MP3 saved: {final}")
            return final
        except ImportError:
            logger.warning("pydub not installed — output will be WAV")
            final = mp3_path.with_suffix(".wav")
            wav_path.rename(final)
            return final
        except Exception as e:
            logger.warning(f"MP3 conversion failed ({e}) — output will be WAV")
            final = mp3_path.with_suffix(".wav")
            try:
                wav_path.rename(final)
            except Exception:
                pass
            return final

    def _split_chunks(self, text: str) -> list[str]:
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        chunks: list[str] = []
        current = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if current and len(current) + len(sentence) + 1 > CHUNK_SIZE:
                chunks.append(current.strip())
                current = sentence
            else:
                current = (current + " " + sentence).strip() if current else sentence
        if current.strip():
            chunks.append(current.strip())
        return [c for c in chunks if c]
