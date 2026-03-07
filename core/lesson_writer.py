"""
lesson_writer.py — Transforms raw extracted text into a teaching script
using the active AI provider, then saves it to Data/lessons/<name>_lesson.txt.

The AI is prompted to act as an enthusiastic tutor — not just reading the text
but explaining it, using analogies, asking rhetorical questions, and structuring
it as a proper spoken lesson.
"""

from __future__ import annotations
import json
import logging
import traceback
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

from app_config import Config

logger = logging.getLogger(__name__)

TUTOR_SYSTEM_PROMPT = """You are an enthusiastic, clear, and friendly tutor creating a spoken audio lesson.
Your job is to transform raw study material into a natural spoken lesson script.

Rules you must follow:
- Write entirely in natural spoken language — no bullet points, no markdown, no headers
- Never say "as shown above" or "see figure" or reference visual elements
- Use teaching phrases: "Now let's think about this", "Here's the key thing to understand",
  "Think of it this way", "Let me give you an example", "Does that make sense? Let's keep going"
- Add relatable real-world analogies where possible
- Ask rhetorical questions to maintain engagement: "So why does this matter?", "But wait — what happens when...?"
- Break content into short paragraphs — each paragraph = one natural speaking pause
- Start with a warm introduction: "Welcome! Today we're going to explore..."
- End with a clear summary: "So to wrap up what we covered today..."
- Write as if speaking directly to one student, not a crowd
- Keep a warm, encouraging tone throughout
- Output ONLY the lesson script — no titles, no metadata, no commentary"""


class LessonWriter:

    def write_lesson(self, source_texts: dict[str, str]) -> Path:
        """
        Transform source texts into a teaching script.

        Args:
            source_texts: {stem: content} for each selected file

        Returns:
            Path to saved lesson script .txt file
        """
        from core.key_store import load_key, load_model, load_active_provider

        provider = load_active_provider()
        api_key  = load_key(provider)
        model    = load_model(provider)

        if not api_key:
            raise RuntimeError(
                f"No API key for '{provider}'. Go to ⚙ Settings and enter your key."
            )

        # Combine all source texts
        combined = "\n\n".join(
            f"=== {name} ===\n{text}" for name, text in source_texts.items()
        )

        user_prompt = (
            f"Transform the following study material into a spoken audio lesson "
            f"following the tutor style described. Be thorough and detailed — "
            f"a good lesson should take 5-10 minutes to listen to.\n\n"
            f"STUDY MATERIAL:\n{combined[:14000]}"
        )

        logger.info(f"Requesting lesson script from {provider}/{model}")
        script = self._call_api(provider, api_key, model, user_prompt)
        return self._save(source_texts, script)

    # ── API dispatch ───────────────────────────────────────────────────────────

    def _call_api(self, provider: str, api_key: str, model: str, prompt: str) -> str:
        if provider == "anthropic":
            return self._call_anthropic(api_key, model, prompt)
        elif provider == "openai":
            return self._call_openai(api_key, model, prompt)
        elif provider == "gemini":
            return self._call_gemini(api_key, model, prompt)
        raise RuntimeError(f"Unknown provider: {provider}")

    def _call_anthropic(self, api_key: str, model: str, prompt: str) -> str:
        payload = json.dumps({
            "model":      model,
            "max_tokens": 4096,
            "system":     TUTOR_SYSTEM_PROMPT,
            "messages":   [{"role": "user", "content": prompt}],
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages", data=payload,
            headers={"Content-Type": "application/json",
                     "x-api-key": api_key, "anthropic-version": "2023-06-01"},
            method="POST",
        )
        with self._open(req) as resp:
            return json.loads(resp.read())["content"][0]["text"]

    def _call_openai(self, api_key: str, model: str, prompt: str) -> str:
        payload = json.dumps({
            "model":      model,
            "max_tokens": 4096,
            "messages":   [
                {"role": "system", "content": TUTOR_SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
        }).encode()
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions", data=payload,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {api_key}"},
            method="POST",
        )
        with self._open(req) as resp:
            return json.loads(resp.read())["choices"][0]["message"]["content"]

    def _call_gemini(self, api_key: str, model: str, prompt: str) -> str:
        full_prompt = f"{TUTOR_SYSTEM_PROMPT}\n\n{prompt}"
        payload = json.dumps({
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"maxOutputTokens": 4096},
        }).encode()
        url = (
            f"https://generativelanguage.googleapis.com/v1/models/"
            f"{model}:generateContent?key={api_key}"
        )
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self._open(req) as resp:
            body = json.loads(resp.read())
            return body["candidates"][0]["content"]["parts"][0]["text"]

    def _open(self, req):
        try:
            return urllib.request.urlopen(req, timeout=60)
        except urllib.error.HTTPError as e:
            msg = f"API HTTP {e.code}: {e.read().decode()}"
            print(f"[API ERROR] {msg}", flush=True)
            logger.error(msg)
            raise RuntimeError(msg) from e
        except Exception as e:
            msg = f"API request failed: {e}"
            print(f"[API ERROR] {msg}", flush=True)
            logger.error(msg)
            traceback.print_exc()
            raise RuntimeError(msg) from e

    # ── Save ───────────────────────────────────────────────────────────────────

    def _save(self, source_texts: dict[str, str], script: str) -> Path:
        Config.LESSONS_DIR.mkdir(parents=True, exist_ok=True)

        import re
        stems = list(source_texts.keys())
        base  = "_".join(stems)
        base  = re.sub(r'[\\/*?:"<>|\s]', "_", base).strip("_")[:100]

        candidate = Config.LESSONS_DIR / f"{base}_lesson.txt"
        counter   = 2
        while candidate.exists():
            candidate = Config.LESSONS_DIR / f"{base}_lesson_{counter}.txt"
            counter  += 1

        candidate.write_text(script, encoding="utf-8")
        logger.info(f"Lesson script saved: {candidate}")
        return candidate
