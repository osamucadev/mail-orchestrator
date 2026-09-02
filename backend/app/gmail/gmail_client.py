from __future__ import annotations

from googleapiclient.discovery import build
from googleapiclient.discovery import Resource
from sqlalchemy.orm import Session

from app.gmail.credentials_provider import get_valid_credentials


def get_gmail_service(db: Session) -> Resource | None:
    creds = get_valid_credentials(db)
    if not creds:
        return None

    # cache_discovery=False avoids creating cache files locally.
    return build("gmail", "v1", credentials=creds, cache_discovery=False)
