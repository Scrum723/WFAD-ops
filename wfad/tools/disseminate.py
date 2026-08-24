"""Send the package. Real email is optional; a labeled stub is acceptable until Wednesday."""

from __future__ import annotations

import json
import os
import smtplib
import uuid
from email.message import EmailMessage
from typing import Any

from .store import record_run


def _loads(payload: str | dict[str, Any] | list[Any]) -> Any:
    if isinstance(payload, (dict, list)):
        return payload
    try:
        return json.loads(payload or "{}")
    except json.JSONDecodeError:
        return payload


def _smtp_send(subject: str, body: str, recipients: list[str]) -> dict[str, Any]:
    host = os.environ.get("SMTP_HOST")
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    from_addr = os.environ.get("WFAD_FROM_EMAIL") or user
    if not (host and user and password and from_addr and recipients):
        return {
            "sent": False,
            "mode": "stub",
            "message_ids": [],
            "note": (
                "FAKE SEND — no email left this machine. "
                "Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD, WFAD_FROM_EMAIL "
                "for a real outbound message (required for the video)."
            ),
        }
    port = int(os.environ.get("SMTP_PORT", "587"))
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(recipients)
    msg.set_content(body)
    with smtplib.SMTP(host, port, timeout=20) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.send_message(msg)
    return {
        "sent": True,
        "mode": "smtp",
        "message_ids": [msg.get("Message-ID") or uuid.uuid4().hex],
        "note": "Real SMTP send completed.",
    }


def _leesa_placeholder() -> dict[str, Any]:
    return {
        "status": "skipped",
        "reason": (
            "Leesa posting client is not wired this week. "
            "One Leesa call is allowed only after the Firestore loop works. "
            "See docs/DISCLOSURE.md."
        ),
    }


def disseminate_package(package_json: str, channels_json: str = '["email"]') -> dict:
    """Persist the run and send approved channels.

    Args:
        package_json: JSON string of briefing + alert + watch facts.
        channels_json: JSON list of channels, for example '["email"]'.

    Returns:
        message ids, Firestore run_id, and send mode (stub or smtp).
    """
    package = _loads(package_json)
    if not isinstance(package, dict):
        package = {"raw": package}
    channels = _loads(channels_json)
    if isinstance(channels, str):
        channels = [channels]
    if not isinstance(channels, list):
        channels = ["email"]

    briefing = package.get("briefing") or package
    alert = package.get("alert") or {}
    loc = (package.get("watch") or {}).get("location") or {}
    city = loc.get("city") or briefing.get("location") or "WFAD"
    severity = alert.get("severity") or package.get("severity") or "ROUTINE"
    recipients = alert.get("recipients") or [
        item.strip()
        for item in os.environ.get("WFAD_RECIPIENTS", "operator@localhost").split(",")
        if item.strip()
    ]
    script = briefing.get("script") or package.get("script") or json.dumps(package)[:1500]
    social = briefing.get("social_blurb") or script[:260]

    subject = f"WFAD {severity} — {city}"
    body = (
        f"WFAD package\n"
        f"Severity: {severity}\n"
        f"Location: {city}\n"
        f"Channels: {', '.join(str(c) for c in channels)}\n\n"
        f"{script}\n\n"
        f"Social: {social}\n"
    )

    send_result: dict[str, Any] = {"sent": False, "mode": "skipped", "message_ids": [], "note": ""}
    if "email" in channels:
        send_result = _smtp_send(subject, body, recipients)

    leesa = _leesa_placeholder() if "social_stub" in channels else {"status": "not_requested"}

    persist_package = {
        "watch": package.get("watch"),
        "briefing": briefing,
        "alert": alert,
        "channels": channels,
        "severity": severity,
        "email_body": body,
        "send": send_result,
        "leesa": leesa,
    }
    stored = record_run(json.dumps(persist_package, default=str))

    return {
        "status": "success" if stored.get("status") == "success" else "partial",
        "send_mode": send_result.get("mode"),
        "message_ids": send_result.get("message_ids") or [],
        "firestore_run_id": stored.get("run_id"),
        "backend": stored.get("backend"),
        "email_body": body,
        "note": send_result.get("note"),
        "leesa": leesa,
        "record_run": stored,
    }
