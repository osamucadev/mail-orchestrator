from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class EmailAttachmentIn(BaseModel):
    filename: str = Field(..., min_length=1, max_length=512)
    mime_type: str = Field(..., min_length=1, max_length=128)
    size_bytes: int = Field(..., ge=0)
    disposition: str = Field(..., min_length=1, max_length=16)
    content_id: str | None = Field(default=None, max_length=256)

    storage_path: str | None = Field(
        default=None,
        max_length=1024,
        description="Local storage path, will be used later when file upload is implemented.",
    )


class EmailSendRequest(BaseModel):
    to: str = Field(..., min_length=3, max_length=320)
    subject: str = Field(..., min_length=1, max_length=998)
    body_text: str | None = None
    body_html: str | None = None
    attachments: list[EmailAttachmentIn] = Field(default_factory=list)


class EmailSendResponse(BaseModel):
    id: int
    sent_at: datetime

    class Config:
        from_attributes = True


class EmailHistoryItem(BaseModel):
    id: int
    to: str
    subject: str
    sent_at: datetime
    responded: bool

    relative_time: str
    status_emoji: str

    class Config:
        from_attributes = True


class EmailHistoryResponse(BaseModel):
    items: list[EmailHistoryItem]
    limit: int
    offset: int
    total: int
