from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.email import EmailHistoryResponse, EmailSendRequest, EmailSendResponse
from app.services.email_service import create_email, list_history

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
