# app/models.py
from datetime import datetime, time
from sqlalchemy import (
    Column, Integer, String, DateTime, Time, ForeignKey, Text, Date,
    Enum as SQLAlchemyEnum, Boolean, LargeBinary, JSON, Numeric, Index,
    UniqueConstraint  # <-- Import added here
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import enum

# Enhanced Enum Classes for better type safety
class UserRole(str, enum.Enum):
    admin = "admin"
    staff = "staff" 
    doctor = "doctor"
    nurse = "nurse"
    receptionist = "receptionist"
    manager = "manager"
    
    @property
    def mfa_enabled(self):
        return False
    
    @property 
    def is_active(self):
        return True
    
    @property
    def failed_login_attempts(self):
        return 0
    
    @property
    def account_locked_until(self):
        return None
    
    @property
    def permissions(self):
        return {}


class AppointmentStatus(str, enum.Enum):
    scheduled = "scheduled"
    confirmed = "confirmed"
    checked_in = "checked_in"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"
    rescheduled = "rescheduled"

class CommunicationType(str, enum.Enum):
    whatsapp = "whatsapp"
    email = "email"
    sms = "sms"
    phone = "phone"

class AuditAction(str, enum.Enum):
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    MFA_SETUP = "MFA_SETUP"
    MFA_VERIFY = "MFA_VERIFY"
    PASSWORD_RESET = "PASSWORD_RESET"
    ACCESS_DENIED = "ACCESS_DENIED"
    EXPORT = "EXPORT"
    PRINT = "PRINT"
    BULK_ACTION = "BULK_ACTION"

class DocumentType(str, enum.Enum):
    medical_record = "medical_record"
    prescription = "prescription"
    lab_result = "lab_result"
    insurance_card = "insurance_card"
    consent_form = "consent_form"
    identification = "identification"
    other = "other"

# User Management Models
class User(Base):
    """Enhanced User model with comprehensive security features"""
    __tablename__ = "users"
    __table_args__ = (
        Index('idx_users_username', 'username'),
        Index('idx_users_email', 'email'),
        Index('idx_users_role_active', 'role', 'is_active'),
    )

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLAlchemyEnum(UserRole, name='user_role'), default=UserRole.staff, nullable=False)
    
    created_patients = relationship("Patient", back_populates="creator", foreign_keys="Patient.created_by")
    appointments = relationship("Appointment", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    prescribed_medications = relationship("Prescription", back_populates="prescriber")
    uploaded_documents = relationship("Document", back_populates="uploader")
    remarks_authored = relationship("Remark", back_populates="author")
    
    # Enhanced security fields
    mfa_secret = Column(String(32), nullable=True)
    mfa_backup_codes = Column(JSON, nullable=True)
    mfa_enabled = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime(timezone=True), nullable=True)
    password_last_changed = Column(DateTime(timezone=True), nullable=True)
    must_change_password = Column(Boolean, default=False)
    
    # Session and security tracking
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_login_ip = Column(String(45), nullable=True)
    current_session_id = Column(String(255), nullable=True)
    
    # Account status and permissions
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    permissions = Column(JSON, nullable=True)  # Custom permissions per user
    is_super_admin = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete


# Enum for AppointmentSlot status
class SlotStatus(str, enum.Enum):
    available = "available"
    booked = "booked"
    unavailable = "unavailable" # Could be used if manually blocked or during generation if needed

# ==================== EMR / Consultation Models (NEW) ====================


