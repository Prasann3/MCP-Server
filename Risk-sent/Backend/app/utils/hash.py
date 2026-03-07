import hashlib
from passlib.context import CryptContext
from app.core.logging import logger
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception as e:  
        logger.error(f"Password verification error: {e}")
        return False
