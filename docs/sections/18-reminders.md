# 18. Reminders API — `/api/reminders`

> File: `app/api/reminders.py` → `app/services/reminder_service.py` (+ `app/core/scheduler.py`) ·
> Blueprint: `reminders_bp` · **5 endpoints** · **JWT-protected**

Smart, gentle reminders. A background **APScheduler** job (`ZENFLOW_SCHEDULER_ENABLED`, default on)
polls due reminders and delivers them as an **in-app notification + Expo push**.

---

## 18.1 `POST /api/reminders/` — Schedule a reminder

- **Auth:** 🔒 JWT · **Content-Type:** `application/json`

| Field | Type | Required | Notes |
|-------|------|:--------:|-------|
| `title` | string | ✅ | notification title |
| `fireAt` | string | ✅ | `YYYY-MM-DD` (→ 09:00 UTC) or ISO datetime |
| `message` | string | ❌ | notification body |
| `relatedType` | string | ❌ | e.g. `task` |
| `relatedId` | string | ❌ | id of the related resource |

**Responses**

| Code | Body |
|------|------|
| `201` | reminder object (`status: "pending"`) |
| `400` | `{ "message": "title and fireAt are required" }` \| `{ "message": "fireAt must be an ISO date or datetime" }` |

```json
{ "reminderId": "…", "userId": "…", "title": "Stand up", "message": "Take a break",
  "fireAt": "2026-10-20T09:00:00+00:00", "relatedType": "", "relatedId": "",
  "status": "pending", "createdAt": "…", "updatedAt": "…" }
```

---

## 18.2 `GET /api/reminders/` — List reminders

- **Auth:** 🔒 JWT · Query: `status` (`pending` \| `sent`, optional) → array, soonest `fireAt` first.

## 18.3 `GET /api/reminders/upcoming` — Upcoming pending

- **Auth:** 🔒 JWT · Query: `hours` (default `48`) → pending reminders due within the window.

## 18.4 `GET /api/reminders/<reminder_id>`

- **Responses:** `200` · `404 { "message": "Reminder not found" }`

## 18.5 `DELETE /api/reminders/<reminder_id>`

- **Responses:** `200 { "message": "Reminder deleted" }` · `404`
- Recorded as a sync tombstone.

---

## ⏰ Delivery

On each scheduler tick, for every **pending** reminder whose `fireAt` has passed:

1. an in-app notification is created (`type: "reminder"`);
2. a push message is sent to every registered device of that user (via [devices](17-devices.md));
3. tokens Expo reports as dead are pruned;
4. the reminder is marked `status: "sent"` with a `sentAt` timestamp.

> Ticks are `max_instances=1`, `coalesce=True` and fully exception-guarded — a provider hiccup
> never kills the job. Provider calls fail soft (logged, not raised).

```bash
curl -X POST http://127.0.0.1:5000/api/reminders/ \
  -H "Authorization: Bearer <access_token>" -H "Content-Type: application/json" \
  -d '{"title":"Stand up","message":"Take a break","fireAt":"2026-10-20T09:00:00Z"}'
```