class Consultation(Base):
    """Represents a single clinical encounter or consultation."""
    __tablename__ = "consultations"
    __table_args__ = (
        Index('idx_consultations_patient_date', 'patient_id', 'consultation_date'),
        Index('idx_consultations_user_date', 'user_id', 'consultation_date'),
        Index('idx_consultations_appointment', 'appointment_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # Doctor who conducted
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True, unique=True) # Link to the scheduled appt
    consultation_date = Column(DateTime(timezone=True), nullable=False, default=func.now())

    # Subjective
    complaints = Column(Text, nullable=True)
    history_of_presenting_illness = Column(Text, nullable=True) # Or break down further

    # Objective
    quick_notes = Column(Text, nullable=True) # Could store Quill Delta JSON here
    systemic_examination = Column(Text, nullable=True) # Could store Quill Delta JSON here
    
    # Assessment
    # Diagnoses are stored in a separate table (ConsultationDiagnosis)

    # Plan
    # Medications are stored in a separate table (ConsultationMedication)
    investigations_notes = Column(Text, nullable=True) # E.g., "CBC, LFT, KFT"
    tests_requested = Column(Text, nullable=True)
    usg_findings = Column(Text, nullable=True) # Quill Delta JSON
    lab_tests_imaging = Column(Text, nullable=True) # Quill Delta JSON
    advice = Column(Text, nullable=True) # Quill Delta JSON
    
    # Follow Up
    next_visit_date = Column(Date, nullable=True)
    next_visit_instructions = Column(String(255), nullable=True) # e.g., "3 Months"
    
    # Referrals
    referral_doctor_name = Column(String(100), nullable=True)
    referral_speciality = Column(String(100), nullable=True)
    referral_phone = Column(String(20), nullable=True)
    referral_email = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="consultations")
    user = relationship("User") # One-way relationship is fine here if not navigating User -> Consultations
    appointment = relationship("Appointment", back_populates="consultation")
    vitals = relationship("Vitals", back_populates="consultation", uselist=False, cascade="all, delete-orphan")
    diagnoses = relationship("ConsultationDiagnosis", back_populates="consultation", cascade="all, delete-orphan")
    medications = relationship("ConsultationMedication", back_populates="consultation", cascade="all, delete-orphan")

class Vitals(Base):
    """Vitals recorded during a consultation."""
    __tablename__ = "vitals"
    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id"), nullable=False, unique=True)
    
    bp_systolic = Column(Integer, nullable=True)
    bp_diastolic = Column(Integer, nullable=True)
    pulse = Column(Integer, nullable=True)
    height = Column(Numeric(5, 2), nullable=True) # e.g., cm
    weight = Column(Numeric(5, 2), nullable=True) # e.g., kg
    bmi = Column(Numeric(4, 2), nullable=True)
    waist = Column(Numeric(5, 2), nullable=True)
    hip = Column(Numeric(5, 2), nullable=True)
    temperature = Column(Numeric(4, 1), nullable=True) # e.g., F or C
    spo2 = Column(Integer, nullable=True)
    
    # OB/GYN
    lmp = Column(Date, nullable=True)
    edd = Column(Date, nullable=True)
    gestational_age_weeks = Column(Integer, nullable=True)
    gestational_age_days = Column(Integer, nullable=True)

    # Timestamps (Optional, but good practice)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    consultation = relationship("Consultation", back_populates="vitals")

class ConsultationDiagnosis(Base):
    """Diagnoses made during a consultation (Many-to-one with Consultation)."""
    __tablename__ = "consultation_diagnoses"
    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id"), nullable=False)
    diagnosis_name = Column(String(255), nullable=False)
    # Could add FK to a DiagnosisMaster table, ICD-10 code, etc.
    
    # Relationship
    consultation = relationship("Consultation", back_populates="diagnoses")

class ConsultationMedication(Base):
    """Medications prescribed during a consultation (Many-to-one with Consultation)."""
    __tablename__ = "consultation_medications"
    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id"), nullable=False)
    
    type = Column(String(10), nullable=True) # TAB, INJ, etc.
    medicine_name = Column(String(255), nullable=False)
    dosage = Column(String(50), nullable=True)
    when = Column(String(50), nullable=True) # Before Food, etc.
    frequency = Column(String(50), nullable=True) # daily, etc.
    duration = Column(String(50), nullable=True) # 20 days, etc.
    notes = Column(Text, nullable=True)
    
    # Relationship
    consultation = relationship("Consultation", back_populates="medications")

class PatientMenstrualHistory(Base):
    """Stores menstrual history for a patient (One-to-one with Patient)."""
    __tablename__ = "patient_menstrual_history"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, unique=True)
    
    age_at_menarche = Column(Integer, nullable=True)
    lmp = Column(Date, nullable=True)
    regularity = Column(String(50), nullable=True)
    duration_of_bleeding = Column(String(50), nullable=True)
    period_of_cycle = Column(String(50), nullable=True)
    details_of_issues = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    patient = relationship("Patient", back_populates="menstrual_history")


