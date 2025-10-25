# app/routers/slots.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date, datetime, time, timezone, timedelta
from .. import crud
from ..services import slot_service
from .. import schemas, models # Import models for user dependency
from ..database import get_db
from ..security import get_current_user # Assuming authentication is needed

router = APIRouter(
    prefix="/slots",
    tags=["slots"],
    dependencies=[Depends(get_current_user)], # Apply authentication
    responses={404: {"description": "Not found"}},
)

@router.get("/{location_id}/{target_date}", response_model=List[schemas.AppointmentSlot])
def get_available_slots(
    location_id: int,
    target_date: date,
    db: Session = Depends(get_db)
):
    """
    Retrieve available appointment slots for a given location and date.
    Returns a list of AppointmentSlot objects.
    """
    try:
        # 1. First, try to get existing slots
        available_slots = slot_service.get_available_slots_for_day(
            db=db,
            location_id=location_id,
            target_date=target_date
        )

        # 2. If no slots exist, and the date is in the future, generate them Just-In-Time (JIT)
        if not available_slots and target_date >= date.today():
            print(f"No slots found for {target_date}. Attempting JIT generation...")
            
            # 3. Find the schedule rule for this day
            day_of_week = target_date.weekday() # Monday is 0, Sunday is 6
            target_schedule = db.query(models.LocationSchedule).filter(
                models.LocationSchedule.location_id == location_id,
                models.LocationSchedule.day_of_week == day_of_week,
                models.LocationSchedule.is_available == True
            ).first()

            if not target_schedule:
                print(f"No schedule found for Loc {location_id} on day {day_of_week}. Returning empty list.")
                return []

            # 4. Check if this day is blocked by an UnavailablePeriod
            IST = timezone(timedelta(hours=5, minutes=30))
            day_start_utc = datetime.combine(target_date, time.min).replace(tzinfo=IST).astimezone(timezone.utc)
            day_end_utc = datetime.combine(target_date, time.max).replace(tzinfo=IST).astimezone(timezone.utc)
            is_blocked = db.query(models.UnavailablePeriod).filter(
                models.UnavailablePeriod.location_id == location_id,
                models.UnavailablePeriod.start_datetime < day_end_utc,
                models.UnavailablePeriod.end_datetime > day_start_utc
            ).first()

            if is_blocked:
                print(f"Date {target_date} is blocked by unavailable period {is_blocked.id}. Returning empty list.")
                return []

            # 5. Generate, save, and return the new slots
            print(f"JIT: Generating new slots for {target_date} based on schedule {target_schedule.id}")
            new_slots_orm = slot_service.generate_slots_for_schedule_day(db, target_schedule, target_date)
            
            if new_slots_orm:
                db.add_all(new_slots_orm)
                db.commit()
                print(f"JIT: Committed {len(new_slots_orm)} new slots.")
                # Re-fetch to be safe, now that they are committed
                return slot_service.get_available_slots_for_day(
                    db=db,
                    location_id=location_id,
                    target_date=target_date
                )
            else:
                return [] # Generation produced no slots

        return available_slots # Return the originally found slots
    except Exception as e:
        # Log the error for debugging
        print(f"ERROR fetching slots for {location_id} on {target_date}: {e}")
        # Return a generic error to the client
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching available slots."
        )

# Remember to include this router in your main FastAPI app (app/main.py)