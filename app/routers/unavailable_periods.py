# app/routers/unavailable_periods.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date, timedelta, datetime, timezone # Added imports
from ..services import slot_service # Import slot service

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
    db_period = crud.create_unavailable_period(db=db, period=period, created_by=current_user.id)
    
    # --- Start Slot Deletion ---
    if db_period:
        try:
            # Ensure datetimes are timezone-aware UTC for the service function
            start_dt_utc = db_period.start_datetime.astimezone(timezone.utc) if db_period.start_datetime.tzinfo else db_period.start_datetime.replace(tzinfo=timezone.utc)
            end_dt_utc = db_period.end_datetime.astimezone(timezone.utc) if db_period.end_datetime.tzinfo else db_period.end_datetime.replace(tzinfo=timezone.utc)
            
            slot_service.delete_slots_for_period(
                db=db, 
                location_id=db_period.location_id, 
                start_dt_utc=start_dt_utc,
                end_dt_utc=end_dt_utc
            )
            db.commit() # Commit the slot deletions
            print(f"Successfully deleted slots for new unavailable period {db_period.id}.")
        except Exception as slot_error:
            db.rollback() # Rollback slot deletion on error
            print(f"ERROR: Failed to delete slots for new unavailable period {db_period.id}: {slot_error}")
            # Log error, potentially raise HTTPException or just log and continue
    # --- End Slot Deletion ---
            
    return db_period

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
    # --- Start Slot Regeneration on Update ---
    # 1. Get old period details BEFORE update
    old_period = crud.get_unavailable_period(db=db, period_id=period_id)
    if old_period is None:
        raise HTTPException(status_code=404, detail="Unavailable period not found")
    old_start = old_period.start_datetime
    old_end = old_period.end_datetime
    location_id = old_period.location_id
    
    # 2. Perform the update
    updated_period = crud.update_unavailable_period(db=db, period_id=period_id, period_update=period_update)
    if updated_period is None: # Should not happen if old_period existed, but safety check
        raise HTTPException(status_code=404, detail="Unavailable period not found after update attempt")
        
    # 3. Regenerate slots for the combined date range
    try:
        # Ensure datetimes are timezone-aware UTC
        old_start_utc = old_start.astimezone(timezone.utc) if old_start.tzinfo else old_start.replace(tzinfo=timezone.utc)
        old_end_utc = old_end.astimezone(timezone.utc) if old_end.tzinfo else old_end.replace(tzinfo=timezone.utc)
        new_start_utc = updated_period.start_datetime.astimezone(timezone.utc) if updated_period.start_datetime.tzinfo else updated_period.start_datetime.replace(tzinfo=timezone.utc)
        new_end_utc = updated_period.end_datetime.astimezone(timezone.utc) if updated_period.end_datetime.tzinfo else updated_period.end_datetime.replace(tzinfo=timezone.utc)

        # Determine the full range affected (min of starts to max of ends)
        combined_start_dt = min(old_start_utc, new_start_utc)
        combined_end_dt = max(old_end_utc, new_end_utc)
        
        # Convert back to date objects for the regeneration function
        start_date = combined_start_dt.date()
        end_date = combined_end_dt.date()

        # Fetch the current weekly schedule for the location
        full_weekly_schedule = crud.get_schedules_for_location(db=db, location_id=location_id)
        
        if full_weekly_schedule:
            slot_service.regenerate_slots_for_location(
                db=db, 
                location_id=location_id, 
                start_date=start_date, 
                end_date=end_date, 
                weekly_schedules=full_weekly_schedule
            )
            print(f"Successfully regenerated slots for location {location_id} after updating unavailable period {period_id}.")
        else:
            print(f"WARNING: Could not fetch schedule for location {location_id}. Slots not regenerated for period {period_id}.")
            db.commit() # Commit the period update even if slot regen fails
            
    except Exception as slot_error:
        # Regeneration commits/rolls back itself, but log error here
        print(f"ERROR: Failed during slot regeneration for unavailable period {period_id} update: {slot_error}")
        # Ensure the primary update is still returned
        # The transaction within regenerate_slots_for_location handles its own rollback/commit.

    # --- End Slot Regeneration on Update ---
    return updated_period

@router.delete("/{period_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_unavailable_period_route(
    period_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Delete an unavailable period.
    """
    # --- Start Slot Regeneration on Delete ---
    # 1. Get period details BEFORE deleting
    period_to_delete = crud.get_unavailable_period_by_id(db=db, period_id=period_id) # <-- FIX: Correct function name
    if period_to_delete is None:
        raise HTTPException(status_code=404, detail="Unavailable period not found")
        
    location_id = period_to_delete.location_id
    start_dt = period_to_delete.start_datetime
    end_dt = period_to_delete.end_datetime

    # 2. Perform the deletion
    success = crud.delete_unavailable_period(db=db, period_id=period_id)
    if not success:
        # This case should ideally be caught by the check above, but for safety:
        raise HTTPException(status_code=404, detail="Unavailable period not found during delete attempt")

    # 3. Regenerate slots for the affected date range if deletion was successful
    try:
        # Ensure datetimes are timezone-aware UTC and get date range
        start_dt_utc = start_dt.astimezone(timezone.utc) if start_dt.tzinfo else start_dt.replace(tzinfo=timezone.utc)
        end_dt_utc = end_dt.astimezone(timezone.utc) if end_dt.tzinfo else end_dt.replace(tzinfo=timezone.utc)
        start_date = start_dt_utc.date()
        end_date = end_dt_utc.date()

        # Fetch the current weekly schedule
        full_weekly_schedule = crud.get_schedules_for_location(db=db, location_id=location_id)

        if full_weekly_schedule:
            slot_service.regenerate_slots_for_location(
                db=db, 
                location_id=location_id, 
                start_date=start_date, 
                end_date=end_date, 
                weekly_schedules=full_weekly_schedule
            )
            print(f"Successfully regenerated slots for location {location_id} after deleting unavailable period {period_id}.")
        else:
            print(f"WARNING: Could not fetch schedule for location {location_id}. Slots not regenerated for deleted period {period_id}.")
            db.commit() # Commit the period deletion even if slot regen fails
            
    except Exception as slot_error:
        # Regeneration handles its own commit/rollback. Log error.
        print(f"ERROR: Failed during slot regeneration after deleting unavailable period {period_id}: {slot_error}")
        # Ensure deletion is committed if regeneration fails after successful delete
        if success: 
             try:
                 db.commit() # Try to commit deletion if not already done by regeneration
             except Exception as commit_err:
                 print(f"ERROR: Failed to commit deletion of period {period_id} after slot regen error: {commit_err}")
                 db.rollback()

    # --- End Slot Regeneration on Delete ---
    # No return content needed for HTTP 204
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