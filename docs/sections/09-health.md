# 09 — Health

**Blueprint:** `health_bp` · **Prefix:** `/api` · **File:** `app/api/health.py`
**Auth:** public (no JWT — load balancers and Railway/K8s probes cannot carry credentials)

Probe conventions:

- **Liveness** (`/api/health`) — is the process up and serving HTTP? Never checks dependencies.
- **Readiness** (`/api/health/ready`) — can the app serve traffic? Pings MongoDB; returns `503` when unreachable so the orchestrator retries/drains instead of routing requests to a broken instance.

Both return the standard response envelope.

---

## GET /api/health

Liveness probe.

**Request** — no body, no headers beyond the defaults.

**Responses**

| Status | Body |
|--------|------|
| `200` | `{"status": "ok"}` |

```bash
curl http://127.0.0.1:5000/api/health
```

---

## GET /api/health/ready

Readiness probe (Mongo ping).

**Responses**

| Status | Body | Meaning |
|--------|------|---------|
| `200` | `{"status": "ready"}` | Mongo answered the ping |
| `503` | `{"status": "unavailable"}` | Mongo unreachable — probe fails, instance not ready |

```bash
curl http://127.0.0.1:5000/api/health/ready
```
