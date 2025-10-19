# ZenFlow Server — API Documentation

Flask REST API for **ZenFlow** (tasks, planner, summaries, notifications, mood, reminders,
progress, and offline sync).
Stack: **Flask + Flask-JWT-Extended + MongoDB (PyMongo) + Waitress**, served via `run.py`.

> [!IMPORTANT]
> 📱 **Client app:** [BazilSuhail/Zenflow-App](https://github.com/BazilSuhail/Zenflow-App) — **React Native + Expo**.
> This repo is the server only. Point the app's base URL at this API.

- **Base URL (local):** `http://127.0.0.1:5000`
- **All routes prefixed with:** `/api`
- **Auth:** JWT Bearer token (`Authorization: Bearer <access_token>`), access token expires in **1 hour (3600s)**
- **Content type:** `application/json` (except voice / image / PDF uploads → `multipart/form-data`)
- **Response envelope:** every endpoint returns raw JSON via `api_response(data, status_code)`
  (`ObjectId` → `str`, `datetime` → ISO 8601)

---

## 📊 API Count

| # | Section | Blueprint | Prefix | Endpoints | File |
|---|---------|-----------|--------|:---------:|------|
| 1 | [Auth](sections/01-auth.md) | `auth_bp` | `/api/auth` | 6 | `app/api/auth.py` |
| 2 | [Users](sections/02-users.md) | `users_bp` | `/api/users` | 7 | `app/api/users.py` |
| 3 | [Tasks](sections/03-tasks.md) | `tasks_bp` | `/api/tasks` | 11 | `app/api/tasks.py` |
| 4 | [Subtasks](sections/04-subtasks.md) | `subtasks_bp` | `/api/subtasks` | 5 | `app/api/subtasks.py` |
| 5 | [Notifications](sections/05-notifications.md) | `notifications_bp` | `/api/notifications` | 5 | `app/api/notifications.py` |
| 6 | [Planner](sections/06-planner.md) | `planner_bp` | `/api/planner` | 6 | `app/api/planner.py` |
| 7 | [Summaries](sections/07-summaries.md) | `summaries_bp` | `/api/summaries` | 6 | `app/api/summaries.py` |
| 8 | [Daily Recap](sections/08-daily-recap.md) | `daily_recap_bp` | `/api/daily-recap` | 1 | `app/api/daily_recap.py` |
| 9 | [Weekly Recap](sections/10-weekly-recap.md) | `weekly_recap_bp` | `/api/weekly-recap` | 1 | `app/api/weekly_recap.py` |
| 10 | [Health](sections/09-health.md) | `health_bp` | `/api` | 2 | `app/api/health.py` |
| 11 | [Dashboard](sections/11-dashboard.md) | `dashboard_bp` | `/api/dashboard` | 1 | `app/api/dashboard.py` |
| 12 | [Calendar](sections/12-calendar.md) | `calendar_bp` | `/api/calendar` | 1 | `app/api/calendar.py` |
| 13 | [Mood](sections/13-mood.md) | `mood_bp` | `/api/mood` | 6 | `app/api/mood.py` |
| 14 | [Reflections](sections/14-reflections.md) | `reflections_bp` | `/api/reflections` | 5 | `app/api/reflections.py` |
| 15 | [Progress](sections/15-progress.md) | `progress_bp` | `/api/progress` | 1 | `app/api/progress.py` |
| 16 | [Suggestions](sections/16-suggestions.md) | `suggestions_bp` | `/api/suggestions` | 1 | `app/api/suggestions.py` |
| 17 | [Devices](sections/17-devices.md) | `devices_bp` | `/api/devices` | 3 | `app/api/devices.py` |
| 18 | [Reminders](sections/18-reminders.md) | `reminders_bp` | `/api/reminders` | 5 | `app/api/reminders.py` |
| 19 | [Sync](sections/19-sync.md) | `sync_bp` | `/api/sync` | 2 | `app/api/sync.py` |
| | **TOTAL** | | | **75** | |

**By method:** POST 24 · GET 30 · PUT 10 · DELETE 11 → **75 active endpoints**
(Flask's auto-registered `/static/<path>` is not counted; commented-out legacy routes in
`planner.py` are not counted either)

**By auth:** 7 public (signup/login/refresh/health/health-ready/avatar catalogue/avatar images) ·
68 require JWT

**Pagination:** `GET /api/tasks/`, `GET /api/notifications/`, `GET /api/summaries/`,
`GET /api/mood/` accept optional `page`/`limit` (max 100) — bare array without them, paged
`{items, pagination}` envelope with them.

---

## 🗂️ Sections

| Section | File | Endpoints |
|---------|------|:---------:|
| Auth | [sections/01-auth.md](sections/01-auth.md) | 6 |
| Users | [sections/02-users.md](sections/02-users.md) | 7 |
| Tasks | [sections/03-tasks.md](sections/03-tasks.md) | 11 |
| Subtasks | [sections/04-subtasks.md](sections/04-subtasks.md) | 5 |
| Notifications | [sections/05-notifications.md](sections/05-notifications.md) | 5 |
| Planner | [sections/06-planner.md](sections/06-planner.md) | 6 |
| Summaries | [sections/07-summaries.md](sections/07-summaries.md) | 6 |
| Daily Recap | [sections/08-daily-recap.md](sections/08-daily-recap.md) | 1 |
| Health | [sections/09-health.md](sections/09-health.md) | 2 |
| Weekly Recap | [sections/10-weekly-recap.md](sections/10-weekly-recap.md) | 1 |
| Dashboard | [sections/11-dashboard.md](sections/11-dashboard.md) | 1 |
| Calendar | [sections/12-calendar.md](sections/12-calendar.md) | 1 |
| Mood | [sections/13-mood.md](sections/13-mood.md) | 6 |
| Reflections | [sections/14-reflections.md](sections/14-reflections.md) | 5 |
| Progress | [sections/15-progress.md](sections/15-progress.md) | 1 |
| Suggestions | [sections/16-suggestions.md](sections/16-suggestions.md) | 1 |
| Devices | [sections/17-devices.md](sections/17-devices.md) | 3 |
| Reminders | [sections/18-reminders.md](sections/18-reminders.md) | 5 |
| Sync | [sections/19-sync.md](sections/19-sync.md) | 2 |

**Cross-cutting:** [🤖 AI flows — voice, NLP, notes & summaries](ai-flows.md)
(pipelines, provider config, per-flow failure statuses)

**Client-facing:** [📱 Client guide — build the app](client.md)
(screens, every option → API, request/response examples)

➡️ Open work items: **[TODO.md](TODO.md)**

---

## 🔑 Quick Start

```bash
# 1. Get a token
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"secret"}'
# → { "access_token": "...", "refresh_token": "...", "userId": "..." }

# 2. Use it on protected routes
curl http://127.0.0.1:5000/api/tasks/ \
  -H "Authorization: Bearer <access_token>"
```

---

## ⚠️ Conventions & Error Shapes

| Status | Meaning | Body |
|--------|---------|------|
| `200` | OK / updated / deleted | resource or `{"message": "..."}` |
| `201` | Created | created resource |
| `400` | Validation / missing fields | `{"message": "..."}` |
| `401` | Bad credentials or missing/invalid/revoked JWT | `{"message": "..."}` |
| `404` | Not found (or not owned by the caller) | `{"message": "..."}` |
| `413` | Upload over `ZENFLOW_MAX_UPLOAD_MB` | `{"message": "Request payload too large"}` |
| `415` | Wrong content type (NLP task) | `{"message": "..."}` |
| `429` | Per-IP rate limit exceeded | `{"message": "Rate limit exceeded"}` + `X-RateLimit-*` / `Retry-After` headers |
| `500` | Server error | `{"message": "Internal server error"}` (details only in server logs) |
| `502` | Upstream provider failure (AI/OCR) | `{"message": "..."}` |
| `503` | DB unreachable, or AI/OCR provider not configured | `{"status": "unavailable"}` / `{"message": "AI provider is not configured"}` |

**Database collections:** `users`, `tasks`, `subtasks`, `notifications`, `planner`, `summaries`,
`mood_entries`, `reflections`, `push_devices`, `scheduled_reminders`, `tombstones`, `token_blocklist`
(all with unique indexes on their `*Id` field — see `app/db.py`).

**Timestamps & sync:** every synced document carries `updatedAt` (ISO 8601). Offline clients pull
deltas since their last cursor and receive deletions from the `tombstones` collection — see
[sections/19-sync.md](sections/19-sync.md).
