"""Extract plain text from an uploaded PDF.

``PyPDF2`` is imported lazily: it is a heavy optional dependency, and a missing
package should fail *this endpoint* with a 500 instead of preventing the whole
application from booting (which is what the legacy eager import did).
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def extract_pdf_text(file_stream: Any) -> str:
    """Return the concatenated text of every page in the uploaded PDF.

    Raises:
        RuntimeError: when PyPDF2 is not installed.
        Exception: when the file cannot be parsed (legacy contract: callers
            surface these as HTTP 500).
    """
    try:
        import PyPDF2
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError(
            "PDF support requires the 'PyPDF2' package (pip install -r requirements.txt)"
        ) from exc

    try:
        reader = PyPDF2.PdfReader(file_stream)
        pages: list[str] = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n".join(pages) + ("\n" if pages else "")
    except Exception as exc:
        raise Exception(f"Failed to extract PDF text: {exc}") from exc
