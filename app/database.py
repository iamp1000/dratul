# app/database.py (SYNC VERSION)

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import get_settings


settings = get_settings()

# Normalize async DSN to sync DSN if present
DATABASE_URL = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")

# Create sync engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # validates connections before use
)

# Classic sync session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base
Base = declarative_base()

# FastAPI dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
