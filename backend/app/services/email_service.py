from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.time_utils import format_relative_time, pick_status_emoji
from app.models.email import Email
from app.models.email_attachment import EmailAttachment
from app.services.settings_service import get_or_create_settings
from app.models.email_attachment import EmailAttachment


def create_email(
    db: Session,
    data: dict,
    *,
    gmail_message_id: str | None = None,
    gmail_thread_id: str | None = None,
) -> Email:
    attachments = data.pop("attachments", [])

    email = Email(
        to=data["to"],
        subject=data["subject"],
        body_text=data.get("body_text"),
        body_html=data.get("body_html"),
        sent_at=datetime.now(timezone.utc),
        responded=False,
        responded_at=None,
        responded_source=None,
        last_checked_at=None,
        gmail_message_id=gmail_message_id,
        gmail_thread_id=gmail_thread_id,
    )

    db.add(email)
    db.commit()
    db.refresh(email)

    for a in attachments:
        db.add(
            EmailAttachment(
                email_id=email.id,
                filename=a["filename"],
                mime_type=a["mime_type"],
                size_bytes=a["size_bytes"],
                storage_path=a.get("storage_path") or "pending",
                disposition=a["disposition"],
                content_id=a.get("content_id"),
            )
        )

    db.commit()
    db.refresh(email)
    return email


def list_history(db: Session, limit: int, offset: int) -> dict:
    total = db.scalar(select(func.count()).select_from(Email)) or 0

    stmt = select(Email).order_by(Email.id.desc()).limit(limit).offset(offset)
    emails = list(db.scalars(stmt).all())

    settings = get_or_create_settings(db)
    thresholds = {
        "t_white_minutes": settings.t_white_minutes,
        "t_blue_minutes": settings.t_blue_minutes,
        "t_yellow_minutes": settings.t_yellow_minutes,
        "t_red_minutes": settings.t_red_minutes,
    }

    now = datetime.now(timezone.utc)
    items = []

    for e in emails:
        sent_at = e.sent_at
        if sent_at.tzinfo is None:
            sent_at = sent_at.replace(tzinfo=timezone.utc)

        elapsed_minutes = int((now - sent_at).total_seconds() // 60)
        if elapsed_minutes < 0:
            elapsed_minutes = 0

        relative_time = format_relative_time(sent_at, now=now)

        if e.responded:
            status_emoji = "🟢"
        else:
            status_emoji = pick_status_emoji(elapsed_minutes, thresholds)

        items.append(
            {
                "id": e.id,
                "to": e.to,
                "subject": e.subject,
                "sent_at": e.sent_at,
                "responded": e.responded,
                "relative_time": relative_time,
                "status_emoji": status_emoji,
            }
        )

    return {
        "items": items,
        "limit": limit,
        "offset": offset,
        "total": total,
    }

def mark_responded(db: Session, email_id: int, responded: bool = True) -> Email | None:
    email = db.get(Email, email_id)
    if email is None:
        return None

    if responded:
        email.responded = True
        email.responded_at = datetime.now(timezone.utc)
        email.responded_source = "manual"
    else:
        email.responded = False
        email.responded_at = None
        email.responded_source = None

    db.commit()
    db.refresh(email)
    return email


def resend_email(db: Session, email_id: int) -> Email | None:
    """
    Local-only resend for now.

    Creates a new Email row with the same content and attachment metadata,
    but a new sent_at timestamp.

    Later this will be replaced by a real Gmail send operation.
    """
    original = db.get(Email, email_id)
    if original is None:
        return None

    new_email = Email(
        to=original.to,
        subject=original.subject,
        body_text=original.body_text,
        body_html=original.body_html,
        sent_at=datetime.now(timezone.utc),
        responded=False,
        responded_at=None,
        responded_source=None,
        last_checked_at=None,
        gmail_message_id=None,
        gmail_thread_id=None,
    )

    db.add(new_email)
    db.commit()
    db.refresh(new_email)

    # Copy attachment metadata
    for a in original.attachments:
        db.add(
            EmailAttachment(
                email_id=new_email.id,
                filename=a.filename,
                mime_type=a.mime_type,
                size_bytes=a.size_bytes,
                storage_path=a.storage_path,
                disposition=a.disposition,
                content_id=a.content_id,
            )
        )

    db.commit()
    db.refresh(new_email)
    return new_email

