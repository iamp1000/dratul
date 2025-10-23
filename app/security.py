
import os
import secrets
import hashlib
import pyotp
import qrcode
from io import BytesIO
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Dict, Any, List
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import redis
import json
import logging
from ipaddress import ip_address, ip_network
from .database import get_db
from . import models, crud


# Configure logging for security events
logging.basicConfig(level=logging.INFO)
security_logger = logging.getLogger("security")

# Enhanced password hashing with multiple algorithms
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__rounds=4,
    argon2__memory_cost=65536,
    argon2__parallelism=1,
)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
MFA_TOKEN_EXPIRE_MINUTES = 5

# OAuth2 schemes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")
bearer_scheme = HTTPBearer(auto_error=False)

# Redis for session management and rate limiting
try:
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        password=os.getenv("REDIS_PASSWORD"),
        decode_responses=True
    )
    redis_client.ping()
except:
    redis_client = None
    security_logger.warning("Redis not available, using in-memory storage")

# In-memory fallback for sessions
in_memory_sessions = {}

class SecurityConfig:
    """HIPAA-compliant security configuration"""
    # Password policies
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL_CHARS = True
    PASSWORD_HISTORY_COUNT = 12

    # Account lockout policies
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30

    # Session security
    SESSION_TIMEOUT_MINUTES = 30
    FORCE_LOGOUT_INACTIVE_MINUTES = 120

    # MFA settings
    MFA_REQUIRED_FOR_ADMIN = True
    MFA_BACKUP_CODES_COUNT = 10

    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_WINDOW_MINUTES = 15
    
    WHATSAPP_MESSAGE_LIMIT = 3  
    WHATSAPP_MESSAGE_WINDOW = 1  
    
    # Appointment booking limits
    APPOINTMENT_BOOKING_DAILY_LIMIT = 2  
    APPOINTMENT_BOOKING_COOLDOWN_HOURS = 1  

    # IP allowlisting
    ALLOWED_IP_RANGES = [
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "127.0.0.1/32"
    ]

class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""

    def __init__(self):
        self.master_key = os.getenv("MASTER_ENCRYPTION_KEY")
        if not self.master_key:
            # Generate a new key if not provided (for development only)
            self.master_key = Fernet.generate_key().decode()
            security_logger.warning("Using generated encryption key - not suitable for production")

        self.fernet = Fernet(self.master_key.encode())

    def encrypt(self, data: str) -> bytes:
        """Encrypt sensitive data"""
        if not data:
            return b""
        return self.fernet.encrypt(data.encode())

    def decrypt(self, encrypted_data: bytes) -> str:
        """Decrypt sensitive data"""
        if not encrypted_data:
            return ""
        return self.fernet.decrypt(encrypted_data).decode()

    def hash_for_lookup(self, data: str) -> str:
        """Create a hash for searchable lookups (one-way)"""
        if not data:
            return ""
        return hashlib.sha256(data.lower().strip().encode()).hexdigest()

