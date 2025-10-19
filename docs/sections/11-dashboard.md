# 11. Dashboard API — `/api/dashboard`

> File: `app/api/dashboard.py` → `app/services/dashboard_service.py` · Blueprint: `dashboard_bp` · **1 endpoint** · **JWT-protected**

One call that powers the home screen, instead of four round-trips (tasks + recap +
notifications + summaries).

---

## 11.1 `GET /api/dashboard/` — Home summary

- **Auth:** 🔒 JWT

**Responses**

| Code | Body |
|------|------|
| `200` | see below |
| `401` | missing/invalid/revoked token |

```json
{
  "date": "2026-10-17T09:15:00+00:00",
  "tasks": { "total": 12, "completed": 5, "pending": 7, "dueToday": 3 },
  "todayTasks": [ { "taskId": "…", "title": "Finish report", "dueDate": "2026-10-17" } ],
  "unreadNotifications": 2,
  "nextReminders": [ { "reminderId": "…", "title": "Stand up", "fireAt": "2026-10-17T18:00:00+00:00" } ],
  "latestMood": { "moodId": "…", "mood": "good", "score": 4 } ,
  "latestSummary": { "summaryId": "…", "summaryBullets": ["…"] },
  "streak": 3,
  "suggestions": [ { "id": "log_mood", "type": "wellbeing", "priority": "low", "title": "How are you feeling?", "message": "…" } ]
}
```

**Notes**
- `todayTasks` = tasks whose `dueDate` starts with today's UTC date.
- `nextReminders` = up to 5 pending reminders due at/after now.
- `latestMood` / `latestSummary` are `null` when nothing exists yet.
- `streak` is the current active-day streak (same source as `GET /api/progress/`).
- `suggestions` is the full adaptive list (same as `GET /api/suggestions/`).

```bash
curl http://127.0.0.1:5000/api/dashboard/ \
  -H "Authorization: Bearer <access_token>"
```
