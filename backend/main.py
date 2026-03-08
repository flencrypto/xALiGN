"""
aLiGN – FastAPI application entry point.

Starts the API server, registers middleware, mounts all routers,
and initialises the database schema on first run.
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from backend.database import Base, engine
from backend.migrations import run_migrations
from backend.routers.accounts import contacts_router, router as accounts_router
from backend.routers.accounts import signals_router
from backend.routers.bids import router as bids_router
from backend.routers.blog import router as blog_router
from backend.routers.csv_import_export import router as csv_router
from backend.routers.debriefs import router as debriefs_router
from backend.routers.estimating import router as estimating_router
from backend.routers.exports import router as exports_router
from backend.routers.frameworks import router as frameworks_router
from backend.routers.intel import router as intel_router
from backend.routers.intelligence import router as intelligence_router
from backend.routers.leadtime import router as leadtime_router
from backend.routers.opportunities import router as opportunities_router
from backend.routers.swoop import router as swoop_router
from backend.routers.tender import router as tender_router
from backend.routers.uploads import router as uploads_router
from backend.routers.calls import router as calls_router
from backend.routers.crm import router as crm_router
from backend.routers.processing import router as processing_router
from backend.routers.agents import router as agents_router
from backend.routers.projects import router as projects_router
from backend.routers.setup import router as setup_router
from backend.routers.webhooks import router as webhooks_router
from backend.seed_data import run_seed
from backend.core.config import settings
from backend.services.scheduler import setup_scheduler

# Import all models so SQLAlchemy metadata is populated before create_all
import backend.models  # noqa: F401

logger = logging.getLogger("align")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all database tables, run schema migrations, and seed initial records on startup."""
    logger.info("aLiGN starting – creating database tables…")
    Base.metadata.create_all(bind=engine)
    run_migrations()
    logger.info("Database ready.")
    run_seed()
    setup_scheduler(app)
    yield
    logger.info("aLiGN shutting down.")


app = FastAPI(
    title="aLiGN API",
    description=(
        "AI-native Bid + Delivery OS for Data Centre Refurbs & New Builds. "
        "Provides account intelligence, opportunity qualification, bid pack "
        "management, and estimating scope gap detection."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────

# Parse the comma-separated CORS_ORIGINS setting so multiple origins are
# supported in production (e.g. "https://app.example.com,https://preview.example.com").
_cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Audit Logging Middleware ───────────────────────────────────────────────────

_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@app.middleware("http")
async def audit_log_middleware(request: Request, call_next) -> Response:
    """Log all write operations with method, path, status code, and duration."""
    start = time.perf_counter()
    response: Response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 1)

    if request.method in _WRITE_METHODS:
        logger.info(
            "AUDIT %s %s → %d (%.1fms) client=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request.client.host if request.client else "unknown",
        )

    return response


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(accounts_router, prefix="/api/v1")
app.include_router(contacts_router, prefix="/api/v1")
app.include_router(signals_router, prefix="/api/v1")
app.include_router(csv_router, prefix="/api/v1")
app.include_router(swoop_router, prefix="/api/v1")
app.include_router(opportunities_router, prefix="/api/v1")
app.include_router(bids_router, prefix="/api/v1")
app.include_router(exports_router, prefix="/api/v1")
app.include_router(debriefs_router, prefix="/api/v1")
app.include_router(estimating_router, prefix="/api/v1")
app.include_router(intel_router, prefix="/api/v1")
app.include_router(blog_router, prefix="/api/v1")
app.include_router(uploads_router, prefix="/api/v1")
app.include_router(tender_router, prefix="/api/v1")
app.include_router(calls_router, prefix="/api/v1")
app.include_router(crm_router, prefix="/api/v1")
app.include_router(leadtime_router, prefix="/api/v1")
app.include_router(frameworks_router, prefix="/api/v1")
app.include_router(intelligence_router, prefix="/api/v1")
app.include_router(agents_router, prefix="/api/v1")
app.include_router(setup_router, prefix="/api/v1")
app.include_router(processing_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(webhooks_router)


# ── Health Check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"], summary="Health check")
def health_check():
    """Return 200 OK when the service is running."""
    return {"status": "ok", "service": "align"}
