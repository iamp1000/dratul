# app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas, security, models
from ..database import get_db

router = APIRouter(
    tags=["Users"],
    dependencies=[Depends(security.require_admin)],
    responses={404: {"description": "Not found"}},
)

@router.post("/users", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_new_user(
    user: schemas.UserCreate, 
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(security.require_admin)
):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    new_user = crud.create_user(db=db, user=user)
    crud.create_audit_log(
        db=db, user_id=current_admin.id, action="CREATE", category="USER",
        resource_id=new_user.id, details=f"Created new user: {new_user.username} with role {new_user.role.value}",
        new_values=user.dict()
    )
    return new_user

@router.get("/users", response_model=List[schemas.User])
def read_all_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@router.put("/users/{user_id}", response_model=schemas.User)
def update_existing_user(
    user_id: int, 
    user_update: schemas.UserUpdate, 
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(security.require_admin)
):
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = crud.update_user(db, user_id=user_id, user_update=user_update)
    crud.create_audit_log(
        db=db, user_id=current_admin.id, action="UPDATE", category="USER",
        resource_id=user_id, details=f"Updated user: {updated_user.username}",
        new_values=user_update.dict(exclude_unset=True)
    )
    return updated_user

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(security.require_admin)
):
    db_user = crud.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deletion of super admin
    if getattr(db_user, 'is_super_admin', False) or db_user.username == "iamp1000":
        raise HTTPException(status_code=403, detail="Cannot delete super admin user.")
    
    username = db_user.username
    crud.delete_user(db, user_id=user_id)
    crud.create_audit_log(
        db=db, user_id=current_admin.id, action="DELETE", category="USER",
        resource_id=user_id, details=f"Deleted user: {username}"
    )
    return