# Backend

Python 3.12+ REST API using FastAPI, SQLAlchemy, SQLite, Alembic and Gmail API.
Each authenticated Gmail owns its emails, templates and settings.

## Development

Follow [the setup guide](../SETUP.md) for Google credentials and the virtual
environment. From `backend/`, with the environment active:

```sh
python -m pip install -e '.[test]'
# Back up an existing installation before applying migrations:
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

The development server does not apply migrations itself.
[Swagger](http://localhost:8000/docs), [OpenAPI](http://localhost:8000/openapi.json)
and [health](http://localhost:8000/api/health) are available locally.

## Authentication and ownership

OAuth begins from the frontend, not a standalone copied URL. Login binds state
and PKCE to an HttpOnly browser session; the callback obtains the Gmail address
from the authenticated profile and stores encrypted credentials for that account.

All data routes use `get_account_db`: a valid browser session and an authorized
`X-Account-ID` are mandatory. Mutations also require the configured frontend
Origin. `GET /api/auth/status` lists accounts available to that browser, not all
accounts in the database. Logout disconnects the selected account on all browsers
while preserving its data.

Use [the API overview](../README.md#api) for routes. Header requirements are not
automatically exposed as Swagger's Authorize control.

## Tests

```sh
python -m unittest discover -s tests -v
```

Tests cover account access, resource ownership, uploads, mocked OAuth/Gmail and
legacy migration preservation. They create temporary databases and do not send
real email.

## Persistence and operations

Docker uses bind mounts for `data/`, `secrets/` and `storage/`. Credentials are
encrypted in SQLite; `secrets/account-token.key` is needed to decrypt them.
Message bodies and uploaded files are not encrypted by the app.

- [Accounts, backup, migration and rollback](ACCOUNTS.md)
- [Developer guide and code navigation](GUIDE.md)
- [Configuration example](.env.example)
- [Known limitations](../TECHNICAL_DEBT.md)

Do not run the test browser fixture against production data or expose the default
local setup as a public service.
