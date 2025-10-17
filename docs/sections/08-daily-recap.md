# 8. Daily Recap API — `/api/daily-recap`

> File: `app/api/daily_recap.py` → `app/services/daily_recap_service.py` · Blueprint: `daily_recap_bp` · **1 endpoint** · **JWT-protected**

---

## 8.1 `GET /api/daily-recap/` — Today's recap

- **Auth:** 🔒 JWT
- **Intended behavior:** fetch today's tasks (UTC), split into completed/pending,
  and read today's planner mood → return a day summary.

**Responses (intended)**

| Code | Body |
|------|------|
| `200` | see below |
| `500` | `{ "message": "Internal server error" }` |

```json
{
  "date": "2026-10-05T00:00:00+00:00",
  "completedTasks": ["Buy groceries"],
  "pendingTasks": ["Finish report"],
  "mood": "Focused"
}
```

```bash
curl http://127.0.0.1:5000/api/daily-recap/ \
  -H "Authorization: Bearer <access_token>"
```

**Mood source:** `planner.mood` for today, else `"Not recorded"`.

---

## ✅ Fixed in the production refactor

- [x] **`/api/daily-recap/` now works** — logic moved to `app/services/daily_recap_service.py`;
      the local unregistered `tasks_bp` and the tuple-causing trailing comma are gone.
      The recap reports the planner's `reflection` (the `mood` field it used to read was
      removed from the schema in commit `4aa10cc`); an empty/missing reflection yields
      `"Not recorded"`.
- [x] Covered by `tests/test_daily_recap_api.py` (200 shape, planner mood, 401 without token).
