import os
from celery import Celery

celery_app = Celery(
    "legal_simplifier",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
)


@celery_app.task
def simplify_document_async(document_id: int):
    """Background task for document simplification."""
    from src.database import SessionLocal
    from src.models.document import Document
    from src.pipelines.simplification import simplify_text

    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            simplified = simplify_text(doc.original_text)
            doc.simplified_text = simplified
            doc.processing_status = "completed"
            db.commit()
    finally:
        db.close()
