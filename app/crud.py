# app/crud.py - FULLY RESTORED AND CORRECTED
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, desc, func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, timedelta, date, time
from typing import Optional, List, Dict, Any
import secrets
import logging
import asyncio
from . import models, schemas
from .security import get_password_hash, verify_password, encryption_service, SecurityConfig
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) # Force DEBUG level for this logger
# IMPORTANT: Avoid importing services at module import time to prevent circular imports.
# Import service classes lazily inside functions when needed.

class CRUDError(Exception):
    pass

# --- NEW UTILITY FUNCTION ---
def _ensure_complete_user(user: models.User) -> models.User:
    """Ensures the user object has non-None values for required boolean/integer fields."""
    if user:
        if getattr(user, 'mfa_enabled', None) is None:
            user.mfa_enabled = False
        if getattr(user, 'is_active', None) is None:
            user.is_active = True
        if getattr(user, 'failed_login_attempts', None) is None:
            user.failed_login_attempts = 0
    return user

# ==================== USER CRUD OPERATIONS (UPGRADED) ====================

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """Get user by ID with error handling."""
    try:
        user = db.query(models.User).filter(models.User.id == user_id, models.User.deleted_at.is_(None)).first()
        return _ensure_complete_user(user)
    except SQLAlchemyError as e:
        logger.error(f"Error fetching user {user_id}: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def get_user_by_identifier(db: Session, identifier: str) -> Optional[models.User]:
    """Get user by username OR email."""
    try:
        user = db.query(models.User).filter(
            or_(models.User.username == identifier, models.User.email == identifier),
            models.User.deleted_at.is_(None)
        ).first()
        return _ensure_complete_user(user)
    except SQLAlchemyError as e:
        logger.error(f"Error fetching user by identifier '{identifier}': {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    try:
        user = db.query(models.User).filter(
            models.User.username == username,
            models.User.deleted_at.is_(None)
        ).first()
        return _ensure_complete_user(user)
    except SQLAlchemyError as e:
        logger.error(f"Error fetching user by username '{username}': {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def get_users(db: Session, skip: int = 0, limit: int = 100, role: str = None, is_active: bool = None) -> List[models.User]:
    """Get users with optional filters."""
    try:
        query = db.query(models.User).filter(models.User.deleted_at.is_(None))
        if role:
            query = query.filter(models.User.role == role)
        if is_active is not None:
            query = query.filter(models.User.is_active == is_active)
        users = query.order_by(models.User.username).offset(skip).limit(limit).all()
        # Fix for permissions being None which causes a validation error
        for user in users:
            user.permissions = user.permissions or {}
        return [_ensure_complete_user(u) for u in users]
    except SQLAlchemyError as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def create_user(db: Session, user: schemas.UserCreate, created_by: int = None) -> models.User:
    """Create new user with comprehensive validation."""
    try:
        if db.query(models.User).filter(models.User.username == user.username).first():
            raise CRUDError("Username already exists")
        if db.query(models.User).filter(models.User.email == user.email).first():
            raise CRUDError("Email already exists")
        
        hashed_password = get_password_hash(user.password)
        db_user = models.User(
            username=user.username,
            email=user.email,
            phone_number=user.phone_number,
            password_hash=hashed_password,
            role=user.role,
            is_active=True,
            is_verified=False,
            mfa_enabled=False,
            failed_login_attempts=0,
            password_last_changed=datetime.utcnow(),
            permissions=(getattr(user, 'permissions', {}) or {})
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"Created new user: {user.username} (ID: {db_user.id})")
        return _ensure_complete_user(db_user)
    except IntegrityError:
        db.rollback()
        raise CRUDError("User creation failed due to data constraints")
    except SQLAlchemyError as e:
        db.rollback()
        raise CRUDError(f"Database error: {str(e)}")

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate) -> Optional[models.User]:
    db_user = get_user(db, user_id=user_id)
    if not db_user:
        return None
    update_data = user_update.dict(exclude_unset=True)
    if "password" in update_data:
        update_data["password_hash"] = get_password_hash(update_data["password"])
        del update_data["password"]
    for key, value in update_data.items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int) -> bool:
    db_user = get_user(db, user_id=user_id)
    if not db_user:
        return False
    # Soft delete by default
    setattr(db_user, 'deleted_at', datetime.utcnow())
    setattr(db_user, 'is_active', False)
    db.commit()
    return True

def get_patient(db: Session, patient_id: int) -> Optional[models.Patient]:
    """Get a single patient by ID."""
    return db.query(models.Patient).filter(models.Patient.id == patient_id).first()

# ==================== PATIENT CRUD OPERATIONS (NEW) ====================


def create_patient(db: Session, patient: schemas.PatientCreate, created_by: int) -> models.Patient:
    # Combine first and last name into a single stored name
    full_name = patient.first_name.strip()
    if getattr(patient, "last_name", None):
        full_name = (full_name + " " + patient.last_name.strip()).strip()

    db_patient = models.Patient(
        name_encrypted=encryption_service.encrypt(full_name),
        phone_number_encrypted=encryption_service.encrypt(patient.phone_number) if patient.phone_number else None,
        email_encrypted=encryption_service.encrypt(patient.email) if patient.email else None,
        name_hash=encryption_service.hash_for_lookup(full_name),
        phone_hash=encryption_service.hash_for_lookup(patient.phone_number) if patient.phone_number else None,
        email_hash=encryption_service.hash_for_lookup(patient.email) if patient.email else None,
        date_of_birth=patient.date_of_birth,
        gender=patient.gender,
        city=patient.city,
        created_by=created_by
    )
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

def get_patients(db: Session, skip: int = 0, limit: int = 100, search: str = None) -> List[models.Patient]:
    """Get patients with optional search"""
    query = db.query(models.Patient)
    if search:
        # Search by name hash contains – compute on provided search string
        search_hash = encryption_service.hash_for_lookup(search)
        query = query.filter(models.Patient.name_hash.ilike(f"%{search_hash}%"))
    return query.offset(skip).limit(limit).all()

def update_patient(db: Session, patient_id: int, patient_update: schemas.PatientUpdate) -> Optional[models.Patient]:
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not db_patient:
        return None

    update_data = patient_update.dict(exclude_unset=True)

    for key, value in update_data.items():
        if key == 'first_name':
            # Combine with existing last name if present in update
            last = update_data.get('last_name')
            full_name = value if not last else f"{value} {last}"
            db_patient.name_encrypted = encryption_service.encrypt(full_name)
            db_patient.name_hash = encryption_service.hash_for_lookup(full_name)
        elif key == 'last_name':
            # Combine with existing first name from decrypted stored name
            current_name = encryption_service.decrypt(db_patient.name_encrypted) if db_patient.name_encrypted else ""
            parts = current_name.split(" ", 1)
            first = parts[0] if parts else ""
            full_name = f"{first} {value}".strip()
            db_patient.name_encrypted = encryption_service.encrypt(full_name)
            db_patient.name_hash = encryption_service.hash_for_lookup(full_name)
        elif key == 'phone_number' and value:
            db_patient.phone_number_encrypted = encryption_service.encrypt(value)
            db_patient.phone_hash = encryption_service.hash_for_lookup(value)
        elif key == 'email' and value:
            db_patient.email_encrypted = encryption_service.encrypt(value)
            db_patient.email_hash = encryption_service.hash_for_lookup(value)
        else:
            setattr(db_patient, key, value)

    db.commit()
    db.refresh(db_patient)
    return db_patient

def delete_patient(db: Session, patient_id: int) -> bool:
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not db_patient:
        return False
    # Using soft delete
    setattr(db_patient, 'is_active', False)
    db.commit()
    return True

# ==================== APPOINTMENT CRUD OPERATIONS (NEW) ====================

async def create_appointment(db: Session, appointment: schemas.AppointmentCreate, user_id: int) -> models.Appointment:
    """
    Create a new appointment. If new_patient data is provided, a new patient
    is created first.
    """
    appointment_data = appointment.dict()

    # Validate start time and duration
    start_time = appointment_data['start_time']
    end_time = appointment_data['end_time']

    # Pull configured interval (default 15)
    interval_entry = get_system_config(db, "appointment_interval_minutes")
    slot_minutes = int(interval_entry.value) if interval_entry and str(interval_entry.value).isdigit() else 15
    if start_time.minute % slot_minutes != 0:
        raise CRUDError(f"Appointments must start on a {slot_minutes}-minute interval.")
    if (end_time - start_time) != timedelta(minutes=slot_minutes):
        raise CRUDError(f"Appointment duration must be exactly {slot_minutes} minutes.")

    # Enforce weekly schedule availability and unavailable periods
    # 1) Weekly schedule
    day_of_week = start_time.weekday()
    schedule = db.query(models.LocationSchedule).filter(
        models.LocationSchedule.location_id == appointment_data['location_id'],
        models.LocationSchedule.day_of_week == day_of_week,
        models.LocationSchedule.is_available == True
    ).first()
    if not schedule:
        raise CRUDError("Selected day is unavailable for this location.")
    # Ensure within working hours
    schedule_start = datetime.combine(start_time.date(), schedule.start_time)
    schedule_end = datetime.combine(start_time.date(), schedule.end_time)
    if not (schedule_start <= start_time and end_time <= schedule_end):
        raise CRUDError("Selected time is outside working hours for this location.")
    # Respect break times if configured
    if schedule.break_start and schedule.break_end:
        break_start_dt = datetime.combine(start_time.date(), schedule.break_start)
        break_end_dt = datetime.combine(start_time.date(), schedule.break_end)
        if not (end_time <= break_start_dt or start_time >= break_end_dt):
            raise CRUDError("Selected time falls within a break period.")

    # 2) Unavailable periods
    overlaps_unavailable = db.query(models.UnavailablePeriod).filter(
        models.UnavailablePeriod.location_id == appointment_data['location_id'],
        models.UnavailablePeriod.start_datetime < end_time,
        models.UnavailablePeriod.end_datetime > start_time
    ).first()
    if overlaps_unavailable:
        raise CRUDError("Selected time is blocked due to unavailability.")

    # 3) Daily booking limits per patient (basic limit)
    patient_id_for_limit = appointment_data.get('patient_id')
    if patient_id_for_limit:
        day_start = datetime.combine(start_time.date(), time.min)
        day_end = datetime.combine(start_time.date(), time.max)
        limit_entry = get_system_config(db, "appointment_daily_limit")
        daily_limit_val = int(limit_entry.value) if limit_entry and str(limit_entry.value).isdigit() else SecurityConfig.APPOINTMENT_BOOKING_DAILY_LIMIT
        daily_count = db.query(models.Appointment).filter(
            models.Appointment.patient_id == patient_id_for_limit,
            models.Appointment.start_time >= day_start,
            models.Appointment.end_time <= day_end,
            models.Appointment.status != models.AppointmentStatus.cancelled
        ).count()
        if daily_count >= daily_limit_val:
            raise CRUDError("Daily booking limit reached for this patient.")

    # 4) Respect Google Calendar busy times as source of truth
    try:
        from app.services.calendar_service import GoogleCalendarService
        calendar_service = GoogleCalendarService()
        if calendar_service.enabled:
            busy = await calendar_service.get_busy_times(start_time, end_time)
            if busy:
                raise CRUDError("Selected time is busy in Google Calendar.")
    except Exception:
        # Fail-open if calendar check throws; we already enforce overlaps elsewhere
        pass

    # NEW: Add calendar event creation to the appointment workflow
    appointment_data['google_calendar_event_id'] = None # Initialize field

    # If new patient data is present, create the patient first
    if appointment.new_patient:
        new_patient_data = appointment.new_patient
        
        patient_schema = schemas.PatientCreate(
            first_name=new_patient_data.first_name,
            last_name=new_patient_data.last_name,
            date_of_birth=new_patient_data.date_of_birth,
            city=new_patient_data.city,
            phone_number=new_patient_data.phone_number,
            email=new_patient_data.email
        )
        
        # Create the patient and get their ID
        created_patient = create_patient(db=db, patient=patient_schema, created_by=user_id)
        appointment_data['patient_id'] = created_patient.id
        
        # Remove the nested new_patient object as it's not part of the Appointment model
        del appointment_data['new_patient']


    # Check for scheduling conflicts for the location/doctor
    existing_appointment = db.query(models.Appointment).filter(
        models.Appointment.location_id == appointment_data['location_id'], # Assuming one doctor per location for now
        models.Appointment.start_time < appointment_data['end_time'],
        models.Appointment.end_time > appointment_data['start_time'],
        models.Appointment.status != models.AppointmentStatus.cancelled
    ).first()

    if existing_appointment:
        raise CRUDError("An appointment already exists at this time.")

    # Create the appointment model instance
    db_appointment = models.Appointment(**appointment_data, user_id=user_id)
    
    try:
        db.add(db_appointment)
        db.commit()
        db.refresh(db_appointment)
        logger.info(f"Successfully created appointment {db_appointment.id} for patient {db_appointment.patient_id}")

        # NEW: Create Google Calendar event
        try:
            # Lazy import to avoid circular dependency
            from app.services.calendar_service import GoogleCalendarService
            calendar_service = GoogleCalendarService()
            patient = get_patient(db, db_appointment.patient_id)
            location = get_location(db, db_appointment.location_id)
            if patient and location and calendar_service.enabled:
                event_id = await calendar_service.create_calendar_event(db_appointment, patient, location)
                if event_id:
                    update_appointment_calendar_event(db, db_appointment.id, event_id)
                    db.refresh(db_appointment)
        except Exception as e:
            logger.error(f"Failed to create calendar event for appointment {db_appointment.id}: {e}")
            # Do not raise error, appointment is already created. Log and continue.

        return db_appointment
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error on appointment creation: {e}")
        raise CRUDError("Could not create appointment due to a database integrity issue.")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during appointment creation: {e}")
        raise CRUDError("A database error occurred while creating the appointment.")

async def update_appointment(db: Session, appointment_id: int, appointment_update: schemas.AppointmentUpdate) -> Optional[models.Appointment]:
    db_appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not db_appointment:
        return None
    update_data = appointment_update.dict(exclude_unset=True)
    # If times are being updated, enforce schedule and unavailable periods
    if 'start_time' in update_data or 'end_time' in update_data:
        new_start = update_data.get('start_time', db_appointment.start_time)
        new_end = update_data.get('end_time', db_appointment.end_time)
        # Weekly schedule
        day_of_week = new_start.weekday()
        schedule = db.query(models.LocationSchedule).filter(
            models.LocationSchedule.location_id == db_appointment.location_id,
            models.LocationSchedule.day_of_week == day_of_week,
            models.LocationSchedule.is_available == True
        ).first()
        if not schedule:
            raise CRUDError("Selected day is unavailable for this location.")
        schedule_start = datetime.combine(new_start.date(), schedule.start_time)
        schedule_end = datetime.combine(new_start.date(), schedule.end_time)
        if not (schedule_start <= new_start and new_end <= schedule_end):
            raise CRUDError("Selected time is outside working hours for this location.")
        if schedule.break_start and schedule.break_end:
            break_start_dt = datetime.combine(new_start.date(), schedule.break_start)
            break_end_dt = datetime.combine(new_start.date(), schedule.break_end)
            if not (new_end <= break_start_dt or new_start >= break_end_dt):
                raise CRUDError("Selected time falls within a break period.")
        # Unavailable periods
        overlaps_unavailable = db.query(models.UnavailablePeriod).filter(
            models.UnavailablePeriod.location_id == db_appointment.location_id,
            models.UnavailablePeriod.start_datetime < new_end,
            models.UnavailablePeriod.end_datetime > new_start
        ).first()
        if overlaps_unavailable:
            raise CRUDError("Selected time is blocked due to unavailability.")

        # Google Calendar busy check on update
        try:
            from app.services.calendar_service import GoogleCalendarService
            calendar_service = GoogleCalendarService()
            if calendar_service.enabled:
                busy = await calendar_service.get_busy_times(new_start, new_end)
                if busy:
                    raise CRUDError("Selected time is busy in Google Calendar.")
        except Exception:
            pass
    for key, value in update_data.items():
        setattr(db_appointment, key, value)
    db.commit()
    db.refresh(db_appointment)

    # NEW: Update Google Calendar event
    try:
        if db_appointment.google_calendar_event_id:
            from app.services.calendar_service import GoogleCalendarService
            calendar_service = GoogleCalendarService()
            if calendar_service.enabled:
                patient = get_patient(db, db_appointment.patient_id)
                location = get_location(db, db_appointment.location_id)
                if patient and location:
                    await calendar_service.update_calendar_event(
                        event_id=db_appointment.google_calendar_event_id,
                        appointment=db_appointment,
                        patient=patient,
                        location=location
                    )
    except Exception as e:
        logger.error(f"Failed to update calendar event for appointment {db_appointment.id}: {e}")

    return db_appointment

async def delete_appointment(db: Session, appointment_id: int) -> bool:
    db_appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not db_appointment:
        return False

    # NEW: Delete Google Calendar event
    try:
        if db_appointment.google_calendar_event_id:
            from app.services.calendar_service import GoogleCalendarService
            calendar_service = GoogleCalendarService()
            if calendar_service.enabled:
                await calendar_service.delete_calendar_event(db_appointment.google_calendar_event_id)
    except Exception as e:
        logger.error(f"Failed to delete calendar event for appointment {db_appointment.id}: {e}")

    db.delete(db_appointment)
    db.commit()
    return True

# ==================== SCHEDULE CRUD OPERATIONS (NEW) ====================

def get_location(db: Session, location_id: int) -> Optional[models.Location]:
    """Get a single location by ID."""
    return db.query(models.Location).filter(models.Location.id == location_id).first()

def get_location_by_name(db: Session, name: str) -> Optional[models.Location]:
    """Get a single location by its name."""
    return db.query(models.Location).filter(models.Location.name == name).first()

def get_locations(db: Session, skip: int = 0, limit: int = 100) -> List[models.Location]:
    """Get all locations."""
    return db.query(models.Location).offset(skip).limit(limit).all()

def create_location(db: Session, location: schemas.LocationCreate) -> models.Location:
    """Create a new location."""
    db_location = models.Location(**location.dict())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

def get_appointments_without_calendar_events(db: Session) -> List[models.Appointment]:
    """Get all appointments that are missing a Google Calendar event ID."""
    return db.query(models.Appointment).filter(models.Appointment.google_calendar_event_id.is_(None)).all()

def update_appointment_calendar_event(db: Session, appointment_id: int, event_id: str) -> None:
    """Update an appointment with its Google Calendar event ID."""
    db.query(models.Appointment).filter(models.Appointment.id == appointment_id).update({'google_calendar_event_id': event_id})
    db.commit()

# ==================== SCHEDULE CRUD OPERATIONS (NEW) ====================

def get_schedules_for_location(db: Session, location_id: int) -> List[models.LocationSchedule]:
    """Retrieve all schedule entries for a given location."""
    return db.query(models.LocationSchedule).filter(models.LocationSchedule.location_id == location_id).all()

def update_schedules_for_location(db: Session, location_id: int, schedules: List[schemas.LocationScheduleCreate]) -> List[models.LocationSchedule]:
    """Update or create schedule entries for a location for a full week."""
    logger.debug(f"[update_schedules_for_location] START for loc {location_id}. Received {len(schedules)} schedule entries.")
    logger.debug(f"[update_schedules_for_location] Incoming data: {schedules}")
    try:
        # --- OVERLAP VALIDATION --- START ---
        logger.debug(f"[update_schedules_for_location] Checking for overlaps with other location...")
        # Determine the other location's ID (assuming 1 and 2 are the only locations)
        other_location_id = 2 if location_id == 1 else 1
        other_schedules = get_schedules_for_location(db, other_location_id)
        other_schedules_map = {s.day_of_week: s for s in other_schedules}
        day_names_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        for new_day_schedule in schedules:
            if not new_day_schedule.is_available:
                continue # This day is off, no conflict possible

            other_day_schedule = other_schedules_map.get(new_day_schedule.day_of_week)
            
            # Check if the other location is also available on this day
            if other_day_schedule and other_day_schedule.is_available:
                day_name_str = day_names_list[new_day_schedule.day_of_week]
                
                # Ensure times are valid time objects (Pydantic should handle this, but checking is safe)
                if not isinstance(new_day_schedule.start_time, time) or not isinstance(new_day_schedule.end_time, time) or \
                   not isinstance(other_day_schedule.start_time, time) or not isinstance(other_day_schedule.end_time, time):
                    logger.warning(f"Skipping overlap check for {day_name_str} due to invalid time data.")
                    continue # Skip check if data is corrupt

                # Check for overlap: (StartA < EndB) and (EndA > StartB)
                overlap = (new_day_schedule.start_time < other_day_schedule.end_time) and \
                          (new_day_schedule.end_time > other_day_schedule.start_time)
                
                if overlap:
                    logger.warning(f"Overlap detected for {day_name_str} between loc {location_id} and {other_location_id}")
                    other_loc_name = "Hospital" if other_location_id == 2 else "Clinic"
                    current_loc_name = "Clinic" if location_id == 1 else "Hospital"
                    raise CRUDError(
                        f"Schedule Conflict for {day_name_str}: The time {new_day_schedule.start_time.strftime('%H:%M')}-{new_day_schedule.end_time.strftime('%H:%M')} "
                        f"at {current_loc_name} conflicts with the schedule {other_day_schedule.start_time.strftime('%H:%M')}-{other_day_schedule.end_time.strftime('%H:%M')} "
                        f"at the {other_loc_name}."
                    )
        logger.debug("[update_schedules_for_location] No location overlaps found.")
        # --- OVERLAP VALIDATION --- END ---

        # --- OVERLAP VALIDATION --- START ---
        logger.debug(f"[update_schedules_for_location] Checking for overlaps with other location...")
        # Determine the other location's ID (assuming 1 and 2 are the only locations)
        other_location_id = 2 if location_id == 1 else 1
        other_schedules = get_schedules_for_location(db, other_location_id)
        other_schedules_map = {s.day_of_week: s for s in other_schedules}
        day_names_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        for new_day_schedule in schedules:
            if not new_day_schedule.is_available:
                continue # This day is off, no conflict possible

            other_day_schedule = other_schedules_map.get(new_day_schedule.day_of_week)
            
            # Check if the other location is also available on this day
            if other_day_schedule and other_day_schedule.is_available:
                day_name_str = day_names_list[new_day_schedule.day_of_week]
                
                # Ensure times are valid time objects (Pydantic should handle this, but checking is safe)
                if not isinstance(new_day_schedule.start_time, time) or not isinstance(new_day_schedule.end_time, time) or \
                   not isinstance(other_day_schedule.start_time, time) or not isinstance(other_day_schedule.end_time, time):
                    logger.warning(f"Skipping overlap check for {day_name_str} due to invalid time data.")
                    continue # Skip check if data is corrupt

                # Check for overlap: (StartA < EndB) and (EndA > StartB)
                overlap = (new_day_schedule.start_time < other_day_schedule.end_time) and \
                          (new_day_schedule.end_time > other_day_schedule.start_time)
                
                if overlap:
                    logger.warning(f"Overlap detected for {day_name_str} between loc {location_id} and {other_location_id}")
                    other_loc_name = "Hospital" if other_location_id == 2 else "Clinic"
                    current_loc_name = "Clinic" if location_id == 1 else "Hospital"
                    raise CRUDError(
                        f"Schedule Conflict for {day_name_str}: The time {new_day_schedule.start_time.strftime('%H:%M')}-{new_day_schedule.end_time.strftime('%H:%M')} "
                        f"at {current_loc_name} conflicts with the schedule {other_day_schedule.start_time.strftime('%H:%M')}-{other_day_schedule.end_time.strftime('%H:%M')} "
                        f"at the {other_loc_name}."
                    )
        logger.debug("[update_schedules_for_location] No location overlaps found.")
        # --- OVERLAP VALIDATION --- END ---

        # --- VALIDATION --- START ---
        logger.debug("[update_schedules_for_location] Validating max_appointments...")
        today = date.today() # Dummy date for time calculations
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for schedule_data in schedules:
            day_name = day_names[schedule_data.day_of_week]
            if schedule_data.is_available and schedule_data.max_appointments is not None and schedule_data.max_appointments > 0:
                duration = schedule_data.appointment_duration
                if duration is None or duration <= 0:
                    # Use global default or fallback if per-day duration isn't set/valid
                    interval_entry = get_system_config(db, "appointment_interval_minutes")
                    duration = int(interval_entry.value) if interval_entry and str(interval_entry.value).isdigit() else 30
                    logger.warning(f"[update_schedules_for_location] Invalid/missing duration for {day_name}, using fallback: {duration} min")
                
                if duration <= 0: # Still invalid after fallback
                    raise CRUDError(f"Invalid appointment duration ({duration} mins) for {day_name}. Must be positive.")

                try:
                    logger.debug(f"Validating {day_name}: Start={schedule_data.start_time} (Type: {type(schedule_data.start_time)}), End={schedule_data.end_time} (Type: {type(schedule_data.end_time)}), Duration={duration}")

                    # 1. Check for missing time values (Pydantic should convert, but a direct None check is safest)
                    if not isinstance(schedule_data.start_time, time) or not isinstance(schedule_data.end_time, time):
                        # This handles if the data is None or still a string (Pydantic failed parsing)
                        raise CRUDError(f"Validation Error for {day_name}: Start Time ('{schedule_data.start_time}') and End Time ('{schedule_data.end_time}') are required and must be valid HH:MM format when 'Available' is checked.")

                    logger.debug(f"Combining datetimes for {day_name}...")
                    start_dt = datetime.combine(today, schedule_data.start_time)
                    end_dt = datetime.combine(today, schedule_data.end_time)
                    
                    # 2. Calculate total minutes (time period)
                    total_minutes = (end_dt - start_dt).total_seconds() / 60
                    logger.debug(f"{day_name} total minutes: {total_minutes}")

                    if total_minutes <= 0:
                         logger.warning(f"{day_name} has invalid time range: {schedule_data.start_time} to {schedule_data.end_time}. Total minutes: {total_minutes}")
                         raise CRUDError(f"Validation Error for {day_name}: End Time ({schedule_data.end_time.strftime('%H:%M')}) must be after Start Time ({schedule_data.start_time.strftime('%H:%M')}).")
                    
                    # 3. Check duration (time between appointments)
                    if duration == 0:
                        raise CRUDError(f"Validation Error for {day_name}: Appointment duration cannot be zero.")

                    # 4. Calculate max appointments
                    max_possible = int(total_minutes // duration)
                    logger.debug(f"{day_name}: Max Possible={max_possible}, User Max={schedule_data.max_appointments}")

                    # 5. Check user input against max
                    if schedule_data.max_appointments > max_possible:
                        time_period_hours = round(total_minutes / 60, 1)
                        raise CRUDError(
                            f"Max appointments ({schedule_data.max_appointments}) for {day_name} exceeds the possible {max_possible} slots. The {time_period_hours} hour period ({schedule_data.start_time.strftime('%H:%M')} - {schedule_data.end_time.strftime('%H:%M')}) with a {duration} min duration only allows {max_possible} appointments."
                        )
                
                # Catch specific calculation errors
                except (TypeError, ValueError) as calc_err: 
                     logger.error(f"[update_schedules_for_location] Error calculating max appointments for {day_name} (Day {schedule_data.day_of_week}): {calc_err}", exc_info=True)
                     raise CRUDError(f"Internal Error for {day_name}: Calculation failed. Ensure Start Time ('{schedule_data.start_time}') and End Time ('{schedule_data.end_time}') are both set and valid.")
                # Re-raise our specific validation errors
                except CRUDError: 
                    raise
                # Catch any other unexpected error
                except Exception as e: 
                     logger.error(f"[update_schedules_for_location] UNEXPECTED Error for {day_name}: {e}", exc_info=True)
                     raise CRUDError(f"An unknown error occurred while validating {day_name}.")
        # Check count before delete
        count_before = db.query(models.LocationSchedule).filter(models.LocationSchedule.location_id == location_id).count()
        logger.debug(f"[update_schedules_for_location] Count before delete for loc {location_id}: {count_before}")
        
        # Delete existing schedules for the week for simplicity.
        deleted_count = db.query(models.LocationSchedule).filter(models.LocationSchedule.location_id == location_id).delete()
        logger.debug(f"[update_schedules_for_location] Deleted {deleted_count} existing schedules for loc {location_id}.")
        
        # Check count after delete (before flush/commit)
        count_after_delete = db.query(models.LocationSchedule).filter(models.LocationSchedule.location_id == location_id).count()
        logger.debug(f"[update_schedules_for_location] Count after delete (pre-commit) for loc {location_id}: {count_after_delete}")
        # Note: Depending on transaction isolation, this count might not reflect the delete until commit.
        # Let's flush to see the effect sooner if possible without full commit.
        try:
            db.flush() # Try to push delete to DB connection buffer
            count_after_flush = db.query(models.LocationSchedule).filter(models.LocationSchedule.location_id == location_id).count()
            logger.debug(f"[update_schedules_for_location] Count after delete (post-flush) for loc {location_id}: {count_after_flush}")
        except SQLAlchemyError as flush_err:
             logger.warning(f"[update_schedules_for_location] DB flush after delete failed (might be expected): {flush_err}")

        new_schedules_models = []
        for idx, schedule_data in enumerate(schedules):
            # Ensure location_id is present, even though schema requires it, belt-and-suspenders approach.
            if schedule_data.location_id != location_id:
                 logger.warning(f"[update_schedules_for_location] Mismatch! schedule_data location_id ({schedule_data.location_id}) != path location_id ({location_id}). Forcing path ID.")
            
            schedule_dict = schedule_data.dict()
            schedule_dict['location_id'] = location_id # Explicitly ensure correct location_id

            new_schedule = models.LocationSchedule(**schedule_dict)
            logger.debug(f"[update_schedules_for_location] Creating model instance {idx}: Day={new_schedule.day_of_week}, Start={new_schedule.start_time}, End={new_schedule.end_time}, Avail={new_schedule.is_available}, LocID={new_schedule.location_id}")
            new_schedules_models.append(new_schedule)
        
        logger.debug(f"[update_schedules_for_location] Prepared {len(new_schedules_models)} model instances for addition.")
        db.add_all(new_schedules_models)
        
        count_before_commit = db.query(models.LocationSchedule).filter(models.LocationSchedule.location_id == location_id).count()
        logger.debug(f"[update_schedules_for_location] Count after add_all (pre-commit) for loc {location_id}: {count_before_commit}")

        logger.debug(f"[update_schedules_for_location] Committing transaction for loc {location_id}...")
        db.commit()
        logger.debug(f"[update_schedules_for_location] Commit successful for loc {location_id}.")
        
        # Fetch from DB to confirm what was actually saved
        saved_schedules = db.query(models.LocationSchedule).filter(models.LocationSchedule.location_id == location_id).all()
        logger.debug(f"[update_schedules_for_location] Fetched {len(saved_schedules)} schedules from DB post-commit for loc {location_id}.")
        for s in saved_schedules:
             logger.debug(f"  -> DB State: Day={s.day_of_week}, Start={s.start_time}, End={s.end_time}, Avail={s.is_available}, ID={s.id}")
        
        # Return the models added (note: IDs might not be populated correctly on the original list)
        # It's safer to return the 'saved_schedules' fetched after commit.
        return saved_schedules
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"[update_schedules_for_location] SQLAlchemyError for location {location_id}: {e}")
        raise CRUDError("A database error occurred while updating schedules.")
    except Exception as e:
        db.rollback()
        logger.error(f"[update_schedules_for_location] Unexpected Error for location {location_id}: {e}")
        raise CRUDError(f"An unexpected error occurred: {e}")

def update_schedule_for_day(db: Session, location_id: int, day_of_week: int, schedule_update: schemas.LocationScheduleCreate) -> models.LocationSchedule:
    """Update or create a schedule for a specific day and location."""
    try:
        db_schedule = db.query(models.LocationSchedule).filter(
            models.LocationSchedule.location_id == location_id,
            models.LocationSchedule.day_of_week == day_of_week
        ).first()

        if db_schedule:
            # Update existing schedule
            for key, value in schedule_update.dict().items():
                setattr(db_schedule, key, value)
        else:
            # Create new schedule
            db_schedule = models.LocationSchedule(
                **schedule_update.dict(),
                location_id=location_id,
                day_of_week=day_of_week
            )
            db.add(db_schedule)
        
        db.commit()
        db.refresh(db_schedule)
        return db_schedule
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error updating schedule for location {location_id}, day {day_of_week}: {e}")
        raise CRUDError("A database error occurred while updating the day schedule.")

async def get_available_slots(db: Session, location_id: int, for_date: date) -> List[time]:
    """
    Calculate available appointment slots for a given location and date,
    factoring in Google Calendar events.
    """
    try:
        # 1. Get the weekly schedule for the given day
        day_of_week = for_date.weekday()  # Monday is 0 and Sunday is 6
        schedule = db.query(models.LocationSchedule).filter(
            models.LocationSchedule.location_id == location_id,
            models.LocationSchedule.day_of_week == day_of_week,
            models.LocationSchedule.is_available == True
        ).first()

        if not schedule:
            return []  # Doctor is not available on this day

        # 2. Get all existing appointments for the day
        start_of_day = datetime.combine(for_date, time.min)
        end_of_day = datetime.combine(for_date, time.max)
        
        appointments = db.query(models.Appointment).filter(
            models.Appointment.location_id == location_id,
            models.Appointment.start_time >= start_of_day,
            models.Appointment.end_time <= end_of_day,
            models.Appointment.status != models.AppointmentStatus.cancelled
        ).all()

        booked_slots = set()
        for appt in appointments:
            slot_time = appt.start_time
            while slot_time < appt.end_time:
                booked_slots.add(slot_time.time())
                slot_time += timedelta(minutes=15)

        # 3. Get any manually blocked periods for the day
        unavailable_periods = db.query(models.UnavailablePeriod).filter(
            models.UnavailablePeriod.location_id == location_id,
            models.UnavailablePeriod.start_datetime <= end_of_day,
            models.UnavailablePeriod.end_datetime >= start_of_day
        ).all()

        for period in unavailable_periods:
            slot_time = period.start_datetime
            while slot_time < period.end_datetime:
                if slot_time.date() == for_date:
                    booked_slots.add(slot_time.time())
                slot_time += timedelta(minutes=15)

        # 4. NEW: Get busy times from Google Calendar
        from app.services.calendar_service import GoogleCalendarService
        calendar_service = GoogleCalendarService()
        if calendar_service.enabled:
            gcal_busy_times = await calendar_service.get_busy_times(start_of_day, end_of_day)
            for busy_period in gcal_busy_times:
                slot_time = busy_period['start']
                # Ensure timezone awareness matches for comparison
                if slot_time.tzinfo is None:
                    slot_time = slot_time.replace(tzinfo=start_of_day.tzinfo)

                while slot_time < busy_period['end']:
                    if slot_time.date() == for_date:
                        booked_slots.add(slot_time.time())
                    slot_time += timedelta(minutes=15)

        # 5. Generate potential slots and filter out booked/unavailable ones
        available_slots = []
        slot_duration = timedelta(minutes=15)
        current_time = datetime.combine(for_date, schedule.start_time)
        end_time = datetime.combine(for_date, schedule.end_time)

        while current_time < end_time:
            if current_time.time() not in booked_slots:
                available_slots.append(current_time.time())
            current_time += slot_duration
            
        return available_slots
    except SQLAlchemyError as e:
        logger.error(f"Error calculating available slots for location {location_id} on {for_date}: {e}")
        raise CRUDError("A database error occurred while calculating availability.")
async def get_available_slots_detailed(db: Session, location_id: int, for_date: date) -> List[Dict[str, Any]]:
    """Return slot list with availability and reason (available, booked, break, unavailable, gcal_busy)."""
    result: List[Dict[str, Any]] = []
    try:
        day_of_week = for_date.weekday()
        schedule = db.query(models.LocationSchedule).filter(
            models.LocationSchedule.location_id == location_id,
            models.LocationSchedule.day_of_week == day_of_week,
            models.LocationSchedule.is_available == True
        ).first()
        if not schedule:
            return []

        start_of_day = datetime.combine(for_date, time.min)
        end_of_day = datetime.combine(for_date, time.max)

        appointments = db.query(models.Appointment).filter(
            models.Appointment.location_id == location_id,
            models.Appointment.start_time >= start_of_day,
            models.Appointment.end_time <= end_of_day,
            models.Appointment.status != models.AppointmentStatus.cancelled
        ).all()

        booked_ranges = [(a.start_time, a.end_time) for a in appointments]

        unavailable_periods = db.query(models.UnavailablePeriod).filter(
            models.UnavailablePeriod.location_id == location_id,
            models.UnavailablePeriod.start_datetime <= end_of_day,
            models.UnavailablePeriod.end_datetime >= start_of_day
        ).all()
        unavailable_ranges = [(u.start_datetime, u.end_datetime) for u in unavailable_periods]

        gcal_ranges: List[tuple] = []
        try:
            from app.services.calendar_service import GoogleCalendarService
            calendar_service = GoogleCalendarService()
            if calendar_service.enabled:
                gcal_busy = await calendar_service.get_busy_times(start_of_day, end_of_day)
                for b in gcal_busy:
                    gcal_ranges.append((b['start'], b['end']))
        except Exception:
            pass

        slot_duration = timedelta(minutes=15)
        current_time = datetime.combine(for_date, schedule.start_time)
        end_time = datetime.combine(for_date, schedule.end_time)

        while current_time < end_time:
            reason = "available"
            # break window
            if schedule.break_start and schedule.break_end:
                bs = datetime.combine(for_date, schedule.break_start)
                be = datetime.combine(for_date, schedule.break_end)
                if not (current_time + slot_duration <= bs or current_time >= be):
                    reason = "break"

            # booked
            if reason == "available":
                for s, e in booked_ranges:
                    if s <= current_time < e:
                        reason = "booked"
                        break

            # unavailable
            if reason == "available":
                for s, e in unavailable_ranges:
                    if s <= current_time < e:
                        reason = "unavailable"
                        break

            # gcal busy
            if reason == "available":
                for s, e in gcal_ranges:
                    if s <= current_time < e:
                        reason = "gcal_busy"
                        break

            result.append({
                "time": current_time.time(),
                "available": reason == "available",
                "reason": reason
            })
            current_time += slot_duration

        return result
    except SQLAlchemyError as e:
        logger.error(f"Error calculating detailed slots for location {location_id} on {for_date}: {e}")
        raise CRUDError("A database error occurred while calculating availability.")

    except SQLAlchemyError as e:
        logger.error(f"Error calculating available slots for location {location_id} on {for_date}: {e}")
        raise CRUDError("A database error occurred while calculating availability.")

async def emergency_cancel_appointments(db: Session, block_date: date, reason: str, user_id: int) -> List[models.Appointment]:
    """
    Cancels all appointments for a given day, notifies patients via WhatsApp,
    and creates an unavailable period for the entire day.
    """
    start_of_day = datetime.combine(block_date, time.min)
    end_of_day = datetime.combine(block_date, time.max)

    # 1. Find all appointments for the given day that are not already cancelled
    appointments_to_cancel = db.query(models.Appointment).filter(
        models.Appointment.start_time >= start_of_day,
        models.Appointment.end_time <= end_of_day,
        models.Appointment.status != models.AppointmentStatus.cancelled
    ).all()

    cancelled_appointments = []
    for appointment in appointments_to_cancel:
        # 2. Cancel the appointment
        appointment.status = 'cancelled'
        appointment.cancellation_reason = f"EMERGENCY: {reason}"
        cancelled_appointments.append(appointment)

        # 3. Notify patient via WhatsApp
        patient = get_patient(db, appointment.patient_id)
        try:
            if patient and patient.whatsapp_number:
                from app.services.whatsapp_service import WhatsAppService
                ws = WhatsAppService()
                if ws.enabled:
                    # We don't have separate first name; use full name
                    patient_name = encryption_service.decrypt(patient.name_encrypted) if patient.name_encrypted else "Patient"
                    message = (
                        f"EMERGENCY CANCELLATION: Dear {patient_name}, due to an emergency, all appointments for "
                        f"{block_date.strftime('%A, %B %d')} have been cancelled. We sincerely apologize for any inconvenience. "
                        "Please contact us to reschedule."
                    )
                    await ws.send_message(patient.whatsapp_number, message)
        except Exception:
            pass
    
    # 4. Create an unavailable period for the entire day for both locations
    for location_id in [1, 2]: # Assuming location IDs 1 and 2
        unavailable_period_data = schemas.UnavailablePeriodCreate(
            location_id=location_id,
            start_datetime=start_of_day,
            end_datetime=end_of_day,
            reason=f"EMERGENCY: {reason}"
        )
        create_unavailable_period(db=db, period=unavailable_period_data, created_by=user_id)

    db.commit()
    return cancelled_appointments

def create_unavailable_period(db: Session, period: schemas.UnavailablePeriodCreate, created_by: int) -> models.UnavailablePeriod:
    """
    Create a new unavailable period for a location.
    """
    try:
        db_period = models.UnavailablePeriod(
            **period.dict(),
            created_by=created_by
        )
        db.add(db_period)
        db.commit()
        db.refresh(db_period)
        return db_period
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating unavailable period: {e}")
        raise CRUDError("A database error occurred while creating the unavailable period.")

def get_unavailable_period_by_id(db: Session, period_id: int) -> Optional[models.UnavailablePeriod]:
    """Get a single unavailable period by its ID."""
    try:
        return db.query(models.UnavailablePeriod).filter(models.UnavailablePeriod.id == period_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching unavailable period {period_id}: {e}")
        raise CRUDError("A database error occurred while fetching the unavailable period.")

def get_unavailable_periods(db: Session, location_id: int, start_date: date, end_date: date) -> List[models.UnavailablePeriod]:
    """
    Retrieve unavailable periods for a given location and date range.
    """
    try:
        start_datetime = datetime.combine(start_date, time.min)
        end_datetime = datetime.combine(end_date, time.max)
        
        return db.query(models.UnavailablePeriod).filter(
            models.UnavailablePeriod.location_id == location_id,
            models.UnavailablePeriod.start_datetime <= end_datetime,
            models.UnavailablePeriod.end_datetime >= start_datetime
        ).all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching unavailable periods: {e}")
        raise CRUDError("A database error occurred while fetching unavailable periods.")

def update_unavailable_period(db: Session, period_id: int, period_update: schemas.UnavailablePeriodUpdate) -> Optional[models.UnavailablePeriod]:
    """
    Update an existing unavailable period.
    """
    try:
        db_period = get_unavailable_period_by_id(db, period_id)
        if not db_period:
            return None

        update_data = period_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_period, key, value)
        
        db.commit()
        db.refresh(db_period)
        return db_period
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error updating unavailable period {period_id}: {e}")
        raise CRUDError("A database error occurred while updating the unavailable period.")

def delete_unavailable_period(db: Session, period_id: int) -> bool:
    """
    Delete an unavailable period.
    """
    try:
        db_period = get_unavailable_period_by_id(db, period_id)
        if not db_period:
            return False
        
        db.delete(db_period)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error deleting unavailable period {period_id}: {e}")
        raise CRUDError("A database error occurred while deleting the unavailable period.")

# ==================== PRESCRIPTION CRUD OPERATIONS (NEW) ====================

def create_prescription(db: Session, prescription: schemas.PrescriptionCreate, prescribed_by: int) -> models.Prescription:
    """
    Create a new prescription for a patient.
    """
    try:
        db_prescription = models.Prescription(
            **prescription.dict(),
            prescribed_by=prescribed_by
        )
        db.add(db_prescription)
        db.commit()
        db.refresh(db_prescription)
        logger.info(f"Created new prescription {db_prescription.id} for patient {db_prescription.patient_id}")
        return db_prescription
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating prescription: {e}")
        raise CRUDError("A database error occurred while creating the prescription.")

def get_prescriptions_for_patient(db: Session, patient_id: int) -> List[models.Prescription]:
    """
    Retrieve all prescriptions for a specific patient.
    """
    try:
        return db.query(models.Prescription).filter(models.Prescription.patient_id == patient_id).order_by(models.Prescription.prescribed_date.desc()).all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching prescriptions for patient {patient_id}: {e}")
        raise CRUDError("A database error occurred while fetching prescriptions.")

def get_recent_prescriptions(db: Session, limit: int = 5) -> List[models.Prescription]:
    try:
        return db.query(models.Prescription).order_by(models.Prescription.prescribed_date.desc()).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching recent prescriptions: {e}")
        raise CRUDError("A database error occurred while fetching recent prescriptions.")


# ==================== REMARK CRUD OPERATIONS (NEW) ====================

def create_remark(db: Session, patient_id: int, author_id: int, text: str) -> models.Remark:
    """Create a new remark for a patient."""
    try:
        db_remark = models.Remark(text=text, patient_id=patient_id, author_id=author_id)
        db.add(db_remark)
        db.commit()
        db.refresh(db_remark)
        return db_remark
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating remark for patient {patient_id}: {e}")
        raise CRUDError("A database error occurred while creating the remark.")

def get_remarks_for_patient(db: Session, patient_id: int) -> List[models.Remark]:
    """Retrieve all remarks for a specific patient, joined with author info."""
    try:
        return db.query(models.Remark).options(joinedload(models.Remark.author)).filter(models.Remark.patient_id == patient_id).order_by(models.Remark.created_at.desc()).all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching remarks for patient {patient_id}: {e}")
        raise CRUDError("A database error occurred while fetching remarks.")


# ==================== EMR / CONSULTATION CRUD OPERATIONS (NEW) ====================

def create_consultation(db: Session, consultation: schemas.ConsultationCreate, user_id: int) -> models.Consultation:
    """Create a new consultation record, including nested vitals, diagnoses, and medications."""
    try:
        # Create the main consultation record
        consultation_data = consultation.dict(exclude={'vitals', 'diagnoses', 'medications'})
        db_consultation = models.Consultation(**consultation_data, user_id=user_id)
        db.add(db_consultation)
        db.flush() # Flush to get the consultation ID before adding related items

        # Create Vitals if provided
        if consultation.vitals:
            # Ensure consultation_id is added before creating the model
            vitals_data = consultation.vitals.dict()
            vitals_data['consultation_id'] = db_consultation.id
            db_vitals = models.Vitals(**vitals_data)
            db.add(db_vitals)

        # Create Diagnoses
        for diagnosis in consultation.diagnoses:
            db_diagnosis = models.ConsultationDiagnosis(**diagnosis.dict(), consultation_id=db_consultation.id)
            db.add(db_diagnosis)

        # Create Medications
        for medication in consultation.medications:
            db_medication = models.ConsultationMedication(**medication.dict(), consultation_id=db_consultation.id)
            db.add(db_medication)

        # Update patient's last visit date
        db.query(models.Patient).filter(models.Patient.id == consultation.patient_id).update({'last_visit_date': datetime.utcnow()})

        db.commit()
        # After commit, relationships might need explicit loading depending on configuration
        # Let's reload the object with relationships
        db.refresh(db_consultation)
        # Explicitly load relationships if refresh doesn't automatically do it
        db_consultation = get_consultation(db, db_consultation.id)

        logger.info(f"Created consultation {db_consultation.id} for patient {db_consultation.patient_id} by user {user_id}")
        return db_consultation
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error on consultation creation: {e}")
        raise CRUDError("Could not create consultation due to a database integrity issue (e.g., patient not found).")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during consultation creation: {e}")
        raise CRUDError("A database error occurred while creating the consultation.")

def get_consultation(db: Session, consultation_id: int) -> Optional[models.Consultation]:
    """Get a single consultation by ID, including related data."""
    try:
        return db.query(models.Consultation).options(
            joinedload(models.Consultation.vitals),
            joinedload(models.Consultation.diagnoses),
            joinedload(models.Consultation.medications),
            joinedload(models.Consultation.patient),
            joinedload(models.Consultation.user)
        ).filter(models.Consultation.id == consultation_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching consultation {consultation_id}: {e}")
        raise CRUDError("A database error occurred while fetching the consultation.")

def get_consultations_for_patient(db: Session, patient_id: int, skip: int = 0, limit: int = 20) -> List[models.Consultation]:
    """Get all consultations for a specific patient, ordered by date descending."""
    try:
        return db.query(models.Consultation).options(
            joinedload(models.Consultation.vitals),
            joinedload(models.Consultation.diagnoses),
            joinedload(models.Consultation.medications),
            joinedload(models.Consultation.user) # Load user who performed consultation
        ).filter(models.Consultation.patient_id == patient_id).order_by(models.Consultation.consultation_date.desc()).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching consultations for patient {patient_id}: {e}")
        raise CRUDError("A database error occurred while fetching consultations.")

# --- Patient Menstrual History CRUD ---

def get_patient_menstrual_history(db: Session, patient_id: int) -> Optional[models.PatientMenstrualHistory]:
    """Get menstrual history for a patient."""
    try:
        return db.query(models.PatientMenstrualHistory).filter(models.PatientMenstrualHistory.patient_id == patient_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching menstrual history for patient {patient_id}: {e}")
        raise CRUDError("Database error fetching menstrual history.")

def create_or_update_patient_menstrual_history(db: Session, patient_id: int, history_data: schemas.PatientMenstrualHistoryCreate) -> models.PatientMenstrualHistory:
    """Create or update menstrual history for a patient."""
    try:
        db_history = get_patient_menstrual_history(db, patient_id)
        if db_history:
            # Update
            update_data = history_data.dict(exclude_unset=True)
            # Ensure patient_id isn't accidentally changed if included in update_data
            update_data.pop('patient_id', None)
            for key, value in update_data.items():
                setattr(db_history, key, value)
        else:
            # Create
            # Ensure patient_id is set correctly for creation
            create_data = history_data.dict()
            create_data['patient_id'] = patient_id # Explicitly set patient_id
            db_history = models.PatientMenstrualHistory(**create_data)
            db.add(db_history)
        db.commit()
        db.refresh(db_history)
        return db_history
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error saving menstrual history for patient {patient_id}: {e}")
        raise CRUDError("Database error saving menstrual history.")


# ==================== AUDIT LOG CRUD OPERATIONS (NEW) ====================

def create_audit_log(
    db: Session, 
    user_id: Optional[int], 
    action: str, 
    category: str,
    severity: str = "INFO",
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    details: Optional[str] = None,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
    ip_address: Optional[str] = None
) -> models.AuditLog:
    """Create a new structured audit log entry."""
    try:
        # Denormalize username for audit integrity
        username = db.query(models.User.username).filter(models.User.id == user_id).scalar() if user_id else "System"
        
        db_log = models.AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            category=category,
            severity=severity,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address
        )
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        return db_log
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating audit log: {e}")
        # Don't re-raise CRUDError, as logging failure should not crash main operations

def get_audit_logs(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    user_id: Optional[int] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[models.AuditLog]:
    """Retrieve audit logs with filtering.""" 
    try:
        query = db.query(models.AuditLog).options(joinedload(models.AuditLog.user))
        
        if user_id:
            query = query.filter(models.AuditLog.user_id == user_id)
        if category:
            query = query.filter(models.AuditLog.category == category)
        if severity:
            query = query.filter(models.AuditLog.severity == severity)
        if start_date:
            query = query.filter(models.AuditLog.timestamp >= start_date)
        if end_date:
            # Add one day to end_date to include the entire day
            query = query.filter(models.AuditLog.timestamp < (end_date + timedelta(days=1)))
            
        return query.order_by(models.AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching audit logs: {e}")
        raise CRUDError("A database error occurred while fetching audit logs.")


# ==================== ALL OTHER CRUD FUNCTIONS (RESTORED) ====================

def get_dashboard_stats(db: Session, location_id: int = None) -> Dict[str, Any]:
    """Get comprehensive dashboard statistics"""
    try:
        stats = {}
        stats["total_patients"] = db.query(models.Patient).count()
        stats["total_appointments"] = db.query(models.Appointment).count()
        stats["appointments_today"] = db.query(models.Appointment).filter(func.date(models.Appointment.start_time) == date.today()).count()
        stats["pending_appointments"] = db.query(models.Appointment).filter(models.Appointment.status.in_(['scheduled', 'confirmed'])).count()
        stats["appointments_week"] = db.query(models.Appointment).filter(models.Appointment.start_time >= (datetime.now() - timedelta(days=7))).count()
        return stats
    except SQLAlchemyError as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def get_appointments(db: Session, skip: int = 0, limit: int = 100, **kwargs) -> List[models.Appointment]:
    """Get appointments with comprehensive filtering"""
    try:
        return db.query(models.Appointment).options(joinedload(models.Appointment.patient)).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching appointments: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def get_appointments_by_date_range(db: Session, start_date: datetime, end_date: datetime, location_id: Optional[int] = None) -> List[models.Appointment]:
    try:
        # --- START EDIT: Add location_id filter ---
        query = db.query(models.Appointment).options(joinedload(models.Appointment.patient)).filter(
            models.Appointment.start_time >= start_date,
            models.Appointment.end_time <= end_date
        )
        if location_id is not None:
            query = query.filter(models.Appointment.location_id == location_id)
        # --- END EDIT ---
        return query.order_by(models.Appointment.start_time.asc()).all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching appointments by range: {e}")
        raise CRUDError("A database error occurred while fetching appointments.")

# ==================== MISSING HELPERS USED BY ROUTERS/SERVICES ====================

def get_patient_by_phone(db: Session, phone_number: str) -> Optional[models.Patient]:
    if not phone_number:
        return None
    phone_hash = encryption_service.hash_for_lookup(phone_number)
    return db.query(models.Patient).filter(models.Patient.phone_hash == phone_hash).first()

def get_patient_by_email(db: Session, email: str) -> Optional[models.Patient]:
    if not email:
        return None
    email_hash = encryption_service.hash_for_lookup(email)
    return db.query(models.Patient).filter(models.Patient.email_hash == email_hash).first()

def get_patient_by_phone_hash(db: Session, phone_number: str) -> Optional[models.Patient]:
    # Alias for services expecting this name
    return get_patient_by_phone(db, phone_number)

def create_patient_document(db: Session, patient_id: int, file_path: str, description: str, user_id: Optional[int]) -> models.Document:
    import hashlib as _hashlib
    # Encrypt stored file path and compute a simple checksum of the path
    encrypted_path = encryption_service.encrypt(file_path)
    checksum = _hashlib.sha256(file_path.encode()).hexdigest()
    document = models.Document(
        patient_id=patient_id,
        name=file_path.split('/')[-1],
        description=description,
        document_type=models.DocumentType.other,
        file_path_encrypted=encrypted_path,
        checksum=checksum,
        encryption_key_id="default",
        uploaded_by=user_id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document

def create_document_for_patient(
    db: Session,
    patient_id: int,
    file_path: str,
    description: str,
    user_id: Optional[int],
    document_type: Optional[models.DocumentType] = None,
    mime_type: Optional[str] = None,
    file_size: Optional[int] = None,
) -> models.Document:
    import hashlib as _hashlib
    encrypted_path = encryption_service.encrypt(file_path)
    checksum = _hashlib.sha256(file_path.encode()).hexdigest()
    document = models.Document(
        patient_id=patient_id,
        name=file_path.split('/')[-1],
        description=description,
        document_type=document_type or models.DocumentType.prescription,
        mime_type=mime_type,
        file_size=file_size,
        file_path_encrypted=encrypted_path,
        checksum=checksum,
        encryption_key_id="default",
        uploaded_by=user_id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document

def get_available_appointment_slots(db: Session, days_ahead: int = 7) -> List[Dict[str, Any]]:
    # Provide simple default slots at 10:00 for location 1 for the next N days
    slots: List[Dict[str, Any]] = []
    today = datetime.now().date()
    ten_am = time(hour=10, minute=0)
    for i in range(days_ahead):
        day = today + timedelta(days=i)
        slots.append({"date": day, "time": ten_am, "location_id": 1})
    return slots

def create_patient_from_whatsapp(db: Session, patient_data: schemas.PatientCreate) -> models.Patient:
    return create_patient(db, patient_data, created_by=None)

def create_or_get_patient_from_payload(db: Session, payload: Dict[str, Any], created_by: Optional[int] = None) -> models.Patient:
    """Single entry point to deduplicate and create a patient from loose payload.
    Supported keys: first_name, last_name, phone_number, email, date_of_birth, city
    If phone or email matches existing, return existing; else create new.
    """
    phone = payload.get('phone_number')
    email = payload.get('email')
    existing = None
    if phone:
        existing = get_patient_by_phone(db, phone)
    if not existing and email:
        existing = get_patient_by_email(db, email)
    if existing:
        return existing
    patient_schema = schemas.PatientCreate(
        first_name=payload.get('first_name') or payload.get('name') or 'Patient',
        last_name=payload.get('last_name'),
        phone_number=phone,
        email=email,
        date_of_birth=payload.get('date_of_birth'),
        city=payload.get('city'),
        gender=payload.get('gender'),
        whatsapp_number=payload.get('whatsapp_number')
    )
    return create_patient(db, patient_schema, created_by=created_by if created_by is not None else None)

def has_active_appointment(db: Session, phone_number: str) -> bool:
    patient = get_patient_by_phone(db, phone_number)
    if not patient:
        return False
    now = datetime.now()
    return db.query(models.Appointment).filter(
        models.Appointment.patient_id == patient.id,
        models.Appointment.start_time >= now,
        models.Appointment.status.in_([models.AppointmentStatus.scheduled, models.AppointmentStatus.confirmed])
    ).first() is not None

def create_appointment_with_validation(db: Session, appointment_data: schemas.AppointmentCreate, phone_number: Optional[str] = None) -> models.Appointment:
    data = appointment_data.dict()
    # Basic conflict check
    conflict = db.query(models.Appointment).filter(
        models.Appointment.location_id == data['location_id'],
        models.Appointment.start_time < data['end_time'],
        models.Appointment.end_time > data['start_time'],
        models.Appointment.status != models.AppointmentStatus.cancelled
    ).first()
    if conflict:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Time slot is not available")
    appt = models.Appointment(**data)
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return appt

def get_patient_upcoming_appointments(db: Session, patient_id: int) -> List[models.Appointment]:
    now = datetime.now()
    return db.query(models.Appointment).filter(
        models.Appointment.patient_id == patient_id,
        models.Appointment.start_time >= now
    ).order_by(models.Appointment.start_time.asc()).all()

def get_whatsapp_session(db: Session, phone_number: str) -> Optional[models.WhatsAppSession]:
    return db.query(models.WhatsAppSession).filter(models.WhatsAppSession.phone_number == phone_number, models.WhatsAppSession.is_active == True).first()

def create_whatsapp_session(db: Session, phone_number: str) -> models.WhatsAppSession:
    session = models.WhatsAppSession(
        phone_number=phone_number,
        session_id=secrets.token_urlsafe(16),
        is_active=True,
        context_data={},
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def update_whatsapp_session(db: Session, session_id: int, context_data: Dict[str, Any]) -> None:
    db.query(models.WhatsAppSession).filter(models.WhatsAppSession.id == session_id).update({
        models.WhatsAppSession.context_data: context_data,
        models.WhatsAppSession.last_activity: datetime.now()
    })
    db.commit()

def create_communication_log(db: Session, log: schemas.CommunicationLogCreate) -> models.CommunicationLog:
    entry = models.CommunicationLog(
        patient_id=log.patient_id,
        communication_type=models.CommunicationType(log.communication_type),
        direction=log.direction,
        content=log.content,
        status=log.status,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

# ==================== PRESCRIPTION SHARING HELPERS ====================

def get_patient_details(db: Session, patient_id: int) -> Optional[Dict[str, Any]]:
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        return None
    name = encryption_service.decrypt(patient.name_encrypted) if patient.name_encrypted else ""
    phone_plain = encryption_service.decrypt(patient.phone_number_encrypted) if patient.phone_number_encrypted else None
    email_plain = encryption_service.decrypt(patient.email_encrypted) if patient.email_encrypted else None
    return {
        "id": patient.id,
        "name": name,
        "whatsapp_number": patient.whatsapp_number,
        "phone_number": phone_plain,
        "email": email_plain,
    }

def create_prescription_share_log(db: Session, user_id: int, patient_id: int, method: str, success: bool) -> None:
    status_text = "success" if success else "failed"
    try:
        create_communication_log(db, schemas.CommunicationLogCreate(
            patient_id=patient_id,
            communication_type=schemas.CommunicationType.whatsapp if method == "whatsapp" else schemas.CommunicationType.email,
            direction="outbound",
            content=f"Prescription shared via {method}: {status_text}",
            status="sent" if success else "failed",
        ))
    except Exception:
        pass

# ==================== SYSTEM CONFIGURATION HELPERS ====================

def get_system_config(db: Session, key: str) -> Optional[models.SystemConfiguration]:
    return db.query(models.SystemConfiguration).filter(models.SystemConfiguration.key == key).first()

def set_system_config(
    db: Session,
    key: str,
    value: Any,
    value_type: str = "string",
    description: Optional[str] = None,
    category: Optional[str] = None,
) -> models.SystemConfiguration:
    entry = get_system_config(db, key)
    if entry is None:
        entry = models.SystemConfiguration(
            key=key,
            value=value,
            value_type=value_type,
            description=description,
            category=category,
        )
        db.add(entry)
    else:
        entry.value = value
        entry.value_type = value_type
        if description is not None:
            entry.description = description
        if category is not None:
            entry.category = category
    db.commit()
    db.refresh(entry)
    return entry
        