class AuditLogger:
    """HIPAA-compliant audit logging service"""

    def __init__(self):
        self.logger = logging.getLogger("hipaa_audit")
        handler = logging.FileHandler("hipaa_audit.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log_access(self, user_id: int, action: str, resource: str, 
                resource_id: str = None, patient_id: int = None,
                ip_address: str = None, user_agent: str = None,
                success: bool = True, details: str = None):
        """Log access to PHI or system resources"""
        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "resource_id": resource_id,
            "patient_id": patient_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "success": success,
            "details": details
        }

        self.logger.info(json.dumps(audit_entry))
    def info(self, message: str, **kwargs):
        self._log("INFO", message, kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning level message"""
        self._log("WARNING", message, kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error level message"""
        self._log("ERROR", message, kwargs)
    
    def _log(self, level: str, message: str, extra_data: dict = None):
        """Internal logging method"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
            **(extra_data or {})
        }
        
        if level == "INFO":
            self.logger.info(json.dumps(log_entry))
        elif level == "WARNING":
            self.logger.warning(json.dumps(log_entry))
        elif level == "ERROR":
            self.logger.error(json.dumps(log_entry))


class RateLimiter:
    """Rate limiting service for API endpoints and WhatsApp messages"""
    def __init__(self):
        self.requests = {}  # Fallback in-memory storage
    
    def is_allowed(self, key: str, limit: int = SecurityConfig.RATE_LIMIT_REQUESTS,  window_minutes: int = SecurityConfig.RATE_LIMIT_WINDOW_MINUTES) -> bool:
        """Check if request is allowed under rate limit"""
        now = datetime.now()
        window_start = now - timedelta(minutes=window_minutes)
        
        if redis_client:
            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start.timestamp())
            pipe.zadd(key, {str(now.timestamp()): now.timestamp()})
            pipe.zcount(key, window_start.timestamp(), now.timestamp())
            pipe.expire(key, window_minutes * 60)
            results = pipe.execute()
            request_count = results[2]
            return request_count <= limit
        else:
            # Fallback to in-memory
            if key not in self.requests:
                self.requests[key] = []
            
            # Clean old requests
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > window_start
            ]
            
            if len(self.requests[key]) >= limit:
                return False
            
            self.requests[key].append(now)
            return True
    
    def limit(self, rate_string: str):
        def decorator(func):
            import functools
            from fastapi import HTTPException, Request, status
            
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                
                if request:
                    # Parse rate_string (e.g., "5/minute")
                    parts = rate_string.split('/')
                    if len(parts) == 2:
                        try:
                            requests_limit = int(parts[0])
                            time_unit = parts[1].lower()
                            
                            # Convert time unit to minutes
                            if time_unit in ['minute', 'minutes']:
                                window_minutes = 1
                            elif time_unit in ['hour', 'hours']:
                                window_minutes = 60
                            elif time_unit in ['day', 'days']:
                                window_minutes = 1440
                            else:
                                window_minutes = 1  # Default to 1 minute
                            
                            # Create rate limit key based on IP
                            client_ip = getattr(request.client, 'host', 'unknown')
                            rate_key = f"rate_limit:{func.__name__}:{client_ip}"
                            
                            # Check rate limit
                            if not self.is_allowed(rate_key, requests_limit, window_minutes):
                                raise HTTPException(
                                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                                    detail=f"Rate limit exceeded: {rate_string}"
                                )
                        except ValueError:
                            pass
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator

    def check_whatsapp_rate_limit(self, phone_number: str, 
        message_limit: int = 3, 
        window_minutes: int = 1) -> bool:
        rate_key = f"whatsapp:{phone_number}"
        return self.is_allowed(rate_key, message_limit, window_minutes)
        
    def check_appointment_booking_limit(self, phone_number: str, daily_limit: int = 2) -> bool:
        today = datetime.now().strftime('%Y-%m-%d')
        rate_key = f"appointment_booking:{phone_number}:{today}"
        return self.is_allowed(rate_key, daily_limit, window_minutes=1440)


class SessionManager:
    """Secure session management with Redis backend"""

    def __init__(self):
        self.encryption_service = EncryptionService()

    def create_session(self, user_id: int, user_data: Dict[str, Any], 
                      ip_address: str) -> str:
        """Create a new secure session"""
        session_id = secrets.token_urlsafe(32)
        session_data = {
            "user_id": user_id,
            "user_data": user_data,
            "ip_address": ip_address,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat()
        }

        # Encrypt session data
        encrypted_data = self.encryption_service.encrypt(json.dumps(session_data))

        if redis_client:
            redis_client.setex(
                f"session:{session_id}",
                SecurityConfig.SESSION_TIMEOUT_MINUTES * 60,
                encrypted_data
            )
        else:
            in_memory_sessions[session_id] = {
                "data": encrypted_data,
                "expires": datetime.now() + timedelta(minutes=SecurityConfig.SESSION_TIMEOUT_MINUTES)
            }

        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve and validate session data"""
        try:
            if redis_client:
                encrypted_data = redis_client.get(f"session:{session_id}")
            else:
                session_entry = in_memory_sessions.get(session_id)
                if session_entry and session_entry["expires"] > datetime.now():
                    encrypted_data = session_entry["data"]
                else:
                    encrypted_data = None

            if not encrypted_data:
                return None

            session_data = json.loads(self.encryption_service.decrypt(encrypted_data))

            # Update last activity
            session_data["last_activity"] = datetime.now(timezone.utc).isoformat()
            self.update_session(session_id, session_data)

            return session_data
        except Exception as e:
            security_logger.error(f"Session retrieval error: {str(e)}")
            return None

    def update_session(self, session_id: str, session_data: Dict[str, Any]):
        """Update session data"""
        encrypted_data = self.encryption_service.encrypt(json.dumps(session_data))

        if redis_client:
            redis_client.setex(
                f"session:{session_id}",
                SecurityConfig.SESSION_TIMEOUT_MINUTES * 60,
                encrypted_data
            )
        else:
            if session_id in in_memory_sessions:
                in_memory_sessions[session_id]["data"] = encrypted_data

    def destroy_session(self, session_id: str):
        """Destroy a session"""
        if redis_client:
            redis_client.delete(f"session:{session_id}")
        else:
            in_memory_sessions.pop(session_id, None)

class MFAService:
    """Multi-Factor Authentication service"""

    def __init__(self):
        self.encryption_service = EncryptionService()

    def generate_secret(self, username: str) -> tuple[str, str, List[str]]:
        """Generate MFA secret and backup codes"""
        secret = pyotp.random_base32()

        # Generate QR code
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            username,
            issuer_name="Dr. Dhingra's Clinic"
        )

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)

        qr_image = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        qr_image.save(buffer, format="PNG")
        qr_code = base64.b64encode(buffer.getvalue()).decode()

        # Generate backup codes
        backup_codes = [secrets.token_hex(4).upper() for _ in range(SecurityConfig.MFA_BACKUP_CODES_COUNT)]

        return secret, qr_code, backup_codes

    def verify_totp(self, secret: str, token: str) -> bool:
        """Verify TOTP token"""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=1)  # Allow 30 seconds window
        except:
            return False

    def verify_backup_code(self, user_backup_codes: List[str], code: str) -> bool:
        """Verify backup code and remove it if valid"""
        code_upper = code.upper()
        if code_upper in user_backup_codes:
            user_backup_codes.remove(code_upper)
            return True
        return False

