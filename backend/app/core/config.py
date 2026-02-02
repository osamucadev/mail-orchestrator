from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str


def get_settings() -> Settings:
    """
    Simple env-based config.
    Deployment-ready because it can be overridden by DATABASE_URL later.
    """
    database_url = os.getenv("DATABASE_URL", "sqlite:///./mail_orchestrator.db")
    return Settings(database_url=database_url)
