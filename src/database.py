"""Database connection and session management"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from src.settings import settings

# Create database engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,  # Log SQL queries in debug mode
    pool_pre_ping=True,   # Test connections before using them
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for all models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency injection for database sessions in FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
