import os
import sys
from datetime import datetime, timezone
from sqlalchemy.orm import Session

# Ensure app package import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal  # If your session factory is named differently, adjust import
from app import models
from app.security import get_password_hash

def get_env(name: str, default: str | None = None, required: bool = False) -> str:
    val = os.getenv(name, default)
    if required and not val:
        raise RuntimeError(f"Missing required env var: {name}")
    return val or ""

def upsert_admin(db: Session):
    username = get_env("ADMIN_DEFAULT_USERNAME", "admin")
    email = get_env("ADMIN_DEFAULT_EMAIL", "admin@example.com")
    phone = get_env("ADMIN_DEFAULT_PHONE", "0000000000")
    raw_password = get_env("ADMIN_DEFAULT_PASSWORD", required=True)

    # Find existing admin by username or email
    user = db.query(models.User).filter(
        (models.User.username == username) | (models.User.email == email)
    ).first()

    password_hash = get_password_hash(raw_password)

    if user:
        # Update to ensure active admin with known password
        user.username = username
        user.email = email
        user.phone = phone
        user.role = models.UserRole.admin
        user.is_active = True
        user.account_locked_until = None
        user.failed_login_attempts = 0 if hasattr(user, "failed_login_attempts") else 0
        user.password_hash = password_hash if hasattr(user, "password_hash") else password_hash
        user.updated_at = datetime.now(timezone.utc) if hasattr(user, "updated_at") else None
        action = "updated"
    else:
        # Create admin
        user = models.User(
            username=username,
            email=email,
            phone=phone,
            role=models.UserRole.admin,
            is_active=True,
            password_hash=password_hash,
            failed_login_attempts=0 if hasattr(models.User, "failed_login_attempts") else 0,
            created_at=datetime.now(timezone.utc) if hasattr(models.User, "created_at") else None,
            updated_at=datetime.now(timezone.utc) if hasattr(models.User, "updated_at") else None,
        )
        db.add(user)
        action = "created"

    db.commit()
    print(f"Admin user {action}: username='{username}', email='{email}'")

def main():
    # Load .env if using python-dotenv (optional). If not, ensure env is set before running.
    # from dotenv import load_dotenv; load_dotenv()

    # Validate required env
    _ = get_env("ADMIN_DEFAULT_PASSWORD", required=True)

    db = SessionLocal()
    try:
        upsert_admin(db)
    finally:
        db.close()

if __name__ == "__main__":
    main()