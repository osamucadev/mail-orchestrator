# Setup guide

## Prerequisites

- Git.
- Docker Engine/Desktop with the Compose plugin for the container workflow.
- For development or the host-side migration helpers: Python 3.12+ and a virtual
  environment. Node.js 18+ and npm are needed for frontend development.
- A Google Cloud project with Gmail API enabled and a Web application OAuth client.

There is no `scripts/setup.py` or `requirements.txt`. Dependencies are defined in
`backend/pyproject.toml` and the root/frontend `package.json` files.

## 1. Clone and configure Gmail

```sh
git clone https://github.com/osamucadev/mail-orchestrator
cd mail-orchestrator
```

In [Google Cloud Console](https://console.cloud.google.com/), enable the Gmail API
and configure the OAuth application's audience and consent. Create a **Web
application** client with the exact authorized redirect URI:

```text
http://localhost:8000/api/auth/callback
```

The application requests `gmail.send` and `gmail.readonly`. If the OAuth project
is in testing mode, add each Gmail you intend to connect as a test user. Follow
[Google's OAuth guide](https://developers.google.com/identity/protocols/oauth2/web-server)
for current console and authorization requirements.

Save the downloaded JSON as `backend/secrets/credentials.json`.
Use [credentials-example.jsonc](backend/secrets/credentials-example.jsonc) only as
an annotated reference; runtime credentials must be valid JSON without comments.
Do not overwrite an existing working credentials file.

## 2A. Run with Docker

From the repository root:

```sh
docker compose up -d --build --wait
docker compose ps
```

Open [the app](http://localhost:5173). Docker runs migrations automatically.
State stays in `backend/data/`, `backend/secrets/` and `backend/storage/`.

For an existing database, read [the backup/migration guide](backend/ACCOUNTS.md)
before starting a newer image. Docker uses its Compose environment, not the
host's `backend/.env`. Local Python/Node dependencies are not needed just to
run the containers.

The default mappings expose ports 8000 and 5173 on host interfaces. Keep this a
trusted local installation; public hosting needs additional hardening.

## 2B. Run in development

Stop the Docker services first if they use the same ports/data:

```sh
docker compose stop
```

### Python environment

From the repository root, on Linux/macOS:

```sh
python3 -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install -e './backend[test]'
```

On Windows PowerShell:

```powershell
py -3 -m venv backend/.venv
.\backend\.venv\Scripts\Activate.ps1
python -m pip install -e "./backend[test]"
```

Use a Python installation meeting the required version. Activation must be
repeated in each terminal running the backend.

For a new development installation, copy `backend/.env.example` to
`backend/.env` without overwriting an existing configuration. Keep both Gmail
scope URLs on a single line. Relative backend paths are resolved from `backend/`.

Install JavaScript dependencies from the repository root:

```sh
npm ci
npm --prefix frontend ci
```

For a new database, apply the schema before starting the dev server:

```sh
cd backend
python -m alembic upgrade head
cd ..
npm run dev
```

For an existing database, back up first. The combined runner starts both servers
and opens the browser. It does **not** run Alembic automatically.

On Windows, separate terminals avoid the known reload issue. From the repository
root, use `npm run dev:backend` in an activated Python environment and
`npm run dev:frontend` in the other terminal. See [known limitations](TECHNICAL_DEBT.md).

## 3. Connect accounts

1. Open [http://localhost:5173](http://localhost:5173).
2. Click **Open Gmail Login** and authorize Gmail.
3. If the popup is inconvenient, use **Continue login in this tab**.
4. Use **Add / reconnect account** for each additional Gmail.
5. Use **Gmail / sender** to switch the entire workspace.

The first migration assigns old data to `srcaetite@gmail.com`; that account must
authenticate again to see it. New accounts start empty. Disconnecting retains
data but removes that account's app connection across browsers.

## Build and test

From the repository root:

```sh
npm --prefix frontend run build
```

From `backend/`, with the virtual environment active:

```sh
python -m unittest discover -s tests -v
```

The tests use temporary databases and simulated Gmail calls.

## Operations and troubleshooting

- **Port already in use:** do not run Docker and development servers together.
  Changing ports also requires matching the frontend API URL, backend
  `FRONTEND_ORIGIN`, callback URI and Google client configuration.
- **Popup blocked/cancelled:** use the same-tab link or start a fresh login.
  OAuth attempts expire after 10 minutes and cannot be replayed.
- **Account missing or data appears empty:** check the selected Gmail. On a new
  browser or after session expiry, authorize the account again. The legacy
  `token.json` does not restore a browser session.
- **Gmail authorization expired:** reconnect that account; do not delete the DB.
- **403 on a manual API call:** check session membership, `X-Account-ID` and,
  for mutations, Origin. CORS configuration is not an authentication substitute.
- **Encryption key lost:** restore the matching key from a protected backup;
  do not delete data or replace the key expecting existing ciphertext to decrypt.
- **Database/schema error:** stop and back up the backend before applying
  migrations; never reset/delete the database as a shortcut.
- **Virtual environment activation on Windows:** use the environment's Python
  executable directly if activation is unavailable; do not weaken system policy
  merely to run the app.

Use `docker compose logs --tail=100 backend` to investigate container startup
and `docker compose ps` for health. Avoid sharing unredacted logs or secrets.

For backups and rollback, see [ACCOUNTS.md](backend/ACCOUNTS.md).
