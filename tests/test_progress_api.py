"""Progress tracker endpoint (feature 13)."""
from __future__ import annotations


def test_progress_requires_auth(client):
    assert client.get("/api/progress/").status_code == 401


def test_progress_counts_tasks_and_completion_rate(client, auth):
    headers = auth()
    task = client.post("/api/tasks/", headers=headers, json={"title": "One"}).get_json()
    client.post("/api/tasks/", headers=headers, json={"title": "Two"})
    client.put(
        f"/api/tasks/{task['taskId']}", headers=headers, json={"isCompleted": True}
    )

    body = client.get("/api/progress/", headers=headers).get_json()
    assert body["totals"]["tasks"] == 2
    assert body["totals"]["completedTasks"] == 1
    assert body["totals"]["pendingTasks"] == 1
    assert body["totals"]["completionRate"] == 0.5
    assert len(body["loadBalance"]) == 7


def test_progress_awards_first_task_achievement(client, auth):
    headers = auth()
    client.post("/api/tasks/", headers=headers, json={"title": "One"})
    body = client.get("/api/progress/", headers=headers).get_json()
    earned = {a["id"] for a in body["achievements"] if a["earned"]}
    assert "first_task" in earned
    assert "ten_tasks" not in earned


def test_progress_streak_counts_mood_logging(client, auth):
    headers = auth()
    client.post("/api/mood/", headers=headers, json={"mood": "good"})
    body = client.get("/api/progress/", headers=headers).get_json()
    assert body["streak"]["current"] >= 1
    assert body["totals"]["moodEntries"] == 1
