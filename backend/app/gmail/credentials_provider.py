from __future__ import annotations
import json
from fastapi import HTTPException
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from sqlalchemy.orm import Session
from app.models.account import Account
from app.services.account_service import account_id, credential_cipher

def get_valid_credentials(db: Session) -> Credentials | None:
    account = db.get(Account, account_id(db))
    if not account or not account.credentials_encrypted:
        return None
    cipher = credential_cipher()
    creds = Credentials.from_authorized_user_info(json.loads(cipher.decrypt(account.credentials_encrypted.encode())))
    if creds.valid:
        return creds
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError:
            raise HTTPException(401, "Gmail authorization expired. Reconnect this account.")
        account.credentials_encrypted = cipher.encrypt(creds.to_json().encode()).decode()
        db.commit()
        return creds
    return None
