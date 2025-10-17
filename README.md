# ZenFlow Server

A Flask REST API for task management (tasks, subtasks, planner, summaries, notifications) with MongoDB and JWT authentication.

- **API reference:** [`docs/README.md`](docs/README.md) — **41 endpoints** across 10 sections
- **Open work:** [`docs/TODO.md`](docs/TODO.md)

***

## 🚀 Setup Instructions

1. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate   # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt        # runtime
   pip install -r requirements-dev.txt    # runtime + tests
   ```

3. **Set up your environment:**
   ```bash
   copy .env.example .env
   ```
   Set at minimum `ZENFLOW_MONGO_URI` (or legacy `MONGO_URI`) and, in production,
   `ZENFLOW_JWT_SECRET`. All variables are listed in [`.env.example`](.env.example).

4. **Run the server:**
   ```bash
   python run.py                # development (Waitress, verbose logging)
   python run.py --production   # production (Waitress)
   python run.py --flask-debug  # Flask dev server (auto-reload)
   python run.py --help
   ```

***

## 🗂️ Project Structure

```
zenflow-server/
├── run.py                        # entrypoint: dev/prod/debug runners (Waitress)
├── pytest.ini                    # test discovery config
├── requirements.txt              # pinned runtime deps
├── requirements-dev.txt          # runtime + pytest, ruff, mypy, coverage
├── .env.example                  # every supported env var, documented
│
├── app/
│   ├── __init__.py               # create_app() — the single composition root
│   ├── config.py                 # Settings: typed, immutable, env-driven
│   ├── extensions.py             # JWT + CORS init
│   ├── db.py                     # Mongo connection + index bootstrap
│   │
│   ├── core/                     # cross-cutting primitives
│   │   ├── logging.py            # JSON logs + per-request correlation id
│   │   ├── exceptions.py         # AppError hierarchy (400/401/404/415)
│   │   └── responses.py          # api_response() — the one serializer
│   │
│   ├── api/                      # HTTP layer: validate → service → serialize
│   │   ├── __init__.py           # blueprint registration (URL prefixes live here)
│   │   ├── auth.py               # signup / login
│   │   ├── users.py              # profile CRUD
│   │   ├── tasks.py              # manual / NLP / voice creation + CRUD
│   │   ├── subtasks.py           # grouped subtask operations
│   │   ├── notifications.py      # notification feed
│   │   ├── planner.py            # daily planner
│   │   ├── summaries.py          # PDF summaries
│   │   └── daily_recap.py        # end-of-day recap
│   │
│   ├── services/                 # business rules (no Flask request objects)
│   │   ├── __init__.py           # Services container + get_services()
│   │   ├── auth_service.py       # user_service.py, task_service.py, ...
│   │   └── daily_recap_service.py
│   │
│   ├── repositories/             # data access (Mongo queries only)
│   │   ├── base.py               # shared insert/find/update/delete helpers
│   │   └── *_repository.py       # one per collection
│   │
│   ├── utils/                    # external integrations (Groq, AssemblyAI, PDF)
│
└── tests/
    ├── conftest.py               # app/client/auth fixtures (in-memory DB)
    ├── support/fake_mongo.py     # dependency-free PyMongo stand-in
    └── test_*.py                 # 99 endpoint/security tests
```

***

## 📚 API Endpoints

Base URL: `http://127.0.0.1:5000` · all routes under `/api` · JWT required except auth + health.
Full request/response schemas: **[`docs/README.md`](docs/README.md)**

| Section | Endpoints |
|---------|-----------|
| **Auth** (6) | `POST /api/auth/signup` · `POST /api/auth/login` · `POST /api/auth/refresh` · `POST /api/auth/logout` · `GET /api/auth/me` · `PUT /api/auth/password` |
| **Users** (3) | `GET/PUT/DELETE /api/users/profile` |
| **Tasks** (7) | `POST /api/tasks/` · `POST /api/tasks/create/natural-language` · `POST /api/tasks/create/voice` · `GET /api/tasks/` *(filters + paging)* · `GET/PUT/DELETE /api/tasks/<task_id>` |
| **Subtasks** (5) | `POST /api/subtasks/create` · `GET/DELETE /api/subtasks/task/<task_id>` · `PUT/DELETE /api/subtasks/<subtask_id>` |
| **Notifications** (5) | `POST/GET /api/notifications/` *(unread filter + paging)* · `GET/PUT/DELETE /api/notifications/<notification_id>` |
| **Planner** (6) | `POST/GET /api/planner/` · `PUT /api/planner/<planner_id>` · `PUT /api/planner/<planner_id>/focus` · `PUT /api/planner/<planner_id>/tasks` · `DELETE /api/planner/<planner_id>` |
| **Summaries** (5) | `POST /api/summaries/create` · `GET /api/summaries/` *(paging)* · `PUT/DELETE /api/summaries/<summary_id>` · `POST /api/summaries/<summary_id>/convert-to-tasks` |
| **Daily Recap** (1) | `GET /api/daily-recap/` |
| **Weekly Recap** (1) | `GET /api/weekly-recap/` |
| **Health** (2) | `GET /api/health` · `GET /api/health/ready` (public) |
| **Total** | **41** |

***

## 🧪 Testing & Quality Gates

```bash
pip install -r requirements-dev.txt
python -m pytest              # 99 tests + coverage gate (fails under 85%)
ruff check app tests run.py   # lint — must be clean
mypy                          # type check — must be clean
```

Tests run against an in-memory Mongo stand-in — no database or network needed.

***

## 📌 Notes

- MongoDB must be reachable at boot (5s fail-fast timeout); indexes are created automatically.
- Logs are structured JSON with `X-Request-ID` correlation ids (echoed in responses).
- Secrets come from the environment (`.env` locally) — see `.env.example`.
- **Production boot fails fast** if `ZENFLOW_JWT_SECRET` is unset (built-in secret);
  every response carries `X-Content-Type-Options`/`X-Frame-Options`/`Referrer-Policy`.
  CORS allowlist (`ZENFLOW_CORS_ORIGINS`, default `*`) and the 16 MB upload cap
  (`ZENFLOW_MAX_UPLOAD_MB`) are configurable.
- **Per-IP rate limiting** (default 600/min; auth routes 60/min — `ZENFLOW_RATELIMIT_*`)
  returns JSON `429`; health probes are exempt. Sentry reports 500s when
  `ZENFLOW_SENTRY_DSN` is set (disabled otherwise).
