"""
summarizer.py — AI-powered summarization using the active provider from key_store.

Saves each run as Data/summaries/summary<N>.txt
The file contains a header block listing source files, then the summary text.
"""

from __future__ import annotations
import json
import logging
import traceback
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

from app_config import Config

logger = logging.getLogger(__name__)


class Summarizer:

    def summarize(self, source_texts: dict[str, str]) -> Path:
        """
        Call the active AI provider to summarize the combined texts.

        Args:
            source_texts: {stem: text_content} for each selected file

        Returns:
            Path to the saved summary .txt file

        Raises:
            RuntimeError on API or config errors
        """
        from core.key_store import load_key, load_model, load_active_provider

        provider = load_active_provider()
        api_key  = load_key(provider)
        model    = load_model(provider)

        if not api_key:
            msg = (
                f"No API key configured for provider: {provider}. "
                f"Go to ⚙ Settings and enter your key."
            )
            print(f"[API ERROR] {msg}", flush=True)
            logger.error(msg)
            raise RuntimeError(msg)

        combined = "\n\n".join(
            f"=== {name} ===\n{text}" for name, text in source_texts.items()
        )

        prompt = (
            "You are an expert study assistant. Summarize the following study material "
            "clearly and concisely. Structure the summary with:\n"
            "  1. A short overview paragraph\n"
            "  2. Key points as a bullet list\n"
            "  3. Important terms or concepts (if any)\n\n"
            "Write in plain text — no markdown formatting, no asterisks, no hashes.\n\n"
            f"Study material:\n{combined[:14000]}"
        )

        raw = self._call_api(provider, api_key, model, prompt)
        save_path = self._save(source_texts, raw)
        return save_path

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
            "max_tokens": 2048,
            "messages":   [{"role": "user", "content": prompt}],
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type":      "application/json",
                "x-api-key":         api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        with self._open(req) as resp:
            return json.loads(resp.read())["content"][0]["text"]

    def _call_openai(self, api_key: str, model: str, prompt: str) -> str:
        payload = json.dumps({
            "model":      model,
            "messages":   [{"role": "user", "content": prompt}],
            "max_tokens": 2048,
        }).encode()
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            headers={
                "Content-Type":  "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with self._open(req) as resp:
            return json.loads(resp.read())["choices"][0]["message"]["content"]

    def _call_gemini(self, api_key: str, model: str, prompt: str) -> str:
        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 2048},
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
            msg = f"API HTTP error {e.code}: {e.read().decode()}"
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

    def _save(self, source_texts: dict[str, str], summary: str) -> Path:
        Config.SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)

        # Build filename from source file stems joined by "_"
        # e.g. one file  → "chapterone_summarized.txt"
        # e.g. two files → "chapterone_chaptertwo_summarized.txt"
        stems = list(source_texts.keys())
        base  = "_".join(stems)

        # Sanitise: strip characters illegal on Windows/Linux
        import re
        base = re.sub(r'[\\/*?:"<>|\s]', "_", base)
        base = base.strip("_")[:120]   # cap length for filesystem safety

        # If that exact name already exists, append _2, _3, etc.
        candidate = Config.SUMMARIES_DIR / f"{base}_summarized.txt"
        counter   = 2
        while candidate.exists():
            candidate = Config.SUMMARIES_DIR / f"{base}_summarized_{counter}.txt"
            counter  += 1
        path = candidate

        header = (
            f"SUMMARY\n"
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Sources:   {', '.join(stems)}\n"
            f"{'─' * 60}\n\n"
        )
        path.write_text(header + summary, encoding="utf-8")
        return path
