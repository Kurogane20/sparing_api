from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db import get_db
from app.api.deps import require_roles
from app.models.models import User, Site, ViewerSite

router = APIRouter()

@router.post("/viewer-sites", dependencies=[Depends(require_roles("admin"))])
async def assign_viewer(payload: dict, db: AsyncSession = Depends(get_db)):
    # payload: user_id (viewer), site_uid
    user_id = int(payload["user_id"])
    site_uid = payload["site_uid"]
    u = (await db.execute(select(User).where(User.id==user_id))).scalar_one_or_none()
    if not u or u.role != "viewer":
        raise HTTPException(400, "Not a viewer")
    s = (await db.execute(select(Site).where(Site.uid==site_uid))).scalar_one_or_none()
    if not s:
        raise HTTPException(400, "Invalid site_uid")
    exists = (await db.execute(select(ViewerSite).where(ViewerSite.user_id==u.id, ViewerSite.site_id==s.id))).scalar_one_or_none()
    if exists:
        return {"ok": True}
    db.add(ViewerSite(user_id=u.id, site_id=s.id)); await db.commit()
    return {"ok": True}

@router.delete("/viewer-sites", dependencies=[Depends(require_roles("admin"))])
async def unassign_viewer(payload: dict, db: AsyncSession = Depends(get_db)):
    # payload: user_id (viewer), site_uid
    user_id = int(payload["user_id"])
    site_uid = payload["site_uid"]
    u = (await db.execute(select(User).where(User.id==user_id))).scalar_one_or_none()
    if not u or u.role != "viewer":
        raise HTTPException(400, "Not a viewer")
    s = (await db.execute(select(Site).where(Site.uid==site_uid))).scalar_one_or_none()
    if not s:
        raise HTTPException(400, "Invalid site_uid")
    vs = (await db.execute(select(ViewerSite).where(ViewerSite.user_id==u.id, ViewerSite.site_id==s.id))).scalar_one_or_none()
    if not vs:
        return {"ok": True}
    await db.delete(vs); await db.commit()
    return {"ok": True}

@router.get("/viewer-sites", dependencies=[Depends(require_roles("admin"))])
async def list_viewer_sites(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ViewerSite))
    viewer_sites = result.scalars().all()
    return {"viewer_sites": [{"user_id": vs.user_id, "site_id": vs.site_id} for vs in viewer_sites]}

@router.get("/viewers", dependencies=[Depends(require_roles("admin"))])
async def list_viewers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.role=="viewer"))
    viewers = result.scalars().all()
    return {"viewers": [{"id": v.id,  "email": v.email} for v in viewers]}

@router.get("/users", dependencies=[Depends(require_roles("admin"))])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return {"users": [{"id": u.id, "email": u.email, "role": u.role} for u in users]}

@router.post("/users", dependencies=[Depends(require_roles("admin"))])
async def create_user(payload: dict, db: AsyncSession = Depends(get_db)):
    # payload: username, email, password, role
    from app.core.security import get_password_hash
    # username = payload["username"]
    email = payload["email"]
    password = payload["password"]
    role = payload.get("role", "viewer")
    if role not in ["admin", "editor", "viewer"]:
        raise HTTPException(400, "Invalid role")
    existing_user = (await db.execute(select(User).where((User.username==username) | (User.email==email)))).scalar_one_or_none()
    if existing_user:
        raise HTTPException(400, "Username or email already exists")
    hashed_password = get_password_hash(password)
    new_user = User(username=username, email=email, hashed_password=hashed_password, role=role)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return {"id": new_user.id, "username": new_user.username, "email": new_user.email, "role": new_user.role}

