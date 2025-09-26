from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
from app.core.db import get_db
from app.api.deps import get_viewer_site_uids
from app.models.models import Site, SensorData

router = APIRouter()

@router.get("/sites/{uid}/stats/last-seen")
async def last_seen(uid: str, db: AsyncSession = Depends(get_db), viewer_uids: list[str] = Depends(get_viewer_site_uids)):
    res = await db.execute(select(Site).where(Site.uid==uid))
    site = res.scalar_one_or_none()
    if not site:
        raise HTTPException(404, "Site not found")
    if viewer_uids and uid not in viewer_uids:
        raise HTTPException(403, "Forbidden")
    row = (await db.execute(select(func.max(SensorData.ts)).where(SensorData.site_id==site.id))).scalar_one_or_none()
    return {"site_uid": uid, "last_ts": row}

@router.get("/sites/{uid}/metrics")
async def site_metrics(uid: str, db: AsyncSession = Depends(get_db), viewer_uids: list[str] = Depends(get_viewer_site_uids)):
    res = await db.execute(select(Site).where(Site.uid==uid))
    site = res.scalar_one_or_none()
    if not site:
        raise HTTPException(404, "Site not found")
    if viewer_uids and uid not in viewer_uids:
        raise HTTPException(403, "Forbidden")
    now = datetime.now(timezone.utc)
    day_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    q = await db.execute(select(
        func.avg(SensorData.ph), func.min(SensorData.ph), func.max(SensorData.ph),
        func.avg(SensorData.tss), func.min(SensorData.tss), func.max(SensorData.tss),
        func.avg(SensorData.debit), func.min(SensorData.debit), func.max(SensorData.debit),
    ).where(SensorData.site_id==site.id, SensorData.ts>=day_start))
    (ph_avg, ph_min, ph_max, tss_avg, tss_min, tss_max, debit_avg, debit_min, debit_max) = q.one()
    return {
        "today": {
            "ph": {"avg": ph_avg, "min": ph_min, "max": ph_max},
            "tss": {"avg": tss_avg, "min": tss_min, "max": tss_max},
            "debit": {"avg": debit_avg, "min": debit_min, "max": debit_max},
        }
    }
