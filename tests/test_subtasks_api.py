"""Subtask endpoints with the LLM generator stubbed (no network in tests)."""
from __future__ import annotations

_STUBBED_SUBTASKS = ["Research sources", "Write first draft", "Review and submit"]


def _create_task(client, headers, title="Big project", description="Long description"):
    response = client.post(
        "/api/tasks/",
        headers=headers,
        json={"title": title, "description": description},
    )
    assert response.status_code == 201
    return response.get_json()


def test_create_subtasks_returns_201_and_flags_parent(client, auth, monkeypatch):
    monkeypatch.setattr(
        "app.services.subtask_service.generate_subtasks_from_description",
        lambda _description: _STUBBED_SUBTASKS,
    )
    headers = auth()
    task = _create_task(client, headers)

    response = client.post(
        "/api/subtasks/create", headers=headers, json={"taskId": task["taskId"]}
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["subTasks"] == _STUBBED_SUBTASKS
    assert body["done"] is False

    parent = client.get(f"/api/tasks/{task['taskId']}", headers=headers).get_json()
    assert parent["hasSubtasks"] is True


def test_create_subtasks_returns_400_when_task_id_missing(client, auth):
    headers = auth()
    response = client.post("/api/subtasks/create", headers=headers, json={})
    assert response.status_code == 400
    assert response.get_json() == {"message": "taskId is required"}


def test_create_subtasks_returns_404_when_task_missing(client, auth, monkeypatch):
    monkeypatch.setattr(
        "app.services.subtask_service.generate_subtasks_from_description",
        lambda _description: _STUBBED_SUBTASKS,
    )
    headers = auth()
    response = client.post(
        "/api/subtasks/create",
        headers=headers,
        json={"taskId": "689ffffffffffffffffffff"},
    )
    assert response.status_code == 404
    assert response.get_json() == {"message": "Task not found"}


def test_list_subtasks_returns_404_when_task_missing(client, auth):
    headers = auth()
    response = client.get("/api/subtasks/task/689ffffffffffffffffffff", headers=headers)
    assert response.status_code == 404
    assert response.get_json() == {"message": "Task not found"}


def test_update_subtask_returns_200_when_done_flips(client, auth, monkeypatch):
    monkeypatch.setattr(
        "app.services.subtask_service.generate_subtasks_from_description",
        lambda _description: _STUBBED_SUBTASKS,
    )
    headers = auth()
    task = _create_task(client, headers)
    subtask = client.post(
        "/api/subtasks/create", headers=headers, json={"taskId": task["taskId"]}
    ).get_json()

    response = client.put(
        f"/api/subtasks/{subtask['subtaskId']}", headers=headers, json={"done": True}
    )
    assert response.status_code == 200
    assert response.get_json() == {"message": "Subtask updated"}


def test_delete_subtasks_for_task_returns_count_and_resets_parent(
    client, auth, monkeypatch
):
    monkeypatch.setattr(
        "app.services.subtask_service.generate_subtasks_from_description",
        lambda _description: _STUBBED_SUBTASKS,
    )
    headers = auth()
    task = _create_task(client, headers)
    client.post(
        "/api/subtasks/create", headers=headers, json={"taskId": task["taskId"]}
    )

    response = client.delete(f"/api/subtasks/task/{task['taskId']}", headers=headers)
    assert response.status_code == 200
    assert (
        "1 subtask(s) deleted" in response.get_json()["message"]
    )

    parent = client.get(f"/api/tasks/{task['taskId']}", headers=headers).get_json()
    assert parent["hasSubtasks"] is False
