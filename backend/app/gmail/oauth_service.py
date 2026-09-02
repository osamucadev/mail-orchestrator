from __future__ import annotations
import json
import time
from fastapi import HTTPException
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.models.account import Account, BrowserSession, OAuthAttempt, SessionAccount
from app.services.account_service import credential_cipher, digest

def get_flow(state: str | None = None) -> Flow:
    settings = get_settings()
    flow = Flow.from_client_secrets_file(settings.google_oauth_client_secrets_file,
                                         scopes=settings.google_oauth_scopes, state=state)
    flow.redirect_uri = settings.google_oauth_redirect_uri
    return flow

def get_login_url(db: Session, session: BrowserSession) -> str:
    flow = get_flow()
    url, state = flow.authorization_url(access_type="offline", include_granted_scopes="true",
                                         prompt="consent select_account")
    now = int(time.time())
    db.execute(delete(OAuthAttempt).where(OAuthAttempt.expires_at <= now))
    db.add(OAuthAttempt(state_hash=digest(state), session_id=session.id,
                        verifier_encrypted=credential_cipher().encrypt(flow.code_verifier.encode()).decode(),
                        expires_at=now + 600))
    db.commit()
    return url

def exchange_code_for_token(db: Session, session: BrowserSession | None, code: str | None, state: str | None) -> Account:
    attempt = db.get(OAuthAttempt, digest(state)) if state else None
    if (not session or not attempt or attempt.session_id != session.id
            or attempt.expires_at <= int(time.time())):
        raise HTTPException(400, "Invalid or expired OAuth request. Start login again.")
    verifier = credential_cipher().decrypt(attempt.verifier_encrypted.encode()).decode()
    # One-time consumption: cancelled and replayed callbacks cannot authorize an account.
    result = db.execute(delete(OAuthAttempt).where(OAuthAttempt.state_hash == attempt.state_hash))
    db.commit()
    if result.rowcount != 1 or not code:
        raise HTTPException(400, "Authorization was cancelled or already used")
    flow = get_flow(state)
    flow.code_verifier = verifier
    flow.fetch_token(code=code)
    creds = flow.credentials
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    profile = service.users().getProfile(userId="me").execute()
    email = (profile.get("emailAddress") or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(400, "Could not identify the authorized Gmail account")
    account = db.scalar(select(Account).where(Account.email == email))
    if account is None:
        account = Account(email=email)
        db.add(account)
        db.flush()
    token_data = json.loads(creds.to_json())
    if not token_data.get("refresh_token") and account.credentials_encrypted:
        old = json.loads(credential_cipher().decrypt(account.credentials_encrypted.encode()))
        token_data["refresh_token"] = old.get("refresh_token")
    account.credentials_encrypted = credential_cipher().encrypt(json.dumps(token_data).encode()).decode()
    if db.get(SessionAccount, (session.id, account.id)) is None:
        db.add(SessionAccount(session_id=session.id, account_id=account.id))
    db.commit()
    return account
