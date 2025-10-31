# app/schemas.py
from datetime import datetime, date, time
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, EmailStr, validator, model_validator, computed_field
# Import for encryption_service moved inside computed_field to avoid circular import
from .models import SlotStatus # Import SlotStatus
from enum import Enum

# --- Enum Classes ---
class UserRole(str, Enum):
    admin = "admin"
    staff = "staff" 
    doctor = "doctor"
    viewer = "viewer"

class AppointmentStatus(str, Enum):
    scheduled = "scheduled"
    confirmed = "confirmed"
    checked_in = "checked_in"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"
    rescheduled = "rescheduled"

class CommunicationType(str, Enum):
    whatsapp = "whatsapp"
    email = "email"
    sms = "sms"
    phone = "phone"

class AuditAction(str, Enum):
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
    LOGIN_SUCCESS = "Login Success"
    APPOINTMENT_CREATE = "Created Appointment"
    SLOT_BOOK_SUCCESS = "Booked Slot"
    SLOT_BOOK_FAILED = "Slot Booking Failed"
    SCHEDULE_WEEK_UPDATE = "Updated Weekly Schedule"
    SCHEDULE_DAY_UPDATE = "Updated Day Schedule"
    SLOT_RECONCILE_START = "Started Slot Reconciliation"
    SLOTS_DELETE = "Deleted Slots"
    SLOTS_GENERATE = "Generated Slots"
    SLOT_RECONCILE_FINISH = "Finished Slot Reconciliation"
    SLOT_RECONCILE_FAILED = "Failed Slot Reconciliation"
    SLOT_EMERGENCY_BLOCK = "Emergency Block Slots"
    SLOT_EMERGENCY_UNBLOCK = "Reverted Emergency Block Slots"

# --- Base Schemas ---
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True


# --- Permissions Schema ---
class PermissionSet(BaseSchema):
    # Core System Access
    can_access_logs: bool = Field(False, description="Can view the Audit Logs and System Health status.")
    can_run_anomaly_fix: bool = Field(False, description="Can execute anomaly fixing tools in LogViewer.")
    
    # User Management
    can_manage_users: bool = Field(False, description="Can add, edit, or delete user accounts.")
    
    # Patient/Data Management
    can_edit_patient_info: bool = Field(False, description="Can edit existing patient demographic details.")
    can_delete_patient: bool = Field(False, description="Can permanently delete patient records.")

    # Appointment/Schedule Management
    can_edit_schedule: bool = Field(False, description="Can modify weekly doctor schedules and set unavailable periods.")
    can_manage_appointments: bool = Field(True, description="Can schedule, reschedule, and cancel appointments.")


class User(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: UserRole
    permissions: PermissionSet = Field(default_factory=PermissionSet, description="Detailed feature permissions")
    is_active: Optional[bool] = None
    mfa_enabled: Optional[bool] = None
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Config:
    from_attributes = True


# --- User Schemas ---
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    role: UserRole
    phone_number: Optional[str] = Field(None, max_length=20)
    permissions: Optional[PermissionSet] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v

class UserUpdate(BaseSchema):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    role: Optional[UserRole] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None
    mfa_enabled: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    mfa_enabled: bool
    last_login: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True # Allow conversion from ORM model


# --- Appointment Slot Schemas ---
class AppointmentSlotBase(BaseSchema):
    location_id: int
    start_time: datetime
    end_time: datetime
    status: SlotStatus = SlotStatus.available

class AppointmentSlotCreate(AppointmentSlotBase):
    pass # No extra fields needed for internal creation

class AppointmentSlot(AppointmentSlotBase): # Schema for API responses
    id: int
    # REFACTORED: Removed old 'appointment_id' (1:1) and added capacity fields.
    max_strict_capacity: int
    current_strict_appointments: int
    
    # FIX: Add timezone for client-side time display correction
    location_timezone: Optional[str] = None

    class Config:
        from_attributes = True # Ensure compatibility with ORM model
    updated_at: Optional[datetime]

# --- Patient Schemas ---
class PatientBase(BaseSchema):
    first_name: str = Field(..., min_length=1, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    date_of_birth: Optional[date] = None
    city: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, max_length=10)
    preferred_communication: CommunicationType = CommunicationType.phone
    whatsapp_number: Optional[str] = Field(None, max_length=20)
    whatsapp_opt_in: bool = False
    hipaa_authorization: bool = False
    consent_to_treatment: bool = False

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseSchema):
    first_name: Optional[str] = Field(None, min_length=1, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=10)
    preferred_communication: Optional[CommunicationType] = None
    whatsapp_number: Optional[str] = Field(None, max_length=20)
    whatsapp_opt_in: Optional[bool] = None
    hipaa_authorization: Optional[bool] = None
    consent_to_treatment: Optional[bool] = None

