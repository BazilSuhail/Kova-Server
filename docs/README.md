# ZenFlow Server — API Documentation

Flask REST API for ZenFlow (task management, planner, summaries, notifications).
Stack: **Flask + Flask-JWT-Extended + MongoDB (PyMongo) + Waitress**, served via `run.py`.

- **Base URL (local):** `http://127.0.0.1:5000`
- **All routes prefixed with:** `/api`
- **Auth:** JWT Bearer token (`Authorization: Bearer <access_token>`), token expires in **1 hour (3600s)**
- **Content type:** `application/json` (except voice/PDF uploads → `multipart/form-data`)
- **Response envelope:** every endpoint returns raw JSON via `api_response(data, status_code)`
  (`ObjectId` → `str`, `datetime` → ISO 8601)

---

## 📊 API Count

| # | Section | Blueprint | Prefix | Endpoints | File |
|---|---------|-----------|--------|-----------|------|
| 1 | [Auth](sections/01-auth.md) | `auth_bp` | `/api/auth` | 6 | `app/api/auth.py` |
| 2 | [Users](sections/02-users.md) | `users_bp` | `/api/users` | 3 | `app/api/users.py` |
| 3 | [Tasks](sections/03-tasks.md) | `tasks_bp` | `/api/tasks` | 7 | `app/api/tasks.py` |
| 4 | [Subtasks](sections/04-subtasks.md) | `subtasks_bp` | `/api/subtasks` | 5 | `app/api/subtasks.py` |
| 5 | [Notifications](sections/05-notifications.md) | `notifications_bp` | `/api/notifications` | 5 | `app/api/notifications.py` |
| 6 | [Planner](sections/06-planner.md) | `planner_bp` | `/api/planner` | 6 | `app/api/planner.py` |
| 7 | [Summaries](sections/07-summaries.md) | `summaries_bp` | `/api/summaries` | 5 | `app/api/summaries.py` |
| 8 | [Daily Recap](sections/08-daily-recap.md) | `daily_recap_bp` | `/api/daily-recap` | 1 | `app/api/daily_recap.py` |
| 9 | [Health](sections/09-health.md) | `health_bp` | `/api` | 2 | `app/api/health.py` |
| 10 | [Weekly Recap](sections/10-weekly-recap.md) | `weekly_recap_bp` | `/api/weekly-recap` | 1 | `app/api/weekly_recap.py` |
| | **TOTAL** | | | **41** | |

**By method:** POST 12 · GET 13 · PUT 10 · DELETE 6 → **41 active endpoints**
(commented-out legacy routes in `planner.py` are not counted)

**By auth:** 5 public (signup/login/refresh/health/health-ready) · 36 require JWT

**Pagination:** `GET /api/tasks/`, `GET /api/notifications/`, `GET /api/summaries/`
accept optional `page`/`limit` (max 100) — bare array without them, paged
`{items, pagination}` envelope with them.

---

## 🗂️ Sections

| Section | File | Endpoints |
|---------|------|-----------|
| Auth | [sections/01-auth.md](sections/01-auth.md) | 6 |
| Users | [sections/02-users.md](sections/02-users.md) | 3 |
| Tasks | [sections/03-tasks.md](sections/03-tasks.md) | 7 |
| Subtasks | [sections/04-subtasks.md](sections/04-subtasks.md) | 5 |
| Notifications | [sections/05-notifications.md](sections/05-notifications.md) | 5 |
| Planner | [sections/06-planner.md](sections/06-planner.md) | 6 |
| Summaries | [sections/07-summaries.md](sections/07-summaries.md) | 5 |
| Daily Recap | [sections/08-daily-recap.md](sections/08-daily-recap.md) | 1 |
| Health | [sections/09-health.md](sections/09-health.md) | 2 |
| Weekly Recap | [sections/10-weekly-recap.md](sections/10-weekly-recap.md) | 1 |

➡️ Open work items: **[TODO.md](TODO.md)**

---

## 🔑 Quick Start

```bash
# 1. Get a token
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"secret"}'
# → { "access_token": "...", "userId": "..." }

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
| `401` | Bad credentials or missing/invalid JWT | `{"message": "..."}` |
| `404` | Not found | `{"message": "..."}` |
| `413` | Upload over `ZENFLOW_MAX_UPLOAD_MB` | `{"message": "Request payload too large"}` |
| `415` | Wrong content type (NLP task) | `{"message": "..."}` |
| `500` | Server error | `{"message": "Internal server error"}` (details only in server logs) |
| `503` | DB unreachable (readiness probe) | `{"status": "unavailable"}` |

**Database collections:** `users`, `tasks`, `subtasks`, `notifications`, `planner`, `summaries`
(all with unique indexes on their `*Id` field — see `app/__init__.py`)
