from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime
from typing import List
from app.core.db import get_db
from app.api.deps import get_current_user, get_viewer_site_uids
from app.models.models import Site, SensorData, SensorDevice
from app.schemas.common import Page
from app.schemas.data import DataOut

router = APIRouter()

@router.get("", response_model=Page)
async def list_data(
    db: AsyncSession = Depends(get_db),
    viewer_uids: List[str] = Depends(get_viewer_site_uids),
    site_uid: str | None = None,
    device_id: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    order: str = "desc",
    page: int = 1,
    per_page: int = 50,
    fields: str | None = None,
):
    if per_page < 1 or per_page > 500:
        raise HTTPException(400, "per_page out of range")
    stmt = select(SensorData)
    cnt = select(func.count(SensorData.id))
    site_id = None
    if site_uid:
        res = await db.execute(select(Site).where(Site.uid==site_uid))
        site = res.scalar_one_or_none()
        if not site:
            return {"total": 0, "page": page, "per_page": per_page, "items": []}
        site_id = site.id
        if viewer_uids and site_uid not in viewer_uids:
            return {"total": 0, "page": page, "per_page": per_page, "items": []}
        stmt = stmt.where(SensorData.site_id==site.id)
        cnt = cnt.where(SensorData.site_id==site.id)
    if device_id:
        stmt = stmt.where(SensorData.device_id==device_id)
        cnt = cnt.where(SensorData.device_id==device_id)
    if date_from:
        stmt = stmt.where(SensorData.ts >= date_from)
        cnt = cnt.where(SensorData.ts >= date_from)
    if date_to:
        stmt = stmt.where(SensorData.ts < date_to)
        cnt = cnt.where(SensorData.ts < date_to)

    total = (await db.execute(cnt)).scalar_one()
    order_by = SensorData.ts.desc() if order.lower()=="desc" else SensorData.ts.asc()
    rows = (await db.execute(stmt.order_by(order_by).offset((page-1)*per_page).limit(per_page))).scalars().all()

    selected = None
    if fields:
        selected = set([f.strip() for f in fields.split(",") if f.strip()])

    items = []
    for r in rows:
        d = DataOut(
            id=r.id, site_id=r.site_id, device_id=r.device_id, ts=r.ts,
            ph=r.ph, tss=r.tss, debit=r.debit, nh3n=r.nh3n, cod=r.cod, temp=r.temp, rh=r.rh,
            wind_speed_kmh=r.wind_speed_kmh, wind_deg=r.wind_deg, noise=r.noise,
            co=r.co, so2=r.so2, no2=r.no2, o3=r.o3, pm25=r.pm25, pm10=r.pm10, tvoc=r.tvoc,
            voltage=r.voltage, current=r.current
        ).model_dump()
        if selected:
            d = {k:v for k,v in d.items() if k in selected or k in ("id","ts","site_id","device_id")}
        items.append(d)

    return {"total": total, "page": page, "per_page": per_page, "items": items}

@router.get("/last")
async def last_record(site_uid: str, db: AsyncSession = Depends(get_db), viewer_uids: List[str] = Depends(get_viewer_site_uids)):
    res = await db.execute(select(Site).where(Site.uid==site_uid))
    site = res.scalar_one_or_none()
    if not site:
        raise HTTPException(404, "Site not found")
    if viewer_uids and site_uid not in viewer_uids:
        raise HTTPException(403, "Forbidden")
    row = (await db.execute(select(SensorData).where(SensorData.site_id==site.id).order_by(SensorData.ts.desc()).limit(1))).scalar_one_or_none()
    if not row:
        return {}
    return {
        "id": row.id, "ts": row.ts, "site_id": row.site_id, "device_id": row.device_id,
        "ph": row.ph, "tss": row.tss, "debit": row.debit, "temp": row.temp, "rh": row.rh
    }
