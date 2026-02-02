from __future__ import annotations

from pydantic import BaseModel, Field


class TemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    subject_template: str | None = None
    body_text_template: str | None = None
    body_html_template: str | None = None


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(TemplateBase):
    pass


class TemplateRead(TemplateBase):
    id: int

    class Config:
        from_attributes = True
