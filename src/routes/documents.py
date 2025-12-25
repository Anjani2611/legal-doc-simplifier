"""Document-related API endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.document import Document
from src.schemas.document import DocumentCreate, DocumentResponse, DocumentList

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/", response_model=DocumentList)
async def list_documents(
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
    doc: DocumentCreate,
    db: Session = Depends(get_db),
):
    """Create a new document (placeholder)"""
    # This is a placeholder - real implementation would handle file uploads
    
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
