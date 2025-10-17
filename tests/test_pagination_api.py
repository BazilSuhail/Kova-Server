"""Opt-in pagination and filters for tasks/notifications (legacy shape intact)."""
from __future__ import annotations


def _create_task(client, headers, title: str, **overrides):
    payload = {"title": title, **overrides}
    response = client.post("/api/tasks/", headers=headers, json=payload)
    assert response.status_code == 201
    return response.get_json()


def test_task_list_without_page_keeps_legacy_bare_array(client, auth):
    headers = auth()
    _create_task(client, headers, "One")
    _create_task(client, headers, "Two")
    response = client.get("/api/tasks/", headers=headers)
    assert response.status_code == 200
    body = response.get_json()
    assert isinstance(body, list)
    assert len(body) == 2


def test_task_list_paging_returns_envelope(client, auth):
    headers = auth()
    for index in range(5):
        _create_task(client, headers, f"Task {index}")

    response = client.get("/api/tasks/?page=2&limit=2", headers=headers)
    assert response.status_code == 200
    body = response.get_json()
    assert len(body["items"]) == 2
    assert body["pagination"] == {
        "page": 2,
        "limit": 2,
        "total": 5,
        "totalPages": 3,
        "hasNext": True,
        "hasPrev": True,
    }


def test_task_list_rejects_invalid_page_params(client, auth):
    headers = auth()
    not_a_number = client.get("/api/tasks/?page=abc", headers=headers)
    assert not_a_number.status_code == 400
    assert not_a_number.get_json()["message"] == "page must be an integer"

    too_big = client.get("/api/tasks/?limit=1000", headers=headers)
    assert too_big.status_code == 400
    assert too_big.get_json()["message"] == "limit must be at most 100"

    zero = client.get("/api/tasks/?page=0", headers=headers)
    assert zero.status_code == 400


def test_task_completed_filter(client, auth):
    headers = auth()
    pending = _create_task(client, headers, "Pending task")
    done = _create_task(client, headers, "Finished task")
    client.put(
        f"/api/tasks/{done['taskId']}", headers=headers, json={"isCompleted": True}
    )

    completed = client.get("/api/tasks/?completed=true", headers=headers)
    assert completed.status_code == 200
    titles = [task["title"] for task in completed.get_json()]
    assert titles == ["Finished task"]

    open_tasks = client.get("/api/tasks/?completed=false", headers=headers)
    assert [task["taskId"] for task in open_tasks.get_json()] == [pending["taskId"]]

    invalid = client.get("/api/tasks/?completed=maybe", headers=headers)
    assert invalid.status_code == 400


def test_task_category_and_text_search_filters(client, auth):
    headers = auth()
    _create_task(client, headers, "Deep Work session", category="focus")
    _create_task(client, headers, "Buy groceries", category="home")

    by_category = client.get("/api/tasks/?category=focus", headers=headers)
    assert [t["title"] for t in by_category.get_json()] == ["Deep Work session"]

    # Case-insensitive title substring (the $regex/$options path).
    search = client.get("/api/tasks/?q=DEEP", headers=headers)
    assert [t["title"] for t in search.get_json()] == ["Deep Work session"]

    no_match = client.get("/api/tasks/?q=zzz-nothing", headers=headers)
    assert no_match.get_json() == []


def test_notification_unread_filter_and_paging(client, auth):
    headers = auth()
    for index in range(3):
        client.post(
            "/api/notifications/",
            headers=headers,
            json={"title": f"Notice {index}", "message": "Body"},
        )
    feed = client.get("/api/notifications/", headers=headers).get_json()
    first_id = feed[0]["notificationId"]
    client.put(
        f"/api/notifications/{first_id}", headers=headers, json={"read": True}
    )

    unread = client.get("/api/notifications/?unread=true", headers=headers)
    assert unread.status_code == 200
    assert len(unread.get_json()) == 2

    paged = client.get("/api/notifications/?page=1&limit=2", headers=headers)
    body = paged.get_json()
    assert len(body["items"]) == 2
    assert body["pagination"]["total"] == 3

    read_only = client.get("/api/notifications/?unread=false", headers=headers)
    assert [n["notificationId"] for n in read_only.get_json()] == [first_id]
