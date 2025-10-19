<div align="center">

# 🌿 ZenFlow Server

**The REST API powering ZenFlow — a Personal AI Life Assistant for students.**

Plan, prioritize, reflect, and grow: natural-language tasks, voice capture, mood-aware
suggestions, smart reminders, progress tracking, and offline sync.

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-PyMongo%204.18-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![JWT](https://img.shields.io/badge/Auth-JWT%20%2B%20bcrypt-c0392b)](#-authentication)
[![API](https://img.shields.io/badge/API-75%20endpoints-informational)](#-api-reference)
[![Tests](https://img.shields.io/badge/tests-186%20passing-success)](#-testing--quality-gates)
[![Coverage](https://img.shields.io/badge/coverage-89%25-success)](#-testing--quality-gates)
[![Ruff](https://img.shields.io/badge/lint-ruff-261230?logo=ruff&logoColor=white)](#-testing--quality-gates)
[![mypy](https://img.shields.io/badge/types-mypy-blue)](#-testing--quality-gates)

</div>

---

> [!IMPORTANT]
> 📱 **This is the server only.** The ZenFlow **mobile client** is built with **React Native + Expo**:
> **[github.com/BazilSuhail/Zenflow-App](https://github.com/BazilSuhail/Zenflow-App)**
> Clone both repos — run this API, point the app at `http://<your-lan-ip>:5000`, and you have the full product.

> [!TIP]
> New here? Jump straight to **[🚀 Quick Start](#-quick-start)** (≈2 minutes), then
> **[🔑 Authentication](#-authentication)** and the **[📚 API Reference](#-api-reference)**.

---

## 📖 Overview

ZenFlow Server is a production-minded **Flask + MongoDB** REST API that backs an AI life-assistant:
it turns messy input (typed sentences, voice notes, photos of notes) into structured tasks,
automatically categorises them, plans your day, watches your mood, nudges you at the right time,
and keeps everything working offline.

**Highlights**

- 🧠 **AI flows** — natural-language, voice (AssemblyAI), notes, and camera/OCR → structured tasks (Groq).
- 🎯 **Smart categorisation** — every task is labelled (academics, work, health, social, finance, errands, …).
- 📅 **Planner & calendar** — day / week / month views with drag-and-drop-friendly planner tasks.
- 💚 **Mood journal & trends** — log how you feel, see trends, get load-adjusted suggestions.
- ⏰ **Smart reminders & nudges** — scheduled in-app + Expo push delivery via a background scheduler.
- 📈 **Progress tracker** — streaks, completion stats, load balance, achievements.
- 🔌 **Offline-first sync** — delta pull/push with `updatedAt` cursors and deletion tombstones.
- 🧩 **Clean architecture** — routes → services → repositories, with a service container and no ORM.
- 🔒 **Hardened** — JWT rotation + instant revocation, rate limiting, security headers, structured JSON logs.
- ✅ **Well tested** — 186 tests against an in-memory Mongo, 89% coverage, ruff + mypy clean.

---

## 🚀 Quick Start

> [!NOTE]
> Requires **Python 3.13+** and a reachable **MongoDB** (local or Atlas). All commands are
> shown for Windows PowerShell; macOS/Linux equivalents are the same with `source .venv/bin/activate`.

### 1. Clone & create a virtual environment

```bash
git clone <this-repo-url> ZenFlow-Server
cd ZenFlow-Server
python -m venv .venv
.\.venv\Scripts\Activate          # Windows
# source .venv/bin/activate       # macOS / Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt        # runtime only
pip install -r requirements-dev.txt    # runtime + tests, ruff, mypy, coverage
```

> [!TIP]
> Prefer [`uv`](https://github.com/astral-sh/uv)? It's much faster:
> `uv venv` then `uv pip install -r requirements-dev.txt`.

### 3. Configure the environment

```bash
copy .env.example .env      # Windows
# cp .env.example .env      # macOS / Linux
```

At minimum set:

| Variable | Purpose |
|----------|---------|
| `ZENFLOW_MONGO_URI` | MongoDB connection string (default `mongodb://localhost:27017/zenflow`) |
| `ZENFLOW_JWT_SECRET` | **Required in production** — boot fails fast without it |
| `ZENFLOW_GROQ_API_KEY` | Enables NLP / voice / notes / OCR task generation |
| `ZENFLOW_ASSEMBLYAI_API_KEY` | Enables voice transcription |
| `ZENFLOW_OCR_API_KEY` | Enables camera/OCR quick-add |

Every supported variable is documented in [`.env.example`](.env.example).

### 4. Run it

```bash
python run.py                  # development (Waitress, verbose logging)
python run.py --production     # production (Waitress)
python run.py --flask-debug    # Flask dev server (auto-reload)
python run.py --help           # all options
```

The API is then live at **`http://127.0.0.1:5000`**, all routes under `/api`.

### 5. Smoke test

```bash
# health (public)
curl http://127.0.0.1:5000/api/health

# create a user → returns access + refresh tokens
curl -X POST http://127.0.0.1:5000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"Lorde","email":"you@example.com","password":"secret123"}'

# use the token
curl http://127.0.0.1:5000/api/tasks/ -H "Authorization: Bearer <access_token>"
```

---

## 🔑 Authentication

ZenFlow uses **stateless JWT** auth with **refresh-token rotation** and **instant revocation**.

| Concept | Detail |
|---------|--------|
| Header | `Authorization: Bearer <access_token>` |
| Access token | Valid **1 hour** (`ZENFLOW_JWT_EXPIRES_SECONDS=3600`) |
| Refresh token | Valid **7 days** (`ZENFLOW_JWT_REFRESH_EXPIRES_SECONDS=604800`), **rotated on every refresh** |
| Revocation | `POST /api/auth/logout` blocklists the token's `jti` (TTL collection) → next request fails immediately |
| Passwords | bcrypt, cost **12** |

**Flow**

```text
signup / login ──▶ { access_token, refresh_token, userId }
       │
       ├─ send access_token on every request
       │
       └─ on 401 ──▶ POST /api/auth/refresh (refresh_token) ──▶ new pair, old refresh token dies
```

> [!WARNING]
> Never commit `.env` or real secrets. Production **refuses to boot** with the built-in JWT
> secret unless `ZENFLOW_ALLOW_INSECURE_JWT=1` (development escape hatch only).

**Public endpoints:** `POST /api/auth/signup`, `POST /api/auth/login`, `POST /api/auth/refresh`,
`GET /api/health`, `GET /api/health/ready`, `GET /api/users/avatars`,
`GET /api/users/avatars/<file>`. **Everything else requires a JWT.**

---

## 📚 API Reference

**Base URL** `http://127.0.0.1:5000` · base path `/api` · JSON in/out (voice & PDF uploads are `multipart/form-data`).
Full per-endpoint schemas, bodies, and examples: **[`docs/README.md`](docs/README.md)**.

| # | Section | Prefix | Endpoints |
|---|---------|--------|:---------:|
| 1 | [Auth](docs/sections/01-auth.md) | `/api/auth` | 6 |
| 2 | [Users](docs/sections/02-users.md) | `/api/users` | 7 |
| 3 | [Tasks](docs/sections/03-tasks.md) | `/api/tasks` | 11 |
| 4 | [Subtasks](docs/sections/04-subtasks.md) | `/api/subtasks` | 5 |
| 5 | [Notifications](docs/sections/05-notifications.md) | `/api/notifications` | 5 |
| 6 | [Planner](docs/sections/06-planner.md) | `/api/planner` | 6 |
| 7 | [Summaries](docs/sections/07-summaries.md) | `/api/summaries` | 6 |
| 8 | [Daily Recap](docs/sections/08-daily-recap.md) | `/api/daily-recap` | 1 |
| 9 | [Weekly Recap](docs/sections/10-weekly-recap.md) | `/api/weekly-recap` | 1 |
| 10 | [Health](docs/sections/09-health.md) | `/api` | 2 |
| 11 | [Dashboard](docs/sections/11-dashboard.md) | `/api/dashboard` | 1 |
| 12 | [Calendar](docs/sections/12-calendar.md) | `/api/calendar` | 1 |
| 13 | [Mood](docs/sections/13-mood.md) | `/api/mood` | 6 |
| 14 | [Reflections](docs/sections/14-reflections.md) | `/api/reflections` | 5 |
| 15 | [Progress](docs/sections/15-progress.md) | `/api/progress` | 1 |
| 16 | [Suggestions](docs/sections/16-suggestions.md) | `/api/suggestions` | 1 |
| 17 | [Devices](docs/sections/17-devices.md) | `/api/devices` | 3 |
| 18 | [Reminders](docs/sections/18-reminders.md) | `/api/reminders` | 5 |
| 19 | [Sync](docs/sections/19-sync.md) | `/api/sync` | 2 |
| | **TOTAL** | | **75** |

**By method:** POST 24 · GET 30 · PUT 10 · DELETE 11 · **Public 7 / JWT 68**
**Pagination:** `page`/`limit` (max 100) on `GET /api/tasks/`, `/api/notifications/`, `/api/summaries/`, `/api/mood/` —
a bare array without them, a `{items, pagination}` envelope with them.

### Feature → endpoint map

| Product feature | Endpoint(s) |
|-----------------|-------------|
| Register / login | `/api/auth/*` |
| Home dashboard | `GET /api/dashboard/` |
| Task from natural language | `POST /api/tasks/create/natural-language` |
| Task from voice | `POST /api/tasks/create/voice` |
| Task from camera / scan (OCR) | `POST /api/tasks/create/image` |
| Smart categorisation | auto on create + `POST /api/tasks/<id>/categorize` |
| Smart title generator | `POST /api/tasks/suggest-title`, `POST /api/tasks/<id>/rewrite-title` |
| Goals → checklist | `POST /api/subtasks/create` |
| Notes summariser (3–5 bullets) | `POST /api/summaries/create-from-text` |
| Planner & calendar | `/api/planner/*`, `GET /api/calendar/` |
| Mood journal & trends | `/api/mood/*`, `GET /api/mood/trends` |
| Mood-based load suggestion | `POST /api/mood/suggestions` |
| Progress tracker | `GET /api/progress/` |
| Adaptive suggestions | `GET /api/suggestions/` |
| Reminders & push | `/api/reminders/*`, `/api/devices/*` |
| Offline sync | `POST /api/sync/pull`, `POST /api/sync/push` |
| Notification centre | `/api/notifications/*` |
| Daily / weekly recap | `GET /api/daily-recap/`, `GET /api/weekly-recap/` |
| Affirmation / reflection | `GET /api/reflections/today`, `POST /api/reflections/` |
| Customisation | `GET/PUT /api/users/profile/settings` |
| Avatar picker | `GET /api/users/avatars`, `GET /api/users/avatars/<file>` |
| Delete account (cascade) | `DELETE /api/users/profile` — removes all owned data |

---

## 🏗️ Architecture

```text
        ┌──────────────────────────────┐
        │  React Native (Expo) client  │   BazilSuhail/Zenflow-App
        └───────────────┬──────────────┘
                        │ HTTPS / JSON (JWT Bearer)
        ┌───────────────▼──────────────┐
        │            Flask app          │
        │  api/  ──▶  services/  ──▶  repositories/
        │  (validate)   (rules)        (Mongo queries)
        └───────┬───────────────┬───────┘
                │               │
        ┌───────▼──────┐  ┌─────▼─────────────────────────────┐
        │   MongoDB    │  │ External providers (all optional) │
        │ collections  │  │ Groq · AssemblyAI · OCR.space ·   │
        │ + indexes    │  │ Expo Push                          │
        └──────────────┘  └───────────────────────────────────┘
                ▲
        APScheduler ── fires due reminders ──▶ in-app + push
```

**Request lifecycle**

```text
HTTP ──▶ api/<blueprint>.py   validate + auth (JWT)
      ──▶ services/<name>.py   business rules (no Flask request objects)
      ──▶ repositories/*.py    Mongo reads/writes (via BaseRepository)
      ──▶ core/responses.py    api_response() serialises (ObjectId→str, datetime→ISO)
```

Routes fetch services from a container (`get_services()`) — no globals, no monkey-patching.

### Feature modules added

| Area | Routes | Service | Repository / util |
|------|--------|---------|-------------------|
| Dashboard | `api/dashboard.py` | `dashboard_service.py` | — |
| Calendar | `api/calendar.py` | `calendar_service.py` | planner + task repos |
| Mood | `api/mood.py` | `mood_service.py` | `mood_repository.py` |
| Reflections | `api/reflections.py` | `reflection_service.py` | `reflection_repository.py`, `utils/affirmations.py` |
| Progress | `api/progress.py` | `progress_service.py` | derived |
| Suggestions | `api/suggestions.py` | `suggestion_service.py` | derived |
| Devices | `api/devices.py` | `device_service.py` | `device_repository.py`, `utils/push_client.py` |
| Reminders | `api/reminders.py` | `reminder_service.py`, `core/scheduler.py` | `reminder_repository.py` |
| Sync | `api/sync.py` | `sync_service.py` | `tombstone_repository.py` |
| Titles / OCR / categorise | `api/tasks.py` | `task_service.py` | `utils/title_utils.py`, `utils/ocr_utils.py`, `utils/categorization.py` |

---

## 🗂️ Project Structure

```text
zenflow-server/
├── run.py                        # entrypoint: dev / prod / debug runners (Waitress)
├── pytest.ini                    # test discovery + coverage gate (85%)
├── requirements.txt              # pinned runtime deps
├── requirements-dev.txt          # runtime + pytest, ruff, mypy, coverage
├── .env.example                  # every supported env var, documented
│
├── app/
│   ├── __init__.py               # create_app() — the composition root
│   ├── config.py                 # Settings: typed, immutable, env-driven
│   ├── extensions.py             # JWT, CORS, compression, rate limiting
│   ├── db.py                     # Mongo connection + index bootstrap
│   │
│   ├── core/                     # cross-cutting primitives
│   │   ├── logging.py            # JSON logs + per-request correlation id
│   │   ├── exceptions.py         # AppError hierarchy (400/401/404/413/415/503)
│   │   ├── responses.py          # api_response() — the one serializer
│   │   ├── query.py              # pagination helpers
│   │   ├── validation.py         # require_fields()
│   │   ├── telemetry.py          # Sentry (opt-in)
│   │   └── scheduler.py          # APScheduler reminder-delivery job
│   │
│   ├── api/                      # HTTP layer: validate → service → serialise
│   │   ├── __init__.py           # blueprint registration (URL prefixes)
│   │   ├── auth.py  users.py  tasks.py  subtasks.py  notifications.py
│   │   ├── planner.py  summaries.py  daily_recap.py  weekly_recap.py
│   │   ├── dashboard.py  calendar.py  mood.py  reflections.py  progress.py
│   │   ├── suggestions.py  devices.py  reminders.py  sync.py  health.py
│   │
│   ├── services/                 # business rules
│   │   ├── __init__.py           # Services container + get_services()
│   │   └── *_service.py          # auth, task, mood, reminder, sync, …
│   │
│   ├── repositories/             # data access (Mongo queries only)
│   │   ├── base.py               # insert/find/update/delete + updatedAt stamping
│   │   └── *_repository.py       # one per collection
│   │
│   ├── utils/                    # external integrations
│   │   ├── groq_client.py  llm_utils.py  llm_prompts.py   # NLP + titles + summaries
│   │   ├── assemblyai_utils.py  pdf_to_text.py            # voice + PDF
│   │   ├── ocr_utils.py  push_client.py                   # OCR + Expo push
│   │   ├── categorization.py  title_utils.py  affirmations.py
│   │   ├── summary_utils.py  sub_tasks_utils.py
│   │   └── avatars.py                                     # server-hosted avatar catalogue
│   │
│   └── assets/avatars/           # avatar images (GET /api/users/avatars/<file>)
│
├── docs/
│   ├── README.md                 # full API reference (index + conventions)
│   ├── sections/                 # per-blueprint request/response docs (01–19)
│   ├── client.md                 # build-the-app guide (screens → endpoints)
│   ├── ai-flows.md               # AI pipelines + provider config
│   └── TODO.md                   # done / open work
│
└── tests/
    ├── conftest.py               # app / client / auth fixtures (in-memory DB)
    ├── support/fake_mongo.py     # dependency-free PyMongo stand-in
    └── test_*.py                 # 186 endpoint / security / feature tests
```

---

## 🧪 Testing & Quality Gates

```bash
pip install -r requirements-dev.txt
python -m pytest              # 186 tests + coverage gate (fails under 85%)
ruff check app tests run.py   # lint — must be clean
mypy                          # type check — must be clean
```

| Gate | Status |
|------|--------|
| Tests | **186 passing** |
| Coverage | **89%** (gate 85%) |
| Lint (`ruff`) | clean |
| Types (`mypy`) | clean |

Tests run against an **in-memory Mongo stand-in** (`tests/support/fake_mongo.py`) — no database or
network required. Provider calls (Groq / AssemblyAI / OCR / Expo) are stubbed, and the scheduler +
push are disabled in the test settings.

---

## 🗄️ Database

MongoDB collections (indexes auto-created at boot; every `*Id` is uniquely indexed):

| Collection | Holds |
|------------|-------|
| `users` | accounts, `preferences` (theme, fontSize, layout, notificationStyle) |
| `tasks` | tasks incl. `category`, `dueDate`, `hasSubtasks`, `createdFrom`, `updatedAt` |
| `subtasks` | checklist items per task |
| `planner` | per-day plans (focus, tasks, reflection) |
| `summaries` | PDF / note summaries + bullets |
| `notifications` | in-app notification feed |
| `mood_entries` | mood journal (`mood`, `score`, `energy`, tags) |
| `reflections` | daily journal entries |
| `push_devices` | Expo push tokens per user |
| `scheduled_reminders` | reminders (pending → sent) |
| `tombstones` | deletion records for offline sync |
| `token_blocklist` | revoked JWTs (TTL-indexed) |

---

## 📌 Notes & Configuration

- **MongoDB must be reachable at boot** (5s fail-fast); indexes are created automatically.
- **Logs** are structured JSON with `X-Request-ID` correlation ids (echoed in responses).
- **Security headers** on every response: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`.
- **Rate limiting** per IP (default `600/min`, auth routes `60/min`) → JSON `429`; health probes exempt.
- **Uploads** capped via `ZENFLOW_MAX_UPLOAD_MB` (default 16 MB) → JSON `413`.
- **AI flows** need keys; without them they answer `503` (never crash). See [`docs/ai-flows.md`](docs/ai-flows.md).
- **Scheduler** (`ZENFLOW_SCHEDULER_ENABLED`, default on) uses APScheduler to deliver due reminders.
- **Offline sync** relies on `updatedAt` on every document + `tombstones` for deletions.
- **Errors:** JSON `{ "message": "..." }` for 4xx/5xx; server details stay in the logs.
- **Filtering/paging:** list endpoints return a bare array unless `page`/`limit` are supplied.

---

## 📎 Documentation

| Doc | What's inside |
|-----|---------------|
| **[docs/README.md](docs/README.md)** | API index, conventions, error shapes, quick start |
| **[docs/sections/](docs/sections/)** | Per-blueprint request/response reference (01–19) |
| **[docs/client.md](docs/client.md)** | Build-the-app guide: screens → endpoints |
| **[docs/ai-flows.md](docs/ai-flows.md)** | AI pipelines, provider config, failure semantics |
| **[docs/TODO.md](docs/TODO.md)** | Done + open work |

---

<div align="center">

**Client app:** [BazilSuhail/Zenflow-App](https://github.com/BazilSuhail/Zenflow-App) · React Native + Expo
**Server:** this repo

Built with 🌿 for students who want to plan, reflect, and grow.

</div>
