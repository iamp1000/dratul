# models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text,Date, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .database import Base

# --- Enum for User Roles ---
class UserRole(str, enum.Enum):
    admin = "admin"
    staff = "staff"

# --- User Model ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String)
    password_hash = Column(String, nullable=False)
    role = Column(SQLAlchemyEnum(UserRole), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    logs = relationship("ActivityLog", back_populates="user")

# --- Activity Log Model ---
class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    action = Column(String, nullable=False)
    details = Column(Text)

    user = relationship("User", back_populates="logs")

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone_number = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    date_of_birth = Column(Date, nullable=True) 
    appointments = relationship("Appointment", back_populates="patient")
    documents = relationship("Document", back_populates="patient", cascade="all, delete-orphan")
    remarks = relationship("Remark", back_populates="patient", cascade="all, delete-orphan")

# --- Location Model ---
class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    appointments = relationship("Appointment", back_populates="location")


# --- Appointment Model ---
class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False)
    reason = Column(Text)
    status = Column(String, nullable=False, default="Confirmed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    patient = relationship("Patient", back_populates="appointments")
    location = relationship("Location", back_populates="appointments")
    
    
# --- NEW Document Model ---
class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    file_path = Column(String, nullable=False) # Stores the path to the saved file
    description = Column(String)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="documents")

# --- NEW Remark Model ---
class Remark(Base):
    __tablename__ = "remarks"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False) # Who wrote the remark
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="remarks")
    author = relationship("User") # Link to the user who wrote it
