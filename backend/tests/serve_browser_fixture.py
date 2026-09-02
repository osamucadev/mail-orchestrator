"""Manual browser-test fixture, never imported by the production application.

Run from backend: .venv/bin/python -m tests.serve_browser_fixture
Uses a temporary database and fake OAuth; Gmail sending is explicitly disabled.
"""
import os
import secrets
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlencode
from unittest.mock import MagicMock

temporary = tempfile.TemporaryDirectory(prefix="mail-orchestrator-browser-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{temporary.name}/test.db"
os.environ["ACCOUNT_TOKEN_KEY_FILE"] = str(Path(temporary.name) / "key")
os.environ["FRONTEND_ORIGIN"] = "http://127.0.0.1:5174"

import uvicorn
from fastapi.responses import HTMLResponse
from google.oauth2.credentials import Credentials
from app.db.base import Base
from app.db.session import engine
from app.main import app
from app.gmail import oauth_service
from app.api import emails
from app.services import email_service

Base.metadata.create_all(engine)


class FakeFlow:
    code_verifier = "browser-test-verifier"

    def authorization_url(self, **kwargs):
        state = secrets.token_urlsafe(24)
        return f"http://127.0.0.1:8001/test-consent?{urlencode({'state': state})}", state

    def fetch_token(self, code):
        self.credentials = Credentials(
            token=code, refresh_token="fake-refresh", token_uri="https://example.invalid/token",
            client_id="fake-client", client_secret="fake-secret",
            expiry=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1),
        )


def fake_build(*args, credentials, **kwargs):
    service = MagicMock()
    service.users.return_value.getProfile.return_value.execute.return_value = {"emailAddress": credentials.token}
    return service


def never_send(**kwargs):
    raise RuntimeError("Real sending is disabled in the browser-test fixture")


oauth_service.get_flow = lambda state=None: FakeFlow()
oauth_service.build = fake_build
emails.send_email_via_gmail = never_send
email_service.send_email_via_gmail = never_send


@app.get("/test-consent", response_class=HTMLResponse)
def consent(state: str):
    links = "".join(
        f'<p><a href="/api/auth/callback?{urlencode({"state": state, "code": email})}">{email}</a></p>'
        for email in ("first@example.com", "second@example.com")
    )
    return f"<h1>Simulated Gmail authorization — test data only</h1>{links}"


if __name__ == "__main__":
    try:
        uvicorn.run(app, host="127.0.0.1", port=8001)
    finally:
        engine.dispose()
        temporary.cleanup()
