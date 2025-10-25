"""Curated avatar catalogue served from disk (feature 15 — customisation).

Avatars are plain image files shipped with the server
(``app/assets/avatars``) or dropped in later by the operator.  Clients pick one
by ``avatarId`` and the server stores the resolved URL in ``profilePicture`` —
nothing is uploaded, so there is no abuse surface and the mobile app only has
to point an ``<Image>`` at the returned URL.
"""
from __future__ import annotations

import re
import secrets
from pathlib import Path
from typing import IO

from flask import current_app

from ..core.exceptions import ValidationError

# Anything else in the folder is ignored (README, .DS_Store, …).
ALLOWED_EXTENSIONS = (".svg", ".png", ".jpg", ".jpeg", ".webp")

# Public URL prefix; the image route is intentionally unauthenticated.
URL_PREFIX = "/api/users/avatars"
UPLOAD_URL_PREFIX = f"{URL_PREFIX}/uploads"

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
# Generated names only: ``<userId>_<random hex>.<ext>`` — nothing user-supplied.
_UPLOAD_NAME = re.compile(r"^[A-Za-z0-9]{1,64}_[0-9a-f]{32}\.(?:jpg|png|webp)$")


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


# --- User-uploaded photos -------------------------------------------------


def uploads_dir() -> Path:
    """Resolve the upload folder, honouring ``KOVA_AVATAR_UPLOAD_DIR`` when set."""
    configured = current_app.config.get("AVATAR_UPLOAD_DIR")
    if configured:
        return Path(configured)
    return Path(current_app.instance_path) / "avatar_uploads"


def sniff_image_type(head: bytes) -> str | None:
    """File extension from magic bytes (jpeg/png/webp); ``None`` for anything else."""
    if head.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return None


def save_upload(user_id: str, stream: IO[bytes]) -> str:
    """Validate and store an uploaded photo; return its public URL.

    The client's filename and content type are ignored: the type comes from
    the bytes themselves and the stored name is generated.
    """
    data = stream.read(MAX_UPLOAD_BYTES + 1)
    if not data:
        raise ValidationError("Image file is empty")
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValidationError("Image must be 5 MB or smaller")
    extension = sniff_image_type(data[:12])
    if extension is None:
        raise ValidationError("Image must be a JPEG, PNG or WebP file")
    name = f"{user_id}_{secrets.token_hex(16)}.{extension}"
    if not _UPLOAD_NAME.match(name):  # user ids are ObjectId hex; refuse anything odd
        raise ValidationError("Cannot store avatar for this account")
    directory = uploads_dir()
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_bytes(data)
    return f"{UPLOAD_URL_PREFIX}/{name}"


def upload_file(filename: str) -> Path | None:
    """Resolve a request filename to a stored upload; strict name check (no traversal)."""
    if not _UPLOAD_NAME.match(filename):
        return None
    path = uploads_dir() / filename
    return path if path.is_file() else None


def delete_upload(user_id: str, url: str | None) -> None:
    """Remove ``url``'s file if it is one of *this user's* uploads (else no-op)."""
    if not url or not url.startswith(f"{UPLOAD_URL_PREFIX}/"):
        return
    name = url.rsplit("/", 1)[-1]
    if not name.startswith(f"{user_id}_"):
        return  # a profile may point at someone else's URL; never delete theirs
    path = upload_file(name)
    if path is not None:
        path.unlink(missing_ok=True)
