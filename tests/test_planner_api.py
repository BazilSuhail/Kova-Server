"""Planner endpoints: creation validation, task detail enrichment, focus swaps."""
from __future__ import annotations


def test_create_planner_returns_201_when_date_present(client, auth):
    headers = auth()
    response = client.post(
        "/api/planner/", headers=headers, json={"date": "2026-10-05"}
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["plannerId"]
    assert body["focusTasks"] == []
    assert body["tasks"] == []


def test_create_planner_returns_400_when_date_missing(client, auth):
    headers = auth()
    response = client.post("/api/planner/", headers=headers, json={})
    assert response.status_code == 400
    assert response.get_json() == {"message": "Date required"}


def test_list_planners_resolves_linked_task_details(client, auth):
    headers = auth()
    task = client.post(
        "/api/tasks/", headers=headers, json={"title": "Linked task"}
    ).get_json()
    client.post(
        "/api/planner/",
        headers=headers,
        json={"date": "2026-10-05", "tasks": [task["taskId"]]},
    )

    listing = client.get("/api/planner/", headers=headers)
    assert listing.status_code == 200
    planners = listing.get_json()
    assert len(planners) == 1
    details = planners[0]["tasksDetails"]
    assert [detail["taskId"] for detail in details] == [task["taskId"]]


def test_update_focus_returns_400_when_focus_tasks_missing(client, auth):
    headers = auth()
    response = client.put(
        "/api/planner/689ffffffffffffffffffff/focus", headers=headers, json={}
    )
    assert response.status_code == 400
    assert response.get_json() == {"message": "focusTasks required"}


def test_update_focus_returns_200_when_planner_exists(client, auth):
    headers = auth()
    planner = client.post(
        "/api/planner/", headers=headers, json={"date": "2026-10-05"}
    ).get_json()
    response = client.put(
        f"/api/planner/{planner['plannerId']}/focus",
        headers=headers,
        json={"focusTasks": ["Ship the refactor"]},
    )
    assert response.status_code == 200
    assert response.get_json() == {"message": "Focus tasks updated"}


def test_update_focus_returns_404_when_planner_missing(client, auth):
    headers = auth()
    response = client.put(
        "/api/planner/689ffffffffffffffffffff/focus",
        headers=headers,
        json={"focusTasks": ["x"]},
    )
    assert response.status_code == 404
    assert response.get_json() == {"message": "Planner not found"}


def test_delete_planner_returns_200_then_list_is_empty(client, auth):
    headers = auth()
    planner = client.post(
        "/api/planner/", headers=headers, json={"date": "2026-10-05"}
    ).get_json()
    response = client.delete(f"/api/planner/{planner['plannerId']}", headers=headers)
    assert response.status_code == 200
    assert response.get_json() == {"message": "Planner deleted"}
    assert client.get("/api/planner/", headers=headers).get_json() == []


def test_full_update_applies_whitelisted_fields(client, auth):
    headers = auth()
    planner = client.post(
        "/api/planner/", headers=headers, json={"date": "2026-10-05"}
    ).get_json()

    response = client.put(
        f"/api/planner/{planner['plannerId']}",
        headers=headers,
        json={"reflection": "Great focus day", "focusTasks": ["Write docs"]},
    )
    assert response.status_code == 200
    assert response.get_json() == {"message": "Planner updated"}

    listing = client.get("/api/planner/", headers=headers).get_json()
    assert listing[0]["reflection"] == "Great focus day"
    assert listing[0]["focusTasks"] == ["Write docs"]
    assert listing[0]["date"] == "2026-10-05"


def test_full_update_returns_404_when_planner_missing(client, auth):
    headers = auth()
    response = client.put(
        "/api/planner/689ffffffffffffffffffff",
        headers=headers,
        json={"reflection": "x"},
    )
    assert response.status_code == 404
    assert response.get_json() == {"message": "Planner not found"}


def test_full_update_rejects_body_without_updatable_fields(client, auth):
    headers = auth()
    planner = client.post(
        "/api/planner/", headers=headers, json={"date": "2026-10-05"}
    ).get_json()

    missing_body = client.put(f"/api/planner/{planner['plannerId']}", headers=headers)
    assert missing_body.status_code == 400

    unknown_only = client.put(
        f"/api/planner/{planner['plannerId']}", headers=headers, json={"mood": "x"}
    )
    assert unknown_only.status_code == 400
    assert unknown_only.get_json()["message"].startswith("No updatable fields")
