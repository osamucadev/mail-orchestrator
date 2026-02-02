from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.gmail.gmail_client import get_gmail_service

router = APIRouter(prefix="/api/gmail", tags=["gmail"])


@router.get("/profile")
def gmail_profile():
    service = get_gmail_service()
    if not service:
        raise HTTPException(status_code=401, detail="Not authenticated. Complete OAuth login first.")

    profile = service.users().getProfile(userId="me").execute()
    return {
        "emailAddress": profile.get("emailAddress"),
        "messagesTotal": profile.get("messagesTotal"),
        "threadsTotal": profile.get("threadsTotal"),
        "historyId": profile.get("historyId"),
    }
