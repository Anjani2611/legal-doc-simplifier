from src.schemas.document import DocumentResponse
from src.models.document import Document
from src.database import SessionLocal

db = SessionLocal()
doc = db.query(Document).first()
print("DOC:", doc, type(doc.created_at))

validated = DocumentResponse.model_validate(doc)
print("VALIDATED:", validated)
