# app/database.py
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy import inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import get_settings

# Create engine
engine = create_engine(
    get_settings().database_url,
    pool_pre_ping=True,
    echo=False
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all database tables - MUST import models first!"""
    # Import models to register them with Base.metadata
    from . import models  # This line is CRITICAL

    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
    # Lightweight migration: ensure new columns exist without full Alembic run
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        if 'is_super_admin' not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_super_admin BOOLEAN DEFAULT FALSE"))
        presc_cols = [col['name'] for col in inspector.get_columns('prescriptions')]
        if 'document_id' not in presc_cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE prescriptions ADD COLUMN IF NOT EXISTS document_id INTEGER"))
    except Exception:
        # Non-fatal: if this fails, Alembic can manage migrations
        pass

def drop_tables():
    """Drop all database tables"""
    Base.metadata.drop_all(bind=engine)
    print("Database tables dropped successfully!")
