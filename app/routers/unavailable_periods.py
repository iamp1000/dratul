# app/routers/unavailable_periods.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from .. import crud, schemas, security, models
from ..database import get_db

router = APIRouter(
    prefix="/unavailable-periods",
    tags=["Unavailable Periods"],
    dependencies=[Depends(security.get_current_user)],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.UnavailablePeriodResponse, status_code=status.HTTP_201_CREATED)
def create_unavailable_period(
    period: schemas.UnavailablePeriodCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Create a new unavailable period for a location.
    """
    return crud.create_unavailable_period(db=db, period=period, created_by=current_user.id)

@router.get("/{location_id}", response_model=List[schemas.UnavailablePeriodResponse])
def read_unavailable_periods(
    location_id: int,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db)
):
    """
    Retrieve unavailable periods for a given location and date range.
    """
    return crud.get_unavailable_periods(db=db, location_id=location_id, start_date=start_date, end_date=end_date)

# Removed duplicate emergency_block_day definition below.

@router.post("/emergency-block", response_model=List[schemas.AppointmentResponse])
@router.put("/{period_id}", response_model=schemas.UnavailablePeriodResponse)
def update_unavailable_period_route(
    period_id: int,
    period_update: schemas.UnavailablePeriodUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Update an existing unavailable period.
    """
    db_period = crud.update_unavailable_period(db=db, period_id=period_id, period_update=period_update)
    if db_period is None:
        raise HTTPException(status_code=404, detail="Unavailable period not found")
    return db_period

@router.delete("/{period_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_unavailable_period_route(
    period_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Delete an unavailable period.
    """
    success = crud.delete_unavailable_period(db=db, period_id=period_id)
    if not success:
        raise HTTPException(status_code=404, detail="Unavailable period not found")
    return

@router.post("/emergency-block", response_model=List[schemas.AppointmentResponse])
async def emergency_block_day(
    block_data: schemas.EmergencyBlockCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Cancel all appointments for a given day and mark it as unavailable.
    This is an emergency feature and will notify patients.
    """
    try:
        cancelled_appointments = await crud.emergency_cancel_appointments(
            db=db, 
            block_date=block_data.block_date, 
            reason=block_data.reason, 
            user_id=current_user.id
        )
        return cancelled_appointments
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))