# 15. Progress API — `/api/progress`

> File: `app/api/progress.py` → `app/services/progress_service.py` · Blueprint: `progress_bp` · **1 endpoint** · **JWT-protected**

Personal progress tracker. Everything is **derived on read** from tasks, mood logs, and
reflections — no stored aggregates, so it can never drift.

---

## 15.1 `GET /api/progress/` — Progress summary

- **Auth:** 🔒 JWT

```json
{
  "totals": {
    "tasks": 24, "completedTasks": 15, "pendingTasks": 9,
    "completionRate": 0.63, "moodEntries": 11, "reflections": 4
  },
  "streak": { "current": 3, "longest": 6 },
  "loadBalance": [
    { "day": "Mon", "completed": 3, "pending": 1 },
    { "day": "Tue", "completed": 0, "pending": 2 }
  ],
  "achievements": [
    { "id": "first_task", "label": "Created your first task", "earned": true, "progress": 24, "target": 1 },
    { "id": "ten_done", "label": "Completed 10 tasks", "earned": true, "progress": 10, "target": 10 },
    { "id": "streak_7", "label": "7-day streak", "earned": false, "progress": 3, "target": 7 }
  ],
  "activeDays": 8
}
```

**Notes**
- `completionRate` = completed / total (0.0 when there are no tasks).
- An **active day** has at least one of: a completed task (by `dueDate`, else `createdAt`),
  a mood entry, or a reflection.
- `streak.current` counts consecutive active days ending **today**; `longest` is the best run ever.
- `loadBalance` covers the **last 7 days**, based on task `dueDate`.
- Achievement ids: `first_task`, `ten_tasks`, `fifty_tasks`, `ten_done`, `streak_3`, `streak_7`,
  `mood_7`, `reflections_5`.

```bash
curl http://127.0.0.1:5000/api/progress/ \
  -H "Authorization: Bearer <access_token>"
```
