"""Main FastAPI application entry point"""

from src.routes import documents, simplification, analysis
from datetime import datetime
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from src.middleware import RequestLoggingMiddleware, limiter
from sqlalchemy.orm import Session
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from src.settings import settings
from src.database import get_db, engine, Base
from datetime import datetime
from src.schemas.document import HealthResponse

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description="Backend API for legal document simplification and analysis.",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(RequestLoggingMiddleware)
# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],  # Restrict origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

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
        # Test database connection
        from sqlalchemy import text
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
    return {
        "app_name": settings.app_name,
        "environment": settings.environment,
        "debug": settings.debug,
        "database_url": settings.database_url.replace(
            settings.database_url.split("@"),
            "postgresql://***:***",
        ),
    }

app.include_router(documents.router)
app.include_router(simplification.router)
app.include_router(analysis.router)


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print(f" Starting {settings.app_name}")
    print(f" Environment: {settings.environment}")
    print(f" Database: {settings.database_url.split('@')}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print(f" Shutting down {settings.app_name}")
