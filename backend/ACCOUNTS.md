# Multiple Gmail accounts

Each Gmail account owns its emails, attachment references, templates, placeholders,
settings and credentials. Every data request requires an HttpOnly browser-session
cookie and an explicit `X-Account-ID`; the server verifies that the browser has
authenticated that account. The selected account is kept per tab, not globally.

## Existing installation

Migration `b4a81e220001` assigns every existing email, template and settings row to
`srcaetite@gmail.com`, as confirmed by the owner. Attachments and placeholders
retain their original parent IDs and files are not moved or deleted.

After upgrading, log in again as `srcaetite@gmail.com` to access the existing data.
The old global `secrets/token.json` is preserved but is no longer read by the app.
Identity is obtained from Gmail's authenticated profile, never from a submitted
email address.

Use **Add / reconnect account** to authorize another Gmail. The account selector
changes the sender and the entire workspace. New accounts start with no emails or
templates and independent default settings. Switching reloads the page after
confirmation, discarding unsaved edits.

**Disconnect account** removes its locally stored credentials and browser access
on all browsers, but keeps all saved data. Reauthorizing the same Gmail restores
access. It does not revoke the app's authorization in Google's account settings.

If popups are blocked or inconvenient, use **Continue login in this tab**.

## Security and persistence

- Google credentials are encrypted in the database with a Fernet key stored in
  `backend/secrets/account-token.key` (mode 0600).
- Preserve the key with the database. Losing it requires restoring the key or
  reauthorizing accounts; never commit it or a data backup.
- Browser sessions expire after 30 days; login attempts expire after 10 minutes.
- OAuth state and PKCE are bound to the initiating browser and consumed once.
- Mutations require the configured frontend Origin; all API responses use no-store.
- JSON sends cannot reference arbitrary server attachment paths; uploaded files
  use account-specific directories and unique filenames.
- This remains a local-first application, not a public multi-tenant hosting setup.
  HTTPS, deployment hardening and operational limits are needed before exposing it.

`FRONTEND_ORIGIN` defaults to `http://localhost:5173`.
`ACCOUNT_TOKEN_KEY_FILE` defaults to a file beside the legacy token.
The frontend supports `VITE_API_BASE`, defaulting to `http://localhost:8000`.

The OAuth chooser uses Google's documented
[web-server OAuth flow](https://developers.google.com/identity/protocols/oauth2/web-server).

## Safe upgrades

From the repository root:

```sh
docker compose stop backend
backend/.venv/bin/python backend/scripts/backup_local_data.py
# Substitute the exact directory printed by the backup command:
backend/.venv/bin/python backend/scripts/rehearse_account_migration.py BACKUP_DIRECTORY
docker compose up -d --build
backend/.venv/bin/python backend/scripts/verify_account_migration.py BACKUP_DIRECTORY
```

Backups under `backend/data/backups/` contain a consistent SQLite snapshot plus
an archive of storage, secrets and the backend environment file if present.
Verification compares every pre-existing row and file, checks SQLite integrity
and foreign keys, and confirms original ownership. Run it immediately after
upgrading, before new app activity changes the data.

Do not use `docker compose down -v` or delete the bind-mounted data folders.
A downgrade intentionally refuses to discard ownership: rollback requires stopping
the backend and restoring the matching pre-upgrade code, database and files from
backup. Back up newer data separately first; restoring a snapshot loses changes
made after that snapshot.

## Tests

From `backend/`:

```sh
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/python -m unittest discover -s tests -v
```

Tests use temporary databases and mocked Gmail calls; they do not send real email.
The optional browser fixture is started with
`.venv/bin/python -m tests.serve_browser_fixture` on port 8001; start Vite on
127.0.0.1:5174 with `VITE_API_BASE=http://127.0.0.1:8001`.
This fixture never runs in the production Docker image.
