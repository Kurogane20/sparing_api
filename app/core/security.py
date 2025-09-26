from datetime import datetime, timedelta, timezone
from typing import Optional, List
import jwt
from passlib.hash import argon2
from fastapi import HTTPException, status, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import uuid

from app.core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_token(creds: HTTPAuthorizationCredentials = Security(bearer_scheme)) -> str:
    if not creds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return creds.credentials  # <- JWT string

def hash_password(p: str) -> str:
    return argon2.hash(p)

def verify_password(p: str, h: str) -> bool:
    return argon2.verify(p, h)

def create_jwt(sub: str, role: str, user_id: int, site_uids: Optional[List[str]]=None, expires_minutes: int=60, token_type: str="access"):
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_minutes)
    jti = str(uuid.uuid4())
    payload = {
        "sub": sub,
        "role": role,
        "user_id": user_id,
        "site_uids": site_uids or [],
        "jti": jti,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)
    return token, jti, exp

def decode_jwt(token: str):
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
