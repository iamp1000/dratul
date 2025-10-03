# app/database.py
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import get_settings

settings = get_settings()

# Normalize async DSN to sync DSN if present
DATABASE_URL = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")

# Create sync engine with connection pooling and performance optimizations
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,           # Validates connections before use
    pool_size=20,                 # Number of connections to maintain in pool
    max_overflow=30,              # Number of connections to allow beyond pool_size
    pool_timeout=30,              # Timeout to get connection from pool
    pool_recycle=3600,            # Recycle connections after 1 hour
    echo=False,                   # Set to True for debugging SQL queries
    connect_args={
        "application_name": "clinic_management_system",
        "options": "-c timezone=UTC"
    }
)

# Session factory with optimized settings
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False        # Don't expire objects after commit
)

# Single declarative base for all models
Base = declarative_base()

# Dependency to get database session
def get_db():
    """
    Database dependency for FastAPI endpoints.
    Yields a database session and ensures proper cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def create_tables():
    """
    Create all database tables.
    Should be called on application startup.
    """
    Base.metadata.create_all(bind=engine)
    
def drop_tables():
    """
    Drop all database tables.
    Use with caution - only for development/testing.
    """
    Base.metadata.drop_all(bind=engine)

# Event listeners for database optimizations
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance (if using SQLite)"""
    if "sqlite" in str(engine.url):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=1000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()

@event.listens_for(engine, "connect")
def set_postgresql_settings(dbapi_connection, connection_record):
    """Set PostgreSQL connection settings for better performance"""
    if "postgresql" in str(engine.url):
        with dbapi_connection.cursor() as cursor:
            # Enable JIT compilation for complex queries (PostgreSQL 11+)
            cursor.execute("SET jit = on")
            # Set work memory for sorting/hashing operations
            cursor.execute("SET work_mem = '16MB'")
            # Set timezone to UTC
            cursor.execute("SET timezone = 'UTC'")