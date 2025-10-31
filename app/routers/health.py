# app/routers/health.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timezone

from .. import crud, schemas, models, security
from ..database import get_db
from ..models import UserRole

router = APIRouter(
    prefix="/health",
    tags=["Health Checks"],
    responses={404: {"description": "Not found"}},
)

# Dependency to ensure only admins can access
async def get_current_admin_user(current_user: models.User = Depends(security.get_current_user)) -> models.User:
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )
    return current_user

@router.get("/consistency-check", response_model=schemas.ConsistencyReport, dependencies=[Depends(get_current_admin_user)])
async def check_system_consistency(db: Session = Depends(get_db)) -> schemas.ConsistencyReport:
    """
    Performs data consistency checks for slots and appointments.
    Accessible only by admin users.
    """
    print("INFO: Running system consistency checks...")
    # Call the synchronous function without 'await'
    inconsistencies = crud.run_consistency_checks(db=db)
    print(f"INFO: Consistency checks completed. Found {len(inconsistencies.get('booked_slots_without_appointments', []))} issues of type 1.")
    
    # The CRUD function returns a dict, which Pydantic will validate against the response_model
    return inconsistencies

@router.post("/fix-anomalies", response_model=schemas.ConsistencyFixReport, dependencies=[Depends(get_current_admin_user)])
async def fix_system_anomalies(db: Session = Depends(get_db)):
    """
    Runs the consistency checker and automatically fixes anomalies.
    Returns a report of all actions taken.
    Accessible only by admin users.
    """
    print("INFO: Running system consistency FIX...")
    # Call the synchronous function without 'await'
    fix_report = crud.fix_consistency_issues(db=db)
    print(f"INFO: Consistency fix completed. Fixed {len(fix_report.fixed_slots)} slots and {len(fix_report.fixed_counters)} counters.")
    return fix_report

# Remember to include this router in app/main.py