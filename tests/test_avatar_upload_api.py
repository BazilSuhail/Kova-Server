"""User-uploaded avatar photos: magic-byte validation, storage, cleanup."""
from __future__ import annotations

import io

import pytest
from app.utils.avatars import MAX_UPLOAD_BYTES, sniff_image_type

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
WEBP = b"RIFF\x24\x00\x00\x00WEBPVP8 " + b"\x00" * 64


@pytest.fixture(autouse=True)
def _upload_dir(app, tmp_path):
    app.config["AVATAR_UPLOAD_DIR"] = str(tmp_path)
    return tmp_path


def _upload(client, headers, data: bytes, filename: str = "photo.png"):
    return client.post(
        "/api/users/profile/avatar",
        headers=headers,
        data={"file": (io.BytesIO(data), filename)},
        content_type="multipart/form-data",
    )


def test_sniff_accepts_only_jpeg_png_webp():
    assert sniff_image_type(PNG[:12]) == "png"
    assert sniff_image_type(JPEG[:12]) == "jpg"
    assert sniff_image_type(WEBP[:12]) == "webp"
    assert sniff_image_type(b"GIF89a......") is None
    assert sniff_image_type(b"<svg xmlns=") is None


def test_upload_sets_profile_picture_and_serves_file(client, auth, tmp_path):
    headers = auth()
    response = _upload(client, headers, PNG)
    assert response.status_code == 200
    url = response.get_json()["profilePicture"]
    assert url.startswith("/api/users/avatars/uploads/")
    assert url.endswith(".png")
    assert "photo" not in url  # client filename is never used

    served = client.get(url)  # public, like catalogue avatars
    assert served.status_code == 200
    assert served.data == PNG
    assert len(list(tmp_path.iterdir())) == 1


def test_type_comes_from_bytes_not_extension(client, auth):
    response = _upload(client, auth(), b"<?php echo 'hi'; ?>" * 4, "evil.png")
    assert response.status_code == 400
    assert response.get_json() == {"message": "Image must be a JPEG, PNG or WebP file"}

    webp = _upload(client, auth("w@example.com"), WEBP, "photo.jpg")
    assert webp.status_code == 200
    assert webp.get_json()["profilePicture"].endswith(".webp")


def test_upload_rejects_oversized_and_missing_files(client, auth):
    headers = auth()
    too_big = PNG + b"\x00" * (MAX_UPLOAD_BYTES + 1 - len(PNG))
    response = _upload(client, headers, too_big)
    assert response.status_code == 400
    assert response.get_json() == {"message": "Image must be 5 MB or smaller"}

    missing = client.post(
        "/api/users/profile/avatar", headers=headers, data={},
        content_type="multipart/form-data",
    )
    assert missing.status_code == 400

    assert _upload(client, headers, b"").status_code == 400


def test_upload_requires_auth(client):
    assert _upload(client, {}, PNG).status_code == 401


def test_new_upload_deletes_previous_one(client, auth, tmp_path):
    headers = auth()
    first = _upload(client, headers, PNG).get_json()["profilePicture"]
    second = _upload(client, headers, JPEG).get_json()["profilePicture"]
    assert first != second
    assert client.get(first).status_code == 404
    assert client.get(second).status_code == 200
    assert len(list(tmp_path.iterdir())) == 1


def test_choosing_catalogue_avatar_or_deleting_account_removes_upload(
    client, auth, tmp_path
):
    headers = auth()
    _upload(client, headers, PNG)
    client.put("/api/users/profile", headers=headers, json={"avatarId": "avatar2"})
    assert list(tmp_path.iterdir()) == []

    _upload(client, headers, PNG)
    assert client.delete("/api/users/profile", headers=headers).status_code == 200
    assert list(tmp_path.iterdir()) == []


def test_pointing_profile_at_someone_elses_upload_never_deletes_it(client, auth, tmp_path):
    owner_url = _upload(client, auth("a@example.com"), PNG).get_json()["profilePicture"]
    other = auth("b@example.com")
    client.put("/api/users/profile", headers=other, json={"profilePicture": owner_url})
    client.put("/api/users/profile", headers=other, json={"avatarId": "avatar1"})
    assert client.get(owner_url).status_code == 200


@pytest.mark.parametrize(
    "name",
    ["..%2F..%2Fconfig.py", "abc.png", "x_" + "0" * 32 + ".svg", "%2e%2e"],
)
def test_upload_route_only_serves_generated_names(client, name):
    assert client.get(f"/api/users/avatars/uploads/{name}").status_code == 404
