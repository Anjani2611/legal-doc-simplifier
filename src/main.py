"""Main FastAPI application entry point"""

import logging
import time
from collections import Counter
from datetime import datetime

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from src.logging_config import setup_logging
from src.database import Base, engine, get_db
from src.logging_config import setup_logging
from src.middleware import RequestLoggingMiddleware, limiter
from src.routes import analysis, documents, simplification
from src.schemas.document import HealthResponse
from src.settings import settings
from src.webhooks import webhook_manager
from src.metrics import api_requests  # Prometheus Counter
from src.api.v1 import v1_router
from src.api.v2 import v2_router


# ---- Logging setup ----
setup_logging()
logger = logging.getLogger("app")

# ---- DB setup ----
Base.metadata.create_all(bind=engine)

# ---- FastAPI app ----
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description="Backend API for legal document simplification and analysis.",
)

# ---- Rate limiting + logging middleware ----
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# ---- CORS ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# ---- Optional in-memory metrics ----
metrics = Counter()


@app.middleware("http")
async def metrics_and_logging(request: Request, call_next):
    """Collect Prometheus + basic metrics and log each request."""
    metrics["requests_total"] += 1
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    metrics["latency_sum_ms"] += duration_ms

    api_requests.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code,
    ).inc()

    logger.info(
        f"{request.method} {request.url.path} "
        f"status={response.status_code} duration_ms={duration_ms:.2f}"
    )
    return response


@app.get("/metrics/basic", tags=["metrics"])
async def basic_metrics():
    """Return simple in-memory metrics for requests."""
    total = metrics.get("requests_total", 0)
    latency_sum = metrics.get("latency_sum_ms", 0.0)
    avg_latency = latency_sum / total if total else 0.0
    return {
        "requests_total": total,
        "avg_latency_ms": round(avg_latency, 2),
    }


@app.get("/metrics", tags=["metrics"])
async def metrics_endpoint():
    """Prometheus-compatible metrics endpoint."""
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@app.post("/webhooks/register", tags=["webhooks"])
async def register_webhook(event: str, url: str):
    """Register a webhook for document events."""
    if event not in webhook_manager.webhooks:
        webhook_manager.webhooks[event] = []
    webhook_manager.webhooks[event].append(url)
    return {"status": "registered", "event": event}


@app.get("/", tags=["root"])
async def read_root():
    """Root endpoint - returns API info"""
    return {
        "message": f"{settings.app_name} is running",
        "environment": settings.environment,
        "docs": "/docs",
    }


@app.get("/health", tags=["health"], response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check including database"""
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        database=db_status,
        timestamp=datetime.utcnow(),
    )


@app.get("/config", tags=["debug"])
async def get_config():
    """Get current config (debug endpoint - remove in production)"""
    if not settings.debug:
        return {"error": "Not available in production"}

    masked_db_url = settings.database_url
    if "@" in masked_db_url:
        _user_part, rest = masked_db_url.split("@", 1)
        masked_db_url = "postgresql://***:***@" + rest

    return {
        "app_name": settings.app_name,
        "environment": settings.environment,
        "debug": settings.debug,
        "database_url": masked_db_url,
    }


# ---- Legacy routers (if you still want non-versioned paths) ----
app.include_router(documents.router)
app.include_router(simplification.router)
app.include_router(analysis.router)

# ---- Versioned routers ----
app.include_router(v1_router)
app.include_router(v2_router)


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info(f"Starting {settings.app_name}")
    logger.info(f"Environment: {settings.environment}")
    logger.info("Database configured")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info(f"Shutting down {settings.app_name}")
