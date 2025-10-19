"""OCR client for quick-add from camera/scans (feature 11).

Uses OCR.space by default (``KOVA_OCR_URL``) — a plain multipart HTTP call,
so no heavy native dependency. A missing key raises ``AIConfigError`` (503),
matching the other provider guards: server misconfiguration must not look like
client error.
"""
from __future__ import annotations

import logging
from typing import Any

import requests
from flask import current_app

from ..core.exceptions import AIConfigError

logger = logging.getLogger(__name__)

_DEFAULT_OCR_URL = "https://api.ocr.space/parse/image"


def extract_text_from_image(file_stream: Any, *, filename: str = "upload.jpg") -> str:
    """Return the OCR text for an uploaded image.

    Raises:
        AIConfigError: no OCR key configured (callers answer 503).
        ValueError: transport failure or an unusable OCR response — callers
            decide the HTTP status (the image flow answers 400/500).
    """
    api_key = current_app.config.get("OCR_API_KEY")
    if not api_key:
        logger.error("ocr_not_configured")
        raise AIConfigError("OCR provider is not configured")

    url = current_app.config.get("OCR_URL") or _DEFAULT_OCR_URL
    timeout = int(current_app.config.get("OCR_TIMEOUT_SECONDS") or 60)
    try:
        response = requests.post(
            url,
            headers={"apikey": api_key},
            files={"file": (filename, file_stream)},
            data={"language": "eng", "isOverlayRequired": "false", "OCREngine": "2"},
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.exceptions.RequestException as exc:
        raise ValueError(f"OCR request failed: {exc}") from exc

    if payload.get("IsErroredOnProcessing"):
        message = payload.get("ErrorMessage") or "OCR processing failed"
        if isinstance(message, list):
            message = "; ".join(str(item) for item in message)
        raise ValueError(str(message))

    results = payload.get("ParsedResults") or []
    text = "\n".join(
        (result.get("ParsedText") or "").strip() for result in results
    ).strip()
    if not text:
        raise ValueError("OCR returned no text")
    logger.info("ocr_extracted", extra={"chars": len(text)})
    return text
