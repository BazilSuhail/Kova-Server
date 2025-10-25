"""Minimal outbound mail over stdlib ``smtplib`` (password-reset codes).

Configured by ``SMTP_HOST``/``SMTP_PORT``/``SMTP_USER``/``SMTP_PASSWORD``/
``MAIL_FROM``. With no host configured nothing is sent; in development the
reset code is logged instead so the flow stays testable locally.
"""
from __future__ import annotations

import logging
import smtplib
import threading
from email.message import EmailMessage

from flask import Flask, current_app

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 10


def smtp_configured(app: Flask) -> bool:
    return bool(app.config.get("SMTP_HOST"))


def send_mail(app: Flask, to: str, subject: str, body: str) -> None:
    """Send one plain-text message synchronously (raises on SMTP failure)."""
    config = app.config
    host = config["SMTP_HOST"]
    port = int(config.get("SMTP_PORT") or 587)
    message = EmailMessage()
    message["From"] = config.get("MAIL_FROM") or config.get("SMTP_USER") or "no-reply@kova.app"
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    if port == 465:
        server: smtplib.SMTP = smtplib.SMTP_SSL(host, port, timeout=_TIMEOUT_SECONDS)
    else:
        server = smtplib.SMTP(host, port, timeout=_TIMEOUT_SECONDS)
    with server:
        if port != 465:
            server.ehlo()
            if server.has_extn("starttls"):
                server.starttls()
                server.ehlo()
        if config.get("SMTP_USER"):
            server.login(config["SMTP_USER"], config.get("SMTP_PASSWORD") or "")
        server.send_message(message)


def _send_logged(app: Flask, to: str, subject: str, body: str) -> None:
    try:
        send_mail(app, to, subject, body)
    except (smtplib.SMTPException, OSError):
        logger.exception("mail_send_failed")


def deliver_reset_code(email: str, code: str) -> None:
    """Mail a reset code without blocking the request.

    Sending happens on a background thread so response time does not reveal
    whether the address belongs to an account.
    """
    app: Flask = current_app._get_current_object()  # type: ignore[attr-defined]
    subject = "Your Kova password reset code"
    body = (
        f"Your Kova password reset code is {code}.\n\n"
        "It expires in 15 minutes. If you did not ask to reset your password, "
        "you can ignore this email."
    )
    if not smtp_configured(app):
        # Never log codes outside development: a log stream is not a mailbox.
        if app.debug or app.config.get("FLASK_ENV") == "development":
            logger.info("password_reset_code (SMTP not configured)", extra={"code": code})
        else:
            logger.warning("password_reset_requested but SMTP is not configured")
        return
    threading.Thread(
        target=_send_logged, args=(app, email, subject, body), daemon=True
    ).start()
