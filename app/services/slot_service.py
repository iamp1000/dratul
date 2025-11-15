# app/services/slot_service.py
# FINAL IST-ONLY VERSION
from sqlalchemy.orm import Session
from datetime import date, datetime, time, timedelta, timezone
from typing import List, Optional

from .. import models, schemas
from .. import config  # Import config from app directory
from .. import crud  # Import crud for logging


def generate_slots_for_schedule_day(db: Session, schedule: models.LocationSchedule, target_date: date) -> List[models.AppointmentSlot]:
    print(f"--- JIT Generating slots for Location {schedule.location_id}, Date: {target_date}, Schedule ID: {schedule.id} (IST) ---")

    if not schedule.is_available:
        print(f"Schedule ID {schedule.id} is not available for {target_date}. Skipping slot generation.")
        return []

    # Get schedule times and duration
    start_time_obj = schedule.start_time
    end_time_obj = schedule.end_time
    duration = schedule.appointment_duration  # This should be set from the schedule UI
    max_slots = schedule.max_appointments  # Get the max appointments

    print(f"DEBUG [JIT]: Generating slots with: Start={start_time_obj}, End={end_time_obj}, Duration={duration}, MaxSlots={max_slots}")

    if not duration or duration <= 0:
        print(f"Warning: Invalid duration ({duration}) on schedule {schedule.id}. Using default 15 mins.")
        duration = 15  # Default fallback

    # --- FINAL FIX: Force all storage and processing to use IST (UTC+5:30) ---
    IST = timezone(timedelta(hours=5, minutes=30))
    local_tz = IST  # All naive schedule times are assumed to be in IST

    current_dt_naive = datetime.combine(target_date, start_time_obj)
    end_dt_naive = datetime.combine(target_date, end_time_obj)

    # Ensure start/end are timezone-aware IST for database storage and loop
    current_dt_ist = current_dt_naive.replace(tzinfo=local_tz)
    end_dt_ist = end_dt_naive.replace(tzinfo=local_tz)

    current_dt_loop = current_dt_ist
    end_dt_loop = end_dt_ist

    slots_to_add = []
    slot_count = 0

    while current_dt_loop < end_dt_loop and (not max_slots or slot_count < max_slots):
        slot_end_dt_ist = current_dt_loop + timedelta(minutes=duration)

        if slot_end_dt_ist > end_dt_loop:
            print(f"Slot ending at {slot_end_dt_ist} exceeds schedule end time {end_dt_loop}. Stopping generation.")
            break

        existing_slot = db.query(models.AppointmentSlot).filter(
            models.AppointmentSlot.location_id == schedule.location_id,
            models.AppointmentSlot.start_time == current_dt_loop  # Compare using IST
        ).first()

        if existing_slot:
            print(f"Slot already exists for {schedule.location_id} at {current_dt_loop}. Skipping.")
        else:
            slot_capacity = schedule.max_appointments if schedule.max_appointments and schedule.max_appointments > 0 else 1
            new_slot = models.AppointmentSlot(
                location_id=schedule.location_id,
                start_time=current_dt_loop,  # Store IST
                end_time=slot_end_dt_ist,  # Store IST
                status=models.SlotStatus.available,
                max_strict_capacity=slot_capacity,
                current_strict_appointments=0
            )
            slots_to_add.append(new_slot)
            slot_count += 1
            print(f"Prepared JIT slot: Loc {schedule.location_id}, Start {current_dt_loop}, End {slot_end_dt_ist}")

        current_dt_loop = slot_end_dt_ist

    return slots_to_add


