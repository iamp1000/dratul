# app/routers/slots.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import date, datetime, time, timezone, timedelta
from .. import crud
from ..services import slot_service
from .. import schemas, models # Import models for user dependency
from ..database import get_db
from ..security import get_current_user # Assuming authentication is needed
from ..models import SlotStatus, UserRole # Import enums

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
    Retrieve available appointment slots for a given location and date (processed in IST).
    Returns a list of AppointmentSlot objects.
    """
    try:
        # --- 1. Calculate IST Date Range (REQUIRED for filtering all slots) ---
        IST = timezone(timedelta(hours=5, minutes=30))
        day_start_ist = datetime.combine(target_date, time.min).replace(tzinfo=IST)
        day_end_ist = datetime.combine(target_date, time.max).replace(tzinfo=IST)

        # 2. First, try to get existing slots. Eagerly load location to get timezone for client-side display.
        available_slots_query = db.query(models.AppointmentSlot).options(joinedload(models.AppointmentSlot.location)).filter(
            models.AppointmentSlot.location_id == location_id,
            models.AppointmentSlot.start_time >= day_start_ist,
            models.AppointmentSlot.start_time <= day_end_ist
        ).order_by(models.AppointmentSlot.start_time)
        
        available_slots = available_slots_query.all()

        # 3. If no slots exist, and the date is in the future, generate them Just-In-Time (JIT)
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

            # 4. Check if this day is blocked by an UnavailablePeriod (variables already defined in step 1)
            is_blocked = db.query(models.UnavailablePeriod).filter(
                models.UnavailablePeriod.location_id == location_id,
                models.UnavailablePeriod.start_datetime < day_end_ist,
                models.UnavailablePeriod.end_datetime > day_start_ist
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
                # Re-fetch the newly created slots AFTER commit
                # We must re-run the query to get the slots with their generated IDs and relationships
                refetched_slots = available_slots_query.all()
                # Add location timezone to each slot before returning
                for slot in refetched_slots:
                    if slot.location:
                        setattr(slot, 'location_timezone', slot.location.timezone)
                    else:
                        setattr(slot, 'location_timezone', "Asia/Kolkata") # Fallback
                return refetched_slots
            else:
                return [] # Generation produced no slots

        # Add location timezone to each slot before returning
        for slot in available_slots:
            if slot.location:
                slot.location_timezone = slot.location.timezone # Populate the schema field
            else:
                slot.location_timezone = "Asia/Kolkata" # Fallback if location isn't loaded

        return available_slots # Return the originally found slots
    except Exception as e:
        # Log the error for debugging
        print(f"ERROR fetching slots for {location_id} on {target_date}: {e}")
        # Return a generic error to the client
        raise HTTPException(
            status_code=500,
            detail="An error occurred while fetching available slots."
        )

# --- NEW: API Endpoints for Emergency Blocking and Slot Updates ---

@router.post("/{location_id}/emergency-block", status_code=status.HTTP_200_OK)
def emergency_block_slots(
    location_id: int,
    block_data: schemas.EmergencyBlockCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Create an 'emergency_block' for all available slots on a specific date.
    This also creates a corresponding UnavailablePeriod to block the calendar.
    """
    # Only admin/manager/staff roles can perform this action
    if current_user.role not in [UserRole.admin, UserRole.manager, UserRole.staff, UserRole.receptionist, UserRole.doctor]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action."
        )

    print(f"User {current_user.username} initiating emergency block for {block_data.block_date} at loc {location_id}")

    # FIX: Use IST directly for emergency block calculations
    IST = timezone(timedelta(hours=5, minutes=30))
    start_of_day_ist = datetime.combine(block_data.block_date, time.min).replace(tzinfo=IST)
    end_of_day_ist = datetime.combine(block_data.block_date, time.max).replace(tzinfo=IST)

    try:
        # 1. Find all slots that are 'available' for this day and location (using IST)
        slots_to_block = db.query(models.AppointmentSlot).filter(
            models.AppointmentSlot.location_id == location_id,
            models.AppointmentSlot.start_time >= start_of_day_ist,
            models.AppointmentSlot.start_time <= end_of_day_ist,
            models.AppointmentSlot.status == SlotStatus.available
        ).with_for_update().all()

        if not slots_to_block:
            print("No available slots found to block.")

        # 2. Update their status to 'emergency_block'
        for slot in slots_to_block:
            slot.status = SlotStatus.emergency_block
            db.add(slot)
        
        print(f"Marked {len(slots_to_block)} slots as emergency_block.")

        # 3. Create a corresponding UnavailablePeriod to block the calendar
        # Check if one already exists for this exact time/reason to avoid duplicates (using IST)
        existing_period = db.query(models.UnavailablePeriod).filter(
            models.UnavailablePeriod.location_id == location_id,
            models.UnavailablePeriod.start_datetime == start_of_day_ist,
            models.UnavailablePeriod.end_datetime == end_of_day_ist,
            models.UnavailablePeriod.reason_type == "emergency"
        ).first()

        if not existing_period:
            unavailable_period_schema = schemas.UnavailablePeriodCreate(
                location_id=location_id,
                start_datetime=start_of_day_ist,
                end_datetime=end_of_day_ist,
                reason=block_data.reason,
                reason_type="emergency"
            )
            crud.create_unavailable_period(db=db, period=unavailable_period_schema, created_by=current_user.id)
            print(f"Created corresponding UnavailablePeriod for emergency block.")
        else:
            print("UnavailablePeriod for this emergency block already exists.")

        # 4. Add Audit Log
        crud.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=models.AuditAction.EMERGENCY_BLOCK_SLOTS,
            category="SLOTS",
            severity="WARN",
            resource_id=location_id,
            details=f"User emergency blocked {len(slots_to_block)} slots for {block_data.block_date} at loc {location_id}. Reason: {block_data.reason}"
        )

        db.commit()
        return {"message": f"Successfully blocked {len(slots_to_block)} slots for {block_data.block_date}."}

    except Exception as e:
        db.rollback()
        print(f"ERROR during emergency block: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal error occurred: {e}"
        )