class Location(Base):
    """Enhanced Location model for multi-clinic support"""
    __tablename__ = "locations"
    __table_args__ = (
        Index('idx_locations_active', 'is_active'),
        Index('idx_locations_timezone', 'timezone'),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(20), nullable=True)
    country = Column(String(50), default="US")
    
    # Contact information
    phone_number = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    
    # Operational details
    timezone = Column(String(50), default="UTC")
    license_number = Column(String(100), nullable=True)
    
    # Settings and configuration
    settings = Column(JSON, nullable=True)  # Location-specific settings
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    appointments = relationship("Appointment", back_populates="location")
    schedules = relationship("LocationSchedule", back_populates="location")
    unavailable_periods = relationship("UnavailablePeriod", back_populates="location")

class Patient(Base):
    """HIPAA-compliant Patient model with encryption"""
    __tablename__ = "patients"
    __table_args__ = (
        Index('idx_patients_phone_hash', 'phone_hash'),
        Index('idx_patients_email_hash', 'email_hash'),
        Index('idx_patients_dob', 'date_of_birth'),
        Index('idx_patients_created', 'created_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    
    # Encrypted PII fields (stored as binary)
    name_encrypted = Column(LargeBinary, nullable=False)
    phone_number_encrypted = Column(LargeBinary, nullable=True)
    email_encrypted = Column(LargeBinary, nullable=True)
    address_encrypted = Column(LargeBinary, nullable=True)
    
    # Searchable hashes for encrypted fields
    phone_hash = Column(String(64), index=True, nullable=True)
    email_hash = Column(String(64), index=True, nullable=True)
    name_hash = Column(String(64), index=True, nullable=False)
    
    # Non-encrypted demographic data
    city = Column(String(100), nullable=True)
    
    # Non-encrypted demographic data
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    
    # Medical information
    blood_type = Column(String(5), nullable=True)
    allergies = Column(Text, nullable=True)  # Could be encrypted in production
    emergency_contact_encrypted = Column(LargeBinary, nullable=True)
    emergency_contact_hash = Column(String(64), nullable=True)
    
    # Insurance and billing
    insurance_provider = Column(String(100), nullable=True)
    insurance_number_encrypted = Column(LargeBinary, nullable=True)
    insurance_number_hash = Column(String(64), nullable=True)
    
    # Communication preferences
    preferred_communication = Column(SQLAlchemyEnum(CommunicationType, name='communication_type'), default=CommunicationType.phone)
    communication_preferences = Column(JSON, nullable=True)  # Detailed preferences
    
    # WhatsApp integration
    whatsapp_number = Column(String(20), nullable=True)
    whatsapp_opt_in = Column(Boolean, default=False)
    whatsapp_opt_in_date = Column(DateTime(timezone=True), nullable=True)
    
    # Consent and legal
    hipaa_authorization = Column(Boolean, default=False)
    hipaa_authorization_date = Column(DateTime(timezone=True), nullable=True)
    consent_to_treatment = Column(Boolean, default=False)
    consent_to_treatment_date = Column(DateTime(timezone=True), nullable=True)
    marketing_consent = Column(Boolean, default=False)
    
    # Status and tracking
    is_active = Column(Boolean, default=True)
    vip_status = Column(Boolean, default=False)
    language_preference = Column(String(10), default="en")
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_visit_date = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    creator = relationship("User", back_populates="created_patients", foreign_keys=[created_by])
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="patient", cascade="all, delete-orphan")
    prescriptions = relationship("Prescription", back_populates="patient", cascade="all, delete-orphan")
    communications = relationship("CommunicationLog", back_populates="patient", cascade="all, delete-orphan")
    whatsapp_sessions = relationship("WhatsAppSession", back_populates="patient")
    remarks = relationship("Remark", back_populates="patient", cascade="all, delete-orphan")
    consultations = relationship("Consultation", back_populates="patient", cascade="all, delete-orphan")
    menstrual_history = relationship("PatientMenstrualHistory", back_populates="patient", uselist=False, cascade="all, delete-orphan")

class Appointment(Base):
    """Comprehensive Appointment model with calendar integration"""
    __tablename__ = "appointments"
    __table_args__ = (
        Index('idx_appointments_patient_date', 'patient_id', 'start_time'),
        Index('idx_appointments_location_date', 'location_id', 'start_time'),
        Index('idx_appointments_user_date', 'user_id', 'start_time'),
        Index('idx_appointments_status_date', 'status', 'start_time'),
        Index('idx_appointments_date_range', 'start_time', 'end_time'),
    )

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Assigned staff/doctor
    
    # Appointment timing
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes = Column(Integer, nullable=False, default=30)
    
    # Appointment details
    appointment_type = Column(String(50), default="consultation")
    reason = Column(Text, nullable=True)
    chief_complaint = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)  # Staff-only notes
    
    # Status and workflow
    status = Column(SQLAlchemyEnum(AppointmentStatus, name='appointment_status'), default=AppointmentStatus.scheduled, index=True)
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    
    # Check-in and workflow timestamps
    scheduled_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    checked_in_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Integration fields
    google_calendar_event_id = Column(String(255), nullable=True)
    zoom_meeting_id = Column(String(255), nullable=True)  # For telemedicine
    
    # Billing and insurance
    billing_status = Column(String(50), default="pending")
    insurance_authorization = Column(String(100), nullable=True)
    copay_amount = Column(Numeric(10, 2), nullable=True)
    copay_collected = Column(Boolean, default=False)
    
    # Reminders and notifications
    reminder_sent_24h = Column(Boolean, default=False)
    reminder_sent_2h = Column(Boolean, default=False)
    no_show_fee_applied = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    location = relationship("Location", back_populates="appointments")
    user = relationship("User", back_populates="appointments")
    # Link to the consultation record created during this appointment
    consultation = relationship("Consultation", back_populates="appointment", uselist=False)

