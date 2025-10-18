"""Reflection prompt + journal (feature 18)."""
from __future__ import annotations


def test_today_returns_prompt_and_affirmation(client, auth):
    body = client.get("/api/reflections/today", headers=auth()).get_json()
    assert body["prompt"]
    assert body["affirmation"]
    assert body["reflection"] is None


def test_logging_a_reflection_then_reading_it_back(client, auth):
    headers = auth()
    created = client.post(
        "/api/reflections/",
        headers=headers,
        json={"text": "Good focus today", "mood": "good"},
    )
    assert created.status_code == 201
    assert created.get_json()["text"] == "Good focus today"

    today = client.get("/api/reflections/today", headers=headers).get_json()
    assert today["reflection"]["text"] == "Good focus today"


def test_logging_twice_replaces_the_same_day(client, auth):
    headers = auth()
    client.post("/api/reflections/", headers=headers, json={"text": "first"})
    client.post("/api/reflections/", headers=headers, json={"text": "second"})

    listing = client.get("/api/reflections/", headers=headers).get_json()
    assert len(listing) == 1
    assert listing[0]["text"] == "second"


def test_logging_requires_text(client, auth):
    response = client.post("/api/reflections/", headers=auth(), json={})
    assert response.status_code == 400
    assert response.get_json() == {"message": "text is required"}


def test_reflection_is_owner_scoped(client, auth):
    mine = auth("mine@example.com")
    theirs = auth("theirs@example.com")
    entry = client.post(
        "/api/reflections/", headers=theirs, json={"text": "private"}
    ).get_json()
    assert (
        client.get(
            f"/api/reflections/{entry['reflectionId']}", headers=mine
        ).status_code
        == 404
    )
