"""Text simplification endpoints"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import Depends
import logging

from src.database import get_db
from src.models.document import Document
from src.pipelines import get_simplification_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/simplify", tags=["simplification"])


class SimplifyRequest(BaseModel):
    """Request schema for simplification"""
    text: str = Field(..., min_length=10, max_length=10000)
    document_id: Optional[int] = Field(None, description="Optional: Document ID to update")


class SimplifyResponse(BaseModel):
    """Response schema for simplification"""
    original: str
    simplified: str
    reduction: float  # Percentage reduction


@router.post("/text", response_model=SimplifyResponse)
async def simplify_text(request: SimplifyRequest):
    """Simplify raw legal text"""
    try:
        pipeline = get_simplification_pipeline()
        simplified = pipeline.simplify(request.text)
        
        # Calculate reduction percentage
        reduction = ((len(request.text) - len(simplified)) / len(request.text)) * 100
        
        return SimplifyResponse(
            original=request.text,
            simplified=simplified,
            reduction=round(reduction, 2),
        )
    
    except Exception as e:
        logger.error(f"Simplification error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/document/{document_id}")
async def simplify_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    """Simplify and update a document from database"""
    try:
        # Get document
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Simplify
        pipeline = get_simplification_pipeline()
        simplified_text = pipeline.simplify(doc.original_text)
        
        # Update document
        doc.simplified_text = simplified_text
        doc.is_processed = True
        doc.processing_status = "completed"
        
        db.commit()
        db.refresh(doc)
        
        return {
            "id": doc.id,
            "filename": doc.filename,
            "original_length": len(doc.original_text),
            "simplified_length": len(simplified_text),
            "status": "completed",
        }
    
    except Exception as e:
        logger.error(f"Document simplification error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
