from __future__ import annotations

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from app.core.config import get_settings
from app.gmail.token_store import load_credentials, save_credentials

settings = get_settings()


def get_valid_credentials() -> Credentials | None:
    creds = load_credentials(settings.google_oauth_token_file)
    if not creds:
        return None

    if creds.valid:
        return creds

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_credentials(settings.google_oauth_token_file, creds)
        return creds

    return None
