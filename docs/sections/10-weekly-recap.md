# 10 — Weekly Recap

**Blueprint:** `weekly_recap_bp` · **Prefix:** `/api/weekly-recap` · **File:** `app/api/weekly_recap.py`
**Auth:** 🔒 JWT

Rolling **7-day** window ending on a chosen date (UTC). Each day entry uses the
exact shape of the daily recap (§08), so clients can render both uniformly.

---

## GET `/api/weekly-recap/`

**Query parameters**

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `end` | `YYYY-MM-DD` | ❌ | last day of the window; defaults to **today (UTC)** |

`startDate` is `end - 6 days` (inclusive window).

**Responses**

| Code | Body |
|------|------|
| `200` | recap payload (below) |
| `400` | `{ "message": "end must be a YYYY-MM-DD date" }` |
| `401` | missing/invalid JWT |

```json
{
  "startDate": "2026-09-29",
  "endDate": "2026-10-05",
  "days": [
    {
      "date": "2026-09-29",
      "completedTasks": ["Ship the refactor"],
      "pendingTasks": ["Write docs"],
      "mood": "Solid start"
    }
  ],
  "totals": { "completedTasks": 12, "pendingTasks": 5 }
}
```

- Tasks are matched by `dueDate` prefix per day (same rule as the daily recap).
- `mood` comes from that day's planner `reflection` (`"Not recorded"` when absent).
- `days` always has exactly 7 entries, oldest → newest.

```bash
curl "http://127.0.0.1:5000/api/weekly-recap/?end=2026-10-05" \
  -H "Authorization: Bearer <access_token>"
```
