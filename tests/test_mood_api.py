"""Mood journal, trends, and load suggestions (features 6 & 12)."""
from __future__ import annotations


def test_create_mood_returns_201_with_score(client, auth):
    headers = auth()
    response = client.post("/api/mood/", headers=headers, json={"mood": "great"})
    assert response.status_code == 201
    body = response.get_json()
    assert body["mood"] == "great"
    assert body["score"] == 5
    assert body["moodId"]


def test_create_mood_requires_the_mood_field(client, auth):
    response = client.post("/api/mood/", headers=auth(), json={"note": "x"})
    assert response.status_code == 400
    assert response.get_json() == {"message": "mood is required"}


def test_mood_feed_is_newest_first_and_deletable(client, auth):
    headers = auth()
    first = client.post("/api/mood/", headers=headers, json={"mood": "low"}).get_json()
    client.post("/api/mood/", headers=headers, json={"mood": "good"})

    listing = client.get("/api/mood/", headers=headers).get_json()
    assert [item["mood"] for item in listing] == ["good", "low"]

    deleted = client.delete(f"/api/mood/{first['moodId']}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.get_json() == {"message": "Mood entry deleted"}


def test_mood_trends_summarises_the_window(client, auth):
    headers = auth()
    client.post("/api/mood/", headers=headers, json={"mood": "good", "energy": 4})
    client.post("/api/mood/", headers=headers, json={"mood": "awful"})

    body = client.get("/api/mood/trends?days=7", headers=headers).get_json()
    assert body["range"]["days"] == 7
    assert len(body["series"]) == 7
    assert body["entries"] == 2
    assert body["averageScore"] == 2.5  # good=4, awful=1 → (4 + 1) / 2
    assert body["distribution"] == {"good": 1, "awful": 1}
    assert body["streak"] == 1


def test_mood_trends_rejects_bad_window(client, auth):
    response = client.get("/api/mood/trends?days=0", headers=auth())
    assert response.status_code == 400
    assert response.get_json() == {"message": "days must be between 1 and 365"}


def test_mood_load_suggestion_uses_supplied_mood(client, auth):
    body = client.post(
        "/api/mood/suggestions", headers=auth(), json={"mood": "awful", "energy": 1}
    ).get_json()
    assert body["suggestedLoad"] == "light"
    assert body["score"] == 1


def test_mood_load_suggestion_falls_back_to_latest_logged(client, auth):
    headers = auth()
    client.post("/api/mood/", headers=headers, json={"mood": "great"})
    body = client.post("/api/mood/suggestions", headers=headers, json={}).get_json()
    assert body["suggestedLoad"] == "stretch"


def test_get_single_mood_returns_404_for_other_user(client, auth):
    mine = auth("mine@example.com")
    theirs = auth("theirs@example.com")
    entry = client.post("/api/mood/", headers=theirs, json={"mood": "good"}).get_json()
    response = client.get(f"/api/mood/{entry['moodId']}", headers=mine)
    assert response.status_code == 404
