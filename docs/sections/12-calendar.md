# 12. Calendar API — `/api/calendar`

> File: `app/api/calendar.py` → `app/services/calendar_service.py` · Blueprint: `calendar_bp` · **1 endpoint** · **JWT-protected**

Read-only day / week / month views over tasks + planner. No new storage — it aggregates
existing collections so the client can render any view in one request.

---

## 12.1 `GET /api/calendar/` — Calendar view

- **Auth:** 🔒 JWT
- **Query params**

| Param | Type | Default | Notes |
|-------|------|---------|-------|
| `view` | string | `week` | `day` \| `week` \| `month` |
| `date` | string | today (UTC) | `YYYY-MM-DD` anchor date |

**Responses**

| Code | Body |
|------|------|
| `200` | `{ view, start, end, days: [...] }` |
| `400` | `{ "message": "view must be one of: day, week, month" }` \| `{ "message": "date must be a YYYY-MM-DD date" }` |
| `401` | missing/invalid/revoked token |

```json
{
  "view": "week",
  "start": "2026-10-05",
  "end": "2026-10-11",
  "days": [
    {
      "date": "2026-10-05",
      "tasks": [ { "taskId": "…", "title": "Physics revision", "dueDate": "2026-10-05" } ],
      "planner": { "plannerId": "…", "date": "2026-10-05", "focusTasks": [], "tasks": [] }
    }
  ]
}
```

**Notes**
- **`day`** → single day. **`week`** → ISO week starting **Monday**. **`month`** → first to last day of the anchor's month.
- Each day buckets tasks by `dueDate` and attaches that day's planner document (`null` if none).
- Range is inclusive of `start`, exclusive of the day after `end`.

```bash
curl "http://127.0.0.1:5000/api/calendar/?view=month&date=2026-10-05" \
  -H "Authorization: Bearer <access_token>"
```
