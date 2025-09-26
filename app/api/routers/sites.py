from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.core.db import get_db
from app.api.deps import get_current_user, require_roles, get_viewer_site_uids
from app.models.models import Site
from app.schemas.site import SiteCreate, SiteUpdate, SiteOut

router = APIRouter()

@router.post("", dependencies=[Depends(require_roles("admin","operator"))])
async def create_site(data: SiteCreate, db: AsyncSession = Depends(get_db)):
    exists = await db.execute(select(Site).where(Site.uid==data.uid))
    if exists.scalar_one_or_none():
        raise HTTPException(409, "uid exists")
    s = Site(**data.model_dump())
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return {"ok": True, "id": s.id}

@router.get("", response_model=list[SiteOut])
async def list_sites(db: AsyncSession = Depends(get_db), viewer_uids: list[str] = Depends(get_viewer_site_uids)):
    stmt = select(Site)
    if viewer_uids:
        stmt = stmt.where(Site.uid.in_(viewer_uids))
    res = await db.execute(stmt.order_by(Site.id.desc()))
    return [SiteOut(**{
        "id": s.id, "uid": s.uid, "name": s.name, "company_name": s.company_name,
        "lat": s.lat, "lon": s.lon, "is_active": s.is_active
    }) for s in res.scalars().all()]

@router.get("/{id}", response_model=SiteOut)
async def get_site(id: int, db: AsyncSession = Depends(get_db), viewer_uids: list[str] = Depends(get_viewer_site_uids)):
    res = await db.execute(select(Site).where(Site.id==id))
    s = res.scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Not found")
    if viewer_uids and s.uid not in viewer_uids:
        raise HTTPException(403, "Forbidden")
    return SiteOut(id=s.id, uid=s.uid, name=s.name, company_name=s.company_name, lat=s.lat, lon=s.lon, is_active=s.is_active)

@router.patch("/{id}", dependencies=[Depends(require_roles("admin","operator"))])
async def update_site(id: int, data: SiteUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Site).where(Site.id==id))
    s = res.scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Not found")
    payload = data.model_dump(exclude_unset=True)
    for k,v in payload.items():
        setattr(s, k, v)
    await db.commit()
    return {"ok": True}

@router.delete("/{id}", dependencies=[Depends(require_roles("admin"))])
async def delete_site(id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Site).where(Site.id==id))
    s = res.scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Not found")
    await db.delete(s); await db.commit()
    return {"ok": True}
