"""
link_extractor.py — Extracts real content from URLs.

YouTube flow:
  1. Fetch video title via YouTube oEmbed (free, no API key)
  2. Fetch real transcript via youtube-transcript-api (pip install youtube-transcript-api)
  3. Send transcript + title to AI → polished written article
  4. Filename = sanitised video title + ".txt"

Other URLs:
  1. Fetch raw HTML, strip tags
  2. Extract <title> tag for filename
  3. Send page text to AI → structured written summary
  4. Filename = sanitised page title + ".txt"

Install requirement (add to your pip install step):
  pip install youtube-transcript-api
"""

from __future__ import annotations
import json
import logging
import re
import traceback
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path

logger = logging.getLogger(__name__)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _sanitise_filename(name: str, max_len: int = 80) -> str:
    """Strip characters illegal on Windows/Linux and cap length."""
    name = re.sub(r'[\\/*?:"<>|\r\n]', "_", name)
    name = name.strip(". _")
    return name[:max_len] or "untitled"


def _strip_html(html: str) -> str:
    """Crude but fast HTML tag stripper."""
    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>",  " ", text,  flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;",  "&", text)
    text = re.sub(r"&lt;",   "<", text)
    text = re.sub(r"&gt;",   ">", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_html_title(html: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if m:
        return _strip_html(m.group(1)).strip()
    return ""


def _fetch_url(url: str, timeout: int = 12) -> str:
    """Fetch URL and return decoded text. Returns '' on error."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; PersonalTutor/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        logger.warning(f"Fetch failed for {url}: {e}")
        return ""


def _extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r"(?:youtube\.com/watch\?.*v=)([A-Za-z0-9_-]{11})",
        r"(?:youtu\.be/)([A-Za-z0-9_-]{11})",
        r"(?:youtube\.com/embed/)([A-Za-z0-9_-]{11})",
        r"(?:youtube\.com/shorts/)([A-Za-z0-9_-]{11})",
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    return None


def _get_youtube_title(video_id: str) -> str:
    """Fetch the real YouTube video title via the free oEmbed API."""
    try:
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        raw = _fetch_url(oembed_url)
        if raw:
            data = json.loads(raw)
            return data.get("title", "").strip()
    except Exception as e:
        logger.warning(f"oEmbed title fetch failed: {e}")
    return ""


def _get_youtube_transcript(video_id: str) -> str:
    """
    Fetch the real transcript using youtube-transcript-api.
    Handles both the old API (v0.x) and new API (v1.x) call signatures.
    Returns empty string if not available or library not installed.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        # ── New API (v1.x): use fetch() via YouTubeTranscriptApi instance ──────
        try:
            ytt = YouTubeTranscriptApi()
            fetched = ytt.fetch(video_id)
            # fetched is a FetchedTranscript — iterate its snippets
            lines = [snippet.text for snippet in fetched]
            if lines:
                logger.info(f"Transcript fetched via new API ({len(lines)} snippets)")
                return " ".join(lines)
        except Exception:
            pass

        # ── Old API (v0.x): class-method get_transcript() ─────────────────────
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(
                video_id, languages=["en", "en-US", "en-GB"]
            )
            lines = [entry["text"] for entry in transcript_list]
            if lines:
                logger.info(f"Transcript fetched via old API ({len(lines)} entries)")
                return " ".join(lines)
        except Exception:
            pass

        logger.warning(f"No transcript found for {video_id}")
        return ""

    except ImportError:
        logger.warning("youtube-transcript-api not installed. Run: pip install youtube-transcript-api")
        return ""
    except Exception as e:
        logger.warning(f"Transcript fetch failed for {video_id}: {e}")
        return ""


# ── Main extractor class ───────────────────────────────────────────────────────

class LinkExtractor:
    """
    Extracts content from a URL, using real data where possible,
    then sends it to the active AI provider for a polished written version.

    Returns (filename_stem, written_content).
    """

    def extract(self, url: str) -> tuple[str, str]:
        """
        Returns (filename_stem, text_content).
        filename_stem is the real title of the page/video (sanitised for filesystem).
        """
        video_id = _extract_video_id(url)
        if video_id:
            return self._handle_youtube(url, video_id)
        else:
            return self._handle_webpage(url)

    # ── YouTube ────────────────────────────────────────────────────────────────

    def _handle_youtube(self, url: str, video_id: str) -> tuple[str, str]:
        logger.info(f"Processing YouTube video: {video_id}")

        # 1. Get real title
        title = _get_youtube_title(video_id)
        if not title:
            title = f"YouTube Video {video_id}"
        logger.info(f"Video title: {title}")

        # 2. Get real transcript
        transcript = _get_youtube_transcript(video_id)

        if transcript:
            logger.info(f"Got transcript ({len(transcript)} chars) — sending to AI")
            prompt = (
                f"The following is the real transcript of a YouTube video titled: \"{title}\"\n"
                f"URL: {url}\n\n"
                f"TRANSCRIPT:\n{transcript[:12000]}\n\n"
                f"Using this transcript, write a detailed, well-structured written article "
                f"that captures the full content of this video. Structure it as:\n"
                f"  - Introduction\n"
                f"  - Main content broken into clear sections with headings\n"
                f"  - Key takeaways\n"
                f"  - Conclusion\n\n"
                f"Write in clear, engaging prose. Preserve all specific details, "
                f"names, facts, and narratives from the transcript."
            )
        else:
            logger.info("No transcript available — using title-based AI generation")
            prompt = (
                f"A user wants to study the content of this YouTube video:\n"
                f"Title: \"{title}\"\n"
                f"URL: {url}\n\n"
                f"Note: The automatic transcript could not be retrieved. "
                f"Based on the video title and any knowledge you have about this specific "
                f"video, write the most accurate and detailed written version you can. "
                f"Be clear about what you know vs what you are inferring.\n\n"
                f"Structure as:\n"
                f"  - Introduction\n"
                f"  - Main content\n"
                f"  - Key takeaways\n"
                f"  - Conclusion"
            )

        content = self._call_ai(prompt)
        filename_stem = _sanitise_filename(title)
        return filename_stem, content

    # ── Webpage ────────────────────────────────────────────────────────────────

    def _handle_webpage(self, url: str) -> tuple[str, str]:
        logger.info(f"Processing webpage: {url}")

        # 1. Fetch the page
        html      = _fetch_url(url)
        page_text = _strip_html(html)[:10000] if html else ""
        page_title = _extract_html_title(html) if html else ""

        # Use domain as fallback title
        if not page_title:
            domain = urllib.parse.urlparse(url).netloc or url
            page_title = domain

        logger.info(f"Page title: {page_title}, content length: {len(page_text)}")

        if page_text:
            prompt = (
                f"The following is the text content from this webpage:\n"
                f"Title: \"{page_title}\"\n"
                f"URL: {url}\n\n"
                f"PAGE CONTENT:\n{page_text}\n\n"
                f"Write a detailed, well-structured written summary of this content. "
                f"Preserve all key facts, arguments, data, and details. "
                f"Structure it clearly with an introduction, main points, and conclusion."
            )
        else:
            prompt = (
                f"A user wants to extract content from this URL:\n"
                f"Title: \"{page_title}\"\n"
                f"URL: {url}\n\n"
                f"The page could not be fetched directly. Based on the URL and title, "
                f"describe what this page likely contains in as much detail as possible."
            )

        content = self._call_ai(prompt)
        filename_stem = _sanitise_filename(page_title)
        return filename_stem, content

    # ── AI call ────────────────────────────────────────────────────────────────

    def _call_ai(self, prompt: str) -> str:
        from core.key_store import load_key, load_model, load_active_provider
        provider = load_active_provider()
        api_key  = load_key(provider)
        model    = load_model(provider)

        if not api_key:
            raise RuntimeError(
                f"No API key for '{provider}'. Go to ⚙ Settings and enter your key."
            )

        if provider == "anthropic":
            return self._call_anthropic(api_key, model, prompt)
        elif provider == "openai":
            return self._call_openai(api_key, model, prompt)
        elif provider == "gemini":
            return self._call_gemini(api_key, model, prompt)
        raise RuntimeError(f"Unknown provider: {provider}")

    def _call_anthropic(self, api_key: str, model: str, prompt: str) -> str:
        payload = json.dumps({
            "model": model, "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
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
            "model": model, "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
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
            print(f"[API ERROR] {msg}", flush=True)
            logger.error(msg)
            raise RuntimeError(msg) from e
        except Exception as e:
            msg = f"API request failed: {e}"
            print(f"[API ERROR] {msg}", flush=True)
            logger.error(msg)
            traceback.print_exc()
            raise RuntimeError(msg) from e
