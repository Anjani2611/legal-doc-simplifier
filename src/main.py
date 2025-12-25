from fastapi import FastAPI

from src.settings import settings


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
    description="Backend API for legal document simplification and analysis.",
)


@app.get("/", tags=["root"])
async def read_root():
    return {
        "message": "Legal Document Simplifier API is running",
        "environment": settings.environment,
    }


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
