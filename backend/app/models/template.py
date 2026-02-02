from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(160), nullable=False)

    subject_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_text_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_html_template: Mapped[str | None] = mapped_column(Text, nullable=True)

    placeholders = relationship(
        "TemplatePlaceholder",
        back_populates="template",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="TemplatePlaceholder.order_index",
    )
