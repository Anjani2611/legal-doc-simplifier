"""Pydantic schemas for request/response validation"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    """Schema for creating a new document"""
    filename: str = Field(..., min_length=1, max_length=255)
    file_size: int = Field(..., gt=0)
    document_type: str = Field(default="contract")
    language: str = Field(default="en")
    original_text: str = Field(..., min_length=1)


class DocumentResponse(BaseModel):
    """Schema for document response"""
    id: int
    filename: str
    file_size: int
    document_type: str
    language: str
    is_processed: bool
    processing_status: str
    simplified_text: Optional[str] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DocumentList(BaseModel):
    """Schema for list of documents"""
    total: int
    documents: list[DocumentResponse]


class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    database: str
    timestamp: datetime
