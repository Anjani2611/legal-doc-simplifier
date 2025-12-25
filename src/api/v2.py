from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.tasks import simplify_document_async

v2_router = APIRouter(prefix="/api/v2", tags=["v2"])


@v2_router.post("/documents/upload/async")
async def upload_document_async(doc_id: int, db: Session = Depends(get_db)):
    """Queue document for background simplification."""
    # yahan optionally check kar sakte ho ki document exist karta hai
    task = simplify_document_async.delay(doc_id)
    return {
        "task_id": task.id,
        "status": "processing",
        "document_id": doc_id,
    }
