"""AssemblyAI client: upload audio, then poll until transcription completes."""
from __future__ import annotations

import logging
import time
from typing import Any, BinaryIO

import requests
from flask import current_app

from ..core.exceptions import AIConfigError

logger = logging.getLogger(__name__)

_ASSEMBLYAI_BASE_URL = "https://api.assemblyai.com/v2"
_POLL_INTERVAL_SECONDS = 3
# Bounded so a stuck upstream fails the request instead of holding a thread
# forever (the legacy loop had no ceiling).
_MAX_POLL_ATTEMPTS = 100


def _headers() -> dict[str, str]:
    api_key = current_app.config.get("ASSEMBLYAI_API_KEY")
    if not api_key:
        # Server misconfiguration → 503, not an upstream 401 dressed up as a
        # client error (or a bare TypeError from a None header).
        logger.error("assemblyai_not_configured")
        raise AIConfigError("AI provider is not configured")
    return {"authorization": api_key}


def upload_audio(file_stream: BinaryIO | Any) -> str:
    """Upload raw audio bytes and return the hosted URL AssemblyAI can fetch."""
    logger.info("assemblyai_upload_start")
    content = file_stream.read()
    logger.info("assemblyai_upload_content_read", extra={"bytes": len(content)})
    res = requests.post(
        f"{_ASSEMBLYAI_BASE_URL}/upload",
        headers={**_headers(), "content-type": "application/octet-stream"},
        data=content,
        timeout=120,
    )
    logger.info("assemblyai_upload_response", extra={"status": res.status_code})
    res.raise_for_status()
    upload_url: str = res.json()["upload_url"]
    logger.info("assemblyai_upload_done", extra={"hasUrl": bool(upload_url)})
    return upload_url


def transcribe_audio(audio_url: str) -> str:
    """Poll AssemblyAI until the transcript is ready and return its text.

    Raises:
        Exception: when AssemblyAI reports a failed transcription or does not
            finish within the poll ceiling (both surface as HTTP 500 upstream,
            matching the legacy contract).
    """
    headers = _headers()
    logger.info("assemblyai_transcribe_start", extra={"audioUrl": audio_url})
    trans_resp = requests.post(
        f"{_ASSEMBLYAI_BASE_URL}/transcript",
        json={"audio_url": audio_url},
        headers=headers,
        timeout=30,
    )
    logger.info("assemblyai_transcribe_response", extra={"status": trans_resp.status_code})
    trans_resp.raise_for_status()
    transcript_id = trans_resp.json()["id"]
    logger.info("assemblyai_transcribe_polling", extra={"transcriptId": transcript_id})

    for _ in range(_MAX_POLL_ATTEMPTS):
        status_res = requests.get(
            f"{_ASSEMBLYAI_BASE_URL}/transcript/{transcript_id}",
            headers=headers,
            timeout=30,
        ).json()
        status = status_res.get("status")
        logger.info("assemblyai_poll", extra={"status": status})
        if status == "completed":
            text: str = status_res["text"]
            logger.info("transcription_completed", extra={"transcript_id": transcript_id, "chars": len(text)})
            return text
        if status == "error":
            err_msg = status_res.get("error", "Transcription failed.")
            logger.error("transcription_error", extra={"transcriptId": transcript_id, "error": err_msg, "status": status_res})
            raise Exception(f"Transcription failed: {err_msg}")
        time.sleep(_POLL_INTERVAL_SECONDS)

    logger.error("transcription_timeout", extra={"transcriptId": transcript_id})
    raise Exception("Transcription timed out.")