def delete_slots_for_period(db: Session, location_id: int, start_dt_ist: datetime, end_dt_ist: datetime):
    """
    Deletes AppointmentSlot records within a given IST datetime range for a location.
    Does NOT commit the transaction.
    """
    print(f"--- Deleting slots for Location {location_id} between {start_dt_ist} and {end_dt_ist} (IST) ---")

    slots_to_delete = db.query(models.AppointmentSlot).filter(
        models.AppointmentSlot.location_id == location_id,
        models.AppointmentSlot.start_time < end_dt_ist,  # Compare using IST
        models.AppointmentSlot.end_time > start_dt_ist,  # Compare using IST
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


def regenerate_slots_for_location(db: Session, location_id: int, start_date: date, end_date: date, weekly_schedules: List[models.LocationSchedule], user_id: Optional[int] = None):
    """
    REWRITTEN: Smartly reconciles future slots for a location based on new schedule rules (using IST).
    - Deletes 'available'/'emergency_block'/'unavailable' slots that are no longer in schedule.
    - Creates new 'available' slots that are missing.
    - DOES NOT touch 'booked' slots.
    """
    print(f"--- SMART RECONCILIATION for Loc {location_id} from {start_date} to {end_date} (IST) ---")

    try:
        crud.create_audit_log(db=db, user_id=user_id, action="Started Slot Reconciliation", category="SLOTS", details=f"Started slot reconciliation for location ID {location_id} from {start_date} to {end_date}.")
    except Exception as log_error:
        print(f"ERROR: Failed to create audit log for start of slot reconciliation: {log_error}")

    schedules_by_day = {sch.day_of_week: sch for sch in weekly_schedules}
    IST = timezone(timedelta(hours=5, minutes=30))

    # --- FINAL FIX: Use IST for all range calculations ---
    range_start_ist = datetime.combine(start_date, time.min).replace(tzinfo=IST)
    range_end_ist = datetime.combine(end_date, time.max).replace(tzinfo=IST)

    unavailable_periods = db.query(models.UnavailablePeriod).filter(
        models.UnavailablePeriod.location_id == location_id,
        models.UnavailablePeriod.start_datetime <= range_end_ist,  # Compare using IST
        models.UnavailablePeriod.end_datetime >= range_start_ist  # Compare using IST
    ).all()

    current_date = start_date
    total_created = 0
    total_deleted = 0

    try:
        while current_date <= end_date:
            day_of_week = current_date.weekday()
            target_schedule = schedules_by_day.get(day_of_week)

            # --- FINAL FIX: Use IST for daily range checks ---
            day_start_ist = datetime.combine(current_date, time.min).replace(tzinfo=IST)
            day_end_ist = datetime.combine(current_date, time.max).replace(tzinfo=IST)
            is_blocked = False
            for period in unavailable_periods:
                # Ensure period times are timezone-aware before comparison if necessary
                period_start = period.start_datetime
                period_end = period.end_datetime
                if period_start.tzinfo is None: period_start = period_start.replace(tzinfo=IST)  # Assume IST if naive
                if period_end.tzinfo is None: period_end = period_end.replace(tzinfo=IST)  # Assume IST if naive

                if period_start < day_end_ist and period_end > day_start_ist:
                    is_blocked = True
                    break

            # --- FINAL FIX: Use IST for fetching existing slots ---
            existing_slots_for_day = db.query(models.AppointmentSlot).filter(
                models.AppointmentSlot.location_id == location_id,
                models.AppointmentSlot.start_time >= day_start_ist,
                models.AppointmentSlot.start_time <= day_end_ist
            ).all()

            existing_slots_map = {slot.start_time: slot for slot in existing_slots_for_day}
            ideal_start_times_ist = set()
            slot_duration_minutes = 15  # Default
            slot_capacity = 1  # Default fallback

            if target_schedule and target_schedule.is_available and not is_blocked:
                start_time_obj = target_schedule.start_time
                end_time_obj = target_schedule.end_time
                duration = target_schedule.appointment_duration
                max_slots = target_schedule.max_appointments

                if not duration or duration <= 0:
                    duration = 15  # Fallback
                slot_duration_minutes = duration
                slot_capacity = max_slots if max_slots and max_slots > 0 else 1

                current_dt_naive = datetime.combine(current_date, start_time_obj)
                end_dt_naive = datetime.combine(current_date, end_time_obj)

                # --- FINAL FIX: Use timezone-aware IST directly for loop ---
                current_dt_ist_loop = current_dt_naive.replace(tzinfo=IST)
                end_dt_ist_loop = end_dt_naive.replace(tzinfo=IST)

                print(f"DEBUG [{current_date}]: Generating slots. Rule: {start_time_obj}-{end_time_obj} (IST). Max: {max_slots}. -> IST Range: {current_dt_ist_loop} to {end_dt_ist_loop}")

                slot_count = 0
                while current_dt_ist_loop < end_dt_ist_loop and (not max_slots or slot_count < max_slots):
                    slot_end_dt_ist_loop = current_dt_ist_loop + timedelta(minutes=duration)
                    if slot_end_dt_ist_loop > end_dt_ist_loop:
                        break
                    ideal_start_times_ist.add(current_dt_ist_loop)
                    slot_count += 1
                    current_dt_ist_loop = slot_end_dt_ist_loop

            # Reconcile using IST times
            for slot_start_time, slot in existing_slots_map.items():
                if slot.status in [models.SlotStatus.available, models.SlotStatus.emergency_block, models.SlotStatus.unavailable]:
                    if slot_start_time not in ideal_start_times_ist:
                        print(f"Reconciling: Deleting slot {slot.id} ({slot.start_time}) on {current_date} as it's no longer in schedule.")
                        db.delete(slot)
                        total_deleted += 1

            for ideal_start in ideal_start_times_ist:
                if ideal_start not in existing_slots_map:
                    new_slot = models.AppointmentSlot(
                        location_id=location_id,
                        start_time=ideal_start,  # Store IST
                        end_time=ideal_start + timedelta(minutes=slot_duration_minutes),  # Store IST
                        status=models.SlotStatus.available,
                        max_strict_capacity=slot_capacity,
                        current_strict_appointments=0
                    )
                    db.add(new_slot)
                    total_created += 1
                    print(f"Reconciling: Creating missing slot for {ideal_start} on {current_date}.")

            current_date += timedelta(days=1)

        db.commit()
        print(f"Reconciliation complete: {total_created} slots created, {total_deleted} slots deleted.")

        try:
            crud.create_audit_log(db=db, user_id=user_id, action="Finished Slot Reconciliation", category="SLOTS", details=f"Finished slot reconciliation for location ID {location_id}: {total_created} slots created, {total_deleted} slots deleted.")
        except Exception as log_error:
            print(f"ERROR: Failed to create audit log for end of slot reconciliation: {log_error}")

    except Exception as e:
        db.rollback()
        print(f"Error during slot reconciliation: {e}")
        try:
            crud.create_audit_log(db=db, user_id=user_id, action="Failed Slot Reconciliation", category="SLOTS", severity="ERROR", details=f"Slot reconciliation failed for location ID {location_id}. Error: {str(e)}")
        except Exception:
            pass
        raise

    return {"status": "success", "total_generated": total_created, "total_deleted": total_deleted}


def get_available_slots_for_day(db: Session, location_id: int, target_date: date) -> List[models.AppointmentSlot]:
    """
    Retrieves all AppointmentSlot records for a given location and date
    with the status 'available', ordered by start time (in IST).
    """
    print(f"--- Fetching available slots for Location {location_id} on {target_date} (IST) ---")

    # --- FINAL FIX: Use IST for filtering ---
    IST = timezone(timedelta(hours=5, minutes=30))
    start_dt_ist = datetime.combine(target_date, time.min).replace(tzinfo=IST)
    end_dt_ist = datetime.combine(target_date, time.max).replace(tzinfo=IST)

    available_slots = db.query(models.AppointmentSlot).filter(
        models.AppointmentSlot.location_id == location_id,
        models.AppointmentSlot.start_time >= start_dt_ist,  # Filter using IST
        models.AppointmentSlot.start_time <= end_dt_ist,  # Filter using IST
        models.AppointmentSlot.status == models.SlotStatus.available
    ).order_by(models.AppointmentSlot.start_time).all()

    print(f"Found {len(available_slots)} available slots.")
    return available_slots

# Import func alias needs to be at top, but placing here for context if needed later
# from sqlalchemy import func as sql_func
