from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.settings import Settings


DEFAULT_SETTINGS_ID = 1


def get_or_create_settings(db: Session) -> Settings:
    settings = db.get(Settings, DEFAULT_SETTINGS_ID)

    if settings is None:
        settings = Settings(
            id=DEFAULT_SETTINGS_ID,
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
