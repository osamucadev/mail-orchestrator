from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EmailAttachment(Base):
    __tablename__ = "email_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    email_id: Mapped[int] = mapped_column(ForeignKey("emails.id"), nullable=False)

    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)

    disposition: Mapped[str] = mapped_column(String(16), nullable=False)
    content_id: Mapped[str | None] = mapped_column(String(256), nullable=True)

    email = relationship("Email", back_populates="attachments")
