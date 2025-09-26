import asyncio
from datetime import datetime, timedelta, timezone
import random

from app.core.db import SessionLocal, engine
from app.models.models import User, Site, ViewerSite, SensorDevice, SensorData
from app.core.security import hash_password

async def main():
    async with SessionLocal() as db:
        # admin/operator/viewer
        admin = User(name="Admin", email="admin@example.com", role="admin", password_hash=hash_password("Admin#123"))
        op = User(name="Operator", email="op@example.com", role="operator", password_hash=hash_password("Op#12345"))
        viewer = User(name="Viewer", email="viewer@example.com", role="viewer", password_hash=hash_password("Viewer#123"))
        db.add_all([admin, op, viewer]); await db.commit()
        await db.refresh(admin); await db.refresh(op); await db.refresh(viewer)

        s1 = Site(uid="aqmsFOEmmEPISI01", name="Site A", company_name="Mitra Mutiara")
        s2 = Site(uid="aqmsXYZ", name="Site B", company_name="Contoso")
        db.add_all([s1, s2]); await db.commit(); await db.refresh(s1); await db.refresh(s2)

        db.add(ViewerSite(user_id=viewer.id, site_id=s1.id)); await db.commit()

        d1 = SensorDevice(site_id=s1.id, name="Device A")
        d2 = SensorDevice(site_id=s1.id, name="Device B")
        d3 = SensorDevice(site_id=s2.id, name="Device C")
        db.add_all([d1, d2, d3]); await db.commit(); await db.refresh(d1); await db.refresh(d2); await db.refresh(d3)

        now = datetime.now(timezone.utc)
        for site in (s1, s2):
            for day in range(7):
                base = now - timedelta(days=day)
                for i in range(50):
                    ts = base - timedelta(minutes=30 * i)
                    sd = SensorData(
                        site_id=site.id, device_id=d1.id if site == s1 else d3.id, ts=ts,
                        ph=round(random.uniform(6.5, 7.5), 2),
                        tss=round(random.uniform(50, 200), 1),
                        debit=round(random.uniform(10, 20), 1),
                        temp=round(random.uniform(24, 30), 1),
                        rh=round(random.uniform(60, 90), 1),
                    )
                    db.add(sd)
        await db.commit()

    # penting: tutup pool/engine sebelum loop ditutup
    await engine.dispose()
    print("Seed done")

if __name__ == "__main__":
    asyncio.run(main())
