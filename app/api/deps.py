# AFTER
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from app.core.db import get_db
from app.core.security import decode_jwt
from app.models.models import User, ViewerSite, Site, AuthTokenBlacklist

bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_token(
    creds: HTTPAuthorizationCredentials = Security(bearer_scheme),
) -> str:
    if not creds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return creds.credentials  # JWT string

async def get_current_user(
    token: str = Depends(get_current_token),   # 👈 pakai bearer, bukan OAuth2
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_jwt(token)
    jti = payload.get("jti")
    # blacklist check
    res = await db.execute(select(AuthTokenBlacklist).where(AuthTokenBlacklist.jti == jti))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=401, detail="Token revoked")

    uid = payload.get("user_id")
    res = await db.execute(select(User).where(User.id == uid, User.is_active == True))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    user._site_uids = payload.get("site_uids", [])
    user._role = payload.get("role", "viewer")
    return user

def require_roles(*roles: str):
    async def _dep(user: User = Depends(get_current_user)):
        if user._role not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return _dep

async def get_viewer_site_uids(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> List[str]:
    if user._role == "viewer":
        return list(user._site_uids or [])
    return []
