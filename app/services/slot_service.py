# app/services/slot_service.py
from sqlalchemy.orm import Session
from datetime import date, datetime, time, timedelta, timezone
from typing import List, Optional

from .. import models, schemas
from .. import config # Import config from app directory
from .. import crud # Import crud for logging

def generate_slots_for_schedule_day(db: Session, schedule: models.LocationSchedule, target_date: date) -> List[models.AppointmentSlot]:
    """
    Generates AppointmentSlot records for a specific date based on a LocationSchedule.
    Does NOT commit the transaction. Returns a list of ORM objects to be added.
    """
    print(f"--- JIT Generating slots for Location {schedule.location_id}, Date: {target_date}, Schedule ID: {schedule.id} ---")

    if not schedule.is_available:
        print(f"Schedule ID {schedule.id} is not available for {target_date}. Skipping slot generation.")
        return []

    # Get schedule times and duration
    start_time_obj = schedule.start_time
    end_time_obj = schedule.end_time
    duration = schedule.appointment_duration # This should be set from the schedule UI
    max_slots = schedule.max_appointments # Get the max appointments

    # --- DEBUGGING LOG ---
    print(f"DEBUG [JIT]: Generating slots with: Start={start_time_obj}, End={end_time_obj}, Duration={duration}, MaxSlots={max_slots}")
    # --- END DEBUGGING LOG ---

    if not duration or duration <= 0:
        # Fallback if duration is missing or invalid on the schedule
        print(f"Warning: Invalid duration ({duration}) on schedule {schedule.id}. Using default 15 mins.")
        duration = 15 # Default fallback

    # Combine date with time objects, assuming schedule times are naive (local timezone)
    IST = timezone(timedelta(hours=5, minutes=30))
    local_tz = IST # All naive schedule times are assumed to be in IST
    
    current_dt_naive = datetime.combine(target_date, start_time_obj)
    end_dt_naive = datetime.combine(target_date, end_time_obj)

    # Ensure start/end are timezone-aware
    current_dt = current_dt_naive.replace(tzinfo=local_tz)
    end_dt = end_dt_naive.replace(tzinfo=local_tz)

    # Convert to UTC for database storage
    current_dt_utc = current_dt.astimezone(timezone.utc)
    end_dt_utc = end_dt.astimezone(timezone.utc)

    slots_to_add = []
    slot_count = 0

    while current_dt_utc < end_dt_utc and (not max_slots or slot_count < max_slots):
        slot_end_dt_utc = current_dt_utc + timedelta(minutes=duration)

        if slot_end_dt_utc > end_dt_utc:
            print(f"Slot ending at {slot_end_dt_utc} exceeds schedule end time {end_dt_utc}. Stopping generation.")
            break

        # Check for existing slot (should not happen if JIT is called correctly, but good for safety)
        existing_slot = db.query(models.AppointmentSlot).filter(
            models.AppointmentSlot.location_id == schedule.location_id,
            models.AppointmentSlot.start_time == current_dt_utc
        ).first()

        if existing_slot:
            print(f"Slot already exists for {schedule.location_id} at {current_dt_utc}. Skipping.")
        else:
            new_slot = models.AppointmentSlot(
                location_id=schedule.location_id,
                start_time=current_dt_utc,
                end_time=slot_end_dt_utc,
                status=models.SlotStatus.available
            )
            slots_to_add.append(new_slot)
            slot_count += 1
            print(f"Prepared JIT slot: Loc {schedule.location_id}, Start {current_dt_utc}, End {slot_end_dt_utc}")

        # Move to the next slot start time
        current_dt_utc = slot_end_dt_utc
        
    return slots_to_add # Return the list of ORM objects


# --- Functions for Deleting/Updating Slots based on UnavailablePeriods ---
def delete_slots_for_period(db: Session, location_id: int, start_dt_utc: datetime, end_dt_utc: datetime):
    """
    Deletes AppointmentSlot records within a given UTC datetime range for a location.
    Does NOT commit the transaction.
    """
    print(f"--- Deleting slots for Location {location_id} between {start_dt_utc} and {end_dt_utc} ---")
    
    # Find slots that *overlap* with the unavailable period
    # A slot overlaps if: slot.start < period.end AND slot.end > period.start
    slots_to_delete = db.query(models.AppointmentSlot).filter(
        models.AppointmentSlot.location_id == location_id,
        models.AppointmentSlot.start_time < end_dt_utc,
        models.AppointmentSlot.end_time > start_dt_utc,
        # --- FIX: Ensure we do NOT delete booked OR emergency_block slots during regeneration ---
        ~models.AppointmentSlot.status.in_([models.SlotStatus.booked, models.SlotStatus.emergency_block])
    ).all()

    if not slots_to_delete:
        print("No available/unavailable slots found in the specified period to delete.")
        return 0

    count = 0
    for slot in slots_to_delete:
        print(f"Marking slot for deletion: ID {slot.id}, Start {slot.start_time}")
        db.delete(slot)
        count += 1
        
    print(f"Marked {count} slots for deletion in session for Location {location_id}.")
    return count


