from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.gmail.gmail_client import get_gmail_service
from app.gmail.gmail_sender import send_email_via_gmail
from app.schemas.email import (
    EmailActionResponse,
    EmailHistoryResponse,
    EmailMarkRespondedRequest,
    EmailSendRequest,
    EmailSendResponse,
)

from app.services.email_service import (
    check_reply,
    create_email,
    list_history,
    mark_responded,
    resend_email,
)

STORAGE_DIR = Path("./storage")

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

@router.post("/{email_id}/resend", response_model=EmailActionResponse, status_code=status.HTTP_201_CREATED)
def resend(
    email_id: int,
    db: Session = Depends(get_db),
):
    email = resend_email(db, email_id=email_id)
    if email is None:
        raise HTTPException(status_code=404, detail="Email not found")
    return email

@router.post("/send-multipart", response_model=EmailSendResponse, status_code=status.HTTP_201_CREATED)
def send_email_multipart(
    to: Annotated[str, Form()],
    subject: Annotated[str, Form()],
    body_text: Annotated[str | None, Form()] = None,
    body_html: Annotated[str | None, Form()] = None,
    inline_meta: Annotated[str | None, Form()] = None,
    inline_images: list[UploadFile] = File(default=[]),
    attachments: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
):
    service = get_gmail_service()
    if not service:
        raise HTTPException(status_code=401, detail="Not authenticated. Complete OAuth login first.")

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    upload_dir = STORAGE_DIR / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    inline_meta_list = []
    if inline_meta:
        try:
            inline_meta_list = json.loads(inline_meta)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid inline_meta JSON")

    meta_by_filename = {}
    for m in inline_meta_list:
        filename = str(m.get("filename") or "").strip()
        if filename:
            meta_by_filename[filename] = m

    stored_attachments = []

    # Save inline images
    for f in inline_images:
        content = f.file.read()
        filename = f.filename or "inline"
        meta = meta_by_filename.get(filename, {})
        content_id = str(meta.get("content_id") or "").strip()
        if not content_id:
            raise HTTPException(status_code=400, detail=f"Missing content_id for inline image: {filename}")

        dest = upload_dir / f"{int(datetime.now(timezone.utc).timestamp())}_{filename}"
        dest.write_bytes(content)

        stored_attachments.append(
            {
                "filename": filename,
                "mime_type": f.content_type or str(meta.get("mime_type") or "application/octet-stream"),
                "size_bytes": len(content),
                "storage_path": str(dest),
                "disposition": "inline",
                "content_id": content_id,
            }
        )

    # Save normal attachments
    for f in attachments:
        content = f.file.read()
        filename = f.filename or "attachment"
        dest = upload_dir / f"{int(datetime.now(timezone.utc).timestamp())}_{filename}"
        dest.write_bytes(content)

        stored_attachments.append(
            {
                "filename": filename,
                "mime_type": f.content_type or "application/octet-stream",
                "size_bytes": len(content),
                "storage_path": str(dest),
                "disposition": "attachment",
                "content_id": None,
            }
        )

    # Send via Gmail
    ids = send_email_via_gmail(
        service=service,
        to=to,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        attachments=stored_attachments,
    )

    data = {
        "to": to,
        "subject": subject,
        "body_text": body_text,
        "body_html": body_html,
        "attachments": stored_attachments,
    }

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
