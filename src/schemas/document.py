from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, field_validator


# ====== Models used by document routes ======

class DocumentCreate(BaseModel):
    filename: str
    file_size: int
    original_text: str
    document_type: str
    language: str = "en"


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    file_size: int
    document_type: str
    processing_status: str
    created_at: str

    model_config = {"from_attributes": True}


class DocumentList(BaseModel):
    total: int
    documents: List[DocumentResponse]


class DocumentUploadSchema(BaseModel):
    document_type: str = Field(..., min_length=1, max_length=50)

    @field_validator("document_type")
    @classmethod
    def validate_document_type(cls, v):
        allowed_types = {"contract", "agreement", "nda", "terms", "other"}
        if v.lower() not in allowed_types:
            raise ValueError(f"Invalid type. Must be one of {allowed_types}")
        return v.lower()


class SimplifyTextSchema(BaseModel):
    text: str = Field(..., min_length=10, max_length=50000)

    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Text must be at least 10 characters")
        return v


class TargetLevel(str, Enum):
    simple = "simple"
    intermediate = "intermediate"
    advanced = "advanced"


class SimplifyRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to simplify")
    target_level: TargetLevel
    language: str
    options: Optional[Dict[str, Any]] = None


class SimplifyResponse(BaseModel):
    original: str
    simplified: str
    reduction: float


class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime
