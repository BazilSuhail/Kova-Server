"""Forgot/reset password by emailed 6-digit code."""
from __future__ import annotations

import logging
import smtplib
from datetime import timedelta

import pytest
from app.services import auth_service
from app.utils import mailer

EMAIL = "ada@example.com"
OLD = "oldpass123"
NEW = "newpass456"
GENERIC = {"message": "If that email has an account, a reset code is on its way"}


@pytest.fixture()
def outbox(monkeypatch):
    sent: list[tuple[str, str]] = []
    monkeypatch.setattr(mailer, "deliver_reset_code", lambda e, c: sent.append((e, c)))
    return sent


@pytest.fixture()
def tokens(client):
    signup = client.post(
        "/api/auth/signup", json={"name": "Ada", "email": EMAIL, "password": OLD}
    )
    assert signup.status_code == 201
    return signup.get_json()


def _forgot(client, email=EMAIL):
    return client.post("/api/auth/password/forgot", json={"email": email})


def _reset(client, code, password=NEW, email=EMAIL):
    return client.post(
        "/api/auth/password/reset",
        json={"email": email, "code": code, "newPassword": password},
    )


def _login(client, password):
    return client.post("/api/auth/login", json={"email": EMAIL, "password": password})


def test_happy_path_sets_password_and_ends_sessions(client, tokens, outbox):
    response = _forgot(client)
    assert response.status_code == 200
    assert response.get_json() == GENERIC
    [(to, code)] = outbox
    assert to == EMAIL
    assert len(code) == 6 and code.isdigit()

    assert _reset(client, code).status_code == 200

    assert _login(client, OLD).status_code == 401
    assert _login(client, NEW).status_code == 200
    # Sessions issued before the reset are dead everywhere.
    me = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert me.status_code == 401
    refresh = client.post(
        "/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh.status_code == 401
    # The code is single-use.
    assert _reset(client, code, "another123").status_code == 400


def test_code_is_stored_hashed_and_never_exposed(app, client, tokens, outbox, auth):
    _forgot(client)
    [(_, code)] = outbox
    stored = app.db.users.find_one({"email": EMAIL})["passwordReset"]
    assert code not in str(stored)
    assert stored["attempts"] == 0
    profile = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    ).get_json()
    assert "passwordReset" not in profile


def test_wrong_code_is_rejected_and_counted(client, tokens, outbox):
    _forgot(client)
    [(_, code)] = outbox
    wrong = "000000" if code != "000000" else "111111"
    response = _reset(client, wrong)
    assert response.status_code == 400
    assert response.get_json() == {"message": "Invalid or expired code"}
    assert _login(client, OLD).status_code == 200
    # A wrong guess does not burn the code.
    assert _reset(client, code).status_code == 200


def test_expired_code_is_rejected(client, tokens, outbox, monkeypatch):
    monkeypatch.setattr(auth_service, "RESET_CODE_TTL", timedelta(seconds=-1))
    _forgot(client)
    [(_, code)] = outbox
    response = _reset(client, code)
    assert response.status_code == 400
    assert response.get_json() == {"message": "Invalid or expired code"}
    assert _login(client, OLD).status_code == 200


def test_attempts_exhausted_discards_the_code(client, tokens, outbox):
    _forgot(client)
    [(_, code)] = outbox
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(auth_service.RESET_MAX_ATTEMPTS):
        assert _reset(client, wrong).status_code == 400
    response = _reset(client, code)
    assert response.status_code == 400
    assert response.get_json() == {"message": "Too many attempts. Request a new code."}
    assert _reset(client, code).get_json() == {"message": "Invalid or expired code"}
    assert _login(client, OLD).status_code == 200


def test_unknown_email_still_200_and_sends_nothing(client, tokens, outbox):
    response = _forgot(client, "nobody@example.com")
    assert response.status_code == 200
    assert response.get_json() == GENERIC
    assert outbox == []
    assert _reset(client, "123456", email="nobody@example.com").status_code == 400


def test_resend_cooldown_keeps_first_code(client, tokens, outbox):
    _forgot(client)
    _forgot(client)
    assert len(outbox) == 1
    assert _reset(client, outbox[0][1]).status_code == 200


def test_validation(client, tokens, outbox):
    assert client.post("/api/auth/password/forgot", json={}).status_code == 400
    assert client.post(
        "/api/auth/password/reset", json={"email": EMAIL, "code": "1"}
    ).status_code == 400
    _forgot(client)
    weak = _reset(client, outbox[0][1], password="short")
    assert weak.status_code == 400
    # A weak password does not consume an attempt or the code.
    assert _reset(client, outbox[0][1]).status_code == 200


# --- mailer -------------------------------------------------------------------


def test_unconfigured_smtp_logs_code_only_in_development(app, caplog):
    caplog.set_level(logging.INFO, logger="app.utils.mailer")
    with app.app_context():
        app.config["FLASK_ENV"] = "production"
        mailer.deliver_reset_code(EMAIL, "424242")
        assert "424242" not in caplog.text
        app.config["FLASK_ENV"] = "development"
        mailer.deliver_reset_code(EMAIL, "424242")
    assert any(getattr(r, "code", None) == "424242" for r in caplog.records)


class _FakeSMTP:
    instances: list[_FakeSMTP] = []

    def __init__(self, host, port, timeout):
        self.host, self.port, self.sent, self.logged_in = host, port, [], None
        _FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def ehlo(self):
        pass

    def has_extn(self, name):
        return True

    def starttls(self):
        self.tls = True

    def login(self, user, password):
        self.logged_in = (user, password)

    def send_message(self, message):
        self.sent.append(message)


def test_configured_smtp_sends_over_starttls(app, monkeypatch):
    _FakeSMTP.instances = []
    monkeypatch.setattr(smtplib, "SMTP", _FakeSMTP)
    # Run the background send inline so it can be asserted.
    monkeypatch.setattr(
        mailer.threading, "Thread",
        lambda target, args, daemon: type("T", (), {"start": lambda s: target(*args)})(),
    )
    app.config.update(
        SMTP_HOST="smtp.test", SMTP_PORT=587, SMTP_USER="u", SMTP_PASSWORD="p",
        MAIL_FROM="Kova <no-reply@kova.test>",
    )
    with app.app_context():
        mailer.deliver_reset_code(EMAIL, "135790")
    [server] = _FakeSMTP.instances
    assert server.tls and server.logged_in == ("u", "p")
    [message] = server.sent
    assert message["To"] == EMAIL
    assert "135790" in message.get_content()


def test_smtp_failure_is_logged_not_raised(app, monkeypatch, caplog):
    def boom(*args, **kwargs):
        raise OSError("connection refused")

    monkeypatch.setattr(smtplib, "SMTP", boom)
    app.config.update(SMTP_HOST="smtp.test", SMTP_PORT=587)
    mailer._send_logged(app, EMAIL, "s", "b")  # must not raise
