from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.settings import router as settings_router
from app.api.templates import router as templates_router
from app.api.emails import router as emails_router

app = FastAPI(
    title="Mail Orchestrator API",
    version="0.1.0",
    description="Local-first email composer and sent mail tracker powered by Gmail.",
)

app.include_router(settings_router)
app.include_router(templates_router)
app.include_router(emails_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.head("/api/health")
def health_head():
    return None
