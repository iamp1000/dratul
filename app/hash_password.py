# This script initializes the admin user on startup.
import os
import logging
from .database import SessionLocal
from .schemas import UserCreate

# This function is the ONLY thing that should be imported from this file.
def create_or_update_admin():
    """
    Checks for and creates/updates the admin user on startup.
    Imports are done LOCALLY inside the function to prevent circular dependencies.
    """
    # --- Local Imports to break circular dependency ---
    from . import crud
    from .security import get_password_hash, verify_password
    # --- End Local Imports ---

    db = SessionLocal()
    try:
        admin_username = "admin"
        admin_password = os.getenv("ADMIN_DEFAULT_PASSWORD")
        logger = logging.getLogger(__name__)

        if not admin_password:
            logger.warning("ADMIN_DEFAULT_PASSWORD not set in .env file. Skipping admin user setup.")
            return

        user = crud.get_user_by_identifier(db, admin_username)

        if user:
            # Only update the hash if the current password doesn't match
            if not verify_password(admin_password, user.password_hash):
                user.password_hash = get_password_hash(admin_password)
                db.commit()
                logger.info("Admin user password has been updated on startup to match .env file.")
        else:
            # If admin user does not exist, create them
            admin_email = os.getenv("ADMIN_DEFAULT_EMAIL", "admin@example.com")
            admin_phone = os.getenv("ADMIN_DEFAULT_PHONE", "1234567890")
            user_in = UserCreate(
                username=admin_username,
                email=admin_email,
                password=admin_password, # The crud function will hash this
                role="admin",
                phone_number=admin_phone,
                # Set required fields that are not in UserCreate schema
                id=0, # Placeholder, will be ignored by DB
                is_active=True,
                mfa_enabled=False,
                created_at=None,
                updated_at=None,
                last_login=None,
                permissions={}
            )
            crud.create_user(db, user_in)
            logger.info("Admin user has been created on startup.")
    except Exception as e:
        logging.getLogger(__name__).error(f"CRITICAL: Error during admin user initialization: {e}")
    finally:
        db.close()