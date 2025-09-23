# app/schemas.py
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from typing import Optional, List
from datetime import datetime, date
from .models import UserRole
import re

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, pattern=r"^(\+?91)?[6-9]\d{9}$")
    role: UserRole

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

    @model_validator(mode='after')
    def validate_password_strength(self) -> 'UserCreate':
        password = self.password
        if password:
            if len(re.findall(r'[A-Z]', password)) < 1:
                raise ValueError("Password must contain at least 1 uppercase letter")
            if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
                raise ValueError("Password must contain at least 1 special character")
        return self

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None

class User(UserBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class ActivityLog(BaseModel):
    id: int
    timestamp: datetime
    action: str
    details: Optional[str] = None
    user: User
    model_config = ConfigDict(from_attributes=True)
class Location(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class DocumentBase(BaseModel):
    description: Optional[str] = None
    file_path: str

class Document(DocumentBase):
    id: int
    patient_id: int
    upload_date: datetime
    model_config = ConfigDict(from_attributes=True)

class RemarkCreate(BaseModel):
    text: str
    
class Remark(BaseModel):
    id: int
    text: str
    created_at: datetime
    author: User
    model_config = ConfigDict(from_attributes=True)

class AppointmentBase(BaseModel):
    location_id: int
    start_time: datetime
    end_time: datetime
    reason: Optional[str] = None
    status: str

class PatientBase(BaseModel):
    name: str
    phone_number: str
    email: Optional[EmailStr] = None
    date_of_birth: date 


class AppointmentCreate(AppointmentBase):
    patient_id: int

class PatientCreate(PatientBase):
    pass


class AppointmentUpdate(BaseModel):
    status: Optional[str] = None
    reason: Optional[str] = None


class Appointment(AppointmentBase):
    id: int
    patient: 'Patient'  # Forward reference to Patient
    location: Location
    model_config = ConfigDict(from_attributes=True)

class Patient(PatientBase):
    id: int
    created_at: datetime
    age: Optional[int] = None
    appointments: List[Appointment] = []
    documents: List[Document] = []
    remarks: List[Remark] = []
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='after')
    def calculate_age(self) -> 'Patient':
        if self.date_of_birth:
            today = date.today()
            self.age = today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return self


class Remark(BaseModel): 
    id: int
    text: str
    created_at: datetime
    author: User
    model_config = ConfigDict(from_attributes=True)

class Appointment(AppointmentBase):
    id: int
    patient: 'Patient' 
    location: 'Location'
    model_config = ConfigDict(from_attributes=True)

# --- Location Schema ---
class Location(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

# --- Appointment Schemas ---
class AppointmentBase(BaseModel):
    patient_id: int
    location_id: int
    start_time: datetime
    end_time: datetime
    reason: Optional[str] = None
    status: str

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    status: Optional[str] = None
    reason: Optional[str] = None

class Appointment(AppointmentBase):
    id: int
    patient: Patient
    location: Location
    model_config = ConfigDict(from_attributes=True)
    
class DocumentBase(BaseModel):
    description: Optional[str] = None
    file_path: str

class Document(BaseModel):
    id: int
    file_path: str
    description: Optional[str] = None
    upload_date: datetime
    model_config = ConfigDict(from_attributes=True)


Patient.model_rebuild()
Appointment.model_rebuild()
Remark.model_rebuild()