class Document(Base):
    """Secure Document storage with encryption and audit trail"""
    __tablename__ = "documents"
    __table_args__ = (
        Index('idx_documents_patient', 'patient_id'),
        Index('idx_documents_type_date', 'document_type', 'uploaded_at'),
        Index('idx_documents_uploader', 'uploaded_by'),
    )

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    
    # Document metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    document_type = Column(SQLAlchemyEnum(DocumentType, name='document_type'), default=DocumentType.other)
    mime_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=True)
    
    # Security and storage
    file_path_encrypted = Column(LargeBinary, nullable=False)  # Encrypted file path
    checksum = Column(String(64), nullable=False)  # File integrity verification
    encryption_key_id = Column(String(64), nullable=False)  # Key management
    
    # Access control
    is_sensitive = Column(Boolean, default=True)
    access_level = Column(String(20), default="confidential")  # public, internal, confidential, restricted
    retention_date = Column(Date, nullable=True)  # When document can be deleted
    
    # Metadata and audit
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    access_count = Column(Integer, default=0)

    # Relationships
    patient = relationship("Patient", back_populates="documents")
    uploader = relationship("User", back_populates="uploaded_documents")

class Prescription(Base):
    """Enhanced Prescription model with drug interaction tracking"""
    __tablename__ = "prescriptions"
    __table_args__ = (
        Index('idx_prescriptions_patient', 'patient_id'),
        Index('idx_prescriptions_prescriber', 'prescribed_by'),
        Index('idx_prescriptions_active', 'is_active', 'prescribed_date'),
        Index('idx_prescriptions_medication', 'medication_name'),
    )

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    prescribed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Medication details
    medication_name = Column(String(255), nullable=False)
    generic_name = Column(String(255), nullable=True)
    dosage = Column(String(100), nullable=False)
    dosage_form = Column(String(50), nullable=True)  # tablet, capsule, liquid, etc.
    strength = Column(String(50), nullable=True)  # 500mg, 10mg/ml, etc.
    
    # Instructions
    frequency = Column(String(100), nullable=False)
    duration = Column(String(100), nullable=False)
    instructions = Column(Text, nullable=True)
    food_instructions = Column(Text, nullable=True)  # take with food, etc.
    
    # Dispensing information
    quantity = Column(String(50), nullable=True)
    refills_allowed = Column(Integer, default=0)
    refills_used = Column(Integer, default=0)
    days_supply = Column(Integer, nullable=True)
    
    # Clinical information
    indication = Column(Text, nullable=True)  # Why prescribed
    contraindications = Column(Text, nullable=True)
    side_effects = Column(Text, nullable=True)
    
    # Status and tracking
    is_active = Column(Boolean, default=True)
    is_discontinued = Column(Boolean, default=False)
    discontinuation_reason = Column(Text, nullable=True)
    document_id = Column(Integer, nullable=True)  # linked editor document
    
    # E-prescribing
    ndc_number = Column(String(20), nullable=True)  # National Drug Code
    dea_schedule = Column(String(5), nullable=True)  # Controlled substance schedule
    prior_authorization_required = Column(Boolean, default=False)
    
    # Timestamps
    prescribed_date = Column(DateTime(timezone=True), server_default=func.now())
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    last_filled_date = Column(Date, nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="prescriptions")
    prescriber = relationship("User", back_populates="prescribed_medications")

