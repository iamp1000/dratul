
from datetime import datetime, time
from sqlalchemy import (
    Column, Integer, String, DateTime, Time, ForeignKey, Text, Date,
    Enum as SQLAlchemyEnum, Boolean, LargeBinary, JSON, Numeric
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


# --- Enhanced Enum Classes ---
class UserRole(str, enum.Enum):
    admin = "admin"
    staff = "staff"
    doctor = "doctor"
    nurse = "nurse"
    receptionist = "receptionist"

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
    ACCESS_DENIED = "ACCESS_DENIED"
    EXPORT = "EXPORT"
    PRINT = "PRINT"

# --- Enhanced User Model with HIPAA Features ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True)
    phone_number = Column(String(20))
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLAlchemyEnum(UserRole), nullable=False)

    # HIPAA Compliance Fields
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True))
    login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True), default=func.now())
    must_change_password = Column(Boolean, default=False)

    # Audit Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Two-Factor Authentication
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(32))  # Encrypted TOTP secret

    # Relationships
    audit_logs = relationship("AuditLog", back_populates="user")
    created_patients = relationship("Patient", foreign_keys="Patient.created_by")
    remarks_authored = relationship("Remark", back_populates="author")

    # Permissions - JSON field for fine-grained permissions
    permissions = Column(JSON, default=dict)

# --- Enhanced Audit Log Model ---
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Can be null for system events
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    action = Column(SQLAlchemyEnum(AuditAction), nullable=False)

    # HIPAA Required Fields
    resource_type = Column(String(50))  # e.g., "Patient", "Appointment"
    resource_id = Column(String(50))    # ID of the accessed resource
    patient_id = Column(Integer, ForeignKey("patients.id"))  # For PHI access tracking

    # Additional Context
    ip_address = Column(String(45))     # IPv4 or IPv6
    user_agent = Column(Text)
    session_id = Column(String(128))

    # Event Details
    details = Column(Text)  # JSON string with event-specific details
    old_values = Column(Text)  # JSON string of previous values (for updates)
    new_values = Column(Text)  # JSON string of new values (for creates/updates)

    # Success/Failure
    success = Column(Boolean, default=True)
    error_message = Column(Text)

    # Data Access Justification
    access_reason = Column(String(200))  # Business justification for access

    # Relationships
    user = relationship("User", back_populates="audit_logs")
    patient = relationship("Patient", back_populates="audit_logs")

# --- Enhanced Patient Model with Encryption ---
class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)

    # Encrypted PII Fields (these would be encrypted at application level)
    name_encrypted = Column(LargeBinary)  # Encrypted name
    phone_number_encrypted = Column(LargeBinary)  # Encrypted phone
    email_encrypted = Column(LargeBinary)  # Encrypted email
    address_encrypted = Column(LargeBinary)  # Encrypted address
    ssn_encrypted = Column(LargeBinary)  # Encrypted SSN (if applicable)

    # Searchable hash fields for lookups
    phone_hash = Column(String(64), unique=True, index=True)  # SHA-256 hash for lookup
    email_hash = Column(String(64), unique=True, index=True)  # SHA-256 hash for lookup

    # Non-encrypted fields
    date_of_birth = Column(Date)
    gender = Column(String(10))

    # WhatsApp Integration
    whatsapp_number_encrypted = Column(LargeBinary)
    whatsapp_opt_in = Column(Boolean, default=False)
    whatsapp_opt_in_date = Column(DateTime(timezone=True))

    # Communication Preferences
    preferred_communication = Column(SQLAlchemyEnum(CommunicationType), default=CommunicationType.phone)

    # HIPAA Compliance
    consent_to_treatment = Column(Boolean, default=False)
    consent_to_treatment_date = Column(DateTime(timezone=True))
    hipaa_authorization = Column(Boolean, default=False)
    hipaa_authorization_date = Column(DateTime(timezone=True))

    # Audit Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("users.id"))

    # Soft Delete for HIPAA Compliance
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    appointments = relationship("Appointment", back_populates="patient")
    documents = relationship("Document", back_populates="patient")
    remarks = relationship("Remark", back_populates="patient")
    prescriptions = relationship("Prescription", back_populates="patient")
    audit_logs = relationship("AuditLog", back_populates="patient")
    communication_logs = relationship("CommunicationLog", back_populates="patient")

# --- Enhanced Location Model ---
class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(100))

    # Operating Hours
    timezone = Column(String(50), default="UTC")
    is_active = Column(Boolean, default=True)

    # Audit Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    schedules = relationship("LocationSchedule", back_populates="location")
    appointments = relationship("Appointment", back_populates="location")
    unavailable_periods = relationship("UnavailablePeriod", back_populates="location")

class LocationSchedule(Base):
    __tablename__ = "location_schedules"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_active = Column(Boolean, default=True)

    # Break times
    break_start = Column(Time)
    break_end = Column(Time)

    location = relationship("Location", back_populates="schedules")

class UnavailablePeriod(Base):
    __tablename__ = "unavailable_periods"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    start_datetime = Column(DateTime(timezone=True), nullable=False)
    end_datetime = Column(DateTime(timezone=True), nullable=False)
    reason = Column(String(200))

    # Google Calendar Integration
    google_calendar_event_id = Column(String(100))

    # Audit Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))

    location = relationship("Location", back_populates="unavailable_periods")

