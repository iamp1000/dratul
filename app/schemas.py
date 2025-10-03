
from datetime import datetime, date, time
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict
from enum import Enum
import re
from decimal import Decimal

# --- Enum Classes ---
class UserRole(str, Enum):
    admin = "admin"
    staff = "staff"
    doctor = "doctor"
    nurse = "nurse"
    receptionist = "receptionist"

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
    ACCESS_DENIED = "ACCESS_DENIED"
    EXPORT = "EXPORT"
    PRINT = "PRINT"

# --- Base Schemas ---
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class TimestampSchema(BaseSchema):
    created_at: datetime
    updated_at: Optional[datetime] = None

# --- User Schemas ---
class UserBase(BaseSchema):
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    role: UserRole

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)

    @validator('password')
    def validate_password_strength(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

class UserUpdate(BaseSchema):
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    permissions: Optional[Dict[str, Any]] = None

class UserPasswordChange(BaseSchema):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @validator('new_password')
    def validate_password_strength(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

class User(UserBase, TimestampSchema):
    id: int
    is_active: bool
    last_login: Optional[datetime] = None
    mfa_enabled: bool = False
    must_change_password: bool = False
    permissions: Optional[Dict[str, Any]] = None

class UserLogin(BaseSchema):
    username: str
    password: str
    mfa_code: Optional[str] = Field(None, pattern=r'^\d{6}$')

class UserSession(BaseSchema):
    user_id: int
    username: str
    role: UserRole
    permissions: Dict[str, Any]
    session_id: str
    expires_at: datetime

# --- Authentication Schemas ---
class Token(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User

class MFASetup(BaseSchema):
    secret: str
    qr_code: str
    backup_codes: List[str]

class MFAVerify(BaseSchema):
    code: str = Field(..., pattern=r'^\d{6}$')

# --- Patient Schemas ---
class PatientBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    phone_number: str = Field(..., pattern=r'^\+?[1-9]\d{1,14}$')
    email: Optional[EmailStr] = None
    date_of_birth: date
    gender: Optional[str] = Field(None, pattern=r'^(male|female|other|prefer_not_to_say)$')
    address: Optional[str] = Field(None, max_length=500)
    whatsapp_number: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')

    @validator('date_of_birth')
    def validate_birth_date(cls, v):
        if v >= date.today():
            raise ValueError('Date of birth must be in the past')
        age = (date.today() - v).days // 365
        if age > 150:
            raise ValueError('Age cannot exceed 150 years')
        return v

class PatientCreate(PatientBase):
    preferred_communication: Optional[CommunicationType] = CommunicationType.phone
    whatsapp_opt_in: bool = False
    consent_to_treatment: bool = Field(..., description="Patient must consent to treatment")
    hipaa_authorization: bool = Field(..., description="Patient must authorize HIPAA")

class PatientUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    email: Optional[EmailStr] = None
    address: Optional[str] = Field(None, max_length=500)
    whatsapp_number: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    preferred_communication: Optional[CommunicationType] = None
    whatsapp_opt_in: Optional[bool] = None

class PatientSearch(BaseSchema):
    query: str = Field(..., min_length=1, max_length=100)
    search_type: str = Field("all", pattern=r'^(name|phone|email|all)$')

class Patient(PatientBase, TimestampSchema):
    id: int
    age: Optional[int] = None
    preferred_communication: CommunicationType
    whatsapp_opt_in: bool
    consent_to_treatment: bool
    consent_to_treatment_date: Optional[datetime]
    hipaa_authorization: bool
    hipaa_authorization_date: Optional[datetime]
    is_deleted: bool = False

    @validator('age', pre=True, always=True)
    def calculate_age(cls, v, values):
        if 'date_of_birth' in values and values['date_of_birth']:
            today = date.today()
            birth_date = values['date_of_birth']
            return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return v

# --- Appointment Schemas ---
class AppointmentBase(BaseSchema):
    patient_id: int
    location_id: int
    start_time: datetime
    end_time: datetime
    reason: Optional[str] = Field(None, max_length=500)
    appointment_type: Optional[str] = Field("consultation", max_length=50)
    preparation_instructions: Optional[str] = Field(None, max_length=1000)

    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v

    @validator('start_time')
    def validate_future_appointment(cls, v):
        if v <= datetime.now():
            raise ValueError('Appointment must be scheduled for the future')
        return v

class AppointmentCreate(AppointmentBase):
    notes: Optional[str] = Field(None, max_length=1000)

class AppointmentUpdate(BaseSchema):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    reason: Optional[str] = Field(None, max_length=500)
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = Field(None, max_length=1000)
    preparation_instructions: Optional[str] = Field(None, max_length=1000)

class AppointmentReschedule(BaseSchema):
    new_start_time: datetime
    new_end_time: datetime
    reason: Optional[str] = Field(None, max_length=200)

    @validator('new_end_time')
    def validate_end_time(cls, v, values):
        if 'new_start_time' in values and v <= values['new_start_time']:
            raise ValueError('End time must be after start time')
        return v

class AppointmentCancel(BaseSchema):
    reason: str = Field(..., min_length=1, max_length=200)
    notify_patient: bool = True

class Appointment(AppointmentBase, TimestampSchema):
    id: int
    status: AppointmentStatus
    confirmation_sent: bool = False
    confirmation_sent_at: Optional[datetime] = None
    reminder_sent: bool = False
    reminder_sent_at: Optional[datetime] = None
    notes: Optional[str] = None
    estimated_cost: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None
    insurance_covered: bool = False
    google_calendar_event_id: Optional[str] = None

class AppointmentWithDetails(Appointment):
    patient: Patient
    location: 'Location'

# --- Location Schemas ---
class LocationBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    email: Optional[EmailStr] = None
    timezone: str = Field("UTC", max_length=50)

class LocationCreate(LocationBase):
    pass

class LocationUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    email: Optional[EmailStr] = None
    timezone: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None

class Location(LocationBase, TimestampSchema):
    id: int
    is_active: bool = True

class LocationScheduleBase(BaseSchema):
    day_of_week: int = Field(..., ge=0, le=6)  # 0=Monday, 6=Sunday
    start_time: time
    end_time: time
    break_start: Optional[time] = None
    break_end: Optional[time] = None

    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v

class LocationScheduleCreate(LocationScheduleBase):
    location_id: int

class LocationSchedule(LocationScheduleBase):
    id: int
    location_id: int
    is_active: bool = True

class UnavailablePeriodBase(BaseSchema):
    location_id: int
    start_datetime: datetime
    end_datetime: datetime
    reason: Optional[str] = Field(None, max_length=200)

    @validator('end_datetime')
    def validate_end_datetime(cls, v, values):
        if 'start_datetime' in values and v <= values['start_datetime']:
            raise ValueError('End datetime must be after start datetime')
        return v

class UnavailablePeriodCreate(UnavailablePeriodBase):
    pass

class UnavailablePeriod(UnavailablePeriodBase, TimestampSchema):
    id: int
    google_calendar_event_id: Optional[str] = None

# --- Document Schemas ---
class DocumentBase(BaseSchema):
    description: Optional[str] = Field(None, max_length=500)
    document_type: str = Field("general", max_length=50)
    sensitivity_level: str = Field("high", pattern=r'^(high|medium|low)$')

class DocumentCreate(DocumentBase):
    patient_id: int
    filename: str = Field(..., min_length=1, max_length=255)

class DocumentUpdate(BaseSchema):
    description: Optional[str] = Field(None, max_length=500)
    document_type: Optional[str] = Field(None, max_length=50)

class Document(DocumentBase, TimestampSchema):
    id: int
    patient_id: int
    filename: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    is_encrypted: bool = True
    upload_date: datetime
    last_accessed: Optional[datetime] = None
    access_count: int = 0

# --- Prescription Schemas ---
class PrescriptionBase(BaseSchema):
    medication_name: str = Field(..., min_length=1, max_length=200)
    dosage: str = Field(..., min_length=1, max_length=100)
    frequency: str = Field(..., min_length=1, max_length=100)
    duration: str = Field(..., min_length=1, max_length=100)
    quantity: int = Field(..., gt=0)
    refills: int = Field(0, ge=0, le=12)
    instructions: Optional[str] = Field(None, max_length=1000)
    notes: Optional[str] = Field(None, max_length=500)

class PrescriptionCreate(PrescriptionBase):
    patient_id: int
    appointment_id: Optional[int] = None

class PrescriptionUpdate(BaseSchema):
    status: Optional[str] = Field(None, pattern=r'^(active|completed|cancelled)$')
    notes: Optional[str] = Field(None, max_length=500)

class Prescription(PrescriptionBase, TimestampSchema):
    id: int
    patient_id: int
    appointment_id: Optional[int] = None
    status: str = "active"
    prescribed_date: datetime

class PrescriptionShare(BaseSchema):
    patient_id: int
    prescription_id: int
    method: str = Field(..., pattern=r'^(whatsapp|email)$')
    recipient: Optional[str] = None  # Phone number for WhatsApp, email for email
    message: Optional[str] = Field(None, max_length=500)

# --- Remark Schemas ---
class RemarkBase(BaseSchema):
    title: Optional[str] = Field(None, max_length=200)
    text: str = Field(..., min_length=1, max_length=2000)
    category: Optional[str] = Field("general", max_length=50)
    priority: str = Field("normal", pattern=r'^(high|normal|low)$')
    is_confidential: bool = False
    visible_to_roles: Optional[List[str]] = None

class RemarkCreate(RemarkBase):
    patient_id: int

class RemarkUpdate(BaseSchema):
    title: Optional[str] = Field(None, max_length=200)
    text: Optional[str] = Field(None, min_length=1, max_length=2000)
    category: Optional[str] = Field(None, max_length=50)
    priority: Optional[str] = Field(None, pattern=r'^(high|normal|low)$')
    is_confidential: Optional[bool] = None

class Remark(RemarkBase, TimestampSchema):
    id: int
    patient_id: int
    author_id: int

class RemarkWithAuthor(Remark):
    author: User

# --- Communication Schemas ---
class CommunicationBase(BaseSchema):
    communication_type: CommunicationType
    subject: Optional[str] = Field(None, max_length=200)
    content: str = Field(..., min_length=1, max_length=2000)

class CommunicationCreate(CommunicationBase):
    patient_id: int
    direction: str = Field("outbound", pattern=r'^(inbound|outbound)$')

class CommunicationLog(CommunicationBase, TimestampSchema):
    id: int
    patient_id: int
    direction: str
    status: str = "sent"
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    external_message_id: Optional[str] = None

# --- Bulk Communication Schemas ---
class BulkCommunicationBase(BaseSchema):
    title: str = Field(..., min_length=1, max_length=200)
    message_content: str = Field(..., min_length=1, max_length=2000)
    communication_type: CommunicationType
    target_criteria: Optional[Dict[str, Any]] = None

class BulkCommunicationCreate(BulkCommunicationBase):
    scheduled_for: Optional[datetime] = None

class BulkCommunication(BulkCommunicationBase, TimestampSchema):
    id: int
    status: str = "draft"
    scheduled_for: Optional[datetime] = None
    total_recipients: int = 0
    sent_count: int = 0
    delivered_count: int = 0
    failed_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

# --- Audit Log Schemas ---
class AuditLogCreate(BaseSchema):
    action: AuditAction
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    patient_id: Optional[int] = None
    details: Optional[str] = None
    access_reason: Optional[str] = Field(None, max_length=200)

class AuditLog(BaseSchema):
    id: int
    user_id: Optional[int] = None
    timestamp: datetime
    action: AuditAction
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    patient_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    details: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    access_reason: Optional[str] = None

# --- WhatsApp Integration Schemas ---
class WhatsAppMessage(BaseSchema):
    phone_number: str = Field(..., pattern=r'^\+?[1-9]\d{1,14}$')
    message: str = Field(..., min_length=1, max_length=1000)
    message_type: str = Field("text", pattern=r'^(text|template|interactive)$')

class WhatsAppWebhook(BaseSchema):
    object: str
    entry: List[Dict[str, Any]]

class WhatsAppSession(BaseSchema):
    id: int
    phone_number: str
    patient_id: Optional[int] = None
    session_id: str
    is_active: bool = True
    current_flow: Optional[str] = None
    current_step: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None
    started_at: datetime
    last_activity: Optional[datetime] = None
    expires_at: Optional[datetime] = None

# --- Calendar Integration Schemas ---
class CalendarEvent(BaseSchema):
    summary: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    start_datetime: datetime
    end_datetime: datetime
    location: Optional[str] = Field(None, max_length=200)

    @validator('end_datetime')
    def validate_end_datetime(cls, v, values):
        if 'start_datetime' in values and v <= values['start_datetime']:
            raise ValueError('End datetime must be after start datetime')
        return v

class GoogleCalendarSync(BaseSchema):
    calendar_id: str = Field(..., min_length=1)
    sync_enabled: bool = True

# --- System Configuration Schemas ---
class SystemConfigurationBase(BaseSchema):
    key: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-zA-Z0-9_\.]+$')
    value: str = Field(..., min_length=1)
    description: Optional[str] = Field(None, max_length=500)
    data_type: str = Field("string", pattern=r'^(string|integer|boolean|json)$')

class SystemConfigurationCreate(SystemConfigurationBase):
    pass

class SystemConfigurationUpdate(BaseSchema):
    value: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, max_length=500)

class SystemConfiguration(SystemConfigurationBase, TimestampSchema):
    id: int

# --- Response Schemas ---
class SuccessResponse(BaseSchema):
    success: bool = True
    message: str
    data: Optional[Any] = None

class ErrorResponse(BaseSchema):
    success: bool = False
    error: str
    details: Optional[str] = None

class PaginatedResponse(BaseSchema):
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int

class HealthCheck(BaseSchema):
    status: str = "healthy"
    timestamp: datetime
    version: str = "1.0.0"
    database: str = "connected"
    services: Dict[str, str] = {}

# --- Statistics and Dashboard Schemas ---
class DashboardStats(BaseSchema):
    total_patients: int
    appointments_today: int
    appointments_week: int
    pending_appointments: int
    completed_appointments_today: int
    revenue_today: Optional[Decimal] = None
    revenue_month: Optional[Decimal] = None

class AppointmentStats(BaseSchema):
    total: int
    by_status: Dict[str, int]
    by_type: Dict[str, int]
    upcoming_today: int
    upcoming_week: int

# Update forward references
AppointmentWithDetails.model_rebuild()
