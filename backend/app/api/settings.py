from __future__ import annotations

from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.settings import SettingsRead, SettingsUpdate
from app.services.settings_service import get_or_create_settings, update_settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsRead)
def read_settings(db: Session = Depends(get_db)):
    return get_or_create_settings(db)


@router.put("", response_model=SettingsRead)
def write_settings(payload: SettingsUpdate, db: Session = Depends(get_db)):
    return update_settings(db, payload.model_dump())
