from __future__ import annotations

import os
from dataclasses import dataclass


from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    database_url: str

    google_oauth_client_secrets_file: str
    google_oauth_token_file: str
    google_oauth_redirect_uri: str
    google_oauth_scopes: list[str]


def get_settings() -> Settings:
    database_url = os.getenv("DATABASE_URL", "sqlite:///./mail_orchestrator.db")

    client_secrets_file = os.getenv("GOOGLE_OAUTH_CLIENT_SECRETS_FILE", "./secrets/credentials.json")
    token_file = os.getenv("GOOGLE_OAUTH_TOKEN_FILE", "./secrets/token.json")
    redirect_uri = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/auth/callback")
    scopes_raw = os.getenv(
        "GOOGLE_OAUTH_SCOPES",
        "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly",
    )
    scopes = [s.strip() for s in scopes_raw.split() if s.strip()]

    return Settings(
        database_url=database_url,
        google_oauth_client_secrets_file=client_secrets_file,
        google_oauth_token_file=token_file,
        google_oauth_redirect_uri=redirect_uri,
        google_oauth_scopes=scopes,
    )