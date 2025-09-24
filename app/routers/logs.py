from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import crud, schemas, security, models
from ..database import get_db

router = APIRouter(
    prefix="/logs",
    tags=["Activity Logs"],
    dependencies=[Depends(security.get_current_user)],
)

@router.get("/", response_model=List[schemas.ActivityLog])
def get_activity_logs(
    category: Optional[str] = Query(None, description="Filter by category: Patient, Admin, Appointments, Prescription, General"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get activity logs with optional category filtering"""
    if category:
        return crud.get_activity_logs_by_category(db, category=category, skip=skip, limit=limit)
    else:
        return crud.get_activity_logs(db, skip=skip, limit=limit)

@router.get("/categories")
def get_log_categories():
    """Get available log categories"""
    return {
        "categories": [
            "General",
            "Patient", 
            "Admin",
            "Appointments",
            "Prescription",
            "System"
        ]
    }
    