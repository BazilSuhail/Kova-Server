"""Health probes: liveness for process checks, readiness for dependency checks.

Both endpoints are public (no JWT) — load balancers and Railway/Kubernetes
probes cannot carry credentials.
"""
from __future__ import annotations

import logging

from flask import Blueprint, Response, current_app

from ..core.responses import api_response

logger = logging.getLogger(__name__)

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health() -> Response:
    """Liveness: the process is up and serving HTTP (no dependencies checked)."""
    return api_response({"status": "ok"}, 200)


@health_bp.route("/health/ready", methods=["GET"])
def readiness() -> Response:
    """Readiness: Mongo answers a ping → 200, otherwise 503 (probe retries)."""
    try:
        current_app.db.command("ping")
    except Exception:
        logger.warning("readiness_probe_failed", extra={"dependency": "mongodb"})
        return api_response({"status": "unavailable"}, 503)
    return api_response({"status": "ready"}, 200)
