from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
import jwt
from datetime import datetime, timezone
from fastapi.responses import PlainTextResponse

from app.core.config import settings
from app.core.db import get_db
from app.models.models import Site, SensorData, IngestLog

router = APIRouter()

@router.get("/api/get-key", response_class=PlainTextResponse)
async def get_key():
    return  "sparing"

@router.post("/api/post-data")
async def post_data(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.json()
    token = body.get("token")
    if not token:
        raise HTTPException(400, "Token is required")
    
    try:
        decode = jwt.decode(token, settings.jwt_secret or "sparing", algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(400, "invalid token format")
    
    uid = decode.get("uid")
    data = decode.get("data")
    if not uid or not isinstance(data, list) or len(data) == 0 or len(data) > 30:
        raise HTTPException (400, "Invalid data format")
    
    site = (await db.execute(select(Site).where(Site.uid==uid))).scalar_one_or_none()
    if not site: 
        raise HTTPException(401, "Invalid UID")
    
    rows = []
    now = datetime.now(timezone.utc)
    for d in data:
        ts = datetime.fromtimestamp(int(d["datetime"]), tz=timezone.utc)
        ph = float(d["ph"])
        if not (0 <= ph <= 14):
            raise HTTPException(400, "Invalid pH value")
        cod = float(d["cod"])
        if cod < 0:
            raise HTTPException(400, "Invalid COD value")
        tss = float(d["tss"])
        if tss < 0:
            raise HTTPException(400, "Invalid TSS value")
        debit = float(d["debit"])
        if debit < 0:
            raise HTTPException(400, "Invalid Debit value")
        rows.append({
            "site_id": site.id, "ts": ts, "ph": ph, "cod": cod,
             "tss": tss, "debit": debit, "created_at": now,
              "ingest_source": "getdata", "payload": None
              })
        
        if rows:
            await db.execute(insert(SensorData), rows)
            await db.commit()

        db.add(IngestLog(source_ip=(request.client.host if request.client else None),
                         api_key_or_user_id="getdata", status="ok",))
        await db.commit()
        return {"message": "Data Berhasil Disimpan", "rows": len(rows)}
