"""Account credentials stay on the server; cookies hold random session IDs."""
from __future__ import annotations
import hashlib
import os
import secrets
import time
from pathlib import Path
from cryptography.fernet import Fernet
from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.deps import get_db
from app.models.account import Account, BrowserSession, SessionAccount

COOKIE_NAME = "mo_session"
SESSION_SECONDS = 30 * 24 * 60 * 60

def frontend_origin() -> str:
    return os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").rstrip("/")

def require_origin(request: Request) -> None:
    if request.headers.get("origin") != frontend_origin():
        raise HTTPException(403, "Untrusted request origin")

def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()

def credential_cipher() -> Fernet:
    path = Path(os.getenv("ACCOUNT_TOKEN_KEY_FILE", str(Path(get_settings().google_oauth_token_file).with_name("account-token.key"))))
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        pass
    else:
        with os.fdopen(fd, "wb") as file:
            file.write(Fernet.generate_key())
    return Fernet(path.read_bytes())

def current_session(request: Request, db: Session) -> BrowserSession | None:
    raw = request.cookies.get(COOKIE_NAME)
    session = db.get(BrowserSession, digest(raw)) if raw else None
    if session is None or session.expires_at <= int(time.time()):
        return None
    return session

def ensure_session(request: Request, response: Response, db: Session) -> BrowserSession:
    session = current_session(request, db)
    if session is None:
        raw = secrets.token_urlsafe(32)
        session = BrowserSession(id=digest(raw), expires_at=int(time.time()) + SESSION_SECONDS)
        db.add(session)
        db.commit()
        response.set_cookie(COOKIE_NAME, raw, max_age=SESSION_SECONDS, httponly=True,
                            secure=frontend_origin().startswith("https://"), samesite="lax", path="/api")
    return session

def account_id(db: Session) -> int:
    value = db.info.get("account_id")
    if value is None:
        raise HTTPException(401, "Select an authenticated Gmail account")
    return value

def get_account_db(request: Request, db: Session = Depends(get_db)) -> Session:
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        require_origin(request)
    session = current_session(request, db)
    if session is None:
        raise HTTPException(401, "Login with Gmail first")
    try:
        selected = int(request.headers.get("X-Account-ID", ""))
    except ValueError:
        raise HTTPException(400, "X-Account-ID is required")
    membership = db.get(SessionAccount, (session.id, selected))
    account = db.get(Account, selected) if membership else None
    if account is None or not account.credentials_encrypted:
        raise HTTPException(403, "Account is not connected in this browser")
    db.info["account_id"] = account.id
    return db

def connected_accounts(db: Session, session: BrowserSession | None) -> list[dict]:
    if session is None:
        return []
    accounts = db.scalars(select(Account).join(SessionAccount).where(
        SessionAccount.session_id == session.id, Account.credentials_encrypted.is_not(None),
    ).order_by(Account.email)).all()
    return [{"id": account.id, "email": account.email} for account in accounts]
