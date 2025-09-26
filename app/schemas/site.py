from pydantic import BaseModel, Field
from typing import Optional

class SiteCreate(BaseModel):
    uid: str
    name: str
    company_name: str
    lat: float | None = None
    lon: float | None = None
    is_active: bool = True

class SiteUpdate(BaseModel):
    name: str | None = None
    company_name: str | None = None
    lat: float | None = None
    lon: float | None = None
    is_active: bool | None = None

class SiteOut(BaseModel):
    id: int
    uid: str
    name: str
    company_name: str
    lat: float | None = None
    lon: float | None = None
    is_active: bool
