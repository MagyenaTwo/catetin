from pydantic import BaseModel
from datetime import datetime

class RecapCreate(BaseModel):
    bulan: int
    tahun: int

class RecapResponse(BaseModel):
    id: int
    bulan: int
    tahun: int
    total_konten: int
    total_views: int
    created_at: datetime

    class Config:
        from_attributes = True