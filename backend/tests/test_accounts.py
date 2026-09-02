"""Account isolation tests. All Gmail calls are mocked; no real email is sent."""
import json
import os
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from google.oauth2.credentials import Credentials
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.deps import get_db
from app.main import app
from app.models.account import Account, BrowserSession, OAuthAttempt, SessionAccount
from app.models.email import Email
from app.models.email_attachment import EmailAttachment
from app.models.settings import Settings
from app.models.template import Template
from app.services.account_service import COOKIE_NAME, credential_cipher, digest


class AccountTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {
            "ACCOUNT_TOKEN_KEY_FILE": str(Path(self.tmp.name) / "token.key"),
            "FRONTEND_ORIGIN": "http://localhost:5173",
        })
        self.env.start()
        self.engine = create_engine("sqlite:///" + str(Path(self.tmp.name) / "test.db"),
                                    connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        def db_override():
            with self.sessions() as db:
                yield db
        app.dependency_overrides[get_db] = db_override
        self.client = TestClient(app)
        self.client.headers["Origin"] = "http://localhost:5173"
        self.client.headers["X-Account-ID"] = "1"
        self.client.cookies.set(COOKIE_NAME, "test-session", path="/api")
        self.creds = Credentials(token="fake-access", refresh_token="fake-refresh",
                                 token_uri="https://oauth2.googleapis.com/token",
                                 client_id="test-client", client_secret="test-secret",
                                 expiry=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1))
        encrypted = credential_cipher().encrypt(self.creds.to_json().encode()).decode()
        with self.sessions() as db:
            db.add_all([Account(id=1, email="srcaetite@gmail.com", credentials_encrypted=encrypted),
                        Account(id=2, email="other@example.com", credentials_encrypted=encrypted),
                        BrowserSession(id=digest("test-session"), expires_at=int(time.time()) + 3600)])
            db.flush()
            db.add_all([SessionAccount(session_id=digest("test-session"), account_id=i) for i in (1, 2)])
            for i in (1, 2):
                db.add(Email(id=i, account_id=i, to=f"recipient{i}@example.com",
                             subject=f"Account {i}", sent_at=datetime.now(timezone.utc),
                             gmail_thread_id=f"thread-{i}", send_count=1))
                db.add(Template(id=i, account_id=i, name=f"Template {i}"))
                db.add(Settings(id=i, account_id=i, t_white_minutes=10 * i,
                                t_blue_minutes=20, t_yellow_minutes=30, t_red_minutes=40))
            db.commit()

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.engine.dispose()
        self.env.stop()
        self.tmp.cleanup()

    def test_authentication_and_membership_are_required(self):
        self.client.cookies.clear()
        for path in ("/api/templates", "/api/settings", "/api/emails/history", "/api/gmail/profile"):
            self.assertEqual(self.client.get(path).status_code, 401)
        self.assertEqual(self.client.get("/api/auth/status").json()["accounts"], [])
        self.client.cookies.set(COOKIE_NAME, "test-session", path="/api")
        self.client.headers["X-Account-ID"] = "3"
        self.assertEqual(self.client.get("/api/templates").status_code, 403)
        with self.sessions() as db:
            db.delete(db.get(SessionAccount, (digest("test-session"), 2)))
            db.commit()
        self.client.headers["X-Account-ID"] = "2"
        self.assertEqual(self.client.get("/api/templates").status_code, 403)

    def test_expired_session_and_missing_account_are_rejected(self):
        del self.client.headers["X-Account-ID"]
        self.assertEqual(self.client.get("/api/templates").status_code, 400)
        with self.sessions() as db:
            db.get(BrowserSession, digest("test-session")).expires_at = 0
            db.commit()
        self.assertEqual(self.client.get("/api/templates").status_code, 401)

    def test_history_templates_settings_are_separate(self):
        for selected in (1, 2):
            self.client.headers["X-Account-ID"] = str(selected)
            history = self.client.get("/api/emails/history").json()
            self.assertEqual(history["total"], 1)
            self.assertEqual([item["id"] for item in history["items"]], [selected])
            templates = self.client.get("/api/templates").json()
            self.assertEqual([item["id"] for item in templates], [selected])
            self.assertEqual(self.client.get("/api/settings").json()["t_white_minutes"], 10 * selected)

    def test_other_accounts_ids_cannot_be_read_modified_or_sent(self):
        with patch("app.services.email_service.get_gmail_service") as gmail:
            requests = [
                ("GET", "/api/templates/2", None),
                ("GET", "/api/templates/2/placeholders", None),
                ("PUT", "/api/templates/2", {"name": "overwrite"}),
                ("DELETE", "/api/templates/2", None),
                ("POST", "/api/emails/2/mark-responded", {"responded": True}),
                ("POST", "/api/emails/2/resend", None),
                ("POST", "/api/emails/2/check-reply", None),
                ("DELETE", "/api/emails/2", None),
            ]
            for method, path, payload in requests:
                with self.subTest(path=path, method=method):
                    self.assertEqual(self.client.request(method, path, json=payload).status_code, 404)
            gmail.assert_not_called()
        with self.sessions() as db:
            self.assertEqual(db.get(Template, 2).name, "Template 2")
            self.assertFalse(db.get(Email, 2).responded)

    def test_new_template_and_placeholders_belong_to_selected_account(self):
        response = self.client.post("/api/templates", json={"name": "New", "body_text_template": "Hi {{company}}"})
        self.assertEqual(response.status_code, 201)
        template_id = response.json()["id"]
        self.assertEqual(self.client.get(f"/api/templates/{template_id}/placeholders").json()[0]["key"], "company")
        self.client.headers["X-Account-ID"] = "2"
        self.assertEqual(self.client.get(f"/api/templates/{template_id}").status_code, 404)

    def test_settings_updates_do_not_change_other_account(self):
        response = self.client.put("/api/settings", json={
            "t_white_minutes": 99, "t_blue_minutes": 100, "t_yellow_minutes": 101, "t_red_minutes": 102})
        self.assertEqual(response.status_code, 200)
        self.client.headers["X-Account-ID"] = "2"
        self.assertEqual(self.client.get("/api/settings").json()["t_white_minutes"], 20)

    def test_new_account_starts_empty_with_default_settings(self):
        with self.sessions() as db:
            db.add(Account(id=3, email="new@example.com", credentials_encrypted="fake"))
            db.flush()
            db.add(SessionAccount(session_id=digest("test-session"), account_id=3))
            db.commit()
        self.client.headers["X-Account-ID"] = "3"
        self.assertEqual(self.client.get("/api/emails/history").json()["total"], 0)
        self.assertEqual(self.client.get("/api/templates").json(), [])
        self.assertEqual(self.client.get("/api/settings").json()["t_white_minutes"], 1140)

    def test_json_attachments_cannot_read_arbitrary_server_files(self):
        with patch("app.api.emails.get_gmail_service", return_value=MagicMock()), patch("app.api.emails.send_email_via_gmail") as send:
            response = self.client.post("/api/emails/send", json={
                "to": "recipient@example.com", "subject": "Test", "attachments": [{
                    "filename": "secret", "mime_type": "text/plain", "size_bytes": 1,
                    "disposition": "attachment", "storage_path": "/etc/passwd"}]})
            self.assertEqual(response.status_code, 400)
            send.assert_not_called()

    def test_sends_and_resends_use_selected_credentials(self):
        def service(db):
            return f"gmail-account-{db.info['account_id']}"
        for selected in (1, 2):
            self.client.headers["X-Account-ID"] = str(selected)
            with patch("app.api.emails.get_gmail_service", side_effect=service), patch(
                "app.api.emails.send_email_via_gmail", return_value={"gmail_message_id": "fake", "gmail_thread_id": "fake-thread"}) as send:
                response = self.client.post("/api/emails/send", json={"to": "recipient@example.com", "subject": "Test"})
                self.assertEqual(response.status_code, 201)
                self.assertEqual(send.call_args.kwargs["service"], f"gmail-account-{selected}")
                with self.sessions() as db:
                    self.assertEqual(db.get(Email, response.json()["id"]).account_id, selected)
            with patch("app.services.email_service.get_gmail_service", side_effect=service), patch(
                "app.services.email_service.send_email_via_gmail", return_value={}) as send:
                self.assertEqual(self.client.post(f"/api/emails/{selected}/resend").status_code, 201)
                self.assertEqual(send.call_args.kwargs["service"], f"gmail-account-{selected}")

    def test_multipart_uploads_are_namespaced_and_collision_safe(self):
        with patch("app.api.emails.STORAGE_DIR", Path(self.tmp.name) / "uploads"), patch(
            "app.api.emails.get_gmail_service", return_value=MagicMock()), patch(
            "app.api.emails.send_email_via_gmail", return_value={}):
            for selected in (1, 2):
                self.client.headers["X-Account-ID"] = str(selected)
                response = self.client.post("/api/emails/send-multipart", data={"to": "recipient@example.com", "subject": "Test"},
                                            files=[("attachments", ("../../same.txt", b"contents", "text/plain"))])
                self.assertEqual(response.status_code, 201, response.text)
                with self.sessions() as db:
                    attachment = db.scalar(select(EmailAttachment).where(EmailAttachment.email_id == response.json()["id"]))
                    path = Path(attachment.storage_path)
                    self.assertEqual(path.parent.name, str(selected))
                    self.assertEqual(attachment.filename, "same.txt")
                    self.assertEqual(path.read_bytes(), b"contents")

    def test_disconnect_keeps_data_and_other_accounts_connected(self):
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 200)
        self.assertEqual(self.client.get("/api/auth/status").json()["accounts"], [{"id": 2, "email": "other@example.com"}])
        self.assertEqual(self.client.get("/api/templates").status_code, 403)
        with self.sessions() as db:
            self.assertIsNotNone(db.get(Email, 1))
            self.assertIsNotNone(db.get(Template, 1))
            self.assertIsNotNone(db.get(Settings, 1))
            self.assertIsNone(db.get(Account, 1).credentials_encrypted)

    def test_mutations_reject_untrusted_origin(self):
        self.client.headers["Origin"] = "https://malicious.example"
        self.assertEqual(self.client.post("/api/auth/login").status_code, 403)
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 403)
        self.assertEqual(self.client.delete("/api/emails/1").status_code, 403)

    def fake_flow(self):
        flow = MagicMock()
        flow.authorization_url.return_value = ("https://accounts.google.com/test", "test-state")
        flow.code_verifier = "test-verifier"
        flow.credentials = self.creds
        return flow

    def test_oauth_binds_browser_state_and_reconnects_original_data(self):
        flow = self.fake_flow()
        with patch("app.gmail.oauth_service.get_flow", return_value=flow), patch("app.gmail.oauth_service.build") as build:
            build.return_value.users.return_value.getProfile.return_value.execute.return_value = {"emailAddress": "SRCaetite@gmail.com"}
            self.client.post("/api/auth/logout")
            self.assertEqual(self.client.post("/api/auth/login").status_code, 200)
            flow.authorization_url.assert_called_once_with(access_type="offline", include_granted_scopes="true", prompt="consent select_account")
            response = self.client.get("/api/auth/callback?code=fake&state=test-state", follow_redirects=False)
            self.assertIn("account_id=1", response.headers["location"])
            self.assertEqual(flow.code_verifier, "test-verifier")
            self.assertEqual(self.client.get("/api/emails/history").json()["total"], 1)
            response = self.client.get("/api/auth/callback?code=fake&state=test-state", follow_redirects=False)
            self.assertIn("error=", response.headers["location"])
            flow.fetch_token.assert_called_once()
        with self.sessions() as db:
            account = db.get(Account, 1)
            self.assertNotIn("fake-refresh", account.credentials_encrypted)
            self.assertEqual(json.loads(credential_cipher().decrypt(account.credentials_encrypted.encode()))["refresh_token"], "fake-refresh")

    def test_oauth_wrong_browser_expired_and_cancelled_are_rejected(self):
        flow = self.fake_flow()
        with patch("app.gmail.oauth_service.get_flow", return_value=flow):
            self.client.post("/api/auth/login")
            self.client.cookies.clear()
            response = self.client.get("/api/auth/callback?code=fake&state=test-state", follow_redirects=False)
            self.assertIn("error=", response.headers["location"])
            self.client.cookies.set(COOKIE_NAME, "test-session", path="/api")
            response = self.client.get("/api/auth/callback?error=access_denied&state=test-state", follow_redirects=False)
            self.assertIn("error=", response.headers["location"])
            self.client.post("/api/auth/login")
            with self.sessions() as db:
                db.get(OAuthAttempt, digest("test-state")).expires_at = 0
                db.commit()
            response = self.client.get("/api/auth/callback?code=fake&state=test-state", follow_redirects=False)
            self.assertIn("error=", response.headers["location"])
            flow.fetch_token.assert_not_called()

    def test_new_login_cookie_is_http_only(self):
        self.client.cookies.clear()
        with patch("app.gmail.oauth_service.get_flow", return_value=self.fake_flow()):
            response = self.client.post("/api/auth/login")
        self.assertEqual(response.status_code, 200)
        cookie = response.headers["set-cookie"]
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=lax", cookie)


if __name__ == "__main__":
    unittest.main()
