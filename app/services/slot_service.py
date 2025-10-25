# app/services/slot_service.py
from sqlalchemy.orm import Session
from datetime import date, datetime, time, timedelta, timezone
from typing import List, Optional

from .. import models, schemas
from .. import config # Import config from app directory

def generate_slots_for_schedule_day(db: Session, schedule: models.LocationSchedule, target_date: date):
    """
    Generates AppointmentSlot records for a specific date based on a LocationSchedule.
    Does NOT commit the transaction.
    """
    print(f"--- Generating slots for Location {schedule.location_id}, Date: {target_date}, Schedule ID: {schedule.id} ---")

    if not schedule.is_available:
        print(f"Schedule ID {schedule.id} is not available for {target_date}. Skipping slot generation.")
        return []

    # Get schedule times and duration
    start_time_obj = schedule.start_time
    end_time_obj = schedule.end_time
    # Use default from actual config if duration is null/None on schedule
    # Assuming config.settings.DEFAULT_APPOINTMENT_DURATION exists in your app/config.py
    duration = schedule.appointment_duration if schedule.appointment_duration is not None else config.settings.DEFAULT_APPOINTMENT_DURATION 

    # Combine date with time objects, assuming schedule times are naive (local timezone)
    # TODO: Confirm timezone handling - are schedule times UTC or local? Assuming local for now.
    # We should store slots in UTC in the database.
    local_tz = timezone.utc # Placeholder - Replace with actual location timezone lookup if needed
    
    current_dt_naive = datetime.combine(target_date, start_time_obj)
    end_dt_naive = datetime.combine(target_date, end_time_obj)

    # Ensure start/end are timezone-aware (using placeholder UTC for now)
    current_dt = current_dt_naive.replace(tzinfo=local_tz)
    end_dt = end_dt_naive.replace(tzinfo=local_tz)

    # Convert to UTC for database storage
    current_dt_utc = current_dt.astimezone(timezone.utc)
    end_dt_utc = end_dt.astimezone(timezone.utc)


    slots_to_add = []
    slot_count = 0

    while current_dt_utc < end_dt_utc:
        slot_end_dt_utc = current_dt_utc + timedelta(minutes=duration)

        # Basic check to ensure slot doesn't exceed the end time
        if slot_end_dt_utc > end_dt_utc:
            print(f"Slot ending at {slot_end_dt_utc} exceeds schedule end time {end_dt_utc}. Stopping generation.")
            break

        # Check for existing slot (should ideally not happen with unique constraint, but good practice)
        # Also check against potential break times if defined in schedule model (not implemented here)
        existing_slot = db.query(models.AppointmentSlot).filter(
            models.AppointmentSlot.location_id == schedule.location_id,
            models.AppointmentSlot.start_time == current_dt_utc
        ).first()

        if existing_slot:
            print(f"Slot already exists for {schedule.location_id} at {current_dt_utc}. Skipping.")
        else:
            # TODO: Add check here for break_start/break_end from schedule model
            # if current_dt_naive.time() >= schedule.break_start and current_dt_naive.time() < schedule.break_end:
            #     print(f"Skipping slot during break time: {current_dt_naive.time()}")
            #     current_dt_utc = current_dt_utc + timedelta(minutes=duration) # Adjust next start time? Or jump to break_end?
            #     continue # Skip adding this slot
                
            new_slot = models.AppointmentSlot(
                location_id=schedule.location_id,
                start_time=current_dt_utc,
                end_time=slot_end_dt_utc,
                status=models.SlotStatus.available # Use the enum from models directly
            )
            slots_to_add.append(new_slot)
            slot_count += 1
            print(f"Prepared slot: Loc {schedule.location_id}, Start {current_dt_utc}, End {slot_end_dt_utc}")

        # Move to the next slot start time
        current_dt_utc = slot_end_dt_utc

    # Add all prepared slots to the session
    if slots_to_add:
        db.add_all(slots_to_add)
        print(f"Added {slot_count} slots to session for Location {schedule.location_id} on {target_date}.")
        
    return slots_to_add # Return the list of added ORM objects (not committed yet)


# Default duration is now expected to come from the imported app.config

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
        models.AppointmentSlot.status != models.SlotStatus.booked # Important: Do not delete booked slots automatically? Or should we? Needs policy decision.
                                                                    # Maybe change status to 'unavailable' instead of deleting?
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


# --- Function for Regenerating Slots ---
def regenerate_slots_for_location(db: Session, location_id: int, start_date: date, end_date: date, weekly_schedules: List[models.LocationSchedule]):
    """
    Deletes existing available slots and generates new slots for a location within a date range
    based on the provided weekly schedule rules. Commits the transaction.
    """
    print(f"--- Regenerating slots for Location {location_id} from {start_date} to {end_date} ---")

    # Convert start/end dates to timezone-aware UTC datetimes for boundary checks
    start_dt_utc = datetime.combine(start_date, time.min).replace(tzinfo=timezone.utc)
    # End date is inclusive, so we go to the end of that day
    end_dt_utc = datetime.combine(end_date, time.max).replace(tzinfo=timezone.utc)

    # 1. Delete existing AVAILABLE slots in the date range for this location
    try:
        num_deleted = delete_slots_for_period(db, location_id, start_dt_utc, end_dt_utc)
        print(f"Deletion phase completed. Marked {num_deleted} slots for deletion.")
        # Flush to execute deletions before adding new ones, prevents potential unique constraint issues if times overlap slightly
        db.flush()
    except Exception as e:
        db.rollback()
        print(f"Error during slot deletion phase: {e}")
        raise  # Re-raise the exception

    # 2. Generate new slots day by day
    schedules_by_day = {sch.day_of_week: sch for sch in weekly_schedules}
    current_date = start_date
    total_generated = 0
    generated_map = {} # Keep track of generated ORM objects

    try:
        while current_date <= end_date:
            day_of_week = current_date.weekday() # Monday is 0, Sunday is 6
            target_schedule = schedules_by_day.get(day_of_week)

            if target_schedule and target_schedule.is_available:
                # TODO: Check against UnavailablePeriod for this specific date before generating
                # is_unavailable = db.query(models.UnavailablePeriod).filter(...).first()
                # if is_unavailable:
                #     print(f"Date {current_date} is within an unavailable period. Skipping slot generation.")
                #     current_date += timedelta(days=1)
                #     continue

                generated_slots = generate_slots_for_schedule_day(db, target_schedule, current_date)
                generated_map[current_date] = generated_slots # Store ORM objects
                total_generated += len(generated_slots)
            else:
                print(f"No schedule or schedule not available for Location {location_id} on {current_date} (Day {day_of_week}).")

            current_date += timedelta(days=1)

        # 3. Commit the transaction
        db.commit()
        print(f"Generation phase completed. Total {total_generated} new slots generated and committed.")

    except Exception as e:
        db.rollback()
        print(f"Error during slot generation phase: {e}")
        # Optionally: Log the error, notify admin
        raise # Re-raise after rollback

    # Optional: Return status or generated slots info
    return {"status": "success", "total_generated": total_generated}


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