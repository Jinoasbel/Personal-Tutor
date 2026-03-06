"""
key_store.py — Secure local storage for API keys.
Keys are saved to Data/keys.json, obfuscated (not plaintext).
Never committed to version control — add Data/ to your .gitignore.
"""

from __future__ import annotations
import base64
import json
import os
from pathlib import Path

from app_config import Config

_KEY_FILE = Config.DATA_DIR / "keys.json"

# Supported providers
PROVIDERS = ["anthropic", "openai", "gemini"]

PROVIDER_LABELS = {
    "anthropic": "Anthropic (Claude)",
    "openai":    "OpenAI (GPT)",
    "gemini":    "Google (Gemini)",
}

PROVIDER_MODELS = {
    "anthropic": ["claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-haiku-4-5-20251001"],
    "openai":    ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
    "gemini":    ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
}


def _encode(value: str) -> str:
    return base64.b64encode(value.encode()).decode()


def _decode(value: str) -> str:
    try:
        return base64.b64decode(value.encode()).decode()
    except Exception:
        return ""


def _load_raw() -> dict:
    if _KEY_FILE.exists():
        try:
            return json.loads(_KEY_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_raw(data: dict) -> None:
    _KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    _KEY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def save_key(provider: str, api_key: str, model: str = "") -> None:
    """Save an API key and optional model for a provider."""
    data = _load_raw()
    data[provider] = {
        "key":   _encode(api_key),
        "model": model or PROVIDER_MODELS[provider][0],
    }
    _save_raw(data)


def load_key(provider: str) -> str:
    """Return the stored API key for a provider, or empty string."""
    raw = _load_raw().get(provider, {})
    encoded = raw.get("key", "")
    if encoded:
        return _decode(encoded)
    # Fall back to environment variables
    env_map = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai":    "OPENAI_API_KEY",
        "gemini":    "GEMINI_API_KEY",
    }
    return os.environ.get(env_map.get(provider, ""), "")


def load_model(provider: str) -> str:
    """Return the stored model for a provider."""
    raw = _load_raw().get(provider, {})
    return raw.get("model", PROVIDER_MODELS[provider][0])


def load_active_provider() -> str:
    """Return the currently selected provider."""
    return _load_raw().get("_active_provider", "anthropic")


def save_active_provider(provider: str) -> None:
    data = _load_raw()
    data["_active_provider"] = provider
    _save_raw(data)


def has_key(provider: str) -> bool:
    return bool(load_key(provider))
