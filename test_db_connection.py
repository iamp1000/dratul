#!/usr/bin/env python3
"""
Database Connection Diagnostic Tool
Tests your DATABASE_URL and provides detailed error information
"""
import sys
import os
from urllib.parse import urlparse, quote_plus

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

def test_database_connection():
    """Test database connection and provide diagnostics"""
    print("=" * 60)
    print("Database Connection Diagnostic Tool")
    print("=" * 60)
    
    # Get DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("\n[ERROR] DATABASE_URL is not set in .env file")
        print("\nPlease add DATABASE_URL to your .env file:")
        print("DATABASE_URL=postgresql://username:password@localhost:5432/database_name")
        return False
    
    print(f"\n[INFO] DATABASE_URL found (length: {len(database_url)} characters)")
    
    # Parse URL
    try:
        parsed = urlparse(database_url)
        print(f"\n[INFO] Parsed URL components:")
        print(f"  Scheme: {parsed.scheme}")
        print(f"  Username: {parsed.username or '(not set)'}")
        print(f"  Password: {'*' * len(parsed.password) if parsed.password else '(not set)'}")
        print(f"  Hostname: {parsed.hostname or 'localhost'}")
        print(f"  Port: {parsed.port or 5432}")
        print(f"  Database: {parsed.path.lstrip('/') or '(not set)'}")
    except Exception as e:
        print(f"\n[ERROR] Failed to parse DATABASE_URL: {e}")
        return False
    
    # Validate format
    if not database_url.startswith(("postgresql://", "postgresql+psycopg2://", "sqlite:///")):
        print(f"\n[ERROR] Invalid DATABASE_URL format")
        print("Must start with: postgresql://, postgresql+psycopg2://, or sqlite:///")
        return False
    
    # Check for common issues
    issues = []
    if not parsed.username:
        issues.append("Username is missing")
    if not parsed.password:
        issues.append("Password is missing")
    if not parsed.path or parsed.path == "/":
        issues.append("Database name is missing")
    
    if issues:
        print(f"\n[WARNING] Potential issues found:")
        for issue in issues:
            print(f"  - {issue}")
    
    # Test connection
    print(f"\n[INFO] Testing database connection...")
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.exc import OperationalError
        
        engine = create_engine(database_url, pool_pre_ping=True, connect_args={"connect_timeout": 5})
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"\n[SUCCESS] Connection successful!")
            print(f"  PostgreSQL version: {version[:50]}...")
            
            # Test database exists
            db_name = parsed.path.lstrip('/')
            if db_name:
                result = conn.execute(text("SELECT current_database()"))
                current_db = result.fetchone()[0]
                print(f"  Connected to database: {current_db}")
            
            # Test user permissions
            result = conn.execute(text("SELECT current_user"))
            current_user = result.fetchone()[0]
            print(f"  Connected as user: {current_user}")
        
        engine.dispose()
        print(f"\n[SUCCESS] All tests passed! Your database connection is working.")
        return True
        
    except OperationalError as e:
        error_str = str(e)
        print(f"\n[ERROR] Connection failed!")
        
        if "password authentication failed" in error_str:
            print(f"\n  Issue: Password authentication failed")
            print(f"  This means:")
            print(f"    - The username '{parsed.username}' exists in PostgreSQL")
            print(f"    - BUT the password is incorrect")
            print(f"\n  Solutions:")
            print(f"    1. Verify the password in your .env file")
            print(f"    2. Check if password contains special characters that need URL encoding:")
            print(f"       @ = %40, # = %23, $ = %24, % = %25, & = %26, + = %2B, = = %3D")
            print(f"    3. Reset the PostgreSQL user password:")
            print(f"       ALTER USER {parsed.username} WITH PASSWORD 'new_password';")
            
        elif "could not connect" in error_str.lower() or "connection refused" in error_str.lower():
            print(f"\n  Issue: Cannot connect to PostgreSQL server")
            print(f"  Server: {parsed.hostname or 'localhost'}:{parsed.port or 5432}")
            print(f"\n  Solutions:")
            print(f"    1. Check if PostgreSQL is running:")
            print(f"       Windows: Get-Service -Name postgresql*")
            print(f"    2. Start PostgreSQL if not running:")
            print(f"       Windows: Start-Service postgresql-x64-<version>")
            print(f"    3. Verify hostname and port are correct")
            
        elif "database" in error_str.lower() and "does not exist" in error_str.lower():
            print(f"\n  Issue: Database '{parsed.path.lstrip('/')}' does not exist")
            print(f"\n  Solution: Create the database:")
            print(f"    CREATE DATABASE {parsed.path.lstrip('/')};")
            
        elif "role" in error_str.lower() and "does not exist" in error_str.lower():
            print(f"\n  Issue: User '{parsed.username}' does not exist in PostgreSQL")
            print(f"\n  Solution: Create the user:")
            print(f"    CREATE USER {parsed.username} WITH PASSWORD 'your_password';")
            print(f"    GRANT ALL PRIVILEGES ON DATABASE {parsed.path.lstrip('/')} TO {parsed.username};")
            
        else:
            print(f"\n  Error: {error_str}")
        
        print(f"\n  Full error details:")
        print(f"    {error_str}")
        return False
        
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)

