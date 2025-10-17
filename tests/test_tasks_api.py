"""Task endpoints: CRUD, validation, per-user isolation, NLP content-type rules."""
from __future__ import annotations


def _create_task(client, headers, title="Write the report"):
    response = client.post("/api/tasks/", headers=headers, json={"title": title})
    assert response.status_code == 201
    return response.get_json()


def test_create_task_returns_201_when_title_present(client, auth):
    headers = auth()
    task = _create_task(client, headers)
    assert task["title"] == "Write the report"
    assert task["isCompleted"] is False
    assert task["createdFrom"] == "manual"
    assert task["hasSubtasks"] is False


def test_create_task_returns_400_when_title_missing(client, auth):
    headers = auth()
    response = client.post("/api/tasks/", headers=headers, json={"description": "x"})
    assert response.status_code == 400
    assert response.get_json() == {"message": "Title required"}


def test_list_tasks_returns_only_callers_tasks(client, auth):
    alice = auth(email="alice@example.com")
    bob = auth(email="bob@example.com")
    _create_task(client, alice, title="Alice task")
    listing = client.get("/api/tasks/", headers=bob)
    assert listing.status_code == 200
    assert listing.get_json() == []


def test_get_task_returns_404_when_task_belongs_to_other_user(client, auth):
    alice = auth(email="alice@example.com")
    bob = auth(email="bob@example.com")
    task = _create_task(client, alice)
    response = client.get(f"/api/tasks/{task['taskId']}", headers=bob)
    assert response.status_code == 404
    assert response.get_json() == {"message": "Task not found"}


def test_update_task_returns_200_when_field_changes(client, auth):
    headers = auth()
    task = _create_task(client, headers)
    response = client.put(
        f"/api/tasks/{task['taskId']}", headers=headers, json={"isCompleted": True}
    )
    assert response.status_code == 200
    assert response.get_json() == {"message": "Task updated"}


def test_update_task_returns_404_when_task_missing(client, auth):
    headers = auth()
    response = client.put(
        "/api/tasks/689ffffffffffffffffffff", headers=headers, json={"title": "x"}
    )
    assert response.status_code == 404
    assert response.get_json() == {"message": "Task not found"}


def test_delete_task_returns_200_and_task_disappears(client, auth):
    headers = auth()
    task = _create_task(client, headers)
    response = client.delete(f"/api/tasks/{task['taskId']}", headers=headers)
    assert response.status_code == 200
    assert response.get_json() == {"message": "Task deleted"}
    assert (
        client.get(f"/api/tasks/{task['taskId']}", headers=headers).status_code == 404
    )


def test_create_nlp_task_returns_400_when_prompt_missing(client, auth):
    headers = auth()
    response = client.post(
        "/api/tasks/create/natural-language", headers=headers, json={}
    )
    assert response.status_code == 400
    assert response.get_json() == {"message": "prompt is required in JSON body"}


def test_create_nlp_task_returns_415_when_body_is_not_json(client, auth):
    headers = auth()
    response = client.post(
        "/api/tasks/create/natural-language",
        headers=headers,
        data="plain text",
        content_type="text/plain",
    )
    assert response.status_code == 415
    assert response.get_json() == {"message": "Request must be JSON"}


def test_create_voice_task_returns_400_when_file_missing(client, auth):
    headers = auth()
    response = client.post("/api/tasks/create/voice", headers=headers)
    assert response.status_code == 400
    assert response.get_json() == {"message": "Audio file is required."}


def test_unmatched_url_still_returns_404(client):
    # Unknown routes keep Flask's default behaviour after the error-handler pass.
    assert client.get("/api/definitely-not-a-route").status_code == 404
