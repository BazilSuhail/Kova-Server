"""AssemblyAI client: upload audio, then poll until transcription completes."""
from __future__ import annotations

import logging
import time
from typing import Any, BinaryIO

import requests
from flask import current_app

logger = logging.getLogger(__name__)

_ASSEMBLYAI_BASE_URL = "https://api.assemblyai.com/v2"
_POLL_INTERVAL_SECONDS = 3
# Bounded so a stuck upstream fails the request instead of holding a thread
# forever (the legacy loop had no ceiling).
_MAX_POLL_ATTEMPTS = 100


def _headers() -> dict[str, str]:
    return {"authorization": current_app.config["ASSEMBLYAI_API_KEY"]}


def upload_audio(file_stream: BinaryIO | Any) -> str:
    """Upload raw audio bytes and return the hosted URL AssemblyAI can fetch."""
    res = requests.post(
        f"{_ASSEMBLYAI_BASE_URL}/upload",
        headers=_headers(),
        data=file_stream,
        timeout=120,
    )
    res.raise_for_status()
    upload_url: str = res.json()["upload_url"]
    return upload_url


def transcribe_audio(audio_url: str) -> str:
    """Poll AssemblyAI until the transcript is ready and return its text.

    Raises:
        Exception: when AssemblyAI reports a failed transcription or does not
            finish within the poll ceiling (both surface as HTTP 500 upstream,
            matching the legacy contract).
    """
    headers = _headers()
    trans_resp = requests.post(
        f"{_ASSEMBLYAI_BASE_URL}/transcript",
        json={"audio_url": audio_url},
        headers=headers,
        timeout=30,
    )
    trans_resp.raise_for_status()
    transcript_id = trans_resp.json()["id"]

    for _ in range(_MAX_POLL_ATTEMPTS):
        status_res = requests.get(
            f"{_ASSEMBLYAI_BASE_URL}/transcript/{transcript_id}",
            headers=headers,
            timeout=30,
        ).json()
        status = status_res.get("status")
        if status == "completed":
            text: str = status_res["text"]
            logger.info("transcription_completed", extra={"transcript_id": transcript_id})
            return text
        if status == "error":
            raise Exception("Transcription failed.")
        time.sleep(_POLL_INTERVAL_SECONDS)

    raise Exception("Transcription timed out.")
