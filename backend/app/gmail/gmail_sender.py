from __future__ import annotations

import base64
from typing import Any

from googleapiclient.discovery import Resource

from app.gmail.mime_builder import build_email_message


def _base64url_encode(raw_bytes: bytes) -> str:
    # Gmail expects base64url. Padding is optional but we strip it.
    return base64.urlsafe_b64encode(raw_bytes).decode("utf-8").rstrip("=")


def send_email_via_gmail(
    *,
    service: Resource,
    to: str,
    subject: str,
    body_text: str | None,
    body_html: str | None,
    attachments: list[dict[str, Any]] | None = None,
) -> dict[str, str]:
    msg = build_email_message(
        to=to,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        attachments=attachments,
    )

    raw = _base64url_encode(msg.as_bytes())

    result = (
        service.users()
        .messages()
        .send(userId="me", body={"raw": raw})
        .execute()
    )

    return {
        "gmail_message_id": result.get("id", ""),
        "gmail_thread_id": result.get("threadId", ""),
    }
