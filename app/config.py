"""Typed, immutable application settings sourced from the environment (12-factor).

Canonical names follow the project convention ``ZENFLOW_<DOMAIN>_<KEY>``; every
legacy name (``MONGO_URI``, ``JWT_SECRET_KEY``, ...) is still accepted so the
existing ``.env`` and Railway/Heroku config keep working unchanged.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Preserved verbatim from the legacy ``Config``: changing it would invalidate
# every token ever issued to clients.
DEFAULT_JWT_SECRET = "kasnkdjnaskjdfnskdjf6454sdf"
DEFAULT_MONGO_URI = "mongodb://localhost:27017/zenflow"
DEFAULT_GROQ_LLM_URL = "https://api.groq.com/openai/v1/chat/completions"


def _env(name: str, *legacy_names: str, default: str | None = None) -> str | None:
    """Read ``name`` first, then legacy aliases, else ``default``.

    Present-but-empty values are returned as-is (``is not None``) to mirror the
    legacy ``os.getenv`` behaviour exactly — an empty key must not silently
    fall back to a default.
    """
    for key in (name, *legacy_names):
        value = os.environ.get(key)
        if value is not None:
            return value
    return default


@dataclass(frozen=True)
class Settings:
    """Immutable runtime configuration; build via :meth:`from_env`."""

    env: str
    mongo_uri: str
    jwt_secret: str
    jwt_expires_seconds: int
    log_level: str
    assemblyai_api_key: str | None
    groq_api_key: str | None
    groq_llm_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        """Load ``.env`` then read settings, preferring ``ZENFLOW_*`` names."""
        load_dotenv()
        return cls(
            env=_env("ZENFLOW_ENV", "FLASK_ENV", default="production") or "production",
            mongo_uri=_env("ZENFLOW_MONGO_URI", "MONGO_URI", default=DEFAULT_MONGO_URI)
            or DEFAULT_MONGO_URI,
            jwt_secret=_env("ZENFLOW_JWT_SECRET", "JWT_SECRET_KEY", default=DEFAULT_JWT_SECRET)
            or DEFAULT_JWT_SECRET,
            jwt_expires_seconds=int(
                _env("ZENFLOW_JWT_EXPIRES_SECONDS", default="3600") or "3600"
            ),
            log_level=(_env("ZENFLOW_LOG_LEVEL", "LOG_LEVEL", default="INFO") or "INFO").upper(),
            assemblyai_api_key=_env("ZENFLOW_ASSEMBLYAI_API_KEY", "ASSEMBLYAI_API_KEY"),
            groq_api_key=_env("ZENFLOW_GROQ_API_KEY", "GROQ_API_KEY"),
            groq_llm_url=_env("ZENFLOW_GROQ_LLM_URL", "GROQ_LLM_URL", default=DEFAULT_GROQ_LLM_URL)
            or DEFAULT_GROQ_LLM_URL,
        )

    @classmethod
    def for_testing(cls) -> "Settings":
        """Deterministic settings for the test suite (no ``.env`` read)."""
        return cls(
            env="test",
            mongo_uri="mongodb://localhost:27017/zenflow_test",
            jwt_secret="test-secret-key-that-is-at-least-32-bytes-long",
            jwt_expires_seconds=3600,
            log_level="WARNING",
            assemblyai_api_key=None,
            groq_api_key=None,
            groq_llm_url=DEFAULT_GROQ_LLM_URL,
        )

    @property
    def uses_default_jwt_secret(self) -> bool:
        """True when the insecure built-in secret is still active."""
        return self.jwt_secret == DEFAULT_JWT_SECRET
