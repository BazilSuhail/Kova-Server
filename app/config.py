"""Typed, immutable application settings sourced from the environment (12-factor).

Canonical names follow the project convention ``KOVA_<DOMAIN>_<KEY>``; every
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
DEFAULT_MONGO_URI = "mongodb://localhost:27017/kova"
DEFAULT_GROQ_LLM_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_OCR_URL = "https://api.ocr.space/parse/image"
DEFAULT_PUSH_URL = "https://exp.host/--/api/v2/push/send"

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


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


def _parse_origins(raw: str | None) -> tuple[str, ...]:
    """Split a comma-separated CORS allowlist; unset/empty falls back to ``*``."""
    if not raw:
        return ("*",)
    origins = tuple(part.strip() for part in raw.split(",") if part.strip())
    return origins or ("*",)


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
    # --- Sprint A hardening knobs (all optional, sensible defaults) ---
    cors_origins: tuple[str, ...] = ("*",)
    # Console renderer: "text" (emoji UI, default) or "json" for log aggregators.
    log_format: str = "text"
    max_upload_mb: int = 16
    allow_insecure_jwt: bool = False
    # --- Sprint B: refresh-token lifetime (7 days) ---
    jwt_refresh_expires_seconds: int = 604800
    # --- Sprint C: rate limiting + error tracking ---
    rate_limit_enabled: bool = True
    rate_limit_default: str = "600 per minute"
    rate_limit_auth: str = "60 per minute"
    rate_limit_storage_uri: str = "memory://"
    sentry_dsn: str | None = None
    sentry_traces_sample_rate: float = 0.0
    # --- Sprint D: AI provider knobs ---
    groq_model: str = "llama-3.3-70b-versatile"
    llm_timeout_seconds: int = 60
    # --- Sprint E: performance ---
    compress_enabled: bool = True
    # --- Sprint F: life-assistant features ---
    # Local keyword categoriser runs on every manual create (no network, no key).
    auto_categorize: bool = True
    ocr_api_key: str | None = None
    ocr_url: str = DEFAULT_OCR_URL
    ocr_timeout_seconds: int = 60
    # Expo push delivery for scheduled reminders/nudges.
    push_enabled: bool = True
    push_url: str = DEFAULT_PUSH_URL
    push_access_token: str | None = None
    # In-process APScheduler that fires due reminders. Off in tests.
    scheduler_enabled: bool = True
    scheduler_interval_seconds: int = 30
    # Folder holding the selectable avatar files (default: ``app/assets/avatars``).
    avatar_dir: str | None = None

    @classmethod
    def from_env(cls) -> Settings:
        """Load ``.env`` then read settings, preferring ``KOVA_*`` names."""
        load_dotenv()
        return cls(
            env=_env("KOVA_ENV", "FLASK_ENV", default="production") or "production",
            mongo_uri=_env("KOVA_MONGO_URI", "MONGO_URI", default=DEFAULT_MONGO_URI)
            or DEFAULT_MONGO_URI,
            jwt_secret=_env("KOVA_JWT_SECRET", "JWT_SECRET_KEY", default=DEFAULT_JWT_SECRET)
            or DEFAULT_JWT_SECRET,
            jwt_expires_seconds=int(
                _env("KOVA_JWT_EXPIRES_SECONDS", default="3600") or "3600"
            ),
            log_level=(_env("KOVA_LOG_LEVEL", "LOG_LEVEL", default="INFO") or "INFO").upper(),
            log_format=(_env("KOVA_LOG_FORMAT", default="text") or "text").lower(),
            assemblyai_api_key=_env("KOVA_ASSEMBLYAI_API_KEY", "ASSEMBLYAI_API_KEY"),
            groq_api_key=_env("KOVA_GROQ_API_KEY", "GROQ_API_KEY"),
            groq_llm_url=_env("KOVA_GROQ_LLM_URL", "GROQ_LLM_URL", default=DEFAULT_GROQ_LLM_URL)
            or DEFAULT_GROQ_LLM_URL,
            cors_origins=_parse_origins(_env("KOVA_CORS_ORIGINS")),
            max_upload_mb=int(_env("KOVA_MAX_UPLOAD_MB", default="16") or "16"),
            allow_insecure_jwt=(
                (_env("KOVA_ALLOW_INSECURE_JWT", default="") or "").strip().lower()
                in _TRUE_VALUES
            ),
            jwt_refresh_expires_seconds=int(
                _env("KOVA_JWT_REFRESH_EXPIRES_SECONDS", default="604800")
                or "604800"
            ),
            rate_limit_enabled=(
                (_env("KOVA_RATELIMIT_ENABLED", default="") or "").strip().lower()
                not in ("0", "false", "no", "off")
            ),
            rate_limit_default=_env(
                "KOVA_RATELIMIT_DEFAULT", default="600 per minute"
            )
            or "600 per minute",
            rate_limit_auth=_env("KOVA_RATELIMIT_AUTH", default="60 per minute")
            or "60 per minute",
            rate_limit_storage_uri=_env(
                "KOVA_RATELIMIT_STORAGE_URI", default="memory://"
            )
            or "memory://",
            sentry_dsn=_env("KOVA_SENTRY_DSN", "SENTRY_DSN") or None,
            sentry_traces_sample_rate=float(
                _env("KOVA_SENTRY_TRACES_SAMPLE_RATE", default="0") or "0"
            ),
            groq_model=_env("KOVA_GROQ_MODEL", default="llama-3.3-70b-versatile")
            or "llama-3.3-70b-versatile",
            llm_timeout_seconds=int(
                _env("KOVA_LLM_TIMEOUT_SECONDS", default="60") or "60"
            ),
            compress_enabled=(
                (_env("KOVA_COMPRESS_ENABLED", default="") or "").strip().lower()
                not in ("0", "false", "no", "off")
            ),
            auto_categorize=(
                (_env("KOVA_AUTO_CATEGORIZE", default="") or "").strip().lower()
                not in ("0", "false", "no", "off")
            ),
            ocr_api_key=_env("KOVA_OCR_API_KEY", "OCR_API_KEY"),
            ocr_url=_env("KOVA_OCR_URL", default=DEFAULT_OCR_URL) or DEFAULT_OCR_URL,
            ocr_timeout_seconds=int(
                _env("KOVA_OCR_TIMEOUT_SECONDS", default="60") or "60"
            ),
            push_enabled=(
                (_env("KOVA_PUSH_ENABLED", default="") or "").strip().lower()
                not in ("0", "false", "no", "off")
            ),
            push_url=_env("KOVA_PUSH_URL", default=DEFAULT_PUSH_URL) or DEFAULT_PUSH_URL,
            push_access_token=_env("KOVA_PUSH_ACCESS_TOKEN"),
            scheduler_enabled=(
                (_env("KOVA_SCHEDULER_ENABLED", default="") or "").strip().lower()
                not in ("0", "false", "no", "off")
            ),
            scheduler_interval_seconds=int(
                _env("KOVA_SCHEDULER_INTERVAL_SECONDS", default="30") or "30"
            ),
            avatar_dir=_env("KOVA_AVATAR_DIR") or None,
        )

    @classmethod
    def for_testing(cls) -> Settings:
        """Deterministic settings for the test suite (no ``.env`` read)."""
        return cls(
            env="test",
            mongo_uri="mongodb://localhost:27017/kova_test",
            jwt_secret="test-secret-key-that-is-at-least-32-bytes-long",
            jwt_expires_seconds=3600,
            log_level="WARNING",
            assemblyai_api_key=None,
            groq_api_key=None,
            groq_llm_url=DEFAULT_GROQ_LLM_URL,
            # Tests must never start a background scheduler or hit push providers.
            scheduler_enabled=False,
            push_enabled=False,
        )

    @property
    def uses_default_jwt_secret(self) -> bool:
        """True when the insecure built-in secret is still active."""
        return self.jwt_secret == DEFAULT_JWT_SECRET
