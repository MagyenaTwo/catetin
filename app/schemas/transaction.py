from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TransactionCreate(BaseModel):
  description: str
  amount: float
  image_url: Optional[str] = None
  image_public_id: Optional[str] = None


class TransactionUpdate(BaseModel):
  description: Optional[str] = None
  amount: Optional[float] = None
  image_url: Optional[str] = None
  image_public_id: Optional[str] = None


class TransactionResponse(BaseModel):
  id: int
  user_id: int
  description: str
  amount: float
  image_url: Optional[str] = None
  image_public_id: Optional[str] = None
  created_at: datetime

  class Config:
    from_attributes = True


class WhatsAppWebhookPayload(BaseModel):
  sender: str
  message: str