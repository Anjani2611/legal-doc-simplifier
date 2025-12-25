"""Document analysis endpoints (risk detection, metrics, etc.)"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import logging
from typing import List, Optional

from src.database import get_db
from src.models.document import Document, RiskFlag
from src.pipelines import get_risk_detector

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analyze", tags=["analysis"])


class RiskItem(BaseModel):
    """Single risk detection result"""
    risk_level: str
    risk_score: int
    description: str
    recommendation: str


class AnalysisResponse(BaseModel):
    """Analysis response for a document"""
    document_id: int
    filename: str
    text_length: int
    word_count: int
    risks_detected: int
    risks: List[RiskItem]
    avg_risk_score: Optional[float]


@router.post("/document/{document_id}", response_model=AnalysisResponse)
async def analyze_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    """Analyze document for risks"""
    try:
        # Get document
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Run risk detection
        detector = get_risk_detector()
        detected_risks = detector.detect_risks(doc.original_text)
        
        # Save risks to database
        existing_risks = db.query(RiskFlag).filter(RiskFlag.document_id == document_id).all()
        for risk in existing_risks:
            db.delete(risk)
        
        for risk in detected_risks:
            risk_flag = RiskFlag(
                document_id=document_id,
                risk_level=risk["risk_level"],
                risk_score=risk["risk_score"],
                clause_text=risk["clause_text"],
                description=risk["description"],
                recommendation=risk["recommendation"],
            )
            db.add(risk_flag)
        
        db.commit()
        
        # Calculate stats
        word_count = len(doc.original_text.split())
        avg_risk_score = (
            sum(r["risk_score"] for r in detected_risks) / len(detected_risks)
            if detected_risks else 0
        )
        
        return AnalysisResponse(
            document_id=doc.id,
            filename=doc.filename,
            text_length=len(doc.original_text),
            word_count=word_count,
            risks_detected=len(detected_risks),
            risks=[RiskItem(**r) for r in detected_risks],
            avg_risk_score=round(avg_risk_score, 2),
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/document/{document_id}/risks")
async def get_document_risks(
    document_id: int,
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get detected risks for a document"""
    try:
        query = db.query(RiskFlag).filter(RiskFlag.document_id == document_id)
        
        if risk_level:
            query = query.filter(RiskFlag.risk_level == risk_level.upper())
        
        risks = query.all()
        
        return {
            "document_id": document_id,
            "total_risks": len(risks),
            "risks": [
                {
                    "id": r.id,
                    "risk_level": r.risk_level,
                    "risk_score": r.risk_score,
                    "description": r.description,
                    "recommendation": r.recommendation,
                }
                for r in risks
            ],
        }
    
    except Exception as e:
        logger.error(f"Get risks failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
