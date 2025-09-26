from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

class IngestStateIn(BaseModel):
    site_uid: str
    device_id: int | None = None
    ts: datetime | None = None
    ph: float | None = None
    tss: float | None = None
    debit: float | None = None
    nh3n: float | None = None
    cod: float | None = None
    temp: float | None = None
    rh: float | None = None
    wind_speed_kmh: float | None = None
    wind_deg: float | None = None
    noise: float | None = None
    co: float | None = None
    so2: float | None = None
    no2: float | None = None
    o3: float | None = None
    pm25: float | None = None
    pm10: float | None = None
    tvoc: float | None = None
    voltage: float | None = None
    current: float | None = None
    payload: dict[str, Any] | None = None

class IngestBulkIn(BaseModel):
    bulk: list[IngestStateIn]

class DataOut(BaseModel):
    id: int
    site_id: int
    device_id: int | None = None
    ts: datetime
    ph: float | None = None
    tss: float | None = None
    debit: float | None = None
    nh3n: float | None = None
    cod: float | None = None
    temp: float | None = None
    rh: float | None = None
    wind_speed_kmh: float | None = None
    wind_deg: float | None = None
    noise: float | None = None
    co: float | None = None
    so2: float | None = None
    no2: float | None = None
    o3: float | None = None
    pm25: float | None = None
    pm10: float | None = None
    tvoc: float | None = None
    voltage: float | None = None
    current: float | None = None
