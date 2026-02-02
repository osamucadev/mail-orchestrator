from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parseaddr
from typing import Any

from googleapiclient.discovery import Resource


@dataclass(frozen=True)
class ReplyCheckResult:
    replied: bool
    replied_at: datetime | None
    reason: str


def get_my_email(service: Resource) -> str:
    profile = service.users().getProfile(userId="me").execute()
    return str(profile.get("emailAddress") or "").strip().lower()


def _parse_from_header(headers: list[dict[str, str]]) -> str:
    for h in headers:
        if (h.get("name") or "").lower() == "from":
            _, addr = parseaddr(h.get("value") or "")
            return (addr or "").strip().lower()
    return ""


def _internal_date_to_dt(msg: dict[str, Any]) -> datetime | None:
    internal_date = msg.get("internalDate")
    if not internal_date:
        return None

    try:
        ms = int(internal_date)
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    except Exception:
        return None


def check_thread_for_reply(
    *,
    service: Resource,
    thread_id: str,
    sent_at: datetime,
) -> ReplyCheckResult:
    if sent_at.tzinfo is None:
        sent_at = sent_at.replace(tzinfo=timezone.utc)

    my_email = get_my_email(service)

    thread = (
        service.users()
        .threads()
        .get(
            userId="me",
            id=thread_id,
            format="metadata",
            metadataHeaders=["From", "Date", "Message-Id", "In-Reply-To", "References"],
        )
        .execute()
    )

    messages: list[dict[str, Any]] = thread.get("messages") or []
    if not messages:
        return ReplyCheckResult(replied=False, replied_at=None, reason="thread_has_no_messages")

    newest_reply_dt: datetime | None = None

    for m in messages:
        payload = m.get("payload") or {}
        headers = payload.get("headers") or []
        from_addr = _parse_from_header(headers)

        msg_dt = _internal_date_to_dt(m)
        if not msg_dt:
            continue

        is_after_send = msg_dt > sent_at
        is_from_other = bool(from_addr) and (from_addr != my_email)

        if is_after_send and is_from_other:
            if newest_reply_dt is None or msg_dt > newest_reply_dt:
                newest_reply_dt = msg_dt

    if newest_reply_dt:
        return ReplyCheckResult(replied=True, replied_at=newest_reply_dt, reason="reply_found_in_thread")

    return ReplyCheckResult(replied=False, replied_at=None, reason="no_reply_found")
