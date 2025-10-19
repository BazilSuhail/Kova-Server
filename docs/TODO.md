# 📌 TODO — Kova API Docs & Improvements

Work list generated from the API analysis of `app/` + `run.py`.

## ✅ Done

- [x] Analyze all blueprints registered in `app/api/__init__.py`
- [x] Document all **41 active endpoints** across 10 sections
- [x] Add API count index → [docs/README.md](README.md)
- [x] Document auth scheme (JWT, 1h expiry) and response envelope
- [x] Document request/response bodies for every endpoint

## 🛡️ Sprint A — Security & Debt (done)

- [x] Fail-fast JWT secret: production refuses to boot with the built-in secret
      (`KOVA_ALLOW_INSECURE_JWT=1` opts out, development warns only)
- [x] CORS allowlist via `KOVA_CORS_ORIGINS` (comma-separated; default `*` = legacy parity)
- [x] Upload cap `MAX_CONTENT_LENGTH` via `KOVA_MAX_UPLOAD_MB` (default 16 MB) → JSON `413`
- [x] Security headers on every response: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`
- [x] Health endpoints `GET /api/health` + `GET /api/health/ready` (public)
- [x] Dead code deleted: `app/models/` (6 stubs) + `app/middleware/`
- [x] Deleting a task now cascade-deletes its subtasks (no more orphans)
- [x] bcrypt cost pinned to `rounds=12` explicitly
- [x] Test suite: **54 passing** (`python -m pytest`)

## 🚀 Sprint B — API Completeness (done)

- [x] `POST /api/auth/refresh` — 7-day refresh tokens with **rotation** (old token revoked on use)
- [x] `POST /api/auth/logout` — blocklists access + optional refresh token (`token_blocklist`
      collection, TTL index, checked on every protected request → instant revocation)
- [x] `GET /api/auth/me` and `PUT /api/auth/password` (verify current, min 8 chars)
- [x] `refresh_token` now returned by signup/login (additive — existing clients unaffected)
- [x] Pagination (`page`/`limit`, max 100) + filters for `GET /api/tasks/`
      (`completed`, `category`, `q`), `GET /api/notifications/` (`unread`),
      `GET /api/summaries/` — bare array kept when no page params are sent
- [x] `GET`/`DELETE /api/notifications/<id>`
- [x] Single-subtask `DELETE /api/subtasks/<id>` (resets parent `hasSubtasks` when last)
- [x] `PUT /api/planner/<id>` full update (whitelisted fields, was commented-out only)
- [x] `POST /api/summaries/<id>/convert-to-tasks` — persists the task suggestion
- [x] `GET /api/weekly-recap/` — rolling 7-day recap (`?end=YYYY-MM-DD`)
- [x] Test suite: **87 passing**; endpoint count **41** (29 legacy + health + 10 new)

## 🧰 Sprint C — Quality Gates (done)

- [x] Rate limiting (`flask-limiter`): per-IP `KOVA_RATELIMIT_DEFAULT` (600/min)
      + stricter `KOVA_RATELIMIT_AUTH` (60/min on signup/login/refresh/password),
      `X-RateLimit-*` headers, JSON `429`, health probes exempt,
      `KOVA_RATELIMIT_ENABLED=false` off-switch, `KOVA_RATELIMIT_STORAGE_URI` for Redis
- [x] Request-validation layer (`app/core/validation.py` — `require_fields`) wired into
      11 route payload checks with contract-identical messages
- [x] Sentry error tracking: active only when `KOVA_SENTRY_DSN` is set; 500s reported
- [x] Lint gate: **ruff clean** (config in `pyproject.toml`)
- [x] Type gate: **mypy clean** — 48 files
- [x] Coverage gate: `--cov-fail-under=85` in `pytest.ini` (current **88%**)
- [x] Test suite: **99 passing**

## 🤖 Sprint D — AI Features (done)

- [x] Fixed **hard-coded decommissioned Groq model** (`llama3-70b-8192` → configurable
      `KOVA_GROQ_MODEL`, default `llama-3.3-70b-versatile`) — all three AI flows were
      failing against live Groq
- [x] Shared Groq transport (`app/utils/groq_client.py`) — one place for URL, model,
      timeout (`KOVA_LLM_TIMEOUT_SECONDS`), key guard, and response envelope
- [x] Missing provider key → **503** `{"message": "AI provider is not configured"}`
      on all AI flows (was a confusing upstream 401 reported as client error)
- [x] **Subtask LLM failures now 502** `{"message": "Subtask generation failed"}`
      (tracked issue closed — was wrongly 404; task-not-found stays 404)
- [x] Subtask over-delivery (>8 items) truncated to the promised 3–8 instead of stored raw
- [x] Task-field type validation (a hallucinated non-string field can no longer be persisted)
- [x] Legacy status contracts preserved everywhere else: NLP → 400, voice/summary → 500
- [x] AI flow reference doc → [docs/ai-flows.md](ai-flows.md)
- [x] Test suite: **115 passing**; coverage **92%**

## 🚀 Sprint E — Performance (done)

- [x] **Planner list N+1 eliminated** — one `$in` query for all planners instead of
      one task lookup per planner (output order/dangling-id semantics unchanged)
- [x] **Weekly recap 14 queries → 2** — one dueDate range + one planner date range
      for the whole 7-day window instead of two lookups per day
- [x] **Response compression** (gzip/brotli via `flask-compress`) for JSON/text ≥500 B
      when the client sends `Accept-Encoding` — `KOVA_COMPRESS_ENABLED=false` opts out
- [x] New indexes: `tasks(userId, dueDate)`, `planner(userId, date)`,
      `notifications(userId, createdAt)` — cover recap ranges and feed sorts
- [x] `Server-Timing: app;dur=<ms>` header on every response (latency visibility)
- [x] Waitress thread count configurable via `KOVA_WEB_THREADS` (defaults unchanged)
- [x] Fake-Mongo test double gained `$gt/$gte/$lt/$lte` range operators
- [x] Test suite: **121 passing**; coverage **92%**

## 🌿 Sprint F — Life-Assistant MVP (done)

- [x] **20/20 product features** now have server support (17 core + 3 bonus); API grew **41 → 73 endpoints**
- [x] New surfaces: dashboard, calendar (day/week/month), mood journal + trends, reflections +
      affirmations, progress tracker, adaptive suggestions, devices (Expo push), reminders, sync
- [x] Task flows: auto-categorisation (local heuristic + `POST /api/tasks/<id>/categorize`),
      smart title generator (`/suggest-title`, `/<id>/rewrite-title`),
      camera/OCR quick-add (`POST /api/tasks/create/image` via OCR.space)
- [x] Notes summariser `POST /api/summaries/create-from-text` (3–5 bullets; PDF path unchanged 4–9)
- [x] Customisation `GET/PUT /api/users/profile/settings` (theme, fontSize, layout, notificationStyle)
- [x] **Smart reminders**: APScheduler job (`app/core/scheduler.py`) delivers due reminders as
      in-app notifications + Expo push; dead tokens auto-pruned
- [x] **Offline sync**: `updatedAt` on every document + `POST /api/sync/pull` / `push`
      (delta pull, last-write-wins push) + `tombstones` collection for deletions
- [x] New collections: `mood_entries`, `reflections`, `push_devices`, `scheduled_reminders`,
      `tombstones` (+ indexes incl. `(userId, updatedAt)` sync scans)
- [x] Declared previously-missing runtime dep `Flask-Limiter`; added `APScheduler`
- [x] Server-hosted **avatar catalogue**: `GET /api/users/avatars` (catalogue) +
      `GET /api/users/avatars/<file>` (public image), selectable via `avatarId` on
      `PUT /api/users/profile`; assets live in `app/assets/avatars`
- [x] `DELETE /api/users/profile` now **cascades** — removes tasks, subtasks, planner,
      summaries, notifications, mood, reflections, reminders, devices, tombstones and
      revoked-token rows (other users untouched)
- [x] Tests: **186 passing**; coverage **89%**; ruff + mypy clean
- [x] Docs: 9 new section pages (11–19), refreshed root + API README, `.env.example`, client guide
      (5-tab navigation + stacks, every screen → endpoint, "Zenith Aura" design tokens)

## 📝 Documentation TODOs

- [ ] Add copy-paste `curl` example to every single endpoint (currently per-section only)
- [ ] Add real example responses captured from a live server run
- [ ] Generate an OpenAPI/Swagger spec (`swagger.json`) from these docs
- [x] Document utility/LLM endpoints flow (AssemblyAI + Groq: voice → transcript → task)
      → [docs/ai-flows.md](ai-flows.md)
- [ ] Add a "Postman collection" export
- [x] Update root `README.md` — rewritten in the production refactor (full endpoint table)

## 🐛 Code Issues Found While Documenting

Fixed in the production refactor:

- [x] **`/api/daily-recap/` was permanently broken** (unregistered local `tasks_bp`,
      tuple-caused regex bug, missing `mood` field) → rewritten as `DailyRecapService`.
- [x] `summaries_bp.db = app.db` assigned twice in `app/api/__init__.py` — blueprint
      `db` injection removed entirely (services container in `app/extensions`-style wiring).
- [x] Dead/commented-out route block at the bottom of `app/api/planner.py` — removed.
- [x] Debug `print()` calls (25 of them) → structured JSON logs with correlation ids.
- [x] Error messages leaked internals (`Server error: {str(e)}`) → generic
      `{"message": "Internal server error"}` with the full traceback in logs only.
- [x] `JWT_SECRET_KEY` hard-coded fallback → still accepted for token compatibility,
      but **production now refuses to boot** with the built-in secret (Sprint A);
      development logs `jwt_secret_insecure_default`.
- [x] `run.py` crashed on Windows when stdout was redirected (cp1252 vs emoji banners) → fixed.

Still open:

- [ ] **`summaries` create still returns an unpersisted `task` suggestion** (legacy
      response kept as-is) — clients can persist it via the new
      `POST /api/summaries/<id>/convert-to-tasks`.
- [x] Subtask **LLM parse failures returned 404** (legacy mapped every `ValueError` to
      404) → **fixed in Sprint D**: they now answer `502` with a stable message;
      task-not-found still returns `404`.
- [ ] **Corrupt/unreadable PDF still answers 500** on `POST /api/summaries/create`
      (legacy contract) — could become `400` with a client-aware decision.

## 🔮 Feature/API TODOs

- [x] Add `GET /api/notifications/<id>` (single) + `DELETE /api/notifications/<id>`
- [x] Add single-subtask delete (`DELETE /api/subtasks/<subtask_id>`)
- [x] Add pagination for `GET /api/tasks/`, `GET /api/summaries/`, `GET /api/notifications/`
      (+ task filters `completed`/`category`/`q` and notification `unread`)
- [x] Add `POST /api/auth/refresh` (rotating refresh token) and `POST /api/auth/logout` (blocklist)
- [x] Add `PUT /api/planner/<planner_id>` (full update — route existed only commented out)
- [x] Add `POST /api/summaries/<summary_id>/convert-to-tasks` (persist task suggestion)
- [x] Add `GET /api/weekly-recap/` (rolling 7-day recap)
- [x] Add health-check endpoint `GET /api/health` for Railway/Waitress probes
      (+ `GET /api/health/ready` with Mongo ping → 503)
- [x] Rate limiting + request validation layer — *Sprint C* (see above)
- [x] Tests for all active endpoints under `tests/` — **99 passing**
