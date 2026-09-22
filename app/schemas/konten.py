from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl

class ContentBase(BaseModel):
    nama: str
    akun: str
    status_vt: str = "Kerkun"
    views: int = 0
    link_video: str
    tanggal_upload: date
    status_upload: str = "Uploaded"
    review: str = "Not Yet"

class ContentCreate(ContentBase):
    pass

class ContentUpdate(BaseModel):
    nama: Optional[str] = None
    akun: Optional[str] = None
    status_vt: Optional[str] = None
    views: Optional[int] = None
    link_video: Optional[str] = None
    tanggal_upload: Optional[date] = None
    status_upload: Optional[str] = None
    review: Optional[str] = None

class ContentResponse(ContentBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True