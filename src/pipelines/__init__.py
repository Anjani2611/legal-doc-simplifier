"""Pipelines for document processing"""

from src.pipelines.simplification import get_simplification_pipeline

def get_risk_detector():
    """Stub: Risk detection pipeline (TODO: implement)"""
    return None

__all__ = ["get_simplification_pipeline", "get_risk_detector"]
