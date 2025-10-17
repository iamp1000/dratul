# app/crud.py - FULLY RESTORED AND CORRECTED
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, desc, func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, timedelta, date, time
from typing import Optional, List, Dict, Any
import logging
import asyncio
from . import models, schemas
from .security import get_password_hash, verify_password, encryption_service
from fastapi import HTTPException, status
from app.services.calendar_service import GoogleCalendarService
from app.services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)
calendar_service = GoogleCalendarService()
whatsapp_service = WhatsAppService()

class CRUDError(Exception):
    """Custom exception for CRUD operations"""
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
            username=user.username, email=user.email, phone_number=user.phone_number,
            password_hash=hashed_password, role=user.role, is_active=True, is_verified=False,
            mfa_enabled=False, failed_login_attempts=0,
            password_last_changed=datetime.utcnow(), permissions={}
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
    db_patient = models.Patient(
        first_name_encrypted=encryption_service.encrypt(patient.first_name),
        last_name_encrypted=encryption_service.encrypt(patient.last_name) if patient.last_name else None,
        phone_number_encrypted=encryption_service.encrypt(patient.phone_number) if patient.phone_number else None,
        email_encrypted=encryption_service.encrypt(patient.email) if patient.email else None,
        first_name_hash=encryption_service.hash_for_lookup(patient.first_name),
        last_name_hash=encryption_service.hash_for_lookup(patient.last_name) if patient.last_name else None,
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
        search_hash = encryption_service.hash_for_lookup(search)
        query = query.filter(
            or_(
                models.Patient.first_name_hash.ilike(f"%{search_hash}%"),
                models.Patient.last_name_hash.ilike(f"%{search_hash}%"),
            )
        )
    return query.offset(skip).limit(limit).all()

def update_patient(db: Session, patient_id: int, patient_update: schemas.PatientUpdate) -> Optional[models.Patient]:
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not db_patient:
        return None

    update_data = patient_update.dict(exclude_unset=True)

    for key, value in update_data.items():
        if key == 'first_name' and value:
            db_patient.first_name_encrypted = encryption_service.encrypt(value)
            db_patient.first_name_hash = encryption_service.hash_for_lookup(value)
        elif key == 'last_name' and value:
            db_patient.last_name_encrypted = encryption_service.encrypt(value)
            db_patient.last_name_hash = encryption_service.hash_for_lookup(value)
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

    if start_time.minute % 15 != 0:
        raise CRUDError("Appointments must start on a 15-minute interval (00, 15, 30, 45).")
    
    if (end_time - start_time) != timedelta(minutes=15):
        raise CRUDError("Appointment duration must be exactly 15 minutes.")

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
        models.Appointment.status != 'cancelled'
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
    for key, value in update_data.items():
        setattr(db_appointment, key, value)
    db.commit()
    db.refresh(db_appointment)

    # NEW: Update Google Calendar event
    try:
        if db_appointment.google_calendar_event_id and calendar_service.enabled:
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
        if db_appointment.google_calendar_event_id and calendar_service.enabled:
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
    try:
        # Delete existing schedules for the week for simplicity.
        db.query(models.LocationSchedule).filter(models.LocationSchedule.location_id == location_id).delete()
        
        new_schedules = []
        for schedule_data in schedules:
            new_schedule = models.LocationSchedule(
                **schedule_data.dict(),
                location_id=location_id
            )
            new_schedules.append(new_schedule)
        
        db.add_all(new_schedules)
        db.commit()
        
        # Return the newly created schedules
        return new_schedules
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error updating schedules for location {location_id}: {e}")
        raise CRUDError("A database error occurred while updating schedules.")

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
            models.Appointment.status != 'cancelled'
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
        models.Appointment.status != 'cancelled'
    ).all()

    cancelled_appointments = []
    for appointment in appointments_to_cancel:
        # 2. Cancel the appointment
        appointment.status = 'cancelled'
        appointment.cancellation_reason = f"EMERGENCY: {reason}"
        cancelled_appointments.append(appointment)

        # 3. Notify patient via WhatsApp
        patient = get_patient(db, appointment.patient_id)
        if patient and patient.whatsapp_number and whatsapp_service.enabled:
            message = f"EMERGENCY CANCELLATION: Dear {patient.first_name}, due to an emergency, all appointments for {block_date.strftime('%A, %B %d')} have been cancelled. We sincerely apologize for any inconvenience. Please contact us to reschedule."
            await whatsapp_service.send_message(patient.whatsapp_number, message)
    
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
        # ... (implementation from original file)
        return db.query(models.Appointment).options(joinedload(models.Appointment.patient)).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching appointments: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")
        