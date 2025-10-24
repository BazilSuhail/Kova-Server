# 🚀 Deployment & Operations — Kova Server

Everything an operator needs: what this service is, how it is packaged, how it
is tested in CI, and how it is deployed to Docker Hub. Complements the product
overview in the [root README](../README.md) and the per-endpoint reference in
[`docs/README.md`](README.md).

---

## 1. What this service is

Kova Server is a **Flask 3.1 + MongoDB** JSON REST API that powers the Kova
AI life-assistant for students. It turns messy input (typed text, voice, note
photos/PDFs) into structured, categorised tasks; plans days; tracks mood and
progress; delivers reminders; and syncs offline clients.

| Aspect | Value |
|--------|-------|
| Language / runtime | Python **3.13** |
| Framework | Flask **3.1.3**, served by **Waitress** in prod |
| Database | MongoDB (PyMongo 4.18, no ORM — repositories over raw queries) |
| Auth | Stateless JWT (access 1h, refresh 7d, rotation + revocation blocklist) |
| Endpoints | **75** across 19 blueprints (7 public, 68 JWT-protected) |
| Default port | `5000` (`PORT` overrides) |
| Entry point | `python run.py --production` |

### Layered architecture

```text
HTTP ──▶ app/api/<blueprint>.py      validate + JWT auth   (HTTP layer)
      ──▶ app/services/<name>.py     business rules         (no Flask request objects)
      ──▶ app/repositories/*.py      Mongo reads/writes      (BaseRepository)
      ──▶ app/core/responses.py      api_response() serialiser (ObjectId→str, datetime→ISO)
```

Cross-cutting pieces: `app/config.py` (typed, immutable `Settings`),
`app/db.py` (connection + index bootstrap), `app/extensions.py`
(JWT/CORS/rate-limit/compression), `app/core/*` (logging, errors, validation,
telemetry, scheduler), `app/utils/*` (Groq, AssemblyAI, OCR, PDF, Expo push,
avatars, categorisation).

### Runtime topology

```text
        ┌──────────────────────────────┐
        │  React Native (Expo) client  │
        └───────────────┬──────────────┘
                        │ HTTPS / JSON (JWT Bearer)
        ┌───────────────▼──────────────┐
        │        Kova Server           │  ◀── this container
        │  Flask · Waitress · APSched. │
        └───────┬───────────────┬──────┘
                │               │
        ┌───────▼──────┐  ┌─────▼─────────────────────────────┐
        │   MongoDB    │  │ External providers (all optional) │
        │  collections │  │ Groq · AssemblyAI · OCR.space ·   │
        │  + indexes   │  │ Expo Push                         │
        └──────────────┘  └───────────────────────────────────┘
```

---

## 2. Repository map

| Path | Responsibility |
|------|----------------|
| `run.py` | Entry point — `--production` / `--development` / `--flask-debug` runners. |
| `app/__init__.py` | `create_app()` composition root (config → extensions → errors → DB → services → blueprints). |
| `app/config.py` | Immutable `Settings` from env (`Settings.from_env`, `Settings.for_testing`). |
| `app/db.py` | Mongo connect (5s fail-fast) + idempotent index bootstrap. |
| `app/extensions.py` | JWT, CORS, rate limiting, compression wiring. |
| `app/api/` | 19 blueprints — the HTTP surface (`/api/*`). |
| `app/services/` | Business rules; one module per feature. |
| `app/repositories/` | Mongo data access (`base.py` + one per collection). |
| `app/utils/` | External integrations (Groq/AssemblyAI/OCR/PDF/Expo) + helpers. |
| `app/core/` | Logging, exceptions, responses, pagination, validation, Sentry, scheduler. |
| `app/assets/avatars/` | Avatar catalogue served at `GET /api/users/avatars/<file>`. |
| `tests/` | 186 offline tests + `support/fake_mongo.py` in-memory double. |
| `docs/` | API reference (`docs/README.md`, `docs/sections/`), client + AI-flow guides. |

### Endpoint inventory (75)

`auth` 6 · `users` 7 · `tasks` 11 · `subtasks` 5 · `notifications` 5 ·
`planner` 6 · `summaries` 6 · `daily-recap` 1 · `weekly-recap` 1 · `health` 2 ·
`dashboard` 1 · `calendar` 1 · `mood` 6 · `reflections` 5 · `progress` 1 ·
`suggestions` 1 · `devices` 3 · `reminders` 5 · `sync` 2.

Mongo collections: `users`, `tasks`, `subtasks`, `planner`, `summaries`,
`notifications`, `mood_entries`, `reflections`, `push_devices`,
`scheduled_reminders`, `tombstones`, `token_blocklist`. Indexes are created
automatically at boot.

---

## 3. Test & quality map

