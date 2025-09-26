from pydantic import BaseModel
from typing import Optional

class DeviceCreate(BaseModel):
    site_uid: str
    name: str
    modbus_addr: int | None = None
    model: str | None = None
    serial_no: str | None = None
    is_active: bool = True

class DeviceUpdate(BaseModel):
    name: str | None = None
    modbus_addr: int | None = None
    model: str | None = None
    serial_no: str | None = None
    is_active: bool | None = None

class DeviceOut(BaseModel):
    id: int
    site_id: int
    name: str
    modbus_addr: int | None = None
    model: str | None = None
    serial_no: str | None = None
    is_active: bool
