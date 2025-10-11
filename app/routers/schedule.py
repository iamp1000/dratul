# app/routers/schedule.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import crud, models, schemas
from ..database import get_db
from ..security import get_current_user

router = APIRouter(
    prefix="/schedules",
    tags=["schedules"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)

@router.get("/{location_id}", response_model=List[schemas.LocationScheduleResponse])
def read_schedules_for_location(location_id: int, db: Session = Depends(get_db)):
    """
    Retrieve all schedule entries for a specific location.
    """
    schedules = crud.get_schedules_for_location(db=db, location_id=location_id)
    if not schedules:
        return []
    return schedules

@router.post("/{location_id}", response_model=List[schemas.LocationScheduleResponse])
def update_schedules_for_location(
    location_id: int, 
    schedules: List[schemas.LocationScheduleCreate], 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Update the entire weekly schedule for a specific location.
    This will replace all existing schedule entries for the location.
    Requires admin or manager privileges.
    """
    if current_user.role not in [schemas.UserRole.admin, schemas.UserRole.manager]:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to update schedules"
        )
    
    try:
        updated_schedules = crud.update_schedules_for_location(db=db, location_id=location_id, schedules=schedules)
        return updated_schedules
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))