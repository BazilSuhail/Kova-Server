"""Offline sync: delta pull + push with tombstones (feature 14)."""
from __future__ import annotations


def test_pull_returns_all_collections(client, auth):
    headers = auth()
    client.post("/api/tasks/", headers=headers, json={"title": "Offline one"})
    client.post("/api/planner/", headers=headers, json={"date": "2026-10-05"})

    body = client.post("/api/sync/pull", headers=headers, json={}).get_json()
    assert body["full"] is True
    assert len(body["tasks"]) == 1
    assert len(body["planner"]) == 1
    assert body["deleted"] == []
    assert body["serverTime"]


def test_pull_since_filters_older_documents(client, auth):
    headers = auth()
    client.post("/api/tasks/", headers=headers, json={"title": "Old"})
    cursor = client.post("/api/sync/pull", headers=headers, json={}).get_json()[
        "serverTime"
    ]
    client.post("/api/tasks/", headers=headers, json={"title": "New"})

    body = client.post("/api/sync/pull", headers=headers, json={"since": cursor}).get_json()
    titles = [task["title"] for task in body["tasks"]]
    assert titles == ["New"]


def test_push_creates_client_side_document(client, auth):
    headers = auth()
    document = {
        "taskId": "client-task-1",
        "title": "Made offline",
        "isCompleted": False,
    }
    body = client.post(
        "/api/sync/push", headers=headers, json={"changes": {"tasks": [document]}}
    ).get_json()
    assert body["applied"]["tasks"] == 1

    tasks = client.get("/api/tasks/", headers=headers).get_json()
    assert [t["title"] for t in tasks] == ["Made offline"]


def test_push_records_deletion_tombstone(client, auth):
    headers = auth()
    task = client.post("/api/tasks/", headers=headers, json={"title": "Bye"}).get_json()
    client.post(
        "/api/sync/push",
        headers=headers,
        json={"changes": {"deletions": [{"collection": "tasks", "id": task["taskId"]}]}},
    )
    assert client.get("/api/tasks/", headers=headers).get_json() == []

    body = client.post("/api/sync/pull", headers=headers, json={}).get_json()
    assert body["deleted"][0]["docId"] == task["taskId"]


def test_push_ignores_document_for_unknown_subtask_task(client, auth):
    headers = auth()
    body = client.post(
        "/api/sync/push",
        headers=headers,
        json={
            "changes": {
                "subtasks": [{"subtaskId": "s1", "taskId": "does-not-exist", "title": "x"}]
            }
        },
    ).get_json()
    assert body["applied"]["subtasks"] == 0
    assert body["skipped"]
