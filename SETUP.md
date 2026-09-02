# Setup Guide

## Prerequisites
- Python 3.12+
- Node 18+
- Git

## Quick Start (All platforms)

### Windows (PowerShell)
```powershell
# 1. Clone and enter directory
git clone https://github.com/osamucadev/mail-orchestrator
cd mail-orchestrator

# 2. Run setup script
python scripts/setup.py
```

### macOS/Linux (Bash)
```bash
git clone https://github.com/osamucadev/mail-orchestrator
cd mail-orchestrator
python scripts/setup.py
```

## Manual Setup (if script fails)

### Backend
```bash
cd backend
python -m venv .venv

# Activate venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
```

### Frontend
```bash
npm install
```

### Google OAuth Setup
1. Go to https://console.cloud.google.com
2. Create new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Web application)
5. Add redirect: `http://localhost:8000/api/auth/callback`
6. Download credentials as JSON
7. Save to `backend/secrets/credentials.json`

### Run
```bash
npm run dev
```

Visit http://localhost:5173

## Docker (persistent local data)

The Compose setup runs the backend and frontend in separate containers and
keeps local state on the host:

- SQLite database: `backend/data/mail_orchestrator.db`
- Gmail OAuth credentials and token: `backend/secrets/`
- Uploaded attachments: `backend/storage/`

Start in the background:

```bash
docker compose up -d --build
```

Open http://localhost:5173. Both services use `restart: unless-stopped`, so
they restart with the Docker daemon unless they were stopped manually.

Useful commands:

```bash
docker compose ps
docker compose logs -f
docker compose restart
docker compose stop
docker compose start
docker compose down
```

`docker compose down` does not delete the persisted database, secrets, or
attachments because they are bind-mounted from the paths above.

---

## Troubleshooting

### venv not activating
- Windows: Use PowerShell or cmd.exe
- macOS/Linux: Use `source .venv/bin/activate`

### Database errors
```bash
cd backend
alembic upgrade head
```

### Port already in use
- Change port in `scripts/dev.mjs` or kill process using port 5173/8000
