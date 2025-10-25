"""OCR client for quick-add from camera/scans (feature 11).

Uses OCR.space (``/parse/image``) authenticated with an API key
(``KOVA_OCR_API_KEY``). The image is sent as multipart form data with the
file under the ``filename`` field, so uploads are capped at **1 MB** before
any network call — enough for a note/whiteboard photo and inside OCR.space's
free tier limits. No native dependency and no Cloud Storage bucket required.

A missing key raises ``AIConfigError`` (503), an unusable upload raises
``ValidationError`` (400), and provider/transport failures raise ``ValueError``
(callers answer 500) — matching the other provider guards.
"""
from __future__ import annotations

import logging
from typing import Any

import requests
from flask import current_app

from ..core.exceptions import AIConfigError, ValidationError

logger = logging.getLogger(__name__)

_DEFAULT_OCR_URL = "https://api.ocr.space/parse/image"
_DEFAULT_LANGUAGE = "eng"
_MAX_IMAGE_BYTES = 1 * 1024 * 1024  # 1 MiB


def _read_capped(file_stream: Any) -> bytes:
    """Read at most ``_MAX_IMAGE_BYTES``; reject anything larger (never upload it)."""
    content = file_stream.read(_MAX_IMAGE_BYTES + 1)
    if not content:
        raise ValidationError("Image file is empty.")
    if len(content) > _MAX_IMAGE_BYTES:
        raise ValidationError("Image must be 1 MB or smaller.")
    return content


def extract_text_from_image(file_stream: Any, *, filename: str = "upload.jpg") -> str:
    """Return the OCR text for an uploaded image (≤ 1 MB).

    Raises:
        AIConfigError: no OCR key configured (callers answer 503).
        ValidationError: empty or oversized upload (callers answer 400).
        ValueError: transport failure or an unusable OCR response — callers
            decide the HTTP status (the image flow answers 500).
    """
    api_key = current_app.config.get("OCR_API_KEY")
    if not api_key:
        logger.error("ocr_not_configured")
        raise AIConfigError("OCR provider is not configured")

    content = _read_capped(file_stream)
    logger.info("ocr_send_start", extra={"bytes": len(content), "uploadFilename": filename})

    url = current_app.config.get("OCR_URL") or _DEFAULT_OCR_URL
    timeout = int(current_app.config.get("OCR_TIMEOUT_SECONDS") or 60)
    language = current_app.config.get("OCR_LANGUAGE") or _DEFAULT_LANGUAGE

    try:
        response = requests.post(
            url,
            files={"filename": (filename, content)},
            data={"apikey": api_key, "language": language},
            timeout=timeout,
        )
        logger.info(
            "ocr_http_response",
            extra={"status": response.status_code, "contentLength": len(response.content)},
        )
        response.raise_for_status()
        body = response.json()
    except requests.exceptions.RequestException as exc:
        logger.exception("ocr_http_error", extra={"error": str(exc)})
        raise ValueError(f"OCR request failed: {exc}") from exc

    if body.get("IsErroredOnProcessing"):
        message = body.get("ErrorMessage") or "OCR processing failed"
        logger.error("ocr_provider_error", extra={"message": message, "response": body})
        raise ValueError(f"OCR failed: {message}")

    parsed_results = body.get("ParsedResults")
    if not parsed_results:
        logger.error("ocr_no_responses", extra={"response": body})
        raise ValueError("OCR returned no result")

    text = (parsed_results[0].get("ParsedText") or "").strip()
    if not text:
        logger.error("ocr_empty_text")
        raise ValueError("OCR returned no text")

    logger.info("ocr_extracted", extra={"chars": len(text), "bytes": len(content)})
    return text