class IPValidator:
    """IP address validation for security"""

    @staticmethod
    def is_allowed_ip(ip_str: str) -> bool:
        """Check if IP address is in allowed ranges"""
        if not SecurityConfig.ALLOWED_IP_RANGES:
            return True  # No restrictions

        try:
            client_ip = ip_address(ip_str)
            for allowed_range in SecurityConfig.ALLOWED_IP_RANGES:
                if client_ip in ip_network(allowed_range):
                    return True
            return False
        except:
            return False  # Invalid IP format

# Initialize services
encryption_service = EncryptionService()
audit_logger = AuditLogger()
rate_limiter = RateLimiter()
session_manager = SessionManager()
mfa_service = MFAService()

# Password utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Unknown/legacy hash formats should not crash login; treat as non-match
        return False

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

def validate_password_strength(password: str) -> Dict[str, bool]:
    """Validate password against HIPAA requirements"""
    # Define allowed special characters clearly to avoid quoting issues
    special_chars = set('!@#$%^&*(),.?":{}|<>')

    checks = {
        "length": len(password) >= SecurityConfig.MIN_PASSWORD_LENGTH,
        "uppercase": any(c.isupper() for c in password) if SecurityConfig.REQUIRE_UPPERCASE else True,
        "lowercase": any(c.islower() for c in password) if SecurityConfig.REQUIRE_LOWERCASE else True,
        "digits": any(c.isdigit() for c in password) if SecurityConfig.REQUIRE_DIGITS else True,
        "special": any(c in special_chars for c in password) if SecurityConfig.REQUIRE_SPECIAL_CHARS else True
    }
    return checks

# JWT utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "type": "access",
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_urlsafe(16)  # JWT ID for token blacklisting
    })

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_urlsafe(16)
    })

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_mfa_token(user_id: int) -> str:
    """Create temporary MFA verification token"""
    data = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=MFA_TOKEN_EXPIRE_MINUTES),
        "type": "mfa",
        "iat": datetime.now(timezone.utc)
    }

    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != token_type:
            return None

        return payload
    except JWTError:
        return None

