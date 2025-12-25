from fastapi import APIRouter
from src.routes import documents, simplification, analysis

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(documents.router)
v1_router.include_router(simplification.router)
v1_router.include_router(analysis.router)