class Remark(Base):
    __tablename__ = "remarks"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    patient = relationship("Patient", back_populates="remarks")
    author = relationship("User", back_populates="remarks_authored")


class CommunicationLog(Base):
    """Comprehensive Communication tracking for all channels"""
    __tablename__ = "communication_logs"
    __table_args__ = (
        Index('idx_communications_patient', 'patient_id'),
        Index('idx_communications_type_date', 'communication_type', 'sent_at'),
        Index('idx_communications_direction', 'direction', 'sent_at'),
        Index('idx_communications_status', 'status', 'sent_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    
    # Communication details
    communication_type = Column(SQLAlchemyEnum(CommunicationType, name='communication_type'), nullable=False)
    direction = Column(String(20), nullable=False)  # inbound/outbound
    
    # Message content (encrypted for sensitive data)
    subject = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    content_encrypted = Column(LargeBinary, nullable=True)  # For sensitive content
    
    # Channel-specific information
    from_address = Column(String(255), nullable=True)  # email address, phone number, etc.
    to_address = Column(String(255), nullable=True)
    channel_message_id = Column(String(255), nullable=True)  # WhatsApp message ID, email ID
    
    # Status tracking
    status = Column(String(20), default="sent")  # sent, delivered, read, failed
    error_message = Column(Text, nullable=True)
    
    # Templates and automation
    template_name = Column(String(100), nullable=True)
    is_automated = Column(Boolean, default=False)
    campaign_id = Column(String(100), nullable=True)
    
    # Compliance and audit
    business_justification = Column(Text, nullable=True)  # HIPAA compliance
    consent_obtained = Column(Boolean, default=False)
    
    # Timestamps
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    patient = relationship("Patient", back_populates="communications")

class WhatsAppSession(Base):
    """WhatsApp conversation session management"""
    __tablename__ = "whatsapp_sessions"
    __table_args__ = (
        Index('idx_whatsapp_phone', 'phone_number'),
        Index('idx_whatsapp_active', 'is_active', 'last_activity'),
        Index('idx_whatsapp_patient', 'patient_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    
    # Conversation state
    current_flow = Column(String(50), nullable=True)  # appointment_booking, prescription_request
    flow_step = Column(String(50), nullable=True)  # collect_name, collect_date, etc.
    context_data = Column(JSON, nullable=True)  # Conversation context
    
    # Session management
    session_id = Column(String(100), nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    session_started_at = Column(DateTime(timezone=True), server_default=func.now())
    session_ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # AI and automation
    ai_enabled = Column(Boolean, default=True)
    language_preference = Column(String(10), default="en")
    
    # Analytics
    message_count = Column(Integer, default=0)
    successful_bookings = Column(Integer, default=0)

    # Relationships
    patient = relationship("Patient", back_populates="whatsapp_sessions")

class LocationSchedule(Base):
    """Operating hours and availability for each location"""
    __tablename__ = "location_schedules"
    __table_args__ = (
        Index('idx_schedule_location_day', 'location_id', 'day_of_week'),
        Index('idx_schedule_available', 'is_available'),
        UniqueConstraint('location_id', 'day_of_week', name='uq_location_day')  # Ensure only one entry per day per location
    )

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    
    # Schedule details
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_available = Column(Boolean, default=True)
    
    # Break times and limitations
    break_start = Column(Time, nullable=True)
    break_end = Column(Time, nullable=True)
    max_appointments = Column(Integer, nullable=True)
    appointment_duration = Column(Integer, default=30)  # minutes
    
    # Effective dates
    effective_from = Column(Date, nullable=True)
    effective_until = Column(Date, nullable=True)

    # Relationships
    location = relationship("Location", back_populates="schedules")

class AppointmentSlot(Base):
    """Represents a pre-generated, bookable appointment time slot."""
    __tablename__ = "appointment_slots"
    __table_args__ = (
        Index('idx_slot_location_start_status', 'location_id', 'start_time', 'status'),
        Index('idx_slot_appointment', 'appointment_id'),
        UniqueConstraint('location_id', 'start_time', name='uq_location_start_time'), # Ensure no duplicate slots
    )

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(SQLAlchemyEnum(SlotStatus, name='slot_status'), default=SlotStatus.available, nullable=False, index=True)

    # Link to the appointment that books this slot
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True, unique=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    location = relationship("Location") # Define back_populates if needed later
    appointment = relationship("Appointment") # Define back_populates if needed later

class UnavailablePeriod(Base):
    """Track holidays, vacations, and other unavailable periods"""
    __tablename__ = "unavailable_periods"
    __table_args__ = (
        Index('idx_unavailable_location_date', 'location_id', 'start_datetime'),
        Index('idx_unavailable_date_range', 'start_datetime', 'end_datetime'),
    )

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    
    # Unavailable period
    start_datetime = Column(DateTime(timezone=True), nullable=False)
    end_datetime = Column(DateTime(timezone=True), nullable=False)
    reason = Column(String(255), nullable=True)
    reason_type = Column(String(50), default="other")  # vacation, holiday, maintenance, emergency
    
    # Affected services
    affects_all_staff = Column(Boolean, default=True)
    affected_staff_ids = Column(JSON, nullable=True)  # List of user IDs if not all staff
    
    # Recurring patterns
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(JSON, nullable=True)  # For recurring holidays
    
    # Integration
    google_calendar_event_id = Column(String(255), nullable=True)
    
    # Notifications
    patients_notified = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    location = relationship("Location", back_populates="unavailable_periods")

class AuditLog(Base):
    """HIPAA-compliant audit logging with tamper detection"""
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index('idx_audit_user_date', 'user_id', 'timestamp'),
        Index('idx_audit_action_date', 'action', 'timestamp'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_ip_date', 'ip_address', 'timestamp'),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(50), nullable=True)  # Denormalized for audit integrity
    action = Column(SQLAlchemyEnum(AuditAction, name='audit_action'), nullable=False)
    category = Column(String(50), nullable=False, default="GENERAL", index=True)
    severity = Column(String(20), default="INFO", index=True) # INFO, WARN, ERROR, CRITICAL
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    user = relationship("User", back_populates="audit_logs")

# System Configuration and Settings
class SystemConfiguration(Base):
    """System-wide configuration settings"""
    __tablename__ = "system_configuration"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(JSON, nullable=True)
    value_type = Column(String(20), default="string")  # string, integer, boolean, json
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # security, email, whatsapp, etc.
    is_encrypted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class NotificationQueue(Base):
    """Queue for outbound notifications and communications"""
    __tablename__ = "notification_queue"
    __table_args__ = (
        Index('idx_notifications_status_priority', 'status', 'priority', 'scheduled_for'),
        Index('idx_notifications_patient', 'patient_id'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    
    # Notification details
    notification_type = Column(String(50), nullable=False)  # reminder, prescription, marketing
    channel = Column(SQLAlchemyEnum(CommunicationType), nullable=False)
    recipient = Column(String(255), nullable=False)  # phone/email
    
    # Content
    subject = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    template_id = Column(String(100), nullable=True)
    template_data = Column(JSON, nullable=True)
    
    # Scheduling and priority
    priority = Column(String(20), default="normal")  # high, normal, low
    scheduled_for = Column(DateTime(timezone=True), nullable=False)
    
    # Status tracking
    status = Column(String(20), default="pending")  # pending, sent, failed, cancelled
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())