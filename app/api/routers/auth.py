from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.core.db import get_db
from app.core.security import hash_password, verify_password, create_jwt
from app.models.models import User, ViewerSite, Site, AuthTokenBlacklist
from app.schemas.auth import LoginIn, TokenOut, UserOut
from app.api.deps import get_current_user, require_roles

router = APIRouter()

@router.post("/login", response_model=TokenOut)
async def login(data: LoginIn, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.email==data.email))
    user = res.scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    site_uids = []
    if user.role == "viewer":
        q = await db.execute(select(Site.uid).join(ViewerSite, ViewerSite.site_id==Site.id).where(ViewerSite.user_id==user.id))
        site_uids = [r[0] for r in q.all()]
    access, jti_a, _ = create_jwt(user.email, user.role, user.id, site_uids, expires_minutes=60, token_type="access")
    refresh, jti_r, _ = create_jwt(user.email, user.role, user.id, site_uids, expires_minutes=60*24*7, token_type="refresh")
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    site_uids = []
    if user._role == "viewer":
        site_uids = user._site_uids or []
    return {"id": user.id, "name": user.name, "email": user.email, "role": user._role, "site_uids": site_uids}

@router.post("/register", dependencies=[Depends(require_roles("admin"))])
async def register_user(payload: dict, db: AsyncSession = Depends(get_db)):
    # payload: name, email, password, role
    if payload.get("role") not in ("admin","operator","viewer"):
        raise HTTPException(400, "Invalid role")
    exists = await db.execute(select(User).where(User.email==payload["email"]))
    if exists.scalar_one_or_none():
        raise HTTPException(409, "Email already exists")
    u = User(name=payload["name"], email=payload["email"], role=payload["role"], password_hash=hash_password(payload["password"]))
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return {"ok": True, "id": u.id}

@router.post("/refresh", response_model=TokenOut)
async def refresh(token: str, db: AsyncSession = Depends(get_db)):
    # token in body
    from app.core.security import decode_jwt
    payload = decode_jwt(token)
    if payload.get("type") != "refresh":
        raise HTTPException(400, "Not a refresh token")
    user_id = payload.get("user_id")
    res = await db.execute(select(User).where(User.id==user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(401, "User not found")
    site_uids = payload.get("site_uids", [])
    access, _, _ = create_jwt(user.email, user.role, user.id, site_uids, expires_minutes=60, token_type="access")
    refresh_t, _, _ = create_jwt(user.email, user.role, user.id, site_uids, expires_minutes=60*24*7, token_type="refresh")
    return {"access_token": access, "refresh_token": refresh_t, "token_type": "bearer"}

@router.post("/logout")
async def logout(token: str, db: AsyncSession = Depends(get_db)):
    from app.core.security import decode_jwt
    payload = decode_jwt(token)
    jti = payload.get("jti")
    user_id = payload.get("user_id")
    exp = payload.get("exp")
    from datetime import datetime, timezone
    expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
    db.add(AuthTokenBlacklist(jti=jti, user_id=user_id, expires_at=expires_at, reason="logout"))
    await db.commit()
    return {"ok": True}