# Dependencies for FastAPI
async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    security_logger.info(f"get_current_user called for path: {request.url.path}")
    security_logger.info(f"Received token: {token[:30]}...") # Log first 30 chars for safety
    security_logger.info(f"Request headers: {dict(request.headers)}")
    security_logger.info(f"get_current_user called for path: {request.url.path}")
    security_logger.info(f"Received token: {token[:30]}...") # Log first 30 chars for safety
    security_logger.info(f"Request headers: {dict(request.headers)}")
    security_logger.info(f"get_current_user called for path: {request.url.path}")
    security_logger.info(f"Received token: {token[:30]}...") # Log first 30 chars for safety
    security_logger.info(f"Request headers: {dict(request.headers)}")
    """Get current authenticated user with comprehensive security checks"""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Rate limiting
    client_ip = request.client.host
    rate_key = f"auth:{client_ip}"

    if not rate_limiter.is_allowed(rate_key):
        audit_logger.log_access(
            user_id=None,
            action="ACCESS_DENIED",
            resource="authentication",
            ip_address=client_ip,
            success=False,
            details="Rate limit exceeded"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests"
        )

    # IP validation
    if not IPValidator.is_allowed_ip(client_ip):
        audit_logger.log_access(
            user_id=None,
            action="ACCESS_DENIED",
            resource="authentication",
            ip_address=client_ip,
            success=False,
            details="IP address not allowed"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied from this IP address"
        )

    # Verify token
    payload = verify_token(token, "access")
    if not payload:
        raise credentials_exception

    username = payload.get("sub")
    user_id = payload.get("user_id")

    if not username or not user_id:
        raise credentials_exception

    # Get user from database
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise credentials_exception

    # Check if user is active
    if not user.is_active:
        audit_logger.log_access(
            user_id=user_id,
            action="ACCESS_DENIED",
            resource="authentication",
            ip_address=client_ip,
            success=False,
            details="User account is inactive"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Check account lockout
    if user.account_locked_until and user.account_locked_until > datetime.now(timezone.utc):
        audit_logger.log_access(
            user_id=user_id,
            action="ACCESS_DENIED",
            resource="authentication",
            ip_address=client_ip,
            success=False,
            details="Account is locked"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is temporarily locked"
        )

    # Log successful access
    audit_logger.log_access(
        user_id=user_id,
        action="READ",
        resource="authentication",
        ip_address=client_ip,
        user_agent=request.headers.get("User-Agent"),
        success=True
    )

    return user

def require_role(*allowed_roles: str):
    """Decorator factory for role-based access control"""
    def role_dependency(current_user: models.User = Depends(get_current_user)) -> models.User:
        if current_user.role.value not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user

    return role_dependency

def require_permission(permission: str):
    """Decorator factory for permission-based access control"""
    def permission_dependency(current_user: models.User = Depends(get_current_user)) -> models.User:
        user_permissions = current_user.permissions or {}
        if not user_permissions.get(permission, False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required permission: {permission}"
            )
        return current_user

    return permission_dependency

# Specific role dependencies
require_admin = require_role("admin")
require_staff = require_role("admin", "staff", "doctor", "nurse")
require_medical_staff = require_role("admin", "doctor", "nurse")

# Permission constants
class Permissions:
    # Patient management
    PATIENT_READ = "patient:read"
    PATIENT_WRITE = "patient:write"
    PATIENT_DELETE = "patient:delete"

    # Appointment management
    APPOINTMENT_READ = "appointment:read"
    APPOINTMENT_WRITE = "appointment:write"
    APPOINTMENT_DELETE = "appointment:delete"

    # Medical records
    MEDICAL_RECORD_READ = "medical_record:read"
    MEDICAL_RECORD_WRITE = "medical_record:write"

    # User management
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"

    # System administration
    SYSTEM_CONFIG = "system:config"
    AUDIT_READ = "audit:read"
    BULK_COMMUNICATION = "communication:bulk"

# Middleware for additional security headers
def add_security_headers(response):
    """Add security headers to response"""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Export all security services and utilities
__all__ = [
    "SecurityConfig",
    "EncryptionService", 
    "AuditLogger",
    "RateLimiter",
    "SessionManager",
    "MFAService",
    "IPValidator",
    "encryption_service",
    "audit_logger",
    "rate_limiter",
    "session_manager",
    "mfa_service",
    "verify_password",
    "get_password_hash",
    "validate_password_strength",
    "create_access_token",
    "create_refresh_token",
    "create_mfa_token",
    "verify_token",
    "get_current_user",
    "require_role",
    "require_permission",
    "require_admin",
    "require_staff",
    "require_medical_staff",
    "Permissions",
    "add_security_headers"
]
