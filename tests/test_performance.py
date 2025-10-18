"""Sprint E: query batching, response compression, and timing observability."""
from __future__ import annotations

import dataclasses
import gzip
import json

from app import create_app
from app.config import Settings
from app.repositories.planner_repository import PlannerRepository
from app.repositories.task_repository import TaskRepository

from tests.support.fake_mongo import FakeMongoClient


def test_planner_list_batches_task_lookups_into_one_query(client, auth, monkeypatch):
    headers = auth()
    task_ids = [
        client.post(
            "/api/tasks/", headers=headers, json={"title": f"Task {i}"}
        ).get_json()["taskId"]
        for i in range(2)
    ]
    for index, task_id in enumerate(task_ids, start=1):
        client.post(
            "/api/planner/",
            headers=headers,
            json={"date": f"2026-10-0{index}", "tasks": [task_id]},
        )

    calls = 0
    original = TaskRepository.find_many_by_ids

    def _counting(self, ids):
        nonlocal calls
        calls += 1
        return original(self, ids)

    monkeypatch.setattr(TaskRepository, "find_many_by_ids", _counting)

    listing = client.get("/api/planner/", headers=headers)
    assert listing.status_code == 200
    planners = listing.get_json()
    assert len(planners) == 2
    assert calls == 1  # was: one query per planner (N+1)

    details_by_date = {
        planner["date"]: [d["taskId"] for d in planner["tasksDetails"]]
        for planner in planners
    }
    assert details_by_date["2026-10-01"] == [task_ids[0]]
    assert details_by_date["2026-10-02"] == [task_ids[1]]


def test_weekly_recap_uses_range_queries_instead_of_per_day_lookups(
    client, auth, monkeypatch
):
    headers = auth()
    client.post(
        "/api/tasks/",
        headers=headers,
        json={"title": "Weekly deliverable", "dueDate": "2026-10-05"},
    )
    client.post(
        "/api/planner/", headers=headers, json={"date": "2026-10-05"}
    )

    counts = {"due_on": 0, "by_date": 0}
    original_due = TaskRepository.find_due_on
    original_by_date = PlannerRepository.find_by_date

    def _count_due(self, *args, **kwargs):
        counts["due_on"] += 1
        return original_due(self, *args, **kwargs)

    def _count_by_date(self, *args, **kwargs):
        counts["by_date"] += 1
        return original_by_date(self, *args, **kwargs)

    monkeypatch.setattr(TaskRepository, "find_due_on", _count_due)
    monkeypatch.setattr(PlannerRepository, "find_by_date", _count_by_date)

    response = client.get("/api/weekly-recap/?end=2026-10-05", headers=headers)
    assert response.status_code == 200
    # 7 days × 2 per-day lookups → both helpers must now be bypassed entirely.
    assert counts == {"due_on": 0, "by_date": 0}

    body = response.get_json()
    assert body["startDate"] == "2026-09-29"
    assert body["endDate"] == "2026-10-05"
    assert len(body["days"]) == 7
    day = next(d for d in body["days"] if d["date"] == "2026-10-05")
    assert day["pendingTasks"] == ["Weekly deliverable"]
    assert body["totals"] == {"completedTasks": 0, "pendingTasks": 1}


def _seed_big_task(client, headers) -> None:
    client.post(
        "/api/tasks/",
        headers=headers,
        json={"title": "Compress me", "description": "x" * 1500},
    )


def test_json_is_gzip_compressed_when_client_accepts_it(client, auth):
    headers = dict(auth())
    _seed_big_task(client, headers)

    response = client.get(
        "/api/tasks/", headers={**headers, "Accept-Encoding": "gzip"}
    )
    assert response.status_code == 200
    assert response.headers.get("Content-Encoding") == "gzip"
    assert response.headers.get("Vary", "").lower().find("accept-encoding") >= 0

    payload = json.loads(gzip.decompress(response.data))
    assert payload[0]["title"] == "Compress me"


def test_json_stays_plain_without_gzip_acceptance(client, auth):
    headers = dict(auth())
    _seed_big_task(client, headers)

    response = client.get(
        "/api/tasks/", headers={**headers, "Accept-Encoding": "identity"}
    )
    assert response.status_code == 200
    assert response.headers.get("Content-Encoding") is None
    assert response.get_json()[0]["title"] == "Compress me"


def test_compression_can_be_disabled_via_settings():
    settings = dataclasses.replace(Settings.for_testing(), compress_enabled=False)
    application = create_app(settings=settings, mongo_client=FakeMongoClient())
    application.config["TESTING"] = True
    application.config["PROPAGATE_EXCEPTIONS"] = False
    client = application.test_client()
    token = client.post(
        "/api/auth/signup",
        json={"name": "Ada", "email": "ada@example.com", "password": "pw123456"},
    ).get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    _seed_big_task(client, headers)

    response = client.get(
        "/api/tasks/", headers={**headers, "Accept-Encoding": "gzip"}
    )
    assert response.status_code == 200
    assert response.headers.get("Content-Encoding") is None
    assert response.get_json()[0]["title"] == "Compress me"


def test_every_response_carries_server_timing(client, auth):
    response = client.get("/api/health", headers=auth())
    timing = response.headers.get("Server-Timing", "")
    assert timing.startswith("app;dur=")
    assert float(timing.removeprefix("app;dur=")) >= 0
