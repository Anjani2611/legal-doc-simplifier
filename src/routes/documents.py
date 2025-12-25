"""Document-related API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
import logging

from src.middleware import limiter
from src.database import get_db
from src.models.document import Document
from src.schemas.document import DocumentCreate, DocumentResponse, DocumentList
from src.config import settings
from src.utils.document_extractor import DocumentExtractor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

# Create uploads directory if it doesn't exist
Path(settings.UPLOAD_DIR).mkdir(exist_ok=True)


@router.get("/", response_model=DocumentList)
async def list_documents(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """List all uploaded documents"""
    documents = db.query(Document).offset(skip).limit(limit).all()
    total = db.query(Document).count()

    return DocumentList(
        total=total,
        documents=documents,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific document by ID"""
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@router.post("/", response_model=DocumentResponse)
async def create_document(
    request: Request,
    doc: DocumentCreate,
    db: Session = Depends(get_db),
):
    """Create a new document (placeholder)"""

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

    return db_doc


@router.post("/upload", response_model=DocumentResponse)
@limiter.limit("10/minute")  # 10 uploads per minute per IP
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    document_type: str = "contract",
    db: Session = Depends(get_db),
):
    """Upload and process a document"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="Invalid filename")

        extension = Path(file.filename).suffix.lower()[1:]
        if extension not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format. Allowed: {settings.ALLOWED_EXTENSIONS}",
            )

        # Save uploaded file
        file_path = Path(settings.UPLOAD_DIR) / file.filename
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        file_size = file_path.stat().st_size

        # Validate file size
        if file_size > settings.MAX_FILE_SIZE:
            file_path.unlink()
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max: {settings.MAX_FILE_SIZE} bytes",
            )

        # Extract text from document
        logger.info(f"Extracting text from {file.filename}")
        extractor = DocumentExtractor()
        original_text, file_type = extractor.extract_text(str(file_path))

        if not original_text.strip():
            file_path.unlink()
            raise HTTPException(status_code=400, detail="No text found in document")

        # Create database entry
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

        return db_doc

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db),
):
    """Delete a document"""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete file if exists
        if Path(document.file_path).exists():
            Path(document.file_path).unlink()

        # Delete from database
        db.delete(document)
        db.commit()

        return {"status": "deleted", "id": document_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
