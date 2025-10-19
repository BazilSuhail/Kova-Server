"""Curated avatar catalogue served from disk (feature 15 — customisation).

Avatars are plain image files shipped with the server
(``app/assets/avatars``) or dropped in later by the operator.  Clients pick one
by ``avatarId`` and the server stores the resolved URL in ``profilePicture`` —
nothing is uploaded, so there is no abuse surface and the mobile app only has
to point an ``<Image>`` at the returned URL.
"""
from __future__ import annotations

from pathlib import Path

from flask import current_app

# Anything else in the folder is ignored (README, .DS_Store, …).
ALLOWED_EXTENSIONS = (".svg", ".png", ".jpg", ".jpeg", ".webp")

# Public URL prefix; the image route is intentionally unauthenticated.
URL_PREFIX = "/api/users/avatars"


def avatars_dir() -> Path:
    """Resolve the avatar folder, honouring ``KOVA_AVATAR_DIR`` when set."""
    configured = current_app.config.get("AVATAR_DIR")
    if configured:
        return Path(configured)
    return Path(current_app.root_path) / "assets" / "avatars"


def _candidates() -> list[Path]:
    directory = avatars_dir()
    if not directory.is_dir():
        return []
    files = [
        entry
        for entry in directory.iterdir()
        if entry.is_file() and entry.suffix.lower() in ALLOWED_EXTENSIONS
    ]
    return sorted(files, key=lambda entry: (entry.stem.lower(), entry.suffix.lower()))


def avatar_url(filename: str) -> str:
    return f"{URL_PREFIX}/{filename}"


def list_avatars() -> list[dict[str, str]]:
    """Catalogue of selectable avatars (id + filename + URL)."""
    return [
        {"id": entry.stem, "filename": entry.name, "url": avatar_url(entry.name)}
        for entry in _candidates()
    ]


def resolve_avatar_id(value: str) -> str | None:
    """Map an ``avatarId`` (``avatar1``), filename or full URL to its URL.

    Returns ``None`` when nothing matches so the service can reject it with a
    400 instead of silently storing a broken picture.
    """
    candidate = (value or "").strip()
    if not candidate:
        return None
    name = candidate.rsplit("/", 1)[-1]
    stem = Path(name).stem
    for entry in _candidates():
        if entry.name == name or entry.stem == candidate or entry.stem == stem:
            return avatar_url(entry.name)
    return None


def avatar_file(filename: str) -> Path | None:
    """Resolve a request filename to a real file, refusing path traversal."""
    name = Path(filename).name
    for entry in _candidates():
        if entry.name == name:
            return entry
    return None
