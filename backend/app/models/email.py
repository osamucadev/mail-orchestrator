from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    gmail_message_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    gmail_thread_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    to: Mapped[str] = mapped_column(String(320), nullable=False)
    subject: Mapped[str] = mapped_column(String(998), nullable=False)

    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)

    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    send_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    responded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    responded_source: Mapped[str | None] = mapped_column(String(16), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    attachments = relationship(
        "EmailAttachment",
        back_populates="email",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
