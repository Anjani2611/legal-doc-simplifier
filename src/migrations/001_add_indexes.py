from sqlalchemy import text
from src.database import engine

def add_indexes():
    """Add database indexes for frequently queried columns"""
    with engine.connect() as conn:
        # Index on document_id in risk_flags (foreign key lookups)
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_risk_flags_document_id 
            ON risk_flags(document_id);
        """))
        
        # Index on processing_status (filtering documents)
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_documents_processing_status 
            ON documents(processing_status);
        """))
        
        # Index on risk_level (filtering risks)
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_risk_flags_risk_level 
            ON risk_flags(risk_level);
        """))
        
        # Composite index for common queries
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_documents_created_status 
            ON documents(created_at, processing_status);
        """))
        
        conn.commit()
        print("✓ Indexes created successfully")

if __name__ == "__main__":
    add_indexes()
