from __future__ import annotations

from googleapiclient.discovery import build
from googleapiclient.discovery import Resource

from app.gmail.credentials_provider import get_valid_credentials


def get_gmail_service() -> Resource | None:
    creds = get_valid_credentials()
    if not creds:
        return None

    # cache_discovery=False avoids creating cache files locally.
    return build("gmail", "v1", credentials=creds, cache_discovery=False)
