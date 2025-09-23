
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_
from datetime import datetime
from . import models, schemas, security

# --- User CRUD Functions ---

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        phone_number=user.phone_number,
        password_hash=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
    
def create_initial_admin_user(db: Session, username: str, password: str):
    """Special function for startup user creation."""
    hashed_password = security.get_password_hash(password)
    db_user = models.User(
        username=username,
        password_hash=hashed_password,
        role=models.UserRole.admin
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.dict(exclude_unset=True)
    if "password" in update_data:
        hashed_password = security.get_password_hash(update_data["password"])
        db_user.password_hash = hashed_password
        del update_data["password"]

    for key, value in update_data.items():
        setattr(db_user, key, value)
        
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    db.delete(db_user)
    db.commit()
    return db_user

# --- Activity Log CRUD Functions ---

def create_activity_log(db: Session, user_id: int, action: str, details: str = None):
    db_log = models.ActivityLog(user_id=user_id, action=action, details=details)
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_activity_logs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ActivityLog).options(joinedload(models.ActivityLog.user)).order_by(models.ActivityLog.timestamp.desc()).offset(skip).limit(limit).all()


# --- Appointment CRUD Functions ---
def get_appointment(db: Session, appointment_id: int):
    return db.query(models.Appointment).options(joinedload(models.Appointment.patient), joinedload(models.Appointment.location)).filter(models.Appointment.id == appointment_id).first()

def get_appointments_by_date_range(db: Session, start_date: datetime, end_date: datetime):
    return db.query(models.Appointment).options(joinedload(models.Appointment.patient), joinedload(models.Appointment.location)).filter(
        and_(
            models.Appointment.start_time >= start_date,
            models.Appointment.start_time < end_date
        )
    ).order_by(models.Appointment.start_time).all()

def create_appointment(db: Session, appointment: schemas.AppointmentCreate, user_id: int):
    db_appointment = models.Appointment(**appointment.dict())
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    # Log the action
    create_activity_log(db, user_id=user_id, action="Create Appointment", details=f"Created appointment for patient ID {db_appointment.patient_id} at {db_appointment.start_time}")
    return db_appointment

def update_appointment_status(db: Session, appointment_id: int, status: str, user_id: int):
    db_appointment = get_appointment(db, appointment_id=appointment_id)
    if not db_appointment:
        return None
    
    original_status = db_appointment.status
    db_appointment.status = status
    db.commit()
    db.refresh(db_appointment)
    # Log the action
    create_activity_log(db, user_id=user_id, action="Update Appointment Status", details=f"Changed status for appointment ID {appointment_id} from '{original_status}' to '{status}'")
    return db_appointment


def get_patient_by_phone(db: Session, phone_number: str):
    return db.query(models.Patient).filter(models.Patient.phone_number == phone_number).first()

def get_patients(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Patient).offset(skip).limit(limit).all()

def create_patient(db: Session, patient: schemas.PatientCreate):
    db_patient = models.Patient(name=patient.name, phone_number=patient.phone_number, email=patient.email)
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

# --- Location CRUD Functions ---

def get_locations(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Location).offset(skip).limit(limit).all()

def create_location(db: Session, location_name: str):
    db_location = models.Location(name=location_name)
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

def create_patient_document(db: Session, patient_id: int, file_path: str, description: str):
    db_doc = models.Document(patient_id=patient_id, file_path=file_path, description=description)
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc

def create_remark(db: Session, patient_id: int, author_id: int, text: str):
    db_remark = models.Remark(patient_id=patient_id, author_id=author_id, text=text)
    db.add(db_remark)
    db.commit()
    db.refresh(db_remark)
    create_activity_log(db, user_id=author_id, action="Add Remark", details=f"Added remark for patient ID {patient_id}")
    return db_remark

def get_patient_details(db: Session, patient_id: int):
    return db.query(models.Patient).options(
        selectinload(models.Patient.appointments).joinedload(models.Appointment.location),
        selectinload(models.Patient.documents),
        selectinload(models.Patient.remarks).joinedload(models.Remark.author)
    ).filter(models.Patient.id == patient_id).first()

