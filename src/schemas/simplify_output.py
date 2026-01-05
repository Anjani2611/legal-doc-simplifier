"""Pydantic schemas for simplification API with OpenAPI examples."""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


class Clause(BaseModel):
    """Individual legal clause with metadata."""

    id: str = Field(
        ...,
        description="Unique clause ID",
        example="clause_1",
    )
    type: str = Field(
        ...,
        description="Clause type (payment_obligation, liability, termination, etc.)",
        example="payment_obligation",
    )
    original_text: str = Field(
        ...,
        description="Original clause text from input",
        example="Payment clause: The buyer shall pay the seller $1000 USD within 30 days of delivery.",
    )
    simplified_text: str = Field(
        ...,
        description="Simplified plain-English version",
        example="The buyer must pay the seller $1000 USD no later than 30 days of delivery.",
    )
    risk_level: str = Field(
        ...,
        description="Risk level: low, medium, or high",
        example="high",
    )
    key_entities: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted entities (parties, amounts, deadlines, etc.)",
        example={
            "party_1": "buyer",
            "party_2": "seller",
            "amount": "$1000",
            "deadline": "30 days",
            "conditions": False,
            "numerics": ["1000", "30"],
        },
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Clause-specific warnings",
        example=["numerics_present", "time_sensitive"],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "clause_1",
                "type": "payment_obligation",
                "original_text": "The buyer shall pay $1000 within 30 days.",
                "simplified_text": "The buyer must pay $1000 no later than 30 days.",
                "risk_level": "medium",
                "key_entities": {
                    "party_1": "buyer",
                    "amount": "$1000",
                    "deadline": "30 days",
                },
                "warnings": ["time_sensitive"],
            }
        }


class SimplifyOutput(BaseModel):
    """Response schema for simplification endpoint."""

    summary: str = Field(
        ...,
        description="Overall plain-English summary of the document",
        example="The buyer must pay the seller $1000 USD no later than 30 days of delivery.",
    )
    clauses: List[Clause] = Field(
        default_factory=list,
        description="List of extracted and analyzed clauses",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Document-level warnings (input_too_short, validation_failed, etc.)",
        example=[],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "summary": "The buyer must pay the seller $1000 USD no later than 30 days.",
                "clauses": [
                    {
                        "id": "clause_1",
                        "type": "payment_obligation",
                        "original_text": "Payment clause: The buyer shall pay the seller $1000 USD within 30 days of delivery.",
                        "simplified_text": "The buyer must pay the seller $1000 USD no later than 30 days of delivery.",
                        "risk_level": "high",
                        "key_entities": {
                            "party_1": "buyer",
                            "party_2": "seller",
                            "amount": "$1000",
                            "deadline": "30 days",
                        },
                        "warnings": ["time_sensitive"],
                    }
                ],
                "warnings": [],
            }
        }
