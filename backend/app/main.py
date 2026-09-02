from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.settings import router as settings_router
from app.api.templates import router as templates_router
from app.api.emails import router as emails_router
from app.api.auth import router as auth_router
from app.api.gmail import router as gmail_router
from app.services.account_service import frontend_origin

app = FastAPI(
    title="Mail Orchestrator API",
    version="0.1.0",
    description="Local-first email composer and sent mail tracker powered by Gmail.",
)

app.include_router(settings_router)
app.include_router(templates_router)
app.include_router(emails_router)
app.include_router(auth_router)
app.include_router(gmail_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def prevent_private_data_caching(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.head("/api/health")
def health_head():
    return None
