"""Pipelines for document processing"""

from src.pipelines.simplification import get_simplification_pipeline
from src.pipelines.risk_detection import get_risk_detector

__all__ = ["get_simplification_pipeline", "get_risk_detector"]
