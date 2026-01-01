from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class DocumentBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    filename: str
    file_path: str
    file_size: int
    original_text: str
    document_type: str
    language: str
    processing_status: Optional[str] = None


class DocumentCreate(BaseModel):
    filename: str
    file_size: int
    original_text: str
    document_type: str
    language: str = "en"


class DocumentResponse(DocumentBase):
    id: int
    created_at: datetime


class DocumentList(BaseModel):
    total: int
    documents: List[DocumentResponse]

    model_config = ConfigDict(from_attributes=True)
