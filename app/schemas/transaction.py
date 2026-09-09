from typing import Optional

from pydantic import BaseModel
from datetime import datetime

class TransactionCreate(BaseModel):
    description: str
    amount: float

class TransactionResponse(BaseModel):
    id: int
    user_id: int
    description: str
    amount: float
    created_at: datetime

    class Config:
        from_attributes = True
# --- TAMBAHKAN CLASS INI ---
class TransactionUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
class WhatsAppWebhookPayload(BaseModel):
    sender: str
    message: str
