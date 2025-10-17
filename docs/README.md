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
| 1 | [Auth](sections/01-auth.md) | `auth_bp` | `/api/auth` | 2 | `app/api/auth.py` |
| 2 | [Users](sections/02-users.md) | `users_bp` | `/api/users` | 3 | `app/api/users.py` |
| 3 | [Tasks](sections/03-tasks.md) | `tasks_bp` | `/api/tasks` | 7 | `app/api/tasks.py` |
| 4 | [Subtasks](sections/04-subtasks.md) | `subtasks_bp` | `/api/subtasks` | 4 | `app/api/subtasks.py` |
| 5 | [Notifications](sections/05-notifications.md) | `notifications_bp` | `/api/notifications` | 3 | `app/api/notifications.py` |
| 6 | [Planner](sections/06-planner.md) | `planner_bp` | `/api/planner` | 5 | `app/api/planner.py` |
| 7 | [Summaries](sections/07-summaries.md) | `summaries_bp` | `/api/summaries` | 4 | `app/api/summaries.py` |
| 8 | [Daily Recap](sections/08-daily-recap.md) | `daily_recap_bp` | `/api/daily-recap` | 1 | `app/api/daily_recap.py` |
| 9 | [Health](sections/09-health.md) | `health_bp` | `/api` | 2 | `app/api/health.py` |
| | **TOTAL** | | | **31** | |

**By method:** POST 9 · GET 10 · PUT 8 · DELETE 4 → **31 active endpoints**
(commented-out legacy routes in `planner.py` are not counted)

**By auth:** 4 public (signup/login/health) · 27 require JWT

---

## 🗂️ Sections

| Section | File | Endpoints |
|---------|------|-----------|
| Auth | [sections/01-auth.md](sections/01-auth.md) | 2 |
| Users | [sections/02-users.md](sections/02-users.md) | 3 |
| Tasks | [sections/03-tasks.md](sections/03-tasks.md) | 7 |
| Subtasks | [sections/04-subtasks.md](sections/04-subtasks.md) | 4 |
| Notifications | [sections/05-notifications.md](sections/05-notifications.md) | 3 |
| Planner | [sections/06-planner.md](sections/06-planner.md) | 5 |
| Summaries | [sections/07-summaries.md](sections/07-summaries.md) | 4 |
| Daily Recap | [sections/08-daily-recap.md](sections/08-daily-recap.md) | 1 |
| Health | [sections/09-health.md](sections/09-health.md) | 2 |

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
| `415` | Wrong content type (NLP task) | `{"message": "..."}` |
| `500` | Server error | `{"message": "Internal server error"}` (details only in server logs) |

**Database collections:** `users`, `tasks`, `subtasks`, `notifications`, `planner`, `summaries`
(all with unique indexes on their `*Id` field — see `app/__init__.py`)
