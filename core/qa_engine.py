"""
qa_engine.py — Question generation and quiz grading.
Supports Anthropic, OpenAI, and Gemini via key_store.
"""

from __future__ import annotations
import json
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

import logging
import traceback
from app_config import Config

logger = logging.getLogger(__name__)


class QAEngine:

    # ── Generate ───────────────────────────────────────────────────────────────

    def generate_questions(self, source_texts: dict[str, str], count: int | None = None) -> Path:
        from core.key_store import load_key, load_model, load_active_provider
        count    = count or Config.AI_QUESTION_COUNT
        provider = load_active_provider()
        api_key  = load_key(provider)
        model    = load_model(provider)

        if not api_key:
            raise RuntimeError(
                f"No API key for '{provider}'.\n"
                f"Go to ⚙ Settings and enter your key."
            )

        combined = "\n\n".join(
            f"=== {name} ===\n{text}" for name, text in source_texts.items()
        )
        prompt = (
            f"You are a tutor. Based on the study material below, generate "
            f"{count} multiple-choice questions to test understanding.\n\n"
            f"Return ONLY a valid JSON array — no markdown, no explanation, no extra text.\n"
            f"Each item must have exactly:\n"
            f"  id (integer starting at 1)\n"
            f"  question (string)\n"
            f"  options (array of 4 strings, prefixed 'A. ' 'B. ' 'C. ' 'D. ')\n"
            f"  answer (string: 'A', 'B', 'C', or 'D')\n\n"
            f"Study material:\n{combined[:12000]}"
        )

        raw = self._call_api(provider, api_key, model, prompt)
        questions = self._parse_questions(raw)

        data = {
            "provider":      provider,
            "model":         model,
            "source_files":  list(source_texts.keys()),
            "generated_at":  datetime.now().isoformat(),
            "questions":     questions,
        }

        path = self._next_path(Config.QUESTIONS_DIR, "question")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    # ── Score ──────────────────────────────────────────────────────────────────

    def score_attempt(self, question_file: Path, user_answers: dict[int, str]) -> Path:
        data      = json.loads(question_file.read_text(encoding="utf-8"))
        questions = data["questions"]
        score     = 0
        answers_out = []

        for q in questions:
            qid      = q["id"]
            correct  = q["answer"].upper()
            selected = user_answers.get(qid, "").upper()
            ok       = selected == correct
            if ok:
                score += 1
            answers_out.append({
                "id":         qid,
                "question":   q["question"],
                "selected":   selected,
                "correct":    correct,
                "is_correct": ok,
            })

        result = {
            "question_file": question_file.name,
            "attempted_at":  datetime.now().isoformat(),
            "score":         score,
            "total":         len(questions),
            "answers":       answers_out,
        }

        path = self._next_path(Config.RESULTS_DIR, "result")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    # ── API Dispatch ───────────────────────────────────────────────────────────

    def _call_api(self, provider: str, api_key: str, model: str, prompt: str) -> str:
        if provider == "anthropic":
            return self._call_anthropic(api_key, model, prompt)
        elif provider == "openai":
            return self._call_openai(api_key, model, prompt)
        elif provider == "gemini":
            return self._call_gemini(api_key, model, prompt)
        else:
            raise RuntimeError(f"Unknown provider: {provider}")

    def _call_anthropic(self, api_key: str, model: str, prompt: str) -> str:
        payload = json.dumps({
            "model":      model,
            "max_tokens": 4096,
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
            "max_tokens": 4096,
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
            msg = f"API HTTP error {e.code}: {e.read().decode()}"
            logger.error(msg)
            print(f"[API ERROR] {msg}", flush=True)
            raise RuntimeError(msg) from e
        except Exception as e:
            msg = f"API request failed: {e}"
            logger.error(msg)
            print(f"[API ERROR] {msg}", flush=True)
            traceback.print_exc()
            raise RuntimeError(msg) from e

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _parse_questions(self, raw: str) -> list[dict]:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "questions" in data:
                return data["questions"]
            raise ValueError("Unexpected structure")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Could not parse AI response as JSON: {e}\n\nRaw:\n{raw[:400]}")

    def _next_path(self, folder: Path, prefix: str) -> Path:
        folder.mkdir(parents=True, exist_ok=True)
        i = 1
        while (folder / f"{prefix}{i}.json").exists():
            i += 1
        return folder / f"{prefix}{i}.json"

    # kept for backward compat
    def set_context(self, text: str) -> None:
        self._context = text

    def ask(self, question: str) -> str:
        return "[Use the Ask Questions panel to generate a quiz.]"
