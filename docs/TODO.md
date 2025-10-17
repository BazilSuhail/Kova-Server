# 📌 TODO — ZenFlow API Docs & Improvements

Work list generated from the API analysis of `app/` + `run.py`.

## ✅ Done

- [x] Analyze all blueprints registered in `app/api/__init__.py`
- [x] Document all **29 active endpoints** across 8 sections
- [x] Add API count index → [docs/README.md](README.md)
- [x] Document auth scheme (JWT, 1h expiry) and response envelope
- [x] Document request/response bodies for every endpoint

## 📝 Documentation TODOs

- [ ] Add copy-paste `curl` example to every single endpoint (currently per-section only)
- [ ] Add real example responses captured from a live server run
- [ ] Generate an OpenAPI/Swagger spec (`swagger.json`) from these docs
- [ ] Document MongoDB schemas from `app/models/` as a separate "Data Models" section
- [ ] Document utility/LLM endpoints flow (AssemblyAI + Groq: voice → transcript → task)
- [ ] Add a "Postman collection" export
- [ ] Update root `README.md` — its endpoint list is outdated/incomplete
      (missing NLP/voice task creation, summaries CRUD, daily recap, PUT/DELETE profile)

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
      but production boots log `jwt_secret_insecure_default` until `ZENFLOW_JWT_SECRET` is set.
- [x] `run.py` crashed on Windows when stdout was redirected (cp1252 vs emoji banners) → fixed.

Still open:

- [ ] **`summaries` create returns a `task` that is never inserted** into `db.tasks`
      (legacy behavior — kept as-is to avoid silent data-model changes).
- [ ] Subtask **LLM parse failures return 404** (legacy mapped every `ValueError` to 404);
      should become 400/502 — needs a client-aware decision.
- [ ] `app/models/` (schema stubs) and `app/middleware/auth.py` are dead code — awaiting
      approval to delete or wire up.

## 🔮 Feature/API TODOs

- [ ] Add `GET /api/notifications/<id>` (single) + `DELETE /api/notifications/<id>`
- [ ] Add `POST /api/subtasks/<subtask_id>`-style single-subtask delete (currently only bulk per task)
- [ ] Add pagination for `GET /api/tasks/`, `GET /api/summaries/`, `GET /api/notifications/`
- [ ] Add `POST /api/auth/refresh` (refresh token) and `POST /api/auth/logout` (token blacklist)
- [ ] Add `PUT /api/planner/<planner_id>` (full update — route exists only commented out)
- [ ] Add health-check endpoint `GET /api/health` for Railway/Waitress probes
- [ ] Rate limiting + request validation layer (e.g. `flask-smorest` / `marshmallow`)
- [ ] Tests for all 29 endpoints under `tests/`
