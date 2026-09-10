from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TransaksiKeluarBase(BaseModel):
    description: str = Field(..., min_length=1, example="Beli Makan Siang")
    amount: float = Field(..., gt=0, example=45000.0)
    category: Optional[str] = Field(None, example="Makanan")


# Sesuaikan nama class ini agar cocok dengan import router kamu
class Transaksi_KeluarCreate(TransaksiKeluarBase):
    pass


class Transaksi_KeluarUpdate(BaseModel):
    description: Optional[str] = Field(None, min_length=1)
    amount: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None)


class Transaksi_KeluarResponse(TransaksiKeluarBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)