# Backend developer guide

The backend is a FastAPI REST API with SQLite/SQLAlchemy persistence, Alembic
migrations and Gmail integration. The most important invariant is account
ownership: an authenticated browser may act only on an account authorized in
that session, and only on that account's records.

Start with [setup](../SETUP.md), [the API contract](../README.md#api) and
[account operations](ACCOUNTS.md).

## Code map

```text
backend/
  app/
    main.py                       FastAPI, routers, CORS, no-store, health
    api/                          auth, gmail, emails, templates, settings
    core/config.py                Database and OAuth environment settings
    core/time_utils.py            Relative time and emoji thresholds
    db/base.py                    Declarative Base
    db/session.py                 Engine and SessionLocal
    db/deps.py                    get_db request lifecycle
    models/account.py             Account, BrowserSession, SessionAccount, OAuthAttempt
    models/                       Email, attachment, template, placeholder, settings
    schemas/                      Pydantic request/response contracts
    services/account_service.py   Browser session, Origin, ownership, encryption key
    services/email_service.py     Scoped history, creation, resend, reply checks, deletion
    services/template_service.py  Scoped CRUD and placeholder detection
    services/settings_service.py  Per-account settings/defaults
    gmail/oauth_service.py        Browser-bound OAuth and account connection
    gmail/credentials_provider.py Decrypt/refresh selected account credentials
    gmail/gmail_client.py         Build selected account's Gmail client
    gmail/gmail_sender.py         Encode MIME and call messages.send
    gmail/mime_builder.py         Build EmailMessage with attachments/inline parts
    gmail/reply_detector.py       Fetch thread and detect newer incoming messages
    gmail/token_store.py          Legacy file helpers, unused by active auth flow
  alembic/versions/               Versioned schema migrations
  scripts/                       Backup, legacy rehearsal and verification helpers
  tests/                         Isolation/migration tests and optional browser fixture
  pyproject.toml                 Runtime dependencies and optional test dependencies
```

## Request authorization

`get_db()` opens/closes a SQLAlchemy session; it does not authenticate anyone.
Use `Depends(get_account_db)` on protected data routes.

`get_account_db` performs these checks:

1. For mutations, require Origin to match `FRONTEND_ORIGIN`.
2. Hash the `mo_session` cookie and find an unexpired browser session.
3. Require a valid integer `X-Account-ID`.
4. Check `session_accounts` membership and connected account credentials.
5. Set `db.info["account_id"]` for that request.

Services retrieve the selected ID through `account_id(db)`, which fails closed
if no authorized account is bound. Do not use a module-level active-account
variable or trust a client-supplied email address.

Protected lookups must include both record ID and owner:

```python
email = db.scalar(
    select(Email).where(
        Email.id == email_id,
        Email.account_id == account_id(db),
    )
)
```

An unscoped `db.get(Email, email_id)` would allow cross-account access.
Counts, pagination, updates and deletes must use the same ownership filter.
Dependent rows are accessed only after authorization of their parent.

Authentication metadata routes use `get_db` deliberately: status lists only the
current session's accounts; login establishes a session; the callback validates
the pending browser-bound authorization before linking an account.

## OAuth and credential lifecycle

1. The frontend starts `POST /api/auth/login` with credentials included.
2. The backend validates Origin and creates/reuses an HttpOnly browser session.
3. `get_login_url(db, session)` asks for offline consent and account selection.
   The state hash, encrypted PKCE verifier and expiry are stored in SQLite.
4. Google returns to the callback. The backend verifies the browser, expiry and
   state, consumes the attempt once, and exchanges the code with PKCE.
5. Gmail's authenticated profile supplies the normalized email address.
6. The account is created or reused; credentials are encrypted and session
   membership is added. An existing refresh token is preserved if needed.
7. The frontend receives the account ID in its callback fragment. Popup results
   are checked against source/origin and server status; same-tab login reloads
   the normal application.
8. Subsequent Gmail calls use `get_gmail_service(db)`, which delegates to
   `get_valid_credentials(db)` to decrypt and refresh only the selected account.

Browser sessions expire after 30 days; pending attempts after 10 minutes. Status
means a local connection exists, not that a fresh Google API call has succeeded.
A revoked/expired Google authorization may require reconnection.

`POST /api/auth/logout` clears the selected account's credentials and all of its
session associations. It retains email/template/settings data and does not
revoke the grant remotely at Google.

The encryption key is separate from the database. See [configuration and key
backup](ACCOUNTS.md#security-and-persistence). The old `token.json` is not read by
the current credential provider.

## Persistence model

`Account` has a unique email and nullable encrypted credential payload.
`BrowserSession` stores only a hashed session identifier plus expiry.
`SessionAccount` is the membership relation.
`OAuthAttempt` binds a one-time attempt to the browser session.

`Email` includes owner, recipient, subject, body variants, Gmail IDs, timestamps,
send count and response state. Attachments store local paths and MIME metadata
under their email. `Template` owns its detected placeholder rows. `Settings`
has a unique `account_id`, not a fixed global ID.

Lazy-created settings currently default to 1140, 4320, 7200 and 10080 minutes.
Migrated settings retain their original values.

## Sending and uploads

`POST /api/emails/send` accepts JSON for messages without attachments.
Although the schema retains attachment metadata fields, this route rejects a
nonempty attachment list. Use `/send-multipart` for actual files.

Multipart fields include `to`, `subject`, `body_text`, `body_html`,
`inline_meta`, `inline_images` and `attachments`.
Uploads are saved under `storage/uploads/<account_id>/` with unique filenames;
legacy paths remain valid. Inline metadata supplies Content-ID mappings.

The route obtains the authorized Gmail client and calls
`send_email_via_gmail`. `mime_builder.py` returns a Python `EmailMessage` with
text/HTML alternatives, related inline images and regular attachments.
The sender encodes the message as URL-safe base64 and calls Gmail.

Only after a successful Gmail response does `create_email` persist local history
and attachment records. Gmail delivery and database commits are not an atomic
transaction; see [known limitations](../TECHNICAL_DEBT.md).

`EmailSendResponse` contains `id`, `sent_at` and `send_count`, not the complete
message. Review `app/schemas/email.py` before changing the HTTP contract.

## History, resend and reply checks

`list_history(db, limit, offset, sort)` scopes both the count and returned rows,
then calculates relative time and emoji using the same account's settings.
Replied items show 🟢; other statuses use the configured minute bounds.

`resend_email(db, email_id)` first authorizes ownership. It sends the original
content/attachments, increments send count and updates the same row's sent time,
Gmail IDs and response state.

`check_reply(db, email_id)` authorizes the record before using Gmail. The detector
returns a `ReplyCheckResult` dataclass with `replied`, `replied_at` and `reason`.
It fetches the selected Gmail's profile and stored thread, looking for messages
newer than the send from another sender. The service updates local response state.

Deleting history removes email and child attachment rows; physical upload cleanup
and Gmail message deletion are not implemented by that route.

## Templates and settings

Template CRUD scopes queries by account. Placeholder detection collects unique
keys matching `{{key}}` in first-appearance order across subject/text/HTML.
Updating a template recreates its detected fields.

Substitution and dynamic fields belong to the frontend composer, not the backend
send service. Settings are fetched/created and updated for the authorized account.

## Configuration, Docker and migrations

See [the configuration table](../README.md#configuration) and [.env.example](.env.example).
Run backend development commands from `backend/` so relative data/storage paths
resolve correctly.

Docker mounts the host database, secrets and storage directories and runs
`alembic upgrade head` before Uvicorn. Development Uvicorn does not run migrations.
Do not start both backends against the same database.

Migration `b4a81e220001` assigns legacy records to `srcaetite@gmail.com` without
changing existing IDs or file paths. Its downgrade intentionally fails rather
than remove account ownership. [ACCOUNTS.md](ACCOUNTS.md) explains backups,
one-time legacy rehearsal and restoring a matching snapshot/code version.

Do not assume every migration is safely reversible or that the SQLite schema
change is covered by one transactional rollback.

## Tests and development checklist

From `backend/` with its virtual environment active:

```sh
python -m pip install -e '.[test]'
python -m unittest discover -s tests -v
```

- `test_accounts.py`: session/membership, per-account CRUD/history/settings,
  rejected foreign IDs, upload namespacing, credential selection and mocked OAuth.
- `test_account_migration.py`: legacy rows/relationships survive the migration,
  restart is idempotent, and integrity/foreign-key checks pass.
- `serve_browser_fixture.py`: explicitly started disposable UI-test backend,
  with simulated OAuth and sending disabled. Not imported by production.

Before adding a feature:

1. Trace its route, authorization dependency, service and model.
2. Scope every query and parent lookup; test both owning and foreign accounts.
3. Mock Gmail calls. Do not send real mail as part of automated tests.
4. Add a migration when persistence changes, and test existing-data preservation.
5. Update schemas, frontend callers and documentation together.
6. Back up before applying changes to the user's installation.

## Learning path

Use this repository to study HTTP/dependency injection, Pydantic validation,
SQLAlchemy relationships/transactions, migrations, OAuth state/PKCE, MIME and
test isolation. Trace sending first, then a cross-account 404 and a reconnect.

Suggested code-reading order: `main.py` → `account_service.py` →
`api/emails.py` → `email_service.py` → Gmail helpers → models/schemas →
migration tests. The application is local-first; production readiness requires
additional hardening, not only a successful build.
