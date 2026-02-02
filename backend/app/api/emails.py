from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.email import (
    EmailHistoryResponse,
    EmailSendRequest,
    EmailSendResponse,
    EmailMarkRespondedRequest,
    EmailActionResponse,
)
from app.services.email_service import create_email, list_history, mark_responded, resend_email, check_reply

from app.gmail.gmail_client import get_gmail_service
from app.gmail.gmail_sender import send_email_via_gmail

router = APIRouter(prefix="/api/emails", tags=["emails"])


@router.post("/send", response_model=EmailSendResponse, status_code=status.HTTP_201_CREATED)
def send_email(payload: EmailSendRequest, db: Session = Depends(get_db)):
    service = get_gmail_service()
    if not service:
        raise HTTPException(status_code=401, detail="Not authenticated. Complete OAuth login first.")

    data = payload.model_dump()

    ids = send_email_via_gmail(
        service=service,
        to=data["to"],
        subject=data["subject"],
        body_text=data.get("body_text"),
        body_html=data.get("body_html"),
        attachments=data.get("attachments") or [],
    )

    email = create_email(
        db,
        data,
        gmail_message_id=ids.get("gmail_message_id") or None,
        gmail_thread_id=ids.get("gmail_thread_id") or None,
    )
    return email


@router.get("/history", response_model=EmailHistoryResponse)
def read_history(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return list_history(db, limit=limit, offset=offset)

@router.post("/{email_id}/mark-responded", response_model=EmailActionResponse)
def manual_mark_responded(
    email_id: int,
    payload: EmailMarkRespondedRequest,
    db: Session = Depends(get_db),
):
    email = mark_responded(db, email_id=email_id, responded=payload.responded)
    if email is None:
        raise HTTPException(status_code=404, detail="Email not found")
    return email


@router.post("/{email_id}/resend", response_model=EmailActionResponse, status_code=status.HTTP_201_CREATED)
def resend(
    email_id: int,
    db: Session = Depends(get_db),
):
    email = resend_email(db, email_id=email_id)
    if email is None:
        raise HTTPException(status_code=404, detail="Email not found")
    return email

@router.post("/{email_id}/check-reply")
def check_reply_now(email_id: int, db: Session = Depends(get_db)):
    result = check_reply(db, email_id=email_id)

    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="Email not found")

    if result.get("status") == "missing_thread_id":
        raise HTTPException(status_code=400, detail="This email has no gmail_thread_id. Send via Gmail first.")

    if result.get("status") == "not_authenticated":
        raise HTTPException(status_code=401, detail="Not authenticated. Complete OAuth login first.")

    return result