# --- Enhanced Appointment Model ---
class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)

    # Timing
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False)

    # Appointment Details
    reason = Column(Text)
    status = Column(SQLAlchemyEnum(AppointmentStatus), default=AppointmentStatus.scheduled)
    appointment_type = Column(String(50))  # "consultation", "follow-up", "procedure", etc.

    # Communication Tracking
    confirmation_sent = Column(Boolean, default=False)
    confirmation_sent_at = Column(DateTime(timezone=True))
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime(timezone=True))

    # Google Calendar Integration
    google_calendar_event_id = Column(String(100))

    # Notes and Instructions
    notes = Column(Text)
    preparation_instructions = Column(Text)

    # Pricing (if applicable)
    estimated_cost = Column(Numeric(10, 2))
    actual_cost = Column(Numeric(10, 2))
    insurance_covered = Column(Boolean, default=False)

    # Audit Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    location = relationship("Location", back_populates="appointments")
    prescriptions = relationship("Prescription", back_populates="appointment")

# --- Document Management ---
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)

    # File Information
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # Encrypted file path
    file_size = Column(Integer)
    mime_type = Column(String(100))

    # Document Details
    document_type = Column(String(50))  # "prescription", "lab_result", "image", etc.
    description = Column(Text)

    # Encryption Information
    is_encrypted = Column(Boolean, default=True)
    encryption_key_id = Column(String(100))  # Reference to key management service

    # Access Control
    sensitivity_level = Column(String(20), default="high")  # high, medium, low

    # Audit Fields
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    last_accessed = Column(DateTime(timezone=True))
    access_count = Column(Integer, default=0)

    patient = relationship("Patient", back_populates="documents")

# --- Prescription Management ---
class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"))

    # Prescription Details
    medication_name = Column(String(200), nullable=False)
    dosage = Column(String(100))
    frequency = Column(String(100))
    duration = Column(String(100))
    quantity = Column(Integer)
    refills = Column(Integer, default=0)

    # Instructions
    instructions = Column(Text)
    notes = Column(Text)

    # Status
    status = Column(String(50), default="active")  # active, completed, cancelled

    # Audit Fields
    prescribed_date = Column(DateTime(timezone=True), server_default=func.now())
    prescribed_by = Column(Integer, ForeignKey("users.id"))

    patient = relationship("Patient", back_populates="prescriptions")
    appointment = relationship("Appointment", back_populates="prescriptions")

# --- Remarks/Notes ---
class Remark(Base):
    __tablename__ = "remarks"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Content
    title = Column(String(200))
    text = Column(Text, nullable=False)

    # Categorization
    category = Column(String(50))  # "medical", "administrative", "billing", etc.
    priority = Column(String(20), default="normal")  # high, normal, low

    # Visibility
    is_confidential = Column(Boolean, default=False)
    visible_to_roles = Column(JSON)  # Array of roles that can see this remark

    # Audit Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    patient = relationship("Patient", back_populates="remarks")
    author = relationship("User", back_populates="remarks_authored")

# --- Communication Log ---
class CommunicationLog(Base):
    __tablename__ = "communication_logs"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)

    # Communication Details
    communication_type = Column(SQLAlchemyEnum(CommunicationType), nullable=False)
    direction = Column(String(10))  # "inbound", "outbound"
    subject = Column(String(200))
    content = Column(Text)

    # Delivery Status
    status = Column(String(20))  # "sent", "delivered", "failed", "read"
    sent_at = Column(DateTime(timezone=True))
    delivered_at = Column(DateTime(timezone=True))
    read_at = Column(DateTime(timezone=True))

    # External References
    external_message_id = Column(String(100))  # WhatsApp/Email message ID

    # Audit Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))

    patient = relationship("Patient", back_populates="communication_logs")

# --- WhatsApp Integration ---
class WhatsAppSession(Base):
    __tablename__ = "whatsapp_sessions"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))

    # Session Management
    session_id = Column(String(100), unique=True)
    is_active = Column(Boolean, default=True)
    current_flow = Column(String(50))  # "booking", "inquiry", "prescription", etc.
    current_step = Column(String(50))
    context_data = Column(JSON)  # Store conversation context

    # Timing
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))

    patient = relationship("Patient")

# --- System Configuration ---
class SystemConfiguration(Base):
    __tablename__ = "system_configurations"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    description = Column(Text)

    # Data Type Information
    data_type = Column(String(20))  # "string", "integer", "boolean", "json"

    # Audit Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("users.id"))

# --- Bulk Communication ---
class BulkCommunication(Base):
    __tablename__ = "bulk_communications"

    id = Column(Integer, primary_key=True, index=True)

    # Campaign Details
    title = Column(String(200), nullable=False)
    message_content = Column(Text, nullable=False)
    communication_type = Column(SQLAlchemyEnum(CommunicationType), nullable=False)

    # Targeting
    target_criteria = Column(JSON)  # Criteria for selecting recipients

    # Status
    status = Column(String(20), default="draft")  # draft, scheduled, sending, completed, failed
    scheduled_for = Column(DateTime(timezone=True))

    # Results
    total_recipients = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    delivered_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)

    # Audit Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

 # models.py
class ActivityLog(AuditLog):
    __tablename__ = 'activity_logs'  
