# app/crud.py - Production-ready CRUD operations with encryption and comprehensive error handling
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_, desc, asc, func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any, Union
import logging
from . import models, schemas
from .security import get_password_hash, verify_password, encryption_service

logger = logging.getLogger(__name__)

class CRUDError(Exception):
    """Custom exception for CRUD operations"""
    pass

# ==================== USER CRUD OPERATIONS ====================

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """Get user by ID with error handling"""
    try:
        return db.query(models.User).filter(
            models.User.id == user_id,
            models.User.deleted_at.is_(None)
        ).first()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching user {user_id}: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """Get user by username"""
    try:
        return db.query(models.User).filter(
            models.User.username == username,
            models.User.deleted_at.is_(None)
        ).first()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching user by username {username}: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Get user by email"""
    try:
        return db.query(models.User).filter(
            models.User.email == email,
            models.User.deleted_at.is_(None)
        ).first()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching user by email: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def get_users(db: Session, skip: int = 0, limit: int = 100, role: str = None, is_active: bool = None) -> List[models.User]:
    """Get users with optional filters"""
    try:
        query = db.query(models.User).filter(models.User.deleted_at.is_(None))
        
        if role:
            query = query.filter(models.User.role == role)
        if is_active is not None:
            query = query.filter(models.User.is_active == is_active)
        
        return query.order_by(models.User.username).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def create_user(db: Session, user: schemas.UserCreate, created_by: int = None) -> models.User:
    """Create new user with comprehensive validation"""
    try:
        # Check for existing username
        if get_user_by_username(db, user.username):
            raise CRUDError("Username already exists")
        
        # Check for existing email
        if get_user_by_email(db, user.email):
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
            password_last_changed=datetime.utcnow(),
            permissions={}
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"Created new user: {user.username} (ID: {db_user.id})")
        return db_user
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error creating user {user.username}: {str(e)}")
        raise CRUDError("User creation failed due to data constraints")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating user {user.username}: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate, updated_by: int = None) -> Optional[models.User]:
    """Update user with validation and audit trail"""
    try:
        db_user = get_user(db, user_id)
        if not db_user:
            return None
        
        update_data = user_update.dict(exclude_unset=True)
        
        # Handle password update
        if "password" in update_data and update_data["password"]:
            update_data["password_hash"] = get_password_hash(update_data["password"])
            update_data["password_last_changed"] = datetime.utcnow()
            update_data["must_change_password"] = False
            del update_data["password"]
        
        # Check for username/email uniqueness if being updated
        if "username" in update_data:
            existing = get_user_by_username(db, update_data["username"])
            if existing and existing.id != user_id:
                raise CRUDError("Username already exists")
        
        if "email" in update_data:
            existing = get_user_by_email(db, update_data["email"])
            if existing and existing.id != user_id:
                raise CRUDError("Email already exists")
        
        # Apply updates
        for field, value in update_data.items():
            if hasattr(db_user, field):
                setattr(db_user, field, value)
        
        db_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"Updated user: {db_user.username} (ID: {user_id})")
        return db_user
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error updating user {user_id}: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def soft_delete_user(db: Session, user_id: int, deleted_by: int = None) -> bool:
    """Soft delete user (set deleted_at timestamp)"""
    try:
        db_user = get_user(db, user_id)
        if not db_user:
            return False
        
        db_user.deleted_at = datetime.utcnow()
        db_user.is_active = False
        db.commit()
        
        logger.info(f"Soft deleted user: {db_user.username} (ID: {user_id})")
        return True
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error soft deleting user {user_id}: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

# ==================== PATIENT CRUD OPERATIONS WITH ENCRYPTION ====================

def _encrypt_patient_fields(patient_data: dict) -> dict:
    """Encrypt sensitive patient fields and create hashes"""
    encrypted_data = {}
    
    if "name" in patient_data:
        encrypted_data["name_encrypted"] = encryption_service.encrypt(patient_data["name"])
        encrypted_data["name_hash"] = encryption_service.hash_for_lookup(patient_data["name"])
    
    if "phone_number" in patient_data and patient_data["phone_number"]:
        encrypted_data["phone_number_encrypted"] = encryption_service.encrypt(patient_data["phone_number"])
        encrypted_data["phone_hash"] = encryption_service.hash_for_lookup(patient_data["phone_number"])
    
    if "email" in patient_data and patient_data["email"]:
        encrypted_data["email_encrypted"] = encryption_service.encrypt(patient_data["email"])
        encrypted_data["email_hash"] = encryption_service.hash_for_lookup(patient_data["email"])
    
    if "address" in patient_data and patient_data["address"]:
        encrypted_data["address_encrypted"] = encryption_service.encrypt(patient_data["address"])
    
    if "emergency_contact" in patient_data and patient_data["emergency_contact"]:
        encrypted_data["emergency_contact_encrypted"] = encryption_service.encrypt(patient_data["emergency_contact"])
        encrypted_data["emergency_contact_hash"] = encryption_service.hash_for_lookup(patient_data["emergency_contact"])
    
    if "insurance_number" in patient_data and patient_data["insurance_number"]:
        encrypted_data["insurance_number_encrypted"] = encryption_service.encrypt(patient_data["insurance_number"])
        encrypted_data["insurance_number_hash"] = encryption_service.hash_for_lookup(patient_data["insurance_number"])
    
    return encrypted_data

def _decrypt_patient_fields(patient: models.Patient) -> models.Patient:
    """Decrypt patient fields for display"""
    try:
        if patient.name_encrypted:
            patient.name = encryption_service.decrypt(patient.name_encrypted)
        
        if patient.phone_number_encrypted:
            patient.phone_number = encryption_service.decrypt(patient.phone_number_encrypted)
        
        if patient.email_encrypted:
            patient.email = encryption_service.decrypt(patient.email_encrypted)
        
        if patient.address_encrypted:
            patient.address = encryption_service.decrypt(patient.address_encrypted)
        
        if patient.emergency_contact_encrypted:
            patient.emergency_contact = encryption_service.decrypt(patient.emergency_contact_encrypted)
        
        if patient.insurance_number_encrypted:
            patient.insurance_number = encryption_service.decrypt(patient.insurance_number_encrypted)
        
    except Exception as e:
        logger.error(f"Error decrypting patient data for patient {patient.id}: {str(e)}")
        # Continue without decryption rather than failing
    
    return patient

def get_patient(db: Session, patient_id: int) -> Optional[models.Patient]:
    """Get patient by ID with decryption"""
    try:
        patient = db.query(models.Patient).filter(
            models.Patient.id == patient_id,
            models.Patient.is_active == True
        ).first()
        
        if patient:
            patient = _decrypt_patient_fields(patient)
        
        return patient
    except SQLAlchemyError as e:
        logger.error(f"Error fetching patient {patient_id}: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def get_patient_by_phone(db: Session, phone_number: str) -> Optional[models.Patient]:
    """Get patient by phone number using hash lookup"""
    try:
        phone_hash = encryption_service.hash_for_lookup(phone_number)
        patient = db.query(models.Patient).filter(
            models.Patient.phone_hash == phone_hash,
            models.Patient.is_active == True
        ).first()
        
        if patient:
            patient = _decrypt_patient_fields(patient)
        
        return patient
    except SQLAlchemyError as e:
        logger.error(f"Error fetching patient by phone: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def get_patient_by_email(db: Session, email: str) -> Optional[models.Patient]:
    """Get patient by email using hash lookup"""
    try:
        email_hash = encryption_service.hash_for_lookup(email)
        patient = db.query(models.Patient).filter(
            models.Patient.email_hash == email_hash,
            models.Patient.is_active == True
        ).first()
        
        if patient:
            patient = _decrypt_patient_fields(patient)
        
        return patient
    except SQLAlchemyError as e:
        logger.error(f"Error fetching patient by email: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def search_patients(db: Session, search_term: str, skip: int = 0, limit: int = 100) -> List[models.Patient]:
    """Search patients by name, phone, or email using hash lookups"""
    try:
        search_hash = encryption_service.hash_for_lookup(search_term)
        
        # Search by phone hash, email hash, or name hash
        patients = db.query(models.Patient).filter(
            or_(
                models.Patient.phone_hash == search_hash,
                models.Patient.email_hash == search_hash,
                models.Patient.name_hash == search_hash
            ),
            models.Patient.is_active == True
        ).offset(skip).limit(limit).all()
        
        # Decrypt fields for all patients
        decrypted_patients = []
        for patient in patients:
            decrypted_patients.append(_decrypt_patient_fields(patient))
        
        return decrypted_patients
    except SQLAlchemyError as e:
        logger.error(f"Error searching patients: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def get_patients(db: Session, skip: int = 0, limit: int = 100, search: str = None) -> List[models.Patient]:
    """Get patients with optional search"""
    try:
        if search:
            return search_patients(db, search, skip, limit)
        
        patients = db.query(models.Patient).filter(
            models.Patient.is_active == True
        ).order_by(models.Patient.created_at.desc()).offset(skip).limit(limit).all()
        
        # Decrypt fields for all patients
        decrypted_patients = []
        for patient in patients:
            decrypted_patients.append(_decrypt_patient_fields(patient))
        
        return decrypted_patients
    except SQLAlchemyError as e:
        logger.error(f"Error fetching patients: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def create_patient(db: Session, patient: schemas.PatientCreate, created_by: int) -> models.Patient:
    """Create patient with field encryption"""
    try:
        # Check for existing patient by phone or email
        if patient.phone_number and get_patient_by_phone(db, patient.phone_number):
            raise CRUDError("Patient with this phone number already exists")
        
        if patient.email and get_patient_by_email(db, patient.email):
            raise CRUDError("Patient with this email already exists")
        
        # Prepare patient data
        patient_dict = patient.dict()
        encrypted_fields = _encrypt_patient_fields(patient_dict)
        
        # Create patient record
        db_patient = models.Patient(
            **encrypted_fields,
            date_of_birth=patient.date_of_birth,
            gender=patient.gender,
            blood_type=patient.blood_type,
            allergies=patient.allergies,
            insurance_provider=patient.insurance_provider,
            preferred_communication=patient.preferred_communication,
            communication_preferences=patient.communication_preferences,
            whatsapp_number=patient.whatsapp_number,
            whatsapp_opt_in=patient.whatsapp_opt_in,
            whatsapp_opt_in_date=datetime.utcnow() if patient.whatsapp_opt_in else None,
            hipaa_authorization=patient.hipaa_authorization,
            hipaa_authorization_date=datetime.utcnow() if patient.hipaa_authorization else None,
            consent_to_treatment=patient.consent_to_treatment,
            consent_to_treatment_date=datetime.utcnow() if patient.consent_to_treatment else None,
            marketing_consent=patient.marketing_consent,
            language_preference=patient.language_preference or "en",
            created_by=created_by
        )
        
        db.add(db_patient)
        db.commit()
        db.refresh(db_patient)
        
        # Decrypt fields for response
        db_patient = _decrypt_patient_fields(db_patient)
        
        logger.info(f"Created new patient: ID {db_patient.id}")
        return db_patient
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error creating patient: {str(e)}")
        raise CRUDError("Patient creation failed due to data constraints")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating patient: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def update_patient(db: Session, patient_id: int, patient_update: schemas.PatientUpdate, updated_by: int = None) -> Optional[models.Patient]:
    """Update patient with field encryption"""
    try:
        db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
        if not db_patient:
            return None
        
        update_dict = patient_update.dict(exclude_unset=True)
        
        # Handle encrypted fields
        encrypted_updates = _encrypt_patient_fields(update_dict)
        
        # Apply all updates
        all_updates = {**update_dict, **encrypted_updates}
        
        for field, value in all_updates.items():
            if hasattr(db_patient, field) and field not in ["name", "phone_number", "email", "address", "emergency_contact", "insurance_number"]:
                setattr(db_patient, field, value)
            elif hasattr(db_patient, field + "_encrypted"):
                # Skip plain text fields that are now encrypted
                continue
            elif hasattr(db_patient, field):
                setattr(db_patient, field, value)
        
        db_patient.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_patient)
        
        # Decrypt fields for response
        db_patient = _decrypt_patient_fields(db_patient)
        
        logger.info(f"Updated patient: ID {patient_id}")
        return db_patient
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error updating patient {patient_id}: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

# ==================== APPOINTMENT CRUD OPERATIONS ====================

def get_appointment(db: Session, appointment_id: int) -> Optional[models.Appointment]:
    """Get appointment with related data"""
    try:
        appointment = db.query(models.Appointment).options(
            joinedload(models.Appointment.patient),
            joinedload(models.Appointment.location),
            joinedload(models.Appointment.user)
        ).filter(models.Appointment.id == appointment_id).first()
        
        if appointment and appointment.patient:
            appointment.patient = _decrypt_patient_fields(appointment.patient)
        
        return appointment
    except SQLAlchemyError as e:
        logger.error(f"Error fetching appointment {appointment_id}: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def get_appointments(db: Session, skip: int = 0, limit: int = 100, 
                    start_date: datetime = None, end_date: datetime = None,
                    status: str = None, location_id: int = None,
                    patient_id: int = None, user_id: int = None) -> List[models.Appointment]:
    """Get appointments with comprehensive filtering"""
    try:
        query = db.query(models.Appointment).options(
            joinedload(models.Appointment.patient),
            joinedload(models.Appointment.location),
            joinedload(models.Appointment.user)
        )
        
        # Apply filters
        if start_date:
            query = query.filter(models.Appointment.start_time >= start_date)
        if end_date:
            query = query.filter(models.Appointment.start_time <= end_date)
        if status:
            query = query.filter(models.Appointment.status == status)
        if location_id:
            query = query.filter(models.Appointment.location_id == location_id)
        if patient_id:
            query = query.filter(models.Appointment.patient_id == patient_id)
        if user_id:
            query = query.filter(models.Appointment.user_id == user_id)
        
        appointments = query.order_by(models.Appointment.start_time.desc()).offset(skip).limit(limit).all()
        
        # Decrypt patient data
        for appointment in appointments:
            if appointment.patient:
                appointment.patient = _decrypt_patient_fields(appointment.patient)
        
        return appointments
    except SQLAlchemyError as e:
        logger.error(f"Error fetching appointments: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def create_appointment(db: Session, appointment: schemas.AppointmentCreate, user_id: int = None) -> models.Appointment:
    """Create appointment with validation"""
    try:
        # Validate patient exists
        patient = get_patient(db, appointment.patient_id)
        if not patient:
            raise CRUDError("Patient not found")
        
        # Validate location exists
        location = db.query(models.Location).filter(models.Location.id == appointment.location_id).first()
        if not location:
            raise CRUDError("Location not found")
        
        # Check for scheduling conflicts
        existing_appointment = db.query(models.Appointment).filter(
            models.Appointment.location_id == appointment.location_id,
            models.Appointment.start_time < appointment.end_time,
            models.Appointment.end_time > appointment.start_time,
            models.Appointment.status.in_(["scheduled", "confirmed", "checked_in", "in_progress"])
        ).first()
        
        if existing_appointment:
            raise CRUDError("Time slot is already booked")
        
        # Calculate duration
        duration = int((appointment.end_time - appointment.start_time).total_seconds() / 60)
        
        db_appointment = models.Appointment(
            patient_id=appointment.patient_id,
            location_id=appointment.location_id,
            user_id=user_id,
            start_time=appointment.start_time,
            end_time=appointment.end_time,
            duration_minutes=duration,
            appointment_type=appointment.appointment_type,
            reason=appointment.reason,
            chief_complaint=appointment.chief_complaint,
            notes=appointment.notes,
            status=appointment.status,
            priority=appointment.priority or "normal"
        )
        
        db.add(db_appointment)
        db.commit()
        db.refresh(db_appointment)
        
        # Load relationships
        db_appointment = get_appointment(db, db_appointment.id)
        
        logger.info(f"Created new appointment: ID {db_appointment.id}")
        return db_appointment
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error creating appointment: {str(e)}")
        raise CRUDError("Appointment creation failed due to data constraints")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating appointment: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def update_appointment(db: Session, appointment_id: int, appointment_update: schemas.AppointmentUpdate) -> Optional[models.Appointment]:
    """Update appointment with validation"""
    try:
        db_appointment = get_appointment(db, appointment_id)
        if not db_appointment:
            return None
        
        update_dict = appointment_update.dict(exclude_unset=True)
        
        # Validate time changes don't create conflicts
        if "start_time" in update_dict or "end_time" in update_dict:
            new_start = update_dict.get("start_time", db_appointment.start_time)
            new_end = update_dict.get("end_time", db_appointment.end_time)
            
            # Check for conflicts (excluding current appointment)
            existing_appointment = db.query(models.Appointment).filter(
                models.Appointment.id != appointment_id,
                models.Appointment.location_id == db_appointment.location_id,
                models.Appointment.start_time < new_end,
                models.Appointment.end_time > new_start,
                models.Appointment.status.in_(["scheduled", "confirmed", "checked_in", "in_progress"])
            ).first()
            
            if existing_appointment:
                raise CRUDError("Updated time slot conflicts with existing appointment")
            
            # Update duration
            duration = int((new_end - new_start).total_seconds() / 60)
            update_dict["duration_minutes"] = duration
        
        # Apply updates
        for field, value in update_dict.items():
            if hasattr(db_appointment, field):
                setattr(db_appointment, field, value)
        
        # Update workflow timestamps based on status changes
        if "status" in update_dict:
            now = datetime.utcnow()
            if update_dict["status"] == "confirmed" and not db_appointment.confirmed_at:
                db_appointment.confirmed_at = now
            elif update_dict["status"] == "checked_in" and not db_appointment.checked_in_at:
                db_appointment.checked_in_at = now
            elif update_dict["status"] == "in_progress" and not db_appointment.started_at:
                db_appointment.started_at = now
            elif update_dict["status"] == "completed" and not db_appointment.completed_at:
                db_appointment.completed_at = now
            elif update_dict["status"] == "cancelled":
                db_appointment.cancelled_at = now
        
        db_appointment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_appointment)
        
        logger.info(f"Updated appointment: ID {appointment_id}")
        return db_appointment
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error updating appointment {appointment_id}: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def update_appointment_calendar_event(db: Session, appointment_id: int, event_id: str) -> bool:
    """Update appointment with Google Calendar event ID"""
    try:
        db_appointment = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
        if db_appointment:
            db_appointment.google_calendar_event_id = event_id
            db.commit()
            return True
        return False
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error updating calendar event for appointment {appointment_id}: {str(e)}")
        return False

# ==================== LOCATION CRUD OPERATIONS ====================

def get_location(db: Session, location_id: int) -> Optional[models.Location]:
    """Get location by ID"""
    try:
        return db.query(models.Location).filter(
            models.Location.id == location_id,
            models.Location.is_active == True
        ).first()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching location {location_id}: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def get_locations(db: Session, skip: int = 0, limit: int = 100, is_active: bool = True) -> List[models.Location]:
    """Get locations with optional filtering"""
    try:
        query = db.query(models.Location)
        
        if is_active is not None:
            query = query.filter(models.Location.is_active == is_active)
        
        return query.order_by(models.Location.name).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching locations: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def create_location(db: Session, location: schemas.LocationCreate, created_by: int = None) -> models.Location:
    """Create new location"""
    try:
        db_location = models.Location(**location.dict())
        db.add(db_location)
        db.commit()
        db.refresh(db_location)
        
        logger.info(f"Created new location: {location.name} (ID: {db_location.id})")
        return db_location
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error creating location: {str(e)}")
        raise CRUDError("Location creation failed due to data constraints")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating location: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

# ==================== PRESCRIPTION CRUD OPERATIONS ====================

def get_prescriptions_for_patient(db: Session, patient_id: int, is_active: bool = None) -> List[models.Prescription]:
    """Get prescriptions for a patient"""
    try:
        query = db.query(models.Prescription).options(
            joinedload(models.Prescription.prescriber)
        ).filter(models.Prescription.patient_id == patient_id)
        
        if is_active is not None:
            query = query.filter(models.Prescription.is_active == is_active)
        
        return query.order_by(models.Prescription.prescribed_date.desc()).all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching prescriptions for patient {patient_id}: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def create_prescription(db: Session, prescription: schemas.PrescriptionCreate, prescribed_by: int) -> models.Prescription:
    """Create new prescription"""
    try:
        # Validate patient exists
        patient = get_patient(db, prescription.patient_id)
        if not patient:
            raise CRUDError("Patient not found")
        
        # Validate prescriber exists and has appropriate role
        prescriber = get_user(db, prescribed_by)
        if not prescriber or prescriber.role not in ["doctor", "nurse", "admin"]:
            raise CRUDError("Invalid prescriber")
        
        db_prescription = models.Prescription(
            **prescription.dict(),
            prescribed_by=prescribed_by
        )
        
        db.add(db_prescription)
        db.commit()
        db.refresh(db_prescription)
        
        logger.info(f"Created new prescription: ID {db_prescription.id} for patient {prescription.patient_id}")
        return db_prescription
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error creating prescription: {str(e)}")
        raise CRUDError("Prescription creation failed due to data constraints")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating prescription: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

# ==================== COMMUNICATION CRUD OPERATIONS ====================

def log_communication(db: Session, communication: schemas.CommunicationLogCreate) -> models.CommunicationLog:
    """Log communication with patient"""
    try:
        db_communication = models.CommunicationLog(**communication.dict())
        db.add(db_communication)
        db.commit()
        db.refresh(db_communication)
        
        return db_communication
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error logging communication: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def get_patient_communications(db: Session, patient_id: int, skip: int = 0, limit: int = 100) -> List[models.CommunicationLog]:
    """Get communications for a patient"""
    try:
        return db.query(models.CommunicationLog).filter(
            models.CommunicationLog.patient_id == patient_id
        ).order_by(models.CommunicationLog.sent_at.desc()).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching communications for patient {patient_id}: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

# ==================== WHATSAPP SESSION OPERATIONS ====================

def get_whatsapp_session(db: Session, phone_number: str) -> Optional[models.WhatsAppSession]:
    """Get active WhatsApp session by phone number"""
    try:
        return db.query(models.WhatsAppSession).filter(
            models.WhatsAppSession.phone_number == phone_number,
            models.WhatsAppSession.is_active == True
        ).first()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching WhatsApp session: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def create_whatsapp_session(db: Session, phone_number: str, patient_id: int = None) -> models.WhatsAppSession:
    """Create new WhatsApp session"""
    try:
        # Deactivate any existing sessions for this number
        db.query(models.WhatsAppSession).filter(
            models.WhatsAppSession.phone_number == phone_number
        ).update({"is_active": False})
        
        session_id = f"wa_{phone_number}_{int(datetime.utcnow().timestamp())}"
        
        db_session = models.WhatsAppSession(
            phone_number=phone_number,
            patient_id=patient_id,
            session_id=session_id,
            context_data={}
        )
        
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        
        return db_session
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating WhatsApp session: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def update_whatsapp_session(db: Session, session_id: int, context_data: dict = None, 
                           current_flow: str = None, flow_step: str = None) -> bool:
    """Update WhatsApp session context"""
    try:
        db_session = db.query(models.WhatsAppSession).filter(models.WhatsAppSession.id == session_id).first()
        if db_session:
            if context_data is not None:
                db_session.context_data = context_data
            if current_flow is not None:
                db_session.current_flow = current_flow
            if flow_step is not None:
                db_session.flow_step = flow_step
            
            db_session.last_activity = datetime.utcnow()
            db_session.message_count += 1
            db.commit()
            return True
        return False
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error updating WhatsApp session {session_id}: {str(e)}")
        return False

# ==================== AUDIT LOG OPERATIONS ====================

def create_audit_log(db: Session, user_id: int = None, action: str = None, 
                    resource_type: str = None, resource_id: int = None, 
                    details: dict = None, old_values: dict = None, 
                    new_values: dict = None, ip_address: str = None, 
                    user_agent: str = None, session_id: str = None,
                    business_justification: str = None) -> models.AuditLog:
    """Create comprehensive audit log entry"""
    try:
        # Get user info for denormalization
        username = None
        user_role = None
        if user_id:
            user = get_user(db, user_id)
            if user:
                username = user.username
                user_role = user.role
        
        audit_log = models.AuditLog(
            user_id=user_id,
            username=username,
            user_role=user_role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            business_justification=business_justification
        )
        
        db.add(audit_log)
        db.commit()
        
        return audit_log
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating audit log: {str(e)}")
        # Don't raise exception for audit logs to avoid breaking main operations
        return None

def get_audit_logs(db: Session, skip: int = 0, limit: int = 100, 
                  user_id: int = None, action: str = None, 
                  resource_type: str = None, start_date: datetime = None, 
                  end_date: datetime = None) -> List[models.AuditLog]:
    """Get audit logs with comprehensive filtering"""
    try:
        query = db.query(models.AuditLog).options(joinedload(models.AuditLog.user))
        
        if user_id:
            query = query.filter(models.AuditLog.user_id == user_id)
        if action:
            query = query.filter(models.AuditLog.action == action)
        if resource_type:
            query = query.filter(models.AuditLog.resource_type == resource_type)
        if start_date:
            query = query.filter(models.AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(models.AuditLog.timestamp <= end_date)
        
        return query.order_by(models.AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching audit logs: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

# ==================== DASHBOARD STATISTICS ====================

def get_dashboard_stats(db: Session, location_id: int = None, date_from: date = None, date_to: date = None) -> Dict[str, Any]:
    """Get comprehensive dashboard statistics"""
    try:
        stats = {}
        
        # Base queries
        patients_query = db.query(models.Patient).filter(models.Patient.is_active == True)
        appointments_query = db.query(models.Appointment)
        
        if location_id:
            appointments_query = appointments_query.filter(models.Appointment.location_id == location_id)
        
        # Total patients
        stats["total_patients"] = patients_query.count()
        
        # Total appointments
        stats["total_appointments"] = appointments_query.count()
        
        # Today's appointments
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        stats["appointments_today"] = appointments_query.filter(
            models.Appointment.start_time >= today_start,
            models.Appointment.start_time <= today_end
        ).count()
        
        # Pending appointments (scheduled, confirmed)
        stats["pending_appointments"] = appointments_query.filter(
            models.Appointment.status.in_(["scheduled", "confirmed"])
        ).count()
        
        # This week's appointments
        week_start = today - timedelta(days=today.weekday())
        week_start_dt = datetime.combine(week_start, datetime.min.time())
        week_end_dt = week_start_dt + timedelta(days=7)
        
        stats["appointments_week"] = appointments_query.filter(
            models.Appointment.start_time >= week_start_dt,
            models.Appointment.start_time < week_end_dt
        ).count()
        
        # Appointment status breakdown
        status_stats = db.query(
            models.Appointment.status,
            func.count(models.Appointment.id).label('count')
        ).group_by(models.Appointment.status).all()
        
        stats["appointments_by_status"] = {status: count for status, count in status_stats}
        
        # Recent patient registrations (last 30 days)
        month_ago = datetime.utcnow() - timedelta(days=30)
        stats["new_patients_month"] = patients_query.filter(
            models.Patient.created_at >= month_ago
        ).count()
        
        # Communication statistics
        comm_stats = db.query(
            models.CommunicationLog.communication_type,
            func.count(models.CommunicationLog.id).label('count')
        ).filter(
            models.CommunicationLog.sent_at >= month_ago
        ).group_by(models.CommunicationLog.communication_type).all()
        
        stats["communications_month"] = {comm_type: count for comm_type, count in comm_stats}
        
        return stats
    except SQLAlchemyError as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

# ==================== NOTIFICATION QUEUE OPERATIONS ====================

def queue_notification(db: Session, notification: schemas.NotificationCreate) -> models.NotificationQueue:
    """Queue a notification for sending"""
    try:
        db_notification = models.NotificationQueue(**notification.dict())
        db.add(db_notification)
        db.commit()
        db.refresh(db_notification)
        return db_notification
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error queuing notification: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def get_pending_notifications(db: Session, limit: int = 50) -> List[models.NotificationQueue]:
    """Get pending notifications for processing"""
    try:
        now = datetime.utcnow()
        return db.query(models.NotificationQueue).filter(
            models.NotificationQueue.status == "pending",
            models.NotificationQueue.scheduled_for <= now
        ).order_by(
            models.NotificationQueue.priority.desc(),
            models.NotificationQueue.scheduled_for.asc()
        ).limit(limit).all()
    except SQLAlchemyError as e:
        logger.error(f"Error fetching pending notifications: {str(e)}")
        raise CRUDError(f"Database error: {str(e)}")

def update_notification_status(db: Session, notification_id: int, status: str, 
                             error_message: str = None, sent_at: datetime = None) -> bool:
    """Update notification status"""
    try:
        notification = db.query(models.NotificationQueue).filter(
            models.NotificationQueue.id == notification_id
        ).first()
        
        if notification:
            notification.status = status
            notification.attempts += 1
            notification.last_attempt_at = datetime.utcnow()
            
            if error_message:
                notification.error_message = error_message
                
            if sent_at:
                notification.sent_at = sent_at
            
            # Schedule retry if failed and under max attempts
            if status == "failed" and notification.attempts < notification.max_attempts:
                notification.status = "pending"
                notification.next_retry_at = datetime.utcnow() + timedelta(minutes=5 * notification.attempts)
            
            db.commit()
            return True
        return False
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error updating notification status: {str(e)}")
        return False