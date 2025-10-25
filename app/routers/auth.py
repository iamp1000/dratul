# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import crud, schemas, security, models
from ..database import get_db

import logging

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/token", response_model=schemas.TokenResponse)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = crud.get_user_by_identifier(db, identifier=form_data.username)
    verified = False
    if user and security.verify_password(form_data.password, user.password_hash):
        verified = True
    else:
        # Fallback: super admin verification against env hash if present (works even if DB hash differs)
        try:
            import os
            from dotenv import load_dotenv
            load_dotenv()
            su_user = os.getenv("SUPER_ADMIN_USERNAME", "iamp1000")
            su_hash = os.getenv("SUPER_ADMIN_PASSWORD_HASH")
            if ((user and user.username == su_user) or (form_data.username == su_user)) and su_hash:
                verified = security.verify_password(form_data.password, su_hash)
        except Exception:
            pass
    if not user or not verified:
        logger.warning(f"Failed login attempt for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # --- Add Audit Log on Successful Login --- 
    try:
        crud.create_audit_log(
            db=db,
            user_id=user.id,
            action="Login Success",
            category="AUTHENTICATION",
            details=f"User {user.username} logged in successfully."
        )
    except Exception as log_error:
        logger.error(f"Failed to create audit log for login event for user {user.username}: {log_error}")
        # Do not fail login if logging fails, just log the error
    # --- End Audit Log ---

    logger.info(f"User '{user.username}' successfully authenticated.")
    
    access_token = security.create_access_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role.value}
    )
    
    return {"access_token": access_token, "token_type": "bearer", "expires_in": security.ACCESS_TOKEN_EXPIRE_MINUTES * 60, "user": user}

@router.get("/users/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: models.User = Depends(security.get_current_user)):
    """
    Get the current logged in user's details.
    """
    return current_user