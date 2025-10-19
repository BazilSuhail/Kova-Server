"""Health probes, security headers, and the CORS surface (all public)."""
from __future__ import annotations


def test_health_returns_200_without_token(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_readiness_returns_200_when_database_reachable(client):
    response = client.get("/api/health/ready")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ready"}


def test_responses_carry_security_headers(client):
    response = client.get("/api/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"


def test_cors_allowlist_echoes_origin_by_default(client):
    # Default KOVA_CORS_ORIGINS is "*": any Origin is accepted (legacy parity).
    response = client.get("/api/health", headers={"Origin": "http://localhost:3000"})
    assert response.headers.get("Access-Control-Allow-Origin") in (
        "*",
        "http://localhost:3000",
    )
