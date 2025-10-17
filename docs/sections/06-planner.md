# 6. Planner API — `/api/planner`

> File: `app/api/planner.py` · Blueprint: `planner_bp` · **5 endpoints** · **All JWT-protected**

A planner is a **per-day plan**: focus tasks, task list, and a reflection/mood.
Collection: `planner` (unique index on `plannerId`, indexed on `userId`, `date`).

---

## 6.1 `POST /api/planner/` — Create planner

- **Auth:** 🔒 JWT
- **Content-Type:** `application/json`

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `date` | string | ✅ | — |
| `focusTasks` | array | ❌ | `[]` |
| `tasks` | array (taskIds) | ❌ | `[]` |
| `reflection` | string | ❌ | `""` |

```json
{
  "date": "2026-10-05",
  "focusTasks": ["Finish report"],
  "tasks": ["6890abc..."],
  "reflection": "Productive morning"
}
```

**Responses:** `201` planner object · `400 { "message": "Date required" }` · `500`

---

## 6.2 `GET /api/planner/` — List planners (with task details)

- **Auth:** 🔒 JWT
- **Behavior:** each planner is enriched with `tasksDetails` — full task documents resolved
  from the `tasks` id array.

**Responses:** `200` array of planners (each incl. `tasksDetails`) · `500`

```json
[
  {
    "plannerId": "6890pln...",
    "userId": "68862e...",
    "date": "2026-10-05",
    "focusTasks": ["Finish report"],
    "tasks": ["6890abc..."],
    "reflection": "Productive morning",
    "tasksDetails": [ { "taskId": "6890abc...", "title": "Finish report", "...": "..." } ]
  }
]
```

```bash
curl http://127.0.0.1:5000/api/planner/ -H "Authorization: Bearer <access_token>"
```

---

## 6.3 `PUT /api/planner/<planner_id>/focus` — Replace focus tasks

- **Auth:** 🔒 JWT
- **Content-Type:** `application/json`

| Field | Type | Required |
|-------|------|----------|
| `focusTasks` | array | ✅ |

```json
{ "focusTasks": ["Finish report", "Gym"] }
```

**Responses:** `200 { "message": "Focus tasks updated" }` · `404 Planner not found` · `400 focusTasks required` · `500`

---

## 6.4 `PUT /api/planner/<planner_id>/tasks` — Replace task id list

- **Auth:** 🔒 JWT
- **Content-Type:** `application/json`

| Field | Type | Required |
|-------|------|----------|
| `tasks` | array (taskIds) | ✅ |

```json
{ "tasks": ["6890abc...", "6890def..."] }
```

**Responses:** `200 { "message": "Task IDs updated" }` · `404 Planner not found` · `400 tasks required` · `500`

---

## 6.5 `DELETE /api/planner/<planner_id>` — Delete planner

- **Auth:** 🔒 JWT

**Responses:** `200 { "message": "Planner deleted" }` · `404 { "message": "Planner not found" }` · `500`

**⚠️ Note:** a full `PUT /api/planner/<planner_id>` update exists only as commented-out code.
