# hash_password.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

# --- SET YOUR DESIRED PASSWORD HERE ---
password_to_hash = "adminpass" 
hashed_password = hash_password(password_to_hash)

print(f"Password: {password_to_hash}")
print(f"Hashed Password: {hashed_password}")