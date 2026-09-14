import logging

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import Base, engine
from app.deps import limiter
from app.routers import auth, contacts, emergency, location, safety, whatsapp

logging.basicConfig(level=logging.INFO)

# Creates tables if they don't exist yet (fine for SQLite prototyping;
# use Alembic migrations for PostgreSQL in production).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="Consent-based GPS safety & family location alert system.",
    version="1.0.0",
)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Too many requests. Please slow down and try again shortly."})


app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "http://127.0.0.1:5500", "http://localhost:5500", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(contacts.router)
app.include_router(location.router)
app.include_router(safety.router)
app.include_router(emergency.router)
app.include_router(whatsapp.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}


# Mount frontend static files if available
for candidate_dir in [
    Path(__file__).resolve().parent.parent.parent / "frontend",
    Path(__file__).resolve().parent.parent / "frontend",
    Path("/app/frontend"),
]:
    if candidate_dir.exists() and (candidate_dir / "index.html").exists():
        app.mount("/", StaticFiles(directory=str(candidate_dir), html=True), name="frontend")
        break
