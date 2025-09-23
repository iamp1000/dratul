# app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas, security, models
from ..database import get_db

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(security.require_admin)], # All routes require admin
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_new_user(
    user: schemas.UserCreate, 
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(security.require_admin)
):
    """
    Create a new user. Only accessible by administrators.
    """
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    new_user = crud.create_user(db=db, user=user)
    crud.create_activity_log(db, user_id=current_admin.id, action="Create User", details=f"Created new user: {new_user.username} with role {new_user.role.value}")
    return new_user

@router.get("/", response_model=List[schemas.User])
def read_all_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve all users. Only accessible by administrators.
    """
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@router.put("/{user_id}", response_model=schemas.User)
def update_existing_user(
    user_id: int, 
    user_update: schemas.UserUpdate, 
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(security.require_admin)
):
    """
    Update a user's information. Only accessible by administrators.
    """
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = crud.update_user(db, user_id=user_id, user_update=user_update)
    crud.create_activity_log(db, user_id=current_admin.id, action="Update User", details=f"Updated user: {updated_user.username}")
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(security.require_admin)
):
    """
    Delete a user. Only accessible by administrators.
    """
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if db_user.username in ["p1000", "dratul"]:
        raise HTTPException(status_code=403, detail="Cannot delete initial admin users.")
    
    username = db_user.username
    crud.delete_user(db, user_id=user_id)
    crud.create_activity_log(db, user_id=current_admin.id, action="Delete User", details=f"Deleted user: {username}")
    return

@router.get("/logs", response_model=List[schemas.ActivityLog])
def read_activity_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve activity logs. Only accessible by administrators.
    """
    logs = crud.get_activity_logs(db, skip=skip, limit=limit)
    return logs
