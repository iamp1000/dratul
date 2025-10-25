# app/routers/schedule.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date, time, timedelta # Added timedelta
from ..services import slot_service # Import slot service
from .. import crud, models, schemas
from ..database import get_db
from ..security import get_current_user
from .. import crud

router = APIRouter(
    prefix="/schedules",
    tags=["schedules"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)

@router.get("/by-location/{location_id}", response_model=List[schemas.LocationScheduleResponse])
def read_schedules_for_location(location_id: int, db: Session = Depends(get_db)):
    """
    Retrieve all schedule entries for a specific location.
    """
    schedules = crud.get_schedules_for_location(db=db, location_id=location_id)
    if not schedules:
        return []
    return schedules

@router.post("/by-location/{location_id}", response_model=List[schemas.LocationScheduleResponse])
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

        # --- Add Audit Log --- 
        try:
            crud.create_audit_log(
                db=db,
                user_id=current_user.id,
                action="Updated Weekly Schedule",
                category="SCHEDULE",
                resource_type="LocationSchedule",
                resource_id=location_id, # Log against the location ID
                details=f"User {current_user.username} updated the full weekly schedule for location ID {location_id}."
            )
        except Exception as log_error:
            print(f"ERROR: Failed to create audit log for weekly schedule update (loc {location_id}): {log_error}")
        # --- End Audit Log ---
        
        # --- Start Slot Regeneration ---
        try:
            start_date = date.today()
            end_date = start_date + timedelta(days=30) # Regenerate for the next 30 days
            slot_service.regenerate_slots_for_location(
                db=db, 
                location_id=location_id, 
                start_date=start_date, 
                end_date=end_date, 
                weekly_schedules=updated_schedules # Pass the updated ORM models
            )
            print(f"Successfully regenerated slots for location {location_id} after full schedule update.")
        except Exception as slot_error:
            # Log the error, but don't fail the request as schedule update succeeded
            print(f"ERROR: Failed to regenerate slots for location {location_id} after schedule update: {slot_error}")
            # Consider logging to a file or monitoring system here
        # --- End Slot Regeneration ---
        
        return updated_schedules
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/config")
def get_schedule_config(db: Session = Depends(get_db)):
    """Get global schedule configuration (limits and intervals)."""
    interval = crud.get_system_config(db, "appointment_interval_minutes")
    daily_limit = crud.get_system_config(db, "appointment_daily_limit")
    return {
        "appointment_interval_minutes": (interval.value if interval else 15),
        "appointment_daily_limit": (daily_limit.value if daily_limit else 2)
    }


@router.post("/config")
def set_schedule_config(
    appointment_interval_minutes: int,
    appointment_daily_limit: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Set global schedule configuration (requires admin/manager)."""
    if current_user.role not in [schemas.UserRole.admin, schemas.UserRole.manager]:
        raise HTTPException(status_code=403, detail="Not authorized to update config")
    if appointment_interval_minutes not in [10, 15, 20, 30, 60]:
        raise HTTPException(status_code=400, detail="Invalid interval")
    if appointment_daily_limit < 1 or appointment_daily_limit > 10:
        raise HTTPException(status_code=400, detail="Invalid daily limit")

    crud.set_system_config(db, "appointment_interval_minutes", appointment_interval_minutes, "integer", "Slot interval in minutes", "scheduling")
    crud.set_system_config(db, "appointment_daily_limit", appointment_daily_limit, "integer", "Daily booking limit per patient", "scheduling")
    return {"success": True}

@router.put("/{location_id}/{day_of_week}", response_model=schemas.LocationScheduleResponse)
def update_day_schedule(
    location_id: int,
    day_of_week: int,
    schedule_update: schemas.LocationScheduleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Update the schedule for a specific day of the week for a location.
    Requires admin or manager privileges.
    """
    if current_user.role not in [schemas.UserRole.admin, schemas.UserRole.manager]:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to update schedules"
        )
    
    try:
        updated_schedule = crud.update_schedule_for_day(
            db=db, 
            location_id=location_id, 
            day_of_week=day_of_week, 
            schedule_update=schedule_update
        )

        # --- Add Audit Log --- 
        try:
            day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day_of_week]
            crud.create_audit_log(
                db=db,
                user_id=current_user.id,
                action="Updated Day Schedule",
                category="SCHEDULE",
                resource_type="LocationSchedule",
                resource_id=location_id, # Log against location ID
                details=f"User {current_user.username} updated schedule for {day_name} (Day {day_of_week}) at location ID {location_id}."
            )
        except Exception as log_error:
            print(f"ERROR: Failed to create audit log for daily schedule update (loc {location_id}, day {day_of_week}): {log_error}")
        # --- End Audit Log ---
        
        # --- Start Slot Regeneration ---
        try:
            # Fetch the complete updated weekly schedule for regeneration logic
            full_weekly_schedule = crud.get_schedules_for_location(db=db, location_id=location_id)
            if full_weekly_schedule: # Ensure schedule exists
                start_date = date.today()
                end_date = start_date + timedelta(days=30) # Regenerate for the next 30 days
                slot_service.regenerate_slots_for_location(
                    db=db, 
                    location_id=location_id, 
                    start_date=start_date, 
                    end_date=end_date, 
                    weekly_schedules=full_weekly_schedule
                )
                print(f"Successfully regenerated slots for location {location_id} after updating day {day_of_week}.")
            else:
                 print(f"WARNING: Could not fetch full schedule for location {location_id} after updating day {day_of_week}. Slots not regenerated.")
                 
        except Exception as slot_error:
            # Log the error, but don't fail the request as schedule update succeeded
            print(f"ERROR: Failed to regenerate slots for location {location_id} after updating day {day_of_week}: {slot_error}")
            # Consider logging to a file or monitoring system here
        # --- End Slot Regeneration ---

        return updated_schedule
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Removed duplicate route definition above.

@router.get("/availability/{location_id}/{for_date}", response_model=List[time])
async def get_availability_for_date(
    location_id: int,
    for_date: date,
    db: Session = Depends(get_db)
):
    """
    Retrieve available appointment slots for a given location and date.
    """
    try:
        return await crud.get_available_slots(db=db, location_id=location_id, for_date=for_date)
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/availability-detailed/{location_id}/{for_date}")
async def get_availability_detailed(
    location_id: int,
    for_date: date,
    db: Session = Depends(get_db)
):
    """Return slot list with availability and reason codes for UI tooltips/colors."""
    try:
        return await crud.get_available_slots_detailed(db=db, location_id=location_id, for_date=for_date)
    except crud.CRUDError as e:
        raise HTTPException(status_code=400, detail=str(e))