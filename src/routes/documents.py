"""Document-related API endpoints"""

import logging
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session

from src.middleware import limiter
from src.database import get_db
from src.models.document import Document
from src.schemas.document import DocumentCreate  # input schema
from src.config import settings
from src.utils.document_extractor import DocumentExtractor
from src.cache import cache_result
from src.tasks import celery_app
from src.monitoring.metrics import record_document_operation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

# Ensure uploads directory exists
Path(settings.upload_dir).mkdir(exist_ok=True)


def serialize_document(doc: Document) -> dict:
    """Convert SQLAlchemy Document -> plain dict with ISO datetime."""
    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_path": doc.file_path,
        "file_size": doc.file_size,
        "original_text": doc.original_text,
        "document_type": doc.document_type,
        "language": doc.language,
        "processing_status": doc.processing_status,
        "created_at": (
            doc.created_at.isoformat()
            if isinstance(doc.created_at, datetime)
            else None
        ),
    }


@router.get("/")
@limiter.limit("60/minute")          # list soft limit
@cache_result(ttl_seconds=300)
async def list_documents(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """List all uploaded documents."""
    documents = db.query(Document).offset(skip).limit(limit).all()
    total = db.query(Document).count()

    return {
        "total": total,
        "documents": [serialize_document(d) for d in documents],
    }


@router.get("/{document_id}")
@limiter.limit("60/minute")
async def get_document(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific document by ID."""
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return serialize_document(document)


@router.post("/")
@limiter.limit("30/minute")          # metadata create
async def create_document(
    request: Request,
    doc: DocumentCreate,
    db: Session = Depends(get_db),
):
    """Create a new document entry without file upload."""
    db_doc = Document(
        filename=doc.filename,
        file_path=f"/uploads/{doc.filename}",
        file_size=doc.file_size,
        original_text=doc.original_text,
        document_type=doc.document_type,
        language=doc.language,
    )

    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    # Metrics: document create operation
    record_document_operation("create")

    return serialize_document(db_doc)


@router.post("/upload")
@limiter.limit("10/minute")          # heavy upload
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    document_type: str = "contract",
    db: Session = Depends(get_db),
):
    """Upload and process a document."""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Invalid filename")

        extension = Path(file.filename).suffix.lower()[1:]
        if extension not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format. Allowed: {settings.ALLOWED_EXTENSIONS}",
            )

        file_path = Path(settings.upload_dir) / file.filename
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        file_size = file_path.stat().st_size

        if file_size > settings.MAX_FILE_SIZE:
            file_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max: {settings.MAX_FILE_SIZE} bytes",
            )

        logger.info(f"Extracting text from {file.filename}")
        extractor = DocumentExtractor()
        original_text, file_type = extractor.extract_text(str(file_path))

        if not original_text.strip():
            file_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=400,
                detail="No text found in document",
            )

        db_doc = Document(
            filename=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            original_text=original_text,
            document_type=document_type,
            language="en",
            processing_status="pending",
        )

        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)

        logger.info(f"✓ Document uploaded: {file.filename} (ID: {db_doc.id})")

        # Metrics: document upload operation
        record_document_operation("upload")

        return serialize_document(db_doc)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Upload failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/{document_id}")
@limiter.limit("30/minute")
async def delete_document(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db),
):
    """Delete a document."""
    try:
        document = (
            db.query(Document)
            .filter(Document.id == document_id)
            .first()
        )

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if document.file_path and Path(document.file_path).exists():
            Path(document.file_path).unlink()

        db.delete(document)
        db.commit()

        # Metrics: document delete operation
        record_document_operation("delete")

        return {"status": "deleted", "id": document_id}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Delete failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/tasks/{task_id}", tags=["tasks"])
@limiter.limit("60/minute")
async def get_task_status(
    request: Request, 
    task_id: str,
):
    """Get Celery task status."""
    task = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None,
    }
