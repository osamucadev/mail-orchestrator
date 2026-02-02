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
from app.services.email_service import create_email, list_history, mark_responded, resend_email

router = APIRouter(prefix="/api/emails", tags=["emails"])


@router.post("/send", response_model=EmailSendResponse, status_code=status.HTTP_201_CREATED)
def send_email(payload: EmailSendRequest, db: Session = Depends(get_db)):
    email = create_email(db, payload.model_dump())
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
