# app/schemas.py
from datetime import datetime, date, time
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, EmailStr, validator
from enum import Enum

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
    class Config:
        from_attributes = True


class User(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: UserRole
    permissions: Dict[str, Any] = {}
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

class PatientResponse(PatientBase):
    id: int
    phone_hash: Optional[str] = None
    email_hash: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime]

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

class AppointmentBase(BaseSchema):
    patient_id: Optional[int] = None
    location_id: int
    start_time: datetime
    end_time: datetime
    reason: Optional[str] = None
    notes: Optional[str] = None
    appointment_type: str = Field(default="consultation", max_length=50)
    status: AppointmentStatus = AppointmentStatus.scheduled

class AppointmentCreate(AppointmentBase):
    new_patient: Optional[NewPatient] = None

    @validator('patient_id', pre=True, always=True)
    def check_patient_logic(cls, v, values):
        if v is None and values.get('new_patient') is None:
            raise ValueError('Either patient_id or new_patient must be provided.')
        if v is not None and values.get('new_patient') is not None:
            raise ValueError('Cannot provide both patient_id and new_patient.')
        return v

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

class LocationScheduleCreate(LocationScheduleBase):
    pass

class LocationScheduleResponse(LocationScheduleBase):
    id: int

# --- Unavailable Period Schemas ---
class UnavailablePeriodBase(BaseSchema):
    location_id: int
    start_datetime: datetime
    end_datetime: datetime
    reason: Optional[str] = Field(None, max_length=255)

class UnavailablePeriodCreate(UnavailablePeriodBase):
    pass

class UnavailablePeriodResponse(UnavailablePeriodBase):
    id: int
    created_by: int
    created_at: datetime

# --- Emergency Block Schemas ---
class EmergencyBlockCreate(BaseSchema):
    block_date: date
    reason: str = Field(..., min_length=5, max_length=255)

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