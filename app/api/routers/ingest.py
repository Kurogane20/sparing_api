from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db import get_db
from app.api.deps import get_current_user
from app.models.models import Site, SensorDevice, SensorData, IngestLog
from app.schemas.data import IngestStateIn, IngestBulkIn
from app.utils.time import to_utc

router = APIRouter()

def _validate_ranges(data: IngestStateIn):
    if data.ph is not None and not (0 <= data.ph <= 14):
        raise HTTPException(400, "pH out of range")
    if data.tss is not None and data.tss < 0:
        raise HTTPException(400, "tss must be >= 0")
    if data.debit is not None and data.debit < 0:
        raise HTTPException(400, "debit must be >= 0")
    if data.temp is not None and not (-40 <= data.temp <= 80):
        raise HTTPException(400, "temp out of range")
    if data.rh is not None and not (0 <= data.rh <= 100):
        raise HTTPException(400, "rh out of range")
    if data.wind_speed_kmh is not None and data.wind_speed_kmh < 0:
        raise HTTPException(400, "wind_speed_kmh must be >= 0")
    if data.noise is not None and data.noise < 0:
        raise HTTPException(400, "noise must be >= 0")

@router.post("/state")
async def ingest_state(body: IngestStateIn, request: Request, db: AsyncSession = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), user=Depends(get_current_user)):
    ip = request.client.host if request.client else None
    try:
        res = await db.execute(select(Site).where(Site.uid==body.site_uid))
        site = res.scalar_one_or_none()
        if not site:
            raise HTTPException(400, "Invalid site_uid")
        if user._role == "viewer":
            # viewers cannot POST
            raise HTTPException(403, "Forbidden")
        _validate_ranges(body)
        # check idempotency
        if idempotency_key:
            ex = await db.execute(select(SensorData).where(SensorData.ingest_idempotency_key==idempotency_key))
            row = ex.scalar_one_or_none()
            if row:
                return {"ok": True, "id": row.id}
        ts_utc = to_utc(body.ts)
        data = SensorData(
            site_id=site.id,
            device_id=body.device_id,
            ts=ts_utc,
            payload=body.payload,
            ph=body.ph, tss=body.tss, debit=body.debit, nh3n=body.nh3n, cod=body.cod,
            temp=body.temp, rh=body.rh, wind_speed_kmh=body.wind_speed_kmh, wind_deg=body.wind_deg, noise=body.noise,
            co=body.co, so2=body.so2, no2=body.no2, o3=body.o3, pm25=body.pm25, pm10=body.pm10, tvoc=body.tvoc,
            voltage=body.voltage, current=body.current,
            ingest_source="api", ingest_idempotency_key=idempotency_key
        )
        db.add(data); await db.commit(); await db.refresh(data)
        db.add(IngestLog(source_ip=ip, api_key_or_user_id=str(user.id), status="ok"))
        await db.commit()
        return {"ok": True, "id": data.id}
    except HTTPException as e:
        db.add(IngestLog(source_ip=ip, api_key_or_user_id=str(user.id), status="error", error_msg=str(e.detail)))
        await db.commit()
        raise

@router.post("/bulk")
async def ingest_bulk(body: IngestBulkIn, request: Request, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    if len(body.bulk) > 1000:
        raise HTTPException(400, "bulk too large (max 1000)")
    results = []
    for item in body.bulk:
        try:
            res = await ingest_state(item, request, db, None, user)  # reuse logic
            results.append(res)
        except HTTPException as e:
            results.append({"ok": False, "error": str(e.detail)})
    return {"results": results}
