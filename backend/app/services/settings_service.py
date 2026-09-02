from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.services.account_service import account_id

from app.models.settings import Settings




def get_or_create_settings(db: Session) -> Settings:
    settings = db.scalar(select(Settings).where(Settings.account_id == account_id(db)))

    if settings is None:
        settings = Settings(
            account_id=account_id(db),
            t_white_minutes=1140,
            t_blue_minutes=4320,
            t_yellow_minutes=7200,
            t_red_minutes=10080,
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return settings


def update_settings(db: Session, data: dict) -> Settings:
    settings = get_or_create_settings(db)

    for key, value in data.items():
        setattr(settings, key, value)

    db.commit()
    db.refresh(settings)
    return settings
