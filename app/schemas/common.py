from pydantic import BaseModel, Field, ConfigDict
from typing import Any, List, Optional

class Page(BaseModel):
    total: int
    page: int = 1
    per_page: int = 50
    items: list[Any]

class Message(BaseModel):
    ok: bool = True
    message: str = "ok"
