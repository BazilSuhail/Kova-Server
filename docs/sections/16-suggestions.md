# 16. Suggestions API — `/api/suggestions`

> File: `app/api/suggestions.py` → `app/services/suggestion_service.py` · Blueprint: `suggestions_bp` · **1 endpoint** · **JWT-protected**

Adaptive, habit-aware suggestions derived on read from tasks, mood logs, reflections, and
reminders. Rules are transparent and deterministic (nothing is persisted/learned yet).

---

## 16.1 `GET /api/suggestions/` — Adaptive suggestions

- **Auth:** 🔒 JWT

```json
{
  "generatedAt": "2026-10-17T09:15:00+00:00",
  "suggestions": [
    {
      "id": "reschedule_overdue",
      "type": "reschedule",
      "priority": "high",
      "title": "Reschedule what slipped",
      "message": "2 task(s) are past due — move them to a realistic day so the list stays trustworthy."
    }
  ]
}
```

**Rules emitted** (each independently, in this order)

| `id` | Emitted when | `priority` |
|------|--------------|:----------:|
| `reschedule_overdue` | pending tasks past their `dueDate` | high |
| `log_mood` | no mood logged today | low |
| `reduce_load` | avg of last 3 moods ≤ 2 **and** > 5 pending tasks | medium |
| `habit_block` | tasks exist (busiest creation weekday detected) | low |
| `set_reminder` | tasks due today **and** no pending reminders | medium |
| `momentum` | overall completion rate ≥ 70% | low |
| `reflect_today` | work due today **and** no reflection written today | low |

`type` is a coarse category (`reschedule`, `wellbeing`, `load`, `habit`, `reminder`,
`encouragement`, `reflection`) for client-side icon/colour mapping.

```bash
curl http://127.0.0.1:5000/api/suggestions/ \
  -H "Authorization: Bearer <access_token>"
```
