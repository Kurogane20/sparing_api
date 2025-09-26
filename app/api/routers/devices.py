from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db import get_db
from app.api.deps import require_roles, get_viewer_site_uids
from app.models.models import Site, SensorDevice
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceOut

router = APIRouter()

@router.post("", dependencies=[Depends(require_roles("admin","operator"))])
async def create_device(data: DeviceCreate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Site).where(Site.uid==data.site_uid))
    site = res.scalar_one_or_none()
    if not site:
        raise HTTPException(400, "Invalid site_uid")
    d = SensorDevice(site_id=site.id, name=data.name, modbus_addr=data.modbus_addr, model=data.model, serial_no=data.serial_no, is_active=data.is_active)
    db.add(d); await db.commit(); await db.refresh(d)
    return {"ok": True, "id": d.id}

@router.get("", response_model=list[DeviceOut])
async def list_devices(site_uid: str | None = None, db: AsyncSession = Depends(get_db), viewer_uids: list[str] = Depends(get_viewer_site_uids)):
    stmt = select(SensorDevice)
    if site_uid:
        res = await db.execute(select(Site).where(Site.uid==site_uid))
        site = res.scalar_one_or_none()
        if not site:
            return []
        stmt = stmt.where(SensorDevice.site_id==site.id)
        if viewer_uids and site_uid not in viewer_uids:
            return []
    res = await db.execute(stmt.order_by(SensorDevice.id.desc()))
    return [DeviceOut(id=d.id, site_id=d.site_id, name=d.name, modbus_addr=d.modbus_addr, model=d.model, serial_no=d.serial_no, is_active=d.is_active) for d in res.scalars().all()]

@router.get("/{id}", response_model=DeviceOut)
async def get_device(id: int, db: AsyncSession = Depends(get_db), viewer_uids: list[str] = Depends(get_viewer_site_uids)):
    res = await db.execute(select(SensorDevice).where(SensorDevice.id==id))
    d = res.scalar_one_or_none()
    if not d:
        raise HTTPException(404, "Not found")
    if viewer_uids:
        site = (await db.execute(select(Site).where(Site.id==d.site_id))).scalar_one_or_none()
        if site and site.uid not in viewer_uids:
            raise HTTPException(403, "Forbidden")
    return DeviceOut(id=d.id, site_id=d.site_id, name=d.name, modbus_addr=d.modbus_addr, model=d.model, serial_no=d.serial_no, is_active=d.is_active)

@router.patch("/{id}", dependencies=[Depends(require_roles("admin","operator"))])
async def update_device(id: int, data: DeviceUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(SensorDevice).where(SensorDevice.id==id))
    d = res.scalar_one_or_none()
    if not d:
        raise HTTPException(404, "Not found")
    for k,v in data.model_dump(exclude_unset=True).items():
        setattr(d, k, v)
    await db.commit()
    return {"ok": True}

@router.delete("/{id}", dependencies=[Depends(require_roles("admin"))])
async def delete_device(id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(SensorDevice).where(SensorDevice.id==id))
    d = res.scalar_one_or_none()
    if not d:
        raise HTTPException(404, "Not found")
    await db.delete(d); await db.commit()
    return {"ok": True}
