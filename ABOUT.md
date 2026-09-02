# Mail Orchestrator: product and architecture

Mail Orchestrator is a local-first Gmail composer and sent-mail tracker.
Its purpose is to help with outreach and follow-up: know what was sent, which
messages received replies and when to act again.

This document describes the implemented design. For commands, use
[SETUP.md](SETUP.md); for the engineering narrative, see [JOURNEY.md](JOURNEY.md).

## Product scope

The application supports multiple Gmail accounts within one local installation.
Every Gmail has its own history, attachments, templates, placeholders and
settings. It is not a public hosting platform or a separate organization/user
management system.

The frontend is vanilla JavaScript/HTML/SCSS with Vite. The backend is Python with
FastAPI, Pydantic and SQLAlchemy. SQLite stores local state; Alembic evolves the
schema. Docker optionally serves the frontend through Nginx and runs the API
with the same persistent host directories.

## Account ownership is part of the model

- `accounts` identifies a Gmail address and stores encrypted Google credentials.
- `emails`, `templates` and `settings` have an `account_id`.
- Attachments inherit ownership from their email; placeholders from their template.
- Settings have a unique owner, rather than a global fixed row with ID 1.
- Browser sessions are associated only with accounts authorized in that browser.
- OAuth attempts store browser-bound state, an encrypted PKCE verifier and expiry.

The account selected in the UI is stored per tab. Every API data request identifies
it explicitly, and the backend validates session membership before running scoped
queries. Sending and checking replies use that account's Gmail credentials.

Switching accounts reloads the workspace after confirmation. Unsaved changes are
discarded. Disconnecting clears the account's local credentials and browser
associations without deleting saved data. Reconnecting restores access to the
same account's records.

## OAuth design

The project uses the Google **Web application** authorization-code flow, not an
installed-app client. The default callback is
`http://localhost:8000/api/auth/callback`.

The backend obtains the address from Gmail's authenticated profile, not a text
field provided by the browser. Credentials are encrypted in SQLite using the
Fernet key at `backend/secrets/account-token.key`. Only a random session identifier
is sent in the HttpOnly cookie; the browser does not store Google tokens.

OAuth state/PKCE are checked against the initiating browser and consumed once.
The frontend supports both popup and same-tab continuation. See
[account lifecycle and migration](backend/ACCOUNTS.md).

## Compose, templates and MIME

The composer has a visual Editor and Preview. Plain text is derived for sending
alongside HTML. Rich text conversion is intentionally practical rather than a
lossless round-trip editor.

The backend detects ordered unique placeholder keys with
`\{\{\s*([a-zA-Z0-9_]+)\s*\}\}`. The frontend builds the fields and substitutes
their values before sending. Templates and their fields are account-specific.

Files are uploaded, not referenced by arbitrary server paths. New files use
account-specific directories with unique names. Inline images are displayed as
data URLs in the browser and sent with MIME Content-ID references.

The MIME builder creates a text body, optional HTML alternative, related inline
parts and regular attachments. Gmail sending uses `messages.send`; the local
record stores the returned message and thread IDs.

## History and replies

History shows recipient, subject, sent time, send count and response state.
It is paginated and can be sorted newest/oldest first.

Time-based statuses use the active account's thresholds. A response, detected
through Gmail or marked manually, takes precedence and displays 🟢.

A reply check fetches the saved thread and looks for a newer message from another
sender. Resending updates the original local record and its latest Gmail IDs,
rather than adding a separate send-event row. Tracking older resend threads is
still a limitation.

Deleting a local history entry removes its database attachment records but does
not delete the Gmail message or clean the physical upload files automatically.

## Preserving existing data

The account migration assigns original records to `srcaetite@gmail.com`, as
explicitly confirmed by the owner. Relationships and file paths are preserved.
The old global token is retained on disk but not used for authorization.

The migration is preceded by backup and can be rehearsed against a temporary
copy. The verification helper compares pre-existing rows and file contents.
See [backup scope and rollback precautions](backend/ACCOUNTS.md).

## Boundaries and next steps

Account isolation protects application-level access; it is not full encryption
of the mailbox database. Email bodies and attachments remain ordinary local data.
Public hosting would require additional network, HTTPS, abuse-control and
operational work.

Future features include follow-up chains, scheduling, richer resend history and
importing sent messages. Multi-account support and persistent Docker deployment
are already implemented.

See the [API overview](README.md#api), [developer guide](backend/GUIDE.md) and
[known limitations](TECHNICAL_DEBT.md) for details.