# --- Function for Regenerating Slots (SMART RECONCILIATION) ---
def regenerate_slots_for_location(db: Session, location_id: int, start_date: date, end_date: date, weekly_schedules: List[models.LocationSchedule]):
    """
    REWRITTEN: Smartly reconciles future slots for a location based on new schedule rules.
    - Deletes 'available'/'emergency_block' slots that are no longer in schedule.
    - Creates new 'available' slots that are missing.
    - DOES NOT touch 'booked' slots.
    """
    print(f"--- SMART RECONCILIATION for Loc {location_id} from {start_date} to {end_date} ---")
    
    # --- Log Start ---
    try:
        crud.create_audit_log(
            db=db, user_id=None, action="Started Slot Reconciliation", category="SLOTS",
            resource_type="LocationSchedule", resource_id=location_id,
            details=f"System started smart reconciliation for location {location_id} from {start_date} to {end_date}."
        )
    except Exception as log_error:
        print(f"ERROR: Failed to create audit log for start of slot reconciliation: {log_error}")
    # --- End Log ---

    schedules_by_day = {sch.day_of_week: sch for sch in weekly_schedules}
    IST = timezone(timedelta(hours=5, minutes=30))
    
    # Get all unavailable periods in the entire range for this location (as UTC datetimes)
    range_start_utc = datetime.combine(start_date, time.min).replace(tzinfo=IST).astimezone(timezone.utc)
    range_end_utc = datetime.combine(end_date, time.max).replace(tzinfo=IST).astimezone(timezone.utc)
    
    unavailable_periods = db.query(models.UnavailablePeriod).filter(
        models.UnavailablePeriod.location_id == location_id,
        models.UnavailablePeriod.start_datetime <= range_end_utc,
        models.UnavailablePeriod.end_datetime >= range_start_utc
    ).all()

    current_date = start_date
    total_created = 0
    total_deleted = 0

    try:
        while current_date <= end_date:
            day_of_week = current_date.weekday() # Monday is 0, Sunday is 6
            target_schedule = schedules_by_day.get(day_of_week)

            # 1. Check if this specific day is blocked
            is_blocked = False
            day_start_utc = datetime.combine(current_date, time.min).replace(tzinfo=IST).astimezone(timezone.utc)
            day_end_utc = datetime.combine(current_date, time.max).replace(tzinfo=IST).astimezone(timezone.utc)

            for period in unavailable_periods:
                if period.start_datetime < day_end_utc and period.end_datetime > day_start_utc:
                    is_blocked = True
                    break
            
            # 2. Get all existing slots for this day (any status)
            existing_slots_for_day = db.query(models.AppointmentSlot).filter(
                models.AppointmentSlot.location_id == location_id,
                models.AppointmentSlot.start_time >= day_start_utc,
                models.AppointmentSlot.start_time <= day_end_utc
            ).all()
            
            existing_slots_map = {slot.start_time: slot for slot in existing_slots_for_day}
            ideal_start_times_utc = set()
            slot_duration_minutes = 15 # Default

            # 3. Case A: Day is Available in schedule AND not blocked
            if target_schedule and target_schedule.is_available and not is_blocked:
                # --- Calculate Ideal Slots --- 
                start_time_obj = target_schedule.start_time
                end_time_obj = target_schedule.end_time
                duration = target_schedule.appointment_duration
                max_slots = target_schedule.max_appointments

                if not duration or duration <= 0:
                    duration = 15 # Fallback
                slot_duration_minutes = duration # Store for later use
                
                current_dt_naive = datetime.combine(current_date, start_time_obj)
                end_dt_naive = datetime.combine(current_date, end_time_obj)
                
                # THIS IS THE FIX: We must use the correct timezone (IST) for schedule times
                current_dt_local = current_dt_naive.replace(tzinfo=IST)
                end_dt_local = end_dt_naive.replace(tzinfo=IST)

                current_dt_utc = current_dt_local.astimezone(timezone.utc)
                end_dt_utc = end_dt_local.astimezone(timezone.utc)
                
                print(f"DEBUG [{current_date}]: Generating slots. Rule: {start_time_obj}-{end_time_obj} (IST). Max: {max_slots}. -> UTC Range: {current_dt_utc} to {end_dt_utc}")

                slot_count = 0
                while current_dt_utc < end_dt_utc and (not max_slots or slot_count < max_slots):
                    slot_end_dt_utc = current_dt_utc + timedelta(minutes=duration)
                    if slot_end_dt_utc > end_dt_utc:
                        break
                    
                    ideal_start_times_utc.add(current_dt_utc)
                    slot_count += 1
                    current_dt_utc = slot_end_dt_utc
                # --- End Ideal Slot Calculation ---

            # 4. Reconcile: Delete old/invalid slots, Create new slots
            
            # Delete slots that are 'available' or 'emergency_block' but are NO LONGER in the ideal list
            for slot_start_time, slot in existing_slots_map.items():
                if slot.status in [models.SlotStatus.available, models.SlotStatus.emergency_block, models.SlotStatus.unavailable]:
                    if slot_start_time not in ideal_start_times_utc:
                        print(f"Reconciling: Deleting slot {slot.id} ({slot.start_time}) on {current_date} as it's no longer in schedule.")
                        db.delete(slot)
                        total_deleted += 1

            # Create slots that are in the ideal list but DO NOT exist in the DB
            for ideal_start in ideal_start_times_utc:
                if ideal_start not in existing_slots_map:
                    # Create it
                    new_slot = models.AppointmentSlot(
                        location_id=location_id,
                        start_time=ideal_start,
                        end_time=ideal_start + timedelta(minutes=slot_duration_minutes),
                        status=models.SlotStatus.available
                    )
                    db.add(new_slot)
                    total_created += 1
                    print(f"Reconciling: Creating missing slot for {ideal_start} on {current_date}.")

            current_date += timedelta(days=1)
        
        # 5. Commit all changes at the end
        db.commit()
        print(f"Reconciliation complete: {total_created} slots created, {total_deleted} slots deleted.")

        # --- Log Completion --- 
        try:
            crud.create_audit_log(
                db=db, user_id=None, action="Finished Slot Reconciliation", category="SLOTS",
                details=f"System reconciliation complete for loc {location_id}: {total_created} created, {total_deleted} deleted."
            )
        except Exception as log_error:
            print(f"ERROR: Failed to create audit log for end of slot reconciliation: {log_error}")
        # --- End Log ---

    except Exception as e:
        db.rollback()
        print(f"Error during slot reconciliation: {e}")
        try:
             crud.create_audit_log(
                db=db, user_id=None, action="Failed Slot Reconciliation", category="SLOTS", severity="ERROR",
                details=f"System reconciliation FAILED for loc {location_id}: {e}"
            )
        except Exception: pass # Avoid error in error handler
        raise

    return {"status": "success", "total_generated": total_created, "total_deleted": total_deleted}


# --- Functions for Regenerating Slots ---
def get_available_slots_for_day(db: Session, location_id: int, target_date: date) -> List[models.AppointmentSlot]:
    """
    Retrieves all AppointmentSlot records for a given location and date
    with the status 'available', ordered by start time.
    """
    print(f"--- Fetching available slots for Location {location_id} on {target_date} ---")

    # Define the start and end of the target date in UTC
    start_dt_utc = datetime.combine(target_date, time.min).replace(tzinfo=timezone.utc)
    end_dt_utc = datetime.combine(target_date, time.max).replace(tzinfo=timezone.utc)

    available_slots = db.query(models.AppointmentSlot).filter(
        models.AppointmentSlot.location_id == location_id,
        models.AppointmentSlot.start_time >= start_dt_utc,
        models.AppointmentSlot.start_time <= end_dt_utc, # Check start_time is within the day
        models.AppointmentSlot.status == models.SlotStatus.available
    ).order_by(models.AppointmentSlot.start_time).all()

    print(f"Found {len(available_slots)} available slots.")
    return available_slots

# (To be added later)

from sqlalchemy import func as sql_func # Alias func to avoid conflict

# --- Service function to get available slots for API ---
# (To be added later)