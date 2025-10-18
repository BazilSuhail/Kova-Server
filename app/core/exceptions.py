"""Error hierarchy translated into JSON responses by the app's error handlers.

Routes raise nothing themselves for domain failures; services raise these so
status codes are defined in exactly one place and handlers stay free of
try/except boilerplate.  Status codes mirror the legacy per-route behaviour
(400/401/404/415) so existing clients see no contract change.
"""
from __future__ import annotations


class AppError(Exception):
    """Base class for every error the API maps to a JSON ``{"message": ...}``."""

    status_code: int = 500

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code

    def to_payload(self) -> dict[str, str]:
        """Shape the error exactly the way clients already expect it."""
        return {"message": self.message}


class ValidationError(AppError):
    """Input the caller can fix (mirrors the legacy 400 paths)."""

    status_code = 400


class AuthenticationError(AppError):
    """Bad or missing credentials (mirrors the legacy 401 paths)."""

    status_code = 401


class NotFoundError(AppError):
    """Resource missing or not owned by the caller (mirrors the legacy 404 paths)."""

    status_code = 404


class UnsupportedMediaTypeError(AppError):
    """Endpoint received a content type it does not accept (legacy 415 paths)."""

    status_code = 415


class AIConfigError(AppError):
    """An AI provider (Groq/AssemblyAI) has no API key configured.

    This is server misconfiguration, not client input — every AI flow answers
    503 with a stable message instead of forwarding ``Bearer None`` upstream and
    reporting the resulting 401 as the caller's fault.
    """

    status_code = 503


class AIProviderError(AppError):
    """The AI provider answered, but the response was unusable (502)."""

    status_code = 502
