from __future__ import annotations

from pydantic import BaseModel, Field


class SettingsBase(BaseModel):
    t_white_minutes: int = Field(..., ge=0)
    t_blue_minutes: int = Field(..., ge=0)
    t_yellow_minutes: int = Field(..., ge=0)
    t_red_minutes: int = Field(..., ge=0)


class SettingsRead(SettingsBase):
    id: int

    class Config:
        from_attributes = True


class SettingsUpdate(SettingsBase):
    pass
