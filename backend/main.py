"""
Adaptive (Java) — FastAPI application.

    cd backend && uvicorn main:app --reload --port 8000

Deliberately small. All behaviour lives in core/ and builders/; this file wires
routers, configures logging, and initialises the database.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core import auth, store
from core.docs_loader import docs_loader
from core.logging_setup import configure_logging, get_logger
from routers import health, runs

logger = get_logger("adaptive.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await store.init_db()

    # Load docs at startup and SAY what happened. AUX loads silently, so an
    # empty bundle only shows up as subtly worse generated code much later.
    docs_loader.load()
    diag = docs_loader.diagnose()
    if diag["ungrounded"]:
        logger.warning("Ungrounded docs bundles: %s", ", ".join(diag["ungrounded"]))
    else:
        logger.info("Docs grounded: %d bundles", len(diag["bundles"]))

    if not auth.is_enforced():
        logger.warning(
            "ADAPTIVE_API_TOKEN is not set - approve and deploy are UNAUTHENTICATED.")

    logger.info("Adaptive backend ready")
    yield


app = FastAPI(
    title="Adaptive (Java)",
    description="Step-gated generation of QAD Adaptive artifacts.",
    version="0.1.0",
    lifespan=lifespan,
)

# Local dev only. Tighten before this is reachable from anywhere but localhost —
# and note that CORS is not a substitute for the auth on the mutating routes.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(runs.router)


@app.get("/")
async def root():
    return {
        "app": "Adaptive (Java)",
        "docs": "/docs",
        "health": "/api/health",
        "stages": "/api/run/stages",
    }