class PatientResponse(BaseSchema): # Inherit from BaseSchema, not PatientBase
    id: int

    # --- Non-PII fields (copied from PatientBase) ---
    date_of_birth: Optional[date] = None
    city: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, max_length=10)
    preferred_communication: CommunicationType = CommunicationType.phone
    whatsapp_number: Optional[str] = Field(None, max_length=20)
    whatsapp_opt_in: bool = False
    hipaa_authorization: bool = False
    consent_to_treatment: bool = False

    # --- Metadata fields ---
    phone_hash: Optional[str] = None
    email_hash: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime]

    # --- Private fields for internal use ---
    # These are populated from the ORM model but excluded from the JSON response.
    # They are used by the @computed_field properties below.
    name_encrypted: Optional[bytes] = Field(None, exclude=True)
    phone_number_encrypted: Optional[bytes] = Field(None, exclude=True)
    email_encrypted: Optional[bytes] = Field(None, exclude=True)

    # --- Computed Fields for PII ---
    # These fields are now compatible as they don't override a parent.

    @computed_field
    @property
    def first_name(self) -> str:
        from app.security import encryption_service # LAZY IMPORT
        if not self.name_encrypted:
            return "N/A"
        try:
            decrypted_name = encryption_service.decrypt(self.name_encrypted)
            return decrypted_name.split(' ', 1)[0]
        except Exception:
            return "[Decrypt Error]"

    @computed_field
    @property
    def last_name(self) -> Optional[str]:
        from app.security import encryption_service # LAZY IMPORT
        if not self.name_encrypted:
            return None
        try:
            decrypted_name = encryption_service.decrypt(self.name_encrypted)
            parts = decrypted_name.split(' ', 1)
            return parts[1] if len(parts) > 1 else None
        except Exception:
            return "[Decrypt Error]"

    @computed_field
    @property
    def phone_number(self) -> Optional[str]:
        from app.security import encryption_service # LAZY IMPORT
        if not self.phone_number_encrypted:
            return None
        try:
            return encryption_service.decrypt(self.phone_number_encrypted)
        except Exception:
            return "[Decrypt Error]"

    @computed_field
    @property
    def email(self) -> Optional[EmailStr]:
        from app.security import encryption_service # LAZY IMPORT
        if not self.email_encrypted:
            return None
        try:
            return encryption_service.decrypt(self.email_encrypted)
        except Exception:
            return "[Decrypt Error]"

# --- Location Schemas ---
class LocationBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    address: Optional[str] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    timezone: str = Field(default="UTC", max_length=50)

class LocationCreate(LocationBase):
    pass

class LocationUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    timezone: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None

