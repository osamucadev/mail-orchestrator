from __future__ import annotations

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

from app.core.config import get_settings
from app.gmail.token_store import load_credentials, save_credentials

settings = get_settings()

# Guarda o code_verifier gerado no login, indexado pelo state,
# até o callback chegar e poder reaplicar ele no flow.
_pending_verifiers: dict[str, str] = {}


def get_flow(state: str | None = None) -> Flow:
    flow = Flow.from_client_secrets_file(
        settings.google_oauth_client_secrets_file,
        scopes=settings.google_oauth_scopes,
        state=state,
    )
    flow.redirect_uri = settings.google_oauth_redirect_uri
    return flow


def get_login_url() -> tuple[str, str]:
    flow = get_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    # o Flow gera o code_verifier (PKCE) sozinho aqui dentro.
    # guardamos ele para poder reaplicar no flow do callback.
    _pending_verifiers[state] = flow.code_verifier
    return auth_url, state


def exchange_code_for_token(code: str, state: str | None = None) -> Credentials:
    flow = get_flow(state=state)

    code_verifier = _pending_verifiers.pop(state, None) if state else None
    if code_verifier:
        flow.code_verifier = code_verifier

    flow.fetch_token(code=code)
    creds: Credentials = flow.credentials
    save_credentials(settings.google_oauth_token_file, creds)
    return creds


def get_saved_credentials() -> Credentials | None:
    return load_credentials(settings.google_oauth_token_file)