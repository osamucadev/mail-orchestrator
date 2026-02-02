from __future__ import annotations

from pydantic import BaseModel, Field


class TemplatePlaceholderRead(BaseModel):
    id: int
    template_id: int
    key: str = Field(..., min_length=1, max_length=128)
    label: str = Field(..., min_length=1, max_length=160)
    order_index: int

    class Config:
        from_attributes = True
