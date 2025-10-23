# This script initializes the admin user on startup.
import os
from dotenv import load_dotenv
import logging
from .database import SessionLocal
from .schemas import UserCreate, LocationCreate
from . import crud

def create_initial_data():
    """Creates initial data like locations if they don't exist."""
    db = SessionLocal()
    try:
        logger = logging.getLogger(__name__)
        locations_to_create = [
            LocationCreate(name="Home Clinic", address="123 Home St", timezone="UTC"),
            LocationCreate(name="Hospital", address="456 Hospital Ave", timezone="UTC")
        ]
        for loc_data in locations_to_create:
            location = crud.get_location_by_name(db, loc_data.name)
            if not location:
                crud.create_location(db, loc_data)
                logger.info(f"Initial location '{loc_data.name}' created.")
    except Exception as e:
        logging.getLogger(__name__).error(f"CRITICAL: Error during initial data creation: {e}")
    finally:
        db.close()


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
        # Ensure .env is loaded before reading env vars (when config isn't imported yet)
        try:
            load_dotenv()
        except Exception:
            pass
        # Ensure super admin exists and cannot be deleted (production-ready: no plaintext in code)
        super_username = os.getenv("SUPER_ADMIN_USERNAME", "iamp1000")
        super_password_hash = os.getenv("SUPER_ADMIN_PASSWORD_HASH")
        super_password_plain = os.getenv("SUPER_ADMIN_PASSWORD")  # optional fallback; will be hashed then discarded
        logger = logging.getLogger(__name__)

        # Determine a hash to enforce
        from .security import get_password_hash, verify_password
        enforced_hash = None
        if super_password_hash:
            enforced_hash = super_password_hash
        elif super_password_plain:
            enforced_hash = get_password_hash(super_password_plain)

        # Upsert super admin (if we have some credential source)
        su = crud.get_user_by_identifier(db, super_username)
        if su:
            # Ensure role and flags
            su.role = "admin" if getattr(su.role, 'value', su.role) != 'admin' else su.role
            su.is_active = True
            su.is_super_admin = True
            # Keep password synced to provided secret/hash (if configured)
            if enforced_hash and su.password_hash != enforced_hash:
                # If env provided hash, set directly; else if plain was provided, we already hashed
                su.password_hash = enforced_hash
            db.commit()
            logger.info("Super admin verified/updated.")
        else:
            if enforced_hash:
                admin_email = os.getenv("ADMIN_DEFAULT_EMAIL", "admin@example.com")
                admin_phone = os.getenv("ADMIN_DEFAULT_PHONE", "1234567890")
                # Create with a temp password, then overwrite hash to enforced_hash to avoid handling plaintext
                user_in = UserCreate(
                    username=super_username,
                    email=admin_email,
                    password=super_password_plain or "TempPass123!",  # will be overridden below
                    role="admin",
                    phone_number=admin_phone,
                )
                created = crud.create_user(db, user_in)
                created.is_super_admin = True
                created.password_hash = enforced_hash
                db.commit()
                logger.info("Super admin created.")
            else:
                logger.warning("SUPER_ADMIN_PASSWORD_HASH or SUPER_ADMIN_PASSWORD not set. Super admin not created.")

        admin_username = "admin"
        admin_password = os.getenv("ADMIN_DEFAULT_PASSWORD")

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
        
    