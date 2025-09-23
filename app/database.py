# database.py
# This file handles the connection to our PostgreSQL database using SQLAlchemy.

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import get_settings
settings = get_settings()

# IMPORTANT: Replace 'YourSecurePasswordHere' with your actual password.
# For production, use environment variables for security.
DATABASE_URL = settings.DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency for Database Sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()