Run everything exactly as CI does:

```bash
pip install -r requirements-dev.txt
ruff check app tests run.py     # lint  (config in pyproject.toml)
mypy                            # types (79 source files)
python -m pytest                # 186 tests, gate: ≥85% coverage (pytest.ini)
```

| Gate | Tool | Result |
|------|------|--------|
| Lint | `ruff` | clean |
| Types | `mypy` | clean |
| Tests | `pytest` | **186 passed** |
| Coverage | `pytest-cov` | **≈89%** (gate 85%) |

**Why the suite is CI-safe:** every test runs against the in-memory
`tests/support/fake_mongo.py` double and stubs all outbound calls
(`app.utils.groq_client.requests.post`, AssemblyAI, OCR, Expo). No database,
network, or API keys are required — which is why the container `test` stage can
run the whole suite during `docker build`.

---

## 4. Container image

`Dockerfile` is a simple single-stage build on `python:3.13-slim`: install
`requirements.txt`, copy `app/` + `run.py`, expose `5000`, and run
`python run.py --production` (Waitress). It needs no compiler toolchain — every
dependency ships a wheel.

```bash
# Build the production image
docker build -t kova-server .

# Run it (needs a reachable MongoDB + a real JWT secret)
docker run --rm -p 5000:5000 \
  -e KOVA_MONGO_URI="mongodb://host.docker.internal:27017/kova" \
  -e KOVA_JWT_SECRET="$(openssl rand -hex 32)" \
  kova-server
```

---

## 5. Local stack with Compose

`docker-compose.yml` runs the API and a MongoDB 7 instance with a health gate.

```bash
docker compose up --build          # http://localhost:5000
curl http://localhost:5000/api/health/ready
docker compose down                # add -v to wipe the Mongo volume
```

Defaults are development-safe (`KOVA_ENV=development` so the insecure JWT
secret only warns). Override via a local `.env` file — see `.env.example`.

---

## 6. CI/CD (GitHub Actions)

One workflow, `.github/workflows/docker.yml`, runs on push to `master`/`main`
and on `v*` tags (or manually from the Actions tab). It:

1. Sets up Python 3.13 and installs `requirements-dev.txt`.
2. Runs the test suite (`python -m pytest`) — a failure stops the pipeline.
3. Logs in to Docker Hub and runs a plain `docker build`.
4. Pushes `latest` and the commit-SHA tag with `docker push`.

This mirrors what the GitHub-hosted runner already supports out of the box
(Docker is pre-installed), so it needs no extra tooling.

### Required repository secrets

Set these under **Settings → Secrets and variables → Actions**:

| Secret | Description |
|--------|-------------|
| `DOCKERHUB_USERNAME` | Docker Hub account (namespace) that owns the image. |
| `DOCKERHUB_TOKEN` | Docker Hub **access token** (Account → Security → New access token) with Read & Write scope. |

The image is published as
`docker.io/<DOCKERHUB_USERNAME>/kova-server`. Change `IMAGE_NAME` in the
workflow to rename it.

```bash
# Pull the published image
docker pull <DOCKERHUB_USERNAME>/kova-server:latest
```

---

## 7. Required runtime configuration

Only two variables are effectively mandatory in production:

| Variable | Notes |
|----------|-------|
| `KOVA_MONGO_URI` | MongoDB connection string. The server **fails fast at boot** if unreachable (5s). |
| `KOVA_JWT_SECRET` | **Required** in `KOVA_ENV=production` — boot refuses the built-in secret. |

Common optional knobs (full list in `.env.example`): `PORT`, `KOVA_ENV`,
`KOVA_WEB_THREADS`, `KOVA_CORS_ORIGINS`, `KOVA_SCHEDULER_ENABLED`,
`KOVA_GROQ_API_KEY`, `KOVA_ASSEMBLYAI_API_KEY`, `KOVA_OCR_API_KEY`,
`KOVA_SENTRY_DSN`, `KOVA_RATELIMIT_*`, `KOVA_MAX_UPLOAD_MB`. Missing AI keys
never crash the app — those endpoints answer `503` instead.

### Production checklist

- [ ] `KOVA_ENV=production` and a strong `KOVA_JWT_SECRET`.
- [ ] Reachable MongoDB (Atlas or self-hosted) with the connection string set.
- [ ] `KOVA_CORS_ORIGINS` set to your client origin(s) instead of `*`.
- [ ] `KOVA_RATELIMIT_STORAGE_URI=redis://…` when running multiple workers.
- [ ] `KOVA_SENTRY_DSN` set to capture 500s.
- [ ] Terminate TLS at a proxy/load balancer (the app does not redirect to HTTPS).
- [ ] Probe `/api/health` for liveness and `/api/health/ready` for readiness.
