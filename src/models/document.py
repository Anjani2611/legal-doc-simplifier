"""Database models for legal documents"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func

from src.database import Base


class Document(Base):
    """Model for uploaded legal documents"""
    
    __tablename__ = "documents"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Document info
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)  # In bytes
    
    # Document content
    original_text = Column(Text, nullable=False)
    simplified_text = Column(Text, nullable=True)
    
    # Metadata
    document_type = Column(String(50), default="contract")  # contract, lease, nda, etc.
    language = Column(String(10), default="en")
    
    # Status
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, error
    
    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}')>"


class RiskFlag(Base):
    """Model for identified risks in documents"""
    
    __tablename__ = "risk_flags"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to document
    document_id = Column(Integer, nullable=False, index=True)
    
    # Risk info
    risk_level = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    risk_score = Column(Integer, nullable=False)  # 0-100
    clause_text = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<RiskFlag(id={self.id}, document_id={self.document_id}, risk_level='{self.risk_level}')>"