@router.put("/{slot_id}/capacity", response_model=schemas.AppointmentSlot)
def update_slot_capacity(
    slot_id: int,
    capacity: int = Depends(lambda capacity: int(capacity)), # Simple way to get a single int value
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Update the 'max_strict_capacity' for a single slot (for contingencies).
    """
    # Only admin/manager/staff roles can perform this action
    if current_user.role not in [UserRole.admin, UserRole.manager, UserRole.staff, UserRole.receptionist, UserRole.doctor]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action."
        )
    
    if capacity < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Capacity cannot be negative."
        )

    try:
        target_slot = db.query(models.AppointmentSlot).filter(
            models.AppointmentSlot.id == slot_id
        ).with_for_update().first()

        if not target_slot:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")

        old_capacity = target_slot.max_strict_capacity
        target_slot.max_strict_capacity = capacity

        # Re-evaluate slot status based on new capacity
        if target_slot.current_strict_appointments < target_slot.max_strict_capacity:
            # If it was 'booked' (full) but now has space, make it 'available'
            if target_slot.status == SlotStatus.booked:
                target_slot.status = SlotStatus.available
        elif target_slot.current_strict_appointments >= target_slot.max_strict_capacity:
             # If it now has no space, mark it 'booked' (full)
            if target_slot.status == SlotStatus.available:
                target_slot.status = SlotStatus.booked

        db.add(target_slot)
        
        crud.create_audit_log(
            db=db,
            user_id=current_user.id,
            action=models.AuditAction.UPDATE,
            category="SLOTS",
            resource_id=slot_id,
            details=f"User updated slot capacity from {old_capacity} to {capacity}. Status is now {target_slot.status.value}",
            old_values={"max_strict_capacity": old_capacity},
            new_values={"max_strict_capacity": capacity}
        )
        
        db.commit()
        db.refresh(target_slot)
        return target_slot

    except Exception as e:
        db.rollback()
        print(f"ERROR during slot capacity update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal error occurred: {e}"
        )


# Remember to include this router in your main FastAPI app (app/main.py)