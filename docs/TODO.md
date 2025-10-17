# 📌 TODO — ZenFlow API Docs & Improvements

Work list generated from the API analysis of `app/` + `run.py`.

## ✅ Done

- [x] Analyze all blueprints registered in `app/api/__init__.py`
- [x] Document all **41 active endpoints** across 10 sections
- [x] Add API count index → [docs/README.md](README.md)
- [x] Document auth scheme (JWT, 1h expiry) and response envelope
- [x] Document request/response bodies for every endpoint

## 🛡️ Sprint A — Security & Debt (done)

- [x] Fail-fast JWT secret: production refuses to boot with the built-in secret
      (`ZENFLOW_ALLOW_INSECURE_JWT=1` opts out, development warns only)
- [x] CORS allowlist via `ZENFLOW_CORS_ORIGINS` (comma-separated; default `*` = legacy parity)
- [x] Upload cap `MAX_CONTENT_LENGTH` via `ZENFLOW_MAX_UPLOAD_MB` (default 16 MB) → JSON `413`
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

## 📝 Documentation TODOs

- [ ] Add copy-paste `curl` example to every single endpoint (currently per-section only)
- [ ] Add real example responses captured from a live server run
- [ ] Generate an OpenAPI/Swagger spec (`swagger.json`) from these docs
- [ ] Document utility/LLM endpoints flow (AssemblyAI + Groq: voice → transcript → task)
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
- [ ] Subtask **LLM parse failures return 404** (legacy mapped every `ValueError` to 404);
      should become 400/502 — needs a client-aware decision.

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
- [ ] Rate limiting + request validation layer (e.g. `flask-smorest` / `marshmallow`) — *Sprint C*
- [x] Tests for all active endpoints under `tests/` — **87 passing**