class LocationResponse(LocationBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

# --- Appointment Schemas ---
class NewPatient(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    date_of_birth: date
    city: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None

    @validator('email', pre=True)
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v

class AppointmentBase(BaseSchema):
    patient_id: Optional[int] = None
    location_id: int
    start_time: datetime # Required again
    end_time: datetime   # Required again
    reason: Optional[str] = None
    notes: Optional[str] = None
    appointment_type: str = Field(default="consultation", max_length=50)
    status: AppointmentStatus = AppointmentStatus.scheduled

class AppointmentCreate(AppointmentBase):
    new_patient: Optional[NewPatient] = None
    is_walk_in: Optional[bool] = False # Flag to indicate walk-in status from frontend

    @model_validator(mode='after')
    def check_patient_logic(self):
        patient_id = self.patient_id
        new_patient = self.new_patient

        if patient_id is None and new_patient is None:
            raise ValueError('Either patient_id or new_patient must be provided.')
        if patient_id is not None and new_patient is not None:
            raise ValueError('Cannot provide both patient_id and new_patient.')
        return self

class AppointmentUpdate(BaseSchema):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    appointment_type: Optional[str] = Field(None, max_length=50)
    status: Optional[AppointmentStatus] = None

class AppointmentResponse(AppointmentBase):
    id: int
    user_id: Optional[int] = None
    google_calendar_event_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime]

    # Nested objects
    patient: Optional[PatientResponse] = None
    location: Optional[LocationResponse] = None
    user: Optional[UserResponse] = None

# --- Prescription Schemas ---
class PrescriptionBase(BaseSchema):
    patient_id: int
    medication_name: str = Field(..., min_length=1, max_length=255)
    dosage: str = Field(..., min_length=1, max_length=100)
    frequency: str = Field(..., min_length=1, max_length=100)
    duration: str = Field(..., min_length=1, max_length=100)
    instructions: Optional[str] = None

class PrescriptionCreate(PrescriptionBase):
    pass

class PrescriptionUpdate(BaseSchema):
    medication_name: Optional[str] = Field(None, min_length=1, max_length=255)
    dosage: Optional[str] = Field(None, min_length=1, max_length=100)
    frequency: Optional[str] = Field(None, min_length=1, max_length=100)
    duration: Optional[str] = Field(None, min_length=1, max_length=100)
    instructions: Optional[str] = None
    is_active: Optional[bool] = None

class PrescriptionResponse(PrescriptionBase):
    id: int
    prescribed_by: int
    is_active: bool
    prescribed_date: datetime

    patient: Optional[PatientResponse] = None
    prescriber: Optional[UserResponse] = None

class PrescriptionShare(BaseSchema):
    patient_id: int
    document_id: int
    method: str  # "whatsapp" or "email"
    whatsapp_number: Optional[str] = None
    email: Optional[EmailStr] = None
    message: Optional[str] = None

# --- Document Schemas ---
class DocumentBase(BaseSchema):
    description: str
    file_path: str

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: int
    patient_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Remark Schemas ---
class RemarkBase(BaseSchema):
    text: str

class RemarkCreate(RemarkBase):
    pass

class RemarkResponse(RemarkBase):
    id: int
    patient_id: int
    author_id: int
    created_at: datetime
    author: Optional[UserResponse] = None

# --- Communication Schemas ---
class CommunicationLogBase(BaseSchema):
    patient_id: Optional[int] = None
    communication_type: CommunicationType
    direction: str = Field(..., max_length=20)  # inbound/outbound
    content: Optional[str] = None
    status: str = Field(default="sent", max_length=20)

class CommunicationLogCreate(CommunicationLogBase):
    pass

class CommunicationLogResponse(CommunicationLogBase):
    id: int
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    patient: Optional[PatientResponse] = None

# --- Authentication Schemas ---
class TokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class MFAVerifyRequest(BaseSchema):
    mfa_token: str
    mfa_code: str = Field(..., min_length=6, max_length=6)

class MFASetupResponse(BaseSchema):
    secret: str
    qr_code: str
    backup_codes: List[str]

# --- Audit Log Schemas ---
class ActivityLogBase(BaseSchema):
    action: str
    details: Optional[str] = None

class ActivityLogCreate(ActivityLogBase):
    pass

class ActivityLog(ActivityLogBase):
    id: int
    user_id: int
    created_at: datetime
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True
        
class AuditLogResponse(BaseSchema):
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: AuditAction
    category: str
    severity: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    details: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True # Ensure nested ORM models (like user) are converted

# --- WhatsApp Schemas ---
class WhatsAppSessionResponse(BaseSchema):
    id: int
    phone_number: str
    patient_id: Optional[int] = None
    context_data: Optional[Dict[str, Any]] = None
    last_activity: datetime
    is_active: bool

# --- Dashboard Schemas ---
class DashboardStatsResponse(BaseSchema):
    total_patients: int
    total_appointments: int
    appointments_today: int
    pending_appointments: int
    appointments_week: int

# --- Location Schedule Schemas ---
class LocationScheduleBase(BaseSchema):
    location_id: int
    day_of_week: int = Field(..., ge=0, le=6)  # 0=Monday, 6=Sunday
    start_time: time
    end_time: time
    is_available: bool = True
    appointment_duration: Optional[int] = Field(None, ge=5, le=60) # Duration in minutes (e.g., 5-60)
    max_appointments: Optional[int] = Field(None, ge=0) # Max appointments for this day (0 or None means no limit)

class LocationScheduleCreate(LocationScheduleBase):
    pass

class LocationScheduleResponse(LocationScheduleBase):
    id: int
    # Explicitly include inherited fields for clarity in response
    appointment_duration: Optional[int] = None 
    max_appointments: Optional[int] = None

# --- Unavailable Period Schemas ---
class UnavailablePeriodBase(BaseSchema):
    location_id: int
    start_datetime: datetime
    end_datetime: datetime
    reason: Optional[str] = Field(None, max_length=255)

class UnavailablePeriodCreate(UnavailablePeriodBase):
    pass

class UnavailablePeriodUpdate(BaseSchema):
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    reason: Optional[str] = Field(None, max_length=255)

class UnavailablePeriodResponse(UnavailablePeriodBase):
    id: int
    created_by: int
    created_at: datetime

# --- Emergency Block Schemas ---
class EmergencyBlockCreate(BaseSchema):
    block_date: date
    reason: str = Field(..., min_length=5, max_length=255)
    
# --- Service Status Schemas ---
class ServiceStatusResponse(BaseSchema):
    enabled: bool
    status: str
    last_check: Optional[datetime] = None
    error: Optional[str] = None

class ServicesStatusResponse(BaseSchema):
    whatsapp: ServiceStatusResponse
    email: ServiceStatusResponse
    calendar: ServiceStatusResponse

class NotificationCreate(BaseSchema):
    patient_id: Optional[int] = None
    message: str
    notification_type: str = "general"
    channel: str = "whatsapp"
    
class NotificationResponse(BaseSchema):
    id: int
    patient_id: Optional[int] = None
    message: str
    notification_type: str
    channel: str
    status: str
    created_at: datetime

from typing import Union, Literal # <-- Add Union and Literal

# --- Health Check Schemas ---

class SlotInconsistency(BaseModel):
    slot_id: int
    location_id: int
    start_time: datetime
    status: str
    issue: str # e.g., "Booked but no appointments found"

class AppointmentInconsistency(BaseModel):
    appointment_id: int
    patient_id: int
    slot_id: Optional[int]
    start_time: Optional[datetime]
    status: str
    issue: str # e.g., "Linked to available slot"

class ConsistencyReport(BaseModel):
    checked_at: datetime
    booked_slots_without_appointments: List[SlotInconsistency] = []
    available_slots_with_appointments: List[SlotInconsistency] = []
    status_counter_mismatches: List[SlotInconsistency] = []
    # Add more lists here as we implement more checks

class FixedSlotReport(BaseModel):
    slot_id: int
    previous_status: str
    new_status: str
    details: str

class FixedCounterReport(BaseModel):
    slot_id: int
    previous_count: int
    new_count: int
    details: str

class ConsistencyFixReport(BaseModel):
    checked_at: datetime
    fixed_slots: List[FixedSlotReport] = []
    fixed_counters: List[FixedCounterReport] = []
    errors: List[str] = []

# --- Combined Log/Health Entry Schema ---
class HealthCheckEntry(BaseModel):
    # Mimics AuditLogResponse fields where possible for easier frontend display
    id: Optional[int] = None # Health checks don't have IDs like logs
    timestamp: datetime
    username: str = "System Health"
    category: str = "HEALTH_CHECK"
    severity: str = "WARN" # Default severity for inconsistencies
    action: str # Describes the check type, e.g., "Booked Slot Anomaly"
    resource_type: Optional[str] = None # e.g., "AppointmentSlot"
    resource_id: Optional[int] = None # e.g., slot_id
    details: str # The specific issue found
    log_type: Literal['health_alert'] = 'health_alert' # Differentiator field

class AuditLogEntry(AuditLogResponse):
    # Add a differentiator field to the existing log response
    log_type: Literal['audit_log'] = 'audit_log'

# Union type for the comprehensive log endpoint response
ComprehensiveLogEntry = Union[AuditLogEntry, HealthCheckEntry]

# --- EMR / Consultation Schemas ---

# --- Vitals ---
class VitalsBase(BaseSchema):
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    pulse: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    bmi: Optional[float] = None
    waist: Optional[float] = None
    hip: Optional[float] = None
    temperature: Optional[float] = None
    spo2: Optional[int] = None
    # OB/GYN specific
    lmp: Optional[date] = None
    edd: Optional[date] = None
    gestational_age_weeks: Optional[int] = None
    gestational_age_days: Optional[int] = None

class VitalsCreate(VitalsBase):
    # All fields optional during creation via Consultation
    pass

class VitalsUpdate(BaseSchema): # Not inheriting from VitalsBase to make all fields optional
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    pulse: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    bmi: Optional[float] = None
    waist: Optional[float] = None
    hip: Optional[float] = None
    temperature: Optional[float] = None
    spo2: Optional[int] = None
    lmp: Optional[date] = None
    edd: Optional[date] = None
    gestational_age_weeks: Optional[int] = None
    gestational_age_days: Optional[int] = None

class VitalsResponse(VitalsBase):
    id: int
    consultation_id: int

# --- Consultation Diagnosis ---
class ConsultationDiagnosisBase(BaseSchema):
    diagnosis_name: str

class ConsultationDiagnosisCreate(ConsultationDiagnosisBase):
    pass

class ConsultationDiagnosisUpdate(BaseSchema):
    diagnosis_name: Optional[str] = None

class ConsultationDiagnosisResponse(ConsultationDiagnosisBase):
    id: int
    consultation_id: int

# --- Consultation Medication ---
class ConsultationMedicationBase(BaseSchema):
    type: Optional[str] = Field(None, max_length=10) # e.g., TAB, INJ
    medicine_name: str = Field(..., max_length=255)
    dosage: Optional[str] = Field(None, max_length=50)
    when: Optional[str] = Field(None, max_length=50) # e.g., Before Food
    frequency: Optional[str] = Field(None, max_length=50) # e.g., daily
    duration: Optional[str] = Field(None, max_length=50) # e.g., 20 days
    notes: Optional[str] = None

class ConsultationMedicationCreate(ConsultationMedicationBase):
    pass

class ConsultationMedicationUpdate(BaseSchema):
    type: Optional[str] = Field(None, max_length=10)
    medicine_name: Optional[str] = Field(None, max_length=255)
    dosage: Optional[str] = Field(None, max_length=50)
    when: Optional[str] = Field(None, max_length=50)
    frequency: Optional[str] = Field(None, max_length=50)
    duration: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None

class ConsultationMedicationResponse(ConsultationMedicationBase):
    id: int
    consultation_id: int

# --- Patient Menstrual History --- (Links to Patient, not Consultation)
class PatientMenstrualHistoryBase(BaseSchema):
    age_at_menarche: Optional[int] = None
    lmp: Optional[date] = None
    regularity: Optional[str] = Field(None, max_length=50) # e.g., Regular, Irregular
    duration_of_bleeding: Optional[str] = Field(None, max_length=50)
    period_of_cycle: Optional[str] = Field(None, max_length=50)
    details_of_issues: Optional[str] = None

class PatientMenstrualHistoryCreate(PatientMenstrualHistoryBase):
    patient_id: int # Required on creation

class PatientMenstrualHistoryUpdate(BaseSchema):
    age_at_menarche: Optional[int] = None
    lmp: Optional[date] = None
    regularity: Optional[str] = Field(None, max_length=50)
    duration_of_bleeding: Optional[str] = Field(None, max_length=50)
    period_of_cycle: Optional[str] = Field(None, max_length=50)
    details_of_issues: Optional[str] = None

class PatientMenstrualHistoryResponse(PatientMenstrualHistoryBase):
    id: int
    patient_id: int

# --- Consultation (Main EMR Record) ---
class ConsultationBase(BaseSchema):
    patient_id: int
    appointment_id: Optional[int] = None # Link back to the original appointment
    consultation_date: datetime = Field(default_factory=datetime.utcnow)
    quick_notes: Optional[str] = None # Quill Delta JSON stored as string or JSONB
    complaints: Optional[str] = None
    systemic_examination: Optional[str] = None # Quill Delta JSON stored as string or JSONB
    # NEW: Physical Examination
    physical_examination_notes: Optional[str] = None # Quill Delta JSON
    breast_examination_notes: Optional[str] = None # Quill Delta JSON
    per_speculum_notes: Optional[str] = None # Quill Delta JSON
    advice: Optional[str] = None # Quill Delta JSON stored as string or JSONB
    # Follow Up
    next_visit_date: Optional[date] = None
    next_visit_instructions: Optional[str] = None # e.g., "3 Months"
    # Referrals
    referral_doctor_name: Optional[str] = Field(None, max_length=100)
    referral_speciality: Optional[str] = Field(None, max_length=100)
    referral_phone: Optional[str] = Field(None, max_length=20)
    referral_email: Optional[EmailStr] = None
    # Investigations
    tests_requested: Optional[str] = None
    investigations_notes: Optional[str] = None # Renamed from 'Investigations'
    usg_findings: Optional[str] = None # Quill Delta JSON stored as string or JSONB
    lab_tests_imaging: Optional[str] = None # Quill Delta JSON stored as string or JSONB

class ConsultationCreate(ConsultationBase):
    vitals: Optional[VitalsCreate] = None
    diagnoses: List[ConsultationDiagnosisCreate] = []
    medications: List[ConsultationMedicationCreate] = []

class ConsultationUpdate(BaseSchema):
    consultation_date: Optional[datetime] = None
    quick_notes: Optional[str] = None
    complaints: Optional[str] = None
    systemic_examination: Optional[str] = None
    physical_examination_notes: Optional[str] = None
    breast_examination_notes: Optional[str] = None
    per_speculum_notes: Optional[str] = None
    advice: Optional[str] = None
    next_visit_date: Optional[date] = None
    next_visit_instructions: Optional[str] = None
    referral_doctor_name: Optional[str] = Field(None, max_length=100)
    referral_speciality: Optional[str] = Field(None, max_length=100)
    referral_phone: Optional[str] = Field(None, max_length=20)
    referral_email: Optional[EmailStr] = None
    tests_requested: Optional[str] = None
    investigations_notes: Optional[str] = None
    usg_findings: Optional[str] = None
    lab_tests_imaging: Optional[str] = None
    # Nested Updates
    vitals: Optional[VitalsUpdate] = None
    # Note: Updating lists like diagnoses/medications typically involves replacing the whole list
    # or specific CRUD operations on list items, which requires more complex API design.
    # For simplicity, we might only allow updating the main fields here.

class ConsultationResponse(ConsultationBase):
    id: int
    user_id: int # Who conducted the consultation
    created_at: datetime
    updated_at: Optional[datetime]
    # Nested Responses
    vitals: Optional[VitalsResponse] = None
    diagnoses: List[ConsultationDiagnosisResponse] = []
    medications: List[ConsultationMedicationResponse] = []
    patient: PatientResponse
    user: UserResponse