from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import HTTPException, Request, status, Depends
from app.core.config import settings
from typing import Optional


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    now = datetime.utcnow()
    payload = {
        "sub": str(subject),
        "iat": now,
        "exp": now + expires_delta
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def verify_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        subject: str = payload.get("sub")
        if subject is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return subject
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


async def get_current_user(request: Request) -> str:
    # We expect access token inside cookies under key "access_token"
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    subject = verify_token(token)
    return subject
