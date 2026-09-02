from __future__ import annotations
import logging
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import delete
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.gmail.oauth_service import exchange_code_for_token, get_login_url
from app.models.account import Account, SessionAccount
from app.services.account_service import (
    account_id, connected_accounts, current_session, ensure_session, frontend_origin,
    get_account_db, require_origin,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)

@router.get("/status")
def auth_status(request: Request, db: Session = Depends(get_db)):
    accounts = connected_accounts(db, current_session(request, db))
    return {"authenticated": bool(accounts), "accounts": accounts}

@router.post("/login")
def auth_login(request: Request, response: Response, db: Session = Depends(get_db)):
    require_origin(request)
    session = ensure_session(request, response, db)
    return {"auth_url": get_login_url(db, session)}

@router.get("/callback")
def auth_callback(request: Request, code: str | None = None, state: str | None = None,
                  error: str | None = None, db: Session = Depends(get_db)):
    try:
        account = exchange_code_for_token(db, current_session(request, db), None if error else code, state)
        fragment = f"auth-callback?account_id={account.id}"
    except Exception as exc:
        logger.warning("OAuth callback failed (%s)", type(exc).__name__)
        db.rollback()
        fragment = "auth-callback?error=authorization_failed"
    return RedirectResponse(url=f"{frontend_origin()}/#{fragment}", status_code=303)

@router.post("/logout")
def auth_logout(db: Session = Depends(get_account_db)):
    selected = account_id(db)
    account = db.get(Account, selected)
    account.credentials_encrypted = None
    db.execute(delete(SessionAccount).where(SessionAccount.account_id == selected))
    db.commit()
    return {"ok": True}
