# Backend

FastAPI REST API for Mail Orchestrator.

Run locally:

python -m venv .venv
. .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --port 8000

Swagger:
- http://localhost:8000/docs
