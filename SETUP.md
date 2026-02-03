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