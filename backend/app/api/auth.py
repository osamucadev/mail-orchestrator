from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.gmail.oauth_service import exchange_code_for_token, get_login_url, get_saved_credentials
from app.gmail.token_store import delete_credentials

router = APIRouter(prefix="/api/auth", tags=["auth"])

settings = get_settings()


@router.get("/status")
def auth_status():
    creds = get_saved_credentials()
    if not creds:
        return {"authenticated": False}

    return {
        "authenticated": True,
        "scopes": list(creds.scopes or []),
        "expiry": creds.expiry.isoformat() if creds.expiry else None,
    }


@router.post("/login")
def auth_login():
    url, state = get_login_url()
    return {"auth_url": url, "state": state}


@router.get("/callback")
def auth_callback(
    code: str = Query(...),
    state: str | None = Query(default=None),
):
    try:
        exchange_code_for_token(code=code, state=state)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth exchange failed: {e}")

    # For now, redirect to frontend. Vite runs on 5173.
    return RedirectResponse(url="http://localhost:5173/#auth-callback")


@router.post("/logout")
def auth_logout():
    delete_credentials(settings.google_oauth_token_file)
    return {"ok": True}
